"""Select platform for Solar EV Charger Controller."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODE_LABELS, MODE_VALUES_BY_LABEL, OPT_MODE
from .coordinator import SolarEVChargerCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities."""
    coordinator: SolarEVChargerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SolarEVChargerModeSelect(coordinator)])


class SolarEVChargerModeSelect(
    CoordinatorEntity[SolarEVChargerCoordinator],
    SelectEntity,
):
    """Charge mode select."""

    _attr_has_entity_name = True
    _attr_translation_key = "mode"
    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator: SolarEVChargerCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.entity_unique_id("mode")
        self._attr_suggested_object_id = "solar_ev_charger_mode"
        self._attr_device_info = coordinator.device_info
        self._attr_options = list(MODE_LABELS.values())

    @property
    def current_option(self) -> str:
        """Return selected mode."""
        return MODE_LABELS[str(self.coordinator.options[OPT_MODE])]

    async def async_select_option(self, option: str) -> None:
        """Select mode."""
        await self.coordinator.async_set_option(OPT_MODE, MODE_VALUES_BY_LABEL[option])
