// @SID: EXT_SOLANALEDGER_V1
import * as fs from 'fs';
import * as fsp from 'fs/promises';
import * as path from 'path';
import { spawn } from 'child_process';
import * as vscode from 'vscode';
import { createJsonlDecoder } from './jsonl';
import type {
    EntropySettlement,
    LedgerReceipt,
    RustLedgerErrorResponse,
    RustLedgerRequest,
    RustLedgerSuccessResponse,
} from './types';

export interface RustLedgerOptions {
    rpcUrl: string;
    autostartValidator: boolean;
    hostBinaryPath?: string;
    walletPath?: string;
    idlPath?: string;
}

interface PendingRequest {
    resolve: (receipt: LedgerReceipt) => void;
    reject: (error: Error) => void;
}

export class RustLedgerHostClient implements vscode.Disposable {
    private rootPath: string | null = null;
    private options: RustLedgerOptions = {
        rpcUrl: 'http://127.0.0.1:8899',
        autostartValidator: false,
    };
    private ledgerFilePath: string | null = null;
    private validatorProcess: import('child_process').ChildProcess | null = null;
    private hostProcess: import('child_process').ChildProcess | null = null;
    private requestCounter = 1;
    private readonly pending = new Map<number, PendingRequest>();

    constructor(
        private readonly output: vscode.OutputChannel,
    ) {}

    async start(rootPath: string, options: RustLedgerOptions): Promise<void> {
        this.rootPath = rootPath;
        this.options = options;

        const ledgerDir = path.join(rootPath, '.chthonic', 'ledger');
        await fsp.mkdir(ledgerDir, { recursive: true });
        this.ledgerFilePath = path.join(ledgerDir, 'entropy-settlements.jsonl');

        if (options.autostartValidator) {
            this.startValidator();
        }
        this.startHostProcess();
    }

    async commitEntropy(settlement: EntropySettlement): Promise<LedgerReceipt> {
        if (!this.rootPath || !this.ledgerFilePath) {
            return {
                mode: 'offline',
                detail: 'Ledger host not started',
            };
        }

        const payload = {
            ...settlement,
            rpcUrl: this.options.rpcUrl,
            recordedAt: Date.now(),
        };

        let receipt: LedgerReceipt = {
            mode: 'offline',
            detail: 'Rust ledger host unavailable; persisted settlement locally.',
        };

        try {
            receipt = await this.submitToHost(settlement);
        } catch (error) {
            this.output.appendLine(`[ledger-rust] submit failed: ${stringifyError(error)}`);
        }

        await fsp.appendFile(this.ledgerFilePath, `${JSON.stringify({ ...payload, receipt })}\n`, 'utf8');
        return receipt;
    }

    dispose(): void {
        for (const [id, pending] of this.pending) {
            pending.reject(new Error(`request ${id} cancelled`));
        }
        this.pending.clear();

        this.hostProcess?.kill();
        this.hostProcess = null;

        this.validatorProcess?.kill();
        this.validatorProcess = null;
    }

    private startHostProcess(): void {
        if (!this.rootPath || this.hostProcess) {
            return;
        }

        const binaryPath = resolveLedgerBinaryPath(this.rootPath, this.options.hostBinaryPath);
        const walletPath = this.options.walletPath ?? path.join(this.rootPath, '.chthonic', 'wallets', 'payer.json');
        const idlPath = this.options.idlPath ?? path.join(this.rootPath, '.chthonic', 'wallets', 'entropy_ledger.json');

        this.hostProcess = spawn(binaryPath, [
            '--wallet',
            walletPath,
            '--idl',
            idlPath,
            '--rpc-url',
            this.options.rpcUrl,
        ], {
            cwd: this.rootPath,
            stdio: ['pipe', 'pipe', 'pipe'],
        });

        const decoder = createJsonlDecoder(
            (payload) => this.handleHostPayload(payload),
            (error) => this.output.appendLine(`[ledger-rust] invalid JSON payload: ${error.message}`),
        );

        this.hostProcess.stdout?.on('data', (chunk: Buffer) => decoder.push(chunk));
        this.hostProcess.stderr?.on('data', (chunk: Buffer) => {
            this.output.appendLine(`[ledger-rust] ${chunk.toString().trimEnd()}`);
        });
        this.hostProcess.on('error', (error) => {
            this.output.appendLine(`[ledger-rust] failed to spawn host: ${error.message}`);
            this.rejectAllPending(new Error(`host spawn failed: ${error.message}`));
            this.hostProcess = null;
        });
        this.hostProcess.on('exit', (code) => {
            decoder.flush();
            this.output.appendLine(`[ledger-rust] host exited with code ${code ?? -1}`);
            this.rejectAllPending(new Error('ledger host exited'));
            this.hostProcess = null;
        });
    }

    private async submitToHost(settlement: EntropySettlement): Promise<LedgerReceipt> {
        if (!this.hostProcess || this.hostProcess.killed) {
            this.startHostProcess();
        }
        if (!this.hostProcess?.stdin || this.hostProcess.killed) {
            return {
                mode: 'offline',
                detail: 'Rust host binary is missing or not executable.',
            };
        }

        const id = this.requestCounter++;
        const request: RustLedgerRequest = {
            jsonrpc: '2.0',
            id,
            method: 'submit_entropy',
            params: {
                entropy_score: Math.max(0, Math.round((settlement.leafCount * 17) + 13)),
                merkle_root: settlement.rootHash,
                leaf_count: settlement.leafCount,
                reason: settlement.reason,
            },
        };

        const response = await new Promise<LedgerReceipt>((resolve, reject) => {
            this.pending.set(id, { resolve, reject });
            this.hostProcess?.stdin?.write(`${JSON.stringify(request)}\n`, (error) => {
                if (!error) {
                    return;
                }
                this.pending.delete(id);
                reject(error);
            });
        });

        return response;
    }

    private handleHostPayload(payload: Record<string, unknown>): void {
        const rawId = payload.id;
        if (typeof rawId !== 'number') {
            return;
        }
        const pending = this.pending.get(rawId);
        if (!pending) {
            return;
        }
        this.pending.delete(rawId);

        if (payload.error && typeof payload.error === 'object') {
            const errorPayload = payload as unknown as RustLedgerErrorResponse;
            pending.resolve({
                mode: 'offline',
                detail: `Rust ledger error ${errorPayload.error.code}: ${errorPayload.error.message}`,
            });
            return;
        }

        const success = payload as unknown as RustLedgerSuccessResponse;
        pending.resolve({
            mode: 'validator-rust',
            txSignature: success.result.signature,
            detail: `Rust anchor-client submission accepted${success.result.slot ? ` (slot ${success.result.slot})` : ''}.`,
        });
    }

    private rejectAllPending(error: Error): void {
        for (const [id, pending] of this.pending) {
            this.pending.delete(id);
            pending.reject(error);
        }
    }

    private startValidator(): void {
        if (!this.rootPath || this.validatorProcess) {
            return;
        }

        const solanaValidator = resolveValidatorBinaryPath(this.rootPath);
        const port = parsePort(this.options.rpcUrl) ?? 8899;
        const ledgerDir = path.join(this.rootPath, '.chthonic', 'solana-ledger');

        this.validatorProcess = spawn(solanaValidator, [
            '--ledger',
            ledgerDir,
            '--rpc-port',
            String(port),
            '--reset',
            '--quiet',
        ], {
            cwd: this.rootPath,
            stdio: ['ignore', 'pipe', 'pipe'],
        });

        this.validatorProcess.stdout?.on('data', (chunk: Buffer) => {
            this.output.appendLine(`[solana] ${chunk.toString().trimEnd()}`);
        });
        this.validatorProcess.stderr?.on('data', (chunk: Buffer) => {
            this.output.appendLine(`[solana] ${chunk.toString().trimEnd()}`);
        });
        this.validatorProcess.on('error', (error) => {
            this.output.appendLine(`[solana] validator spawn error: ${error.message}`);
            this.validatorProcess = null;
        });
        this.validatorProcess.on('exit', (code) => {
            this.output.appendLine(`[solana] validator exited with code ${code ?? -1}`);
            this.validatorProcess = null;
        });
    }
}

function resolveLedgerBinaryPath(rootPath: string, overridePath?: string): string {
    if (overridePath) {
        return overridePath;
    }
    const binary = process.platform === 'win32' ? 'entropy-ledger-host.exe' : 'entropy-ledger-host';
    return path.join(rootPath, 'native', 'target', 'release', binary);
}

function resolveValidatorBinaryPath(rootPath: string): string {
    const binary = process.platform === 'win32' ? 'solana-test-validator.exe' : 'solana-test-validator';
    const local = path.join(rootPath, '.chthonic', 'bin', binary);
    if (fs.existsSync(local)) {
        return local;
    }
    return process.platform === 'win32' ? 'solana-test-validator' : binary;
}

function parsePort(rpcUrl: string): number | null {
    try {
        const parsed = new URL(rpcUrl);
        if (!parsed.port) {
            return null;
        }
        const value = Number(parsed.port);
        return Number.isFinite(value) ? value : null;
    } catch {
        return null;
    }
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}
