# <img src="packaging/macos/assets/app-icon-master.png" alt="in:si-Logo" width="72" align="center"> in:si

**in:si 0.6.0** ist eine lokale Desktop-Lernumgebung für modulare
Informatikkurse. Sie verbindet Kursverwaltung, Lerntexte, interaktive Aufgaben,
automatische Trainer, Lernstand, Projekte und Autorenwerkzeuge in einer
gemeinsamen, offline nutzbaren Anwendung.

in:si ist nicht auf eine Programmiersprache festgelegt. Ein Kurs entscheidet,
welche Inhalte, Werkzeuge und Fachmodule benötigt werden. Der derzeitige
Beispielkurs verwendet [PyKIM](https://github.com/finalnode/PyKIM) für einen
visuellen Einstieg in Python; weitere Kursarten und Kombinationen werden als
unabhängige Module ergänzt.

> **Projektstatus: Alpha.** Kurs- und Schülerdaten werden lokal gespeichert.
> Desktop-Builds sind derzeit weder signiert noch notarisiert.

## in:si herunterladen

| Betriebssystem | Architektur | Download |
|---|---|---|
| Windows | x86_64 | **[Windows-App herunterladen](https://github.com/finalnode/insi/releases/tag/v0.6.0)** |
| macOS | Apple Silicon (`arm64`) | **[macOS-App für Apple Silicon herunterladen](https://github.com/finalnode/insi/releases/tag/v0.6.0)** |
| macOS | Intel (`x86_64`) | **[macOS-App für Intel herunterladen](https://github.com/finalnode/insi/releases/tag/v0.6.0)** |
| Linux | x86_64 | **[Linux-App herunterladen](https://github.com/finalnode/insi/releases/tag/v0.6.0)** |

Die Apps werden durch GitHub Actions auf dem jeweiligen Zielsystem gebaut und
unter [GitHub Releases](https://github.com/finalnode/insi/releases)
bereitgestellt.

### Beispielkurs

- **[Setupdatei des PyKIM-Standardkurses](https://raw.githubusercontent.com/finalnode/insi/main/examples/course-setups/pykim-standardkurs.pykim-setup)**
- **[Kursinhalte und Trainer ansehen](https://github.com/finalnode/PyKIM_Kurs)**
- **[PyKIM-Pythonmodul ansehen](https://github.com/finalnode/PyKIM)**

Die Setupdatei wird nach dem App-Start in der Kursauswahl hochgeladen. in:si
lädt anschließend die öffentlichen Kursinhalte und richtet einen lokalen
Arbeitsbereich ein.

## Was in:si leistet

### Für Lernende

- mehrere installierte Kurse auswählen und im laufenden Betrieb wechseln;
- Lerntexte mit dynamischem Inhaltsverzeichnis lesen;
- Codebeispiele kopieren, starten und stoppen;
- Aufgaben im integrierten Editor oder in einer erkannten externen IDE lösen;
- Antwort-, Zuordnungs- und Code-Sortieraufgaben bearbeiten;
- gestufte Hinweise öffnen und verwendete Hinweise nachvollziehen;
- automatische Tests mit verständlichem Feedback ausführen;
- eigene Projekte und persönliche Erweiterungen kursübergreifend verwenden;
- Lernstand lokal und getrennt von den unveränderlichen Kursquellen speichern;
- Projektordner direkt im Dateimanager öffnen.

### Für Lehrkräfte und Kursautorinnen und -autoren

- Kurse vollständig in der Suite anlegen und in einer realistischen Vorschau
  prüfen;
- vorhandene Ordner analysieren und Dateien nachträglich Skripten, Aufgaben
  oder Trainern zuordnen;
- Lerntexte und Aufgaben in annotiertem Markdown (**M@rkdown**) schreiben;
- Hinweise, Tags, Quellen, Lizenz und verantwortliche Stelle hinterlegen;
- automatische Trainer deklarativ als YAML erstellen und validieren;
- Kurse als portables ZIP-Archiv exportieren oder über ein Git-Repository
  veröffentlichen;
- Setupdateien für eine einfache Installation verteilen.

### Kursverwaltung

- Import über `.pykim-setup` und sichere ZIP-Archive;
- öffentliche Git-Repositories unabhängig vom Git-Host als Kursquelle;
- lokaler Kurskatalog mit optionaler Aktualisierung;
- sichtbare Herkunfts- und Vertrauenswarnung vor dem Import;
- Konfliktdialog, wenn ein Import einen vorhandenen Kurs ersetzen würde;
- Inhaltsupdates mit getrenntem Student Workspace;
- ignorierte Dateien und Ordner über führenden Unterstrich, beispielsweise
  `_backup/` oder `_entwurf.md`.

Das Suffix `.pykim-setup` bleibt aus Kompatibilitätsgründen bestehen. Es
bezeichnet das bestehende Kursinstallationsformat und bindet in:si nicht an das
PyKIM-Modul.

## Fachmodule und Mischkurse

in:si trennt Plattform, Fachlaufzeit und Kursinhalt:

```text
in:si
├── Kursverwaltung, Lernstand und Autorenwerkzeuge
├── Fachmodule und lokale Werkzeuge
│   └── PyKIM (heute verfügbar)
├── Kursrepositories oder portable Kursarchive
└── Student Workspace mit eigenen Projekten und Erweiterungen
```

[PyKIM](https://github.com/finalnode/PyKIM) ist das erste angebundene
Fachmodul. Seine Pixelwelt, Python-API und Trainerlogik werden unabhängig von
in:si versioniert. Die vollständige PyKIM-Dokumentation steht deshalb bewusst
nicht in dieser README, sondern im
[PyKIM-Repository](https://github.com/finalnode/PyKIM#readme).

Geplant sind eigenständige Kurs- und Werkzeugprofile für reines Python,
Markdown, HTML/CSS, SQLite und weitere Informatikthemen. Mischkurse sollen
mehrere Profile kombinieren können, beispielsweise Python mit SQLite oder
PyKIM mit einer selbst erstellten Datenbank. Das Menü zeigt dann nur die vom
Kurs benötigten Bereiche.

Persönliche Erweiterungen sollen nicht an einen einzelnen Kurs gebunden sein.
Lernende können dadurch selbst entwickelte Pythonmodule, Datenbanken,
Webressourcen oder andere Artefakte später in einem weiteren Kurs erneut
verwenden.

## Kurse installieren

### Über eine Setupdatei

Eine Setupdatei enthält nur die geprüfte Kursquelle und die nötigen
Metadaten. Sie enthält keine Schülerlösung. Beispiel:

```json
{
  "name": "PyKIM Standardkurs",
  "repository": "https://github.com/finalnode/PyKIM_Kurs.git",
  "branch": "main"
}
```

### Über ein ZIP-Archiv

Ein Kursarchiv enthält genau eine `.pykim-setup`-Datei sowie die referenzierten
Kursinhalte. Pfade werden vor dem Entpacken geprüft; absolute Pfade,
Verzeichniswechsel und symbolische Links werden abgelehnt. Damit können Kurse
auch ohne Netzwerk über exFAT-formatierte USB-Sticks zwischen Windows, macOS
und Linux verteilt werden.

### Über den Kurskatalog

Der Katalog zeigt frei verfügbare Kurse mit Titel, Kurzbeschreibung, Niveau,
Tags, verantwortlicher Stelle und Quelle. Die mitgelieferte Katalogkopie
funktioniert offline; eine Aktualisierung lädt die Registry aus diesem
Repository.

## M@rkdown

M@rkdown ist normales Markdown mit einfachen Annotationen für strukturierte
Aufgabeninformationen:

```markdown
# Eine Linie zeichnen

Zeichne eine rote Linie von `(20, 20)` bis `(30, 20)`.

@hint: Beginne mit set_position.
@hint: Eine Schleife vermeidet Wiederholungen.
@tags: schleifen, koordinaten, farben
@source: https://example.org/aufgabe
```

Der integrierte Parser prüft Syntax, bekannte Annotationen und notwendige
Felder. Die Vorschau verwendet dieselbe Darstellung wie der spätere Kurs.
Trainerdefinitionen bleiben getrennte, deklarative YAML-Dateien; ausführbarer
Code wird nicht aus Markdown-Metadaten erzeugt.

## Kursquelle und Student Workspace

in:si unterscheidet bewusst zwischen zwei Bereichen:

- **Kursquelle:** veröffentlichte Skripte, Aufgaben, Beispiele und Trainer;
- **Student Workspace:** Lösungen, Lernstand, Projekte, Antworten und
  persönliche Erweiterungen.

Ein Kursupdate ersetzt nur die aktualisierbare Kursquelle. Bestehende
Schülerprojekte und Fortschritte werden nicht als Teil des Repository-Updates
überschrieben. Vor zukünftigen Formatmigrationen sollen Version,
Kompatibilität und Sicherung explizit geprüft werden.

## Sicherheit

Kurse und Schülerprogramme sind potenziell fremder Code. in:si behandelt sie
nicht als automatisch vertrauenswürdig:

- sichtbare Warnung vor Kursimport und Ausführung;
- validierte Repository-, Archiv- und Inhaltspfade;
- getrennte Prozesse für integrierte Programmläufe;
- bereinigte Umgebungsvariablen;
- Laufzeit- und Ausgabegrenzen;
- beendbare Prozessgruppen;
- deklarative statt frei ausführbarer Trainerdaten.

Diese Maßnahmen sind **keine vollständige Sandbox**. Eine garantierte
Abschottung von Dateisystem, Netzwerk und Betriebssystemrechten besteht noch
nicht. Die weitere Architektur soll vorhandene Isolationsmechanismen des
jeweiligen Betriebssystems nutzen, statt eine eigene Sicherheitsgrenze zu
behaupten. Details und Meldeweg stehen in [SECURITY.md](SECURITY.md).

## Offline, Speicherorte und Datenschutz

Nach der Installation eines Kurses funktionieren Lerntexte, Aufgaben, Trainer,
Lernstand und Projekte lokal. Netzwerkzugriffe entstehen nur für ausdrücklich
angestoßene Vorgänge wie Kursinstallation, Katalogabgleich oder Updates.

in:si verwendet derzeit aus Kompatibilitätsgründen den lokalen Basisordner
`PyKIM-Kurse`. Der tatsächliche aktive Kursordner wird in der App angezeigt
und kann direkt geöffnet werden. Langfristig gehören dazu:

- lokale Mehrbenutzerprofile mit getrennten Workspaces;
- atomare und absturzsichere Schreibvorgänge;
- Wiederherstellung nach unterbrochenen USB-Schreibvorgängen;
- reproduzierbare virtuelle Umgebungen pro Betriebssystem und Architektur;
- verständliche Datenschutz- und Berechtigungsübersichten.

## Installation für die Entwicklung

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

Unter Windows wird die virtuelle Umgebung mit
`.venv\Scripts\activate` aktiviert.

## Architektur

Die Anwendung liegt vollständig im Pythonpaket `insi`. `app.py` ist ein
kleiner Application Composer; Zustände und Dienste werden über einen expliziten
`AppContext` an getrennte Views übergeben. Architekturtests verhindern, dass
erneut eine zentrale, mehrere tausend Zeilen große `main()` entsteht.

Die generische Trainingsschicht liegt unter `insi.training`: Sie verwaltet den
aktiven Kurs, Zuordnungs- und Parsons-Aktivitäten, Feedback und Versuche.
Fachmodule liefern ausschließlich ihre domänenspezifischen Prüfbausteine. Für
PyKIM geschieht diese lose Kopplung über den Entry-Point
`pykim.trainer_provider`; konkrete YAML-Definitionen bleiben beim Kurs.

### Wer besitzt welche Trainerdaten?

| Bestandteil | Verantwortlich |
|---|---|
| konkrete Aufgaben, Hinweise und `Trainer/*.yml` | Kursquelle |
| aktiver Kurs, Registry, Feedback, Versuche und Lernstand | in:si |
| PyKIM-Welt und PyKIM-spezifische Prüfregeln | PyKIM-Fachmodul |
| Schülercode und eigene Projekte | getrennter Student Workspace |

Eine Trainerdatei im Kurs beschreibt nur Sollwerte und führt selbst keinen
Pythoncode aus. Ein minimales Beispiel sieht so aus:

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

Der Ablauf beim Öffnen und Bearbeiten eines Kurses ist bewusst gerichtet:

```text
Kursquelle mit Trainer/*.yml
        ↓
in:si aktiviert genau diesen Kurs in insi.training
        ↓
Schülerprogramm ruft run(check="rote-linie") auf
        ↓
PyKIMs neutrale Provider-Schnittstelle fragt in:si
        ↓
PyKIM-Prüfregel bewertet die Welt; in:si zeigt Feedback und speichert den Versuch
```

in:si registriert diese Verbindung als normalen Python-Entry-Point:

```toml
[project.entry-points."pykim.trainer_provider"]
insi = "insi.training.provider:provider"
```

Dadurch kann PyKIM auch ohne in:si verwendet werden und in:si später weitere
Fachmodule für Python, SQLite, HTML/CSS oder andere Informatikthemen anbinden.
Kursquelle, Anwendung und Student Workspace bleiben getrennt: Ein Kursupdate
darf veröffentlichte Inhalte ersetzen, aber niemals bearbeitete Schülerprojekte
oder deren Fortschritt überschreiben.

Wichtige Grenzen:

- in:si darf PyKIM als Fachmodul verwenden;
- PyKIM darf in:si nicht importieren;
- Kurse werden über Dateisystem- und Metadatenverträge angebunden;
- Student Workspaces gehören weder zum App- noch zum Kursrepository;
- fachliche Module sollen unabhängig versioniert und austauschbar bleiben.

## Desktop-Apps bauen

Der Workflow [`.github/workflows/build-desktop.yml`](.github/workflows/build-desktop.yml)
führt zuerst die Tests aus und baut anschließend vier Pakete:

| Ziel | GitHub-Runner | Releaseformat |
|---|---|---|
| Windows x86_64 | `windows-2025` | `.zip` |
| Linux x86_64 | `ubuntu-24.04` | `.tar.gz` |
| macOS Intel | `macos-15-intel` | `.dmg` |
| macOS Apple Silicon | `macos-15` | `.dmg` |

Ein Versionstag erzeugt nach erfolgreichen Builds ein GitHub Release:

```bash
git tag v0.6.0
git push origin v0.6.0
```

Lokale Buildbefehle:

```bash
# Windows oder Linux
python tools/build_desktop_app.py
python tools/package_desktop_app.py

# macOS
python tools/build_macos_dmg.py --rebuild-app
```

Ergebnisse liegen unter `dist/releases/`. Unter Windows sind zwei
`insi.exe`-Prozesse im nativen Fenstermodus normal: lokaler Server und
WebView-Fenster laufen getrennt. Falls das native Fenster nicht erscheint,
öffnet in:si die Oberfläche im Standardbrowser und schreibt eine Startdiagnose.

## Roadmap

Die nächsten technischen Etappen sind:

- Umgebungs- und Kompatibilitätsprüfung vor Kursstart;
- reproduzierbare virtuelle Umgebungen;
- lokale Mehrbenutzerprofile;
- robuste USB- und Absturzwiederherstellung;
- Kurs- und Paketvertrauen mit Prüfsummen und Berechtigungen;
- versionierte Daten- und Kursmigrationen;
- Datenschutzübersicht sowie verpflichtende Lizenz-, Quellen- und
  Verantwortlichkeitsangaben;
- validierte PyKIM-Sprachpakete, die kanonische Lernbefehle mit lokalen
  API-Aliasen verbinden, sobald diese Funktion im PyKIM-Modul verfügbar ist;
- weitere Fachmodule und konfigurierbare Menüs für Mischkurse.

Spätere didaktische Ausbaustufen umfassen Peer Review, Kompetenzmodelle und
weitergehende Zusammenarbeit. Sie werden erst auf der stabilisierten lokalen
Kurs- und Benutzerarchitektur aufgebaut.

Ebenfalls geplant ist ein **Kursbaukasten aus wiederverwendbaren
Inhaltsbibliotheken** für Lehrkräfte. Versionierte Quellen aus Repositories oder
Archiven sollen Aufgaben, Skriptkapitel und weitere Kursbausteine zusammen mit
Metadaten, Tags, Bewertung, Hinweisen, Quellen, Lizenzen und
Trainerdefinitionen bereitstellen. Das Kursstudio soll diese Bausteine
durchsuchbar machen, in der späteren Schüleransicht als Vorschau darstellen und
eine freie Zusammenstellung und Bearbeitung zu Kapiteln und Mischkursen
ermöglichen. Beim Export werden die ausgewählten Versionen vollständig in den
Kurs übernommen, damit er reproduzierbar und offlinefähig bleibt; geschützte
Trainerdaten und Student Workspaces bleiben dabei klar von den bearbeitbaren
Kursinhalten getrennt.

Das Kursstudio soll außerdem einen verständlichen Git-Arbeitsablauf anbieten:
Lehrkräfte können einen Kurs als Repository anlegen oder ein vorhandenes
Repository verbinden, Änderungen prüfen und versionieren sowie sie nach
ausdrücklicher Bestätigung committen und zu einem frei wählbaren Git-Hoster
übertragen. ZIP-Export und rein lokale Kurse bleiben gleichwertige Wege, damit
Git keine Voraussetzung für die Arbeit mit in:si wird.

## Simplicissima

in:si ist die Informatik-Lernumgebung von **Simplicissima**. Die didaktische
Leitidee lautet:

> So viel vereinfachen wie nötig, so wenig abstrahieren wie möglich.

Die Plattform soll technische Einstiegshürden senken, ohne Lernende in einem
proprietären Endsystem festzuhalten. Kurse verwenden echte Sprachen, Dateien
und Werkzeuge; die unterstützende Struktur kann mit wachsender Erfahrung
schrittweise zurücktreten.

## Quellen und Lizenz

Der Footer der Anwendung bündelt Softwarequellen, Kursrepository,
Verantwortliche, Lizenzen und aufgabenspezifische Quellen. Kursautorinnen und
-autoren können Quellen zusätzlich direkt an einzelnen Aufgaben hinterlegen.

in:si steht unter der [MIT-Lizenz](LICENSE). Drittanbieter-Komponenten und
Kursinhalte können eigene Lizenzen besitzen und werden separat ausgewiesen.
