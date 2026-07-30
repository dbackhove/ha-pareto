"""Records which entities a human operates through Home Assistant."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from homeassistant.const import EVENT_CALL_SERVICE
from homeassistant.core import Context, Event, HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import BLOCKED_DOMAINS, BLOCKED_SERVICES
from .store import ParetoStore

_LOGGER = logging.getLogger(__name__)


def is_blocked_service(domain: str, service: str) -> bool:
    """Return whether this call is plumbing rather than using an entity."""
    if domain in BLOCKED_DOMAINS:
        return True
    if f"{domain}.{service}" in BLOCKED_SERVICES:
        return True
    return service == "reload" or service.startswith("reload_")


async def async_resolve_targets(
    hass: HomeAssistant,
    domain: str,
    service: str,
    data: dict[str, Any],
    context: Context,
) -> set[str]:
    """Resolve a service call's targets to concrete entity ids.

    The plain ``entity_id`` form covers nearly every call from the UI and is
    handled directly. Area, device, label and floor targets go through HA's
    target-resolution helper, wrapped in try/except so a future API change
    degrades to "no targets" rather than killing the listener.

    ``context`` is accepted to keep this function's interface stable even
    though the current resolution path (``homeassistant.helpers.target``)
    does not need it -- it operates purely on the raw target ids in ``data``.
    """
    entity_id = data.get("entity_id")
    if isinstance(entity_id, str) and entity_id != "all":
        return {entity_id}
    if isinstance(entity_id, list):
        return {e for e in entity_id if isinstance(e, str)}

    if not any(k in data for k in ("area_id", "device_id", "label_id", "floor_id")):
        return set()

    try:
        from homeassistant.helpers.target import (
            TargetSelection,
            async_extract_referenced_entity_ids,
        )

        # Confirmed synchronous via inspect.iscoroutinefunction against the
        # pinned test HA (2026.2.3); this module already existed there, well
        # before the integration's actual minimum supported HA version.
        selected = async_extract_referenced_entity_ids(hass, TargetSelection(data))
        return set(selected.referenced) | set(selected.indirectly_referenced)
    except Exception:  # one odd call must not stop tracking
        _LOGGER.debug("Could not resolve targets for %s.%s", domain, service, exc_info=True)
        return set()


class UsageTracker:
    """Listens for service calls and counts the ones a human made directly."""

    def __init__(
        self, hass: HomeAssistant, store: ParetoStore, on_recorded: Callable[[], None]
    ) -> None:
        self._hass = hass
        self._store = store
        self._on_recorded = on_recorded
        self._unsub: Callable[[], None] | None = None

    @callback
    def async_start(self) -> None:
        self._unsub = self._hass.bus.async_listen(EVENT_CALL_SERVICE, self._async_handle)

    @callback
    def async_stop(self) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None

    async def _async_handle(self, event: Event) -> None:
        context = event.context
        # user_id set means a human; parent_id empty means they acted directly
        # rather than this being a script or automation carrying their context.
        if context.user_id is None or context.parent_id is not None:
            return

        domain = event.data.get("domain")
        service = event.data.get("service")
        if not isinstance(domain, str) or not isinstance(service, str):
            return
        if is_blocked_service(domain, service):
            return

        data = event.data.get("service_data") or {}
        if not isinstance(data, dict):
            return

        targets = await async_resolve_targets(self._hass, domain, service, data, context)
        # Nothing validates the ids carried on an EVENT_CALL_SERVICE, and the
        # store happily creates an entry for any string it is handed. Since
        # prune() only drops buckets by age, an add-on or integration firing
        # invented ids would otherwise grow the file for a full retention
        # window. Ranking filters unknown entities out of the *output* already;
        # this keeps them out of storage in the first place.
        targets = {e for e in targets if self._hass.states.get(e) is not None}
        if not targets:
            return

        now = dt_util.now()
        for entity_id in targets:
            self._store.record(entity_id, context.user_id, now)
        self._on_recorded()
