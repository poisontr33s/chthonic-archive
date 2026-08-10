import * as vscode from 'vscode';
import { existsSync } from 'fs';
import { spawn } from 'child_process';
import type { ChildProcessWithoutNullStreams } from 'child_process';

type TerminalInit = {
  extensionUri: vscode.Uri;
  deepseekApiKey?: string;
  openaiApiKey?: string;
  anthropicApiKey?: string;
  workspaceFiles: string[];
};

type PendingRequest = {
  onChunk?: (delta: string) => void;
  onDone?: () => void;
};

type FileEdit = {
  uri: string;
  range: {
    start?: { line: number; character: number };
    end?: { line: number; character: number };
    startLine?: number;
    startCharacter?: number;
    endLine?: number;
    endCharacter?: number;
  };
  newText: string;
};

type EditPlan = {
  planId: string;
  summary: string;
  edits: FileEdit[];
};

export class ChthonicTerminal implements vscode.Pseudoterminal {
  private readonly writeEmitter = new vscode.EventEmitter<string>();
  private readonly closeEmitter = new vscode.EventEmitter<number>();
  private child: ChildProcessWithoutNullStreams | undefined;
  private requestId = 1;
  private pending = new Map<string, PendingRequest>();
  private stdoutBuffer = '';
  private inputBuffer = '';
  private busy = false;
  private pendingPlan: EditPlan | undefined;
  private lastAppliedPlanId: string | undefined;
  private closing = false;
  private suppressNextExit = false;
  private restartTimer: NodeJS.Timeout | undefined;
  private restartAttempts = 0;
  private readonly maxRestartAttempts = 5;

  public readonly onDidWrite = this.writeEmitter.event;
  public readonly onDidClose = this.closeEmitter.event;

  constructor(private readonly init: TerminalInit) {}

  public open(_dimensions: vscode.TerminalDimensions | undefined): void {
    this.startSidecar();
  }

  private startSidecar(): void {
    const binaryPath = this.resolveBinaryPath();
    if (!binaryPath) {
      this.writeEmitter.fire('deepseek-core.exe not found. Run `bun run build:core` or set chthonic.corePath.\r\n');
      this.closeEmitter.fire(1);
      return;
    }

    this.child = spawn(binaryPath, ['rpc'], {
      cwd: vscode.Uri.joinPath(this.init.extensionUri, 'core').fsPath,
      env: coreProcessEnv(),
      windowsHide: true,
    });

    this.child.stdout.on('data', (data: Buffer) => this.handleStdout(data.toString('utf8')));
    this.child.stderr.on('data', (data: Buffer) => {
      this.writeEmitter.fire(`\x1b[31m${data.toString().replace(/\n/g, '\r\n')}\x1b[0m`);
    });
    this.child.on('exit', (code) => this.handleExit(code));

    this.initializeRuntime();

    this.writeEmitter.fire('Chthonic agent ready. Type a question, /help, /undo, or Ctrl+C to cancel.\r\n\r\n');
    this.prompt();
  }

  public close(): void {
    this.closing = true;
    this.clearRestartTimer();
    if (this.child && !this.child.killed) {
      this.child.kill();
    }
  }

  public handleInput(data: string): void {
    if (data.includes('\x03')) {
      this.cancelCurrentRequest();
      return;
    }

    if (this.busy) return;

    for (const character of data) {
      if (character === '\r') {
        const line = this.inputBuffer.trim();
        this.inputBuffer = '';
        this.writeEmitter.fire('\r\n');
        void this.submit(line);
        continue;
      }

      if (character === '\x7f') {
        if (this.inputBuffer.length > 0) {
          this.inputBuffer = this.inputBuffer.slice(0, -1);
          this.writeEmitter.fire('\b \b');
        }
        continue;
      }

      this.inputBuffer += character;
      this.writeEmitter.fire(character);
    }
  }

  private initializeRuntime(): void {
    this.send('initialize', {
      deepseekApiKey: this.init.deepseekApiKey,
      openaiApiKey: this.init.openaiApiKey,
      anthropicApiKey: this.init.anthropicApiKey,
    });
    this.send('workspace/files', { files: this.init.workspaceFiles });
  }

  private cancelCurrentRequest(): void {
    this.writeEmitter.fire('^C\r\nCancelling current request...\r\n');
    this.send('agent/cancel', {}, {
      onDone: () => {
        this.busy = false;
        this.prompt();
      },
    });
  }

  private handleExit(code: number | null): void {
    this.child = undefined;
    this.pending.clear();
    this.busy = false;
    if (this.closing) {
      this.closeEmitter.fire(code ?? 0);
      return;
    }

    if (this.suppressNextExit) {
      this.suppressNextExit = false;
      return;
    }

    this.scheduleRestart(code);
  }

  private scheduleRestart(code: number | null): void {
    if (this.restartAttempts >= this.maxRestartAttempts) {
      this.writeEmitter.fire(`\r\nChthonic sidecar exited with code ${code ?? 'unknown'}; restart limit reached.\r\n`);
      this.prompt();
      return;
    }

    const delayMs = Math.min(30_000, 1000 * Math.pow(2, this.restartAttempts));
    this.restartAttempts += 1;
    this.writeEmitter.fire(`\r\nChthonic sidecar exited with code ${code ?? 'unknown'}; restarting in ${Math.ceil(delayMs / 1000)}s...\r\n`);
    this.restartTimer = setTimeout(() => {
      this.restartTimer = undefined;
      this.startSidecar();
    }, delayMs);
  }

  private clearRestartTimer(): void {
    if (this.restartTimer) {
      clearTimeout(this.restartTimer);
      this.restartTimer = undefined;
    }
  }

  private async submit(line: string): Promise<void> {
    if (!line) {
      this.prompt();
      return;
    }

    if (line === '/help') {
      this.writeEmitter.fire('Commands: /help, /undo, /plan-edit <file>\r\n');
      this.prompt();
      return;
    }

    if (line === '/undo') {
      this.busy = true;
      this.send('edit/rollback', { planId: this.lastAppliedPlanId }, {
        onDone: () => {
          this.busy = false;
          this.writeEmitter.fire('\r\nRollback request complete.\r\n');
          this.prompt();
        },
      });
      return;
    }

    this.busy = true;
    const workspace = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? 'terminal';
    this.send('chat.stream', { text: line, workspace }, {
      onChunk: (delta) => this.writeEmitter.fire(delta.replace(/\n/g, '\r\n')),
      onDone: () => {
        this.busy = false;
        this.writeEmitter.fire('\r\n');
        this.prompt();
      },
    });
  }

  private send(method: string, params: unknown, pending: PendingRequest = {}): string {
    const id = String(this.requestId++);
    this.pending.set(id, pending);
    if (!this.child || this.child.killed) {
      this.pending.delete(id);
      this.writeEmitter.fire('\r\ndeepseek-core is not running.\r\n');
      return id;
    }
    this.child.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
    return id;
  }

  private handleStdout(chunk: string): void {
    this.stdoutBuffer += chunk;
    let newlineIndex = this.stdoutBuffer.indexOf('\n');

    while (newlineIndex >= 0) {
      const line = this.stdoutBuffer.slice(0, newlineIndex).trim();
      this.stdoutBuffer = this.stdoutBuffer.slice(newlineIndex + 1);
      if (line) this.handleLine(line);
      newlineIndex = this.stdoutBuffer.indexOf('\n');
    }
  }

  private handleLine(line: string): void {
    let message: any;
    try {
      message = JSON.parse(line);
    } catch {
      return;
    }

    if (message.method === 'chat.chunk') {
      const pending = this.pending.get(String(message.params?.id ?? ''));
      pending?.onChunk?.(String(message.params?.delta ?? ''));
      return;
    }

    if (message.method === 'edit/plan') {
      void this.handleEditPlan(message.params as EditPlan);
      return;
    }

    if (message.method === 'diff/apply') {
      void applyWorkspaceEdit(message.params?.edits ?? []);
      return;
    }

    if (message.id !== undefined) {
      const id = String(message.id);
      const pending = this.pending.get(id);
      this.pending.delete(id);

      if (message.error) {
        this.writeEmitter.fire(`\r\n${String(message.error.message ?? 'request failed')}\r\n`);
        this.busy = false;
        this.prompt();
        return;
      }

      pending?.onDone?.();
    }
  }

  private async handleEditPlan(plan: EditPlan): Promise<void> {
    this.pendingPlan = plan;
    this.writeEmitter.fire(`\r\nEdit plan: ${plan.summary} (${plan.edits.length} edit${plan.edits.length === 1 ? '' : 's'})\r\n`);
    const choice = await vscode.window.showInformationMessage(
      `Apply plan: ${plan.summary} (${plan.edits.length} edit${plan.edits.length === 1 ? '' : 's'})`,
      { modal: false },
      'Apply',
      'Reject'
    );

    if (choice === 'Apply') {
      this.send('edit/confirm', { planId: plan.planId }, {
        onDone: () => {
          this.lastAppliedPlanId = plan.planId;
          this.pendingPlan = undefined;
          this.writeEmitter.fire('Plan applied. Use /undo to rollback.\r\n');
        },
      });
    } else {
      this.send('edit/reject', { planId: plan.planId }, {
        onDone: () => {
          this.pendingPlan = undefined;
          this.writeEmitter.fire('Plan rejected.\r\n');
        },
      });
    }
  }

  private resolveBinaryPath(): string | undefined {
    const configured = vscode.workspace.getConfiguration('chthonic').get<string>('corePath', '').trim();
    const candidates = [
      configured,
      vscode.Uri.joinPath(this.init.extensionUri, 'core', 'target', 'release', 'deepseek-core.exe').fsPath,
      vscode.Uri.joinPath(this.init.extensionUri, 'core', 'target', 'debug', 'deepseek-core.exe').fsPath,
    ].filter(Boolean);

    return candidates.find((candidate) => existsSync(candidate));
  }

  private prompt(): void {
    this.writeEmitter.fire('> ');
  }
}

async function applyWorkspaceEdit(edits: FileEdit[]): Promise<void> {
  const workspaceEdit = new vscode.WorkspaceEdit();

  for (const edit of edits) {
    const startLine = edit.range.start?.line ?? edit.range.startLine ?? 0;
    const startCharacter = edit.range.start?.character ?? edit.range.startCharacter ?? 0;
    const endLine = edit.range.end?.line ?? edit.range.endLine ?? startLine;
    const endCharacter = edit.range.end?.character ?? edit.range.endCharacter ?? startCharacter;

    workspaceEdit.replace(
      vscode.Uri.parse(edit.uri),
      new vscode.Range(startLine, startCharacter, endLine, endCharacter),
      edit.newText
    );
  }

  if (edits.length > 0) {
    await vscode.workspace.applyEdit(workspaceEdit);
  }
}

function coreProcessEnv(): NodeJS.ProcessEnv {
  const config = vscode.workspace.getConfiguration('chthonic');
  return {
    ...process.env,
    CHTHONIC_PROVIDER: config.get<string>('provider', 'auto'),
    CHTHONIC_DEEPSEEK_MODEL: config.get<string>('deepseekModel', 'deepseek-chat'),
  };
}
