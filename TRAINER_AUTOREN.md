# Trainer und interaktive Aufgaben erstellen

in:si besitzt eine fachmodulneutrale Trainer-Registry. Eine Trainerdatei benennt
ihre Engine ausdrücklich; das Fachmodul validiert und prüft anschließend nur
seine eigenen deklarativen Bausteine. PyKIM ist die erste mitgelieferte Engine.
HTML/CSS, SQLite und Filius können denselben Vertrag später ergänzen, ohne
Registry, Lernstand oder Rückmeldungsansicht umzubauen.

Die Kurswerkstatt bietet dafür einen visuellen Markdowneditor, Formularfelder
für Schwierigkeit, Tags, Quellen und gestufte Hinweise sowie einen Builder für
Prüfbausteine. Markdown und YAML bleiben als Expertenansicht zugänglich. Die
gespeicherten Dateien sind normale, portable Textdateien.

Das aktuelle in:si-Format sieht so aus:

```yaml
format: insi-trainer-v1
engine: pykim
exercises:
  - id: roter-punkt
    title: Ein roter Punkt
    tests:
      - type: pixels
        cells: [[20, 20, red]]
```

Vorhandene PyKIM-Dateien mit `format: 1` bleiben kompatibel und werden beim
Laden automatisch der PyKIM-Engine zugeordnet. Neue Dateien sollten die Engine
ausdrücklich angeben. Trainerdaten enthalten keine ausführbaren Funktionen und
keine Python-Imports.

Alle mitgelieferten Definitionen stehen momentan in
`src/insi/Trainer/definitions.yml`:

```yaml
format: insi-trainer-v1
engine: pykim
exercises:
  - id: roter-punkt
    title: Ein roter Punkt
    tests:
      - type: pixels
        cells:
          - [20, 20, red]
        success: Der rote Punkt liegt richtig.
        failure: Der rote Punkt fehlt oder liegt falsch.
        hint: Gehe zuerst zu (20, 20) und male dort rot.
      - type: position
        position: [20, 20]
    optimization:
      optimal_lines: 5
```

`id` ist die stabile Kennung, die auch bei `run(check="roter-punkt")`
verwendet wird. `title` erscheint in den Testergebnissen. Jeder Eintrag unter
`tests` benötigt einen bekannten `type`.

## Rückmeldungen

Jeder Test kann drei Texte überschreiben:

```yaml
- type: loop
  success: Du verwendest eine Schleife für alle acht Punkte.
  failure: Die Wiederholungen sind noch einzeln notiert.
  hint: Setze paint() und right(2) in eine for-Schleife.
```

Fehlen Texte, verwendet der Trainer verständliche Standardmeldungen. Für
veröffentlichte Aufgaben sollte insbesondere ein konkreter Tipp vorhanden sein.

## Zeichnungen prüfen

Einzelne farbige Pixel:

```yaml
- type: pixels
  cells:
    - [20, 20, purple]
    - [21, 20, orange]
```

Nur Positionen, ohne Farbprüfung:

```yaml
- type: pixels
  exact: false
  cells:
    - [20, 20]
    - [21, 20]
```

Gerade Linien einschließlich Start- und Endpunkt:

```yaml
- type: pixels
  paths:
    - {start: [20, 20], end: [30, 20], color: purple}
    - {start: [30, 20], end: [30, 30], color: orange}
```

Für häufige Unterrichtsmuster existieren kompakte Vorlagen:

```yaml
- type: pixels
  checkerboard:
    start: [20, 20]
    size: [8, 8]
    colors: [purple, orange]

- type: pixels
  stairs: {start: [50, 50], steps: 5, size: 5}

- type: square
  start: [50, 50]
  side: 5
```

Zusätzliche Pixel und die Gesamtzahl lassen sich getrennt bewerten:

```yaml
- type: no-extra-pixels
  stairs: {start: [50, 50], steps: 5, size: 5}
- type: pixel-count
  count: 51
  success: Die Treppe besitzt genau die richtige Länge.
```

## Figuren und Weltzustand

```yaml
- type: position
  pixel: KIM
  position: [30, 20]
- type: positions
  positions: {KIM: [30, 20], MIA: [40, 20]}
- type: pixel-names
  names: [KIM, MIA]
- type: visibility
  pixel: MIA
  visible: false
```

## Töne und Pausen

Audioereignisse werden als `[Note, beats]` angegeben. `null` steht für eine
Pause:

```yaml
- type: audio
  events:
    - [C4, 1]
    - [E4, 1]
    - [G4, 2]
    - [null, 1]
```

## Kontrollstrukturen und Aufrufe

```yaml
- type: loop
- type: nested-loop
- type: condition
  calls: [get_color]
- type: function
  name: update
- type: calls
  names: [cls, run]
- type: parallel
```

## Klassen prüfen

```yaml
- type: class
  name: MusikPixel
  base: Pixel
- type: super-init
  class: MusikPixel
- type: methods
  class: MusikPixel
  names: [update, draw]
```

## Codeumfang bewerten

```yaml
optimization:
  optimal_lines: 10
```

Gezählt werden nichtleere Codezeilen ohne reine Kommentare. Zehn oder weniger
relevante Zeilen ergeben 100 %, 15 Zeilen 67 % und 20 Zeilen 50 %. Die
fachlichen Tests entscheiden unabhängig davon, ob die Lösung korrekt ist.

## Engineunabhängige Aktivitäten

Einfache Interaktionen benötigen kein Fachmodul. Die Core-Engine unterstützt
freie Antworten, Zuordnungen und Parsons-Puzzles:

```yaml
format: insi-trainer-v1
engine: core
id: begriffe-zuordnen
title: Begriffe zuordnen
mode: matching
pairs:
  - {id: bedingung, left: if, right: Bedingung}
  - {id: schleife, left: for, right: Wiederholung}
```

## Sicherheit und Erweiterungen

Die YAML-Datei wird mit `yaml.safe_load()` gelesen. Unbekannte Felder und
Prüftypen werden abgelehnt. Ein Inhaltspaket kann daher keine eigenen
Python-Befehle einschleusen.

Wenn ein neuer fachlicher Prüftyp benötigt wird, wird er einmal in der
zuständigen Fachmodul-Engine implementiert und getestet. Neue Engines werden
über den Entry-Point `insi.trainer_backends` registriert. Sie liefern
deklarative Aufgaben, die zugehörigen Starterdateien und werten eine neutrale
`Submission` aus. Darin kann in:si Quelltext, einen Einstiegspunkt oder ein
ganzes Projektverzeichnis übergeben. Damit benötigt etwa eine HTML/CSS-Engine
keinen fingierten Python-`checker`. in:si verwaltet Feedback, Versuche und
Kurswechsel. Beliebiger Python-Code, Lambdas oder dynamische Imports gehören
nicht in Trainingsdaten.

Die Aufgabenstellung bleibt als gleichnamige Markdown-Datei unter
`src/insi/Aufgaben/imperativ/` oder `Aufgaben/oop/`. Das Autorenwerkzeug
von in:si erzeugt und validiert YAML und Markdown gemeinsam und speichert
Entwürfe unter `.pykim/author_drafts/` im Kursordner.
