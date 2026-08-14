# Funktionen mit Parametern und Rückgabewerten

Eine parameterlose Funktion zeichnet immer dieselbe Form. Parameter machen eine Funktion flexibel: Werte wie Größe, Farbe oder Position werden erst beim Aufruf festgelegt.

## Vom festen Wert zum Parameter

@button:copy
```python
def zeichne_linie():
    paint("purple")
    right(5)
    paint_stop()
```

Die Länge ist fest eingebaut. Eine allgemeinere Funktion erhält einen Parameter:

@button:copy
```python
def zeichne_linie(laenge):
    paint("purple")
    right(laenge)
    paint_stop()
```

Beim Aufruf wird ein konkretes Argument eingesetzt:

@button:copy
```python
zeichne_linie(5)
zeichne_linie(12)
```

- `laenge` heißt **Parameter** und steht in der Definition.
- `5` und `12` heißen **Argumente** und stehen in den Aufrufen.
- Innerhalb der Funktion verhält sich der Parameter wie eine lokale Variable.

## Mehrere Parameter

Parameter und Argumente werden durch Kommas getrennt. Ihre Reihenfolge muss zusammenpassen:

@button:run
@button:copy
```python
from pykim import *

def zeichne_rechteck(breite, hoehe, farbe):
    paint(farbe)
    right(breite)
    down(hoehe)
    left(breite)
    up(hoehe)
    paint_stop()

set_position(20, 20)
zeichne_rechteck(10, 5, "cyan")

run()
```

Mit Schlüsselwortargumenten wird die Bedeutung beim Aufruf besonders deutlich:

@button:copy
```python
zeichne_rechteck(breite=10, hoehe=5, farbe="cyan")
```

## Standardwerte

Ein Parameter kann einen Standardwert besitzen:

@button:copy
```python
def male_markierung(farbe="orange"):
    paint(farbe)
    paint_stop()

male_markierung()          # orange
male_markierung("yellow") # yellow
```

Pflichtparameter stehen vor Parametern mit Standardwert:

@button:copy
```python
def zeichne_linie(laenge, farbe="purple"):
    paint(farbe)
    right(laenge)
    paint_stop()
```

## Wachsende Figuren

@button:run
@button:copy
```python
from pykim import *

def zeichne_rechteck(breite, hoehe, farbe="lime"):
    paint(farbe)
    right(breite)
    down(hoehe)
    left(breite)
    up(hoehe)
    paint_stop()

set_position(20, 20)

for groesse in range(4, 13, 2):
    zeichne_rechteck(groesse, groesse, "lime")

run()
```

Die Schleifenvariable wird bei jedem Aufruf als Argument übergeben. Dadurch arbeitet dieselbe Funktion mit verschiedenen Größen.

## Ergebnisse mit return zurückgeben

Funktionen können nicht nur Aktionen ausführen, sondern auch Werte berechnen:

@button:run
@button:copy
```python
def flaeche(breite, hoehe):
    return breite * hoehe

ergebnis = flaeche(8, 5)
print(ergebnis)  # 40
```

`return` beendet den aktuellen Funktionsaufruf und liefert den Wert an die Aufrufstelle zurück.

@button:run
@button:copy
```python
def ist_in_welt(x, y, breite, hoehe):
    return 0 <= x < breite and 0 <= y < hoehe

if ist_in_welt(25, 30, 160, 120):
    print("Die Position ist gültig.")
```

Ohne ausdrückliches `return` liefert eine Python-Funktion den Wert `None`.

## Frühes Beenden

@button:copy
```python
def pruefe_farbe(farbe):
    if farbe == "black":
        return "frei"
    return "belegt"
```

Sobald ein `return` ausgeführt wurde, werden die darunterliegenden Zeilen dieses Funktionsaufrufs nicht mehr bearbeitet.

## Typische Fehler

### Falsche Anzahl von Argumenten

Wenn `zeichne_rechteck(breite, hoehe, farbe)` definiert wurde, benötigt ein normaler Aufruf drei Argumente. Sonst entsteht ein `TypeError`.

### Reihenfolge verwechselt

`zeichne_rechteck("red", 10, 5)` setzt die Argumente an falschen Stellen ein. Schlüsselwortargumente können solche Fehler vermeiden.

### `print` statt `return`

`print()` zeigt einen Wert nur an. `return` liefert ihn zurück, damit das Programm damit weiterrechnen kann.

### Rückgabewert ignoriert

@button:copy
```python
flaeche(8, 5)
```

Der Wert wird berechnet, aber nicht gespeichert oder verwendet. Sinnvoll ist beispielsweise `rechteck_flaeche = flaeche(8, 5)`.

## Übungen

1. Erweitere eine Quadratfunktion um den Parameter `kantenlaenge`.
2. Ergänze den Parameter `farbe` mit dem Standardwert `"purple"`.
3. Schreibe `zeichne_punktlinie(anzahl, abstand, farbe)`.
4. Schreibe eine Funktion, die aus Breite und Höhe den Umfang zurückgibt.
5. Schreibe `ist_gerade(zahl)`, das einen Wahrheitswert zurückliefert.
6. Zeichne in einer Schleife Rechtecke mit wachsender Breite und wechselnder Farbe.

## Merksatz

Parameter machen Funktionen allgemein verwendbar. Argumente liefern die konkreten Werte. `return` gibt ein Ergebnis an das aufrufende Programm zurück.
