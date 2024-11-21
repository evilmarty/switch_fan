import voluptuous as vol
from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlowResult,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.const import (
    CONF_ENTITIES,
    CONF_NAME,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import selector

from .const import DOMAIN


DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): str,
    vol.Required(CONF_ENTITIES): selector({
        "entity": {
            "filter": {
                "domain": ["switch", "light"],
            },
            "multiple": True,
        }
    }),
})


class SwitchFanConfigFlow(ConfigFlow, domain=DOMAIN):
    """Switch Fan Config Flow"""

    VERSION = 1
    MINOR_VERSION = 1
    
    async def async_step_user(self, user_input) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=user_input["name"],
                data={},
                options=user_input,
            )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SwitchFanOptionsFlowHandler(config_entry)


class SwitchFanOptionsFlowHandler(OptionsFlow):
    """Switch Fan Options Flow"""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry  # HA should be setting this but its not

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.config_entry, options=user_input
            )
            return self.async_create_entry(title=None, data=None)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                DATA_SCHEMA, self.config_entry.options
            ),
        )