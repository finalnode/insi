# <img src="packaging/macos/assets/app-icon-master.png" alt="in:si-Logo" width="72" align="center"> in:si

**in:si 0.6.0** ist eine lokale Desktop-Lernumgebung für modulare
Informatikkurse. Sie bringt Kursinstallation, Lerntexte, interaktive Aufgaben,
automatische Tests, Lernstand, Projekte und Autorenwerkzeuge in eine gemeinsame
Anwendung, die nach der Einrichtung weitgehend offline funktioniert.

Der aktuell verfügbare Beispielkurs vermittelt Python mit dem unabhängigen
Fachmodul [PyKIM](https://github.com/finalnode/PyKIM). Die Plattform ist für
weitere Fachmodule und Mischkurse vorbereitet, diese sind aber noch nicht
fertig implementiert.

> **Projektstatus: Alpha.** Lokale Datenformate und Oberflächen können sich noch
> ändern. Desktop-Builds sind derzeit weder signiert noch notarisiert.

## In 30 Sekunden

| Frage | Antwort |
|---|---|
| Für wen? | Lernende, Lehrkräfte und Autorinnen und Autoren lokaler Informatikkurse |
| Was läuft heute? | Python-/PyKIM-Kurse auf Windows, Linux und macOS |
| Wo liegen Daten? | Lokal im Kursordner beziehungsweise in lokalen App-Verzeichnissen |
| Funktioniert es offline? | Ja, nach der Einrichtung; Zusatzpakete können optional ins Kurs-ZIP eingebettet werden |
| Wie kommen Kurse hinein? | `.insi-setup`, portables ZIP oder öffentlicher GitHub-Kurskatalog |
| Was bleibt bei Updates erhalten? | Lösungen, Projekte, Antworten und Lernstand im Student Workspace |
| Ist Schülercode sicher sandboxed? | Nein. Prozesse werden begrenzt und getrennt, aber es gibt noch keine garantierte OS-Sandbox |

Schnellnavigation:

- [Was in:si ist – und was nicht](#was-insi-ist--und-was-nicht)
- [Alle implementierten Funktionen](#alle-implementierten-funktionen)
- [Herunterladen und ausprobieren](#herunterladen-und-ausprobieren)
- [So funktionieren Kurse](#so-funktionieren-kurse)
- [Sicherheit, Offlinebetrieb und Datenschutz](#sicherheit-offlinebetrieb-und-datenschutz)
- [Entwicklung und Architektur](#entwicklung-und-architektur)
- [Roadmap](#roadmap-noch-nicht-implementiert)

## Was in:si ist – und was nicht

| in:si ist … | in:si ist nicht … |
|---|---|
| eine lokale Lern- und Autorenanwendung | ein Cloud-LMS oder eine gehostete Schulplattform |
| eine Hülle für echte Sprachen, Dateien und Werkzeuge | eine proprietäre vereinfachte Programmiersprache |
| eine Plattform für versionierte Kursquellen und getrennte Schülerarbeit | ein Ersatz für GitHub, Moodle oder die Schulverwaltung |
| derzeit praktisch auf Python und PyKIM fokussiert | bereits eine fertige Universalumgebung für alle Informatikthemen |
| offline-first und ohne Konto nutzbar | vollständig ohne Netzwerk installierbar, sofern ein Kurs nicht alle Zusatzpakete einbettet |
| gegen typische Archiv- und Prozessfehler gehärtet | eine garantierte Sicherheitsgrenze gegen bösartigen Pythoncode |
| ein Alpha-Projekt mit funktionierenden Desktop-Builds | bereits eine signierte, notarisierte oder langfristig formatstabile Produktionsversion |

**in:si und PyKIM sind getrennte Projekte.** in:si verwaltet Kurse, Lernstand,
Workspaces und Autorenabläufe. PyKIM liefert die Pixelwelt, die Python-API und
fachspezifische Prüfregeln. PyKIM kann ohne in:si verwendet werden und importiert
in:si nicht.

## Alle implementierten Funktionen

Die folgenden Punkte sind vorhanden und durch automatisierte Tests abgedeckt.
Noch offene Arbeiten stehen ausschließlich in der [Roadmap](#roadmap-noch-nicht-implementiert).

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
- persönliche Erweiterungen kursübergreifend verwenden;
- Thonny und VS Code mit dem ausgewählten Kursinterpreter starten;
- Pyxel-Ressourcen und offizielle Beispiele verwenden.

### Kurse installieren und verwalten

- neue `.insi-setup`-Dateien importieren;
- historische `.pykim-setup`-Dateien importieren und mit Backup migrieren;
- sichere portable Kurs-ZIPs importieren;
- öffentliche GitHub-Kursrepositories synchronisieren;
- freie Kurse aus einem lokal zwischengespeicherten Katalog installieren;
- Herkunfts- und Vertrauenswarnungen vor externen Importen anzeigen;
- Namenskonflikte als Kopie oder kontrolliertes Update behandeln;
- veröffentlichte Kursinhalte getrennt vom Student Workspace aktualisieren;
- Dateien und Ordner mit führendem Unterstrich aus Kursen ausblenden;
- Kursordner in den Systempapierkorb verschieben, ohne andere Verzeichnisse zu
  löschen.

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
- Skripte und Aufgaben in annotiertem Markdown (**M@rkdown**) bearbeiten;
- Hinweise, Tags, Quellen, Lizenz und Verantwortung hinterlegen;
- automatische Trainer deklarativ als YAML erzeugen und validieren;
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
- Laufzeit- und Ausgabegrenzen für integrierte Ausführungen;
- bereinigte Umgebungsvariablen beim Start von Schülercode;
- validierte Repository-, Archiv- und Inhaltspfade;
- Schutz vor ZIP-Pfadwechseln, absoluten Pfaden und symbolischen Links;
- deklarative Trainerdaten statt frei ausführbarer Trainerdefinitionen;
- getrennte Updatekanäle für Anwendung und Lerninhalte;
- sichtbare Quellen-, Lizenz- und Verantwortlichkeitsübersicht.

## Herunterladen und ausprobieren

### Desktop-App

| Betriebssystem | Architektur | Download |
|---|---|---|
| Windows | x86_64 | **[Windows-App herunterladen](https://github.com/finalnode/insi/releases/tag/v0.6.0)** |
| Linux | x86_64 | **[Linux-App herunterladen](https://github.com/finalnode/insi/releases/tag/v0.6.0)** |
| macOS | Apple Silicon (`arm64`) | **[macOS-App für Apple Silicon herunterladen](https://github.com/finalnode/insi/releases/tag/v0.6.0)** |
| macOS | Intel (`x86_64`) | **[macOS-App für Intel herunterladen](https://github.com/finalnode/insi/releases/tag/v0.6.0)** |

Die Pakete werden durch GitHub Actions auf dem jeweiligen Zielsystem gebaut und
unter [GitHub Releases](https://github.com/finalnode/insi/releases)
bereitgestellt.

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

Jeder neu exportierte Kurs enthält `runtime.toml` mit Python 3.11, den genauen
PyKIM-/Pyxel-Versionen und optionalen Zusatzpaketen. Alte Archive ohne Manifest
bleiben importierbar.

Der Standardexport enthält **keine Paket-Wheels** und bleibt klein. Zusatzpakete
werden als `paket==version` eingetragen. Nur wenn die standardmäßig deaktivierte
Option **Zusätzliche Pakete … einbetten** aktiviert und mindestens ein Ziel
gewählt wird, lädt in:si die vollständige Wheel-Abhängigkeitskette für:

- Windows x86_64;
- Linux x86_64;
- macOS Apple Silicon;
- macOS Intel.

Jede zusätzliche Plattform kann das ZIP deutlich vergrößern. PyKIM und Pyxel
stellt die jeweilige in:si-Installation bereit und dupliziert sie deshalb nicht
im Kurs. Manifest und Wheels werden versioniert im Kurs abgelegt und mit
SHA-256-Prüfsummen abgesichert.

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
ausführbarer Pythoncode erzeugt.

### Deklarative Trainer

Trainer bleiben getrennte YAML-Dateien und beschreiben erwartete Ergebnisse:

```yaml
format: 1
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
Schülerprogramm ruft run(check="rote-linie") auf
        ↓
PyKIM fragt über seine neutrale Provider-Schnittstelle in:si
        ↓
PyKIM bewertet die Welt; in:si zeigt Feedback und speichert den Versuch
```

## Sicherheit, Offlinebetrieb und Datenschutz

Kurse und Schülerprogramme sind potenziell fremder Code. Importiere nur Kurse
aus Quellen, denen du vertraust. in:si validiert Datenstrukturen und begrenzt
integrierte Prozesse, behauptet aber ausdrücklich **keine vollständige
Sandbox**. Gestarteter Pythoncode kann mit den Rechten des angemeldeten Kontos
auf Dateien, Netzwerk und Betriebssystemfunktionen zugreifen. Details und
Meldeweg stehen in [SECURITY.md](SECURITY.md).

Nach der vollständigen Einrichtung funktionieren Lerntexte, Aufgaben, Trainer,
Lernstand und Projekte lokal. Netzwerkzugriffe entstehen insbesondere bei:

- der ersten Installation eines Onlinekurses;
- ausdrücklich ausgelösten Kurs-, Katalog- oder App-Updates;
- dem Aufbau einer Runtime mit nicht eingebetteten Zusatzpaketen.

in:si verwendet aus Kompatibilitätsgründen weiterhin den lokalen Basisordner
`PyKIM-Kurse`. Der aktive Kursordner ist in der App sichtbar und lässt sich
direkt öffnen. Es gibt derzeit weder zentrale Benutzerkonten noch Telemetrie in
der Anwendung. Lokale Mehrbenutzerprofile und eine eigene Berechtigungsübersicht
sind noch Teil der Roadmap.

## Entwicklung und Architektur

### Entwicklungsinstallation

Voraussetzungen: Python 3.10 oder neuer und Git.

```bash
git clone https://github.com/finalnode/PyKIM.git
git clone https://github.com/finalnode/insi.git

cd insi
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ../PyKIM
python -m pip install -e '.[test]'
python -m pytest
insi
```

Unter Windows wird die Umgebung mit `.venv\Scripts\activate` aktiviert.

### Architekturgrenzen

`insi.app` ist ein kleiner Application Composer. Zustände und Dienste gelangen
über einen expliziten `AppContext` in getrennte Views. Die generische
Trainingsschicht `insi.training` verwaltet aktiven Kurs, Aktivitäten, Feedback
und Versuche. Fachmodule liefern nur ihre fachspezifischen Prüfbausteine.

| Bestandteil | Verantwortlich |
|---|---|
| konkrete Aufgaben, Hinweise und `Trainer/*.yml` | Kursquelle |
| Kursverwaltung, Registry, Feedback, Versuche und Lernstand | in:si |
| Pixelwelt und PyKIM-spezifische Prüfregeln | PyKIM-Fachmodul |
| Schülercode und eigene Projekte | Student Workspace |

PyKIM bindet den in:si-Provider als normalen Python-Entry-Point ein:

```toml
[project.entry-points."pykim.trainer_provider"]
insi = "insi.training.provider:provider"
```

Wichtige Grenzen:

- in:si darf Fachmodule wie PyKIM verwenden;
- PyKIM darf in:si nicht importieren;
- Kurse werden über Dateisystem- und Metadatenverträge angebunden;
- Student Workspaces gehören weder zum App- noch zum Kursrepository;
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

Ergebnisse liegen unter `dist/releases/`. Unter Windows sind im nativen Modus
zwei `insi.exe`-Prozesse normal: lokaler Server und WebView laufen getrennt. Ein
Versionstag wie `v0.6.0` veröffentlicht erfolgreiche CI-Builds als GitHub
Release.

## Roadmap (noch nicht implementiert)

Die nächsten technischen Etappen sind:

1. automatischer Neuaufbau und versionsübergreifende Migration verwalteter
   Kursumgebungen, wenn sich der Runtime-Vertrag ändert;
2. lokale Mehrbenutzerprofile mit getrennten Workspaces;
3. robuste USB- und Absturzwiederherstellung;
4. signierte Kursveröffentlichungen, Herausgebervertrauen und ein sichtbares
   Berechtigungsmodell;
5. versionierte Daten- und Kursmigrationen;
6. eine eigene Datenschutz- und Datenbestandsübersicht;
7. validierte PyKIM-Sprachpakete mit kanonischen Lernbefehlen und lokalen
   API-Aliasen;
8. weitere Fachmodule und konfigurierbare Menüs für Mischkurse.

Spätere Ausbaustufen umfassen Peer Review, Kompetenzmodelle und Zusammenarbeit.
Außerdem geplant sind ein Kursbaukasten aus wiederverwendbaren, versionierten
Inhaltsbibliotheken sowie ein verständlicher, optionaler Git-Arbeitsablauf im
Kursstudio. ZIP-Export und rein lokale Kurse bleiben gleichwertige Wege.

Eine spätere Migration der internen `.pykim`-Datenpfade ist ausdrücklich von
der bereits abgeschlossenen Umbenennung sichtbarer Setupdateien getrennt.
Fortschritt, Projekte, Sicherungen und installierte Kurse dürfen dabei nicht
verloren gehen oder überschrieben werden.

## Name, Quellen und Lizenz

**in:si** steht für **informatica simplicissima**:

> So viel vereinfachen wie nötig, so wenig abstrahieren wie möglich.

Die Plattform senkt Einstiegshürden, ohne Lernende in einem proprietären
Endsystem festzuhalten. Kurse verwenden echte Sprachen, Dateien und Werkzeuge;
die Hilfsstruktur kann mit wachsender Erfahrung zurücktreten.

Der App-Footer bündelt Softwarequellen, Kursrepository, Verantwortung, Lizenzen
und aufgabenspezifische Quellen. in:si steht unter der [MIT-Lizenz](LICENSE).
Drittanbieter-Komponenten und Kursinhalte können eigene Lizenzen besitzen und
werden separat ausgewiesen.
