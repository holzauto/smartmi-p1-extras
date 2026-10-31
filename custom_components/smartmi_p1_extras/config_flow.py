"""Manual local setup with connection validation and reconfiguration."""

from __future__ import annotations

from typing import Any

import probatio as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.helpers import selector

from .client import CannotConnect, P1Client
from .const import (
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_PROTOCOL,
    DOMAIN,
    DP_MODE,
    DP_POWER,
    DP_SPEED,
    MODES,
    NAME,
    PROTOCOLS,
)


def schema(defaults: dict[str, Any]) -> vol.Schema:
    fields = {
        vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
        vol.Required(CONF_DEVICE_ID, default=defaults.get(CONF_DEVICE_ID, "")): str,
        vol.Required(CONF_LOCAL_KEY): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
        vol.Required(CONF_PROTOCOL, default=defaults.get(CONF_PROTOCOL, "3.3")): vol.In(PROTOCOLS),
    }
    return vol.Schema(fields)


class P1ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def _validate(self, user_input) -> dict[str, Any]:
        data = dict(user_input)
        data[CONF_HOST] = data[CONF_HOST].strip()
        data[CONF_DEVICE_ID] = data[CONF_DEVICE_ID].strip()
        if not data[CONF_HOST] or not data[CONF_DEVICE_ID]:
            raise ValueError("missing_connection_data")
        if len(data[CONF_LOCAL_KEY].encode("utf-8")) != 16:
            raise ValueError("invalid_key")
        client = P1Client(
            data[CONF_HOST], data[CONF_DEVICE_ID], data[CONF_LOCAL_KEY], data[CONF_PROTOCOL]
        )
        dps = await self.hass.async_add_executor_job(client.status)
        # Standalone control requires power, a known mode and manual fan level.
        if (
            type(dps.get(DP_POWER)) is not bool
            or dps.get(DP_MODE) not in MODES
            or type(dps.get(DP_SPEED)) is not int
            or not 1 <= dps[DP_SPEED] <= 100
        ):
            raise ValueError("unsupported_device")
        return data

    async def async_step_user(self, user_input=None):
        return await self._async_configure("user", user_input)

    async def async_step_reconfigure(self, user_input=None):
        return await self._async_configure("reconfigure", user_input)

    async def _async_configure(self, step_id, user_input):
        errors = {}
        entry = self._get_reconfigure_entry() if step_id == "reconfigure" else None
        defaults = dict(entry.data) if entry else {}
        if user_input is not None:
            defaults.update(user_input)
            try:
                data = await self._validate(user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except ValueError as err:
                errors["base"] = str(err)
            else:
                await self.async_set_unique_id(data[CONF_DEVICE_ID])
                if entry:
                    self._abort_if_unique_id_mismatch()
                    return self.async_update_reload_and_abort(entry, data=data)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=NAME, data=data)
        return self.async_show_form(step_id=step_id, data_schema=schema(defaults), errors=errors)
