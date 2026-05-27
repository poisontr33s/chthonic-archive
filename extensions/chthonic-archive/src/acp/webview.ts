// @SID: EXT_WEBVIEW_V1
/**
 * Chthonic Chat Webview — ACP agent chat panel inside VS Code.
 * Themed to match Flesh & Earth / ROGBIV. Renders markdown, code blocks, streaming.
 */
import * as vscode from 'vscode';
import { AcpConnection } from './connection';
import type { SessionNotification } from '@agentclientprotocol/sdk';

export class ChthonicChatProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'chthonic.chatView';
    private view?: vscode.WebviewView;
    private connection: AcpConnection | null = null;
    private isConnecting = false;

    constructor(
        private readonly extensionUri: vscode.Uri,
        private readonly log: (msg: string) => void,
    ) {}

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
        webviewView.webview.html = this.getHtml();

        webviewView.webview.onDidReceiveMessage(async (msg) => {
            switch (msg.type) {
                case 'connect':
                    await this.connectAgent();
                    break;
                case 'prompt':
                    await this.sendPrompt(msg.text);
                    break;
                case 'cancel':
                    await this.connection?.cancel();
                    break;
                case 'disconnect':
                    this.disconnectAgent();
                    break;
            }
        });
    }

    private async connectAgent(): Promise<void> {
        if (this.isConnecting || this.connection?.isConnected()) return;
        this.isConnecting = true;
        this.postMessage({ type: 'status', status: 'connecting' });

        try {
            const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || process.cwd();
            this.connection = new AcpConnection(this.log);

            // Listen for streaming session updates
            this.connection.getClient()?.on('session-update', (update: SessionNotification) => {
                this.postMessage({ type: 'session-update', update });
            });

            const session = await this.connection.connect(cwd);
            this.postMessage({
                type: 'connected',
                agentName: session.agentName,
                agentVersion: session.agentVersion,
            });
            this.log(`Chat connected: ${session.agentName}`);
        } catch (e: any) {
            this.log(`Chat connect failed: ${e.message}`);
            this.postMessage({ type: 'error', message: e.message });
        } finally {
            this.isConnecting = false;
        }
    }

    private async sendPrompt(text: string): Promise<void> {
        if (!this.connection?.isConnected()) {
            this.postMessage({ type: 'error', message: 'Not connected' });
            return;
        }

        this.postMessage({ type: 'prompt-start' });

        try {
            const response = await this.connection.prompt(text);
            this.postMessage({ type: 'prompt-end', response });
        } catch (e: any) {
            this.postMessage({ type: 'error', message: e.message });
        }
    }

    private disconnectAgent(): void {
        this.connection?.disconnect();
        this.connection = null;
        this.postMessage({ type: 'disconnected' });
    }

    private postMessage(msg: any): void {
        this.view?.webview.postMessage(msg);
    }

    dispose(): void {
        this.connection?.disconnect();
    }

    private getHtml(): string {
        return /*html*/`<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: var(--vscode-font-family, 'Segoe UI', sans-serif);
    font-size: var(--vscode-font-size, 13px);
    color: var(--vscode-foreground);
    background: var(--vscode-sideBar-background);
    height: 100vh;
    display: flex;
    flex-direction: column;
}
#status-bar {
    padding: 6px 10px;
    background: var(--vscode-sideBarSectionHeader-background);
    border-bottom: 1px solid var(--vscode-panel-border);
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11px;
}
#status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--vscode-editorWarning-foreground, #C9A55A);
}
#status-dot.connected { background: var(--vscode-charts-green, #A8C686); }
#status-dot.connecting { background: var(--vscode-editorWarning-foreground); animation: pulse 1s infinite; }
@keyframes pulse { 50% { opacity: 0.4; } }

#messages {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.msg {
    padding: 8px 12px;
    border-radius: 6px;
    max-width: 95%;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-word;
}
.msg.user {
    align-self: flex-end;
    background: var(--vscode-button-background, #D4A5A5);
    color: var(--vscode-button-foreground, #0E0B09);
}
.msg.agent {
    align-self: flex-start;
    background: var(--vscode-editorWidget-background);
    border: 1px solid var(--vscode-editorWidget-border);
}
.msg.system {
    align-self: center;
    color: var(--vscode-descriptionForeground);
    font-style: italic;
    font-size: 11px;
}
.msg code {
    font-family: var(--vscode-editor-font-family, 'Cascadia Code', monospace);
    background: var(--vscode-textCodeBlock-background, rgba(0,0,0,0.2));
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 12px;
}
.msg pre {
    background: var(--vscode-textCodeBlock-background, rgba(0,0,0,0.3));
    padding: 8px;
    border-radius: 4px;
    overflow-x: auto;
    margin: 6px 0;
}
.msg pre code { background: none; padding: 0; }

#input-area {
    padding: 8px 10px;
    border-top: 1px solid var(--vscode-panel-border);
    display: flex;
    gap: 6px;
}
#prompt-input {
    flex: 1;
    background: var(--vscode-input-background);
    color: var(--vscode-input-foreground);
    border: 1px solid var(--vscode-input-border);
    border-radius: 4px;
    padding: 6px 10px;
    font-family: inherit;
    font-size: inherit;
    resize: none;
    min-height: 32px;
    max-height: 120px;
}
#prompt-input:focus { outline: 1px solid var(--vscode-focusBorder); }
button {
    background: var(--vscode-button-background);
    color: var(--vscode-button-foreground);
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    cursor: pointer;
    font-size: 12px;
}
button:hover { background: var(--vscode-button-hoverBackground); }
button:disabled { opacity: 0.5; cursor: not-allowed; }
#connect-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    gap: 12px;
}
#connect-area h3 { color: var(--vscode-sideBarTitle-foreground); }
</style>
</head>
<body>
<div id="status-bar">
    <span id="status-dot"></span>
    <span id="status-text">Disconnected</span>
    <span style="flex:1"></span>
    <button id="btn-disconnect" style="display:none;font-size:10px;padding:2px 8px" onclick="disconnect()">×</button>
</div>

<div id="connect-area">
    <h3>☥ Chthonic Agent</h3>
    <p style="color:var(--vscode-descriptionForeground);font-size:11px;text-align:center">
        Connect to Copilot CLI (Claude) inside VS Code
    </p>
    <button onclick="connect()" id="btn-connect">Connect Agent</button>
</div>

<div id="messages" style="display:none"></div>

<div id="input-area" style="display:none">
    <textarea id="prompt-input" rows="1" placeholder="Ask the agent..." disabled></textarea>
    <button id="btn-send" onclick="send()" disabled>Send</button>
</div>

<script>
const vscode = acquireVsCodeApi();
const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('prompt-input');
const connectArea = document.getElementById('connect-area');
const inputArea = document.getElementById('input-area');

let currentAgentMsg = null;

function connect() {
    vscode.postMessage({ type: 'connect' });
}

function disconnect() {
    vscode.postMessage({ type: 'disconnect' });
}

function send() {
    const text = inputEl.value.trim();
    if (!text) return;
    addMessage('user', text);
    inputEl.value = '';
    inputEl.style.height = 'auto';
    inputEl.disabled = true;
    document.getElementById('btn-send').disabled = true;
    vscode.postMessage({ type: 'prompt', text });
}

function addMessage(role, text) {
    const el = document.createElement('div');
    el.className = 'msg ' + role;
    el.textContent = text;
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return el;
}

// Auto-resize textarea
inputEl.addEventListener('input', () => {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
});

// Enter to send, Shift+Enter for newline
inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        send();
    }
});

// Handle messages from extension
window.addEventListener('message', (event) => {
    const msg = event.data;
    switch (msg.type) {
        case 'status':
            document.getElementById('status-dot').className = msg.status;
            document.getElementById('status-text').textContent =
                msg.status === 'connecting' ? 'Connecting...' : msg.status;
            break;

        case 'connected':
            document.getElementById('status-dot').className = 'connected';
            document.getElementById('status-text').textContent = msg.agentName + ' v' + msg.agentVersion;
            document.getElementById('btn-disconnect').style.display = '';
            connectArea.style.display = 'none';
            messagesEl.style.display = 'flex';
            inputArea.style.display = 'flex';
            inputEl.disabled = false;
            document.getElementById('btn-send').disabled = false;
            addMessage('system', '☥ Connected to ' + msg.agentName);
            inputEl.focus();
            break;

        case 'disconnected':
            document.getElementById('status-dot').className = '';
            document.getElementById('status-text').textContent = 'Disconnected';
            document.getElementById('btn-disconnect').style.display = 'none';
            connectArea.style.display = 'flex';
            messagesEl.style.display = 'none';
            inputArea.style.display = 'none';
            currentAgentMsg = null;
            break;

        case 'session-update':
            handleSessionUpdate(msg.update);
            break;

        case 'prompt-start':
            currentAgentMsg = addMessage('agent', '');
            break;

        case 'prompt-end':
            if (msg.response && msg.response.content) {
                const text = msg.response.content
                    .filter(b => b.type === 'text')
                    .map(b => b.text)
                    .join('\\n');
                if (currentAgentMsg) {
                    currentAgentMsg.textContent = text;
                } else {
                    addMessage('agent', text);
                }
            }
            currentAgentMsg = null;
            inputEl.disabled = false;
            document.getElementById('btn-send').disabled = false;
            inputEl.focus();
            break;

        case 'error':
            addMessage('system', '⚠ ' + msg.message);
            inputEl.disabled = false;
            document.getElementById('btn-send').disabled = false;
            break;
    }
});

function handleSessionUpdate(update) {
    if (!update || !update.content) return;
    for (const block of update.content) {
        if (block.type === 'text' && block.text) {
            if (!currentAgentMsg) {
                currentAgentMsg = addMessage('agent', '');
            }
            currentAgentMsg.textContent += block.text;
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }
    }
}
</script>
</body>
</html>`;
    }
}
