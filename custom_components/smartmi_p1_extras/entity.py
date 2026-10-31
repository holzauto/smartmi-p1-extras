"""Shared local entity behavior."""

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, DOMAIN


class P1Entity(CoordinatorEntity):
    """A datapoint may be absent on a different firmware: report unavailable."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, dp: str, key: str) -> None:
        super().__init__(coordinator)
        self.dp = dp
        self._attr_unique_id = f"{entry.data[CONF_DEVICE_ID]}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])},
            name="Smartmi P1",
            manufacturer="Smartmi",
            model="Air Purifier P1",
        )

    @property
    def available(self) -> bool:
        return super().available and self.dp in (self.coordinator.data or {})

    @property
    def dp_value(self):
        return (self.coordinator.data or {}).get(self.dp)
