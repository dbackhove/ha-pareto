"""Decides which entities are maintenance clutter rather than usage.

Kept out of ``ranking.py`` on purpose: that module answers to plain pytest and
imports nothing from Home Assistant, while this one has to read the entity
registry. Ranking takes the resulting predicate as an argument.
"""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import NON_OPERABLE_DOMAINS


def _nothing_is_maintenance(_entity_id: str) -> bool:
    return False


def build_maintenance_filter(hass: HomeAssistant, enabled: bool) -> Callable[[str], bool]:
    """Return a predicate reporting whether an entity is clutter.

    Home Assistant already classifies entities that configure a device rather
    than being what the device does, and that classification is what a firmware
    update carries. Leaning on it means every integration is covered, including
    ones that do not exist yet, with no list to keep up to date. ``hidden_by``
    follows the same reasoning from the other side: somebody who hid an entity
    in Home Assistant has answered this question already.

    Returning a constant when the option is off keeps the disabled path free of
    registry lookups.
    """
    if not enabled:
        return _nothing_is_maintenance

    registry = er.async_get(hass)

    def is_maintenance(entity_id: str) -> bool:
        if entity_id.split(".", 1)[0] in NON_OPERABLE_DOMAINS:
            return True
        entry = registry.async_get(entity_id)
        if entry is None:
            # Plenty of real entities are never registered (YAML platforms,
            # templates). Absence is not evidence of clutter.
            return False
        return entry.entity_category is not None or entry.hidden_by is not None

    return is_maintenance
