"""Sensor entities publishing the Pareto lists."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ParetoCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the top and recent list sensors for one config entry."""
    coordinator: ParetoCoordinator = hass.data[DOMAIN][entry.entry_id].coordinator
    async_add_entities(
        [
            ParetoListSensor(coordinator, entry, "top", "Top"),
            ParetoListSensor(coordinator, entry, "recent", "Recent"),
        ]
    )


class ParetoListSensor(SensorEntity):
    """One rendered list.

    HA caps state values at 255 characters, so the list itself cannot live
    there. The state carries the length and the payload sits in an attribute.
    """

    _attr_has_entity_name = False
    _attr_should_poll = False
    _attr_icon = "mdi:sort-variant"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self, coordinator: ParetoCoordinator, entry: ConfigEntry, mode: str, label: str
    ) -> None:
        self._coordinator = coordinator
        self._mode = mode
        self._attr_name = f"Pareto {label}"
        self._attr_unique_id = f"{entry.entry_id}_{mode}"

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._coordinator.async_add_listener(self._handle_update))
        self._handle_update()

    @callback
    def _handle_update(self) -> None:
        # By the time this entity is registered as a coordinator listener,
        # `self.hass` has already been assigned (add_to_platform_start runs
        # before async_added_to_hass), and the listener is unregistered
        # synchronously -- before any `await` -- as the first step of entity
        # removal. So `self.hass` is never actually None here in practice.
        # The guard stays anyway: it is one cheap check against relying on
        # that lifecycle ordering forever, and it turns a would-be
        # RuntimeError from async_write_ha_state into a silent no-op instead
        # of a caught-and-logged exception on every listener fan-out.
        if self.hass is not None:
            self.async_write_ha_state()

    @property
    def _entries(self) -> list[dict[str, Any]]:
        ranked = self._coordinator.top if self._mode == "top" else self._coordinator.recent
        rows = [asdict(item) for item in ranked]
        if self._mode == "recent":
            for row in rows:
                row.pop("score", None)
        return rows

    @property
    def native_value(self) -> int:
        return len(self._entries)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"entities": self._entries}
