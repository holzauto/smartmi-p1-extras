"""Changing the host/key must keep the entry and device identity stable."""

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import SOURCE_RECONFIGURE
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.smartmi_p1_extras.const import DOMAIN


async def test_reconfigure_updates_host_without_creating_entry(hass, connection_data, device_state):
    entry = MockConfigEntry(domain=DOMAIN, unique_id="test_p1", data=connection_data)
    entry.add_to_hass(hass)
    with (
        patch(
            "custom_components.smartmi_p1_extras.config_flow.P1Client.status",
            return_value=device_state,
        ),
        patch.object(hass.config_entries, "async_reload", new_callable=AsyncMock),
    ):
        flow = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
        )
        assert flow["type"] == "form"
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"], {**connection_data, "host": "192.0.2.20"}
        )
        assert result["reason"] == "reconfigure_successful"
        assert entry.data["host"] == "192.0.2.20"
        assert entry.unique_id == "test_p1"
        assert len(hass.config_entries.async_entries(DOMAIN)) == 1
        await hass.async_block_till_done()
