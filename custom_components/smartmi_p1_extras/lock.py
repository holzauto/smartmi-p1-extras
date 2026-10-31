"""P1 child lock."""

from homeassistant.components.lock import LockEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DP_CHILD_LOCK
from .entity import P1Entity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    async_add_entities([P1ChildLock(entry.runtime_data, entry, DP_CHILD_LOCK, "child_lock")])


class P1ChildLock(P1Entity, LockEntity):
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def is_locked(self) -> bool | None:
        return self.dp_value if type(self.dp_value) is bool else None

    async def async_lock(self, **kwargs) -> None:
        await self.coordinator.async_write(self.dp, True)

    async def async_unlock(self, **kwargs) -> None:
        await self.coordinator.async_write(self.dp, False)
