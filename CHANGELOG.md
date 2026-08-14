# Änderungen

## Unveröffentlicht

- sichtbare Desktop-Lernumgebung von PyKIM Suite zu **in:si** umbenannt;
  ausführbare Dateien, App-Bundle und Release-Artefakte verwenden den sicheren
  technischen Namen `insi`.
- `insi` als eigenständigen Kommandozeileneinstieg ergänzt; bestehende
  Kursformate und lokale Speicherorte bleiben über Migrationen kompatibel.
- den bisherigen 2.500-Zeilen-UI-Einstieg in einen kleinen Application Composer,
  einen expliziten `AppContext` und getrennte Kurs-, Setup-, Werkzeug-, Aufgaben-
  und Abgabeansichten zerlegt; Architekturgrenzen werden durch Tests geschützt.
- übliche Repository-Dokumente wie `README.md`, `CHANGELOG.md` oder
  `SECURITY.md` bei der Kursanalyse standardmäßig ignoriert und aus bereits
  importierten Skript- und Aufgabenlisten ausgeblendet.
- in:si mit gefilterter Historie in das eigenständige Repository
  `finalnode/insi` überführt und den bisherigen Suite-Namespace `pykim.guide`
  entfernt; PyKIM hängt weder von der Anwendung noch von ihrer Kursverwaltung
  ab.
- Footerlinks in eine gemeinsame Quellenübersicht überführt, die Software,
  Lizenz, Kursrepository, Verantwortliche und Aufgabenquellen bündelt.
- Kurs-, Aktivitäts- und Trainerregistrys beim Inhaltswechsel explizit auf
  denselben geprüften Stand umgestellt.
- farbbasierte Hindernisse, Hintergrundfarben, Nachbarschaftserkennung und
  vorbereitete Spielfelder ergänzt.
- einsammelbare Farbfelder samt automatisch prüfbaren Sammelaufgaben ergänzt.
- gemeinsame Ausführungsrichtlinie für Schüler-, Kurs- und Beispielcode
  eingeführt: getrennte Prozessgruppen, bereinigte Umgebungen sowie Laufzeit-
  und Ausgabegrenzen für integrierte Programmläufe.
- aktuellen Schutzumfang und die noch fehlende garantierte OS-Sandbox sichtbar
  im Systemcheck und in `SECURITY.md` dokumentiert.
- veränderlichen Kernzustand für Position, Welt, Audio und Animation in einer
  gebundenen `Runtime`-Standardinstanz zusammengeführt, ohne die imperative API
  zu verändern.

## 0.5.5

- Kursstudio zum Anlegen, Bearbeiten, Zuordnen, Prüfen und Vorschauen eigener
  Skripte, Aufgaben und Trainerdaten ergänzt.
- bestehende Ordner analysierbar gemacht und einen vollständigen Export als
  portables Kursarchiv ergänzt.
- ZIP-Kursimport mit Pfadvalidierung, Strukturprüfung und Konfliktbehandlung
  eingeführt.
- M@rkdown-Parser und -Validator für Aufgabenmetadaten, Hinweise, Quellen und
  Tags ergänzt.
- Kursupdates sichern lokale Schülerarbeit weiterhin getrennt von aktivierten
  Kursinhalten; geplante Kompatibilitätsregeln sind dokumentiert.
- App- und Favicon-Ressourcen in Desktop-Builds aufgenommen.

## 0.5.4.1

- Versions- und Downloadverweise für die korrigierten Desktop-Builds
  vereinheitlicht.

## 0.5.4

- Zuordnungsaufgaben und verschiebbare Codeblöcke samt Ausführung und
  automatischer Auswertung ergänzt.
- gestufte Hinweise, Aufgabenquellen und lokale Erfassung genutzter Hinweise
  eingeführt.
- öffentlichen Kurskatalog mit Tags, Kurzbeschreibungen und Installation
  frei verfügbarer Kurse ergänzt.
- Update-Hinweis zu einem Dialog mit getrennten App- und Inhaltsupdates
  ausgebaut.
- Trainer für Code-, Antwort- und strukturbezogene Aufgaben erweitert.

## 0.5.3

- Windows-Desktopstart diagnostizierbar gemacht und einen Browser-Fallback
  ergänzt, wenn das native Fenster nicht geöffnet werden kann.
- kompatible eingebettete .NET-/pythonnet-Laufzeit festgelegt und im
  Build-Workflow geprüft.
- automatischen Windows-Starttest samt Diagnoseartefakten ergänzt.

## 0.5.2

- Beispielgalerie um sichtbaren Laufstatus, Programmausgabe und Stop-Funktion ergänzt.
- Grafische Beispiele weisen während der Ausführung auf ihr separates Fenster hin.
- Kursimport zeigt Spinner, Fortschrittsbalken und einen verständlichen Arbeitshinweis.
- paralleler Download kleiner Kursdateien verkürzt den ersten Import deutlich.

## 0.5.1

- Kurslöschung reagiert ohne zusätzliches Zeichen auf den exakt eingegebenen Kursnamen.
- Desktop-Builds enthalten ein verlässliches CA-Bündel für den HTTPS-Abruf von Kursinhalten.
- Beispielkurs und Setupdatei sind direkt im Downloadbereich der README verlinkt.

## 0.5.0

- mehrere Kurse pro Installation samt kompakter Auswahl beim App-Start ergänzt
- `.pykim-setup`-Dateien direkt in der Kursauswahl importierbar gemacht
- Repository-Inhalte automatisch aus `Skripte/`, `Aufgaben/` und `Trainer/`
  entdeckt; Dateien und Ordner mit führendem `_` werden ignoriert
- getrennte, offline nutzbare Inhaltsstände pro Kurs eingerichtet
- automatischen Repo-Abgleich beim Kursstart und manuellen Refresh ergänzt
- freie Aufgaben ohne Trainer samt lokal gespeichertem Antwortfeld unterstützt
- Kursordner direkt aus der Auswahl im plattformspezifischen Dateimanager öffnen
- Kurse nach exakter Namensbestätigung sicher in den Systempapierkorb verschieben
- Versionsangabe des macOS-Bundles an `pyproject.toml` gekoppelt
- `get_position()` für imperative und objektorientierte Positionsabfragen ergänzt
- reproduzierbare PyInstaller-Builds für Windows und Linux ergänzt
- GitHub-Actions-Matrix für Windows, Linux, macOS Intel und Apple Silicon samt
  Release-Artefakten eingerichtet
- erfolgreiche Plattformpakete in getrennten `dist/releases`-Buildordnern
  gesammelt und bei Versionstags automatisch als GitHub Release veröffentlicht
- gemeinsamen Desktop-Einstieg und plattformgerechten eingebetteten
  Python-Runner eingeführt
- veralteten lokalen Kurs-Snapshot und betriebssystemgenerierte Dateien aus dem
  Repository entfernt

## 0.4.0

- `world.zoom()` als Kamera-Zoom umgesetzt: größere Weltpixel bei unveränderter
  Fenster- und Weltgröße
- Projektansicht zu einem Arbeitsbereich mit seitlicher Projektauswahl und
  breitem Python-Editor umgebaut
- `README.md` pro Schülerprojekt samt Markdown-Editor, Live-Vorschau und
  Reflexionsvorlage ergänzt
- atomare Speicherung und Konflikterkennung für Projektcode und Dokumentation
  eingebaut
- übernommene Pyxel-Beispiele sofort mit „Meine Projekte“ synchronisiert
- Python-Spielwiese um Syntaxhervorhebung sowie Ein- und Ausrücken mit
  `Tab`/`Shift+Tab` erweitert
- festen, kompakten Suite-Footer mit Repository-, Lizenz- und Herkunftshinweis
  ergänzt

## 0.3.0

- PyKIM Suite als lokale Desktop-Lernumgebung ausgebaut
- Kursinhalte von der App getrennt und per `.pykim-setup` konfigurierbar gemacht
- Skripte, Aufgaben und YAML-Trainer aus einem Kurs-Repository synchronisiert
- Trainerdateien vor Testläufen gegen ihre Repository-Hashes geprüft
- Aufgabenansicht, Testdetails, Codeeditor und Lernstand überarbeitet
- Thonny-, VS-Code- und Python-Laufzeiterkennung ergänzt
- Pyxel-Beispiele, Ressourceneditor und persönliche Projekte integriert
- Imperative und objektorientierte Lernwege getrennt strukturiert
- Mehrere Pixel, parallele Abläufe, Sichtbarkeit, Farben und Töne erweitert
- Persönliches Modul `erweiterungen.py` für eigene Funktionen und Klassen ergänzt
- macOS-App- und DMG-Build vorbereitet

## 0.2.0

- Erste zusammenhängende PyKIM-API, Traineraufgaben und NiceGUI-Prototypen
