# in:si 0.7.1 – Release Notes

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

# in:si 0.7.1 – Release notes

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
