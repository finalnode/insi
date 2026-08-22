# Qualitätssicherung und Unterrichtspilot

Dieses Dokument trennt automatisiert geprüfte Eigenschaften von Prüfungen, die
auf echten Schulgeräten oder im Unterricht stattfinden müssen.

## Aktueller Nachweis für 0.8

Auf `develop/v0.8` umfasst der normale Testlauf für `0.8.0.dev0` am
23. August 2026 insgesamt 475 bestandene Prüfungen und eine auf macOS erwartbar
übersprungene Linux-Bubblewrap-Prüfung. Alle vier bewusst separat markierten
NiceGUI-E2E-Prüfungen bestehen ebenfalls. Die Zahl ist ein fortzuschreibender
Entwicklungsstand, kein Ersatz für die unten aufgeführte Plattformmatrix.

## Automatisch geprüft

- Kern-API, Welt, Pixel, Farben, Töne und Parallelplanung
- sämtliche Trainer und Optimierungsregeln
- fachmodulneutrale Trainer-Engine-Registry, explizite Engineformate und
  sichere Engine-Starterpfade
- verlustfreies Trennen und Zusammensetzen visueller Aufgabenmetadaten
- kontextabhängiges TOAST-Toolbar-Plugin, debouncte Servervalidierung und
  editorlokale Zeilennummern für Aufgabeninhalte
- lokal gebündelte Markdowneditor-, Sprach- und Lizenzdateien
- Vollständigkeit der Aufgaben- und Skriptdateien
- Klassifikation aller mit `@button:run` freigegebenen Codeblöcke
- vollständiger fensterloser Probelauf aller Konsolen- und PyKIM-Beispiele
- atomisches Speichern und Erkennen externer Dateiänderungen
- Backups beim Zurücksetzen einer Aufgabe
- portable Lernstände innerhalb des Kursordners
- kontrolliertes Starten, Stoppen und Live-Streaming lokaler Prozesse
- Fail-closed-Verhalten ohne verfügbaren Sandbox-Adapter
- validierte Windows-Brokerkonfiguration ohne Netzwerkfähigkeit und mit
  begrenzten AppContainer-Dateirechten
- echter Windows-AppContainer-Lauf im Desktop-Build gegen Hostdateizugriff,
  Netzwerk, Prozessüberschreitung, zu große Schreibmengen und eine fehlende
  Pyxel-Grafikinitialisierung
- Bubblewrap-Kommandokonstruktion ohne Host-`PYTHONPATH`, Netzwerk oder
  pauschale Kursordnerfreigabe
- echter Linux-Bubblewrap-Lauf im Desktop-Build gegen Lesen und Schreiben
  außerhalb des Workspaces, Netzwerkzugriff, falsche Netzwerk-/PID-Namespaces
  sowie Prozess-, RAM-, CPU- und temporäre Schreibgrenzverletzungen
- echtes Pyxel-Fenster im Linux-Build über einen headless Weston und einen
  einzeln eingebundenen Wayland-Socket
- echter macOS-Seatbelt-Lauf in beiden Desktop-Builds gegen Lesen und Schreiben
  außerhalb des Workspaces, Netzwerkzugriff sowie Prozess-, RAM-, CPU- und
  Schreibgrenzverletzungen
- Abbruch des Prozessbaums bei RAM-, CPU-, Prozess-, Ausgabe- und
  Schreibgrenzverletzungen
- sichere globale, kursweite und projektbezogene Dateiimporte ohne
  Überschreiben, Pfadausbruch oder Symlink-Übernahme
- begrenzte Projektstände und validierte Rückführung von Lernstand aus einem
  privaten Aufgabenlauf
- Windows- und Linux-Kommandowahl zum Öffnen von Dateien
- Erkennung und Auswahl einer getrennten Schüler-Laufzeit
- lokale VS-Code-Workspace-Konfiguration mit erhaltenen Benutzereinstellungen
- sichere Projektordner, Vorlagen und relative `.pyxres`-Ressourcen
- Projektstart mit ausgewählter Runtime und korrektem Arbeitsverzeichnis
- Offline-Installation mit `--no-index` aus einem plattformspezifischen Wheelhouse
- isoliertes Thonny-Profil mit derselben Runtime wie Suite und VS Code
- Reparatur nur innerhalb einer von in:si verwalteten Kursumgebung
- Wheel-Inhalt einschließlich Markdown-Bibliothek
- browserloser NiceGUI-Smoke: Übersicht → Aufgaben → Skript → Autorenwerkzeuge
- macOS-Bundle enthält Runtime, Trainer-Module, Beispiele und Offline-Wheelhouse
- Startprüfung für getrennte App- und Inhaltsversionen blockiert Offline-Starts nicht
- Inhaltsupdates prüfen Archiv- und Einzeldateihashes und verändern keinen Schülercode

Normaler Entwicklungsnachweis:

```bash
python -m pytest
```

Die Linux-Sicherheitsjobs verwenden derzeit den weiterhin unterstützten
GitHub-Runner `ubuntu-22.04`. Der Runner `ubuntu-24.04` verweigert Bubblewrap in
der gehosteten CI beim Konfigurieren des isolierten Loopback-Interfaces. Die
Prüfung wird deshalb nicht übersprungen oder abgeschwächt, sondern auf dem
Runner ausgeführt, der den echten Netzwerk-Namespace bereitstellen kann.

Der UI-Gesamtworkflow benötigt NiceGUI und lokale Prozess-Semaphoren:

```bash
python -m pip install -e '.[test]'
pytest -m e2e
```

## Manuelle Plattformmatrix

Vor einem breiten Rollout wird jede Zeile auf einem echten Gerät geprüft:

| Umgebung | Setup | IDE | Sandboxstatus | Pyxel | Stoppen | Status |
|---|---:|---:|---:|---:|---:|---|
| Windows 10 Schulimage | ☐ | ☐ | AppContainer-Probelauf erfolgreich | ☐ | ☐ | offen |
| Windows 11 Schulimage | ☐ | ☐ | AppContainer-Probelauf erfolgreich | ☐ | ☐ | offen |
| macOS Lehrkraftgerät | DMG-Payload und Ad-hoc-Signatur geprüft | ☐ | ✓ lokaler Seatbelt-Probelauf am 21.08.2026 | ☐ | ☐ | teilweise |
| Linux Wayland + bwrap | ☐ | ☐ | Namespace-Probelauf erfolgreich | ☐ | ☐ | offen |
| Linux ohne bwrap/X11 | ☐ | ☐ | gesperrt bzw. nur headless | IDE | ☐ | offen |

Zu protokollieren sind Python-Version, Installationsart, IDE-Pfad,
Pyxel-Version, Laufwerkstyp und die genaue Fehlermeldung.

### macOS-Bundle

1. `insi.app` startet als **in:si** per Doppelklick ohne systemweit installiertes Python.
2. Übersicht, Skript, Aufgaben und Beispiele öffnen ohne Serverfehler.
3. Ein mitgeliefertes PyKIM-Beispiel öffnet das Pyxel-Fenster und lässt sich
   wieder stoppen.
4. Der Systemcheck meldet **macOS Seatbelt** und gibt integrierte Aufgaben- und
   Projektstarts erst nach bestandenem Selbsttest frei.
5. Ein neues Projekt enthält relative `.pyxres`-Pfade und startet in der IDE
   offline.
6. Nach Neustart bleiben Kursordner, IDE und Runtime-Auswahl erhalten.
7. Gatekeeper-Verhalten wird nach Signierung und Notarisierung erneut geprüft.

Der vollständige native Test lässt sich aus dem Repository ausführen:

```bash
python tools/check_macos_sandbox.py --gui
```

Er prüft Datei- und Netzwerkgrenzen, einen geerbten Kindprozess, Prozessanzahl,
RAM, CPU-Zeit, Schreibvolumen und mit `--gui` zusätzlich ein echtes
Pyxel-Fenster.

### Linux-Sandbox

Der vollständige native Test kann in einer Wayland-Sitzung mit
`python tools/check_linux_sandbox.py --gui` ausgeführt werden.

1. Der Systemcheck unterscheidet fehlendes, unbrauchbares und aktives
   Bubblewrap.
2. Ein Aufgabenlauf kann nur seine private Laufablage beschreiben.
3. Ein Projektlauf kann das aktuelle Projekt, aber kein anderes Projekt
   verändern.
4. Kursweite und globale importierte Dateien sind lesbar und nicht schreibbar.
5. Home-Verzeichnis, `.pykim`-Interna, D-Bus und Netzwerk sind nicht erreichbar.
6. Unter Wayland öffnet ein Pyxel-Fenster; unter X11 verweist die App auf die
   externe IDE.
7. RAM-, CPU-, Prozess-, Ausgabe- und Schreibtests beenden den gesamten
   Prozessbaum und nennen den Abbruchgrund.

### Windows-Sandbox

1. Der Systemcheck erzeugt einen AppContainer und gibt den integrierten Start
   nur nach bestandenem Datei- und Netzwerkprobelauf frei.
2. Ein Aufgabenlauf kann ausschließlich seine private Laufablage beschreiben.
3. Ein Projektlauf kann das aktuelle Projekt, aber keine anderen Benutzer- oder
   Kursdateien verändern.
4. Ohne Netzwerk-Capability sind Internet und lokales Netz nicht erreichbar.
5. Prozess-, RAM-, CPU-, Ausgabe- und Schreibgrenzen beenden über das Job Object
   beziehungsweise den Broker den vollständigen Prozessbaum.
6. Nach dem Lauf sind temporäres AppContainer-Profil und dessen explizite
   Dateirechte entfernt.
7. Ein Pyxel-Projekt öffnet sein Fenster im AppContainer und lässt sich aus
   in:si vollständig stoppen.

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

in:si unterstützt bewusst das **nacheinander** Arbeiten auf mehreren Geräten.
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
