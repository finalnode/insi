"""Erste Inhalte des lokalen Begleithefts."""

CHEATSHEET = r"""
# PyKIM-Cheatsheet

## Bewegung und Position

```python
set_position(20, 20)
get_x()
get_y()
get_position()
up()       # Standardschritt: 1
down(5)
left(3)
right(10)
```

## Farben und Malen

```python
paint("purple")            # aktuellen Pixel färben, Spur beginnen
right(10)
paint_stop()               # Spur beenden
paint("orange")            # genau ein Pixel: sofort wieder stoppen
paint_stop()
get_color()                # Farbe unter KIM
get_color("right")         # Farbe rechts von KIM
```

Farben: `black`, `navy`, `purple`, `green`, `brown`, `dark_blue`,
`light_blue`, `white`, `red`, `orange`, `yellow`, `lime`, `cyan`, `gray`,
`pink`, `peach`.

## Töne

```python
play_tone("C4")
play_tone("G4", beats=2)
play_pause()
```

## Mehrere Pixel

```python
mia = world.new_pixel("MIA", 20, 30)
mia.paint("orange")
mia.right(10)

with world.parallel():
    kim.right(10)
    mia.left(10)
```

## Interaktiver Modus

```python
def update():
    if world.btn("right"):
        kim.right()

def draw():
    world.cls("black")
    kim.draw()

world.run(update, draw)
```
"""

SCRIPT = r"""
# PyKIM-Dokubuch

## 1. Von Befehlen zu Programmen

Ein Programm ist zunächst eine Folge eindeutiger Anweisungen. KIM startet bei
`(0, 0)`. Die x-Koordinate wächst nach rechts, die y-Koordinate nach unten.

```python
from pykim import *

set_position(20, 20)
paint("purple")
right(10)
down(5)
run()
```

## 2. Wiederholungen

Schleifen ersetzen wiederholten Code:

```python
for _ in range(5):
    right(5)
    down(5)
```

## 3. Entscheidungen

Mit einer Bedingung reagiert das Programm auf seine Welt:

```python
if get_color() == "red":
    play_tone("C4")
else:
    play_pause()
```

## 4. Funktionen

Eine Funktion gibt einer Teilaufgabe einen Namen:

```python
def zeichne_quadrat():
    for _ in range(4):
        right(5)
        down(5)
```

## 5. Objekte und eigene Klassen

Mehrere Pixel besitzen jeweils eigenen Zustand. Mit Vererbung entsteht eigenes
Verhalten:

```python
class MusikPixel(Pixel):
    def __init__(self, pixel_world, name, x, y, note):
        super().__init__(pixel_world, name, x, y)
        self.note = note

    def update(self):
        if self.world.btnp("space"):
            self.play_tone(self.note)
```

## 6. Der Übergang zu Pyxel

PyKIM bereitet die Spielschleife bereits vor:

| PyKIM | Pyxel |
|---|---|
| `world.btn("right")` | `pyxel.btn(pyxel.KEY_RIGHT)` |
| `world.cls("black")` | `pyxel.cls(0)` |
| `world.pset(...)` | `pyxel.pset(...)` |
| `world.run(update, draw)` | `pyxel.run(update, draw)` |

In beiden Fällen verändert `update()` den Zustand und `draw()` zeichnet das
aktuelle Bild. Sprites, Tilemaps und mehrere Soundkanäle kommen anschließend
als neue Pyxel-Werkzeuge hinzu.
"""

PYXEL_REFERENCE = r"""
# Pyxel-Kurzreferenz

```python
import pyxel

x, y = 20, 20

def update():
    global x
    if pyxel.btn(pyxel.KEY_RIGHT):
        x += 1

def draw():
    pyxel.cls(0)
    pyxel.pset(x, y, 7)

pyxel.init(160, 120, title="Mein Spiel")
pyxel.run(update, draw)
```

Wichtige Bereiche der Pyxel-API:

- Eingabe: `btn`, `btnp`, `btnr`
- Grafik: `pset`, `line`, `rect`, `circ`, `text`, `blt`
- Ressourcen: `load`, Bildbanken und Tilemaps
- Audio: `sound`, `music`, `play`, `stop`

Die vollständige, jeweils aktuelle Referenz steht in der
[offiziellen Pyxel-Dokumentation](https://github.com/kitao/pyxel).
"""

PYODIDE_PLAYGROUND = r"""
<div class="pykim-playground">
  <p id="pyodide-status"><strong>Python wird erst beim Ausführen geladen.</strong></p>
  <div class="pykim-playground-editor">
    <pre id="pyodide-highlight" aria-hidden="true"><code></code></pre>
    <textarea id="pyodide-code" aria-label="Python-Code" spellcheck="false"
      autocapitalize="off" autocomplete="off"
      oninput="window.syncPyKIMBrowserEditor()"
      onscroll="window.syncPyKIMBrowserEditorScroll()"
      onkeydown="return window.handlePyKIMBrowserEditorKey(event)">for zahl in range(1, 6):
    print(zahl, zahl * zahl)</textarea>
  </div>
  <div style="margin: .75rem 0">
    <button class="pykim-run-button" onclick="window.runPyKIMPython()">▶ Ausführen</button>
    <button class="pykim-clear-button" onclick="window.stopPyKIMBrowserPython()">■ Stoppen</button>
    <button class="pykim-clear-button" onclick="window.resetPyKIMBrowserExample()">Beispiel laden</button>
    <button class="pykim-clear-button" onclick="document.getElementById('pyodide-output').textContent = ''">Ausgabe leeren</button>
  </div>
  <pre id="pyodide-output">Bereit.</pre>
</div>
"""
