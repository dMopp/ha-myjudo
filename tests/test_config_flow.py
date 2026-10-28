"""Tests for the config and options flow."""

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResultType

from custom_components.myjudo.api import BASE_URL
from custom_components.myjudo.const import (
    CONF_SODIUM_INPUT,
    CONF_SODIUM_LIMIT,
    CONF_SOFTWELL_P,
    DOMAIN,
)

USER_INPUT = {CONF_USERNAME: "JudoUser", CONF_PASSWORD: "secret"}


async def test_user_flow(hass, mock_api):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "JudoUser"
    assert result["data"] == USER_INPUT
    assert result["result"].unique_id == "judouser"


async def test_user_flow_invalid_auth_then_ok(hass, aioclient_mock, mock_api):
    aioclient_mock.clear_requests()
    aioclient_mock.get(
        f"{BASE_URL}?command=login", json={"status": "error", "data": "login failed"}
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    aioclient_mock.clear_requests()
    aioclient_mock.get(
        f"{BASE_URL}?command=login", json={"status": "ok", "token": "TOKEN"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_cannot_connect(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}?command=login", status=503)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["errors"] == {"base": "cannot_connect"}


async def test_already_configured(hass, setup_integration):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth(hass, setup_integration):
    result = await setup_integration.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert setup_integration.data[CONF_PASSWORD] == "new"


async def test_options(hass, setup_integration):
    result = await hass.config_entries.options.async_init(setup_integration.entry_id)
    assert result["type"] is FlowResultType.FORM
    options = {
        CONF_SCAN_INTERVAL: 60,
        CONF_SOFTWELL_P: False,
        CONF_SODIUM_INPUT: 7.74,
        CONF_SODIUM_LIMIT: 200,
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], options
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert setup_integration.options == options
