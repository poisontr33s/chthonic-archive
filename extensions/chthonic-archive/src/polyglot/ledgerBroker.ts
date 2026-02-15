import * as vscode from 'vscode';
import { EntropySettlement, LedgerReceipt } from './types';
import { RustLedgerHostClient } from './solanaLedger';

export type LedgerMode = 'bankrun' | 'validator';

export interface LedgerBrokerOptions {
    mode: LedgerMode;
    rpcUrl: string;
    autostartValidator: boolean;
    hostBinaryPath?: string;
    walletPath?: string;
    idlPath?: string;
}

interface LedgerBackend extends vscode.Disposable {
    start(rootPath: string): Promise<void>;
    commitEntropy(settlement: EntropySettlement): Promise<LedgerReceipt>;
}

export class LedgerBroker implements vscode.Disposable {
    private backend: LedgerBackend | null = null;

    constructor(
        private readonly output: vscode.OutputChannel,
        private readonly options: LedgerBrokerOptions,
    ) {}

    async start(rootPath: string): Promise<void> {
        this.backend = this.options.mode === 'bankrun'
            ? new PhantomBankrunBackend(this.output)
            : new RustValidatorBackend(this.output, this.options);
        await this.backend.start(rootPath);
    }

    async commitEntropy(settlement: EntropySettlement): Promise<LedgerReceipt> {
        if (!this.backend) {
            return {
                mode: 'offline',
                detail: 'LedgerBroker backend not initialized.',
            };
        }
        return this.backend.commitEntropy(settlement);
    }

    dispose(): void {
        this.backend?.dispose();
        this.backend = null;
    }
}

class PhantomBankrunBackend implements LedgerBackend {
    private sequence = 0;

    constructor(
        private readonly output: vscode.OutputChannel,
    ) {}

    async start(_rootPath: string): Promise<void> {
        this.output.appendLine('[ledger] phantom mode active (bankrun simulation).');
    }

    async commitEntropy(settlement: EntropySettlement): Promise<LedgerReceipt> {
        this.sequence += 1;
        const pseudoSignature = `bankrun-${settlement.rootHash.slice(0, 20)}-${this.sequence}`;
        return {
            mode: 'bankrun',
            txSignature: pseudoSignature,
            detail: 'In-memory bankrun simulation accepted the entropy settlement.',
        };
    }

    dispose(): void {}
}

class RustValidatorBackend implements LedgerBackend {
    private readonly client: RustLedgerHostClient;

    constructor(
        output: vscode.OutputChannel,
        private readonly options: LedgerBrokerOptions,
    ) {
        this.client = new RustLedgerHostClient(output);
    }

    async start(rootPath: string): Promise<void> {
        await this.client.start(rootPath, {
            rpcUrl: this.options.rpcUrl,
            autostartValidator: this.options.autostartValidator,
            hostBinaryPath: this.options.hostBinaryPath,
            walletPath: this.options.walletPath,
            idlPath: this.options.idlPath,
        });
    }

    async commitEntropy(settlement: EntropySettlement): Promise<LedgerReceipt> {
        return this.client.commitEntropy(settlement);
    }

    dispose(): void {
        this.client.dispose();
    }
}
