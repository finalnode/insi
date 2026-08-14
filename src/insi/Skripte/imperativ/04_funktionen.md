# Parameterlose Funktionen

Eine Funktion fasst mehrere Anweisungen unter einem Namen zusammen. Dadurch wird eine Teilaufgabe wiederverwendbar und das Hauptprogramm leichter lesbar.

## Warum Funktionen?

Ohne Funktion müsste ein Quadrat bei jeder Verwendung erneut ausgeschrieben werden:

@button:run
@button:copy
```python
from pykim import *

paint("purple")
right(5)
down(5)
left(5)
up(5)
paint_stop()

right(8)

paint("purple")
right(5)
down(5)
left(5)
up(5)
paint_stop()

run()
```

Eine Funktion beschreibt das Quadrat einmal:

@button:run
@button:copy
```python
from pykim import *

def zeichne_quadrat():
    paint("purple")
    right(5)
    down(5)
    left(5)
    up(5)
    paint_stop()

zeichne_quadrat()
right(8)
zeichne_quadrat()

run()
```

## Definition und Aufruf

@button:copy
```python
def zeichne_quadrat():
    paint("purple")
    right(5)
    down(5)
    left(5)
    up(5)
    paint_stop()
```

- `def` beginnt eine Funktionsdefinition.
- `zeichne_quadrat` ist der Funktionsname.
- Die Klammern sind hier leer, weil es noch keine Parameter gibt.
- Der Doppelpunkt beginnt den Funktionskörper.
- Die eingerückten Anweisungen gehören zur Funktion.

Durch die Definition allein wird noch nichts gezeichnet. Erst der Aufruf führt den Funktionskörper aus:

@button:copy
```python
zeichne_quadrat()
```

## Reihenfolge im Programm

Python muss die Definition ausgeführt haben, bevor die Funktion aufgerufen wird:

@button:copy
```python
def male_punkt():
    paint("orange")
    paint_stop()

male_punkt()
```

Ein Aufruf oberhalb der Definition würde zu einem `NameError` führen.

## Funktionen und Schleifen kombinieren

@button:run
@button:copy
```python
from pykim import *

def zeichne_kreuz():
    paint("cyan")
    paint_stop()
    right()
    paint("cyan")
    paint_stop()
    left(2)
    paint("cyan")
    paint_stop()
    right()
    up()
    paint("cyan")
    paint_stop()
    down(2)
    paint("cyan")
    paint_stop()
    up()

set_position(20, 20)

for _ in range(5):
    zeichne_kreuz()
    right(4)

run()
```

Die Funktion beschreibt **was** ein Kreuz ist. Die Schleife beschreibt **wie oft** und die Bewegung im Hauptprogramm **wo** es erscheint.

## Hauptprogramm und Teilaufgaben

Ein übersichtliches Programm liest sich fast wie eine Arbeitsanweisung:

@button:run
@button:copy
```python
from pykim import *

def vorbereiten():
    set_position(20, 20)
    speed(70)

def zeichnen():
    for _ in range(4):
        paint("yellow")
        paint_stop()
        right(3)

vorbereiten()
zeichnen()
run()
```

Funktionen sollten möglichst eine klar benennbare Aufgabe erledigen. Ein Name wie `mache_etwas()` erklärt wenig; `zeichne_punktlinie()` beschreibt die Absicht.

## Lokale Variablen

Eine Variable, die innerhalb einer Funktion angelegt wird, ist normalerweise nur dort verfügbar:

@button:run
@button:copy
```python
def berechne_laenge():
    laenge = 5
    print(laenge)

berechne_laenge()
```

Außerhalb der Funktion ist `laenge` nicht definiert. Diese Begrenzung verhindert, dass sich unabhängige Programmteile versehentlich gegenseitig verändern.

## Typische Fehler

### Funktion nicht aufgerufen

`zeichne_quadrat` bezeichnet die Funktion. `zeichne_quadrat()` ruft sie auf.

### Aufruf innerhalb der eigenen Funktion

```text
def zeichne_quadrat():
    zeichne_quadrat()
```

Das ist eine Rekursion ohne Abbruchbedingung und endet mit einem `RecursionError`.

### Falsche Einrückung

Nur eingerückte Anweisungen gehören zur Funktion. Eine versehentlich nicht eingerückte Zeile wird sofort beim Definieren des Programms ausgeführt oder verursacht einen Fehler.

### Zu große Funktion

Wenn eine Funktion viele unterschiedliche Aufgaben erledigt, sollte sie in kleinere Funktionen zerlegt werden.

## Übungen

1. Schreibe eine Funktion `zeichne_punkt()`, die einen roten Punkt malt.
2. Schreibe eine Funktion für ein Quadrat der festen Kantenlänge 5.
3. Rufe die Quadratfunktion in einer Schleife viermal an verschiedenen Positionen auf.
4. Schreibe Funktionen `vorbereiten()`, `zeichne_muster()` und `beenden()` und strukturiere damit ein Programm.
5. Erkläre den Unterschied zwischen Funktionsdefinition und Funktionsaufruf.

## Merksatz

Eine Funktion gibt einer Teilaufgabe einen Namen. Sie wird einmal definiert und kann anschließend beliebig oft aufgerufen werden.
