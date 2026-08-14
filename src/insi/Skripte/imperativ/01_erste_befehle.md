# Erste Schritte mit PyKIM

In diesem Kapitel lernst du, wie ein Python-Programm aufgebaut ist, wie KIM in seiner Pixelwelt bewegt wird und wie dabei Zeichnungen entstehen. Du brauchst dafür keine Vorkenntnisse.

## Ein erstes Programm

@button:run
@button:copy
```python
from pykim import *

right(10)
down(5)

run()
```

Das Programm wird von oben nach unten ausgeführt:

1. `from pykim import *` stellt die Befehle von PyKIM bereit.
2. `right(10)` bewegt KIM zehn Pixel nach rechts.
3. `down(5)` bewegt KIM fünf Pixel nach unten.
4. `run()` öffnet die Pixelwelt und zeigt das Ergebnis.

Jede Anweisung steht normalerweise in einer eigenen Zeile. Python unterscheidet Groß- und Kleinschreibung: `right()` funktioniert, `Right()` ist ein anderer Name und deshalb unbekannt.

## Das Koordinatensystem

KIM startet ohne weitere Einstellungen bei `(0, 0)`. Der erste Wert ist die x-Koordinate, der zweite die y-Koordinate.

- x wird größer, wenn KIM nach rechts geht.
- x wird kleiner, wenn KIM nach links geht.
- y wird größer, wenn KIM nach unten geht.
- y wird kleiner, wenn KIM nach oben geht.

Das unterscheidet sich vom Koordinatensystem aus dem Mathematikunterricht. Es entspricht der Darstellung auf Bildschirmen, deren linke obere Ecke der Ursprung ist.

@button:run
@button:copy
```python
from pykim import *

set_position(20, 15)
right(8)
down(4)

print(get_x())  # 28
print(get_y())  # 19
run()
```

Mit `set_position(x, y)` setzt du KIM direkt auf eine Position. `get_x()` und `get_y()` liefern die aktuelle Position.

## Bewegen und zeichnen

Eine Bewegung zeichnet nicht automatisch. Mit `paint()` schaltest du die Spur ein und mit `paint_stop()` wieder aus.

@button:run
@button:copy
```python
from pykim import *

set_position(20, 20)
paint("purple")
right(10)
down(5)
paint_stop()
right(3)

run()
```

`paint("orange")` färbt sofort das aktuelle Feld und schaltet die Spur ein.
Mit einem direkt folgenden `paint_stop()` bleibt es bei genau diesem Feld:

@button:run
@button:copy
```python
from pykim import *

set_position(10, 10)
paint("orange")
paint_stop()
right(2)
paint("cyan")
paint_stop()

run()
```

## Argumente und Standardwerte

Der Wert in den runden Klammern heißt **Argument**. Er beeinflusst den Befehl.

@button:copy
```python
right(5)
down(12)
paint("red")
paint_stop()
```

Bei den Bewegungsbefehlen ist das Argument freiwillig. Ohne Angabe bewegt sich KIM einen Pixel:

@button:copy
```python
right()   # entspricht right(1)
down()    # entspricht down(1)
```

Die Klammern gehören auch dann zum Funktionsaufruf, wenn kein Argument übergeben wird.

## Kommentare

Alles hinter `#` ist ein Kommentar und wird von Python nicht ausgeführt. Kommentare erklären eine Absicht, nicht jede offensichtliche Codezeile.

@button:run
@button:copy
```python
from pykim import *

# Startpunkt der Zeichnung
set_position(30, 20)

paint("yellow")
right(12)  # obere Kante
paint_stop()

run()
```

## Typische Fehler

### Klammern vergessen

```text
right
```

Hier wird die Funktion nicht aufgerufen. Richtig ist `right()` oder beispielsweise `right(5)`.

### Text ohne Anführungszeichen

```text
paint(purple)
```

Python sucht dabei nach einer Variable namens `purple`. Ein Farbname ist ein Text und benötigt Anführungszeichen: `paint("purple")`.

### `run()` fehlt

Ohne `run()` wird die vorbereitete Welt in einem normalen PyKIM-Zeichenprogramm nicht angezeigt.

### Position außerhalb der Welt

Wenn KIM am Rand weiterläuft, kann die Position ungültig werden. Später lernst du, Bewegungen mit Bedingungen abzusichern.

## Übungen

1. Setze KIM auf `(20, 20)` und male eine zehn Pixel lange rote Linie nach rechts.
2. Zeichne einen Weg aus fünf Pixeln nach rechts und fünf Pixeln nach unten.
3. Zeichne zwei getrennte Linien, ohne den Zwischenraum zu färben.
4. Male an den Positionen `(10, 10)`, `(20, 10)` und `(30, 10)` drei verschiedenfarbige Punkte.
5. Sage vor dem Start voraus, an welcher Position KIM nach deinem Programm endet. Prüfe die Vorhersage mit `get_x()` und `get_y()`.

## Merksatz

Ein Programm ist eine eindeutige Folge von Anweisungen. Position, Farbe und Malzustand bilden zusammen den aktuellen Zustand von KIM.
