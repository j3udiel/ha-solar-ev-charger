"""Coordinator and control logic for Solar EV Charger Controller."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
import logging
import math
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CAR_SOC_SENSOR,
    CONF_CHARGE_AMPS_ENTITY,
    CONF_CHARGER_ENABLE_SWITCH,
    CONF_GRID_POWER_INVERTED,
    CONF_GRID_POWER_SENSOR,
    CONF_HOME_BATTERY_POWER_INVERTED,
    CONF_HOME_BATTERY_POWER_SENSOR,
    CONF_HOME_BATTERY_SOC_SENSOR,
    CONF_START_CHARGE_ENTITY,
    CONF_STOP_CHARGE_ENTITY,
    DEFAULT_OPTIONS,
    DOMAIN,
    MODE_CHEAP_HOURS,
    MODE_FORCE_CHARGE,
    MODE_HYBRID,
    MODE_MANUAL,
    MODE_OFF,
    MODE_SOLAR_ONLY,
    MODES,
    OPT_ALLOW_GRID_IMPORT,
    OPT_ALLOW_HOME_BATTERY,
    OPT_CHEAP_HOURS_ALL_WEEKEND,
    OPT_CHEAP_HOURS_END,
    OPT_CHEAP_HOURS_START,
    OPT_ENABLED,
    OPT_HOME_BATTERY_MIN_SOC,
    OPT_MAX_AMPS,
    OPT_MAX_GRID_IMPORT_W,
    OPT_MIN_ACTION_INTERVAL,
    OPT_MIN_AMPS,
    OPT_MIN_SURPLUS_W,
    OPT_MODE,
    OPT_NEED_CAR_TOMORROW,
    OPT_READY_BY_TIME,
    OPT_SAFETY_MARGIN_W,
    OPT_SOLAR_WINDOW_END,
    OPT_SOLAR_WINDOW_START,
    OPT_SURPLUS_OFF_DURATION,
    OPT_SURPLUS_ON_DURATION,
    OPT_TARGET_CAR_SOC,
    OPT_UPDATE_INTERVAL,
    OPT_VOLTAGE,
    STATE_CHARGING_CHEAP,
    STATE_CHARGING_FORCED,
    STATE_CHARGING_SOLAR,
    STATE_ERROR,
    STATE_IDLE,
    STATE_MANUAL,
    STATE_OFF,
    STATE_PAUSED_HOME_BATTERY_PROTECTION,
    STATE_PAUSED_NO_SURPLUS,
    STATE_PAUSED_OUTSIDE_SCHEDULE,
    STATE_WAITING_FOR_SURPLUS,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class ControllerData:
    """Current calculated controller state."""

    available_surplus_w: float = 0
    controllable_surplus_w: float = 0
    grid_power_w: float = 0
    import_w: float = 0
    current_charge_power_w: float = 0
    recommended_amps: int = 0
    current_state: str = STATE_IDLE
    last_action: str = "none"
    reason: str = "Controller initialized"
    estimated_power_w: float = 0
    has_surplus: bool = False
    in_cheap_hours: bool = False
    in_solar_window: bool = False
    home_battery_protected: bool = False
    should_charge: bool = False
    is_charging: bool = False


class SolarEVChargerCoordinator(DataUpdateCoordinator[ControllerData]):
    """Main controller loop."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.config_entry = entry
        self.options: dict[str, Any] = {**DEFAULT_OPTIONS, **dict(entry.options)}
        self._last_action_time: datetime | None = None
        self._last_amps_update_time: datetime | None = None
        self._surplus_since: datetime | None = None
        self._no_surplus_since: datetime | None = None
        self._controlled_charging = False
        self._last_set_amps: int | None = None
        self.suppress_next_entry_reload = False

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=int(self.options[OPT_UPDATE_INTERVAL])),
        )
        self.data = ControllerData()

    async def async_set_option(self, key: str, value: Any) -> None:
        """Persist and apply a controller option."""
        if key == OPT_MODE and value not in MODES:
            raise ValueError(f"Unsupported mode: {value}")

        self.options[key] = value
        new_options = {**dict(self.config_entry.options), key: value}
        self.suppress_next_entry_reload = True
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            options=new_options,
        )
        self.update_interval = timedelta(seconds=int(self.options[OPT_UPDATE_INTERVAL]))
        await self.async_request_refresh()

    async def async_start_now(self) -> None:
        """Manually request start charge."""
        await self._set_charge_amps(int(self.options[OPT_MAX_AMPS]), force=True)
        await self._start_charging("Manual start requested", force=True)
        await self.async_request_refresh()

    async def async_stop_now(self) -> None:
        """Manually request stop charge."""
        await self._stop_charging("Manual stop requested", force=True)
        await self.async_request_refresh()

    async def async_recalculate_now(self) -> None:
        """Trigger a recalculation."""
        await self.async_request_refresh()

    async def _async_update_data(self) -> ControllerData:
        now = dt_util.now()
        data = ControllerData(last_action=self.data.last_action if self.data else "none")

        try:
            grid_power = self._required_float(self.config_entry.data[CONF_GRID_POWER_SENSOR])
        except ValueError as err:
            data.current_state = STATE_ERROR
            data.reason = str(err)
            return data

        data.grid_power_w = grid_power
        grid_inverted = bool(self.config_entry.data.get(CONF_GRID_POWER_INVERTED, False))
        if grid_inverted:
            data.available_surplus_w = max(0, grid_power)
            data.import_w = max(0, -grid_power)
        else:
            data.available_surplus_w = max(0, -grid_power)
            data.import_w = max(0, grid_power)

        data.current_charge_power_w = self._current_charge_power_w()
        data.controllable_surplus_w = max(
            0,
            data.available_surplus_w + data.current_charge_power_w - data.import_w,
        )
        data.in_cheap_hours = self._in_cheap_hours(now)
        data.in_solar_window = self._in_time_window(
            str(self.options[OPT_SOLAR_WINDOW_START]),
            str(self.options[OPT_SOLAR_WINDOW_END]),
            now.time(),
        )
        data.recommended_amps = self._calculate_recommended_amps(data.controllable_surplus_w)
        data.estimated_power_w = data.recommended_amps * float(self.options[OPT_VOLTAGE])
        data.has_surplus = data.recommended_amps >= int(self.options[OPT_MIN_AMPS])
        data.home_battery_protected = self._home_battery_is_protected()

        self._update_hysteresis(data.has_surplus, now)

        mode = str(self.options[OPT_MODE])
        enabled = bool(self.options[OPT_ENABLED])

        if not enabled:
            data.current_state = STATE_OFF
            data.reason = "Controller is disabled"
            data.should_charge = False
            data.is_charging = self._controlled_charging or self._is_charge_switch_on()
            return data

        if mode == MODE_OFF:
            data.current_state = STATE_OFF
            data.reason = "Off mode is enabled"
            data.should_charge = False
            if self._controlled_charging or self._is_charge_switch_on():
                await self._stop_charging(data.reason)
            return data

        if mode == MODE_MANUAL:
            data.current_state = STATE_MANUAL
            data.reason = "Manual mode enabled, no control actions are being sent"
            data.is_charging = self._controlled_charging
            return data

        car_soc = self._optional_float(self.config_entry.data.get(CONF_CAR_SOC_SENSOR))
        if car_soc is not None and car_soc >= float(self.options[OPT_TARGET_CAR_SOC]):
            data.current_state = STATE_IDLE
            data.reason = "Paused because target car SOC is reached"
            data.should_charge = False
            if self._controlled_charging or self._is_charge_switch_on():
                await self._stop_charging(data.reason)
            return data

        decision_state, reason, desired_amps = self._decide_charge(data, mode, now)
        data.current_state = decision_state
        data.reason = reason
        data.should_charge = desired_amps > 0

        if data.should_charge:
            await self._set_charge_amps(desired_amps)
            await self._start_charging(reason)
            data.is_charging = True
        else:
            if (
                (self._controlled_charging or self._is_charge_switch_on())
                and self._should_stop_charging(data, now)
            ):
                await self._stop_charging(reason)
            data.is_charging = self._controlled_charging

        data.last_action = self.data.last_action if self.data else "none"
        return data

    def _decide_charge(
        self,
        data: ControllerData,
        mode: str,
        now: datetime,
    ) -> tuple[str, str, int]:
        if mode == MODE_FORCE_CHARGE:
            desired_amps = self._limit_amps_by_grid_import(int(self.options[OPT_MAX_AMPS]), data)
            if desired_amps < int(self.options[OPT_MIN_AMPS]):
                return (
                    STATE_PAUSED_NO_SURPLUS,
                    "Paused because maximum grid import limit would be exceeded",
                    0,
                )
            return (
                STATE_CHARGING_FORCED,
                "Charging because Force charge mode is enabled",
                desired_amps,
            )

        if mode == MODE_CHEAP_HOURS:
            if data.in_cheap_hours:
                desired_amps = self._limit_amps_by_grid_import(int(self.options[OPT_MAX_AMPS]), data)
                if desired_amps < int(self.options[OPT_MIN_AMPS]):
                    return (
                        STATE_PAUSED_NO_SURPLUS,
                        "Paused because maximum grid import limit would be exceeded",
                        0,
                    )
                return (
                    STATE_CHARGING_CHEAP,
                    "Charging because cheap hours are active",
                    desired_amps,
                )
            return (STATE_PAUSED_OUTSIDE_SCHEDULE, "Paused because cheap hours are inactive", 0)

        if mode == MODE_SOLAR_ONLY:
            return self._solar_decision(data, now)

        if mode == MODE_HYBRID:
            if data.in_solar_window and data.has_surplus:
                return self._solar_decision(data, now)
            if data.in_cheap_hours and (
                bool(self.options[OPT_NEED_CAR_TOMORROW])
                or bool(self.options[OPT_ALLOW_GRID_IMPORT])
            ):
                desired_amps = self._limit_amps_by_grid_import(int(self.options[OPT_MAX_AMPS]), data)
                if desired_amps < int(self.options[OPT_MIN_AMPS]):
                    return (
                        STATE_PAUSED_NO_SURPLUS,
                        "Paused because maximum grid import limit would be exceeded",
                        0,
                    )
                return (
                    STATE_CHARGING_CHEAP,
                    "Charging because Hybrid mode allows cheap-hours charging",
                    desired_amps,
                )
            if not data.in_solar_window and not data.in_cheap_hours:
                return (STATE_PAUSED_OUTSIDE_SCHEDULE, "Paused because outside allowed schedules", 0)
            return (STATE_PAUSED_NO_SURPLUS, "Paused because no surplus is available", 0)

        return (STATE_IDLE, "Controller is idle", 0)

    def _solar_decision(
        self,
        data: ControllerData,
        now: datetime,
    ) -> tuple[str, str, int]:
        if not data.in_solar_window:
            return (STATE_PAUSED_OUTSIDE_SCHEDULE, "Paused because outside solar window", 0)
        if data.home_battery_protected:
            return (
                STATE_PAUSED_HOME_BATTERY_PROTECTION,
                "Paused because home battery protection is active",
                0,
            )
        if not data.has_surplus:
            return (STATE_PAUSED_NO_SURPLUS, "Paused because no surplus is available", 0)
        if not self._surplus_on_elapsed(now):
            return (STATE_WAITING_FOR_SURPLUS, "Waiting for stable surplus before charging", 0)
        desired_amps = self._limit_amps_by_grid_import(data.recommended_amps, data)
        if desired_amps < int(self.options[OPT_MIN_AMPS]):
            return (
                STATE_PAUSED_NO_SURPLUS,
                "Paused because maximum grid import limit would be exceeded",
                0,
            )
        return (STATE_CHARGING_SOLAR, "Charging with solar surplus", desired_amps)

    def _calculate_recommended_amps(self, surplus_w: float) -> int:
        useful_w = surplus_w - float(self.options[OPT_SAFETY_MARGIN_W])
        if useful_w < float(self.options[OPT_MIN_SURPLUS_W]):
            return 0

        amps = math.floor(useful_w / float(self.options[OPT_VOLTAGE]))
        if amps < int(self.options[OPT_MIN_AMPS]):
            return 0
        return max(
            int(self.options[OPT_MIN_AMPS]),
            min(int(self.options[OPT_MAX_AMPS]), amps),
        )

    def _current_charge_power_w(self) -> float:
        """Estimate power already assigned to the car when this controller is charging.

        The grid sensor only sees remaining export after the car has consumed power.
        While charging, add the current charge power back before recalculating amps.
        """
        if not self._controlled_charging:
            return 0

        current_amps = self._optional_float(self.config_entry.data.get(CONF_CHARGE_AMPS_ENTITY))
        if current_amps is None:
            current_amps = self._last_set_amps
        if current_amps is None:
            return 0

        return max(0, current_amps * float(self.options[OPT_VOLTAGE]))

    def _limit_amps_by_grid_import(self, requested_amps: int, data: ControllerData) -> int:
        max_grid_import_w = float(self.options[OPT_MAX_GRID_IMPORT_W])
        voltage = float(self.options[OPT_VOLTAGE])

        allowed_total_charge_power_w = (
            data.current_charge_power_w
            + max_grid_import_w
            - data.import_w
            + data.available_surplus_w
        )
        allowed_amps = math.floor(max(0, allowed_total_charge_power_w) / voltage)
        return max(0, min(requested_amps, allowed_amps, int(self.options[OPT_MAX_AMPS])))

    def _home_battery_is_protected(self) -> bool:
        if bool(self.options[OPT_ALLOW_HOME_BATTERY]):
            return False

        soc = self._optional_float(self.config_entry.data.get(CONF_HOME_BATTERY_SOC_SENSOR))
        if soc is not None and soc < float(self.options[OPT_HOME_BATTERY_MIN_SOC]):
            return True

        power_entity = self.config_entry.data.get(CONF_HOME_BATTERY_POWER_SENSOR)
        if power_entity:
            power = self._optional_float(power_entity)
            if power is not None:
                inverted = bool(self.config_entry.data.get(CONF_HOME_BATTERY_POWER_INVERTED, False))
                discharging = power < 0 if inverted else power > 0
                if discharging:
                    return True
        return False

    async def _set_charge_amps(self, amps: int, force: bool = False) -> None:
        entity_id = self.config_entry.data.get(CONF_CHARGE_AMPS_ENTITY)
        if not entity_id:
            return

        now = dt_util.now()
        if (
            not force
            and self._last_amps_update_time is not None
            and (now - self._last_amps_update_time).total_seconds() < int(self.options[OPT_UPDATE_INTERVAL])
        ):
            return

        current = self._optional_float(entity_id)
        if not force and current is not None and abs(current - amps) < 1:
            return
        if not force and self._last_set_amps == amps:
            return

        await self.hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": entity_id, "value": amps},
            blocking=False,
        )
        self._last_amps_update_time = now
        self._last_set_amps = amps
        self.data.last_action = f"Set charge current to {amps} A"

    async def _start_charging(self, reason: str, force: bool = False) -> None:
        if not force and not self._action_allowed():
            return

        enable_switch = self.config_entry.data.get(CONF_CHARGER_ENABLE_SWITCH)
        if enable_switch:
            await self.hass.services.async_call(
                "switch",
                "turn_on",
                {"entity_id": enable_switch},
                blocking=False,
            )

        entity_id = self.config_entry.data[CONF_START_CHARGE_ENTITY]
        await self._call_control_entity(entity_id, True)
        self._controlled_charging = True
        self._last_action_time = dt_util.now()
        self.data.last_action = f"Start charge: {reason}"

    async def _stop_charging(self, reason: str, force: bool = False) -> None:
        if not force and not self._action_allowed():
            return

        entity_id = self.config_entry.data[CONF_STOP_CHARGE_ENTITY]
        await self._call_control_entity(entity_id, False)
        self._controlled_charging = False
        self._last_action_time = dt_util.now()
        self.data.last_action = f"Stop charge: {reason}"

    async def _call_control_entity(self, entity_id: str, turn_on: bool) -> None:
        domain = entity_id.split(".", 1)[0]
        if domain == "button":
            await self.hass.services.async_call(
                "button",
                "press",
                {"entity_id": entity_id},
                blocking=False,
            )
            return

        if domain == "switch":
            await self.hass.services.async_call(
                "switch",
                "turn_on" if turn_on else "turn_off",
                {"entity_id": entity_id},
                blocking=False,
            )
            return

        _LOGGER.warning("Unsupported control entity domain for %s", entity_id)

    def _action_allowed(self) -> bool:
        if self._last_action_time is None:
            return True
        elapsed = (dt_util.now() - self._last_action_time).total_seconds()
        return elapsed >= int(self.options[OPT_MIN_ACTION_INTERVAL])

    def _update_hysteresis(self, has_surplus: bool, now: datetime) -> None:
        if has_surplus:
            self._no_surplus_since = None
            if self._surplus_since is None:
                self._surplus_since = now
        else:
            self._surplus_since = None
            if self._no_surplus_since is None:
                self._no_surplus_since = now

    def _surplus_on_elapsed(self, now: datetime) -> bool:
        if self._surplus_since is None:
            return False
        return (now - self._surplus_since).total_seconds() >= int(self.options[OPT_SURPLUS_ON_DURATION])

    def _surplus_off_elapsed(self, now: datetime) -> bool:
        if self._no_surplus_since is None:
            return False
        return (now - self._no_surplus_since).total_seconds() >= int(self.options[OPT_SURPLUS_OFF_DURATION])

    def _should_stop_charging(self, data: ControllerData, now: datetime) -> bool:
        if data.current_state in {
            STATE_IDLE,
            STATE_PAUSED_HOME_BATTERY_PROTECTION,
            STATE_PAUSED_OUTSIDE_SCHEDULE,
            STATE_OFF,
        }:
            return True

        if "maximum grid import limit" in data.reason:
            return True

        return self._surplus_off_elapsed(now)

    def _required_float(self, entity_id: str) -> float:
        value = self._optional_float(entity_id)
        if value is None:
            raise ValueError(f"Required entity {entity_id} has no numeric state")
        return value

    def _optional_float(self, entity_id: str | None) -> float | None:
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return None
        try:
            return float(state.state)
        except (TypeError, ValueError):
            return None

    def _is_charge_switch_on(self) -> bool:
        start_entity = self.config_entry.data.get(CONF_START_CHARGE_ENTITY)
        stop_entity = self.config_entry.data.get(CONF_STOP_CHARGE_ENTITY)
        if not start_entity or start_entity != stop_entity or not start_entity.startswith("switch."):
            return False

        state = self.hass.states.get(start_entity)
        return state is not None and state.state == "on"

    @staticmethod
    def _in_time_window(start_value: str, end_value: str, current: time) -> bool:
        start = _parse_time(start_value)
        end = _parse_time(end_value)
        if start == end:
            return True
        if start < end:
            return start <= current < end
        return current >= start or current < end

    def _in_cheap_hours(self, now: datetime) -> bool:
        if bool(self.options[OPT_CHEAP_HOURS_ALL_WEEKEND]) and now.weekday() >= 5:
            return True

        return self._in_time_window(
            str(self.options[OPT_CHEAP_HOURS_START]),
            str(self.options[OPT_CHEAP_HOURS_END]),
            now.time(),
        )

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self.config_entry.entry_id)},
            "name": self.config_entry.title,
            "manufacturer": "Solar EV Charger Controller",
            "model": "Controller",
        }

    def entity_unique_id(self, key: str) -> str:
        return f"{self.config_entry.entry_id}_{key}"

    def suggested_object_id(self, key: str) -> str:
        registry = er.async_get(self.hass)
        existing = registry.async_get_entity_id("sensor", DOMAIN, self.entity_unique_id(key))
        if existing:
            return existing.split(".", 1)[1]
        return f"solar_ev_charger_{key}"


def _parse_time(value: str | time) -> time:
    if isinstance(value, time):
        return value

    parts = value.split(":")
    if len(parts) < 2:
        raise ValueError(f"Invalid time value: {value}")
    return time(int(parts[0]), int(parts[1]))
