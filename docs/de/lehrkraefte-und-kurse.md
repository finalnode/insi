# Lehrkräfte und Kursautoren

in:si-Kurse bestehen aus normalen Dateien. Skripte verwenden Markdown,
Programmieraufgaben kombinieren Markdown mit deklarativen Trainerdefinitionen,
und Projekte bleiben echte Quellordner. Ein Kurs kann lokal bearbeitet, als ZIP
weitergegeben oder über ein Repository veröffentlicht werden.

## Kursstruktur

Eine typische Kursquelle enthält:

```text
Skripte/
Aufgaben/
Trainer/
runtime.toml
*.insi-setup
```

Die Setupdatei beschreibt Kursname, verantwortliche Person, optionale Schule,
Pfade und gegebenenfalls das Kursrepository. `runtime.toml` hält Pythonversion
und benötigte Pakete nachvollziehbar fest.

## Kursstudio

Das Kursstudio bearbeitet Skripte und Aufgaben wahlweise visuell oder als
Markdown. Kanonisch gespeichert wird ausschließlich Markdown. Das
Annotationsmenü fügt nur bekannte in:si-Metadaten ein; der Validator meldet
Probleme mit Zeilennummern.

Aufgabenmetadaten wie Schwierigkeit, Tags, Hinweise, Quellen und Anforderungen
werden als eigene Felder bearbeitet und beim Speichern wieder in portable
Kursdateien übertragen.

## Trainer

Das Format `insi-trainer-v1` trennt die Plattform von der fachlichen Engine.
`pykim` bewertet Pythoncode und die Pixelwelt. `core` stellt freie Antworten,
Zuordnungen und Parsons-Puzzles bereit. Weitere Fachmodule können eine Engine
über den Entry-Point `insi.trainer_backends` registrieren.

Trainerdateien sind Daten, dürfen aber fachliche Auswertungen an eine
registrierte Engine übergeben. Aus Markdown-Metadaten wird kein beliebiger
Pythoncode erzeugt.

## Veröffentlichung

Vor der Weitergabe sollten mindestens geprüft werden:

1. Setupdatei und Verzeichnisstruktur sind valide.
2. Quellen und Lizenzen sämtlicher Kursmaterialien sind angegeben.
3. `runtime.toml` verwendet konkrete, offline bereitstellbare Versionen.
4. Alle ausführbaren Beispiele und Trainer laufen in einer frischen Umgebung.
5. Das Kurs-ZIP enthält keine Lösungen, privaten Schlüssel oder personenbezogene
   Lernstände.
6. Die Nutzung von Netzwerk, Dateien und externen Programmen ist dokumentiert.

## Verantwortung

in:si zeigt Kursname, Lehrkraft beziehungsweise verantwortliche Person,
Organisation, Repository, Quellen und Lizenzinformationen sichtbar an. Ein
Kursimport ersetzt keine fachliche, urheberrechtliche oder sicherheitstechnische
Prüfung durch die veröffentlichende Person.

Ausführliche Formatdetails stehen in [TRAINER_AUTOREN.md](../../TRAINER_AUTOREN.md).
