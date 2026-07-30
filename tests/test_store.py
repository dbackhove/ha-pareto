from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from custom_components.pareto.store import ParetoStore, ParetoStoreError

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
    assert store.record_import("light.a", USER_A, "2026-07-25", 1, "2026-07-25T12:00:00+02:00")
    assert store.aggregated()[0].counts == {"2026-07-25": 1}


async def test_import_is_idempotent(store):
    store.record_import("light.a", USER_A, "2026-07-25", 1, "2026-07-25T12:00:00+02:00")
    store.record_import("light.a", USER_A, "2026-07-25", 1, "2026-07-25T12:00:00+02:00")
    assert store.aggregated()[0].counts == {"2026-07-25": 1}


async def test_import_never_overwrites_live_data(store):
    store.record("light.a", USER_A, datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN))
    wrote = store.record_import("light.a", USER_A, "2026-07-30", 1, "2026-07-30T08:00:00+02:00")
    assert wrote is False
    assert store.aggregated()[0].counts == {"2026-07-30": 1}


async def test_import_fills_only_the_missing_day(store):
    store.record("light.a", USER_A, datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN))
    store.record_import("light.a", USER_A, "2026-07-29", 1, "2026-07-29T12:00:00+02:00")
    assert store.aggregated()[0].counts == {"2026-07-29": 1, "2026-07-30": 1}


async def test_prune_drops_old_buckets(store):
    store.record_import("light.a", USER_A, "2026-01-01", 1, "2026-01-01T12:00:00+01:00")
    store.record_import("light.a", USER_A, "2026-07-30", 1, "2026-07-30T12:00:00+02:00")
    store.prune(date(2026, 7, 30), keep_days=90)
    assert store.aggregated()[0].counts == {"2026-07-30": 1}


async def test_prune_removes_entities_left_with_nothing(store):
    store.record_import("light.a", USER_A, "2026-01-01", 1, "2026-01-01T12:00:00+01:00")
    store.prune(date(2026, 7, 30), keep_days=90)
    assert store.aggregated() == []


async def test_prune_keeps_a_bucket_exactly_on_the_boundary(store):
    store.record_import("light.a", USER_A, "2026-05-01", 1, "2026-05-01T12:00:00+02:00")
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
    with (
        patch.object(s._store, "async_load", side_effect=NotImplementedError),
        pytest.raises(ParetoStoreError),
    ):
        await s.async_load()


async def test_flush_persists_a_pending_delayed_save(hass):
    """There is otherwise no coverage at all of the save/load round trip.

    async_delay_save only schedules a write; without async_flush forcing it
    through Store.async_save immediately, a fresh ParetoStore created right
    after (e.g. the reload after an options change) would read the file
    before that delayed write ever lands."""
    store = ParetoStore(hass)
    await store.async_load()
    store.record("light.a", USER_A, datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN))

    await store.async_flush()

    fresh = ParetoStore(hass)
    await fresh.async_load()
    assert fresh.aggregated()[0].entity_id == "light.a"
    assert fresh.aggregated()[0].counts == {"2026-07-30": 1}


async def test_corrupt_entry_missing_buckets_does_not_crash(hass):
    """Spec promises 'corrupt -> start empty, never crash'. A stored entry
    that is valid JSON but missing 'buckets' used to raise KeyError out of
    aggregated(), which runs inside async_start() and fails setup."""
    s = ParetoStore(hass)
    with patch.object(
        s._store,
        "async_load",
        return_value={"data": {"light.a": {"last_used": "2026-07-25T12:00:00+02:00"}}},
    ):
        await s.async_load()
    usages = s.aggregated()
    assert usages[0].entity_id == "light.a"
    assert usages[0].counts == {}


async def test_last_used_survives_a_dst_fall_back(store):
    """02:30+02:00 and 02:30+01:00 are the same wall clock an hour apart.
    String comparison ranks them backwards; datetime comparison does not."""
    summer = datetime(2026, 10, 25, 2, 30, tzinfo=timezone(timedelta(hours=2)))
    winter = datetime(2026, 10, 25, 2, 30, tzinfo=timezone(timedelta(hours=1)))
    store.record("light.a", USER_A, summer)
    store.record("light.a", USER_A, winter)
    assert store.aggregated()[0].last_used == winter.isoformat()


async def test_a_later_record_does_not_regress_last_used(store):
    """Recording an older timestamp after a newer one must not move it back."""
    later = datetime(2026, 7, 30, 18, 0, tzinfo=BERLIN)
    earlier = datetime(2026, 7, 30, 9, 0, tzinfo=BERLIN)
    store.record("light.a", USER_A, later)
    store.record("light.a", USER_A, earlier)
    assert store.aggregated()[0].last_used == later.isoformat()
