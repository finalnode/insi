# in:si 0.8 – Release-Notes (Entwurf)

Stand: 27. August 2026 · Version: `0.8.0.dev0` · Zweig: `develop/v0.8` · noch
nicht veröffentlicht

Diese Datei begleitet die Entwicklung von 0.8. Sie wird nach jedem
abgeschlossenen, getesteten Arbeitsschritt aktualisiert. Die stabilen Downloads
bleiben bis zur Freigabe bei 0.7.1.

Der Funktionsumfang ist seit dem 23. August 2026 geschlossen. Das
[Abschlussprotokoll](v0.8-abschlussprotokoll.md) trennt umgesetzte Funktionen,
lokale Nachweise und die noch offenen Freigabeprüfungen. Bis zu deren Abschluss
kommen keine weiteren Produktfunktionen hinzu.

## Was 0.8 sichtbar verbessert

- Lernende können automatische und benannte Projektstände in einer Zeitleiste
  sehen, kommentieren und sicher wiederherstellen. Vor dem Rücksprung wird der
  aktuelle Arbeitsstand erneut gesichert.
- Einstellungen, Kursmarker und Lernstände werden über eine versionierte,
  idempotente 0.7→0.8-Migration mit Originalbackup aktualisiert.
- Kurse öffnen schneller: Eine künstliche Mindestwartezeit entfällt, inaktive
  Ansichten werden erst bei Bedarf gebaut und mehrfaches Einlesen von Kurs- und
  Lernstandsdaten wurde reduziert.
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
  Schülerdateien bleiben dabei durch eigene Regressionstests abgesichert;
  `course_setup.py` sank von 467 auf 444 Zeilen.
- ZIP-Prüfung und -Erstellung sind von der Speicherung installierter Inhalte,
  Runtime-Stände und Quellenmarker getrennt. Die beiden Module umfassen
  zusammen 550 statt 557 Zeilen; Kursdateien und Offline-Wheels werden beim
  Export nur noch einmal gelesen.
- Der Runtime-Preflight wiederholt fehlgeschlagene Paketprüfungen nicht mehr
  und prüft einen bereits verworfenen bevorzugten Interpreter bei der
  anschließenden Suche nicht erneut. `runtime.py` sank damit von ursprünglich
  901 auf 863 Zeilen.
- Das Offline-Wheelhouse ist vom App-Paketbaum getrennt. Der lokale
  macOS-ARM-DMG-Prototyp sank von rund 113 MB auf rund 82 MiB.
- Die Desktop-Builds verwenden aus ihren vier Zielmanifesten abgeleitete
  Dependency-Locks für Windows, Linux, macOS Intel und macOS ARM.
- Der selbst gepflegte Python-Produktivcode liegt nach den Freigabekorrekturen
  bei 18.806 Zeilen, gegenüber 18.746 Zeilen zu Beginn der Konsolidierung
  (+60, rund +0,3 %). Der sicherheitskritische Dateivertrag und
  seine Oberfläche bleiben bewusst getrennt und gezielt testbar.

## Aktueller Teststand

- 483 normale Prüfungen bestanden;
- eine Linux-Bubblewrap-Prüfung auf macOS übersprungen;
- vier NiceGUI-E2E-Prüfungen im eigenen PR-CI-Job ausgeführt und bestanden;
- CI auf Python 3.11 bis 3.13 sowie Desktop-, Sandbox- und native GUI-Matrix auf
  Commit `c3e2923` bestanden;
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

Status: 27 August 2026 · version: `0.8.0.dev0` · branch: `develop/v0.8` · not
released

Version 0.8 focuses on safe 0.7-to-0.8 data migration, visible project-state
restoration, faster course startup, smaller packages and clearer architectural
boundaries. The current development check reports 483 passed tests, one
platform-related skip and four passing E2E tests in a dedicated CI job. Full
offline runtime rebuilds passed on all four packaged targets. Real-device
verification remains required before release. Stable downloads therefore
continue to point to 0.7.1.
