const vscode = acquireVsCodeApi();
const hmrKey = 'chthonic.hmr.design-frame.reloadCount';
const reloadCount = Number(sessionStorage.getItem(hmrKey) || '0');
const state = window.__DESIGN_FRAME_STATE__ || {};

document.getElementById('select').addEventListener('click', () => vscode.postMessage({ type: 'selectExport' }));
document.getElementById('refresh').addEventListener('click', () => vscode.postMessage({ type: 'refresh' }));
document.getElementById('run-intake').addEventListener('click', () => vscode.postMessage({ type: 'runIntake' }));
document.getElementById('open-contract').addEventListener('click', () => vscode.postMessage({ type: 'openContract' }));
document.getElementById('copy-handoff').addEventListener('click', () => vscode.postMessage({ type: 'copyHandoff' }));

window.addEventListener('message', (event) => {
    const message = event.data;
    if (message?.type === 'reload') {
        sessionStorage.setItem(hmrKey, String(reloadCount + 1));
        vscode.postMessage({ type: 'webviewHmr.reloadRequested', surface: 'design-frame' });
        setTimeout(() => location.reload(), 100);
    }
});

function text(value) {
    return value === null || value === undefined || value === '' ? 'n/a' : String(value);
}

function badgeClass(status) {
    const value = String(status || '').toLowerCase();
    if (value.includes('admitted')) return 'admitted';
    if (value.includes('blocked')) return 'blocked';
    if (value.includes('degraded')) return 'degraded';
    return 'open';
}

function render() {
    document.getElementById('selected-path').textContent = state.frameRoot
        ? `Frame: ${state.frameRoot}`
        : text(state.selectedRoot || 'No export selected');
    renderGates();
    renderTokens();
    renderPreview();
    renderContract();
    renderErrors();
}

function renderGates() {
    const root = document.getElementById('gates');
    root.innerHTML = '';
    const gates = Array.isArray(state.gates) ? state.gates : [];
    if (!gates.length) {
        root.innerHTML = '<div class="empty">No gate ledger loaded. Run intake or select a frame folder.</div>';
        return;
    }
    for (const gate of gates) {
        const row = document.createElement('div');
        row.className = 'gate-row';
        const level = document.createElement('strong');
        level.textContent = gate.level;
        const status = document.createElement('span');
        status.className = `badge ${badgeClass(gate.status)}`;
        status.textContent = gate.status;
        row.append(level, status);
        root.appendChild(row);
    }
}

function renderTokens() {
    const root = document.getElementById('tokens');
    root.innerHTML = '';
    const tokens = state.tokens || {};
    const rows = [];
    addTokenRows(rows, 'Color', tokens.colors, (item) => `${item.value} · ${item.source}`);
    addTokenRows(rows, 'Type', tokens.typography, (item) => `${item.role}: ${item.value}`);
    addTokenRows(rows, 'Space', tokens.spacing, (item) => `${item.name}: ${item.value}`);
    addTokenRows(rows, 'Radius', tokens.radii, (item) => `${item.value}`);
    addTokenRows(rows, 'Shadow', tokens.shadows, (item) => `${item.value}`);
    addTokenRows(rows, 'Asset', tokens.assets, (item) => `${item.path} · ${item.role}`);
    if (!rows.length) {
        root.innerHTML = '<div class="empty">No tokens loaded yet.</div>';
        return;
    }
    for (const rowData of rows.slice(0, 80)) {
        const row = document.createElement('div');
        row.className = 'token-row';
        const label = document.createElement('span');
        label.className = 'badge';
        label.textContent = rowData.label;
        const value = document.createElement('span');
        value.className = 'mono';
        value.textContent = rowData.value;
        row.append(label, value);
        root.appendChild(row);
    }
}

function addTokenRows(rows, label, list, renderItem) {
    if (!Array.isArray(list)) return;
    for (const item of list) {
        rows.push({ label, value: renderItem(item) });
    }
}

function renderPreview() {
    const root = document.getElementById('preview');
    root.innerHTML = '';
    const preview = state.preview || {};
    if (preview.mode === 'image' && preview.uri) {
        const img = document.createElement('img');
        img.className = 'preview-image';
        img.src = preview.uri;
        img.alt = preview.label || 'Claude Design screenshot';
        root.appendChild(img);
        return;
    }
    if (preview.mode === 'html' && preview.uri) {
        const iframe = document.createElement('iframe');
        iframe.className = 'preview-frame';
        iframe.title = preview.label || 'Claude Design HTML export';
        iframe.src = preview.uri;
        root.appendChild(iframe);
        return;
    }
    const empty = document.createElement('div');
    empty.className = 'empty';
    empty.textContent = preview.label || 'No local preview available.';
    root.appendChild(empty);
}

function renderContract() {
    const contract = document.getElementById('contract');
    const content = state.designContract || state.handoffPrompt || '';
    contract.textContent = content || 'No design_contract.md loaded.';
}

function renderErrors() {
    const root = document.getElementById('errors');
    root.innerHTML = '';
    const errors = Array.isArray(state.errors) ? state.errors : [];
    for (const error of errors) {
        const item = document.createElement('li');
        item.textContent = error;
        root.appendChild(item);
    }
}

function postHmrLoaded() {
    vscode.postMessage({
        type: 'webviewHmr.loaded',
        surface: 'design-frame',
        reloadCount,
        html: document.documentElement.outerHTML,
    });
}

render();
postHmrLoaded();
