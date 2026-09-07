# in:si 0.7.2 – Release Notes (Testkandidat)

## Testkandidat 0.7.2

Unter Windows enthält der portable App-Ordner nur noch eine `insi.exe`. Dieselbe
Datei startet ohne internen Schalter die Desktop-App und führt mit dem internen
Runner-Schalter kontrollierte Schüler-, Sandbox- und Prüfläufe aus. Eine
verwechselbare `insi-python.exe` liegt nicht mehr daneben.

Der AppContainer erhält eine explizite Lesefreigabe für diese EXE. Kurzzeitige
Fremdsperren beim anschließenden Entfernen des Probeordners werden begrenzt
wiederholt und nicht mehr mit einer fehlgeschlagenen Isolation verwechselt. Die
eigentliche Datei- und Netzwerkprüfung bleibt unverändert fail-closed.

Ein realer iServ-Test zeigte außerdem, dass ein direkter Start aus einer
UNC-Ablage mehrere sichtbare `icacls.exe`-Prozesse, langsames Laden und einen
45-Sekunden-Timeout auslöste. Der Kandidat cached den direkt im Netz gestarteten
Build nun inhaltsgebunden im lokalen Benutzerbereich und setzt den Start
automatisch fort. AppContainer-Läufe spiegeln ausschließlich die freigegebenen
Netzwerkpfade lokal; erlaubte Projektänderungen werden nach Prozessende mit
Konflikterkennung zurückgeschrieben. Der Lernprozess selbst behält seine
Netzwerksperre. Die ACL-Helfer laufen fensterlos.

Die vorherige automatisierte Desktopmatrix war erfolgreich. Vor einer
Veröffentlichung müssen der korrigierte Build und die [reale Abnahme für
direkten iServ-/UNC-, lokalen und USB-Start](windows-test-0.7.2.md) auf den
betroffenen Schulrechnern erneut erfolgreich sein.

## Hotfix 0.7.1

Unter Windows starten Kurse nun auch aus Benutzerordnern wie
`C:\Users\...`, ohne dass der Pfad im Footer irrtümlich als Python-Literal
ausgewertet wird und einen HTTP-500-Fehler auslöst.

in:si 0.7 legt die technische Grundlage für kontrollierte Programmläufe,
fachmodulneutrale Trainer und einen lokalen visuellen Kurseditor. Die Version
bleibt ausdrücklich Alpha: Daten- und Kursformate erhalten erst mit 1.0 eine
langfristige Stabilitätszusage.

## Wichtigste Änderungen

- Fail-closed Sandbox-Runner für Windows, Linux und macOS mit echten
  Selbsttests und Ressourcenbegrenzung.
- Neutraler Vertrag `insi-trainer-v1`; PyKIM ist der erste Adapter, freie
  Antworten, Zuordnungen und Parsons-Puzzles liegen im Core.
- Offline gebündelter TOAST UI Editor mit WYSIWYG-/Markdown-Wechsel,
  kursabhängigen Annotationen und kanonischer Validierung.
- Sichere globale, kursweite und projektbezogene Dateiimporte sowie begrenzte
  Projektstände vor integrierten Starts.
- Manuell ausgelöste statt versteckter GitHub-Prüfungen und dokumentierter
  lokaler Datenbestand.
- Deutsche und englische Offline-Dokumentation direkt in der App.
- Lizenzwechsel für in:si auf `AGPL-3.0-or-later`; PyKIM und
  Drittanbieterkomponenten behalten ihre eigenen Lizenzen.

## Sicherheitsmodell

Integrierter Kurs- und Schülercode startet nur, wenn der Plattformadapter einen
Datei- und Netzwerkprobelauf besteht. Ohne funktionsfähige Isolation bleibt der
Start gesperrt; **In IDE öffnen** ist der sichtbare, nicht eingeschränkte
Ausweichweg. Linux benötigt Bubblewrap und für grafische Starts Wayland. macOS
verwendet weiterhin die nicht als stabile öffentliche API zugesagte
Seatbelt-Profilsprache.

## Bekannte Einschränkungen

- Die abschließende manuelle Schulgeräte-Matrix und die visuelle Toolbar-Abnahme
  sind noch nicht vollständig; Details und Ausweichwege stehen in
  `KNOWN_ISSUES.md`.
- Desktop-Pakete sind noch nicht produktionssigniert beziehungsweise
  notarisiert.
- Automatische versionsübergreifende Migration, sichtbare Wiederherstellung und
  Mehrbenutzerprofile folgen in späteren Versionen.

Details stehen in [KNOWN_ISSUES.md](../KNOWN_ISSUES.md), das Sicherheitsmodell
in [SECURITY.md](../SECURITY.md) und die weitere Planung in
[ROADMAP.md](../ROADMAP.md).

---

# in:si 0.7.2 – Draft release notes

## 0.7.2 release candidate

The portable Windows folder now contains a single `insi.exe` which serves as
both the desktop entry point and, with an internal switch, the controlled
Python and sandbox runner. Explicit AppContainer access to this executable and
bounded retries for transient probe-directory cleanup address the two observed
school-device failure paths without weakening the isolation test. The previous
candidate passed the complete automated desktop matrix.

A real iServ test subsequently showed visible `icacls.exe` windows, slow
loading and a 45-second timeout when the package was executed directly from a
UNC share. The corrected candidate caches the build in the local user profile
and continues the network launch automatically. Each AppContainer run mirrors
only the explicitly allowed network paths locally and synchronizes permitted
project changes back with conflict detection, while student code remains
network-isolated. ACL helpers run without a visible console. The corrected
build still requires a fresh desktop matrix and real-device checks from the
affected iServ share, local storage and USB.

## Hotfix 0.7.1

On Windows, courses now open correctly from user directories such as
`C:\Users\...`; the footer no longer interprets the path as a Python literal
and therefore no longer triggers the corresponding HTTP 500 error.

in:si 0.7 establishes the technical foundation for controlled program
execution, subject-neutral trainers and a local visual course editor. This is
still an alpha release; long-term format stability starts with version 1.0.

Highlights include fail-closed sandbox adapters for Windows, Linux and macOS,
the `insi-trainer-v1` contract, an offline WYSIWYG/Markdown editor, controlled
file imports, local project snapshots, explicit network actions, bilingual
offline documentation and the move to `AGPL-3.0-or-later` for in:si itself.

The final real-device matrix and visual toolbar check are not yet complete;
details and workarounds are documented in `KNOWN_ISSUES.md`. Desktop packages
are not yet production-signed or notarized.
