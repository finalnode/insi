# Windows-Praxistest für in:si 0.7.2

Diese kurze Abnahme prüft den portablen Ein-EXE-Testkandidaten auf einem echten
Windows-Schulgerät. Sie ist vor der Veröffentlichung von 0.7.2 einmal lokal,
aus einer iServ-/UNC-Ablage und von einem USB-Datenträger durchzuführen.

## Vorbereitung

1. Das Windows-Artefakt des 0.7.2-Testkandidaten vollständig entpacken. Nicht
   nur einzelne Dateien aus dem ZIP starten oder kopieren.
2. Im entpackten App-Ordner prüfen: `insi.exe` ist vorhanden,
   `insi-python.exe` darf nicht vorhanden sein.
3. Windows-Version, vollständigen Testpfad und beim USB-Test das Dateisystem
   des Datenträgers (zum Beispiel NTFS oder exFAT) notieren.

## Abnahme je Speicherort

Die folgenden Schritte nacheinander aus einem lokalen Ordner, der betroffenen
iServ-/UNC-Ablage und vom USB-Datenträger ausführen:

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

## Ergebnisprotokoll

| Speicherort | Pfad / Dateisystem | App-Start | Code | Grafik | Beenden / Neustart | Bemerkung |
|---|---|---|---|---|---|---|
| lokal |  |  |  |  |  |  |
| iServ / UNC |  |  |  |  |  |  |
| USB |  |  |  |  |  |  |

Ein Fehlschlag ist mit Screenshot, vollständigem Pfad, Windows-Version und dem
genauen Wortlaut der Meldung zu dokumentieren. Bis alle drei Zeilen erfolgreich
sind, bleibt 0.7.2 ein Testkandidat.
