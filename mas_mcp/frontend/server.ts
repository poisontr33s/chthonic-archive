/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * 🧬 MAS-MCP Dashboard Server
 * Bun-native HTTP server for Genesis Scheduler monitoring
 * 
 * Uses Bun.serve with routes API (v1.2.3+) for zero-dependency routing
 * Bun v1.3.4 compatible with development mode
 * ═══════════════════════════════════════════════════════════════════════════════
 */

import { join } from "node:path";
import { apiRoutes, cycleControlRoutes } from "./api/routes";
import { config, paths } from "./lib/config";

const PUBLIC_DIR = paths.publicDir();

// Global state for hot reload persistence
declare global {
  var reloadCount: number;
}
globalThis.reloadCount ??= 0;
globalThis.reloadCount++;

const server = Bun.serve({
  port: config.port,
  hostname: config.host,
  development: true,
  
  routes: {
    // ═══════════════════════════════════════════════════════════════════════════
    // API Routes - JSON endpoints for MAS-MCP data
    // ═══════════════════════════════════════════════════════════════════════════
    
    "/api/health": () => Response.json({ 
      status: "ok", 
      version: "2.0.0",
      bun_version: Bun.version,
      gpu_provider: config.gpuProvider,
      reloads: globalThis.reloadCount,
      timestamp: new Date().toISOString(),
      paths: {
        logs: paths.logsDir(),
        artifacts: paths.artifactsDir(),
        registry: paths.entityRegistry(),
      },
    }),
    
    "/api/digest": apiRoutes.getDigest,
    "/api/digest/:date": apiRoutes.getDigestByDate,
    "/api/cycles": apiRoutes.getCycles,
    "/api/cycles/:id": apiRoutes.getCycleById,
    "/api/metrics": apiRoutes.getMetrics,
    "/api/metrics/history": apiRoutes.getMetricsHistory,
    "/api/monitoring": apiRoutes.getMonitoringScore,
    "/api/entities": apiRoutes.getEntities,
    "/api/entities/recent": apiRoutes.getRecentEntities,
    
    // ═══════════════════════════════════════════════════════════════════════════
    // Cycle Control Routes - IPC bridge to Python/uv backend (Phase 1 Gemini)
    // ═══════════════════════════════════════════════════════════════════════════
    
    "POST /api/cycle/start": cycleControlRoutes.startCycle,
    "/api/cycle/status": cycleControlRoutes.getCycleStatus,
    "/api/probe": cycleControlRoutes.runProbe,
    "POST /api/activate": cycleControlRoutes.activateMilfs,
    "/api/milfs": cycleControlRoutes.getMilfs,
    "/api/profiles": cycleControlRoutes.getProfiles,
    
    // ═══════════════════════════════════════════════════════════════════════════
    // Static Files - Bun.file() for zero-copy serving
    // ═══════════════════════════════════════════════════════════════════════════
    
    "/": () => new Response(Bun.file(join(PUBLIC_DIR, "index.html"))),
    "/styles.css": () => new Response(Bun.file(join(PUBLIC_DIR, "styles.css"))),
    "/app.js": () => new Response(Bun.file(join(PUBLIC_DIR, "app.js"))),
    "/favicon.ico": () => new Response(null, { status: 204 }),
  },
  
  // Fallback for unmatched routes
  fetch(req) {
    const url = new URL(req.url);
    const pathname = url.pathname;
    
    // Try serving static files from public/
    if (!pathname.startsWith("/api/")) {
      const file = Bun.file(join(PUBLIC_DIR, pathname));
      return new Response(file);
    }
    
    return Response.json({ error: "Not found", path: pathname }, { status: 404 });
  },
  
  error(error) {
    console.error("[Server Error]", error);
    return Response.json({ 
      error: "Internal server error", 
      message: error.message 
    }, { status: 500 });
  },
});

console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║  🧬 MAS-MCP Genesis Dashboard v2.0.0                                          ║
║  ─────────────────────────────────────────────────────────────────────────────║
║  Server:    ${server.url.toString().padEnd(63)}║
║  Bun:       v${Bun.version.padEnd(62)}║
║  Mode:      development (hot reload #${String(globalThis.reloadCount).padEnd(37)}║
║  ─────────────────────────────────────────────────────────────────────────────║
║  Logs:      ${paths.logsDir().padEnd(63)}║
║  Artifacts: ${paths.artifactsDir().padEnd(63)}║
║  GPU:       ${config.gpuProvider.padEnd(63)}║
╚═══════════════════════════════════════════════════════════════════════════════╝
`);

// Keep event loop alive with heartbeat (Bun Windows requirement)
setInterval(() => {
  // Heartbeat - keeps process alive
}, 1000 * 60);
