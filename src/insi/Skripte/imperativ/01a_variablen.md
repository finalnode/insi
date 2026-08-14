# Variablen: Werte speichern und wiederverwenden

Variablen gehören zu den wichtigsten Grundlagen der Programmierung. Mit ihnen erhalten Werte einen Namen und können später erneut verwendet oder verändert werden.

## Die Zuweisung

@button:copy
```python
kantenlaenge = 5
farbe = "purple"
```

Das Gleichheitszeichen ist in Python der **Zuweisungsoperator**. Die Anweisung wird in dieser Reihenfolge verarbeitet:

1. Python wertet den Ausdruck auf der rechten Seite aus.
2. Das Ergebnis wird unter dem Namen auf der linken Seite gespeichert.

@button:run
@button:copy
```python
ergebnis = 3 + 4 * 2
print(ergebnis)  # 11
```

Zuerst wird `3 + 4 * 2` berechnet. Danach wird `11` in `ergebnis` gespeichert.

## Anders als eine mathematische Gleichung

@button:run
@button:copy
```python
schrittweite = 5
schrittweite = schrittweite + 2
print(schrittweite)  # 7
```

Die zweite Zeile wäre als mathematische Gleichung unsinnig. Als Zuweisung bedeutet sie:

1. Lies den bisherigen Wert `5`.
2. Berechne `5 + 2`.
3. Speichere `7` wieder unter `schrittweite`.

Die Kurzform lautet:

@button:copy
```python
schrittweite += 2
```

Entsprechend gibt es `-=`, `*=`, `/=` und weitere zusammengesetzte Zuweisungen.

## Variablen in PyKIM

@button:run
@button:copy
```python
from pykim import *

start_x = 20
start_y = 20
kantenlaenge = 6
zeichenfarbe = "orange"

set_position(start_x, start_y)
paint(zeichenfarbe)
right(kantenlaenge)
down(kantenlaenge)
paint_stop()

run()
```

Das Programm lässt sich an wenigen Stellen verändern. Alle Befehle arbeiten anschließend mit den neuen Werten.

## Gute Variablennamen

Ein Name sollte den Zweck des gespeicherten Wertes erklären.

@button:copy
```python
# unklar
x = 8
a = "cyan"

# verständlicher
kantenlaenge = 8
linienfarbe = "cyan"
```

Für Python wird üblicherweise `snake_case` verwendet:

@button:copy
```python
anzahl_der_stufen = 5
aktuelle_position_x = 20
```

Regeln für Bezeichner:

- Sie dürfen Buchstaben, Ziffern und Unterstriche enthalten.
- Sie dürfen nicht mit einer Ziffer beginnen.
- Leerzeichen und Bindestriche sind nicht erlaubt.
- Python-Schlüsselwörter wie `for`, `if` oder `class` dürfen nicht verwendet werden.
- Vermeide Umlaute, damit Code auf allen Systemen problemlos lesbar bleibt.
- Klassennamen werden später üblicherweise in `CamelCase` geschrieben.

## Deklarieren, Initialisieren und Verändern

Beim ersten Zuweisen wird eine Variable in Python erzeugt und initialisiert:

@button:copy
```python
punkte = 0
```

Später kann sie verändert werden:

@button:copy
```python
punkte = punkte + 10
```

Python verlangt keine vorherige Angabe des Datentyps. Der Typ ergibt sich aus dem gespeicherten Wert.

## Mehrere zusammengehörige Werte

@button:copy
```python
kim_x = 20
kim_y = 30
kim_farbe = "purple"
```

Für wenige Werte ist das übersichtlich. Wenn später mehrere Pixel jeweils Position, Farbe und Namen besitzen, werden Objekte geeigneter sein. Variablen bereiten dieses Verständnis vor: Auch ein Objekt speichert Zustand, nur strukturiert an einer gemeinsamen Stelle.

## Variablen und Schleifen

@button:run
@button:copy
```python
from pykim import *

set_position(20, 20)
laenge = 2

for _ in range(5):
    paint("lime")
    right(laenge)
    paint_stop()
    down(2)
    laenge += 2

run()
```

In jedem Durchlauf wird `laenge` größer. Dadurch entstehen Linien mit den Längen 2, 4, 6, 8 und 10.

## Typische Fehler

### Variable vor der Zuweisung verwenden

```text
right(kantenlaenge)
kantenlaenge = 5
```

Python kennt `kantenlaenge` in der ersten Zeile noch nicht. Das führt zu einem `NameError`.

### Unterschiedliche Schreibweisen

```text
kantenlaenge = 5
right(kantenLaenge)
```

`kantenlaenge` und `kantenLaenge` sind zwei verschiedene Namen.

### Eingebaute Namen überschreiben

```text
list = [1, 2, 3]
```

Damit wird der eingebaute Name `list` überschrieben. Verwende beispielsweise `zahlen`.

## Übungen

1. Speichere Startposition, Farbe und Kantenlänge eines Quadrats in Variablen.
2. Zeichne fünf waagerechte Linien, deren Länge in jedem Durchlauf um zwei wächst.
3. Tausche die Werte zweier Variablen `farbe_1` und `farbe_2`.
4. Erkläre in eigenen Worten, warum `punkte = punkte + 1` möglich ist.
5. Verbessere die Namen in diesem Code: `a = 20`, `b = 5`, `c = "red"`.

## Merksatz

Bei einer Zuweisung wird zuerst rechts gerechnet und danach links gespeichert. Gute Namen machen den Zustand eines Programms verständlich.
