"""Native HA fan control over the P1's local Tuya datapoints."""

from __future__ import annotations

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.exceptions import HomeAssistantError

from .const import DP_MODE, DP_POWER, DP_SPEED, MODES
from .entity import P1Entity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    async_add_entities([P1Fan(entry.runtime_data, entry)])


class P1Fan(P1Entity, FanEntity):
    """Primary device entity, with actual power and manual target speed."""

    _attr_name = None
    _attr_icon = "mdi:air-purifier"
    _attr_supported_features = (
        FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.SET_SPEED
        | FanEntityFeature.PRESET_MODE
    )
    _attr_preset_modes = list(MODES)
    _attr_speed_count = 100

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, DP_POWER, "fan")
        self._attr_translation_key = "air_purifier"

    @property
    def is_on(self) -> bool | None:
        return self.dp_value if type(self.dp_value) is bool else None

    @property
    def percentage(self) -> int | None:
        if self.is_on is False:
            return 0
        # DP109 is the configured manual level, not the motor speed in auto/sleep.
        if self.is_on is not True or self.preset_mode != "manual":
            return None
        value = self.coordinator.data.get(DP_SPEED)
        return value if type(value) is int and 1 <= value <= 100 else None

    @property
    def preset_mode(self) -> str | None:
        value = self.coordinator.data.get(DP_MODE)
        return value if value in MODES else None

    async def async_turn_on(self, percentage=None, preset_mode=None, **kwargs) -> None:
        if preset_mode is not None and preset_mode not in MODES:
            raise HomeAssistantError("Unsupported Smartmi P1 preset")
        if percentage is not None:
            if preset_mode not in (None, "manual"):
                raise HomeAssistantError("Choose a preset or a manual speed")
            await self.async_set_percentage(percentage)
            return
        changes = {DP_MODE: preset_mode} if preset_mode is not None else {}
        changes[DP_POWER] = True
        await self.coordinator.async_write_many(changes)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_write(DP_POWER, False)

    async def async_set_percentage(self, percentage: int) -> None:
        if type(percentage) is not int or not 0 <= percentage <= 100:
            raise HomeAssistantError("Manual speed must be an integer from 0 to 100")
        if percentage == 0:
            await self.async_turn_off()
            return
        await self.coordinator.async_write_many(
            {DP_MODE: "manual", DP_SPEED: percentage, DP_POWER: True}
        )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode not in MODES:
            raise HomeAssistantError("Unsupported Smartmi P1 preset")
        await self.coordinator.async_write(DP_MODE, preset_mode)
