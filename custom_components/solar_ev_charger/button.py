"""Button platform for Solar EV Charger Controller."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SolarEVChargerCoordinator


@dataclass(frozen=True, kw_only=True)
class SolarEVChargerButtonDescription(ButtonEntityDescription):
    """Button description."""

    press_fn: Callable[[SolarEVChargerCoordinator], Awaitable[None]]


BUTTONS: tuple[SolarEVChargerButtonDescription, ...] = (
    SolarEVChargerButtonDescription(
        key="start_now",
        translation_key="start_now",
        press_fn=lambda coordinator: coordinator.async_start_now(),
    ),
    SolarEVChargerButtonDescription(
        key="stop_now",
        translation_key="stop_now",
        press_fn=lambda coordinator: coordinator.async_stop_now(),
    ),
    SolarEVChargerButtonDescription(
        key="recalculate",
        translation_key="recalculate",
        press_fn=lambda coordinator: coordinator.async_recalculate_now(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up buttons."""
    coordinator: SolarEVChargerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        SolarEVChargerButton(coordinator, description) for description in BUTTONS
    )


class SolarEVChargerButton(CoordinatorEntity[SolarEVChargerCoordinator], ButtonEntity):
    """Solar EV Charger button."""

    entity_description: SolarEVChargerButtonDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SolarEVChargerCoordinator,
        description: SolarEVChargerButtonDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = coordinator.entity_unique_id(description.key)
        self._attr_suggested_object_id = f"solar_ev_charger_{description.key}"
        self._attr_device_info = coordinator.device_info

    async def async_press(self) -> None:
        """Press button."""
        await self.entity_description.press_fn(self.coordinator)
