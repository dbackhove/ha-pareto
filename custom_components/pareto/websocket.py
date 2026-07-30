"""WebSocket commands behind the Pareto card.

The card asks for a ranking once per visit to a dashboard view and does not
re-sort while it is on screen, so these are plain request/response commands
rather than a subscription: a push channel would spend its time delivering
reorderings the card is required to ignore.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .ranking import RankedEntity, build_ranked_list, merge_personal_and_global

ERR_NOT_LOADED = "not_loaded"
ERR_UNKNOWN_ENTITY = "unknown_entity"


@callback
def async_register(hass: HomeAssistant) -> None:
    """Register both commands.

    Called from ``async_setup`` rather than ``async_setup_entry``: command
    handlers are global and cannot be unregistered, so tying them to an entry
    that reloads on every options change would re-register them each time.
    """
    websocket_api.async_register_command(hass, websocket_lists)
    websocket_api.async_register_command(hass, websocket_set_pref)


@callback
def _runtime(hass: HomeAssistant) -> Any | None:
    """Return the single loaded entry's runtime, or None if there is none.

    Pareto is single-instance -- the config flow aborts a second entry -- so
    "the" runtime is unambiguous.
    """
    return next(iter(hass.data.get(DOMAIN, {}).values()), None)


@callback
def _ranked(runtime: Any, user_id: str, mode: str) -> list[tuple[RankedEntity, bool]]:
    """Rank one list for one person.

    Personal preferences are layered onto the same options the global
    sensors rank with, taken from the coordinator so the two cannot drift.
    """
    store = runtime.store
    coordinator = runtime.coordinator

    prefs = store.prefs(user_id)
    hidden = frozenset(prefs["hidden"])

    context = coordinator.ranking_context()
    context["exclude_entities"] = context["exclude_entities"] | hidden
    # Hiding beats a house-wide pin. build_ranked_list deliberately walks pins
    # past every filter, so without this subtraction a pinned entity would
    # outrank the wish of the one person who asked never to see it again --
    # and they would have no way to act on that from their own card.
    context["pinned"] = tuple(
        entity_id for entity_id in (*context["pinned"], *prefs["pinned"]) if entity_id not in hidden
    )

    limit = coordinator.limit_for(mode)
    personal = build_ranked_list(
        store.aggregated_for_user(user_id), mode=mode, limit=limit, **context
    )
    fallback = build_ranked_list(store.aggregated(), mode=mode, limit=limit, **context)
    return merge_personal_and_global(personal, fallback, limit)


def _as_row(entry: RankedEntity, personal: bool, mode: str) -> dict[str, Any]:
    """Render one entry for the wire, matching what the sensors publish."""
    row = asdict(entry)
    if mode == "recent":
        row.pop("score", None)
    row["personal"] = personal
    return row


@websocket_api.websocket_command({vol.Required("type"): "pareto/lists"})
@callback
def websocket_lists(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Send both lists, ranked for the person who asked.

    Both come back in one response so that two cards on one view do not cost
    two round trips.
    """
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], ERR_NOT_LOADED, "Pareto is not set up")
        return

    user_id = connection.user.id
    hidden = runtime.store.prefs(user_id)["hidden"]

    connection.send_result(
        msg["id"],
        {
            "top": [_as_row(e, p, "top") for e, p in _ranked(runtime, user_id, "top")],
            "recent": [_as_row(e, p, "recent") for e, p in _ranked(runtime, user_id, "recent")],
            # Entities that have since disappeared would show up in the card's
            # edit mode as unrestorable rows with no name.
            "hidden": [e for e in hidden if hass.states.get(e) is not None],
        },
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "pareto/set_pref",
        vol.Required("entity_id"): cv.entity_id,
        vol.Optional("hidden"): bool,
        vol.Optional("pinned"): bool,
    }
)
@callback
def websocket_set_pref(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Hide or pin one entity, for the caller only.

    No admin check: this writes nothing outside the caller's own preferences.
    The user id comes from the authenticated connection and never from the
    payload -- accepting one there would let any signed-in account rewrite
    somebody else's list.
    """
    runtime = _runtime(hass)
    if runtime is None:
        connection.send_error(msg["id"], ERR_NOT_LOADED, "Pareto is not set up")
        return

    if "hidden" not in msg and "pinned" not in msg:
        connection.send_error(
            msg["id"],
            websocket_api.ERR_INVALID_FORMAT,
            "Either hidden or pinned is required",
        )
        return

    entity_id = msg["entity_id"]
    if hass.states.get(entity_id) is None:
        connection.send_error(msg["id"], ERR_UNKNOWN_ENTITY, f"Unknown entity {entity_id}")
        return

    prefs = runtime.store.set_pref(
        connection.user.id,
        entity_id,
        hidden=msg.get("hidden"),
        pinned=msg.get("pinned"),
    )
    connection.send_result(msg["id"], prefs)
