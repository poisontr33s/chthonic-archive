import * as crypto from 'crypto';
import type { EntropyMerkleLeaf, EntropySettlement, PolyglotScanReason } from './types';

export class EntropyMerkleAccumulator {
    private readonly leaves = new Map<string, string>();
    private dirty = false;

    upsert(leaf: EntropyMerkleLeaf): boolean {
        const normalizedPath = normalizePath(leaf.path);
        const digest = hashLeaf(normalizedPath, leaf);
        const previous = this.leaves.get(normalizedPath);
        if (previous !== digest) {
            this.leaves.set(normalizedPath, digest);
            this.dirty = true;
            return true;
        }
        return false;
    }

    hasDirty(): boolean {
        return this.dirty;
    }

    settle(reason: PolyglotScanReason): EntropySettlement | null {
        if (!this.dirty || this.leaves.size === 0) {
            return null;
        }
        const rootHash = merkleRoot(Array.from(this.leaves.entries()).sort((a, b) => a[0].localeCompare(b[0])));
        this.dirty = false;
        return {
            reason,
            rootHash,
            leafCount: this.leaves.size,
            generatedAt: Date.now(),
        };
    }
}

function hashLeaf(path: string, leaf: EntropyMerkleLeaf): string {
    const payload = [
        path,
        leaf.entropy.toFixed(6),
        leaf.complexity,
        leaf.debt,
        leaf.freshness.toFixed(6),
        leaf.ruffViolations,
        leaf.updatedAt,
    ].join('|');
    return sha256(payload);
}

function merkleRoot(entries: Array<[string, string]>): string {
    if (entries.length === 0) {
        return sha256('EMPTY');
    }
    let layer = entries.map(([path, digest]) => sha256(`${path}:${digest}`));
    while (layer.length > 1) {
        const next: string[] = [];
        for (let i = 0; i < layer.length; i += 2) {
            const left = layer[i];
            const right = layer[i + 1] ?? layer[i];
            next.push(sha256(`${left}${right}`));
        }
        layer = next;
    }
    return layer[0];
}

function sha256(value: string): string {
    return crypto.createHash('sha256').update(value, 'utf8').digest('hex');
}

function normalizePath(rawPath: string): string {
    return rawPath.replace(/\\/g, '/');
}
