// @SID: EXT_STYLUS_INPUT_V1
import * as vscode from 'vscode';
import { loadWebviewHtml } from '../runtime/webviewLoader';
import { trackWebview } from '../runtime/webviewHmrWatcher';

/**
 * StylusInputProvider — Sidebar webview for stylus / handwriting input.
 *
 * On Android tablets running VS Code via tunnel (Chrome browser), focusing
 * the textarea in this panel and switching Gboard to handwriting mode lets
 * the user write with a stylus. The panel then routes the recognised text to
 * the active editor, the integrated terminal, or the Copilot chat input.
 *
 * Pen detection: Pointer Events API (`pointerType === 'pen'`) — when the
 * stylus is active, the textarea auto-focuses and a visual indicator appears.
 *
 * Route targets:
 *   → Active Editor  — inserts text at the current cursor position
 *   → Terminal       — sends text to the active terminal (without executing)
 *   → Chat           — copies text + opens Copilot chat input
 */
export class StylusInputProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'chthonic.stylusView';

    private _view?: vscode.WebviewView;

    constructor(private readonly _extensionUri: vscode.Uri) {}

    resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ): void {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri],
        };

        webviewView.webview.html = this._getHtml(webviewView.webview);
        trackWebview('stylus', webviewView, () => {
            webviewView.webview.html = this._getHtml(webviewView.webview);
        });

        webviewView.webview.onDidReceiveMessage(async (msg: {
            type: 'insert' | 'terminal' | 'chat';
            text: string;
        }) => {
            switch (msg.type) {
                case 'insert':
                    await this._insertInEditor(msg.text);
                    break;
                case 'terminal':
                    this._sendToTerminal(msg.text);
                    break;
                case 'chat':
                    await this._sendToChat(msg.text);
                    break;
            }
        });
    }

    /** Insert at cursor in the active text editor. */
    private async _insertInEditor(text: string): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('Stylus Pad: No active editor — open a file first.');
            return;
        }
        await editor.edit((eb) => {
            for (const sel of editor.selections) {
                eb.replace(sel, text);
            }
        });
        vscode.window.showTextDocument(editor.document, editor.viewColumn);
    }

    /** Send text to the active terminal (does NOT press Enter). */
    private _sendToTerminal(text: string): void {
        const terminal = vscode.window.activeTerminal ?? vscode.window.createTerminal('Stylus');
        terminal.show(true);
        terminal.sendText(text, false);
    }

    /** Copy text to clipboard + open Copilot chat. */
    private async _sendToChat(text: string): Promise<void> {
        await vscode.env.clipboard.writeText(text);
        try {
            await vscode.commands.executeCommand('workbench.action.chat.open', { query: text });
        } catch {
            // Copilot chat not available — show info with clipboard hint
            vscode.window.showInformationMessage(
                'Stylus Pad: Text copied to clipboard. Paste into chat (Ctrl+V / Cmd+V).',
            );
        }
    }

    /** Focus the textarea — called from command palette. */
    public focus(): void {
        this._view?.show(true);
        this._view?.webview.postMessage({ type: 'focus' });
    }

    private _getHtml(webview: vscode.Webview): string {
        return loadWebviewHtml(webview, this._extensionUri, 'stylus');
    }
}
