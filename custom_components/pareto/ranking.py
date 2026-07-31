"""Pure ranking logic for Pareto.

This module deliberately imports nothing from Home Assistant. Decay maths and
sort order are the parts of this integration most likely to be wrong, and
keeping them free of the HA runtime means they can be tested with plain pytest.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from .const import MIN_RETENTION_DAYS, RETENTION_HALF_LIVES


@dataclass(frozen=True)
class EntityUsage:
    """Usage of one entity, already aggregated across all users."""

    entity_id: str
    counts: dict[str, int]
    last_used: str | None


@dataclass(frozen=True)
class RankedEntity:
    """One entry in a rendered Pareto list."""

    entity_id: str
    score: float
    count: int
    last_used: str | None
    pinned: bool


def parse_day(day: str) -> date | None:
    """Return the date for an ISO day key, or None if it is malformed."""
    try:
        return date.fromisoformat(day)
    except (ValueError, TypeError):
        return None


def decay_score(counts: dict[str, int], today: date, half_life_days: float) -> float:
    """Sum the day buckets, weighting each by exponential decay.

    A bucket dated in the future (clock skew, timezone edits) is clamped to age
    zero rather than allowed to score above its raw count.
    """
    if half_life_days <= 0:
        return float(total_count(counts))

    score = 0.0
    for day, count in counts.items():
        parsed = parse_day(day)
        if parsed is None:
            continue
        age = max(0, (today - parsed).days)
        score += count * (0.5 ** (age / half_life_days))
    return score


def total_count(counts: dict[str, int]) -> int:
    """Return the undecayed number of recorded uses."""
    return sum(counts.values())


def retention_days(half_life_days: float) -> int:
    """Return how many days of buckets are worth keeping.

    Beyond six half-lives a bucket contributes under 1.6% of its original
    weight, so it is storage cost without ranking value.
    """
    return max(MIN_RETENTION_DAYS, int(RETENTION_HALF_LIVES * half_life_days))


def _domain_of(entity_id: str) -> str:
    return entity_id.split(".", 1)[0]


def _passes_filters(
    entity_id: str,
    include_domains: frozenset[str],
    exclude_domains: frozenset[str],
    exclude_entities: frozenset[str],
) -> bool:
    domain = _domain_of(entity_id)
    if include_domains and domain not in include_domains:
        return False
    if domain in exclude_domains:
        return False
    return entity_id not in exclude_entities


def build_ranked_list(
    usages: list[EntityUsage],
    *,
    mode: str,
    today: date,
    half_life_days: float,
    limit: int,
    include_domains: frozenset[str],
    exclude_domains: frozenset[str],
    exclude_entities: frozenset[str],
    pinned: tuple[str, ...],
    exists: Callable[[str], bool],
) -> list[RankedEntity]:
    """Render one Pareto list.

    ``mode`` is "top" (sorted by decayed score) or "recent" (sorted by
    ``last_used``). Pinned entities are prepended in their configured order and
    count against ``limit``; an explicit pin bypasses all filters
    (include_domains, exclude_domains, exclude_entities), because pinning
    something and filtering it out is a contradiction the user resolved by
    pinning it. Entities that no longer exist are removed before truncation,
    so a full list stays full.
    """
    by_id = {u.entity_id: u for u in usages}

    def to_ranked(entity_id: str, is_pinned: bool) -> RankedEntity:
        found = by_id.get(entity_id)
        counts = found.counts if found else {}
        return RankedEntity(
            entity_id=entity_id,
            score=round(decay_score(counts, today, half_life_days), 2),
            count=total_count(counts),
            last_used=found.last_used if found else None,
            pinned=is_pinned,
        )

    pinned_ids = [e for e in dict.fromkeys(pinned) if exists(e)]
    pinned_set = set(pinned_ids)

    candidates = [
        u
        for u in usages
        if u.entity_id not in pinned_set
        and _passes_filters(u.entity_id, include_domains, exclude_domains, exclude_entities)
        and exists(u.entity_id)
    ]

    if mode == "recent":
        candidates = [u for u in candidates if u.last_used is not None]
        candidates.sort(key=lambda u: u.last_used or "", reverse=True)
    else:
        candidates.sort(key=lambda u: decay_score(u.counts, today, half_life_days), reverse=True)

    ranked = [to_ranked(e, True) for e in pinned_ids]
    ranked.extend(to_ranked(u.entity_id, False) for u in candidates)
    return ranked[:limit]


def merge_personal_and_global(
    personal: list[RankedEntity],
    fallback: list[RankedEntity],
    limit: int,
) -> list[tuple[RankedEntity, bool]]:
    """Pad a personal list out of the global one, up to ``limit``.

    Somebody who installed Pareto an hour ago -- or who mostly operates the
    house by wall switch, where no user id is attached to anything -- has
    almost no usage of their own. An empty card would be honest and useless.

    Own entries keep their order and stay in front; the global ranking
    supplies the rest, skipping anything already listed. The list therefore
    personalises itself as real usage accumulates, with no switchover to see.

    Globally pinned entities need no special case here: ``build_ranked_list``
    puts pins in front without requiring any usage, so they are already in
    ``personal``. This only ever appends unpinned filler.

    The flag is True for entries that came from the reader's own usage.
    """
    merged: list[tuple[RankedEntity, bool]] = [(entry, True) for entry in personal[:limit]]
    seen = {entry.entity_id for entry, _ in merged}

    for entry in fallback:
        if len(merged) >= limit:
            break
        if entry.entity_id in seen:
            continue
        seen.add(entry.entity_id)
        merged.append((entry, False))

    return merged
