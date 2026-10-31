"""The one-time helper exports one device key, never cloud tokens."""

import json
import runpy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

HELPER = Path(__file__).resolve().parents[1] / "scripts/get_local_key.py"


def test_private_file_does_not_overwrite(tmp_path):
    module = runpy.run_path(str(HELPER))
    path = tmp_path / "private" / "p1.local.json"
    module["save_private"](path, {"local_key": "local-test-key"})
    assert path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        module["save_private"](path, {"local_key": "replacement"})
    assert json.loads(path.read_text())["local_key"] == "local-test-key"


def test_qr_export_is_limited_to_selected_device(tmp_path, monkeypatch, capsys):
    output = tmp_path / "private" / "p1.local.json"
    monkeypatch.setattr(
        "sys.argv",
        [str(HELPER), "--host", "192.0.2.10", "--device-id", "test_p1", "--output", str(output)],
    )
    monkeypatch.setattr("getpass.getpass", lambda _: "test-user-code")
    monkeypatch.setattr("builtins.input", lambda _: "")
    login = MagicMock()
    login.qr_code.return_value = {"success": True, "result": {"qrcode": "test-qr-token"}}
    auth = {"terminal_id": "test-terminal", "endpoint": "https://example.invalid"}
    auth.update(
        {k: f"test-{k}" for k in ("t", "uid", "expire_time", "access_token", "refresh_token")}
    )
    login.login_result.return_value = (True, auth)
    monkeypatch.setattr("tuya_sharing.LoginControl", lambda: login)
    manager = MagicMock()
    manager.device_map = {
        "test_p1": SimpleNamespace(id="test_p1", name="P1", local_key="0123456789abcdef"),
        "other": SimpleNamespace(id="other", name="Other", local_key="do-not-export"),
    }
    monkeypatch.setattr("tuya_sharing.Manager", lambda *args: manager)
    monkeypatch.setattr("qrcode.QRCode", MagicMock())
    module = runpy.run_path(str(HELPER))
    module["main"]()
    data = json.loads(output.read_text())
    assert data == {"host": "192.0.2.10", "device_id": "test_p1", "local_key": "0123456789abcdef"}
    text = capsys.readouterr().out
    assert "0123456789abcdef" not in text
    assert "test-access_token" not in text
    assert "Other" not in text
