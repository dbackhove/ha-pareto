from datetime import datetime, timedelta, timezone

from homeassistant.const import EVENT_CALL_SERVICE
from homeassistant.core import Context
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pareto.const import DOMAIN

BERLIN = timezone(timedelta(hours=2))
USER = "0123456789abcdef0123456789abcdef"


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
