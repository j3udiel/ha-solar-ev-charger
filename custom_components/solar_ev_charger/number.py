"""Number platform for Solar EV Charger Controller."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent, UnitOfPower, UnitOfElectricPotential
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    OPT_HOME_BATTERY_MIN_SOC,
    OPT_MAX_AMPS,
    OPT_MAX_GRID_IMPORT_W,
    OPT_MIN_AMPS,
    OPT_MIN_SURPLUS_W,
    OPT_SAFETY_MARGIN_W,
    OPT_TARGET_CAR_SOC,
    OPT_VOLTAGE,
)
from .coordinator import SolarEVChargerCoordinator


@dataclass(frozen=True, kw_only=True)
class SolarEVChargerNumberDescription(NumberEntityDescription):
    """Number description."""

    option_key: str


NUMBERS: tuple[SolarEVChargerNumberDescription, ...] = (
    SolarEVChargerNumberDescription(
        key="min_amps",
        translation_key="min_amps",
        option_key=OPT_MIN_AMPS,
        native_min_value=1,
        native_max_value=64,
        native_step=1,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    ),
    SolarEVChargerNumberDescription(
        key="max_amps",
        translation_key="max_amps",
        option_key=OPT_MAX_AMPS,
        native_min_value=1,
        native_max_value=64,
        native_step=1,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    ),
    SolarEVChargerNumberDescription(
        key="safety_margin_w",
        translation_key="safety_margin_w",
        option_key=OPT_SAFETY_MARGIN_W,
        native_min_value=0,
        native_max_value=5000,
        native_step=50,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    SolarEVChargerNumberDescription(
        key="min_surplus_w",
        translation_key="min_surplus_w",
        option_key=OPT_MIN_SURPLUS_W,
        native_min_value=0,
        native_max_value=22000,
        native_step=50,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    SolarEVChargerNumberDescription(
        key="target_car_soc",
        translation_key="target_car_soc",
        option_key=OPT_TARGET_CAR_SOC,
        native_min_value=1,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
    ),
    SolarEVChargerNumberDescription(
        key="home_battery_min_soc",
        translation_key="home_battery_min_soc",
        option_key=OPT_HOME_BATTERY_MIN_SOC,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
    ),
    SolarEVChargerNumberDescription(
        key="max_grid_import_w",
        translation_key="max_grid_import_w",
        option_key=OPT_MAX_GRID_IMPORT_W,
        native_min_value=0,
        native_max_value=22000,
        native_step=50,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    SolarEVChargerNumberDescription(
        key="voltage",
        translation_key="voltage",
        option_key=OPT_VOLTAGE,
        native_min_value=100,
        native_max_value=260,
        native_step=1,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up numbers."""
    coordinator: SolarEVChargerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SolarEVChargerNumber(coordinator, description) for description in NUMBERS
    )


class SolarEVChargerNumber(CoordinatorEntity[SolarEVChargerCoordinator], NumberEntity):
    """Solar EV Charger number."""

    entity_description: SolarEVChargerNumberDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SolarEVChargerCoordinator,
        description: SolarEVChargerNumberDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = coordinator.entity_unique_id(description.key)
        self._attr_suggested_object_id = f"solar_ev_charger_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float:
        """Return current value."""
        return float(self.coordinator.options[self.entity_description.option_key])

    async def async_set_native_value(self, value: float) -> None:
        """Update value."""
        await self.coordinator.async_set_option(
            self.entity_description.option_key,
            int(value),
        )
