from homeassistant import config_entries, data_entry_flow
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pareto.const import (
    CONF_HALF_LIFE_DAYS,
    CONF_PINNED_ENTITIES,
    CONF_RECENT_COUNT,
    CONF_TOP_COUNT,
    DOMAIN,
)


async def test_user_flow_creates_the_entry(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Pareto"


async def test_only_one_instance_is_allowed(hass):
    MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_options_flow_stores_values(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_TOP_COUNT: 7,
            CONF_RECENT_COUNT: 3,
            CONF_HALF_LIFE_DAYS: 21,
            CONF_PINNED_ENTITIES: [],
        },
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_TOP_COUNT] == 7
    assert result["data"][CONF_HALF_LIFE_DAYS] == 21
