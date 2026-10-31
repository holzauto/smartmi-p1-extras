"""Standalone local P1 air-quality and filter measurements."""

import math

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfDensity, UnitOfRatio, UnitOfTime
from homeassistant.helpers.entity import EntityCategory

from .const import DP_FILTER_HOURS, DP_FILTER_LIFE, DP_PM10, DP_PM25
from .entity import P1Entity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    async_add_entities(
        [
            P1Sensor(
                entry.runtime_data,
                entry,
                DP_PM25,
                "pm25",
                SensorDeviceClass.PM25,
                UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
            ),
            P1Sensor(
                entry.runtime_data,
                entry,
                DP_FILTER_LIFE,
                "filter_life",
                None,
                UnitOfRatio.PERCENTAGE,
            ),
            P1Sensor(
                entry.runtime_data,
                entry,
                DP_PM10,
                "pm10",
                SensorDeviceClass.PM10,
                UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
            ),
            P1Sensor(
                entry.runtime_data,
                entry,
                DP_FILTER_HOURS,
                "filter_hours",
                SensorDeviceClass.DURATION,
                UnitOfTime.HOURS,
            ),
        ]
    )


class P1Sensor(P1Entity, SensorEntity):
    def __init__(self, coordinator, entry, dp, key, device_class, unit) -> None:
        super().__init__(coordinator, entry, dp, key)
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        if dp in (DP_PM25, DP_PM10):
            self._attr_state_class = SensorStateClass.MEASUREMENT
        else:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
            self._attr_icon = "mdi:air-filter"

    @property
    def native_value(self) -> int | float | None:
        value = self.dp_value
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            return None
        if self.dp == DP_FILTER_LIFE and value > 100:
            return None
        return value
