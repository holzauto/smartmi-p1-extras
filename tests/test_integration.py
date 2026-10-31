"""Real HA config flows, platforms, grouping, actions and unload."""

from unittest.mock import patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.smartmi_p1_extras.client import CannotConnect
from custom_components.smartmi_p1_extras.const import DOMAIN
from custom_components.smartmi_p1_extras.diagnostics import async_get_config_entry_diagnostics


async def test_config_flow_success_and_duplicate(hass, connection_data, device_state):
    with (
        patch(
            "custom_components.smartmi_p1_extras.config_flow.P1Client.status",
            return_value=device_state,
        ),
        patch("custom_components.smartmi_p1_extras.async_setup_entry", return_value=True),
    ):
        flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        assert flow["type"] == "form"
        result = await hass.config_entries.flow.async_configure(flow["flow_id"], connection_data)
        assert result["type"] == "create_entry"
        await hass.async_block_till_done()
        flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(flow["flow_id"], connection_data)
        assert result["reason"] == "already_configured"


async def test_config_flow_failures(hass, connection_data):
    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    with patch(
        "custom_components.smartmi_p1_extras.config_flow.P1Client.status",
        side_effect=CannotConnect("unreachable"),
    ):
        result = await hass.config_entries.flow.async_configure(flow["flow_id"], connection_data)
    assert result["errors"] == {"base": "cannot_connect"}
    result = await hass.config_entries.flow.async_configure(
        flow["flow_id"], {**connection_data, "local_key": "bad"}
    )
    assert result["errors"] == {"base": "invalid_key"}


async def test_entities_grouping_actions_diagnostics_and_unload(
    hass, connection_data, device_state
):
    hk_entry = MockConfigEntry(domain="homekit_controller", unique_id="homekit_p1")
    hk_entry.add_to_hass(hass)
    devices = dr.async_get(hass)
    existing = devices.async_get_or_create(
        config_entry_id=hk_entry.entry_id,
        identifiers={("homekit_controller", "test_homekit_p1")},
        name="Smartmi P1",
        manufacturer="Smartmi",
        model="ZMKQJHQP11",
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="test_p1",
        data={
            **connection_data,
            "homekit_device": existing.id,
        },
    )
    entry.add_to_hass(hass)
    with (
        patch(
            "custom_components.smartmi_p1_extras.client.P1Client.status", return_value=device_state
        ),
        patch(
            "custom_components.smartmi_p1_extras.client.P1Client.write",
            return_value={**device_state, "3": "sleep"},
        ) as write,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        registry = er.async_get(hass)
        entities = er.async_entries_for_config_entry(registry, entry.entry_id)
        assert len(entities) == 7
        assert all(entity.device_id != existing.id for entity in entities)
        assert len({entity.device_id for entity in entities}) == 1
        mode = registry.async_get_entity_id("select", DOMAIN, "test_p1_mode")
        pm10 = registry.async_get_entity_id("sensor", DOMAIN, "test_p1_pm10")
        assert hass.states.get(pm10).state == "12"
        await hass.services.async_call(
            "select",
            "select_option",
            {
                "entity_id": mode,
                "option": "sleep",
            },
            blocking=True,
        )
        write.assert_called_once_with("3", "sleep")
        assert hass.states.get(mode).state == "sleep"
        diagnostics = await async_get_config_entry_diagnostics(hass, entry)
        assert "local_key" not in str(diagnostics)
        assert connection_data["local_key"] not in str(diagnostics)
        # Missing firmware datapoints must not be fabricated or retained as current values.
        entry.runtime_data.async_set_updated_data({"3": "auto"})
        await hass.async_block_till_done()
        assert hass.states.get(pm10).state == "unavailable"
        assert await hass.config_entries.async_unload(entry.entry_id)
        assert devices.async_get(existing.id) is not None
        assert hk_entry.entry_id == devices.async_get(existing.id).config_entry_id


async def test_setup_retries_on_unreachable_device(hass, connection_data):
    entry = MockConfigEntry(domain=DOMAIN, unique_id="test_p1", data=connection_data)
    entry.add_to_hass(hass)
    with patch(
        "custom_components.smartmi_p1_extras.client.P1Client.status",
        side_effect=CannotConnect("unreachable"),
    ):
        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert entry.state.value == "setup_retry"
