# Objekte: Welt und Pixel trennen

In einem rein imperativen Programm werden Position, Farbe und Sichtbarkeit häufig in einzelnen Variablen gespeichert. Bei mehreren Spielfiguren entstehen schnell viele zusammengehörige Namen. Objekte bündeln Zustand und Verhalten.

## Mehrere Zustände mit einzelnen Variablen

@button:copy
```python
kim_x = 20
kim_y = 20
kim_farbe = "purple"

mia_x = 30
mia_y = 20
mia_farbe = "orange"
```

Das funktioniert, aber die Zugehörigkeit besteht nur in den Namen. Eine Funktion müsste viele einzelne Werte erhalten oder verändern.

## Pixel als Objekte

@button:run
@button:copy
```python
from pykim import *

mia = world.new_pixel("MIA", 30, 20)
leo = world.new_pixel("LEO", 40, 20)

mia.paint("orange")
mia.right(10)
mia.paint_stop()

leo.paint("cyan")
leo.down(8)
leo.paint_stop()

run()
```

`mia` und `leo` verweisen auf verschiedene Pixelobjekte. Beide besitzen eigene Position, eigenen Malzustand und eigene Sichtbarkeit.

## Attribute und Methoden

Ein Objekt verbindet:

- **Attribute:** gespeicherter Zustand, etwa Name oder Position
- **Methoden:** Verhalten, etwa `right()`, `paint()` oder `hide()`

Die Punktschreibweise wählt aus, welches Objekt handeln soll:

@button:copy
```python
mia.right(5)
leo.right(5)
```

Der Methodenname ist gleich, aber der Zustand unterschiedlicher Objekte wird verändert.

Positionen sind im Objektweg Eigenschaften statt Getter-Methoden:

@button:copy
```python
print(mia.x)
print(mia.y)
print(mia.position)

mia.x = 40
mia.position = (50, 30)
```

Die älteren Methoden `get_x()`, `get_y()` und `set_position(...)` bleiben
kompatibel, werden im OOP-Lernweg aber nicht mehr aktiv verwendet.

## Die Welt als eigenes Objekt

`world` besitzt Aufgaben, die nicht zu einem einzelnen Pixel gehören:

@button:copy
```python
world.cls("black")
world.pset(10, 10, "yellow")
world.btn("right")
world.play_tone("C4")
world.run(update, draw)
```

Die Trennung lautet:

- Ein Pixel kennt seinen eigenen Zustand und seine Bewegungen.
- Die Welt verwaltet Anzeige, Eingaben, Töne, gemeinsames Zeichnen und mehrere Pixel.

Ein Pixel darf ebenfalls einen Ton auslösen, beispielsweise
`mia.play_tone("E4")`. Welt und Pixel verwenden dabei dasselbe Audiosystem.

Diese Zuständigkeiten werden später bei eigenen Klassen wichtig.

## Referenzen auf Objekte

@button:copy
```python
mia = world.new_pixel("MIA", 30, 20)
freundin = mia

freundin.right(5)
```

`mia` und `freundin` bezeichnen hier dasselbe Objekt. Es wurde kein zweites Pixel erzeugt. Änderungen über einen Namen sind über den anderen sichtbar.

## Objekte in Listen

@button:run
@button:copy
```python
from pykim import *

pixel = [
    world.new_pixel("MIA", 20, 20),
    world.new_pixel("LEO", 30, 20),
    world.new_pixel("NOA", 40, 20),
]

for figur in pixel:
    figur.paint("orange")
    figur.down(5)
    figur.paint_stop()

run()
```

Alle Listenelemente bieten dieselben Pixelmethoden. Eine Schleife kann sie deshalb einheitlich behandeln.

## Sequenziell und parallel

Normalerweise werden Aktionen nacheinander animiert:

@button:copy
```python
mia.right(10)
leo.down(10)
```

Mit dem Weltkontext werden Aktionen gemeinsam abgespielt:

@button:copy
```python
with world.parallel():
    mia.right(10)
    leo.down(10)
```

Das ist ein didaktisches Parallelmodell der Welt, keine Aufforderung, eigene Threads zu programmieren. Die Welt koordiniert die Animation kontrolliert.

## Sichtbarkeit und Lebenszyklus

@button:copy
```python
leo.hide()
leo.show()
```

Sichtbarkeit ist Zustand des Pixelobjekts. Verstecken löscht nicht automatisch bereits gezeichnete Linien und zerstört das Objekt nicht.

## Typische Fehler

### Methode am falschen Objekt

`world.right()` ist keine Pixelbewegung. `mia.right()` bewegt MIA.

### Neues Objekt erwartet

`freundin = mia` erzeugt keine Kopie. Für ein weiteres Pixel wird `world.new_pixel(...)` verwendet.

### Zustand doppelt speichern

Zusätzliche Variablen `mia_x` und `mia_y` können von der tatsächlichen Objektposition abweichen. Nutze möglichst den Zustand des Objekts als eindeutige Quelle.

### Parallelität mit Threads verwechseln

`world.parallel()` plant PyKIM-Aktionen gemeinsam. Es vermeidet die Komplexität und Fehlergefahren echter Threads.

## Übungen

1. Erzeuge zwei benannte Pixel an verschiedenen Positionen.
2. Gib beiden unterschiedliche Farben und Wege.
3. Speichere drei Pixel in einer Liste und bewege sie mit einer Schleife.
4. Kombiniere eine sequenzielle mit einer parallelen Phase.
5. Verstecke ein Pixel erst nach seiner letzten Bewegung und erkläre den Unterschied zwischen Sichtbarkeit und Zeichnung.
6. Ordne verschiedene Operationen entweder der Welt oder einem Pixel zu und begründe die Zuständigkeit.

## Merksatz

Ein Objekt bündelt zusammengehörigen Zustand und passendes Verhalten. Die Welt und ihre Pixel sind getrennte Objekte mit unterschiedlichen Verantwortlichkeiten.
