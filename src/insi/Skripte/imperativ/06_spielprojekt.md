# Projekt: Ein eigenes Spiel planen und entwickeln

Ein Spielprojekt verbindet Variablen, Bedingungen, Schleifen, Funktionen, Listen und interaktive Steuerung. Damit das Projekt nicht an zu vielen Ideen gleichzeitig scheitert, wird es in kleine, überprüfbare Schritte zerlegt.

## 1. Spielidee auswählen

Eine gute erste Spielidee besitzt eine klare Hauptmechanik. Geeignet sind beispielsweise:

- Gegenstände einsammeln
- einem Hindernis ausweichen
- ein Labyrinth durchqueren
- ein Reaktionsspiel
- ein einfaches Memory oder Tic-Tac-Toe
- eine Figur zu einem Ziel bewegen

Formuliere die Idee in einem Satz:

> Die Spielfigur sammelt innerhalb von 30 Sekunden möglichst viele gelbe Punkte und darf die roten Hindernisse nicht berühren.

Ist der Satz sehr lang oder enthält viele `und`, ist die Idee wahrscheinlich noch zu groß.

## 2. Zielgruppe und Bedienung

Halte schriftlich fest:

- Für wen ist das Spiel gedacht?
- Welche Tasten werden benutzt?
- Muss die Steuerung erklärt werden?
- Wie lang dauert eine Runde?
- Woran erkennt man Erfolg oder Misserfolg?

Eine Steuerung sollte im Spiel sichtbar erklärt werden und konsistent bleiben.

## 3. Mindestversion festlegen

Die Mindestversion ist die kleinste vollständig spielbare Fassung.

Beispiel:

1. Ein Spieler wird angezeigt.
2. Er kann mit Pfeiltasten bewegt werden.
3. Ein Gegenstand ist sichtbar.
4. Bei Berührung steigt der Punktestand.
5. Nach einer festgelegten Zeit endet das Spiel.

Musik, Animationen, mehrere Level und besondere Effekte sind Erweiterungen. Sie werden erst begonnen, wenn die Mindestversion zuverlässig funktioniert.

## 4. Storyboard und Bildschirme

Skizziere die wichtigsten Ansichten:

1. Startbildschirm
2. laufendes Spiel
3. Gewinn- oder Verlustbildschirm

Notiere für jede Ansicht:

- sichtbare Elemente
- mögliche Eingaben
- Übergang zur nächsten Ansicht

Das Storyboard muss keine Kunstzeichnung sein. Kästen, Pfeile und Beschriftungen reichen aus.

## 5. Zustand des Spiels

Erstelle eine Tabelle der benötigten Daten:

| Wert | Beispiel | Bedeutung |
|---|---|---|
| `spielzustand` | `"menu"` | aktuelle Ansicht |
| `spieler_x` | `20` | horizontale Position |
| `spieler_y` | `30` | vertikale Position |
| `punkte` | `0` | erreichter Punktestand |
| `zeit` | `30` | verbleibende Sekunden |
| `gegenstaende` | Liste | Positionen der Sammelobjekte |

Diese Übersicht hilft bei der Entscheidung, welche Werte einfache Variablen, Listen oder später Objekte sein sollen.

## 6. Update und Darstellung planen

@button:run
@button:copy
```python
from pykim import *

spieler_x = 20
spieler_y = 20
punkte = 0
spielzustand = "menu"

def update():
    global spieler_x, spieler_y, spielzustand

    if spielzustand == "menu":
        if world.btnp("space"):
            spielzustand = "spiel"
        return

    if world.btn("right"):
        spieler_x += 1
    if world.btn("left"):
        spieler_x -= 1

def draw():
    world.cls("black")

    if spielzustand == "menu":
        world.text(10, 10, "Leertaste: Start", "white")
        return

    world.pset(spieler_x, spieler_y, "yellow")
    world.text(5, 5, f"Punkte: {punkte}", "white")

world.run(update, draw)
```

Der Code ist noch kein vollständiges Spiel. Er bildet aber bereits einen tragfähigen Rahmen.

## 7. In kleinen Schritten entwickeln

Eine sinnvolle Reihenfolge:

1. Fenster öffnen und Hintergrund zeichnen
2. Spieler anzeigen
3. Spieler bewegen
4. Grenzen prüfen
5. ein Ziel oder Objekt anzeigen
6. Kollision erkennen
7. Punktestand verändern
8. Ende des Spiels ergänzen
9. Neustart ermöglichen
10. erst danach Grafik und Audio verfeinern

Nach jedem Schritt wird das Programm gestartet und geprüft. Wenn mehrere neue Funktionen gleichzeitig ergänzt werden, ist die Ursache eines Fehlers schwerer zu finden.

## 8. Kollisionen

Bei einzelnen Pixeln genügt ein Positionsvergleich:

@button:copy
```python
def gleiche_position(x_1, y_1, x_2, y_2):
    return x_1 == x_2 and y_1 == y_2
```

@button:copy
```python
if gleiche_position(spieler_x, spieler_y, ziel_x, ziel_y):
    punkte += 1
```

Für rechteckige Figuren werden später Bereiche miteinander verglichen.

## 9. Funktionen als Aufgabenverteilung

@button:copy
```python
def bewege_spieler():
    pass

def pruefe_kollisionen():
    pass

def aktualisiere_zeit():
    pass

def zeichne_spieler():
    pass

def zeichne_oberflaeche():
    pass
```

Die Namen bilden einen Arbeitsplan. Jede Funktion kann einzeln entwickelt und geprüft werden.

## 10. Testen

Teste nicht nur den Normalfall:

- Was passiert an jeder Weltgrenze?
- Können zwei Objekte dieselbe Position besitzen?
- Kann der Punktestand mehrfach für dieselbe Kollision steigen?
- Funktioniert ein Neustart wirklich mit zurückgesetzten Werten?
- Was passiert bei gleichzeitig gedrückten Tasten?
- Ist jeder Spielzustand erreichbar und wieder verlassbar?

Automatische Tests eignen sich besonders für Funktionen wie Kollisionsprüfung, Punkteberechnung und gültige Bewegungen.

## 11. Dokumentation und Präsentation

Zur Abgabe gehören:

- kurze Beschreibung der Spielidee
- Steuerung und Regeln
- verwendete Konzepte
- bekannte Einschränkungen
- sinnvolle Kommentare im Code
- Quellen für fremde Bilder, Töne oder Ideen
- kurze Reflexion: Was gelang, was war schwierig, was würdest du verbessern?

Bei einer Präsentation sollte zuerst eine funktionierende Runde gezeigt und anschließend eine interessante technische Stelle erklärt werden.

## 12. Erweiterungen

Mögliche Erweiterungen nach der Mindestversion:

- mehrere Level
- steigender Schwierigkeitsgrad
- Musik und Soundeffekte
- Animationen
- Highscore
- Gegner mit einfachem Verhalten
- zufällige oder datenbasierte Level
- eigene Pixelklassen
- Sprites und Tilemaps mit Pyxel

## Bewertungsideen

Ein transparenter Bewertungsbogen kann diese Bereiche getrennt betrachten:

- Funktionalität und Regeln
- sinnvoller Einsatz von Kontrollstrukturen
- Struktur durch Funktionen oder Klassen
- Lesbarkeit und Benennung
- Fehlerbehandlung und Tests
- Gestaltung und Bedienbarkeit
- Dokumentation und Reflexion

Zusatzfunktionen sollten eine funktionierende Grundversion nicht ersetzen.

## Übungen zur Projektvorbereitung

1. Formuliere drei Spielideen jeweils in einem Satz.
2. Wähle eine Idee und beschreibe ihre Mindestversion mit höchstens fünf Punkten.
3. Zeichne ein Storyboard mit drei Ansichten.
4. Erstelle eine Zustandstabelle für dein Spiel.
5. Zerlege die Entwicklung in mindestens acht überprüfbare Schritte.
6. Formuliere fünf Randfälle, die du testen musst.
7. Ordne geplante Funktionen in Pflicht und Erweiterung ein.

## Merksatz

Ein gutes Spieleprojekt wächst aus einer kleinen spielbaren Mindestversion. Planung, schrittweises Testen und klare Zustände sind wichtiger als möglichst viele Funktionen.
