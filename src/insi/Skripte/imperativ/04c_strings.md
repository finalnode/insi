# Strings, Eingaben und Datentypkonvertierung

Ein String ist eine Zeichenkette: ein Text aus keinem, einem oder vielen Zeichen. Namen, Farben, Noten und Benutzereingaben werden häufig als Strings verarbeitet.

## Strings schreiben

@button:copy
```python
name = "KIM"
farbe = 'purple'
leerer_text = ""
```

Einfache und doppelte Anführungszeichen sind gleichwertig. Die gewählte Form muss am Ende wieder geschlossen werden.

Enthält der Text selbst ein Anführungszeichen, kann die andere Form außen verwendet werden:

@button:copy
```python
satz = "KIM sagt: 'Hallo!'"
```

## Texte verbinden

@button:run
@button:copy
```python
vorname = "Kim"
nachname = "Pixel"
voller_name = vorname + " " + nachname
print(voller_name)
```

Mit `*` kann ein String wiederholt werden:

@button:run
@button:copy
```python
print("KIM " * 3)
```

## f-Strings

f-Strings setzen Werte direkt in einen lesbaren Text ein:

@button:run
@button:copy
```python
name = "KIM"
punkte = 42
print(f"{name} hat {punkte} Punkte.")
```

In den geschweiften Klammern dürfen auch Ausdrücke stehen:

@button:run
@button:copy
```python
breite = 8
hoehe = 5
print(f"Fläche: {breite * hoehe}")
```

## Eingaben mit input

@button:copy
```python
name = input("Wie heißt du? ")
print(f"Hallo, {name}!")
```

`input()` liefert immer einen String, auch wenn Ziffern eingegeben wurden.

@button:copy
```python
alter_text = input("Wie alt bist du? ")
print(type(alter_text))  # str
```

## Datentypen konvertieren

@button:run
@button:copy
```python
alter_text = "16"
alter = int(alter_text)
print(alter + 1)
```

Häufige Konvertierungsfunktionen:

| Funktion | Zieltyp | Beispiel |
|---|---|---|
| `int()` | ganze Zahl | `int("16")` |
| `float()` | Kommazahl | `float("2.5")` |
| `str()` | String | `str(42)` |
| `bool()` | Wahrheitswert | `bool(1)` |

@button:copy
```python
kantenlaenge = int(input("Kantenlänge: "))
print(f"Das Quadrat wird {kantenlaenge} Pixel breit.")
```

Eine ungültige Umwandlung wie `int("fuenf")` führt zu einem `ValueError`.

## Fehlerhafte Eingaben behandeln

@button:copy
```python
try:
    zahl = int(input("Ganze Zahl: "))
    print(f"Das Doppelte ist {zahl * 2}.")
except ValueError:
    print("Das war keine ganze Zahl.")
```

Der `try`-Block enthält Code, der fehlschlagen kann. Der passende `except`-Block behandelt den erwarteten Fehler. Fange möglichst konkrete Fehlertypen ab.

Eine Eingabe kann bis zum Erfolg wiederholt werden:

@button:copy
```python
zahl = None

while zahl is None:
    try:
        zahl = int(input("Ganze Zahl: "))
    except ValueError:
        print("Bitte nur Ziffern eingeben.")

print(f"Gespeichert: {zahl}")
```

## Strings ähneln Listen

Jedes Zeichen besitzt einen Index:

@button:run
@button:copy
```python
wort = "PIXEL"

print(wort[0])   # P
print(wort[2])   # X
print(wort[-1])  # L
print(len(wort)) # 5
```

Strings können durchlaufen und in Ausschnitte zerlegt werden:

@button:run
@button:copy
```python
for zeichen in "KIM":
    print(zeichen)

print("PIXEL"[1:4]) # IXE
```

Anders als Listen sind Strings unveränderlich. `wort[0] = "F"` ist nicht erlaubt. Stattdessen wird ein neuer String erzeugt.

## Enthaltensein prüfen

@button:run
@button:copy
```python
text = "KIM läuft durch die Pixelwelt"

if "Pixel" in text:
    print("Das Wort wurde gefunden.")
```

`not in` prüft das Gegenteil.

## Wichtige Stringmethoden

@button:run
@button:copy
```python
eingabe = "  Purple,Orange,Cyan  "

bereinigt = eingabe.strip()
klein = bereinigt.lower()
farben = klein.split(",")

print(farben)
```

| Methode | Wirkung |
|---|---|
| `strip()` | entfernt Leerraum außen |
| `lower()` | wandelt in Kleinbuchstaben um |
| `upper()` | wandelt in Großbuchstaben um |
| `replace(a, b)` | ersetzt Textstellen |
| `split(trenner)` | zerlegt einen String in eine Liste |
| `join(liste)` | verbindet Strings einer Liste |
| `startswith()` | prüft den Anfang |
| `endswith()` | prüft das Ende |
| `isdigit()` | prüft, ob nur Ziffern enthalten sind |

@button:run
@button:copy
```python
farben = ["red", "green", "cyan"]
text = ", ".join(farben)
print(text)
```

## Strings in PyKIM

Farben und Noten sind Strings:

@button:run
@button:copy
```python
from pykim import *

farbe = "orange"
note = "C4"

paint(farbe)
play_tone(note)
run()
```

Wenn Schülerprogramme später Namen, Statusmeldungen oder Punktestände anzeigen, werden Strings mit Zahlen und Zuständen kombiniert.

## Typische Fehler

### Anführungszeichen fehlen

`paint(red)` sucht eine Variable. `paint("red")` übergibt einen String.

### Zahl und Text addieren

`"Punkte: " + 10` führt zu einem `TypeError`. Verwende einen f-String oder `str(10)`.

### Komma statt Punkt

`float("1,5")` funktioniert nicht. Python erwartet `"1.5"`, sofern die Eingabe nicht vorher angepasst wird.

### Groß- und Kleinschreibung

`"Purple" == "purple"` ist `False`. Benutzereingaben können mit `strip().lower()` normalisiert werden.

## Übungen

1. Frage einen Namen ab und begrüße die Person mit einem f-String.
2. Frage zwei ganze Zahlen ab und gib ihre Summe aus.
3. Zähle die Zeichen eines eingegebenen Wortes.
4. Prüfe, ob das Wort `pixel` unabhängig von Großschreibung in einem Text vorkommt.
5. Zerlege `"red,green,cyan"` in eine Liste und male die Farben mit PyKIM.
6. Wiederhole eine Zahleneingabe, bis eine gültige ganze Zahl eingegeben wurde.
7. Gib einen String rückwärts aus, ohne eine fertige Umkehrfunktion zu verwenden.

## Merksatz

`input()` liefert Text. Konvertiere Eingaben bewusst in den benötigten Datentyp und behandle erwartbare Fehler verständlich.
