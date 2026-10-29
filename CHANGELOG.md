# Changelog

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
