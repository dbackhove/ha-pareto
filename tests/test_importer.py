from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.util import dt as dt_util

from custom_components.pareto.importer import async_import_history
from custom_components.pareto.store import ParetoStore

BERLIN = timezone(timedelta(hours=2))
USER = "0123456789abcdef0123456789abcdef"
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
        entry(
            "light.a", "2026-07-28T12:00:00+02:00", domain="homeassistant", service="update_entity"
        )
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


async def test_two_calls_on_the_same_day_aggregate_to_two(hass, store):
    """record_import refuses a bucket that already exists, so importing one
    row at a time would silently clamp every day to at most 1. The importer
    must aggregate same-day rows before writing."""
    rows = [
        entry("light.a", "2026-07-28T09:00:00+02:00"),
        entry("light.a", "2026-07-28T20:00:00+02:00"),
    ]
    with patch(PATCH_TARGET, AsyncMock(side_effect=[rows] + [[]] * 9)):
        written = await async_import_history(hass, store, days=10)
    assert written == 2
    assert store.aggregated()[0].counts == {"2026-07-28": 2}
    # Compared as datetimes, not strings: the test hass's local timezone need
    # not be Berlin, so the stored last_used may carry a different offset for
    # the very same instant.
    last_used = dt_util.parse_datetime(store.aggregated()[0].last_used)
    assert last_used == dt_util.parse_datetime("2026-07-28T20:00:00+02:00")
