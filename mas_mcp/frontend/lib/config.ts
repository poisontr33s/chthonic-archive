// ═══════════════════════════════════════════════════════════════════════════════
// 🧬 MAS-MCP Dashboard Configuration
// Bun-native config with environment variable parsing
// ═══════════════════════════════════════════════════════════════════════════════

import path from "path";

/** Server configuration */
export const config = {
  port: Number(process.env.PORT) || 4000,
  host: process.env.HOST || "127.0.0.1",
  
  /** GPU provider name for display */
  gpuProvider: process.env.GENESIS_GPU_PROVIDER || "CUDA+TensorRT",
  
  /** SLO thresholds */
  slo: {
    acceptanceRate: Number(process.env.SLO_ACCEPTANCE_RATE) || 0.35,
    p50LatencyMs: Number(process.env.SLO_P50_LATENCY_MS) || 50,
    p95LatencyMs: Number(process.env.SLO_P95_LATENCY_MS) || 200,
    vramPct: Number(process.env.SLO_VRAM_PCT) || 90,
  },
} as const;

/** Path configuration - relative to frontend/ directory */
export const paths = {
  /** Genesis cycle logs directory */
  logsDir: () => path.resolve(import.meta.dir, "..", process.env.GENESIS_LOGS_DIR || "../logs/genesis"),
  
  /** Genesis artifacts directory */
  artifactsDir: () => path.resolve(import.meta.dir, "..", process.env.GENESIS_ARTIFACTS_DIR || "../genesis_artifacts"),
  
  /** Entity registry path */
  entityRegistry: () => path.resolve(import.meta.dir, "..", process.env.ENTITY_REGISTRY_PATH || "../data/entity_registry.json"),
  
  /** Public static files */
  publicDir: () => path.resolve(import.meta.dir, "..", "public"),
} as const;

/** Check if SLO is compliant */
export function checkSLO(metrics: {
  acceptanceRate: number;
  p50Ms: number;
  p95Ms: number;
  vramPct: number;
}): { acceptance_rate: boolean; p50_latency: boolean; p95_latency: boolean; vram: boolean; overall: boolean } {
  const compliance = {
    acceptance_rate: metrics.acceptanceRate >= config.slo.acceptanceRate,
    p50_latency: metrics.p50Ms <= config.slo.p50LatencyMs,
    p95_latency: metrics.p95Ms <= config.slo.p95LatencyMs,
    vram: metrics.vramPct <= config.slo.vramPct,
  };
  
  return {
    ...compliance,
    overall: Object.values(compliance).every(Boolean),
  };
}
