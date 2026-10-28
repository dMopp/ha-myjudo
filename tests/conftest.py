"""Fixtures for JUDO myjudo tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.myjudo.api import BASE_URL
from custom_components.myjudo.const import DOMAIN

FIXTURES = Path(__file__).parent / "fixtures"
SERIAL = "0123456789ab"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in all tests."""


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def device_data() -> dict[str, Any]:
    return load_fixture("device_data.json")


@pytest.fixture
def error_messages() -> dict[str, Any]:
    return load_fixture("error_messages.json")


@pytest.fixture
def mock_api(
    aioclient_mock: AiohttpClientMocker, device_data, error_messages
) -> AiohttpClientMocker:
    """Answer login, device data, message log and writes like myjudo.eu does."""
    aioclient_mock.get(
        f"{BASE_URL}?command=login", json={"status": "ok", "token": "TOKEN"}
    )
    aioclient_mock.get(f"{BASE_URL}?command=get+device+data", json=device_data)
    aioclient_mock.get(f"{BASE_URL}?command=get+error+messages", json=error_messages)
    aioclient_mock.get(f"{BASE_URL}?command=write+data", json={"status": "ok"})
    return aioclient_mock


@pytest.fixture
def config_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="judouser",
        unique_id="judouser",
        data={CONF_USERNAME: "judouser", CONF_PASSWORD: "secret"},
    )


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api
) -> MockConfigEntry:
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry


def writes(mock: AiohttpClientMocker) -> list[tuple[str, str]]:
    """(index, data) of all write requests sent so far."""
    result = []
    for _method, url, _data, _headers in mock.mock_calls:
        if url.query.get("command") == "write data":
            result.append((url.query["index"], url.query["data"]))
    return result
