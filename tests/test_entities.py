"""Tests for setup, entity states and commands."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
import pytest

from custom_components.myjudo.api import BASE_URL
from custom_components.myjudo.const import CONF_SODIUM_INPUT, CONF_SODIUM_LIMIT, DOMAIN

from .conftest import SERIAL, writes


def entity_id(hass, platform: str, key: str) -> str:
    eid = er.async_get(hass).async_get_entity_id(platform, DOMAIN, f"{SERIAL}_{key}")
    assert eid, f"{platform}.{key} missing"
    return eid


def state(hass, platform: str, key: str):
    return hass.states.get(entity_id(hass, platform, key))


async def test_states(hass, setup_integration):
    assert setup_integration.state is ConfigEntryState.LOADED
    assert state(hass, "sensor", "total_water").state == "667.249"
    assert (
        state(hass, "sensor", "total_water").attributes["unit_of_measurement"] == "m³"
    )
    assert state(hass, "sensor", "hard_water").state == "227.756"
    assert state(hass, "sensor", "input_hardness").state == "15"
    assert state(hass, "sensor", "salt_range").state == "205"
    assert state(hass, "sensor", "next_service").state == "354"
    assert state(hass, "sensor", "last_message").state == "w_28"
    assert (
        state(hass, "sensor", "last_message_time").state == "2026-02-22T08:10:06+00:00"
    )
    assert state(hass, "sensor", "last_regeneration").state == "unknown"
    assert state(hass, "number", "output_hardness").state == "5"
    assert state(hass, "number", "salt_stock").state == "20.5"
    assert state(hass, "number", "max_flow").state == "3000"
    assert state(hass, "select", "holiday_mode").state == "off"
    assert state(hass, "valve", "valve").state == "open"
    assert state(hass, "binary_sensor", "online").state == "on"
    assert state(hass, "binary_sensor", "regeneration_running").state == "off"
    # Register 93 is all zeros: no backup battery, so no entity
    assert not er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{SERIAL}_battery"
    )


async def test_unload(hass, setup_integration):
    assert await hass.config_entries.async_unload(setup_integration.entry_id)
    assert setup_integration.state is ConfigEntryState.NOT_LOADED


async def test_auth_failure_starts_reauth(hass, config_entry, aioclient_mock):
    aioclient_mock.get(
        f"{BASE_URL}?command=login", json={"status": "error", "data": "login failed"}
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress()
    assert any(f["context"]["source"] == "reauth" for f in flows)


async def test_offline_cloud_retries(hass, config_entry, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}?command=login", status=500)
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_set_numbers(hass, setup_integration, mock_api):
    for key, value in (("max_flow", 2500), ("salt_stock", 25), ("output_hardness", 6)):
        await hass.services.async_call(
            "number",
            "set_value",
            {ATTR_ENTITY_ID: entity_id(hass, "number", key), "value": value},
            blocking=True,
        )
    assert writes(mock_api) == [("75", "C409"), ("94", "A861"), ("60", "06")]
    assert state(hass, "number", "max_flow").state == "2500"


async def test_sleep_mode(hass, setup_integration, mock_api):
    eid = entity_id(hass, "number", "sleep_mode")
    await hass.services.async_call(
        "number", "set_value", {ATTR_ENTITY_ID: eid, "value": 4}, blocking=True
    )
    await hass.services.async_call(
        "number", "set_value", {ATTR_ENTITY_ID: eid, "value": 0}, blocking=True
    )
    assert writes(mock_api) == [("171", "4"), ("171", ""), ("73", "")]


async def test_sodium_limit(hass, setup_integration, mock_api):
    hass.config_entries.async_update_entry(
        setup_integration, options={CONF_SODIUM_INPUT: 7.74, CONF_SODIUM_LIMIT: 100}
    )
    await hass.async_block_till_done()
    eid = entity_id(hass, "number", "output_hardness")
    # (15 - 3) * 8.2 + 7.74 = 106.1 mg/L > 100
    with pytest.raises(ServiceValidationError) as exc:
        await hass.services.async_call(
            "number", "set_value", {ATTR_ENTITY_ID: eid, "value": 3}, blocking=True
        )
    assert exc.value.translation_placeholders["minimum"] == "4"
    await hass.services.async_call(
        "number", "set_value", {ATTR_ENTITY_ID: eid, "value": 4}, blocking=True
    )
    assert writes(mock_api) == [("60", "04")]


async def test_valve_select_button(hass, setup_integration, mock_api):
    valve = entity_id(hass, "valve", "valve")
    await hass.services.async_call(
        "valve", "close_valve", {ATTR_ENTITY_ID: valve}, blocking=True
    )
    assert hass.states.get(valve).state == "closed"
    await hass.services.async_call(
        "valve", "open_valve", {ATTR_ENTITY_ID: valve}, blocking=True
    )

    select = entity_id(hass, "select", "holiday_mode")
    await hass.services.async_call(
        "select",
        "select_option",
        {ATTR_ENTITY_ID: select, "option": "lock"},
        blocking=True,
    )
    await hass.services.async_call(
        "select",
        "select_option",
        {ATTR_ENTITY_ID: select, "option": "off"},
        blocking=True,
    )

    await hass.services.async_call(
        "button",
        "press",
        {ATTR_ENTITY_ID: entity_id(hass, "button", "start_regeneration")},
        blocking=True,
    )
    assert writes(mock_api) == [
        ("72", ""),
        ("73", ""),
        ("77", "9"),
        ("73", ""),
        ("77", "0"),
        ("65", ""),
    ]
    assert state(hass, "binary_sensor", "regeneration_running").state == "on"


async def test_write_error(hass, setup_integration, aioclient_mock, device_data):
    aioclient_mock.clear_requests()
    aioclient_mock.get(
        f"{BASE_URL}?command=write+data",
        json={"status": "error", "data": "device offline"},
    )
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "button",
            "press",
            {ATTR_ENTITY_ID: entity_id(hass, "button", "start_regeneration")},
            blocking=True,
        )
