"""Protocol failure cases and actual write confirmation."""

from unittest.mock import MagicMock, call, patch

import pytest

from custom_components.smartmi_p1_extras.client import CannotConnect, P1Client, extract_dps
from custom_components.smartmi_p1_extras.const import P1_QUERY_DPS


@pytest.mark.parametrize(
    "response",
    [None, {}, {"Error": "bad", "dps": {"3": "auto"}}, {"Err": "914"}, {"dps": []}, {"data": None}],
)
def test_invalid_response(response):
    with pytest.raises(CannotConnect):
        extract_dps(response)


def test_wrapped_response():
    assert extract_dps({"data": {"dps": {102: 0}}}) == {"102": 0}


def test_p1_status_queries_explicit_datapoints_without_writing():
    device = MagicMock()
    device.status.return_value = {"dps": {"3": "manual", "102": 1}}
    with patch(
        "custom_components.smartmi_p1_extras.client.tinytuya.Device", return_value=device
    ) as constructor:
        client = P1Client("192.0.2.10", "test", "0123456789abcdef", "3.3")
    assert constructor.call_args.kwargs["dev_type"] == "device22"
    device.set_dpsUsed.assert_called_once_with(dict.fromkeys(P1_QUERY_DPS))
    assert client.status() == {"3": "manual", "102": 1}
    device.set_value.assert_not_called()
    device.set_multiple_values.assert_not_called()


def test_write_readback_and_restrictions():
    device = MagicMock()
    device.set_value.return_value = None
    device.status.return_value = {"dps": {"3": "sleep"}}
    with patch("custom_components.smartmi_p1_extras.client.tinytuya.Device", return_value=device):
        client = P1Client("192.0.2.10", "test", "0123456789abcdef", "3.4")
    assert client.write("3", "sleep") == {"3": "sleep"}
    device.set_value.assert_called_once_with("3", "sleep")
    for dp, value in [
        ("1", 1),
        ("104", 100),
        ("3", "night"),
        ("7", 1),
        ("109", 0),
        ("109", 101),
        ("109", True),
    ]:
        with pytest.raises(ValueError):
            client.write(dp, value)
    device.status.return_value = {"dps": {"3": "auto"}}
    with pytest.raises(CannotConnect, match="did not confirm"):
        client.write("3", "sleep")


def test_device_errors_do_not_expose_secrets():
    device = MagicMock()
    device.status.side_effect = RuntimeError("SECRET_KEY_AND_RAW_PAYLOAD")
    with patch("custom_components.smartmi_p1_extras.client.tinytuya.Device", return_value=device):
        client = P1Client("192.0.2.10", "test", "0123456789abcdef", "3.3")
    with pytest.raises(CannotConnect) as err:
        client.status()
    assert "SECRET" not in str(err.value)


def test_multi_write_validates_everything_before_first_packet():
    device = MagicMock()
    with patch("custom_components.smartmi_p1_extras.client.tinytuya.Device", return_value=device):
        client = P1Client("192.0.2.10", "test", "0123456789abcdef", "3.3")
    with pytest.raises(ValueError):
        client.write_many({"3": "manual", "109": 101, "1": True})
    device.set_value.assert_not_called()
    device.set_value.return_value = None
    device.status.return_value = {"dps": {"3": "manual", "109": 20, "1": True}}
    assert client.write_many({"3": "manual", "109": 20, "1": True})["109"] == 20
    assert device.set_value.call_args_list == [
        call("3", "manual"),
        call("109", 20),
        call("1", True),
    ]
    device.status.return_value = {"dps": {"3": "auto", "109": 20, "1": True}}
    with pytest.raises(CannotConnect, match="did not confirm"):
        client.write_many({"3": "manual", "109": 20, "1": True})
