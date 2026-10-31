"""Non-blocking polling and serialized local commands."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import CannotConnect, P1Client
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class P1Coordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Read on a 30-second interval; commands trigger an immediate confirmed update."""

    def __init__(self, hass: HomeAssistant, client: P1Client, entry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=30),
            always_update=False,
        )
        self.client = client
        self.io_lock = asyncio.Lock()

    async def _async_update_data(self) -> dict[str, Any]:
        async with self.io_lock:
            try:
                # A poll must contain the current values; missing DPs become unavailable.
                return await self.hass.async_add_executor_job(self.client.status)
            except CannotConnect as err:
                raise UpdateFailed(str(err)) from None

    async def async_write(self, dp: str, value: Any) -> None:
        async with self.io_lock:
            try:
                data = await self.hass.async_add_executor_job(self.client.write, dp, value)
            except CannotConnect as err:
                self.async_set_update_error(UpdateFailed(str(err)))
                raise HomeAssistantError(str(err)) from None
            self.async_set_updated_data(data)
