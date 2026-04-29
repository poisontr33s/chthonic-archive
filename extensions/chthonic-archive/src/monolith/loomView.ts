// @SID: EXT_LOOMVIEW_V1
import * as vscode from 'vscode';
import type { EntropySnapshot } from '../entropy/entropyWorkerClient';
import { loadWebviewHtml } from '../runtime/webviewLoader';
import { trackWebview } from '../runtime/webviewHmrWatcher';
import type { RustificationReport } from './rustificationScore';

export class LoomViewProvider implements vscode.WebviewViewProvider, vscode.Disposable {
    static readonly viewType = 'chthonic.loomView';

    private view: vscode.WebviewView | null = null;
    private report: RustificationReport | null = null;
    private snapshot: EntropySnapshot | null = null;

    constructor(private readonly extensionUri: vscode.Uri) {}

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
        webviewView.webview.html = this.buildHtml(webviewView.webview);
        trackWebview('loom', webviewView, () => {
            webviewView.webview.html = this.buildHtml(webviewView.webview);
            this.postState();
        });

        webviewView.webview.onDidReceiveMessage((message: unknown) => {
            if (!message || typeof message !== 'object') {
                return;
            }
            const payload = message as { type?: string };
            if (payload.type === 'refresh') {
                void vscode.commands.executeCommand('chthonic.refreshRustification');
            }
            if (payload.type === 'rescan') {
                void vscode.commands.executeCommand('chthonic.entropyRefresh');
            }
            if (payload.type === 'heal') {
                void vscode.commands.executeCommand('chthonic.slabHeal');
            }
            if (payload.type === 'deepFocus') {
                void vscode.commands.executeCommand('chthonic.deepFocus');
            }
            if (payload.type === 'restoreOrder') {
                void vscode.commands.executeCommand('chthonic.restoreOrder');
            }
        });

        this.postState();
    }

    update(report: RustificationReport): void {
        this.report = report;
        this.postState();
    }

    updateWorkspaceHealth(snapshot: EntropySnapshot): void {
        this.snapshot = snapshot;
        this.postState();
    }

    dispose(): void {
        this.view = null;
    }

    private postState(): void {
        if (!this.view) {
            return;
        }
        this.view.webview.postMessage({
            type: 'state',
            report: this.report,
            snapshot: this.snapshot,
        });
    }

    private buildHtml(webview: vscode.Webview): string {
        return loadWebviewHtml(webview, this.extensionUri, 'loom');
    }
}
