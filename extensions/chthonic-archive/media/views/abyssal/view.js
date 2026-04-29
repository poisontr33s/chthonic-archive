const vscode = acquireVsCodeApi();
const hmrKey = 'chthonic.hmr.abyssal.reloadCount';
const reloadCount = Number(sessionStorage.getItem(hmrKey) || '0');

window.__CHTHONIC_ABYSSAL__ = {{bootstrapJson}};

function postHmrLoaded() {
    vscode.postMessage({
        type: 'webviewHmr.loaded',
        surface: 'abyssal',
        reloadCount,
        html: document.documentElement.outerHTML,
    });
}

window.addEventListener('message', (event) => {
    if (event.data?.type !== 'reload') {
        return;
    }
    sessionStorage.setItem(hmrKey, String(reloadCount + 1));
    vscode.postMessage({ type: 'webviewHmr.reloadRequested', surface: 'abyssal' });
    setTimeout(() => location.reload(), 100);
});

postHmrLoaded();
