# Änderungen

## 0.2.0 — Eigenständige lokale Integration

- Neuer Anzeigename **Smartmi P1 Local**; Repository und Domain bleiben für Updates erhalten.
- Eigene Lüfterentität mit Ein/Aus, manueller Leistung 1–100 % und vier Betriebsmodi.
- Eigene Sensoren für PM2.5 und Filterrestlebensdauer, zusätzlich zu PM10 und Filterstunden.
- Einrichtung ohne HomeKit-Auswahl. Einmalige Tuya-/Smart-Life-Aktivierung und Local Key bleiben erforderlich.
- Automatische Migration der Konfiguration von Version 1 auf Version 2; vorhandene Zusatzentitäten behalten ihre Kennungen.
- Mehrteilige Lüfterbefehle werden vorab vollständig validiert und nach dem Schreiben zurückgelesen.
- Manuelle Prozentwerte werden in Automatik-, Nacht- und Maximum-Modus nicht als aktuelle Drehzahl ausgegeben.
- Dokumentation und Beispielkarte auf die eigenständige Bedienung umgestellt.

Validiert mit Home Assistant 2026.10.4 / Python 3.14. Am P1 mit Firmware 1.0.7
wurden Ein/Aus, Nachtmodus, Automatik und eine manuelle Leistungsänderung lokal
getestet; Ton, Display und Timer durch Zurückschreiben ihrer aktuellen Werte.
Der vorherige Gerätezustand wurde anschließend wiederhergestellt.

Die Kindersicherung wird auf dem getesteten P1 lokal nicht gemeldet. Betrieb mit
gesperrtem Internetzugang und nach Stromunterbrechung ist noch nicht validiert.
Andere Luftreiniger benötigen eine gesonderte Datenpunktzuordnung.

## 0.1.1 — Gezielte Statusabfragen

- Explizite P1-Datenpunktabfrage für Tuya-Protokoll 3.3 (`device22`).
- Zusatzfunktionen am realen Gerät erfolgreich gelesen.

## 0.1.0 — Erste Zusatzfunktionen

- Lokaler Betriebsmodus, PM10, Timer, Signaltöne, Display und Filterstunden.
- Separates Hilfsskript zur einmaligen Local-Key-Beschaffung.
