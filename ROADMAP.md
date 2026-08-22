# Roadmap bis in:si 1.3

Diese Roadmap beschreibt die geplanten Qualitätsstufen bis zur ersten stabilen
Version 1.0 und die darauf aufbauenden Etappen bis 1.3. Die Versionsnummern sind
Zielkorridore, keine festen Termine. Ein Meilenstein gilt erst als
abgeschlossen, wenn neben den Funktionen auch seine Migrationen, Dokumentation
und Plattformprüfungen fertig sind.

| Version | Schwerpunkt | Sichtbares Ergebnis |
|---|---|---|
| 0.7 | Sicherheit und technische Entkopplung | geschützte Programmläufe, neutraler Trainervertrag und neuer Kurseditor |
| 0.8.x | Zuverlässigkeit, Wartbarkeit und Performance | schlankerer wartbarer Kern, messbar schnellere Abläufe, getestete Migrationen und Wiederherstellung |
| 0.9 | Schuleinsatz | getrennte Profile, nachvollziehbare Kursrechte und Unterrichtspilot |
| 1.0 | Stabilität | dokumentierte 1.x-Verträge und produktionsreife Desktop-Verteilung |
| 1.1 | Kursökosystem | wiederverwendbare Inhaltsbausteine, weitere Engines und Autorenworkflow |
| 1.2 | Projektlernen | lokale Projektplanung und optionale Kompetenzentwicklung |
| 1.3 | Zusammenarbeit | portable Abgaben, Rückmeldungen und Peer Review ohne Herstellerkonto |

Die Reihenfolge ist bewusst gewählt: Zusammenarbeit und umfangreichere
Lernmodelle bauen auf verlässlichen lokalen Daten, stabilen Formaten und einem
geprüften Berechtigungsmodell auf. Einzelne Vorarbeiten dürfen früher entstehen,
die jeweilige öffentliche Zusage gilt aber erst mit dem genannten Meilenstein.
Der jeweils aktuelle Ist-Stand mit Auswirkungen und Workarounds wird getrennt
in [Bekannte Probleme und Einschränkungen](KNOWN_ISSUES.md) gepflegt.

Für den Arbeitszweig `develop/v0.8` dienen README, Changelog,
[0.8-Release-Notes](docs/release-notes-0.8.md), diese Roadmap und die bekannten
Probleme als lebende Vorab-Dokumentation. Nach jedem abgeschlossenen und
getesteten Schritt werden mindestens Teststand, umgesetzte Änderung und
verbleibende Einschränkungen in den jeweils betroffenen Markdown-Dateien
aktualisiert. Die stabilen Downloadlinks zeigen bis zur Freigabe weiterhin auf
0.7.0; Paket und Laufzeitanzeige des Zweigs tragen `0.8.0.dev0`.

## 0.7 – sichere technische Grundlage

Ziel: Fremden Kurs- und Schülercode kontrolliert ausführen und Kurse unabhängig
von einer einzelnen Trainerimplementierung bearbeiten können.

0.7 ersetzt mehrere provisorische Grenzen des bisherigen Prototyps. Besonders
wichtig ist, dass eine bequeme Schaltfläche zum Starten von Lerncode nicht
unbemerkt zu einem ungeschützten Hostprozess führt. Gleichzeitig darf weder der
Kurseditor noch das Trainerformat dauerhaft an PyKIM gebunden bleiben.

Der technische Kern, die Datenschutzübersicht und die zweisprachige
Offline-Dokumentation sind umgesetzt. Vor der Freigabe liegen die Schwerpunkte
auf der visuellen Oberflächenabnahme und der abschließenden Plattformmatrix.

- capability-basierter, fail-closed Sandbox-Runner für Windows, macOS und Linux;
- fachmodulneutraler Trainervertrag mit PyKIM als erstem Adapter;
- versionierte Kurs-Runtime und geprüfte Offline-Abhängigkeiten;
- lokaler Markdown-/WYSIWYG-Editor für Kurs- und Projektdokumente;
- sichere Dateiimporte und begrenzte lokale Projektstände;
- Datenschutz- und Datenbestandsübersicht einschließlich Speicherorten,
  Exporten, Netzwerkzielen sowie Lösch- und Aufbewahrungswegen;
- Systembenutzername in Exporten entfernen oder ausdrücklich optional machen;
- GitHub-Updateprüfung transparent und lokal abschaltbar beziehungsweise
  ausschließlich manuell nutzbar machen;
- aussagekräftige deutsche und englische README sowie zweisprachige, offline
  auslieferbare Dokumentation;
- vollständige automatisierte Tests, Desktop-Builds und dokumentierte
  Smoke-Tests auf den unterstützten Plattformen.

Freigabekriterium: Alle Kernabläufe funktionieren ohne Internet. Fremdcode
startet integriert nur nach bestandenem Sandbox-Selbsttest. Bekannte
Einschränkungen der noch nicht signierten beziehungsweise notarisierten
Distribution sind sichtbar dokumentiert.

Nicht Teil von 0.7 sind automatische Datenmigrationen über mehrere
Programmversionen, Mehrbenutzerprofile und eine Zusage stabiler öffentlicher
Formate. Diese folgen, nachdem die neue technische Grundlage im Alltag geprüft
wurde.

Die Sandbox bleibt auch nach 0.7 eine dauerhafte Wartungs- und Prüfaufgabe.
Betriebssystem-, Runner-, Grafik- und Paketänderungen können ihre tatsächlichen
Garantien verändern. Deshalb werden Selbsttests, Plattformproben,
Ressourcengrenzen und der Fail-closed-Ausführungspfad mit jedem weiteren
Meilenstein erneut geprüft und bei Bedarf gehärtet.

## 0.8.x – verlässliche Daten und Wiederherstellung

Ziel: Updates, beschädigte Umgebungen und unterbrochene Arbeitsabläufe dürfen
keine Lernarbeit verlieren.

Mit 0.7 kann in:si Daten bereits getrennt speichern und Sicherungsstände
anlegen. In 0.8 werden daraus für Nutzerinnen und Nutzer sichtbare,
versionsübergreifend getestete Abläufe. Entscheidend ist nicht nur, dass ein
Backup existiert, sondern dass sein Inhalt verständlich ausgewählt und sicher
wiederhergestellt werden kann.

### Arbeitsbaseline vom 22. August 2026

Die 0.8.x-Konsolidierung startet mit 18.746 Zeilen selbst gepflegtem
Python-Produktivcode unter `src/insi` und einer grünen Testsuite mit 392
bestandenen, einer übersprungenen und zwei bewusst abgewählten Prüfungen. Das
vorhandene macOS-arm64-DMG der Version 0.7.0 ist 113 MB groß; davon entfallen im
Buildverzeichnis rund 39 MB auf eingebettete Wheels. Andere Plattformpakete
werden separat gemessen, sobald reproduzierbare Release-Builds vorliegen.

Als erster kleiner Entkopplungsschritt wurde der schwere Import der
Kursauswahl aus `insi.app` entfernt und durch einen Architekturtest gegen eine
Rückkehr abgesichert. Die kumulierte Importzeit von `insi.app` sank in derselben
lokalen `-X importtime`-Messung von rund 155 ms auf 20 ms. Diese Werte dienen
als Arbeitsreferenz, nicht als plattformübergreifendes Leistungsversprechen.

Der erste Buildschnitt trennt außerdem das Offline-Wheelhouse der Kurs-Runtime
vom bereits in der App enthaltenen Anwendungs-Paketbaum. PyKIM 0.6.0 wird über
einen festen Commit, Pyxel 2.9.9 und PyYAML 6.0.3 werden als exakte Versionen
bezogen; ein Manifest dokumentiert Dateien und SHA-256-Prüfsummen. Dadurch sank
das Wheelhouse im lokalen macOS-arm64-Build von 38,7 auf 6,9 MiB und das DMG
von rund 113 MB auf 86.324.169 Byte beziehungsweise rund 82 MiB. Der
Offline-Aufbau einer frischen Kurs-Runtime aus diesem Bestand wurde geprüft;
Windows, Linux und macOS Intel müssen denselben Nachweis in ihren Release-Builds
erbringen.

Die allgemeinen Packaging-Artefakte tragen danach ebenfalls den in:si-Namen:
PyInstaller-Specs, interne Buildvariablen, Buildverzeichnisse und der Schalter
des eingebetteten Python-Runners wurden umgestellt. Nur die gezielt erkannte
Runnerdatei eines alten PyKIM-Suite-Bundles erhält vorübergehend noch ihren
damaligen Schalter; neue Builds und Prüfpfade verwenden ihn nicht mehr.

Die direkten Anwendungs-, Test-, Build- und Bootstrap-Abhängigkeiten sind auf
den gemeinsam geprüften Stand festgelegt. Zusätzlich enthält jedes
Desktop-Artefakt ein plattformspezifisches Buildmanifest aller tatsächlich
aufgelösten Pakete und Versionen sowie der veröffentlichbaren VCS-Herkunft. Die
transitiven Stände werden zunächst damit nachvollziehbar; reproduzierbare
plattformspezifische Locks werden aus den Windows-, Linux-, macOS-Intel- und
macOS-ARM-Builds abgeleitet und bleiben vor der 0.8.x-Freigabe offen.

Externe Trainer-Entry-Points werden inzwischen zunächst ausschließlich über
Distributionsmetadaten inventarisiert. Ein Kurs kann ihren Import nicht mehr
beiläufig über eine Registry-Abfrage auslösen: Vor dem ersten `load()` zeigt
in:si Paket, Version, Engine, Herausgeber und Quelle und verlangt eine
versionsbezogene Zustimmung. Ablehnung und Versionswechsel bleiben fail-closed;
die allgemeine Kursimportwarnung weist bereits vor der Installation auf die
App-Rechte solcher Module hin.

Die neutrale Trainings-Registry importiert den eingebauten PyKIM-Adapter nicht
mehr beim Start. Sie aktiviert ihn erst, wenn ein Kurs eine PyKIM-Engine oder
das eindeutig zuordenbare numerische Altformat deklariert. Allgemeiner
Systemstatus und Abgabeexport lesen die Fachmodulversion aus Paketmetadaten,
ohne dafür PyKIM-Code auszuführen; Architekturtests sichern diese Richtung.

Auch Erkennung, Auswahl und Reparatur der Python-Laufzeit arbeiten inzwischen
mit einem generischen Paketbestand und den exakten Anforderungen des
Kursmanifests statt mit fest eingebauten PyKIM-/Pyxel-Schaltern. Die
Installation übernimmt für manifestierte Kurse die vollständige versionierte
Paketliste; ein Testkurs mit einem ausschließlich fremden Trainingspaket sichert
diese Modulneutralität ab. Nur für ältere 0.7-Kurse ohne Runtime-Manifest bleibt
ein ausdrücklich als Legacy-Fallback bezeichnetes PyKIM-Profil erhalten. Neue
Runtime-Umgebungsvariablen tragen den `INSI_`-Präfix, während die bisherigen
Namen vorläufig als lesbare Kompatibilitätsaliasse erhalten bleiben.

Die erste echte Codebereinigung entfernt zwei parallel gewachsene
Autorenoberflächen: Eine nicht mehr registrierte ältere Kurswerkstatt wurde
vollständig gestrichen, und der doppelte Entwurfseditor unter „Werkzeuge“ führt
nun in die kanonische Kurswerkstatt. Aufgabenprüfung sowie Datei-, Import- und
Exportfunktionen bleiben erhalten. Gleichzeitig beziehen allgemeine
Autorenmodule Erzeugung, Parsing, Regelbeschriftungen und Audit nur noch über
einen optionalen Fachmodulvertrag; allein der eingebaute Adapter importiert
dafür `pykim.trainer`. Der selbst gepflegte Python-Produktivcode sank trotz der
neuen Runtime-, Zustimmungs-, Manifest- und Architekturprüfungen gegenüber der
Baseline netto von 18.746 auf 18.345 Zeilen. Architekturtests sichern den
einzigen UI-Pfad und die Importgrenze.

Die Codefingerprints für Ähnlichkeitshinweise sind ebenfalls vom Fachmodul
entkoppelt. Der allgemeine AST-Algorithmus importiert PyKIM nicht mehr;
versionierte Profile mit geschützten Lernbefehlen stammen aus dem jeweils
zuständigen Traineradapter. Neue Abgaben dokumentieren ihre Engine, während
Abgaben ohne Engine-Feld über den bisherigen Algorithmusnamen `pykim-ast-v1`
rückwärtskompatibel geprüft werden.

Verwaltete Kurs-Runtimes werden nicht mehr durch eine Reparatur an Ort und
Stelle verändert. in:si erzeugt stattdessen eine neue Runtime-Generation in
ihrem endgültigen Pfad, installiert und prüft dort Python- und Paketvertrag und
aktiviert sie erst anschließend über einen atomar ersetzten Marker. Schlägt
Erstellung, Installation oder Prüfung fehl, werden nur die unvollständigen
neuen Dateien entfernt; aktive Generation und Interpreterpräferenz bleiben
unverändert. Nach erfolgreichem Wechsel bleibt die vorherige Generation als
Rückfallstand erhalten. Tests decken den echten venv-Aufbau, beide
Transaktionsausgänge und manipulierte Markerpfade ab.

Der erste UI-Hotspot ist ebenfalls strukturell aufgelöst: `theme.py` wurde von
885 auf 33 Zeilen reduziert und lädt die bislang eingebetteten Styles und
Browserskripte nun aus paketierten, nach Verantwortung getrennten Assets. Die
größte JavaScript-Datei umfasst 191 Zeilen. Die erste anschließende Reduktion
hat Header, Navigation, Dialograhmen, Logos und Footer auf die von NiceGUI
bereitgestellten Quasar- und Tailwind-Klassen umgestellt; dadurch sank das
gemeinsame Stylesheet von 471 auf 384 Zeilen. Anwendungsspezifische Selektoren,
generiertes Markdown, Animationen und Browserinteraktionen bleiben als
statische Assets bestehen. Der visuelle Vergleich dieser zweiten Stufe ist vor
ihrer Abnahme verpflichtend.

Die manuelle Zwischenabnahme auf macOS beschreibt die umgestellte Oberfläche
als angenehmer und insgesamt sehr flüssig. Kursöffnung und Kursladen wirken
deutlich schneller als vor der Konsolidierung; beim ersten Nachladen einzelner
Ansichten sind jedoch noch kleine Haker wahrnehmbar. Vor weiteren Eingriffen
werden deshalb App-Start, Kursprüfung und erster Ansichtsaufbau getrennt
gemessen, damit die verbleibende synchrone Arbeit gezielt reduziert wird.
Ein erstes CPU-Profil des browserlosen NiceGUI-Gesamtwegs ordnet dem Aufbau von
`render_setup_panel` rund 0,45 Sekunden je Kursöffnung zu; Werkzeuge und Aufgaben
folgen mit rund 0,07 beziehungsweise 0,05 Sekunden. Kursauswahl, Header, Footer
und reine Kurskonfigurationsprüfung liegen jeweils deutlich darunter. Der
nächste Performance-Schnitt konzentriert sich deshalb auf die große Setup-View
und den bislang vorab aufgebauten Inhalt inaktiver Tabs.

Dieser Schnitt ist umgesetzt: Der Setup-Tab wird erst bei seiner ersten
Auswahl erzeugt, während NiceGUIs `run.io_bound` die reine Laufzeiterkennung
nach dem ersten Seitenaufbau in einem Worker-Thread vorlädt. Bis zu vier
unabhängige Interpreter werden dort parallel geprüft; auf dem lokalen macOS-
System sank die Erkennung von acht Kandidaten von rund 0,42 auf 0,14 Sekunden.
Im erneuten Gesamtprofil sank der synchrone Seitenaufbau je Kursöffnung von
rund 0,37 auf 0,14 Sekunden und der eigentliche Setup-UI-Aufbau nach vorhandenem
Snapshot von rund 0,45 auf 0,02 Sekunden. Der erweiterte E2E-Lauf einschließlich
erstmaligem Öffnen des Setup-Tabs sank zugleich von 6,93 auf 5,94 Sekunden.

Eine kontrollierte Speicherprobe im nativen macOS-Entwicklungsbetrieb trennt
den tatsächlichen physischen Speicher von reserviertem virtuellem Adressraum
und gleichnamigen Fremdprozessen. Direkt nach dem Start belegten der
in:si-Server rund 75 MiB und der von NiceGUI gestartete native GUI-Prozess rund
129 MiB physischen Speicher; Resource-Tracker und zugehörige WebKit-Prozesse
erhöhten den beobachteten Gesamtbedarf auf etwa 400 bis 550 MiB. Die von WebKit
reservierte 4-GiB-JavaScript-Gigacage ist dabei unzugewiesener virtueller
Adressraum und kein belegter Arbeitsspeicher. Zwei kontrollierte Stopps – über
den Server und über das Ende des nativen GUI-Prozesses – räumten Server,
Resource-Tracker und die jeweils zugehörigen WebKit-Prozesse vollständig auf.
Ein zunächst verdächtiger älterer WebContent-Prozess mit rund 676 MiB ließ sich
über seine geöffneten Datenpfade eindeutig Safari statt in:si zuordnen. Für
weitere macOS-Vergleiche gilt deshalb ein Leerlauf-Richtwert von höchstens
600 MiB für den vollständigen frisch gestarteten in:si-Prozessverbund; gemessen
werden Prozess-Footprints und der Lebenszyklus einer isolierten Start-/Stopp-
Probe, nicht die nach Prozessnamen gruppierte Anzeige des Activity Monitors.

In der Kurswerkstatt unterscheidet das Aufgaben-Plus nun sichtbar zwischen
freier und geprüfter PyKIM-Aufgabe. Beide Wege zeigen gestufte Hinweise als
eigenes Formularfeld; bei geprüften Aufgaben erklärt die Oberfläche zusätzlich
die davon getrennten regelbezogenen Tipps in der Trainer-YAML. Ein NiceGUI-
End-to-End-Test öffnet beide Autorenwege, damit Hints nicht erneut nur im
Datenmodell vorhanden, aber in der Oberfläche schwer auffindbar sind.

### Kern entschlacken, wartbarer machen und beschleunigen

Zu Beginn der 0.8.x-Reihe und vor größeren neuen Funktionen wird der seit dem
Prototyp gewachsene Code verhaltenswahrend konsolidiert. Ziel sind weniger
doppelte Abläufe, klarere Zuständigkeiten, weniger unnötige Arbeit zur Laufzeit
und kleinere, gezielter prüfbare Einheiten. Eine bloße Umverteilung von Code,
zusätzliche Abstraktionsschichten oder ein vollständiger Rewrite gelten nicht
als Verbesserung.

- Startzeit, Zeit bis zur bedienbaren Kursansicht, Ansichtswechsel,
  Speicherverbrauch und zentrale Datei-, Runtime- und Systemprüfungen vor dem
  Umbau reproduzierbar messen;
- Umfang und Duplikation des selbst gepflegten Produktivcodes getrennt von
  Tests, vendorten Bibliotheken und generierten Dateien erfassen und über die
  0.8.x-Reihe netto reduzieren; neue Abstraktionen oder Kompatibilitätsschichten
  müssen ihren zusätzlichen Umfang durch eine konkrete Vereinfachung
  rechtfertigen;
- das komprimierte Desktop-Releasepaket pro Plattform nach Möglichkeit unter
  100 MB halten; dieser Zielwert ist kein Freigabeblocker, Abweichungen sollen
  aber gemessen und durch notwendige Laufzeit-, Sandbox- oder
  Plattformkomponenten begründet werden;
- für Tests und Desktop-Releases alle tatsächlich eingebauten externen
  Abhängigkeiten reproduzierbar festlegen; insbesondere PyKIM und andere
  Git-Abhängigkeiten über einen Release-Tag oder Commit statt über `main`
  beziehen, Buildwerkzeuge versionieren und die aufgelösten Paketversionen je
  Release-Artefakt dokumentieren;
- Prozessstarts, Kursimport-Vertrauenspfade und den vollständigen Schülerlauf
  als zusammenhängende Abläufe erfassen und durch Charakterisierungstests
  absichern;
- wiederholte UI-, Validierungs-, Datei- und Zustandslogik zusammenführen;
- unnötige Importe, wiederholte Dateisystemscans, redundante Validierungen und
  mehrfach aufgebaute UI-Zustände aus häufig genutzten Abläufen entfernen;
- parallele Implementierungen desselben Ablaufs auf einen kanonischen Pfad
  zurückführen und bevorzugt Code löschen oder vereinfachen, statt ihn nur in
  weitere Hilfsschichten zu verschieben;
- große Kern- und View-Module entlang bestehender Verantwortlichkeiten
  schrittweise zerlegen, insbesondere Sandbox, Runtime, Updates und
  Kurswerkzeuge;
- die Größe der gesamten App- und View-Schicht betrachten statt nur
  `app.py`: ausgelagerte Großmodule wie Kurswerkstatt, Setup, Kursauswahl,
  Aufgaben, Werkzeuge und Theme dürfen die Komplexität nicht lediglich aus dem
  Einstiegspunkt verschieben; tote und doppelte UI-Abläufe löschen,
  Geschäftslogik aus Views in bestehende Fachbereiche zurückführen,
  wiederholte Dialog-, Status- und Validierungsmuster zusammenführen und
  Architekturtests mit Budgets für den gesamten UI-Schnitt ergänzen;
- die am 22. August 2026 sichtbaren Strukturhotspots gezielt abbauen:
  `theme.py` enthält praktisch seine gesamten 885 Zeilen in einer Funktion,
  die Hauptfunktionen von Kurswerkstatt, Setup, Kursauswahl, Aufgaben und
  Werkzeugen umfassen jeweils rund 493 bis 784 Zeilen; CSS und JavaScript aus
  `theme.py` als prüfbare statische Assets führen und die View-Monolithen in
  kleinere Zustands- und Darstellungsbereiche überführen, ohne dieselbe Logik
  lediglich auf mehr Dateien zu verteilen;
- `test_guide.py` nach fachlichen Verträgen aufteilen,
  damit Änderungen nicht weiterhin einen zentralen Sammeltest als
  Wissensmonopol benötigen;
- die Plattform- und Prozessverantwortlichkeiten aus `sandbox.py` mit derzeit
  1.408 Zeilen erst als letzten Konsolidierungsschritt unmittelbar vor der
  0.8.x-Releaseprüfung in klar begrenzte Adaptermodule überführen; den
  umfangreichen Windows-Helper separat betrachten und gemeinsame
  Sicherheitsprüfungen nicht zwischen Plattformimplementierungen duplizieren.
  Wegen der hohen Deploy- und Plattformempfindlichkeit folgt direkt danach die
  vollständige Build-, Sandbox- und Plattformmatrix, bevor 0.8.x veröffentlicht
  wird;
- `runtime.py`, `updates.py`, `course_archive.py` und `course_setup.py` entlang
  ihrer bereits erkennbaren Phasen Erkennung, Prüfung, Transaktion, Format und
  Aktivierung entflechten; Schnittstellen nur dann einführen, wenn dadurch
  Zustandskopplung oder Gesamtcode nachweisbar sinken;
- die Fachmodulgrenze konsequent durchsetzen: Der in:si-Kern besitzt nur neutrale
  Verträge, Registry, Ausführungssteuerung, generische Aktivitäten, Feedback und
  Lernstand; konkrete Trainerdefinitionen bleiben im Kurs, während Auswertung,
  fachspezifische Validierung, Autorenfelder und Laufzeitanforderungen dem
  jeweiligen Fachmodul gehören;
- direkte PyKIM-Abhängigkeiten aus allgemeinen Runtime-, Autoren-, System- und
  Abgabepfaden entfernen; PyKIM als separat versionierten Adapter behandeln,
  der für ein Offline-Standardpaket weiterhin bewusst mitgeliefert werden kann,
  ohne Bestandteil des in:si-Kerns zu sein;
- externe Fachmodule nicht still als normale Kursdaten behandeln: Vor Auswahl
  oder Installation bei der Kurserstellung und vor dem ersten Öffnen eines
  importierten Kurses müssen Paketname, genaue Version, Herkunft und
  Herausgeber sichtbar sein; nicht durch in:si geprüfte Module erhalten eine
  klare Warnung und benötigen eine bewusste Zustimmung für genau diese Version;
- Trainer-Entry-Points zunächst ohne Import inventarisieren und Drittmodule
  nicht vor der Zustimmung mit `load()` im App-Prozess ausführen; bis eine
  getrennte Modul-Isolation existiert, gelten solche Module ausdrücklich als
  vertrauenswürdige App-Erweiterungen mit den Rechten der Anwendung und nicht
  als durch die Schülercode-Sandbox begrenzte Kursinhalte;
- globale Zustände und ihre jeweils maßgebliche Datenquelle dokumentieren und
  nur dort ersetzen, wo daraus eine konkrete Vereinfachung entsteht;
- verbliebene PyKIM-Namensartefakte in der allgemeinen in:si-Infrastruktur
  erfassen und bereinigen, etwa alte Spec-Namen, Buildvariablen,
  Kommandozeilenoptionen und generische UI-Präfixe; echte PyKIM-Adapter sowie
  aus Kompatibilitätsgründen benötigte Datenpfade und Formate klar davon
  abgrenzen und nur mit dokumentierter Migration umbenennen;
- überholte Kompatibilitätspfade und nachweislich ungenutzten Code entfernen;
- große Sammeltests nach fachlichen Verantwortlichkeiten aufteilen.

Die Konsolidierung darf keine Kurs-, Workspace-, Trainer- oder Runtimeformate
stillschweigend ändern. Vor und nach jedem Schritt müssen die vorhandenen Tests
und die betroffenen Plattformproben dasselbe Verhalten bestätigen. Für die
wichtigsten Abläufe werden überprüfbare Performance-Budgets festgelegt;
Änderungen ohne messbare Vereinfachung oder Verbesserung werden nicht allein
wegen einer vermeintlich saubereren Architektur übernommen.

### Wartbarkeit als Freigabekriterium

Der Aufwand einer Änderung soll nicht mit jeder Version überproportional
wachsen. Hoher Analyse- und Kontextbedarf, Änderungen an vielen fachlich
unabhängigen Dateien und eine nur vollständig ausführbare Testsammlung gelten
als Hinweise auf zu starke Kopplung. In 0.8.x werden deshalb nicht nur Laufzeit
und Paketgröße, sondern auch Änderungsschnitt und Prüfbarkeit betrachtet.

- Verantwortlichkeit und öffentliche beziehungsweise interne Verträge jedes
  Kernbereichs knapp dokumentieren;
- Abhängigkeitsrichtungen durch Architekturtests sichern, insbesondere keine
  direkten Fachmodulimporte im in:si-Kern und keine Geschäftslogik in Views;
- typische Änderungen auf den zuständigen Teil des Systems begrenzen, sodass
  nicht gleichzeitig Kurs, Runtime, Training, Sandbox und mehrere Views
  angepasst werden müssen;
- schnelle, fachlich zugeschnittene Tests ermöglichen und die vollständige
  Plattformmatrix für Integrations- und Releaseprüfungen reservieren;
- zentrale Abläufe und ihre maßgeblichen Datenquellen so dokumentieren, dass
  sie ohne erneute Rekonstruktion über das gesamte Repository verständlich
  bleiben;
- neue Sonderfälle nur aufnehmen, wenn sie sich in einen bestehenden Vertrag
  einfügen oder eine bewusst dokumentierte Vertragsänderung rechtfertigen;
- Kompatibilitätscode mit einem benannten Zweck und Entfernungskriterium
  versehen, damit Übergangslösungen nicht dauerhaft den Kern vergrößern.

Freigabekriterium der Konsolidierung: Eine typische Änderung innerhalb eines
Kernbereichs lässt sich mit dessen Dokumentation und gezielten Tests bearbeiten,
ohne den gesamten Anwendungskontext laden oder fachlich unabhängige Module
anfassen zu müssen. Architekturtests verhindern, dass erneut zentrale
Sammelmodule oder direkte Abhängigkeiten von einzelnen Fachmodulen entstehen.

Aktueller Funktionsstand des 0.8-Datenblocks:

- **umgesetzt:** verwaltete Kursumgebungen bei geändertem Runtime-Vertrag als
  neue, atomar aktivierte Generation aufbauen;
- **umgesetzt:** versionierte Migrationen für Einstellungen, Lernstände und
  Kursdaten mit unverändertem Originalbackup;
- **automatisiert geprüft, Hardwareprobe offen:** entfernte Datenträger und
  unerwartete Abbrüche bei Migration, Export und Wiederherstellung;
- **umgesetzt:** automatische und benannte Projektstände sichtbar auswählen,
  kommentieren und sicher wiederherstellen;
- **umgesetzt:** Backup-, Import- und Wiederherstellungsabläufe mit
  simulierten Schreib-, Prüf- und Aktivierungsfehlern absichern;
- **umgesetzt:** Gesamtexport und vollständiges lokales Entfernen als getrennte,
  ausdrücklich bestätigte Oberflächenabläufe zugänglich machen.

### Versionierte Datenmigrationen

Das erste 0.7→0.8-Migrationsgerüst ist umgesetzt. Lokale Einstellungen ohne
Formatkennung werden unter Erhalt unbekannter Schlüssel in das Format
`insi-settings-v1` überführt. Kursöffnungen prüfen die Kurskennung und den
Lernstand, ergänzen bei älteren Lernständen die inzwischen erwarteten Bereiche
für freie Antworten und Hinweise und schreiben erst zuletzt den Marker
`data-version.json`. Vor jeder tatsächlichen Änderung entsteht genau einmal ein
Originalbackup unter `.pykim/backups/migrations/0.7-to-0.8` beziehungsweise im
lokalen Konfigurations-Backup.

Alle Quelldateien werden vor der ersten Änderung validiert, einzelne Dateien
atomar ersetzt und abgeschlossene Schritte idempotent erneut ausführbar
gehalten. Ein simulierter Abbruch unmittelbar vor dem Versionsmarker lässt sich
dadurch beim nächsten Öffnen fortsetzen, ohne das Originalbackup zu ersetzen.
Unbekannte zukünftige Formate und beschädigte Lernstände bleiben unverändert
und blockieren die Kursöffnung mit einer sichtbaren Fehlermeldung. Eigene
Migrations-Tests liegen bewusst außerhalb des bisherigen Sammeltests.

Auch ein während Backup oder atomarem Ersetzen simulierter entfernter
Datenträger ist abgedeckt: Die Quelldatei bleibt unverändert, ein bereits
vollständiges Originalbackup erhalten, temporäre Dateien werden nach
Möglichkeit entfernt und der nächste Versuch kann die Migration abschließen.
Noch offen sind weitere reale 0.7-Beispieldaten und Hardwareproben auf
tatsächlich entfernten Datenträgern. Die Fehlergrenze des Datenexports und die
kontrollierte Oberfläche zum Export und vollständigen lokalen Löschen sind
automatisiert abgedeckt, benötigen vor der Freigabe aber weiterhin die reale
Plattformmatrix.

### Verständliche Projektstände statt Git-Pflicht

Die bereits vor integrierten Starts erzeugten automatischen Projektsicherungen
werden zu einer sichtbaren, bewusst einfachen Versionsgeschichte ausgebaut.
Lernende können jederzeit einen benannten Projektstand speichern und in einem
kurzen Kommentar festhalten, was funktioniert, was verändert wurde oder woran
sie als Nächstes arbeiten möchten. Die Oberfläche spricht von „Projektstand
speichern“ und „wiederherstellen“, nicht von Commit, Stage, Branch oder Push.
Git kann für fortgeschrittene Projekte später zusätzlich
verwendet werden, ist aber keine Voraussetzung für dieses Lernmodell.

Der verbindliche Umfang für 0.8.x bleibt bewusst klein: benannten Stand mit
Kommentar speichern, automatische und benannte Stände auflisten, einen Stand
auswählen und ohne Verlust des aktuellen Arbeitsstands wiederherstellen. Damit
wird die bestehende Sicherung erstmals unmittelbar nutzbar, ohne für 0.8 eine
vollständige Versionsverwaltung zu bauen.

- automatische Sicherheitsstände und bewusst benannte Projektstände in einer
  gemeinsamen Zeitleiste unterscheidbar anzeigen;
- unmittelbar vor jeder Ausführung einen automatischen Stand anlegen, sofern
  sich der Projektinhalt seit dem letzten intakten Stand verändert hat;
- identische Ausführungen per Dateiliste und SHA-256-Prüfsummen zusammenfassen
  und nur die zehn neuesten automatischen Stände behalten;
- benannte Stände mit Zeitpunkt, Kommentar, Dateiliste und Prüfsummen
  unveränderlich speichern und nicht durch die automatische Aufbewahrungsgrenze
  entfernen;
- vor jeder Wiederherstellung zunächst den aktuellen Arbeitsstand automatisch
  sichern und anschließend den gewählten Stand atomar aktivieren;
- Wiederherstellungen niemals als Löschen neuerer Stände behandeln: Wer nach
  einem Rücksprung weiterarbeitet, speichert daraus einfach einen neuen Stand;
- zunächst eine lineare, verständliche Geschichte anbieten und keine
  Branch-Oberfläche nachbauen.

Ein grafischer Vergleich geänderter Textdateien und der portable Export einer
vollständigen Projekthistorie sind sinnvolle spätere Ergänzungen, aber keine
Freigabeblocker für 0.8.x.

Das 0.8.x-MVP ist umgesetzt. Neue automatische und benannte Stände besitzen
eine getrennte Manifestdatei mit Typ, Zeitpunkt, Titel, Kommentar, Dateiliste
und SHA-256-Prüfsummen; vorhandene 0.7-Snapshots ohne Manifest bleiben lesbar
und wiederherstellbar. Benannte Stände fallen nicht unter die begrenzte
Aufbewahrung automatischer Sicherungen. Vor einer Wiederherstellung wird der
gewählte Stand vollständig geprüft und vorbereitet, anschließend der aktuelle
Arbeitsstand gesichert und das Projekt über einen Rückfallordner ausgetauscht.
Manipulierte oder unvollständige Stände bleiben sichtbar, können aber nicht
aktiviert werden. Kopieren und Wiederherstellen laufen über NiceGUIs
I/O-Worker, während die Oberfläche bedienbar bleibt. Architekturbudgets trennen
Projekteditor, Zeitleisten-UI und dateisystemische Transaktion; Unit-Tests
decken Aufbewahrung, ältere Formate, Manipulation und fehlgeschlagene
Aktivierung ab, ein NiceGUI-E2E-Test den vollständigen Schülerweg. Projektstarts
erzeugen einen als „Automatisch vor Ausführung“ bezeichneten Stand nur bei
geändertem Inhalt; wiederholtes Ausführen desselben Inhalts erzeugt keine
Dubletten. Sichern und Starten laufen dabei außerhalb des UI-Event-Loops. Bei
Pyxel-Projekten öffnen getrennte Schaltflächen den offiziellen Editor gezielt
im Sprite- beziehungsweise Musikbereich; der dafür verwendete interne Einstieg
ist durch die exakt festgelegte Pyxel-Version und Aufruftests abgesichert.
Interpreterpfade virtueller Umgebungen bleiben dabei bewusst unaufgelöst,
damit deren Paketbestand nicht durch den globalen Systeminterpreter ersetzt
wird. Eine kurze Startprüfung meldet sofort beendete Editorprozesse als Fehler,
statt bereits das bloße Erzeugen des Prozesses als Erfolg anzuzeigen.

Der erste Runtime-Konsolidierungsschnitt vereinheitlicht Python-Kompatibilität,
installierten Kursvertrag und die Erkennung zusätzlicher Pakete. Der Preflight
normalisiert jeden Kandidatenpfad nur noch einmal und verwendet das bereits
vorliegende Prüfergebnis des bevorzugten Interpreters, statt dafür einen
zweiten Prozess zu starten. Der Paketbestand des unveränderlichen App-
Interpreters wird einmal je Sitzung inventarisiert. `runtime.py` sank dadurch
zunächst von 901 auf 892 Zeilen, seine Preflight-Funktion von 157 auf 144
Zeilen. Zwei gezielte Regressionstests sichern Wiederverwendung und Cache.

Der zweite Runtime-Schnitt entfernt den fachmodulspezifischen
`_package_source`-Altpfad. Ausschließlich ältere 0.7-Kurse ohne
Runtime-Manifest verwenden als dokumentierten Kompatibilitätsfallback PyKIM
0.6.0, Pyxel 2.9.9 und PyYAML 6.0.3; zuvor konnte dort der vollständige
in:si-Quellbaum samt unnötiger App-Abhängigkeiten in der Kursumgebung landen.
Für neue Kurse legt allein der Kursersteller Python-Version und vollständige
Paketliste fest. in:si validiert und installiert diesen Vertrag unverändert;
beim Offline-Export wird seine gesamte Wheel-Kette eingebettet. Reparaturen
reichen außerdem den bereits geprüften Basisinterpreter weiter, statt
unmittelbar einen identischen zweiten Prüfprozess zu starten. `runtime.py`
umfasst danach 865 Zeilen, 36 weniger als vor seiner Konsolidierung.

Der nächste View-Schnitt entfernt ungenutzten Auswahlzustand aus der
Kurswerkstatt, lädt die Trainernavigation nur einmal je Aktualisierung und
vereinheitlicht Aufgabenmetadaten, Markdown-Aufbau, Validierungsanzeige und
Speicherablauf. `course_studio_view.py` sank von 894 auf 849 Zeilen; ein
Architekturtest begrenzt den erneuten Zuwachs auf 850 Zeilen. Zusammen mit der
kleinen getesteten Formularfunktion ist der betroffene Produktionscode netto
25 Zeilen kleiner. Die vollständige normale Testsuite umfasst danach 448
bestandene Prüfungen.

Im anschließenden Setup-Schnitt wird die Beschriftung gefundener Interpreter
als UI-freie Funktion gegen den Kursvertrag geprüft. Die allgemeine
Einrichtungsoberfläche bezeichnet verwaltete Umgebungen nicht länger
fälschlich als PyKIM-Laufzeiten und verspricht bei Reparaturen nur noch die im
Kursvertrag festgelegten Pakete. `setup_view.py` sank von 756 auf 744 Zeilen,
seine Hauptfunktion von 661 auf 625 Zeilen. Architekturtests begrenzen beide
Werte; die neuen Setup-Vertragstests liegen außerhalb des bisherigen
Sammeltests. Die vollständige normale Testsuite umfasst danach 451 bestandene
Prüfungen.

Der Kursauswahl-Schnitt beseitigt eine künstliche Mindestwartezeit von 1,05
Sekunden bei jeder Kursöffnung. Nach zwei Browser-Frames für sichtbares Feedback
wird nun unmittelbar nur noch auf die tatsächlich notwendige Migration,
Inhaltsaktivierung und Runtime-Prüfung gewartet. Pro Kurskarte entfallen außerdem
32 auch im unsichtbaren Leerlauf animierte DOM-Elemente; das gemeinsame
Stylesheet sinkt dadurch von 384 auf 335 Zeilen. Kursordner und Zertifikate
werden beim Aufbau von Karten und Katalog nur noch einmal statt zweimal
eingelesen. `course_selection_view.py` sank von 707 auf 672 Zeilen, seine
Hauptfunktion von 659 auf 625 Zeilen. Architekturtests sichern Wartezeit,
Einfachscan und Größenbudgets. Die vollständige normale Testsuite umfasst danach
452 bestandene Prüfungen.

Der folgende Startpfad-Schnitt baut beim Öffnen eines Kurses nur noch die
zunächst sichtbare Übersicht auf. Werkzeuge, Aufgaben, Beispiele, Projekte,
Erweiterungen, Abgabe, Referenzen und Spielwiesen werden erst bei ihrer ersten
Auswahl erzeugt und anschließend wiederverwendet. Vor dem synchronen Aufbau
erhält der Browser einen Render-Frame, damit der Tabwechsel sofort sichtbar
reagiert. Allein Werkzeuge und Aufgaben belegten im letzten lokalen Profil
zusammen rund 0,12 Sekunden des bisherigen Startpfads; die vermiedene Arbeit
der weiteren acht Ansichten kommt hinzu. Die dafür notwendige Lazy-Orchestrierung
vergrößert `workspace_view.py` von 189 auf 242 Zeilen und ist als bewusster
Tausch von kleinem Steuerungscode gegen weniger Startzeit, DOM und Speicher
dokumentiert. Ein Architekturtest sichert den einmaligen Aufbau. Die
vollständige normale Testsuite umfasst danach 453 bestandene Prüfungen.

Der erste Aufbau des nun verzögert geladenen Aufgaben-Tabs verwendet den
bereits einmal eingelesenen Lernstand auch für Hint-Zustände und anfängliche
Testergebnisse. Zuvor wurde dieselbe JSON-Datei nach dem zentralen Laden für
jede programmierbare Aufgabe und jede vorhandene Hint-Gruppe erneut gelesen
und geparst; im Standardkurs entfallen damit typischerweise rund zehn
redundante Ladevorgänge. Aktualisierungen nach Ausführung, Reset oder neuem
Hinweis laden beziehungsweise speichern weiterhin den aktuellen Stand. Ein
Architekturtest begrenzt den Erstaufbau auf einen Lesevorgang. Die vollständige
normale Testsuite umfasst danach 455 bestandene Prüfungen.

Der Werkzeuge-Schnitt entfernt die zweite, vollständig vorgebaute
Update-Oberfläche. Der Headerstatus führt nun verlässlich zum einzigen manuellen
Updatebereich; App-Prüfung, Kursabgleich und Inhaltsaktivierung bleiben dort
getrennt steuerbar. Dadurch entfallen der versteckte Dialog sowie seine
doppelte Status- und Schaltflächenpflege. Die lokale Systemerkennung wird pro
Aufbau nur noch einmal ausgeführt. `tools_view.py` sank von 516 auf 360 Zeilen,
seine Hauptfunktion von 493 auf 337 Zeilen; Architekturtests sichern den
einzigen Updatepfad und beide Größenbudgets. Die vollständige normale Testsuite
umfasst danach 456 bestandene Prüfungen.

Der erste Schnitt am zentralen Sammeltest verschiebt Lernstand und
Traineraufzeichnung sowie Projektmodell, Konfliktschutz und Projektstarts in
zwei eigenständige Testmodule. `test_guide.py` sank dadurch von zwischenzeitlich
2.862 auf 2.626 Zeilen und wird per Architekturtest auf höchstens 2.650 Zeilen
begrenzt. Die elf ausgelagerten Fachtests laufen lokal zusammen in weniger als
einer Sekunde, sodass Änderungen in diesen Bereichen nicht mehr den gesamten
Guide-Kontext benötigen. Die vollständige normale Testsuite umfasst danach 457
bestandene Prüfungen.

Der zweite Schnitt verschiebt 33 Prüfungen für Runtime-Erkennung und -Reparatur,
IDE-Konfiguration, Systemwerkzeuge und Pyxel-Editoren nach
`test_runtime_tools.py`. Das neue Fachmodul läuft lokal in rund 3,7 Sekunden;
`test_guide.py` sinkt von 2.626 auf 1.920 Zeilen. Architekturtests begrenzen den
verbleibenden Sammeltest auf 2.000 und das neue Modul auf 750 Zeilen. Damit kann
dieser Integrationsbereich gezielt geprüft werden, ohne die weiterhin im
Sammeltest liegenden Kurs-, Inhalts- und Updateverträge einzusammeln. Die
vollständige normale Testsuite umfasst weiterhin 457 bestandene Prüfungen.

Der Update-Backend-Schnitt führt die unabhängige App- und allgemeine
Inhaltsprüfung parallel aus. Ist ein Repositorykurs ausgewählt, entfällt die
für diesen Kurs wirkungslose Abfrage des allgemeinen Inhaltsmanifests
vollständig; der bewusste Kursabgleich bleibt davon getrennt. Beide
Installationswege aktivieren geprüfte Inhaltsstände nun über denselben atomaren
Markerhelfer. Der zuvor bei jeder manuellen Prüfung geschriebene, aber nirgends
gelesene `update-status.json`-Cache entfällt. `updates.py` sinkt von 650 auf 649
Zeilen, `tools_view.py` bleibt bei 360 Zeilen. Drei neue gezielte Prüfungen
sichern Parallelität, den ausgelassenen Fremdkanal und das Größenbudget; die
vollständige normale Testsuite umfasst danach 460 bestandene Prüfungen.

Der erste gemeinsame Kursimport-Schnitt ersetzt die jeweils doppelt gepflegten
Installationsfolgen für neue und vorhandene Repository- beziehungsweise
ZIP-Kurse durch je eine interne Transaktion. Schreiben von Setup, Quelle und
Runtime sowie Registry-Aktivierung und Starterbereitstellung laufen dadurch
über denselben Pfad; nur das kontrollierte Neuanlegen eines Workspaces bleibt
eine ausdrückliche Option. Zwei neue Regressionstests sichern, dass beide
Importarten vorhandene Schülerdateien erhalten. `course_setup.py` sinkt von 467
auf 444 Zeilen und wird auf höchstens 450 Zeilen begrenzt. Die weiterhin 557
Zeilen umfassende Archivprüfung und -speicherung bleibt der nächste getrennte
Schnitt. Die vollständige normale Testsuite umfasst danach 463 bestandene
Prüfungen.

Der zweite Kursarchiv-Schnitt trennt ZIP-Format, vollständige Prüfung und
Erstellung von der atomaren Speicherung installierter Inhalte,
Runtime-Verträge und Quellenmarker. `course_archive.py` sinkt dadurch von 557
auf 308 Zeilen; `course_storage.py` hält die getrennte Speicherverantwortung bei
242 Zeilen. Zusammen umfassen beide Bereiche 550 statt zuvor 557 Zeilen. Ein
gemeinsamer atomarer JSON-Pfad ersetzt doppelte Markerlogik. Beim Kurs-Export
werden ausgewählte Quelldateien und Offline-Wheels außerdem nur noch einmal vom
Datenträger gelesen. Architekturtests begrenzen beide Module und verhindern
eine Rückvermischung von ZIP- und Speicherlogik. Die vollständige normale
Testsuite umfasst danach 464 bestandene Prüfungen.

Der dritte Runtime-Schnitt entfernt zwei verbliebene doppelte Paketprüfungen.
Schlägt eine Prüfung im Preflight fehl, wird derselbe Interpreter nicht mehr
unmittelbar mit einem identischen Subprocess-Aufruf geprüft. Ebenso überspringt
die anschließende Laufzeitsuche einen bereits geprüften und verworfenen
bevorzugten Interpreter. Zwei Verhaltensprüfungen sichern die genaue Zahl der
Paketproben; ein Architekturtest begrenzt `runtime.py` weiterhin auf höchstens
865 Zeilen. Das Modul sinkt von zuletzt 865 auf 863 Zeilen und damit insgesamt
38 Zeilen unter seinen Stand vor der Konsolidierung. Die vollständige normale
Testsuite umfasst danach 467 bestandene Prüfungen.

Der Datenkontroll-Schnitt macht den vollständigen lokalen Datenbestand erstmals
als zusammenhängenden Oberflächenablauf zugänglich. Ein portables ZIP enthält
Einstellungen, globale Dateien und sämtliche Daten erreichbarer registrierter
Kursordner einschließlich Lösungen, Projekte, Lernstände und Backups. Erneut
ladbare Inhaltscaches und Runtimes werden nicht unnötig dupliziert; symbolische
Links werden dokumentiert, aber nicht über die Datenwurzeln hinaus verfolgt.
Exportziele innerhalb der Quelldaten sind gesperrt, der Export wird atomar
aktiviert und temporäre Archive werden auch bei einem simulierten
Datenträgerfehler entfernt. Die getrennte Löschaktion validiert zunächst alle
erreichbaren Kurse, verlangt die exakte Texteingabe `ALLE LOKALEN DATEN` und
verschiebt danach Kurse sowie den vollständigen App-Datenordner in den
Systempapierkorb. Exporte und Kopien an anderen Orten bleiben ausdrücklich
unberührt. Acht neue Backend- und Architekturprüfungen sowie der erweiterte
NiceGUI-E2E-Schülerweg sichern diesen Ablauf; die vollständige normale
Testsuite umfasst danach 475 bestandene Prüfungen.

Der dritte Schnitt am zentralen Sammeltest verschiebt 16 Verträge für
Inhaltsoverlays, App- und Inhaltsupdates, atomare Aktivierung sowie
zertifikatsgebundene Kurs- und Trainerabgleiche nach
`test_content_updates.py`. Das Fachmodul läuft lokal in weniger als einer
Sekunde; `test_guide.py` sinkt von 1.920 auf 1.438 Zeilen. Architekturtests
begrenzen den verbleibenden Sammeltest auf 1.500 und das neue Modul auf 550
Zeilen. Die Paketmetadaten in `pyproject.toml` und die Laufzeitversion melden
auf dem Entwicklungszweig nun konsistent `0.8.0.dev0`; der vorhandene
Release-Versionscheck bestätigt den Stand. Die normale Testsuite umfasst
weiterhin 475 Prüfungen; alle vier separat markierten NiceGUI-E2E-Abläufe
bestehen ebenfalls.

Der selbst gepflegte Python-Produktivcode liegt nach diesem neuen
Freigabefeature bei 18.793 Zeilen und damit 47 Zeilen beziehungsweise rund 0,3
Prozent über der 0.8-Ausgangsbasis. Gegenüber dem vorherigen Zwischenstand
kommen netto 347 klar abgegrenzte Zeilen hinzu. Diese Zahl wird nicht durch
künstliche Verdichtung kaschiert: Exportvertrag und UI bleiben getrennt und
gezielt testbar; die folgende Konsolidierung konzentriert sich weiter auf
vorhandene Sonder- und Doppelpfade.

Freigabekriterium: Ein Upgrade von 0.7 auf 0.8 sowie simulierte Abbrüche und
beschädigte Laufzeitumgebungen werden reproduzierbar getestet, ohne vorhandene
Lernstände oder Projekte zu überschreiben.

Typische Abnahmeszenarien sind ein während des Speicherns entferntes
USB-Laufwerk, eine unterbrochene Runtime-Einrichtung, ein extern veränderter
Projektordner und die Wiederherstellung eines älteren Projektstands. Kein
Fehlerfall darf still einen neueren Datenstand vernichten.

## 0.9 – bereit für den Schuleinsatz

Ziel: in:si kann auf gemeinsam oder wechselnd genutzten Schulgeräten mit
nachvollziehbaren Kursquellen pilotiert werden.

Diese Etappe verschiebt den Blick vom einzelnen lokalen Arbeitsplatz auf reale
Schulumgebungen. Dort teilen sich häufig mehrere Personen ein Gerät, Kurse
stammen aus unterschiedlichen Quellen und technische Rechte müssen auch ohne
Entwicklerwissen verständlich sein.

- lokale Mehrbenutzerprofile mit getrennten Workspaces;
- sichtbare Berechtigungen für Kursinhalte, Trainer, Dateizugriffe und
  Programmstarts;
- signierte Kursveröffentlichungen und ein nachvollziehbares
  Herausgebervertrauen;
- validierte PyKIM-Sprachpakete mit kanonischen Lernbefehlen und lokalen
  API-Aliasen;
- mindestens eine weitere fachliche Engine aus HTML/CSS oder SQLite als Probe
  des neutralen Trainervertrags;
- dokumentierter Unterrichtspilot auf den unterstützten Plattformen;
- Rückmeldungen aus dem Pilotbetrieb hinsichtlich Bedienbarkeit,
  Barrierearmut, Datenschutz und Wiederherstellung auswerten.

Freigabekriterium: Profile und Kursrechte sind voneinander getrennt, ein
Kursupdate bleibt nachvollziehbar, und mindestens ein realer Unterrichtspilot
hat keine kritischen Datenverlust-, Sicherheits- oder Bedienprobleme ergeben.

Der Pilot soll mindestens Installation, Kurswechsel, Aufgabenbearbeitung,
Projektstart, externe IDE, Kursupdate, Export und Wiederherstellung abdecken.
Er dient nicht nur als Vorführung: Beobachtete Blockaden und kritische Befunde
werden vor 1.0 dokumentiert und bearbeitet.

## 1.0 – stabiler Produktvertrag

Ziel: eine langfristig wartbare, dokumentierte und verlässlich aktualisierbare
Desktop-Lernumgebung.

Version 1.0 ist weniger ein einzelnes großes Feature als eine belastbare Zusage.
Kursautorinnen, Schulen und Lernende sollen wissen, welche Formate unterstützt
werden, welche Daten bei einem Update erhalten bleiben und auf welchen
Plattformen die Schutzmechanismen tatsächlich geprüft sind.

- Kurs-, Trainer-, Setup-, Runtime- und Datenformate als stabile öffentliche
  Verträge dokumentieren;
- unterstützte Upgradepfade und Kompatibilitätsgrenzen festlegen;
- Produktionsverteilung für alle unterstützten Systeme abschließen; unter
  macOS insbesondere mit signiertem und notarisiertem Sandbox-Helper;
- Sicherheits- und Datenschutzprüfung gegen den veröffentlichten Datenbestand
  abschließen;
- deutsch- und englischsprachige Dokumentation für Lernende, Lehrkräfte,
  Kursautorinnen und Entwickler vollständig ausliefern;
- Installations-, Update-, Offline-, Sandbox- und Wiederherstellungsmatrix auf
  echten Zielgeräten bestehen;
- alle kritischen Befunde aus dem 0.9-Unterrichtspilot schließen.

Freigabekriterium: Für alle unterstützten Plattformen existiert ein geprüfter
Installations- und Upgradeweg. Dokumentierte 1.x-Kompatibilitätszusagen können
ohne bekannte kritische Sicherheits- oder Datenverlustrisiken eingehalten
werden.

Ab 1.0 werden inkompatible Änderungen an veröffentlichten Formaten nicht mehr
still vorgenommen. Sie benötigen eine neue Formatversion, einen dokumentierten
Migrationsweg oder eine ausdrücklich angekündigte Kompatibilitätsgrenze.

## 1.1 – Kursökosystem und Autorenworkflow

Ziel: Kursinhalte lassen sich modular wiederverwenden, nachvollziehbar pflegen
und um weitere Fachgebiete erweitern.

Nach der Stabilisierung des Kerns richtet sich 1.1 vor allem an Autorinnen und
Autoren. Wiederkehrende Erklärungen, Aufgabenbausteine oder Konfigurationen
sollen nicht in jedem Kurs kopiert werden müssen. Git bleibt dabei ein
optionaler Veröffentlichungsweg; lokale Ordner und ZIP-Dateien bleiben
vollwertig.

- wiederverwendbare, versionierte Inhaltsbibliotheken für den Kursbaukasten;
- verständlicher optionaler Git-Arbeitsablauf im Kursstudio;
- zusätzliche Fach-Engines wie HTML/CSS, SQLite und Filius;
- konfigurierbare Navigation und Werkzeuge für Mischkurse;
- Abhängigkeiten zwischen Kursen und Inhaltsbibliotheken sichtbar prüfen und
  aktualisieren;
- Autorenworkflow, Formate und Erweiterungsschnittstellen mit Beispielkursen
  dokumentieren.

Freigabekriterium: Ein Kurs kann Inhalte aus einer versionierten Bibliothek und
mindestens zwei unterschiedliche Fach-Engines reproduzierbar verwenden, ohne
den vollständig lokalen ZIP-Arbeitsweg vorauszusetzen oder einzuschränken.

Ein Konflikt zwischen Bibliotheksversionen muss vor Veröffentlichung sichtbar
werden. Ein Kursarchiv muss außerdem weiterhin alle für seinen Offlinebetrieb
benötigten Inhalte eindeutig beschreiben können.

## 1.2 – Projekte und Kompetenzentwicklung

Ziel: Längere Lernprojekte werden übersichtlich planbar und Lernfortschritt
kann über einzelne Aufgaben hinaus nachvollzogen werden.

Die Projektansicht soll nicht zu einem allgemeinen Aufgabenmanager werden.
Planung und Kompetenzzuordnung dienen unmittelbar dem Lernprojekt: Eine Karte
kann etwa auf Quellcode, Dokumentation, einen Test oder eine Reflexion zeigen.
Kompetenzmodelle bleiben optional und werden vom jeweiligen Kurs definiert.
Ausgewählte Ergebnisse sollen außerdem bewusst aus ihrem ursprünglichen Kurs in
einen persönlichen globalen Bestand übernommen werden können. So lässt sich
beispielsweise eine in einem Datenbankkurs entwickelte Datenbank später in
anderen Kursen oder eigenen Projekten weiterverwenden, ohne den gesamten
ursprünglichen Kurs kopieren zu müssen.

Vor dieser Erweiterung wird die logische und physische Ablagestruktur von
in:si als eigener Architekturentscheid überprüft. Ziel ist eine eindeutige
Trennung von versionierter, grundsätzlich unveränderlicher Kursquelle,
kursgebundenem persönlichem Workspace, App-Cache und Runtimes sowie einer
persönlichen kursübergreifenden Bibliothek. Der bereits vorhandene globale
Dateibereich ist dafür ein Vorläufer, aber noch kein ausreichendes
Wiederverwendungsmodell.

Die globale Bibliothek soll nicht nur ein gemeinsam beschreibbarer
`assets`-Ordner sein. Ergebnisse werden bewusst als eigenständige Bausteine
veröffentlicht und erhalten mindestens Typ, stabile Kennung, Revision,
Ursprungskurs beziehungsweise Ursprungsprojekt, Dateiliste und Prüfsummen.
Andere Kurse und Projekte binden eine konkrete Revision lesbar ein oder
übernehmen ausdrücklich eine eigene Kopie; sie verändern niemals still das
Original und brechen dadurch keine früheren Arbeiten. Der Begriff `assets`
bleibt den Dateien innerhalb eines solchen Bausteins oder Projekts vorbehalten,
während die übergreifende Ebene in der Oberfläche als persönliche Bibliothek
erscheint. Die bestehende globale Dateiablage wird später kontrolliert in
dieses Modell migriert, statt daneben einen zweiten globalen Speicher zu
eröffnen.

- lokale Kanban-Boards mit Karten, Checklisten und Projektdateiverknüpfungen;
- Kompetenzmodelle als optionale, kursdefinierte Struktur;
- Aufgaben, Projekte und Rückmeldungen nachvollziehbar Kompetenzen zuordnen;
- ausgewählte Kursergebnisse mit nachvollziehbarer Herkunft in den persönlichen
  globalen Bestand übernehmen und in anderen Kursen oder Projekten verwenden;
- wiederverwendbare Bausteine mit stabiler Kennung und konkreter Revision
  referenzieren oder bewusst als unabhängige Kopie übernehmen;
- persönliche Übersichten für Projektstand und Kompetenzentwicklung;
- verständlicher Export der zugehörigen lokalen Daten ohne Bindung an einen
  zentralen Dienst.

Freigabekriterium: Ein mehrwöchiges Projekt lässt sich lokal planen,
dokumentieren und mit einem optionalen Kompetenzmodell auswerten. Bestehende
Kurse ohne Kompetenzdaten funktionieren unverändert weiter.

Selbsteinschätzungen, Trainerergebnisse und Rückmeldungen müssen unterscheidbar
bleiben. in:si leitet daraus nicht automatisch Schulnoten oder vermeintlich
objektive Gesamtbewertungen ab.

## 1.3 – lokale Zusammenarbeit und Peer Review

Ziel: Lernende und Lehrkräfte können Ergebnisse austauschen und Rückmeldungen
geben, ohne dass in:si einen verpflichtenden Cloud-Dienst oder ein zentrales
Benutzerkonto voraussetzt.

Zusammenarbeit bedeutet hier zuerst einen nachvollziehbaren Datenaustausch, nicht
den Aufbau eines eigenen sozialen Netzwerks. Eine Schule kann einen geeigneten
Austauschweg bereitstellen; in:si soll die Pakete, Rollen, Versionen und
Rückgaben kontrollieren, ohne einen bestimmten Anbieter vorzuschreiben.

- Peer-Review-Aufträge mit klaren Kriterien und getrennten Rollen;
- portable Übergabe von Abgaben und Rückmeldungen;
- nachvollziehbare Versionen, Autorenschaft und Konfliktbehandlung beim Import;
- datensparsame Zusammenarbeit über ausdrücklich gewählte lokale oder
  schulisch betriebene Austauschwege;
- Berechtigungs-, Lösch- und Aufbewahrungsregeln für geteilte Inhalte;
- Pilotprüfung der Zusammenarbeit auf realen Schulgeräten.

Freigabekriterium: Eine Abgabe kann kontrolliert verteilt, anonymisiert oder
namentlich begutachtet, zurückgegeben und erneut importiert werden. Der gesamte
Ablauf bleibt ohne Herstellerkonto möglich und legt keine Daten ohne bewusste
Aktion außerhalb des gewählten Speicherorts ab.

Echtzeit-Kollaboration ist kein notwendiges Ziel für 1.3. Vorrang haben
verständliche Übergaben, Konfliktfreiheit, Datensparsamkeit und ein Ablauf, der
auch mit USB-Datenträgern oder schulisch verwalteten Dateiablagen funktioniert.

## Leitplanken über 1.3 hinaus

ZIP-Export und vollständig lokale Kurse bleiben unabhängig davon gleichwertige
Arbeitswege. Fortschritt, Projekte, Sicherungen und installierte Kurse dürfen
bei keiner Migration still verloren gehen oder überschrieben werden.

Neue Funktionen müssen weiterhin ohne verpflichtendes Herstellerkonto
nutzbar, in exportierbaren Formaten dokumentiert und gegenüber bestehenden
Kursen abwärtskompatibel oder sauber migrierbar sein. Eine Funktion wird nicht
allein deshalb Teil des Kerns, weil sie technisch möglich ist; sie muss einen
konkreten Lern-, Unterrichts- oder Autorenablauf verbessern.
