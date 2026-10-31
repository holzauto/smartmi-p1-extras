"""P1 sound setting."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DP_SOUND
from .entity import P1Entity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    async_add_entities([P1Sound(entry.runtime_data, entry, DP_SOUND, "sound")])


class P1Sound(P1Entity, SwitchEntity):
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self) -> bool | None:
        return self.dp_value if type(self.dp_value) is bool else None

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_write(self.dp, True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_write(self.dp, False)
