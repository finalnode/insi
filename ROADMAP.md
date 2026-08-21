# Roadmap bis in:si 1.3

Diese Roadmap beschreibt die geplanten Qualitätsstufen bis zur ersten stabilen
Version 1.0 und die darauf aufbauenden Etappen bis 1.3. Die Versionsnummern sind
Zielkorridore, keine festen Termine. Ein Meilenstein gilt erst als
abgeschlossen, wenn neben den Funktionen auch seine Migrationen, Dokumentation
und Plattformprüfungen fertig sind.

| Version | Schwerpunkt | Sichtbares Ergebnis |
|---|---|---|
| 0.7 | Sicherheit und technische Entkopplung | geschützte Programmläufe, neutraler Trainervertrag und neuer Kurseditor |
| 0.8 | Zuverlässigkeit | getestete Migrationen, Wiederherstellung und vollständige Datenkontrolle |
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

## 0.8 – verlässliche Daten und Wiederherstellung

Ziel: Updates, beschädigte Umgebungen und unterbrochene Arbeitsabläufe dürfen
keine Lernarbeit verlieren.

Mit 0.7 kann in:si Daten bereits getrennt speichern und Sicherungsstände
anlegen. In 0.8 werden daraus für Nutzerinnen und Nutzer sichtbare,
versionsübergreifend getestete Abläufe. Entscheidend ist nicht nur, dass ein
Backup existiert, sondern dass sein Inhalt verständlich ausgewählt und sicher
wiederhergestellt werden kann.

- verwaltete Kursumgebungen bei geändertem Runtime-Vertrag automatisch neu
  aufbauen und versionsübergreifend migrieren;
- versionierte Migrationen für Einstellungen, Lernstände und Kursdaten;
- robuste Behandlung entfernter USB-Laufwerke und unerwarteter App-Abbrüche;
- vorhandene automatische Projektstände sichtbar auswählen und
  wiederherstellen;
- Backup-, Import- und Wiederherstellungsabläufe mit realistischen
  Fehlerfällen testen;
- Datenexport und vollständiges lokales Löschen in der Oberfläche verständlich
  zugänglich machen.

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

- lokale Kanban-Boards mit Karten, Checklisten und Projektdateiverknüpfungen;
- Kompetenzmodelle als optionale, kursdefinierte Struktur;
- Aufgaben, Projekte und Rückmeldungen nachvollziehbar Kompetenzen zuordnen;
- ausgewählte Kursergebnisse mit nachvollziehbarer Herkunft in den persönlichen
  globalen Bestand übernehmen und in anderen Kursen oder Projekten verwenden;
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
