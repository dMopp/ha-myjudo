"""Config flow for JUDO myjudo."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
import voluptuous as vol

from .api import JudoAuthError, JudoClient, JudoError
from .const import (
    CONF_SODIUM_INPUT,
    CONF_SODIUM_LIMIT,
    CONF_SOFTWELL_P,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SODIUM_INPUT,
    DEFAULT_SODIUM_LIMIT,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)
from .coordinator import JudoConfigEntry

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): TextSelector(
            TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="username")
        ),
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD, autocomplete="current-password"
            )
        ),
    }
)


class JudoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for JUDO myjudo."""

    VERSION = 1

    async def _validate(self, username: str, password: str) -> str | None:
        """Try to log in. Return an error key or None."""
        client = JudoClient(async_get_clientsession(self.hass), username, password)
        try:
            await client.login()
        except JudoAuthError:
            return "invalid_auth"
        except JudoError:
            return "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected error during login")
            return "unknown"
        return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_USERNAME].strip().lower())
            self._abort_if_unique_id_configured()
            if not (
                error := await self._validate(
                    user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )
            ):
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )
            errors["base"] = error
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, user_input),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            username = entry.data[CONF_USERNAME]
            if not (error := await self._validate(username, user_input[CONF_PASSWORD])):
                return self.async_update_reload_and_abort(
                    entry, data_updates=user_input
                )
            errors["base"] = error
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {vol.Required(CONF_PASSWORD): USER_SCHEMA.schema[CONF_PASSWORD]}
            ),
            description_placeholders={"username": entry.data[CONF_USERNAME]},
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: JudoConfigEntry) -> OptionsFlow:
        return JudoOptionsFlow()


class JudoOptionsFlow(OptionsFlow):
    """Options: polling interval, device variant and sodium limit."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=3600,
                        step=1,
                        unit_of_measurement="s",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(CONF_SOFTWELL_P, default=False): bool,
                vol.Required(
                    CONF_SODIUM_INPUT, default=DEFAULT_SODIUM_INPUT
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0,
                        max=500,
                        step=0.01,
                        unit_of_measurement="mg/L",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_SODIUM_LIMIT, default=DEFAULT_SODIUM_LIMIT
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=500,
                        step=1,
                        unit_of_measurement="mg/L",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                schema, self.config_entry.options
            ),
        )
