import * as fs from 'fs';
import { createRequire } from 'module';
import * as path from 'path';
import * as vscode from 'vscode';
import type { SedimentSynapseResult, SynapseDescriptor } from './types';

interface SynapseBinding {
    SynapseReader: new (shmId: string, eventName?: string) => SynapseReaderInstance;
}

interface SynapseReaderInstance {
    wait_for_signal(timeoutMs: number): boolean;
    read_chunk(): Buffer | null;
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
    ) {
        this.transportMode = normalizeTransportMode(transportMode);
    }

    updateDescriptor(descriptor: SynapseDescriptor): void {
        this.descriptor = descriptor;
        if (this.transportMode === 'jsonl') {
            this.output.appendLine('[synapse] disabled by transport=jsonl');
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
            return false;
        }
        return this.reader !== null && this.descriptor?.status === 'ready' && this.descriptor.mode === 'shared_memory';
    }

    async drain(
        response: SedimentSynapseResult,
        onChunk: (chunk: Uint8Array) => void,
    ): Promise<number> {
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

    private ensureBindingLoaded(): SynapseBinding {
        if (this.binding) {
            return this.binding;
        }

        const candidates = [
            path.join(this.extensionRoot, 'src', 'reactor', 'synapse.node'),
            path.join(this.extensionRoot, 'native', 'target', 'release', 'synapse.node'),
        ];
        const existing = candidates.find((candidate) => fs.existsSync(candidate));
        if (!existing) {
            throw new Error(`synapse.node not found in ${candidates.join(', ')}`);
        }

        const req = createRequire(__filename);
        this.binding = req(existing) as SynapseBinding;
        return this.binding;
    }
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
