"""Persistence for Pareto usage counters."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store
from homeassistant.util.dt import parse_datetime

from .const import SAVE_DELAY, STORAGE_KEY, STORAGE_VERSION
from .ranking import EntityUsage

_LOGGER = logging.getLogger(__name__)


class ParetoStoreError(Exception):
    """Raised when stored data exists but cannot be used safely."""


def _normalize_entries(entries: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Coerce loaded data into the shape every accessor relies on.

    A hand-edited or partially-written storage file can be valid JSON while
    missing ``buckets`` or ``last_used`` on an entry. Normalising once here,
    right after load, means ``aggregated()`` and ``prune()`` never have to
    guard against it themselves -- a corrupt entry starts empty rather than
    raising ``KeyError`` out of ``async_start()`` and failing setup.
    """
    normalized: dict[str, dict[str, Any]] = {}
    for entity_id, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        buckets = entry.get("buckets")
        normalized[entity_id] = {
            "last_used": entry.get("last_used"),
            "buckets": buckets if isinstance(buckets, dict) else {},
        }
    return normalized


class ParetoStore:
    """Per-entity, per-user, per-day usage counters backed by HA's Store.

    Layout keeps the entity on the outside and the user on the inside. Phase 1
    aggregates across users; a future per-user card reads one level deeper
    without a data migration.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict[str, dict[str, Any]] = {}

    async def async_load(self) -> None:
        """Load from disk.

        Unreadable data starts empty rather than blocking setup. Data written
        by a *newer* Pareto is different: starting empty would look harmless
        until the first delayed save destroyed it, so that case raises.
        """
        try:
            raw = await self._store.async_load()
        except NotImplementedError as err:
            raise ParetoStoreError(
                "Pareto storage was written by a newer version and cannot be read"
            ) from err
        except Exception:  # never let bad data block setup
            _LOGGER.warning(
                "Could not read Pareto storage, starting with empty data", exc_info=True
            )
            self._data = {}
            return

        if not isinstance(raw, dict):
            self._data = {}
            return
        entries = raw.get("data")
        self._data = _normalize_entries(entries) if isinstance(entries, dict) else {}

    @callback
    def is_empty(self) -> bool:
        """Whether nothing has ever been recorded or imported."""
        return not self._data

    @callback
    def raw(self) -> dict[str, dict[str, Any]]:
        """Return the underlying structure, by reference. For tests only."""
        return self._data

    def _entry(self, entity_id: str) -> dict[str, Any]:
        return self._data.setdefault(entity_id, {"last_used": None, "buckets": {}})

    def _update_last_used(self, entry: dict[str, Any], when_iso: str) -> None:
        """Update last_used if when_iso is later, using datetime comparison.

        Compares parsed datetimes to handle DST transitions correctly. If the
        stored last_used cannot be parsed, treats it as missing.
        """
        incoming = parse_datetime(when_iso)
        if incoming is None:
            return

        if entry["last_used"] is None:
            entry["last_used"] = when_iso
            return

        existing = parse_datetime(entry["last_used"])
        if existing is None or incoming > existing:
            entry["last_used"] = when_iso

    @callback
    def record(self, entity_id: str, user_id: str, when: datetime) -> None:
        """Count one live usage. ``when`` must already be in local time."""
        entry = self._entry(entity_id)
        day = when.date().isoformat()
        buckets = entry["buckets"].setdefault(user_id, {})
        buckets[day] = buckets.get(day, 0) + 1

        stamp = when.isoformat()
        self._update_last_used(entry, stamp)
        self.schedule_save()

    @callback
    def record_import(
        self, entity_id: str, user_id: str, day: str, count: int, when_iso: str
    ) -> bool:
        """Write one historical day's usage, but only into a bucket that does
        not exist.

        ``count`` is the true total for that (entity, user, day) -- the
        importer aggregates same-day rows before calling this, so a lamp
        operated twenty times on Monday is written as 20, not clamped to 1.
        This single rule (never touch an existing bucket) makes the import
        idempotent, stops it from ever clobbering live data, and lets an
        aborted run resume by simply being run again. Returns whether
        anything was written.
        """
        entry = self._entry(entity_id)
        buckets = entry["buckets"].setdefault(user_id, {})
        if day in buckets:
            return False

        buckets[day] = count
        self._update_last_used(entry, when_iso)
        self.schedule_save()
        return True

    @callback
    def prune(self, today: date, keep_days: int) -> None:
        """Drop buckets older than ``keep_days``, and entities left with none."""
        cutoff = (today - timedelta(days=keep_days)).isoformat()

        for entity_id in list(self._data):
            entry = self._data[entity_id]
            for user_id in list(entry["buckets"]):
                kept = {d: c for d, c in entry["buckets"][user_id].items() if d >= cutoff}
                if kept:
                    entry["buckets"][user_id] = kept
                else:
                    del entry["buckets"][user_id]
            if not entry["buckets"]:
                del self._data[entity_id]

        self.schedule_save()

    @callback
    def aggregated(self) -> list[EntityUsage]:
        """Collapse per-user buckets into one set of counts per entity."""
        result: list[EntityUsage] = []
        for entity_id, entry in self._data.items():
            counts: dict[str, int] = {}
            for user_buckets in entry["buckets"].values():
                for day, count in user_buckets.items():
                    counts[day] = counts.get(day, 0) + count
            result.append(
                EntityUsage(entity_id=entity_id, counts=counts, last_used=entry["last_used"])
            )
        return result

    @callback
    def schedule_save(self) -> None:
        """Queue a delayed write. Bursts collapse into a single disk write."""
        self._store.async_delay_save(lambda: {"data": self._data}, SAVE_DELAY)

    async def async_flush(self) -> None:
        """Write the current state to disk immediately.

        ``Store.async_save`` also cancels any pending delayed write, so this
        is the only safe thing to call before this store's owner goes away:
        without it, a reload (e.g. right after an options change) can start a
        fresh ``ParetoStore`` that reads the file *before* this instance's
        delayed write lands, after which every later save is built on that
        stale snapshot -- silently losing up to ``SAVE_DELAY`` seconds of
        counts. Call this from ``async_unload_entry`` and from the
        setup-failure unwind path, which has the same exposure.
        """
        await self._store.async_save({"data": self._data})
