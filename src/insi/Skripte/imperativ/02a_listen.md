# Listen: viele Werte gemeinsam speichern

Eine Liste speichert eine geordnete Folge von Werten unter einem Namen. Sie eignet sich beispielsweise für Farben, Noten, Positionen, Punktstände oder Spielzüge.

## Eine Liste anlegen

@button:copy
```python
farben = ["green", "purple", "orange", "cyan"]
noten = ["C4", "D4", "E4", "F4"]
punkte = [12, 5, 18, 9]
```

Eine Liste beginnt mit `[` und endet mit `]`. Die Elemente werden durch Kommas getrennt. Eine leere Liste wird mit `[]` erzeugt.

Python erlaubt gemischte Datentypen, doch gleichartige Werte sind meistens verständlicher:

@button:copy
```python
gemischt = ["KIM", 20, 30, True]
```

## Indexzugriff

Jedes Element besitzt eine Position, den **Index**. Python beginnt bei null:

| Index | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| Wert | green | purple | orange | cyan |

@button:run
@button:copy
```python
farben = ["green", "purple", "orange", "cyan"]

print(farben[0])  # green
print(farben[2])  # orange
```

Negative Indizes zählen vom Ende:

@button:copy
```python
print(farben[-1]) # cyan
print(farben[-2]) # orange
```

Ein ungültiger Index führt zu einem `IndexError`.

## Elemente verändern

Listen sind veränderbar:

@button:run
@button:copy
```python
farben = ["green", "purple", "orange"]
farben[1] = "red"
print(farben)  # ['green', 'red', 'orange']
```

## Länge und wichtige Methoden

@button:run
@button:copy
```python
farben = ["green", "purple"]

farben.append("orange")   # hinten ergänzen
farben.insert(1, "cyan") # an Index 1 einfügen
farben.remove("green")    # ersten passenden Wert entfernen
letzte_farbe = farben.pop() # letztes Element entfernen und liefern

print(len(farben))
print(letzte_farbe)
```

`in` prüft, ob ein Wert enthalten ist:

@button:copy
```python
if "purple" in farben:
    print("Violett ist vorhanden.")
```

## Durch eine Liste iterieren

Wenn nur die Werte gebraucht werden, ist diese Form am besten lesbar:

@button:run
@button:copy
```python
farben = ["red", "orange", "yellow", "green"]

for farbe in farben:
    print(farbe)
```

Ein Durchlauf über die Indizes ist sinnvoll, wenn die Position benötigt wird:

@button:copy
```python
for index in range(len(farben)):
    print(index, farben[index])
```

`enumerate()` liefert Index und Wert gemeinsam:

@button:copy
```python
for index, farbe in enumerate(farben):
    print(index, farbe)
```

## Farben mit PyKIM darstellen

@button:run
@button:copy
```python
from pykim import *

farben = ["green", "purple", "orange", "cyan", "yellow"]
set_position(20, 20)

for farbe in farben:
    paint(farbe)
    paint_stop()
    right(3)

run()
```

## Eine Tonfolge abspielen

@button:run
@button:copy
```python
from pykim import *

noten = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]

for note in noten:
    play_tone(note)

run()
```

Die Liste enthält die Daten, die Schleife verarbeitet sie. Wird eine Note geändert, muss der Ablauf nicht umgeschrieben werden.

## Teile einer Liste: Slicing

@button:run
@button:copy
```python
zahlen = [0, 1, 2, 3, 4, 5]

print(zahlen[1:4])  # [1, 2, 3]
print(zahlen[:3])   # [0, 1, 2]
print(zahlen[3:])   # [3, 4, 5]
print(zahlen[::2])  # [0, 2, 4]
```

Wie bei `range()` ist die obere Grenze nicht enthalten.

## Kopieren oder gemeinsam verwenden

@button:run
@button:copy
```python
farben_1 = ["red", "green"]
farben_2 = farben_1
farben_2.append("blue")

print(farben_1)  # ebenfalls verändert
```

Beide Namen zeigen auf dieselbe Liste. Eine flache Kopie entsteht beispielsweise mit:

@button:copy
```python
farben_2 = farben_1.copy()
```

## Typische Fehler

### Ab eins zählen

Das erste Element besitzt Index `0`, nicht `1`.

### Obergrenze bei range

`range(len(farben))` erzeugt genau die gültigen Indizes von `0` bis `len(farben) - 1`.

### Liste während des Durchlaufens verändern

Elemente innerhalb derselben `for`-Schleife zu entfernen, kann Werte überspringen. Arbeite bei Bedarf mit einer Kopie oder baue eine neue Liste auf.

### Variable und Element verwechseln

In `for farbe in farben:` enthält `farbe` jeweils einen einzelnen Wert, `farben` bleibt die gesamte Liste.

## Übungen

1. Lege eine Liste mit fünf PyKIM-Farben an und gib das erste sowie letzte Element aus.
2. Ergänze eine Farbe mit `append()` und ersetze ein anderes Element über seinen Index.
3. Male alle Farben als Punktreihe.
4. Speichere eine Melodie in einer Liste und spiele sie mit einer Schleife.
5. Ermittle ohne `max()` den höchsten Wert einer Punkteliste.
6. Erzeuge aus einer Liste eine zweite Liste, die nur Werte größer als 10 enthält.
7. Zeichne Farbe und Position gemeinsam, indem du `enumerate()` verwendest.

## Merksatz

Listen speichern geordnete Folgen. Indizes beginnen bei null. Meistens ist die direkte Iteration `for wert in liste` verständlicher als ein manueller Index.
