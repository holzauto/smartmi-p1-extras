"""Manual local setup with connection validation and reconfiguration."""

from __future__ import annotations

from typing import Any

import probatio as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import selector

from .client import CannotConnect, P1Client
from .const import (
    CONF_DEVICE_ID,
    CONF_HOMEKIT_DEVICE,
    CONF_LOCAL_KEY,
    CONF_PROTOCOL,
    DOMAIN,
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
        vol.Optional(CONF_HOMEKIT_DEVICE): selector.DeviceSelector(
            selector.DeviceSelectorConfig(integration="homekit_controller")
        ),
    }
    if defaults.get(CONF_HOMEKIT_DEVICE):
        fields[vol.Optional(CONF_HOMEKIT_DEVICE, default=defaults[CONF_HOMEKIT_DEVICE])] = (
            fields.pop(vol.Optional(CONF_HOMEKIT_DEVICE))
        )
    return vol.Schema(fields)


class P1ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _validate(self, user_input) -> dict[str, Any]:
        data = dict(user_input)
        data[CONF_HOST] = data[CONF_HOST].strip()
        data[CONF_DEVICE_ID] = data[CONF_DEVICE_ID].strip()
        if not data[CONF_HOST] or not data[CONF_DEVICE_ID]:
            raise ValueError("missing_connection_data")
        if len(data[CONF_LOCAL_KEY].encode("utf-8")) != 16:
            raise ValueError("invalid_key")
        if device_id := data.get(CONF_HOMEKIT_DEVICE):
            device = dr.async_get(self.hass).async_get(device_id)
            if (
                not device
                or not device.identifiers
                or not any(
                    identifier[0] == "homekit_controller" for identifier in device.identifiers
                )
                or device.manufacturer != "Smartmi"
            ):
                raise ValueError("invalid_device")
        client = P1Client(
            data[CONF_HOST], data[CONF_DEVICE_ID], data[CONF_LOCAL_KEY], data[CONF_PROTOCOL]
        )
        dps = await self.hass.async_add_executor_job(client.status)
        # A Tuya device with only unrelated DPs is not a supported P1.
        if not any(dp in dps for dp in ("3", "102", "103", "105", "110")):
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
                    return self.async_update_reload_and_abort(entry, data_updates=data)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Smartmi P1 Extras", data=data)
        return self.async_show_form(step_id=step_id, data_schema=schema(defaults), errors=errors)
