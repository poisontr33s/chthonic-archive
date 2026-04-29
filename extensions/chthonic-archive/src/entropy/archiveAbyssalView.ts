// @SID: EXT_ARCHIVEABYSSALVIEW_V1
import * as path from 'path';
import * as vscode from 'vscode';
import { jsonForInlineScript, loadWebviewHtml } from '../runtime/webviewLoader';
import { trackWebview } from '../runtime/webviewHmrWatcher';
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
        trackWebview('abyssal', webviewView, () => {
            webviewView.webview.html = this.getHtml(webviewView.webview);
        });

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

        const bootstrap = {
            wasmModuleUri: wasmModuleUri.toString(),
            wasmBinaryUri: wasmBinaryUri.toString(),
            loomWasmModuleUri: loomWasmModuleUri.toString(),
            loomWasmBinaryUri: loomWasmBinaryUri.toString(),
        };

        return loadWebviewHtml(webview, this.extensionUri, 'abyssal', {
            bootstrapJson: jsonForInlineScript(bootstrap),
            rendererScriptUri: rendererScriptUri.toString(),
            csp: [
                "default-src 'none'",
                'img-src {{cspSource}} data:',
                "style-src {{cspSource}} 'unsafe-inline'",
                "script-src 'nonce-{{nonce}}' {{cspSource}}",
                'connect-src {{cspSource}}',
            ].join('; '),
        });
    }
}
