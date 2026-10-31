"""Additional local P1 measurements."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfDensity, UnitOfTime
from homeassistant.helpers.entity import EntityCategory

from .const import DP_FILTER_HOURS, DP_PM10
from .entity import P1Entity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    async_add_entities(
        [
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
        if dp == DP_PM10:
            self._attr_state_class = SensorStateClass.MEASUREMENT
        else:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> int | float | None:
        value = self.dp_value
        return value if type(value) in (int, float) and value >= 0 else None
