# Pareto Phase 1 (Backend) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Home Assistant custom integration that counts which entities a human actually operates and exposes the Top X and Recent X as two sensor entities.

**Architecture:** A listener on `EVENT_CALL_SERVICE` records user-initiated service calls into per-day, per-user buckets in HA's `Store`. A coordinator recomputes two ranked lists — one by exponentially decayed score, one by recency — on a debounce and once daily. Two sensors publish those lists as attributes. All ranking math lives in `ranking.py` with zero Home Assistant imports, so it is testable with plain pytest.

**Tech Stack:** Python 3.13+, Home Assistant 2026.7+, `pytest`, `pytest-homeassistant-custom-component`, `freezegun`. No runtime dependencies beyond Home Assistant itself.

**Spec:** `docs/superpowers/specs/2026-07-30-ha-pareto-design.md`

## Global Constraints

- Integration domain is `pareto`. Storage key is `pareto_usage`, storage version `1`.
- Code, comments, docstrings, README and `strings.json` are **English**. German goes only in `translations/de.json`.
- **Never** add a `Co-Authored-By` trailer or any Claude/Anthropic attribution to commit messages. This repo will be public.
- A usage event counts only when `context.user_id is not None` **and** `context.parent_id is None`.
- Day buckets use **local** dates via `dt_util.now()`, never UTC.
- `ranking.py` must not import anything from `homeassistant`. This is enforced by a test.
- Defaults: `top_count=10`, `recent_count=5`, `half_life_days=14`.
- Bucket retention is `max(90, 6 * half_life_days)` days.
- `Store` writes use `async_delay_save` with a 60 second delay. Sensor recomputes are debounced by 5 seconds.
- The integration is single-instance.
- Every commit message uses Conventional Commits (`feat:`, `test:`, `chore:`, `docs:`, `fix:`).

## File Structure

| File | Responsibility |
|---|---|
| `custom_components/pareto/const.py` | Domain, option keys, defaults, service blacklists |
| `custom_components/pareto/ranking.py` | **Pure.** Decay math, filter pipeline, pins, truncation |
| `custom_components/pareto/store.py` | Persistence, bucket writes, pruning, aggregation |
| `custom_components/pareto/tracker.py` | Event listener, context filter, target resolution |
| `custom_components/pareto/coordinator.py` | Holds store, debounced + daily recompute, listener fan-out |
| `custom_components/pareto/importer.py` | Logbook backfill |
| `custom_components/pareto/config_flow.py` | Setup flow and options flow |
| `custom_components/pareto/sensor.py` | `sensor.pareto_top`, `sensor.pareto_recent` |
| `custom_components/pareto/__init__.py` | Wiring: setup entry, unload, service registration |

Dependency direction is strictly one-way: `ranking` ← `store` ← `coordinator` ← `sensor`. Nothing imports upward.

**One deviation from the spec's file list:** the spec put recompute orchestration in
`__init__.py`. This plan gives it its own `coordinator.py`, because otherwise
`__init__.py` would carry setup, listener registration, service registration *and*
state management. Everything else matches the spec.

---

### Task 1: Project scaffolding and decay math

**Files:**
- Create: `pyproject.toml`
- Create: `requirements-test.txt`
- Create: `custom_components/pareto/__init__.py` (empty placeholder)
- Create: `custom_components/pareto/const.py`
- Create: `custom_components/pareto/ranking.py`
- Test: `tests/test_ranking_decay.py`
- Test: `tests/test_ranking_purity.py`

**Interfaces:**
- Consumes: nothing (first task)
- Produces:
  - `EntityUsage(entity_id: str, counts: dict[str, int], last_used: str | None)` — frozen dataclass
  - `RankedEntity(entity_id: str, score: float, count: int, last_used: str | None, pinned: bool)` — frozen dataclass
  - `decay_score(counts: dict[str, int], today: date, half_life_days: float) -> float`
  - `total_count(counts: dict[str, int]) -> int`
  - `retention_days(half_life_days: float) -> int`
  - const module with `DOMAIN`, option keys, defaults, blacklists

- [ ] **Step 1: Create the project files**

`pyproject.toml`:

```toml
[project]
name = "ha-pareto"
version = "0.1.0"
description = "Home Assistant integration that ranks entities by how often you actually use them"
requires-python = ">=3.13"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
target-version = "py313"
line-length = 100
```

`requirements-test.txt`:

```
pytest
pytest-homeassistant-custom-component
freezegun
ruff
```

`custom_components/pareto/__init__.py` — leave completely empty for now; Task 6 fills it.

- [ ] **Step 2: Create `custom_components/pareto/const.py`**

```python
"""Constants for the Pareto integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "pareto"

STORAGE_KEY: Final = "pareto_usage"
STORAGE_VERSION: Final = 1
SAVE_DELAY: Final = 60
UPDATE_DEBOUNCE: Final = 5

CONF_TOP_COUNT: Final = "top_count"
CONF_RECENT_COUNT: Final = "recent_count"
CONF_HALF_LIFE_DAYS: Final = "half_life_days"
CONF_INCLUDE_DOMAINS: Final = "include_domains"
CONF_EXCLUDE_DOMAINS: Final = "exclude_domains"
CONF_EXCLUDE_ENTITIES: Final = "exclude_entities"
CONF_PINNED_ENTITIES: Final = "pinned_entities"

DEFAULT_TOP_COUNT: Final = 10
DEFAULT_RECENT_COUNT: Final = 5
DEFAULT_HALF_LIFE_DAYS: Final = 14

MIN_RETENTION_DAYS: Final = 90
RETENTION_HALF_LIVES: Final = 6

# Service calls that are configuration plumbing, not "using" an entity.
BLOCKED_DOMAINS: Final = frozenset(
    {"persistent_notification", "recorder", "system_log", "frontend", DOMAIN}
)
BLOCKED_SERVICES: Final = frozenset({"homeassistant.update_entity", "logbook.log"})

SERVICE_IMPORT_HISTORY: Final = "import_history"
ATTR_DAYS: Final = "days"
DEFAULT_IMPORT_DAYS: Final = 10
```

- [ ] **Step 3: Write the failing tests**

`tests/test_ranking_decay.py`:

```python
"""Decay math is the part most likely to be subtly wrong, so pin it to exact numbers."""

from datetime import date

import pytest

from custom_components.pareto.ranking import decay_score, retention_days, total_count

TODAY = date(2026, 7, 30)


def test_today_counts_at_full_weight():
    assert decay_score({"2026-07-30": 4}, TODAY, 14.0) == pytest.approx(4.0)


def test_one_half_life_ago_counts_half():
    # 2026-07-16 is exactly 14 days before 2026-07-30
    assert decay_score({"2026-07-16": 4}, TODAY, 14.0) == pytest.approx(2.0)


def test_two_half_lives_ago_counts_a_quarter():
    # 2026-07-02 is exactly 28 days before 2026-07-30
    assert decay_score({"2026-07-02": 4}, TODAY, 14.0) == pytest.approx(1.0)


def test_buckets_are_summed():
    counts = {"2026-07-30": 1, "2026-07-16": 4}
    assert decay_score(counts, TODAY, 14.0) == pytest.approx(3.0)


def test_empty_counts_score_zero():
    assert decay_score({}, TODAY, 14.0) == pytest.approx(0.0)


def test_future_bucket_is_not_amplified():
    """A clock skew must never let a bucket score above its raw count."""
    assert decay_score({"2026-08-05": 4}, TODAY, 14.0) == pytest.approx(4.0)


def test_malformed_day_key_is_ignored():
    assert decay_score({"not-a-date": 99, "2026-07-30": 2}, TODAY, 14.0) == pytest.approx(2.0)


def test_total_count_sums_raw_values():
    assert total_count({"2026-07-30": 1, "2026-07-16": 4}) == 5


def test_total_count_empty():
    assert total_count({}) == 0


def test_retention_uses_floor_of_90_days():
    assert retention_days(14.0) == 90


def test_retention_scales_with_long_half_life():
    assert retention_days(30.0) == 180
```

`tests/test_ranking_purity.py`:

```python
"""ranking.py must stay free of Home Assistant imports so it tests without fixtures."""

import ast
import pathlib


def test_ranking_module_has_no_homeassistant_imports():
    source = pathlib.Path("custom_components/pareto/ranking.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)

    offenders = [name for name in imported if name.split(".")[0] == "homeassistant"]
    assert offenders == [], f"ranking.py must stay HA-free, found: {offenders}"
```

- [ ] **Step 4: Run the tests to verify they fail**

```bash
pip install -r requirements-test.txt
python -m pytest tests/test_ranking_decay.py tests/test_ranking_purity.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'custom_components.pareto.ranking'`

- [ ] **Step 5: Write `custom_components/pareto/ranking.py`**

```python
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
```

- [ ] **Step 6: Run the tests to verify they pass**

```bash
python -m pytest tests/test_ranking_decay.py tests/test_ranking_purity.py -v
```

Expected: PASS, 12 tests.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml requirements-test.txt custom_components tests
git commit -m "feat: add project scaffolding and decay scoring"
```

---

### Task 2: The filter pipeline

**Files:**
- Modify: `custom_components/pareto/ranking.py`
- Test: `tests/test_ranking_pipeline.py`

**Interfaces:**
- Consumes: `EntityUsage`, `RankedEntity`, `decay_score`, `total_count` from Task 1
- Produces:
  ```python
  def build_ranked_list(
      usages: list[EntityUsage],
      *,
      mode: str,                      # "top" or "recent"
      today: date,
      half_life_days: float,
      limit: int,
      include_domains: frozenset[str],
      exclude_domains: frozenset[str],
      exclude_entities: frozenset[str],
      pinned: tuple[str, ...],
      exists: Callable[[str], bool],
  ) -> list[RankedEntity]
  ```

The pipeline order from the spec is load-bearing and the tests below pin it:

```
usages -> include_domains -> exclude_domains/entities -> sort -> prepend pins
       -> drop non-existent -> truncate to limit
```

- [ ] **Step 1: Write the failing tests**

`tests/test_ranking_pipeline.py`:

```python
"""Pipeline order is load-bearing: pins outrank score, and pins count against the limit."""

from datetime import date

from custom_components.pareto.ranking import EntityUsage, build_ranked_list

TODAY = date(2026, 7, 30)
NONE: frozenset[str] = frozenset()


def usage(entity_id: str, count: int, day: str = "2026-07-30", last_used: str | None = None):
    return EntityUsage(
        entity_id=entity_id,
        counts={day: count},
        last_used=last_used or f"{day}T12:00:00+02:00",
    )


def build(usages, *, mode="top", limit=10, include=NONE, exclude_d=NONE,
          exclude_e=NONE, pinned=(), exists=lambda _e: True):
    return build_ranked_list(
        usages,
        mode=mode,
        today=TODAY,
        half_life_days=14.0,
        limit=limit,
        include_domains=include,
        exclude_domains=exclude_d,
        exclude_entities=exclude_e,
        pinned=pinned,
        exists=exists,
    )


def test_top_sorts_by_descending_score():
    result = build([usage("light.a", 1), usage("light.b", 5), usage("light.c", 3)])
    assert [r.entity_id for r in result] == ["light.b", "light.c", "light.a"]


def test_recent_sorts_by_descending_last_used():
    usages = [
        EntityUsage("light.old", {"2026-07-28": 9}, "2026-07-28T10:00:00+02:00"),
        EntityUsage("light.new", {"2026-07-30": 1}, "2026-07-30T18:00:00+02:00"),
    ]
    result = build(usages, mode="recent")
    assert [r.entity_id for r in result] == ["light.new", "light.old"]


def test_recent_ignores_entries_without_last_used():
    usages = [
        EntityUsage("light.a", {"2026-07-30": 1}, None),
        EntityUsage("light.b", {"2026-07-30": 1}, "2026-07-30T18:00:00+02:00"),
    ]
    result = build(usages, mode="recent")
    assert [r.entity_id for r in result] == ["light.b"]


def test_limit_truncates():
    result = build([usage(f"light.l{i}", i) for i in range(1, 6)], limit=2)
    assert len(result) == 2


def test_include_domains_acts_as_whitelist():
    result = build([usage("light.a", 5), usage("switch.b", 9)], include=frozenset({"light"}))
    assert [r.entity_id for r in result] == ["light.a"]


def test_empty_include_domains_lets_everything_through():
    result = build([usage("light.a", 5), usage("switch.b", 9)])
    assert len(result) == 2


def test_exclude_domains_removes_whole_domain():
    result = build([usage("light.a", 5), usage("switch.b", 9)], exclude_d=frozenset({"switch"}))
    assert [r.entity_id for r in result] == ["light.a"]


def test_exclude_entities_removes_one_entity():
    result = build([usage("light.a", 5), usage("light.b", 9)], exclude_e=frozenset({"light.b"}))
    assert [r.entity_id for r in result] == ["light.a"]


def test_pins_come_first_regardless_of_score():
    result = build([usage("light.a", 1), usage("light.b", 99)], pinned=("light.a",))
    assert [r.entity_id for r in result] == ["light.a", "light.b"]
    assert result[0].pinned is True
    assert result[1].pinned is False


def test_pins_keep_their_configured_order():
    result = build([usage("light.a", 1), usage("light.b", 2)], pinned=("light.b", "light.a"))
    assert [r.entity_id for r in result] == ["light.b", "light.a"]


def test_pin_without_usage_history_appears_with_zero():
    result = build([usage("light.a", 5)], pinned=("switch.never_used",))
    assert result[0].entity_id == "switch.never_used"
    assert result[0].count == 0
    assert result[0].score == 0.0
    assert result[0].pinned is True


def test_pins_count_against_the_limit():
    usages = [usage(f"light.l{i}", i) for i in range(1, 6)]
    result = build(usages, limit=3, pinned=("light.l1",))
    assert len(result) == 3
    assert result[0].entity_id == "light.l1"


def test_pin_is_not_duplicated_when_it_also_ranks():
    result = build([usage("light.a", 99), usage("light.b", 1)], pinned=("light.a",))
    assert [r.entity_id for r in result] == ["light.a", "light.b"]


def test_pin_overrides_exclusion():
    """An explicit pin is a stronger statement than a blanket domain exclusion."""
    result = build([usage("light.a", 5)], exclude_d=frozenset({"light"}), pinned=("light.a",))
    assert [r.entity_id for r in result] == ["light.a"]


def test_nonexistent_entities_are_dropped():
    result = build(
        [usage("light.gone", 9), usage("light.here", 1)],
        exists=lambda e: e != "light.gone",
    )
    assert [r.entity_id for r in result] == ["light.here"]


def test_dropping_nonexistent_entities_still_fills_the_limit():
    """Removal happens before truncation, so the list is not left short."""
    usages = [usage("light.gone", 99), usage("light.a", 5), usage("light.b", 3)]
    result = build(usages, limit=2, exists=lambda e: e != "light.gone")
    assert [r.entity_id for r in result] == ["light.a", "light.b"]


def test_nonexistent_pin_is_dropped_too():
    result = build([usage("light.a", 1)], pinned=("light.ghost",), exists=lambda e: e == "light.a")
    assert [r.entity_id for r in result] == ["light.a"]


def test_empty_input_yields_empty_list():
    assert build([]) == []
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
python -m pytest tests/test_ranking_pipeline.py -v
```

Expected: FAIL — `ImportError: cannot import name 'build_ranked_list'`

- [ ] **Step 3: Append the pipeline to `custom_components/pareto/ranking.py`**

Add `from collections.abc import Callable` to the imports at the top, then append:

```python
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
    count against ``limit``; an explicit pin beats the exclusion filters,
    because pinning something and excluding it is a contradiction the user
    resolved by pinning it. Entities that no longer exist are removed before
    truncation, so a full list stays full.
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
        candidates.sort(
            key=lambda u: decay_score(u.counts, today, half_life_days), reverse=True
        )

    ranked = [to_ranked(e, True) for e in pinned_ids]
    ranked.extend(to_ranked(u.entity_id, False) for u in candidates)
    return ranked[:limit]
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
python -m pytest tests/ -v
```

Expected: PASS, 30 tests total.

- [ ] **Step 5: Commit**

```bash
git add custom_components/pareto/ranking.py tests/test_ranking_pipeline.py
git commit -m "feat: add ranking filter pipeline with pins and exclusions"
```

---

### Task 3: Persistence layer

**Files:**
- Create: `custom_components/pareto/store.py`
- Test: `tests/test_store.py`
- Test: `tests/conftest.py`

**Interfaces:**
- Consumes: `EntityUsage` from Task 1, constants from Task 1
- Produces:
  ```python
  class ParetoStoreError(Exception): ...

  class ParetoStore:
      def __init__(self, hass: HomeAssistant) -> None
      async def async_load(self) -> None   # raises ParetoStoreError on a newer format
      def record(self, entity_id: str, user_id: str, when: datetime) -> None
      def record_import(self, entity_id: str, user_id: str, day: str, when_iso: str) -> bool
      def prune(self, today: date, keep_days: int) -> None
      def aggregated(self) -> list[EntityUsage]
      def schedule_save(self) -> None
  ```
  `record_import` returns `True` if it wrote, `False` if the bucket already existed.

- [ ] **Step 1: Create `tests/conftest.py`**

```python
"""Shared fixtures. auto_enable_custom_integrations is required by
pytest-homeassistant-custom-component before HA will load anything from
custom_components/."""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield
```

- [ ] **Step 2: Write the failing tests**

`tests/test_store.py`:

```python
from datetime import date, datetime, timedelta, timezone

import pytest

from custom_components.pareto.store import ParetoStore

BERLIN = timezone(timedelta(hours=2))
USER_A = "69d919fb68524e7086650439297dd452"
USER_B = "a3f1c2d4e5f6a7b8c9d0e1f2a3b4c5d6"


@pytest.fixture
async def store(hass):
    s = ParetoStore(hass)
    await s.async_load()
    return s


async def test_load_starts_empty(store):
    assert store.aggregated() == []


async def test_record_creates_a_bucket(store):
    store.record("light.a", USER_A, datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN))
    usage = store.aggregated()[0]
    assert usage.entity_id == "light.a"
    assert usage.counts == {"2026-07-30": 1}


async def test_repeated_records_increment_the_same_bucket(store):
    when = datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN)
    for _ in range(3):
        store.record("light.a", USER_A, when)
    assert store.aggregated()[0].counts == {"2026-07-30": 3}


async def test_aggregation_sums_across_users(store):
    when = datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN)
    store.record("light.a", USER_A, when)
    store.record("light.a", USER_B, when)
    store.record("light.a", USER_B, when)
    assert store.aggregated()[0].counts == {"2026-07-30": 3}


async def test_users_are_kept_separate_internally(store):
    """Phase 2 builds per-user lists from this, so the split must survive."""
    when = datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN)
    store.record("light.a", USER_A, when)
    store.record("light.a", USER_B, when)
    buckets = store.raw()["light.a"]["buckets"]
    assert buckets[USER_A] == {"2026-07-30": 1}
    assert buckets[USER_B] == {"2026-07-30": 1}


async def test_last_used_tracks_the_most_recent_across_users(store):
    store.record("light.a", USER_A, datetime(2026, 7, 30, 18, 0, tzinfo=BERLIN))
    store.record("light.a", USER_B, datetime(2026, 7, 30, 9, 0, tzinfo=BERLIN))
    assert store.aggregated()[0].last_used == "2026-07-30T18:00:00+02:00"


async def test_late_evening_lands_in_the_local_day(store):
    """23:30 Berlin is 21:30 UTC. A UTC bucket key would be right here but wrong
    in winter; what matters is that we use the local date of the passed value."""
    store.record("light.a", USER_A, datetime(2026, 7, 30, 23, 30, tzinfo=BERLIN))
    assert store.aggregated()[0].counts == {"2026-07-30": 1}


async def test_import_writes_into_an_empty_bucket(store):
    assert store.record_import("light.a", USER_A, "2026-07-25", "2026-07-25T12:00:00+02:00")
    assert store.aggregated()[0].counts == {"2026-07-25": 1}


async def test_import_is_idempotent(store):
    store.record_import("light.a", USER_A, "2026-07-25", "2026-07-25T12:00:00+02:00")
    store.record_import("light.a", USER_A, "2026-07-25", "2026-07-25T12:00:00+02:00")
    assert store.aggregated()[0].counts == {"2026-07-25": 1}


async def test_import_never_overwrites_live_data(store):
    store.record("light.a", USER_A, datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN))
    wrote = store.record_import("light.a", USER_A, "2026-07-30", "2026-07-30T08:00:00+02:00")
    assert wrote is False
    assert store.aggregated()[0].counts == {"2026-07-30": 1}


async def test_import_fills_only_the_missing_day(store):
    store.record("light.a", USER_A, datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN))
    store.record_import("light.a", USER_A, "2026-07-29", "2026-07-29T12:00:00+02:00")
    assert store.aggregated()[0].counts == {"2026-07-29": 1, "2026-07-30": 1}


async def test_prune_drops_old_buckets(store):
    store.record_import("light.a", USER_A, "2026-01-01", "2026-01-01T12:00:00+01:00")
    store.record_import("light.a", USER_A, "2026-07-30", "2026-07-30T12:00:00+02:00")
    store.prune(date(2026, 7, 30), keep_days=90)
    assert store.aggregated()[0].counts == {"2026-07-30": 1}


async def test_prune_removes_entities_left_with_nothing(store):
    store.record_import("light.a", USER_A, "2026-01-01", "2026-01-01T12:00:00+01:00")
    store.prune(date(2026, 7, 30), keep_days=90)
    assert store.aggregated() == []


async def test_prune_keeps_a_bucket_exactly_on_the_boundary(store):
    store.record_import("light.a", USER_A, "2026-05-01", "2026-05-01T12:00:00+02:00")
    store.prune(date(2026, 7, 30), keep_days=90)  # 2026-05-01 is 90 days before
    assert store.aggregated()[0].counts == {"2026-05-01": 1}


async def test_corrupt_payload_starts_empty_instead_of_raising(hass):
    s = ParetoStore(hass)
    with patch.object(s._store, "async_load", side_effect=ValueError("corrupt")):
        await s.async_load()
    assert s.aggregated() == []


async def test_non_dict_payload_starts_empty(hass):
    s = ParetoStore(hass)
    with patch.object(s._store, "async_load", return_value=["not", "a", "dict"]):
        await s.async_load()
    assert s.aggregated() == []


async def test_newer_storage_format_refuses_to_load(hass):
    """A file written by a future Pareto must not be silently replaced.

    Starting empty here would look harmless until the first delayed save
    overwrote real data. Refusing to load surfaces it instead.
    """
    s = ParetoStore(hass)
    with patch.object(s._store, "async_load", side_effect=NotImplementedError):
        with pytest.raises(ParetoStoreError):
            await s.async_load()
```

Add these to the imports at the top of the file:

```python
from unittest.mock import patch

from custom_components.pareto.store import ParetoStore, ParetoStoreError
```

- [ ] **Step 3: Run the tests to verify they fail**

```bash
python -m pytest tests/test_store.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'custom_components.pareto.store'`

- [ ] **Step 4: Write `custom_components/pareto/store.py`**

```python
"""Persistence for Pareto usage counters."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

from .const import SAVE_DELAY, STORAGE_KEY, STORAGE_VERSION
from .ranking import EntityUsage

_LOGGER = logging.getLogger(__name__)


class ParetoStoreError(Exception):
    """Raised when stored data exists but cannot be used safely."""


class ParetoStore:
    """Per-entity, per-user, per-day usage counters backed by HA's Store.

    Layout keeps the entity on the outside and the user on the inside. Phase 1
    aggregates across users; a future per-user card reads one level deeper
    without a data migration.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict[str, dict[str, Any]] = {}

    async def async_load(self) -> None:
        """Load from disk.

        Unreadable data starts empty rather than blocking setup. Data written
        by a *newer* Pareto is different: starting empty would look harmless
        until the first delayed save destroyed it, so that case raises.
        """
        try:
            raw = await self._store.async_load()
        except NotImplementedError as err:
            raise ParetoStoreError(
                "Pareto storage was written by a newer version and cannot be read"
            ) from err
        except Exception:  # noqa: BLE001 - never let bad data block setup
            _LOGGER.warning("Could not read Pareto storage, starting with empty data", exc_info=True)
            self._data = {}
            return

        if not isinstance(raw, dict):
            self._data = {}
            return
        entries = raw.get("data")
        self._data = entries if isinstance(entries, dict) else {}

    @callback
    def raw(self) -> dict[str, dict[str, Any]]:
        """Return the underlying structure. For tests and the importer."""
        return self._data

    def _entry(self, entity_id: str) -> dict[str, Any]:
        return self._data.setdefault(entity_id, {"last_used": None, "buckets": {}})

    @callback
    def record(self, entity_id: str, user_id: str, when: datetime) -> None:
        """Count one live usage. ``when`` must already be in local time."""
        entry = self._entry(entity_id)
        day = when.date().isoformat()
        buckets = entry["buckets"].setdefault(user_id, {})
        buckets[day] = buckets.get(day, 0) + 1

        stamp = when.isoformat()
        if entry["last_used"] is None or stamp > entry["last_used"]:
            entry["last_used"] = stamp
        self.schedule_save()

    @callback
    def record_import(self, entity_id: str, user_id: str, day: str, when_iso: str) -> bool:
        """Write one historical usage, but only into a bucket that does not exist.

        This single rule makes the import idempotent, stops it from ever
        clobbering live data, and lets an aborted run resume by simply being
        run again. Returns whether anything was written.
        """
        entry = self._entry(entity_id)
        buckets = entry["buckets"].setdefault(user_id, {})
        if day in buckets:
            return False

        buckets[day] = 1
        if entry["last_used"] is None or when_iso > entry["last_used"]:
            entry["last_used"] = when_iso
        self.schedule_save()
        return True

    @callback
    def prune(self, today: date, keep_days: int) -> None:
        """Drop buckets older than ``keep_days``, and entities left with none."""
        cutoff = (today - timedelta(days=keep_days)).isoformat()

        for entity_id in list(self._data):
            entry = self._data[entity_id]
            for user_id in list(entry["buckets"]):
                kept = {d: c for d, c in entry["buckets"][user_id].items() if d >= cutoff}
                if kept:
                    entry["buckets"][user_id] = kept
                else:
                    del entry["buckets"][user_id]
            if not entry["buckets"]:
                del self._data[entity_id]

        self.schedule_save()

    @callback
    def aggregated(self) -> list[EntityUsage]:
        """Collapse per-user buckets into one set of counts per entity."""
        result: list[EntityUsage] = []
        for entity_id, entry in self._data.items():
            counts: dict[str, int] = {}
            for user_buckets in entry["buckets"].values():
                for day, count in user_buckets.items():
                    counts[day] = counts.get(day, 0) + count
            result.append(
                EntityUsage(entity_id=entity_id, counts=counts, last_used=entry["last_used"])
            )
        return result

    @callback
    def schedule_save(self) -> None:
        """Queue a delayed write. Bursts collapse into a single disk write."""
        self._store.async_delay_save(lambda: {"data": self._data}, SAVE_DELAY)
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
python -m pytest tests/test_store.py -v
```

Expected: PASS, 17 tests.

- [ ] **Step 6: Commit**

```bash
git add custom_components/pareto/store.py tests/test_store.py tests/conftest.py
git commit -m "feat: add usage store with idempotent import writes"
```

---

### Task 4: Event tracker

**Files:**
- Create: `custom_components/pareto/tracker.py`
- Test: `tests/test_tracker.py`

**Interfaces:**
- Consumes: `ParetoStore.record` from Task 3, blacklists from Task 1
- Produces:
  ```python
  def is_blocked_service(domain: str, service: str) -> bool
  async def async_resolve_targets(hass, domain, service, data, context) -> set[str]

  class UsageTracker:
      def __init__(self, hass: HomeAssistant, store: ParetoStore,
                   on_recorded: Callable[[], None]) -> None
      def async_start(self) -> None
      def async_stop(self) -> None
  ```

**Before writing code, verify one API.** `async_extract_referenced_entity_ids` has moved between HA releases. Run this and use whichever import resolves:

```bash
python -c "from homeassistant.helpers.service import async_extract_referenced_entity_ids as f; import inspect; print('helpers.service', inspect.signature(f))"
python -c "from homeassistant.core import ServiceCall; import inspect; print('ServiceCall', inspect.signature(ServiceCall.__init__))"
```

The implementation below handles the direct `entity_id` case itself and only falls back to the helper for area/device/label targets, wrapped in `try/except`. If the helper's signature differs, only `async_resolve_targets` needs adjusting.

- [ ] **Step 1: Write the failing tests**

`tests/test_tracker.py`:

```python
from unittest.mock import Mock

import pytest
from homeassistant.const import EVENT_CALL_SERVICE
from homeassistant.core import Context

from custom_components.pareto.store import ParetoStore
from custom_components.pareto.tracker import UsageTracker, is_blocked_service

USER = "69d919fb68524e7086650439297dd452"


@pytest.fixture
async def wired(hass):
    store = ParetoStore(hass)
    await store.async_load()
    on_recorded = Mock()
    tracker = UsageTracker(hass, store, on_recorded)
    tracker.async_start()
    hass.states.async_set("light.a", "off")
    hass.states.async_set("light.b", "off")
    yield hass, store, on_recorded
    tracker.async_stop()


async def fire(hass, domain, service, data, context):
    hass.bus.async_fire(
        EVENT_CALL_SERVICE,
        {"domain": domain, "service": service, "service_data": data},
        context=context,
    )
    await hass.async_block_till_done()


def counted(store) -> list[str]:
    return [u.entity_id for u in store.aggregated()]


async def test_direct_user_action_is_counted(wired):
    hass, store, _ = wired
    await fire(hass, "light", "turn_on", {"entity_id": "light.a"}, Context(user_id=USER))
    assert counted(store) == ["light.a"]


async def test_automation_without_user_is_not_counted(wired):
    hass, store, _ = wired
    await fire(hass, "light", "turn_on", {"entity_id": "light.a"}, Context())
    assert counted(store) == []


async def test_inherited_context_is_not_counted(wired):
    """A script the user started propagates their user_id to every inner call.
    parent_id is what separates 'I clicked' from 'that was the consequence'."""
    hass, store, _ = wired
    ctx = Context(user_id=USER, parent_id="01KYSENX84PWTVTCNACZBVYXX9")
    await fire(hass, "light", "turn_on", {"entity_id": "light.a"}, ctx)
    assert counted(store) == []


async def test_multiple_entity_ids_each_count(wired):
    hass, store, _ = wired
    await fire(
        hass, "light", "turn_on", {"entity_id": ["light.a", "light.b"]}, Context(user_id=USER)
    )
    assert sorted(counted(store)) == ["light.a", "light.b"]


async def test_call_without_target_is_ignored(wired):
    hass, store, _ = wired
    await fire(hass, "notify", "mobile_app_x", {"message": "hi"}, Context(user_id=USER))
    assert counted(store) == []


async def test_blocked_service_is_not_counted(wired):
    hass, store, _ = wired
    await fire(
        hass, "homeassistant", "update_entity", {"entity_id": "light.a"}, Context(user_id=USER)
    )
    assert counted(store) == []


async def test_reload_service_is_not_counted(wired):
    hass, store, _ = wired
    await fire(hass, "automation", "reload", {"entity_id": "light.a"}, Context(user_id=USER))
    assert counted(store) == []


async def test_callback_fires_when_something_was_recorded(wired):
    hass, store, on_recorded = wired
    await fire(hass, "light", "turn_on", {"entity_id": "light.a"}, Context(user_id=USER))
    assert on_recorded.called


async def test_callback_does_not_fire_for_ignored_events(wired):
    hass, store, on_recorded = wired
    await fire(hass, "light", "turn_on", {"entity_id": "light.a"}, Context())
    assert not on_recorded.called


async def test_stop_unsubscribes(wired):
    hass, store, _ = wired
    tracker = UsageTracker(hass, store, Mock())
    tracker.async_start()
    tracker.async_stop()
    await fire(hass, "light", "turn_on", {"entity_id": "light.b"}, Context(user_id=USER))
    assert "light.b" not in counted(store)


async def test_area_target_counts_every_entity_in_the_area(hass):
    """Targeting an area must resolve to its entities, not be dropped.

    If this fails, async_extract_referenced_entity_ids has a different
    signature in this HA version -- fix async_resolve_targets, not this test.
    """
    from homeassistant.helpers import area_registry as ar
    from homeassistant.helpers import entity_registry as er

    area = ar.async_get(hass).async_create("Wohnzimmer")
    registry = er.async_get(hass)

    store = ParetoStore(hass)
    await store.async_load()
    tracker = UsageTracker(hass, store, Mock())
    tracker.async_start()

    for suffix in ("a", "b"):
        created = registry.async_get_or_create("light", "demo", f"uid_{suffix}")
        registry.async_update_entity(created.entity_id, area_id=area.id)
        hass.states.async_set(created.entity_id, "off")

    await fire(hass, "light", "turn_on", {"area_id": area.id}, Context(user_id=USER))
    tracker.async_stop()

    assert len(counted(store)) == 2


@pytest.mark.parametrize(
    ("domain", "service", "blocked"),
    [
        ("light", "turn_on", False),
        ("homeassistant", "turn_on", False),
        ("homeassistant", "update_entity", True),
        ("logbook", "log", True),
        ("automation", "reload", True),
        ("template", "reload_config", True),
        ("persistent_notification", "create", True),
        ("pareto", "import_history", True),
        ("recorder", "purge", True),
    ],
)
def test_blocklist_rules(domain, service, blocked):
    assert is_blocked_service(domain, service) is blocked
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
python -m pytest tests/test_tracker.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'custom_components.pareto.tracker'`

- [ ] **Step 3: Write `custom_components/pareto/tracker.py`**

```python
"""Records which entities a human operates through Home Assistant."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from homeassistant.const import EVENT_CALL_SERVICE
from homeassistant.core import Context, Event, HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import BLOCKED_DOMAINS, BLOCKED_SERVICES
from .store import ParetoStore

_LOGGER = logging.getLogger(__name__)


def is_blocked_service(domain: str, service: str) -> bool:
    """Return whether this call is plumbing rather than using an entity."""
    if domain in BLOCKED_DOMAINS:
        return True
    if f"{domain}.{service}" in BLOCKED_SERVICES:
        return True
    return service == "reload" or service.startswith("reload_")


async def async_resolve_targets(
    hass: HomeAssistant,
    domain: str,
    service: str,
    data: dict[str, Any],
    context: Context,
) -> set[str]:
    """Resolve a service call's targets to concrete entity ids.

    The plain ``entity_id`` form covers nearly every call from the UI and is
    handled directly. Area, device and label targets go through HA's helper,
    whose import path has moved between releases -- so a failure there degrades
    to "no targets" rather than killing the listener.
    """
    entity_id = data.get("entity_id")
    if isinstance(entity_id, str) and entity_id != "all":
        return {entity_id}
    if isinstance(entity_id, list):
        return {e for e in entity_id if isinstance(e, str)}

    if not any(k in data for k in ("area_id", "device_id", "label_id", "floor_id")):
        return set()

    try:
        from homeassistant.core import ServiceCall
        from homeassistant.helpers.service import async_extract_referenced_entity_ids

        call = ServiceCall(hass, domain, service, dict(data), context)
        selected = await async_extract_referenced_entity_ids(hass, call)
        return set(selected.referenced) | set(selected.indirectly_referenced)
    except Exception:  # noqa: BLE001 - one odd call must not stop tracking
        _LOGGER.debug("Could not resolve targets for %s.%s", domain, service, exc_info=True)
        return set()


class UsageTracker:
    """Listens for service calls and counts the ones a human made directly."""

    def __init__(
        self, hass: HomeAssistant, store: ParetoStore, on_recorded: Callable[[], None]
    ) -> None:
        self._hass = hass
        self._store = store
        self._on_recorded = on_recorded
        self._unsub: Callable[[], None] | None = None

    @callback
    def async_start(self) -> None:
        self._unsub = self._hass.bus.async_listen(EVENT_CALL_SERVICE, self._async_handle)

    @callback
    def async_stop(self) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None

    async def _async_handle(self, event: Event) -> None:
        context = event.context
        # user_id set means a human; parent_id empty means they acted directly
        # rather than this being a script or automation carrying their context.
        if context.user_id is None or context.parent_id is not None:
            return

        domain = event.data.get("domain")
        service = event.data.get("service")
        if not isinstance(domain, str) or not isinstance(service, str):
            return
        if is_blocked_service(domain, service):
            return

        data = event.data.get("service_data") or {}
        if not isinstance(data, dict):
            return

        targets = await async_resolve_targets(self._hass, domain, service, data, context)
        if not targets:
            return

        now = dt_util.now()
        for entity_id in targets:
            self._store.record(entity_id, context.user_id, now)
        self._on_recorded()
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
python -m pytest tests/test_tracker.py -v
```

Expected: PASS, 20 tests.

- [ ] **Step 5: Commit**

```bash
git add custom_components/pareto/tracker.py tests/test_tracker.py
git commit -m "feat: add service call tracker with context filtering"
```

---

### Task 5: Coordinator

**Files:**
- Create: `custom_components/pareto/coordinator.py`
- Test: `tests/test_coordinator.py`

**Interfaces:**
- Consumes: `ParetoStore` (Task 3), `build_ranked_list`/`retention_days` (Tasks 1–2)
- Produces:
  ```python
  class ParetoCoordinator:
      def __init__(self, hass: HomeAssistant, entry: ConfigEntry, store: ParetoStore) -> None
      top: list[RankedEntity]      # property
      recent: list[RankedEntity]   # property
      async def async_start(self) -> None
      async def async_stop(self) -> None
      def async_add_listener(self, update_cb: Callable[[], None]) -> Callable[[], None]
      def async_request_refresh(self) -> None    # debounced, safe from callbacks
      def async_recompute(self) -> None          # immediate
  ```

- [ ] **Step 1: Write the failing tests**

`tests/test_coordinator.py`:

```python
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pareto.const import (
    CONF_EXCLUDE_ENTITIES,
    CONF_PINNED_ENTITIES,
    CONF_TOP_COUNT,
    DOMAIN,
)
from custom_components.pareto.coordinator import ParetoCoordinator
from custom_components.pareto.store import ParetoStore

BERLIN = timezone(timedelta(hours=2))
USER = "69d919fb68524e7086650439297dd452"


async def make(hass, options=None):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options=options or {})
    entry.add_to_hass(hass)
    store = ParetoStore(hass)
    await store.async_load()
    coordinator = ParetoCoordinator(hass, entry, store)
    return coordinator, store


async def test_top_is_empty_before_any_usage(hass):
    coordinator, _ = await make(hass)
    coordinator.async_recompute()
    assert coordinator.top == []


async def test_top_reflects_recorded_usage(hass):
    coordinator, store = await make(hass)
    hass.states.async_set("light.a", "off")
    store.record("light.a", USER, datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN))
    coordinator.async_recompute()
    assert [r.entity_id for r in coordinator.top] == ["light.a"]


async def test_unknown_entities_are_filtered_out(hass):
    """light.a is recorded but never registered in the state machine."""
    coordinator, store = await make(hass)
    store.record("light.a", USER, datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN))
    coordinator.async_recompute()
    assert coordinator.top == []


async def test_top_count_option_limits_the_list(hass):
    coordinator, store = await make(hass, {CONF_TOP_COUNT: 1})
    for name in ("light.a", "light.b"):
        hass.states.async_set(name, "off")
        store.record(name, USER, datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN))
    coordinator.async_recompute()
    assert len(coordinator.top) == 1


async def test_exclusion_option_is_applied(hass):
    coordinator, store = await make(hass, {CONF_EXCLUDE_ENTITIES: ["light.a"]})
    for name in ("light.a", "light.b"):
        hass.states.async_set(name, "off")
        store.record(name, USER, datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN))
    coordinator.async_recompute()
    assert [r.entity_id for r in coordinator.top] == ["light.b"]


async def test_pin_option_is_applied(hass):
    coordinator, store = await make(hass, {CONF_PINNED_ENTITIES: ["switch.pinned"]})
    hass.states.async_set("switch.pinned", "off")
    hass.states.async_set("light.a", "off")
    store.record("light.a", USER, datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN))
    coordinator.async_recompute()
    assert coordinator.top[0].entity_id == "switch.pinned"
    assert coordinator.top[0].pinned is True


async def test_recent_list_is_built_too(hass):
    coordinator, store = await make(hass)
    hass.states.async_set("light.a", "off")
    store.record("light.a", USER, datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN))
    coordinator.async_recompute()
    assert [r.entity_id for r in coordinator.recent] == ["light.a"]


async def test_listeners_are_notified_on_recompute(hass):
    coordinator, _ = await make(hass)
    listener = Mock()
    coordinator.async_add_listener(listener)
    coordinator.async_recompute()
    assert listener.called


async def test_removing_a_listener_stops_notifications(hass):
    coordinator, _ = await make(hass)
    listener = Mock()
    remove = coordinator.async_add_listener(listener)
    remove()
    coordinator.async_recompute()
    assert not listener.called


async def test_a_failing_listener_does_not_break_the_others(hass):
    coordinator, _ = await make(hass)
    good = Mock()
    coordinator.async_add_listener(Mock(side_effect=RuntimeError("boom")))
    coordinator.async_add_listener(good)
    coordinator.async_recompute()
    assert good.called


async def test_request_refresh_eventually_recomputes(hass):
    coordinator, store = await make(hass)
    await coordinator.async_start()
    hass.states.async_set("light.a", "off")
    store.record("light.a", USER, datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN))
    coordinator.async_request_refresh()
    await hass.async_block_till_done()
    assert [r.entity_id for r in coordinator.top] == ["light.a"]
    await coordinator.async_stop()


async def test_stop_is_safe_without_start(hass):
    coordinator, _ = await make(hass)
    await coordinator.async_stop()


async def test_daily_pass_recomputes_without_new_events(hass):
    """Decay alone reorders the list, so this pass is not optional."""
    coordinator, store = await make(hass)
    coordinator.async_recompute()
    hass.states.async_set("light.a", "off")
    store.record("light.a", USER, datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN))
    assert coordinator.top == []

    coordinator._async_daily(None)
    assert [r.entity_id for r in coordinator.top] == ["light.a"]


async def test_daily_pass_prunes_stale_buckets(hass):
    coordinator, store = await make(hass)
    store.record_import("light.old", USER, "2020-01-01", "2020-01-01T12:00:00+01:00")
    coordinator._async_daily(None)
    assert store.aggregated() == []


async def test_start_schedules_the_daily_pass_just_after_midnight(hass):
    coordinator, _ = await make(hass)
    with patch("custom_components.pareto.coordinator.async_track_time_change") as track:
        await coordinator.async_start()
    assert track.called
    assert track.call_args.kwargs == {"hour": 0, "minute": 1, "second": 0}
    await coordinator.async_stop()
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
python -m pytest tests/test_coordinator.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'custom_components.pareto.coordinator'`

- [ ] **Step 3: Write `custom_components/pareto/coordinator.py`**

```python
"""Turns stored counters into two rendered lists, and decides when to redo it."""

from __future__ import annotations

import logging
from collections.abc import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from .const import (
    CONF_EXCLUDE_DOMAINS,
    CONF_EXCLUDE_ENTITIES,
    CONF_HALF_LIFE_DAYS,
    CONF_INCLUDE_DOMAINS,
    CONF_PINNED_ENTITIES,
    CONF_RECENT_COUNT,
    CONF_TOP_COUNT,
    DEFAULT_HALF_LIFE_DAYS,
    DEFAULT_RECENT_COUNT,
    DEFAULT_TOP_COUNT,
    UPDATE_DEBOUNCE,
)
from .ranking import RankedEntity, build_ranked_list, retention_days
from .store import ParetoStore

_LOGGER = logging.getLogger(__name__)


class ParetoCoordinator:
    """Holds the current lists and republishes them when they can have changed."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, store: ParetoStore) -> None:
        self._hass = hass
        self._entry = entry
        self._store = store
        self._listeners: list[Callable[[], None]] = []
        self._unsub_daily: Callable[[], None] | None = None
        self._top: list[RankedEntity] = []
        self._recent: list[RankedEntity] = []
        self._debouncer = Debouncer(
            hass,
            _LOGGER,
            cooldown=UPDATE_DEBOUNCE,
            immediate=True,
            function=self._async_debounced_recompute,
        )

    @property
    def top(self) -> list[RankedEntity]:
        return self._top

    @property
    def recent(self) -> list[RankedEntity]:
        return self._recent

    async def async_start(self) -> None:
        """Compute once, then recompute daily just after local midnight.

        The daily pass is not optional: decay alone reorders the list, so
        without it a quiet week would leave the ranking frozen.
        """
        self.async_recompute()
        self._unsub_daily = async_track_time_change(
            self._hass, self._async_daily, hour=0, minute=1, second=0
        )

    async def async_stop(self) -> None:
        if self._unsub_daily is not None:
            self._unsub_daily()
            self._unsub_daily = None
        await self._debouncer.async_shutdown()

    @callback
    def async_add_listener(self, update_cb: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(update_cb)

        @callback
        def remove() -> None:
            if update_cb in self._listeners:
                self._listeners.remove(update_cb)

        return remove

    @callback
    def async_request_refresh(self) -> None:
        """Ask for a recompute, collapsing bursts into one."""
        self._hass.async_create_task(self._debouncer.async_call())

    async def _async_debounced_recompute(self) -> None:
        self.async_recompute()

    @callback
    def _async_daily(self, _now) -> None:
        self._store.prune(dt_util.now().date(), retention_days(self._half_life))
        self.async_recompute()

    @property
    def _half_life(self) -> float:
        return float(self._entry.options.get(CONF_HALF_LIFE_DAYS, DEFAULT_HALF_LIFE_DAYS))

    @callback
    def async_recompute(self) -> None:
        """Rebuild both lists from the store and notify listeners."""
        options = self._entry.options
        usages = self._store.aggregated()
        today = dt_util.now().date()
        shared = {
            "today": today,
            "half_life_days": self._half_life,
            "include_domains": frozenset(options.get(CONF_INCLUDE_DOMAINS, [])),
            "exclude_domains": frozenset(options.get(CONF_EXCLUDE_DOMAINS, [])),
            "exclude_entities": frozenset(options.get(CONF_EXCLUDE_ENTITIES, [])),
            "pinned": tuple(options.get(CONF_PINNED_ENTITIES, [])),
            "exists": lambda entity_id: self._hass.states.get(entity_id) is not None,
        }

        self._top = build_ranked_list(
            usages,
            mode="top",
            limit=int(options.get(CONF_TOP_COUNT, DEFAULT_TOP_COUNT)),
            **shared,
        )
        self._recent = build_ranked_list(
            usages,
            mode="recent",
            limit=int(options.get(CONF_RECENT_COUNT, DEFAULT_RECENT_COUNT)),
            **shared,
        )

        for listener in list(self._listeners):
            try:
                listener()
            except Exception:  # noqa: BLE001 - one bad sensor must not block the rest
                _LOGGER.exception("Pareto listener raised during update")
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
python -m pytest tests/test_coordinator.py -v
```

Expected: PASS, 15 tests.

- [ ] **Step 5: Commit**

```bash
git add custom_components/pareto/coordinator.py tests/test_coordinator.py
git commit -m "feat: add coordinator with debounced and daily recompute"
```

---

### Task 6: Config flow, manifest, and setup wiring

**Files:**
- Create: `custom_components/pareto/manifest.json`
- Create: `custom_components/pareto/config_flow.py`
- Create: `custom_components/pareto/strings.json`
- Create: `custom_components/pareto/translations/en.json`
- Modify: `custom_components/pareto/__init__.py`
- Test: `tests/test_config_flow.py`
- Test: `tests/test_init.py`

**Interfaces:**
- Consumes: `ParetoStore` (Task 3), `UsageTracker` (Task 4), `ParetoCoordinator` (Task 5)
- Produces:
  ```python
  # __init__.py
  PLATFORMS: list[Platform] = [Platform.SENSOR]
  async def async_setup_entry(hass, entry) -> bool
  async def async_unload_entry(hass, entry) -> bool
  async def async_reload_entry(hass, entry) -> None

  @dataclass
  class ParetoRuntime:
      store: ParetoStore
      coordinator: ParetoCoordinator
      tracker: UsageTracker
  # stored at hass.data[DOMAIN][entry.entry_id]
  ```

- [ ] **Step 1: Create `custom_components/pareto/manifest.json`**

Use these values verbatim — `dbackhove` is the real GitHub account.

```json
{
  "domain": "pareto",
  "name": "Pareto",
  "codeowners": ["@dbackhove"],
  "config_flow": true,
  "after_dependencies": ["recorder", "logbook"],
  "documentation": "https://github.com/dbackhove/ha-pareto",
  "integration_type": "service",
  "iot_class": "calculated",
  "issue_tracker": "https://github.com/dbackhove/ha-pareto/issues",
  "requirements": [],
  "version": "0.1.0"
}
```

`after_dependencies` rather than `dependencies`: Pareto loads after the recorder when one exists, but still works without it — only the backfill is unavailable.

- [ ] **Step 2: Write the failing tests**

`tests/test_config_flow.py`:

```python
import pytest
from homeassistant import config_entries, data_entry_flow
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pareto.const import (
    CONF_HALF_LIFE_DAYS,
    CONF_PINNED_ENTITIES,
    CONF_RECENT_COUNT,
    CONF_TOP_COUNT,
    DOMAIN,
)


async def test_user_flow_creates_the_entry(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Pareto"


async def test_only_one_instance_is_allowed(hass):
    MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_options_flow_stores_values(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_TOP_COUNT: 7,
            CONF_RECENT_COUNT: 3,
            CONF_HALF_LIFE_DAYS: 21,
            CONF_PINNED_ENTITIES: [],
        },
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_TOP_COUNT] == 7
    assert result["data"][CONF_HALF_LIFE_DAYS] == 21
```

`tests/test_init.py`:

```python
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import Context
from homeassistant.const import EVENT_CALL_SERVICE
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pareto.const import DOMAIN

USER = "69d919fb68524e7086650439297dd452"


async def test_setup_and_unload(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert entry.entry_id in hass.data[DOMAIN]

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert entry.entry_id not in hass.data[DOMAIN]


async def test_tracking_is_live_after_setup(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set("light.a", "off")
    hass.bus.async_fire(
        EVENT_CALL_SERVICE,
        {"domain": "light", "service": "turn_on", "service_data": {"entity_id": "light.a"}},
        context=Context(user_id=USER),
    )
    await hass.async_block_till_done()

    runtime = hass.data[DOMAIN][entry.entry_id]
    assert [u.entity_id for u in runtime.store.aggregated()] == ["light.a"]


async def test_tracking_stops_after_unload(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    runtime = hass.data[DOMAIN][entry.entry_id]

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set("light.b", "off")
    hass.bus.async_fire(
        EVENT_CALL_SERVICE,
        {"domain": "light", "service": "turn_on", "service_data": {"entity_id": "light.b"}},
        context=Context(user_id=USER),
    )
    await hass.async_block_till_done()
    assert [u.entity_id for u in runtime.store.aggregated()] == []
```

- [ ] **Step 3: Run the tests to verify they fail**

```bash
python -m pytest tests/test_config_flow.py tests/test_init.py -v
```

Expected: FAIL — the integration cannot be set up yet.

- [ ] **Step 4: Write `custom_components/pareto/config_flow.py`**

```python
"""Config and options flows for Pareto."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_EXCLUDE_DOMAINS,
    CONF_EXCLUDE_ENTITIES,
    CONF_HALF_LIFE_DAYS,
    CONF_INCLUDE_DOMAINS,
    CONF_PINNED_ENTITIES,
    CONF_RECENT_COUNT,
    CONF_TOP_COUNT,
    DEFAULT_HALF_LIFE_DAYS,
    DEFAULT_RECENT_COUNT,
    DEFAULT_TOP_COUNT,
    DOMAIN,
)


def _count_selector(minimum: int, maximum: int) -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(min=minimum, max=maximum, step=1, mode=NumberSelectorMode.BOX)
    )


class ParetoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Single-step setup. Everything configurable lives in the options flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Pareto", data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return ParetoOptionsFlow()


class ParetoOptionsFlow(OptionsFlow):
    """Everything the user can tune, all on one page."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        options = self.config_entry.options
        domains = sorted({state.entity_id.split(".", 1)[0] for state in self.hass.states.async_all()})
        domain_selector = SelectSelector(
            SelectSelectorConfig(options=domains, multiple=True, mode=SelectSelectorMode.DROPDOWN)
        )
        entity_selector = EntitySelector(EntitySelectorConfig(multiple=True))

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_TOP_COUNT, default=options.get(CONF_TOP_COUNT, DEFAULT_TOP_COUNT)
                ): _count_selector(1, 50),
                vol.Optional(
                    CONF_RECENT_COUNT,
                    default=options.get(CONF_RECENT_COUNT, DEFAULT_RECENT_COUNT),
                ): _count_selector(1, 50),
                vol.Optional(
                    CONF_HALF_LIFE_DAYS,
                    default=options.get(CONF_HALF_LIFE_DAYS, DEFAULT_HALF_LIFE_DAYS),
                ): _count_selector(1, 90),
                vol.Optional(
                    CONF_INCLUDE_DOMAINS, default=options.get(CONF_INCLUDE_DOMAINS, [])
                ): domain_selector,
                vol.Optional(
                    CONF_EXCLUDE_DOMAINS, default=options.get(CONF_EXCLUDE_DOMAINS, [])
                ): domain_selector,
                vol.Optional(
                    CONF_EXCLUDE_ENTITIES, default=options.get(CONF_EXCLUDE_ENTITIES, [])
                ): entity_selector,
                vol.Optional(
                    CONF_PINNED_ENTITIES, default=options.get(CONF_PINNED_ENTITIES, [])
                ): entity_selector,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
```

- [ ] **Step 5: Write `custom_components/pareto/strings.json`**

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Pareto",
        "description": "Pareto learns which entities you actually operate and publishes the most used and most recent ones as sensors. There is nothing to configure here — everything is available afterwards under Configure."
      }
    },
    "abort": {
      "single_instance_allowed": "Pareto is already set up. Only one instance is needed."
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "Pareto options",
        "data": {
          "top_count": "Number of most used entities",
          "recent_count": "Number of recently used entities",
          "half_life_days": "Half-life in days",
          "include_domains": "Only rank these domains",
          "exclude_domains": "Never show these domains",
          "exclude_entities": "Never show these entities",
          "pinned_entities": "Always show these entities"
        },
        "data_description": {
          "half_life_days": "How fast past usage loses weight. At 14 days, something used a fortnight ago counts half as much as today.",
          "include_domains": "Leave empty to allow every domain.",
          "pinned_entities": "Shown first, in this order, even if never used. Pinned entities count towards the numbers above."
        }
      }
    }
  },
  "services": {
    "import_history": {
      "name": "Import history",
      "description": "Reads past usage from the logbook. Only fills days that hold no data yet, so running it twice is safe.",
      "fields": {
        "days": {
          "name": "Days",
          "description": "How far back to read. Limited by your recorder retention, typically 10 days."
        }
      }
    }
  }
}
```

Copy this file verbatim to `custom_components/pareto/translations/en.json`.

- [ ] **Step 6: Write `custom_components/pareto/__init__.py`**

```python
"""The Pareto integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError

from .const import DOMAIN
from .coordinator import ParetoCoordinator
from .store import ParetoStore, ParetoStoreError
from .tracker import UsageTracker

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


@dataclass
class ParetoRuntime:
    """Everything one config entry owns at runtime."""

    store: ParetoStore
    coordinator: ParetoCoordinator
    tracker: UsageTracker


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pareto from a config entry."""
    store = ParetoStore(hass)
    try:
        await store.async_load()
    except ParetoStoreError as err:
        # Refuse to run rather than overwrite data from a newer version.
        raise ConfigEntryError(str(err)) from err

    coordinator = ParetoCoordinator(hass, entry, store)
    tracker = UsageTracker(hass, store, coordinator.async_request_refresh)

    await coordinator.async_start()
    tracker.async_start()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = ParetoRuntime(
        store=store, coordinator=coordinator, tracker=tracker
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Tear down a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unloaded:
        return False

    runtime: ParetoRuntime = hass.data[DOMAIN].pop(entry.entry_id)
    runtime.tracker.async_stop()
    await runtime.coordinator.async_stop()
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload after the options changed. Usage data is untouched."""
    await hass.config_entries.async_reload(entry.entry_id)
```

- [ ] **Step 7: Run the tests to verify they pass**

```bash
python -m pytest tests/ -v
```

Expected: PASS. `test_config_flow.py` and `test_init.py` add 6 tests.

- [ ] **Step 8: Commit**

```bash
git add custom_components/pareto tests/test_config_flow.py tests/test_init.py
git commit -m "feat: add config flow, manifest and entry setup"
```

---

### Task 7: Sensor entities

**Files:**
- Create: `custom_components/pareto/sensor.py`
- Test: `tests/test_sensor.py`

**Interfaces:**
- Consumes: `ParetoRuntime`, `ParetoCoordinator` (Tasks 5–6)
- Produces: entities `sensor.pareto_top` and `sensor.pareto_recent`, each with
  `state` = list length and attribute `entities` = list of dicts holding
  `entity_id`, `count`, `last_used`, `pinned`, plus `score` on the top sensor only.

- [ ] **Step 1: Write the failing tests**

`tests/test_sensor.py`:

```python
from datetime import datetime, timedelta, timezone

from homeassistant.core import Context
from homeassistant.const import EVENT_CALL_SERVICE
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pareto.const import DOMAIN

BERLIN = timezone(timedelta(hours=2))
USER = "69d919fb68524e7086650439297dd452"


async def setup_pareto(hass, options=None):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options=options or {}, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_both_sensors_are_created(hass):
    await setup_pareto(hass)
    assert hass.states.get("sensor.pareto_top") is not None
    assert hass.states.get("sensor.pareto_recent") is not None


async def test_sensors_start_at_zero(hass):
    await setup_pareto(hass)
    assert hass.states.get("sensor.pareto_top").state == "0"
    assert hass.states.get("sensor.pareto_top").attributes["entities"] == []


async def test_state_is_the_list_length(hass):
    entry = await setup_pareto(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    hass.states.async_set("light.a", "off")
    runtime.store.record("light.a", USER, datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN))
    runtime.coordinator.async_recompute()
    await hass.async_block_till_done()
    assert hass.states.get("sensor.pareto_top").state == "1"


async def test_top_attribute_carries_the_expected_keys(hass):
    entry = await setup_pareto(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    hass.states.async_set("light.a", "off")
    runtime.store.record("light.a", USER, datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN))
    runtime.coordinator.async_recompute()
    await hass.async_block_till_done()

    first = hass.states.get("sensor.pareto_top").attributes["entities"][0]
    assert first["entity_id"] == "light.a"
    assert first["count"] == 1
    assert first["pinned"] is False
    assert "score" in first
    assert "last_used" in first


async def test_recent_attribute_omits_score(hass):
    entry = await setup_pareto(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]
    hass.states.async_set("light.a", "off")
    runtime.store.record("light.a", USER, datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN))
    runtime.coordinator.async_recompute()
    await hass.async_block_till_done()

    first = hass.states.get("sensor.pareto_recent").attributes["entities"][0]
    assert "score" not in first
    assert first["entity_id"] == "light.a"


async def test_sensor_updates_from_a_real_service_call(hass):
    """End to end: firing a service call moves the sensor."""
    await setup_pareto(hass)
    hass.states.async_set("light.a", "off")
    hass.bus.async_fire(
        EVENT_CALL_SERVICE,
        {"domain": "light", "service": "turn_on", "service_data": {"entity_id": "light.a"}},
        context=Context(user_id=USER),
    )
    await hass.async_block_till_done()
    assert hass.states.get("sensor.pareto_top").state == "1"
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
python -m pytest tests/test_sensor.py -v
```

Expected: FAIL — `sensor.pareto_top` is None.

- [ ] **Step 3: Write `custom_components/pareto/sensor.py`**

```python
"""Sensor entities publishing the Pareto lists."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ParetoCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: ParetoCoordinator = hass.data[DOMAIN][entry.entry_id].coordinator
    async_add_entities(
        [
            ParetoListSensor(coordinator, entry, "top", "Top"),
            ParetoListSensor(coordinator, entry, "recent", "Recent"),
        ]
    )


class ParetoListSensor(SensorEntity):
    """One rendered list.

    HA caps state values at 255 characters, so the list itself cannot live
    there. The state carries the length and the payload sits in an attribute.
    """

    _attr_has_entity_name = False
    _attr_should_poll = False
    _attr_icon = "mdi:sort-variant"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self, coordinator: ParetoCoordinator, entry: ConfigEntry, mode: str, label: str
    ) -> None:
        self._coordinator = coordinator
        self._mode = mode
        self._attr_name = f"Pareto {label}"
        self._attr_unique_id = f"{entry.entry_id}_{mode}"

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._coordinator.async_add_listener(self._handle_update))
        self._handle_update()

    @callback
    def _handle_update(self) -> None:
        if self.hass is not None:
            self.async_write_ha_state()

    @property
    def _entries(self) -> list[dict[str, Any]]:
        ranked = self._coordinator.top if self._mode == "top" else self._coordinator.recent
        rows = [asdict(item) for item in ranked]
        if self._mode == "recent":
            for row in rows:
                row.pop("score", None)
        return rows

    @property
    def native_value(self) -> int:
        return len(self._entries)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"entities": self._entries}
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
python -m pytest tests/ -v
```

Expected: PASS, 6 new tests.

- [ ] **Step 5: Commit**

```bash
git add custom_components/pareto/sensor.py tests/test_sensor.py
git commit -m "feat: add top and recent sensor entities"
```

---

### Task 8: Logbook backfill

**Files:**
- Create: `custom_components/pareto/importer.py`
- Create: `custom_components/pareto/services.yaml`
- Modify: `custom_components/pareto/__init__.py`
- Test: `tests/test_importer.py`

**Interfaces:**
- Consumes: `ParetoStore.record_import` (Task 3), `is_blocked_service` (Task 4)
- Produces:
  ```python
  async def async_import_history(hass, store: ParetoStore, days: int) -> int
  async def async_fetch_logbook_day(hass, day_start: datetime, day_end: datetime) -> list[dict]
  ```
  `async_import_history` returns how many usages it wrote. `async_fetch_logbook_day` is
  a separate seam so tests can patch it without a real recorder.

**Verify the logbook API before writing.** Its internal path has changed across releases:

```bash
python -c "from homeassistant.components.logbook.processor import EventProcessor; print('ok')"
```

If that import fails, find the current entry point with
`python -c "import homeassistant.components.logbook as l; print(l.__file__)"` and read the module.
Only `async_fetch_logbook_day` needs to change — everything else is tested against the seam.

- [ ] **Step 1: Write the failing tests**

`tests/test_importer.py`:

```python
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.pareto.importer import async_import_history
from custom_components.pareto.store import ParetoStore

BERLIN = timezone(timedelta(hours=2))
USER = "69d919fb68524e7086650439297dd452"
PATCH_TARGET = "custom_components.pareto.importer.async_fetch_logbook_day"


def entry(entity_id, when, user_id=USER, domain="light", service="turn_on"):
    return {
        "entity_id": entity_id,
        "when": when,
        "context_user_id": user_id,
        "context_event_type": "call_service",
        "context_domain": domain,
        "context_service": service,
    }


@pytest.fixture
async def store(hass):
    s = ParetoStore(hass)
    await s.async_load()
    return s


async def test_imports_a_user_call(hass, store):
    rows = [entry("light.a", "2026-07-28T12:00:00+02:00")]
    with patch(PATCH_TARGET, AsyncMock(side_effect=[rows] + [[]] * 9)):
        written = await async_import_history(hass, store, days=10)
    assert written == 1
    assert store.aggregated()[0].counts == {"2026-07-28": 1}


async def test_skips_entries_without_a_user(hass, store):
    rows = [entry("light.a", "2026-07-28T12:00:00+02:00", user_id=None)]
    with patch(PATCH_TARGET, AsyncMock(side_effect=[rows] + [[]] * 9)):
        written = await async_import_history(hass, store, days=10)
    assert written == 0
    assert store.aggregated() == []


async def test_skips_non_service_call_entries(hass, store):
    rows = [entry("light.a", "2026-07-28T12:00:00+02:00")]
    rows[0]["context_event_type"] = "homekit_state_change"
    with patch(PATCH_TARGET, AsyncMock(side_effect=[rows] + [[]] * 9)):
        written = await async_import_history(hass, store, days=10)
    assert written == 0


async def test_skips_blocked_services(hass, store):
    rows = [
        entry("light.a", "2026-07-28T12:00:00+02:00", domain="homeassistant", service="update_entity")
    ]
    with patch(PATCH_TARGET, AsyncMock(side_effect=[rows] + [[]] * 9)):
        written = await async_import_history(hass, store, days=10)
    assert written == 0


async def test_running_twice_changes_nothing(hass, store):
    rows = [entry("light.a", "2026-07-28T12:00:00+02:00")]
    with patch(PATCH_TARGET, AsyncMock(side_effect=[rows] + [[]] * 9)):
        await async_import_history(hass, store, days=10)
    with patch(PATCH_TARGET, AsyncMock(side_effect=[rows] + [[]] * 9)):
        second = await async_import_history(hass, store, days=10)
    assert second == 0
    assert store.aggregated()[0].counts == {"2026-07-28": 1}


async def test_live_data_survives_an_import(hass, store):
    store.record("light.a", USER, datetime(2026, 7, 28, 20, 0, tzinfo=BERLIN))
    store.record("light.a", USER, datetime(2026, 7, 28, 21, 0, tzinfo=BERLIN))
    rows = [entry("light.a", "2026-07-28T12:00:00+02:00")]
    with patch(PATCH_TARGET, AsyncMock(side_effect=[rows] + [[]] * 9)):
        written = await async_import_history(hass, store, days=10)
    assert written == 0
    assert store.aggregated()[0].counts == {"2026-07-28": 2}


async def test_a_failing_day_does_not_abort_the_run(hass, store):
    rows = [entry("light.a", "2026-07-28T12:00:00+02:00")]
    side_effect = [RuntimeError("recorder busy"), rows] + [[]] * 8
    with patch(PATCH_TARGET, AsyncMock(side_effect=side_effect)):
        written = await async_import_history(hass, store, days=10)
    assert written == 1


async def test_malformed_rows_are_skipped(hass, store):
    rows = [{"nonsense": True}, entry("light.a", "2026-07-28T12:00:00+02:00")]
    with patch(PATCH_TARGET, AsyncMock(side_effect=[rows] + [[]] * 9)):
        written = await async_import_history(hass, store, days=10)
    assert written == 1
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
python -m pytest tests/test_importer.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'custom_components.pareto.importer'`

- [ ] **Step 3: Write `custom_components/pareto/importer.py`**

```python
"""One-off backfill of past usage from the logbook."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .tracker import is_blocked_service

_LOGGER = logging.getLogger(__name__)


async def async_fetch_logbook_day(
    hass: HomeAssistant, day_start: datetime, day_end: datetime
) -> list[dict[str, Any]]:
    """Return raw logbook rows for one day.

    Isolated on purpose: this is the only part tied to recorder internals, and
    reading day by day keeps memory bounded and behaviour predictable. During
    research the REST logbook returned different results for the same entity
    depending on window size, so large single queries are avoided.
    """
    from homeassistant.components.logbook.processor import EventProcessor

    processor = EventProcessor(hass, [], entity_ids=None, device_ids=None, context_id=None)
    return await hass.async_add_executor_job(
        processor.get_events, day_start, day_end
    )


def _extract(row: dict[str, Any]) -> tuple[str, str, str, str] | None:
    """Return (entity_id, user_id, day, when_iso) if this row is a user action."""
    if row.get("context_event_type") != "call_service":
        return None

    user_id = row.get("context_user_id")
    entity_id = row.get("entity_id")
    when = row.get("when")
    if not isinstance(user_id, str) or not isinstance(entity_id, str) or not when:
        return None

    domain = row.get("context_domain")
    service = row.get("context_service")
    if isinstance(domain, str) and isinstance(service, str) and is_blocked_service(domain, service):
        return None

    try:
        moment = dt_util.parse_datetime(str(when))
    except (TypeError, ValueError):
        return None
    if moment is None:
        return None

    local = dt_util.as_local(moment)
    return entity_id, user_id, local.date().isoformat(), local.isoformat()


async def async_import_history(hass: HomeAssistant, store, days: int) -> int:
    """Import up to ``days`` of past usage. Returns how many rows were written.

    Only writes into day buckets that do not exist yet, which makes the whole
    thing idempotent, unable to clobber live data, and resumable after a
    failure. A day that fails is logged and skipped, never fatal.
    """
    written = 0
    today = dt_util.now().date()

    for offset in range(days):
        day = today - timedelta(days=offset)
        day_start = dt_util.start_of_local_day(day)
        day_end = day_start + timedelta(days=1)

        try:
            rows = await async_fetch_logbook_day(hass, day_start, day_end)
        except Exception:  # noqa: BLE001 - one bad day must not lose the rest
            _LOGGER.warning("Pareto could not read the logbook for %s", day, exc_info=True)
            continue

        for row in rows or []:
            if not isinstance(row, dict):
                continue
            parsed = _extract(row)
            if parsed is None:
                continue
            entity_id, user_id, bucket_day, when_iso = parsed
            if store.record_import(entity_id, user_id, bucket_day, when_iso):
                written += 1

    _LOGGER.info("Pareto imported %s past usages", written)
    return written
```

- [ ] **Step 4: Run the importer tests to verify they pass**

```bash
python -m pytest tests/test_importer.py -v
```

Expected: PASS, 8 tests.

- [ ] **Step 5: Create `custom_components/pareto/services.yaml`**

```yaml
import_history:
  fields:
    days:
      required: false
      default: 10
      selector:
        number:
          min: 1
          max: 90
          step: 1
          mode: box
```

- [ ] **Step 6: Wire the import into `custom_components/pareto/__init__.py`**

Add these imports at the top:

```python
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import ATTR_DAYS, DEFAULT_IMPORT_DAYS, DOMAIN, SERVICE_IMPORT_HISTORY
from .importer import async_import_history
```

Add this module-level schema after `PLATFORMS`:

```python
IMPORT_SCHEMA = vol.Schema(
    {vol.Optional(ATTR_DAYS, default=DEFAULT_IMPORT_DAYS): vol.All(int, vol.Range(min=1, max=90))}
)
```

Then insert this block in `async_setup_entry`, immediately before the
`async_forward_entry_setups` call:

```python
    async def _handle_import(call: ServiceCall) -> None:
        written = await async_import_history(hass, store, call.data[ATTR_DAYS])
        coordinator.async_recompute()
        _LOGGER.info("Pareto history import finished, %s usages added", written)

    hass.services.async_register(
        DOMAIN, SERVICE_IMPORT_HISTORY, _handle_import, schema=IMPORT_SCHEMA
    )

    async def _initial_import(_event=None) -> None:
        """Backfill once at setup, in the background and never fatally."""
        try:
            written = await async_import_history(hass, store, DEFAULT_IMPORT_DAYS)
        except Exception:  # noqa: BLE001 - setup must survive a failed import
            _LOGGER.warning("Pareto history import failed", exc_info=True)
            return
        coordinator.async_recompute()
        if written:
            persistent_notification.async_create(
                hass,
                f"Pareto imported {written} past usages from the logbook.",
                title="Pareto",
                notification_id="pareto_import",
            )

    entry.async_create_background_task(hass, _initial_import(), "pareto_initial_import")
```

Add `from homeassistant.components import persistent_notification` to the imports.

Finally, deregister the service in `async_unload_entry`, right after the
`hass.data[DOMAIN].pop(...)` line:

```python
    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, SERVICE_IMPORT_HISTORY)
```

- [ ] **Step 7: Run the whole suite**

```bash
python -m pytest tests/ -v
```

Expected: PASS. Setup tests still pass because the background import finds no
recorder in the test harness and logs a warning rather than failing.

- [ ] **Step 8: Commit**

```bash
git add custom_components/pareto tests/test_importer.py
git commit -m "feat: add logbook backfill with idempotent writes"
```

---

### Task 9: Distribution files and German translation

**Files:**
- Create: `hacs.json`
- Create: `custom_components/pareto/translations/de.json`
- Create: `README.md`
- Create: `.github/workflows/validate.yml`
- Test: `tests/test_translations.py`

**Interfaces:**
- Consumes: `strings.json` from Task 6
- Produces: nothing consumed by other tasks

- [ ] **Step 1: Write the failing test**

`tests/test_translations.py`:

```python
"""A translation file that drifts from strings.json shows raw keys in the UI."""

import json
import pathlib

BASE = pathlib.Path("custom_components/pareto")


def load(name: str) -> dict:
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def keys(node, prefix=""):
    found = set()
    for key, value in node.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            found |= keys(value, path)
        else:
            found.add(path)
    return found


def test_english_translation_matches_strings():
    assert keys(load("strings.json")) == keys(load("translations/en.json"))


def test_german_translation_matches_strings():
    assert keys(load("strings.json")) == keys(load("translations/de.json"))


def test_manifest_points_at_the_real_repository():
    manifest = load("manifest.json")
    assert manifest["codeowners"] == ["@dbackhove"]
    assert manifest["documentation"] == "https://github.com/dbackhove/ha-pareto"
    assert manifest["issue_tracker"] == "https://github.com/dbackhove/ha-pareto/issues"
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
python -m pytest tests/test_translations.py -v
```

Expected: FAIL — `de.json` does not exist, and the manifest still holds the placeholder.

- [ ] **Step 3: Create `custom_components/pareto/translations/de.json`**

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Pareto",
        "description": "Pareto lernt, welche Entities du tatsächlich bedienst, und veröffentlicht die meistgenutzten und die zuletzt genutzten als Sensoren. Hier gibt es nichts einzustellen — alles Weitere findest du danach unter Konfigurieren."
      }
    },
    "abort": {
      "single_instance_allowed": "Pareto ist bereits eingerichtet. Eine Instanz genügt."
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "Pareto-Optionen",
        "data": {
          "top_count": "Anzahl der meistgenutzten Entities",
          "recent_count": "Anzahl der zuletzt genutzten Entities",
          "half_life_days": "Halbwertszeit in Tagen",
          "include_domains": "Nur diese Domains ranken",
          "exclude_domains": "Diese Domains nie anzeigen",
          "exclude_entities": "Diese Entities nie anzeigen",
          "pinned_entities": "Diese Entities immer anzeigen"
        },
        "data_description": {
          "half_life_days": "Wie schnell vergangene Nutzung an Gewicht verliert. Bei 14 Tagen zählt eine Bedienung von vor zwei Wochen halb so viel wie eine von heute.",
          "include_domains": "Leer lassen, um alle Domains zuzulassen.",
          "pinned_entities": "Werden zuerst angezeigt, in dieser Reihenfolge, auch ohne jede Nutzung. Angeheftete Entities zählen gegen die Anzahlen oben."
        }
      }
    }
  },
  "services": {
    "import_history": {
      "name": "Historie importieren",
      "description": "Liest vergangene Nutzung aus dem Logbuch. Füllt nur Tage, zu denen noch keine Daten vorliegen — ein zweiter Lauf ist also gefahrlos.",
      "fields": {
        "days": {
          "name": "Tage",
          "description": "Wie weit zurück gelesen wird. Begrenzt durch die Aufbewahrungsdauer deines Recorders, typischerweise 10 Tage."
        }
      }
    }
  }
}
```

- [ ] **Step 4: Confirm the manifest points at the real repository**

`manifest.json` was written in Task 6 with the real account (`dbackhove`). Verify
`codeowners`, `documentation` and `issue_tracker` match what the test above expects;
no edit should be needed.

- [ ] **Step 5: Create `hacs.json`**

```json
{
  "name": "Pareto",
  "content_in_root": false,
  "render_readme": true,
  "homeassistant": "2026.7.0"
}
```

- [ ] **Step 6: Create `README.md`**

````markdown
# Pareto for Home Assistant

Home Assistant knows everything about your entities except the one thing a
dashboard needs: which of them you actually touch. Pareto watches the service
calls you make yourself and publishes two lists — the ones you use most, and the
ones you used last.

## What counts as usage

A service call counts when Home Assistant recorded a user behind it **and** it
was a direct action rather than a consequence of one. In practice that means
clicking in the web UI, the companion app, or a voice assistant — not
automations, and not the ten follow-on calls a script makes on your behalf.

Not counted, deliberately: HomeKit commands, physical switches, and other
integrations acting on their own. Home Assistant does not attribute those to a
user. Making this configurable is on the roadmap.

## Installation

1. Add this repository to HACS as a custom repository (category: Integration).
2. Install **Pareto** and restart Home Assistant.
3. Add the integration under **Settings → Devices & Services**.

On setup, Pareto imports whatever usage your recorder still holds — normally
about ten days — so the lists are useful immediately rather than after a
fortnight of learning.

## Entities

| Entity | State | Attribute `entities` |
|---|---|---|
| `sensor.pareto_top` | Number of entries | Ranked by decayed usage |
| `sensor.pareto_recent` | Number of entries | Ranked by last use |

Each entry holds `entity_id`, `count`, `last_used`, `pinned`, and — on the top
sensor — `score`.

## Options

| Option | Default | Meaning |
|---|---|---|
| Top count | 10 | Length of the most-used list |
| Recent count | 5 | Length of the recently-used list |
| Half-life | 14 days | How fast past usage loses weight |
| Only these domains | empty | Whitelist; empty allows all |
| Never these domains | empty | Domain blocklist |
| Never these entities | empty | Entity blocklist |
| Always these entities | empty | Pins, shown first, counting towards the numbers above |

## Showing the list

A card is planned. Until then, a Markdown card is enough to see the ranking:

```yaml
type: markdown
content: |
  {% for e in state_attr('sensor.pareto_top','entities') %}
  {{ loop.index }}. {{ state_attr(e.entity_id,'friendly_name') or e.entity_id }}
     — {{ e.count }}x (score {{ e.score }})
  {% endfor %}
```

## Service

`pareto.import_history` re-reads the logbook. It only fills days that hold no
data yet, so running it twice changes nothing and it can never overwrite what
was recorded live.

## How the score works

Every use is bucketed by local day. The score sums those buckets, weighting each
by `0.5 ^ (age_in_days / half_life)`. With the default half-life, something used
twice yesterday outranks something used ten times a month ago. The lists are also
recomputed once a day, because decay alone changes the order — otherwise a quiet
week would leave the ranking frozen.
````

- [ ] **Step 7: Create `.github/workflows/validate.yml`**

```yaml
name: Validate

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: pip install -r requirements-test.txt
      - run: python -m pytest tests/ -v
      - run: python -m ruff check custom_components tests

  hassfest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: home-assistant/actions/hassfest@master

  hacs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hacs/action@main
        with:
          category: integration
```

- [ ] **Step 8: Run the full suite and the linter**

```bash
python -m pytest tests/ -v
python -m ruff check custom_components tests
```

Expected: all tests pass, ruff reports no errors.

- [ ] **Step 9: Commit**

```bash
git add hacs.json README.md .github custom_components/pareto/translations tests/test_translations.py custom_components/pareto/manifest.json
git commit -m "docs: add README, HACS metadata, CI and German translation"
```

---

## Manual verification against the real installation

Automated tests cannot prove the ranking is *useful*. After Task 9, install the
integration in the real Home Assistant and check the spec's success criteria:

1. Both sensors hold plausible lists right after setup, without waiting — the
   backfill worked.
2. Run a script that switches several lights. Exactly **one** usage is recorded,
   not one per light. This is the `parent_id` filter doing its job and is the
   single most important behaviour to confirm by hand.
3. The top list is mostly entities you recognise as things you actually operate.
4. Call `pareto.import_history` a second time. No number changes.
5. Check `.storage/pareto_usage` — buckets are keyed by local date, and an
   evening action after 23:00 sits on that same day.

If point 3 disappoints, that is the signal to revisit the ranking before
investing in the Phase 2 card. That is exactly why the card was deferred.
