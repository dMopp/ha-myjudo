# Changelog

## [0.3.2] - 2026-11-11

### Changed
- Logs in the way JUDO's JU-Control app does (app key `JC`, no `nohash` field). The JU-Control app and ju-control.app use the same server as before (`www.myjudo.eu/interface/`), so entities, entity IDs and statistics stay unchanged and no reconfiguration is needed
- Texts now speak of the JU-Control cloud instead of myjudo.eu, which JUDO no longer maintains as a website

### Fixed
- A rejected login no longer stops the integration for good. During JUDO's server maintenance (2026-11-06 to 2026-11-09) the cloud rejected valid logins, the integration treated that as a wrong password and stayed unavailable until it was reloaded by hand. Now it keeps retrying, asks for the password only after logins have failed for an hour, and withdraws that prompt once a login works again

## [0.3.1] - 2026-11-04

### Fixed
- Switching holiday mode to "off" only reopens the valve when leaving the "lock" variant. Before, it always sent the open command, so leaving holiday mode 1 or 2 could reopen a valve that the leakage protection had closed after a leak alarm
- Setting the sleep mode to 0 only opens the valve when a sleep mode is running. Before, it always sent the open command, with the same risk of reopening a valve closed by the leakage protection

## [0.3.0] - 2026-11-04

### Changed
- **Breaking:** the integration domain is now `judo_myjudo` (folder `custom_components/judo_myjudo`) instead of `myjudo`, which is already used by another integration in the HACS catalog. To migrate an existing install: remove the JUDO myjudo integration in Home Assistant, delete `config/custom_components/myjudo`, update via HACS, restart and add the integration again. Entity IDs may change.

## [0.2.1] - 2026-11-03

### Fixed
- Diagnostics now also redact the config entry `title` and `unique_id`, which contain the myjudo.eu login name

## [0.2.0] - 2026-10-29

### Changed
- Renamed `JudoMessage.type` to `JudoMessage.msg_type` to avoid shadowing the built-in `type` function
- Added serial existence checks in `coordinator.py` (`async_write`, `set_optimistic`) and `entity.py` (`device` property, `has_value`) to prevent errors when device data is unavailable
- Fixed timezone handling in `_parse_local()` to properly handle both timezone-aware and timezone-naive datetime strings
- Updated `JudoMessageSensor` to return raw message code (e.g. `unknown_28`) for unrecognized message codes instead of "other"
- Updated diagnostic attributes in `JudoMessageSensor` to use `msg_type` instead of `type`

### Fixed
- Potential `TypeError` when accessing `JudoMessage.type` (now `msg_type`)
- Potential `KeyError` when serial is not present in coordinator data
- Timezone comparison errors when parsing datetime strings with mixed timezone awareness
