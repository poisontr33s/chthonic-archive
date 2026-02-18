// ---------------------------------------------------------------------------
// ANNO manifest types (mirrors chthonic-daemon/src/types.rs)
// ---------------------------------------------------------------------------

export interface AnnoManifest {
    languages: LanguagePolicy[];
    tool_owners: Record<string, ToolOwner>;
    detected_markers: DetectedMarker[];
    warnings: string[];
}

export interface LanguagePolicy {
    language: string;
    tool: ToolOwner;
    shim_priority: number;
}

export type ToolOwner =
    | 'uv'
    | 'rv'
    | 'goup'
    | 'mise'
    | 'fnm'
    | 'bun'
    | 'volta'
    | 'rustup'
    | 'system';

export interface DetectedMarker {
    path: string;
    kind: string;
}

// ---------------------------------------------------------------------------
// Environment provisioning types
// ---------------------------------------------------------------------------

export interface EnvReport {
    path_mutations: PathSegment[];
    dev_kit: DevKitReport | null;
    vulkan_status: string;
    warnings: string[];
}

export interface PathSegment {
    path: string;
    owner: string;
    priority: number;
}

export interface DevKitReport {
    msys2_home: string;
    ucrt64_bin: string;
    perl_path: string;
    cc: string;
    cxx: string;
    env_vars: Array<[string, string]>;
    path_prepend: string[];
}

// ---------------------------------------------------------------------------
// Reactor types
// ---------------------------------------------------------------------------

export interface SedimentVertex {
    x: number;
    y: number;
    z: number;
    radius: number;
    r: number;
    g: number;
    b: number;
    alpha: number;
}

export interface SedimentResult {
    vertices: SedimentVertex[];
    layer_count: number;
    file_count: number;
    compute_time_ms: number;
    backend: string;
}

export interface SedimentChunk {
    chunk_index: number;
    total_chunks: number;
    layer_count: number;
    file_count: number;
    backend: string;
    vertices: SedimentVertex[];
}

export interface SynapseDescriptor {
    status: 'ready' | 'unavailable' | 'disabled';
    mode: 'shared_memory' | 'jsonl';
    shm_id?: string;
    event_name?: string | null;
    slot_capacity?: number;
    vertex_capacity?: number;
    slot_stride?: number;
    high_water_mark?: number;
    reason?: string;
}

export interface SedimentSynapseResult {
    backend: string;
    layer_count: number;
    file_count: number;
    compute_time_ms: number;
    total_chunks: number;
    chunks_written: number;
    dropped_chunks: number;
    queue_depth: number;
    transport: 'shared_memory' | 'jsonl';
}

export interface EntropyToolState {
    tool: string;
    manager: string;
    requested: string;
    cycle?: string | null;
    latest_cycle?: string | null;
    latest_stable: boolean;
    eol: boolean;
    near_eol: boolean;
    days_until_eol?: number | null;
    status: 'latest' | 'outdated' | 'near_eol' | 'eol' | 'unknown' | 'unmanaged';
    note?: string | null;
}

export interface EntropyState {
    status: 'pristine' | 'degraded' | 'critical' | 'stale';
    decay_score: number;
    stale: boolean;
    critical: boolean;
    validator_active: boolean;
    validator_source_mise: boolean;
    validator_process?: string | null;
    firedancer_surge: boolean;
    simulated_tps: number;
    checked_at_epoch_ms: number;
    source_mise?: string | null;
    auto_update: 'auto' | 'manual' | 'unknown';
    auto_update_enabled: boolean;
    critical_tools: string[];
    tracked_tools: EntropyToolState[];
    warning?: string | null;
}

export interface FiredancerSurgeState {
    slot: number;
    shred_count: number;
    packet_count: number;
    simulated_tps: number;
    surge: boolean;
}

// ---------------------------------------------------------------------------
// Daemon JSON-RPC wire types
// ---------------------------------------------------------------------------

export interface DaemonNotification<T = unknown> {
    jsonrpc: '2.0';
    method: string;
    params: T;
}

export interface DaemonResponse<T = unknown> {
    jsonrpc: '2.0';
    id: number;
    result?: T;
    error?: {
        code: number;
        message: string;
    };
}
