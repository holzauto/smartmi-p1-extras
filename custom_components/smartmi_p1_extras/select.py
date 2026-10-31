"""Explicit P1 modes, timer and display settings."""

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DISPLAY_MODES, DP_DISPLAY, DP_MODE, DP_TIMER, MODES, TIMERS
from .entity import P1Entity

SELECTS = (
    (DP_MODE, "mode", MODES),
    (DP_TIMER, "timer", TIMERS),
    (DP_DISPLAY, "display", DISPLAY_MODES),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    async_add_entities(
        P1Select(entry.runtime_data, entry, dp, key, options) for dp, key, options in SELECTS
    )


class P1Select(P1Entity, SelectEntity):
    def __init__(self, coordinator, entry, dp, key, options) -> None:
        super().__init__(coordinator, entry, dp, key)
        self._attr_options = list(options)
        if dp != DP_MODE:
            self._attr_entity_category = EntityCategory.CONFIG

    @property
    def current_option(self) -> str | None:
        return self.dp_value if self.dp_value in self._attr_options else None

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_write(self.dp, option)
