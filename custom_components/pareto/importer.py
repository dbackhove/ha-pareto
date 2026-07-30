"""One-off backfill of past usage from the logbook."""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .tracker import is_blocked_service

_LOGGER = logging.getLogger(__name__)


async def async_fetch_logbook_day(
    hass: HomeAssistant, day_start: datetime, day_end: datetime
) -> list[dict[str, Any]]:
    """Return raw logbook rows for one day.

    Isolated on purpose: this is the only part tied to recorder internals, and
    reading day by day keeps memory bounded and behaviour predictable. During
    research the REST logbook returned different results for the same entity
    depending on window size, so large single queries are avoided.

    ``event_types`` must be resolved through ``async_determine_event_types``,
    mirroring the logbook's own REST view
    (``homeassistant.components.logbook.rest_api``): passing an empty list
    here made the underlying query ``Events.event_type_id.in_(())``, which
    matches no rows at all, so nothing was ever imported. The query itself
    must also run on the recorder's own executor via ``get_instance(hass)``,
    not ``hass.async_add_executor_job`` -- the latter falls through to an
    unpooled, unprotected SQLite connection and logs a usage warning naming
    this integration on every call.
    """
    from homeassistant.components.logbook.helpers import async_determine_event_types
    from homeassistant.components.logbook.processor import EventProcessor
    from homeassistant.components.recorder import get_instance

    event_types = async_determine_event_types(hass, None, None)
    processor = EventProcessor(hass, event_types)
    return await get_instance(hass).async_add_executor_job(processor.get_events, day_start, day_end)


def _extract(row: dict[str, Any]) -> tuple[str, str, str, str] | None:
    """Return (entity_id, user_id, day, when_iso) if this row is a user action."""
    if row.get("context_event_type") != "call_service":
        return None

    user_id = row.get("context_user_id")
    entity_id = row.get("entity_id")
    when = row.get("when")
    if not isinstance(user_id, str) or not isinstance(entity_id, str) or not when:
        return None

    domain = row.get("context_domain")
    service = row.get("context_service")
    if isinstance(domain, str) and isinstance(service, str) and is_blocked_service(domain, service):
        return None

    try:
        moment = dt_util.parse_datetime(str(when))
    except (TypeError, ValueError):
        return None
    if moment is None:
        return None

    local = dt_util.as_local(moment)
    return entity_id, user_id, local.date().isoformat(), local.isoformat()


def _latest_iso(a: str, b: str) -> str:
    """Return whichever of two ISO timestamps is later, compared as datetimes.

    String comparison would rank e.g. two DST-offset timestamps backwards; an
    unparseable value loses to one that parses.
    """
    parsed_a = dt_util.parse_datetime(a)
    parsed_b = dt_util.parse_datetime(b)
    if parsed_a is None:
        return b
    if parsed_b is None:
        return a
    return b if parsed_b > parsed_a else a


async def async_import_history(hass: HomeAssistant, store, days: int) -> int:
    """Import up to ``days`` of past usage. Returns how many usages were written.

    The logbook is read one row per service call, but the store only writes
    once per (entity, user, day) -- ``record_import`` refuses to touch a
    bucket that already exists, so a second row for the same day would
    otherwise be silently dropped instead of counted. Rows are aggregated
    per day slice first, and each (entity, user, day) is then written with
    its true total in a single call. This keeps the write idempotent, unable
    to clobber live data, and resumable after a failure. A day that fails is
    logged and skipped, never fatal.
    """
    written = 0
    today = dt_util.now().date()

    for offset in range(days):
        day = today - timedelta(days=offset)
        day_start = dt_util.start_of_local_day(day)
        day_end = day_start + timedelta(days=1)

        try:
            rows = await async_fetch_logbook_day(hass, day_start, day_end)
        except Exception:  # one bad day must not lose the rest
            _LOGGER.warning("Pareto could not read the logbook for %s", day, exc_info=True)
            continue

        counts: Counter[tuple[str, str, str]] = Counter()
        latest_when: dict[tuple[str, str, str], str] = {}
        for row in rows or []:
            if not isinstance(row, dict):
                continue
            parsed = _extract(row)
            if parsed is None:
                continue
            entity_id, user_id, bucket_day, when_iso = parsed
            key = (entity_id, user_id, bucket_day)
            counts[key] += 1
            existing = latest_when.get(key)
            latest_when[key] = when_iso if existing is None else _latest_iso(existing, when_iso)

        for key, count in counts.items():
            entity_id, user_id, bucket_day = key
            if store.record_import(entity_id, user_id, bucket_day, count, latest_when[key]):
                written += count

    _LOGGER.info("Pareto imported %s past usages", written)
    return written
