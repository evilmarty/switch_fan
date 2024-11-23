"""Test the Switch Fan integration."""

import pytest

from homeassistant.components.fan import FanEntityFeature
from homeassistant.components.switch_fan.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from tests.common import MockConfigEntry


@pytest.mark.parametrize("platform", ["fan"])
async def test_setup_and_remove_config_entry(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    platform: str,
) -> None:
    """Test setting up and removing a config entry."""
    switch_fan_entity_id = f"{platform}.my_switch_fan"

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "entities": ["switch.low", "switch.medium", "switch.high"],
            "name": "My switch fan",
        },
        title="My switch fan",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Check the entity is registered in the entity registry
    assert entity_registry.async_get(switch_fan_entity_id) is not None

    # Check the platform is setup correctly
    state = hass.states.get(switch_fan_entity_id)
    assert state.state == "off"
    assert state.attributes == {
        "friendly_name": "My switch fan",
        "percentage": 0,
        "percentage_step": 33.333333333333336,
        "preset_mode": None,
        "preset_modes": None,
        "supported_features": FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.SET_SPEED,
    }

    # Remove the config entry
    assert await hass.config_entries.async_remove(config_entry.entry_id)
    await hass.async_block_till_done()

    # Check the state and entity registry entry are removed
    assert hass.states.get(switch_fan_entity_id) is None
    assert entity_registry.async_get(switch_fan_entity_id) is None


# @pytest.mark.skip
# @pytest.mark.parametrize(("count", "domain"), [(1, "switch")])
# @pytest.mark.parametrize(
#     "config",
#     [
#         {
#             "switch": {
#                 "platform": DOMAIN,
#                 "sensors": {
#                     "state": {
#                         "value_template": "{{ states.sensor.test_sensor.state }}"
#                     },
#                 },
#             },
#             "template": [
#                 {
#                     "trigger": {"platform": "event", "event_type": "event_1"},
#                     "sensor": {
#                         "name": "top level",
#                         "state": "{{ trigger.event.data.source }}",
#                     },
#                 },
#                 {
#                     "sensor": {
#                         "name": "top level state",
#                         "state": "{{ states.sensor.top_level.state }} + 2",
#                     },
#                     "binary_sensor": {
#                         "name": "top level state",
#                         "state": "{{ states.sensor.top_level.state == 'init' }}",
#                     },
#                 },
#             ],
#         },
#     ],
# )
# @pytest.mark.usefixtures("start_ha")
# async def test_change_device(
#     hass: HomeAssistant,
#     device_registry: dr.DeviceRegistry,
#     config_entry_options: dict[str, str],
#     config_user_input: dict[str, str],
# ) -> None:
#     """Test the link between the device and the config entry.

#     Test, for each platform, that the device was linked to the
#     config entry and the link was removed when the device is
#     changed in the integration options.
#     """

#     # Configure devices registry
#     entry_device1 = MockConfigEntry()
#     entry_device1.add_to_hass(hass)
#     device1 = device_registry.async_get_or_create(
#         config_entry_id=entry_device1.entry_id,
#         identifiers={("test", "identifier_test1")},
#         connections={("mac", "20:31:32:33:34:01")},
#     )
#     entry_device2 = MockConfigEntry()
#     entry_device2.add_to_hass(hass)
#     device2 = device_registry.async_get_or_create(
#         config_entry_id=entry_device1.entry_id,
#         identifiers={("test", "identifier_test2")},
#         connections={("mac", "20:31:32:33:34:02")},
#     )
#     await hass.async_block_till_done()

#     device_id1 = device1.id
#     assert device_id1 is not None

#     device_id2 = device2.id
#     assert device_id2 is not None

#     # Setup the config entry
#     fan_config_entry = MockConfigEntry(
#         data={},
#         domain=DOMAIN,
#         options=config_entry_options | {"device_id": device_id1},
#         title="My Switch Fan",
#     )
#     fan_config_entry.add_to_hass(hass)
#     assert await hass.config_entries.async_setup(fan_config_entry.entry_id)
#     await hass.async_block_till_done()

#     # Confirm that the config entry has been added to the device 1 registry (current)
#     current_device = device_registry.async_get(device_id=device_id1)
#     assert fan_config_entry.entry_id in current_device.config_entries

#     # Change config options to use device 2 and reload the integration
#     result = await hass.config_entries.options.async_init(fan_config_entry.entry_id)
#     result = await hass.config_entries.options.async_configure(
#         result["flow_id"],
#         user_input=config_user_input | {"device_id": device_id2},
#     )
#     await hass.async_block_till_done()

#     # Confirm that the config entry has been removed from the device 1 registry
#     previous_device = device_registry.async_get(device_id=device_id1)
#     assert fan_config_entry.entry_id not in previous_device.config_entries

#     # Confirm that the config entry has been added to the device 2 registry (current)
#     current_device = device_registry.async_get(device_id=device_id2)
#     assert fan_config_entry.entry_id in current_device.config_entries

#     # Change the config options to remove the device and reload the integration
#     result = await hass.config_entries.options.async_init(fan_config_entry.entry_id)
#     result = await hass.config_entries.options.async_configure(
#         result["flow_id"],
#         user_input=config_user_input,
#     )
#     await hass.async_block_till_done()

#     # Confirm that the config entry has been removed from the device 2 registry
#     previous_device = device_registry.async_get(device_id=device_id2)
#     assert fan_config_entry.entry_id not in previous_device.config_entries

#     # Confirm that there is no device with the helper config entry
#     assert (
#         dr.async_entries_for_config_entry(device_registry, fan_config_entry.entry_id)
#         == []
#     )
