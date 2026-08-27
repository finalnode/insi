# Änderungen

## 0.8.0 – in Entwicklung

- den veröffentlichten `v0.7.1`-Stand in `develop/v0.8` übernommen und die
  stabile Downloadversion sowie die Plattformnachweise fortgeschrieben;
- die Mindestversion für Quellinstallationen und erkannte Laufzeiten auf
  Python 3.11 angehoben, weil das festgelegte Pyxel 2.9.9 für Python 3.10
  nicht veröffentlicht wird;
- Windows-AppContainer erhalten für den gestarteten PyInstaller-Runner neben
  dem Runtimeordner eine explizite Datei-Lesefreigabe, damit das eingebettete
  PKG-Archiv unabhängig von geerbten ACLs erneut geöffnet werden kann;
- Paket- und Laufzeitversion des Entwicklungszweigs auf `0.8.0.dev0`
  vereinheitlicht; stabile Downloadlinks bleiben bis zur Freigabe bei 0.7.1;
- die ausgeschriebene Bedeutung **informatica simplicissima** und ihre
  didaktische Leitidee in der deutschen und englischen README wieder direkt in
  der Einleitung sichtbar gemacht;
- den Funktionsumfang für 0.8 geschlossen und in einem Abschlussprotokoll mit
  umgesetzten Bereichen, Messwerten, Wartungsschuld und sechs verbleibenden
  Freigabeschritten festgehalten;
- den Windows-AppContainer-Nachweis nach dem grünen `v0.7.1`-Release für den
  zusammengeführten 0.8-Stand und echte Schulgeräte als Freigabepunkt
  beibehalten;
- versionierte, idempotente 0.7→0.8-Migrationen für Einstellungen, Kursmarker
  und Lernstände samt unverändertem Originalbackup und simulierten
  Abbruch-/Datenträgerfehlern ergänzt;
- automatische und benannte Projektstände mit Kommentaren, Prüfsummen,
  Aufbewahrungsregeln und sicherer Wiederherstellung in einer sichtbaren
  Zeitleiste umgesetzt;
- einen portablen Gesamtexport für persönliche App-Daten und alle erreichbaren
  registrierten Kursordner sowie eine separat bestätigte Papierkorbaktion für
  sämtliche lokalen in:si-Daten im Werkzeugbereich ergänzt;
- Pyxel-Sprite- und Musikeditor als getrennte Projektaktionen angebunden und
  fehlgeschlagene Editorstarts sichtbar gemacht;
- Runtime-, Kursauswahl-, Setup-, Aufgaben- und Workspace-Startpfade
  konsolidiert; unnötige Prozessstarts, Dateizugriffe, Animationen und eine
  künstliche Mindestwartezeit entfernt;
- zunächst nur die sichtbare Kursansicht aufgebaut und die übrigen Ansichten
  bei ihrer ersten Auswahl nachgeladen;
- doppelte Updateoberfläche entfernt und App-, Kurs- und Inhaltsabgleich im
  gemeinsamen Werkzeugbereich zusammengeführt;
- unabhängige App- und allgemeine Inhaltsprüfung parallelisiert, die für
  Repositorykurse überflüssige allgemeine Inhaltsabfrage übersprungen und den
  nie gelesenen Update-Statuscache entfernt; beide Inhaltswege aktivieren einen
  geprüften Stand nun über denselben atomaren Markerpfad;
- die vier parallelen Installationsfolgen für neue beziehungsweise vorhandene
  Repository- und ZIP-Kurse auf je eine gemeinsame Transaktion und einen
  gemeinsamen Workspace-Aktivierungspfad zurückgeführt; Regressionstests
  sichern den Erhalt vorhandener Schülerdateien;
- ZIP-Formatprüfung und Erstellung von der atomaren Speicherung installierter
  Kursinhalte, Runtime-Stände und Quellenmarker getrennt; gemeinsame
  JSON-Aktivierung vereinheitlicht und Exportdateien sowie Offline-Wheels nur
  noch einmal vom Datenträger gelesen;
- fehlgeschlagene Paketprüfungen im Runtime-Preflight werden nicht mehr
  unmittelbar wiederholt; ein bereits verworfener bevorzugter Interpreter
  wird bei der anschließenden Suche nicht erneut per Subprocess geprüft;
- große Sammeltests schrittweise in fachlich getrennte, schneller ausführbare
  Testmodule zerlegt und Architekturbudgets gegen erneutes Wachstum ergänzt;
  `test_guide.py` sank dabei bislang von 2.862 auf 1.460 Zeilen; 33 Runtime-,
  IDE- und Pyxel-Verträge sowie 16 Inhalts-, Update- und Zertifikatsverträge
  liegen in eigenen, gezielt ausführbaren Modulen;
- Offline-Wheelhouse vom App-Paketbaum getrennt und den lokalen
  macOS-ARM-DMG-Prototyp von rund 113 MB auf rund 82 MiB verkleinert;
- Packaging-Artefakte auf den Namen in:si umgestellt, direkte Abhängigkeiten
  festgelegt und plattformspezifische Buildmanifeste ergänzt;
- externe Trainer-Plugins vor dem Import inventarisiert und an eine sichtbare,
  paket- und versionsbezogene Zustimmung gebunden;
- Stand 27. August 2026: 477 normale Prüfungen bestanden, eine
  plattformbedingt übersprungen sowie vier separat ausgeführte E2E-Prüfungen
  bestanden;
  selbst gepflegter Python-Produktivcode 18.806 gegenüber 18.746 Zeilen zu
  Beginn der 0.8-Konsolidierung.

## 0.7.1 – 2026-08-27

- einen Windows-Startfehler behoben, bei dem Kursordner unter
  `C:\Users\...` durch die Auswertung des Footer-Tooltips als Python-Literal
  einen HTTP-500-Fehler auslösten.

## 0.7.0 – 2026-08-22

- in:si von MIT auf `AGPL-3.0-or-later` umgestellt; bereits veröffentlichte
  MIT-Versionen, PyKIM, externe Kurse und Drittanbieterbestandteile behalten
  ihre jeweiligen Lizenzen. Hauptlizenz und Lizenzabgrenzung werden nun auch
  in die Desktop-Pakete aufgenommen.
- deutsche und englische Offline-Dokumentation für Lernende, Lehrkräfte und
  Kursautorinnen beziehungsweise Kursautoren ergänzt und über **Hilfe** direkt
  in der App zugänglich gemacht.
- den Quellen-/Lizenzdialog um Copyright, Gewährleistungsausschluss und lokal
  lesbare AGPL-, Umfangs- und Drittanbietertexte erweitert.
- die TOAST-Toolbar innerhalb des Editorrahmens begrenzt, Pluginaktionen vor
  den optionalen Scrollbereich verschoben und das Annotationsmenü aus dem
  scrollbaren Editor-DOM gelöst.
- einen strikten, transitiven Laufzeit-Lizenzcheck in alle Desktop-Builds
  aufgenommen und vorhandene Paketmetadaten samt Lizenzdateien in die
  Distribution übernommen.
- App-, Inhalts- und Kursrepositoryprüfungen auf ausdrücklich manuell
  ausgelöste GitHub-Abfragen umgestellt; die Oberfläche erklärt den
  Netzwerkzugriff vor der Prüfung.
- den lokalen Systembenutzernamen vollständig aus verschlüsselten
  Lernstandsexporten entfernt. Ohne bewusst eingetragenen Namen oder Kürzel
  bleibt das Identitätsfeld leer.
- eine technische Datenschutz- und Datenbestandsübersicht mit Speicherorten,
  Netzwerkzielen, Exportinhalten, Empfängern sowie Lösch- und
  Aufbewahrungswegen ergänzt.

- die Trainingsschicht von PyKIM-Datenmodellen entkoppelt und einen
  fachmodulneutralen Engine-Vertrag für Abgaben, Ergebnisse und Starterdateien
  eingeführt. PyKIM ist als kompatibler Adapter angebunden; weitere Engines
  können sich über `insi.trainer_backends` registrieren und Quelltext,
  Einstiegspunkte oder ganze Projektverzeichnisse auswerten.
- das versionierte Format `insi-trainer-v1` mit expliziter Engine eingeführt;
  vorhandene numerische PyKIM-Definitionen bleiben kompatibel. Freie Antworten,
  Zuordnungen und Parsons-Puzzles werden als Core-Aktivitäten gemeinsam
  registriert.
- den MIT-lizenzierten TOAST UI Editor samt deutscher Oberfläche und
  Lizenztexten vollständig offline gebündelt. Kursinhalte und
  Projektdokumentationen lassen sich visuell oder direkt als Markdown
  bearbeiten; gespeichert wird ausschließlich portables Markdown.
- Schwierigkeit, Tags, gestufte Hinweise und Quellen im Kursstudio aus dem
  sichtbaren Aufgabentext gelöst und als visuelle Formularfelder angebunden;
  ein eigenes TOAST-Plugin stellt kursabhängige Annotationen direkt in der
  Editor-Toolbar sowie live validierte, anklickbare Zeilenmeldungen bereit.
  Projektdokumentationen der Lernenden bleiben ohne Kursannotation-Menü.

- einen zentralen, capability-basierten Sandbox-Runner eingeführt: externer
  Kurs- und Schülercode startet nur noch mit einem verifizierten OS-Adapter;
  ohne Adapter verweist in:si auf die konfigurierte IDE und fällt nicht still
  auf einen ungeschützten Prozess zurück.
- unter Linux Bubblewrap mit getrennten Datei-, Prozess- und
  Netzwerk-Namespaces angebunden; der Runner sieht nur Programm, Runtime,
  aktive Kursinhalte und ausdrücklich freigegebene Workspace-Dateien. Netzwerk
  ist standardmäßig gesperrt, grafische Starts benötigen Wayland. Ein echter
  Selbsttest prüft Datei-, Netzwerk- und Namespace-Isolation; der Desktop-Build
  prüft zusätzlich Prozess-, RAM-, CPU- und temporäre Schreibgrenzen sowie ein
  Pyxel-Fenster über einen isolierten headless Weston.
- unter Windows einen nativen Broker ergänzt, der Schülercode in einem eigenen
  AppContainer ohne Netzwerkfähigkeit startet. Temporäre ACL-Freigaben zeigen
  ausschließlich auf Runtime, ausgewählte Lesedateien und vorgesehene
  Schreibbereiche; ein Job Object begrenzt CPU, RAM und Prozessanzahl und
  beendet beim Schließen den gesamten Prozessbaum. Ein echter Windows-CI-Test
  prüft Hostdatei-, Netzwerk-, Prozess- und Schreibgrenzen sowie die
  Pyxel-Grafikinitialisierung.
- unter macOS einen nativen Seatbelt-Adapter ergänzt, der pro Start nur
  ausgewählte Lese- und Schreibpfade freigibt, Netzwerkzugriff blockiert und
  seine Wirksamkeit vor der Freigabe mit einem echten Isolationstest prüft. Die
  macOS-CI testet zusätzlich Prozess-, RAM-, CPU- und Schreibgrenzen; ein
  optionaler manueller Test öffnet ein Pyxel-Fenster im Seatbelt-Profil.
- Prozessaufsicht für Lauf- und CPU-Zeit, Arbeitsspeicher, Kindprozessanzahl,
  Ausgabe sowie neu geschriebenes Datenvolumen ergänzt; bei einer Verletzung
  wird die gesamte Prozessgruppe mit sichtbarem Grund beendet.
- sichere Dateiimporte für globale, kursweite und projektbezogene Ressourcen
  ergänzt. Lerncode liest globale und kursweite Dateien nur, während
  ausschließlich das aktuelle Projekt beziehungsweise ein privater Laufbereich
  schreibbar ist.
- Projekte vor jedem integrierten Start automatisch versioniert, symbolische
  Links abgelehnt und höchstens zehn lokale Projektstände behalten.
- Lernfortschritt für Aufgabenläufe über eine private Laufkopie entkoppelt und
  nur validierte neue Trainer-Versuche in den Host-Lernstand zurückgeführt.

- neue Kurssetups und portable Kursarchive verwenden das neutrale Format
  `.insi-setup` (`insi-course-setup-v1`); vorhandene `.pykim-setup`-Dateien
  bleiben importierbar und werden in installierten Kursen mit Backup migriert.
- Kursarchive enthalten einen versionierten `runtime.toml`-Vertrag für Python
  und exakte Paketversionen; Zusatzpakete können optional und standardmäßig
  deaktiviert samt geprüfter Wheel-Abhängigkeiten für ausdrücklich gewählte
  Windows-, macOS- und Linux-Ziele eingebettet werden.
- vor Kursstart und nach Kursupdates werden Python-Version, Plattform,
  Paketversionen und Offline-Wheel-Prüfsummen kontrolliert; inkompatible Kurse
  bleiben gesperrt und bieten eine direkte Reparatur oder die Einrichtung einer
  getrennten Kursumgebung aus einem passenden Basis-Python an.
- virtuelle Python-Umgebungen behalten auf POSIX-Systemen ihren Interpreterpfad,
  auch wenn `bin/python` als Symlink auf das Basis-Python angelegt wurde.

## 0.6.0 – 2026-08-14

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
- konkrete Trainerregistrys, Zuordnungs-/Parsons-Aktivitäten, Konsolenfeedback
  und Versuchsspeicherung aus PyKIM nach `insi.training` verschoben; PyKIM wird
  nur noch über eine optionale Provider-Schnittstelle angebunden.
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
