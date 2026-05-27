// @SID: EXT_FLUX_LAUNCHER_VIEW_V1
import * as vscode from 'vscode';

export interface FluxLauncherState {
    readonly version: string;
    readonly workspaceRoot: string | null;
    readonly satelliteRunning: boolean;
    readonly bridgeAvailable: boolean;
    readonly bridgeCandidates: readonly string[];
}

type FluxLauncherCommand =
    | 'openPanel'
    | 'startBackend'
    | 'stopBackend'
    | 'verifyPresence'
    | 'showOutput';

interface FluxLauncherMessage {
    readonly command?: FluxLauncherCommand;
}

export class FluxLauncherViewProvider implements vscode.WebviewViewProvider, vscode.Disposable {
    static readonly viewType = 'chthonic.fluxLauncherView';

    private view: vscode.WebviewView | null = null;
    private state: FluxLauncherState;

    constructor(
        initialState: FluxLauncherState,
        private readonly dispatch: (command: FluxLauncherCommand) => void,
    ) {
        this.state = initialState;
    }

    resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ): void {
        this.view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
        };
        webviewView.webview.html = this.html();
        webviewView.webview.onDidReceiveMessage((message: FluxLauncherMessage) => {
            if (message.command) {
                this.dispatch(message.command);
            }
        });
        webviewView.onDidDispose(() => {
            this.view = null;
        });
        this.postState();
    }

    update(state: FluxLauncherState): void {
        this.state = state;
        this.postState();
    }

    dispose(): void {
        this.view = null;
    }

    private postState(): void {
        this.view?.webview.postMessage({
            type: 'state',
            state: this.state,
        });
    }

    private html(): string {
        const nonce = Math.random().toString(36).slice(2);
        return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';" />
<style>
  :root { color-scheme: dark; }
  body {
    margin: 0;
    padding: 12px;
    font-family: var(--vscode-font-family);
    color: var(--vscode-foreground);
    background: var(--vscode-sideBar-background);
  }
  .shell {
    display: grid;
    gap: 12px;
  }
  .title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }
  h2 {
    margin: 0;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0;
  }
  .badge {
    font-size: 11px;
    padding: 2px 6px;
    border: 1px solid var(--vscode-panel-border);
    color: var(--vscode-descriptionForeground);
    white-space: nowrap;
  }
  .state {
    display: grid;
    gap: 6px;
    border: 1px solid var(--vscode-panel-border);
    padding: 8px;
    background: var(--vscode-editor-background);
  }
  .row {
    display: grid;
    grid-template-columns: 74px minmax(0, 1fr);
    gap: 8px;
    font-size: 12px;
    min-width: 0;
  }
  .key {
    color: var(--vscode-descriptionForeground);
  }
  .value {
    min-width: 0;
    overflow-wrap: anywhere;
  }
  .ok { color: var(--vscode-testing-iconPassed); }
  .warn { color: var(--vscode-testing-iconQueued); }
  .bad { color: var(--vscode-testing-iconFailed); }
  .actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }
  button {
    min-height: 30px;
    border: 0;
    padding: 6px 8px;
    color: var(--vscode-button-foreground);
    background: var(--vscode-button-background);
    font-family: inherit;
    font-size: 12px;
    cursor: pointer;
  }
  button:hover {
    background: var(--vscode-button-hoverBackground);
  }
  button.secondary {
    color: var(--vscode-button-secondaryForeground);
    background: var(--vscode-button-secondaryBackground);
  }
  button.secondary:hover {
    background: var(--vscode-button-secondaryHoverBackground);
  }
  details {
    border-top: 1px solid var(--vscode-panel-border);
    padding-top: 8px;
  }
  summary {
    cursor: pointer;
    color: var(--vscode-descriptionForeground);
    font-size: 12px;
  }
  code {
    display: block;
    margin-top: 6px;
    padding: 6px;
    color: var(--vscode-editor-foreground);
    background: var(--vscode-textCodeBlock-background);
    overflow-wrap: anywhere;
    font-family: var(--vscode-editor-font-family);
    font-size: 11px;
  }
</style>
</head>
<body>
  <main class="shell">
    <section class="title">
      <h2>FLUX Gate</h2>
      <span id="version" class="badge">v?</span>
    </section>
    <section class="state" aria-live="polite">
      <div class="row"><span class="key">Extension</span><span class="value ok">active</span></div>
      <div class="row"><span class="key">Satellite</span><span id="satellite" class="value">unknown</span></div>
      <div class="row"><span class="key">Bridge</span><span id="bridge" class="value">checking</span></div>
      <div class="row"><span class="key">Workspace</span><span id="workspace" class="value">checking</span></div>
    </section>
    <section class="actions">
      <button data-command="openPanel">Open Panel</button>
      <button data-command="verifyPresence">Verify</button>
      <button class="secondary" data-command="startBackend">Start Backend</button>
      <button class="secondary" data-command="stopBackend">Stop Backend</button>
      <button class="secondary" data-command="showOutput">Output</button>
    </section>
    <details>
      <summary>Bridge candidates</summary>
      <div id="candidates"></div>
    </details>
  </main>
<script nonce="${nonce}">
const vscode = acquireVsCodeApi();
const satellite = document.getElementById('satellite');
const bridge = document.getElementById('bridge');
const workspace = document.getElementById('workspace');
const version = document.getElementById('version');
const candidates = document.getElementById('candidates');

document.addEventListener('click', (event) => {
  const target = event.target;
  if (!target || !target.dataset || !target.dataset.command) return;
  vscode.postMessage({ command: target.dataset.command });
});

window.addEventListener('message', (event) => {
  const message = event.data;
  if (!message || message.type !== 'state') return;
  render(message.state);
});

function render(state) {
  version.textContent = 'v' + state.version;
  satellite.textContent = state.satelliteRunning ? 'running' : 'idle';
  satellite.className = 'value ' + (state.satelliteRunning ? 'ok' : 'warn');
  bridge.textContent = state.bridgeAvailable ? 'found' : 'missing';
  bridge.className = 'value ' + (state.bridgeAvailable ? 'ok' : 'bad');
  workspace.textContent = state.workspaceRoot || 'unavailable';
  workspace.className = 'value ' + (state.workspaceRoot ? 'ok' : 'bad');
  candidates.innerHTML = '';
  for (const candidate of state.bridgeCandidates || []) {
    const code = document.createElement('code');
    code.textContent = candidate;
    candidates.appendChild(code);
  }
}
</script>
</body>
</html>`;
    }
}
