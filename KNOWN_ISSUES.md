# Bekannte Probleme und Einschränkungen

Stand: 23. August 2026, Entwicklungsstand 0.8 auf `develop/v0.8`

Diese Liste nennt bekannte, reproduzierbare Probleme und bewusst noch nicht
erfüllte Produktzusagen. Sie ist keine vollständige Sammlung zukünftiger
Funktionen; dafür gibt es die [Roadmap](ROADMAP.md). Ein behobener Eintrag wird
entfernt oder im [Changelog](CHANGELOG.md) als erledigt dokumentiert.

## Offen für den Abschluss von 0.8

| Problem | Auswirkung | Derzeitiger Umgang | Ziel |
|---|---|---|---|
| Die überarbeitete TOAST-UI-Toolbar ist bei den vorgesehenen schmalen Browser- und nativen Fensterbreiten noch nicht vollständig manuell abgenommen. | Die Toolbar bleibt nun innerhalb des Editorrahmens und kann horizontal scrollen; bei unbekannten WebView-Größen sind optische Abweichungen weiterhin möglich. Bearbeitung und Speicherung funktionieren. | Bei Bedarf innerhalb der Toolbar horizontal scrollen. | Browser- und native Breiten in der manuellen 0.8-Matrix abschließend prüfen. |
| Die manuelle Schulgeräte-Matrix ist noch offen. | Automatisierte Builds prüfen viele technische Eigenschaften, ersetzen aber keinen vollständigen Test auf realen Windows-, macOS- und Linux-Geräten. | Entwicklungstests und CI-Builds verwenden; Alpha-Status beachten. | Dokumentierte Smoke-Tests vor der Freigabe von 0.8. |
| Vier browsergestützte NiceGUI-E2E-Prüfungen sind vom normalen lokalen Testlauf getrennt. | Der normale Lauf bleibt schnell und reproduzierbar, deckt den vollständigen Browserweg aber nicht ab. In eingeschränkten Entwicklungsumgebungen fehlen dafür nutzbare Prozess-Semaphoren. | E2E-Prüfungen mit `pytest -m e2e` in einer geeigneten lokalen Umgebung oder CI ausführen. | Grüner E2E- und Plattformnachweis vor der 0.8-Freigabe. |
| Reproduzierbare Paket-Locks und Offline-Buildnachweise fehlen noch für Windows, Linux und macOS Intel. | Das verkleinerte Wheelhouse und der vollständige Offline-Runtime-Aufbau sind bislang lokal für macOS ARM nachgewiesen. | 0.8 nicht allein anhand des lokalen ARM-Builds veröffentlichen. | Alle vier Release-Builds samt Manifest, Paketgröße und Offline-Aufbau prüfen. |

## Plattform- und Sicherheitsgrenzen

| Einschränkung | Bedeutung und sicherer Umgang | Geplante Einordnung |
|---|---|---|
| Die Desktop-Pakete sind noch nicht produktionssigniert; der macOS-Build ist nur ad-hoc signiert und nicht notarisiert. | Betriebssysteme können Warnungen anzeigen oder den Start blockieren. Pakete nur aus den offiziellen GitHub Releases beziehungsweise den zugehörigen dokumentierten Builds beziehen. | Produktionsverteilung spätestens für 1.0. |
| Ein unter einem synchronisierten macOS-`Documents`-Ordner erzeugter loser `.app`-Ordner kann nach dem Signieren erneut Finder-/File-Provider-Metadaten erhalten. | `codesign --verify` kann für den losen lokalen Build fehlschlagen, obwohl der Buildinhalt korrekt ist. | Für die Verteilung `build_macos_dmg.py` verwenden; es bereinigt und signiert den tatsächlichen Payload im privaten Tempordner. Der erzeugte 0.7-DMG-Payload wurde lokal erfolgreich verifiziert. | Dauerhafte Buildumgebungen außerhalb synchronisierter Ordner verwenden; der CI- und Releaseweg bleibt der DMG. |
| Der macOS-Runner verwendet derzeit `/usr/bin/sandbox-exec` und eine von Apple nicht als stabile öffentliche API zugesagte Profilsprache. | Nach einem macOS-Update kann der Selbsttest scheitern. in:si startet Fremdcode dann nicht ungeschützt, sondern sperrt den integrierten Start. | Signierter und notarisierter Sandbox-Helper für 1.0. |
| Unter Linux benötigt der integrierte Fremdcodestart Bubblewrap. Grafische Sandboxstarts funktionieren nur über Wayland, nicht über einen pauschal freigegebenen X11-Socket. | Ohne funktionsfähiges Bubblewrap bleibt der integrierte Start gesperrt. Unter X11 oder für besondere Geräte ist **In IDE öffnen** der bewusste Ausweichweg; dort gilt die in:si-Sandbox nicht. | Unterstützte Linux-Konfigurationen bis 1.0 abschließend festlegen und dokumentieren. |
| Starts in Thonny, VS Code oder einer anderen externen IDE laufen mit den normalen Rechten des Benutzerkontos. | Netzwerk, Hostdateien und externe Programme sind dort nicht durch den in:si-Runner begrenzt. | Dauerhafte Produktgrenze; die Oberfläche muss diesen Wechsel klar kennzeichnen. |
| Betriebssystem-Sandboxen sind keine Garantie gegen unbekannte Kernel-, Runtime-, Grafik- oder Sandboxlücken. | Nur nachvollziehbare Kursquellen verwenden, Rechte klein halten und wichtige Projekte zusätzlich sichern. | Dauerhafte Sicherheitsgrenze; Details stehen in `SECURITY.md`. |

## Noch fehlende Produktfähigkeiten

Diese Punkte sind keine Defekte des aktuellen Entwicklungsstands, begrenzen aber
den heutigen Einsatz:

- die 0.7→0.8-Datenmigration und sichtbare Wiederherstellung von
  Projektständen sind umgesetzt, benötigen vor dem Release aber weitere reale
  0.7-Datenbestände, Hardwareproben mit entfernbaren Datenträgern sowie die
  vollständige E2E- und Plattformmatrix;
- getrennte lokale Profile für mehrere Personen auf demselben Gerät fehlen bis
  0.9;
- PyKIM ist derzeit das einzige vollständig angebundene Fachmodul; weitere
  Engines werden ab 0.9 praktisch erprobt und in 1.1 ausgebaut;
- Setup-, Kurs-, Trainer- und Datenformate gelten während der Alpha-Phase noch
  nicht als langfristig stabil; die 1.x-Kompatibilitätszusage beginnt mit 1.0;
- Klassenverwaltung, Notenverwaltung und verpflichtende Cloudkonten sind
  bewusst nicht vorgesehen.

## Kürzlich behoben

Persönliche App-Daten und alle erreichbaren registrierten Kursordner lassen
sich nun gemeinsam exportieren. Eine getrennte, exakt zu bestätigende Aktion
verschiebt registrierte Kurse und den vollständigen lokalen App-Datenordner in
den Systempapierkorb; externe Kopien und Exporte bleiben unberührt.

Der Wechsel des TOAST UI Editors in den WYSIWYG-Modus konnte Browser und
NiceGUI-Fenster einfrieren. Ursache war ein globaler DOM-Beobachter, der
Schaltflächen in den von ProseMirror verwalteten Editorbereich einfügte und
dadurch eine endlose Änderungsfolge auslöste. Dieser Bereich wird nun
ausgeschlossen; der Wechsel friert in den geprüften Abläufen nicht mehr ein.
Bei diesem Editorproblem bleibt die oben genannte Toolbar-Positionierung offen.

App-, Inhalts- und Kursrepositoryprüfungen werden nicht mehr beim Öffnen einer
Ansicht oder eines Kurses gestartet, sondern nur nach einem bewussten Import
oder Klick. Außerdem enthält der verschlüsselte Lernstandsexport keinen
automatisch ermittelten Systembenutzernamen mehr. Speicherorte, Netzwerkziele,
Exportinhalte und Löschwege sind nun in `DATENSCHUTZ.md` zusammengeführt.

Eine deutsche und englische Kurzdokumentation wird als Markdown mit Wheel und
Desktop-Paketen ausgeliefert und ist über **Hilfe** direkt in der App lesbar.
Unter **Quellen** stehen AGPL, Lizenzumfang und Drittanbieterhinweise ebenfalls
vollständig offline zur Verfügung.
