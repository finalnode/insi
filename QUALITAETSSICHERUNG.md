# Qualitätssicherung und Unterrichtspilot

Dieses Dokument trennt automatisiert geprüfte Eigenschaften von Prüfungen, die
auf echten Schulgeräten oder im Unterricht stattfinden müssen.

## Automatisch geprüft

- Kern-API, Welt, Pixel, Farben, Töne und Parallelplanung
- sämtliche Trainer und Optimierungsregeln
- Vollständigkeit der Aufgaben- und Skriptdateien
- Klassifikation aller mit `@button:run` freigegebenen Codeblöcke
- vollständiger fensterloser Probelauf aller Konsolen- und PyKIM-Beispiele
- atomisches Speichern und Erkennen externer Dateiänderungen
- Backups beim Zurücksetzen einer Aufgabe
- portable Lernstände innerhalb des Kursordners
- kontrolliertes Starten, Stoppen und Live-Streaming lokaler Prozesse
- Windows- und Linux-Kommandowahl zum Öffnen von Dateien
- Erkennung und Auswahl einer getrennten Schüler-Laufzeit
- lokale VS-Code-Workspace-Konfiguration mit erhaltenen Benutzereinstellungen
- sichere Projektordner, Vorlagen und relative `.pyxres`-Ressourcen
- Projektstart mit ausgewählter Runtime und korrektem Arbeitsverzeichnis
- Offline-Installation mit `--no-index` aus einem plattformspezifischen Wheelhouse
- isoliertes Thonny-Profil mit derselben Runtime wie Suite und VS Code
- Reparatur nur innerhalb einer von PyKIM verwalteten Umgebung
- Wheel-Inhalt einschließlich Markdown-Bibliothek
- browserloser NiceGUI-Smoke: Übersicht → Aufgaben → Skript → Autorenwerkzeuge
- macOS-Bundle enthält Runtime, Trainer-Module, Beispiele und Offline-Wheelhouse
- Startprüfung für getrennte App- und Inhaltsversionen blockiert Offline-Starts nicht
- Inhaltsupdates prüfen Archiv- und Einzeldateihashes und verändern keinen Schülercode

Normale Tests:

```bash
pytest
```

Der UI-Gesamtworkflow benötigt NiceGUI und lokale Prozess-Semaphoren:

```bash
python -m pip install -e '.[e2e]'
pytest -m e2e
```

## Manuelle Plattformmatrix

Vor einem breiten Rollout wird jede Zeile auf einem echten Gerät geprüft:

| Umgebung | Setup | Thonny | Pyxel | Stoppen | Netzordner | Status |
|---|---:|---:|---:|---:|---:|---|
| Windows 10 Schulimage | ☐ | ☐ | ☐ | ☐ | ☐ | offen |
| Windows 11 Schulimage | ☐ | ☐ | ☐ | ☐ | ☐ | offen |
| macOS Lehrkraftgerät | ☐ | ☐ | ☐ | ☐ | ☐ | teilweise |
| Linux optional | ☐ | ☐ | ☐ | ☐ | ☐ | offen |

Zu protokollieren sind Python-Version, Installationsart, IDE-Pfad,
Pyxel-Version, Laufwerkstyp und die genaue Fehlermeldung.

### macOS-Bundle

1. `insi.app` startet als **in:si** per Doppelklick ohne systemweit installiertes Python.
2. Übersicht, Skript, Aufgaben und Beispiele öffnen ohne Serverfehler.
3. Ein PyKIM-Beispiel öffnet das Pyxel-Fenster und lässt sich wieder stoppen.
4. Eine Aufgabe lässt sich speichern, prüfen und in die gewählte IDE öffnen.
5. Ein neues Projekt enthält relative `.pyxres`-Pfade und startet offline.
6. Nach Neustart bleiben Kursordner, IDE und Runtime-Auswahl erhalten.
7. Gatekeeper-Verhalten wird nach Signierung und Notarisierung erneut geprüft.

## Testfälle für Thonny und VS Code

1. Suite erkennt eine normale Thonny-Installation.
2. Eine Aufgabe wird mit dem korrekten Pfad geöffnet.
3. Externe Änderung wird in der Suite als Konflikt erkannt.
4. **Neu laden** übernimmt die Thonny-Version.
5. Speichern in der Suite ist anschließend wieder möglich.
6. Umlaute und Leerzeichen im Kursordner funktionieren.
7. VS Code erhält unter `.vscode/settings.json` den gewählten Interpreter.
8. Vorhandene VS-Code-Workspace-Einstellungen bleiben erhalten.
9. Suite, Thonny und VS Code führen dieselbe Schülerdatei mit derselben Runtime aus.

## Testfälle für WebDAV- und Netzlaufwerke

1. Kurs neu anlegen und danach auf demselben Gerät erneut öffnen.
2. Quellcode, Dokubuch und Lernstand synchronisieren vollständig.
3. Zuhause erst nach abgeschlossener Synchronisation weiterarbeiten.
4. Gleichzeitige Änderung auf zwei Geräten erzeugt einen sichtbaren Konflikt.
5. Unterbrochene Verbindung hinterlässt keine halbe `progress.json`.
6. Zurücksetzen erzeugt erreichbare Backups unter `.pykim/backups`.

PyKIM unterstützt bewusst das **nacheinander** Arbeiten auf mehreren Geräten.
Gleichzeitiges Bearbeiten derselben Datei ist kein unterstützter Workflow.

## Unterrichtspilot

Für den ersten Pilotdurchlauf werden beobachtet:

- Finden Schüler Aufgabe, Skript und Testdetails ohne Erklärung?
- Verstehen sie den Unterschied zwischen Speichern und Ausführen?
- Helfen deutsche Fehlermeldungen tatsächlich bei der Selbstkorrektur?
- Welche Skriptblöcke werden ausgeführt und welche nur kopiert?
- Werden Optimierungswerte motivierend oder als reine Benotung verstanden?
- An welchen Stellen wechseln Schüler freiwillig in Thonny?

Probleme werden mit Aufgabe, Betriebssystem, Arbeitsschritt und anonymisiertem
Fehlerbild dokumentiert. Neue Funktionen werden erst nach Auswertung des
Piloten priorisiert.
