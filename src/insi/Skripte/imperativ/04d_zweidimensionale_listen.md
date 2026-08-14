# Zweidimensionale Listen als Spielfelder

Eine eindimensionale Liste ordnet Werte hintereinander an. Für Brettspiele, Labyrinthe, Level und Tilemaps werden Zeilen und Spalten benötigt. Eine Liste aus Listen bildet eine solche zweidimensionale Struktur.

## Von einzelnen Zeilen zum Spielfeld

@button:copy
```python
zeile_0 = ["purple", "orange", "purple"]
zeile_1 = ["orange", "purple", "orange"]
zeile_2 = ["purple", "orange", "purple"]

spielfeld = [zeile_0, zeile_1, zeile_2]
```

Kürzer wird dieselbe Struktur direkt notiert:

@button:copy
```python
spielfeld = [
    ["purple", "orange", "purple"],
    ["orange", "purple", "orange"],
    ["purple", "orange", "purple"],
]
```

Die äußere Liste enthält drei Zeilen. Jede Zeile ist wiederum eine Liste mit drei Spalten.

## Zugriff mit zwei Indizes

@button:copy
```python
print(spielfeld[0])     # gesamte erste Zeile
print(spielfeld[0][1])  # orange
print(spielfeld[2][2])  # purple
```

Der erste Index wählt die Zeile, der zweite die Spalte: `spielfeld[zeile][spalte]`.

| | Spalte 0 | Spalte 1 | Spalte 2 |
|---|---|---|---|
| Zeile 0 | purple | orange | purple |
| Zeile 1 | orange | purple | orange |
| Zeile 2 | purple | orange | purple |

## Werte verändern

@button:copy
```python
spielfeld[1][2] = "cyan"
```

Damit wird genau das Feld in Zeile 1, Spalte 2 verändert.

Eine Spielfigur kann in den Daten verschoben werden:

@button:copy
```python
spielfeld = [
    ["K", "", ""],
    ["", "", ""],
    ["", "", ""],
]

spielfeld[0][1] = spielfeld[0][0]
spielfeld[0][0] = ""
```

Zuerst wird der Wert ins Zielfeld kopiert, danach wird das alte Feld geleert.

## Alle Felder durchlaufen

@button:copy
```python
for zeile in spielfeld:
    for feld in zeile:
        print(feld)
```

Wenn die Koordinaten gebraucht werden, ist `enumerate()` passend:

@button:copy
```python
for zeilen_index, zeile in enumerate(spielfeld):
    for spalten_index, feld in enumerate(zeile):
        print(zeilen_index, spalten_index, feld)
```

## Das Spielfeld mit PyKIM zeichnen

@button:run
@button:copy
```python
from pykim import *

spielfeld = [
    ["purple", "orange", "purple"],
    ["orange", "purple", "orange"],
    ["purple", "orange", "purple"],
]

start_x = 20
start_y = 20

for zeile, farbreihe in enumerate(spielfeld):
    for spalte, farbe in enumerate(farbreihe):
        set_position(start_x + spalte, start_y + zeile)
        paint(farbe)

run()
```

Hier sind **Daten** und **Darstellung** getrennt:

- `spielfeld` speichert, was sich an einer Position befindet.
- Die verschachtelten Schleifen entscheiden, wie die Daten gezeichnet werden.

Diese Trennung ist für Spiele zentral. Später kann dieselbe Datenstruktur anders dargestellt werden, ohne die Spielregeln zu verändern.

## Ein Labyrinth codieren

@button:copy
```python
level = [
    [1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1],
    [1, 0, 1, 0, 1],
    [1, 0, 0, 2, 1],
    [1, 1, 1, 1, 1],
]
```

Eine mögliche Bedeutung:

- `0`: freier Weg
- `1`: Wand
- `2`: Ziel

@button:copy
```python
def farbe_fuer_feld(wert):
    if wert == 1:
        return "gray"
    if wert == 2:
        return "yellow"
    return "black"
```

Die Zahlen sind kompakte Zustände. Eine Funktion übersetzt sie für die Darstellung in Farben.

## Kollisionen prüfen

@button:copy
```python
def ist_frei(level, zeile, spalte):
    if not 0 <= zeile < len(level):
        return False
    if not 0 <= spalte < len(level[zeile]):
        return False
    return level[zeile][spalte] != 1
```

Zuerst werden die Grenzen geprüft. Erst danach wird auf das Feld zugegriffen. So wird ein `IndexError` vermieden.

## Ein leeres Feld erzeugen

@button:copy
```python
breite = 8
hoehe = 6
spielfeld = []

for _ in range(hoehe):
    zeile = ["black"] * breite
    spielfeld.append(zeile)
```

Vorsicht bei dieser scheinbar kürzeren Form:

```text
spielfeld = [["black"] * breite] * hoehe
```

Alle Zeilen verweisen dabei auf dieselbe innere Liste. Eine Änderung in einer Zeile erscheint dann unerwartet in allen Zeilen.

## Rechteckige und unregelmäßige Listen

Python verlangt nicht, dass jede Zeile gleich lang ist:

@button:copy
```python
dreieck = [
    [1],
    [1, 1],
    [1, 1, 1],
]
```

Für ein normales Spielfeld sind gleich lange Zeilen meist sinnvoll. `len(spielfeld)` liefert die Höhe, `len(spielfeld[0])` bei einem nichtleeren rechteckigen Feld die Breite.

## Typische Fehler

### Zeile und Spalte vertauscht

Lege im gesamten Projekt eine Reihenfolge fest, beispielsweise immer `[zeile][spalte]` beziehungsweise `[y][x]`.

### Grenze erst nach Zugriff prüfen

`level[zeile][spalte]` kann bereits einen Fehler auslösen. Prüfe die Indizes vorher.

### Daten und Zeichnen vermischen

Wenn Spiellogik nur über bereits gemalte Pixel arbeitet, wird sie schwer testbar. Speichere den Zustand möglichst in einer Datenstruktur.

### Gemeinsame Zeilenreferenz

Verwende beim Erzeugen einer Matrix für jede Zeile eine neue Liste.

## Übungen

1. Lege ein 3-mal-3-Tic-Tac-Toe-Feld aus leeren Strings an.
2. Setze ein `"X"` in die Mitte und ein `"O"` oben links.
3. Gib das gesamte Feld mit zwei Schleifen aus.
4. Zeichne ein 8-mal-8-Schachmuster mit PyKIM.
5. Codiere ein kleines Labyrinth mit `0`, `1` und `2` und zeichne es farbig.
6. Schreibe `ist_frei()`, das Grenzen und Wände prüft.
7. Erzeuge ein Memory-Feld aus Symbolpaaren und mische die Werte vor dem Einordnen.

## Merksatz

Eine zweidimensionale Liste speichert Werte in Zeilen und Spalten. Sie trennt den Zustand eines Spielfelds von seiner grafischen Darstellung.
