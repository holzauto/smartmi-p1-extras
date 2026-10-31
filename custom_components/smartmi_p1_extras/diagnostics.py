"""Diagnostic export excludes keys and network/device identifiers."""


async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = entry.runtime_data
    return {
        "protocol_version": entry.data["protocol_version"],
        "last_update_success": coordinator.last_update_success,
        "available_datapoints": sorted((coordinator.data or {}).keys()),
    }
