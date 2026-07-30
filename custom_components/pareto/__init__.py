"""The Pareto integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import voluptuous as vol
from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryError

from .const import ATTR_DAYS, DEFAULT_IMPORT_DAYS, DOMAIN, SERVICE_IMPORT_HISTORY
from .coordinator import ParetoCoordinator
from .importer import async_import_history
from .store import ParetoStore, ParetoStoreError
from .tracker import UsageTracker

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

IMPORT_SCHEMA = vol.Schema(
    {vol.Optional(ATTR_DAYS, default=DEFAULT_IMPORT_DAYS): vol.All(int, vol.Range(min=1, max=90))}
)


@dataclass
class ParetoRuntime:
    """Everything one config entry owns at runtime."""

    store: ParetoStore
    coordinator: ParetoCoordinator
    tracker: UsageTracker


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pareto from a config entry."""
    store = ParetoStore(hass)
    try:
        await store.async_load()
    except ParetoStoreError as err:
        # Refuse to run rather than overwrite data from a newer version.
        raise ConfigEntryError(str(err)) from err

    coordinator = ParetoCoordinator(hass, entry, store)
    tracker = UsageTracker(hass, store, coordinator.async_request_refresh)

    try:
        await coordinator.async_start()
        tracker.async_start()

        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = ParetoRuntime(
            store=store, coordinator=coordinator, tracker=tracker
        )

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        # HA never calls async_unload_entry for an entry that did not reach
        # LOADED, so a failure anywhere in this block must unwind itself:
        # otherwise the daily timer and the service-call listener started
        # above would keep running and mutating the on-disk store forever,
        # with no way to stop them short of restarting Home Assistant. Both
        # stop calls are safe even if the matching start above never ran.
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        tracker.async_stop()
        await coordinator.async_stop()
        raise

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Registered only once setup has fully succeeded: if anything above had
    # failed, a service left registered (or an import task left running)
    # against a coordinator/store that was just unwound would be exactly the
    # leak the try/except above exists to prevent.
    async def _handle_import(call: ServiceCall) -> None:
        written = await async_import_history(hass, store, call.data[ATTR_DAYS])
        coordinator.async_recompute()
        _LOGGER.info("Pareto history import finished, %s usages added", written)

    hass.services.async_register(
        DOMAIN, SERVICE_IMPORT_HISTORY, _handle_import, schema=IMPORT_SCHEMA
    )

    async def _initial_import() -> None:
        """Backfill once at setup, in the background and never fatally."""
        try:
            written = await async_import_history(hass, store, DEFAULT_IMPORT_DAYS)
        except Exception:  # noqa: BLE001 - setup must survive a failed import
            _LOGGER.warning("Pareto history import failed", exc_info=True)
            return
        coordinator.async_recompute()
        if written:
            persistent_notification.async_create(
                hass,
                f"Pareto imported {written} past usages from the logbook.",
                title="Pareto",
                notification_id="pareto_import",
            )

    entry.async_create_background_task(hass, _initial_import(), "pareto_initial_import")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Tear down a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unloaded:
        return False

    runtime: ParetoRuntime = hass.data[DOMAIN].pop(entry.entry_id)
    runtime.tracker.async_stop()
    await runtime.coordinator.async_stop()

    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, SERVICE_IMPORT_HISTORY)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload after the options changed. Usage data is untouched."""
    await hass.config_entries.async_reload(entry.entry_id)
