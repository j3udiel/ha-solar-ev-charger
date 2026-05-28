"""Binary sensor platform for Solar EV Charger Controller."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ControllerData, SolarEVChargerCoordinator


@dataclass(frozen=True, kw_only=True)
class SolarEVChargerBinarySensorDescription(BinarySensorEntityDescription):
    """Binary sensor description."""

    value_fn: Callable[[ControllerData], bool]


BINARY_SENSORS: tuple[SolarEVChargerBinarySensorDescription, ...] = (
    SolarEVChargerBinarySensorDescription(
        key="has_surplus",
        translation_key="has_surplus",
        value_fn=lambda data: data.has_surplus,
    ),
    SolarEVChargerBinarySensorDescription(
        key="in_cheap_hours",
        translation_key="in_cheap_hours",
        value_fn=lambda data: data.in_cheap_hours,
    ),
    SolarEVChargerBinarySensorDescription(
        key="in_solar_window",
        translation_key="in_solar_window",
        value_fn=lambda data: data.in_solar_window,
    ),
    SolarEVChargerBinarySensorDescription(
        key="home_battery_protected",
        translation_key="home_battery_protected",
        value_fn=lambda data: data.home_battery_protected,
    ),
    SolarEVChargerBinarySensorDescription(
        key="should_charge",
        translation_key="should_charge",
        value_fn=lambda data: data.should_charge,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    coordinator: SolarEVChargerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SolarEVChargerBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
    )


class SolarEVChargerBinarySensor(
    CoordinatorEntity[SolarEVChargerCoordinator],
    BinarySensorEntity,
):
    """Solar EV Charger binary sensor."""

    entity_description: SolarEVChargerBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SolarEVChargerCoordinator,
        description: SolarEVChargerBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = coordinator.entity_unique_id(description.key)
        self._attr_suggested_object_id = f"solar_ev_charger_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool:
        """Return binary state."""
        return self.entity_description.value_fn(self.coordinator.data)
