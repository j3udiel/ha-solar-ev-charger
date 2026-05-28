"""Constants for Solar EV Charger Controller."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "solar_ev_charger"
NAME = "Solar EV Charger Controller"
VERSION = "0.1.1"

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.BUTTON,
]

CONF_GRID_POWER_SENSOR = "grid_power_sensor"
CONF_GRID_POWER_INVERTED = "grid_power_inverted"
CONF_START_CHARGE_ENTITY = "start_charge_entity"
CONF_STOP_CHARGE_ENTITY = "stop_charge_entity"
CONF_CHARGE_AMPS_ENTITY = "charge_amps_entity"
CONF_SOLAR_POWER_SENSOR = "solar_power_sensor"
CONF_HOUSE_CONSUMPTION_SENSOR = "house_consumption_sensor"
CONF_HOME_BATTERY_POWER_SENSOR = "home_battery_power_sensor"
CONF_HOME_BATTERY_POWER_INVERTED = "home_battery_power_inverted"
CONF_HOME_BATTERY_SOC_SENSOR = "home_battery_soc_sensor"
CONF_CAR_SOC_SENSOR = "car_soc_sensor"
CONF_CHARGER_ENABLE_SWITCH = "charger_enable_switch"
CONF_ENERGY_PRICE_SENSOR = "energy_price_sensor"
CONF_SOLAR_FORECAST_ENTITY = "solar_forecast_entity"

OPT_ENABLED = "enabled"
OPT_MODE = "mode"
OPT_MIN_AMPS = "min_amps"
OPT_MAX_AMPS = "max_amps"
OPT_SAFETY_MARGIN_W = "safety_margin_w"
OPT_MIN_SURPLUS_W = "min_surplus_w"
OPT_TARGET_CAR_SOC = "target_car_soc"
OPT_HOME_BATTERY_MIN_SOC = "home_battery_min_soc"
OPT_MAX_GRID_IMPORT_W = "max_grid_import_w"
OPT_VOLTAGE = "voltage"
OPT_ALLOW_GRID_IMPORT = "allow_grid_import"
OPT_ALLOW_HOME_BATTERY = "allow_home_battery"
OPT_NEED_CAR_TOMORROW = "need_car_tomorrow"
OPT_CHEAP_HOURS_START = "cheap_hours_start"
OPT_CHEAP_HOURS_END = "cheap_hours_end"
OPT_SOLAR_WINDOW_START = "solar_window_start"
OPT_SOLAR_WINDOW_END = "solar_window_end"
OPT_READY_BY_TIME = "ready_by_time"
OPT_SURPLUS_ON_DURATION = "surplus_on_duration"
OPT_SURPLUS_OFF_DURATION = "surplus_off_duration"
OPT_MIN_ACTION_INTERVAL = "minimum_action_interval"
OPT_UPDATE_INTERVAL = "update_interval"

MODE_OFF = "off"
MODE_SOLAR_ONLY = "solar_only"
MODE_CHEAP_HOURS = "cheap_hours"
MODE_HYBRID = "hybrid"
MODE_FORCE_CHARGE = "force_charge"
MODE_MANUAL = "manual"

MODES = [
    MODE_OFF,
    MODE_SOLAR_ONLY,
    MODE_CHEAP_HOURS,
    MODE_HYBRID,
    MODE_FORCE_CHARGE,
    MODE_MANUAL,
]

MODE_LABELS = {
    MODE_OFF: "Off",
    MODE_SOLAR_ONLY: "Solar only",
    MODE_CHEAP_HOURS: "Cheap hours",
    MODE_HYBRID: "Hybrid",
    MODE_FORCE_CHARGE: "Force charge",
    MODE_MANUAL: "Manual",
}

MODE_VALUES_BY_LABEL = {label: value for value, label in MODE_LABELS.items()}

STATE_OFF = "off"
STATE_IDLE = "idle"
STATE_WAITING_FOR_SURPLUS = "waiting_for_surplus"
STATE_CHARGING_SOLAR = "charging_solar"
STATE_CHARGING_CHEAP = "charging_cheap"
STATE_CHARGING_FORCED = "charging_forced"
STATE_PAUSED_NO_SURPLUS = "paused_no_surplus"
STATE_PAUSED_HOME_BATTERY_PROTECTION = "paused_home_battery_protection"
STATE_PAUSED_OUTSIDE_SCHEDULE = "paused_outside_schedule"
STATE_MANUAL = "manual"
STATE_ERROR = "error"

DEFAULT_OPTIONS = {
    OPT_ENABLED: True,
    OPT_MODE: MODE_HYBRID,
    OPT_MIN_AMPS: 6,
    OPT_MAX_AMPS: 16,
    OPT_SAFETY_MARGIN_W: 300,
    OPT_MIN_SURPLUS_W: 1400,
    OPT_TARGET_CAR_SOC: 80,
    OPT_HOME_BATTERY_MIN_SOC: 80,
    OPT_MAX_GRID_IMPORT_W: 0,
    OPT_VOLTAGE: 230,
    OPT_ALLOW_GRID_IMPORT: False,
    OPT_ALLOW_HOME_BATTERY: False,
    OPT_NEED_CAR_TOMORROW: False,
    OPT_CHEAP_HOURS_START: "00:00",
    OPT_CHEAP_HOURS_END: "08:00",
    OPT_SOLAR_WINDOW_START: "09:00",
    OPT_SOLAR_WINDOW_END: "18:00",
    OPT_READY_BY_TIME: "07:30",
    OPT_SURPLUS_ON_DURATION: 180,
    OPT_SURPLUS_OFF_DURATION: 180,
    OPT_MIN_ACTION_INTERVAL: 120,
    OPT_UPDATE_INTERVAL: 30,
}

SERVICE_START = "start"
SERVICE_STOP = "stop"
SERVICE_RECALCULATE = "recalculate"
SERVICE_SET_MODE = "set_mode"
