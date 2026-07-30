"""Shared fixtures. auto_enable_custom_integrations is required by
pytest-homeassistant-custom-component before HA will load anything from
custom_components/."""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield
