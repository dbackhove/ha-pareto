"""Serving the card from inside the integration.

HACS allows one category per repository, so the card cannot be a second,
Lovelace-category entry. It ships with the integration and registers itself.

Registration happens twice over, by design: an extra module url and a
Lovelace resource. The second one is what reaches a client holding a cached
index page -- the iOS companion app above all. See
`_async_register_card_resource`.
"""

from unittest.mock import patch

from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
from homeassistant.components.lovelace.const import LOVELACE_DATA, MODE_YAML
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pareto import _async_register_card_resource
from custom_components.pareto.const import CARD_URL, DOMAIN


async def setup_pareto(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def registered_urls(hass):
    return hass.data[DATA_EXTRA_MODULE_URL].urls


async def test_the_card_is_registered_with_the_frontend(hass):
    await setup_pareto(hass)
    assert any(url.startswith(CARD_URL) for url in registered_urls(hass))


async def test_the_url_carries_a_cache_buster(hass):
    """Without it a browser keeps the previous bundle after an upgrade."""
    await setup_pareto(hass)
    url = next(url for url in registered_urls(hass) if url.startswith(CARD_URL))
    assert "?v=" in url


async def test_setup_survives_a_missing_bundle(hass):
    """A source checkout that was never built still has working sensors."""
    with patch("custom_components.pareto.CARD_FILENAME", "never-built.js"):
        await setup_pareto(hass)

    assert hass.states.get("sensor.pareto_top") is not None
    assert not any(url.startswith(CARD_URL) for url in registered_urls(hass))
    assert card_resources(hass) == []


def card_resources(hass):
    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None:
        return []
    return [
        item
        for item in lovelace.resources.async_items()
        if str(item.get("url", "")).startswith(CARD_URL)
    ]


async def test_the_card_is_registered_as_a_lovelace_resource(hass):
    """The path that actually reaches a client with a cached index page.

    An extra module url alone is rendered into the index page, which such a
    client never re-fetches, so it never learns the card exists and shows
    "Custom element doesn't exist: pareto-card" for every one of them. The
    resource travels over the websocket on each dashboard load instead.
    Asserted on the stored collection rather than on a mock, since what
    matters is that the entry survives in Lovelace's own storage.
    """
    await setup_pareto(hass)

    resources = card_resources(hass)
    assert len(resources) == 1
    assert resources[0]["type"] == "module"
    assert "?v=" in resources[0]["url"]


async def test_a_stale_resource_is_corrected_rather_than_duplicated(hass):
    """A hand-added resource carrying an outdated cache-busting tag.

    Left alone it pins clients to a version that was never installed; added
    beside, the card would load twice under two cache entries and the stale
    one would keep winning on some clients.
    """
    assert await async_setup_component(hass, "lovelace", {})
    collection = hass.data[LOVELACE_DATA].resources
    await collection.async_load()
    collection.loaded = True
    await collection.async_create_item({"res_type": "module", "url": f"{CARD_URL}?v=deadbee"})

    await setup_pareto(hass)

    resources = card_resources(hass)
    assert len(resources) == 1
    assert resources[0]["url"] != f"{CARD_URL}?v=deadbee"
    assert "?v=" in resources[0]["url"]


async def test_registering_the_same_url_twice_does_not_duplicate_it(hass):
    """Upgrades and restarts must not accumulate resources for one card.

    Exercises the registration directly rather than running setup twice:
    `async_setup` runs once per Home Assistant start, and a second call would
    fail earlier, on the static route, for reasons unrelated to what is being
    pinned here.
    """
    await setup_pareto(hass)
    assert len(card_resources(hass)) == 1
    url = card_resources(hass)[0]["url"]

    await _async_register_card_resource(hass, url)

    assert len(card_resources(hass)) == 1
    assert card_resources(hass)[0]["url"] == url


async def test_yaml_resource_mode_is_left_alone(hass):
    """YAML mode owns its resource list; writing to the collection raises."""
    assert await async_setup_component(hass, "lovelace", {})
    hass.data[LOVELACE_DATA].resource_mode = MODE_YAML

    await setup_pareto(hass)

    assert card_resources(hass) == []
