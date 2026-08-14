"""OSZ-KIM-Theme und Browserverhalten des lokalen Lernstudios."""


def configure_theme(ui) -> None:
    ui.colors(primary="#f36b2b", secondary="#9b9da0", accent="#5f6164")
    ui.add_body_html(r"""
        <script>
            if (!window.pykimParsonsPointerReady) {
                window.pykimParsonsPointerReady = true;
                let drag = null;

                const moveParsons = event => {
                    if (!drag || event.pointerId !== drag.pointerId) return;
                    event.preventDefault();
                    drag.card.style.top = `${event.clientY - drag.offsetY}px`;
                    const cards = [...drag.list.querySelectorAll(
                        ':scope > .pykim-parsons-block'
                    )];
                    const successor = cards.find(card => {
                        const bounds = card.getBoundingClientRect();
                        return event.clientY < bounds.top + bounds.height / 2;
                    });
                    drag.list.insertBefore(drag.placeholder, successor || null);
                };

                const stopParsons = event => {
                    if (!drag || (event.pointerId !== undefined &&
                        event.pointerId !== drag.pointerId)) return;
                    const {card, list, placeholder} = drag;
                    list.insertBefore(card, placeholder);
                    placeholder.remove();
                    card.removeAttribute('style');
                    card.classList.remove('pykim-parsons-dragging');
                    card.removeAttribute('aria-grabbed');
                    drag = null;
                };

                document.addEventListener('pointerdown', event => {
                    const card = event.target.closest('.pykim-parsons-block');
                    if (!card || event.target.closest('button') || event.button !== 0) return;
                    const list = card.closest('.pykim-parsons-list');
                    if (!list) return;
                    event.preventDefault();
                    const bounds = card.getBoundingClientRect();
                    const placeholder = document.createElement('div');
                    placeholder.className = 'pykim-parsons-placeholder';
                    placeholder.style.height = `${bounds.height}px`;
                    list.insertBefore(placeholder, card);
                    document.body.appendChild(card);
                    Object.assign(card.style, {
                        position: 'fixed',
                        zIndex: '5000',
                        left: `${bounds.left}px`,
                        top: `${bounds.top}px`,
                        width: `${bounds.width}px`,
                        margin: '0',
                        pointerEvents: 'none',
                    });
                    card.classList.add('pykim-parsons-dragging');
                    card.setAttribute('aria-grabbed', 'true');
                    drag = {
                        card,
                        list,
                        placeholder,
                        pointerId: event.pointerId,
                        offsetY: event.clientY - bounds.top,
                    };
                }, {passive: false});
                window.addEventListener('pointermove', moveParsons, {passive: false});
                window.addEventListener('pointerup', stopParsons);
                window.addEventListener('pointercancel', stopParsons);
                window.addEventListener('blur', stopParsons);
            }
            window.pykimMoveParsons = function(button, direction) {
                const card = button.closest('.pykim-parsons-block');
                const sibling = direction < 0
                    ? card.previousElementSibling : card.nextElementSibling;
                if (!sibling) return;
                if (direction < 0) card.parentElement.insertBefore(card, sibling);
                else card.parentElement.insertBefore(sibling, card);
            };
        </script>
    """)
    ui.add_head_html(r"""
        <style>
            .pykim-skip-link {
                position: fixed; left: 1rem; top: -5rem; z-index: 9999;
                padding: .65rem 1rem; border-radius: .35rem;
                background: #262626; color: white;
            }
            .pykim-skip-link:focus { top: 1rem; }
            :focus-visible {
                outline: 3px solid #1f6feb !important;
                outline-offset: 3px !important;
            }
            .pykim-header {
                display: flex;
                flex-direction: column;
                align-items: stretch;
                padding: 0 !important;
                background: white !important;
                color: #262626 !important;
                box-shadow: 0 2px 7px rgba(38, 38, 38, .14);
            }
            .pykim-header-top {
                min-height: 3.25rem;
                padding: .45rem 1rem;
                margin: 0;
                background: #f36b2b;
                color: white;
            }
            .insi-header-logo {
                flex: 0 0 auto;
                width: 2.35rem;
                height: 2.35rem;
                border-radius: .55rem;
                filter: drop-shadow(0 1px 2px rgba(38, 38, 38, .18));
            }
            .insi-selection-logo {
                flex: 0 0 auto;
                width: 3rem;
                height: 3rem;
                border-radius: .7rem;
                filter: drop-shadow(0 2px 4px rgba(38, 38, 38, .16));
            }
            .insi-course-title {
                display: flex;
                align-items: center;
                min-width: 0;
                margin-left: .65rem;
                overflow: hidden;
                color: rgba(255, 255, 255, .92);
                font-size: 1rem;
                font-weight: 500;
                line-height: 1.2;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .pykim-main-navigation {
                min-height: 3rem;
                background: white;
                color: #4f5154;
                border-bottom: 1px solid #d7d8d9;
            }
            .pykim-main-navigation .q-tab--active {
                color: #d95316;
                font-weight: 700;
            }
            #pykim-main { scroll-margin-top: 7rem; }
            .pykim-footer {
                position: fixed;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 2000;
                min-height: 1.8rem;
                padding: .25rem 1rem;
                color: #f4f4f4;
                background: #4f5154;
                border-top: 2px solid #f36b2b;
                box-shadow: 0 -2px 7px rgba(38, 38, 38, .14);
            }
            .pykim-footer-claim {
                color: #f4f4f4;
                font-size: .72rem;
                letter-spacing: .01em;
            }
            .pykim-footer-version {
                color: #d7d8d9;
                font-size: .7rem;
            }
            .pykim-footer-link {
                color: white !important;
                font-size: .72rem;
                font-weight: 600;
                text-decoration: underline;
                text-underline-offset: .2rem;
            }
            .pykim-footer-link:hover { color: #ffc3a6 !important; }
            .insi-footer-course-path {
                min-width: 0;
                max-width: min(46vw, 38rem);
                color: #f4f4f4 !important;
                font-size: .7rem;
                font-weight: 400;
                text-transform: none;
            }
            .insi-footer-course-path .q-btn__content {
                min-width: 0;
                flex-wrap: nowrap;
            }
            .insi-footer-course-path .q-btn__content .block {
                min-width: 0;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .pykim-parsons-list {
                display: grid; gap: .75rem; width: 100%; max-width: 100%;
                box-sizing: border-box;
            }
            .pykim-parsons-block {
                display: flex; align-items: stretch; gap: .5rem;
                width: 100%; min-width: 0; box-sizing: border-box;
                border: 1px solid #c9cacc; border-left: 5px solid #f36b2b;
                border-radius: .45rem; background: #f7f7f6; cursor: grab;
                box-shadow: 0 1px 3px rgba(38,38,38,.12);
                touch-action: none; user-select: none;
            }
            .pykim-parsons-block:active,
            .pykim-parsons-dragging {
                cursor: grabbing; opacity: .82; transform: scale(.995);
                box-shadow: 0 5px 14px rgba(38,38,38,.2);
            }
            .pykim-parsons-placeholder {
                width: 100%; box-sizing: border-box;
                border: 2px dashed #f36b2b; border-radius: .45rem;
                background: rgba(243, 107, 43, .08);
            }
            .pykim-parsons-block pre {
                flex: 1 1 auto; min-width: 0; margin: 0; padding: .85rem 1rem;
                overflow-x: auto; white-space: pre-wrap;
                font: .9rem ui-monospace, SFMono-Regular, Menlo, monospace;
            }
            .pykim-parsons-controls { display: flex; align-items: center; gap: .2rem; padding: .35rem; }
            .pykim-parsons-controls button {
                border: 1px solid #b8b9bb; border-radius: .3rem; background: white;
                min-width: 2.2rem; min-height: 2.2rem; cursor: pointer;
            }
            .pykim-course-opening {
                position: relative;
                overflow: hidden;
                background: white !important;
                border-color: #f36b2b !important;
                transition: background-color .2s ease, border-color .2s ease;
            }
            .pykim-course-opening > * { position: relative; z-index: 2; }
            .pykim-course-sync-icon {
                animation: pykim-course-spin 1.1s linear infinite;
            }
            .pykim-course-sync-dots::after {
                content: '';
                display: inline-block;
                width: 1.4em;
                text-align: left;
                animation: pykim-course-dots 1.2s steps(4, end) infinite;
            }
            .pykim-course-pixel-field {
                position: absolute !important;
                inset: 0;
                z-index: 1 !important;
                opacity: 0;
                pointer-events: none;
                transition: opacity .2s ease;
            }
            .pykim-course-opening .pykim-course-pixel-field { opacity: .86; }
            .pykim-course-pixel-field span {
                position: absolute;
                left: var(--pixel-x);
                top: var(--pixel-y);
                width: var(--pixel-size);
                height: var(--pixel-size);
                border-radius: .14rem;
                background: rgba(255, 255, 255, .5);
                animation-name: pykim-pixel-field-float;
                animation-duration: var(--pixel-duration);
                animation-delay: var(--pixel-delay);
                animation-timing-function: ease-in-out;
                animation-iteration-count: infinite;
                animation-direction: alternate;
                will-change: transform, opacity, background-color;
            }
            @keyframes pykim-course-spin {
                to { transform: rotate(360deg); }
            }
            @keyframes pykim-course-dots {
                0% { content: ''; }
                25% { content: '·'; }
                50% { content: '··'; }
                75%, 100% { content: '···'; }
            }
            @keyframes pykim-pixel-field-float {
                0% {
                    background: rgba(255, 255, 255, .34);
                    transform: translate3d(-.25rem, .18rem, 0) scale(.72);
                    opacity: .22;
                }
                38% {
                    background: var(--pixel-color-a);
                    transform: translate3d(.12rem, -.2rem, 0) scale(.94);
                    opacity: .76;
                }
                72% {
                    background: var(--pixel-color-b);
                    transform: translate3d(.42rem, -.08rem, 0) scale(1.08);
                    opacity: .9;
                    box-shadow: 0 0 .38rem rgba(33, 186, 69, .3);
                }
                100% {
                    background: rgba(255, 255, 255, .48);
                    transform: translate3d(.68rem, -.3rem, 0) scale(.78);
                    opacity: .3;
                    box-shadow: none;
                }
            }
            .q-page-container { padding-bottom: 2.4rem; }
            .pykim-project-workspace {
                min-height: 48rem;
                border: 1px solid #d7d8d9;
                border-radius: .5rem;
                overflow: hidden;
                background: white;
            }
            .pykim-project-workspace .q-splitter__before {
                background: #f5f5f4;
                border-right: 1px solid #d7d8d9;
            }
            .pykim-project-selector .q-tab {
                justify-content: flex-start;
                min-height: 2.8rem;
                padding: .35rem .75rem;
                text-align: left;
            }
            .pykim-project-selector .q-tab--active {
                color: #d95316;
                background: #fff0e8;
                font-weight: 700;
            }
            pre.pykim-copy-ready {
                position: relative;
                padding: 1rem 1.1rem !important;
                background: #f5f5f4 !important;
                border: 1px solid #d7d8d9;
                border-left: 4px solid #f36b2b;
                border-radius: .45rem;
                box-shadow: 0 1px 2px rgba(40, 40, 40, .06);
            }
            pre.pykim-copy-ready.pykim-has-actions {
                padding-right: 12rem !important;
            }
            pre.pykim-copy-ready code {
                background: transparent !important;
            }
            .pykim-copy-button {
                position: absolute; top: .55rem; right: .55rem; z-index: 2;
                border: 0; border-radius: .4rem; padding: .35rem .65rem;
                background: #686a6d; color: white; cursor: pointer;
                font: 500 .8rem system-ui, sans-serif;
            }
            .pykim-copy-button:hover { background: #f36b2b; }
            .pykim-code-run-button {
                position: absolute; top: .55rem; right: 5.7rem; z-index: 2;
                border: 0; border-radius: .4rem; padding: .35rem .65rem;
                background: #f36b2b; color: white; cursor: pointer;
                font: 500 .8rem system-ui, sans-serif;
            }
            .pykim-code-run-button:hover { background: #cf4f18; }
            .pykim-code-run-button:disabled { opacity: .6; cursor: wait; }
            .pykim-code-output {
                margin: -.35rem 0 1rem;
                padding: .65rem .8rem;
                border: 1px solid #d7d8d9;
                border-top: 0;
                border-radius: 0 0 .4rem .4rem;
                background: #272822;
                color: #f5f5f5;
                white-space: pre-wrap;
                font: .85rem/1.45 ui-monospace, SFMono-Regular, Consolas, monospace;
            }
            .pykim-code-options { display: none !important; }
            .pykim-playground-editor {
                position: relative;
                width: 100%;
                min-height: 15rem;
                overflow: hidden;
                border: 1px solid #cfd0d1; border-left: 4px solid #f36b2b;
                border-radius: .45rem; background: #f5f5f4;
            }
            .pykim-playground-editor textarea,
            .pykim-playground-editor pre {
                box-sizing: border-box;
                width: 100%; min-height: 15rem; margin: 0; padding: 1rem;
                border: 0; background: transparent;
                tab-size: 4;
                white-space: pre;
                overflow: auto;
                font: 14px/1.5 ui-monospace, SFMono-Regular, Consolas, monospace;
            }
            .pykim-playground-editor pre {
                position: absolute; inset: 0;
                pointer-events: none;
                color: #262626;
            }
            .pykim-playground-editor pre code {
                font: inherit;
                white-space: inherit;
            }
            .pykim-playground-editor textarea {
                position: relative;
                resize: vertical;
                color: transparent;
                caret-color: #262626;
                -webkit-text-fill-color: transparent;
            }
            .pykim-playground-editor textarea::selection {
                background: rgba(31, 111, 235, .25);
            }
            .pykim-python-keyword { color: #1565c0; font-weight: 650; }
            .pykim-python-builtin { color: #7b1fa2; }
            .pykim-python-string { color: #c62828; }
            .pykim-python-comment { color: #397b7b; font-style: italic; }
            .pykim-python-number { color: #8a4f08; }
            .pykim-playground-editor:focus-within {
                outline: 3px solid #1f6feb;
                outline-offset: 2px;
            }
            .pykim-run-button, .pykim-clear-button {
                border: 0; border-radius: .4rem; padding: .55rem .9rem;
                color: white; cursor: pointer; margin-right: .4rem;
            }
            .pykim-run-button { background: #f36b2b; }
            .pykim-clear-button { background: #686a6d; }
            .pykim-test-result {
                border: 1px solid #d7d8d9;
                border-left-width: 5px;
                border-radius: .45rem;
                box-shadow: none;
            }
            .pykim-test-passed {
                border-left-color: #2e7d32;
                background: #f2f8f3;
            }
            .pykim-test-failed {
                border-left-color: #d14b34;
                background: #fff5f2;
            }
            .pykim-test-hint {
                background: #fff4eb;
                border-left: 3px solid #f36b2b;
                border-radius: .3rem;
                padding: .55rem .75rem;
            }
            .pykim-script-layout {
                display: grid;
                grid-template-columns: 16rem minmax(0, 1fr);
                gap: 1.25rem;
                margin-top: 1rem;
            }
            .pykim-script-menu {
                position: sticky;
                top: 5rem;
                width: 16rem;
                max-height: calc(100vh - 7rem);
                overflow-y: auto;
                border: 1px solid #d7d8d9;
                border-left: 4px solid #f36b2b;
                background: #f8f8f7;
                padding: .8rem;
            }
            .pykim-script-menu-button {
                min-height: 2.4rem;
                padding: .35rem .5rem;
                border-radius: .35rem;
            }
            .pykim-script-menu-button .q-btn__content {
                width: 100%;
                justify-content: flex-start !important;
                text-align: left !important;
                white-space: normal;
                line-height: 1.25;
                font-size: .88rem;
                font-weight: 500;
            }
            .pykim-script-page {
                border: 1px solid #e0e0df;
                border-radius: .5rem;
                padding: 1.5rem;
                background: white;
            }
            .pykim-chapter-markdown {
                color: #262626;
                font-size: 1rem;
                line-height: 1.65;
                max-width: 58rem;
            }
            .pykim-chapter-markdown h1 {
                font-size: 2rem !important;
                line-height: 1.2 !important;
                font-weight: 700 !important;
                margin: 1.25rem 0 1rem !important;
                letter-spacing: -.02em;
            }
            .pykim-chapter-markdown h2 {
                font-size: 1.4rem !important;
                line-height: 1.3 !important;
                font-weight: 700 !important;
                margin: 1.6rem 0 .65rem !important;
            }
            .pykim-chapter-markdown h3 {
                font-size: 1.15rem !important;
                font-weight: 700 !important;
                margin: 1.3rem 0 .5rem !important;
            }
            .pykim-chapter-markdown p {
                margin: .65rem 0;
            }
            .pykim-chapter-markdown table {
                display: block;
                width: max-content;
                max-width: 100%;
                overflow-x: auto;
                margin: 1rem 0;
                border-collapse: collapse;
            }
            .pykim-chapter-markdown th,
            .pykim-chapter-markdown td {
                padding: .5rem .75rem;
                border: 1px solid #d7d8d9;
                text-align: left;
            }
            .pykim-chapter-markdown th { background: #f2f2f1; }
            @media (max-width: 800px) {
                .pykim-course-path { display: none; }
                .pykim-header-top { min-height: 3rem; }
                .pykim-main-navigation .q-tab { min-width: max-content; }
                .pykim-script-layout { grid-template-columns: 1fr; }
                .pykim-script-menu {
                    position: static;
                    width: 100%;
                    max-height: none;
                }
                .pykim-script-page { padding: 1rem; }
                .pykim-chapter-markdown h1 { font-size: 1.65rem !important; }
            }
            @media (prefers-reduced-motion: reduce) {
                *, *::before, *::after {
                    scroll-behavior: auto !important;
                    animation-duration: .01ms !important;
                    animation-iteration-count: 1 !important;
                    transition-duration: .01ms !important;
                }
            }
        </style>
        <script>
            let pyKIMBrowserWorker = null;
            const createPyKIMBrowserWorker = () => {
                const workerSource = `
                    import { loadPyodide } from 'https://cdn.jsdelivr.net/pyodide/v314.0.2/full/pyodide.mjs';
                    let runtime = null;
                    self.onmessage = async event => {
                        try {
                            if (!runtime) {
                                self.postMessage({type: 'status', text: 'Python wird im Hintergrund geladen …'});
                                runtime = await loadPyodide();
                                self.postMessage({type: 'status', text: 'Python ist bereit.'});
                            }
                            let output = '';
                            runtime.setStdout({batched: value => output += value + '\\n'});
                            runtime.setStderr({batched: value => output += value + '\\n'});
                            const result = await runtime.runPythonAsync(event.data.code);
                            if (result !== undefined) output += String(result);
                            self.postMessage({type: 'result', text: output || 'Programm ohne Ausgabe beendet.'});
                        } catch (error) {
                            self.postMessage({type: 'error', text: String(error)});
                        }
                    };
                `;
                const url = URL.createObjectURL(new Blob([workerSource], {type: 'text/javascript'}));
                const worker = new Worker(url, {type: 'module'});
                URL.revokeObjectURL(url);
                worker.onmessage = event => {
                    const status = document.getElementById('pyodide-status');
                    const output = document.getElementById('pyodide-output');
                    if (event.data.type === 'status' && status) {
                        status.innerHTML = `<strong>${event.data.text}</strong>`;
                    } else if (event.data.type === 'result' && output) {
                        output.textContent = event.data.text;
                    } else if (event.data.type === 'error' && output) {
                        output.textContent = event.data.text;
                    }
                };
                worker.onerror = event => {
                    const status = document.getElementById('pyodide-status');
                    const output = document.getElementById('pyodide-output');
                    if (status) status.textContent = 'Python im Browser konnte nicht geladen werden.';
                    if (output) output.textContent = event.message || 'Unbekannter Worker-Fehler.';
                    pyKIMBrowserWorker = null;
                };
                return worker;
            };
            window.resetPyKIMBrowserExample = () => {
                const editor = document.getElementById('pyodide-code');
                const output = document.getElementById('pyodide-output');
                if (editor) editor.value = 'for zahl in range(1, 6):\n    print(zahl, zahl * zahl)';
                window.syncPyKIMBrowserEditor();
                if (output) output.textContent = 'Bereit.';
            };
            const escapePyKIMCode = value => value
                .replaceAll('&', '&amp;')
                .replaceAll('<', '&lt;')
                .replaceAll('>', '&gt;');
            window.highlightPyKIMPython = source => {
                const keywords = new Set([
                    'and', 'as', 'assert', 'async', 'await', 'break', 'case',
                    'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
                    'False', 'finally', 'for', 'from', 'global', 'if', 'import',
                    'in', 'is', 'lambda', 'match', 'None', 'nonlocal', 'not',
                    'or', 'pass', 'raise', 'return', 'True', 'try', 'while',
                    'with', 'yield'
                ]);
                const builtins = new Set([
                    'bool', 'dict', 'enumerate', 'float', 'input', 'int', 'len',
                    'list', 'max', 'min', 'print', 'range', 'set', 'str', 'sum',
                    'tuple', 'type', 'zip'
                ]);
                let result = '';
                let index = 0;
                const span = (kind, value) =>
                    `<span class="pykim-python-${kind}">${escapePyKIMCode(value)}</span>`;
                while (index < source.length) {
                    const character = source[index];
                    if (character === '#') {
                        let end = source.indexOf('\n', index);
                        if (end < 0) end = source.length;
                        result += span('comment', source.slice(index, end));
                        index = end;
                    } else if (character === '"' || character === "'") {
                        const quote = character;
                        const triple = source.slice(index, index + 3) === quote.repeat(3);
                        let end = index + (triple ? 3 : 1);
                        while (end < source.length) {
                            if (source[end] === '\\') {
                                end += 2;
                            } else if (triple && source.slice(end, end + 3) === quote.repeat(3)) {
                                end += 3;
                                break;
                            } else if (!triple && source[end] === quote) {
                                end += 1;
                                break;
                            } else {
                                end += 1;
                            }
                        }
                        result += span('string', source.slice(index, end));
                        index = end;
                    } else if (/[A-Za-z_]/.test(character)) {
                        let end = index + 1;
                        while (end < source.length && /[A-Za-z0-9_]/.test(source[end])) end += 1;
                        const word = source.slice(index, end);
                        result += keywords.has(word) ? span('keyword', word)
                            : builtins.has(word) ? span('builtin', word)
                            : escapePyKIMCode(word);
                        index = end;
                    } else if (/\d/.test(character)) {
                        let end = index + 1;
                        while (end < source.length && /[\d._]/.test(source[end])) end += 1;
                        result += span('number', source.slice(index, end));
                        index = end;
                    } else {
                        result += escapePyKIMCode(character);
                        index += 1;
                    }
                }
                return result + (source.endsWith('\n') ? ' ' : '');
            };
            window.syncPyKIMBrowserEditor = () => {
                const editor = document.getElementById('pyodide-code');
                const code = document.querySelector('#pyodide-highlight code');
                if (!editor || !code) return;
                code.innerHTML = window.highlightPyKIMPython(editor.value);
                window.syncPyKIMBrowserEditorScroll();
            };
            window.syncPyKIMBrowserEditorScroll = () => {
                const editor = document.getElementById('pyodide-code');
                const highlight = document.getElementById('pyodide-highlight');
                if (!editor || !highlight) return;
                highlight.scrollTop = editor.scrollTop;
                highlight.scrollLeft = editor.scrollLeft;
            };
            window.handlePyKIMBrowserEditorKey = event => {
                if (event.key !== 'Tab') return true;
                event.preventDefault();
                const editor = event.currentTarget;
                const start = editor.selectionStart;
                const end = editor.selectionEnd;
                const lineStart = editor.value.lastIndexOf('\n', start - 1) + 1;
                if (!event.shiftKey && start === end) {
                    editor.setRangeText('    ', start, end, 'end');
                } else {
                    const selectedEnd = editor.value.indexOf('\n', end);
                    const blockEnd = selectedEnd < 0 ? editor.value.length : selectedEnd;
                    const block = editor.value.slice(lineStart, blockEnd);
                    const lines = block.split('\n');
                    const changed = event.shiftKey
                        ? lines.map(line => line.startsWith('    ') ? line.slice(4)
                            : line.startsWith('\t') ? line.slice(1) : line.replace(/^ {1,3}/, ''))
                        : lines.map(line => `    ${line}`);
                    editor.setRangeText(changed.join('\n'), lineStart, blockEnd, 'select');
                }
                window.syncPyKIMBrowserEditor();
                return false;
            };
            const initializePyKIMBrowserEditor = () => {
                const editor = document.getElementById('pyodide-code');
                if (!editor || editor.dataset.highlightReady) return;
                editor.dataset.highlightReady = 'true';
                window.syncPyKIMBrowserEditor();
            };
            new MutationObserver(initializePyKIMBrowserEditor).observe(
                document.documentElement, {childList: true, subtree: true}
            );
            window.runPyKIMPython = async () => {
                const output = document.getElementById('pyodide-output');
                const code = document.getElementById('pyodide-code').value;
                const unsupportedImport = /^\s*(?:from|import)\s+(pykim|pyxel)\b/m.exec(code);
                if (unsupportedImport) {
                    const packageName = unsupportedImport[1] === 'pykim' ? 'PyKIM' : 'Pyxel';
                    output.textContent = `${packageName} läuft nicht in dieser Browser-Spielwiese. `
                        + 'Öffne den Code als Aufgabe oder Projekt und starte ihn mit der lokalen Runtime.';
                    return;
                }
                output.textContent = 'Wird ausgeführt …';
                if (!pyKIMBrowserWorker) pyKIMBrowserWorker = createPyKIMBrowserWorker();
                pyKIMBrowserWorker.postMessage({code});
            };
            window.stopPyKIMBrowserPython = () => {
                if (pyKIMBrowserWorker) {
                    pyKIMBrowserWorker.terminate();
                    pyKIMBrowserWorker = null;
                }
                const status = document.getElementById('pyodide-status');
                const output = document.getElementById('pyodide-output');
                if (status) status.innerHTML = '<strong>Python wird erst beim Ausführen geladen.</strong>';
                if (output) output.textContent = 'Ausführung gestoppt.';
            };
        </script>
        <script>
            (() => {
                const addCopyButtons = root => {
                    root.querySelectorAll('pre:not(.pykim-copy-ready)').forEach(pre => {
                        // Parsons-Blöcke sind selbst interaktive Karten. Das allgemeine
                        // Codeblock-Styling würde dort einen zweiten Rahmen und einen
                        // sinnlosen Kopieren-Button ergänzen.
                        if (pre.closest('.pykim-parsons-block, .pykim-no-code-actions')) return;
                        pre.classList.add('pykim-copy-ready');
                        const pythonCode = pre.querySelector('code');
                        const inScript = Boolean(pre.closest('.pykim-chapter-markdown'));
                        const codeContainer = pre.parentElement?.classList.contains('codehilite')
                            ? pre.parentElement
                            : pre;
                        const markerCandidate = codeContainer.previousElementSibling;
                        const marker = inScript && markerCandidate?.matches(
                            '.pykim-code-options'
                        ) ? markerCandidate : null;
                        const buttons = inScript
                            ? (marker?.dataset.buttons || '').split(',').filter(Boolean)
                            : ['copy'];
                        if (buttons.length) pre.classList.add('pykim-has-actions');

                        if (buttons.includes('copy')) {
                            const button = document.createElement('button');
                            button.className = 'pykim-copy-button';
                            button.type = 'button';
                            button.textContent = 'Kopieren';
                            button.setAttribute('aria-label', 'Code in die Zwischenablage kopieren');
                            button.addEventListener('click', async () => {
                                const text = (pythonCode || pre).innerText;
                                if (navigator.clipboard?.writeText) {
                                    await navigator.clipboard.writeText(text);
                                } else {
                                    const area = document.createElement('textarea');
                                    area.value = text;
                                    area.style.position = 'fixed';
                                    area.style.opacity = '0';
                                    document.body.appendChild(area);
                                    area.select();
                                    document.execCommand('copy');
                                    area.remove();
                                }
                                button.textContent = 'Kopiert ✓';
                                setTimeout(() => button.textContent = 'Kopieren', 1500);
                            });
                            pre.appendChild(button);
                        }

                        if (buttons.includes('run') && pythonCode) {
                            const runButton = document.createElement('button');
                            runButton.className = 'pykim-code-run-button';
                            runButton.type = 'button';
                            runButton.textContent = '▶ Ausführen';
                            runButton.setAttribute('aria-label', 'Python-Code ausführen');
                            runButton.addEventListener('click', async () => {
                                runButton.disabled = true;
                                runButton.textContent = 'Läuft …';
                                let output = pre.nextElementSibling;
                                if (!output?.classList.contains('pykim-code-output')) {
                                    output = document.createElement('div');
                                    output.className = 'pykim-code-output';
                                    pre.insertAdjacentElement('afterend', output);
                                }
                                output.textContent = 'Beispiel wird ausgeführt …';
                                try {
                                    const response = await fetch('/api/script/run', {
                                        method: 'POST',
                                        headers: {'Content-Type': 'application/json'},
                                        body: JSON.stringify({source: pythonCode.innerText}),
                                    });
                                    const started = await response.json();
                                    if (!response.ok) throw new Error(started.detail || 'Ausführung abgelehnt');

                                    let result = null;
                                    while (true) {
                                        const statusResponse = await fetch(
                                            `/api/script/status/${started.job_id}`
                                        );
                                        result = await statusResponse.json();
                                        if (!statusResponse.ok) {
                                            throw new Error(result.detail || 'Status nicht verfügbar');
                                        }
                                        const text = [result.stdout, result.stderr]
                                            .filter(Boolean).join('\n').trim();
                                        output.textContent = text || (
                                            result.running
                                                ? 'Programm läuft …'
                                                : `Programm ohne Ausgabe beendet (Code ${result.returncode}).`
                                        );
                                        output.style.borderLeft = `4px solid ${
                                            result.running ? '#f36b2b' :
                                            result.returncode === 0 ? '#2e7d32' : '#d14b34'
                                        }`;
                                        if (!result.running) break;
                                        await new Promise(resolve => setTimeout(resolve, 150));
                                    }
                                } catch (error) {
                                    output.textContent = `Ausführen fehlgeschlagen: ${error}`;
                                    output.style.borderLeft = '4px solid #d14b34';
                                } finally {
                                    runButton.disabled = false;
                                    runButton.textContent = '▶ Ausführen';
                                }
                            });
                            pre.appendChild(runButton);
                        }
                    });
                };
                document.addEventListener('DOMContentLoaded', () => {
                    addCopyButtons(document);
                    new MutationObserver(() => addCopyButtons(document)).observe(
                        document.body, {childList: true, subtree: true}
                    );
                });
            })();
        </script>
        <script>
            window.pykimHasUnsavedChanges = false;
            window.addEventListener('beforeunload', event => {
                if (window.pykimHasUnsavedChanges) {
                    event.preventDefault();
                    event.returnValue = '';
                }
            });
        </script>
    """)


__all__ = ["configure_theme"]
