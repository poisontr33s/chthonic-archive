import * as vscode from 'vscode';
import type { RustificationReport } from './rustificationScore';

export class LoomViewProvider implements vscode.WebviewViewProvider, vscode.Disposable {
    static readonly viewType = 'chthonic.loomView';

    private view: vscode.WebviewView | null = null;
    private report: RustificationReport | null = null;

    resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ): void {
        this.view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
        };
        webviewView.webview.html = this.buildHtml();

        webviewView.webview.onDidReceiveMessage((message: unknown) => {
            if (!message || typeof message !== 'object') {
                return;
            }
            const payload = message as { type?: string };
            if (payload.type === 'refresh') {
                void vscode.commands.executeCommand('chthonic.refreshRustification');
            }
            if (payload.type === 'heal') {
                void vscode.commands.executeCommand('chthonic.slabHeal');
            }
            if (payload.type === 'deepFocus') {
                void vscode.commands.executeCommand('chthonic.deepFocus');
            }
        });

        this.postState();
    }

    update(report: RustificationReport): void {
        this.report = report;
        this.postState();
    }

    dispose(): void {
        this.view = null;
    }

    private postState(): void {
        if (!this.view || !this.report) {
            return;
        }
        this.view.webview.postMessage({
            type: 'state',
            report: this.report,
        });
    }

    private buildHtml(): string {
        const nonce = createNonce();
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';">
    <title>The Loom</title>
    <style>
        :root {
            --bg: #050505;
            --fg: var(--vscode-editor-foreground);
            --muted: var(--vscode-descriptionForeground);
            --accent: #F4C430;
            --panel: color-mix(in srgb, var(--bg) 88%, #161616);
            --border: color-mix(in srgb, var(--accent) 32%, transparent);
        }
        * { box-sizing: border-box; }
        html, body {
            margin: 0;
            height: 100%;
            background: var(--bg);
            color: var(--fg);
            font-family: var(--vscode-font-family, Segoe UI, sans-serif);
        }
        body { padding: 10px; display: grid; grid-template-rows: auto auto 1fr auto; gap: 10px; }
        .panel {
            border: 1px solid var(--border);
            border-radius: 10px;
            background: var(--panel);
            padding: 10px;
        }
        .title { margin: 0; font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent); }
        .score { font-size: 28px; margin: 8px 0 0; }
        .meta { color: var(--muted); font-size: 11px; }
        .list { margin: 8px 0 0; padding: 0; list-style: none; max-height: 180px; overflow: auto; }
        .list li { font-size: 11px; color: var(--muted); padding: 2px 0; }
        .row { display: flex; gap: 8px; }
        button {
            flex: 1;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: transparent;
            color: var(--fg);
            padding: 8px;
            cursor: pointer;
        }
        button:hover {
            border-color: var(--accent);
            color: var(--accent);
        }
    </style>
</head>
<body>
    <section class="panel">
        <h1 class="title">The Loom</h1>
        <div id="score" class="score">0%</div>
        <div id="tier" class="meta">Gate</div>
    </section>

    <section class="panel">
        <div class="title">Markers Present</div>
        <ul id="present" class="list"></ul>
    </section>

    <section class="panel">
        <div class="title">Markers Missing</div>
        <ul id="missing" class="list"></ul>
    </section>

    <div class="row">
        <button id="refresh">Refresh</button>
        <button id="heal">Self-Heal</button>
        <button id="focus">Deep Focus</button>
    </div>

    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();
        const score = document.getElementById('score');
        const tier = document.getElementById('tier');
        const present = document.getElementById('present');
        const missing = document.getElementById('missing');

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

        document.getElementById('refresh').addEventListener('click', () => vscode.postMessage({ type: 'refresh' }));
        document.getElementById('heal').addEventListener('click', () => vscode.postMessage({ type: 'heal' }));
        document.getElementById('focus').addEventListener('click', () => vscode.postMessage({ type: 'deepFocus' }));

        window.addEventListener('message', (event) => {
            const message = event.data;
            if (!message || message.type !== 'state' || !message.report) {
                return;
            }
            const report = message.report;
            score.textContent = report.score + '%';
            tier.textContent = report.tier;
            setList(present, report.present || []);
            setList(missing, report.missing || []);
        });
    </script>
</body>
</html>`;
    }
}

function createNonce(): string {
    const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let nonce = '';
    for (let i = 0; i < 24; i += 1) {
        nonce += alphabet.charAt(Math.floor(Math.random() * alphabet.length));
    }
    return nonce;
}
