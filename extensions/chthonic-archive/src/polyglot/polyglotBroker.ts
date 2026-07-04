// @SID: EXT_POLYGLOTBROKER_V1
import * as fs from 'fs';
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
    private sidecarRootPath: string | null = null;
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
        private readonly extensionRoot: string,
    ) {}

    start(rootPath: string): void {
        this.rootPath = rootPath;
        this.sidecarRootPath = resolveSidecarRoot(rootPath, this.extensionRoot);
        if (!this.sidecarRootPath) {
            const searched = resolveSidecarCandidates(rootPath, this.extensionRoot).join(', ');
            const message = `sidecar scripts not found. checked: ${searched}`;
            this.output.appendLine(`[polyglot] ${message}`);
            this.fireSidecarError('python', message);
            this.fireSidecarError('ruby', message);
            return;
        }
        this.output.appendLine(`[polyglot] sidecar root: ${this.sidecarRootPath}`);
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
        this.sidecarRootPath = null;
        this.onDidReceiveRuffEmitter.dispose();
        this.onDidReceiveLoreEmitter.dispose();
        this.onDidReceiveSidecarErrorEmitter.dispose();
    }

    private startPythonSidecar(): void {
        if (!this.rootPath || this.pythonSidecar) {
            return;
        }
        if (!this.sidecarRootPath) {
            this.fireSidecarError('python', 'sidecar root unresolved; python scan unavailable.');
            return;
        }

        const scriptPath = path.join(this.sidecarRootPath, 'python', 'entropy_scan.py');
        if (!fs.existsSync(scriptPath)) {
            this.fireSidecarError('python', `python sidecar missing: ${scriptPath}`);
            return;
        }

        const venvBinDir = path.join(this.sidecarRootPath, 'venv', process.platform === 'win32' ? 'Scripts' : 'bin');
        const venvPython = path.join(venvBinDir, process.platform === 'win32' ? 'python.exe' : 'python');
        const hasVenvPython = fs.existsSync(venvPython);
        const pythonCommand = hasVenvPython ? venvPython : 'uv';
        const pythonArgs = hasVenvPython
            ? [scriptPath, '--stdio']
            : ['run', scriptPath, '--stdio'];

        if (!hasVenvPython) {
            this.output.appendLine('[polyglot:python] .chthonic/venv not found, falling back to uv run.');
        }

        this.pythonSidecar = spawn(pythonCommand, pythonArgs, {
            cwd: this.rootPath,
            stdio: ['pipe', 'pipe', 'pipe'],
            env: withPrependedPath(process.env, venvBinDir),
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
            this.fireSidecarError('python', `failed to spawn: ${error.message}`);
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
        if (!this.sidecarRootPath) {
            this.fireSidecarError('ruby', 'sidecar root unresolved; lore unavailable.');
            return;
        }
        const scriptPath = path.join(this.sidecarRootPath, 'ruby', 'lore.rb');
        if (!fs.existsSync(scriptPath)) {
            this.fireSidecarError('ruby', `ruby sidecar missing: ${scriptPath}`);
            return;
        }
        this.rubySidecar = spawn('ruby', ['--zjit', scriptPath], {
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
            this.fireSidecarError('ruby', `failed to spawn: ${error.message}`);
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

    private fireSidecarError(source: 'python' | 'ruby', message: string): void {
        this.onDidReceiveSidecarErrorEmitter.fire({
            type: 'error',
            source,
            message,
        });
        this.output.appendLine(`[polyglot:${source}] ${message}`);
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

function resolveSidecarRoot(rootPath: string, extensionRoot: string): string | null {
    for (const candidate of resolveSidecarCandidates(rootPath, extensionRoot)) {
        if (
            fs.existsSync(path.join(candidate, 'python', 'entropy_scan.py')) &&
            fs.existsSync(path.join(candidate, 'ruby', 'lore.rb'))
        ) {
            return candidate;
        }
    }
    return null;
}

function resolveSidecarCandidates(rootPath: string, extensionRoot: string): string[] {
    const candidates = [
        path.join(rootPath, '.chthonic'),
        path.join(rootPath, 'extensions', 'chthonic-archive', '.chthonic'),
        path.join(extensionRoot, '.chthonic'),
    ];
    return Array.from(new Set(candidates));
}

function withPrependedPath(
    env: NodeJS.ProcessEnv,
    candidatePath: string,
): NodeJS.ProcessEnv {
    if (!fs.existsSync(candidatePath)) {
        return env;
    }
    const pathKey = process.platform === 'win32' ? 'Path' : 'PATH';
    const existing = env[pathKey] ?? process.env[pathKey] ?? '';
    return {
        ...env,
        [pathKey]: existing
            ? `${candidatePath}${path.delimiter}${existing}`
            : candidatePath,
    };
}
