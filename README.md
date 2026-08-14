# <img src="packaging/macos/assets/app-icon-master.png" alt="in:si-Logo" width="72" align="center"> in:si

PyKIM 0.5.5 ist eine deutschsprachige Python-Lernumgebung auf Basis von
[Pyxel](https://github.com/kitao/pyxel). Eine kleine Pixel-Figur namens KIM
bewegt sich durch eine 160 × 120 Pixel große Welt, liest und verändert Farben,
zeichnet Spuren und spielt Töne. Dieselben Grundlagen lassen sich zuerst mit
einfachen Befehlen, später objektorientiert und schließlich mit der Pyxel-API
verwenden.

> **Projektperspektive:** Die bisherige **PyKIM Suite** wird zu **in:si**, der
> Informatik-Lernumgebung von Simplicissima. Die Desktop-Lernumgebung soll neben
> Python und PyKIM auch weitere Themen der Informatik über installierbare Kurse
> bedienen. **PyKIM** wird dafür aus der Suite herausgelöst und als eigenständiges
> Pythonmodul mit seiner Pixelwelt, API und Testunterstützung weiterentwickelt.
> Technische Paketnamen, Kursformate und vorhandene Schülerdaten bleiben bei
> dieser schrittweisen Trennung kompatibel.

## in:si herunterladen

> **Desktop-Version 0.5.5 – letzte Veröffentlichung unter dem bisherigen Namen
> PyKIM Suite. Die nächste Veröffentlichung wird aus diesem Repository gebaut,
> trägt sichtbar den Namen in:si und technisch den Dateinamen `insi`.**

| Betriebssystem | Architektur | Download |
|---|---|---|
| Windows | x86_64 | **[Windows-App herunterladen (.zip)](https://github.com/finalnode/insi/releases)** |
| macOS | Apple Silicon (`arm64`) | **[macOS-App für M1/M2/M3/M4 herunterladen (.dmg)](https://github.com/finalnode/insi/releases)** |
| macOS | Intel (`x86_64`) | **[macOS-App für Intel herunterladen (.dmg)](https://github.com/finalnode/insi/releases)** |
| Linux | x86_64 | **[Linux-App herunterladen (.tar.gz)](https://github.com/finalnode/insi/releases)** |

**Direkt mit dem Beispielkurs starten:**

- **[PyKIM-Standardkurs herunterladen (.pykim-setup)](https://raw.githubusercontent.com/finalnode/insi/main/examples/course-setups/pykim-standardkurs.pykim-setup)** – nach dem App-Start in der Kursauswahl hochladen
- **[Inhalte des Beispielkurses ansehen](https://github.com/finalnode/PyKIM_Kurs)** – Skripte, Aufgaben und automatische Trainer

Die Builds werden durch GitHub Actions geprüft und anschließend dauerhaft unter
[GitHub Releases](https://github.com/finalnode/insi/releases) bereitgestellt.
Die Apps sind derzeit noch nicht signiert oder notarisiert.

Zum Projekt gehören zwei eng verbundene Teile:

- **PyKIM-Bibliothek:** testbare Zeichen-, Bewegungs-, Audio- und Weltlogik.
- **in:si:** lokale Desktop-Lernumgebung mit Skript, Aufgaben, Tests,
  Lernstand, IDE-Anbindung, Projekten und persönlichen Erweiterungen.

Langfristig werden diese Verantwortlichkeiten deutlicher getrennt:

- **in:si:** komfortable Desktop-Lernumgebung für einen breiten Einstieg in
  die Informatik. Sie unterstützt unterschiedliche Themen, Programmiersprachen
  und Werkzeuge, ohne auf Python oder PyKIM festgelegt zu sein.
- **PyKIM:** eigenständiges und erweiterbares Pythonmodul für den Einstieg in
  Programmierung mit Pixelwelt, Bewegung, Farbe, Audio und Pyxel.
- **Kurse:** separat veröffentlichte Inhaltspakete, die PyKIM verwenden können,
  aber nicht darauf beschränkt sind.

Die fachliche Weltlogik liegt nicht nur im Grafikfenster. Aufgaben können
deshalb deterministisch geprüft werden, ohne Bildschirminhalte vergleichen zu
müssen.

> Entwicklungsstand: Alpha. Die Python-Bibliothek ist plattformunabhängig.
> GitHub Actions baut Desktop-Pakete für Windows, Linux sowie macOS auf Intel
> und Apple Silicon. Diese Pakete sind noch nicht signiert oder notarisiert.

## Inhalt

- [in:si herunterladen](#insi-herunterladen)
- [Didaktische Einordnung: Simplicissima und in:si](#didaktische-einordnung-simplicissima-und-insi)
- [Projektperspektive: in:si und PyKIM-Modul](#projektperspektive-insi-und-pykim-modul)
- [Funktionsumfang](#funktionsumfang)
- [Schnellstart](#schnellstart)
- [Grundmodell](#grundmodell)
- [Imperative API](#imperative-api)
- [Farben und Zeichnen](#farben-und-zeichnen)
- [Animation](#animation)
- [Töne und Musik](#töne-und-musik)
- [Objektorientierte API](#objektorientierte-api)
- [Mehrere Pixel und Parallelität](#mehrere-pixel-und-parallelität)
- [Interaktive Programme](#interaktive-programme)
- [Aufgaben und Trainer](#aufgaben-und-trainer)
- [in:si](#insi)
- [Kursordner und Setupdatei](#kursordner-und-setupdatei)
- [Externes Kurs-Repository](#externes-kurs-repository)
- [Eigene Erweiterungen](#eigene-erweiterungen)
- [Eigene Projekte und Pyxel-Ressourcen](#eigene-projekte-und-pyxel-ressourcen)
- [IDE und Python-Laufzeit](#ide-und-python-laufzeit)
- [Sicherheit bei der Codeausführung](#sicherheit-bei-der-codeausführung)
- [Speicherorte und Datenschutz](#speicherorte-und-datenschutz)
- [Installation und Entwicklung](#installation-und-entwicklung)
- [Desktop-Apps bauen](#desktop-apps-bauen)
- [GitHub Actions und Releases](#github-actions-und-releases)
- [Grenzen und zurückgestellte Funktionen](#grenzen-und-zurückgestellte-funktionen)
- [Lizenzierung](#lizenzierung)

## Didaktische Einordnung: Simplicissima und in:si

PyKIM folgt der didaktischen Idee von **Simplicissima**: Komplexe fachliche
Prozesse werden so weit vereinfacht, dass Lernende unmittelbar beginnen können,
ohne den eigentlichen Gegenstand dauerhaft durch eine künstliche Lernwelt zu
ersetzen. Dabei gilt:

> **So viel vereinfachen wie nötig, so wenig abstrahieren wie möglich.**

PyKIM setzt diese Haltung für den Einstieg in Python konkret um. Lernende
schreiben von Anfang an echtes Python. Technische Einstiegshürden wie
Fensterverwaltung, Eventloop und die direkte Arbeit mit einer Spielebibliothek
treten zunächst zurück, während Bewegung, Zustand, Schleifen, Bedingungen und
Funktionen sichtbar bleiben. Die Vereinfachung blendet Komplexität zeitweise
aus, vermittelt aber kein fachlich falsches Modell, das später widerrufen
werden müsste.

Der vorgesehene Lernweg führt deshalb bewusst aus dem Gerüst heraus:

```text
imperative PyKIM-Befehle
        ↓
Objekte verwenden
        ↓
eigene Klassen entwickeln
        ↓
direkt mit Pyxel arbeiten
        ↓
normale Python-Projekte
```

Damit ist PyKIM eine konkrete Umsetzung der Simplicissima-Leitidee und kein
proprietäres Endsystem. In der zukünftigen Marken- und Projektstruktur bildet
**in:si** den Informatikbereich von Simplicissima. Die allgemeine Lern- und
Arbeitsumgebung ist als **in:si** vorgesehen; PyKIM bleibt darin ein
eigenständiges Python-Lernmodul, das auch außerhalb der Suite eingesetzt werden
kann.

```text
Simplicissima         didaktisches Dach
└── in:si             Informatikbereich und Lernumgebung
    ├── PyKIM         Python-Lernmodul
    └── Kurse         didaktische Lernpfade und Inhalte
```

## Projektperspektive: in:si und PyKIM-Modul

in:si, das PyKIM-Modul und die frei verfügbaren Kursinhalte leben in getrennten
Repositories. Dadurch kann die Lernumgebung unterschiedliche Themen tragen,
ohne die Python-Pixelwelt oder einzelne Kurse fest einzubauen:

| Baustein | Zukünftige Verantwortung |
|---|---|
| **in:si** | Allgemeine Lernumgebung für unterschiedliche Themen der Informatik |
| **[PyKIM-Modul](https://github.com/finalnode/PyKIM)** | Installierbares Pythonmodul für Pixelwelt, Bewegung, Farbe, Audio und Tests |
| **Kursrepositories** | Unabhängige Skripte, Aufgaben, Hinweise, Quellen und Trainerdefinitionen |
| **Kurskatalog** | Auffindbarkeit und Installation frei verfügbarer Kurse |

in:si soll damit nicht nur einen einzelnen Pythonkurs abbilden. Denkbare
Kurse können beispielsweise Grundlagen der Informatik, Algorithmen,
Datenstrukturen, Webentwicklung, Datenbanken, Netzwerke oder andere
Programmiersprachen behandeln. Aufgabentypen, Lernstand, Quellen, Hinweise und
Kursinstallation gehören zur Plattform; fachliche Laufzeiten und Bibliotheken
werden als Module angebunden.

PyKIM bleibt dabei erhalten. Es wird aus der Desktop-Anwendung herausgelöst und
als eigenständiges Pythonpaket ausgebaut. Dadurch kann PyKIM sowohl innerhalb
eines in:si-Kurses als auch unabhängig davon in einer IDE, in eigenen
Unterrichtsmaterialien oder in anderen Pythonprojekten verwendet werden.

### Technischer Schwerpunkt für 0.6.0

Der nächste Release konzentriert sich bewusst auf die technische Grundlage.
Zum verbindlichen Umfang gehören:

- eine Umgebungsprüfung vor Kursstart und Programmausführung;
- reproduzierbare, pro Betriebssystem und Architektur neu erzeugte virtuelle
  Python-Umgebungen; Quellcode, Daten und Lockdateien bleiben portabel, eine
  bestehende `.venv` wird nicht zwischen Windows, macOS und Linux kopiert;
- echte lokale Mehrbenutzerprofile mit getrennten Lernständen und Workspaces;
- absturzsichere, atomare Schreibvorgänge und Wiederherstellung für lokale und
  exFAT-basierte USB-Arbeitsordner;
- nachvollziehbares Vertrauen für Kurse und Pakete einschließlich Herkunft,
  Prüfsummen, Berechtigungen und sichtbarer Warnungen;
- Kompatibilitätsprüfungen vor Installation, Öffnen und Aktualisieren;
- versionierte, getestete und vorab gesicherte Daten- und Kursmigrationen;
- datensparsame Voreinstellungen und eine verständliche Datenschutzübersicht;
- verpflichtende Angaben zu Lizenz, Quellen und verantwortlicher Person oder
  Organisation eines Kurses.

Kompetenzmodelle, Peer-Review, weitergehende Kollaboration und andere
didaktische Ausbaustufen bleiben wichtig, gehören aber bewusst in **Future**.
Dieser Release stabilisiert zuerst die technische Basis, auf der solche
Kursmechanismen später verlässlich aufbauen können.

### Geplante Weiterentwicklung von PyKIM

Die Pixelwelt soll schrittweise über reine Zeichen- und Bewegungsaufgaben
hinauswachsen. Als nächste fachliche Ebene sind Hindernisse (`Obstacle`) und
daraus zusammengesetzte Labyrinthe (`Maze`) vorgesehen. KIM soll begehbare und
gesperrte Felder erkennen, Nachbarn untersuchen und gefundene Wege in der
Pixelwelt sichtbar machen können.

Darauf aufbauend sollen typische Themen aus Algorithmik und Graphentheorie
anschaulich programmierbar werden: systematisches Durchsuchen eines Labyrinths,
Breiten- und Tiefensuche sowie die Suche nach kürzesten oder günstigsten Wegen,
beispielsweise mit Breitensuche, Dijkstra oder A*. Die Animation der einzelnen
Suchschritte und passende Trainer sollen nicht nur das Ergebnis, sondern auch
den Weg zum Algorithmus nachvollziehbar und testbar machen.

Diese Bausteine gehören zur geplanten PyKIM-Modul-Roadmap und sind noch nicht
Bestandteil der stabilen API.

Ebenfalls für eine spätere PyKIM-Version vorgesehen ist eine validierte
Sprachmap für die Lern-API. Kurse oder Sprachpakete können damit kanonische
Befehle wie `right`, `paint` oder `get_position` mit lokalen Aliasen wie
`rechts`, `male` oder `position_lesen` anbieten. Kollisionsprüfung und eine
eindeutige Rückführung auf die kanonische API halten Trainer und Projekte
kompatibel; Python-Schlüsselwörter selbst bleiben unverändert.

Die Umstellung erfolgt schrittweise. Der sichtbare App-Name lautet **in:si**,
technische Desktop-Artefakte heißen `insi`; das Pythonmodul, vorhandene
Kursordner und `.pykim-setup`-Dateien behalten ihre kompatiblen PyKIM-Namen.
Die Zielarchitektur macht bestehende Schülerdaten nicht inkompatibel.

## Funktionsumfang

### Programmieren mit PyKIM

- Bewegungen nach oben, unten, links und rechts
- absolute Positionierung und lesbare Koordinaten
- 16 Farben der Pyxel-Standardpalette
- einzelne Farbpixel und durchgehende Malspuren
- Farbsensor am aktuellen Feld, an Nachbarfeldern oder beliebigen Koordinaten
- schrittweise Animation mit einer Geschwindigkeit von 1 bis 100
- Kamera-Zoom von 1-fach bis 10-fach mit `world.zoom()`
- Töne, Pausen, Tonlängen, Rhythmen und Melodien
- imperative Kurzbefehle für Einsteiger
- objektorientierte Steuerung über `Pixel` und `World`
- mehrere benannte Pixel in derselben Welt
- parallele Bewegungsblöcke
- eigene Pixel-Unterklassen mit `update()` und `draw()`
- interaktive Spielschleifen und Tastaturabfragen
- Pyxel-nahe Zeichenoperationen als vorbereiteter API-Übergang

### Lernen mit der Suite

- mehrere lokale Kursordner, die auch auf USB- oder WebDAV-Laufwerken liegen können
- kompakte Kursauswahl bei jedem Start und Kurswechsel im laufenden Betrieb
- direkte Kurseinrichtung durch Upload einer kleinen `.pykim-setup`-Datei
- Skripte, Aufgaben und Trainer aus einem externen GitHub-Repository
- automatischer Repo-Abgleich beim Kursstart und manueller Inhalts-Refresh
- eingebautes Skript mit Inhaltsnavigation
- ausführbare und kopierbare Codebeispiele
- Aufgabenbearbeitung in einem Codeeditor
- freie Aufgaben mit optionalem Antwort-Trainer und dauerhaft gespeichertem Antwortfeld
- Speichern, Starten, Stoppen, Kopieren und Öffnen in einer externen IDE
- deutschsprachige automatische Testfälle mit ausklappbaren Details
- Analyse von Schleifen, Funktionen, Bedingungen, Klassen und Parallelität
- Optimierungsbewertung anhand relevanter Codezeilen
- lokaler Lernstand und persönliches Dokubuch
- Beispielgalerie und Pyxel-Beispiele
- eigene Python-, PyKIM- und Pyxel-Projekte mit integriertem Codeeditor
- projektbezogene Markdown-Dokumentation mit Live-Vorschau
- Start des Pyxel-Ressourceneditors für Sprites, Tilemaps, Sounds und Musik
- persönliches Modul `erweiterungen.py` für eigene Funktionen und Klassen
- Erkennung von Thonny, VS Code, PyCharm und benutzerdefinierten IDEs
- Erkennung und Auswahl geeigneter Python-Interpreter
- verwaltete lokale Python-Laufzeit mit Offline-Wheelhouse
- getrennte Updateprüfung für App und Lerninhalte
- direkter Zugriff auf Kursordner und sicheres Löschen über den Systempapierkorb
- feste, schmale Fußleiste mit Projekt-, Lizenz- und Herkunftshinweis

## Schnellstart

Ein minimales Programm:

```python
from pykim import *

speed(30)
paint("orange")
right(10)
down(5)
paint_stop()

run()
```

KIM startet bei `(0, 0)`. Der Ursprung liegt links oben. `x` wächst nach
rechts, `y` nach unten.

Eine typische Aufgabe mit automatischer Prüfung endet so:

```python
run(check="quadrat-5")
```

Der Trainer wertet vor dem Öffnen des Fensters die logische Welt und den
Quellcode aus und gibt verständliche Rückmeldungen auf der Konsole und in der
Suite aus.

## Grundmodell

Die Welt besitzt die feste Größe:

```python
WIDTH = 160
HEIGHT = 120
```

Gültige Koordinaten sind daher:

- `x`: `0` bis `159`
- `y`: `0` bis `119`

Bewegungen außerhalb der Welt werden nicht abgeschnitten, sondern mit einer
verständlichen `ValueError`-Exception abgewiesen. Schrittweiten und Beats
müssen ganze Zahlen sein; Boolesche Werte werden dabei nicht als Zahlen
akzeptiert.

PyKIM stellt direkt zwei Objekte bereit:

```python
from pykim import kim, world
```

- `kim` ist der mitgelieferte Standardpixel.
- `world` ist die gemeinsame Welt aller Pixel.
- Freie Befehle wie `right()` steuern dasselbe Objekt wie `kim.right()`.

Der veränderliche Zustand von Position, Weltzellen, Audio und Animation liegt
gebündelt in der Standardinstanz `runtime`. Die einfache API bleibt dadurch
unverändert, während der Kern schrittweise von früheren unabhängigen
Modulzuständen entkoppelt wird. `runtime`, `world` und `kim` gehören immer
zusammen; normaler Unterrichtscode muss `runtime` nicht direkt verwenden.

## Imperative API

Der Einsteigerweg verwendet:

```python
from pykim import *
```

### Position lesen und setzen

| Funktion | Wirkung |
|---|---|
| `get_x()` | aktuelle x-Koordinate lesen |
| `get_y()` | aktuelle y-Koordinate lesen |
| `get_position()` | beide Koordinaten als `(x, y)` lesen |
| `set_position(x, y)` | beide Koordinaten setzen |
| `set_x(x)` | nur x setzen |
| `set_y(y)` | nur y setzen |

```python
set_position(20, 30)
print(get_x())  # 20
print(get_y())  # 30
print(get_position())  # (20, 30)
```

### Relativ bewegen

| Funktion | Standard | Wirkung |
|---|---:|---|
| `up(steps=1)` | 1 | nach oben |
| `down(steps=1)` | 1 | nach unten |
| `left(steps=1)` | 1 | nach links |
| `right(steps=1)` | 1 | nach rechts |

```python
set_position(20, 20)
right(8)
down(4)
print(get_x(), get_y())  # 28 24
```

Eine Schrittweite von `0` ist erlaubt. Negative Schrittweiten sind nicht
zulässig; für die Gegenrichtung wird der entsprechende Bewegungsbefehl
verwendet.

### Sichtbarkeit

```python
hide()
show()
```

`hide()` versteckt KIM, löscht aber weder Position noch Malspur. Ein
versteckter Pixel kann sich weiterhin bewegen und malen.

## Farben und Zeichnen

PyKIM verwendet die 16 Farben der Pyxel-Standardpalette:

| Index | Name | Index | Name |
|---:|---|---:|---|
| 0 | `black` | 8 | `red` |
| 1 | `navy` | 9 | `orange` |
| 2 | `purple` | 10 | `yellow` |
| 3 | `green` | 11 | `lime` |
| 4 | `brown` | 12 | `cyan` |
| 5 | `dark_blue` | 13 | `gray` |
| 6 | `light_blue` | 14 | `pink` |
| 7 | `white` | 15 | `peach` |

Farben dürfen als Name oder Index angegeben werden:

```python
set_color("purple")
set_color(2)
```

### Malspur

```python
paint("purple")  # aktuelles Feld malen und Spur einschalten
right(10)        # alle besuchten Felder malen
paint_stop()     # Spur ausschalten
```

`paint()` malt sofort die aktuelle Position. Ohne Argument verwendet es die
zuletzt mit `set_color()` gewählte Farbe, andernfalls Weiß. Für genau einen
Punkt wird die Spur direkt wieder beendet:

```python
paint("orange")
paint_stop()
```

`paint_start()` und `paint_path()` existieren als Kompatibilitätsaliase für
`paint()`, werden aber nicht mehr als Standard-API gelehrt und sind nicht in
`from pykim import *` enthalten.

### Farben lesen

```python
get_color()          # aktuelle Position
get_color("right")   # unmittelbarer rechter Nachbar
get_color(100, 50)   # beliebige Position
```

Erlaubte Richtungsnamen sind `up`, `down`, `left` und `right`. Das Ergebnis
ist immer ein kanonischer Farbname aus der Tabelle. Bei aktiver Animation wird
das gelesene Feld kurz als Sensor markiert, ohne seine gespeicherte Farbe zu
verändern.

### Hintergrund und Hindernisse

Die Welt kann eine eigene Hintergrundfarbe erhalten. Das Setzen der
Hintergrundfarbe leert zugleich die bisherige Zeichnung:

```python
world.set_background("light_blue")
```

Eine oder mehrere Farben lassen sich als Hindernisse markieren. Pixel können
diese Felder nicht betreten und bleiben bei einer längeren Bewegung direkt vor
dem ersten Hindernis stehen:

```python
world.set_background("light_blue")
world.rect(30, 10, 2, 40, "red")
world.set_obstacle("red")

set_position(20, 20)
right(20)                 # KIM bleibt bei (29, 20) stehen

if world.is_obstacle(30, 20):
    print("Hier steht eine Wand.")
```

KIM und alle weiteren Pixel können sämtliche direkt angrenzenden Hindernisse
auf einmal ermitteln. Das Ergebnis enthält die Richtungen `up`, `down`, `left`
und `right`; ein leeres Tupel bedeutet, dass alle vier Nachbarfelder frei sind.
Weltränder werden ebenfalls als Hindernisse gemeldet:

```python
richtungen = get_obstacles()       # zum Beispiel ("up", "right")
richtungen = kim.get_obstacles()   # derselbe Sensor über das KIM-Objekt
richtungen = mia.get_obstacles()   # relativ zur Position von MIA

if "right" not in get_obstacles():
    right()
```

### Gegenstände einsammeln

`collect()` entfernt die Farbe an KIMs aktueller Position, stellt dort die
Hintergrundfarbe wieder her und gibt den Namen der eingesammelten Farbe zurück.
Mit `count_color()` und `items_left()` lassen sich Sammelaufgaben steuern:

```python
while items_left("red"):
    right()
    if get_color() == "red":
        eingesammelt = collect()

print(count_color("red"))  # 0
```

Zusätzliche Figuren sammeln relativ zu ihrer eigenen Position mit
`mia.collect()`. Vorgefertigte Aufgabenspielfelder werden sicher und
deklarativ in den Trainerdaten beschrieben. Der automatisch erzeugte Starter
ruft `prepare("aufgaben-id")` vor dem Schülercode auf:

```yaml
world:
  background: light_blue
  start: [10, 20]
  cells:
    - [12, 20, red]
    - [15, 20, red]
    - [19, 20, red]
  obstacles: [brown]
tests:
  - type: color-count
    color: red
    count: 0
```

Damit gehört der Aufbau des Spielfelds zur Aufgabe und muss von Lernenden
nicht abgetippt werden. `world` akzeptiert ausschließlich Hintergrund,
Startposition, Farbfelder und Hindernisfarben; ausführbarer Python-Code ist in
den Trainerdaten weiterhin nicht erlaubt.

Hindernisse sind bewusst farbbasiert: Wird ein rotes Hindernis mit einer
anderen Farbe übermalt, ist das Feld wieder passierbar. Umgekehrt wird jedes
neu rot gemalte Feld zu einem Hindernis. `set_position()` bleibt als
Start- und Teleportwerkzeug verfügbar und darf eine Figur auch direkt auf ein
Hindernis setzen.

```python
world.set_obstacle("red", "brown")
world.remove_obstacle("brown")
world.clear_obstacles()
```

## Animation

Ohne Animation erscheint die Welt direkt im Endzustand. Mit `animate()` werden
alle Zwischenschritte aufgezeichnet:

```python
animate()       # 0,1 Sekunden pro Schritt
animate(0.25)   # 0,25 Sekunden pro Schritt
```

Die schülerfreundliche Alternative ist:

```python
speed(1)    # sehr langsam
speed(50)   # schnell
speed(100)  # Endzustand sofort anzeigen
```

`speed()` akzeptiert nur ganze Zahlen von 1 bis 100. Animation und
Geschwindigkeit werden vor den Bewegungen konfiguriert.

Beim Start zeigt PyKIM für jeden sichtbaren Pixel eine kurze Achsenanimation.
Danach werden Bewegungen, Malereignisse, Sensorzugriffe und Sichtbarkeit in der
aufgezeichneten Reihenfolge wiedergegeben.

## Töne und Musik

```python
play_tone("C4")
play_tone("F#4", beats=2)
play_tone(60)
play_pause()
play_pause(beats=2)
```

### Tonhöhen

- MIDI-Zahlen von `36` bis `95`
- Notennamen von `C2` bis `B6`
- Vorzeichen `#` und `b`, beispielsweise `F#4` oder `Bb3`

PyKIM verwendet die verbreitete MIDI-Benennung, bei der `C4` der MIDI-Note 60
entspricht. Pyxel benennt seinen internen Bereich anders; PyKIM übersetzt die
Notennamen beim Abspielen automatisch.

`beats` ist eine positive ganze Zahl. Töne und Pausen werden in einer
gemeinsamen Warteschlange gespeichert und nach dem Start des Fensters in
Reihenfolge abgespielt.

```python
notes = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]

for note in notes:
    play_tone(note)
```

## Objektorientierte API

Die freie und die objektorientierte Schreibweise greifen auf denselben
Standardpixel zu:

```python
from pykim import kim, world

kim.set_position(20, 20)
kim.paint("purple")
kim.right(10)
kim.paint_stop()

world.speed(30)
world.run()
```

### `Pixel`

Konstruktor:

```python
Pixel(pixel_world, name, x=0, y=0)
```

Normalerweise werden Pixel mit `world.new_pixel()` oder `world.spawn()`
erzeugt, nicht durch einen direkten Konstruktoraufruf.

| Eigenschaft/Methode | Bedeutung |
|---|---|
| `name` | eindeutiger Anzeigename |
| `world` | zugehörige Welt |
| `x`, `y` | les- und schreibbare Koordinaten |
| `get_x()`, `get_y()` | einzelne Koordinate lesen |
| `get_position()` | Position als Tupel `(x, y)` lesen |
| `position` | kompatible les- und schreibbare Eigenschaft |
| `visible` | aktueller Sichtbarkeitszustand |
| `set_position(x, y)` | Position setzen |
| `set_x(x)`, `set_y(y)` | einzelne Koordinate setzen |
| `up/down/left/right(steps=1)` | bewegen |
| `set_color(color)` | Malfarbe auswählen |
| `paint(color=None)` | Feld malen und Spur aktivieren |
| `paint_stop()` | Spur beenden |
| `get_color(...)` | Farbe lesen |
| `get_obstacles()` | Richtungen angrenzender Hindernisse ermitteln |
| `collect()` | aktuelle Farbe einsammeln und Hintergrund freilegen |
| `hide()`, `show()` | Sichtbarkeit steuern |
| `play_tone(...)`, `play_pause(...)` | Audioereignis einreihen |
| `update()` | Hook pro Frame im interaktiven Modus |
| `draw()` | Figur im interaktiven Modus zeichnen |

### `World`

| Eigenschaft/Methode | Bedeutung |
|---|---|
| `width`, `height` | Weltgröße |
| `cells` | logische Farbmatrix |
| `pixels` | Tupel aus KIM und allen weiteren Pixeln |
| `frame_count` | aktueller Pyxel-Frame, außerhalb des Fensters `0` |
| `background_color` | kanonischer Name der Hintergrundfarbe |
| `obstacle_colors` | Tupel aller aktuell unpassierbaren Farben |
| `new_pixel(name, x=0, y=0)` | normalen Pixel erzeugen |
| `spawn(PixelClass, name, ...)` | eigene Pixel-Unterklasse erzeugen |
| `animate(delay=0.1)` | Animation einschalten |
| `speed(value)` | Geschwindigkeit 1 bis 100 |
| `zoom(value)` | Weltpixel und Kameraansicht 1-fach bis 10-fach vergrößern |
| `play_tone(...)`, `play_pause(...)` | gemeinsames Audiosystem |
| `parallel()` | parallelen Befehlsblock starten |
| `cls(color="black")` | Anzeige bzw. Welt leeren |
| `clear(color="black")` | Alias für `cls()` |
| `set_background(color)` | Hintergrund setzen und Welt damit leeren |
| `set_obstacle(*colors)` | Farben als Hindernisse markieren |
| `remove_obstacle(*colors)` | einzelne Hindernisfarben entfernen |
| `clear_obstacles()` | alle Hindernisfarben entfernen |
| `is_obstacle(x, y)` | Hindernis an einer Position prüfen |
| `get_obstacles(x, y)` | Hindernisrichtungen um eine Position ermitteln |
| `count_color(color)` | Felder einer Farbe zählen |
| `pset(x, y, color)` | einen Weltpixel setzen |
| `rect(x, y, width, height, color)` | gefülltes Rechteck zeichnen |
| `text(x, y, value, color="white")` | Text in `draw()` zeichnen |
| `btn(key)` | Taste wird gehalten |
| `btnp(key)` | Taste wurde neu gedrückt |
| `btnr(key)` | Taste wurde losgelassen |
| `run(...)` | Fenster, Spielschleife oder Trainer starten |

Pixelnamen müssen eindeutig sein. `KIM` ist für den Standardpixel
reserviert.

### Fenstergröße

```python
world.zoom(4)
world.run()
```

`world.zoom()` akzeptiert ganze Zahlen von 1 bis 10. Das Fenster behält seine
Größe, aber jeder logische Weltpixel wird als entsprechend großer Block
dargestellt. Die Kamera folgt KIM und wird an den Rändern der Welt begrenzt.
Die logische Welt bleibt immer 160 × 120 Pixel groß: Koordinaten,
Zeichnungen und Trainerergebnisse ändern sich durch den Zoom nicht. Ohne
Aufruf gilt Zoomstufe 1.

## Mehrere Pixel und Parallelität

```python
from pykim import kim, world

world.speed(25)

kim.set_position(20, 20)
kim.paint("purple")

mia = world.new_pixel("MIA", x=60, y=20)
mia.paint("orange")

leo = world.new_pixel("LEO", x=40, y=60)
leo.paint("cyan")

with world.parallel():
    kim.right(15)
    mia.left(15)
    leo.up(20)

kim.paint_stop()
mia.paint_stop()
leo.paint_stop()
leo.hide()

world.run()
```

Innerhalb von `world.parallel()` werden die Ereignisse verschiedener Pixel
zeitgleich wiedergegeben. Unterschiedlich lange Bewegungen sind erlaubt; ein
früher fertiger Pixel wartet an seiner Zielposition. Parallele Blöcke dürfen
nicht ineinander verschachtelt werden.

### Eigene Pixelklassen

```python
from pykim import Pixel, world


class MusikPixel(Pixel):
    def __init__(self, pixel_world, name, x=0, y=0, note="C4"):
        super().__init__(pixel_world, name, x, y)
        self.note = note

    def update(self):
        if self.world.btnp("space"):
            self.play_tone(self.note)


mia = world.spawn(MusikPixel, "MIA", 40, 30, note="E4")
world.run()
```

`world.spawn()` reicht zusätzliche benannte Argumente an den Konstruktor der
Unterklasse weiter und registriert die Figur für Welt und Animation.

## Interaktive Programme

Wird `run()` ohne Callbacks aufgerufen, zeigt PyKIM eine vorberechnete
Befehlsfolge. Mit `update` und `draw` arbeitet PyKIM als echte Spielschleife:

```python
from pykim import kim, world


def update():
    if world.btn("right") and kim.x < world.width - 1:
        kim.right()
    if world.btn("left") and kim.x > 0:
        kim.left()


def draw():
    world.cls("black")
    world.text(5, 5, "Pfeiltasten bewegen KIM", "white")
    kim.draw()


world.run(update, draw)
```

Vordefinierte Tastennamen:

```text
left right up down space enter escape
```

Buchstaben wie `a`, `w`, `s` und `d` werden ebenfalls auf die entsprechenden
Pyxel-Tastenkonstanten abgebildet. Außerhalb einer aktiven Spielschleife geben
Tastenabfragen `False` zurück.

Der API-Übergang zu Pyxel ist bewusst sichtbar:

```text
world.btn("right")  -> pyxel.btn(pyxel.KEY_RIGHT)
world.cls("black")  -> pyxel.cls(0)
world.pset(...)      -> pyxel.pset(...)
world.rect(...)      -> pyxel.rect(...)
world.text(...)      -> pyxel.text(...)
```

## `run()` und Headless-Betrieb

Signaturen:

```text
run(update=None, draw=None, *, check=None)
world.run(update=None, draw=None, *, check=None)
```

- Ohne Callbacks: aufgezeichnete Welt und Animation anzeigen.
- Mit `update`/`draw`: interaktive Pyxel-Schleife starten.
- Mit `check="kennung"`: vor dem Fenster den Trainer ausführen.
- Mit `PYKIM_HEADLESS=1`: Logik und Tests ausführen, kein Fenster öffnen.

`update` und `draw` müssen Funktionen oder `None` sein.

## Aufgaben und Trainer

Trainerdefinitionen sind YAML-Dateien. Damit müssen Autoren für reguläre
Aufgaben keine Python-Prüfdatei schreiben.

```yaml
format: 1
id: treppe-5
title: Treppe mit 5 Stufen
tests:
  - type: position
    position: [75, 75]
    hint: Prüfe die letzte Bewegung.
  - type: loop
    hint: Verwende eine for-Schleife.
optimization:
  optimal_lines: 8
```

Eine Datei darf eine einzelne Aufgabe oder eine Liste unter `exercises`
enthalten. Jede Aufgabe besitzt:

- eindeutige `id`
- angezeigten `title`
- mindestens einen Eintrag unter `tests`
- optional `optimization.optimal_lines`

Offene Aufgaben können ebenfalls eine gleichnamige Trainerdatei erhalten. Sie
verwenden statt `tests` den Modus `answer` und bleiben damit Aufgaben mit einem
lokal gespeicherten Antwortfeld:

```yaml
format: 1
id: schleifen-vergleichen
title: Schleifen vergleichen
mode: answer
```

### Zuordnungsaufgaben und Code-Scrambles

Mit `mode: matching` werden Begriffspaare als interaktive Zuordnung dargestellt:

```yaml
format: 1
id: operatoren-zuordnen
title: Operatoren zuordnen
mode: matching
pairs:
  - id: modulo
    left: "%"
    right: Rest einer Division
  - id: gleich
    left: "=="
    right: Vergleich auf Gleichheit
```

`mode: parsons` erzeugt ein Parsons-Puzzle beziehungsweise Code-Scramble. Die
Codeblöcke stehen in Lösungsreihenfolge als `@block:kennung`-Annotationen im
Aufgaben-Markdown. Die Suite blendet diese Quelle in der Aufgabenbeschreibung
aus und mischt die Blöcke für Lernende. Mit `step=N` können mehrere Blöcke
derselben Stufe in beliebiger Reihenfolge stehen:

````markdown
# Programm zusammensetzen

Ordne die beiden Codeblöcke.

@block:import step=1
```python
from pykim import *
```

@block:output step=2
```python
print("Hallo")
```
````

Beispielsweise dürfen `@block:position step=2` und `@block:paint step=2`
untereinander vertauscht werden. Sobald eine `step`-Angabe verwendet wird,
benötigt jeder Block der Aufgabe eine Stufe.

Die gleichnamige Trainerdatei enthält nur Modus und fachliche Tests:

```yaml
format: 1
id: hallo-scramble
title: Programm zusammensetzen
mode: parsons
tests:
  - type: calls
    names: [print]
```

Die Blöcke lassen sich per Drag-and-drop oder ↑/↓ anordnen. Der daraus
zusammengesetzte Code kann direkt ausgeführt werden; ein zusätzlicher
Codeeditor wird dafür nicht angezeigt.

### Gestufte Hinweise und Aufgabenquellen

Hinweise gehören in das Aufgaben-Markdown und werden mit `@hint:` verborgen.
Die Suite zeigt sie auf Wunsch nacheinander an und merkt pro Schüler und Kurs,
wie viele Hinweise bereits geöffnet wurden:

```markdown
@hint: Überlege zuerst, welcher Block das Programm vorbereitet.
@hint: Die Schleife muss vor `run(...)` stehen.
```

Optionale Quellen stehen kompakt unter der Aufgabenstellung. Mehrere
`@source`-Zeilen sind zulässig; der Link kann weggelassen werden:

```markdown
@source: CS Circles | https://cscircles.cemc.uwaterloo.ca/
@source: Eigene Erweiterung
```

Hinweise und Quellen werden nicht als Teil des sichtbaren Aufgabentextes
gerendert. Die Testhinweise in den Trainerdateien bleiben davon unabhängig und
erklären weiterhin konkret fehlgeschlagene Prüfungen.

### Unterstützte Prüftypen

| Typ | Prüft |
|---|---|
| `pixels` | erwartete Farbpositionen, Pfade, Treppen oder Schachbrett |
| `no-extra-pixels` | keine zusätzlichen gemalten Felder |
| `pixel-count` | exakte Anzahl gemalter Pixel |
| `square` | Start, Ende, Seitenlänge und geschlossener Rand |
| `position` | Endposition eines Pixels |
| `positions` | Endpositionen mehrerer Pixel |
| `pixel-names` | exakte Figurenmenge |
| `visibility` | sichtbar oder versteckt |
| `audio` | Noten, Pausen, Reihenfolge und Beats |
| `loop` | mindestens eine Schleife; optional gezielt `kind: for` oder `kind: while` |
| `nested-loop` | verschachtelte Schleifen |
| `condition` | Bedingung und optional erforderliche Aufrufe |
| `function` | eigene Funktion, optional mit Name, Parametern und `return` |
| `function-cases` | Funktionsaufrufe mit Argumenten und erwarteten Rückgabewerten |
| `calls` | geforderte Funktions- oder Methodenaufrufe |
| `parallel` | `with world.parallel():` |
| `class` | Klasse und optionale Basisklasse |
| `methods` | geforderte Methoden einer Klasse |
| `super-init` | Aufruf von `super().__init__()` |

Jeder Test kann eigene Texte für `success`, `failure` und `hint` besitzen.
Unbekannte YAML-Felder und unsichere Prüftypen werden abgewiesen.

### Optimierungsbewertung

`optimal_lines` zählt nichtleere Zeilen ohne reine Kommentare:

```text
Bewertung = min(100, optimal_lines / verwendete_Zeilen × 100)
```

Die Optimierungszahl ist ein Lernhinweis und entscheidet nicht automatisch
über die fachliche Korrektheit.

### Trainer-Hash

Jede geladene YAML-Definition erhält einen reproduzierbaren SHA-256-Hash. Vor
einer Bewertung vergleicht die Suite die lokalen Trainerdateien mit
`.pykim/trainer-hashes.json` des konfigurierten Kurs-Repositorys. Bei einer
erreichbaren Quelle werden abweichende Trainer neu synchronisiert. Offline
wird mit dem zuletzt erfolgreich synchronisierten Stand gearbeitet.

## in:si

Dieser Abschnitt beschreibt die aktuelle Anwendung. Ihre allgemeinen
Lernplattform-Funktionen bilden später den Kern von in:si; PyKIM-spezifische
Welt- und Laufzeitfunktionen wandern in das eigenständige Pythonmodul.

Start als Desktopanwendung:

```bash
insi
```

Alternativ im Browserfenster:

```bash
insi --browser
```

Die Suite bindet nur an `127.0.0.1`. Andere Geräte im Netzwerk können die
lokalen Aktionen nicht aufrufen.

### Bereiche der Suite

| Bereich | Funktion |
|---|---|
| **Setup** | Kursordner, Name, Python-Laufzeit und `.pykim-setup` |
| **Werkzeuge** | Ordner, IDE, Interpreter, Pyxel und Updates |
| **Übersicht** | Lernstand und Status der Aufgaben |
| **Aufgaben** | Aufgabenstellung, Editor, Tests, Optimierung und Dokubuch |
| **Beispiele** | mitgelieferte Programme starten, kopieren oder übernehmen |
| **Meine Projekte** | Projekte auswählen, Code bearbeiten, starten und dokumentieren |
| **Erweiterungen** | eigene Funktionen und Klassen wiederverwenden |
| **Cheatsheet** | kompakte Befehlsreferenz |
| **Skript** | Kapitelansicht mit seitlichem Inhaltsverzeichnis |
| **Pyxel** | Pyxel-Referenz, Beispiele und Übergang von PyKIM |
| **Python-Spielwiese** | normales Python mit Pyodide im Browser |

Der experimentelle Bereich **Abgabe** ist im aktuellen Schülerworkflow
ausgeblendet.

Codeblöcke im Skript können durch Autorenanweisungen gesteuert werden:

````markdown
@button:run
@button:copy
```python
print("Hallo")
```
````

`@button:run` ist nur für vollständige, freigegebene Programme vorgesehen.

## Kursordner und Setupdatei

Die Suite kann mehrere Kurse verwalten. Beim Start erscheint eine kompakte
Kursauswahl. Ein bestehender Kurs wird geöffnet oder eine Setupdatei direkt
hochgeladen. Neue Kurse aus einem Upload liegen standardmäßig unter
`~/PyKIM-Kurse/<setup-name>`; bereits bekannte Kursordner bleiben an ihrem
bisherigen Speicherort.

### Freier Kurskatalog

In der Kursauswahl zeigt **Freie Kurse entdecken** öffentlich verfügbare
Kurse wie den PyKIM-Standardkurs. Sie lassen sich ähnlich wie Pakete mit
einem Klick installieren; ein manueller Download der `.pykim-setup`-Datei ist
nicht erforderlich. Bereits installierte Kursrepositories werden erkannt.
Jeder kompakte Eintrag zeigt Niveaustufe und thematische Tags. Beim Aufklappen
erscheinen Kurzbeschreibung, Herausgeber, Repository und Installationsaktion.

Die Suite enthält eine offline verfügbare Katalogkopie und kann über
**Katalog aktualisieren** die aktuelle Registry aus dem in:si-Repository laden.
Jeder Eintrag wird mit denselben Regeln wie eine hochgeladene Setupdatei
validiert: unterstützt werden ausschließlich öffentliche GitHub-Repositories
mit sicheren Branch- und Inhaltspfaden.

Neue freie Kurse werden in
[`src/insi/course_catalog.json`](src/insi/course_catalog.json)
eingetragen. Zur normalen Setupkonfiguration kommen nur Kennung,
Kurzbeschreibung, Niveaustufe und Tags hinzu. Der Standardkurs verwendet zum
Beispiel `Python`, `Programmiergrundlagen`, `PyKIM`, `Pyxel` und `OOP`.

Der Katalog ist bereits als allgemeine Plattformfunktion angelegt. Mit der
späteren Umbenennung zu in:si soll er auch Kurse aufnehmen, die PyKIM nicht
verwenden und andere Themen oder Werkzeuge der Informatik bereitstellen.

### Portable Kursarchive und geplante Git-Quellen

Die Kursauswahl akzeptiert neben `.pykim-setup`-Dateien auch portable ZIP-
Archive. Ein solches Archiv enthält genau eine Setupdatei sowie die sichtbaren
Markdown- und Trainerdateien aus `Skripte/`, `Aufgaben/` und `Trainer/`. Ein
gemeinsamer Oberordner, wie ihn Repository-Downloads häufig verwenden, ist
zulässig. Dateien und Ordner, deren Name mit `_` beginnt, werden wie beim
Repositoryimport ignoriert.

Über **Kurs erstellen** in der Kursauswahl öffnet sich die kleine, in die Suite
integrierte **PyKIM Kurswerkstatt**. Sie legt bei Bedarf `Skripte/`, `Aufgaben/`
und `Trainer/` an. Skriptkapitel können dort vollständig als Markdown geschrieben
werden. Für PyKIM-Aufgaben erzeugt die Werkstatt Aufgaben-Markdown und eine
gekoppelte, deklarative Trainer-YAML aus sicheren Prüfbausteinen; beide Dateien
können anschließend direkt weiterbearbeitet und gemeinsam validiert gespeichert
werden.

Die Arbeitsoberfläche verwendet dabei dieselbe Grundidee wie ein geöffneter
Kurs: Eine dynamische Inhaltsliste zeigt Skripte und Aufgaben nach Lernweg, der
gewählte Titel öffnet sich im Editor und kann jederzeit in eine Vorschau
umgeschaltet werden. Die Vorschau nutzt dieselbe Markdown-Aufbereitung wie die
spätere Lernendenansicht und zeigt bei Aufgaben zusätzlich Hinweise, Quellen,
Tags und die konfigurierten automatischen Tests. Hinweise werden als wiederholte
`@hint:`-Zeilen gespeichert; Aufgabentags stehen kompakt in
`@tags: schleifen, pixel, ...`.

Diese Erweiterung des normalen Markdown heißt im Projekt **M@rkdown**. Ein
eigener Parser erkennt Annotationen und Codeblöcke, während der Validator unter
anderem unbekannte oder falsch platzierte Annotationen, ungültige Tags und
Quellen, doppelte Angaben sowie nicht geschlossene Codeblöcke mit konkreter
Zeilennummer meldet. Kurswerkstatt, Vorschau und Speichern verwenden denselben
Validator, damit fehlerhafte Autorenmetadaten nicht erst bei Lernenden auffallen.

Ein Repository ist dafür nicht erforderlich. Die Werkstatt erzeugt mit einem
Klick sowohl die Setupdatei im Kursstamm als auch ein importierbares Offline-ZIP.
Ein rein lokaler Kurs trägt keine Onlinequelle und wird nach dem ZIP-Import auch
nicht synchronisiert. Optional kann eine GitHub-Adresse eingetragen und der
vollständige Kursordner als Repository veröffentlicht werden. Liegt die
Setupdatei im Kursstamm, ist dann auch ein direkt beim Git-Hoster
heruntergeladenes Repository-ZIP als Kurs importierbar. Weitere Git-Anbieter
bleiben wie unten beschrieben eine geplante Ausbaustufe.

Ein Kurs muss dabei nicht dem vollständigen PyKIM-Standardkurs entsprechen. Er
kann ausschließlich aus Skriptkapiteln, ausschließlich aus freien Aufgaben oder
aus einer beliebigen Mischung bestehen. Freie Aufgaben erhalten in der Suite
ein speicherbares Antwortfeld und benötigen keine Trainerdatei. Nur wenn eine
Aufgabe automatisch geprüft werden soll, werden Aufgaben-Markdown und
Trainer-YAML als gekoppeltes Paar angelegt. Für den Export genügt mindestens
eine sichtbare Skript-, Aufgaben- oder Trainerdatei.

Wird ein bereits gefüllter Ordner als Kursprojekt geöffnet, kann die Werkstatt
dessen Markdown-, Text- und YAML-Dateien analysieren. Sie schlägt anhand von
Dateiformat, M@rkdown-Annotationen und Inhalt eine Zuordnung als Skript, freie
Aufgabe, Trainer oder „Ignorieren“ vor. Jede Zuordnung kann vor der Übernahme
geändert werden. Die einsortierten Kursdateien werden als Kopien angelegt; die
ursprüngliche Materialsammlung wird nicht gelöscht oder überschrieben.

Perspektivisch sollen die Bedienung der Suite und das Erstellen eigener Kurse
selbst über frei verfügbare Kurse vermittelt werden: ein Einstiegskurs für die
Suite sowie ein Kurs „Eigene Kurse erstellen“, der die Kurswerkstatt praktisch
begleitet.

Das ZIP wird vollständig lokal geprüft, gehasht und versioniert installiert.
Pfadtraversal, symbolische Links, verschlüsselte ZIP-Einträge, mehrdeutige
Groß-/Kleinschreibung, zu viele Dateien und entpackt zu große Archive werden
abgewiesen. Nach erfolgreichem Import ist kein Git-Client und keine
Internetverbindung erforderlich; beim Öffnen eines Archivkurses findet kein
Online-Abgleich statt.

Lehrkräfte erzeugen ein passendes Archiv aus einem Kursordner und dessen
Setupdatei mit:

```bash
python tools/build_course_archive.py /pfad/zum/PyKIM_Kurs \
  examples/course-setups/pykim-standardkurs.pykim-setup \
  --output pykim-standardkurs.zip
```

Existiert der reguläre Zielordner bereits, fragt die Suite, ob der Kursstand den
bestehenden Kurs aktualisieren oder als separater Kurs angelegt werden soll.
Die sichere Voreinstellung ist ein zweiter Ordner mit einer fortlaufenden
Endung wie `-2`; Schülerlösungen und Projekte werden dabei nicht überschrieben.

Damit können Lernende App, Kursarchiv und Arbeitsordner auf einem mit exFAT
formatierten USB-Stick mitnehmen und unter Windows, macOS und Linux vollständig
offline arbeiten. Als weitere Ausbaustufe sind Git-Repositories unabhängig von
Anbieter oder Hoster einschließlich selbst betriebener Git-Server vorgesehen.

### Heutige Trennung von Kursquelle und Student Workspace

Die Grundlage für sichere Kursupdates ist bereits implementiert. Geladene
Kursquellen werden nicht in den Arbeitsordner der Lernenden entpackt, sondern
commitgenau und versionsweise unter `~/.pykim/content/versions` gespeichert.
Neue Inhalte landen zunächst in einem temporären Staging-Verzeichnis, werden
dort einschließlich der Trainerdateien validiert und erst danach atomar als
aktive Kursversion markiert. Schlägt Download oder Prüfung fehl, bleibt die
zuletzt erfolgreich aktivierte Version erhalten.

Davon getrennt liegt der persönliche Student Workspace im gewählten
Kursordner. Er enthält insbesondere bearbeitete Python-Aufgaben, `Projekte/`,
`erweiterungen.py`, freie Antworten sowie Lernstand und Dokubuch unter
`.pykim/progress.json`. Beim Einrichten oder erneuten Öffnen erzeugt die Suite
nur fehlende Starterdateien; bereits vorhandene Lösungen werden erkannt und
nicht überschrieben. Auch ein Inhaltsupdate schreibt nicht in Projekte,
Erweiterungen oder den Lernstand.

Damit schützt der heutige Mechanismus bereits die Dateien der Lernenden vor
einem technischen Überschreiben. Die folgenden geplanten Regeln ergänzen diese
Trennung um die noch fehlende semantische Kompatibilität, etwa wenn ein
Kursautor Aufgaben umbenennt, entfernt oder ihre Bewertung verändert.

### Geplante Kompatibilitätsregeln für Kursupdates

Die bestehende Trennung zwischen unveränderlicher Kursquelle und persönlichem
Student Workspace soll zu einem verbindlichen Updatevertrag ausgebaut werden.
Auch künftige Kursupdates dürfen bearbeitete Aufgaben, eigene Projekte,
Erweiterungen, freie Antworten oder den Lernstand nicht überschreiben.

Für semantische Änderungen sind stabile Aufgaben-IDs, versionierte Kursformate
und gespeicherte Trainerrevisionen vorgesehen. Entfernte oder umbenannte
Aufgaben sollen vor der Aktivierung erkannt werden. Notwendige Änderungen
werden über explizite Migrationstabellen zugeordnet; bei inkompatiblen Updates
warnt die Suite und sichert den Workspace, bevor eine Migration bestätigt wird.
Bereits abgegebene Versuche sollen weiterhin mit der Trainerrevision
nachvollziehbar bleiben, unter der sie bearbeitet wurden.

Der erneute Import derselben Setupdatei ist nicht destruktiv: Repository-Inhalte
und Konfiguration werden aktualisiert, während Schülerlösungen, freie Antworten,
Projekte und Lernstand erhalten bleiben. Aus der Kursauswahl kann der Ordner im
Dateimanager geöffnet werden. Das Löschen erfordert die exakte Eingabe des
Kursnamens und verschiebt den gesamten Kursordner in den Systempapierkorb.

Der Kursordner enthält Schülerdateien und bleibt von Inhaltsupdates getrennt:

```text
PyKIM-Kurs/
├── .pykim-course.json
├── .pykim/
│   ├── course.pykim-setup
│   ├── progress.json
│   └── backups/
├── Aufgaben/
│   ├── imperativ/
│   └── oop/
├── Projekte/
└── erweiterungen.py
```

Vorhandene Lösungen werden beim erneuten Setup nicht überschrieben.
Zurückgesetzte Aufgaben und Lernstände werden vorher unter `.pykim/backups`
gesichert.

### Format der Setupdatei

```json
{
  "format": "pykim-course-setup-v1",
  "name": "pykim-standardkurs.pykim-setup",
  "teacher": "Lehrkraft",
  "school": "OSZ KIM",
  "course": "PyKIM Standardkurs",
  "repository": "https://github.com/finalnode/PyKIM_Kurs.git",
  "branch": "main",
  "scripts_path": "Skripte",
  "assignments_path": "Aufgaben",
  "trainers_path": "Trainer"
}
```

Die Datei enthält bewusst keine Schlüssel, Zertifikate oder
Verschlüsselungsdaten. Sie ist eine Konfigurationsdatei und derzeit nicht
kryptografisch authentifiziert.

### Beispielkurs direkt verwenden

Das öffentliche Repository
[finalnode/PyKIM_Kurs](https://github.com/finalnode/PyKIM_Kurs) dient als
vollständiger Beispiel- und Standardkurs. Die passende Konfiguration kann ohne
manuelles Kopieren direkt heruntergeladen und anschließend in der Kursauswahl
hochgeladen werden:

- [PyKIM Standardkurs – Setupdatei direkt herunterladen](https://raw.githubusercontent.com/finalnode/insi/main/examples/course-setups/pykim-standardkurs.pykim-setup)
- [Setupdatei im in:si-Repository ansehen](https://github.com/finalnode/insi/blob/main/examples/course-setups/pykim-standardkurs.pykim-setup)

Weitere Setupdateien können nach demselben Format unter
[`examples/course-setups`](https://github.com/finalnode/insi/tree/main/examples/course-setups)
veröffentlicht und direkt referenziert werden.

Erzeugen:

```bash
pykim-teacher setup \
  --teacher "Frau Beispiel" \
  --school "OSZ KIM" \
  --course "Python 11A" \
  --repository "https://github.com/finalnode/PyKIM_Kurs.git" \
  --branch main \
  --output ./setupdatei
```

Ohne importierte Setupdatei kann in der Startansicht ein neuer Kurs eingerichtet
werden. Skript, Aufgaben und Lernstand werden nach erfolgreicher Synchronisation
eingeblendet. Der Kursname erscheint danach im Header.

## Externes Kurs-Repository

Empfohlene Struktur:

```text
PyKIM_Kurs/
├── .pykim/
│   └── trainer-hashes.json
├── Skripte/
│   ├── imperativ/
│   └── oop/
├── Aufgaben/
│   ├── imperativ/
│   └── oop/
└── Trainer/
    └── *.yml
```

Die Suite übernimmt automatisch alle Markdown-Dateien unter `Skripte/` und
`Aufgaben/` sowie alle YAML-Dateien unter `Trainer/`. Dateien und komplette
Ordnerbäume werden ignoriert, sobald ein Pfadteil mit `_` beginnt. Die
alphabetische Pfadreihenfolge bestimmt die Anzeige. Eine Aufgabenstellung wird
automatisch prüfbar, wenn unter `Trainer/` eine Definition mit demselben
Dateistamm und `tests` liegt. Ohne passenden Trainer oder mit `mode: answer`
erscheint sie als freie Aufgabe mit einem mehrzeiligen, lokal gespeicherten
Antwortfeld.

Die Suite ermittelt zuerst den Commit des konfigurierten Branches und speichert
den vollständigen sichtbaren Stand danach versionsweise und atomar unter
`~/.pykim/content/versions`. Ein eigener aktiver Marker pro Repository und
Branch verhindert, dass zwei Kurse offline versehentlich dieselben Inhalte
verwenden.

Für Vorabstände kann eine Setupdatei beispielsweise auf den Branch `beta`
verweisen. Ein Wechsel des Branches erfolgt durch eine andere Setupdatei.

## Eigene Erweiterungen

Die Suite legt im Kursordner genau ein persönliches Modul an:

```text
erweiterungen.py
```

Schüler können dort selbst entwickelte Funktionen und Klassen speichern:

```python
def square(length):
    for _ in range(4):
        right(length)
        down(length)
```

Alle Erweiterungen importieren:

```python
from erweiterungen import *
```

Gezielt importieren:

```python
from erweiterungen import square
```

Die persönlichen Erweiterungen stehen in allen Aufgaben und eigenen Projekten
desselben Kurses zur Verfügung. Eine einmal entwickelte Funktion oder Klasse
kann dadurch in weiteren Suite-Projekten wiederverwendet werden, ohne den Code
zu kopieren. Erweiterungen sind derzeit kursbezogen: Projekte in einem anderen
Kurs verwenden dessen eigene `erweiterungen.py`.

Die Suite prüft vor dem Hinzufügen:

- gültige Python-Syntax
- mindestens eine öffentliche Funktion oder Klasse
- keine doppelten Namen
- keine Beispielaufrufe oder sonstige Ausführung auf Modulebene

Vorhandene Definitionen können einzeln bearbeitet werden. Andere Funktionen
bleiben dabei unverändert. Der Kursordner wird beim Ausführen automatisch dem
Python-Suchpfad hinzugefügt, sodass der Import auch aus Aufgaben-Unterordnern
funktioniert.

Eine alte, kurzzeitig verwendete Paketstruktur wird bei Bedarf nach
`erweiterungen_altes_paket` verschoben und nicht gelöscht.

## Eigene Projekte und Pyxel-Ressourcen

Die Suite kennt drei Projektvorlagen:

- `empty`: normales Python-Projekt
- `pykim`: PyKIM-Projekt
- `pyxel`: Pyxel-Spiel mit Ressourcen

Beispiel:

```text
Projekte/mein_spiel/
├── main.py
├── README.md
├── projekt.json
└── ressourcen.pyxres
```

`projekt.json` speichert Projektname, Typ, Einstiegspunkt und Ressourcenpfad.
Pfade werden auf den jeweiligen Projektordner begrenzt.

Die Projektansicht ist als Arbeitsbereich aufgebaut: Links wird das Projekt
ausgewählt, rechts steht ein breiter Editor zur Verfügung. Der Reiter **Code**
bietet Syntaxhervorhebung, Speichern, Kopieren sowie **Speichern und starten**.
Der Reiter **Dokumentation** bearbeitet die zugehörige `README.md` und zeigt
darunter unmittelbar die gerenderte Markdown-Vorschau. Neue Projekte erhalten
eine Reflexionsvorlage; ältere Projekte bekommen sie beim ersten Speichern.

Vor dem Speichern vergleicht die Suite den zuletzt geladenen Dateistand. Wurde
`main.py` oder `README.md` zwischenzeitlich in einer externen IDE verändert,
bricht sie das Speichern mit einem Konflikthinweis ab, statt die Änderung zu
überschreiben.

`.pyxres` enthält Pyxel-Sprites, Tilemaps, Sounds und Musik. Die Suite startet
den offiziellen Editor sinngemäß mit:

```bash
python -m pyxel edit ressourcen.pyxres
```

Ein Pyxel-Projekt wird erst gestartet, nachdem seine konfigurierte
Ressourcendatei existiert. Das Arbeitsverzeichnis ist immer der Projektordner;
dadurch funktioniert `pyxel.load("ressourcen.pyxres")` portabel.

Mitgelieferte Beispiele bleiben unverändert. Zum Bearbeiten erstellt die Suite
eine persönliche Kopie unter `Projekte/beispiele`.

## IDE und Python-Laufzeit

Die Suite erkennt unterstützte Installationen und typische Systempfade für:

- Thonny
- Visual Studio Code
- PyCharm
- eigene IDE-Pfade

Die Auswahl wird sofort lokal gespeichert. Aufgaben und Beispiele zeigen den
Namen der ausgewählten IDE im Öffnen-Button.

### VS Code

Beim Öffnen ergänzt die Suite im Kursordner:

```text
.vscode/settings.json
.vscode/extensions.json
```

Der ausgewählte Python-Interpreter wird gesetzt und die offizielle
Python-Erweiterung empfohlen. Vorhandene Einstellungen bleiben erhalten.

### Thonny

PyKIM verwendet ein eigenes Profil unter `~/.pykim/thonny`, damit persönliche
Thonny-Einstellungen nicht überschrieben werden. Kursordner und ausgewählter
Interpreter werden gemeinsam gestartet.

### Interpreter

Die Suite sucht unter anderem nach:

- dem Interpreter der laufenden App
- System-Python-Installationen
- virtuellen Umgebungen
- pyenv-Installationen
- Conda-Umgebungen
- Windows-Python-Launcher-Einträgen
- Thonnys mitgeliefertem Python
- manuell ausgewählten Programmpfaden

Ein Kandidat wird auf Python-Version, PyKIM und Pyxel untersucht. PyKIM
benötigt Python 3.10 oder neuer.

Verwaltete Umgebungen liegen unter `~/.pykim/runtimes` und werden nicht in den
portablen Kursordner geschrieben. Dadurch werden plattformspezifische Pakete
nicht versehentlich über ein Netzlaufwerk synchronisiert.

## Updates

Die Suite prüft App und Lerninhalte getrennt im Hintergrund. Ein fehlendes Netz
blockiert den Start nicht.

### App-Update

- liest das neueste GitHub-Release
- vergleicht die semantische Versionsnummer
- wählt unter macOS ein zur Architektur passendes DMG
- öffnet die Downloadseite
- ersetzt eine installierte App niemals ungefragt selbst

### Kursinhalte

- werden durch Setupdatei, Repository und Branch bestimmt
- werden commitgenau synchronisiert
- werden in einem Staging-Verzeichnis validiert
- werden erst danach atomar aktiviert
- verändern keine Schülerlösungen, Projekte oder Lernstände
- prüfen insbesondere Trainer gegen die Repository-Hashliste

Der ältere ZIP-basierte Inhaltsupdatekanal ist technisch noch vorhanden. Der
aktuelle Kursworkflow verwendet jedoch die direkte GitHub-Synchronisation.

## Sicherheit bei der Codeausführung

Pythonprogramme aus Aufgaben, Kursen und Projekten werden nicht bereits beim
Kursimport ausgeführt. Beim bewussten Start laufen sie in einem getrennten
Prozess mit bereinigter Umgebung; integrierte Aufgabenläufe begrenzen außerdem
Laufzeit und gespeicherte Ausgabe. Typische Zugangsdaten wie API- oder
GitHub-Tokens und die Verbindung zu einem SSH-Agenten werden nicht an den
Lernprozess weitergegeben.

Diese Prozessisolation ist noch **keine Betriebssystem-Sandbox**. Der gestartete
Code kann derzeit grundsätzlich mit den Rechten des angemeldeten Benutzers auf
Dateien, Netzwerk und Systemfunktionen zugreifen. Die Suite weist beim
Kursimport und im Systemcheck sichtbar darauf hin. Die geplante Runner-Architektur
soll vorhandene OS-Sandbox-Mechanismen verwenden und definierte Schreibbereiche
freigeben, sodass beispielsweise SQLite-Datenbanken innerhalb eines
Schülerprojekts möglich bleiben.

Das aktuelle Bedrohungsmodell, aktive Grenzen und ausdrücklich nicht gegebene
Garantien stehen in [SECURITY.md](SECURITY.md).

## Speicherorte und Datenschutz

### Im Kursordner

- Schülername in `.pykim-course.json`
- Aufgabenlösungen
- Projekte
- `erweiterungen.py`
- Lernstand und Dokubuch in `.pykim/progress.json`
- freie Aufgaben-Antworten in `.pykim/progress.json`
- Sicherungen unter `.pykim/backups`
- installierte Kurs-Setupdatei

### Lokal auf dem Rechner

- Suite-Konfiguration: `~/.pykim/config.json`
- synchronisierte Inhaltsversionen: `~/.pykim/content/versions`
- kursgebundene Inhaltsmarker: `~/.pykim/content/active-courses`
- verwaltete Python-Laufzeiten: `~/.pykim/runtimes`
- eigenes Thonny-Profil: `~/.pykim/thonny`

Der Kursordner darf auf einem lokalen Laufwerk, USB-Datenträger oder
eingebundenen WebDAV-Laufwerk liegen. CalDAV ist ein Kalenderprotokoll und kein
Dateisystem. Gleichzeitiges Bearbeiten desselben synchronisierten Ordners auf
mehreren Geräten kann Konflikte erzeugen; vorgesehen ist nacheinander erfolgendes
Arbeiten in Schule und Zuhause.

Die Runtime-Diagnose enthält Plattform, Interpreter, Paketstatus und
Wheelhouse-Pfad, aber keinen Quellcode und keinen Lernstand.

## Python-Spielwiese

Die Spielwiese lädt Pyodide und führt normales Python im Browserkontext aus.
Beim ersten Laden ist eine Internetverbindung erforderlich. Das lokale
PyKIM-/Pyxel-Paket steht dort nicht automatisch zur Verfügung. Ein vollständiges
browserfähiges PyKIM benötigt ein eigenes Canvas-Backend oder die offizielle
Pyxel-WASM-Laufzeit.

Der eingebettete Python-Editor hebt Schlüsselwörter, eingebaute Funktionen,
Zeichenketten, Zahlen und Kommentare hervor. `Tab` fügt vier Leerzeichen ein,
`Shift+Tab` rückt aus; das funktioniert auch für mehrere markierte Zeilen. Die
Ausführung findet in einem Web Worker statt und kann über **Stoppen** beendet
werden, ohne die Suite einzufrieren.

## Installation und Entwicklung

Voraussetzung: Python 3.10 oder neuer.

### Bibliothek installieren

```bash
python -m pip install -e .
```

### Suite installieren

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
insi
```

Unter Windows wird die Umgebung so aktiviert:

```powershell
.venv\Scripts\activate
```

### Tests

```bash
python -m pip install -e '.[test]'
pytest
```

Der reguläre Lauf prüft API, Weltlogik, Animation, Audio, Trainer,
Kursdateien, Erweiterungen, Projekte, Laufzeiten und Suite-Helfer.

NiceGUI-E2E-Test separat:

```bash
python -m pip install -e '.[test]'
pytest -m e2e
```

Manuelle Plattformtests stehen in `QUALITAETSSICHERUNG.md`.

### Architektur der Desktop-Lernumgebung

`src/insi/app.py` ist bewusst nur der Application Composer: Er verbindet
NiceGUI, den expliziten `AppContext`, den Desktop-Lebenszyklus und den
Workspace. Kursauswahl, Setup, Werkzeuge und Updates, Aufgaben, Abgabe sowie
die übrigen Ansichten liegen in getrennten `*_view.py`-Modulen. Umfangreiche
Views werden erst beim tatsächlichen App-Start importiert. Architekturtests
begrenzen die Größe von Composer und Workspace, damit neue Funktionen nicht
erneut in einer zentralen `main()` zusammenwachsen.

Die Anwendung lebt bereits im eigenen Python-Paket `insi`, während die
Pixelwelt und ihre fachlichen APIs im getrennten
[PyKIM-Repository](https://github.com/finalnode/PyKIM) bleiben. Der frühere
Suite-Namespace `pykim.guide` wurde entfernt. Die Anwendung lebt vollständig
unter `insi`; beide Projekte können unabhängig veröffentlicht werden.

### Test-Helfer

`pykim.testing` stellt bereit:

| Funktion | Zweck |
|---|---|
| `reset_world()` | gesamten Zustand zurücksetzen |
| `set_pixel_for_test(x, y, color)` | Testpixel setzen |
| `get_world_state()` | unveränderliche Weltmatrix lesen |
| `get_painted_pixels()` | alle nicht schwarzen Koordinaten lesen |
| `get_pending_tones()` | ausstehende MIDI-Noten lesen |
| `get_pending_audio_events()` | Noten und Beats lesen |

## Offline-Wheelhouse

```bash
python tools/build_wheelhouse.py
```

Das Ergebnis liegt unter `dist/wheelhouse`. Erkennt die Suite diesen Ordner,
installiert oder repariert sie PyKIM und Pyxel ohne Zugriff auf PyPI. Wheels
sind betriebssystem- und architekturabhängig und müssen auf passenden Runnern
gebaut werden.

## Desktop-Apps bauen

Die Builds sind plattformspezifisch: Ein Windows-Paket muss unter Windows,
ein Linux-Paket unter Linux und ein macOS-Paket auf der jeweiligen
Mac-Architektur erzeugt werden. Alle Buildskripte erstellen eine isolierte
Umgebung unter `build/`, bündeln die Suite mit PyInstaller und legen Ergebnisse
unter `dist/` ab.

### Windows

Unter Windows (PowerShell):

```powershell
python tools/build_desktop_app.py
python tools/package_desktop_app.py
```

Das ZIP enthält den vollständigen Ordner `insi`. Nach dem Entpacken wird
`insi.exe` gestartet. Beispiel:

```text
dist/releases/windows/insi-0.5.5-windows-x86_64.zip
```

Unter Windows gehören zwei `insi.exe`-Prozesse zum normalen nativen
Fenstermodus: einer betreibt den lokalen Server, der zweite das WebView-Fenster.
Bleibt das native Fenster auf einem Rechner unsichtbar, öffnet die Suite nach
12 Sekunden automatisch im Standardbrowser. Startdiagnosen stehen unter
`%USERPROFILE%\.pykim\logs\desktop-app-windows.log`.

### Linux

Für den nativen Fenstermodus werden GTK 3 und WebKitGTK benötigt. Unter Ubuntu
24.04 lassen sich die Build-Abhängigkeiten so installieren:

```bash
sudo apt-get update
sudo apt-get install gcc libcairo2-dev libgirepository1.0-dev pkg-config \
  python3-dev gir1.2-gtk-3.0 gir1.2-webkit2-4.1 \
  libgtk-3-dev libwebkit2gtk-4.1-dev
python tools/build_desktop_app.py
python tools/package_desktop_app.py
```

Nach dem Entpacken wird die Suite gestartet mit:

```bash
./insi/insi
```

Das Release-Archiv heißt beispielsweise:

```text
dist/releases/linux/insi-0.5.5-linux-x86_64.tar.gz
```

### macOS

Eigenständige App inklusive Python, PyKIM, Pyxel, NiceGUI und Wheelhouse:

```bash
python tools/build_macos_app.py
open 'dist/macos/insi.app'
```

Schneller Wiederholungs-Build:

```bash
python tools/build_macos_app.py --skip-wheelhouse
```

DMG mit Verknüpfung zum Programme-Ordner:

```bash
python tools/build_macos_dmg.py
```

App und DMG gemeinsam neu bauen:

```bash
python tools/build_macos_dmg.py --rebuild-app
```

Der Dateiname enthält Version und Architektur, beispielsweise:

```text
insi-0.5.5-macos-x86_64.dmg
```

Der Build muss auf derselben macOS-Architektur wie das Ziel erzeugt werden.
Intel (`x86_64`) und Apple Silicon (`arm64`) benötigen getrennte Builds. Ohne
Apple-Developer-Zertifikat wird die App nur ad hoc signiert und nicht
notarisiert.

### Schnelle Wiederholungs-Builds

`--skip-wheelhouse` verwendet das vorhandene plattformspezifische Wheelhouse.
`--skip-clean` behält PyInstallers Arbeitsverzeichnis:

```bash
python tools/build_desktop_app.py --skip-wheelhouse --skip-clean
python tools/build_macos_app.py --skip-wheelhouse --skip-clean
```

Wheelhouses und Desktop-Builds sind nicht zwischen Betriebssystemen oder
Prozessorarchitekturen austauschbar.

## GitHub Actions und Releases

Der Workflow [`.github/workflows/build-desktop.yml`](.github/workflows/build-desktop.yml)
kann in GitHub unter **Actions → Desktop-Builds → Run workflow** manuell
gestartet werden. Vor jedem Build läuft die vollständige Testsuite. Anschließend
entstehen vier getrennte Artefakte:

| Ziel | GitHub-Runner | Releaseformat |
|---|---|---|
| Windows x86_64 | `windows-2025` | `.zip` |
| Linux x86_64 | `ubuntu-24.04` | `.tar.gz` |
| macOS Intel | `macos-15-intel` | `.dmg` |
| macOS Apple Silicon | `macos-15` | `.dmg` |

Erfolgreiche Pakete werden im jeweiligen Buildordner gesammelt:

```text
dist/releases/
├── windows/
├── linux/
├── macos-x86_64/
└── macos-arm64/
```

Die Ordner werden als GitHub-Actions-Artefakte gespeichert. Bei einem
Versionstag lädt der Releasejob die enthaltenen Dateien zusätzlich dauerhaft
in das zugehörige GitHub Release. Die Binärdateien werden nicht in die
Git-Historie committed.

Jeder Build prüft den enthaltenen Python-Runner; unter Windows wird zusätzlich
kontrolliert, ob die gebaute App tatsächlich ein sichtbares Fenster erzeugt.
Erst danach wird das Artefakt hochgeladen. Ein Tag nach dem Schema `v0.5.5`
startet dieselbe Matrix und erstellt
anschließend ein GitHub Release beziehungsweise ergänzt ein bereits vorhandenes
Release um alle vier Dateien:

```bash
git tag v0.5.5
git push origin v0.5.5
```

Die Versionsnummer im Tag muss der Version in `pyproject.toml` und
den Versionsangaben von PyKIM und in:si entsprechen; der Workflow bricht bei
einer Abweichung ab.
Signierung, Apple-Notarisierung und ein
Windows-Code-Signing-Zertifikat sind bewusst noch nicht automatisiert; dafür
wären Repository-Secrets und die jeweiligen Herstellerkonten erforderlich.

## Grenzen und zurückgestellte Funktionen

- Die Setupdatei ist noch nicht signiert oder kryptografisch authentifiziert.
- Schüler- und Kurscode läuft in getrennten, begrenzten Prozessen, aber noch
  nicht in einer garantierten Betriebssystem-Sandbox für Dateisystem und
  Netzwerk.
- Der verschlüsselte Moodle-Dateiexport ist experimentell und ausgeblendet.
- Der alte Zertifikats-/Schlüsselcode ist technische Vorarbeit, nicht Teil des
  stabilen 0.5-Workflows.
- Die automatische Übernahme einer bestandenen Aufgabenfunktion nach
  `erweiterungen.py` ist noch nicht implementiert; Erweiterungen werden derzeit
  manuell hinzugefügt.
- Die Browser-Spielwiese kann normales Python, aber noch kein lokales PyKIM.
- Der Linux-Build ist ein portables PyInstaller-Archiv, kein AppImage oder
  distributionsübergreifend garantierter Installer; GTK/WebKitGTK müssen auf
  dem Zielsystem verfügbar sein.
- Windows-Code-Signing sowie macOS-Signierung und -Notarisierung sind noch offen.
- Das Projekt befindet sich im Alpha-Stadium und ist noch kein abgesicherter
  flächendeckender Schul-Rollout.

## Lizenzierung

Der aktuelle Repository-Code steht unter der MIT License; siehe `LICENSE`.
Der öffentliche Beispielkurs besitzt eine eigene Lizenzdatei im
[PyKIM_Kurs-Repository](https://github.com/finalnode/PyKIM_Kurs/blob/main/LICENSE).
Schülerlösungen und freie Antworten verbleiben in den jeweiligen lokalen
Kursordnern und werden nicht in das Inhaltsrepository übertragen.

> **Concept by human. Crafted by human + AI.**  
> Konzept und pädagogische Verantwortung: Projektverantwortliche von PyKIM  
> KI-Unterstützung: OpenAI Codex
