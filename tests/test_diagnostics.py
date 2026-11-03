"""Tests for diagnostics."""

from homeassistant.components.diagnostics import REDACTED

from custom_components.myjudo.diagnostics import async_get_config_entry_diagnostics


async def test_diagnostics_redacts_account(hass, setup_integration):
    result = await async_get_config_entry_diagnostics(hass, setup_integration)
    entry = result["entry"]
    assert entry["title"] == REDACTED
    assert entry["unique_id"] == REDACTED
    assert entry["data"]["username"] == REDACTED
    assert entry["data"]["password"] == REDACTED
    assert "judouser" not in repr(entry)
