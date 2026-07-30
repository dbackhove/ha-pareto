"""Serving the card from inside the integration.

HACS allows one category per repository, so the card cannot be a second,
Lovelace-category entry. It ships with the integration and registers itself.
"""

from unittest.mock import patch

from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
from pytest_homeassistant_custom_component.common import MockConfigEntry

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
