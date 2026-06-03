# Solar EV Charger Controller

<p align="center">
  <img src="custom_components/solar_ev_charger/brand/icon.png" alt="Solar EV Charger Controller icon" width="160">
</p>

Custom integration for Home Assistant that controls EV charging with solar surplus, cheap electricity windows, and basic home battery protection.

The first target setup is a Tesla Model Y with a Tesla wall charger, solar production, and a Huawei home battery, but the integration is intentionally generic. It controls existing Home Assistant entities instead of depending on one car, charger, inverter, or vendor integration.

## What it does

Solar EV Charger Controller reads your grid power sensor as the main source of truth. If the house is exporting power, it calculates available surplus and recommends a charging current:

```text
recommended_amps = floor((surplus_w - safety_margin_w) / voltage)
```

It then applies minimum and maximum amps, schedules, mode rules, SOC limits, cooldowns, and hysteresis before sending start, stop, or amps commands to your configured Home Assistant entities.

## Current status

This is an early functional version. It supports:

- UI config flow.
- HACS custom repository layout.
- Grid power polarity selection.
- Start and stop through `button` or `switch` entities.
- Charge current through a `number` entity.
- Solar surplus calculation.
- Recommended amps calculation.
- Off, Solar only, Cheap hours, Hybrid, Force charge, and Manual modes.
- Cheap-hours window with midnight crossing support.
- Solar window.
- `need car tomorrow` switch.
- Home battery SOC and discharge protection.
- Start/stop cooldown and surplus hysteresis.
- Diagnostic sensors and binary sensors.

It does not yet implement predictive planning, solar forecast logic, dynamic tariff optimization, multi-car support, or advanced Tesla/Huawei-specific behavior.

## Installation

### Manual

Copy this directory into Home Assistant:

```bash
custom_components/solar_ev_charger
```

For example:

```bash
cp -r custom_components/solar_ev_charger /config/custom_components/
```

Restart Home Assistant, then go to:

```text
Settings -> Devices & services -> Add integration -> Solar EV Charger Controller
```

### HACS custom repository

1. Open HACS.
2. Go to `Integrations`.
3. Open the three-dot menu.
4. Choose `Custom repositories`.
5. Add your GitHub repository URL.
6. Select category `Integration`.
7. Install `Solar EV Charger Controller`.
8. Restart Home Assistant.

## Creating the local repository

If the GitHub repo does not exist yet:

```bash
cd ~/Documents/AI
mkdir -p ha-solar-ev-charger
cd ha-solar-ev-charger
git init
```

If it already exists:

```bash
cd ~/Documents/AI
git clone <repo> ha-solar-ev-charger
cd ha-solar-ev-charger
```

## Initial configuration

Required entities:

- Grid power sensor, for example `sensor.grid_power`.
- Start charge entity, for example `button.tesla_start_charge` or `switch.ev_charger`.
- Stop charge entity, for example `button.tesla_stop_charge` or `switch.ev_charger`.
- Charge amps number entity, for example `number.tesla_charging_amps`.

Optional entities:

- Solar power sensor.
- House consumption sensor.
- Home battery power sensor.
- Home battery SOC sensor.
- Car SOC sensor.
- General charger enable switch.
- Energy price sensor.
- Solar forecast entity.

The grid power sensor is the primary signal. By default, the integration assumes:

```text
positive = importing from grid
negative = exporting to grid
```

If your sensor uses the opposite convention, enable `Grid power positive means export` during setup.

### Setup form field guide

#### English

`Grid power sensor`  
Main sensor used to know whether the house is importing from or exporting to the grid. This is the most important sensor for solar surplus control. It should be a power sensor in watts. Example: `sensor.grid_power`. If the value is negative while exporting, leave `Grid power positive means export` disabled. If the value is positive while exporting, enable it.

`Grid power positive means export`  
Polarity option for the grid sensor. Disabled means `positive = importing` and `negative = exporting`. Enabled means `positive = exporting` and `negative = importing`.

`Start charge entity`  
Existing entity that starts EV charging. Use a `button` if your car integration exposes a start command, for example `button.tesla_start_charge`. Use a `switch` if your charger starts when the switch is turned on, for example `switch.ev_charger`.

`Stop charge entity`  
Existing entity that stops EV charging. Use a stop button such as `button.tesla_stop_charge`, or the same charger switch used above if turning it off stops charging.

`Charge amps number entity`  
Existing `number` entity that sets charging current in amps. Example: `number.tesla_charging_amps`. The integration writes the calculated recommended amps here before or while charging.

`Solar power sensor`  
Optional informational sensor for current solar production. It is not the main decision signal because grid import/export is a better real surplus indicator.

`House consumption sensor`  
Optional informational sensor for current home consumption. It is not required for the first control logic.

`Home battery power sensor`  
Optional sensor for home battery charge/discharge power. Use it if you want to avoid charging the car from the home battery. Example: `sensor.huawei_battery_power`.

`Home battery power positive means charging`  
Polarity option for the home battery power sensor. Disabled means `positive = discharging` and `negative = charging`. Enabled means `positive = charging` and `negative = discharging`.

`Home battery SOC sensor`  
Optional percentage sensor for the home battery state of charge. Example: `sensor.huawei_battery_soc`. If the value is below `Minimum home battery SOC`, the controller can pause charging unless home battery use is allowed.

`Car SOC sensor`  
Optional percentage sensor for the EV battery level. Example: `sensor.tesla_battery_level`. If configured, the controller stops when the car reaches `Target car SOC`.

`Charger enable switch`  
Optional general permission switch for the charger. Most Tesla setups should leave this empty. Use it only if you have a separate switch that enables the charger as a whole, different from the start/stop charge command.

`Current energy price sensor`  
Optional placeholder for future dynamic price logic. It is not required in the current version.

`Solar forecast entity`  
Optional placeholder for future solar forecast planning. It is not required in the current version.

#### Español

`Grid power sensor` / Sensor de potencia de red  
Sensor principal para saber si la casa importa de la red o exporta excedente. Es el sensor mas importante para controlar por excedente solar. Debe ser un sensor de potencia en vatios. Ejemplo: `sensor.grid_power`. Si el valor es negativo cuando exportas, deja desactivado `Grid power positive means export`. Si el valor es positivo cuando exportas, activalo.

`Grid power positive means export` / Potencia de red positiva significa exportacion  
Opcion de polaridad del sensor de red. Desactivado significa `positivo = importacion` y `negativo = exportacion`. Activado significa `positivo = exportacion` y `negativo = importacion`.

`Start charge entity` / Entidad para iniciar carga  
Entidad existente que inicia la carga del coche. Usa un `button` si la integracion del coche expone un comando de arranque, por ejemplo `button.tesla_start_charge`. Usa un `switch` si el cargador empieza a cargar al encender ese switch, por ejemplo `switch.ev_charger`.

`Stop charge entity` / Entidad para parar carga  
Entidad existente que para la carga del coche. Usa un boton de parada como `button.tesla_stop_charge`, o el mismo switch del cargador si apagarlo detiene la carga.

`Charge amps number entity` / Entidad number de amperios  
Entidad `number` existente que define los amperios de carga. Ejemplo: `number.tesla_charging_amps`. La integracion escribe aqui los amperios recomendados antes o durante la carga.

`Solar power sensor` / Sensor de potencia solar  
Sensor opcional informativo de produccion solar actual. No es la senal principal de decision porque la importacion/exportacion de red representa mejor el excedente real.

`House consumption sensor` / Sensor de consumo de casa  
Sensor opcional informativo del consumo actual de la vivienda. No es necesario para la primera logica de control.

`Home battery power sensor` / Sensor de potencia de bateria domestica  
Sensor opcional de potencia de carga/descarga de la bateria domestica. Usalo si quieres evitar cargar el coche desde la bateria de casa. Ejemplo: `sensor.huawei_battery_power`.

`Home battery power positive means charging` / Potencia de bateria positiva significa cargando  
Opcion de polaridad del sensor de potencia de bateria. Desactivado significa `positivo = descargando` y `negativo = cargando`. Activado significa `positivo = cargando` y `negativo = descargando`.

`Home battery SOC sensor` / Sensor de SOC de bateria domestica  
Sensor opcional de porcentaje de carga de la bateria de casa. Ejemplo: `sensor.huawei_battery_soc`. Si el valor esta por debajo de `Minimum home battery SOC`, el controlador puede pausar la carga salvo que permitas usar la bateria domestica.

`Car SOC sensor` / Sensor de SOC del coche  
Sensor opcional de porcentaje de bateria del coche. Ejemplo: `sensor.tesla_battery_level`. Si esta configurado, el controlador para al llegar al `Target car SOC`.

`Charger enable switch` / Switch general del cargador  
Switch opcional de permiso general del cargador. En la mayoria de setups Tesla debe dejarse vacio. Usalo solo si tienes un switch separado que habilita el cargador completo y que no es el comando normal de start/stop.

`Current energy price sensor` / Sensor de precio actual de energia  
Campo opcional preparado para futura logica con precios dinamicos. No es necesario en la version actual.

`Solar forecast entity` / Entidad de prevision solar  
Campo opcional preparado para futura planificacion con prevision solar. No es necesario en la version actual.

## Modes

`Off`: The controller does nothing. If charging was started by this integration, it may stop it.

`Solar only`: Charges only when stable solar surplus exists inside the solar window.

`Cheap hours`: Charges only inside the configured cheap-hours window. It can charge from the grid.

`Hybrid`: Uses solar surplus during the solar window. During cheap hours it can charge if `Need car tomorrow` or `Allow grid import` is enabled.

`Force charge`: Starts charging immediately at max amps, while still respecting target car SOC and basic safety checks.

`Manual`: The integration publishes diagnostics but sends no start, stop, or amps commands.

## Default options

```text
min_amps = 6
max_amps = 16
safety_margin_w = 300
min_surplus_w = 1400
target_car_soc = 80
home_battery_min_soc = 80
max_grid_import_w = 0
voltage = 230
cheap_hours_start = 00:00
cheap_hours_end = 08:00
cheap_hours_all_weekend = false
solar_window_start = 09:00
solar_window_end = 18:00
ready_by_time = 07:30
surplus_on_duration = 180 seconds
surplus_off_duration = 180 seconds
minimum_action_interval = 120 seconds
update_interval = 30 seconds
```

`max_grid_import_w` limits how much grid import the controller may use when choosing charging amps. In solar-first use, keep it low, for example `0` to `300 W`. In cheap-hours or urgent charging, use a higher value only if your electrical installation and contracted power allow it.

Cheap-hours and solar windows support ranges that cross midnight, such as:

```text
23:00 -> 07:00
```

If your tariff has cheap electricity all weekend, enable:

```text
switch.solar_ev_charger_cheap_hours_all_weekend
```

When enabled, Saturday and Sunday are treated as cheap hours for the full day.

## Pausing the controller

Use this switch to pause charging control without disabling or uninstalling the integration:

```text
switch.solar_ev_charger_enabled
```

When this switch is off:

- The integration remains loaded in Home Assistant.
- Diagnostic sensors and binary sensors continue to update.
- The controller does not send start, stop, or charging-amps commands.
- Existing car/charger state is left untouched.

Use `Manual` mode when you want diagnostics and mode context while keeping the car/charger exactly as you left it. Use `Controller enabled = off` when you want a clear global pause for all controller behavior. Use `Off` mode when you explicitly want the controller to stop charging if it was controlling the session.

## Entities created

Switches:

```text
switch.solar_ev_charger_enabled
switch.solar_ev_charger_need_car_tomorrow
switch.solar_ev_charger_allow_grid_import
switch.solar_ev_charger_allow_home_battery
switch.solar_ev_charger_cheap_hours_all_weekend
```

Select:

```text
select.solar_ev_charger_mode
```

Numbers:

```text
number.solar_ev_charger_min_amps
number.solar_ev_charger_max_amps
number.solar_ev_charger_safety_margin_w
number.solar_ev_charger_min_surplus_w
number.solar_ev_charger_target_car_soc
number.solar_ev_charger_home_battery_min_soc
number.solar_ev_charger_max_grid_import_w
number.solar_ev_charger_voltage
```

Sensors:

```text
sensor.solar_ev_charger_available_surplus_w
sensor.solar_ev_charger_controllable_surplus_w
sensor.solar_ev_charger_current_charge_power_w
sensor.solar_ev_charger_grid_power_w
sensor.solar_ev_charger_grid_import_w
sensor.solar_ev_charger_recommended_amps
sensor.solar_ev_charger_current_state
sensor.solar_ev_charger_last_action
sensor.solar_ev_charger_reason
sensor.solar_ev_charger_estimated_power_w
```

Binary sensors:

```text
binary_sensor.solar_ev_charger_has_surplus
binary_sensor.solar_ev_charger_in_cheap_hours
binary_sensor.solar_ev_charger_in_solar_window
binary_sensor.solar_ev_charger_home_battery_protected
binary_sensor.solar_ev_charger_should_charge
```

Buttons:

```text
button.solar_ev_charger_start_now
button.solar_ev_charger_stop_now
button.solar_ev_charger_recalculate
```

## Tesla example

Example entity mapping:

```text
Grid power sensor: sensor.grid_power
Start charge entity: button.tesla_start_charge
Stop charge entity: button.tesla_stop_charge
Charge amps entity: number.tesla_charging_amps
Car SOC sensor: sensor.tesla_battery_level
Home battery SOC sensor: sensor.huawei_battery_soc
Home battery power sensor: sensor.huawei_battery_power
```

Recommended starting options:

```text
mode = Hybrid
min_amps = 6
max_amps = 16
safety_margin_w = 300
min_surplus_w = 1400
target_car_soc = 80
home_battery_min_soc = 80
allow_home_battery = false
cheap_hours_start = 00:00
cheap_hours_end = 08:00
solar_window_start = 09:00
solar_window_end = 18:00
```

## Generic charger example

If your charger is exposed as a switch:

```text
Start charge entity: switch.ev_charger
Stop charge entity: switch.ev_charger
Charge amps entity: number.ev_charger_current
```

The integration will call:

```yaml
service: switch.turn_on
target:
  entity_id: switch.ev_charger
```

and:

```yaml
service: switch.turn_off
target:
  entity_id: switch.ev_charger
```

## Lovelace dashboard example

```yaml
type: entities
title: Solar EV Charger
entities:
  - entity: select.solar_ev_charger_mode
  - entity: switch.solar_ev_charger_enabled
  - entity: switch.solar_ev_charger_need_car_tomorrow
  - entity: switch.solar_ev_charger_allow_grid_import
  - entity: switch.solar_ev_charger_allow_home_battery
  - entity: number.solar_ev_charger_target_car_soc
  - entity: number.solar_ev_charger_max_amps
  - entity: sensor.solar_ev_charger_available_surplus_w
  - entity: sensor.solar_ev_charger_recommended_amps
  - entity: sensor.solar_ev_charger_current_state
  - entity: sensor.solar_ev_charger_last_action
  - entity: sensor.solar_ev_charger_reason
  - entity: button.solar_ev_charger_start_now
  - entity: button.solar_ev_charger_stop_now
```

## Services

Available services:

```text
solar_ev_charger.start
solar_ev_charger.stop
solar_ev_charger.recalculate
solar_ev_charger.set_mode
```

Example:

```yaml
service: solar_ev_charger.set_mode
data:
  mode: "Solar only"
```

If you have multiple controller instances, include `config_entry_id`.

## Home battery protection

If `Allow home battery` is off, the controller pauses charging when:

- Home battery SOC is below the configured minimum.
- Home battery power indicates discharge.

This protection applies to solar-surplus charging. It does not block explicit cheap-hours charging in `Cheap hours` mode, or in `Hybrid` mode when `Need car tomorrow` or `Allow grid import` is enabled. In those cases the controller assumes the intent is to charge from the grid during the cheap window, and the `Maximum grid import` limit is used to cap the charging current.

During setup, choose the battery power polarity. The default is:

```text
positive = discharging
negative = charging
```

Enable the inverted option if your sensor uses:

```text
positive = charging
negative = discharging
```

`Force charge` can bypass home battery protection, but it still respects target car SOC.

## Internal states

The current state sensor can show:

```text
off
idle
waiting_for_surplus
charging_solar
charging_cheap
charging_forced
paused_no_surplus
paused_home_battery_protection
paused_outside_schedule
manual
error
```

## Safety disclaimer

This integration is software automation only. It is not a certified electrical protection device and does not replace physical safety systems such as breakers, RCDs, certified dynamic load management, grid-code-compliant export control, correct wiring, or work performed by a qualified electrician.

Use conservative limits. Test with supervision. You are responsible for ensuring that your charger, vehicle, inverter, home battery, and electrical installation remain within safe and legal operating limits.

## Roadmap

- Solar forecast support.
- Dynamic electricity price support.
- Automatic planning to reach target SOC by a given time.
- Multi-car support.
- Multi-charger support.
- Power-based control instead of amps-only control.
- Calendar integration.
- Spanish 2.0TD tariff helpers.
- Common Huawei/FusionSolar sensor presets.
- Advanced Tesla behavior.
