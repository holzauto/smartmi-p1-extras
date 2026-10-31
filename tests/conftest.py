"""Use Home Assistant's real test fixtures with no network/device access."""

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def connection_data():
    return {
        "host": "192.0.2.10",
        "device_id": "test_p1",
        "local_key": "0123456789abcdef",
        "protocol_version": "3.3",
    }


@pytest.fixture
def device_state():
    return {
        "1": True,
        "2": 5,
        "3": "auto",
        "7": False,
        "101": True,
        "102": 12,
        "103": "0_hour",
        "104": 59,
        "105": 534,
        "109": 42,
        "110": "BRIGHTNESS_LOW",
    }
