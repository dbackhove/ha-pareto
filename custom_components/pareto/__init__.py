"""The Pareto integration."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

import voluptuous as vol
from homeassistant.components import frontend, persistent_notification
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA, MODE_STORAGE
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryError, Unauthorized
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .const import (
    ATTR_DAYS,
    CARD_FILENAME,
    CARD_URL,
    DEFAULT_IMPORT_DAYS,
    DOMAIN,
    SERVICE_IMPORT_HISTORY,
)
from .coordinator import ParetoCoordinator
from .importer import async_import_history
from .store import ParetoStore, ParetoStoreError
from .tracker import UsageTracker
from .websocket import async_register as async_register_websocket

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

IMPORT_SCHEMA = vol.Schema(
    {vol.Optional(ATTR_DAYS, default=DEFAULT_IMPORT_DAYS): vol.All(int, vol.Range(min=1, max=90))}
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Wire up everything that belongs to the component rather than an entry.

    WebSocket command handlers are global and cannot be unregistered, and the
    card only needs serving once. Doing either per entry would repeat it on
    every options-triggered reload.
    """
    async_register_websocket(hass)
    await _async_serve_card(hass)
    return True


async def _async_serve_card(hass: HomeAssistant) -> None:
    """Publish the built card bundle and have the frontend load it.

    HACS allows one category per repository, so the card ships inside the
    integration and registers itself instead of asking the user to add a
    Lovelace resource by hand.
    """
    card_path = Path(__file__).parent / "www" / CARD_FILENAME
    if not await hass.async_add_executor_job(card_path.is_file):
        # A source checkout that was never built. The sensors still work, so
        # this is a missing extra rather than a reason to fail setup.
        _LOGGER.warning("Pareto card bundle missing at %s, not serving it", card_path)
        return

    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(card_path), cache_headers=True)]
    )

    # The query string busts the browser cache on upgrade. It comes from the
    # manifest rather than a second constant, which would eventually drift --
    # which also means the manifest version must be raised for every release,
    # or the bust never busts.
    integration = await async_get_integration(hass, DOMAIN)
    url = f"{CARD_URL}?v={integration.version}"
    frontend.add_extra_js_url(hass, url)
    await _async_register_card_resource(hass, url)


async def _async_register_card_resource(hass: HomeAssistant, url: str) -> None:
    """Register the card as a Lovelace resource as well as an extra module.

    Both are needed, and for different clients. `add_extra_js_url` only puts
    a script tag into the rendered index page (frontend's IndexView reads
    DATA_EXTRA_MODULE_URL at render time), so a client holding a cached index
    -- the iOS companion app above all -- never learns the card exists and
    renders every Pareto card as "Custom element doesn't exist: pareto-card".
    Lovelace resources travel over the websocket on each dashboard load and
    the panel waits for them before building any card, so that is the path
    that actually arrives. The extra module url stays for YAML-mode
    instances, where the resource collection cannot be written to at all.

    Loading the card twice is harmless: both custom elements in the bundle
    register under a `customElements.get` guard.
    """
    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None:
        # Only reachable if `lovelace` failed its own setup, since it is a
        # manifest dependency. The card is still served; nothing to do here.
        return

    if lovelace.resource_mode != MODE_STORAGE:
        # YAML mode owns its resource list in configuration.yaml, and the
        # collection rejects writes. Those users add the resource by hand or
        # rely on the extra module url.
        _LOGGER.debug("Lovelace runs in YAML resource mode, not registering a resource")
        return

    resources = lovelace.resources
    # `loaded` and the explicit load mirror what the lovelace component does
    # for its own reads (see ResourceStorageCollection.async_get_info); there
    # is no public accessor that loads on demand.
    if not resources.loaded:
        await resources.async_load()
        resources.loaded = True

    try:
        for item in resources.async_items():
            if str(item.get("url", "")).startswith(CARD_URL):
                if item["url"] != url:
                    # Adopts a hand-added entry and corrects a stale version
                    # instead of adding a second one beside it.
                    await resources.async_update_item(item["id"], {"url": url})
                return

        await resources.async_create_item({"res_type": "module", "url": url})
    except Exception:
        # A dashboard resource is a convenience; the sensors are the product.
        # Never let this take component setup down with it.
        _LOGGER.exception("Could not register the Pareto card as a Lovelace resource")


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
        try:
            await store.async_flush()
        except Exception:  # must not replace the setup error being re-raised
            _LOGGER.warning("Pareto could not write usage data while unwinding", exc_info=True)
        raise

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Everything below is wired only once setup has fully succeeded: if
    # anything above had failed, a service left registered (or an import task
    # left running) against a coordinator and store that were just unwound
    # would be exactly the leak the try/except above exists to prevent.

    # One import at a time. A full scan runs on the recorder's own executor --
    # the pool that also serves history and the logbook -- so letting calls
    # pile up would stall those for everyone. A second caller is turned away
    # rather than queued: the work is idempotent, so waiting to redo it has no
    # value. Shared with the setup-time backfill below, which could otherwise
    # collide with a manual call.
    import_lock = asyncio.Lock()

    async def _run_import(days: int) -> int:
        if import_lock.locked():
            _LOGGER.warning("Pareto history import already running, ignoring this request")
            return 0
        async with import_lock:
            return await async_import_history(hass, store, days)

    async def _handle_import(call: ServiceCall) -> None:
        # Home Assistant does not gate services on admin rights, so without
        # this any signed-in account could trigger repeated recorder scans.
        # A call with no user id comes from an automation or script and is
        # allowed through, per the usual convention.
        if call.context.user_id is not None:
            user = await hass.auth.async_get_user(call.context.user_id)
            if user is None or not user.is_admin:
                raise Unauthorized(context=call.context)

        written = await _run_import(call.data[ATTR_DAYS])
        coordinator.async_recompute()
        _LOGGER.info("Pareto history import finished, %s usages added", written)

    hass.services.async_register(
        DOMAIN, SERVICE_IMPORT_HISTORY, _handle_import, schema=IMPORT_SCHEMA
    )

    async def _initial_import() -> None:
        """Backfill once at setup, in the background and never fatally."""
        try:
            written = await _run_import(DEFAULT_IMPORT_DAYS)
        except Exception:  # setup must survive a failed import
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

    # Only the very first setup -- before anything has ever been recorded --
    # runs the backfill automatically. On the reference installation a full
    # scan is ~216k logbook rows; running it on every restart and every
    # options-triggered reload to write nothing is not "one-off" in any
    # useful sense. Repeat imports stay available through the
    # pareto.import_history service registered above.
    if store.is_empty():
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
    # Without this, a pending 60s delayed save is still scheduled on this
    # store's Store instance when unload returns. On the very next setup --
    # e.g. right after an options change, which is the normal path here -- a
    # fresh ParetoStore reads the file before that write lands, and every
    # later save then builds on the stale snapshot it read.
    #
    # A disk error here must not abort teardown: the tracker and coordinator
    # are already stopped, so raising would leave the entry half torn down and
    # skip service deregistration below. Losing a minute of counts is the
    # lesser failure.
    try:
        await runtime.store.async_flush()
    except Exception:  # teardown must complete regardless
        _LOGGER.warning("Pareto could not write usage data on unload", exc_info=True)

    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, SERVICE_IMPORT_HISTORY)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload after the options changed. Usage data is untouched."""
    await hass.config_entries.async_reload(entry.entry_id)
