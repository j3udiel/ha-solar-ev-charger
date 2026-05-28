"""Switch platform for Solar EV Charger Controller."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    OPT_ALLOW_GRID_IMPORT,
    OPT_ALLOW_HOME_BATTERY,
    OPT_ENABLED,
    OPT_NEED_CAR_TOMORROW,
)
from .coordinator import SolarEVChargerCoordinator


@dataclass(frozen=True, kw_only=True)
class SolarEVChargerSwitchDescription(SwitchEntityDescription):
    """Switch description."""

    option_key: str


SWITCHES: tuple[SolarEVChargerSwitchDescription, ...] = (
    SolarEVChargerSwitchDescription(
        key="enabled",
        translation_key="enabled",
        option_key=OPT_ENABLED,
    ),
    SolarEVChargerSwitchDescription(
        key="need_car_tomorrow",
        translation_key="need_car_tomorrow",
        option_key=OPT_NEED_CAR_TOMORROW,
    ),
    SolarEVChargerSwitchDescription(
        key="allow_grid_import",
        translation_key="allow_grid_import",
        option_key=OPT_ALLOW_GRID_IMPORT,
    ),
    SolarEVChargerSwitchDescription(
        key="allow_home_battery",
        translation_key="allow_home_battery",
        option_key=OPT_ALLOW_HOME_BATTERY,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switches."""
    coordinator: SolarEVChargerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SolarEVChargerSwitch(coordinator, description) for description in SWITCHES
    )


class SolarEVChargerSwitch(CoordinatorEntity[SolarEVChargerCoordinator], SwitchEntity):
    """Solar EV Charger switch."""

    entity_description: SolarEVChargerSwitchDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SolarEVChargerCoordinator,
        description: SolarEVChargerSwitchDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = coordinator.entity_unique_id(description.key)
        self._attr_suggested_object_id = f"solar_ev_charger_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool:
        """Return switch state."""
        return bool(self.coordinator.options[self.entity_description.option_key])

    async def async_turn_on(self, **kwargs) -> None:
        """Turn switch on."""
        await self.coordinator.async_set_option(self.entity_description.option_key, True)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn switch off."""
        await self.coordinator.async_set_option(self.entity_description.option_key, False)
