"""Config flow for Solar EV Charger Controller."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_CAR_SOC_SENSOR,
    CONF_CHARGE_AMPS_ENTITY,
    CONF_CHARGER_ENABLE_SWITCH,
    CONF_ENERGY_PRICE_SENSOR,
    CONF_GRID_POWER_INVERTED,
    CONF_GRID_POWER_SENSOR,
    CONF_HOME_BATTERY_POWER_INVERTED,
    CONF_HOME_BATTERY_POWER_SENSOR,
    CONF_HOME_BATTERY_SOC_SENSOR,
    CONF_HOUSE_CONSUMPTION_SENSOR,
    CONF_SOLAR_FORECAST_ENTITY,
    CONF_SOLAR_POWER_SENSOR,
    CONF_START_CHARGE_ENTITY,
    CONF_STOP_CHARGE_ENTITY,
    DEFAULT_OPTIONS,
    DOMAIN,
    MODE_LABELS,
    MODE_VALUES_BY_LABEL,
    OPT_ALLOW_GRID_IMPORT,
    OPT_ALLOW_HOME_BATTERY,
    OPT_CHEAP_HOURS_END,
    OPT_CHEAP_HOURS_START,
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
)


class SolarEVChargerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(
                title="Solar EV Charger Controller",
                data=user_input,
                options=DEFAULT_OPTIONS,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_config_schema(),
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SolarEVChargerOptionsFlow:
        """Create the options flow."""
        return SolarEVChargerOptionsFlow(config_entry)


class SolarEVChargerOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.FlowResult:
        if user_input is not None:
            options = dict(user_input)
            options[OPT_MODE] = MODE_VALUES_BY_LABEL.get(options[OPT_MODE], options[OPT_MODE])
            return self.async_create_entry(title="", data=options)

        options = {**DEFAULT_OPTIONS, **dict(self.config_entry.options)}
        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(options),
        )


def _config_schema() -> vol.Schema:
    sensor_entity = selector.EntitySelector(
        selector.EntitySelectorConfig(domain=["sensor"])
    )
    number_entity = selector.EntitySelector(
        selector.EntitySelectorConfig(domain=["number"])
    )
    control_entity = selector.EntitySelector(
        selector.EntitySelectorConfig(domain=["button", "switch"])
    )
    switch_entity = selector.EntitySelector(
        selector.EntitySelectorConfig(domain=["switch"])
    )
    any_entity = selector.EntitySelector(selector.EntitySelectorConfig())

    return vol.Schema(
        {
            vol.Required(CONF_GRID_POWER_SENSOR): sensor_entity,
            vol.Required(CONF_GRID_POWER_INVERTED, default=False): selector.BooleanSelector(),
            vol.Required(CONF_START_CHARGE_ENTITY): control_entity,
            vol.Required(CONF_STOP_CHARGE_ENTITY): control_entity,
            vol.Required(CONF_CHARGE_AMPS_ENTITY): number_entity,
            vol.Optional(CONF_SOLAR_POWER_SENSOR): sensor_entity,
            vol.Optional(CONF_HOUSE_CONSUMPTION_SENSOR): sensor_entity,
            vol.Optional(CONF_HOME_BATTERY_POWER_SENSOR): sensor_entity,
            vol.Optional(CONF_HOME_BATTERY_POWER_INVERTED, default=False): selector.BooleanSelector(),
            vol.Optional(CONF_HOME_BATTERY_SOC_SENSOR): sensor_entity,
            vol.Optional(CONF_CAR_SOC_SENSOR): sensor_entity,
            vol.Optional(CONF_CHARGER_ENABLE_SWITCH): switch_entity,
            vol.Optional(CONF_ENERGY_PRICE_SENSOR): sensor_entity,
            vol.Optional(CONF_SOLAR_FORECAST_ENTITY): any_entity,
        }
    )


def _options_schema(options: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(OPT_MODE, default=MODE_LABELS[options[OPT_MODE]]): selector.SelectSelector(
                selector.SelectSelectorConfig(options=list(MODE_LABELS.values()))
            ),
            vol.Required(OPT_MIN_AMPS, default=options[OPT_MIN_AMPS]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=64, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(OPT_MAX_AMPS, default=options[OPT_MAX_AMPS]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=64, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(OPT_SAFETY_MARGIN_W, default=options[OPT_SAFETY_MARGIN_W]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=5000, step=50, unit_of_measurement="W")
            ),
            vol.Required(OPT_MIN_SURPLUS_W, default=options[OPT_MIN_SURPLUS_W]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=22000, step=50, unit_of_measurement="W")
            ),
            vol.Required(OPT_TARGET_CAR_SOC, default=options[OPT_TARGET_CAR_SOC]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=100, step=1, unit_of_measurement="%")
            ),
            vol.Required(OPT_HOME_BATTERY_MIN_SOC, default=options[OPT_HOME_BATTERY_MIN_SOC]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=1, unit_of_measurement="%")
            ),
            vol.Required(OPT_MAX_GRID_IMPORT_W, default=options[OPT_MAX_GRID_IMPORT_W]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=22000, step=50, unit_of_measurement="W")
            ),
            vol.Required(OPT_VOLTAGE, default=options[OPT_VOLTAGE]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=100, max=260, step=1, unit_of_measurement="V")
            ),
            vol.Required(OPT_ALLOW_GRID_IMPORT, default=options[OPT_ALLOW_GRID_IMPORT]): selector.BooleanSelector(),
            vol.Required(OPT_ALLOW_HOME_BATTERY, default=options[OPT_ALLOW_HOME_BATTERY]): selector.BooleanSelector(),
            vol.Required(OPT_NEED_CAR_TOMORROW, default=options[OPT_NEED_CAR_TOMORROW]): selector.BooleanSelector(),
            vol.Required(OPT_CHEAP_HOURS_START, default=options[OPT_CHEAP_HOURS_START]): selector.TimeSelector(),
            vol.Required(OPT_CHEAP_HOURS_END, default=options[OPT_CHEAP_HOURS_END]): selector.TimeSelector(),
            vol.Required(OPT_SOLAR_WINDOW_START, default=options[OPT_SOLAR_WINDOW_START]): selector.TimeSelector(),
            vol.Required(OPT_SOLAR_WINDOW_END, default=options[OPT_SOLAR_WINDOW_END]): selector.TimeSelector(),
            vol.Required(OPT_READY_BY_TIME, default=options[OPT_READY_BY_TIME]): selector.TimeSelector(),
            vol.Required(OPT_SURPLUS_ON_DURATION, default=options[OPT_SURPLUS_ON_DURATION]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=1800, step=30, unit_of_measurement="s")
            ),
            vol.Required(OPT_SURPLUS_OFF_DURATION, default=options[OPT_SURPLUS_OFF_DURATION]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=1800, step=30, unit_of_measurement="s")
            ),
            vol.Required(OPT_MIN_ACTION_INTERVAL, default=options[OPT_MIN_ACTION_INTERVAL]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=1800, step=30, unit_of_measurement="s")
            ),
            vol.Required(OPT_UPDATE_INTERVAL, default=options[OPT_UPDATE_INTERVAL]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=10, max=300, step=10, unit_of_measurement="s")
            ),
        }
    )
