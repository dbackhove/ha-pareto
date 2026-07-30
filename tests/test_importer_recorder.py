"""End-to-end test of the backfill against a real recorder and the real
``EventProcessor``, not the patched ``async_fetch_logbook_day`` seam every
other importer test uses.

This is the test that would have caught Finding 1: the importer built
``EventProcessor(hass, [], ...)`` -- an empty ``event_types`` list -- which
makes the underlying SQL query ``Events.event_type_id.in_(())``, matching no
rows ever. Every other importer test patches ``async_fetch_logbook_day``
directly and so never touched that code path at all.

Two environment quirks, both load-bearing:

* ``logbook``'s own ``async_setup`` pulls in ``frontend``, which needs the
  ``hass_frontend`` package -- not installed here. So the logbook component
  is never set up through HA's integration loader; instead
  ``hass.data["logbook"]`` is populated directly with the one piece of
  runtime state ``async_determine_event_types``/``EventProcessor`` actually
  read (a ``LogbookConfig``).
* ``recorder_mock`` must be requested ahead of ``hass`` in this test's
  signature. Deep inside pytest-homeassistant-custom-component,
  ``recorder_db_url`` asserts ``not hass_fixture_setup`` -- i.e. that the
  ``hass`` fixture's own body has not started running yet. The module-level
  ``auto_enable_custom_integrations`` autouse fixture in ``conftest.py``
  depends on ``hass`` directly, which would otherwise win that race and trip
  the assertion; it is overridden below to depend on ``recorder_mock``
  first instead, and is not needed by this test anyway since nothing here
  goes through HA's config-entry/component loader.
"""

from __future__ import annotations

import pytest
from homeassistant.components.logbook.helpers import LogbookConfig
from homeassistant.core import Context, HomeAssistant, ServiceCall
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)

from custom_components.pareto.importer import async_import_history
from custom_components.pareto.store import ParetoStore

USER = "69d919fb68524e7086650439297dd452"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(recorder_mock):
    """Override the conftest.py autouse fixture for this module only.

    This test never goes through HA's component loader (no config entry is
    set up), so custom-integration enabling is not needed -- but the
    original fixture's dependency on `hass` must not be allowed to win the
    race against `recorder_mock`'s dependency on `recorder_db_url`. See the
    module docstring.
    """
    yield


async def test_a_real_service_call_is_imported_through_the_real_event_processor(
    recorder_mock, hass: HomeAssistant
) -> None:
    """Fire one genuine service call, let the real recorder persist it, then
    run the real backfill path (async_determine_event_types + EventProcessor
    + get_instance(hass).async_add_executor_job) against it."""
    hass.data["logbook"] = LogbookConfig({}, None, None)

    async def _fake_turn_on(call: ServiceCall) -> None:
        # Mirrors what light.turn_on actually does: the resulting state
        # change carries the same context as the service call that caused
        # it, which is how the logbook can later attach context_domain /
        # context_service / context_user_id to the state-changed row.
        hass.states.async_set(call.data["entity_id"], "on", context=call.context)

    hass.services.async_register("light", "turn_on", _fake_turn_on)
    hass.states.async_set("light.a", "off")

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": "light.a"},
        blocking=True,
        context=Context(user_id=USER),
    )
    await async_wait_recording_done(hass)

    store = ParetoStore(hass)
    await store.async_load()
    written = await async_import_history(hass, store, days=1)

    assert written == 1
    usages = store.aggregated()
    assert [u.entity_id for u in usages] == ["light.a"]
    assert sum(usages[0].counts.values()) == 1
