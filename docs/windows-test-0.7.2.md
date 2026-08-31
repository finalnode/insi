# Windows-Praxistest für in:si 0.7.2

Diese kurze Abnahme prüft den portablen Ein-EXE-Testkandidaten auf einem echten
Windows-Schulgerät. Die integrierte PyKIM-Ausführung benötigt einen lokalen
NTFS-Pfad: AppContainer-SIDs lassen sich nicht sicher auf SMB-/WebDAV-Pfade
übertragen, ohne die zugesagte Netzwerksperre aufzuweichen. iServ und USB
werden deshalb als Transportwege geprüft; von dort wird der vollständige
App-Ordner vor dem Start lokal kopiert.

## Vorbereitung

1. Das Windows-Artefakt des 0.7.2-Testkandidaten vollständig entpacken. Nicht
   nur einzelne Dateien aus dem ZIP starten oder kopieren.
2. Im entpackten App-Ordner prüfen: `insi.exe` ist vorhanden,
   `insi-python.exe` darf nicht vorhanden sein.
3. Einen lokalen Testordner auf einem NTFS-Laufwerk bestimmen, zum Beispiel
   `%LOCALAPPDATA%\in-si-test\0.7.2`.
4. Windows-Version, vollständigen Quell- und Zielpfad und beim USB-Test das
   Dateisystem des Datenträgers notieren.

## Lokale Funktionsabnahme

Den vollständigen entpackten Ordner auf das lokale NTFS-Laufwerk kopieren und
dort die folgenden Schritte ausführen:

1. `insi.exe` starten. Es darf weder ein zweites Konsolenfenster noch die
   Meldung **Unhandled exception in script** erscheinen.
2. Den PyKIM-Standardkurs öffnen und ein vorhandenes Codebeispiel ausführen.
   Die Ausgabe muss erscheinen; insbesondere dürfen weder `WinError 32` noch
   `WinError 87` oder ein fehlgeschlagener AppContainer-Probelauf gemeldet
   werden.
3. Ein grafisches PyKIM-/Pyxel-Beispiel starten und prüfen, ob dessen Fenster
   sichtbar geöffnet und wieder geschlossen werden kann.
4. in:si schließen und im Task-Manager prüfen, dass anschließend kein
   `insi.exe`-Prozess zurückbleibt.
5. in:si erneut starten und kontrollieren, dass der zuletzt verwendete Kurs
   weiterhin geöffnet werden kann.

Wenn der Kurs selbst auf einem Netzlaufwerk liegt, muss **Ausführen** ohne
langen Probelauf auf die lokale Pfadgrenze und die externe IDE hinweisen. Für
die integrierte Ausführung den Kurs ebenfalls auf das lokale NTFS-Laufwerk
kopieren.

## iServ-/UNC- und USB-Transport

1. Den vollständigen App-Ordner in die iServ-/UNC-Ablage legen. Ein direkter
   Start von `insi.exe` dort muss sofort einen verständlichen Hinweis zum
   lokalen Kopieren anzeigen. Es dürfen weder `icacls.exe`-Fenster erscheinen
   noch ein 45-Sekunden-AppContainer-Timeout abgewartet werden.
2. Den Ordner von der iServ-/UNC-Ablage in den lokalen Testordner kopieren und
   die lokale Funktionsabnahme wiederholen.
3. Dasselbe mit dem USB-Datenträger als Quelle wiederholen. Ein direkter Start
   von USB ist kein Freigabekriterium; insbesondere exFAT bietet nicht die vom
   AppContainer benötigten NTFS-ACLs.

## Ergebnisprotokoll

| Transport / Test | Quell- und Zielpfad / Dateisystem | Hinweis bzw. App-Start | Code | Grafik | Beenden / Neustart | Bemerkung |
|---|---|---|---|---|---|---|
| lokales NTFS |  |  |  |  |  |  |
| iServ / UNC → lokales NTFS |  |  |  |  |  |  |
| USB → lokales NTFS |  |  |  |  |  |  |

Ein Fehlschlag ist mit Screenshot, vollständigem Pfad, Windows-Version und dem
genauen Wortlaut der Meldung zu dokumentieren. Bis alle drei Zeilen erfolgreich
sind, bleibt 0.7.2 ein Testkandidat.
