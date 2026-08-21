# Datenschutz und Sicherheit

in:si arbeitet offline-first und benötigt keine zentralen Benutzerkonten. Das
bedeutet nicht, dass keine personenbezogenen Daten entstehen: Namen oder Kürzel,
Lernstände, Quellcode, Rückmeldungen und Exporte können einer Person zugeordnet
werden und müssen auf Schulgeräten entsprechend behandelt werden.

## Datenhaltung

Persönliche Daten liegen grundsätzlich im gewählten Kursordner. Die Anwendung
überträgt Lernstände oder Quellcode nicht automatisch. Netzwerkzugriffe erfolgen
bei bewusst ausgelösten Kursinstallationen, Katalog- oder Updateprüfungen sowie
beim Aufbau einer Runtime mit nicht lokal vorhandenen Paketen.

Die vollständige Datenbestandsübersicht mit Speicherorten, Empfängern,
Aufbewahrung und Löschwegen steht in [DATENSCHUTZ.md](../../DATENSCHUTZ.md).

## Programmausführung

Integrierter Kurs- und Schülercode läuft nur nach bestandenem Sandbox-Selbsttest:

- Windows: AppContainer und Job Object;
- Linux: Bubblewrap, für grafische Starts zusätzlich Wayland;
- macOS: dynamisches Seatbelt-Profil.

Netzwerk, fremde Hostdateien, Prozessanzahl, Laufzeit, CPU, Speicher, Ausgabe und
Schreibvolumen werden nach Plattform begrenzt. Keine Betriebssystem-Sandbox ist
ein absoluter Schutz gegen unbekannte Schwachstellen.

Externe IDEs laufen außerhalb dieser Begrenzung. Kurse sollten deshalb nur aus
nachvollziehbaren Quellen stammen. Das technische Bedrohungsmodell und der
Meldeweg stehen in [SECURITY.md](../../SECURITY.md).

## Empfohlener Schulbetrieb

- getrennte Betriebssystemkonten verwenden, solange lokale in:si-Profile fehlen;
- Kursordner nur über von der Schule freigegebene Speicherorte synchronisieren;
- Exporte vor der Weitergabe auf Namen, Quellcode und Testergebnisse prüfen;
- private Lehrkraftschlüssel getrennt von Kursdateien aufbewahren;
- Desktop-Pakete und Kursarchive nur aus dokumentierten Quellen beziehen;
- Backups und Löschfristen organisatorisch festlegen.
