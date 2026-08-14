# Eigene Klassen, Vererbung und Polymorphie

Eine Klasse ist ein Bauplan für Objekte. Sie beschreibt, welche Daten Instanzen besitzen und welche Methoden sie anbieten. Eigene Pixelklassen verbinden Programmierkonzepte mit sichtbarem Verhalten.

## Eine einfache Klasse

@button:run
@button:copy
```python
class Punktestand:
    def __init__(self, startwert=0):
        self.wert = startwert

    def erhoehen(self, anzahl=1):
        self.wert += anzahl

    def text(self):
        return f"Punkte: {self.wert}"

punkte = Punktestand()
punkte.erhoehen(5)
print(punkte.text())
```

## Konstruktor und self

`__init__()` wird beim Erzeugen einer Instanz aufgerufen:

@button:copy
```python
punkte = Punktestand()
```

`self` bezeichnet innerhalb einer Methode genau die Instanz, auf der die Methode aufgerufen wurde. `self.wert` ist deshalb für jedes Objekt getrennt.

@button:copy
```python
team_rot = Punktestand()
team_blau = Punktestand(10)

team_rot.erhoehen(2)
print(team_rot.wert)   # 2
print(team_blau.wert)  # 10
```

## Eigene Pixelklasse durch Vererbung

@button:copy
```python
from pykim import Pixel

class MusikPixel(Pixel):
    def __init__(self, pixel_world, name, x, y, note, color="purple"):
        super().__init__(pixel_world, name, x, y)
        self.note = note
        self.color = color

    def spiele_note(self):
        self.play_tone(self.note)
```

`MusikPixel` erbt von `Pixel`:

- vorhandene Attribute und Methoden können weiterverwendet werden,
- neue Attribute wie `note` kommen hinzu,
- neue Methoden wie `spiele_note()` ergänzen das Verhalten.

## super

@button:copy
```python
super().__init__(pixel_world, name, x, y)
```

Dieser Aufruf initialisiert den geerbten Pixelanteil. Ohne ihn fehlen möglicherweise Position, Weltbezug und weitere notwendige Attribute.

Die Unterklasse initialisiert anschließend ihre zusätzlichen Daten:

@button:copy
```python
self.note = note
self.color = color
```

## Methoden überschreiben

Eine Unterklasse kann geerbtes oder erwartetes Verhalten spezialisieren:

@button:copy
```python
class MusikPixel(Pixel):
    def __init__(self, pixel_world, name, x, y, note):
        super().__init__(pixel_world, name, x, y)
        self.note = note

    def update(self):
        if self.world.btnp("space"):
            self.play_tone(self.note)

    def draw(self):
        self.world.pset(self.x, self.y, "yellow")
```

`update()` beschreibt das Verhalten pro Frame, `draw()` die Darstellung.

## Mehrere Instanzen

@button:copy
```python
hoch = MusikPixel(world, "HOCH", 20, 20, "C5")
tief = MusikPixel(world, "TIEF", 30, 20, "C3")
```

Beide Objekte folgen demselben Bauplan, besitzen aber unterschiedliche Namen, Positionen und Noten.

## Polymorphie

Verschiedene Klassen können dieselben Methodennamen unterschiedlich umsetzen:

@button:copy
```python
figuren = [hoch, tief]

for figur in figuren:
    figur.update()
```

Die Schleife muss nicht wissen, welche konkrete Unterklasse vorliegt. Entscheidend ist, dass jedes Objekt eine passende `update()`-Methode anbietet. Dieses gemeinsame Verwenden verschiedener Objekttypen heißt Polymorphie.

## Komposition statt Vererbung

Nicht jede Beziehung ist eine Vererbung:

- Ein MusikPixel **ist ein** Pixel: Vererbung kann passen.
- Ein Spiel **hat einen** Punktestand: Komposition ist passender.

@button:copy
```python
class Spiel:
    def __init__(self):
        self.punkte = Punktestand()
```

Komposition verbindet Objekte, ohne sie als spezielle Form voneinander darzustellen.

## Kapselung

Ein Objekt sollte seinen Zustand möglichst über verständliche Methoden verändern:

@button:copy
```python
punkte.erhoehen(5)
```

ist aussagekräftiger als beliebige Änderungen an mehreren internen Variablen. Die Klasse kann später Prüfungen ergänzen, ohne dass alle Aufrufstellen geändert werden müssen.

## Typische Fehler

### self vergessen

Instanzmethoden erhalten `self` als ersten Parameter. Auch Attribute werden als `self.name` gespeichert.

### Lokale Variable statt Attribut

```text
def __init__(self, note):
    note = note
```

Hier wird kein Zustand am Objekt gespeichert. Richtig ist `self.note = note`.

### super nicht aufgerufen

Die Basisklasse bleibt unvollständig initialisiert.

### Vererbung nur zur Codewiederverwendung

Vererbung sollte eine sinnvolle „ist-ein“-Beziehung ausdrücken. Sonst ist ein enthaltenes Hilfsobjekt oft flexibler.

### Eine Klasse erledigt alles

Eine große `Spiel`-Klasse mit Welt, Figuren, Eingabe, Punkten, Audio und Leveldaten wird schwer wartbar. Teile Verantwortlichkeiten auf mehrere Klassen auf.

## Übungen

1. Implementiere eine Klasse `Punktestand` mit `erhoehen()`, `zuruecksetzen()` und `text()`.
2. Erzeuge zwei unabhängige Punktestände und zeige, dass ihre Werte getrennt bleiben.
3. Leite `FarbPixel` von `Pixel` ab und ergänze ein Farbattribut.
4. Entwickle `MusikPixel` mit einer eigenen Note.
5. Überschreibe `update()` und `draw()` für zwei unterschiedliche Pixelklassen.
6. Speichere verschiedene Unterklassen in einer Liste und rufe einheitlich `update()` auf.
7. Entscheide für drei Beziehungen, ob Vererbung oder Komposition besser passt, und begründe die Wahl.

## Merksatz

Klassen sind Baupläne für Objekte. Vererbung spezialisiert eine sinnvolle „ist-ein“-Beziehung; Komposition verbindet Objekte in einer „hat-ein“-Beziehung.
