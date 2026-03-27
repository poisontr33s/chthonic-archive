// @SID: EXT_TYPES_V1
export type PolyglotScanReason = 'interval' | 'save' | 'manual' | 'commit';

export interface RuffFileSummary {
    path: string;
    violations: number;
    byCode: Record<string, number>;
}

export interface RuffSummaryEvent {
    type: 'ruff-summary';
    reason: PolyglotScanReason;
    generatedAt: number;
    totalViolations: number;
    files: RuffFileSummary[];
}

export interface RuffScanRequest {
    type: 'scan';
    reason: PolyglotScanReason;
    root: string;
    files?: string[];
}

export interface LoreRequest {
    type: 'lore-request';
    root: string;
    path: string;
    entropy: number;
    violations: number;
}

export interface LoreMetrics {
    maxNestingDepth: number;
    methodDefinitions: number;
    inheritedClasses: number;
    branchNodes: number;
}

export interface LoreEvent {
    type: 'lore';
    root: string;
    path: string;
    entropy: number;
    violations: number;
    line: string;
    metrics?: LoreMetrics;
    generatedAt: number;
}

export interface SidecarErrorEvent {
    type: 'error';
    source: 'python' | 'ruby';
    message: string;
}

export interface EntropyMerkleLeaf {
    path: string;
    entropy: number;
    complexity: number;
    debt: number;
    freshness: number;
    ruffViolations: number;
    updatedAt: number;
}

export interface EntropySettlement {
    reason: PolyglotScanReason;
    rootHash: string;
    leafCount: number;
    generatedAt: number;
}

export interface LedgerReceipt {
    mode: 'offline' | 'bankrun' | 'validator-rust';
    txSignature?: string;
    detail: string;
}

export interface RustLedgerRequest {
    jsonrpc: '2.0';
    id: number;
    method: 'submit_entropy';
    params: {
        entropy_score: number;
        merkle_root: string;
        leaf_count: number;
        reason: PolyglotScanReason;
    };
}

export interface RustLedgerSuccessResponse {
    jsonrpc: '2.0';
    id: number;
    result: {
        signature: string;
        slot?: number;
    };
}

export interface RustLedgerErrorResponse {
    jsonrpc: '2.0';
    id: number;
    error: {
        code: number;
        message: string;
        data?: string;
    };
}
