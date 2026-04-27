// @SID: EXT_STYLUS_INPUT_V1
import * as vscode from 'vscode';

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
        const nonce = getNonce();
        const csp = [
            `default-src 'none'`,
            `style-src 'unsafe-inline'`,
            `script-src 'nonce-${nonce}'`,
        ].join('; ');

        return /* html */ `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="${csp}">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>Stylus Pad</title>
<style>
  *, *::before, *::after { box-sizing: border-box; }

  :root {
    --bg:       var(--vscode-editor-background, #1e1e1e);
    --fg:       var(--vscode-editor-foreground, #d4d4d4);
    --border:   var(--vscode-panel-border, #454545);
    --btn-bg:   var(--vscode-button-background, #0e639c);
    --btn-fg:   var(--vscode-button-foreground, #fff);
    --btn-hov:  var(--vscode-button-hoverBackground, #1177bb);
    --warn:     var(--vscode-editorWarning-foreground, #cca700);
    --accent:   var(--vscode-focusBorder, #007fd4);
    --radius:   6px;
  }

  body {
    margin: 0;
    padding: 8px;
    background: var(--bg);
    color: var(--fg);
    font-family: var(--vscode-font-family, sans-serif);
    font-size: var(--vscode-font-size, 13px);
    display: flex;
    flex-direction: column;
    gap: 8px;
    min-height: 100vh;
  }

  #pen-indicator {
    display: none;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: var(--accent);
    padding: 4px 6px;
    border: 1px solid var(--accent);
    border-radius: var(--radius);
    background: color-mix(in srgb, var(--accent) 12%, transparent);
  }
  #pen-indicator.active { display: flex; }
  #pen-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--accent);
    animation: pulse 1.2s ease-in-out infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.5; transform: scale(0.7); }
  }

  #pad-label {
    font-size: 11px;
    opacity: 0.6;
    user-select: none;
  }

  #pad {
    flex: 1;
    min-height: 160px;
    width: 100%;
    resize: vertical;
    background: var(--vscode-input-background, #3c3c3c);
    color: var(--vscode-input-foreground, var(--fg));
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 10px 12px;
    font-family: inherit;
    font-size: 15px;          /* larger for stylus tap precision */
    line-height: 1.6;
    outline: none;
    transition: border-color 0.15s;
    /* Android/Gboard hints */
    autocomplete: off;
    autocorrect: off;
    spellcheck: false;
    touch-action: manipulation;
  }
  #pad:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 1px var(--accent);
  }

  #char-count {
    font-size: 10px;
    opacity: 0.45;
    text-align: right;
    user-select: none;
  }

  .btn-row {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 6px;
  }
  .btn-row.secondary {
    grid-template-columns: 1fr 1fr;
  }

  button {
    padding: 8px 4px;
    background: var(--btn-bg);
    color: var(--btn-fg);
    border: none;
    border-radius: var(--radius);
    cursor: pointer;
    font-size: 12px;
    font-weight: 600;
    touch-action: manipulation;
    transition: background 0.1s, transform 0.08s;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  button:hover  { background: var(--btn-hov); }
  button:active { transform: scale(0.96); }
  button.danger {
    background: var(--vscode-button-secondaryBackground, #3a3d41);
    color: var(--vscode-button-secondaryForeground, var(--fg));
  }
  button.danger:hover { background: var(--vscode-button-secondaryHoverBackground, #45494e); }

  #status {
    font-size: 11px;
    opacity: 0.55;
    min-height: 16px;
    text-align: center;
  }
  #status.ok   { color: var(--vscode-testing-iconPassed, #73c991); opacity: 1; }
  #status.warn { color: var(--warn); opacity: 1; }
</style>
</head>
<body>

<div id="pen-indicator">
  <span id="pen-dot"></span>
  <span>Stylus detected — tap textarea, switch Gboard to ✍️ handwriting</span>
</div>

<div id="pad-label">✍️ Stylus / Handwriting Pad</div>

<textarea
  id="pad"
  inputmode="text"
  autocomplete="off"
  autocorrect="off"
  autocapitalize="off"
  spellcheck="false"
  placeholder="Write here with stylus or keyboard…&#10;&#10;On Android: tap here → switch Gboard to handwriting mode (✍️)"
  rows="8"
></textarea>

<div id="char-count">0 chars</div>

<div class="btn-row">
  <button id="btn-editor" title="Insert at cursor in active editor">→ Editor</button>
  <button id="btn-terminal" title="Send to active terminal (no Enter)">→ Terminal</button>
  <button id="btn-chat" title="Send to Copilot Chat">→ Chat</button>
</div>

<div class="btn-row secondary">
  <button id="btn-copy" class="danger" title="Copy to clipboard">Copy</button>
  <button id="btn-clear" class="danger" title="Clear pad">Clear</button>
</div>

<div id="status"></div>

<script nonce="${nonce}">
(function() {
  const vscode = acquireVsCodeApi();
  const pad    = document.getElementById('pad');
  const count  = document.getElementById('char-count');
  const status = document.getElementById('status');
  const penInd = document.getElementById('pen-indicator');

  let penActive = false;

  // ── Pen detection via Pointer Events ─────────────────────────
  function onPointerMove(e) {
    const isPen = e.pointerType === 'pen';
    if (isPen !== penActive) {
      penActive = isPen;
      penInd.classList.toggle('active', isPen);
      if (isPen) pad.focus();
    }
  }
  window.addEventListener('pointermove', onPointerMove, { passive: true });
  window.addEventListener('pointerdown', onPointerMove, { passive: true });

  // ── Char count ────────────────────────────────────────────────
  pad.addEventListener('input', () => {
    count.textContent = pad.value.length + ' chars';
  });

  // ── Status helpers ────────────────────────────────────────────
  let statusTimer;
  function setStatus(msg, type = '') {
    status.textContent = msg;
    status.className = type;
    clearTimeout(statusTimer);
    statusTimer = setTimeout(() => { status.textContent = ''; status.className = ''; }, 3000);
  }

  function getText() {
    const t = pad.value.trim();
    if (!t) { setStatus('Pad is empty.', 'warn'); return null; }
    return t;
  }

  // ── Route buttons ─────────────────────────────────────────────
  document.getElementById('btn-editor').addEventListener('click', () => {
    const t = getText(); if (!t) return;
    vscode.postMessage({ type: 'insert', text: t });
    setStatus('Sent to editor ✓', 'ok');
  });

  document.getElementById('btn-terminal').addEventListener('click', () => {
    const t = getText(); if (!t) return;
    vscode.postMessage({ type: 'terminal', text: t });
    setStatus('Sent to terminal ✓', 'ok');
  });

  document.getElementById('btn-chat').addEventListener('click', () => {
    const t = getText(); if (!t) return;
    vscode.postMessage({ type: 'chat', text: t });
    setStatus('Sent to chat ✓', 'ok');
  });

  document.getElementById('btn-copy').addEventListener('click', async () => {
    const t = getText(); if (!t) return;
    try {
      await navigator.clipboard.writeText(t);
      setStatus('Copied ✓', 'ok');
    } catch {
      vscode.postMessage({ type: 'insert', text: '' }); // fallback: no-op
      setStatus('Use browser copy (Ctrl+C / long-press)', 'warn');
    }
  });

  document.getElementById('btn-clear').addEventListener('click', () => {
    pad.value = '';
    count.textContent = '0 chars';
    pad.focus();
    setStatus('Cleared.', '');
  });

  // ── Focus message from extension ──────────────────────────────
  window.addEventListener('message', (e) => {
    if (e.data?.type === 'focus') pad.focus();
  });
})();
</script>
</body>
</html>`;
    }
}

function getNonce(): string {
    const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let text = '';
    for (let index = 0; index < 32; index += 1) {
        text += alphabet.charAt(Math.floor(Math.random() * alphabet.length));
    }
    return text;
}
