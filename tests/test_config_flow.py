"""Test the Switch Fan config flow."""

from unittest.mock import AsyncMock

import pytest

from homeassistant import config_entries
from homeassistant.components.switch_fan.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry

pytestmark = pytest.mark.usefixtures("mock_setup_entry")


@pytest.mark.parametrize("platform", ["fan"])
async def test_config_flow(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, platform
) -> None:
    """Test the config flow."""
    input_entity_ids = ["switch.low", "switch.medium", "switch.high"]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] is None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "My switch fan", "entities": input_entity_ids},
    )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "My switch fan"
    assert result["data"] == {}
    assert result["options"] == {
        "entities": input_entity_ids,
        "hide_members": False,
        "name": "My switch fan",
    }
    assert len(mock_setup_entry.mock_calls) == 1

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert config_entry.data == {}
    assert config_entry.options == {
        "entities": input_entity_ids,
        "hide_members": False,
        "name": "My switch fan",
    }
    assert config_entry.title == "My switch fan"


def get_suggested(schema, key):
    """Get suggested value for key in voluptuous schema."""
    for k in schema:
        if k == key:
            if k.description is None or "suggested_value" not in k.description:
                return None
            return k.description["suggested_value"]
    # Wanted key absent from schema
    raise KeyError(f"Key `{key}` is missing from schema")


@pytest.mark.parametrize("platform", ["fan"])
async def test_options(
    hass: HomeAssistant,
    platform,
) -> None:
    """Test reconfiguring."""
    hass.states.async_set("switch.low", "off")
    hass.states.async_set("switch.medium", "off")
    hass.states.async_set("switch.high", "off")

    input_entity_ids1 = ["switch.low", "switch.high"]
    input_entity_ids2 = ["switch.low", "switch.medium", "switch.high"]

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "entities": input_entity_ids1,
            "hide_members": False,
            "name": "My switch fan",
        },
        title="My switch fan",
    )

    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"
    schema = result["data_schema"].schema
    assert get_suggested(schema, "entities") == input_entity_ids1

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "entities": input_entity_ids2,
        },
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "entities": input_entity_ids2,
        "hide_members": False,
        "name": "My switch fan",
    }
    assert config_entry.data == {}
    assert config_entry.options == {
        "entities": input_entity_ids2,
        "hide_members": False,
        "name": "My switch fan",
    }
    assert config_entry.title == "My switch fan"

    # Check config entry is reloaded with new options
    await hass.async_block_till_done()

    # Check the entity was updated, no new entity was created
    assert len(hass.states.async_all()) == 4

    state = hass.states.get(f"{platform}.my_switch_fan")
    assert state.state == "off"
