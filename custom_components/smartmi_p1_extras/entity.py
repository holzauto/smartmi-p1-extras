"""Shared supplemental entity behavior."""

from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, CONF_HOMEKIT_DEVICE, DOMAIN


class P1Entity(CoordinatorEntity):
    """A datapoint may be absent on a different firmware: report unavailable."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, dp: str, key: str) -> None:
        super().__init__(coordinator)
        self.dp = dp
        self._attr_unique_id = f"{entry.data[CONF_DEVICE_ID]}_{key}"
        self._attr_translation_key = key
        registry = dr.async_get(coordinator.hass)
        existing = registry.async_get(entry.data.get(CONF_HOMEKIT_DEVICE, ""))
        # HA 2026.10 separates device ownership by integration. Register our own
        # device rather than copying HomeKit identifiers or changing its registry entry.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])},
            name="Smartmi P1 Extras",
            manufacturer="Smartmi",
            model="Air Purifier P1",
        )
        if existing and existing.area_id:
            area = ar.async_get(coordinator.hass).async_get_area(existing.area_id)
            if area:
                self._attr_device_info["suggested_area"] = area.name

    @property
    def available(self) -> bool:
        return super().available and self.dp in (self.coordinator.data or {})

    @property
    def dp_value(self):
        return (self.coordinator.data or {}).get(self.dp)
