document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    const inputSection = document.getElementById('input-section');
    const progressSection = document.getElementById('progress-section');
    const resultSection = document.getElementById('result-section');
    const logs = document.getElementById('logs');
    const repoUrlInput = document.getElementById('repo-url');
    const taskDescInput = document.getElementById('task-desc');

    startBtn.addEventListener('click', async () => {
        const repoUrl = repoUrlInput.value;
        const task = taskDescInput.value;
        const mode = document.querySelector('.option-card.active').dataset.mode;

        if (!repoUrl || !task) {
            alert('Please provide both a repository URL and a task description.');
            return;
        }

        inputSection.classList.add('hidden');
        progressSection.classList.remove('hidden');
        document.getElementById('current-repo').textContent = repoUrl.split('/').pop();

        executeAgentFlow(repoUrl, task, mode);
    });

    function addLog(text, type = 'agent') {
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
        logs.appendChild(entry);
        logs.scrollTop = logs.scrollHeight;
    }

    async function executeAgentFlow(repoUrl, task, mode) {
        try {
            addLog('Connecting to backend server...', 'system');

            const fetchResponse = await fetch('http://localhost:3001/api/repo/fetch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repoUrl })
            });
            const fetchData = await fetchResponse.json();
            if (!fetchResponse.ok) throw new Error(fetchData.detail);

            addLog(`Workspace Ready: ${fetchData.repo}`, 'success');

            const thinkingLevel = document.getElementById('thinking-level')?.value || 2;
            const prIdParam = fetchData.prId ? `&prId=${fetchData.prId}` : '';
            const streamUrl = `http://localhost:3001/api/agent/stream/${fetchData.sessionId}?task=${encodeURIComponent(task)}&mode=${mode}&thinkingLevel=${thinkingLevel}${prIdParam}`;

            const eventSource = new EventSource(streamUrl);

            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.log) {
                    addLog(data.log, data.type || 'agent');
                }

                if (data.status === 'completed') {
                    eventSource.close();
                    addLog('🏁 Agent process finished.', 'success');
                    setTimeout(() => showResult(data), 500);
                }
            };

            eventSource.onerror = (e) => {
                console.error("Stream Error", e);
                eventSource.close();
            };

        } catch (error) {
            addLog(`Error: ${error.message}`, 'system');
        }
    }

    function formatDiff(diffText) {
        if (!diffText) return 'No changes generated.';
        return diffText.split('\n').map(line => {
            let cls = '';
            if (line.startsWith('+') && !line.startsWith('+++')) cls = 'addition';
            else if (line.startsWith('-') && !line.startsWith('---')) cls = 'removal';
            else if (line.startsWith('---') || line.startsWith('+++')) cls = 'header';
            else if (line.startsWith('@@')) cls = 'info';

            const escapedLine = line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
            return `<span class="diff-line ${cls}">${escapedLine || ' '}</span>`;
        }).join('');
    }

    function showResult(data) {
        progressSection.classList.add('hidden');
        resultSection.classList.remove('hidden');

        // Update title based on task type
        const resultTitle = document.querySelector('#result-section h2');
        if (data.title) {
            resultTitle.textContent = data.title;
        } else if (data.filesTouched === 0 && !data.requiresCodeChanges) {
            resultTitle.textContent = 'Analysis Complete';
        } else if (data.filesTouched === 0) {
            resultTitle.textContent = 'Task Complete';
        } else {
            resultTitle.textContent = 'Refactoring Complete';
        }

        // Hide PR-related UI if not applicable
        const shouldShowPR = data.shouldGeneratePR && data.prDescription;
        const prTab = document.querySelector('[data-tab="pr"]');
        const copyPRBtn = document.getElementById('copy-pr-btn');
        const downloadBtn = document.getElementById('download-patch-btn');

        if (!shouldShowPR) {
            if (prTab) prTab.style.display = 'none';
            if (copyPRBtn) copyPRBtn.style.display = 'none';
            if (downloadBtn && data.filesTouched === 0) downloadBtn.style.display = 'none';
        } else {
            if (prTab) prTab.style.display = '';
            if (copyPRBtn) copyPRBtn.style.display = '';
            if (downloadBtn) downloadBtn.style.display = '';
        }

        setupTabs(data);

        // Auto-select Code Changes tab
        const defaultTab = document.querySelector('[data-tab="diff"]');
        if (defaultTab) defaultTab.click();

        setupCopyButtons(data);
    }

    function setupTabs(data) {
        const tabContent = document.getElementById('tab-content');
        const buttons = document.querySelectorAll('.tab-btn');

        buttons.forEach(btn => {
            btn.onclick = () => {
                buttons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                const tab = btn.dataset.tab;
                if (tab === 'diff') {
                    tabContent.innerHTML = `
                        <div class="diff-viewer">
                            <pre><code id="diff-output">${formatDiff(data.diff)}</code></pre>
                        </div>
                    `;
                } else if (tab === 'plan') {
                    tabContent.innerHTML = `
                        <div class="diff-viewer">
                            <h3 style="color:var(--accent); margin-bottom:1rem;">Agent Report</h3>
                            <div style="line-height:1.6; color:var(--text-main); white-space: pre-wrap;">${data.report || 'No detailed report available.'}</div>
                        </div>
                    `;
                } else if (tab === 'pr') {
                    if (data.shouldGeneratePR && data.prDescription) {
                        tabContent.innerHTML = `
                            <div class="diff-viewer">
                                <h3 style="color:var(--primary); margin-bottom:1rem;">Proposed Pull Request</h3>
                                <div style="line-height:1.6; color:var(--text-main); white-space: pre-wrap;">${data.prDescription}</div>
                            </div>
                        `;
                    } else {
                        tabContent.innerHTML = `
                            <div class="diff-viewer">
                                <h3 style="color:var(--text-dim); margin-bottom:1rem;">No PR Generated</h3>
                                <div style="line-height:1.6; color:var(--text-dim);">
                                    This task did not require code changes, so no pull request was generated.
                                    ${data.changeReason ? `<br><br><em>Reason: ${data.changeReason}</em>` : ''}
                                </div>
                            </div>
                        `;
                    }
                }
            };
        });
    }

    function setupCopyButtons(data) {
        document.getElementById('download-patch-btn').onclick = () => {
            navigator.clipboard.writeText(data.diff || '');
            alert('Patch copied to clipboard!');
        };
        document.getElementById('copy-pr-btn').onclick = () => {
            navigator.clipboard.writeText(data.prDescription || '');
            alert('PR Description copied!');
        };
    }

    document.querySelectorAll('.option-card').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('.option-card').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
        });
    });
});
