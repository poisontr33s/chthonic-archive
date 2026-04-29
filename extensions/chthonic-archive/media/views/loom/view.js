const vscode = acquireVsCodeApi();
const hmrKey = 'chthonic.hmr.loom.reloadCount';
const reloadCount = Number(sessionStorage.getItem(hmrKey) || '0');
const score = document.getElementById('score');
const tier = document.getElementById('tier');
const present = document.getElementById('present');
const missing = document.getElementById('missing');
const healthFiles = document.getElementById('health-files');
const healthEntropy = document.getElementById('health-entropy');
const healthDuration = document.getElementById('health-duration');
const healthUpdated = document.getElementById('health-updated');

function setList(element, values) {
    element.innerHTML = '';
    if (!values.length) {
        const item = document.createElement('li');
        item.textContent = 'none';
        element.appendChild(item);
        return;
    }
    for (const value of values) {
        const item = document.createElement('li');
        item.textContent = value;
        element.appendChild(item);
    }
}

function formatElapsed(epochMs) {
    if (!epochMs || Number.isNaN(epochMs)) {
        return 'n/a';
    }
    const elapsed = Math.max(0, Date.now() - epochMs);
    if (elapsed < 1000) return 'just now';
    const sec = Math.floor(elapsed / 1000);
    if (sec < 60) return sec + 's ago';
    const min = Math.floor(sec / 60);
    if (min < 60) return min + 'm ago';
    const hr = Math.floor(min / 60);
    if (hr < 48) return hr + 'h ago';
    const day = Math.floor(hr / 24);
    return day + 'd ago';
}

document.getElementById('refresh').addEventListener('click', () => vscode.postMessage({ type: 'refresh' }));
document.getElementById('rescan').addEventListener('click', () => vscode.postMessage({ type: 'rescan' }));
document.getElementById('heal').addEventListener('click', () => vscode.postMessage({ type: 'heal' }));
document.getElementById('focus').addEventListener('click', () => vscode.postMessage({ type: 'deepFocus' }));
document.getElementById('restore').addEventListener('click', () => vscode.postMessage({ type: 'restoreOrder' }));

window.addEventListener('message', (event) => {
    const message = event.data;
    if (message?.type === 'reload') {
        sessionStorage.setItem(hmrKey, String(reloadCount + 1));
        vscode.postMessage({ type: 'webviewHmr.reloadRequested', surface: 'loom' });
        setTimeout(() => location.reload(), 100);
        return;
    }
    if (!message || message.type !== 'state') {
        return;
    }

    const report = message.report;
    if (report) {
        score.textContent = report.score + '%';
        tier.textContent = report.tier;
        setList(present, report.present || []);
        setList(missing, report.missing || []);
    }

    const snapshot = message.snapshot;
    if (snapshot) {
        healthFiles.textContent = String(snapshot.totalFiles || 0);
        healthEntropy.textContent = Math.round((snapshot.averageEntropy || 0) * 100) + '%';
        healthDuration.textContent = String(snapshot.lastScanDurationMs || 0) + ' ms';
        healthUpdated.textContent = formatElapsed(snapshot.lastScanAt || 0);
    } else {
        healthFiles.textContent = '—';
        healthEntropy.textContent = '—';
        healthDuration.textContent = '—';
        healthUpdated.textContent = 'entropy disabled';
    }
});

function postHmrLoaded() {
    vscode.postMessage({
        type: 'webviewHmr.loaded',
        surface: 'loom',
        reloadCount,
        html: document.documentElement.outerHTML,
    });
}

postHmrLoaded();
