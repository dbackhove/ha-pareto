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
