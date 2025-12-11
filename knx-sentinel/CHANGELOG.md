# Changelog

## 0.1.20
- **Fix**: Resolved `NameError` related to Watchdog map scope in `run.py`.
- **Note**: Hotfix for Alias feature.

## 0.1.19
- **Feature**: Added support for Aliases in Watchdog configuration.
  - You can now specify `Watchdog Entities` as `"Address=Friendly Name"` (e.g., `"6/1/1=binary_sensor.heartbeat"`).
  - The MQTT topic will use the Friendly Name instead of the raw address.

## 0.1.18
- **Debug**: Added verbose logging for Watchdog inputs.
- **Fix**: Improved matching logic for `knx_event` destinations.

## 0.1.17
- **Fix**: Added auto-sanitization for configuration strings (handling quotes).
- **Feature**: Added explicit "Heartbeat Received" (Value: 1.0) telemetry to MQTT.

## 0.1.16
- **Fix**: Changed Watchdog to listen to raw `knx_event` to bypass Home Assistant state deduplication.
  - Required User Action: Update `watchdog_entities` to use Group Addresses (e.g., `6/1/1`).
  - Required User Action: Enable `knx: event:` in `configuration.yaml`.

## 0.1.15
- **Feature**: Initial release of "Dead Man's Switch" (Watchdog).
  - Configurable `watchdog_entities` and `watchdog_timeout`.
  - Sends `value: 0.0` with status `timeout` if no heartbeat is received.

## 0.1.14
- **Maintenance**: Internal logic updates for binary sensor state handling.

## 0.1.0 - 0.1.13
- Initial development and stabilization of S6 Overlay and Token Authentication.
