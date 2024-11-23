"""The tests for the switch fan platform."""

import pytest

from homeassistant.components.fan import (
    ATTR_PERCENTAGE,
    DOMAIN as FAN_DOMAIN,
    SERVICE_SET_PERCENTAGE as FAN_SERVICE_SET_PERCENTAGE,
    SERVICE_TURN_OFF as FAN_SERVICE_TURN_OFF,
    SERVICE_TURN_ON as FAN_SERVICE_TURN_ON,
)
from homeassistant.components.switch import (
    DOMAIN as SWITCH_DOMAIN,
    SERVICE_TURN_OFF as SWITCH_SERVICE_TURN_OFF,
)
from homeassistant.components.switch_fan.const import DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry, setup_test_component_platform
from tests.components.switch.common import MockSwitch

SWITCH_FAN = "fan.my_switch_fan"


@pytest.fixture
async def setup_hass(hass: HomeAssistant) -> None:
    """Initialize components."""
    assert await async_setup_component(hass, "homeassistant", {})
    await hass.async_block_till_done()


@pytest.fixture
async def mock_switch_entity_ids(
    hass: HomeAssistant, mock_switch_entities: list[MockSwitch]
) -> list[str]:
    """Mock switch entities and return their entity IDs."""
    setup_test_component_platform(hass, SWITCH_DOMAIN, mock_switch_entities)

    assert await async_setup_component(
        hass, SWITCH_DOMAIN, {"switch": {"platform": "test"}}
    )
    await hass.async_block_till_done()

    return [mse.entity_id for mse in mock_switch_entities]


@pytest.fixture
async def setup_config_entry(
    hass: HomeAssistant, mock_switch_entity_ids: list[str]
) -> MockConfigEntry:
    """Mock config entry."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "entities": mock_switch_entity_ids,
            "name": "My switch fan",
        },
        title="My switch fan",
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry


@pytest.mark.usefixtures("setup_hass")
@pytest.mark.usefixtures("setup_config_entry")
async def test_state(hass: HomeAssistant, mock_switch_entity_ids: list[str]) -> None:
    """Test handling of state.

    The switch fan state is on if at least one group member is on.
    Otherwise, the switch fan state is off.
    """
    state = hass.states.get(SWITCH_FAN)
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_PERCENTAGE) == 33

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SWITCH_SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: mock_switch_entity_ids},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(SWITCH_FAN)
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_PERCENTAGE) == 0


@pytest.mark.usefixtures("setup_hass")
@pytest.mark.usefixtures("setup_config_entry")
async def test_turn_off(hass: HomeAssistant, mock_switch_entity_ids: list[str]) -> None:
    """Test handling of state.

    The switch fan state is on if at least one group member is on.
    Otherwise, the switch fan state is off.
    """
    await hass.services.async_call(
        FAN_DOMAIN,
        FAN_SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: SWITCH_FAN},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(SWITCH_FAN)
    assert state.state == STATE_OFF

    assert all(
        hass.states.get(entity_id).state == STATE_OFF
        for entity_id in mock_switch_entity_ids
    )


@pytest.mark.parametrize(
    "mock_switch_entities",
    [
        [
            MockSwitch("switch.low", STATE_OFF),
            MockSwitch("switch.medium", STATE_OFF),
            MockSwitch("switch.high", STATE_OFF),
        ]
    ],
)
@pytest.mark.usefixtures("setup_hass")
@pytest.mark.usefixtures("setup_config_entry")
async def test_turn_on_when_off(
    hass: HomeAssistant, mock_switch_entity_ids: list[str]
) -> None:
    """Test handling of state.

    The switch fan state is on if at least one group member is on.
    Otherwise, the switch fan state is off.
    """
    state = hass.states.get(SWITCH_FAN)
    assert state.state == STATE_OFF

    await hass.services.async_call(
        FAN_DOMAIN,
        FAN_SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: SWITCH_FAN},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(SWITCH_FAN)
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_PERCENTAGE) == 33

    assert hass.states.get(mock_switch_entity_ids[0]).state == STATE_ON
    assert hass.states.get(mock_switch_entity_ids[1]).state == STATE_OFF
    assert hass.states.get(mock_switch_entity_ids[2]).state == STATE_OFF


@pytest.mark.usefixtures("setup_hass")
@pytest.mark.usefixtures("setup_config_entry")
async def test_turn_on_when_on(
    hass: HomeAssistant, mock_switch_entity_ids: list[str]
) -> None:
    """Test handling of state.

    The switch fan state is on if at least one group member is on.
    Otherwise, the switch fan state is off.
    """

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "entities": mock_switch_entity_ids,
            "name": "My switch fan",
        },
        title="My switch fan",
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(SWITCH_FAN)
    assert state.state == STATE_ON

    await hass.services.async_call(
        FAN_DOMAIN,
        FAN_SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: SWITCH_FAN},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(SWITCH_FAN)
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_PERCENTAGE) == 33

    assert hass.states.get(mock_switch_entity_ids[0]).state == STATE_ON
    assert hass.states.get(mock_switch_entity_ids[1]).state == STATE_OFF
    assert hass.states.get(mock_switch_entity_ids[2]).state == STATE_OFF


@pytest.mark.parametrize(
    "mock_switch_entities",
    [
        [
            MockSwitch("switch.low", STATE_OFF),
            MockSwitch("switch.medium", STATE_OFF),
            MockSwitch("switch.high", STATE_OFF),
        ]
    ],
)
@pytest.mark.usefixtures("setup_hass")
@pytest.mark.usefixtures("setup_config_entry")
async def test_turn_on_with_percentage(
    hass: HomeAssistant, mock_switch_entity_ids: list[str]
) -> None:
    """Test handling of state.

    The switch fan state is on if at least one group member is on.
    Otherwise, the switch fan state is off.
    """
    state = hass.states.get(SWITCH_FAN)
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_PERCENTAGE) == 0

    await hass.services.async_call(
        FAN_DOMAIN,
        FAN_SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: SWITCH_FAN, ATTR_PERCENTAGE: 66},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(SWITCH_FAN)
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_PERCENTAGE) == 66

    assert hass.states.get(mock_switch_entity_ids[0]).state == STATE_OFF
    assert hass.states.get(mock_switch_entity_ids[1]).state == STATE_ON
    assert hass.states.get(mock_switch_entity_ids[2]).state == STATE_OFF


@pytest.mark.usefixtures("setup_hass")
@pytest.mark.usefixtures("setup_config_entry")
async def test_set_percentage(
    hass: HomeAssistant, mock_switch_entity_ids: list[str]
) -> None:
    """Test handling of state.

    The switch fan state is on if at least one group member is on.
    Otherwise, the switch fan state is off.
    """
    state = hass.states.get(SWITCH_FAN)
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_PERCENTAGE) == 33

    await hass.services.async_call(
        FAN_DOMAIN,
        FAN_SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: SWITCH_FAN, ATTR_PERCENTAGE: 66},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(SWITCH_FAN)
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_PERCENTAGE) == 66

    assert hass.states.get(mock_switch_entity_ids[0]).state == STATE_OFF
    assert hass.states.get(mock_switch_entity_ids[1]).state == STATE_ON
    assert hass.states.get(mock_switch_entity_ids[2]).state == STATE_OFF

    await hass.services.async_call(
        FAN_DOMAIN,
        FAN_SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: SWITCH_FAN, ATTR_PERCENTAGE: 100},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(SWITCH_FAN)
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_PERCENTAGE) == 100

    assert hass.states.get(mock_switch_entity_ids[0]).state == STATE_OFF
    assert hass.states.get(mock_switch_entity_ids[1]).state == STATE_OFF
    assert hass.states.get(mock_switch_entity_ids[2]).state == STATE_ON

    await hass.services.async_call(
        FAN_DOMAIN,
        FAN_SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: SWITCH_FAN, ATTR_PERCENTAGE: 0},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(SWITCH_FAN)
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_PERCENTAGE) == 0

    assert hass.states.get(mock_switch_entity_ids[0]).state == STATE_OFF
    assert hass.states.get(mock_switch_entity_ids[1]).state == STATE_OFF
    assert hass.states.get(mock_switch_entity_ids[2]).state == STATE_OFF
