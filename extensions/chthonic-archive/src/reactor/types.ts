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

export type ToolOwner = 'uv' | 'mise' | 'bun' | 'volta' | 'rustup' | 'system';

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
