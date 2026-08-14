# Welt, Anzeigen und der Übergang zu Pyxel

Bei Turtle werden Zeichenfigur und Fenster häufig über dieselbe Bibliothek gesteuert. PyKIM trennt deutlicher: Pixel bewegen sich in einer `world`, während die Welt Fenstergröße, Hintergrund, Eingaben und direkte Zeichenoperationen verwaltet.

## Größe der Welt

@button:copy
```python
from pykim import *

print(world.width)
print(world.height)
```

Gültige ganzzahlige x-Koordinaten reichen von `0` bis `world.width - 1`, y-Koordinaten von `0` bis `world.height - 1`.

@button:copy
```python
def ist_gueltige_position(x, y):
    return 0 <= x < world.width and 0 <= y < world.height
```

Diese Prüfung sollte vor einem Zugriff auf Leveldaten oder einer Bewegung erfolgen.

## Hintergrund löschen

@button:copy
```python
world.cls("black")
```

`cls` bedeutet „clear screen“. In einer `draw()`-Funktion wird der vorherige Frame gewöhnlich zuerst gelöscht und danach vollständig neu gezeichnet.

## Einzelne Pixel und Rechtecke

@button:copy
```python
world.pset(20, 20, "yellow")
world.rect(30, 20, 12, 6, "green")
```

- `pset(x, y, farbe)` setzt genau einen Bildpunkt.
- `rect(x, y, breite, hoehe, farbe)` zeichnet ein Rechteck.

Diese Funktionen zeichnen direkt in die aktuelle Darstellung. Sie verändern nicht automatisch die Position von KIM.

## Text und Statusanzeigen

@button:copy
```python
punkte = 25
leben = 3

def draw():
    world.cls("black")
    world.text(5, 5, f"Punkte: {punkte}", "white")
    world.text(5, 13, f"Leben: {leben}", "red")
```

Eine Statusanzeige wird in jedem Frame aus dem aktuellen Zustand neu erzeugt. Dadurch muss alter Text nicht einzeln entfernt werden.

## Ein einfaches Scoreboard

@button:run
@button:copy
```python
from pykim import *

punkte = 0

def update():
    global punkte
    if world.btnp("space"):
        punkte += 10

def draw():
    world.cls("navy")
    world.text(8, 8, "Leertaste: +10", "white")
    world.text(8, 18, f"Punkte: {punkte}", "yellow")

world.run(update, draw)
```

Die Eingabe verändert `punkte` in `update()`. `draw()` stellt den neuen Wert dar.

## Schaltflächen selbst modellieren

Eine grafische Schaltfläche besteht zunächst aus einem Rechteck, Text und einer Bedingung für Eingaben. PyKIM konzentriert sich auf Tastatursteuerung; Mausposition und Mausklicks werden später direkt mit Pyxel umgesetzt.

@button:copy
```python
def zeichne_startknopf():
    world.rect(40, 40, 60, 18, "orange")
    world.text(50, 46, "START", "black")
```

Bis zur Maussteuerung kann beispielsweise die Leertaste die Aktion auslösen. So bleiben Darstellung und Aktion bereits getrennt.

## Zeitsteuerung über Frames

Die Welt zählt dargestellte Frames:

@button:run
@button:copy
```python
def update():
    if world.frame_count % 60 == 0:
        print("60 weitere Frames")
```

Ein Countdown kann aus einem Startwert und der Bildrate berechnet werden. Für Unterrichtsprogramme genügt häufig ein eigener Zähler:

@button:copy
```python
verbleibende_frames = 60 * 10

def update():
    global verbleibende_frames
    if verbleibende_frames > 0:
        verbleibende_frames -= 1

def draw():
    sekunden = verbleibende_frames // 60
    world.text(5, 5, f"Zeit: {sekunden}", "white")
```

Zeitlogik gehört in `update()`, die Anzeige in `draw()`.

## PyKIM und Pyxel im Vergleich

PyKIM bereitet die zentralen Begriffe von Pyxel vor:

| PyKIM | Pyxel |
|---|---|
| `world.cls("black")` | `pyxel.cls(0)` |
| `world.pset(x, y, "white")` | `pyxel.pset(x, y, 7)` |
| `world.rect(...)` | `pyxel.rect(...)` |
| `world.text(...)` | `pyxel.text(...)` |
| `world.btn("right")` | `pyxel.btn(pyxel.KEY_RIGHT)` |
| `world.btnp("space")` | `pyxel.btnp(pyxel.KEY_SPACE)` |
| `world.run(update, draw)` | `pyxel.run(update, draw)` |

Der wesentliche Aufbau bleibt gleich. Pyxel ergänzt unter anderem Sprites, Tilemaps, Mausabfragen, mehrere Soundkanäle und Ressourcendateien.

## Ein entsprechendes Pyxel-Grundgerüst

@button:run
@button:copy
```python
import pyxel

x = 20
y = 20

def update():
    global x
    if pyxel.btn(pyxel.KEY_RIGHT):
        x += 1

def draw():
    pyxel.cls(0)
    pyxel.pset(x, y, 7)
    pyxel.text(5, 5, "Mein erstes Pyxel-Programm", 10)

pyxel.init(160, 120, title="Mein Spiel")
pyxel.run(update, draw)
```

## Sprites und Ressourcen

Ein Sprite ist eine kleine Pixelgrafik in einer Bildbank. Pyxel verwaltet Bildbanken, Tilemaps, Sounds und Musik gemeinsam in einer `.pyxres`-Datei.

Der Pyxel-Editor wird über den Werkzeugbereich der Suite gestartet. Ein typischer späterer Zeichenaufruf lautet:

@button:copy
```python
pyxel.blt(x, y, bildbank, u, v, breite, hoehe, transparente_farbe)
```

- `x`, `y`: Position auf dem Bildschirm
- `bildbank`: Nummer der Image Bank
- `u`, `v`: Position des Sprites in der Bildbank
- `breite`, `hoehe`: Größe des Ausschnitts
- `transparente_farbe`: nicht gezeichnete Hintergrundfarbe

## Tilemaps

Eine Tilemap setzt eine Welt aus wiederverwendbaren Bildkacheln zusammen. Das entspricht konzeptionell der zweidimensionalen Liste aus dem vorherigen Kapitel:

- Liste beziehungsweise Tilemap speichert Feldtypen.
- Bildbank enthält die grafischen Kacheln.
- Spielregeln prüfen die Feldtypen.
- Darstellung zeichnet den passenden Ausschnitt.

## Typische Fehler

### Pixelzustand und Bildschirmzeichnung verwechseln

`world.pset()` bewegt KIM nicht. `kim.right()` zeichnet ohne aktivierte Spur nicht automatisch einen Punkt in der direkten Anzeige.

### Anzeige nur einmal zeichnen

In einem interaktiven Programm wird das Bild regelmäßig gelöscht. Dauerhaft sichtbare Elemente müssen in `draw()` erneut gezeichnet werden.

### Logik in draw verändern

Wenn `draw()` Punkte erhöht oder Figuren bewegt, hängt das Spielverhalten von der Darstellung ab. Verändere Zustand in `update()`.

### PyKIM- und Pyxel-Farben verwechseln

PyKIM akzeptiert verständliche Farbnamen. Pyxel verwendet normalerweise Palettennummern.

## Übungen

1. Zeichne direkt mit `world.pset()` ein 5-mal-5-Muster.
2. Erstelle mit `world.rect()` einen farbigen Rahmen.
3. Zeige Punktestand und verbleibende Leben an.
4. Baue einen Countdown über Frames.
5. Übertrage eine PyKIM-Tastatursteuerung auf die entsprechenden Pyxel-Befehle.
6. Entwirf auf Papier eine kleine Sprite-Bildbank und notiere die benötigten `u`-/`v`-Positionen.
7. Erkläre die Verbindung zwischen zweidimensionaler Liste und Tilemap.

## Merksatz

Die Welt verwaltet Anzeige und Eingabe, Pixel verwalten ihren eigenen Zustand. `update()` verändert die Welt, `draw()` stellt sie dar – in PyKIM ebenso wie später in Pyxel.
