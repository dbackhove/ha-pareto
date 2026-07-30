"""Pure ranking logic for Pareto.

This module deliberately imports nothing from Home Assistant. Decay maths and
sort order are the parts of this integration most likely to be wrong, and
keeping them free of the HA runtime means they can be tested with plain pytest.
"""

from __future__ import annotations

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


def _parse_day(day: str) -> date | None:
    """Return the date for an ISO day key, or None if it is malformed."""
    try:
        return date.fromisoformat(day)
    except ValueError:
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
        parsed = _parse_day(day)
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
