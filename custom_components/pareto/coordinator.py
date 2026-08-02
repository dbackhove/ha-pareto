"""Turns stored counters into two rendered lists, and decides when to redo it."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from .const import (
    CONF_EXCLUDE_DOMAINS,
    CONF_EXCLUDE_ENTITIES,
    CONF_HALF_LIFE_DAYS,
    CONF_HIDE_MAINTENANCE,
    CONF_INCLUDE_DOMAINS,
    CONF_PINNED_ENTITIES,
    CONF_RECENT_COUNT,
    CONF_TOP_COUNT,
    DEFAULT_HALF_LIFE_DAYS,
    DEFAULT_HIDE_MAINTENANCE,
    DEFAULT_RECENT_COUNT,
    DEFAULT_TOP_COUNT,
    UPDATE_DEBOUNCE,
)
from .ranking import RankedEntity, build_ranked_list, retention_days
from .relevance import build_maintenance_filter
from .store import ParetoStore

_LOGGER = logging.getLogger(__name__)


class ParetoCoordinator:
    """Holds the current lists and republishes them when they can have changed."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, store: ParetoStore) -> None:
        self._hass = hass
        self._entry = entry
        self._store = store
        self._listeners: list[Callable[[], None]] = []
        self._unsub_daily: Callable[[], None] | None = None
        self._top: list[RankedEntity] = []
        self._recent: list[RankedEntity] = []
        self._debouncer = Debouncer(
            hass,
            _LOGGER,
            cooldown=UPDATE_DEBOUNCE,
            immediate=True,
            function=self._async_debounced_recompute,
        )

    @property
    def top(self) -> list[RankedEntity]:
        return self._top

    @property
    def recent(self) -> list[RankedEntity]:
        return self._recent

    async def async_start(self) -> None:
        """Compute once, then recompute daily just after local midnight.

        The daily pass is not optional: decay alone reorders the list, so
        without it a quiet week would leave the ranking frozen.
        """
        self.async_recompute()
        self._unsub_daily = async_track_time_change(
            self._hass, self._async_daily, hour=0, minute=1, second=0
        )

    async def async_stop(self) -> None:
        if self._unsub_daily is not None:
            self._unsub_daily()
            self._unsub_daily = None
        # Debouncer.async_shutdown is a plain @callback despite the async_
        # prefix (confirmed against the installed homeassistant.helpers.debounce
        # source, and by HA core's own DataUpdateCoordinator calling it the
        # same way) -- it must not be awaited.
        self._debouncer.async_shutdown()

    @callback
    def async_add_listener(self, update_cb: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(update_cb)

        @callback
        def remove() -> None:
            if update_cb in self._listeners:
                self._listeners.remove(update_cb)

        return remove

    @callback
    def async_request_refresh(self) -> None:
        """Ask for a recompute, collapsing bursts into one.

        Debouncer.async_call is a coroutine, so from a synchronous, callback
        context it is scheduled as a task rather than awaited directly.
        """
        self._hass.async_create_task(self._debouncer.async_call())

    async def _async_debounced_recompute(self) -> None:
        self.async_recompute()

    @callback
    def _async_daily(self, _now) -> None:
        self._store.prune(dt_util.now().date(), retention_days(self._half_life))
        self.async_recompute()

    @property
    def _half_life(self) -> float:
        return float(self._entry.options.get(CONF_HALF_LIFE_DAYS, DEFAULT_HALF_LIFE_DAYS))

    @callback
    def ranking_context(self) -> dict[str, Any]:
        """Return the filter arguments ``build_ranked_list`` ranks with.

        Exposed rather than kept private because the websocket API builds
        per-user lists from the same options, with personal preferences
        layered on top. Reading the config entry a second time over there
        would work until the day the two readings drift apart.
        """
        options = self._entry.options
        return {
            "today": dt_util.now().date(),
            "half_life_days": self._half_life,
            "include_domains": frozenset(options.get(CONF_INCLUDE_DOMAINS, [])),
            "exclude_domains": frozenset(options.get(CONF_EXCLUDE_DOMAINS, [])),
            "exclude_entities": frozenset(options.get(CONF_EXCLUDE_ENTITIES, [])),
            "pinned": tuple(options.get(CONF_PINNED_ENTITIES, [])),
            "exists": lambda entity_id: self._hass.states.get(entity_id) is not None,
            "is_maintenance": build_maintenance_filter(
                self._hass,
                bool(options.get(CONF_HIDE_MAINTENANCE, DEFAULT_HIDE_MAINTENANCE)),
            ),
        }

    @callback
    def limit_for(self, mode: str) -> int:
        """Return how many entries one list may hold."""
        options = self._entry.options
        if mode == "recent":
            return int(options.get(CONF_RECENT_COUNT, DEFAULT_RECENT_COUNT))
        return int(options.get(CONF_TOP_COUNT, DEFAULT_TOP_COUNT))

    @callback
    def async_recompute(self) -> None:
        """Rebuild both lists from the store and notify listeners."""
        usages = self._store.aggregated()
        shared = self.ranking_context()

        self._top = build_ranked_list(usages, mode="top", limit=self.limit_for("top"), **shared)
        self._recent = build_ranked_list(
            usages, mode="recent", limit=self.limit_for("recent"), **shared
        )

        for listener in list(self._listeners):
            try:
                listener()
            except Exception:  # one bad sensor must not block the rest
                _LOGGER.exception("Pareto listener raised during update")
