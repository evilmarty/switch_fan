"""Config flow for Switch Fan integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

import voluptuous as vol

from homeassistant.components.input_boolean import DOMAIN as INPUT_BOOLEAN_DOMAIN
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_DEVICE_ID, CONF_ENTITIES, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
    SchemaFlowMenuStep,
)

from .const import DOMAIN

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITIES): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=[INPUT_BOOLEAN_DOMAIN, LIGHT_DOMAIN, SWITCH_DOMAIN],
                multiple=True,
            )
        ),
        vol.Optional(CONF_DEVICE_ID): selector.DeviceSelector(),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): selector.TextSelector(),
    }
).extend(OPTIONS_SCHEMA.schema)

CONFIG_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
    "user": SchemaFlowFormStep(CONFIG_SCHEMA)
}

OPTIONS_FLOW: dict[str, SchemaFlowFormStep | SchemaFlowMenuStep] = {
    "init": SchemaFlowFormStep(OPTIONS_SCHEMA)
}


class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle a config or options flow for Switch Fan."""

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""
        return cast(str, options[CONF_NAME]) if CONF_NAME in options else ""

    @callback
    def async_create_entry(
        self, data: Mapping[str, Any], **kwargs: Any
    ) -> ConfigFlowResult:
        """Finish config flow and create a config entry."""
        self._async_abort_entries_match({CONF_ENTITIES: data[CONF_ENTITIES]})
        return super().async_create_entry(data, **kwargs)
