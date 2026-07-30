"""Config and options flows for Pareto."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_EXCLUDE_DOMAINS,
    CONF_EXCLUDE_ENTITIES,
    CONF_HALF_LIFE_DAYS,
    CONF_INCLUDE_DOMAINS,
    CONF_PINNED_ENTITIES,
    CONF_RECENT_COUNT,
    CONF_TOP_COUNT,
    DEFAULT_HALF_LIFE_DAYS,
    DEFAULT_RECENT_COUNT,
    DEFAULT_TOP_COUNT,
    DOMAIN,
)


def _count_selector(minimum: int, maximum: int) -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(min=minimum, max=maximum, step=1, mode=NumberSelectorMode.BOX)
    )


class ParetoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Single-step setup. Everything configurable lives in the options flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured(error="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="Pareto", data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return ParetoOptionsFlow()


class ParetoOptionsFlow(OptionsFlow):
    """Everything the user can tune, all on one page."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        options = self.config_entry.options
        domains = sorted(
            {state.entity_id.split(".", 1)[0] for state in self.hass.states.async_all()}
        )
        domain_selector = SelectSelector(
            SelectSelectorConfig(options=domains, multiple=True, mode=SelectSelectorMode.DROPDOWN)
        )
        entity_selector = EntitySelector(EntitySelectorConfig(multiple=True))

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_TOP_COUNT, default=options.get(CONF_TOP_COUNT, DEFAULT_TOP_COUNT)
                ): _count_selector(1, 50),
                vol.Optional(
                    CONF_RECENT_COUNT,
                    default=options.get(CONF_RECENT_COUNT, DEFAULT_RECENT_COUNT),
                ): _count_selector(1, 50),
                vol.Optional(
                    CONF_HALF_LIFE_DAYS,
                    default=options.get(CONF_HALF_LIFE_DAYS, DEFAULT_HALF_LIFE_DAYS),
                ): _count_selector(1, 90),
                vol.Optional(
                    CONF_INCLUDE_DOMAINS, default=options.get(CONF_INCLUDE_DOMAINS, [])
                ): domain_selector,
                vol.Optional(
                    CONF_EXCLUDE_DOMAINS, default=options.get(CONF_EXCLUDE_DOMAINS, [])
                ): domain_selector,
                vol.Optional(
                    CONF_EXCLUDE_ENTITIES, default=options.get(CONF_EXCLUDE_ENTITIES, [])
                ): entity_selector,
                vol.Optional(
                    CONF_PINNED_ENTITIES, default=options.get(CONF_PINNED_ENTITIES, [])
                ): entity_selector,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
