# Rekursion und rekursive Funktionen

Eine Funktion ist rekursiv, wenn sie sich direkt oder indirekt selbst aufruft. Rekursion zerlegt ein Problem in kleinere Versionen desselben Problems.

## Ein erstes Beispiel

@button:run
@button:copy
```python
def countdown(zahl):
    if zahl <= 0:
        print("Start!")
        return

    print(zahl)
    countdown(zahl - 1)

countdown(5)
```

Die Aufrufe lauten nacheinander `countdown(5)`, `countdown(4)`, bis `countdown(0)` erreicht wird.

Jede Rekursion benötigt zwei Bestandteile:

1. **Abbruchfall:** Eine einfache Situation, die ohne weiteren Selbstaufruf gelöst wird.
2. **Rekursiver Fall:** Das Problem wird verkleinert und die Funktion erneut aufgerufen.

## Summe von 1 bis n

Mathematisch kann die Summe so zerlegt werden:

- `summe(1) = 1`
- `summe(4) = 4 + summe(3)`
- `summe(3) = 3 + summe(2)`

@button:run
@button:copy
```python
def summe_bis(n):
    if n <= 1:
        return n
    return n + summe_bis(n - 1)

print(summe_bis(4))  # 10
```

Beim Zurückkehren werden die Ergebnisse zusammengesetzt:

```text
summe_bis(4)
= 4 + summe_bis(3)
= 4 + 3 + summe_bis(2)
= 4 + 3 + 2 + summe_bis(1)
= 4 + 3 + 2 + 1
= 10
```

## Aufrufstapel

Jeder noch nicht beendete Funktionsaufruf speichert seine lokalen Variablen und die Stelle, an die er zurückkehren muss. Diese wartenden Aufrufe liegen auf dem **Call Stack** oder Aufrufstapel.

Zu tiefe oder endlose Rekursion füllt den Stapel. Python beendet das Programm dann mit einem `RecursionError`.

## Rekursiv mit PyKIM zeichnen

@button:run
@button:copy
```python
from pykim import *

def zeichne_linie(laenge):
    if laenge <= 0:
        return

    paint("lime")
    right()
    zeichne_linie(laenge - 1)

set_position(20, 20)
zeichne_linie(10)
run()
```

Für eine einfache Linie wäre eine Schleife verständlicher. Das Beispiel zeigt jedoch klar, wie die Problemgröße sinkt.

## Verzweigte Muster

@button:run
@button:copy
```python
from pykim import *

def zeichne_muster(tiefe):
    if tiefe == 0:
        paint("yellow")
        return

    paint("green")
    right()
    zeichne_muster(tiefe - 1)
    left()
    down()
    zeichne_muster(tiefe - 1)
    up()

set_position(30, 20)
zeichne_muster(4)
run()
```

Jeder Aufruf erzeugt zwei kleinere Aufrufe. Die Zahl der Aufrufe wächst deshalb schnell. Schon kleine Tiefen können viele Arbeitsschritte erzeugen.

## Rekursive Datenstrukturen

Rekursion ist besonders passend, wenn auch die Daten rekursiv aufgebaut sind, beispielsweise Ordner mit Unterordnern oder ein Baum mit Teilbäumen.

@button:run
@button:copy
```python
daten = [1, [2, 3], [4, [5, 6]]]

def gib_werte_aus(element):
    if isinstance(element, list):
        for unterelement in element:
            gib_werte_aus(unterelement)
    else:
        print(element)

gib_werte_aus(daten)
```

## Schleife oder Rekursion?

Viele Aufgaben lassen sich auf beide Arten lösen:

@button:copy
```python
def summe_mit_schleife(n):
    ergebnis = 0
    for zahl in range(1, n + 1):
        ergebnis += zahl
    return ergebnis
```

Für lineare Wiederholungen ist die Schleife in Python meist effizienter und einfacher. Rekursion ist stark, wenn ein Problem natürlich aus gleichartigen Teilproblemen besteht.

## Typische Fehler

### Abbruchfall fehlt

Die Funktion ruft sich unbegrenzt weiter auf.

### Problem wird nicht kleiner

`funktion(n)` ruft erneut `funktion(n)` auf. Der Abbruchfall wird nie erreicht.

### Rückgabewert vergessen

Bei Berechnungen muss das Ergebnis des rekursiven Aufrufs meistens mit `return` weitergegeben oder verarbeitet werden.

### Zu große Tiefe

Rekursion ist in Python absichtlich begrenzt. Große lineare Aufgaben sollten mit Schleifen gelöst werden.

## Übungen

1. Schreibe einen rekursiven Countdown.
2. Berechne rekursiv die Summe von 1 bis `n`.
3. Berechne rekursiv `basis ** exponent` für nichtnegative Exponenten.
4. Gib einen String rekursiv rückwärts aus.
5. Zeichne eine rekursive Linie, die in jedem Aufruf die Farbe wechselt.
6. Vergleiche eine rekursive Lösung mit einer Schleifenlösung und begründe, welche verständlicher ist.
7. Erweitere ein verzweigtes Muster vorsichtig und beobachte, wie schnell die Anzahl der Aufrufe wächst.

## Merksatz

Rekursion braucht einen erreichbaren Abbruchfall und einen rekursiven Schritt, der das Problem verkleinert.
