"""Exercise real HA services and the LAN client without HomeKit or a cloud SDK."""

from unittest.mock import patch

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.smartmi_p1_extras.const import DOMAIN


class LocalDevice:
    """Simulate only the TinyTuya socket boundary, not integration behavior."""

    def __init__(self, state):
        self.state = dict(state)
        self.writes = []
        self.fail_read = False
        self.reject = None

    def set_dpsUsed(self, value):
        self.query = value

    def set_socketTimeout(self, value):
        pass

    def set_socketRetryLimit(self, value):
        pass

    def set_socketPersistent(self, value):
        pass

    def status(self):
        if self.fail_read:
            raise OSError("Disconnected")
        return {"dps": dict(self.state)}

    def set_value(self, dp, value):
        self.writes.append((dp, value))
        if dp == self.reject:
            return {"Err": "914"}
        self.state[dp] = value
        return None  # Real Tuya devices can acknowledge without any datapoints.


@pytest.fixture
async def standalone(hass, connection_data, device_state):
    device = LocalDevice(device_state)
    entry = MockConfigEntry(domain=DOMAIN, version=2, unique_id="test_p1", data=connection_data)
    entry.add_to_hass(hass)
    with patch("custom_components.smartmi_p1_extras.client.tinytuya.Device", return_value=device):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        registry = er.async_get(hass)
        ids = {
            key: registry.async_get_entity_id(platform, DOMAIN, f"test_p1_{key}")
            for platform, key in (
                ("fan", "fan"),
                ("select", "mode"),
                ("sensor", "pm25"),
                ("sensor", "filter_life"),
                ("sensor", "pm10"),
            )
        }
        yield entry, device, ids
        await hass.config_entries.async_unload(entry.entry_id)


async def call(hass, domain, service, entity_id, **data):
    await hass.services.async_call(domain, service, {"entity_id": entity_id, **data}, blocking=True)


async def test_fresh_setup_creates_complete_device_without_homekit(
    hass, connection_data, device_state
):
    device = LocalDevice(device_state)
    with patch("custom_components.smartmi_p1_extras.client.tinytuya.Device", return_value=device):
        flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        assert "homekit_device" not in {str(key) for key in flow["data_schema"].schema}
        result = await hass.config_entries.flow.async_configure(flow["flow_id"], connection_data)
        await hass.async_block_till_done()
        assert result["type"] == "create_entry"
        entry = result["result"]
        assert entry.version == 2
        assert not hass.config_entries.async_entries("homekit_controller")
        entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
        assert len(entities) == 10
        assert not device.writes  # Setup must never power on or change the mode.
        await hass.config_entries.async_unload(entry.entry_id)


async def test_power_and_manual_speed(hass, standalone):
    entry, device, ids = standalone
    assert hass.states.get(ids["pm25"]).state == "5"
    assert hass.states.get(ids["pm25"]).attributes["device_class"] == "pm25"
    assert hass.states.get(ids["filter_life"]).state == "59"
    assert hass.states.get(ids["filter_life"]).attributes["unit_of_measurement"] == "%"
    assert hass.states.get(ids["fan"]).attributes["percentage"] is None
    await call(hass, "fan", "turn_off", ids["fan"])
    assert device.writes == [("1", False)]
    assert hass.states.get(ids["fan"]).state == "off"
    assert hass.states.get(ids["fan"]).attributes["percentage"] == 0
    device.writes.clear()
    await call(hass, "fan", "set_percentage", ids["fan"], percentage=27)
    assert device.writes == [("3", "manual"), ("109", 27), ("1", True)]
    assert hass.states.get(ids["fan"]).state == "on"
    assert hass.states.get(ids["fan"]).attributes["percentage"] == 27
    assert hass.states.get(ids["mode"]).state == "manual"
    device.writes.clear()
    await call(hass, "fan", "set_percentage", ids["fan"], percentage=0)
    assert device.writes == [("1", False)]  # Never send DP109=0: valid range is 1..100.


async def test_presets_are_consistent_with_existing_mode_select(hass, standalone):
    entry, device, ids = standalone
    await call(hass, "fan", "turn_on", ids["fan"], preset_mode="sleep")
    assert device.writes == [("3", "sleep"), ("1", True)]
    assert hass.states.get(ids["fan"]).attributes["preset_mode"] == "sleep"
    assert hass.states.get(ids["fan"]).attributes["percentage"] is None
    assert hass.states.get(ids["mode"]).state == "sleep"
    await call(hass, "select", "select_option", ids["mode"], option="auto")
    assert hass.states.get(ids["fan"]).attributes["preset_mode"] == "auto"
    device.writes.clear()
    with pytest.raises(HomeAssistantError):
        await call(hass, "fan", "turn_on", ids["fan"], preset_mode="auto", percentage=50)
    assert not device.writes


async def test_failed_command_is_unavailable_then_recovers(hass, standalone):
    entry, device, ids = standalone
    device.reject = "109"
    with pytest.raises(HomeAssistantError):
        await call(hass, "fan", "set_percentage", ids["fan"], percentage=25)
    assert device.writes == [("3", "manual"), ("109", 25)]  # Stop after first rejected write.
    assert hass.states.get(ids["fan"]).state == "unavailable"
    device.reject = None
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(ids["fan"]).state == "on"
    assert hass.states.get(ids["fan"]).attributes["percentage"] == 42
    device.fail_read = True
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(ids["pm25"]).state == "unavailable"
    device.fail_read = False
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(ids["pm25"]).state == "5"


async def test_v1_migration_keeps_existing_entity_ids_and_homekit(
    hass, connection_data, device_state
):
    homekit = MockConfigEntry(domain="homekit_controller", data={"test": "untouched"})
    homekit.add_to_hass(hass)
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        unique_id="test_p1",
        title="Smartmi P1 Extras",
        data={**connection_data, "homekit_device": "old_homekit_device_id"},
    )
    entry.add_to_hass(hass)
    devices = dr.async_get(hass)
    old_device = devices.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "test_p1")},
        name="Smartmi P1 Extras",
    )
    registry = er.async_get(hass)
    old_sensor = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "test_p1_pm10",
        config_entry=entry,
        device_id=old_device.id,
        suggested_object_id="my_preserved_pm10",
    )
    with patch(
        "custom_components.smartmi_p1_extras.client.P1Client.status", return_value=device_state
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.version == 2
        assert "homekit_device" not in entry.data
        assert entry.title == "Smartmi P1 Local"
        assert (
            registry.async_get_entity_id("sensor", DOMAIN, "test_p1_pm10") == old_sensor.entity_id
        )
        assert registry.async_get(old_sensor.entity_id).device_id == old_device.id
        assert hass.states.get(old_sensor.entity_id).state == "12"
        assert homekit.data == {"test": "untouched"}
        assert hass.config_entries.async_get_entry(homekit.entry_id) is homekit
        await hass.config_entries.async_unload(entry.entry_id)
