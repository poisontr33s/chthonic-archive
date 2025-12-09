// ═══════════════════════════════════════════════════════════════════════════════
// 🧬 MAS-MCP Dashboard - Artifact Reader
// Bun-native file access for Genesis JSON artifacts
// ═══════════════════════════════════════════════════════════════════════════════

import { readdir } from "fs/promises";
import { existsSync } from "fs";
import path from "path";
import type { CycleReport, Entity, DailyDigest, MonitoringScore } from "./types";
import { config, paths, checkSLO } from "./config";

// ─────────────────────────────────────────────────────────────────────────────────
// Cycle Report Reading
// ─────────────────────────────────────────────────────────────────────────────────

/**
 * Read all cycle reports from genesis logs directory
 * @param date - Optional date filter (YYYY-MM-DD or YYYYMMDD format)
 */
export async function readCycleReports(date?: string): Promise<CycleReport[]> {
  const logsDir = paths.logsDir();
  
  if (!existsSync(logsDir)) {
    console.warn(`[artifacts] Logs directory not found: ${logsDir}`);
    return [];
  }
  
  const entries = await readdir(logsDir);
  const cycleFiles = entries.filter(f => f.startsWith("cycle_") && f.endsWith(".json"));
  
  // Normalize date format
  const targetDate = date?.replace(/-/g, "") || "";
  const filtered = targetDate 
    ? cycleFiles.filter(f => f.includes(targetDate))
    : cycleFiles;
  
  const reports: CycleReport[] = [];
  
  for (const file of filtered) {
    try {
      const filePath = path.join(logsDir, file);
      const content = await Bun.file(filePath).json() as CycleReport;
      
      // Ensure timestamp exists
      if (!content.timestamp && content.cycle_id) {
        content.timestamp = content.cycle_id;
      }
      
      reports.push(content);
    } catch (err) {
      console.error(`[artifacts] Failed to read ${file}:`, err);
    }
  }
  
  // Sort by timestamp descending (most recent first)
  return reports.sort((a, b) => {
    const tsA = a.timestamp || a.cycle_id || "";
    const tsB = b.timestamp || b.cycle_id || "";
    return tsB.localeCompare(tsA);
  });
}

/**
 * Get a single cycle report by ID
 */
export async function getCycleById(cycleId: string): Promise<CycleReport | null> {
  const logsDir = paths.logsDir();
  const filePath = path.join(logsDir, `cycle_${cycleId}.json`);
  
  if (!existsSync(filePath)) {
    return null;
  }
  
  try {
    return await Bun.file(filePath).json() as CycleReport;
  } catch {
    return null;
  }
}

// ─────────────────────────────────────────────────────────────────────────────────
// Daily Digest Aggregation
// ─────────────────────────────────────────────────────────────────────────────────

/**
 * Aggregate cycle reports into a daily digest
 */
export function aggregateDigest(date: string, reports: CycleReport[]): DailyDigest {
  if (reports.length === 0) {
    return {
      date,
      total_cycles: 0,
      total_generated: 0,
      total_accepted: 0,
      acceptance_rate: 0,
      latency: { p50: 0, p95: 0, p99: 0 },
      vram_max: 0,
      degraded_cycles: 0,
      error_cycles: 0,
      slo_compliance: {
        acceptance_rate: false,
        p50_latency: true,
        p95_latency: true,
        vram: true,
      },
    };
  }
  
  const totalGenerated = reports.reduce((sum, r) => sum + (r.generated || r.attempts || 0), 0);
  const totalAccepted = reports.reduce((sum, r) => sum + r.accepted, 0);
  const p50Values = reports.map(r => r.latency_p50_ms).filter(v => v > 0);
  const p95Values = reports.map(r => r.latency_p95_ms).filter(v => v > 0);
  const p99Values = reports.map(r => r.latency_p99_ms).filter(v => v > 0);
  const vramMax = Math.max(...reports.map(r => r.vram_usage_pct || 0), 0);
  
  const avgP50 = p50Values.length > 0 ? p50Values.reduce((a, b) => a + b, 0) / p50Values.length : 0;
  const avgP95 = p95Values.length > 0 ? p95Values.reduce((a, b) => a + b, 0) / p95Values.length : 0;
  const avgP99 = p99Values.length > 0 ? p99Values.reduce((a, b) => a + b, 0) / p99Values.length : 0;
  const acceptanceRate = totalGenerated > 0 ? totalAccepted / totalGenerated : 0;
  
  return {
    date,
    total_cycles: reports.length,
    total_generated: totalGenerated,
    total_accepted: totalAccepted,
    acceptance_rate: acceptanceRate,
    latency: { p50: avgP50, p95: avgP95, p99: avgP99 },
    vram_max: vramMax,
    degraded_cycles: reports.filter(r => r.degraded_mode).length,
    error_cycles: reports.filter(r => r.error).length,
    slo_compliance: checkSLO({
      acceptanceRate,
      p50Ms: avgP50,
      p95Ms: avgP95,
      vramPct: vramMax,
    }),
  };
}

/**
 * Get daily digest for a specific date or today
 */
export async function getDailyDigest(date?: string): Promise<DailyDigest> {
  const targetDate = date || new Date().toISOString().slice(0, 10);
  const reports = await readCycleReports(targetDate);
  return aggregateDigest(targetDate, reports);
}

// ─────────────────────────────────────────────────────────────────────────────────
// Entity Registry Reading
// ─────────────────────────────────────────────────────────────────────────────────

/**
 * Read entities from the registry
 */
export async function readEntities(): Promise<Entity[]> {
  const registryPath = paths.entityRegistry();
  
  if (!existsSync(registryPath)) {
    console.warn(`[artifacts] Entity registry not found: ${registryPath}`);
    return [];
  }
  
  try {
    const content = await Bun.file(registryPath).json() as Entity[] | { entities: Entity[] };
    return Array.isArray(content) ? content : content.entities || [];
  } catch (err) {
    console.error(`[artifacts] Failed to read entity registry:`, err);
    return [];
  }
}

/**
 * Get recently generated entities from genesis_artifacts
 */
export async function getRecentEntities(limit = 10): Promise<Entity[]> {
  const artifactsDir = paths.artifactsDir();
  
  if (!existsSync(artifactsDir)) {
    return [];
  }
  
  try {
    const entries = await readdir(artifactsDir);
    const sorted = entries.sort().reverse().slice(0, limit);
    const entities: Entity[] = [];
    
    for (const entry of sorted) {
      const entityPath = path.join(artifactsDir, entry, "entity.json");
      if (existsSync(entityPath)) {
        try {
          const entity = await Bun.file(entityPath).json() as Entity;
          entities.push(entity);
        } catch {
          // Skip invalid files
        }
      }
    }
    
    return entities;
  } catch {
    return [];
  }
}

// ─────────────────────────────────────────────────────────────────────────────────
// Monitoring Score Reading
// ─────────────────────────────────────────────────────────────────────────────────

/**
 * Read all historical monitoring score files
 * Returns array sorted by timestamp (oldest first for charting)
 */
export async function readMonitoringScoreHistory(): Promise<MonitoringScore[]> {
  const artifactsDir = paths.artifactsDir();
  
  if (!existsSync(artifactsDir)) {
    console.warn(`[artifacts] Artifacts directory not found: ${artifactsDir}`);
    return [];
  }
  
  try {
    const entries = await readdir(artifactsDir);
    const scoreFiles = entries.filter(f => 
      f.startsWith("monitoring_score") && f.endsWith(".json")
    );
    
    const scores: MonitoringScore[] = [];
    
    for (const file of scoreFiles) {
      try {
        const filePath = path.join(artifactsDir, file);
        const content = await Bun.file(filePath).json() as MonitoringScore;
        
        // Ensure timestamp exists - extract from filename if missing
        if (!content.timestamp) {
          // monitoring_score_20251207T120000.json → 2025-12-07T12:00:00
          const match = file.match(/monitoring_score_(\d{8})T?(\d{6})?/);
          if (match) {
            const dateStr = match[1];
            const timeStr = match[2] || "000000";
            content.timestamp = `${dateStr.slice(0,4)}-${dateStr.slice(4,6)}-${dateStr.slice(6,8)}T${timeStr.slice(0,2)}:${timeStr.slice(2,4)}:${timeStr.slice(4,6)}Z`;
          } else {
            content.timestamp = new Date().toISOString();
          }
        }
        
        scores.push(content);
      } catch (err) {
        console.error(`[artifacts] Failed to read ${file}:`, err);
      }
    }
    
    // Sort by timestamp ascending (oldest first for charts)
    return scores.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
  } catch (err) {
    console.error("[artifacts] Failed to read monitoring score history:", err);
    return [];
  }
}

/**
 * Read the latest monitoring_score.json artifact
 * Falls back to computed score from recent cycles if file doesn't exist
 */
export async function readMonitoringScore(): Promise<MonitoringScore> {
  const artifactsDir = paths.artifactsDir();
  const monitoringPath = path.join(artifactsDir, "monitoring_score.json");
  
  // Try to read from file first
  if (existsSync(monitoringPath)) {
    try {
      const content = await Bun.file(monitoringPath).json() as MonitoringScore;
      return content;
    } catch (err) {
      console.error("[artifacts] Failed to read monitoring_score.json:", err);
    }
  }
  
  // Fall back: compute from recent cycles
  const reports = await readCycleReports();
  const last24h = reports.filter(r => {
    const ts = new Date(r.timestamp || r.cycle_id);
    const now = new Date();
    return (now.getTime() - ts.getTime()) < 24 * 60 * 60 * 1000;
  });
  
  const totalGenerated = last24h.reduce((s, r) => s + (r.generated || r.attempts || 0), 0);
  const totalAccepted = last24h.reduce((s, r) => s + r.accepted, 0);
  const acceptancePct = totalGenerated > 0 ? (totalAccepted / totalGenerated) * 100 : 0;
  
  const p50Values = last24h.map(r => r.latency_p50_ms).filter(v => v > 0);
  const p95Values = last24h.map(r => r.latency_p95_ms).filter(v => v > 0);
  const avgP50 = p50Values.length > 0 ? p50Values.reduce((a, b) => a + b) / p50Values.length : 0;
  const avgP95 = p95Values.length > 0 ? p95Values.reduce((a, b) => a + b) / p95Values.length : 0;
  
  const errorCount = last24h.filter(r => r.error).length;
  const qualityScore = acceptancePct; // Direct mapping for now
  
  return {
    timestamp: new Date().toISOString(),
    acceptance_pct: acceptancePct,
    latency_p50_ms: avgP50,
    latency_p95_ms: avgP95,
    error_count: errorCount,
    quality_score: qualityScore,
    slo_compliance: checkSLO({
      acceptanceRate: acceptancePct / 100,
      p50Ms: avgP50,
      p95Ms: avgP95,
      vramPct: 0,
    }),
    cycle_count: last24h.length,
    window_hours: 24,
  };
}
