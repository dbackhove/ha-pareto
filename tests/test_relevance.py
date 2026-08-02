"""What counts as maintenance clutter rather than something a person uses."""

from homeassistant.const import EntityCategory
from homeassistant.helpers import entity_registry as er

from custom_components.pareto.relevance import build_maintenance_filter


def register(hass, domain: str, object_id: str, **kwargs) -> str:
    """Put one entity in the registry and return its entity id."""
    registry = er.async_get(hass)
    return registry.async_get_or_create(
        domain, "test_platform", f"{domain}-{object_id}", suggested_object_id=object_id, **kwargs
    ).entity_id


async def test_a_config_entity_is_maintenance(hass):
    """The reported case: a firmware update carries entity_category config."""
    entity_id = register(hass, "switch", "led_indicator", entity_category=EntityCategory.CONFIG)
    assert build_maintenance_filter(hass, True)(entity_id) is True


async def test_a_diagnostic_entity_is_maintenance(hass):
    entity_id = register(hass, "button", "identify", entity_category=EntityCategory.DIAGNOSTIC)
    assert build_maintenance_filter(hass, True)(entity_id) is True


async def test_an_entity_hidden_in_home_assistant_is_maintenance(hass):
    """Hiding it in HA is already the answer; it should not reappear here."""
    entity_id = register(hass, "switch", "tucked_away", hidden_by=er.RegistryEntryHider.USER)
    assert build_maintenance_filter(hass, True)(entity_id) is True


async def test_a_plain_operable_entity_is_kept(hass):
    entity_id = register(hass, "light", "stehlampe")
    assert build_maintenance_filter(hass, True)(entity_id) is False


async def test_an_unregistered_operable_entity_is_kept(hass):
    """No registry entry is not evidence of clutter."""
    assert build_maintenance_filter(hass, True)("light.never_registered") is False


async def test_a_non_operable_domain_is_maintenance_without_any_registry_entry(hass):
    """The safety net for rows already in the store, which carry no category."""
    assert build_maintenance_filter(hass, True)("binary_sensor.gong_ist_stumm") is True


async def test_the_update_domain_is_maintenance_even_without_a_category(hass):
    """Not every integration sets entity_category on its update entities."""
    entity_id = register(hass, "update", "firmware")
    assert build_maintenance_filter(hass, True)(entity_id) is True


async def test_switching_the_option_off_keeps_everything(hass):
    predicate = build_maintenance_filter(hass, False)
    config = register(hass, "switch", "led", entity_category=EntityCategory.CONFIG)
    assert predicate(config) is False
    assert predicate("binary_sensor.anything") is False
    assert predicate("update.firmware") is False
