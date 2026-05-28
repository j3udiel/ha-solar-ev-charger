"""Sensor platform for Solar EV Charger Controller."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ControllerData, SolarEVChargerCoordinator


@dataclass(frozen=True, kw_only=True)
class SolarEVChargerSensorDescription(SensorEntityDescription):
    """Sensor description."""

    value_fn: Callable[[ControllerData], Any]


SENSORS: tuple[SolarEVChargerSensorDescription, ...] = (
    SolarEVChargerSensorDescription(
        key="available_surplus_w",
        translation_key="available_surplus_w",
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda data: round(data.available_surplus_w),
    ),
    SolarEVChargerSensorDescription(
        key="controllable_surplus_w",
        translation_key="controllable_surplus_w",
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda data: round(data.controllable_surplus_w),
    ),
    SolarEVChargerSensorDescription(
        key="current_charge_power_w",
        translation_key="current_charge_power_w",
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda data: round(data.current_charge_power_w),
    ),
    SolarEVChargerSensorDescription(
        key="grid_power_w",
        translation_key="grid_power_w",
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda data: round(data.grid_power_w),
    ),
    SolarEVChargerSensorDescription(
        key="grid_import_w",
        translation_key="grid_import_w",
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda data: round(data.import_w),
    ),
    SolarEVChargerSensorDescription(
        key="recommended_amps",
        translation_key="recommended_amps",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda data: data.recommended_amps,
    ),
    SolarEVChargerSensorDescription(
        key="current_state",
        translation_key="current_state",
        value_fn=lambda data: data.current_state,
    ),
    SolarEVChargerSensorDescription(
        key="last_action",
        translation_key="last_action",
        value_fn=lambda data: data.last_action,
    ),
    SolarEVChargerSensorDescription(
        key="reason",
        translation_key="reason",
        value_fn=lambda data: data.reason,
    ),
    SolarEVChargerSensorDescription(
        key="estimated_power_w",
        translation_key="estimated_power_w",
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda data: round(data.estimated_power_w),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator: SolarEVChargerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SolarEVChargerSensor(coordinator, description) for description in SENSORS
    )


class SolarEVChargerSensor(CoordinatorEntity[SolarEVChargerCoordinator], SensorEntity):
    """Solar EV Charger sensor."""

    entity_description: SolarEVChargerSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SolarEVChargerCoordinator,
        description: SolarEVChargerSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = coordinator.entity_unique_id(description.key)
        self._attr_suggested_object_id = f"solar_ev_charger_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> Any:
        """Return sensor state."""
        return self.entity_description.value_fn(self.coordinator.data)
