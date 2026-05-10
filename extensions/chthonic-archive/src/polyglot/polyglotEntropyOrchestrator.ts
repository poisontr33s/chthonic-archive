// @SID: EXT_POLYGLOTENTROPYORCHESTRATOR_V1
import * as fs from 'fs/promises';
import * as path from 'path';
import * as vscode from 'vscode';
import { EntropyMerkleAccumulator } from './merkleAccumulator';
import { PolyglotBroker } from './polyglotBroker';
import { LedgerBroker, type LedgerMode } from './ledgerBroker';
import type {
    LedgerReceipt,
    LoreEvent,
    PolyglotScanReason,
    RuffFileSummary,
    RuffSummaryEvent,
} from './types';
import { EntropyWorkerClient } from '../entropy/entropyWorkerClient';
import type { LaneRegistry, RuntimeLaneStateKind } from '../runtime/laneState';

interface PolyglotEntropyOrchestratorOptions {
    enabled: boolean;
    pythonScanIntervalMs: number;
    settleDebounceMs: number;
    ledgerMode: LedgerMode;
    solanaRpcUrl: string;
    solanaAutostartValidator: boolean;
    solanaLedgerHostBinaryPath?: string;
    solanaWalletPath?: string;
    solanaIdlPath?: string;
    laneRegistry?: LaneRegistry;
}

interface TooltipAugment {
    ruffViolations: number;
    ruffCodeSummary?: string;
    loreLine?: string;
}

type DecorationRefreshFn = (uris: vscode.Uri[]) => void;

export class PolyglotEntropyOrchestrator implements vscode.Disposable {
    private readonly broker: PolyglotBroker;
    private readonly merkle = new EntropyMerkleAccumulator();
    private readonly ledger: LedgerBroker;
    private readonly tooltipAugments = new Map<string, TooltipAugment>();

    private rootPath: string | null = null;
    private scanTimer: NodeJS.Timeout | null = null;
    private settleTimer: NodeJS.Timeout | null = null;
    private gitPollTimer: NodeJS.Timeout | null = null;
    private gitHeadSnapshot: string | null = null;
    private pendingSettleReason: PolyglotScanReason | null = null;
    private readonly disposables: vscode.Disposable[] = [];

    constructor(
        private readonly output: vscode.OutputChannel,
        private readonly workerClient: EntropyWorkerClient,
        private readonly options: PolyglotEntropyOrchestratorOptions,
        private readonly requestDecorationRefresh: DecorationRefreshFn,
    ) {
        this.broker = new PolyglotBroker(output);
        this.ledger = new LedgerBroker(output, {
            mode: this.options.ledgerMode,
            rpcUrl: this.options.solanaRpcUrl,
            autostartValidator: this.options.solanaAutostartValidator,
            hostBinaryPath: this.options.solanaLedgerHostBinaryPath,
            walletPath: this.options.solanaWalletPath,
            idlPath: this.options.solanaIdlPath,
        });

        this.disposables.push(
            this.broker.onDidReceiveRuff((event) => this.applyRuffSummary(event)),
            this.broker.onDidReceiveLore((event) => this.applyLore(event)),
            this.workerClient.onDidUpdateRecords((uris) => this.captureEntropyLeaves(uris)),
        );
    }

    async start(rootPath: string): Promise<void> {
        this.rootPath = rootPath;
        this.emitPolyglotLane(this.options.enabled ? 'LIVE' : 'DISABLED', this.options.enabled ? 'polyglot entropy lane armed' : 'polyglot sidecars disabled');
        this.emitSettlementLane(this.options.enabled ? 'READY' : 'DISABLED', this.options.enabled ? 'awaiting entropy leaves' : 'polyglot sidecars disabled');
        this.emitLedgerLane(this.options.enabled ? 'READY' : 'DISABLED', initialLedgerReason(this.options));
        if (!this.options.enabled) {
            return;
        }

        this.broker.start(rootPath);
        await this.ledger.start(rootPath);
        this.emitLedgerLane('READY', this.options.ledgerMode === 'validator' ? 'Rust validator backend initialized' : 'bankrun simulation initialized');
        this.broker.requestScan({
            type: 'scan',
            reason: 'manual',
            root: rootPath,
        });
        this.startScanLoop();
        this.startGitWatcher();
    }

    onDidSaveDocument(document: vscode.TextDocument): void {
        if (!this.rootPath || !this.options.enabled || document.uri.scheme !== 'file') {
            return;
        }
        const relative = toRelativePath(this.rootPath, document.uri.fsPath);
        if (!relative) {
            return;
        }
        this.broker.requestScan({
            type: 'scan',
            reason: 'save',
            root: this.rootPath,
            files: [relative],
        });
        this.scheduleSettlement('save');
    }

    requestManualScan(): void {
        if (!this.rootPath || !this.options.enabled) {
            return;
        }
        this.emitPolyglotLane('LIVE', 'manual scan requested');
        this.broker.requestScan({
            type: 'scan',
            reason: 'manual',
            root: this.rootPath,
        });
    }

    getTooltipFragments(uri: vscode.Uri): string[] {
        if (!this.rootPath || uri.scheme !== 'file') {
            return [];
        }
        const relative = toRelativePath(this.rootPath, uri.fsPath);
        if (!relative) {
            return [];
        }

        const augment = this.tooltipAugments.get(relative);
        if (!augment) {
            return [];
        }
        const output: string[] = [];
        if (augment.ruffViolations > 0) {
            output.push(`Ruff ${augment.ruffViolations} violation${augment.ruffViolations === 1 ? '' : 's'}`);
            if (augment.ruffCodeSummary) {
                output.push(`Codes ${augment.ruffCodeSummary}`);
            }
        }
        if (augment.loreLine) {
            output.push(augment.loreLine);
        }
        return output;
    }

    dispose(): void {
        if (this.scanTimer) {
            clearInterval(this.scanTimer);
            this.scanTimer = null;
        }
        if (this.settleTimer) {
            clearTimeout(this.settleTimer);
            this.settleTimer = null;
        }
        if (this.gitPollTimer) {
            clearInterval(this.gitPollTimer);
            this.gitPollTimer = null;
        }
        this.broker.dispose();
        this.ledger.dispose();
        this.disposables.forEach((entry) => entry.dispose());
        this.disposables.length = 0;
    }

    private captureEntropyLeaves(uris: vscode.Uri[]): void {
        if (!this.options.enabled) {
            return;
        }
        let changedLeafCount = 0;
        for (const uri of uris) {
            const record = this.workerClient.getRecord(uri);
            if (!record) {
                continue;
            }
            const augment = this.tooltipAugments.get(record.path);
            const changed = this.merkle.upsert({
                path: record.path,
                entropy: record.entropy,
                complexity: record.complexity,
                debt: record.debt,
                freshness: record.freshness,
                ruffViolations: augment?.ruffViolations ?? 0,
                updatedAt: Date.now(),
            });
            if (changed) {
                changedLeafCount += 1;
            }
        }

        if (changedLeafCount > 0) {
            this.scheduleSettlement('interval');
        }
    }

    private applyRuffSummary(event: RuffSummaryEvent): void {
        if (!this.rootPath || !this.options.enabled) {
            return;
        }
        const files: RuffFileSummary[] = event.files;
        const changedUris: vscode.Uri[] = [];
        let changedLeafCount = 0;
        for (const summary of files) {
            const existing = this.tooltipAugments.get(summary.path);
            const next: TooltipAugment = {
                ruffViolations: summary.violations,
                ruffCodeSummary: formatRuffCodeSummary(summary.byCode),
                loreLine: existing?.loreLine,
            };
            this.tooltipAugments.set(summary.path, next);

            const uri = vscode.Uri.file(path.join(this.rootPath, summary.path));
            changedUris.push(uri);

            const record = this.workerClient.getRecord(uri);
            if (record) {
                const changed = this.merkle.upsert({
                    path: record.path,
                    entropy: record.entropy,
                    complexity: record.complexity,
                    debt: record.debt,
                    freshness: record.freshness,
                    ruffViolations: summary.violations,
                    updatedAt: Date.now(),
                });
                if (changed) {
                    changedLeafCount += 1;
                }

                if (record.entropy >= 0.45 || summary.violations > 0) {
                    this.broker.requestLore({
                        type: 'lore-request',
                        root: this.rootPath,
                        path: summary.path,
                        entropy: record.entropy,
                        violations: summary.violations,
                    });
                }
            }
        }
        if (changedUris.length > 0) {
            this.requestDecorationRefresh(changedUris);
        }
        if (changedLeafCount > 0 || this.merkle.hasDirty()) {
            this.scheduleSettlement(event.reason);
        }
    }

    private applyLore(event: LoreEvent): void {
        if (!this.rootPath || !this.options.enabled) {
            return;
        }
        if (event.root !== this.rootPath) {
            return;
        }
        const existing = this.tooltipAugments.get(event.path);
        this.tooltipAugments.set(event.path, {
            ruffViolations: existing?.ruffViolations ?? event.violations,
            ruffCodeSummary: existing?.ruffCodeSummary,
            loreLine: event.line,
        });
        this.requestDecorationRefresh([
            vscode.Uri.file(path.join(this.rootPath, event.path)),
        ]);
    }

    private startScanLoop(): void {
        if (this.scanTimer || !this.rootPath) {
            return;
        }
        const interval = Math.max(this.options.pythonScanIntervalMs, 10_000);
        this.scanTimer = setInterval(() => {
            if (!this.rootPath) {
                return;
            }
            this.broker.requestScan({
                type: 'scan',
                reason: 'interval',
                root: this.rootPath,
            });
        }, interval);
    }

    private startGitWatcher(): void {
        if (!this.rootPath || this.gitPollTimer) {
            return;
        }
        this.gitHeadSnapshot = null;
        this.gitPollTimer = setInterval(async () => {
            if (!this.rootPath) {
                return;
            }
            const next = await readGitHead(this.rootPath);
            if (!next) {
                return;
            }
            if (!this.gitHeadSnapshot) {
                this.gitHeadSnapshot = next;
                return;
            }
            if (next !== this.gitHeadSnapshot) {
                this.gitHeadSnapshot = next;
                this.output.appendLine('[polyglot] git HEAD changed, scheduling Merkle settlement.');
                if (this.rootPath) {
                    this.broker.requestScan({
                        type: 'scan',
                        reason: 'commit',
                        root: this.rootPath,
                    });
                }
                this.scheduleSettlement('commit');
            }
        }, 6_000);
    }

    private scheduleSettlement(reason: PolyglotScanReason): void {
        if (!this.options.enabled) {
            return;
        }
        this.pendingSettleReason = nextSettlementReason(this.pendingSettleReason, reason);
        this.emitSettlementLane(
            'LIVE',
            `pending ${this.pendingSettleReason} settlement`,
            `${Math.max(this.options.settleDebounceMs, 300)}ms debounce`,
        );
        if (this.settleTimer) {
            clearTimeout(this.settleTimer);
        }
        this.settleTimer = setTimeout(() => {
            this.settleTimer = null;
            void this.flushSettlement();
        }, Math.max(this.options.settleDebounceMs, 300));
    }

    private async flushSettlement(): Promise<void> {
        const reason = this.pendingSettleReason ?? 'manual';
        this.pendingSettleReason = null;

        const settlement = this.merkle.settle(reason);
        if (!settlement) {
            this.emitSettlementLane('READY', `no dirty Merkle leaves after ${reason}`);
            return;
        }

        this.emitSettlementLane(
            'LIVE',
            `committing ${settlement.rootHash.slice(0, 16)}...`,
            `${settlement.leafCount} leaves via ${this.options.ledgerMode}`,
        );

        let receipt: LedgerReceipt;
        try {
            receipt = await this.ledger.commitEntropy(settlement);
        } catch (error) {
            const detail = stringifyError(error);
            this.emitSettlementLane('DEGRADED', `settlement failed: ${detail}`);
            this.emitLedgerLane('DEGRADED', detail);
            this.output.appendLine(`[polyglot] settlement failed: ${detail}`);
            return;
        }
        this.emitSettlementLane(
            'READY',
            `settled ${settlement.rootHash.slice(0, 16)}... leaves=${settlement.leafCount}`,
            receipt.txSignature ? `tx ${receipt.txSignature}` : receipt.detail,
        );
        this.emitLedgerReceipt(receipt);
        const message = [
            `[polyglot] settled Merkle root ${settlement.rootHash.slice(0, 16)}...`,
            `leaves=${settlement.leafCount}`,
            `mode=${receipt.mode}`,
        ];
        if (receipt.txSignature) {
            message.push(`tx=${receipt.txSignature}`);
        }
        message.push(`detail=${receipt.detail}`);
        this.output.appendLine(message.join(' '));
    }

    private emitPolyglotLane(state: RuntimeLaneStateKind, reason?: string, localAction?: string): void {
        this.options.laneRegistry?.set({
            name: 'polyglot-sidecars',
            state,
            reason,
            localAction,
        });
    }

    private emitSettlementLane(state: RuntimeLaneStateKind, reason?: string, localAction?: string): void {
        this.options.laneRegistry?.set({
            name: 'entropy-settlement',
            state,
            reason,
            localAction,
        });
    }

    private emitLedgerReceipt(receipt: LedgerReceipt): void {
        switch (receipt.mode) {
            case 'validator-rust':
                this.emitLedgerLane('LIVE', receipt.txSignature ?? receipt.detail, receipt.detail);
                return;
            case 'bankrun':
                this.emitLedgerLane('READY', receipt.txSignature ?? 'bankrun simulation accepted', receipt.detail);
                return;
            case 'offline':
            default:
                this.emitLedgerLane('DEGRADED', receipt.detail);
        }
    }

    private emitLedgerLane(state: RuntimeLaneStateKind, reason?: string, localAction?: string): void {
        this.options.laneRegistry?.set({
            name: 'solana-ledger',
            state,
            reason,
            localAction,
        });
    }
}

async function readGitHead(rootPath: string): Promise<string | null> {
    const gitDir = path.join(rootPath, '.git');
    const headPath = path.join(gitDir, 'HEAD');
    let head = '';
    try {
        head = await fs.readFile(headPath, 'utf8');
    } catch {
        return null;
    }
    const trimmed = head.trim();
    if (!trimmed) {
        return null;
    }
    if (!trimmed.startsWith('ref:')) {
        return trimmed;
    }

    const refPath = trimmed.slice(4).trim();
    const absoluteRef = path.join(gitDir, refPath);
    try {
        const refValue = await fs.readFile(absoluteRef, 'utf8');
        return `ref:${refPath}:${refValue.trim()}`;
    } catch {
        return `ref:${refPath}:missing`;
    }
}

function toRelativePath(rootPath: string, absolutePath: string): string | null {
    const relative = path.relative(rootPath, absolutePath);
    if (!relative || relative.startsWith('..') || path.isAbsolute(relative)) {
        return null;
    }
    return relative.replace(/\\/g, '/');
}

function formatRuffCodeSummary(byCode: Record<string, number>): string | undefined {
    const entries = Object.entries(byCode)
        .filter((entry) => entry[1] > 0)
        .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
        .slice(0, 3)
        .map(([code, count]) => `${code}×${count}`);

    return entries.length > 0 ? entries.join(', ') : undefined;
}

function nextSettlementReason(
    current: PolyglotScanReason | null,
    incoming: PolyglotScanReason,
): PolyglotScanReason {
    if (!current) {
        return incoming;
    }
    return reasonWeight(incoming) >= reasonWeight(current) ? incoming : current;
}

function reasonWeight(reason: PolyglotScanReason): number {
    switch (reason) {
        case 'commit':
            return 4;
        case 'save':
            return 3;
        case 'manual':
            return 2;
        case 'interval':
        default:
            return 1;
    }
}

function initialLedgerReason(options: PolyglotEntropyOrchestratorOptions): string {
    if (!options.enabled) {
        return 'polyglot sidecars disabled';
    }
    return options.ledgerMode === 'validator'
        ? `validator backend ${options.solanaRpcUrl}`
        : 'bankrun simulation backend';
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}
