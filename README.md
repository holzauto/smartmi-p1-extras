# Smartmi P1 Extras

Lokale Zusatzfunktionen für den **Smartmi Air Purifier P1** neben einer bestehenden
HomeKit-Device-Anbindung in Home Assistant. Version **0.1.1**. Lokales Lesen am realen
P1 (Firmware 1.0.7) bestätigt. Schreiben und Betrieb ohne Internet sind noch nicht
validiert. Getestet mit Home Assistant **2026.10.4 / Python 3.14**.

Installation über HACS als benutzerdefiniertes Repository:
**https://github.com/holzauto/smartmi-p1-extras** (Typ: Integration).
Schreibbefehle und Betrieb ohne Internet sind noch nicht am realen Gerät getestet.
Diese erste Version sollte deshalb zunächst mit beobachtbarem Gerät geprüft werden.

## Funktionen

| Zusatzfunktion | Tuya-Datenpunkt | Verhalten |
|---|---:|---|
| Betriebsmodus | 3 | Automatik, Nachtmodus (`sleep`), Maximum, Manuell |
| PM10 | 102 | Konzentration in µg/m³ laut veröffentlichter P1-Gerätedefinition |
| Ausschalttimer | 103 | Aus, 1, 2, 4 oder 8 Stunden |
| Kindersicherung | 7 | Implementiert; auf dem getesteten Gerät lokal nicht gemeldet |
| Signaltöne | 101 | Ein / Aus |
| Displayhelligkeit | 110 | Hell, gedimmt, aus oder automatisch |
| Filterbetriebsstunden | 105 | Gemeldete Betriebsstunden |

Es werden sieben neue Entitäten angelegt. Fehlende Datenpunkte melden
„nicht verfügbar“. Am getesteten P1 sind sechs Zusatzfunktionen lesbar; DP7 fehlt.
Die Abfrage verwendet Protokoll 3.3 mit expliziten Datenpunkten (`device22`), weil
die automatische Erkennung sonst nur Ein/Aus zurückliefert. Die Werte in einer
Statusabfrage sind `null`; diese Abfrage schreibt keine Geräteeinstellungen.
Nachtmodus wählt den Geräte-Modus `sleep`; das Gerät wird dabei nicht automatisch
eingeschaltet und es werden keine angenommenen Helligkeits- oder Tonwerte gesetzt.

Die vorhandenen HomeKit-Entitäten, Geräte, Namen und Automationen werden nicht verändert.
Die Erweiterung erzeugt keine zweite Lüfterentität. Bei der Einrichtung lässt sich
das vorhandene Smartmi-HomeKit-Gerät auswählen, um dessen Raum als Vorschlag zu
übernehmen. Home Assistant 2026.10 führt die Zusatzfunktionen als eigenes Gerät
„Smartmi P1 Extras“; es werden keine fremden HomeKit-Gerätekennungen übernommen.

Ein bereits über HomeKit eingebundener **VOCOlinc VAP1** wird weiterhin direkt über
HomeKit bedient. Diese erste Version implementiert keine zusätzlichen VAP1-Funktionen.
Die Beispielkarte zeigt beide bestehenden Lüfter zusammen mit den P1-Extras.

## Einmalig den Local Key auslesen

Nur diese Beschaffung benötigt eine Verbindung zur Tuya-Cloud. Das separate
Hilfsskript verwendet das SDK und QR-Anmeldeverfahren der offiziellen HA-Tuya-Integration.
Es ist kein Tuya-Entwicklerkonto erforderlich. Die Verfügbarkeit des Schlüssels hängt
von der aktuellen Tuya-API und den Berechtigungen deines Kontos ab. Das Auslesen
und die anschließende lokale Authentifizierung wurden an einem P1 bestätigt.

Für das Hilfsskript Python 3.14 installieren und im eigenen Terminal ausführen:

```sh
git clone https://github.com/holzauto/smartmi-p1-extras.git
cd smartmi-p1-extras
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-key.txt
.venv/bin/python scripts/get_local_key.py --host DEINE_LOKALE_IP
```

1. Smart Life → Profil/Ich → Einstellungen → Konto und Sicherheit → Benutzercode.
   Je nach App-Version können die Bezeichnungen abweichen.
2. Den Benutzercode am verdeckten Terminalprompt eingeben. Er wird direkt an Tuya
   für die Anmeldung übermittelt. Kein Passwort oder Schlüssel gehört in den Chat.
3. Den im Terminal dargestellten QR-Code mit Smart Life scannen und die Anmeldung
   auf dem iPhone bestätigen. Danach im Terminal Enter drücken und den P1 auswählen.
4. Der Schlüssel wird ausschließlich nach `.secrets/p1.local.json` geschrieben
   (Dateirechte `0600`, im Git-Ignore). Cloud-Tokens werden nicht gespeichert.
   Die Datei nicht hochladen oder veröffentlichen; auch HA-Backups enthalten später
   den in der Integration hinterlegten Local Key.
5. Smart Life vollständig schließen und ausschließlich lesend testen:

```sh
.venv/bin/python scripts/probe_p1.py
```

Der Lesetest probiert die unterstützten Protokollversionen 3.3/3.4/3.5, meldet die
erfolgreiche Version und die verfügbaren Zusatzfunktionen. Er ändert keine Einstellung
und gibt weder Local Key noch Gerätezustände aus. Er kann bis zu etwa einer Minute dauern.

Das Schlüssel-Hilfsskript benötigt nur `requirements-key.txt`. Für `probe_p1.py`
zusätzlich `.venv/bin/python -m pip install -r requirements-dev.txt` ausführen;
der Lesetest benötigt die Integrationsdateien und deren HA-Abhängigkeiten.

## Mit HACS installieren

1. In HACS das Menü **Benutzerdefinierte Repositories** öffnen.
2. `https://github.com/holzauto/smartmi-p1-extras` hinzufügen, Typ **Integration**.
3. **Smartmi P1 Extras** herunterladen und Home Assistant neu starten.
4. Einstellungen → Geräte & Dienste → Integration hinzufügen → **Smartmi P1 Extras**.
5. Lokale IP-Adresse, Tuya-Geräte-ID, Local Key und bestätigte Protokollversion
   eingeben. Am getesteten P1 ist dies **3.3**. Optional das vorhandene
   Smartmi-HomeKit-Gerät auswählen, um dessen Raum vorzuschlagen.

Der Einrichtungsdialog prüft die lokale Verbindung vor dem Speichern.

## Ohne HACS installieren

1. Den Ordner `custom_components/smartmi_p1_extras` aus diesem Projekt bzw. ZIP nach
   `/config/custom_components/smartmi_p1_extras` auf dem HA-System kopieren.
   Die Entwicklung auf dem Mac allein installiert nichts auf HA.
2. Home Assistant neu starten.
3. Einstellungen → Geräte & Dienste → Integration hinzufügen → **Smartmi P1 Extras**.
4. Lokale IP, Tuya-Geräte-ID, Local Key und im Lesetest bestätigte Protokollversion
   eingeben. Optional das vorhandene Smartmi-HomeKit-Gerät auswählen.
5. Der Einrichtungsdialog führt vor dem Speichern einen lokalen Lesetest durch.

Geräte-ID und Schlüssel gehören nicht in öffentliche Projektdateien.
Der Schlüssel ist in der HA-Konfiguration
gespeichert; das Passwortfeld schützt die Anzeige, verschlüsselt aber nicht die
Konfigurationsdateien. IP oder Local Key später über **Neu konfigurieren** ändern.
Ein erneutes Pairing in Smart Life kann den Local Key ändern.

Das Repository ist als benutzerdefinierte HACS-Quelle vorgesehen. Es ist nicht im
HACS-Standardkatalog enthalten. Für einen eigenen Fork kann
`scripts/prepare_hacs.py OWNER/REPOSITORY --maintainer GITHUB_USERNAME` die URLs
und Maintainer-Angabe im Manifest anpassen.

## Betrieb und Prüfung am Gerät

- Nur LAN-Zugriffe auf TCP 6668, alle 30 Sekunden, kurze getrennte Verbindungen.
  Synchrone Netzwerkzugriffe laufen außerhalb des HA-Ereignisloops und werden serialisiert.
- Nach einem Schreibbefehl wird zurückgelesen. Nicht bestätigte Änderungen werden
  als Fehler gemeldet, ohne einen erfolgreichen Gerätezustand vorzutäuschen.
- Die Integration startet keine Tuya-Cloud-Anmeldung und speichert keine Cloud-Tokens.
  Das optionale Schlüssel-Hilfsskript wird nicht mit der HA-Integration installiert.
- Geschlossenes Smart Life und nur ein lokaler Tuya-Client pro Gerät vermeiden
  Verbindungskonflikte. HomeKit verwendet ein eigenes Protokoll; der Parallelbetrieb
  mit lokalem Tuya muss trotzdem am konkreten Gerät geprüft werden.
- Vollständig cloudfreier Gerätebetrieb ist erst nach einem Offline-Test bestätigt:
  Internetzugriff des P1 am Router sperren, lokale HA-Erreichbarkeit erlauben,
  Neustart testen und alle gewünschten Funktionen durchgehen. Manche Tuya-Firmwares
  reagieren empfindlich auf die konkrete Internet-/DNS-Sperre. Nicht pauschal DNS-Regeln ändern.
- Gerätefunktionen einzeln prüfen: Nachtmodus, PM10 im Vergleich zur App, Timer,
  Ton und Display. Vorherige Einstellungen notieren und wiederherstellen.
- Entfernen der Integration entlädt nur die Extras. Für die vollständige Deinstallation
  anschließend den Komponentenordner entfernen und HA neu starten.

## Entwicklung und Quellen

```sh
.venv/bin/ruff check custom_components tests scripts
.venv/bin/pytest -q
```

Die Tests verwenden echte HA-Config-Flows, Entitäten und Dienste mit simuliertem
Gerätetransport. Sie ersetzen weder den P1-Test noch den Offline-Test.

- [Veröffentlichte P1-Datenpunktdefinition](https://github.com/make-all/tuya-local/blob/main/custom_components/tuya_local/devices/smartmi_air_purifier_p1.yaml)
- [TinyTuya LAN-Bibliothek](https://github.com/jasonacox/tinytuya)
- [HomeKit Device](https://www.home-assistant.io/integrations/homekit_controller/)
- [HACS-Anforderungen](https://www.hacs.xyz/docs/publish/integration/)

Eigenständige Implementierung; keine Zugehörigkeit zu Smartmi, Tuya oder VOCOlinc.
