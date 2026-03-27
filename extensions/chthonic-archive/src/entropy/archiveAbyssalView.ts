// @SID: EXT_ARCHIVEABYSSALVIEW_V1
import * as path from 'path';
import * as vscode from 'vscode';
import type { EntropyGraphPayload } from './types';
import type { EntropySnapshot } from './entropyWorkerClient';
import { EntropyWorkerClient } from './entropyWorkerClient';

export class AbyssalPaneProvider implements vscode.WebviewViewProvider, vscode.Disposable {
    static readonly viewType = 'chthonic.abyssalView';

    private readonly disposables: vscode.Disposable[] = [];
    private view: vscode.WebviewView | null = null;
    private rootPath: string | null = null;

    constructor(
        private readonly extensionUri: vscode.Uri,
        private readonly workerClient: EntropyWorkerClient,
    ) {
        this.disposables.push(
            this.workerClient.onDidUpdateGraph((graph) => this.postMessage({ type: 'graph', graph })),
            this.workerClient.onDidUpdateSnapshot((snapshot) => this.postMessage({ type: 'snapshot', snapshot })),
        );
    }

    setRootPath(rootPath: string | null): void {
        this.rootPath = rootPath;
    }

    dispose(): void {
        this.disposables.forEach((entry) => entry.dispose());
        this.disposables.length = 0;
    }

    resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ): void {
        this.view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this.extensionUri],
        };
        webviewView.webview.html = this.getHtml(webviewView.webview);

        webviewView.webview.onDidReceiveMessage((message: unknown) => {
            this.handleMessage(message);
        });
    }

    private handleMessage(message: unknown): void {
        if (!message || typeof message !== 'object') {
            return;
        }
        const payload = message as { type?: string; path?: string };
        if (!payload.type) {
            return;
        }

        if (payload.type === 'ready') {
            this.postMessage({ type: 'snapshot', snapshot: this.workerClient.getSnapshot() });
            this.workerClient.requestGraph(260);
            return;
        }

        if (payload.type === 'requestGraph') {
            this.workerClient.requestGraph(260);
            return;
        }

        if (payload.type === 'requestScan' || payload.type === 'requestSediment') {
            // Keep requestSediment alias for webview backward compatibility.
            this.workerClient.rescanNow();
            this.workerClient.requestGraph(260);
            return;
        }

        if (payload.type === 'openFile' && payload.path && this.rootPath) {
            const normalizedRelative = path.normalize(payload.path);
            if (normalizedRelative.startsWith('..') || path.isAbsolute(normalizedRelative)) {
                return;
            }
            const absolutePath = path.join(this.rootPath, normalizedRelative);
            const uri = vscode.Uri.file(absolutePath);
            vscode.workspace.openTextDocument(uri).then((document) => {
                vscode.window.showTextDocument(document, { preview: false });
            }, () => {
                vscode.window.showWarningMessage(`Unable to open ${payload.path}`);
            });
        }
    }

    private postMessage(message: { type: string; graph?: EntropyGraphPayload; snapshot?: EntropySnapshot }): void {
        if (!this.view) {
            return;
        }
        this.view.webview.postMessage(message);
    }

    private getHtml(webview: vscode.Webview): string {
        const nonce = createNonce();
        const rendererScriptUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this.extensionUri, 'media', 'abyssalPane.js'),
        );
        const wasmModuleUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this.extensionUri, 'media', 'wasm', 'pkg', 'entropy_renderer_wasm.js'),
        );
        const wasmBinaryUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this.extensionUri, 'media', 'wasm', 'pkg', 'entropy_renderer_wasm_bg.wasm'),
        );
        const loomWasmModuleUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this.extensionUri, 'media', 'wasm', 'pkg', 'chthonic_loom.js'),
        );
        const loomWasmBinaryUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this.extensionUri, 'media', 'wasm', 'pkg', 'chthonic_loom_bg.wasm'),
        );

        const csp = [
            "default-src 'none'",
            `img-src ${webview.cspSource} data:`,
            `style-src ${webview.cspSource} 'unsafe-inline'`,
            `script-src 'nonce-${nonce}' ${webview.cspSource}`,
            `connect-src ${webview.cspSource}`,
        ].join('; ');

        const bootstrap = JSON.stringify({
            wasmModuleUri: wasmModuleUri.toString(),
            wasmBinaryUri: wasmBinaryUri.toString(),
            loomWasmModuleUri: loomWasmModuleUri.toString(),
            loomWasmBinaryUri: loomWasmBinaryUri.toString(),
        });

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="${csp}">
    <title>Abyssal Pane</title>
    <style>
        :root {
            --abyss-bg: var(--vscode-editor-background);
            --abyss-panel: var(--vscode-editorWidget-background);
            --abyss-border: var(--vscode-editorWidget-border);
            --abyss-fg: var(--vscode-editor-foreground);
            --abyss-muted: var(--vscode-descriptionForeground);
            --abyss-accent: #c9a962;
        }
        * { box-sizing: border-box; }
        html, body {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            background: var(--abyss-bg);
            color: var(--abyss-fg);
            font-family: var(--vscode-font-family, 'Segoe UI', sans-serif);
        }
        body {
            display: grid;
            grid-template-rows: auto auto 1fr;
            gap: 8px;
            padding: 10px;
        }
        .header {
            border: 1px solid var(--abyss-border);
            border-radius: 10px;
            background: var(--abyss-panel);
            padding: 10px;
        }
        .title {
            margin: 0;
            font-size: 13px;
            color: var(--abyss-accent);
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .subtitle {
            margin: 4px 0 0;
            color: var(--abyss-muted);
            font-size: 11px;
        }
        .stats {
            border: 1px solid var(--abyss-border);
            border-radius: 10px;
            background: var(--abyss-panel);
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 8px;
            padding: 8px;
        }
        .stat {
            border: 1px solid var(--abyss-border);
            border-radius: 8px;
            padding: 8px;
            background: rgba(0, 0, 0, 0.08);
        }
        .stat-label {
            color: var(--abyss-muted);
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .stat-value {
            margin-top: 4px;
            font-size: 14px;
            color: var(--abyss-fg);
        }
        .canvas-shell {
            position: relative;
            border: 1px solid var(--abyss-border);
            border-radius: 10px;
            overflow: hidden;
            background: linear-gradient(160deg, rgba(0, 0, 0, 0.14), rgba(0, 0, 0, 0.04));
        }
        #graph-canvas {
            width: 100%;
            height: 100%;
            min-height: 360px;
            display: block;
        }
        .legend {
            position: absolute;
            right: 10px;
            top: 10px;
            border: 1px solid var(--abyss-border);
            border-radius: 8px;
            padding: 6px 8px;
            background: color-mix(in srgb, var(--abyss-panel) 90%, transparent);
            font-size: 10px;
            color: var(--abyss-muted);
        }
        .legend-row {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 4px;
        }
        .legend-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }
    </style>
</head>
<body>
    <section class="header">
        <h1 class="title">Abyssal Pane · Root System</h1>
        <p class="subtitle">Live workspace-health stream from the worker (snapshot + dependency graph).</p>
    </section>
    <section class="stats">
        <article class="stat">
            <div class="stat-label">Tracked Files</div>
            <div id="stat-files" class="stat-value">0</div>
        </article>
        <article class="stat">
            <div class="stat-label">Avg Entropy</div>
            <div id="stat-entropy" class="stat-value">0%</div>
        </article>
        <article class="stat">
            <div class="stat-label">Render Mode</div>
            <div id="stat-renderer" class="stat-value">booting</div>
        </article>
    </section>
    <section class="canvas-shell">
        <canvas id="graph-canvas" aria-label="Abyssal dependency graph"></canvas>
        <div class="legend">
            <div class="legend-row"><span class="legend-dot" style="background:#7cae67"></span>low entropy</div>
            <div class="legend-row"><span class="legend-dot" style="background:#c9a962"></span>medium entropy</div>
            <div class="legend-row"><span class="legend-dot" style="background:#8a4c2a"></span>high entropy</div>
        </div>
    </section>

    <script nonce="${nonce}">
        window.__CHTHONIC_ABYSSAL__ = ${bootstrap};
    </script>
    <script nonce="${nonce}" type="module" src="${rendererScriptUri}"></script>
</body>
</html>`;
    }
}

function createNonce(): string {
    const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let nonce = '';
    for (let i = 0; i < 32; i += 1) {
        nonce += alphabet.charAt(Math.floor(Math.random() * alphabet.length));
    }
    return nonce;
}
