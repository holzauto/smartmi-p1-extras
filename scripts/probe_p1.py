"""Read-only P1 protocol check using a local credential file."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.smartmi_p1_extras.client import CannotConnect, P1Client  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials", type=Path, default=Path(".secrets/p1.local.json"))
    args = parser.parse_args()
    data = json.loads(args.credentials.read_text())
    versions = [data["protocol_version"]] if "protocol_version" in data else ["3.3", "3.4", "3.5"]
    for protocol in versions:
        client = P1Client(data["host"], data["device_id"], data["local_key"], protocol)
        try:
            dps = client.status()
        except CannotConnect:
            print(f"Protokoll {protocol}: keine gültige Antwort")
            continue
        print(f"Lokale Verbindung bestätigt, Protokoll {protocol}.")
        print("Verfügbare Datenpunkte:", ", ".join(sorted(dps, key=int)))
        print("Lokale Funktionen:")
        for dp, name in {
            "1": "Ein/Aus",
            "2": "PM2.5",
            "3": "Betriebsmodus",
            "7": "Kindersicherung",
            "101": "Signaltöne",
            "102": "PM10",
            "103": "Timer",
            "105": "Filterbetriebsstunden",
            "104": "Filterrestlebensdauer",
            "109": "Manuelle Lüfterleistung",
            "110": "Displayhelligkeit",
        }.items():
            print(f"  {name}: {'vorhanden' if dp in dps else 'nicht gemeldet'}")
        return
    raise SystemExit("Keine Verbindung. IP/Local Key prüfen und Smart Life vollständig schließen.")


if __name__ == "__main__":
    main()
