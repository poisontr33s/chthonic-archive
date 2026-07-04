// @SID: EXT_SYNAPSEBRIDGE_V1
import { spawn } from 'child_process';
import * as fs from 'fs';
import { createRequire } from 'module';
import * as path from 'path';
import * as readline from 'readline';
import type * as vscode from 'vscode';
import type { SedimentSynapseResult, SynapseDescriptor } from './types';
import type { LaneRegistry } from '../runtime/laneState';

interface SynapseBinding {
    SynapseReader: new (shmId: string, eventName?: string) => SynapseReaderInstance;
}

interface SynapseReaderInstance {
    wait_for_signal(timeoutMs: number): boolean;
    read_chunk(): Buffer | null;
}

export interface SynapseDrainRequest {
    maxLayers: number;
    maxFiles: number;
    chunkSize: number;
}

interface SynapseBridgeOptions {
    workspaceRoot?: string | null;
    daemonPath?: string;
    headlessVulkan?: boolean;
    laneRegistry?: LaneRegistry;
}

export class SynapseBridge implements vscode.Disposable {
    private binding: SynapseBinding | null = null;
    private reader: SynapseReaderInstance | null = null;
    private descriptor: SynapseDescriptor | null = null;
    private readonly transportMode: 'auto' | 'shared_memory' | 'jsonl';

    constructor(
        private readonly output: vscode.OutputChannel,
        private readonly extensionRoot: string,
        transportMode: string,
        private readonly options: SynapseBridgeOptions = {},
    ) {
        this.transportMode = normalizeTransportMode(transportMode);
    }

    updateDescriptor(descriptor: SynapseDescriptor): void {
        this.descriptor = descriptor;
        if (this.transportMode === 'jsonl' || descriptor.mode === 'jsonl') {
            this.markJsonlFallback();
            this.output.appendLine('[synapse] JSONL fallback active');
            return;
        }
        if (descriptor.status !== 'ready' || descriptor.mode !== 'shared_memory' || !descriptor.shm_id) {
            this.output.appendLine(`[synapse] unavailable: ${descriptor.reason ?? descriptor.status}`);
            return;
        }

        try {
            const binding = this.ensureBindingLoaded();
            this.reader = new binding.SynapseReader(descriptor.shm_id, descriptor.event_name ?? undefined);
            this.output.appendLine(`[synapse] connected (shm=${descriptor.shm_id})`);
        } catch (error) {
            this.reader = null;
            this.output.appendLine(`[synapse] init failed, falling back to JSONL: ${stringifyError(error)}`);
        }
    }

    isReady(): boolean {
        if (this.transportMode === 'jsonl') {
            return Boolean(this.options.workspaceRoot && this.resolveJsonlDaemonPath());
        }
        return this.reader !== null && this.descriptor?.status === 'ready' && this.descriptor.mode === 'shared_memory';
    }

    async drain(
        response: SedimentSynapseResult,
        onChunk: (chunk: Uint8Array) => void,
        request?: SynapseDrainRequest,
    ): Promise<number> {
        if (this.transportMode === 'jsonl' || response.transport === 'jsonl') {
            return this.drainJsonl(response, onChunk, request);
        }
        if (!this.reader || response.transport !== 'shared_memory') {
            return 0;
        }

        const expected = Math.max(0, response.chunks_written ?? response.total_chunks ?? 0);
        if (expected === 0) {
            return 0;
        }

        let received = 0;
        const started = Date.now();
        while (received < expected && Date.now() - started < 4000) {
            const signaled = this.reader.wait_for_signal(120);
            if (!signaled) {
                await yieldTick();
                continue;
            }

            while (true) {
                const payload = this.reader.read_chunk();
                if (!payload || payload.byteLength === 0) {
                    break;
                }
                const binary = new Uint8Array(payload.buffer, payload.byteOffset, payload.byteLength);
                const copied = new Uint8Array(binary.byteLength);
                copied.set(binary);
                onChunk(copied);
                received += 1;
                if (received >= expected) {
                    break;
                }
            }

            await yieldTick();
        }

        if (received < expected) {
            this.output.appendLine(`[synapse] partial drain: ${received}/${expected}`);
        }
        return received;
    }

    dispose(): void {
        this.reader = null;
    }

    private async drainJsonl(
        response: SedimentSynapseResult,
        onChunk: (chunk: Uint8Array) => void,
        request?: SynapseDrainRequest,
    ): Promise<number> {
        this.markJsonlFallback();

        if (!request) {
            this.output.appendLine('[synapse] JSONL drain skipped: sediment request metadata missing');
            return 0;
        }

        const workspaceRoot = this.options.workspaceRoot;
        const daemonPath = this.resolveJsonlDaemonPath();
        if (!workspaceRoot || !daemonPath) {
            this.output.appendLine('[synapse] JSONL drain unavailable: daemon path or workspace root missing');
            return 0;
        }

        const args = ['--workspace', workspaceRoot, '--transport=jsonl'];
        if (this.options.headlessVulkan) {
            args.push('--headless-vulkan');
        }

        const child = spawn(daemonPath, args, {
            cwd: workspaceRoot,
            env: process.env,
            stdio: ['pipe', 'pipe', 'pipe'],
        });

        let received = 0;
        let reported: SedimentSynapseResult | null = null;

        return new Promise<number>((resolve, reject) => {
            let settled = false;
            const lineReader = readline.createInterface({ input: child.stdout });
            let timeout: ReturnType<typeof setTimeout> | undefined;

            const cleanup = (): void => {
                if (timeout) {
                    clearTimeout(timeout);
                }
                lineReader.close();
            };

            const finish = (value: number): void => {
                if (settled) return;
                settled = true;
                cleanup();
                resolve(value);
            };

            const finishError = (error: Error): void => {
                if (settled) return;
                settled = true;
                cleanup();
                reject(error);
            };

            timeout = setTimeout(() => {
                child.kill();
                finishError(new Error('JSONL synapse drain timed out'));
            }, 6000);

            lineReader.on('line', (line) => {
                const trimmed = line.trim();
                if (!trimmed) return;

                let payload: Record<string, unknown>;
                try {
                    payload = JSON.parse(trimmed) as Record<string, unknown>;
                } catch (error) {
                    this.output.appendLine(`[synapse] invalid JSONL chunk: ${stringifyError(error)}`);
                    return;
                }

                if (payload.method === 'reactor/sedimentSlot') {
                    const chunk = decodeJsonlSlot(payload.params);
                    if (chunk) {
                        onChunk(chunk);
                        received += 1;
                    }
                    return;
                }

                if (payload.id === 1) {
                    if (payload.error && typeof payload.error === 'object') {
                        const error = payload.error as { message?: string };
                        finishError(new Error(error.message ?? 'JSONL synapse request failed'));
                        return;
                    }
                    reported = payload.result as SedimentSynapseResult;
                }
            });

            child.stderr.on('data', (chunk: Buffer) => {
                this.output.appendLine(`[synapse] JSONL daemon: ${chunk.toString().trimEnd()}`);
            });
            child.on('error', (error) => finishError(error));
            child.on('exit', (code) => {
                const finalReport = reported ?? response;
                const expected = Math.max(0, finalReport.chunks_written ?? finalReport.total_chunks ?? 0);
                if (received < expected) {
                    this.output.appendLine(`[synapse] JSONL partial drain: ${received}/${expected}`);
                }
                if (code && !reported) {
                    finishError(new Error(`JSONL synapse daemon exited with code ${code}`));
                    return;
                }
                finish(received);
            });

            const body = {
                jsonrpc: '2.0',
                id: 1,
                method: 'reactor/sediment_synapse',
                params: {
                    max_layers: request.maxLayers,
                    max_files: request.maxFiles,
                    chunk_size: request.chunkSize,
                },
            };
            child.stdin.write(`${JSON.stringify(body)}\n`, (error) => {
                if (error) {
                    finishError(error);
                } else {
                    child.stdin.end();
                }
            });
        });
    }

    private markJsonlFallback(): void {
        this.options.laneRegistry?.set({
            name: 'synapseShm',
            state: 'DEGRADED',
            reason: 'transport=jsonl fallback',
        });
    }

    private resolveJsonlDaemonPath(): string | null {
        if (this.options.daemonPath && fs.existsSync(this.options.daemonPath)) {
            return this.options.daemonPath;
        }

        const workspaceRoot = this.options.workspaceRoot;
        if (!workspaceRoot) {
            return null;
        }

        const binary = process.platform === 'win32' ? 'chthonic-daemon.exe' : 'chthonic-daemon';
        const candidate = path.join(workspaceRoot, 'native', 'target', 'release', binary);
        return fs.existsSync(candidate) ? candidate : null;
    }

    private ensureBindingLoaded(): SynapseBinding {
        if (this.binding) {
            return this.binding;
        }

        const platformArtifact = `synapse-${process.platform}-${process.arch}.node`;
        const candidates = [
            path.join(this.extensionRoot, 'native', 'dist', platformArtifact),
            path.join(this.extensionRoot, 'src', 'reactor', 'synapse.node'),
            path.join(this.extensionRoot, 'native', 'target', 'release', 'synapse.node'),
        ];
        const existing = candidates.find((candidate) => fs.existsSync(candidate));
        if (!existing) {
            throw new Error(`synapse.node not found in ${candidates.join(', ')}`);
        }

        const req = createRequire(path.join(this.extensionRoot, 'package.json'));
        this.binding = req(existing) as SynapseBinding;
        return this.binding;
    }
}

function decodeJsonlSlot(value: unknown): Uint8Array | null {
    if (!value || typeof value !== 'object') {
        return null;
    }
    const params = value as {
        encoding?: unknown;
        payload_base64?: unknown;
        byte_len?: unknown;
    };
    if (params.encoding !== 'base64' || typeof params.payload_base64 !== 'string') {
        return null;
    }

    const payload = Buffer.from(params.payload_base64, 'base64');
    if (typeof params.byte_len === 'number' && payload.byteLength !== params.byte_len) {
        return null;
    }

    const copied = new Uint8Array(payload.byteLength);
    copied.set(payload);
    return copied;
}

function normalizeTransportMode(value: string): 'auto' | 'shared_memory' | 'jsonl' {
    const normalized = value.trim().toLowerCase();
    if (normalized === 'shared_memory') {
        return 'shared_memory';
    }
    if (normalized === 'jsonl') {
        return 'jsonl';
    }
    return 'auto';
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}

async function yieldTick(): Promise<void> {
    await new Promise<void>((resolve) => setTimeout(resolve, 0));
}
