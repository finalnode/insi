# Datenschutz und Datenbestand

Stand: 21. August 2026, in:si 0.7.0

Dieses Dokument beschreibt technisch, welche Daten in:si verarbeitet, wo sie
gespeichert und wann sie übertragen werden. Es ist keine fertige
Datenschutzerklärung für jede Schule. Die einsetzende Schule beziehungsweise
der jeweilige Träger muss insbesondere Verantwortliche, Datenschutzkontakt,
Rechtsgrundlage, konkrete Aufbewahrungsfristen und gegebenenfalls eingesetzte
schulische Austauschdienste ergänzen.

Die DSGVO verlangt unter anderem Datenminimierung und Speicherbegrenzung sowie
Informationen für betroffene Personen. Maßgeblich sind insbesondere
[Artikel 5 und 13 DSGVO](https://eur-lex.europa.eu/eli/reg/2016/679/oj) und die
[Hinweise der BfDI zu Informationspflichten](https://www.bfdi.bund.de/DE/Buerger/Inhalte/Allgemein/Datenschutz/Informationspflichten.html).

## Kurzfassung

- in:si benötigt kein Herstellerkonto und besitzt keinen zentralen in:si-
  Server für Lernstände oder Schülerdateien.
- Lernstände, Lösungen, Projekte und Einstellungen liegen lokal auf dem
  verwendeten Gerät beziehungsweise im ausdrücklich gewählten Kursordner.
- Die Anwendung enthält keine App-Telemetrie, keine Analytics und keine
  Werbe- oder Tracking-SDKs.
- App- und globale Inhaltsupdates werden erst nach einem bewussten Klick über
  GitHub geprüft.
- Repository-basierte Kursinhalte werden ebenfalls nur nach einem bewussten
  Import beziehungsweise Klick auf **Kursinhalte abgleichen** von der im Kurs
  angegebenen GitHub-Quelle geladen.
- Integriert gestarteter Kurs- und Schülercode erhält keinen Netzwerkzugriff.
- Eine verschlüsselte Abgabe wird nur lokal erzeugt. in:si lädt sie nicht selbst
  hoch; die Nutzerin oder der Nutzer entscheidet über die Weitergabe.
- Der lokale Systembenutzername wird nicht in den Lernstandsexport übernommen.

## Rollen und Verantwortlichkeit

Das Open-Source-Projekt stellt die Software bereit und erhält im normalen
lokalen Betrieb keine Lern- oder Schülerdaten. Wer in:si im Unterricht einsetzt
und Zwecke sowie Mittel der Verarbeitung festlegt, ist typischerweise die
Schule oder deren Träger. Die genaue Zuordnung richtet sich nach dem jeweiligen
Einsatz und dem anwendbaren Landes- und Schulrecht.

Vor einem Unterrichtseinsatz sollte die verantwortliche Stelle mindestens
festlegen:

- Name und Kontaktdaten der verantwortlichen Stelle und ihres
  Datenschutzkontakts;
- Rechtsgrundlage und Zweck der Verarbeitung;
- ob Klarnamen erforderlich sind oder Kürzel genügen;
- Löschzeitpunkte für Lernstände, Abgaben und Sicherungen;
- Empfänger von Abgaben und Rückmeldungen;
- zulässige Kursrepositories, Paketquellen und schulische Austauschwege;
- Verfahren für Auskunft, Berichtigung, Export und Löschung;
- technische Regeln für gemeinsam genutzte Geräte und Datenträger.

## Lokale Speicherorte und Datenkategorien

`<Kursordner>` bezeichnet den bei der Einrichtung ausgewählten portablen
Arbeitsordner. Der Konfigurationsordner ist standardmäßig `~/.pykim`; für Tests
und verwaltete Installationen kann er über `PYKIM_CONFIG_DIR` abweichend
gesetzt sein.

| Speicherort | Inhalt | Zweck | Personenbezug und Aufbewahrung |
|---|---|---|---|
| `~/.pykim/config.json` | bekannte und aktiver Kursordner, bevorzugte IDE und Interpreterpfad | lokale Wiederherstellung der Auswahl und Werkzeugkonfiguration | Pfade können Benutzer- oder Gerätenamen enthalten; bleibt bis zum manuellen Entfernen beziehungsweise Zurücksetzen der Konfiguration erhalten |
| `~/.pykim/content/` | geprüfte Kurs- und Inhaltsstände, Manifeste, aktive Versionsmarker und letzter Updatezustand | Offlinebetrieb, atomare Updates und Integritätsprüfung | normalerweise Inhalts- und technische Versionsdaten, keine Lösungen; alte Caches werden derzeit nicht vollständig automatisch bereinigt |
| `~/.pykim/runtimes/` | verwaltete Python-Umgebungen und installierte Pakete | reproduzierbare Kurslaufzeiten | üblicherweise keine Lerndaten; bleibt bis zur manuellen Entfernung oder späteren Runtime-Migration erhalten |
| `~/.pykim/thonny/` | von in:si getrennt angelegtes Thonny-Profil | kursbezogene IDE-Konfiguration | kann durch Thonny weitere lokale Einstellungen und Verlauf enthalten; Löschung manuell nach Ende des Einsatzes |
| `~/.pykim/insi-workspace/Dateien/` | bewusst global importierte Dateien | kursübergreifende lokale Ressourcen | Inhalt wird von der nutzenden Person bestimmt; bleibt bis zur manuellen Löschung |
| `<Kursordner>/.pykim-course.json` | optionaler Name oder Kürzel sowie technische Kurskennung | lokale Ansprache und Zuordnung eines bewusst erzeugten Exports | unmittelbar personenbezogen, wenn ein Klarname eingetragen wird; Kürzel oder leerer Wert sind möglich |
| `<Kursordner>/.pykim/progress.json` | Aufgabenversuche, Zeitstempel, Quelltexte, Testergebnisse, Hinweise, freie Antworten und Dokubuch-Einträge | Lernfortschritt, Rückmeldung und Fortsetzung der Arbeit | Lerndaten; bleibt lokal bis zum Löschen oder Zurücksetzen, wobei beim Zurücksetzen ein Backup entstehen kann |
| `<Kursordner>/.pykim/backups/` | ältere Lernstände, zurückgesetzte Aufgaben, migrierte Setupdateien und Projektstände | Schutz vor Datenverlust und Wiederherstellung | kann vollständige ältere Lösungen und Lernstände enthalten; Projektstände sind auf zehn je Projekt begrenzt, andere Backups haben derzeit keine allgemeine automatische Frist |
| `<Kursordner>/.pykim/author_drafts/` | nicht veröffentlichte Aufgaben- und Trainerentwürfe | Kursentwicklung | kann Namen, Quellen und freie Texte von Autorinnen und Autoren enthalten; bleibt bis zur manuellen Löschung |
| `<Kursordner>/.pykim/submission-certificate.pykim-cert` | öffentliches Kurszertifikat mit Schule, Lehrkraft, Kurs, Gültigkeit und öffentlichem Schlüssel | lokale Verschlüsselung und Prüfung von Abgaben | enthält keine privaten Schlüssel; bleibt bis zur Entfernung oder zum Zertifikatswechsel |
| `<Kursordner>/Aufgaben/`, `Projekte/`, `eigene_projekte/`, `Dateien/` und `erweiterungen.py` | Lösungen, Projektcode, Dokumentationen und bewusst importierte Dateien | eigentliche Lern- und Projektarbeit | Inhalt wird von Lernenden bestimmt und kann personenbezogene Freitexte enthalten; bleibt bis zur manuellen Löschung oder Kurslöschung |
| `<Kursordner>/.vscode/` | ausgewählter Interpreter und empfohlene Erweiterungen | Öffnen des Kurses in VS Code | technische lokale Pfade können Gerätenamen enthalten; kann manuell gelöscht werden |
| `<Kursordner>/abgaben/` oder gewählter Exportordner | verschlüsselte `.pykim-abgabe`-Dateien | bewusste Übergabe an eine Lehrkraft | enthält verschlüsselte Lerndaten; bleibt bis zur manuellen Löschung |
| temporäre `insi-*`-Laufordner des Betriebssystems | private Laufkopie, temporäres Home, Programmausgaben und Schreibdaten eines integrierten Starts | Sandbox und kontrollierte Rückführung gültiger Versuche | wird nach normalem Laufende entfernt; nach einem harten Systemabbruch können Betriebssystemreste bis zur nächsten Systembereinigung verbleiben |

Der vorhandene Basisordner heißt aus Kompatibilitätsgründen weiterhin
`.pykim`. Seine Bezeichnung bedeutet nicht, dass die Daten an PyKIM oder einen
externen Dienst übertragen werden.

Wenn im Kurs kein Name eingetragen ist, liest die Oberfläche den Anzeigenamen
oder Kontonamen des lokalen Betriebssystemkontos für die Begrüßung. Dieser Wert
wird dafür nur im Arbeitsspeicher verwendet, nicht in die Kursmetadaten
geschrieben und nicht exportiert. Auf gemeinsam genutzten Konten kann stattdessen
im Kurs ein nichtsprechendes Kürzel hinterlegt werden.

## Netzwerkverbindungen

Die App bindet ihre lokale Oberfläche ausschließlich an `127.0.0.1`. Diese
Verbindung zwischen Browser beziehungsweise WebView und dem lokalen NiceGUI-
Server verlässt den Rechner nicht.

Externe Verbindungen entstehen nur in den folgenden Situationen:

| Auslöser | Ziel | Übertragene Anfragedaten | Zweck |
|---|---|---|---|
| Klick auf **Jetzt prüfen** oder den Updatehinweis | `api.github.com`, `raw.githubusercontent.com` und gegebenenfalls GitHub Releases | angefragte App-/Inhaltsversion, IP- und übliche HTTPS-Verbindungsdaten, User-Agent `insi/<Version>` | verfügbare App- und Inhaltsupdates feststellen beziehungsweise bewusst herunterladen |
| Import eines repository-basierten Kurses oder Klick auf **Kursinhalte abgleichen** | die im Kurs angegebene GitHub-Quelle über `api.github.com` und `raw.githubusercontent.com` | Repository, Branch und benötigte Inhaltsdateien sowie technische Verbindungsdaten | Kursstand prüfen, herunterladen und anhand von Hashes validieren |
| Klick auf **Katalog aktualisieren** | `raw.githubusercontent.com/finalnode/insi` | Anfrage nach dem öffentlichen Kurskatalog und technische Verbindungsdaten | optionale Aktualisierung der mitgelieferten Kursliste |
| Installation oder Reparatur einer Runtime ohne vollständig eingebettete Wheels | konfigurierte Python-Paketquelle, üblicherweise PyPI | Paketnamen, Versionen, Plattformdaten des Paketabrufs und technische Verbindungsdaten | ausdrücklich benötigte Kursabhängigkeiten installieren |
| Start der optionalen Browser-Spielwiese | `cdn.jsdelivr.net` | Abruf von Pyodide-Dateien und technische Verbindungsdaten | Python ausschließlich im Browser-Worker laden |
| Import oder Export eines repository-gebundenen Kurszertifikats | die im Zertifikat angegebene öffentliche GitHub-Quelle | Zertifikatsdateiname beziehungsweise Hashliste und technische Verbindungsdaten | Berechtigung und bewertungsrelevanten Kursstand prüfen |
| Öffnen eines externen Links oder Downloadbuttons | das sichtbar bezeichnete Ziel | normale Browser-Anfragedaten | Dokumentation, Programme oder Releases öffnen |

Die Serverbetreiber verarbeiten technisch unter anderem IP-Adresse und
Verbindungsmetadaten nach ihren eigenen Bedingungen. in:si sendet bei diesen
Anfragen keine Lösungen, Lernstände, Namen, Dokubuchtexte oder Projektdateien.
Eine Ausnahme wäre nur eine Datei, die eine Person anschließend selbst über
einen externen Dienst hochlädt; dieser Upload erfolgt außerhalb von in:si.

Wer keinerlei externe Verbindung wünscht, verwendet ein portables Kurs-ZIP mit
eingebetteten Abhängigkeiten und löst keine Onlineaktion aus oder blockiert den
Netzwerkzugriff der App zusätzlich auf Betriebssystemebene. Bereits lokal
aktivierte Inhalte bleiben ohne erneuten Repository-Abgleich nutzbar.

## Empfänger und Weitergabe

Im normalen Offlinebetrieb verbleiben die Daten bei der Person beziehungsweise
Organisation, die das Gerät und den gewählten Kursordner kontrolliert. Das
in:si-Projekt erhält keine Kopie.

- GitHub, jsDelivr und gegebenenfalls eine Python-Paketquelle erhalten bei
  bewusst ausgelösten Onlineaktionen die oben beschriebenen technischen
  Verbindungs- und Anfragedaten, aber keine Lernstände oder Lösungen.
- Eine Lehrkraft erhält Lerndaten nur, wenn eine verschlüsselte Abgabedatei
  bewusst übergeben wird. Den privaten Schlüssel verwaltet die Lehrkraft
  außerhalb der Schüleranwendung.
- Moodle, schulische Dateiablagen, USB-Datenträger oder andere Austauschwege
  werden nicht automatisch angesprochen. Sie werden erst durch die bewusste
  Weitergabe einer Datei zu Empfängern beziehungsweise Speicherorten.
- Externe IDEs und deren Erweiterungen können eigene Empfänger und
  Netzwerkziele besitzen. Dafür gelten deren Konfiguration und
  Datenschutzhinweise.
- Kursautorinnen und Kursautoren erhalten durch das bloße Installieren oder
  Nutzen eines Kurses keine Schülerlösungen.

## Integrierter Fremdcode und externe IDEs

Integriert gestarteter Kurs- und Schülercode erhält durch die geprüften
OS-Sandbox-Adapter keinen Netzwerkzugriff. Ohne funktionsfähigen Adapter wird
der Start gesperrt. Das vollständige Modell steht in [SECURITY.md](SECURITY.md).

**In IDE öffnen** ist eine bewusste Grenze: Thonny, VS Code und dort gestartete
Programme laufen mit den normalen Rechten des Benutzerkontos. in:si kann deren
Netzwerkzugriffe, Erweiterungen, Telemetrie oder lokale Datenspeicherung nicht
kontrollieren. Dafür gelten die Einstellungen und Datenschutzhinweise des
jeweiligen Werkzeugs.

## Inhalt des verschlüsselten Lernstandsexports

Eine `.pykim-abgabe` wird lokal für den öffentlichen Schlüssel der Lehrkraft
verschlüsselt. Lesbar ist sie nur mit dem passenden privaten Schlüssel und
dessen Passwort. in:si überträgt die Datei nicht selbst.

Standardmäßig enthält der entschlüsselte Datensatz:

- den im Kurs bewusst eingetragenen Namen oder das Kürzel; bei leerer Angabe
  bleibt der Wert leer;
- Exportzeitpunkt sowie Versionen von in:si, PyKIM, Python und das
  Betriebssystem;
- Aufgabenkennungen, aktuelle Aufgabenquelltexte und Codefingerprints;
- jeweils letztes Testergebnis mit Zeitstempel, Prüfergebnissen und
  Optimierungswerten;
- eine zusammengefasste Zahl bearbeiteter und bestandener Aufgaben.

Der lokale Systembenutzername wird nicht exportiert. Dokubuch und freie
Antworten werden nur aufgenommen, wenn die entsprechende Checkbox bewusst
aktiviert wird. Andere Projekte, globale Dateien, IDE-Konfigurationen, absolute
Pfade, private Schlüssel und der gesamte ungekürzte Lernstandsverlauf sind
nicht Bestandteil des Standardexports.

Vor der Weitergabe sollte die erzeugte Datei wie jede Schülerabgabe behandelt
und nur über den von der Schule vorgesehenen Weg übermittelt werden. Nach dem
Import gelten beim Empfänger dessen Aufbewahrungs- und Löschregeln.

## Löschen, Exportieren und Aufbewahren

in:si legt keine allgemeine schulische Aufbewahrungsfrist fest. Die
verantwortliche Stelle sollte kurze, zweckgebundene Fristen definieren. Die
Software bewahrt lokale Daten ansonsten auf, damit Arbeit nicht unerwartet
verloren geht.

- **Einzelne Aufgabe:** Das Zurücksetzen entfernt zugehörige Versuche aus dem
  aktiven Lernstand, legt aber zuvor ein lokales Backup unter
  `<Kursordner>/.pykim/backups/` an. Für eine vollständige Löschung muss auch
  dieses Backup kontrolliert entfernt werden.
- **Projekt:** Projektdateien lassen sich im gewählten Kursordner verwalten.
  Vor integrierten Starts entstehen höchstens zehn Snapshots je Projekt unter
  `.pykim/backups/project-snapshots/`; ältere werden automatisch entfernt.
- **Gesamter Kurs:** Die Kursverwaltung kann einen eindeutig erkannten Kurs in
  den Systempapierkorb verschieben. Erst das Leeren des Papierkorbs entfernt
  ihn endgültig. Exporte an anderen Orten und globale Dateien bleiben davon
  unberührt.
- **Globale App-Daten:** Konfiguration, Inhaltscache, Runtime, Thonny-Profil und
  globale Dateien liegen standardmäßig unter `~/.pykim`. Sie müssen bei Bedarf
  gezielt über den Dateimanager entfernt werden; eine vollständige
  Löschoberfläche ist für 0.8 geplant.
- **Abgaben:** Lokal erzeugte und bereits an Moodle, Dateiserver, USB-Stick oder
  andere Stellen kopierte Abgaben müssen an jedem Speicherort entsprechend der
  schulischen Regelung gelöscht werden.

Vor dem Löschen sollte geprüft werden, ob Projekte oder Kursdateien noch
benötigt und in einen ausdrücklich gewählten Ordner exportiert werden sollen.
Das bloße Deinstallieren der App entfernt lokale Kursordner und `~/.pykim`
bewusst nicht automatisch.

## Schutzmaßnahmen und verbleibende Grenzen

- lokale Verarbeitung ohne Herstellerkonto oder zentralen Lernstandserver;
- Trennung von veröffentlichter Kursquelle und persönlichem Workspace;
- verschlüsselte Abgaben mit getrenntem privatem Lehrkraftschlüssel;
- TLS-Prüfung für externe HTTPS-Verbindungen;
- Hash- und Pfadprüfung für Kursinhalte, Zertifikate, Archive und Wheels;
- fail-closed Sandbox mit gesperrtem Netzwerk für integrierten Fremdcode;
- begrenzte Laufzeit, Ausgabe, Prozesse, Arbeitsspeicher und Schreibmenge;
- keine App-Analytics, externen Schriftarten oder Trackingdienste.

Lokale Speicherung schützt nicht automatisch vor anderen Personen mit Zugriff
auf dasselbe Betriebssystemkonto, vor Geräteverlust, Schadsoftware oder
unverschlüsselten Datenträgern. Für sensible Lerndaten sollten Schulen daher
getrennte Betriebssystemkonten, Gerätesperren, Datenträgerverschlüsselung,
geregelte Backups und passende Dateirechte einsetzen. Lokale Mehrbenutzerprofile
innerhalb von in:si sind erst für 0.9 geplant.

Aktuelle technische Einschränkungen und Workarounds stehen in
[KNOWN_ISSUES.md](KNOWN_ISSUES.md). Sicherheitslücken sollen nach dem in
[SECURITY.md](SECURITY.md) beschriebenen Verfahren gemeldet werden.
