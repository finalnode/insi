# Verzweigungen, Vergleiche und Zufall

Mit Bedingungen kann ein Programm unterschiedliche Wege wählen. Es reagiert damit auf Farben, Positionen, Eingaben, Zufallswerte oder den Zustand eines Spiels.

## Wahrheitswerte

Eine Bedingung wird zu `True` oder `False` ausgewertet. Diese beiden Werte gehören zum Datentyp `bool`.

@button:run
@button:copy
```python
print(5 > 3)             # True
print(5 == 3)            # False
print("red" != "green")  # True
```

## Vergleichsoperatoren

| Operator | Bedeutung | Beispiel |
|---|---|---|
| `==` | gleich | `farbe == "red"` |
| `!=` | ungleich | `farbe != "black"` |
| `<` | kleiner | `x < 20` |
| `<=` | kleiner oder gleich | `x <= 20` |
| `>` | größer | `punkte > 100` |
| `>=` | größer oder gleich | `leben >= 1` |

`=` weist einen Wert zu, `==` vergleicht zwei Werte.

## Die einfache if-Verzweigung

@button:run
@button:copy
```python
farbe = "red"

if farbe == "red":
    print("Das Feld ist rot.")
```

Der eingerückte Block wird nur ausgeführt, wenn die Bedingung wahr ist.

@button:run
@button:copy
```python
from pykim import *

set_position(20, 20)

if get_color() == "black":
    paint("green")

run()
```

## Genau zwei Fälle mit else

@button:run
@button:copy
```python
from pykim import *

set_position(20, 20)

if get_color() == "red":
    play_tone("C4")
else:
    play_pause()

run()
```

Es wird genau einer der beiden Blöcke ausgeführt.

## Mehrere Fälle mit elif

@button:run
@button:copy
```python
from pykim import *

farbe = get_color()

if farbe == "red":
    play_tone("C4")
elif farbe == "green":
    play_tone("E4")
elif farbe == "cyan":
    play_tone("G4")
else:
    play_pause()

run()
```

Python prüft von oben nach unten. Sobald eine Bedingung wahr ist, wird deren Block ausgeführt und die übrige Kette übersprungen.

## Unabhängige if-Anweisungen oder elif-Kette?

Mehrere einzelne `if`-Anweisungen können alle ausgeführt werden:

@button:run
@button:copy
```python
zahl = 12

if zahl > 0:
    print("positiv")
if zahl % 2 == 0:
    print("gerade")
```

Eine `if`-`elif`-`else`-Kette wählt dagegen höchstens einen Zweig. Die passende Form hängt von der Problemstellung ab.

## Logische Operatoren

### and

Beide Teilbedingungen müssen wahr sein:

@button:run
@button:copy
```python
x = 25
y = 30

if x >= 0 and y >= 0:
    print("Beide Koordinaten sind nicht negativ.")
```

### or

Mindestens eine Teilbedingung muss wahr sein:

@button:run
@button:copy
```python
farbe = "yellow"

if farbe == "yellow" or farbe == "orange":
    print("Eine warme Farbe")
```

### not

`not` kehrt einen Wahrheitswert um:

@button:run
@button:copy
```python
sichtbar = False

if not sichtbar:
    print("Das Pixel ist versteckt.")
```

## Verkettete Vergleiche

Python erlaubt mathematisch lesbare Bereichsprüfungen:

@button:run
@button:copy
```python
x = 25

if 0 <= x < 160:
    print("x liegt innerhalb der Welt.")
```

Für zwei Koordinaten:

@button:copy
```python
if 0 <= x < 160 and 0 <= y < 120:
    print("Die Position ist gültig.")
```

## Verschachtelte Bedingungen

@button:run
@button:copy
```python
farbe = "red"
punkte = 12

if farbe == "red":
    if punkte >= 10:
        print("Rotes Bonusfeld")
```

Oft lässt sich dieselbe Aussage flacher mit `and` schreiben. Zu tiefe Verschachtelungen erschweren das Lesen.

## Zufallszahlen

Das Modul `random` stellt Zufallsfunktionen bereit:

@button:run
@button:copy
```python
from random import randint

zahl = randint(1, 6)
print(zahl)
```

`randint(1, 6)` liefert eine ganze Zahl zwischen 1 und 6 einschließlich beider Grenzen.

Eine zufällige Auswahl aus einer Liste gelingt mit `choice()`:

@button:run
@button:copy
```python
from random import choice

farben = ["red", "green", "cyan", "yellow"]
zufallsfarbe = choice(farben)
print(zufallsfarbe)
```

## Zufälliges Pixelmuster

@button:run
@button:copy
```python
from random import choice
from pykim import *

farben = ["red", "green", "cyan", "yellow"]
set_position(20, 20)

for _ in range(12):
    paint(choice(farben))
    paint_stop()
    right(2)

run()
```

Zufall erzeugt Daten; Bedingungen wenden Regeln darauf an:

@button:run
@button:copy
```python
from random import randint

wurf = randint(1, 6)

if wurf == 6:
    print("Bonus!")
elif wurf >= 4:
    print("Guter Wurf")
else:
    print("Noch einmal versuchen")
```

## Typische Fehler

### Zuweisung statt Vergleich

```text
if farbe = "red":
```

Richtig ist `if farbe == "red":`.

### Doppelpunkt oder Einrückung fehlt

Nach `if`, `elif` und `else` steht ein Doppelpunkt. Der zugehörige Block wird eingerückt.

### Unmögliche Bedingung

@button:copy
```python
if x < 0 and x > 10:
    print("unmöglich")
```

Ein einzelner Wert kann nicht gleichzeitig kleiner als 0 und größer als 10 sein. Vermutlich war `or` gemeint.

### Bedingungen überschneiden sich

@button:run
@button:copy
```python
punkte = 120

if punkte >= 50:
    print("Bronze")
elif punkte >= 100:
    print("Gold")
```

Der Gold-Zweig wird nie erreicht, weil 120 bereits die erste Bedingung erfüllt. Prüfe speziellere beziehungsweise höhere Grenzen zuerst.

### Zufall schlecht testbar

Zufällige Ergebnisse erschweren reproduzierbare Tests. Speichere den Zufallswert in einer Variable und gib ihn während der Entwicklung aus.

## Übungen

1. Prüfe, ob eine Zahl positiv, negativ oder null ist.
2. Prüfe, ob eine Zahl gerade oder ungerade ist.
3. Übersetze vier Farben mit `if`/`elif` in vier Töne.
4. Verhindere eine Bewegung nach rechts, wenn KIM bereits am rechten Rand steht.
5. Würfle eine Zahl von 1 bis 6 und gib eine passende Rückmeldung aus.
6. Erzeuge zwanzig zufällig gefärbte Pixel aus einer vorgegebenen Farbliste.
7. Ordne einen Punktestand den Stufen Bronze, Silber und Gold zu. Achte auf die Reihenfolge der Bedingungen.

## Merksatz

Bedingungen liefern Wahrheitswerte. `if` entscheidet anhand dieser Werte, welcher Programmteil ausgeführt wird. `and`, `or` und `not` verbinden beziehungsweise verändern Bedingungen.
