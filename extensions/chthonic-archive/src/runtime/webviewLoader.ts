// @SID: EXT_RUNTIME_WEBVIEW_LOADER_V1
import * as fs from 'node:fs';
import * as vscode from 'vscode';
import { markWebviewHmrDegraded } from './webviewHmrWatcher';

export type WebviewSubstitutions = Record<string, string>;

export function loadWebviewHtml(
    webview: vscode.Webview,
    mediaUri: vscode.Uri,
    surface: string,
    substitutions: WebviewSubstitutions = {},
): string {
    const nonce = createNonce();
    const templateUri = vscode.Uri.joinPath(mediaUri, 'media', 'views', surface, 'index.html');
    const viewScriptDiskUri = vscode.Uri.joinPath(mediaUri, 'media', 'views', surface, 'view.js');
    const viewScriptUri = webview.asWebviewUri(
        viewScriptDiskUri,
    );
    const csp = [
        `default-src 'none'`,
        `style-src 'unsafe-inline'`,
        `script-src 'nonce-${nonce}'`,
    ].join('; ');

    try {
        const template = fs.readFileSync(templateUri.fsPath, 'utf8');
        const viewScript = fs.readFileSync(viewScriptDiskUri.fsPath, 'utf8');
        return applySubstitutions(template, {
            nonce,
            csp,
            cspSource: webview.cspSource,
            viewScript,
            viewScriptUri: viewScriptUri.toString(),
            ...substitutions,
        });
    } catch (error) {
        const reason = `media/views/${surface}/index.html unreadable: ${stringifyError(error)}`;
        markWebviewHmrDegraded(reason);
        return unavailableHtml(surface, nonce, csp);
    }
}

export function applySubstitutions(template: string, substitutions: WebviewSubstitutions): string {
    return template.replace(/\{\{([A-Za-z0-9_]+)\}\}/g, (match, key: string) => {
        return Object.prototype.hasOwnProperty.call(substitutions, key)
            ? substitutions[key]
            : match;
    });
}

export function jsonForInlineScript(value: unknown): string {
    return JSON.stringify(value).replace(/</g, '\\u003c');
}

function unavailableHtml(surface: string, nonce: string, csp: string): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="${csp}">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${escapeHtml(surface)} unavailable</title>
<style>
body { margin: 0; padding: 12px; font-family: var(--vscode-font-family, sans-serif); color: var(--vscode-editor-foreground); background: var(--vscode-editor-background); }
</style>
</head>
<body>
<p>View unavailable.</p>
<script nonce="${nonce}">window.addEventListener('message', (event) => { if (event.data?.type === 'reload') location.reload(); });</script>
</body>
</html>`;
}

function escapeHtml(value: string): string {
    return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}

function createNonce(): string {
    const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let nonce = '';
    for (let i = 0; i < 32; i += 1) {
        nonce += alphabet.charAt(Math.floor(Math.random() * alphabet.length));
    }
    return nonce;
}
