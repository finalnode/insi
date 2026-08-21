# Drittanbieterhinweise

in:si selbst steht unter `AGPL-3.0-or-later`. Die nachfolgend genannten
Drittanbieterbestandteile werden dadurch nicht neu lizenziert; für sie gelten
weiterhin die jeweils angegebenen Originalbedingungen. Weitere Hinweise zum
Lizenzumfang stehen in `LICENSING.md`.

## Python-Laufzeitabhängigkeiten

Die Desktop-Builds übernehmen die Paketmetadaten einschließlich vorhandener
Lizenzdateien rekursiv in die Distribution. Dazu gehören insbesondere PyKIM
(MIT), NiceGUI (MIT), pywebview (BSD-3-Clause), Pyxel (MIT), certifi (MPL-2.0),
cryptography (Apache-2.0 oder BSD-3-Clause), packaging (Apache-2.0 oder
BSD-2-Clause), PyYAML (MIT) und Send2Trash (BSD).

Die tatsächlich installierte transitive Laufzeitkette lässt sich in der
jeweiligen Buildumgebung reproduzierbar prüfen mit:

```bash
python tools/audit_runtime_licenses.py --strict
```

Der Audit wertet standardisierte Lizenzangaben und
OSI-Lizenzklassifikationen aus und bricht im strikten Modus bei unbekannten
Angaben ab. Plattformpakete wie pythonnet unter Windows, PyObjC unter macOS
oder PyGObject unter Linux bleiben unter ihren eigenen Lizenzbedingungen.

## TOAST UI Editor 3.2.2

in:si bündelt TOAST UI Editor 3.2.2 von NHN Cloud für die vollständig lokale
Markdownbearbeitung. Das Projekt steht unter der MIT-Lizenz. Der vollständige
Lizenztext wird zusammen mit den gebündelten Dateien unter
`src/insi/vendor/toastui_editor/LICENSE.txt` ausgeliefert.

Das offizielle Browser-Bundle enthält DOMPurify 2.3.3, veröffentlicht wahlweise
unter Apache License 2.0 oder Mozilla Public License 2.0, sowie die unter
MIT-Lizenzen veröffentlichten ProseMirror-Bausteine und ihre kleinen
Laufzeitabhängigkeiten. Die Copyright- und Lizenzköpfe des offiziellen Bundles
bleiben unverändert erhalten. Die vollständigen DOMPurify- und
Apache-2.0-Lizenztexte liegen direkt neben dem Bundle.

Projekt: https://github.com/nhn/tui.editor

Bezogene Originaldatei:
`https://uicdn.toast.com/editor/3.2.2/toastui-editor-all.min.js`

SHA-256 des JavaScript-Bundles:
`f50e1b7c0fc4e5d9a1ccd0d8be78cb3a950ccb3bf676fbf1627810c76aeaedd8`

## EasyMDE

EasyMDE wurde als Alternative geprüft, wird aber nicht mit in:si ausgeliefert.
Auch EasyMDE steht unter der MIT-Lizenz. Für die Entscheidung zugunsten von
TOAST UI waren der echte WYSIWYG-Modus und der Wechsel zwischen visueller und
direkter Markdownbearbeitung ausschlaggebend.
