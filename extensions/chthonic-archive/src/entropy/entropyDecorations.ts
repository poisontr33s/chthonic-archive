// @SID: EXT_ENTROPYDECORATIONS_V1
import * as vscode from 'vscode';
import type { EntropyFileRecord } from './types';
import { EntropyWorkerClient } from './entropyWorkerClient';

export class EntropyDecorationProvider implements vscode.FileDecorationProvider, vscode.Disposable {
    private readonly onDidChangeEmitter = new vscode.EventEmitter<vscode.Uri | vscode.Uri[]>();
    readonly onDidChangeFileDecorations = this.onDidChangeEmitter.event;

    private readonly pending = new Map<string, vscode.Uri>();
    private flushTimer: NodeJS.Timeout | null = null;

    constructor(
        private readonly workerClient: EntropyWorkerClient,
        private debounceMs: number,
        private maxPerFlush: number,
        private readonly tooltipAugmentProvider?: (uri: vscode.Uri) => string[],
    ) {
        this.workerClient.onDidUpdateRecords((uris) => this.enqueueUpdates(uris));
    }

    dispose(): void {
        if (this.flushTimer) {
            clearTimeout(this.flushTimer);
            this.flushTimer = null;
        }
        this.onDidChangeEmitter.dispose();
    }

    updateConfig(debounceMs: number, maxPerFlush: number): void {
        this.debounceMs = Math.max(30, debounceMs);
        this.maxPerFlush = Math.max(64, maxPerFlush);
    }

    provideFileDecoration(uri: vscode.Uri): vscode.ProviderResult<vscode.FileDecoration> {
        if (uri.scheme !== 'file') {
            return undefined;
        }
        const record = this.workerClient.getRecord(uri);
        if (!record) {
            return undefined;
        }

        const color = entropyColor(record);
        const tooltipFragments = [
            `Entropy ${(record.entropy * 100).toFixed(0)}%`,
            `Complexity ${record.complexity}`,
            `Debt ${record.debt}`,
            `Freshness ${(record.freshness * 100).toFixed(0)}%`,
        ];

        if (this.tooltipAugmentProvider) {
            tooltipFragments.push(...this.tooltipAugmentProvider(uri));
        }

        return {
            color,
            tooltip: tooltipFragments.join('\n'),
            propagate: false,
        };
    }

    enqueueExternalUpdates(uris: vscode.Uri[]): void {
        this.enqueueUpdates(uris);
    }

    private enqueueUpdates(uris: vscode.Uri[]): void {
        for (const uri of uris) {
            this.pending.set(uri.toString(), uri);
        }
        if (!this.flushTimer) {
            this.flushTimer = setTimeout(() => this.flush(), this.debounceMs);
        }
    }

    private flush(): void {
        this.flushTimer = null;
        if (this.pending.size === 0) {
            return;
        }

        const updates = Array.from(this.pending.values()).slice(0, this.maxPerFlush);
        for (const uri of updates) {
            this.pending.delete(uri.toString());
        }

        this.onDidChangeEmitter.fire(updates);

        if (this.pending.size > 0) {
            this.flushTimer = setTimeout(() => this.flush(), this.debounceMs);
        }
    }
}

function entropyColor(record: EntropyFileRecord): vscode.ThemeColor {
    // FileDecoration.color expects ThemeColor in current vscode.d.ts; use semantic theme tokens.
    const decay = clamp01((record.entropy * 0.78) + ((1 - record.freshness) * 0.22));
    if (decay >= 0.72) {
        return new vscode.ThemeColor('problemsErrorIcon.foreground');
    }
    if (decay >= 0.45) {
        return new vscode.ThemeColor('charts.yellow');
    }
    return new vscode.ThemeColor('charts.green');
}

function clamp01(value: number): number {
    if (value < 0) return 0;
    if (value > 1) return 1;
    return value;
}
