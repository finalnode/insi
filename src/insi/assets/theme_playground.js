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
