"""One-time interactive Tuya login. Run in your own terminal, not in chat."""

from __future__ import annotations

import argparse
import getpass
import json
import logging
import os
from pathlib import Path

import qrcode
from tuya_sharing import LoginControl, Manager, SharingTokenListener

# Public application identifiers used by Home Assistant's official Tuya integration:
# https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/components/tuya/const.py
# These are not account credentials. Authentication still requires the user's QR approval.
TUYA_CLIENT_ID = "HA_3y9q4ak7g4ephrvke"
TUYA_SCHEMA = "haauthorize"


def save_private(path: Path, data: dict) -> None:
    """Create, never overwrite, a file readable only by the current OS user."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, help="Local WLAN address of your P1")
    parser.add_argument("--device-id", help="Only retrieve this device; otherwise choose locally")
    parser.add_argument("--output", type=Path, default=Path(".secrets/p1.local.json"))
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Die Zieldatei existiert bereits; bitte einen neuen --output-Pfad wählen.")
    logging.disable(logging.CRITICAL)
    print("Einmalige Anmeldung direkt bei Tuya mit dem Home-Assistant-Anmeldeverfahren.")
    print("Benutzercode: Smart Life → Profil/Ich → Einstellungen → Konto und Sicherheit.")
    print("Der Code geht an Tuya. Passwort und Cloud-Tokens werden nicht gespeichert.")
    code = getpass.getpass("Benutzercode (Eingabe verborgen): ").strip()
    if not code:
        raise SystemExit("Kein Benutzercode eingegeben.")
    login = LoginControl()
    response = login.qr_code(TUYA_CLIENT_ID, TUYA_SCHEMA, code)
    if not response.get("success"):
        raise SystemExit("Tuya konnte keinen QR-Code ausstellen. Benutzercode prüfen.")
    token = response["result"]["qrcode"]
    qr = qrcode.QRCode(border=2)
    qr.add_data(f"tuyaSmart--qrLogin?token={token}")
    qr.print_ascii(invert=True)
    print("In Smart Life über + → Scannen diesen QR-Code scannen und die Anmeldung freigeben.")
    input("Nach der Freigabe hier Enter drücken: ")
    success, auth = login.login_result(token, TUYA_CLIENT_ID, code)
    if not success:
        raise SystemExit(
            "Keine bestätigte Anmeldung. Skript erneut starten und neuen QR-Code scannen."
        )
    token_info = {k: auth[k] for k in ("t", "uid", "expire_time", "access_token", "refresh_token")}
    manager = Manager(
        TUYA_CLIENT_ID,
        code,
        auth["terminal_id"],
        auth["endpoint"],
        token_info,
        SharingTokenListener(),
    )
    manager.update_device_cache()
    candidates = [
        d for d in manager.device_map.values() if args.device_id is None or d.id == args.device_id
    ]
    if not candidates:
        raise SystemExit("Gerät in diesem Tuya-Konto nicht gefunden.")
    for index, device in enumerate(candidates, 1):
        print(f"{index}: {device.name}")
    if len(candidates) == 1:
        selected = candidates[0]
    else:
        index = int(input("Nummer des Smartmi P1: "))
        if index < 1 or index > len(candidates):
            raise SystemExit("Ungültige Auswahl.")
        selected = candidates[index - 1]
    key = getattr(selected, "local_key", "")
    if not key or len(key.encode("utf-8")) != 16:
        raise SystemExit("Tuya liefert keinen gültigen Local Key für dieses Gerät.")
    save_private(args.output, {"host": args.host, "device_id": selected.id, "local_key": key})
    print(f"Local Key lokal gespeichert: {args.output.resolve()}")
    print("Der Schlüssel wurde nicht ausgegeben. Smart Life jetzt vollständig schließen.")
    print("Als Nächstes: lokaler Lesetest mit scripts/probe_p1.py; keine Cloud-Anmeldung nötig.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt, EOFError:
        raise SystemExit("Abgebrochen.") from None
    except Exception:
        raise SystemExit(
            "Auslesen fehlgeschlagen. Keine Zugangsdaten oder Tokens ausgegeben."
        ) from None
