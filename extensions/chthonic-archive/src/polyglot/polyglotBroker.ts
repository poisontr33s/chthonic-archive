import * as path from 'path';
import { spawn } from 'child_process';
import * as vscode from 'vscode';
import { createJsonlDecoder } from './jsonl';
import type {
    LoreEvent,
    LoreRequest,
    RuffScanRequest,
    RuffSummaryEvent,
    SidecarErrorEvent,
} from './types';

export class PolyglotBroker implements vscode.Disposable {
    private rootPath: string | null = null;
    private pythonSidecar: import('child_process').ChildProcess | null = null;
    private rubySidecar: import('child_process').ChildProcess | null = null;

    private readonly onDidReceiveRuffEmitter = new vscode.EventEmitter<RuffSummaryEvent>();
    readonly onDidReceiveRuff = this.onDidReceiveRuffEmitter.event;

    private readonly onDidReceiveLoreEmitter = new vscode.EventEmitter<LoreEvent>();
    readonly onDidReceiveLore = this.onDidReceiveLoreEmitter.event;

    private readonly onDidReceiveSidecarErrorEmitter = new vscode.EventEmitter<SidecarErrorEvent>();
    readonly onDidReceiveSidecarError = this.onDidReceiveSidecarErrorEmitter.event;

    constructor(
        private readonly output: vscode.OutputChannel,
    ) {}

    start(rootPath: string): void {
        this.rootPath = rootPath;
        this.startPythonSidecar();
        this.startRubySidecar();
    }

    requestScan(request: RuffScanRequest): void {
        if (!this.pythonSidecar || this.pythonSidecar.killed) {
            this.startPythonSidecar();
        }
        this.writeJson(this.pythonSidecar, request);
    }

    requestLore(request: LoreRequest): void {
        if (!this.rubySidecar || this.rubySidecar.killed) {
            this.startRubySidecar();
        }
        this.writeJson(this.rubySidecar, request);
    }

    dispose(): void {
        this.pythonSidecar?.kill();
        this.rubySidecar?.kill();
        this.pythonSidecar = null;
        this.rubySidecar = null;
        this.onDidReceiveRuffEmitter.dispose();
        this.onDidReceiveLoreEmitter.dispose();
        this.onDidReceiveSidecarErrorEmitter.dispose();
    }

    private startPythonSidecar(): void {
        if (!this.rootPath || this.pythonSidecar) {
            return;
        }
        const scriptPath = path.join(this.rootPath, '.chthonic', 'python', 'entropy_scan.py');
        const venvPython = path.join(
            this.rootPath,
            '.chthonic',
            'venv',
            process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python',
        );

        this.pythonSidecar = spawn('uv', [
            'run',
            '--python',
            venvPython,
            scriptPath,
            '--stdio',
        ], {
            cwd: this.rootPath,
            stdio: ['pipe', 'pipe', 'pipe'],
        });

        const decoder = createJsonlDecoder(
            (payload) => this.handlePythonPayload(payload),
            (error) => this.output.appendLine(`[polyglot:python] invalid JSONL payload: ${error.message}`),
        );

        this.pythonSidecar.stdout?.on('data', (chunk: Buffer) => decoder.push(chunk));
        this.pythonSidecar.stderr?.on('data', (chunk: Buffer) => {
            this.output.appendLine(`[polyglot:python] ${chunk.toString().trimEnd()}`);
        });

        this.pythonSidecar.on('error', (error) => {
            this.onDidReceiveSidecarErrorEmitter.fire({
                type: 'error',
                source: 'python',
                message: error.message,
            });
            this.output.appendLine(`[polyglot:python] failed to spawn: ${error.message}`);
            this.pythonSidecar = null;
        });
        this.pythonSidecar.on('exit', (code) => {
            decoder.flush();
            this.output.appendLine(`[polyglot:python] exited with code ${code ?? -1}`);
            this.pythonSidecar = null;
        });
    }

    private startRubySidecar(): void {
        if (!this.rootPath || this.rubySidecar) {
            return;
        }
        const scriptPath = path.join(this.rootPath, '.chthonic', 'ruby', 'lore.rb');
        this.rubySidecar = spawn('ruby', [scriptPath], {
            cwd: this.rootPath,
            stdio: ['pipe', 'pipe', 'pipe'],
        });

        const decoder = createJsonlDecoder(
            (payload) => this.handleRubyPayload(payload),
            (error) => this.output.appendLine(`[polyglot:ruby] invalid JSONL payload: ${error.message}`),
        );

        this.rubySidecar.stdout?.on('data', (chunk: Buffer) => decoder.push(chunk));
        this.rubySidecar.stderr?.on('data', (chunk: Buffer) => {
            this.output.appendLine(`[polyglot:ruby] ${chunk.toString().trimEnd()}`);
        });
        this.rubySidecar.on('error', (error) => {
            this.onDidReceiveSidecarErrorEmitter.fire({
                type: 'error',
                source: 'ruby',
                message: error.message,
            });
            this.output.appendLine(`[polyglot:ruby] failed to spawn: ${error.message}`);
            this.rubySidecar = null;
        });
        this.rubySidecar.on('exit', (code) => {
            decoder.flush();
            this.output.appendLine(`[polyglot:ruby] exited with code ${code ?? -1}`);
            this.rubySidecar = null;
        });
    }

    private writeJson(processRef: import('child_process').ChildProcess | null, payload: object): void {
        if (!processRef?.stdin || processRef.killed) {
            return;
        }
        try {
            processRef.stdin.write(`${JSON.stringify(payload)}\n`);
        } catch (error) {
            this.output.appendLine(`[polyglot] sidecar write failed: ${stringifyError(error)}`);
        }
    }

    private handlePythonPayload(payload: Record<string, unknown>): void {
        if (payload.type === 'ruff-summary') {
            const event = payload as unknown as RuffSummaryEvent;
            this.onDidReceiveRuffEmitter.fire(event);
            return;
        }
        if (payload.type === 'error') {
            const message = String(payload.message ?? 'python sidecar error');
            this.output.appendLine(`[polyglot:python] ${message}`);
            this.onDidReceiveSidecarErrorEmitter.fire({
                type: 'error',
                source: 'python',
                message,
            });
        }
    }

    private handleRubyPayload(payload: Record<string, unknown>): void {
        if (payload.type === 'lore') {
            this.onDidReceiveLoreEmitter.fire(payload as unknown as LoreEvent);
            return;
        }
        if (payload.type === 'error') {
            const message = String(payload.message ?? 'ruby sidecar error');
            this.output.appendLine(`[polyglot:ruby] ${message}`);
            this.onDidReceiveSidecarErrorEmitter.fire({
                type: 'error',
                source: 'ruby',
                message,
            });
        }
    }
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}
