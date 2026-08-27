# <img src="packaging/macos/assets/app-icon-master.png" alt="in:si-Logo" width="72" align="center"> in:si

[![Desktop-Builds](https://github.com/finalnode/insi/actions/workflows/build-desktop.yml/badge.svg?branch=main)](https://github.com/finalnode/insi/actions/workflows/build-desktop.yml)
[![Aktuelles Release](https://img.shields.io/github/v/release/finalnode/insi?label=Download)](https://github.com/finalnode/insi/releases/latest)
[![Lizenz: AGPL-3.0+](https://img.shields.io/badge/Lizenz-AGPL--3.0%2B-blue.svg)](LICENSE)

**Sprache:** Deutsch · [English](README.en.md)

**Dieser Entwicklungszweig baut in:si 0.8.0.dev0.** Er ist noch kein
veröffentlichtes Release. **in:si 0.7.1** bleibt die aktuelle stabile
Veröffentlichung der lokalen Desktop-Lernumgebung für modulare Informatikkurse.
Der aktuelle Arbeitsstand liegt auf
[`develop/v0.8`](https://github.com/finalnode/insi/tree/develop/v0.8); `main`
bleibt bis zur geprüften Freigabe auf dem 0.7-Stand.

Die Anwendung bringt Kursinstallation, Lerntexte, interaktive Aufgaben,
automatische Tests, Lernstand, Projekte und Autorenwerkzeuge in eine gemeinsame
Anwendung, die nach der Einrichtung weitgehend offline funktioniert.

Der Name **in:si** steht für **informatica simplicissima**: Informatik soll so
zugänglich wie möglich vermittelt werden, ohne echte Sprachen, Dateien und
Werkzeuge hinter einer vereinfachten Lernoberfläche zu verstecken. Die
didaktische Leitidee lautet: **So viel vereinfachen wie nötig, so wenig
abstrahieren wie möglich.**

in:si soll den Raum zwischen einer losen Materialsammlung und einem großen
Learning-Management-System füllen: Ein Kurs darf aus echten Markdown-, Python-
und Projektdateien bestehen, soll sich für Lernende aber trotzdem wie eine
zusammenhängende Anwendung anfühlen. Lehrkräfte sollen Inhalte kontrollieren,
weitergeben und weiterentwickeln können, ohne Schülerarbeit an einen
Herstellerdienst oder ein proprietäres Dateiformat zu binden.

Der aktuell verfügbare Beispielkurs vermittelt Python mit dem unabhängigen
Fachmodul [PyKIM](https://github.com/finalnode/PyKIM). Die Plattform ist für
weitere Fachmodule und Mischkurse vorbereitet, diese sind aber noch nicht
fertig implementiert.

> **Projektstatus: Alpha.** Lokale Datenformate und Oberflächen können sich noch
> ändern. Der macOS-Build ist nur lokal ad-hoc, nicht mit einer Developer-ID
> signiert und nicht notarisiert; die übrigen Desktop-Builds sind unsigniert.

> **Aktueller Buildnachweis:** `develop/v0.8` wurde auf Commit `d038417` für
> Windows, Linux sowie beide macOS-Architekturen erfolgreich gebaut. Windows-
> AppContainer und echter Fensterstart, Linux-Bubblewrap/Wayland sowie beide
> macOS-Seatbelt-Prüfungen bestanden. Zusätzlich wurde auf jeder Plattform eine
> frische Kurs-Runtime ausschließlich aus dem paketierten Offline-Wheelhouse
> aufgebaut. Die Abnahme auf echten Schulgeräten bleibt verbindlich.

> **Entwicklungsstand 0.8.0.dev0:** Auf `develop/v0.8` sind die versionierte
> Datenmigration, sichtbare Projektstände, lokale Datenkontrolle, schnellere
> Startpfade und ein fachlich besser testbarer Kern umgesetzt. Der
> aktuelle Nachweis umfasst 480 bestandene, eine plattformbedingt
> übersprungene und zusätzlich vier im eigenen CI-Job bestandene
> E2E-Prüfungen. Fortschritt und
> verbleibende Freigabeblocker stehen im
> [Entwurf der 0.8-Release-Notes](docs/release-notes-0.8.md). Der geschlossene
> Funktionsumfang und die noch offenen Nachweise stehen kompakt im
> [0.8-Abschlussprotokoll](docs/v0.8-abschlussprotokoll.md).

Die kompakte, offline auslieferbare Dokumentation beginnt unter
[docs/de](docs/de/erste-schritte.md). Sie enthält getrennte Einstiege für
Lernende, Lehrkräfte und Kursautorinnen beziehungsweise Kursautoren. Die
[englische Dokumentation](docs/en/getting-started.md) besitzt dieselbe Struktur.

## Warum in:si existiert

Informatikunterricht verteilt sich häufig auf viele einzelne Werkzeuge:
Lerntexte liegen in einem LMS oder als PDF, Programme in einer IDE, Aufgaben in
Arbeitsblättern, automatische Tests in zusätzlichen Skripten und Ergebnisse in
weiteren Ablagen. Für erfahrene Entwicklerinnen und Entwickler ist diese
Trennung normal. Für Lernende erzeugt sie früh organisatorische und technische
Hürden, die wenig mit dem eigentlichen Lernziel zu tun haben.

Gleichzeitig lösen vollständig webbasierte Plattformen dieses Problem oft mit
zentralen Konten, dauerhaftem Internetzugang und plattformeigenen Editoren oder
Formaten. Das kann im schulischen Alltag unpraktisch sein: Geräte und Netze sind
unterschiedlich ausgestattet, personenbezogene Lerndaten sollen sparsam
verarbeitet werden, und selbst erstellte Kurse sollen auch unabhängig von einem
einzelnen Dienst nutzbar bleiben.

in:si verfolgt deshalb einen lokalen, dateibasierten Mittelweg:

- Lernende erhalten einen gemeinsamen Einstieg für Lesen, Ausprobieren, Lösen,
  Testen und längere eigene Projekte;
- Lehrkräfte können Kurse mit normalen Dateien erstellen, prüfen, als ZIP
  weitergeben oder aus einem Repository aktualisieren;
- veröffentlichte Kursinhalte und persönliche Arbeit bleiben technisch
  getrennt, damit ein Kursupdate keine Lösungen überschreibt;
- echte Sprachen, Bibliotheken und IDEs bleiben sichtbar und austauschbar,
  anstatt hinter einer eigenen Lernsprache verborgen zu werden;
- nach der Einrichtung bleiben die zentralen Lernabläufe lokal und möglichst
  offline nutzbar.

Das Ziel ist nicht, jede Komplexität zu verstecken. in:si soll den Einstieg
strukturieren und Hilfen schrittweise zurücknehmbar machen. Wer später direkt
mit Python, Markdown, VS Code, Thonny oder Git arbeitet, soll die in Kursen
entstandenen Dateien weiterverwenden können.

## Grundidee und Zielgruppen

in:si trennt vier Dinge, die im Unterricht unterschiedliche Lebenszyklen
haben: die Desktop-Anwendung, ein Fachmodul wie PyKIM, die von einer Lehrkraft
veröffentlichte Kursquelle und den persönlichen Workspace der lernenden Person.
Dadurch können Anwendung und Kurs aktualisiert werden, während Lösungen,
Antworten, Lernstand und Projekte lokal erhalten bleiben.

Die Anwendung richtet sich an:

- **Lernende**, die Materialien, Aufgaben, Rückmeldungen und Projekte an einem
  Ort nutzen möchten, ohne zuerst eine vollständige Entwicklungsumgebung
  verstehen zu müssen;
- **Lehrkräfte**, die einen reproduzierbaren Kurs verteilen und dennoch echte
  Dateien, externe IDEs und eigene Unterrichtswege verwenden möchten;
- **Kursautorinnen und Kursautoren**, die Lerntexte, Metadaten, Trainer und
  Runtime-Anforderungen gemeinsam prüfen und portabel veröffentlichen wollen;
- **Entwicklerinnen und Entwickler von Fachmodulen**, die weitere Sprachen oder
  Themen über einen neutralen Trainervertrag anbinden möchten.

## Kurzüberblick und Navigation

| Frage | Antwort |
|---|---|
| Für wen? | Lernende, Lehrkräfte und Autorinnen und Autoren lokaler Informatikkurse |
| Was läuft heute? | Python-/PyKIM-Kurse auf Windows, Linux und macOS |
| Wo liegen Daten? | Lokal im Kursordner beziehungsweise in lokalen App-Verzeichnissen |
| Funktioniert es offline? | Ja, nach der Einrichtung; Zusatzpakete können optional ins Kurs-ZIP eingebettet werden |
| Wie kommen Kurse hinein? | `.insi-setup`, portables ZIP oder öffentlicher GitHub-Kurskatalog |
| Was bleibt bei Updates erhalten? | Lösungen, Projekte, Antworten und Lernstand im Student Workspace |
| Wie wird Lerncode begrenzt? | Integrierte Fremdcode-Starts benötigen eine verifizierte OS-Sandbox: AppContainer plus Job Object unter Windows, Bubblewrap unter Linux oder Seatbelt unter macOS |

Schnellnavigation:

- [Warum in:si existiert](#warum-insi-existiert)
- [Grundidee und Zielgruppen](#grundidee-und-zielgruppen)
- [Was in:si ist – und was nicht](#was-insi-ist--und-was-nicht)
- [Bekannte Probleme und Einschränkungen](#bekannte-probleme-und-einschränkungen)
- [Alle implementierten Funktionen](#alle-implementierten-funktionen)
- [Herunterladen und ausprobieren](#herunterladen-und-ausprobieren)
- [So funktionieren Kurse](#so-funktionieren-kurse)
- [Sicherheit, Offlinebetrieb und Datenschutz](#sicherheit-offlinebetrieb-und-datenschutz)
- [Datenschutz- und Datenbestandsübersicht](DATENSCHUTZ.md)
- [Entwicklung und Architektur](#entwicklung-und-architektur)
- [Roadmap](#roadmap)

## Was in:si ist – und was nicht

Im Alltag hat in:si drei eng verbundene Perspektiven: Lernende lesen einen
Kurs, bearbeiten Aufgaben und entwickeln Projekte; Lehrkräfte verwalten Kurse,
Laufzeiten und lokale Arbeitsbereiche; Autorinnen und Autoren erstellen
dieselben Inhalte mit Vorschau und Validierung. Es handelt sich dabei um eine
einzelne lokale Anwendung – nicht um drei getrennte Produkte oder einen Server,
der für den normalen Betrieb administriert werden muss.

| in:si ist … | in:si ist nicht … |
|---|---|
| eine lokale Lern- und Autorenanwendung | ein Cloud-LMS oder eine gehostete Schulplattform |
| eine Hülle für echte Sprachen, Dateien und Werkzeuge | eine proprietäre vereinfachte Programmiersprache |
| eine Plattform für versionierte Kursquellen und getrennte Schülerarbeit | ein Ersatz für GitHub, Moodle oder die Schulverwaltung |
| eine Lernumgebung für Unterricht und selbstständige Projektarbeit | ein Noten-, Klassen- oder Identitätsverwaltungssystem |
| ein strukturierter Einstieg in echte Entwicklungswerkzeuge | ein dauerhaft abgeschlossener Schonraum ohne Dateisystem oder externe IDEs |
| derzeit praktisch auf Python und PyKIM fokussiert | bereits eine fertige Universalumgebung für alle Informatikthemen |
| offline-first und ohne Konto nutzbar | vollständig ohne Netzwerk installierbar, sofern ein Kurs nicht alle Zusatzpakete einbettet |
| gegen typische Archiv- und Prozessfehler gehärtet | eine garantierte Sicherheitsgrenze gegen bösartigen Pythoncode |
| ein Alpha-Projekt mit funktionierenden Desktop-Builds | bereits eine signierte, notarisierte oder langfristig formatstabile Produktionsversion |

Diese Grenzen sind bewusst. Klassenverwaltung, Noten, Identitäten und
Echtzeitkommunikation gehören bereits zu bestehenden Schulplattformen und
würden zentrale personenbezogene Daten erfordern. in:si konzentriert sich
stattdessen auf den lokalen Lernarbeitsplatz und auf portable Schnittstellen zu
solchen Systemen. Ebenso soll der eingebaute Editor den Einstieg erleichtern,
nicht die freie Wahl einer später genutzten IDE verhindern.

**in:si und PyKIM sind getrennte Projekte.** in:si verwaltet Kurse, Lernstand,
Workspaces und Autorenabläufe. PyKIM liefert die Pixelwelt, die Python-API und
fachspezifische Prüfregeln. PyKIM kann ohne in:si verwendet werden und importiert
in:si nicht.

## Bekannte Probleme und Einschränkungen

in:si ist noch eine Alpha-Version. Die wichtigsten aktuell offenen Punkte sind:

- die Toolbar des neuen Kurseditors ist bei manchen Fensterbreiten noch nicht
  abschließend visuell abgenommen; ihre Breitenbegrenzung und das
  Überlaufverhalten wurden überarbeitet, und der zuvor beobachtete Freeze beim
  WYSIWYG-Wechsel ist behoben;
- manuelle Tests auf echten Windows-, macOS- und Linux-Schulgeräten sind für
  den Abschluss von 0.8 noch offen;
- die Desktop-Pakete sind nicht produktionssigniert; unter Linux benötigt die
  integrierte Sandbox Bubblewrap und für grafische Starts Wayland.

Auswirkung, Workaround, Zielversion und weitere Produktgrenzen stehen in der
vollständigen Übersicht [Bekannte Probleme und Einschränkungen](KNOWN_ISSUES.md).

## Alle implementierten Funktionen

Die folgenden Punkte sind vorhanden und durch automatisierte Tests abgedeckt.
Noch offene Arbeiten stehen ausschließlich in der [Roadmap](#roadmap).

### Lernen und Arbeiten

- mehrere lokale Kurse installieren, auswählen und wechseln;
- Skripte mit dynamischem Inhaltsverzeichnis lesen;
- vollständige Codebeispiele kopieren, starten und gezielt stoppen;
- Aufgaben im integrierten Editor oder in einer erkannten externen IDE lösen;
- Code-, Antwort-, Zuordnungs- und Code-Sortieraufgaben bearbeiten;
- gestufte Hinweise anzeigen und ihre Nutzung lokal erfassen;
- automatische Trainer mit verständlichem Feedback ausführen;
- Lernstand, Antworten und Versuche lokal speichern;
- eigene Python-/Pyxel-Projekte anlegen und im Dateimanager öffnen;
- automatische und benannte Projektstände mit Kommentar sichern, prüfen und
  ohne Verlust des aktuellen Arbeitsstands wiederherstellen;
- Projektdokumentationen visuell oder direkt als portables Markdown bearbeiten;
- Dateien gezielt global, für einen Kurs oder für ein Projekt in den
  in:si-Workspace kopieren;
- persönliche App-Daten und registrierte Kursordner gemeinsam als portables
  ZIP exportieren;
- persönliche Erweiterungen innerhalb des jeweiligen Kurses wiederverwenden;
- Thonny und VS Code mit dem ausgewählten Kursinterpreter starten;
- Pyxel-Ressourcen und offizielle Beispiele verwenden.

### Kurse installieren und verwalten

- neue `.insi-setup`-Dateien importieren;
- sichere portable Kurs-ZIPs importieren;
- öffentliche GitHub-Kursrepositories synchronisieren;
- freie Kurse aus einem lokal zwischengespeicherten Katalog installieren;
- Herkunfts- und Vertrauenswarnungen vor externen Importen anzeigen;
- Namenskonflikte als Kopie oder kontrolliertes Update behandeln;
- veröffentlichte Kursinhalte getrennt vom Student Workspace aktualisieren;
- Dateien und Ordner mit führendem Unterstrich aus Kursen ausblenden;
- Kursordner in den Systempapierkorb verschieben, ohne andere Verzeichnisse zu
  löschen;
- nach exakter Bestätigung alle registrierten Kurse und lokalen App-Daten in
  den Systempapierkorb verschieben.

### Laufzeit und Offlinepakete

- installierte Python-, Conda-, pyenv-, uv- und Thonny-Laufzeiten erkennen;
- pro Kurs eine getrennte verwaltete virtuelle Umgebung einrichten;
- Python-, PyKIM-, Pyxel- und Zusatzpaketversionen exakt in `runtime.toml`
  festlegen;
- vor Kursstart Python-Version, Betriebssystem, Architektur und Paketstände
  prüfen;
- beschädigte verwaltete Kursumgebungen reparieren;
- aus einem passenden Basis-Python eine neue Kursumgebung erzeugen;
- die Prüfung nach einem Kursupdate erneut ausführen;
- Diagnoseberichte ohne Schülerdateiinhalte erzeugen;
- zusätzliche Wheels optional für ausdrücklich gewählte Plattformen in ein
  Kurs-ZIP einbetten;
- eingebettete Wheels beim Import und vor ihrer Verwendung per SHA-256 prüfen.

### Kurse erstellen

- vollständige Kurse in der Kurswerkstatt anlegen und realistisch vorschauen;
- vorhandene Ordner analysieren und Dateien Skripten, Aufgaben oder Trainern
  zuordnen;
- Skripte, Aufgaben und Projektdokumentationen in einem lokal gebündelten
  Markdown-/WYSIWYG-Editor bearbeiten und jederzeit zur Quellansicht wechseln;
- M@rkdown-Annotationen über Kursformulare und ein kontextabhängiges Menü
  direkt in der Editor-Toolbar einfügen, ohne die Syntax auswendig zu lernen;
- Kurs-Markdown während des Schreibens mit dem kanonischen in:si-Validator
  prüfen und über anklickbare Meldungen zur betroffenen Zeile springen;
- Hinweise, Tags, Quellen, Lizenz und Verantwortung hinterlegen;
- automatische PyKIM-Trainer aus visuellen Prüfbausteinen erzeugen und
  optional direkt als YAML bearbeiten;
- lokale Kurse ohne Repository erstellen;
- eine öffentliche GitHub-Quelle als Kursmetadatum hinterlegen;
- standardmäßig kompakte Kurs-ZIPs exportieren;
- exakte Zusatzpakete bei Bedarf für Windows, Linux oder beide macOS-
  Architekturen einbetten;
- Setupdateien für einen einfachen Online-Import erzeugen.

### Plattform, Daten und Schutzmaßnahmen

- native Builds für Windows x86_64, Linux x86_64, macOS Intel und macOS Apple
  Silicon;
- Browsermodus als bewusste Alternative und als Desktop-Fallback;
- lokale Nutzung ohne Konto oder zentralen Server;
- getrennte Prozesse und Prozessgruppen für Schülerprogramme und Beispiele;
- zentraler Sandbox-Runner ohne stillen ungeschützten Fallback;
- Windows-Datei-, Netzwerk- und Prozessisolation mit AppContainer und Job
  Object;
- Linux-Dateisystem-, Prozess- und Netzwerkisolation mit Bubblewrap;
- macOS-Datei-, Netzwerk- und Prozessisolation mit einem dynamischen
  Seatbelt-Profil;
- Laufzeit-, CPU-, RAM-, Prozess-, Ausgabe- und Schreibgrenzen;
- kein Netzwerkzugriff für integrierten Kurs- und Schülercode;
- nur das aktuelle Projekt beziehungsweise ein privater Aufgabenlauf ist
  schreibbar; Kurs-, globale und Runtime-Dateien bleiben lesbar;
- automatische, begrenzte Projektstände vor integrierten Starts;
- bereinigte Umgebungsvariablen beim Start von Schülercode;
- validierte Repository-, Archiv- und Inhaltspfade;
- Schutz vor ZIP-Pfadwechseln, absoluten Pfaden und symbolischen Links;
- deklarative Trainerdaten statt frei ausführbarer Trainerdefinitionen;
- getrennte Updatekanäle für Anwendung und Lerninhalte;
- sichtbare Quellen-, Lizenz- und Verantwortlichkeitsübersicht.

## Herunterladen und ausprobieren

### Desktop-App

Die Pakete für `0.7.1` werden automatisiert aus dem zugehörigen Versionstag
gebaut und im offiziellen GitHub Release veröffentlicht:

| Betriebssystem | Architektur | Download |
|---|---|---|
| Windows | x86_64 | **[ZIP direkt herunterladen](https://github.com/finalnode/insi/releases/download/v0.7.1/insi-0.7.1-windows-x86_64.zip)** |
| Linux | x86_64 | **[TAR.GZ direkt herunterladen](https://github.com/finalnode/insi/releases/download/v0.7.1/insi-0.7.1-linux-x86_64.tar.gz)** |
| macOS | Apple Silicon (`arm64`) | **[DMG direkt herunterladen](https://github.com/finalnode/insi/releases/download/v0.7.1/insi-0.7.1-macos-arm64.dmg)** |
| macOS | Intel (`x86_64`) | **[DMG direkt herunterladen](https://github.com/finalnode/insi/releases/download/v0.7.1/insi-0.7.1-macos-x86_64.dmg)** |

Jede Änderung auf `main` wird durch
[GitHub Actions](https://github.com/finalnode/insi/actions/workflows/build-desktop.yml)
auf allen vier Zielsystemen getestet und gebaut. Dauerhaft veröffentlichte,
direkt herunterladbare Pakete stehen unter
[GitHub Releases](https://github.com/finalnode/insi/releases); sie entstehen aus
einem Versionstag wie `v0.7.1`.

### PyKIM-Beispielkurs

1. in:si starten.
2. Die **[Setupdatei des PyKIM-Standardkurses](https://raw.githubusercontent.com/finalnode/insi/main/examples/course-setups/pykim-standardkurs.insi-setup)** herunterladen.
3. Die Datei in der Kursauswahl importieren.
4. Einen lokalen Arbeitsordner wählen und den Runtime-Check abschließen.

Weiterführende Quellen:

- [Kursinhalte und Trainer](https://github.com/finalnode/PyKIM_Kurs)
- [PyKIM-Pythonmodul](https://github.com/finalnode/PyKIM)

## So funktionieren Kurse

in:si trennt Plattform, Fachmodul, veröffentlichte Kursquelle und persönliche
Arbeit:

```text
in:si
├── Kursverwaltung, Lernstand und Autorenwerkzeuge
├── Fachmodule
│   └── PyKIM (heute verfügbar)
├── Kursquelle aus GitHub oder portablem ZIP
└── Student Workspace mit Lösungen, Projekten und Erweiterungen
```

### Kursquelle und Student Workspace

| Bereich | Enthält | Verhalten bei Kursupdates |
|---|---|---|
| Kursquelle | Skripte, Aufgaben, Beispiele und `Trainer/*.yml` | darf durch einen neuen geprüften Kursstand ersetzt werden |
| Student Workspace | Lösungen, Lernstand, Antworten, Projekte und persönliche Erweiterungen | wird nicht durch Kursupdates überschrieben |

### Setupdatei, ZIP und Katalog

Eine `.insi-setup`-Datei enthält Metadaten und die öffentliche GitHub-Quelle,
aber keine Schülerlösung und keine eingebetteten Kursdateien:

```json
{
  "format": "insi-course-setup-v1",
  "name": "pykim-standardkurs.insi-setup",
  "teacher": "PyKIM-Team",
  "school": "OSZ KIM",
  "course": "PyKIM Standardkurs",
  "repository": "https://github.com/finalnode/PyKIM_Kurs.git",
  "branch": "main",
  "scripts_path": "Skripte",
  "assignments_path": "Aufgaben",
  "trainers_path": "Trainer"
}
```

Ein portables ZIP enthält dieselben Kursmetadaten, den Kursinhalt und den
Runtime-Vertrag. Es eignet sich für lokale Kurse, Schulnetze ohne GitHub-Zugriff
und die Weitergabe über exFAT-formatierte USB-Sticks. Der Kurskatalog ist ein
komfortabler Einstieg für bekannte freie GitHub-Kurse; seine mitgelieferte Kopie
funktioniert auch offline.

### Runtime-Vertrag und ZIP-Größe

Jeder neu exportierte Kurs enthält `runtime.toml` mit der vom Kursersteller
gewählten Python-Version und der vollständigen Liste exakt gepinnter
Kurspakete. Ein Kurs kann beispielsweise PyKIM, eine andere Trainingsengine
oder gar kein Fachpaket verlangen. Alte Archive ohne Manifest bleiben über
einen ausdrücklich begrenzten 0.7-Kompatibilitätsfallback importierbar.

Der Standardexport enthält **keine Paket-Wheels** und bleibt klein. Kurspakete
werden als `paket==version` eingetragen. Nur wenn der Offline-Paketexport
aktiviert und mindestens ein Ziel gewählt wird, lädt in:si die vollständige
Wheel-Abhängigkeitskette für:

- Windows x86_64;
- Linux x86_64;
- macOS Apple Silicon;
- macOS Intel.

Jede zusätzliche Plattform kann das ZIP deutlich vergrößern. Python-Version
und vollständige, exakt gepinnte Kurspaketliste werden vom Kursersteller im
Runtime-Vertrag festgelegt; in:si ergänzt oder ersetzt darin keine
Fachmodulversionen. Beim Offline-Export wird die vollständige Wheel-Kette dieses
Kursvertrags eingebettet. Manifest und Wheels werden versioniert im Kurs
abgelegt und mit SHA-256-Prüfsummen abgesichert.

Vor jedem Kursstart und nach Inhaltsupdates prüft der Preflight:

1. Betriebssystem und Architektur;
2. die geforderte Python-Version;
3. alle exakten Paketversionen;
4. die Integrität eingebetteter Wheels.

Ein harter Fehler blockiert den Kursstart. in:si zeigt Soll- und Ist-Zustand und
bietet, soweit möglich, Reparatur oder Einrichtung einer getrennten
Kursumgebung an. Schülerarbeit wird dabei nicht verändert.

## Kursinhalte erstellen

### M@rkdown

M@rkdown ist normales Markdown mit einfachen Annotationen:

```markdown
# Eine Linie zeichnen

Zeichne eine rote Linie von `(20, 20)` bis `(30, 20)`.

@hint: Beginne mit set_position.
@hint: Eine Schleife vermeidet Wiederholungen.
@tags: schleifen, koordinaten, farben
@source: https://example.org/aufgabe
```

Der Parser meldet Fehler mit Zeilennummern. Die Kursvorschau verwendet dieselbe
Darstellung wie die spätere Lernansicht. Aus Markdown-Metadaten wird kein frei
ausführbarer Pythoncode erzeugt. Im Kurseditor ruft ein eigenes TOAST-Plugin
diesen Validator nach Änderungen automatisch auf. Sein Toolbar-Menü fügt nur
für den jeweiligen Dokumenttyp angebotene Annotationen ein; die Fehleranzeige
wechselt beim Anklicken zur betroffenen Markdownzeile. In
Projektdokumentationen der Lernenden ist das Kursplugin nicht aktiv.

### Deklarative Trainer

Trainer bleiben getrennte YAML-Dateien und beschreiben erwartete Ergebnisse:

```yaml
format: insi-trainer-v1
engine: pykim
exercises:
  - id: rote-linie
    title: Rote Linie
    tests:
      - type: pixels
        paths:
          - {start: [20, 20], end: [30, 20], color: red}
        success: Die rote Linie ist vollständig.
        failure: Die Linie fehlt oder liegt noch nicht richtig.
        hint: Beginne bei (20, 20) und bewege KIM zehn Schritte nach rechts.
```

Der Prüfablauf bleibt gerichtet:

```text
Kursquelle mit Trainer/*.yml
        ↓
in:si aktiviert den Kurs in insi.training
        ↓
Schülerprogramm oder Projekt übergibt die fachliche Abgabe
        ↓
die gewählte Fachmodul-Engine bewertet die Abgabe
        ↓
in:si zeigt das neutrale Feedback und speichert den Versuch
```

`engine` trennt die Plattform vom Fachmodul. `pykim` prüft Pythoncode und die
Pixelwelt; `core` deckt freie Antworten, Zuordnungen und Parsons-Puzzles ohne
Fachmodul ab. Weitere Engines registrieren sich über
`insi.trainer_backends`, können andere Abgabearten und Starterdateien liefern
und verwenden denselben Lernstand. Die Engine erhält dafür eine neutrale
`Submission`: je nach Fach also Quelltext, einen Einstiegspunkt oder ein
komplettes, von der Sandbox begrenztes Projektverzeichnis. Bestehende
PyKIM-Trainer im numerischen Format 1 bleiben importierbar.

## Sicherheit, Offlinebetrieb und Datenschutz

Kurse und Schülerprogramme sind potenziell fremder Code. Ab `0.7.0` startet
in:si solchen Code integriert nur noch, wenn ein geprüfter OS-Sandbox-Adapter
die Richtlinie tatsächlich durchsetzen kann. Es gibt keinen stillen
Kompatibilitätsfallback. Ohne Adapter bleiben Bearbeiten, Speichern und
**In IDE öffnen** verfügbar; der Start in der IDE geschieht bewusst mit den
normalen Rechten des Benutzerkontos.

Unter Windows verwendet der strenge Adapter einen eigenen Broker, einen
AppContainer ohne Netzwerkfähigkeit und ein Job Object für den vollständigen
Prozessbaum. Unter Linux verwendet er
[Bubblewrap](https://github.com/containers/bubblewrap); grafische integrierte
Starts benötigen dort zusätzlich eine Wayland-Sitzung. Unter macOS erzeugt der
native Runner pro Start ein minimales Seatbelt-Profil für die ausgewählten
Lese- und Schreibbereiche; Netzwerk und Zugriffe auf andere Dateien bleiben
gesperrt. Alle drei Adapter führen vor ihrer Freigabe einen echten
Isolationstest aus. Schlägt er fehl, bleibt der integrierte Start gesperrt und
in:si verweist auf die externe IDE.
Mit dem Release ausgelieferte, geprüfte Galeriebeispiele bilden eine getrennte
Vertrauensklasse.

Ein Sandboxlauf erhält:

- nur die gestartete Datei beziehungsweise das aktuelle Projekt;
- die benötigte Python-Laufzeit und aktive Kursinhalte nur lesbar;
- globale und kursweite Workspace-Dateien nur lesbar;
- einen privaten Aufgaben-Laufbereich oder ausschließlich das aktuelle Projekt
  als Schreibbereich;
- ein temporäres Home-Verzeichnis und keinen Host-`PYTHONPATH`, D-Bus, Agenten,
  Proxys oder typische Zugangsdaten;
- keinen Netzwerkzugriff;
- feste Grenzen für Laufzeit, CPU-Zeit, RAM, Prozessanzahl, Ausgabe und neu
  geschriebene Daten.

Bei einer Grenzverletzung beendet in:si die gesamte Prozessgruppe und zeigt den
Grund. Vor einem Projektstart wird außerhalb der Sandbox ein begrenzter
Projektstand gesichert. Das reduziert den Schadensradius, ist aber keine
Behauptung absoluter Sicherheit gegen Kernel-, Grafiktreiber- oder bisher
unbekannte Sandboxlücken. Das vollständige Bedrohungsmodell und der Meldeweg
stehen in [SECURITY.md](SECURITY.md).

Nach der vollständigen Einrichtung funktionieren Lerntexte, Aufgaben, Trainer,
Lernstand und Projekte lokal. Netzwerkzugriffe entstehen insbesondere bei:

- der ersten Installation eines Onlinekurses;
- ausdrücklich ausgelösten Katalog-, Kurs-, Inhalts- oder App-Updates;
- dem Aufbau einer Runtime mit nicht eingebetteten Zusatzpaketen.

App-, Kurs- und Inhaltsupdates werden nicht im Hintergrund geprüft, sondern
erst nach einem bewussten Import oder Klick. Die vollständige Übersicht aller
lokalen Daten, Exporte, Netzwerkziele und Löschwege steht in
[Datenschutz und Datenbestand](DATENSCHUTZ.md).

in:si verwendet aus Kompatibilitätsgründen weiterhin den lokalen Basisordner
`PyKIM-Kurse`. Der aktive Kursordner ist in der App sichtbar und lässt sich
direkt öffnen. Es gibt derzeit weder zentrale Benutzerkonten noch Telemetrie in
der Anwendung. Lokale Mehrbenutzerprofile und eine eigene Berechtigungsübersicht
sind noch Teil der Roadmap.

## Entwicklung und Architektur

### Entwicklungsinstallation

Voraussetzungen: Python 3.11 oder neuer und Git.

```bash
git clone https://github.com/finalnode/insi.git

cd insi
python -m venv venv
source venv/bin/activate
python -m pip install --requirement requirements/pykim-0.6.0.txt
python -m pip install -e '.[test]'
python -m pytest
insi
```

Unter Windows wird die Umgebung mit `venv\Scripts\activate` aktiviert. Der
sichtbare Ordnername `venv` vermeidet auf macOS mit Python 3.14, dass
Finder-vererbte Hidden-Flags die `.pth`-Datei einer editierbaren Installation
deaktivieren.
Die Versionsdatei bindet PyKIM 0.6.0 sowie die zugehörige Standard-Runtime an
den gleichen geprüften Stand, den CI und Desktop-Builds verwenden.

### Architekturgrenzen

`insi.app` ist ein kleiner Application Composer. Zustände und Dienste gelangen
über einen expliziten `AppContext` in getrennte Views. Die generische
Trainingsschicht `insi.training` verwaltet aktiven Kurs, Aktivitäten, Feedback
und Versuche. Fachmodule liefern nur ihre fachspezifischen Prüfbausteine.

| Bestandteil | Verantwortlich |
|---|---|
| konkrete Aufgaben, Hinweise und `Trainer/*.yml` | Kursquelle |
| Kursverwaltung, Registry, Feedback, Versuche und Lernstand | in:si |
| Abgabeart, Starterdateien und Auswertung der neutralen `Submission` | registrierte Trainer-Engine |
| Pixelwelt und PyKIM-spezifische Prüfregeln | PyKIM-Fachmodul |
| Schülercode und eigene Projekte | Student Workspace |
| Datei- und Prozessfähigkeiten eines integrierten Laufs | `insi.sandbox` |
| globale, kursweite und projektbezogene Dateiimporte | `insi.workspace_files` |

PyKIM bindet den in:si-Provider als normalen Python-Entry-Point ein:

```toml
[project.entry-points."pykim.trainer_provider"]
insi = "insi.training.provider:provider"
```

Weitere Fachmodule binden ihre Trainer-Engine getrennt an:

```toml
[project.entry-points."insi.trainer_backends"]
mein_modul = "mein_modul.training:backend"
```

Wichtige Grenzen:

- in:si darf Fachmodule wie PyKIM verwenden;
- PyKIM darf in:si nicht importieren;
- Kurse werden über Dateisystem- und Metadatenverträge angebunden;
- Student Workspaces gehören weder zum App- noch zum Kursrepository;
- die in:si-Oberfläche verwaltet Dateien und Backups als vertrauenswürdiger
  Broker; der separate Runner erhält nur ein explizites Fähigkeitsprofil;
- externe IDEs sind ein bewusster, sichtbar unbeschränkter Ausführungsweg und
  erben keine Sicherheitszusage des integrierten Runners;
- Fachmodule sollen unabhängig versioniert und austauschbar bleiben.

### Desktop-Apps bauen

Der Workflow [`.github/workflows/build-desktop.yml`](.github/workflows/build-desktop.yml)
testet das Projekt und baut vier Pakete:

| Ziel | GitHub-Runner | Releaseformat |
|---|---|---|
| Windows x86_64 | `windows-2025` | `.zip` |
| Linux x86_64 | `ubuntu-24.04` | `.tar.gz` |
| macOS Intel | `macos-15-intel` | `.dmg` |
| macOS Apple Silicon | `macos-15` | `.dmg` |

Lokale Buildbefehle:

```bash
# Windows oder Linux
python tools/build_desktop_app.py
python tools/package_desktop_app.py

# macOS
python tools/build_macos_dmg.py --rebuild-app
```

Für integrierte Fremdcode-Starts muss auf einem Linux-Ziel zusätzlich
Bubblewrap als Systemkomponente vorhanden sein, beispielsweise unter
Debian/Ubuntu mit `sudo apt install bubblewrap`. Der Systemcheck führt vor der
Freigabe einen echten Datei-, Netzwerk-, Prozess- und Namespace-Probelauf aus;
die bloße Existenz der Datei `bwrap` reicht nicht. Der Linux-Desktop-Build prüft
zusätzlich CPU-, RAM-, Prozess- und Schreibgrenzen sowie mit einem isolierten
Weston ein echtes Pyxel-Fenster über Wayland. Unter Windows gehören AppContainer
und Job Objects zum
Betriebssystem; in:si prüft auch dort Datei- und Netzwerkisolation mit einem
echten Probelauf. Unter macOS verwendet in:si das vorhandene Systemprogramm
`/usr/bin/sandbox-exec` mit einem pro Lauf erzeugten Seatbelt-Profil. Da Apple
diese Profilschnittstelle nicht als stabile öffentliche API dokumentiert,
entscheidet auch dort ausschließlich ein echter Datei-, Netzwerk- und
Prozessprobelauf über die Freigabe; bei Änderung oder Wegfall bleibt der Start
fail-closed gesperrt.

Ergebnisse liegen unter `dist/releases/`. Unter Windows sind im nativen Modus
zwei `insi.exe`-Prozesse normal: lokaler Server und WebView laufen getrennt. Ein
Versionstag wie `v0.7.1` veröffentlicht erfolgreiche CI-Builds als GitHub
Release.

## Roadmap

Die Meilensteine und Freigabekriterien von 0.7 bis 1.3 stehen in der
[Roadmap bis in:si 1.3](ROADMAP.md). Sie trennt die noch offenen Arbeiten an
Zuverlässigkeit, Wartbarkeit und Performance in 0.8 vom
Schuleinsatz in 0.9, dem stabilen Produktvertrag für 1.0 und den darauf
aufbauenden Kurs-, Projekt- und Zusammenarbeitsfunktionen.

## Name, Quellen und Lizenz

**in:si** steht für **informatica simplicissima**:

> So viel vereinfachen wie nötig, so wenig abstrahieren wie möglich.

Die Plattform senkt Einstiegshürden, ohne Lernende in einem proprietären
Endsystem festzuhalten. Kurse verwenden echte Sprachen, Dateien und Werkzeuge;
die Hilfsstruktur kann mit wachsender Erfahrung zurücktreten.

Der App-Footer bündelt Softwarequellen, Kursrepository, Verantwortung, Lizenzen
und aufgabenspezifische Quellen. in:si steht ab Version 0.7 unter der
[GNU Affero General Public License, Version 3 oder später](LICENSE)
(`AGPL-3.0-or-later`). Kommerzielle Nutzung bleibt erlaubt. Wer eine veränderte
Fassung weitergibt, muss den zugehörigen Quellcode unter denselben Bedingungen
bereitstellen; wer eine veränderte Fassung über ein Netzwerk anbietet, muss den
Nutzenden ebenfalls Zugang zum zugehörigen Quellcode ermöglichen.

Die genaue Abgrenzung zu früheren MIT-Versionen, PyKIM, externen Kursen und
gebündelten Bibliotheken erläutert [LICENSING.md](LICENSING.md).
Drittanbieter-Komponenten und Kursinhalte mit eigener Lizenz werden separat
ausgewiesen. Der lokal gebündelte TOAST UI Editor steht unter MIT; DOMPurify
kann unter Apache 2.0 beziehungsweise MPL 2.0 genutzt werden. Copyrights,
Original-Lizenztexte, Bezugsquelle und Prüfsumme stehen in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

> **Concept by human. Crafted by human + AI.**
> Konzept und pädagogische Verantwortung: Projektverantwortliche von in:si
> KI-Unterstützung: OpenAI Codex
