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


async def test_stop_unsubscribes(hass):
    # Deliberately not using the `wired` fixture: it starts its own tracker
    # that stays subscribed for the whole test body (its async_stop() only
    # runs at fixture teardown), which would record this event regardless of
    # what the tracker under test does here and mask the behaviour we want
    # to check.
    store = ParetoStore(hass)
    await store.async_load()
    hass.states.async_set("light.b", "off")
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
