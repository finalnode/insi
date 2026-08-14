# Fehlermeldungen verstehen und Programme debuggen

Fehler gehören zum Programmieren. Eine Fehlermeldung ist kein Urteil über die Person, sondern eine technische Beschreibung: Wo konnte Python nicht weiterarbeiten und warum?

## Drei Arten von Fehlern

### Syntaxfehler

Der Code entspricht nicht der Grammatik von Python:

```text
if farbe == "red"
    paint("red")
```

Der Doppelpunkt fehlt. Python meldet einen `SyntaxError` und startet das Programm nicht.

### Laufzeitfehler

Der Code ist syntaktisch gültig, scheitert aber während der Ausführung:

```text
farben = ["red", "green"]
print(farben[5])
```

Hier entsteht ein `IndexError`.

### Logikfehler

Das Programm läuft ohne Fehlermeldung, liefert aber das falsche Ergebnis:

@button:copy
```python
breite = 5
hoehe = 4
flaeche = breite + hoehe
```

Python kann nicht wissen, dass die Fläche multipliziert werden sollte. Logikfehler werden durch Tests, Ausgaben und sorgfältiges Nachvollziehen gefunden.

## Einen Traceback lesen

Eine typische Meldung enthält:

```text
Traceback (most recent call last):
  File "aufgabe.py", line 8, in <module>
    right(kantenlaenge)
NameError: name 'kantenlaenge' is not defined
```

Lies sie von unten nach oben:

1. `NameError` nennt die Fehlerart.
2. Der Text erklärt den unbekannten Namen.
3. Dateiname und Zeilennummer zeigen die Stelle.
4. Bei mehreren Funktionsaufrufen zeigen die darüberliegenden Einträge den Weg zum Fehler.

Die markierte Zeile ist der Ort, an dem Python den Fehler bemerkt. Die eigentliche Ursache kann etwas weiter oben liegen.

## Häufige Fehlertypen

| Fehlertyp | Typische Ursache |
|---|---|
| `SyntaxError` | Doppelpunkt, Klammer oder Anführungszeichen fehlt |
| `IndentationError` | Block falsch eingerückt |
| `NameError` | Name falsch geschrieben oder noch nicht definiert |
| `TypeError` | Operation oder Funktionsaufruf passt nicht zum Datentyp |
| `ValueError` | Datentyp grundsätzlich richtig, konkreter Wert ungültig |
| `IndexError` | Listenindex außerhalb des gültigen Bereichs |
| `KeyError` | Dictionary-Schlüssel fehlt |
| `ZeroDivisionError` | Division durch null |
| `AttributeError` | Objekt besitzt das verwendete Attribut oder die Methode nicht |
| `RecursionError` | zu tiefe oder endlose Rekursion |

## Fehler systematisch eingrenzen

1. Fehlermeldung vollständig lesen.
2. Zeile und Fehlerart bestimmen.
3. Letzte Änderung betrachten.
4. Annahmen mit kleinen Ausgaben prüfen.
5. Problem auf ein möglichst kleines Beispiel reduzieren.
6. Nur eine Sache verändern und erneut testen.

## Werte sichtbar machen

@button:copy
```python
print("x vor Bewegung:", x)
x += schrittweite
print("x nach Bewegung:", x)
```

Noch eindeutiger sind f-Strings:

@button:copy
```python
print(f"DEBUG: x={x}, y={y}, farbe={farbe!r}")
```

`!r` zeigt bei Strings auch Anführungszeichen und macht unsichtbare Leerzeichen leichter erkennbar.

## Kontrollfluss prüfen

@button:copy
```python
if punkte >= 100:
    print("DEBUG: Gold-Zweig")
    rang = "Gold"
elif punkte >= 50:
    print("DEBUG: Silber-Zweig")
    rang = "Silber"
```

Solche temporären Ausgaben zeigen, welcher Zweig oder wie viele Schleifendurchläufe erreicht werden.

## Kleine Testfälle

@button:copy
```python
def ist_gerade(zahl):
    return zahl % 2 == 0

assert ist_gerade(2)
assert ist_gerade(0)
assert not ist_gerade(3)
```

`assert` beendet das Programm, wenn die erwartete Bedingung falsch ist. Für größere PyKIM-Aufgaben übernimmt der Trainer diese Idee mit verständlichen Testfällen und Hinweisen.

## Randfälle

Teste nicht nur einen typischen Wert:

- leere Liste oder leerer String
- null und negative Zahlen
- erster und letzter gültiger Index
- Position direkt am Weltrand
- unbekannte Farbe
- gleichzeitig gedrückte Tasten
- bereits erreichter Gewinnzustand

Viele Fehler treten nur an Grenzen auf.

## Thonny-Debugger

In Thonny kann ein Programm schrittweise ausgeführt werden. Beobachte dabei:

- welche Zeile als Nächstes ausgeführt wird,
- welche Werte Variablen besitzen,
- wie sich Werte in Schleifen verändern,
- wann eine Funktion betreten und verlassen wird.

Setze einen Haltepunkt kurz vor die verdächtige Stelle. Starte nicht sofort mit vielen Haltepunkten im gesamten Programm.

## Fehler sinnvoll behandeln

Nicht jeder Fehler sollte abgefangen werden. Programmierfehler wie falsch geschriebene Namen sollten während der Entwicklung sichtbar bleiben. Erwartbare Benutzereingaben können dagegen behandelt werden:

@button:copy
```python
try:
    anzahl = int(input("Anzahl: "))
except ValueError:
    print("Bitte eine ganze Zahl eingeben.")
```

Ein leeres `except:` versteckt auch unerwartete Fehler und erschwert die Diagnose.

## Typische Fehlersuche, die nicht hilft

- wahllos Code verändern
- nur die letzte Zeile der Meldung ignorieren oder wegklicken
- große Teile gleichzeitig neu schreiben
- einen Fehler mit `try/except` verstecken
- Code übernehmen, ohne ihn schrittweise zu verstehen
- annehmen, dass die Bibliothek falsch sein muss, bevor Eingaben und Zustand geprüft wurden

## Übungen

1. Erzeuge absichtlich je einen `NameError`, `TypeError` und `IndexError` und erkläre die Meldung.
2. Repariere ein Programm mit fehlendem Doppelpunkt und falscher Einrückung.
3. Nutze Debug-Ausgaben, um eine falsch laufende Schleife zu untersuchen.
4. Schreibe drei `assert`-Prüfungen für eine Flächenfunktion.
5. Liste Randfälle für eine Funktion auf, die eine Bewegung innerhalb der Welt prüft.
6. Untersuche ein Programm im Thonny-Debugger und dokumentiere drei aufeinanderfolgende Variablenzustände.

## Merksatz

Debugging bedeutet, Annahmen systematisch zu prüfen. Fehlertyp, Zeilennummer, Variablenzustand und ein kleiner reproduzierbarer Test führen meist schneller zur Ursache als Raten.
