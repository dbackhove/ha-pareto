"""Sensor platform for Pareto.

This is a minimal placeholder: ``__init__.py`` declares
``PLATFORMS = [Platform.SENSOR]`` and forwards entry setup to it, so the
module must exist and be importable even before the actual sensor entities
are implemented in a later task.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Pareto sensors. No entities yet; added in a later task."""
