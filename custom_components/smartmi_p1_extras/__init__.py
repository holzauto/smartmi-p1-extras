"""Standalone local control of the Smartmi P1, with no HomeKit dependency."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant

from .client import P1Client
from .const import CONF_DEVICE_ID, CONF_LOCAL_KEY, CONF_PROTOCOL, LEGACY_HOMEKIT_DEVICE, NAME
from .coordinator import P1Coordinator

PLATFORMS = [Platform.FAN, Platform.SELECT, Platform.SENSOR, Platform.SWITCH, Platform.LOCK]


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Retain the domain, device identity and all pre-existing entity unique IDs."""
    if entry.version > 2:
        return False
    if entry.version == 1:
        data = dict(entry.data)
        data.pop(LEGACY_HOMEKIT_DEVICE, None)
        title = NAME if entry.title == "Smartmi P1 Extras" else entry.title
        hass.config_entries.async_update_entry(entry, data=data, version=2, title=title)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Validate local communication before exposing any entities."""
    client = P1Client(
        entry.data[CONF_HOST],
        entry.data[CONF_DEVICE_ID],
        entry.data[CONF_LOCAL_KEY],
        entry.data[CONF_PROTOCOL],
    )
    coordinator = P1Coordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload this integration's local entities."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
