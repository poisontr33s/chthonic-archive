// @SID: EXT_ACTIVATION_COCKPIT_V1
import * as crypto from 'crypto';
import * as vscode from 'vscode';

export function resolveWebCockpitUrl(config: vscode.WorkspaceConfiguration): string {
    const raw = config.get<string>('webCockpit.url', 'http://127.0.0.1:3000').trim();
    if (/^https?:\/\//i.test(raw)) {
        return raw;
    }
    return `http://${raw}`;
}

export function openWebCockpitPanel(
    context: vscode.ExtensionContext,
    outputChannel: vscode.OutputChannel,
    cockpitUrl: string,
): void {
    const panel = vscode.window.createWebviewPanel(
        'chthonicWebCockpit',
        'Chthonic Web Cockpit',
        vscode.ViewColumn.Active,
        {
            enableScripts: true,
            retainContextWhenHidden: true,
        },
    );

    panel.webview.html = buildWebCockpitHtml(cockpitUrl);

    panel.webview.onDidReceiveMessage(
        async (message: unknown) => {
            if (!message || typeof message !== 'object') {
                return;
            }
            const payload = message as { type?: string; url?: string };
            if (payload.type === 'start') {
                await vscode.commands.executeCommand('chthonic.startWebCockpit');
                return;
            }
            if (payload.type === 'openExternal' && payload.url) {
                await vscode.env.openExternal(vscode.Uri.parse(payload.url));
                return;
            }
            outputChannel.appendLine(`[webview] Received message: ${JSON.stringify(message)}`);
        },
        undefined,
        context.subscriptions,
    );

    panel.onDidDispose(
        () => {
            outputChannel.appendLine('[webview] Chthonic Web Cockpit panel disposed');
        },
        undefined,
        context.subscriptions,
    );
}

export function buildWebCockpitHtml(cockpitUrl: string): string {
    const nonce = createNonce();
    const safeUrl = escapeHtml(cockpitUrl);
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; frame-src http: https:; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';">
    <title>Chthonic Web Cockpit</title>
    <style>
        html, body {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            background: var(--vscode-editor-background);
            color: var(--vscode-editor-foreground);
            font-family: var(--vscode-font-family, Segoe UI, sans-serif);
        }
        .shell {
            display: grid;
            grid-template-rows: auto 1fr;
            height: 100%;
        }
        .bar {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 10px;
            border-bottom: 1px solid var(--vscode-panel-border);
            background: var(--vscode-sideBar-background);
            font-size: 12px;
        }
        .status {
            flex: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--vscode-descriptionForeground);
        }
        .btn {
            border: 1px solid var(--vscode-button-border, var(--vscode-panel-border));
            background: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 11px;
            cursor: pointer;
        }
        .btn:hover {
            background: var(--vscode-button-secondaryHoverBackground);
        }
        iframe {
            border: 0;
            width: 100%;
            height: 100%;
            background: #0b0b0b;
        }
    </style>
</head>
<body>
    <section class="shell">
        <header class="bar">
            <div id="status" class="status">Connecting to ${safeUrl}</div>
            <button id="start" class="btn" type="button">Start Server</button>
            <button id="external" class="btn" type="button">Open Browser</button>
        </header>
        <iframe id="cockpit" src="${safeUrl}" title="Chthonic Web Cockpit"></iframe>
    </section>
    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();
        const targetUrl = ${JSON.stringify(cockpitUrl)};
        const statusNode = document.getElementById('status');
        const iframe = document.getElementById('cockpit');
        let loaded = false;

        iframe.addEventListener('load', () => {
            loaded = true;
            statusNode.textContent = 'Connected: ' + targetUrl;
        });

        setTimeout(() => {
            if (!loaded) {
                statusNode.textContent = 'No response from ' + targetUrl + ' (try Start Server).';
            }
        }, 5000);

        document.getElementById('start').addEventListener('click', () => {
            vscode.postMessage({ type: 'start' });
        });
        document.getElementById('external').addEventListener('click', () => {
            vscode.postMessage({ type: 'openExternal', url: targetUrl });
        });
    </script>
</body>
</html>`;
}

export async function isWebCockpitReachable(url: string, timeoutMs = 1_200): Promise<boolean> {
    const abort = new AbortController();
    const timer = setTimeout(() => abort.abort(), Math.max(300, timeoutMs));
    try {
        const response = await fetch(url, {
            method: 'GET',
            redirect: 'follow',
            signal: abort.signal,
        });
        return response.ok;
    } catch {
        return false;
    } finally {
        clearTimeout(timer);
    }
}

export function delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function escapeHtml(value: string): string {
    return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function createNonce(): string {
    return crypto.randomBytes(18).toString('base64');
}
