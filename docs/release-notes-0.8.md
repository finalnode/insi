# in:si 0.8 – Release-Notes (Entwurf)

Stand: 12. September 2026 · Version: `0.8.0.dev0` · Zweig: `develop/v0.8` · noch
nicht veröffentlicht

Diese Datei begleitet die Entwicklung von 0.8. Sie wird nach jedem
abgeschlossenen, getesteten Arbeitsschritt aktualisiert. Die stabilen Downloads
bleiben bis zur Freigabe bei 0.7.1.

Der Funktionsumfang ist seit dem 23. August 2026 geschlossen. Das
[Abschlussprotokoll](v0.8-abschlussprotokoll.md) trennt umgesetzte Funktionen,
lokale Nachweise und die noch offenen Freigabeprüfungen. Bis zu deren Abschluss
kommen keine weiteren Produktfunktionen hinzu.

## Was 0.8 sichtbar verbessert

- Beim Öffnen wird zuerst die gewählte Runtime geprüft. Die breite
  Interpretersuche erfolgt nur bei Bedarf, die Setup-Inventur erst im Setup-Tab.
  Installierte PyKIM-Trainer laden zunächst Metadaten und erst bei Verwendung
  ihre Prüfer. Bekannte Trainer-Engines vermeiden wiederholte Paketsuchen;
  Kursimporte und explizite Validierung prüfen weiterhin alle Trainer.
  Ein lokaler Vergleich desselben Kurses mit 97 PyKIM-Aufgaben ergab
  6,97 Sekunden Vorbereitung auf `1d87570` gegenüber 0,89 Sekunden mit diesen
  Änderungen (Migration, Aktivierung und Runtimeprüfung, ohne UI-Rendering).
- Lernende können automatische und benannte Projektstände in einer Zeitleiste
  sehen, kommentieren und sicher wiederherstellen. Vor dem Rücksprung wird der
  aktuelle Arbeitsstand erneut gesichert.
- Einstellungen, Kursmarker und Lernstände werden über eine versionierte,
  idempotente 0.7→0.8-Migration mit Originalbackup aktualisiert.
- Kurse öffnen schneller: Eine künstliche Mindestwartezeit entfällt, inaktive
  Ansichten werden erst bei Bedarf gebaut und mehrfaches Einlesen von Kurs- und
  Lernstandsdaten wurde reduziert.
- Aufgaben- und Projekteditoren werden erst beim ersten Öffnen aufgebaut und
  behalten ihren Zustand beim Wechsel. Gleichzeitige Lernstandsänderungen
  innerhalb einer App-Instanz werden serialisiert; laufende Aufgaben und
  verspätete Ergebnisse bleiben an ihren ursprünglichen Kurs gebunden.
- Sprite- und Musikeditor lassen sich getrennt aus einem Pyxel-Projekt öffnen;
  sofort fehlgeschlagene Starts werden nicht mehr als Erfolg gemeldet.
- Externe Trainer-Erweiterungen werden vor dem Import mit Paket, Version,
  Herausgeber und Quelle angezeigt und benötigen eine ausdrückliche,
  versionsbezogene Zustimmung.
- Persönliche App-Daten und alle erreichbaren registrierten Kursordner lassen
  sich gemeinsam als portables ZIP sichern. Eine davon getrennte, ausdrücklich
  bestätigte Aktion verschiebt alle lokalen in:si-Daten in den Systempapierkorb.

## Wartbarkeit und Paketgröße

- Große UI- und Testmodule werden mit Architekturbudgets begrenzt und
  schrittweise fachlich getrennt. Der zentrale `test_guide.py` sank bislang von
  2.862 auf 1.460 Zeilen. Neben 33 Runtime-, IDE- und Pyxel-Prüfungen liegen nun
  16 Inhalts-, Update- und Zertifikatsprüfungen in einem eigenen, lokal unter
  einer Sekunde schnellen Testmodul.
- Die doppelte Updateoberfläche wurde entfernt; App-, Kurs- und Inhaltsabgleich
  haben einen gemeinsamen Einstieg. App- und allgemeine Inhaltsprüfung laufen
  parallel; bei Repositorykursen wird die ungenutzte allgemeine Inhaltsabfrage
  vollständig übersprungen. Beide Inhaltswege verwenden denselben atomaren
  Aktivierungspfad, ein nie gelesener Statuscache entfällt.
- Neue und vorhandene Repository- beziehungsweise ZIP-Kurse teilen sich jetzt
  dieselben Installations- und Workspace-Aktivierungspfade. Vorhandene
  Schülerdateien bleiben dabei durch eigene Regressionstests abgesichert.
- ZIP-Prüfung und -Erstellung sind von der Speicherung installierter Inhalte,
  Runtime-Stände und Quellenmarker getrennt. Kursdateien und Offline-Wheels
  werden beim Export blockweise geschrieben. Ein Vergleich mit einer
  synthetischen, stark komprimierbaren 32-MiB-Datei sank
  von 109,5 auf 77,5 MiB gemessenen Python-Spitzenallokationen.
- Atomare Datei- und JSON-Schreibvorgänge verwenden einen gemeinsamen Ablauf;
  Aufgabenmetadaten, Inhaltsmanifeste und Projektstände vermeiden wiederholte
  Lese- und Suchvorgänge.
- Der Runtime-Preflight wiederholt fehlgeschlagene Paketprüfungen nicht mehr
  und prüft einen bereits verworfenen bevorzugten Interpreter bei der
  anschließenden Suche nicht erneut.
- Das Offline-Wheelhouse ist vom App-Paketbaum getrennt. Der lokale
  macOS-ARM-DMG-Prototyp sank von rund 113 MB auf rund 82 MiB.
- Die Desktop-Builds verwenden aus ihren vier Zielmanifesten abgeleitete
  Dependency-Locks für Windows, Linux, macOS Intel und macOS ARM.
- Die historische Messung vom 27. August erfasste den selbst gepflegten
  Python-Produktivcode mit 18.806 Zeilen gegenüber 18.746 zu Beginn der Konsolidierung
  (+60, rund +0,3 %). Der sicherheitskritische Dateivertrag und
  seine Oberfläche bleiben bewusst getrennt und gezielt testbar.

## Aktueller Teststand

- 573 normale Prüfungen lokal bestanden;
- eine Linux-Bubblewrap-Prüfung auf macOS übersprungen;
- acht NiceGUI-E2E-Prüfungen lokal ausgeführt und bestanden;
- CI auf Python 3.11 bis 3.13 sowie Desktop-, Sandbox- und native GUI-Matrix auf
  Commit `f60df90` bestanden; dieser gepushte Stand umfasst 567 normale und
  sieben NiceGUI-E2E-Prüfungen;
- eine frische Kurs-Runtime auf Windows, Linux und beiden macOS-Architekturen
  ausschließlich aus dem paketierten Wheelhouse offline aufgebaut und geprüft.

## Noch offen vor der Freigabe

- weitere reale 0.7-Datenbestände und physisch entfernte Datenträger gegen die
  Migration und Wiederherstellung testen;
- die automatisiert grüne Sandboxmatrix auf echten Zielgeräten, insbesondere
  einem Windows-Schulgerät, bestätigen;
- Toolbar, Kernabläufe und Performance auf echten Zielgeräten manuell abnehmen;
- nach bestandener Freigabematrix die Entwicklungsversion `0.8.0.dev0` auf
  `0.8.0` setzen und den Release-Tag gegen denselben Stand prüfen.

Die ausführliche technische Historie steht in der [Roadmap](../ROADMAP.md),
Auswirkungen und Workarounds in den [bekannten Problemen](../KNOWN_ISSUES.md).

---

# in:si 0.8 – Draft release notes

Status: 11 September 2026 · version: `0.8.0.dev0` · branch: `develop/v0.8` · not
released

Version 0.8 focuses on safe 0.7-to-0.8 data migration, visible project-state
restoration, faster course startup, smaller packages and clearer architectural
boundaries. The current local development check reports 573 passed tests, one
platform-related skip and eight passing E2E tests. Commit `f60df90` passed the
Python 3.11–3.13 CI and all four desktop builds with 567 regular and seven E2E
tests. Full
offline runtime rebuilds passed on all four packaged targets. Real-device
verification remains required before release. Stable downloads therefore
continue to point to 0.7.1.
