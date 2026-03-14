// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: bridge-server.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance: (standalone)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * Claude Code ↔ Chthonic Bridge Implementation
 *
 * @SID           TOOL_BRIDGE_SERVER_V1
 * @Shabti        CLI Script
 * @Heka-Ayni    CONCEPT_CLAUDE_CHTHONIC_BRIDGE
 * @Ankh-Tinku    STATE_BRIDGE_SERVER_ACTIVE
 * @Purpose       Bidirectional communication bridge between Claude Code
 *                and chthonic CLI. Runs as a background service accepting
 *                requests from both sides.
 * Which implementation would best serve your use case?
 */

import Bun from "bun";
import { spawn, exec } from "child_process";
import { randomUUID } from "crypto";
import path from "path";

interface BridgeRequest {
  id: string;
  source: "claude-ide" | "terminal" | "mcp";
  command: string;
  args: string[];
  context?: Record<string, unknown>;
  timestamp: number;
}

interface BridgeResponse {
  id: string;
  status: "success" | "error" | "pending";
  data?: unknown;
  error?: string;
  duration?: number;
  source: "bridge";
}

// ═══════════════════════════════════════════════════════════════════════════════
// CORE BRIDGE - CHOSEN: HTTP + stdio Hybrid
// ═══════════════════════════════════════════════════════════════════════════════

class ChthoniBridge {
  private port: number;
  private chthonic_root: string;
  private pending_requests: Map<string, BridgeResponse> = new Map();

  constructor(port: number = 8888, chthonic_root?: string) {
    this.port = port;
    this.chthonic_root = chthonic_root || process.env.CHTHONIC_REPO_ROOT || process.cwd();
  }

  /**
   * Execute chthonic command via PowerShell
   */
  private async executeChthonic(
    command: string,
    args: string[]
  ): Promise<{ stdout: string; stderr: string; code: number }> {
    return new Promise((resolve) => {
      const cmd = `chthonic ${command} ${args.map((a) => `"${a}"`).join(" ")}`;

      exec(cmd, { cwd: this.chthonic_root }, (error, stdout, stderr) => {
        resolve({
          stdout,
          stderr,
          code: error?.code || 0,
        });
      });
    });
  }

  /**
   * Process a bridge request
   */
  async handleRequest(req: BridgeRequest): Promise<BridgeResponse> {
    const startTime = Date.now();

    console.log(
      `[Bridge] ${req.source} → chthonic.${req.command}(${req.args.join(", ")})`
    );

    try {
      const result = await this.executeChthonic(req.command, req.args);

      if (result.code === 0) {
        return {
          id: req.id,
          status: "success",
          data: result.stdout,
          duration: Date.now() - startTime,
          source: "bridge",
        };
      } else {
        return {
          id: req.id,
          status: "error",
          error: result.stderr || `Exit code ${result.code}`,
          duration: Date.now() - startTime,
          source: "bridge",
        };
      }
    } catch (err) {
      return {
        id: req.id,
        status: "error",
        error: err instanceof Error ? err.message : String(err),
        duration: Date.now() - startTime,
        source: "bridge",
      };
    }
  }

  /**
   * Start HTTP server for bridge requests
   */
  async startHttpServer(): Promise<void> {
    const server = Bun.serve({
      port: this.port,
      fetch: async (req: Request) => {
        // CORS headers for Claude Code
        const corsHeaders = {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        };

        if (req.method === "OPTIONS") {
          return new Response(null, { headers: corsHeaders });
        }

        // POST /execute - Execute chthonic command
        if (req.method === "POST" && req.url.includes("/execute")) {
          try {
            const body = (await req.json()) as BridgeRequest;
            const response = await this.handleRequest(body);
            return new Response(JSON.stringify(response), {
              status: 200,
              headers: {
                "Content-Type": "application/json",
                ...corsHeaders,
              },
            });
          } catch (err) {
            return new Response(
              JSON.stringify({
                status: "error",
                error:
                  err instanceof Error ? err.message : "Invalid request",
              }),
              { status: 400, headers: corsHeaders }
            );
          }
        }

        // GET /status - Health check
        if (req.url.includes("/status")) {
          return new Response(
            JSON.stringify({
              status: "ok",
              version: "1.0.0",
              chthonic_root: this.chthonic_root,
              port: this.port,
              timestamp: new Date().toISOString(),
            }),
            {
              status: 200,
              headers: {
                "Content-Type": "application/json",
                ...corsHeaders,
              },
            }
          );
        }

        // GET / - Welcome
        return new Response(
          JSON.stringify({
            name: "🔥💀⚓ Claude Code ↔ Chthonic Bridge",
            version: "1.0.0",
            endpoints: {
              execute: "POST /execute - Execute chthonic command",
              status: "GET /status - Health check",
            },
            example: {
              curl:
                'curl -X POST http://localhost:8888/execute -H "Content-Type: application/json" -d \'{"command":"status","args":[]}\'',
            },
          }),
          {
            status: 200,
            headers: {
              "Content-Type": "application/json",
              ...corsHeaders,
            },
          }
        );
      },
    });

    console.log(`\n🚀 Bridge HTTP Server: http://localhost:${this.port}`);
    console.log(`   chthonic root: ${this.chthonic_root}`);
    console.log(`   Ready for Claude Code ↔ Terminal communication\n`);
  }

  /**
   * CLI command for testing bridge
   */
  async testBridge(): Promise<void> {
    console.log("\n🧪 Bridge Self-Test...\n");

    const tests: Array<{ cmd: string; args: string[] }> = [
      { cmd: "status", args: [] },
      { cmd: "resolve", args: ["--list"] },
      { cmd: "map", args: ["--json"] },
    ];

    for (const test of tests) {
      const req: BridgeRequest = {
        id: randomUUID(),
        source: "terminal",
        command: test.cmd,
        args: test.args,
        timestamp: Date.now(),
      };

      const response = await this.handleRequest(req);
      console.log(
        `✅ ${test.cmd}: ${response.status} (${response.duration}ms)`
      );

      if (response.status === "error") {
        console.log(`   Error: ${response.error}`);
      }
    }

    console.log("\n✨ Bridge tests complete\n");
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════════

async function main() {
  const bridge = new ChthoniBridge(8888);

  // Test the bridge
  await bridge.testBridge();

  // Start HTTP server
  await bridge.startHttpServer();

  // Keep process alive
  await new Promise(() => {});
}

main().catch((err) => {
  console.error("Bridge error:", err);
  process.exit(1);
});
