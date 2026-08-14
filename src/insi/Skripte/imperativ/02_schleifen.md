# Zählschleifen mit for und range

Programme enthalten häufig dieselben oder sehr ähnliche Anweisungen mehrfach. Eine Schleife beschreibt die Wiederholung einmal und legt fest, wie oft sie ausgeführt wird.

## Wiederholung ohne Schleife

@button:run
@button:copy
```python
from pykim import *

set_position(60, 40)
speed(15)
paint("purple")

right(4)
down(4)
right(4)
down(4)
right(4)
down(4)

run()
```

Der Code funktioniert, ist aber schwer zu verändern. Mit einer Schleife wird die Struktur sichtbar:

@button:run
@button:copy
```python
from pykim import *

set_position(60, 40)
speed(15)
paint("purple")

for durchlauf in range(3):
    right(4)
    down(4)

run()
```

## Aufbau einer for-Schleife

@button:copy
```python
for durchlauf in range(3):
    right(4)
    down(4)
```

- `for` beginnt die Zählschleife.
- `durchlauf` ist die Schleifenvariable.
- `in` verbindet die Variable mit der Zahlenfolge.
- `range(3)` erzeugt die Werte `0`, `1` und `2`.
- Der Doppelpunkt `:` beginnt den Schleifenblock.
- Alle eingerückten Zeilen gehören zur Schleife.

Python verwendet Einrückungen als Teil der Sprache. Üblich sind vier Leerzeichen.

## Die Schleifenvariable beobachten

@button:run
@button:copy
```python
for durchlauf in range(4):
    print(durchlauf)
```

Ausgabe:

```text
0
1
2
3
```

Die Obergrenze gehört nicht mehr zur Folge. `range(4)` liefert also vier Werte, endet aber vor `4`.

Wird die Variable nicht gebraucht, verwendet man häufig `_`:

@button:copy
```python
for _ in range(4):
    paint("cyan")
    paint_stop()
    right()
```

## Die drei Formen von range

### Nur eine Obergrenze

@button:run
@button:copy
```python
for zahl in range(5):
    print(zahl)
```

Erzeugt `0, 1, 2, 3, 4`.

### Start und Obergrenze

@button:run
@button:copy
```python
for zahl in range(2, 6):
    print(zahl)
```

Erzeugt `2, 3, 4, 5`.

### Start, Obergrenze und Schrittweite

@button:run
@button:copy
```python
for zahl in range(2, 11, 2):
    print(zahl)
```

Erzeugt `2, 4, 6, 8, 10`.

Auch rückwärts gerichtete Folgen sind möglich:

@button:run
@button:copy
```python
for zahl in range(5, 0, -1):
    print(zahl)
```

Erzeugt `5, 4, 3, 2, 1`.

## Ein Quadrat als Schleife

Da PyKIM nicht mit Winkeln arbeitet, besteht ein achsenparalleles Quadrat aus vier unterschiedlichen Bewegungsrichtungen:

@button:run
@button:copy
```python
from pykim import *

set_position(20, 20)
paint("purple")

right(5)
down(5)
left(5)
up(5)

paint_stop()
run()
```

Eine Schleife eignet sich besonders, wenn sich eine ganze Struktur wiederholt, etwa bei mehreren Quadraten oder Stufen:

@button:run
@button:copy
```python
from pykim import *

set_position(20, 20)

for _ in range(4):
    paint("orange")
    right(5)
    down(5)
    left(5)
    up(5)
    paint_stop()
    right(6)

run()
```

## Verschachtelte Schleifen

Eine Schleife kann eine weitere Schleife enthalten:

@button:run
@button:copy
```python
from pykim import *

start_x = 20
start_y = 20

for zeile in range(4):
    for spalte in range(6):
        set_position(start_x + spalte, start_y + zeile)
        paint("lime")

run()
```

Die innere Schleife läuft für jede einzelne Wiederholung der äußeren Schleife vollständig durch. Im Beispiel werden `4 * 6 = 24` Felder gemalt.

## Typische Fehler

### Doppelpunkt vergessen

```text
for zahl in range(5)
    print(zahl)
```

Python meldet einen `SyntaxError`.

### Nicht oder falsch eingerückt

```text
for _ in range(4):
right(5)
```

Der Schleifenblock muss eingerückt sein. Unterschiedlich gemischte Einrückungen können einen `IndentationError` auslösen.

### Falsche Obergrenze

`range(1, 5)` enthält `1, 2, 3, 4`, aber nicht `5`.

### Zu viel in der Schleife

@button:copy
```python
for _ in range(4):
    right(5)
    run()
```

`run()` gehört gewöhnlich ans Ende des gesamten Zeichenprogramms, nicht in die Schleife.

## Übungen

1. Gib mit `range()` die Zahlen 0 bis 9 aus.
2. Gib die geraden Zahlen von 2 bis 20 aus.
3. Erzeuge einen Countdown von 10 bis 1.
4. Zeichne eine Punktlinie aus zehn Punkten mit jeweils einem freien Feld dazwischen.
5. Zeichne eine Treppe aus fünf gleich großen Stufen.
6. Zeichne mit zwei verschachtelten Schleifen ein Rechteck aus 8 mal 5 einzelnen Pixeln.
7. Verändere die Rechteckaufgabe so, dass nur der Rand gemalt wird.

## Merksatz

Eine `for`-Schleife eignet sich, wenn die Anzahl oder Folge der Wiederholungen bekannt ist. `range()` endet immer vor seiner Obergrenze.
