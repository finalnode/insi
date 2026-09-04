# Windows-Praxistest für in:si 0.7.2

Diese Abnahme prüft den portablen Ein-EXE-Testkandidaten auf einem echten
Windows-Schulgerät. `insi.exe` und der Kurs dürfen dabei direkt in der
iServ-/UNC-Ablage liegen. in:si spiegelt die Laufzeit und die für einen
AppContainer-Lauf freigegebenen Dateien transparent in den lokalen
Benutzerbereich; der Bedienweg bleibt der Start vom Netzlaufwerk.

## Vorbereitung

1. Das Windows-Artefakt des 0.7.2-Testkandidaten vollständig entpacken. Nicht
   nur einzelne Dateien aus dem ZIP starten oder kopieren.
2. Im entpackten App-Ordner prüfen: `insi.exe` ist vorhanden,
   `insi-python.exe` darf nicht vorhanden sein.
3. Den vollständigen entpackten App-Ordner in der betroffenen iServ-/UNC-Ablage
   ablegen. Er wird nicht manuell auf ein lokales Laufwerk kopiert.
4. Einen PyKIM-Kurs in derselben oder einer anderen erreichbaren
   Netzlaufwerkablage auswählen.
5. Windows-Version und vollständige App- und Kurspfade notieren.

## Abnahme vom Netzlaufwerk

1. `insi.exe` direkt im iServ-/UNC-Ordner starten. Beim ersten Start darf die
   lokale Vorbereitung etwas dauern; anschließend muss in:si automatisch und
   ohne Aufforderung zum manuellen Kopieren erscheinen. Es darf weder ein
   zweites Konsolenfenster noch **Unhandled exception in script** erscheinen.
2. Den PyKIM-Standardkurs öffnen und ein vorhandenes Codebeispiel ausführen.
   Die Ausgabe muss erscheinen; insbesondere dürfen weder `WinError 32` noch
   `WinError 87` oder ein fehlgeschlagener AppContainer-Probelauf gemeldet
   werden. Es dürfen keine sichtbaren `icacls.exe`-Fenster aufblinken.
3. Ein grafisches PyKIM-/Pyxel-Beispiel starten und prüfen, ob dessen Fenster
   sichtbar geöffnet und wieder geschlossen werden kann.
4. Ein Projekt im Netzwerkkurs starten, eine kleine erlaubte Ausgabedatei
   erzeugen und prüfen, dass sie nach Prozessende im Netzlaufwerk vorhanden ist.
5. Dieselbe Projektdatei während eines laufenden Programms außerhalb von in:si
   ändern. in:si darf diese Fremdänderung beim Zurückschreiben nicht
   überschreiben und muss den Synchronisationskonflikt melden.
6. in:si schließen und im Task-Manager prüfen, dass anschließend kein
   `insi.exe`-Prozess zurückbleibt.
7. in:si erneut direkt aus dem UNC-Ordner starten. Der bereits lokal
   zwischengespeicherte, unveränderte Build muss nun deutlich schneller
   erscheinen und den Netzwerkkurs weiterhin öffnen können.

## Zusätzliche Speicherorte

Die Schritte 1 bis 3 zusätzlich mit lokal liegender App sowie von einem
USB-Datenträger wiederholen. Auf allen Wegen bleibt nur `insi.exe` der sichtbare
Starter.

## Ergebnisprotokoll

| Speicherort | App-/Kurspfad bzw. Dateisystem | App-Start | Code / Grafik | Sync / Konflikt | Beenden / Neustart | Bemerkung |
|---|---|---|---|---|---|---|
| iServ / UNC |  |  |  |  |  |  |
| lokales NTFS |  |  |  |  |  |  |
| USB |  |  |  |  |  |  |

Ein Fehlschlag ist mit Screenshot, vollständigem Pfad, Windows-Version und dem
genauen Wortlaut der Meldung zu dokumentieren. Bis alle drei Zeilen erfolgreich
sind, bleibt 0.7.2 ein Testkandidat.
