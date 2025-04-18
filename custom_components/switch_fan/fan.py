"""Fan platform for Switch Fan integration."""

from __future__ import annotations

import math
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_STATE,
    CONF_DEVICE_ID,
    CONF_ENTITIES,
    CONF_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device import async_device_info_to_link_from_device_id
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    Event,
    EventStateChangedData,
    async_track_state_change_event,
)
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Switch Fan config entry."""
    registry = er.async_get(hass)
    # Validate + resolve entity registry id to entity_id
    entity_ids = [
        er.async_validate_entity_id(registry, entity_id)
        for entity_id in config_entry.options[CONF_ENTITIES]
    ]
    name = config_entry.title
    unique_id = config_entry.entry_id
    device_info = async_device_info_to_link_from_device_id(
        hass,
        config_entry.options.get(CONF_DEVICE_ID),
    )

    async_add_entities(
        [
            SwitchFan(
                unique_id=unique_id,
                name=name,
                entity_ids=entity_ids,
                device_info=device_info,
            )
        ]
    )


class SwitchFan(FanEntity):
    """Switch Fan entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        unique_id: str,
        name: str,
        entity_ids: list[str],
        device_info: DeviceInfo | None,
    ) -> None:
        """Initialize the fan entity."""
        features = FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        # If we have more than 1 entity then we can set multiple speeds
        if len(entity_ids) > 1:
            features |= FanEntityFeature.SET_SPEED
        self.entity_ids = entity_ids
        self.entity_states = {}
        self._attr_unique_id = unique_id
        self._attr_name = name
        self._attr_speed_count = len(entity_ids)
        self._attr_supported_features = features
        self._attr_device_info = device_info

    async def call_service(self, service_name: str, entity_ids: list[str]) -> None:
        """Call service for the given entity IDs.

        Batches entities by their domain to minimize service calls.
        """
        groups = {}
        for entity_id in entity_ids:
            domain, *_ = entity_id.split(".", 1)
            if domain in groups:
                groups[domain].add(entity_id)
            else:
                groups[domain] = {
                    entity_id,
                }
        for domain, sub_entity_ids in groups.items():
            await self.hass.services.async_call(
                domain=domain,
                service=service_name,
                service_data={
                    CONF_ENTITY_ID: sub_entity_ids,
                },
            )

    def refresh_entity_states(self):
        """Refresh entity states."""
        self.entity_states = {
            entity_id: getattr(self.hass.states.get(entity_id), ATTR_STATE, None)
            for entity_id in self.entity_ids
        }
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Entity added to HASS."""
        self.refresh_entity_states()
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                self.entity_ids,
                self.async_update_event_state_callback,
            )
        )

    @callback
    def async_update_event_state_callback(self, event: Event[EventStateChangedData]):
        """Watched entity's state has changed."""
        entity_id = event.data["entity_id"]
        self.entity_states[entity_id] = event.data["new_state"].state
        self.async_write_ha_state()

    @property
    def percentage(self) -> int | None:
        """Calculate the fan speed percentage based off entity states.

        The entity that is ON is deemed the active entity. It's index in the
        list of entities is used to determine the speed percentage.
        """
        if len(self.entity_states) != len(self.entity_ids):
            return None
        active_id = next(
            (
                entity_id
                for entity_id, state in self.entity_states.items()
                if state == STATE_ON
            ),
            None,
        )
        if active_id is None:
            return 0
        speed_index = self.entity_ids.index(active_id) + 1
        return ranged_value_to_percentage(self.speed_range, speed_index)

    @property
    def speed_range(self) -> tuple[int, int]:
        """Speed range."""
        return (1, self.speed_count)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the fan speed by percentage.

        The percentage is converted to a index used to select the active
        entity from the list of entities.
        """
        if percentage == 0:
            await self.async_turn_off()
            return
        value = math.ceil(percentage_to_ranged_value(self.speed_range, percentage))
        index = value - 1
        entity_id = self.entity_ids[index]
        await self.call_service(SERVICE_TURN_ON, [entity_id])
        await self.call_service(
            SERVICE_TURN_OFF,
            [eid for eid in self.entity_ids if eid != entity_id],
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan.

        Turns off all entities.
        """
        await self.call_service(SERVICE_TURN_OFF, self.entity_ids)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan.

        If a percentage is given then the fan speed is set to that. Otherwise
        the first entity is turned on.
        """
        if percentage is not None:
            await self.async_set_percentage(percentage)
        elif self.is_on:
            # If we're on then do nothing
            return
        else:
            await self.async_increase_speed()
