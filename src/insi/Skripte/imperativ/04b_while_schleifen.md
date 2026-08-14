# Kopfgesteuerte Schleifen mit while

Eine `for`-Schleife passt, wenn eine Anzahl oder Folge bekannt ist. Eine `while`-Schleife wiederholt Anweisungen, solange eine Bedingung wahr ist. Sie eignet sich, wenn die Zahl der Durchläufe vorher nicht sicher feststeht.

## Grundaufbau

@button:run
@button:copy
```python
zaehler = 0

while zaehler < 5:
    print(zaehler)
    zaehler += 1
```

Ablauf:

1. Die Bedingung `zaehler < 5` wird geprüft.
2. Ist sie `True`, wird der eingerückte Block ausgeführt.
3. Danach springt Python zurück zur Bedingung.
4. Ist sie `False`, wird hinter der Schleife weitergemacht.

Da die Bedingung **vor** jedem Durchlauf geprüft wird, heißt sie kopfgesteuerte Schleife. Ist die Bedingung von Anfang an falsch, wird der Block kein einziges Mal ausgeführt.

## Eine unbekannte Strecke untersuchen

@button:run
@button:copy
```python
from pykim import *

set_position(10, 10)
schritte = 0

while get_color() != "red" and schritte < 50:
    right()
    schritte += 1

print(f"KIM ging {schritte} Schritte.")
run()
```

Die Schleife endet, wenn ein rotes Feld erreicht wurde oder die Sicherheitsgrenze von 50 Schritten erreicht ist.

## Warum eine Abbruchmöglichkeit nötig ist

```text
zaehler = 0

while zaehler < 5:
    print(zaehler)
```

`zaehler` verändert sich nie. Die Bedingung bleibt deshalb immer wahr. Es entsteht eine Endlosschleife.

Bei einer `while`-Schleife solltest du vor dem Start beantworten können:

- Welche Variable oder welcher Zustand wird geprüft?
- Was verändert diesen Zustand?
- Unter welcher Bedingung endet die Schleife?
- Braucht das Programm zusätzlich eine Sicherheitsgrenze?

## Eingaben wiederholen

@button:copy
```python
eingabe = ""

while eingabe != "geheim":
    eingabe = input("Codewort: ").strip().lower()

print("Richtig!")
```

Die Eingabe wird so lange wiederholt, bis sie dem erwarteten Wort entspricht.

## Sentinel-Wert

Ein besonderer Wert kann das Ende einer Eingabefolge markieren:

@button:copy
```python
summe = 0
eingabe = input("Zahl oder Ende: ")

while eingabe != "Ende":
    summe += int(eingabe)
    eingabe = input("Zahl oder Ende: ")

print(f"Summe: {summe}")
```

`"Ende"` heißt hier Sentinel-Wert. Er gehört nicht zu den Nutzdaten, sondern steuert den Ablauf.

## break und continue

`break` beendet die nächste umgebende Schleife sofort:

@button:copy
```python
while True:
    eingabe = input("Befehl: ")
    if eingabe == "ende":
        break
    print(f"Du hast {eingabe} eingegeben.")
```

`continue` springt direkt zur nächsten Bedingungsprüfung:

@button:run
@button:copy
```python
zahl = 0

while zahl < 10:
    zahl += 1
    if zahl % 2 != 0:
        continue
    print(zahl)
```

Beide Befehle sind nützlich, sollten aber sparsam eingesetzt werden. Eine klare Schleifenbedingung ist häufig leichter verständlich.

## while oder for?

@button:copy
```python
for _ in range(5):
    right()
```

ist für genau fünf Wiederholungen klarer als eine manuell gezählte `while`-Schleife.

@button:copy
```python
while get_color() != "red":
    right()
```

ist geeignet, wenn die Entfernung zum roten Feld unbekannt ist.

## Keine eigene Spiel-Endlosschleife

Interaktive PyKIM-Programme verwenden:

@button:copy
```python
world.run(update, draw)
```

Die Welt ruft `update()` und `draw()` wiederholt auf. Eine zusätzliche `while True`-Schleife innerhalb von `update()` würde das Fenster blockieren.

## Typische Fehler

### Veränderung vergessen

Die Schleifenbedingung kann nie falsch werden.

### Falsche Grenze

`while zaehler <= 5` läuft bei Startwert 0 sechsmal. Prüfe Anfangswert, Operator und Veränderung gemeinsam.

### Variable erst im Block anlegen

Die Bedingung wird vor dem ersten Durchlauf geprüft. Alle darin verwendeten Variablen müssen vorher definiert sein.

### Eingabe nicht vereinheitlicht

`"Ende"`, `"ende"` und `" ende "` sind verschiedene Strings. `strip().lower()` kann Eingaben vereinheitlichen.

## Übungen

1. Gib die Zahlen 0 bis 9 mit einer `while`-Schleife aus.
2. Erzeuge einen Countdown von 10 bis 1.
3. Addiere Zahlen, bis die Summe mindestens 100 erreicht.
4. Lasse KIM nach rechts gehen, bis ein farbiges Feld erreicht wird. Ergänze eine Sicherheitsgrenze.
5. Frage eine Eingabe so lange ab, bis `ja` oder `nein` eingegeben wurde.
6. Erkläre, warum eine `while True`-Schleife in `update()` eines Spiels problematisch ist.

## Merksatz

Eine `while`-Schleife läuft, solange ihre Bedingung wahr ist. Jede Schleife benötigt einen nachvollziehbaren Weg zum Ende.
