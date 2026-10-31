# Smartmi P1 Local

Eigenständige lokale Steuerung des **Smartmi Air Purifier P1** in Home Assistant.
Version **0.2.0**. Eine HomeKit-Integration wird nicht benötigt.

Ein fabrikneuer P1 wird einmalig in **Tuya Smart / Smart Life** aktiviert und ins
WLAN aufgenommen. Anschließend werden Geräte-ID und Local Key in dieser Integration
hinterlegt. Der Steuerungsweg im Betrieb ist **Home Assistant → P1 im lokalen Netzwerk**.
Die Smart-Life-App muss dabei nicht geöffnet sein.

Repository: https://github.com/holzauto/smartmi-p1-extras

Der Repository-Name und die interne Domain `smartmi_p1_extras` bleiben für Updates
bestehender Installationen erhalten. Der Anzeigename lautet jetzt **Smartmi P1 Local**.

## Funktionen

| Entität | Funktionen / Messwerte | Tuya-Datenpunkte |
|---|---|---|
| Luftreiniger (`fan`) | Ein/Aus, manuelle Lüfterleistung 1–100 %, Automatik, Nachtmodus, Maximum, Manuell | 1, 3, 109 |
| PM2.5 | Konzentration in µg/m³ | 2 |
| PM10 | Konzentration in µg/m³ laut veröffentlichter Gerätedefinition | 102 |
| Filterrestlebensdauer | Prozent verbleibend | 104 |
| Filterbetriebsstunden | Gemeldete Betriebsstunden | 105 |
| Betriebsmodus (`select`) | Zusätzliche Modusauswahl, synchron mit der Lüfterentität | 3 |
| Ausschalttimer | Aus, 1, 2, 4 oder 8 Stunden | 103 |
| Signaltöne | Ein/Aus | 101 |
| Displayhelligkeit | Hell, gedimmt, aus oder automatisch | 110 |
| Kindersicherung | Implementiert, am getesteten P1 lokal nicht gemeldet | 7 |

Es entstehen zehn Entitäten an einem Gerät. Fehlende Datenpunkte werden als
„nicht verfügbar“ gemeldet. Die Integration unterstützt den P1; sie ist keine
universelle Integration für beliebige Tuya-Luftreiniger.

Die Prozentanzeige beschreibt die **eingestellte manuelle Lüfterleistung**, keine
Drehzahlmessung. Im Automatik-, Nacht- und Maximum-Modus wird deshalb kein
veralteter manueller Prozentwert als aktuelle Leistung angezeigt. Bei ausgeschaltetem
Gerät wird 0 % angezeigt. Eine positive Leistung schaltet auf Manuell und schaltet
das Gerät ein; 0 % schaltet es aus.

`fan.turn_on` kann einen `preset_mode` annehmen: `auto`, `sleep`, `strong` oder `manual`.
Die Dienste `fan.set_preset_mode` und `select.select_option` ändern den Modus, ohne
selbst einen Ein/Aus-Befehl zu senden. Eine manuelle Prozentvorgabe zusammen mit
einem anderen Betriebsmodus wird vor dem ersten Schreibbefehl abgelehnt.

## Einmalige Einrichtung des P1

1. Ein neues Gerät über Tuya Smart / Smart Life ins WLAN aufnehmen und aktivieren.
2. Geräte-ID und **Local Key** beschaffen (siehe Hilfsskript unten).
3. Die lokale WLAN-IP im Router ermitteln; eine DHCP-Reservierung ist sinnvoll.
4. Smart Life vollständig schließen und die lokale Verbindung prüfen.
5. Die HACS-Integration installieren und mit diesen Daten einrichten.

Die ursprüngliche Aktivierung und die Schlüsselbeschaffung benötigen Tuya-Zugang.
Die installierte Integration startet weder eine Cloud-Anmeldung noch das
Schlüssel-Hilfsskript. Es ist kein HomeKit-Pairing und kein Apple-Konto erforderlich.

## Local Key auslesen

Das separate Hilfsskript verwendet das Tuya-SDK und das QR-Anmeldeverfahren der
HA-Tuya-Integration. Ein Tuya-Entwicklerkonto wird dafür nicht benötigt. Verfügbarkeit
und Berechtigungen hängen von der aktuellen Tuya-API ab. Das Verfahren wurde an
einem P1 erfolgreich verwendet.

Auf einem Rechner mit Python 3.14:

```sh
git clone https://github.com/holzauto/smartmi-p1-extras.git
cd smartmi-p1-extras
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-key.txt
.venv/bin/python scripts/get_local_key.py --host DEINE_LOKALE_IP
```

Den Benutzercode aus Smart Life → Profil/Ich → Einstellungen → Konto und Sicherheit
am verdeckten Terminalprompt eingeben. Den QR-Code im Terminal mit Smart Life
scannen, die Anmeldung auf dem iPhone bestätigen und danach im Terminal Enter drücken.
Bei mehreren Geräten den P1 auswählen.

Der Local Key wird nach `.secrets/p1.local.json` geschrieben (Dateirechte `0600`,
im Git-Ignore) und nicht im Terminal ausgegeben. Cloud-Tokens werden nicht gespeichert.
Der Benutzercode dient der einmaligen Cloud-Anmeldung; für die spätere LAN-Verbindung
wird der Local Key verwendet. Schlüsseldateien nicht veröffentlichen oder hochladen.

Für einen ausschließlich lesenden Verbindungstest zusätzlich die HA-Abhängigkeiten
installieren und anschließend ausführen:

```sh
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/probe_p1.py
```

Der Lesetest probiert die unterstützten Protokollversionen 3.3/3.4/3.5, meldet die
erfolgreiche Version und die verfügbaren Funktionen. Er ändert keine Einstellung
und gibt keinen Local Key aus. Am getesteten P1 funktioniert **Protokoll 3.3** mit
expliziten Datenpunktabfragen (`device22`).

## Installation mit HACS

1. In HACS → Menü → **Benutzerdefinierte Repositories** öffnen.
2. `https://github.com/holzauto/smartmi-p1-extras` hinzufügen, Typ **Integration**.
3. **Smartmi P1 Local** herunterladen und Home Assistant neu starten.
4. Einstellungen → Geräte & Dienste → Integration hinzufügen → **Smartmi P1 Local**.
5. Lokale IP-Adresse, Tuya-Geräte-ID, Local Key und Protokollversion eingeben.

Die Einrichtung prüft die lokale Verbindung sowie die grundlegenden P1-Datenpunkte
vor dem Speichern. Eine Einrichtung verändert keine Geräteeinstellungen.
Die Integration ist als benutzerdefinierte HACS-Quelle verfügbar und ist nicht im
HACS-Standardkatalog enthalten.

## Update von 0.1.x

- In HACS aktualisieren und Home Assistant neu starten. Die gespeicherten IP-,
  Geräte-ID-, Schlüssel- und Protokolldaten bleiben erhalten.
- Der Konfigurationseintrag wird automatisch auf Version 2 migriert. Die frühere
  optionale HomeKit-Zuordnung entfällt.
- Die sieben bisherigen Zusatzentitäten behalten ihre Unique IDs und bereits
  vergebenen Entitäts-IDs. Drei Entitäten kommen hinzu: Lüfter, PM2.5 und Filterrestlebensdauer.
- Vorhandene HomeKit-Geräte und deren Automationen werden nicht automatisch verändert.
  Bereits auf HomeKit-Entitäten verweisende Dashboards und Automationen müssen bei
  einem gewünschten Wechsel auf die neuen lokalen Entitäten umgestellt werden.
- Die vollständige Bedienung zunächst an der neuen lokalen Lüfterentität prüfen.
  Danach kann die bisherige P1-Anbindung über **HomeKit Device** entfallen.
  Die HomeKit-Integration eines anderen Geräts, etwa VOCOlinc VAP1, ist davon unabhängig.
- Wer erstmals installiert, benötigt keine vorherige Version und keine HomeKit-Einrichtung.

## Manuelle Installation und Entfernen

Alternativ den Ordner `custom_components/smartmi_p1_extras` nach
`/config/custom_components/smartmi_p1_extras` auf dem HA-System kopieren, HA neu
starten und **Smartmi P1 Local** über Geräte & Dienste hinzufügen.

Zum Entfernen den Integrationseintrag löschen. Für die vollständige Deinstallation
danach das Repository in HACS entfernen bzw. den Komponentenordner entfernen und
HA neu starten. Eigenständig vorhandene HomeKit-Integrationen bleiben bestehen.

## Lokaler Betrieb und Grenzen

- Der Gerätezustand wird alle 30 Sekunden über TCP 6668 im LAN gelesen.
  Befehle und Statusabfragen sind serialisiert. Netzwerkzugriffe laufen außerhalb
  des HA-Ereignisloops, mit kurzen getrennten Verbindungen.
- Änderungen werden anschließend vom Gerät zurückgelesen. Nicht bestätigte
  Befehle werden als Fehler gemeldet; es wird kein Erfolg vorgetäuscht.
  Mehrteilige Lüfterbefehle werden vollständig validiert, bevor etwas gesendet wird.
  Bei einem Fehler kann ein bereits gesendeter Teilschritt angewendet sein;
  die nächste erfolgreiche Abfrage stellt den tatsächlich gemeldeten Zustand dar.
- Nur einen lokalen Tuya-Client pro Gerät verwenden und Smart Life beim lokalen
  Betrieb schließen. Nicht gleichzeitig Tuya Local oder LocalTuya auf denselben P1 richten.
- Die Integration verwendet **TinyTuya**, eine lokal laufende Open-Source-Bibliothek.
  Für die LAN-Steuerung wird kein externer Dienst und kein weiteres Konto benötigt.
  GitHub/HACS dienen zur Installation und für Updates.
- Die Integration unterbindet nicht selbst die Cloud-Verbindungen der Gerätefirmware.
  Für dauerhaft abgeschotteten Betrieb muss der Internetzugang des P1 am Router
  gesperrt und die Erreichbarkeit aus HA weiter erlaubt werden. Ein vollständiger
  Offline- und Neustarttest steht noch aus. DNS-Regeln gerätespezifisch prüfen.
- Geräte-ID und Schlüssel werden in der HA-Konfiguration gespeichert. Das
  Passwortfeld schützt die Anzeige, verschlüsselt aber keine Konfigurationsdateien.
  HA-Backups können den Schlüssel enthalten. Änderungen der IP oder des Local Key
  sind über **Neu konfigurieren** möglich. Erneutes Pairing kann den Local Key ändern.
- Die Kindersicherung ist bei einem P1 mit Firmware 1.0.7 lokal nicht gemeldet worden.
  Die entsprechende Entität bleibt dort nicht verfügbar. Andere Firmwarestände
  können abweichen; weitere Modelle brauchen eine eigene geprüfte Datenpunktzuordnung.

## Entwicklung

```sh
.venv/bin/python -m pip install -r requirements-dev.txt -r requirements-key.txt
.venv/bin/ruff check custom_components tests scripts
.venv/bin/pytest -q
```

Getestet mit Home Assistant **2026.10.4 / Python 3.14**. Die automatisierten Tests
verwenden echte HA-Einrichtungsdialoge, Entitäten und Dienste mit simuliertem
LAN-Transport. Sie prüfen auch die eigenständige Einrichtung ohne HomeKit und
Migration, Kennungserhalt, Fehlerbehandlung und Bestätigung der Schreibbefehle.
Am P1 mit Firmware 1.0.7 wurden lokale Lesezugriffe sowie Ein/Aus, Nachtmodus,
Automatik und eine manuelle Leistungsänderung getestet. Ton, Display und Timer
wurden durch Zurückschreiben ihrer aktuellen Werte bestätigt; anschließend wurde
der vorherige Gerätezustand wiederhergestellt. Die weiteren einzelnen Einstellwerte
und der vollständige Betrieb bei gesperrtem Internetzugang und nach
Stromunterbrechung sind noch zu prüfen.

Für einen eigenen Fork kann `scripts/prepare_hacs.py OWNER/REPOSITORY --maintainer
GITHUB_USERNAME` die Repository-Verweise im Manifest anpassen.

## Quellen

- [Veröffentlichte P1-Datenpunktdefinition](https://github.com/make-all/tuya-local/blob/main/custom_components/tuya_local/devices/smartmi_air_purifier_p1.yaml)
- [TinyTuya LAN-Bibliothek](https://github.com/jasonacox/tinytuya)
- [HACS-Anforderungen](https://www.hacs.xyz/docs/publish/integration/)

Eigenständige Implementierung; keine Zugehörigkeit zu Smartmi oder Tuya.
