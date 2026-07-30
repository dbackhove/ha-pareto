from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pareto.const import (
    CONF_EXCLUDE_ENTITIES,
    CONF_HALF_LIFE_DAYS,
    CONF_PINNED_ENTITIES,
    CONF_TOP_COUNT,
    DOMAIN,
)
from custom_components.pareto.coordinator import ParetoCoordinator
from custom_components.pareto.store import ParetoStore

BERLIN = timezone(timedelta(hours=2))
USER = "0123456789abcdef0123456789abcdef"


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


async def test_options_are_read_live_not_cached_at_construction(hass):
    """CONF_TOP_COUNT must be read from entry.options at recompute time, not
    captured once in __init__ -- otherwise an options-flow change would need
    the coordinator to be rebuilt to take effect, instead of the reload it
    actually gets."""
    coordinator, store = await make(hass, {CONF_TOP_COUNT: 10})
    for name in ("light.a", "light.b"):
        hass.states.async_set(name, "off")
        store.record(name, USER, datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN))
    coordinator.async_recompute()
    assert len(coordinator.top) == 2

    hass.config_entries.async_update_entry(coordinator._entry, options={CONF_TOP_COUNT: 1})
    coordinator.async_recompute()
    assert len(coordinator.top) == 1


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
    store.record_import("light.old", USER, "2020-01-01", 1, "2020-01-01T12:00:00+01:00")
    coordinator._async_daily(None)
    assert store.aggregated() == []


async def test_daily_pass_retention_follows_the_configured_half_life(hass):
    """retention_days(half_life) must actually drive the daily prune, not a
    hardcoded 90: with half_life_days=30, retention is max(90, 6*30)=180
    days, so a bucket 100 days old must survive -- it would not survive a
    hardcoded 90-day cutoff."""
    coordinator, store = await make(hass, {CONF_HALF_LIFE_DAYS: 30})
    old_day = dt_util.now().date() - timedelta(days=100)
    store.record_import(
        "light.old", USER, old_day.isoformat(), 1, f"{old_day.isoformat()}T12:00:00+02:00"
    )

    coordinator._async_daily(None)

    assert store.aggregated() != []
    assert store.aggregated()[0].counts == {old_day.isoformat(): 1}


async def test_start_schedules_the_daily_pass_just_after_midnight(hass):
    coordinator, _ = await make(hass)
    with patch("custom_components.pareto.coordinator.async_track_time_change") as track:
        await coordinator.async_start()
    assert track.called
    assert track.call_args.kwargs == {"hour": 0, "minute": 1, "second": 0}
    await coordinator.async_stop()
