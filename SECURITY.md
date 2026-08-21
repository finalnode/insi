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

Kursimport und Codeausführung sind getrennte Vorgänge. Ein Import führt den
enthaltenen Pythoncode nicht automatisch aus.

## Verbindlicher Runner-Vertrag ab 0.7.0

Externer Kurs- und Schülercode wird innerhalb von in:si nur gestartet, wenn ein
verifizierter Betriebssystemadapter die angeforderte Richtlinie tatsächlich
umsetzen kann. Ist der Adapter nicht verfügbar oder schlägt sein Probelauf fehl,
wird die Ausführung abgelehnt. Es gibt keinen stillen Start mit normalen
Benutzerrechten.

Die vertrauenswürdige in:si-Oberfläche ist der Broker für Dateiimporte,
Speichern, Lernstand und Backups. Der getrennte Runner erhält pro Start nur die
notwendigen Fähigkeiten:

| Bereich | Aufgabenlauf | Projektlauf |
|---|---|---|
| gestartete Datei | nur lesbar | innerhalb des Projekts |
| privater Laufbereich | schreibbar, danach verworfen | temporäre Systemdaten |
| aktuelles Projekt | nicht sichtbar | les- und schreibbar |
| andere Projekte | nicht sichtbar | nicht sichtbar |
| Kurs- und globale Dateien | nur lesbar | nur lesbar |
| Runtime und aktive Kursinhalte | nur lesbar | nur lesbar |
| interne `.pykim`-Daten und Hostdateien | nicht sichtbar | nicht sichtbar |
| Netzwerk | gesperrt | gesperrt |

Der Kurs- und globale Dateiimport kopiert genau eine reguläre Datei in den
gewählten Workspace. Externe Pfade und symbolische Links werden nicht als
dauerhafte Berechtigung übernommen. Projekte mit symbolischen Links starten nur
in einer externen IDE.

## Prozessaufsicht

Jeder integrierte Lauf:

- läuft in einem eigenen Prozess,
- erhält ein temporäres Home-Verzeichnis und nur eine kleine
  Umgebungsvariablen-Allowlist;
- erhält weder Host-`PYTHONPATH` noch D-Bus-, Proxy-, SSH-, GPG- oder typische
  Token-/Passwortvariablen;
- wird auf Laufzeit, CPU-Zeit, Arbeitsspeicher, Prozessanzahl, Ausgabe und neu
  geschriebenes Datenvolumen überwacht;
- wird bei einer Verletzung samt kompletter Prozessgruppe beendet;
- zeigt den konkreten Abbruchgrund in der Oberfläche.

Die Standardgrenzen sind 300 Sekunden Laufzeit, 120 Sekunden CPU-Zeit, 512 MB
Arbeitsspeicher, 16 Prozesse, eine Million Ausgabezeichen je Kanal und 100 MB
neu geschriebene Daten. Diese Grenzen reduzieren unbeabsichtigte Endlosschleifen,
Forkbomben, Ausgabefluten und das Füllen des Workspaces. Sie ersetzen keine
Kernel-Sicherheitsgrenze.

Vor einem integrierten Projektstart legt in:si außerhalb der Sicht des Runners
einen Snapshot an und behält höchstens zehn Stände je Projekt. Aufgabenläufe
schreiben ihren Lernstand zunächst in eine private Kopie; nur strukturell und
größenmäßig validierte neue Trainer-Versuche werden anschließend übernommen.

## Plattformstatus

| Plattform | Integrierter Fremdcode | Grafik | Verhalten ohne Schutz |
|---|---|---|---|
| Linux | Bubblewrap nach echtem Namespace-Probelauf | nur über Wayland | Start gesperrt, IDE bleibt verfügbar |
| Windows | AppContainer und Job Object nach echtem Isolationstest | AppContainer-Fenster | Start gesperrt, IDE bleibt verfügbar |
| macOS | Seatbelt nach echtem Datei-, Netzwerk- und Prozessprobelauf | Seatbelt-Fenster | Start gesperrt, IDE bleibt verfügbar |

Bubblewrap konstruiert unter Linux getrennte Mount-, Prozess- und
Netzwerk-Namespaces. `bwrap` muss als Systemkomponente installiert sein; in:si
verlässt sich nicht allein auf dessen Dateinamen, sondern führt einen Probelauf
aus, der eine Hostdatei unverändert und unsichtbar halten, Netzwerk- und
Schreibzugriffe außerhalb blockieren, einen anderen Netzwerk-Namespace zeigen
und einen geerbten Kindprozess ausführen muss. `/tmp` und `HOME` liegen in einem
privaten, nach dem Lauf gelöschten Verzeichnis und zählen gegen dieselbe
Schreibgrenze wie der Workspace. Für GUI-Zugriff werden nur vorhandene
Wayland-, PipeWire- und Pulse-Sockets einzeln eingebunden; ein gemeinsamer
X11-Socket wird absichtlich nicht freigegeben.

Unter Windows startet ein vertrauenswürdiger Broker für jeden Lauf ein eigenes,
temporäres AppContainer-Profil. Nur Runtime und ausgewählte Kursdateien erhalten
für dessen SID Leserechte; ausschließlich die vorgesehenen Lauf- und
Projektordner erhalten Schreibrechte. Die Freigaben und das Profil werden nach
dem Lauf entfernt. Ohne Netzwerk-Capability blockiert Windows ausgehende und
eingehende Verbindungen. Ein Job Object übernimmt den Prozessbaum und erzwingt
CPU-, Speicher- und Prozessgrenzen; das Schließen seines letzten Handles beendet
alle verbliebenen Kindprozesse. Vor der Freigabe muss ein echter Probelauf das
Lesen einer Hostdatei und den Netzwerkzugriff blockieren, zugleich aber das
Schreiben im freigegebenen Workspace erlauben.

Unter macOS erzeugt in:si für jeden Lauf ein Seatbelt-Profil mit standardmäßig
verweigerten Fähigkeiten. System- und Python-Laufzeit, gestartete Kursdateien
und importierte Workspace-Dateien sind gezielt lesbar; nur der vorgesehene
Projekt- oder Aufgabenbereich und ein anschließend gelöschtes temporäres Home
sind schreibbar. Netzwerkzugriff ist nicht freigegeben. Kindprozesse erben das
Profil, dürfen nur den eigenen Prozessbaum signalisieren und werden zusätzlich
von der plattformübergreifenden Ressourcenaufsicht erfasst. Der Selbsttest muss
vor der Freigabe Lesen und Schreiben außerhalb, Netzwerkzugriff und eine
Manipulation der Hostdatei verhindern, zugleich aber Workspace-Schreiben und
einen geerbten Kindprozess erlauben.

Der aktuelle Adapter verwendet Apples mit macOS ausgeliefertes
`/usr/bin/sandbox-exec`. Die darunterliegende Profilsprache ist keine zugesagte
stabile öffentliche API. Deshalb ist die ausführbare Datei allein nie ein
Verfügbarkeitsnachweis: Scheitert der reale Selbsttest nach einem macOS-Update,
bleibt der integrierte Start gesperrt. Ein signierter App-Sandbox-Helper ist als
Produktionshärtung vorgesehen.

Mit dem Release ausgelieferte Galerie- und Fachmodulbeispiele sind eine eigene,
geprüfte Vertrauensklasse und dürfen lokal starten. Importierter Kurscode gehört
nicht zu dieser Klasse.

Kursarchive werden außerdem vor der Installation gegen absolute Pfade,
Verzeichnisausbrüche und eine unerwartete Struktur geprüft. Schülerarbeit liegt
getrennt von aktivierten Kursinhalten und wird bei Inhaltsupdates nicht
überschrieben.

## Externe IDE

**In IDE öffnen** ist der ausdrückliche Weg für Netzwerk, externe Programme,
besondere Geräte, X11-Grafik und größere Projekte. Die IDE und dort gestarteter
Code laufen mit den normalen Rechten des Benutzerkontos. Die in:si-Sandboxzusage
gilt für diesen Weg nicht.

## Ausdrücklich nicht garantiert

Auch ein korrekt konfigurierter Betriebssystemadapter ist keine mathematisch
vollständige Sicherheitsgarantie. Nicht zugesichert werden insbesondere Schutz
gegen:

- Schwachstellen im Kernel, in AppContainer, Bubblewrap, Seatbelt, Python, Grafik-,
  Audio- oder Laufzeitbibliotheken;
- Hardware- und Seitenkanalangriffe;
- absichtlich schädlichen Code, der eine bisher unbekannte Sandboxlücke
  ausnutzt;
- Datenverlust innerhalb des ausdrücklich schreibbaren aktuellen Projekts;
- irgendeine Isolation für Prozesse, die der Benutzer in einer externen IDE
  startet.

Kurse sollten weiterhin nur aus nachvollziehbaren Quellen importiert werden.

## Sicherheitslücken melden

Bitte veröffentliche reproduzierbare Exploits, Zugangsdaten oder sensible
Schülerdaten nicht in einem öffentlichen Issue. Kontaktiere zunächst den
Repository-Inhaber über das GitHub-Profil, bis ein eigener privater
Meldekanal eingerichtet ist. Allgemeine Härtungsvorschläge ohne vertrauliche
Details können als GitHub-Issue eingereicht werden.
