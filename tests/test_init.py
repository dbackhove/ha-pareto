from unittest.mock import Mock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_CALL_SERVICE
from homeassistant.core import Context
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pareto.const import DOMAIN
from custom_components.pareto.store import ParetoStoreError

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


async def test_daily_timer_is_cancelled_on_unload(hass):
    """Unload must cancel the coordinator's daily timer, not just the tracker.

    A leaked timer would keep firing after every reload, recomputing against a
    coordinator/entry pairing that no longer belongs to the live config entry.
    """
    entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    entry.add_to_hass(hass)

    unsub_daily = Mock()
    with patch(
        "custom_components.pareto.coordinator.async_track_time_change",
        return_value=unsub_daily,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert not unsub_daily.called

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert unsub_daily.called


async def test_store_error_aborts_setup_instead_of_being_swallowed(hass):
    """Data written by a newer Pareto must refuse setup, not be silently ignored."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    entry.add_to_hass(hass)

    with patch(
        "custom_components.pareto.ParetoStore.async_load",
        side_effect=ParetoStoreError("written by a newer version"),
    ):
        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert entry.reason is not None and "newer version" in entry.reason
    assert entry.entry_id not in hass.data.get(DOMAIN, {})
