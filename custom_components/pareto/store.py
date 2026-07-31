"""Persistence for Pareto usage counters."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store
from homeassistant.util.dt import parse_datetime, start_of_local_day

from .const import SAVE_DELAY, STORAGE_KEY, STORAGE_VERSION
from .ranking import EntityUsage, parse_day

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

    ``user_last_used`` arrived with the per-user lists and is simply absent
    from anything written before them. That is not corruption: an entry
    without it falls back to day granularity in ``aggregated_for_user``.
    """
    normalized: dict[str, dict[str, Any]] = {}
    for entity_id, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        buckets = entry.get("buckets")
        stamps = entry.get("user_last_used")
        normalized[entity_id] = {
            "last_used": entry.get("last_used"),
            "buckets": buckets if isinstance(buckets, dict) else {},
            "user_last_used": stamps if isinstance(stamps, dict) else {},
        }
    return normalized


def _normalize_prefs(raw: Any) -> dict[str, dict[str, list[str]]]:
    """Coerce the stored personal preferences into shape.

    Same contract as ``_normalize_entries``: anything unusable becomes empty
    rather than raising. A typo in a hand-edited file costs one person their
    hidden list, not the whole integration's setup.
    """
    normalized: dict[str, dict[str, list[str]]] = {}
    if not isinstance(raw, dict):
        return normalized

    for user_id, prefs in raw.items():
        if not isinstance(prefs, dict):
            continue
        cleaned: dict[str, list[str]] = {}
        for key in ("hidden", "pinned"):
            value = prefs.get(key)
            cleaned[key] = (
                [e for e in value if isinstance(e, str)] if isinstance(value, list) else []
            )
        normalized[user_id] = cleaned
    return normalized


def _later(existing: str | None, incoming: str) -> str | None:
    """Return whichever ISO timestamp is later.

    Compares parsed datetimes so a DST fall-back -- where the later moment
    carries the smaller string -- does not rank backwards. An unparseable
    ``incoming`` leaves ``existing`` standing; an unparseable ``existing`` is
    treated as missing.
    """
    parsed = parse_datetime(incoming)
    if parsed is None:
        return existing
    if existing is None:
        return incoming

    current = parse_datetime(existing)
    if current is None or parsed > current:
        return incoming
    return existing


def _start_of_latest_day(counts: dict[str, int]) -> str | None:
    """Return local midnight of the newest day bucket, or None if there is none.

    This is the recency fallback for usage recorded before per-user stamps
    existed. Midnight is deliberate: it sorts such an entry below every real
    timestamp from the same day, which is right, because it *is* the older
    information.
    """
    days = [parsed for day in counts if (parsed := parse_day(day)) is not None]
    if not days:
        return None
    return start_of_local_day(max(days)).isoformat()


class ParetoStore:
    """Per-entity, per-user, per-day usage counters backed by HA's Store.

    Layout keeps the entity on the outside and the user on the inside, so the
    per-user card reads one level deeper without a data migration.

    Personal preferences (hidden, pinned) live beside the counters under
    ``prefs``, keyed by user. They are settings rather than usage, but they
    belong to a person rather than to the installation, which is what keeps
    them out of the config entry options.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict[str, dict[str, Any]] = {}
        self._prefs: dict[str, dict[str, list[str]]] = {}

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
            self._prefs = {}
            return

        if not isinstance(raw, dict):
            self._data = {}
            self._prefs = {}
            return
        entries = raw.get("data")
        self._data = _normalize_entries(entries) if isinstance(entries, dict) else {}
        self._prefs = _normalize_prefs(raw.get("prefs"))

    @callback
    def is_empty(self) -> bool:
        """Whether nothing has ever been recorded or imported."""
        return not self._data

    @callback
    def raw(self) -> dict[str, dict[str, Any]]:
        """Return the underlying structure, by reference. For tests only."""
        return self._data

    def _entry(self, entity_id: str) -> dict[str, Any]:
        return self._data.setdefault(
            entity_id, {"last_used": None, "buckets": {}, "user_last_used": {}}
        )

    def _record_timestamp(self, entry: dict[str, Any], user_id: str, when_iso: str) -> None:
        """Move both the entity-wide and the per-user stamp forward, never back.

        The entity-wide value feeds the global sensors and is the most recent
        moment across everyone. The per-user value is what a personal Recent
        list sorts on: without it that list would show when *somebody else*
        last touched the thing.
        """
        entity_stamp = _later(entry["last_used"], when_iso)
        if entity_stamp is not None:
            entry["last_used"] = entity_stamp

        per_user = entry["user_last_used"]
        user_stamp = _later(per_user.get(user_id), when_iso)
        if user_stamp is not None:
            per_user[user_id] = user_stamp

    @callback
    def record(self, entity_id: str, user_id: str, when: datetime) -> None:
        """Count one live usage. ``when`` must already be in local time."""
        entry = self._entry(entity_id)
        day = when.date().isoformat()
        buckets = entry["buckets"].setdefault(user_id, {})
        buckets[day] = buckets.get(day, 0) + 1

        self._record_timestamp(entry, user_id, when.isoformat())
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
        self._record_timestamp(entry, user_id, when_iso)
        self.schedule_save()
        return True

    @callback
    def prune(self, today: date, keep_days: int) -> None:
        """Drop buckets older than ``keep_days``, and entities left with none.

        A user's timestamp goes with their last bucket: leaving it behind
        would keep a recency claim alive for usage that no longer exists.

        ``prefs`` are never pruned. A hidden entity usually has no usage at
        all -- that is rather the point -- so expiring it would silently undo
        somebody's decision.
        """
        cutoff = (today - timedelta(days=keep_days)).isoformat()

        for entity_id in list(self._data):
            entry = self._data[entity_id]
            for user_id in list(entry["buckets"]):
                kept = {d: c for d, c in entry["buckets"][user_id].items() if d >= cutoff}
                if kept:
                    entry["buckets"][user_id] = kept
                else:
                    del entry["buckets"][user_id]
                    entry["user_last_used"].pop(user_id, None)
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
    def aggregated_for_user(self, user_id: str) -> list[EntityUsage]:
        """Collapse one user's own buckets, ignoring everybody else's.

        ``last_used`` is that user's own stamp. Usage recorded before per-user
        stamps existed has none, and falls back to local midnight of their
        newest day bucket. It deliberately does *not* fall back to the
        entity-wide value: that would credit this user with somebody else's
        click, which is the exact confusion personal lists exist to remove.
        """
        result: list[EntityUsage] = []
        for entity_id, entry in self._data.items():
            counts = entry["buckets"].get(user_id)
            if not counts:
                continue
            last_used = entry["user_last_used"].get(user_id) or _start_of_latest_day(counts)
            result.append(
                EntityUsage(entity_id=entity_id, counts=dict(counts), last_used=last_used)
            )
        return result

    @callback
    def prefs(self, user_id: str) -> dict[str, list[str]]:
        """Return one user's hidden and pinned entity ids, as copies."""
        stored = self._prefs.get(user_id)
        if stored is None:
            return {"hidden": [], "pinned": []}
        return {"hidden": list(stored["hidden"]), "pinned": list(stored["pinned"])}

    @callback
    def set_pref(
        self,
        user_id: str,
        entity_id: str,
        *,
        hidden: bool | None = None,
        pinned: bool | None = None,
    ) -> dict[str, list[str]]:
        """Set one entity's personal flags and return the user's new prefs.

        ``hidden`` and ``pinned`` are mutually exclusive: setting one clears
        the other, because an entry cannot be both wanted and unwanted. If a
        caller sets both to True anyway, ``pinned`` is applied last and wins.
        """
        stored = self._prefs.setdefault(user_id, {"hidden": [], "pinned": []})

        def apply(key: str, value: bool) -> None:
            listed = stored[key]
            if value and entity_id not in listed:
                listed.append(entity_id)
            elif not value and entity_id in listed:
                listed.remove(entity_id)

        if hidden is not None:
            apply("hidden", hidden)
            if hidden:
                apply("pinned", False)
        if pinned is not None:
            apply("pinned", pinned)
            if pinned:
                apply("hidden", False)

        # A user who has cleared everything should not keep an empty record.
        if not stored["hidden"] and not stored["pinned"]:
            del self._prefs[user_id]

        self.schedule_save()
        return self.prefs(user_id)

    @callback
    def schedule_save(self) -> None:
        """Queue a delayed write. Bursts collapse into a single disk write."""
        self._store.async_delay_save(lambda: self._payload(), SAVE_DELAY)

    def _payload(self) -> dict[str, Any]:
        return {"data": self._data, "prefs": self._prefs}

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
        await self._store.async_save(self._payload())
