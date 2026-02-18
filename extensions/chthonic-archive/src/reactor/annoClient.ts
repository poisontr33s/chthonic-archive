import * as path from 'path';
import { spawn } from 'child_process';
import * as vscode from 'vscode';
import { createJsonlDecoder } from '../polyglot/jsonl';
import type {
    AnnoManifest,
    EntropyState,
    EnvReport,
    SedimentSynapseResult,
    SedimentChunk,
    SedimentResult,
    SynapseDescriptor,
} from './types';

interface PendingRequest<T = unknown> {
    resolve: (value: T) => void;
    reject: (error: Error) => void;
}

/**
 * TypeScript client for the chthonic-daemon Rust sidecar.
 *
 * Handles both:
 * - Unsolicited JSONL notifications (anno/manifest, anno/env, reactor/status)
 *   emitted during daemon startup
 * - Request-response pairs with correlated IDs
 *
 * Follows the same spawn + JSONL decoder pattern as RustLedgerHostClient.
 */
export class AnnoClient implements vscode.Disposable {
    private rootPath: string | null = null;
    private daemonProcess: import('child_process').ChildProcess | null = null;
    private requestCounter = 1;
    private readonly pending = new Map<number, PendingRequest>();

    private readonly onDidReceiveManifestEmitter = new vscode.EventEmitter<AnnoManifest>();
    readonly onDidReceiveManifest = this.onDidReceiveManifestEmitter.event;

    private readonly onDidReceiveEnvEmitter = new vscode.EventEmitter<EnvReport>();
    readonly onDidReceiveEnv = this.onDidReceiveEnvEmitter.event;

    private readonly onDidReceiveSedimentEmitter = new vscode.EventEmitter<SedimentResult>();
    readonly onDidReceiveSediment = this.onDidReceiveSedimentEmitter.event;

    private readonly onDidReceiveSedimentChunkEmitter = new vscode.EventEmitter<SedimentChunk>();
    readonly onDidReceiveSedimentChunk = this.onDidReceiveSedimentChunkEmitter.event;

    private readonly onDidReceiveSynapseEmitter = new vscode.EventEmitter<SynapseDescriptor>();
    readonly onDidReceiveSynapse = this.onDidReceiveSynapseEmitter.event;

    private readonly onDidReceiveEntropyStateEmitter = new vscode.EventEmitter<EntropyState>();
    readonly onDidReceiveEntropyState = this.onDidReceiveEntropyStateEmitter.event;

    constructor(
        private readonly output: vscode.OutputChannel,
        private readonly headlessVulkan: boolean,
        private readonly daemonBinaryOverride?: string,
        private readonly eolApiBase = 'https://endoflife.date/api/v1',
        private readonly entropyMonitorIntervalMs = 6 * 60 * 60 * 1_000,
    ) {}

    start(rootPath: string): void {
        this.rootPath = rootPath;
        this.startDaemon();
    }

    async requestSediment(maxLayers: number, maxFiles: number): Promise<SedimentResult> {
        return this.submitRequest<SedimentResult>('reactor/sediment', {
            max_layers: maxLayers,
            max_files: maxFiles,
        });
    }

    async requestSedimentStream(maxLayers: number, maxFiles: number, chunkSize = 220): Promise<SedimentResult> {
        return this.submitRequest<SedimentResult>('reactor/sediment_stream', {
            max_layers: maxLayers,
            max_files: maxFiles,
            chunk_size: chunkSize,
        });
    }

    async requestSedimentSynapse(maxLayers: number, maxFiles: number, chunkSize = 220): Promise<SedimentSynapseResult> {
        return this.submitRequest<SedimentSynapseResult>('reactor/sediment_synapse', {
            max_layers: maxLayers,
            max_files: maxFiles,
            chunk_size: chunkSize,
        });
    }

    async requestDetect(): Promise<AnnoManifest> {
        return this.submitRequest<AnnoManifest>('anno/detect', {});
    }

    async requestProvision(): Promise<EnvReport> {
        return this.submitRequest<EnvReport>('anno/provision', {});
    }

    async requestEntropyState(): Promise<EntropyState> {
        return this.submitRequest<EntropyState>('reactor/entropy_state', {});
    }

    dispose(): void {
        for (const [, pending] of this.pending) {
            pending.reject(new Error('AnnoClient disposed'));
        }
        this.pending.clear();
        this.daemonProcess?.kill();
        this.daemonProcess = null;
        this.onDidReceiveManifestEmitter.dispose();
        this.onDidReceiveEnvEmitter.dispose();
        this.onDidReceiveSedimentEmitter.dispose();
        this.onDidReceiveSedimentChunkEmitter.dispose();
        this.onDidReceiveSynapseEmitter.dispose();
        this.onDidReceiveEntropyStateEmitter.dispose();
    }

    private startDaemon(): void {
        if (!this.rootPath || this.daemonProcess) {
            return;
        }

        const binaryPath = this.daemonBinaryOverride
            ?? resolveDaemonBinaryPath(this.rootPath);

        const args = ['--workspace', this.rootPath];
        if (this.headlessVulkan) {
            args.push('--headless-vulkan');
        }

        this.daemonProcess = spawn(binaryPath, args, {
            cwd: this.rootPath,
            env: {
                ...process.env,
                CHTHONIC_EOL_API_BASE: this.eolApiBase,
                CHTHONIC_ENTROPY_MONITOR_INTERVAL_MS: String(Math.max(60_000, this.entropyMonitorIntervalMs)),
            },
            stdio: ['pipe', 'pipe', 'pipe'],
        });

        const decoder = createJsonlDecoder(
            (payload) => this.handlePayload(payload),
            (error) => this.output.appendLine(`[daemon] invalid JSONL: ${error.message}`),
        );

        this.daemonProcess.stdout?.on('data', (chunk: Buffer) => decoder.push(chunk));
        this.daemonProcess.stderr?.on('data', (chunk: Buffer) => {
            this.output.appendLine(`[daemon] ${chunk.toString().trimEnd()}`);
        });
        this.daemonProcess.on('error', (error) => {
            this.output.appendLine(`[daemon] spawn failed: ${error.message}`);
            this.rejectAllPending(new Error(`daemon spawn failed: ${error.message}`));
            this.daemonProcess = null;
        });
        this.daemonProcess.on('exit', (code) => {
            decoder.flush();
            this.output.appendLine(`[daemon] exited with code ${code ?? -1}`);
            this.rejectAllPending(new Error('daemon exited'));
            this.daemonProcess = null;
        });
    }

    private handlePayload(payload: Record<string, unknown>): void {
        // Notifications: have 'method' but no 'id'
        if ('method' in payload && !('id' in payload)) {
            this.handleNotification(payload);
            return;
        }
        // Responses: have 'id'
        if ('id' in payload && typeof payload.id === 'number') {
            this.handleResponse(payload);
        }
    }

    private handleNotification(payload: Record<string, unknown>): void {
        const method = payload.method as string;
        const params = payload.params as Record<string, unknown>;

        switch (method) {
            case 'anno/manifest':
                this.onDidReceiveManifestEmitter.fire(params as unknown as AnnoManifest);
                this.output.appendLine(`[daemon] ANNO manifest received (${(params as AnnoManifest).languages?.length ?? 0} languages)`);
                break;
            case 'anno/env':
                this.onDidReceiveEnvEmitter.fire(params as unknown as EnvReport);
                this.output.appendLine(`[daemon] env report received`);
                break;
            case 'reactor/status': {
                const status = (params as Record<string, string>).status ?? 'unknown';
                this.output.appendLine(`[daemon] reactor status: ${status}`);
                break;
            }
            case 'reactor/sedimentChunk':
                this.onDidReceiveSedimentChunkEmitter.fire(params as unknown as SedimentChunk);
                break;
            case 'reactor/synapse':
                this.onDidReceiveSynapseEmitter.fire(params as unknown as SynapseDescriptor);
                this.output.appendLine(`[daemon] synapse status: ${(params as SynapseDescriptor).status} (${(params as SynapseDescriptor).mode})`);
                break;
            case 'reactor/entropyState':
                this.onDidReceiveEntropyStateEmitter.fire(params as unknown as EntropyState);
                this.output.appendLine(`[daemon] entropy state: ${(params as EntropyState).status} (${Math.round(((params as EntropyState).decay_score ?? 0) * 100)}%)`);
                break;
            default:
                this.output.appendLine(`[daemon] unknown notification: ${method}`);
        }
    }

    private handleResponse(payload: Record<string, unknown>): void {
        const id = payload.id as number;
        const pending = this.pending.get(id);
        if (!pending) {
            return;
        }
        this.pending.delete(id);

        if (payload.error && typeof payload.error === 'object') {
            const err = payload.error as { message: string };
            pending.reject(new Error(err.message));
            return;
        }
        pending.resolve(payload.result);
    }

    private submitRequest<T>(method: string, params: object): Promise<T> {
        if (!this.daemonProcess?.stdin || this.daemonProcess.killed) {
            this.startDaemon();
        }
        if (!this.daemonProcess?.stdin) {
            return Promise.reject(new Error('daemon not available'));
        }

        const id = this.requestCounter++;
        const request = { jsonrpc: '2.0', id, method, params };

        return new Promise<T>((resolve, reject) => {
            this.pending.set(id, {
                resolve: resolve as (v: unknown) => void,
                reject,
            });
            this.daemonProcess?.stdin?.write(`${JSON.stringify(request)}\n`, (error) => {
                if (error) {
                    this.pending.delete(id);
                    reject(error);
                }
            });
        });
    }

    private rejectAllPending(error: Error): void {
        for (const [id, pending] of this.pending) {
            this.pending.delete(id);
            pending.reject(error);
        }
    }
}

function resolveDaemonBinaryPath(rootPath: string): string {
    const binary = process.platform === 'win32' ? 'chthonic-daemon.exe' : 'chthonic-daemon';
    return path.join(rootPath, 'native', 'target', 'release', binary);
}
