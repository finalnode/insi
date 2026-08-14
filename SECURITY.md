# Sicherheit

PyKIM und die Lernumgebung in:si sind Lernsoftware im Alpha-Stadium. Kurse
und Schülerprogramme können Pythoncode enthalten. Pythoncode ist grundsätzlich
in der Lage, mit den Rechten des angemeldeten Benutzers auf Dateien, Netzwerk
und andere Systemfunktionen zuzugreifen.

## Vertrauensgrenzen

Die Anwendung unterscheidet konzeptionell drei Codequellen:

| Quelle | Beispiel | Annahme |
|---|---|---|
| mitgeliefert | Beispiele der installierten App | Teil des geprüften Releases |
| Kurs | ausführbare Blöcke und Startercode | kann aus einer externen Quelle stammen |
| Schüler | Aufgabenlösungen und Projekte | lokal bearbeitet, möglicherweise fehlerhaft |

Kursimport und Codeausführung sind getrennte Vorgänge. Beim Import wird auf die
externe Quelle und die noch fehlende garantierte Betriebssystem-Sandbox
hingewiesen. Ein Import führt den enthaltenen Pythoncode nicht automatisch aus.

## Heute aktive Schutzmaßnahmen

In der Suite gestarteter Lerncode:

- läuft in einem eigenen Prozess,
- erhält keine typischen Token-, Passwort-, Schlüssel- oder
  SSH-Agent-Umgebungsvariablen,
- erhält keine `PYTHONSTARTUP`-/`PYTHONINSPECT`-Hooks aus der Elternumgebung,
- besitzt bei integrierten Aufgabenläufen eine Laufzeitgrenze,
- besitzt eine Grenze für die in der Oberfläche gespeicherte Ausgabe,
- wird als eigene Prozessgruppe gestartet und kann von der Suite gestoppt
  werden,
- darf von der Suite nur über validierte Dateien innerhalb des Kursordners
  gestartet werden.

Kursarchive werden außerdem vor der Installation gegen absolute Pfade,
Verzeichnisausbrüche und eine unerwartete Struktur geprüft. Schülerarbeit liegt
getrennt von aktivierten Kursinhalten und wird bei Inhaltsupdates nicht
überschrieben.

## Heute ausdrücklich nicht garantiert

Ein getrennter Prozess ist **keine Sandbox**. Derzeit gelten insbesondere noch
keine garantierten technischen Grenzen für:

- Lese- oder Schreibzugriffe außerhalb des Student Workspace,
- Netzwerkzugriffe,
- Betriebssystem-APIs und gestartete Kindprozesse,
- CPU- und Arbeitsspeicherverbrauch auf allen Plattformen,
- absichtlich schädlichen Code aus einer vertrauten oder fremden Kursquelle.

Die Anwendung zeigt diesen Zustand im Systemcheck an. Kurse sollten deshalb nur
aus nachvollziehbaren Quellen importiert werden.

## Geplantes Sandbox-Modell

Die Suite soll keine eigene Sicherheits-Sandbox implementieren. Stattdessen
wird eine gemeinsame Runner-Schnittstelle betriebssystemspezifische, vorhandene
Sandbox-Mechanismen erkennen und – nach überprüfter Konfiguration – verwenden.
Ohne verfügbaren Adapter bleibt die geringere Schutzstufe sichtbar.

Die Richtlinie arbeitet mit expliziten Fähigkeiten:

- lesbare Programm- und Laufzeitdateien,
- definierte schreibbare Workspace-Verzeichnisse,
- optionaler Netzwerkzugriff,
- Laufzeit-, Ausgabe-, Prozess- und später Speichergrenzen.

Persistenz wird nicht pauschal verboten. Ein Kursprojekt darf innerhalb seines
freigegebenen Workspace beispielsweise SQLite-Datenbanken, Ressourcen und
weitere Projektdaten anlegen. Zugriffe außerhalb dieser Bereiche sollen ein
späterer OS-Sandbox-Adapter verhindern.

## Sicherheitslücken melden

Bitte veröffentliche reproduzierbare Exploits, Zugangsdaten oder sensible
Schülerdaten nicht in einem öffentlichen Issue. Kontaktiere zunächst den
Repository-Inhaber über das GitHub-Profil, bis ein eigener privater
Meldekanal eingerichtet ist. Allgemeine Härtungsvorschläge ohne vertrauliche
Details können als GitHub-Issue eingereicht werden.
