"""Access control and abuse resistance.

The history import is by far the most expensive thing this integration can be
asked to do: a full logbook scan on the recorder's own executor, the same pool
that serves the normal history and logbook views. Home Assistant does not
restrict services to administrators on its own, so without the checks pinned
here any signed-in account -- a guest, a child's account -- could stall the
recorder at will.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import Context
from homeassistant.exceptions import Unauthorized
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pareto.const import ATTR_DAYS, DOMAIN, SERVICE_IMPORT_HISTORY

IMPORT_TARGET = "custom_components.pareto.async_import_history"


async def setup_pareto(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_import_service_refuses_a_non_admin(hass, hass_read_only_user):
    """A signed-in non-admin must not be able to start a recorder scan."""
    await setup_pareto(hass)

    with (
        patch(IMPORT_TARGET, AsyncMock(return_value=0)) as importer,
        pytest.raises(Unauthorized),
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_IMPORT_HISTORY,
            {ATTR_DAYS: 10},
            blocking=True,
            context=Context(user_id=hass_read_only_user.id),
        )

    assert not importer.called


async def test_import_service_allows_an_admin(hass, hass_admin_user):
    await setup_pareto(hass)

    with patch(IMPORT_TARGET, AsyncMock(return_value=0)) as importer:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_IMPORT_HISTORY,
            {ATTR_DAYS: 10},
            blocking=True,
            context=Context(user_id=hass_admin_user.id),
        )

    assert importer.called


async def test_import_service_allows_a_call_with_no_user(hass):
    """Automations and scripts run without a user id and must keep working."""
    await setup_pareto(hass)

    with patch(IMPORT_TARGET, AsyncMock(return_value=0)) as importer:
        await hass.services.async_call(
            DOMAIN, SERVICE_IMPORT_HISTORY, {ATTR_DAYS: 10}, blocking=True, context=Context()
        )

    assert importer.called


async def test_import_service_refuses_an_unknown_user_id(hass):
    """A context naming a user that no longer exists must not be trusted."""
    await setup_pareto(hass)

    with (
        patch(IMPORT_TARGET, AsyncMock(return_value=0)) as importer,
        pytest.raises(Unauthorized),
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_IMPORT_HISTORY,
            {ATTR_DAYS: 10},
            blocking=True,
            context=Context(user_id="deadbeefdeadbeefdeadbeefdeadbeef"),
        )

    assert not importer.called


async def test_a_second_import_is_rejected_while_one_runs(hass, hass_admin_user):
    """Rapid calls must not become parallel recorder scans.

    Sequenced with events rather than sleeps: the second call is only made
    once the first is provably inside the import and holding the lock.
    """
    await setup_pareto(hass)

    started = 0
    first_inside = asyncio.Event()
    may_finish = asyncio.Event()

    async def blocking_import(*args, **kwargs):
        nonlocal started
        started += 1
        first_inside.set()
        await may_finish.wait()
        return 0

    def call():
        return hass.async_create_task(
            hass.services.async_call(
                DOMAIN,
                SERVICE_IMPORT_HISTORY,
                {ATTR_DAYS: 10},
                blocking=True,
                context=Context(user_id=hass_admin_user.id),
            )
        )

    with patch(IMPORT_TARGET, new=blocking_import):
        first = call()
        await first_inside.wait()

        second = call()
        # Must be turned away immediately, not queued behind the first. The
        # timeout matters: without the rejection this waits on the lock
        # forever, and an unbounded await would hang CI instead of failing it.
        await asyncio.wait_for(second, timeout=5)

        may_finish.set()
        await first

    assert started == 1


async def test_unload_survives_a_failing_flush(hass):
    """A disk error while flushing must not abort teardown.

    Unload has already stopped the tracker and coordinator by the time the
    flush runs, so raising here would leave the entry half torn down and skip
    service deregistration.
    """
    entry = await setup_pareto(hass)
    runtime = hass.data[DOMAIN][entry.entry_id]

    with patch.object(runtime.store, "async_flush", side_effect=OSError("disk full")):
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.entry_id not in hass.data[DOMAIN]
    assert not hass.services.has_service(DOMAIN, SERVICE_IMPORT_HISTORY)
