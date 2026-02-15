export interface EntropyFileRecord {
    path: string;
    entropy: number; // 0.0 -> 1.0
    complexity: number;
    debt: number;
    freshness: number; // 0.0 stale -> 1.0 fresh
    mtimeMs: number;
    language: string;
    lines: number;
}

export interface EntropyGraphNode {
    id: string;
    label: string;
    entropy: number;
    degree: number;
    x: number;
    y: number;
}

export interface EntropyGraphEdge {
    source: string;
    target: string;
    weight: number;
}

export interface EntropyGraphPayload {
    nodes: EntropyGraphNode[];
    edges: EntropyGraphEdge[];
    generatedAt: number;
}

export type EntropyWorkerRequest =
    | {
        type: 'scan';
        root: string;
        maxFiles: number;
    }
    | {
        type: 'refresh-file';
        root: string;
        path: string;
    }
    | {
        type: 'graph';
        limit: number;
    }
    | {
        type: 'stop';
    };

export type EntropyWorkerEvent =
    | {
        type: 'scan-progress';
        records: EntropyFileRecord[];
    }
    | {
        type: 'scan-complete';
        total: number;
        durationMs: number;
    }
    | {
        type: 'graph-result';
        graph: EntropyGraphPayload;
    }
    | {
        type: 'error';
        message: string;
        detail?: string;
    };
