# in:si 0.8 – Release-Notes (Entwurf)

Stand: 22. August 2026 · Zweig: `develop/v0.8` · noch nicht veröffentlicht

Diese Datei begleitet die Entwicklung von 0.8. Sie wird nach jedem
abgeschlossenen, getesteten Arbeitsschritt aktualisiert. Die stabilen Downloads
bleiben bis zur Freigabe bei 0.7.0.

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

## Wartbarkeit und Paketgröße

- Große UI- und Testmodule werden mit Architekturbudgets begrenzt und
  schrittweise fachlich getrennt. Der zentrale `test_guide.py` sank bislang von
  2.862 auf 1.920 Zeilen; 33 Runtime-, IDE- und Pyxel-Prüfungen liegen nun in
  einem eigenen, lokal rund 3,7 Sekunden schnellen Testmodul.
- Die doppelte Updateoberfläche wurde entfernt; App-, Kurs- und Inhaltsabgleich
  haben einen gemeinsamen Einstieg.
- Das Offline-Wheelhouse ist vom App-Paketbaum getrennt. Der lokale
  macOS-ARM-DMG-Prototyp sank von rund 113 MB auf rund 82 MiB.
- Der selbst gepflegte Python-Produktivcode liegt aktuell bei 18.479 Zeilen,
  gegenüber 18.746 Zeilen zu Beginn der Konsolidierung (−267, rund −1,4 %),
  obwohl Migration und Projektwiederherstellung hinzugekommen sind.

## Aktueller Teststand

- 457 normale Prüfungen bestanden;
- eine Linux-Bubblewrap-Prüfung auf macOS übersprungen;
- vier NiceGUI-E2E-Prüfungen bewusst separat auszuführen;
- vollständige E2E-, Offline-Build-, Sandbox- und Schulgeräte-Matrix vor der
  Freigabe weiterhin erforderlich.

## Noch offen vor der Freigabe

- weitere reale 0.7-Datenbestände und physisch entfernte Datenträger gegen die
  Migration und Wiederherstellung testen;
- Datenexport und vollständiges lokales Löschen als verständlichen
  Oberflächenablauf fertigstellen;
- reproduzierbare Paket-Locks, Offline-Runtime-Aufbau und Paketgrößen für
  Windows, Linux, macOS Intel und macOS ARM nachweisen;
- Sandbox als letzten großen Plattformblock prüfen und härten;
- verbleibende große Module und Sammeltests weiter zerlegen, ohne neue
  Kompatibilitätsschichten aufzubauen;
- Toolbar, Kernabläufe und Performance auf echten Zielgeräten manuell abnehmen.

Die ausführliche technische Historie steht in der [Roadmap](../ROADMAP.md),
Auswirkungen und Workarounds in den [bekannten Problemen](../KNOWN_ISSUES.md).

---

# in:si 0.8 – Draft release notes

Status: 22 August 2026 · branch: `develop/v0.8` · not released

Version 0.8 focuses on safe 0.7-to-0.8 data migration, visible project-state
restoration, faster course startup, smaller packages and clearer architectural
boundaries. The current development check reports 457 passed tests, one
platform-related skip and four separately executed E2E tests. Full E2E,
offline-build, sandbox and real-device verification remains required before
release. Stable downloads therefore continue to point to 0.7.0.
