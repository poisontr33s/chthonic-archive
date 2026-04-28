// @SID: EXT_RUNTIME_LANE_STATE_V1
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as vscode from 'vscode';

export type RuntimeLaneStateKind = 'READY' | 'LIVE' | 'PARKED' | 'DISABLED' | 'DEGRADED' | 'UNAVAILABLE' | 'MISSING';

export interface RuntimeLaneState {
    readonly name: string;
    readonly state: RuntimeLaneStateKind;
    readonly reason?: string;
    readonly localAction?: string;
    readonly updatedAt?: number;
}

export function formatRuntimeLaneState(lane: RuntimeLaneState): string {
    return lane.reason
        ? `${lane.name}=${lane.state} (${lane.reason})`
        : `${lane.name}=${lane.state}`;
}

export interface LaneSnapshot {
    readonly version: 1;
    readonly emittedAt: number;
    readonly lanes: ReadonlyArray<RuntimeLaneState>;
}

export class LaneRegistry implements vscode.Disposable {
    private readonly lanes = new Map<string, RuntimeLaneState>();
    private readonly emitter = new vscode.EventEmitter<RuntimeLaneState>();
    private snapshotPath: string | undefined;
    private flushHandle: NodeJS.Timeout | undefined;

    readonly onDidChange = this.emitter.event;

    bindSnapshotFile(globalStorageUri: vscode.Uri): void {
        try {
            fs.mkdirSync(globalStorageUri.fsPath, { recursive: true });
            this.snapshotPath = path.join(globalStorageUri.fsPath, 'lane-state.json');
            this.scheduleFlush();
        } catch {
            this.snapshotPath = undefined;
        }
    }

    set(state: RuntimeLaneState): void {
        const stamped: RuntimeLaneState = { ...state, updatedAt: Date.now() };
        this.lanes.set(state.name, stamped);
        this.emitter.fire(stamped);
        this.scheduleFlush();
    }

    setMany(states: ReadonlyArray<RuntimeLaneState>): void {
        const now = Date.now();
        for (const s of states) {
            const stamped: RuntimeLaneState = { ...s, updatedAt: now };
            this.lanes.set(s.name, stamped);
            this.emitter.fire(stamped);
        }
        this.scheduleFlush();
    }

    get(name: string): RuntimeLaneState | undefined {
        return this.lanes.get(name);
    }

    snapshot(): LaneSnapshot {
        return {
            version: 1,
            emittedAt: Date.now(),
            lanes: Array.from(this.lanes.values()).sort((a, b) => a.name.localeCompare(b.name)),
        };
    }

    dispose(): void {
        if (this.flushHandle) {
            clearTimeout(this.flushHandle);
            this.flushHandle = undefined;
        }
        this.flush();
        this.emitter.dispose();
    }

    private scheduleFlush(): void {
        if (!this.snapshotPath || this.flushHandle) return;
        this.flushHandle = setTimeout(() => {
            this.flushHandle = undefined;
            this.flush();
        }, 250);
    }

    private flush(): void {
        if (!this.snapshotPath) return;
        try {
            fs.writeFileSync(this.snapshotPath, JSON.stringify(this.snapshot(), null, 2), 'utf8');
        } catch {
            // best-effort; cockpit will fall back to last good snapshot
        }
    }
}
