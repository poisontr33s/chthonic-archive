// ═══════════════════════════════════════════════════════════════════════════════
// 🧬 MAS-MCP Dashboard - API Routes
// Bun-native HTTP handlers for Genesis artifact access
// ═══════════════════════════════════════════════════════════════════════════════

import { join } from "node:path";
import { 
  readCycleReports, 
  getCycleById, 
  getDailyDigest,
  aggregateDigest,
  readEntities, 
  getRecentEntities,
  readMonitoringScore,
  readMonitoringScoreHistory,
} from "../lib/artifacts";
import { config, paths } from "../lib/config";

// ─────────────────────────────────────────────────────────────────────────────────
// Route Handlers
// ─────────────────────────────────────────────────────────────────────────────────

export const apiRoutes = {
  /**
   * GET /api/digest - Current day's digest
   */
  async getDigest(): Promise<Response> {
    try {
      const digest = await getDailyDigest();
      return Response.json(digest);
    } catch (err) {
      console.error("[API] getDigest error:", err);
      return Response.json({ error: "Failed to load digest" }, { status: 500 });
    }
  },

  /**
   * GET /api/digest/:date - Digest for specific date
   */
  async getDigestByDate(req: Request): Promise<Response> {
    const url = new URL(req.url);
    const date = url.pathname.split("/").pop();
    
    if (!date || !/^\d{4}-?\d{2}-?\d{2}$/.test(date)) {
      return Response.json({ error: "Invalid date format" }, { status: 400 });
    }
    
    try {
      const digest = await getDailyDigest(date);
      return Response.json(digest);
    } catch (err) {
      console.error("[API] getDigestByDate error:", err);
      return Response.json({ error: "Failed to load digest" }, { status: 500 });
    }
  },

  /**
   * GET /api/cycles - List all cycle reports
   */
  async getCycles(req: Request): Promise<Response> {
    const url = new URL(req.url);
    const date = url.searchParams.get("date") || undefined;
    const limit = Number(url.searchParams.get("limit")) || 50;
    const offset = Number(url.searchParams.get("offset")) || 0;
    
    try {
      const allReports = await readCycleReports(date);
      const paginated = allReports.slice(offset, offset + limit);
      
      return Response.json({
        data: paginated,
        total: allReports.length,
        limit,
        offset,
        has_more: offset + limit < allReports.length,
      });
    } catch (err) {
      console.error("[API] getCycles error:", err);
      return Response.json({ error: "Failed to load cycles" }, { status: 500 });
    }
  },

  /**
   * GET /api/cycles/:id - Single cycle report
   */
  async getCycleById(req: Request): Promise<Response> {
    const url = new URL(req.url);
    const id = url.pathname.split("/").pop();
    
    if (!id) {
      return Response.json({ error: "Cycle ID required" }, { status: 400 });
    }
    
    try {
      const cycle = await getCycleById(id);
      
      if (!cycle) {
        return Response.json({ error: "Cycle not found" }, { status: 404 });
      }
      
      return Response.json(cycle);
    } catch (err) {
      console.error("[API] getCycleById error:", err);
      return Response.json({ error: "Failed to load cycle" }, { status: 500 });
    }
  },

  /**
   * GET /api/metrics - Aggregated metrics
   */
  async getMetrics(): Promise<Response> {
    try {
      const today = new Date().toISOString().slice(0, 10);
      const reports = await readCycleReports();
      
      // Group by date
      const byDate = new Map<string, typeof reports>();
      for (const r of reports) {
        const date = (r.timestamp || r.cycle_id).slice(0, 10);
        if (!byDate.has(date)) byDate.set(date, []);
        byDate.get(date)!.push(r);
      }
      
      // Build digest for each date
      const digests = Array.from(byDate.entries())
        .map(([date, reps]) => aggregateDigest(date, reps))
        .sort((a, b) => b.date.localeCompare(a.date))
        .slice(0, 7); // Last 7 days
      
      return Response.json({
        current_date: today,
        days: digests,
        totals: {
          cycles: digests.reduce((s, d) => s + d.total_cycles, 0),
          generated: digests.reduce((s, d) => s + d.total_generated, 0),
          accepted: digests.reduce((s, d) => s + d.total_accepted, 0),
        },
      });
    } catch (err) {
      console.error("[API] getMetrics error:", err);
      return Response.json({ error: "Failed to load metrics" }, { status: 500 });
    }
  },

  /**
   * GET /api/entities - All entities from registry
   */
  async getEntities(): Promise<Response> {
    try {
      const entities = await readEntities();
      return Response.json({
        data: entities,
        total: entities.length,
      });
    } catch (err) {
      console.error("[API] getEntities error:", err);
      return Response.json({ error: "Failed to load entities" }, { status: 500 });
    }
  },

  /**
   * GET /api/entities/recent - Recently generated entities
   */
  async getRecentEntities(req: Request): Promise<Response> {
    const url = new URL(req.url);
    const limit = Number(url.searchParams.get("limit")) || 10;
    
    try {
      const entities = await getRecentEntities(limit);
      return Response.json({
        data: entities,
        total: entities.length,
      });
    } catch (err) {
      console.error("[API] getRecentEntities error:", err);
      return Response.json({ error: "Failed to load recent entities" }, { status: 500 });
    }
  },

  /**
   * GET /api/monitoring - Current monitoring score artifact
   */
  async getMonitoringScore(): Promise<Response> {
    try {
      const score = await readMonitoringScore();
      return Response.json(score);
    } catch (err) {
      console.error("[API] getMonitoringScore error:", err);
      return Response.json({ error: "Failed to load monitoring score" }, { status: 500 });
    }
  },

/**
   * GET /api/metrics/history - Historical monitoring scores for trend charts
   * Returns all monitoring_score_*.json files sorted by timestamp
   */
  async getMetricsHistory(): Promise<Response> {
    try {
      const scores = await readMonitoringScoreHistory();
      
      return Response.json({
        data: scores,
        total: scores.length,
        oldest: scores.length > 0 ? scores[0].timestamp : null,
        newest: scores.length > 0 ? scores[scores.length - 1].timestamp : null,
      });
    } catch (err) {
      console.error("[API] getMetricsHistory error:", err);
      return Response.json({ error: "Failed to load metrics history" }, { status: 500 });
    }
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
// 🔥 Cycle Control Routes - IPC bridge to Python/uv backend (Phase 1 Gemini)
// ═══════════════════════════════════════════════════════════════════════════════

import { CycleActivator } from "../lib/activator";

// Singleton activator instance
const activator = new CycleActivator();

export const cycleControlRoutes = {
  /**
   * POST /api/cycle/start - Start a new MILF execution cycle
   * Spawns: uv run scripts/run_cycle.py
   */
  async startCycle(req: Request): Promise<Response> {
    try {
      const body = await req.json().catch(() => ({}));
      const { milfs, quiet = true, cpuOnly = false, timeout } = body as { 
        milfs?: string[];
        quiet?: boolean;
        cpuOnly?: boolean;
        timeout?: number;
      };
      
      console.log(`[API] startCycle milfs=${milfs?.join(",") || "all"}, cpuOnly=${cpuOnly}`);
      
      const result = await activator.startCycle({ milfs, quiet, cpuOnly, timeout });
      
      return Response.json({
        success: result.success,
        cycle_id: result.cycle_id,
        ssot_hash: result.ssot_hash,
        duration_ms: result.duration_ms,
        milfs_activated: result.milfs_activated,
        artifacts_generated: result.artifacts_generated,
        errors: result.errors,
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      const error = err as Error;
      console.error("[API] startCycle error:", error);
      return Response.json({ 
        success: false, 
        error: error.message,
        stack: error.stack,
      }, { status: 500 });
    }
  },

  /**
   * GET /api/cycle/status - Check cycle subprocess status
   */
  async getCycleStatus(): Promise<Response> {
    try {
      const status = await activator.checkStatus();
      return Response.json({
        ...status,
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      const error = err as Error;
      console.error("[API] getCycleStatus error:", error);
      return Response.json({ 
        running: false,
        status: "error",
        error: error.message,
        timestamp: new Date().toISOString(),
      }, { status: 500 });
    }
  },

  /**
   * GET /api/probe - Run GPU compatibility probe
   * Spawns: uv run scripts/probe_gpu_compatibility.py
   */
  async runProbe(): Promise<Response> {
    try {
      console.log("[API] runProbe - checking GPU compatibility");
      const result = await activator.runProbe();
      
      return Response.json({
        ...result,
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      const error = err as Error;
      console.error("[API] runProbe error:", error);
      return Response.json({ 
        success: false, 
        cuda_available: false,
        error: error.message,
        timestamp: new Date().toISOString(),
      }, { status: 500 });
    }
  },

  /**
   * POST /api/activate - Evaluate MILF activation gates
   * Spawns: uv run scripts/milf_activator.py
   */
  async activateMilfs(req: Request): Promise<Response> {
    try {
      const body = await req.json().catch(() => ({}));
      const { profile = "inference_default", dry_run = false } = body as {
        profile?: string;
        dry_run?: boolean;
      };
      
      console.log(`[API] activateMilfs profile=${profile}, dry_run=${dry_run}`);
      
      const result = await activator.activateMilfs({ profile, dry_run });
      
      return Response.json({
        ...result,
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      const error = err as Error;
      console.error("[API] activateMilfs error:", error);
      return Response.json({ 
        success: false, 
        profile_used: "unknown",
        activated: [],
        rejected: [],
        summary: { total: 0, activated: 0, rejected: 0 },
        error: error.message,
        timestamp: new Date().toISOString(),
      }, { status: 500 });
    }
  },

  /**
   * GET /api/milfs - List all MILFs from registry with activation status
   */
  async getMilfs(): Promise<Response> {
    try {
      const registryPath = join(process.cwd(), "..", "artifacts", "milf_registry.json");
      const registry = JSON.parse(await Bun.file(registryPath).text());
      
      return Response.json({
        version: registry.version,
        ssot_hash: registry.ssot_hash,
        milfs: registry.milfs,
        total: registry.milfs.length,
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      const error = err as Error;
      console.error("[API] getMilfs error:", error);
      return Response.json({ 
        error: error.message,
        milfs: [],
        total: 0,
      }, { status: 500 });
    }
  },

  /**
   * GET /api/profiles - List all scoring profiles
   */
  async getProfiles(): Promise<Response> {
    try {
      const profilesPath = join(process.cwd(), "..", "artifacts", "scoring_profiles.json");
      const profiles = JSON.parse(await Bun.file(profilesPath).text());
      
      return Response.json({
        version: profiles.version,
        profiles: profiles.profiles,
        total: profiles.profiles.length,
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      const error = err as Error;
      console.error("[API] getProfiles error:", error);
      return Response.json({ 
        error: error.message,
        profiles: [],
        total: 0,
      }, { status: 500 });
    }
  },
};