"""Padding a personal list out of the global one.

Pure logic, no Home Assistant: the same reason ranking.py itself has none.
"""

from custom_components.pareto.ranking import RankedEntity, merge_personal_and_global


def entry(entity_id, score=1.0, pinned=False):
    return RankedEntity(entity_id=entity_id, score=score, count=1, last_used=None, pinned=pinned)


def ids(merged):
    return [e.entity_id for e, _ in merged]


def flags(merged):
    return [personal for _, personal in merged]


def test_own_entries_come_first_and_keep_their_order():
    personal = [entry("light.a"), entry("light.b")]
    fallback = [entry("light.z"), entry("light.a")]

    merged = merge_personal_and_global(personal, fallback, limit=10)

    assert ids(merged) == ["light.a", "light.b", "light.z"]
    assert flags(merged) == [True, True, False]


def test_padding_skips_what_is_already_listed():
    merged = merge_personal_and_global([entry("light.a")], [entry("light.a")], limit=10)
    assert ids(merged) == ["light.a"]


def test_an_empty_personal_list_becomes_the_global_one():
    """A fresh install, or somebody who only ever uses wall switches."""
    fallback = [entry("light.a"), entry("light.b")]

    merged = merge_personal_and_global([], fallback, limit=10)

    assert ids(merged) == ["light.a", "light.b"]
    assert flags(merged) == [False, False]


def test_the_limit_holds_across_both_sources():
    personal = [entry("light.a")]
    fallback = [entry("light.b"), entry("light.c"), entry("light.d")]

    merged = merge_personal_and_global(personal, fallback, limit=3)

    assert ids(merged) == ["light.a", "light.b", "light.c"]


def test_a_long_personal_list_is_truncated_before_padding():
    personal = [entry("light.a"), entry("light.b"), entry("light.c")]

    merged = merge_personal_and_global(personal, [entry("light.z")], limit=2)

    assert ids(merged) == ["light.a", "light.b"]


def test_nothing_anywhere_is_an_empty_list():
    assert merge_personal_and_global([], [], limit=5) == []


def test_a_zero_limit_yields_nothing():
    assert merge_personal_and_global([entry("light.a")], [entry("light.b")], limit=0) == []


def test_duplicates_inside_the_fallback_are_only_taken_once():
    merged = merge_personal_and_global([], [entry("light.a"), entry("light.a")], limit=5)
    assert ids(merged) == ["light.a"]
