// @SID: EXT_EXTENSION_V1
/**
 * Chthonic Archive VSCode Extension
 * 
 * Thin VS Code bridge for the Rust-native deepseek-core agent.
 * TypeScript owns editor integration only; Rust owns agent behavior.
 */

import * as vscode from 'vscode';
import { join } from 'path';
import { readFile } from 'fs/promises';
import { existsSync } from 'fs';
import { spawn } from 'child_process';
import type { ChildProcessWithoutNullStreams } from 'child_process';
import { ChthonicTerminal } from './terminal';

let chatPanel: vscode.WebviewPanel | undefined;
let sidecar: RustSidecar | undefined;
let lastEditPlanId: string | undefined;

export async function activate(context: vscode.ExtensionContext) {
  console.log('🔥 Chthonic Archive Assistant activating...');
  if (!vscode.workspace.isTrusted) {
    vscode.window.showErrorMessage('Chthonic requires a trusted workspace to start its local Rust agent.');
    return;
  }

  sidecar = new RustSidecar(context.extensionUri, context);
  context.subscriptions.push(sidecar);
  setupWorkspaceWatchers(context, sidecar);

  // Register chat panel provider
  const provider = new ChthonicChatProvider(context.extensionUri, sidecar);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider('chthonic.chatView', provider)
  );

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand('chthonic.openChat', () => {
      if (chatPanel) {
        chatPanel.reveal(vscode.ViewColumn.Beside);
      } else {
        chatPanel = vscode.window.createWebviewPanel(
          'chthonicChat',
          'Chthonic Chat',
          vscode.ViewColumn.Beside,
          {
            enableScripts: true,
            retainContextWhenHidden: true,
          }
        );
        chatPanel.webview.html = provider.getHtmlForWebview(chatPanel.webview);
        chatPanel.onDidDispose(() => {
          chatPanel = undefined;
        });
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('chthonic.injectSSOT', async () => {
      const ssotPath = await getSSOTPath();
      if (!ssotPath) {
        vscode.window.showErrorMessage('SSOT file not found');
        return;
      }
      const content = await readFile(ssotPath, 'utf-8');
      vscode.window.showInformationMessage(`SSOT loaded (${content.length} bytes)`);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('chthonic.validateHash', async () => {
      const ssotPath = await getSSOTPath();
      if (!ssotPath) return;
      
      // TODO: Implement hash validation using ssot_hash.py
      vscode.window.showInformationMessage('SSOT hash validation: TODO');
    })
  );

  const openTerminal = async () => {
    const [deepseekApiKey, openaiApiKey, anthropicApiKey, files] = await Promise.all([
      context.secrets.get('chthonic.deepseekKey'),
      context.secrets.get('chthonic.openaiKey'),
      context.secrets.get('chthonic.anthropicKey'),
      vscode.workspace.findFiles(
        '**/*',
        '{**/node_modules/**,**/.git/**,**/target/**,**/dist/**}',
        5000
      ),
    ]);

    const terminal = vscode.window.createTerminal({
      name: 'Chthonic Code',
      pty: new ChthonicTerminal({
        extensionUri: context.extensionUri,
        deepseekApiKey,
        openaiApiKey,
        anthropicApiKey,
        workspaceFiles: files.map((file) => file.fsPath),
      }),
    });
    terminal.show();
  };

  context.subscriptions.push(
    vscode.commands.registerCommand('chthonic.openTerminal', openTerminal)
  );
  context.subscriptions.push(
    vscode.commands.registerCommand('chthonic.startTerminal', openTerminal)
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('chthonic.rollbackLastEdit', async () => {
      if (!sidecar?.isAvailable()) {
        vscode.window.showErrorMessage('deepseek-core is not running.');
        return;
      }

      try {
        await sidecar.rollbackLastEdit(lastEditPlanId);
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        vscode.window.showErrorMessage(`Rollback failed: ${message}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('chthonic.cancelRequest', async () => {
      try {
        await sidecar?.cancelCurrentRequest();
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        vscode.window.showErrorMessage(`Cancel failed: ${message}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('chthonic.restartAgent', async () => {
      await sidecar?.restartNow();
    })
  );

  console.log('🔥💀⚓ Chthonic Archive Assistant activated');
}

export function deactivate() {
  sidecar?.dispose();
  console.log('Chthonic Archive Assistant deactivated');
}

class ChthonicChatProvider implements vscode.WebviewViewProvider {
  constructor(
    private readonly extensionUri: vscode.Uri,
    private readonly sidecarClient: RustSidecar
  ) {}

  public resolveWebviewView(
    webviewView: vscode.WebviewView,
    context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken
  ) {
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this.extensionUri],
    };

    webviewView.webview.html = this.getHtmlForWebview(webviewView.webview);

    // Handle messages from webview
    webviewView.webview.onDidReceiveMessage(async (message) => {
      console.log('🔥 Extension: Received message from webview:', message);
      switch (message.type) {
        case 'sendMessage':
          console.log('🔥 Extension: Handling sendMessage:', message.text);
          await this.handleChatMessage(message.text, webviewView.webview);
          break;
        case 'cancel':
          await this.sidecarClient.cancelCurrentRequest();
          break;
        case 'ready':
          console.log('🔥 Extension: Webview ready');
          break;
        default:
          console.log('🔥 Extension: Unknown message type:', message.type);
      }
    });
  }

  private async handleChatMessage(text: string, webview: vscode.Webview) {
    const debugLog: string[] = [];
    
    try {
      debugLog.push('✓ Step 1: handleChatMessage called');
      const workspaceFolder = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? '';

      if (this.sidecarClient.isAvailable()) {
        debugLog.push('✓ Step 2: deepseek-core sidecar available');
        const responseId = Date.now().toString();

        webview.postMessage({
          type: 'responseStart',
          id: responseId,
          timestamp: new Date().toISOString(),
        });

        await this.sidecarClient.streamChat(
          { text, workspace: workspaceFolder },
          (delta) => {
            webview.postMessage({
              type: 'responseChunk',
              id: responseId,
              delta,
            });
          }
        );

        webview.postMessage({
          type: 'responseEnd',
          id: responseId,
          timestamp: new Date().toISOString(),
        });

        debugLog.push('✓ Step 3: sidecar stream complete');
        console.log('🔥 Debug Log:\n' + debugLog.join('\n'));
        return;
      }

      throw new Error('deepseek-core is unavailable. Run `bun run build:core` or set chthonic.corePath.');

    } catch (error) {
      console.error('Chthonic Rust core error:', error);
      const errorMsg = error instanceof Error ? error.message : 'Unknown error';
      const stackTrace = error instanceof Error ? error.stack : '';
      
      debugLog.push(`✗ FAILED at current step`);
      debugLog.push(`✗ Error: ${errorMsg}`);
      
      webview.postMessage({
        type: 'response',
        text: `CHTHONIC RUST CORE TRACE:\n\n${debugLog.join('\n')}\n\nERROR DETAILS:\n${errorMsg}\n\nSTACK TRACE:\n${stackTrace}`,
        timestamp: new Date().toISOString(),
      });
      
      console.log('🔥 Debug Log:\n' + debugLog.join('\n'));
    }
  }

  public getHtmlForWebview(webview: vscode.Webview): string {
    const scriptUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, 'dist', 'index.js')
    );

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src ${webview.cspSource}; style-src ${webview.cspSource} 'unsafe-inline';">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chthonic Chat</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: var(--vscode-font-family);
      font-size: var(--vscode-font-size);
      color: var(--vscode-foreground);
      background: var(--vscode-editor-background);
      height: 100vh;
      display: flex;
      flex-direction: column;
    }
    .shell { flex: 1; display: flex; flex-direction: column; min-height: 0; }
    .empty {
      opacity: 0.65;
      text-align: center;
      margin-top: 2rem;
      line-height: 1.5;
    }
    .messages {
      flex: 1;
      overflow-y: auto;
      padding: 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }
    .message {
      padding: 0.75rem;
      border-radius: 4px;
      max-width: 85%;
      white-space: pre-wrap;
    }
    .message-text { margin: 0; white-space: pre-wrap; font: inherit; }
    .message.user {
      background: var(--vscode-inputValidation-infoBorder);
      align-self: flex-end;
    }
    .message.assistant {
      background: var(--vscode-editorWidget-background);
      align-self: flex-start;
      border: 1px solid var(--vscode-editorWidget-border);
    }
    .streaming-caret {
      display: inline-block;
      margin-left: 2px;
      color: var(--vscode-textLink-foreground);
    }
    .input-container {
      padding: 1rem;
      border-top: 1px solid var(--vscode-panel-border);
      display: flex;
      gap: 0.5rem;
    }
    .stop-button {
      display: none;
    }
    body[data-streaming="true"] .stop-button {
      display: inline-block;
    }
    input {
      flex: 1;
      background: var(--vscode-input-background);
      color: var(--vscode-input-foreground);
      border: 1px solid var(--vscode-input-border);
      padding: 0.5rem;
      font-family: inherit;
      font-size: inherit;
    }
    button {
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none;
      padding: 0.5rem 1rem;
      cursor: pointer;
      font-family: inherit;
    }
    button:hover {
      background: var(--vscode-button-hoverBackground);
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="messages" data-role="messages">
      <div class="empty">
        Chthonic Rust Agent
        <br />
        <small>deepseek-core owns the stream</small>
      </div>
    </section>
    <form class="input-container" data-role="form">
      <input data-role="input" type="text" placeholder="Ask the Rust core..." autofocus />
      <button type="submit">Send</button>
      <button class="stop-button" data-role="stop" type="button">Stop</button>
    </form>
  </main>
  <script type="module" src="${scriptUri}"></script>
</body>
</html>`;
  }
}

type PendingRpc = {
  resolve: (value: unknown) => void;
  reject: (error: Error) => void;
  onChunk?: (delta: string) => void;
};

type FileEdit = {
  uri: string;
  range: {
    startLine?: number;
    startCharacter?: number;
    endLine?: number;
    endCharacter?: number;
    start?: { line: number; character: number };
    end?: { line: number; character: number };
  };
  newText: string;
};

type EditPlan = {
  planId: string;
  summary: string;
  edits: FileEdit[];
};

type WorkspaceFileEntry = {
  uri: string;
  relativePath: string;
  languageId: string;
  lastModified: number;
  size: number;
  dependencies: string[];
};

type WorkspaceFileChange = {
  uri: string;
  type: 'created' | 'changed' | 'deleted';
  relativePath?: string;
  languageId?: string;
};

class RustSidecar implements vscode.Disposable {
  private process: ChildProcessWithoutNullStreams | undefined;
  private nextId = 1;
  private pending = new Map<string, PendingRpc>();
  private buffer = '';
  private unavailableReason = '';
  private readonly statusBar: vscode.StatusBarItem;
  private disposed = false;
  private suppressNextExit = false;
  private restartTimer: NodeJS.Timeout | undefined;
  private restartAttempts = 0;
  private readonly maxRestartAttempts = 5;

  constructor(
    private readonly extensionUri: vscode.Uri,
    private readonly context: vscode.ExtensionContext
  ) {
    this.statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    this.statusBar.command = 'chthonic.restartAgent';
    this.statusBar.text = 'Chthonic: starting';
    this.statusBar.show();
    context.subscriptions.push(this.statusBar);
    this.start();
  }

  public isAvailable(): boolean {
    return Boolean(this.process && !this.process.killed);
  }

  public async streamChat(
    params: { text: string; workspace: string },
    onChunk: (delta: string) => void
  ): Promise<void> {
    await this.request('chat.stream', params, onChunk);
  }

  public async initialize(params: { deepseekApiKey?: string; openaiApiKey?: string; anthropicApiKey?: string }): Promise<void> {
    await this.request('initialize', params);
  }

  public async sendWorkspaceFiles(files: Array<string | WorkspaceFileEntry>): Promise<void> {
    await this.request('workspace/files', { files });
  }

  public sendWorkspaceFileChanged(changes: WorkspaceFileChange[]): void {
    this.notify('workspace/fileChanged', { changes });
  }

  public async status(): Promise<unknown> {
    return this.request('agent/status', {});
  }

  public async confirmEditPlan(planId: string): Promise<void> {
    await this.request('edit/confirm', { planId });
  }

  public async rejectEditPlan(planId: string): Promise<void> {
    await this.request('edit/reject', { planId });
  }

  public async rollbackLastEdit(planId?: string): Promise<void> {
    await this.request('edit/rollback', { planId });
  }

  public async cancelCurrentRequest(): Promise<void> {
    await this.request('agent/cancel', {});
  }

  public async restartNow(): Promise<void> {
    this.clearRestartTimer();
    this.restartAttempts = 0;
    this.rejectPending('deepseek-core restarting');
    if (this.process && !this.process.killed) {
      this.suppressNextExit = true;
      this.process.kill();
    }
    this.process = undefined;
    this.start();
  }

  public dispose(): void {
    this.disposed = true;
    this.clearRestartTimer();
    for (const pending of this.pending.values()) {
      pending.reject(new Error('deepseek-core disposed'));
    }
    this.pending.clear();

    if (this.process && !this.process.killed) {
      try {
        this.process.stdin.write(JSON.stringify({
          jsonrpc: '2.0',
          id: 'shutdown',
          method: 'core.shutdown',
          params: {},
        }) + '\n');
      } catch {
        // Process is already gone.
      }
      this.process.kill();
    }
    this.statusBar.dispose();
  }

  private start(): void {
    const binaryPath = this.resolveBinaryPath();
    if (!binaryPath) {
      this.unavailableReason = 'deepseek-core.exe not built yet';
      this.statusBar.text = 'Chthonic: core missing';
      console.log(`DeepSeek core unavailable: ${this.unavailableReason}`);
      return;
    }

    this.statusBar.text = 'Chthonic: starting';

    this.process = spawn(binaryPath, ['rpc'], {
      cwd: vscode.Uri.joinPath(this.extensionUri, 'core').fsPath,
      env: coreProcessEnv(),
      windowsHide: true,
    });

    this.process.stdout.on('data', (chunk: Buffer) => this.handleStdout(chunk.toString('utf8')));
    this.process.stderr.on('data', (chunk: Buffer) => console.warn(`deepseek-core stderr: ${chunk.toString('utf8')}`));
    this.process.on('exit', (code) => {
      this.unavailableReason = `deepseek-core exited with code ${code}`;
      this.process = undefined;
      this.rejectPending(this.unavailableReason);
      if (this.disposed) return;
      if (this.suppressNextExit) {
        this.suppressNextExit = false;
        return;
      }
      this.scheduleRestart();
    });

    void this.request('core.ping', {})
      .then(async () => {
        this.restartAttempts = 0;
        this.statusBar.text = 'Chthonic: agent ready';
        await this.initializeRuntime();
      })
      .catch((error) => {
        this.unavailableReason = error.message;
        this.statusBar.text = 'Chthonic: ping failed';
        console.warn(`DeepSeek core ping failed: ${error.message}`);
      });
  }

  private scheduleRestart(): void {
    if (this.restartAttempts >= this.maxRestartAttempts) {
      this.statusBar.text = 'Chthonic: restart failed';
      void vscode.window.showErrorMessage(
        'Chthonic agent stopped after repeated restart failures.',
        'Restart Now'
      ).then((choice) => {
        if (choice === 'Restart Now') void this.restartNow();
      });
      return;
    }

    const delayMs = Math.min(30_000, 1000 * Math.pow(2, this.restartAttempts));
    this.restartAttempts += 1;
    this.statusBar.text = `Chthonic: restarting in ${Math.ceil(delayMs / 1000)}s`;
    this.restartTimer = setTimeout(() => {
      this.restartTimer = undefined;
      this.start();
    }, delayMs);
  }

  private clearRestartTimer(): void {
    if (this.restartTimer) {
      clearTimeout(this.restartTimer);
      this.restartTimer = undefined;
    }
  }

  private rejectPending(message: string): void {
    for (const pending of this.pending.values()) {
      pending.reject(new Error(message));
    }
    this.pending.clear();
  }

  private async initializeRuntime(): Promise<void> {
    const [deepseekApiKey, openaiApiKey, anthropicApiKey] = await Promise.all([
      this.context.secrets.get('chthonic.deepseekKey'),
      this.context.secrets.get('chthonic.openaiKey'),
      this.context.secrets.get('chthonic.anthropicKey'),
    ]);

    await this.initialize({ deepseekApiKey, openaiApiKey, anthropicApiKey });

    const files = await vscode.workspace.findFiles(
      '**/*',
      '{**/node_modules/**,**/.git/**,**/target/**,**/dist/**}',
      5000
    );
    const entries = await Promise.all(files.map((file) => toWorkspaceFileEntry(file)));
    await this.sendWorkspaceFiles(entries.filter((entry): entry is WorkspaceFileEntry => Boolean(entry)));
  }

  private resolveBinaryPath(): string | undefined {
    const configured = vscode.workspace.getConfiguration('chthonic').get<string>('corePath', '').trim();
    const candidates = [
      configured,
      vscode.Uri.joinPath(this.extensionUri, 'core', 'target', 'release', 'deepseek-core.exe').fsPath,
      vscode.Uri.joinPath(this.extensionUri, 'core', 'target', 'debug', 'deepseek-core.exe').fsPath,
    ].filter(Boolean);

    return candidates.find((candidate) => existsSync(candidate));
  }

  private request(method: string, params: unknown, onChunk?: (delta: string) => void): Promise<unknown> {
    if (!this.process || this.process.killed) {
      return Promise.reject(new Error(this.unavailableReason || 'deepseek-core is not running'));
    }

    const id = String(this.nextId++);
    const payload = JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n';

    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject, onChunk });
      this.process!.stdin.write(payload, (error) => {
        if (error) {
          this.pending.delete(id);
          reject(error);
        }
      });
    });
  }

  private notify(method: string, params: unknown): void {
    if (!this.process || this.process.killed) {
      return;
    }

    this.process.stdin.write(JSON.stringify({ jsonrpc: '2.0', method, params }) + '\n');
  }

  private handleStdout(chunk: string): void {
    this.buffer += chunk;
    let newlineIndex = this.buffer.indexOf('\n');

    while (newlineIndex >= 0) {
      const line = this.buffer.slice(0, newlineIndex).trim();
      this.buffer = this.buffer.slice(newlineIndex + 1);
      if (line) {
        this.handleLine(line);
      }
      newlineIndex = this.buffer.indexOf('\n');
    }
  }

  private handleLine(line: string): void {
    let message: any;
    try {
      message = JSON.parse(line);
    } catch (error) {
      console.warn(`deepseek-core emitted invalid JSON: ${line}`);
      return;
    }

    if (message.method === 'chat.chunk') {
      const id = String(message.params?.id ?? '');
      const pending = this.pending.get(id);
      pending?.onChunk?.(String(message.params?.delta ?? ''));
      return;
    }

    if (message.method === 'diff/apply') {
      void applyRustWorkspaceEdit(message.params?.edits ?? []);
      return;
    }

    if (message.method === 'edit/plan') {
      void handleEditPlan(message.params as EditPlan, this);
      return;
    }

    if (message.id !== undefined) {
      const id = String(message.id);
      const pending = this.pending.get(id);
      if (!pending) return;

      this.pending.delete(id);
      if (message.error) {
        pending.reject(new Error(String(message.error.message ?? 'deepseek-core request failed')));
      } else {
        pending.resolve(message.result);
      }
    }
  }
}

async function handleEditPlan(plan: EditPlan, client: RustSidecar): Promise<void> {
  const choice = await vscode.window.showInformationMessage(
    `Apply plan: ${plan.summary} (${plan.edits.length} edit${plan.edits.length === 1 ? '' : 's'})`,
    { modal: false },
    'Apply',
    'Reject'
  );

  if (choice === 'Apply') {
    await client.confirmEditPlan(plan.planId);
    lastEditPlanId = plan.planId;
  } else {
    await client.rejectEditPlan(plan.planId);
  }
}

function setupWorkspaceWatchers(context: vscode.ExtensionContext, client: RustSidecar): void {
  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument(async (document) => {
      if (document.uri.scheme !== 'file' || shouldIgnoreWorkspaceUri(document.uri)) return;
      const change = await toWorkspaceFileChange(document.uri, 'changed', document.languageId);
      client.sendWorkspaceFileChanged([change]);
    })
  );

  const watcher = vscode.workspace.createFileSystemWatcher('**/*');
  context.subscriptions.push(
    watcher,
    watcher.onDidCreate(async (uri) => {
      if (shouldIgnoreWorkspaceUri(uri)) return;
      const change = await toWorkspaceFileChange(uri, 'created');
      client.sendWorkspaceFileChanged([change]);
    }),
    watcher.onDidChange(async (uri) => {
      if (shouldIgnoreWorkspaceUri(uri)) return;
      const change = await toWorkspaceFileChange(uri, 'changed');
      client.sendWorkspaceFileChanged([change]);
    }),
    watcher.onDidDelete((uri) => {
      if (shouldIgnoreWorkspaceUri(uri)) return;
      client.sendWorkspaceFileChanged([{ uri: uri.toString(), type: 'deleted' }]);
    })
  );
}

async function toWorkspaceFileEntry(uri: vscode.Uri): Promise<WorkspaceFileEntry | undefined> {
  if (shouldIgnoreWorkspaceUri(uri)) return undefined;

  try {
    const stat = await vscode.workspace.fs.stat(uri);
    if (stat.type !== vscode.FileType.File) return undefined;

    return {
      uri: uri.toString(),
      relativePath: vscode.workspace.asRelativePath(uri, false),
      languageId: languageIdForUri(uri),
      lastModified: stat.mtime,
      size: stat.size,
      dependencies: [],
    };
  } catch {
    return undefined;
  }
}

async function toWorkspaceFileChange(
  uri: vscode.Uri,
  type: WorkspaceFileChange['type'],
  languageId?: string
): Promise<WorkspaceFileChange> {
  return {
    uri: uri.toString(),
    type,
    relativePath: vscode.workspace.asRelativePath(uri, false),
    languageId: languageId ?? languageIdForUri(uri),
  };
}

function languageIdForUri(uri: vscode.Uri): string {
  const openDocument = vscode.workspace.textDocuments.find((document) => document.uri.toString() === uri.toString());
  if (openDocument) return openDocument.languageId;

  const extension = uri.path.split('.').pop()?.toLowerCase();
  switch (extension) {
    case 'js': return 'javascript';
    case 'jsx': return 'javascriptreact';
    case 'ts': return 'typescript';
    case 'tsx': return 'typescriptreact';
    case 'rs': return 'rust';
    case 'py': return 'python';
    case 'json': return 'json';
    case 'md': return 'markdown';
    case 'ps1': return 'powershell';
    case 'toml': return 'toml';
    case 'yaml':
    case 'yml': return 'yaml';
    default: return '';
  }
}

function shouldIgnoreWorkspaceUri(uri: vscode.Uri): boolean {
  if (uri.scheme !== 'file') return true;
  const relativePath = vscode.workspace.asRelativePath(uri, false).replace(/\\/g, '/');
  return (
    relativePath.includes('/node_modules/') ||
    relativePath.startsWith('node_modules/') ||
    relativePath.includes('/.git/') ||
    relativePath.startsWith('.git/') ||
    relativePath.includes('/target/') ||
    relativePath.startsWith('target/') ||
    relativePath.includes('/dist/') ||
    relativePath.startsWith('dist/')
  );
}

async function applyRustWorkspaceEdit(edits: FileEdit[]): Promise<void> {
  const workspaceEdit = new vscode.WorkspaceEdit();

  for (const edit of edits) {
    const startLine = edit.range.start?.line ?? edit.range.startLine ?? 0;
    const startCharacter = edit.range.start?.character ?? edit.range.startCharacter ?? 0;
    const endLine = edit.range.end?.line ?? edit.range.endLine ?? startLine;
    const endCharacter = edit.range.end?.character ?? edit.range.endCharacter ?? startCharacter;

    workspaceEdit.replace(
      vscode.Uri.parse(edit.uri),
      new vscode.Range(
        startLine,
        startCharacter,
        endLine,
        endCharacter
      ),
      edit.newText
    );
  }

  if (edits.length > 0) {
    await vscode.workspace.applyEdit(workspaceEdit);
  }
}

async function getSSOTPath(): Promise<string | undefined> {
  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (!workspaceFolders) return undefined;

  const config = vscode.workspace.getConfiguration('chthonic');
  const relativePath = config.get<string>('ssotPath', '.github/copilot-instructions.md');
  
  return join(workspaceFolders[0].uri.fsPath, relativePath);
}

function coreProcessEnv(): NodeJS.ProcessEnv {
  const config = vscode.workspace.getConfiguration('chthonic');
  return {
    ...process.env,
    CHTHONIC_PROVIDER: config.get<string>('provider', 'auto'),
    CHTHONIC_DEEPSEEK_MODEL: config.get<string>('deepseekModel', 'deepseek-chat'),
  };
}
