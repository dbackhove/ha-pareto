"""The websocket API behind the card.

These tests care about one thing above all: that the list a person is shown is
built from *their* usage and *their* preferences, and that neither leaks
across accounts.
"""

from datetime import datetime, timedelta, timezone

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pareto.const import CONF_PINNED_ENTITIES, DOMAIN

BERLIN = timezone(timedelta(hours=2))
OTHER_USER = "a3f1c2d4e5f6a7b8c9d0e1f2a3b4c5d6"
WHEN = datetime(2026, 7, 30, 12, 0, tzinfo=BERLIN)


async def setup_pareto(hass, options=None):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options=options or {}, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def store_of(hass, entry):
    return hass.data[DOMAIN][entry.entry_id].store


async def call(client, payload, msg_id):
    await client.send_json({"id": msg_id, **payload})
    return await client.receive_json()


async def get_lists(client, msg_id=1):
    return await call(client, {"type": "pareto/lists"}, msg_id)


async def test_lists_returns_the_callers_own_usage(hass, hass_ws_client, hass_admin_user):
    entry = await setup_pareto(hass)
    hass.states.async_set("light.a", "off")
    store_of(hass, entry).record("light.a", hass_admin_user.id, WHEN)

    client = await hass_ws_client(hass)
    msg = await get_lists(client)

    assert msg["success"]
    assert [e["entity_id"] for e in msg["result"]["top"]] == ["light.a"]
    assert msg["result"]["top"][0]["personal"] is True
    assert msg["result"]["top"][0]["count"] == 1


async def test_recent_omits_score_like_the_sensor(hass, hass_ws_client, hass_admin_user):
    entry = await setup_pareto(hass)
    hass.states.async_set("light.a", "off")
    store_of(hass, entry).record("light.a", hass_admin_user.id, WHEN)

    client = await hass_ws_client(hass)
    msg = await get_lists(client)

    assert "score" in msg["result"]["top"][0]
    assert "score" not in msg["result"]["recent"][0]


async def test_thin_history_is_padded_from_the_global_list(hass, hass_ws_client):
    """Somebody else's usage carries the list until the reader has their own."""
    entry = await setup_pareto(hass)
    hass.states.async_set("light.a", "off")
    store_of(hass, entry).record("light.a", OTHER_USER, WHEN)

    client = await hass_ws_client(hass)
    msg = await get_lists(client)

    assert [e["entity_id"] for e in msg["result"]["top"]] == ["light.a"]
    assert msg["result"]["top"][0]["personal"] is False


async def test_own_usage_outranks_the_padding(hass, hass_ws_client, hass_admin_user):
    entry = await setup_pareto(hass)
    store = store_of(hass, entry)
    for entity_id in ("light.mine", "light.theirs"):
        hass.states.async_set(entity_id, "off")

    store.record("light.mine", hass_admin_user.id, WHEN)
    for _ in range(50):  # far more usage, but by somebody else
        store.record("light.theirs", OTHER_USER, WHEN)

    client = await hass_ws_client(hass)
    msg = await get_lists(client)

    top = msg["result"]["top"]
    assert [e["entity_id"] for e in top] == ["light.mine", "light.theirs"]
    assert [e["personal"] for e in top] == [True, False]


async def test_hidden_entity_disappears_from_the_list(hass, hass_ws_client, hass_admin_user):
    entry = await setup_pareto(hass)
    hass.states.async_set("light.a", "off")
    store_of(hass, entry).record("light.a", hass_admin_user.id, WHEN)

    client = await hass_ws_client(hass)
    hidden = await call(
        client, {"type": "pareto/set_pref", "entity_id": "light.a", "hidden": True}, 1
    )
    assert hidden["success"]
    assert hidden["result"] == {"hidden": ["light.a"], "pinned": []}

    msg = await get_lists(client, 2)
    assert msg["result"]["top"] == []
    assert msg["result"]["hidden"] == ["light.a"]


async def test_hiding_beats_a_house_wide_pin(hass, hass_ws_client, hass_admin_user):
    """build_ranked_list walks pins past every filter. The one person who asked
    never to see this again must still get their way."""
    entry = await setup_pareto(hass, options={CONF_PINNED_ENTITIES: ["light.a"]})
    hass.states.async_set("light.a", "off")
    store_of(hass, entry).record("light.a", hass_admin_user.id, WHEN)

    client = await hass_ws_client(hass)
    before = await get_lists(client, 1)
    assert [e["entity_id"] for e in before["result"]["top"]] == ["light.a"]

    await call(client, {"type": "pareto/set_pref", "entity_id": "light.a", "hidden": True}, 2)
    after = await get_lists(client, 3)
    assert after["result"]["top"] == []


async def test_pinning_clears_hiding(hass, hass_ws_client):
    await setup_pareto(hass)
    hass.states.async_set("light.a", "off")
    client = await hass_ws_client(hass)

    await call(client, {"type": "pareto/set_pref", "entity_id": "light.a", "hidden": True}, 1)
    msg = await call(client, {"type": "pareto/set_pref", "entity_id": "light.a", "pinned": True}, 2)

    assert msg["result"] == {"hidden": [], "pinned": ["light.a"]}


async def test_hiding_clears_pinning(hass, hass_ws_client):
    await setup_pareto(hass)
    hass.states.async_set("light.a", "off")
    client = await hass_ws_client(hass)

    await call(client, {"type": "pareto/set_pref", "entity_id": "light.a", "pinned": True}, 1)
    msg = await call(client, {"type": "pareto/set_pref", "entity_id": "light.a", "hidden": True}, 2)

    assert msg["result"] == {"hidden": ["light.a"], "pinned": []}


async def test_a_pin_surfaces_an_entity_that_was_never_used(hass, hass_ws_client):
    await setup_pareto(hass)
    hass.states.async_set("light.never_touched", "off")
    client = await hass_ws_client(hass)

    await call(
        client, {"type": "pareto/set_pref", "entity_id": "light.never_touched", "pinned": True}, 1
    )
    msg = await get_lists(client, 2)

    top = msg["result"]["top"]
    assert [e["entity_id"] for e in top] == ["light.never_touched"]
    assert top[0]["pinned"] is True


async def test_prefs_do_not_leak_between_users(hass, hass_ws_client, hass_admin_user):
    entry = await setup_pareto(hass)
    store = store_of(hass, entry)
    hass.states.async_set("light.a", "off")
    store.record("light.a", hass_admin_user.id, WHEN)
    store.record("light.a", OTHER_USER, WHEN)

    client = await hass_ws_client(hass)
    await call(client, {"type": "pareto/set_pref", "entity_id": "light.a", "hidden": True}, 1)

    assert store.prefs(OTHER_USER) == {"hidden": [], "pinned": []}
    assert store.prefs(hass_admin_user.id)["hidden"] == ["light.a"]


async def test_set_pref_writes_under_the_connections_user(hass, hass_ws_client, hass_admin_user):
    """A user_id in the payload must not be able to redirect the write."""
    entry = await setup_pareto(hass)
    hass.states.async_set("light.a", "off")
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 1,
            "type": "pareto/set_pref",
            "entity_id": "light.a",
            "hidden": True,
            "user_id": OTHER_USER,
        }
    )
    msg = await client.receive_json()

    # The extra key is rejected outright by the schema; either way nothing may
    # land in the other user's preferences.
    assert store_of(hass, entry).prefs(OTHER_USER) == {"hidden": [], "pinned": []}
    if msg["success"]:
        assert store_of(hass, entry).prefs(hass_admin_user.id)["hidden"] == ["light.a"]


async def test_set_pref_rejects_an_unknown_entity(hass, hass_ws_client):
    await setup_pareto(hass)
    client = await hass_ws_client(hass)

    msg = await call(
        client, {"type": "pareto/set_pref", "entity_id": "light.ghost", "hidden": True}, 1
    )

    assert not msg["success"]
    assert msg["error"]["code"] == "unknown_entity"


async def test_set_pref_needs_hidden_or_pinned(hass, hass_ws_client):
    await setup_pareto(hass)
    hass.states.async_set("light.a", "off")
    client = await hass_ws_client(hass)

    msg = await call(client, {"type": "pareto/set_pref", "entity_id": "light.a"}, 1)

    assert not msg["success"]
    assert msg["error"]["code"] == "invalid_format"


async def test_hidden_list_omits_entities_that_are_gone(hass, hass_ws_client):
    """An entity that no longer exists cannot be restored meaningfully, and
    would show up in the card's edit mode as a nameless row."""
    await setup_pareto(hass)
    hass.states.async_set("light.a", "off")
    client = await hass_ws_client(hass)

    await call(client, {"type": "pareto/set_pref", "entity_id": "light.a", "hidden": True}, 1)
    hass.states.async_remove("light.a")

    msg = await get_lists(client, 2)
    assert msg["result"]["hidden"] == []


async def test_lists_reports_not_loaded_after_unload(hass, hass_ws_client):
    entry = await setup_pareto(hass)
    client = await hass_ws_client(hass)

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    msg = await get_lists(client)
    assert not msg["success"]
    assert msg["error"]["code"] == "not_loaded"
