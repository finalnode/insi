# Datentypen, Operatoren und Ausdrücke

Programme verarbeiten Werte. Jeder Wert besitzt einen Datentyp. Operatoren verbinden Werte zu Ausdrücken, die Python auswertet.

## Grundlegende Datentypen

| Datentyp | Beispiele | Bedeutung |
|---|---|---|
| `int` | `5`, `-12`, `0` | ganze Zahl |
| `float` | `2.5`, `-0.75` | Kommazahl |
| `str` | `"purple"`, `"KIM"` | Zeichenkette oder Text |
| `bool` | `True`, `False` | Wahrheitswert |
| `list` | `["C4", "E4"]` | geordnete Sammlung |
| `NoneType` | `None` | bewusst kein Wert |

Mit `type()` lässt sich der Datentyp untersuchen:

@button:run
@button:copy
```python
print(type(4))          # <class 'int'>
print(type(1.5))        # <class 'float'>
print(type("purple"))   # <class 'str'>
print(type(True))       # <class 'bool'>
```

## Operator und Operand

Im Ausdruck `4 + 3` ist `+` der Operator. `4` und `3` sind die Operanden.

@button:copy
```python
ergebnis = 4 + 3
```

Die vollständige rechte Seite heißt **Ausdruck**. Ein Ausdruck wird ausgewertet und besitzt danach einen Wert.

## Rechenoperatoren

| Operator | Bedeutung | Beispiel | Ergebnis |
|---|---|---|---|
| `+` | Addition | `7 + 3` | `10` |
| `-` | Subtraktion | `7 - 3` | `4` |
| `*` | Multiplikation | `7 * 3` | `21` |
| `/` | Division | `7 / 2` | `3.5` |
| `//` | Ganzzahldivision | `7 // 2` | `3` |
| `%` | Divisionsrest | `7 % 2` | `1` |
| `**` | Potenz | `2 ** 3` | `8` |

@button:run
@button:copy
```python
breite = 4 * 5
mitte = breite / 2
volle_reihen = 17 // 5
rest = 17 % 5

print(breite, mitte, volle_reihen, rest)
```

## Reihenfolge der Auswertung

Python beachtet dieselbe grundlegende Reihenfolge wie die Mathematik:

1. Klammern
2. Potenzen
3. Multiplikation, Division, Ganzzahldivision und Modulo
4. Addition und Subtraktion

@button:run
@button:copy
```python
print(3 + 4 * 2)       # 11
print((3 + 4) * 2)     # 14
print(2 ** 3 + 1)      # 9
```

Bei Operatoren gleicher Stufe wird normalerweise von links nach rechts ausgewertet:

@button:run
@button:copy
```python
print(20 / 5 * 2)      # 8.0
```

Klammern sind nicht nur zum Ändern der Reihenfolge nützlich. Sie können einen Ausdruck für Menschen eindeutiger lesbar machen.

## `int` und `float`

Eine Division mit `/` liefert auch bei glattem Ergebnis einen `float`:

@button:run
@button:copy
```python
print(8 / 2)           # 4.0
print(type(8 / 2))     # <class 'float'>
```

Rechnet Python mit `int` und `float` gemeinsam, ist das Ergebnis normalerweise ein `float`:

@button:run
@button:copy
```python
print(3 + 1.5)         # 4.5
```

Kommazahlen werden in Python mit einem Punkt geschrieben. `1,5` ist nicht die Zahl eineinhalb, sondern wird in anderem Kontext als Folge zweier Werte interpretiert.

## Modulo für Muster

Der Modulo-Operator `%` ist für Pixelmuster besonders nützlich. Gerade Zahlen haben bei Division durch zwei den Rest null.

@button:run
@button:copy
```python
from pykim import *

set_position(20, 20)

for nummer in range(8):
    if nummer % 2 == 0:
        paint("purple")
    else:
        paint("orange")
    right()

run()
```

Auch zweidimensionale Wechselmuster lassen sich so beschreiben: `(zeile + spalte) % 2` wechselt bei jedem Schritt zwischen `0` und `1`.

## Operatoren bei Strings

Einige Operatoren funktionieren abhängig vom Datentyp unterschiedlich:

@button:run
@button:copy
```python
print("Py" + "KIM")    # PyKIM
print("KIM " * 3)      # KIM KIM KIM
```

`+` verbindet hier Texte. Eine Zahl und einen Text kann Python nicht ohne Umwandlung addieren:

```text
"Punkte: " + 10
```

Das führt zu einem `TypeError`. Richtig sind beispielsweise `"Punkte: " + str(10)` oder ein f-String: `f"Punkte: {10}"`.

## Zuweisen und Vergleichen

`=` und `==` haben verschiedene Aufgaben:

@button:run
@button:copy
```python
farbe = "red"          # Zuweisung
print(farbe == "red")  # Vergleich, Ergebnis True
```

Weitere Vergleichsoperatoren lernst du im Kapitel über Bedingungen.

## Typische Fehler

### Durch null teilen

`5 / 0` führt zu einem `ZeroDivisionError`.

### Falscher Datentyp

`right("fuenf")` übergibt Text, obwohl eine Zahl erwartet wird. Das führt je nach Funktion zu einem `TypeError` oder einer ungültigen Verarbeitung.

### `=` statt `==`

In einer Bedingung muss verglichen werden: `if farbe == "red":`.

### Ergebnis falsch vorausgesagt

Wenn ein Ausdruck unklar ist, zerlege ihn in Teilausdrücke oder verwende Klammern. `print()` und der Variableninspektor von Thonny helfen beim Prüfen.

## Übungen

1. Sage die Ergebnisse von `5 + 2 * 3`, `(5 + 2) * 3`, `17 // 4` und `17 % 4` voraus. Prüfe sie anschließend.
2. Berechne aus Breite und Höhe die Fläche eines Rechtecks.
3. Prüfe mit `%`, ob eine Zahl gerade ist.
4. Zeichne mit PyKIM eine zehn Pixel lange Linie, deren Farben sich abwechseln.
5. Erzeuge ein 5-mal-5-Muster, in dem `(zeile + spalte) % 2` die Farbe bestimmt.
6. Finde und erkläre den Fehler in `punkte_text = "Punkte: " + 10`.

## Merksatz

Ein Ausdruck besteht aus Werten, Variablen, Funktionsaufrufen und Operatoren. Sein Ergebnis und die erlaubten Operationen hängen von den beteiligten Datentypen ab.
