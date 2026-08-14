# Herkunft und Übertragung des PyKIM-Skripts

Die ausführlichen Grundlagen orientieren sich didaktisch am bereitgestellten
Turtle-Kursskript aus `turtle.zip`. Allgemeine Python-Themen wurden erhalten,
inhaltlich überarbeitet und mit PyKIM-Beispielen neu formuliert.

## Übertragungsprinzipien

- Allgemeine Python-Erklärungen bleiben ausführlich erhalten.
- Turtle-Bewegungen und Zeichenbefehle werden nicht wortwörtlich umbenannt,
  sondern passend zum Koordinaten- und Malmodell von PyKIM erklärt.
- Turtle-Ereignisschleifen werden durch `world.run(update, draw)` ersetzt.
- Mehrere Turtle-Instanzen und Threads werden über getrennte Pixelobjekte und
  `world.parallel()` didaktisch sicher eingeführt.
- Turtle-Fenster, Shapes, GUI-Elemente und Spielkonzepte führen zu den
  entsprechenden Welt- und Pyxel-Konzepten.
- Jedes Kapitel enthält Begriffe, aufbauende Beispiele, typische Fehler,
  Übungen und einen Merksatz.

Die Quelldateien bleiben bewusst normales Markdown, damit Lehrkräfte Inhalte
ohne Änderungen am Python-Code der Suite bearbeiten und ergänzen können.

## Aktionen an Codeblöcken

Schaltflächen werden direkt in Markdown festgelegt. Eine Direktive gilt nur
für den unmittelbar folgenden `python`-Codeblock:

````markdown
@button:run
@button:copy
```python
print("Hallo")
```
````

Mögliche Direktiven:

- `@button:run` zeigt **Ausführen** und gibt den Block für den lokalen Runner frei.
- `@button:copy` zeigt **Kopieren**.
- Beide Direktiven kombinieren beide Aktionen; ihre Reihenfolge ist egal.
- Ohne Direktive erhält ein Skriptblock keine Aktionsschaltfläche.

`@button:run` ist ausschließlich für **eigenständige Programme** gedacht:

- Konsolenbeispiele müssen eine sichtbare Ausgabe erzeugen.
- PyKIM-Beispiele benötigen den Import und abschließend `run()` oder
  `world.run(...)`.
- Ausschnitte, die Variablen aus einem vorherigen Block voraussetzen, erhalten
  nur `@button:copy`.
- Blöcke mit `input()` oder absichtlichem `pass` sind nicht direkt startbar.

Zwischen Direktive und Codezaun darf kein Text und keine Leerzeile stehen,
damit die Zuordnung eindeutig bleibt. Die Direktiven selbst werden in der
Suite nicht angezeigt. Nur exakt mit `@button:run` markierter, unveränderter
Paketcode wird von der lokalen Ausführungsschnittstelle akzeptiert.

Die automatisierte Qualitätsprüfung klassifiziert sämtliche Run-Blöcke und
führt Konsolen- sowie PyKIM-Programme mit `PYKIM_HEADLESS=1` vollständig ohne
Grafikfenster aus. Das Pflegewerkzeug `tools/curate_script_examples.py`
entfernt ungeeignete Run-Markierungen reproduzierbar.
