// ═══════════════════════════════════════════════════════════════════════════════
// 🧬 MAS-MCP Dashboard Types
// Bun-native TypeScript definitions for Genesis artifacts
// ═══════════════════════════════════════════════════════════════════════════════

/** Cycle report from genesis scheduler */
export interface CycleReport {
  cycle_id: string;
  timestamp: string;
  start_time: string;
  end_time: string;
  duration_s: number;
  
  // Generation metrics
  target?: number;
  generated?: number;
  attempts?: number;
  accepted: number;
  rejected?: number;
  acceptance_rate: number;
  
  // Latency metrics
  latency_p50_ms: number;
  latency_p95_ms: number;
  latency_p99_ms: number;
  latency_max_ms?: number;
  
  // Status
  status: string;
  error?: string | null;
  
  // Thresholds
  novelty_threshold: number;
  derivation_tolerance: number;
  
  // GPU info
  gpu_enabled: boolean;
  providers: string[];
  vram_usage_pct?: number;
  
  // Degraded mode
  degraded_mode?: boolean;
  degraded_reason?: string | null;
  
  // Artifacts
  artifact_hashes?: Record<string, string>;
}

/** Daily digest aggregation */
export interface DailyDigest {
  date: string;
  total_cycles: number;
  total_generated: number;
  total_accepted: number;
  acceptance_rate: number;
  latency: {
    p50: number;
    p95: number;
    p99: number;
  };
  vram_max: number;
  degraded_cycles: number;
  error_cycles: number;
  slo_compliance: SLOCompliance;
}

/** SLO compliance status */
export interface SLOCompliance {
  acceptance_rate: boolean;
  p50_latency: boolean;
  p95_latency: boolean;
  vram: boolean;
  overall?: boolean;
}

/** Entity from genesis synthesis */
export interface Entity {
  name: string;
  tier: number;
  faction?: string;
  archetype?: string;
  physique?: {
    whr: number;
    cup_size: string;
    measurements: string;
    height_cm?: number;
    weight_kg?: number;
  };
  created_at?: string;
  cycle_id?: string;
  novelty_score?: number;
  signature_hash?: string;
}

/** Health check response */
export interface HealthResponse {
  status: "ok" | "degraded" | "error";
  version: string;
  bun_version: string;
  gpu_provider: string;
  reloads: number;
  timestamp: string;
}

/** API error response */
export interface APIError {
  error: string;
  message?: string;
  path?: string;
}

/** Paginated response wrapper */
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

/** WebSocket message for live updates */
export interface WSMessage {
  type: "cycle_complete" | "entity_generated" | "slo_alert" | "heartbeat";
  payload: unknown;
  timestamp: string;
}

/** Monitoring score artifact (monitoring_score.json) */
export interface MonitoringScore {
  timestamp: string;
  acceptance_pct: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  error_count: number;
  quality_score: number;
  slo_compliance: SLOCompliance;
  cycle_count?: number;
  window_hours?: number;
}
