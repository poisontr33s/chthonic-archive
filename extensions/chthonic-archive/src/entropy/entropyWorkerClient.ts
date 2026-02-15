import * as path from 'path';
import * as vscode from 'vscode';
import { Worker } from 'worker_threads';
import type {
    EntropyFileRecord,
    EntropyGraphPayload,
    EntropyWorkerEvent,
    EntropyWorkerRequest,
} from './types';

export interface EntropySnapshot {
    totalFiles: number;
    topEntropy: EntropyFileRecord[];
    averageEntropy: number;
    lastScanDurationMs: number;
    lastScanAt: number;
}

export class EntropyWorkerClient implements vscode.Disposable {
    private readonly records = new Map<string, EntropyFileRecord>();
    private readonly recordUris = new Map<string, vscode.Uri>();

    private readonly onDidUpdateRecordsEmitter = new vscode.EventEmitter<vscode.Uri[]>();
    readonly onDidUpdateRecords = this.onDidUpdateRecordsEmitter.event;

    private readonly onDidUpdateGraphEmitter = new vscode.EventEmitter<EntropyGraphPayload>();
    readonly onDidUpdateGraph = this.onDidUpdateGraphEmitter.event;

    private readonly onDidUpdateSnapshotEmitter = new vscode.EventEmitter<EntropySnapshot>();
    readonly onDidUpdateSnapshot = this.onDidUpdateSnapshotEmitter.event;

    private worker: Worker | null = null;
    private rootPath: string | null = null;
    private workerPath: string;
    private maxFiles = 10_000;
    private lastScanDurationMs = 0;
    private lastScanAt = 0;
    private scanTimer: NodeJS.Timeout | null = null;
    private disposed = false;

    constructor(
        private readonly extensionContext: vscode.ExtensionContext,
        private readonly output: vscode.OutputChannel,
    ) {
        this.workerPath = extensionContext.asAbsolutePath(path.join('dist', 'entropy-worker.js'));
    }

    start(rootPath: string, maxFiles: number, scanIntervalMs: number): void {
        this.rootPath = rootPath;
        this.maxFiles = maxFiles;
        this.ensureWorker();
        this.send({
            type: 'scan',
            root: rootPath,
            maxFiles: this.maxFiles,
        });
        this.scheduleScanLoop(scanIntervalMs);
    }

    rescanNow(): void {
        if (!this.rootPath) {
            return;
        }
        this.send({
            type: 'scan',
            root: this.rootPath,
            maxFiles: this.maxFiles,
        });
    }

    refreshFile(uri: vscode.Uri): void {
        if (!this.rootPath || uri.scheme !== 'file') {
            return;
        }
        this.send({
            type: 'refresh-file',
            root: this.rootPath,
            path: uri.fsPath,
        });
    }

    requestGraph(limit: number): void {
        this.send({
            type: 'graph',
            limit,
        });
    }

    getRecord(uri: vscode.Uri): EntropyFileRecord | undefined {
        if (!this.rootPath || uri.scheme !== 'file') {
            return undefined;
        }
        const relative = normalizePath(path.relative(this.rootPath, uri.fsPath));
        return this.records.get(relative);
    }

    getSnapshot(topLimit = 40): EntropySnapshot {
        const values = Array.from(this.records.values());
        const averageEntropy = values.length === 0
            ? 0
            : values.reduce((sum, entry) => sum + entry.entropy, 0) / values.length;

        const topEntropy = values
            .sort((a, b) => b.entropy - a.entropy)
            .slice(0, topLimit);

        return {
            totalFiles: values.length,
            topEntropy,
            averageEntropy,
            lastScanDurationMs: this.lastScanDurationMs,
            lastScanAt: this.lastScanAt,
        };
    }

    dispose(): void {
        this.disposed = true;
        if (this.scanTimer) {
            clearInterval(this.scanTimer);
            this.scanTimer = null;
        }
        this.send({ type: 'stop' });
        this.worker?.terminate();
        this.worker = null;
        this.onDidUpdateRecordsEmitter.dispose();
        this.onDidUpdateGraphEmitter.dispose();
        this.onDidUpdateSnapshotEmitter.dispose();
    }

    private scheduleScanLoop(scanIntervalMs: number): void {
        if (this.scanTimer) {
            clearInterval(this.scanTimer);
        }

        const boundedInterval = Math.max(5_000, scanIntervalMs);
        this.scanTimer = setInterval(() => {
            if (!this.disposed) {
                this.rescanNow();
            }
        }, boundedInterval);
    }

    private ensureWorker(): void {
        if (this.worker) {
            return;
        }

        this.worker = new Worker(this.workerPath);
        this.worker.on('message', (event: EntropyWorkerEvent) => this.handleWorkerEvent(event));
        this.worker.on('error', (error) => {
            this.output.appendLine(`[entropy] worker error: ${error.message}`);
        });
        this.worker.on('exit', (code) => {
            this.output.appendLine(`[entropy] worker exited with code ${code}`);
            this.worker = null;
            if (!this.disposed && code !== 0) {
                // One automatic recovery attempt to keep the system alive.
                this.ensureWorker();
                this.rescanNow();
            }
        });
    }

    private send(request: EntropyWorkerRequest): void {
        this.ensureWorker();
        this.worker?.postMessage(request);
    }

    private handleWorkerEvent(event: EntropyWorkerEvent): void {
        switch (event.type) {
            case 'scan-progress': {
                if (!this.rootPath) {
                    return;
                }
                const changedUris: vscode.Uri[] = [];
                for (const record of event.records) {
                    this.records.set(record.path, record);
                    let uri = this.recordUris.get(record.path);
                    if (!uri) {
                        uri = vscode.Uri.file(path.join(this.rootPath, record.path));
                        this.recordUris.set(record.path, uri);
                    }
                    changedUris.push(uri);
                }
                if (changedUris.length > 0) {
                    this.onDidUpdateRecordsEmitter.fire(changedUris);
                }
                break;
            }
            case 'scan-complete':
                this.lastScanDurationMs = event.durationMs;
                this.lastScanAt = Date.now();
                this.onDidUpdateSnapshotEmitter.fire(this.getSnapshot());
                break;
            case 'graph-result':
                this.onDidUpdateGraphEmitter.fire(event.graph);
                break;
            case 'error':
                this.output.appendLine(`[entropy] ${event.message}${event.detail ? `\n${event.detail}` : ''}`);
                break;
        }
    }
}

function normalizePath(rawPath: string): string {
    return rawPath.replace(/\\/g, '/');
}
