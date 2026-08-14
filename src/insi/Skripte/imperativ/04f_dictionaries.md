# Dictionaries: Werte über Schlüssel zuordnen

Eine Liste ordnet Werte über numerische Indizes. Ein Dictionary verwendet frei wählbare Schlüssel. Dadurch können Zuordnungen direkt ausgedrückt werden, etwa Farbe zu Ton oder Feldtyp zu Darstellung.

## Ein Dictionary anlegen

@button:copy
```python
ton_fuer_farbe = {
    "red": "C4",
    "green": "E4",
    "cyan": "G4",
    "yellow": "C5",
}
```

Jeder Eintrag besteht aus Schlüssel und Wert. Der Doppelpunkt trennt beide, Kommas trennen die Einträge.

## Werte lesen und verändern

@button:copy
```python
print(ton_fuer_farbe["green"])  # E4

ton_fuer_farbe["orange"] = "D4"
ton_fuer_farbe["red"] = "C3"
```

Ein neuer Schlüssel ergänzt einen Eintrag. Ein vorhandener Schlüssel wird überschrieben.

Ein unbekannter Schlüssel führt beim direkten Zugriff zu einem `KeyError`:

```text
ton_fuer_farbe["purple"]
```

`get()` erlaubt einen Standardwert:

@button:copy
```python
note = ton_fuer_farbe.get("purple", "PAUSE")
```

## Schlüssel prüfen

@button:copy
```python
farbe = "red"

if farbe in ton_fuer_farbe:
    print(ton_fuer_farbe[farbe])
```

`in` prüft bei einem Dictionary standardmäßig die Schlüssel.

## Durch Dictionaries laufen

@button:copy
```python
for farbe in ton_fuer_farbe:
    print(farbe)
```

Schlüssel und Wert gemeinsam:

@button:copy
```python
for farbe, note in ton_fuer_farbe.items():
    print(f"{farbe} wird zu {note}")
```

Nur Werte liefert `values()`, nur Schlüssel ausdrücklich `keys()`.

## Farbmelodie ohne lange elif-Kette

@button:run
@button:copy
```python
from pykim import *

ton_fuer_farbe = {
    "red": "C4",
    "green": "E4",
    "cyan": "G4",
    "yellow": "C5",
}

farbe = get_color()
note = ton_fuer_farbe.get(farbe)

if note is None:
    play_pause()
else:
    play_tone(note)

run()
```

Die Zuordnung ist nun ein eigener Datenbestand. Eine weitere Farbe wird durch einen neuen Dictionary-Eintrag ergänzt, nicht durch zusätzliche Kontrollstruktur.

## Strukturierte Datensätze

@button:run
@button:copy
```python
figur = {
    "name": "MIA",
    "x": 20,
    "y": 30,
    "farbe": "orange",
    "sichtbar": True,
}

print(figur["name"])
figur["x"] += 1
```

Für einfache Datensätze ist das praktisch. Besitzt eine Figur zusätzlich viel Verhalten, ist später eine Klasse geeigneter.

## Verschachtelte Strukturen

@button:run
@button:copy
```python
level = {
    "name": "Wald",
    "start": [2, 3],
    "ziel": [8, 7],
    "farben": {
        "wand": "green",
        "weg": "brown",
    },
}

print(level["farben"]["wand"])
```

Listen und Dictionaries können sich gegenseitig enthalten. Achte bei tiefen Strukturen besonders auf verständliche Namen und kleine Verarbeitungsfunktionen.

## Typische Fehler

### Schlüssel und Wert verwechselt

In `ton_fuer_farbe["red"]` ist `"red"` der Schlüssel und `"C4"` der gespeicherte Wert.

### Fehlenden Schlüssel direkt lesen

Prüfe mit `in` oder verwende `get()`, wenn ein Eintrag fehlen darf.

### Während der Iteration Größe verändern

Füge während eines direkten Dictionary-Durchlaufs keine Schlüssel hinzu und entferne keine. Arbeite bei Bedarf mit `list(dictionary)` als Kopie der Schlüssel.

### Dictionary statt Klasse

Wenn dieselben Schlüssel an vielen Stellen erwartet und viele Operationen darauf ausgeführt werden, kann eine Klasse Fehler vermeiden und Verhalten bündeln.

## Übungen

1. Lege ein Dictionary an, das vier Farbnamen auf Noten abbildet.
2. Gib alle Zuordnungen mit `items()` aus.
3. Frage einen Farbnamen ab und verwende bei unbekannter Farbe eine Pause.
4. Speichere Name, Position und Punktestand einer Figur in einem Dictionary.
5. Erstelle ein Dictionary für Feldtypen eines Labyrinths und ihre PyKIM-Farben.
6. Begründe, wann eine Liste, ein Dictionary oder eine Klasse geeigneter ist.

## Merksatz

Dictionaries speichern Zuordnungen von eindeutigen Schlüsseln zu Werten. Sie ersetzen häufig lange Such- oder Fallunterscheidungen durch gut lesbare Daten.
