#!/usr/bin/env bun
// @SID: EXT_DAEMON_JSONL_SMOKE_V1
import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import { SynapseBridge } from '../src/reactor/synapseBridge';
import type { SedimentSynapseResult } from '../src/reactor/types';

const SLOT_MAGIC = 0x5359_4e43;

interface JsonRpcPayload {
    id?: number;
    method?: string;
    params?: unknown;
    result?: SedimentSynapseResult;
    error?: { message?: string };
}

interface SmokeResult {
    slots: number;
    bytes: number;
    firstChunkBytes: number;
    reported: SedimentSynapseResult;
}

const extensionRoot = path.resolve(import.meta.dir, '..');
const repoRoot = path.resolve(extensionRoot, '..', '..');
const daemonPath = resolveDaemonPath();
const request = {
    maxLayers: 10,
    maxFiles: 220,
    chunkSize: 64,
};

const native = await runNativeSmoke();
const bridge = await runBridgeSmoke(native.reported);

if (bridge.received !== native.reported.chunks_written) {
    throw new Error(`SynapseBridge received ${bridge.received} chunks; daemon reported ${native.reported.chunks_written}`);
}

console.log(JSON.stringify({
    status: 'passed',
    daemonPath,
    native,
    bridge,
}, null, 2));

function resolveDaemonPath(): string {
    const candidates = [
        process.env.CHTHONIC_DAEMON_BIN,
        path.join(extensionRoot, 'native', 'target', 'debug', process.platform === 'win32' ? 'chthonic-daemon.exe' : 'chthonic-daemon'),
        path.join(extensionRoot, 'native', 'target', 'release', process.platform === 'win32' ? 'chthonic-daemon.exe' : 'chthonic-daemon'),
    ].filter((candidate): candidate is string => Boolean(candidate));

    const found = candidates.find((candidate) => existsSync(candidate));
    if (!found) {
        throw new Error(`chthonic-daemon binary missing; checked ${candidates.join(', ')}`);
    }
    return found;
}

async function runNativeSmoke(): Promise<SmokeResult> {
    const child = spawn(daemonPath, ['--workspace', repoRoot, '--transport=jsonl'], {
        cwd: repoRoot,
        stdio: ['pipe', 'pipe', 'pipe'],
    });

    let slots = 0;
    let bytes = 0;
    let firstChunkBytes = 0;
    let reported: SedimentSynapseResult | null = null;
    let stderr = '';

    const lineReader = readline.createInterface({ input: child.stdout });
    lineReader.on('line', (line) => {
        const payload = JSON.parse(line.trim()) as JsonRpcPayload;
        if (payload.method === 'reactor/sedimentSlot') {
            const chunk = decodeSlot(payload.params);
            slots += 1;
            bytes += chunk.byteLength;
            firstChunkBytes ||= chunk.byteLength;
            return;
        }
        if (payload.id === 1) {
            if (payload.error) {
                throw new Error(payload.error.message ?? 'daemon JSONL request failed');
            }
            reported = payload.result ?? null;
        }
    });

    child.stderr.on('data', (chunk: Buffer) => {
        stderr += chunk.toString();
    });

    child.stdin.write(`${JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'reactor/sediment_synapse',
        params: {
            max_layers: request.maxLayers,
            max_files: request.maxFiles,
            chunk_size: request.chunkSize,
        },
    })}\n`);
    child.stdin.end();

    const exitCode = await new Promise<number | null>((resolve, reject) => {
        child.on('error', reject);
        child.on('exit', resolve);
    });
    lineReader.close();

    if (exitCode !== 0) {
        throw new Error(`daemon exited with code ${exitCode}: ${stderr.trim()}`);
    }
    if (!reported) {
        throw new Error('daemon did not report a reactor/sediment_synapse response');
    }
    if (slots === 0) {
        throw new Error('daemon emitted zero reactor/sedimentSlot notifications');
    }
    if (slots !== reported.chunks_written) {
        throw new Error(`daemon emitted ${slots} slots; response reported ${reported.chunks_written}`);
    }

    return { slots, bytes, firstChunkBytes, reported };
}

async function runBridgeSmoke(reported: SedimentSynapseResult): Promise<{
    received: number;
    bytes: number;
    firstChunkBytes: number;
    lane: unknown;
}> {
    const output = { appendLine: (line: string) => console.error(line) };
    const lanes: unknown[] = [];
    const bridge = new SynapseBridge(output, extensionRoot, 'jsonl', {
        workspaceRoot: repoRoot,
        daemonPath,
        headlessVulkan: false,
        laneRegistry: { set: (state: unknown) => lanes.push(state) },
    });

    const chunks: Uint8Array[] = [];
    const received = await bridge.drain(
        reported,
        (chunk) => chunks.push(chunk),
        request,
    );
    bridge.dispose();

    if (received === 0) {
        throw new Error('SynapseBridge.drain received zero chunks');
    }

    return {
        received,
        bytes: chunks.reduce((sum, chunk) => sum + chunk.byteLength, 0),
        firstChunkBytes: chunks[0]?.byteLength ?? 0,
        lane: lanes.at(-1) ?? null,
    };
}

function decodeSlot(value: unknown): Buffer {
    if (!value || typeof value !== 'object') {
        throw new Error('sedimentSlot params missing');
    }
    const params = value as {
        encoding?: unknown;
        payload_base64?: unknown;
        byte_len?: unknown;
    };
    if (params.encoding !== 'base64' || typeof params.payload_base64 !== 'string') {
        throw new Error('sedimentSlot payload is not base64');
    }

    const bytes = Buffer.from(params.payload_base64, 'base64');
    if (typeof params.byte_len === 'number' && bytes.byteLength !== params.byte_len) {
        throw new Error(`sedimentSlot byte length mismatch: ${bytes.byteLength} != ${params.byte_len}`);
    }
    if (bytes.readUInt32LE(0) !== SLOT_MAGIC) {
        throw new Error('sedimentSlot magic mismatch');
    }
    return bytes;
}
