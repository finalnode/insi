(() => {
    const addCopyButtons = root => {
        root.querySelectorAll('pre:not(.pykim-copy-ready)').forEach(pre => {
            // TOAST/ProseMirror owns and continuously reconciles its
            // editing DOM. Injecting course action buttons there makes
            // ProseMirror remove them and this observer add them again,
            // resulting in an endless mutation loop on WYSIWYG switch.
            if (pre.closest('.toastui-editor-defaultUI, .ProseMirror')) return;
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
