"""Bounded synchronous LAN transport; never calls a Tuya cloud API."""

from __future__ import annotations

import threading
from typing import Any

import tinytuya

from .const import (
    DISPLAY_MODES,
    DP_CHILD_LOCK,
    DP_DISPLAY,
    DP_MODE,
    DP_POWER,
    DP_SOUND,
    DP_SPEED,
    DP_TIMER,
    MODES,
    P1_QUERY_DPS,
    TIMERS,
)


class CannotConnect(Exception):
    """The local transport or device response failed."""


def extract_dps(response: Any) -> dict[str, Any]:
    """Accept flat and wrapped responses, without exposing raw payloads."""
    if not isinstance(response, dict) or "Error" in response or "Err" in response:
        raise CannotConnect("No valid local response; check key, protocol and connectivity")
    data = response.get("data", response)
    if not isinstance(data, dict) or "Error" in data or "Err" in data:
        raise CannotConnect("Invalid local response")
    dps = data.get("dps")
    if not isinstance(dps, dict) or not dps:
        raise CannotConnect("Local response contains no datapoints")
    return {str(key): value for key, value in dps.items()}


def validate_write(dp: str, value: Any) -> None:
    """Restrict writes to documented P1 controls, never sensor/filter counters."""
    choices = {DP_MODE: MODES, DP_TIMER: TIMERS, DP_DISPLAY: DISPLAY_MODES}
    if dp in choices and isinstance(value, str) and value in choices[dp]:
        return
    if dp in (DP_POWER, DP_CHILD_LOCK, DP_SOUND) and type(value) is bool:
        return
    if dp == DP_SPEED and type(value) is int and 1 <= value <= 100:
        return
    raise ValueError("Unsupported P1 datapoint or value")


class P1Client:
    """One short-lived TCP connection per operation, serialized across workers."""

    def __init__(self, host: str, device_id: str, local_key: str, protocol: str) -> None:
        # This P1 uses the explicit-DP variant of protocol 3.3. Automatic TinyTuya
        # detection resets the query list to DP1 and conceals the other settings.
        self._device = tinytuya.Device(
            device_id,
            host,
            local_key,
            version=float(protocol),
            dev_type="device22" if protocol == "3.3" else "default",
        )
        self._device.set_dpsUsed(dict.fromkeys(P1_QUERY_DPS))
        self._device.set_socketTimeout(3)
        self._device.set_socketRetryLimit(1)
        self._device.set_socketPersistent(False)
        self._lock = threading.Lock()

    def status(self) -> dict[str, Any]:
        """Read state without changing device settings."""
        with self._lock:
            try:
                return extract_dps(self._device.status())
            except CannotConnect:
                raise
            except Exception:
                raise CannotConnect("Local device read failed") from None

    def write(self, dp: str, value: Any) -> dict[str, Any]:
        """Write one setting, then return the state actually reported by the device."""
        return self.write_many({dp: value})

    def write_many(self, changes: dict[str, Any]) -> dict[str, Any]:
        """Apply an ordered command and confirm every field in one readback."""
        if not changes:
            raise ValueError("No P1 settings supplied")
        # Validate the complete command before sending its first packet.
        for dp, value in changes.items():
            validate_write(dp, value)
        with self._lock:
            try:
                for dp, value in changes.items():
                    result = self._device.set_value(dp, value)
                    if isinstance(result, dict) and ("Error" in result or "Err" in result):
                        raise CannotConnect("Local device rejected the setting")
                # Empty acknowledgements are normal. Read back rather than assuming success.
                dps = extract_dps(self._device.status())
                if any(
                    dp not in dps or type(dps[dp]) is not type(value) or dps[dp] != value
                    for dp, value in changes.items()
                ):
                    raise CannotConnect("Device did not confirm the setting; refresh and retry")
                return dps
            except CannotConnect:
                raise
            except Exception:
                raise CannotConnect("Local device write failed") from None
