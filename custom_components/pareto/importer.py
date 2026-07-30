"""One-off backfill of past usage from the logbook."""

from __future__ import annotations

import logging
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
    """
    from homeassistant.components.logbook.processor import EventProcessor

    processor = EventProcessor(hass, [], entity_ids=None, device_ids=None, context_id=None)
    return await hass.async_add_executor_job(processor.get_events, day_start, day_end)


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


async def async_import_history(hass: HomeAssistant, store, days: int) -> int:
    """Import up to ``days`` of past usage. Returns how many rows were written.

    Only writes into day buckets that do not exist yet, which makes the whole
    thing idempotent, unable to clobber live data, and resumable after a
    failure. A day that fails is logged and skipped, never fatal.
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

        for row in rows or []:
            if not isinstance(row, dict):
                continue
            parsed = _extract(row)
            if parsed is None:
                continue
            entity_id, user_id, bucket_day, when_iso = parsed
            if store.record_import(entity_id, user_id, bucket_day, when_iso):
                written += 1

    _LOGGER.info("Pareto imported %s past usages", written)
    return written
