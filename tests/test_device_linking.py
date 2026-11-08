"""Test device association without deprecated device-linking helpers."""

import logging
from typing import Any

import pytest

from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_DEVICE_ID,
    CONF_ENTITIES,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.switch_fan.const import CONF_HIDE_MEMBERS, DOMAIN

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


def create_source_device(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry, identifier: str
) -> dr.DeviceEntry:
    """Create a device owned by a source integration."""
    source_entry = MockConfigEntry(domain="test")
    source_entry.add_to_hass(hass)
    return device_registry.async_get_or_create(
        config_entry_id=source_entry.entry_id,
        identifiers={("test", identifier)},
        name=identifier,
    )


@pytest.mark.parametrize("selection", ["device", "none", "missing"])
async def test_setup_device_link(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    caplog: pytest.LogCaptureFixture,
    selection: str,
) -> None:
    """Remove stale helper devices and link only to an existing source device."""
    source_device = create_source_device(hass, device_registry, "source")
    options: dict[str, Any] = {
        CONF_ENTITIES: ["switch.low"],
        CONF_HIDE_MEMBERS: False,
    }
    if selection != "none":
        options[CONF_DEVICE_ID] = (
            source_device.id if selection == "device" else "missing-device"
        )
    entry = MockConfigEntry(domain=DOMAIN, title="My switch fan", options=options)
    entry.add_to_hass(hass)
    stale_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "stale")},
    )
    other_stale_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "other-stale")},
    )
    fan_entry = entity_registry.async_get_or_create(
        "fan", DOMAIN, entry.entry_id, device_id=stale_device.id
    )

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert device_registry.async_get(stale_device.id) is None
    assert device_registry.async_get(other_stale_device.id) is None
    assert device_registry.async_get(source_device.id) == source_device
    assert dr.async_entries_for_config_entry(device_registry, entry.entry_id) == []
    fan_entry = entity_registry.async_get(fan_entry.entity_id)
    assert fan_entry is not None
    assert fan_entry.device_id == (source_device.id if selection == "device" else None)
    assert hass.states.get(fan_entry.entity_id) is not None
    assert not any(
        record.name == "homeassistant.helpers.frame"
        and record.levelno >= logging.WARNING
        and "custom integration 'switch_fan'" in record.getMessage()
        and "deprecated" in record.getMessage()
        for record in caplog.records
    )


async def test_change_and_remove_device_link(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Reloading the helper updates its entity without co-owning source devices."""
    first_device = create_source_device(hass, device_registry, "first")
    second_device = create_source_device(hass, device_registry, "second")
    base_options: dict[str, Any] = {
        CONF_ENTITIES: ["switch.low"],
        CONF_HIDE_MEMBERS: False,
    }
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="My switch fan",
        options={**base_options, CONF_DEVICE_ID: first_device.id},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    entity_id = entity_registry.async_get_entity_id("fan", DOMAIN, entry.entry_id)
    assert entity_id is not None
    assert entity_registry.async_get(entity_id).device_id == first_device.id

    for device_id in (second_device.id, None):
        options = dict(base_options)
        if device_id is not None:
            options[CONF_DEVICE_ID] = device_id
        hass.config_entries.async_update_entry(entry, options=options)
        await hass.async_block_till_done()

        assert entity_registry.async_get(entity_id).device_id == device_id
        assert dr.async_entries_for_config_entry(device_registry, entry.entry_id) == []
        assert device_registry.async_get(first_device.id) == first_device
        assert device_registry.async_get(second_device.id) == second_device


async def test_linked_fan_controls(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Linking a device preserves speed selection and switch service calls."""
    source_device = create_source_device(hass, device_registry, "source")
    switch_ids = ["switch.low", "switch.medium", "switch.high"]
    for entity_id in switch_ids:
        hass.states.async_set(entity_id, STATE_OFF)

    @callback
    def handle_switch_service(call: ServiceCall) -> None:
        for entity_id in call.data[ATTR_ENTITY_ID]:
            hass.states.async_set(
                entity_id, STATE_ON if call.service == SERVICE_TURN_ON else STATE_OFF
            )

    for service in (SERVICE_TURN_ON, SERVICE_TURN_OFF):
        hass.services.async_register("switch", service, handle_switch_service)

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="My switch fan",
        options={
            CONF_ENTITIES: switch_ids,
            CONF_HIDE_MEMBERS: False,
            CONF_DEVICE_ID: source_device.id,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    entity_id = entity_registry.async_get_entity_id("fan", DOMAIN, entry.entry_id)
    assert entity_id is not None

    for service, data, percentage, active_index in (
        (SERVICE_TURN_ON, {}, 33, 0),
        ("set_percentage", {"percentage": 66}, 66, 1),
        ("set_percentage", {"percentage": 100}, 100, 2),
        (SERVICE_TURN_OFF, {}, 0, None),
    ):
        await hass.services.async_call(
            "fan", service, {ATTR_ENTITY_ID: entity_id, **data}, blocking=True
        )
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == (STATE_ON if active_index is not None else STATE_OFF)
        assert state.attributes["percentage"] == percentage
        assert [
            hass.states.get(switch_id).state for switch_id in switch_ids
        ] == [
            STATE_ON if index == active_index else STATE_OFF for index in range(3)
        ]
        assert entity_registry.async_get(entity_id).device_id == source_device.id
