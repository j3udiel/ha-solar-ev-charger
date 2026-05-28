"""Solar EV Charger Controller integration."""

from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    MODE_VALUES_BY_LABEL,
    MODES,
    OPT_MODE,
    PLATFORMS,
    SERVICE_RECALCULATE,
    SERVICE_SET_MODE,
    SERVICE_START,
    SERVICE_STOP,
)
from .coordinator import SolarEVChargerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Solar EV Charger Controller from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    coordinator = SolarEVChargerCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    if not hass.services.has_service(DOMAIN, SERVICE_START):
        _register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


def _register_services(hass: HomeAssistant) -> None:
    async def handle_start(call: ServiceCall) -> None:
        await _coordinator_from_call(hass, call).async_start_now()

    async def handle_stop(call: ServiceCall) -> None:
        await _coordinator_from_call(hass, call).async_stop_now()

    async def handle_recalculate(call: ServiceCall) -> None:
        await _coordinator_from_call(hass, call).async_recalculate_now()

    async def handle_set_mode(call: ServiceCall) -> None:
        mode = call.data["mode"]
        mode = MODE_VALUES_BY_LABEL.get(mode, mode)
        if mode not in MODES:
            raise HomeAssistantError(f"Unsupported mode: {mode}")
        await _coordinator_from_call(hass, call).async_set_option(OPT_MODE, mode)

    hass.services.async_register(DOMAIN, SERVICE_START, handle_start)
    hass.services.async_register(DOMAIN, SERVICE_STOP, handle_stop)
    hass.services.async_register(DOMAIN, SERVICE_RECALCULATE, handle_recalculate)
    hass.services.async_register(DOMAIN, SERVICE_SET_MODE, handle_set_mode)


def _coordinator_from_call(
    hass: HomeAssistant,
    call: ServiceCall,
) -> SolarEVChargerCoordinator:
    entry_id = call.data.get("config_entry_id")
    coordinators: dict[str, SolarEVChargerCoordinator] = hass.data.get(DOMAIN, {})

    if entry_id:
        coordinator = coordinators.get(entry_id)
        if coordinator is None:
            raise HomeAssistantError(f"No Solar EV Charger entry found for {entry_id}")
        return coordinator

    if len(coordinators) == 1:
        return next(iter(coordinators.values()))

    raise HomeAssistantError("config_entry_id is required when multiple controllers exist")


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries."""
    _LOGGER.debug("Migration not required for entry version %s", entry.version)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload on config entry update."""
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is not None and coordinator.suppress_next_entry_reload:
        coordinator.suppress_next_entry_reload = False
        return

    await hass.config_entries.async_reload(entry.entry_id)
