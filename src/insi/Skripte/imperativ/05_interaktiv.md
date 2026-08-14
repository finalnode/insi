# Interaktive Programme: update, draw und Eingaben

Bisher liefen Programme einmal von oben nach unten und zeigten danach ihr Ergebnis. Ein interaktives Programm reagiert fortlaufend auf Tastendrücke und verändert sein Bild. PyKIM verwendet dafür dasselbe Grundmodell wie Pyxel.

## Die Spielschleife

@button:copy
```python
def update():
    pass

def draw():
    pass

world.run(update, draw)
```

Die Welt wiederholt intern diese Schritte:

1. Eingaben und Ereignisse erfassen
2. `update()` aufrufen
3. `draw()` aufrufen
4. Bild anzeigen
5. beim nächsten Frame wieder von vorn beginnen

Eine eigene `while True`-Schleife ist nicht nötig und würde die Ereignisverarbeitung blockieren.

## Zustand außerhalb der Funktionen

@button:copy
```python
from pykim import *

spieler_x = 20
spieler_y = 20

def update():
    pass

def draw():
    world.cls("black")
    world.pset(spieler_x, spieler_y, "white")

world.run(update, draw)
```

Die Variablen speichern den Zustand zwischen zwei Frames. Lokale Variablen würden bei jedem Funktionsaufruf neu entstehen.

## Tastatur abfragen

@button:run
@button:copy
```python
from pykim import *

spieler_x = 20
spieler_y = 20

def update():
    global spieler_x, spieler_y

    if world.btn("left"):
        spieler_x -= 1
    if world.btn("right"):
        spieler_x += 1
    if world.btn("up"):
        spieler_y -= 1
    if world.btn("down"):
        spieler_y += 1

def draw():
    world.cls("black")
    world.pset(spieler_x, spieler_y, "yellow")

world.run(update, draw)
```

`world.btn(taste)` ist wahr, solange die Taste gehalten wird. `global` zeigt an, dass die außerhalb der Funktion angelegten Variablen verändert werden.

## Gedrückt, gehalten oder losgelassen

- `world.btn("space")`: wahr, solange die Taste gehalten wird
- `world.btnp("space")`: wahr beim Drücken
- `world.btnr("space")`: wahr beim Loslassen

Für eine Bewegung ist `btn()` häufig passend. Ein einzelner Schuss oder ein Menüwechsel sollte meist mit `btnp()` ausgelöst werden.

@button:run
@button:copy
```python
def update():
    if world.btnp("space"):
        print("Einmal ausgelöst")
```

## Grenzen einhalten

@button:copy
```python
def update():
    global spieler_x, spieler_y

    if world.btn("left") and spieler_x > 0:
        spieler_x -= 1
    if world.btn("right") and spieler_x < world.width - 1:
        spieler_x += 1
    if world.btn("up") and spieler_y > 0:
        spieler_y -= 1
    if world.btn("down") and spieler_y < world.height - 1:
        spieler_y += 1
```

Alternativ kann ein berechneter Wert begrenzt werden:

@button:copy
```python
spieler_x = max(0, min(world.width - 1, spieler_x))
```

## Warum draw immer neu zeichnet

@button:copy
```python
def draw():
    world.cls("black")
    world.pset(spieler_x, spieler_y, "yellow")
```

`world.cls()` löscht das vorherige Bild. Danach wird der aktuelle Zustand vollständig dargestellt. Ohne Löschen blieben alte Positionen als Spur sichtbar.

Die Trennung lautet:

- `update()` verändert Zustand und Regeln.
- `draw()` liest Zustand und zeichnet ihn.

Spielregeln sollten nicht von `draw()` abhängen. Dann können sie leichter getestet werden.

## Mit einem Pixelobjekt

@button:run
@button:copy
```python
from pykim import *

def update():
    if world.btn("right"):
        kim.right()
    if world.btn("left"):
        kim.left()

def draw():
    world.cls("black")
    kim.draw()

world.run(update, draw)
```

Das Objekt `kim` speichert seine Position selbst. Dadurch entfallen separate Variablen wie `spieler_x` und `spieler_y`.

## Zustände eines Spiels

Ein Spiel kann sich beispielsweise im Menü, im laufenden Spiel oder am Ende befinden:

@button:copy
```python
spielzustand = "menu"

def update():
    global spielzustand

    if spielzustand == "menu" and world.btnp("space"):
        spielzustand = "spiel"
    elif spielzustand == "spiel" and world.btnp("escape"):
        spielzustand = "menu"

def draw():
    world.cls("black")

    if spielzustand == "menu":
        world.text(10, 10, "Leertaste: Start", "white")
    elif spielzustand == "spiel":
        kim.draw()
```

Eine Zustandsvariable verhindert, dass alle Programmteile gleichzeitig aktiv sind.

## Zeit und Frames

Die Spielschleife läuft mehrfach pro Sekunde. Zeitabhängige Abläufe können zunächst mit einem Framezähler modelliert werden:

@button:run
@button:copy
```python
frames = 0

def update():
    global frames
    frames += 1

    if frames == 60:
        print("Ungefähr eine Sekunde bei 60 FPS")
```

Für genaue Pyxel-Projekte stehen später `pyxel.frame_count` und eine festgelegte Bildrate zur Verfügung.

## Typische Fehler

### `global` fehlt

Wird einer äußeren Zahl innerhalb von `update()` ein neuer Wert zugewiesen, benötigt die einfache imperative Variante `global`.

### Funktionsaufrufe statt Funktionen übergeben

```text
world.run(update(), draw())
```

Das ruft beide Funktionen sofort auf. Richtig ist `world.run(update, draw)`.

### Endlosschleife in update

`while True` verhindert den nächsten Frame und lässt das Fenster einfrieren.

### Zeichnen in update

Das kann zu schwer nachvollziehbaren Bildern führen. Halte Veränderungen und Darstellung getrennt.

### Eine Aktion feuert ständig

Für einmalige Aktionen wurde `btn()` statt `btnp()` verwendet.

## Übungen

1. Bewege einen Punkt mit den Pfeiltasten.
2. Verhindere, dass er die Welt verlässt.
3. Wechsle mit der Leertaste einmalig seine Farbe.
4. Ergänze die Zustände `menu`, `spiel` und `game_over`.
5. Zähle Frames und lasse alle 30 Frames einen neuen Punkt erscheinen.
6. Steuere `kim` als Objekt und zeichne ihn ausschließlich in `draw()`.
7. Übertrage das Programm anschließend auf die entsprechenden Pyxel-Funktionen.

## Merksatz

Interaktive Programme trennen Zustand, Aktualisierung und Darstellung. `world.run(update, draw)` übernimmt die Ereignis- und Spielschleife.
