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
        const tooltip = [
            `Entropy ${(record.entropy * 100).toFixed(0)}%`,
            `Complexity ${record.complexity}`,
            `Debt ${record.debt}`,
            `Freshness ${(record.freshness * 100).toFixed(0)}%`,
        ].join(' • ');

        return {
            color,
            tooltip,
            propagate: false,
        };
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

function entropyColor(record: EntropyFileRecord): string {
    // Green for recently edited / low entropy, brown-red for stale / high entropy.
    const decay = clamp01((record.entropy * 0.78) + ((1 - record.freshness) * 0.22));
    const hue = lerp(118, 24, decay);
    const saturation = lerp(36, 46, decay);
    const lightness = lerp(58, 42, decay);
    return hslToHex(hue, saturation, lightness);
}

function hslToHex(h: number, s: number, l: number): string {
    const hue = h / 360;
    const sat = s / 100;
    const light = l / 100;

    const hueToRgb = (p: number, q: number, t: number): number => {
        let x = t;
        if (x < 0) x += 1;
        if (x > 1) x -= 1;
        if (x < 1 / 6) return p + ((q - p) * 6 * x);
        if (x < 1 / 2) return q;
        if (x < 2 / 3) return p + ((q - p) * ((2 / 3) - x) * 6);
        return p;
    };

    let r: number;
    let g: number;
    let b: number;

    if (sat === 0) {
        r = light;
        g = light;
        b = light;
    } else {
        const q = light < 0.5 ? light * (1 + sat) : light + sat - (light * sat);
        const p = (2 * light) - q;
        r = hueToRgb(p, q, hue + (1 / 3));
        g = hueToRgb(p, q, hue);
        b = hueToRgb(p, q, hue - (1 / 3));
    }

    const toHex = (value: number): string => {
        const channel = Math.round(value * 255).toString(16).padStart(2, '0');
        return channel;
    };

    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

function clamp01(value: number): number {
    if (value < 0) return 0;
    if (value > 1) return 1;
    return value;
}

function lerp(from: number, to: number, ratio: number): number {
    return from + ((to - from) * ratio);
}
