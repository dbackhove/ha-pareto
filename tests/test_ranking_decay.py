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
