// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: claude-chthonic-bridge.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance: (standalone)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * Claude Code ↔ Chthonic Bridge protocol
 *
 * @SID           TOOL_CLAUDE_CHTHONIC_BRIDGE_V1
 * @Shabti        CLI Script
 * @Heka-Ayni     CONCEPT_CLAUDE_CHTHONIC_BRIDGE
 * @Ankh-Tinku    STATE_BRIDGE_PROTOCOL_ACTIVE
 * @Purpose       Cross-communication protocol bridging Claude Code IDE
 *                with chthonic polyglot CLI for context-aware coding.
 */

import Bun from "bun";
import { spawn } from "child_process";

// ═══════════════════════════════════════════════════════════════════════════════
// BRIDGE ARCHITECTURE
// ═══════════════════════════════════════════════════════════════════════════════

interface BridgeConfig {
  socketPath: string;
  chthronicRoot: string;
  claudePort: number;
  protocol: "stdio" | "socket" | "ipc";
}

interface Request {
  id: string;
  source: "claude" | "terminal";
  type: "command" | "query" | "context";
  payload: unknown;
  timestamp: number;
}

interface Response {
  id: string;
  status: "success" | "error" | "pending";
  data?: unknown;
  error?: string;
}

// ═══════════════════════════════════════════════════════════════════════════════
// PROPOSED SOLUTIONS (for Claude Code to review)
// ═══════════════════════════════════════════════════════════════════════════════

const PROPOSED_ARCHITECTURES = {
  // Solution 1: Unix Socket IPC (Fast, Local-Only)
  unixSocket: {
    name: "Unix Socket IPC",
    pros: [
      "Zero network overhead",
      "Native permission model",
      "Supports file descriptors",
    ],
    cons: ["Windows requires WSL or named pipes", "Process-local only"],
    implementation:
      "Use Bun.listen() with Unix socket, create named pipe for Windows",
    recommended: true,
  },

  // Solution 2: Named Pipes (Windows Native)
  namedPipes: {
    name: "Windows Named Pipes",
    pros: [
      "Native Windows support",
      "Built-in security ACLs",
      "Cross-process messaging",
    ],
    cons: ["Not portable to Unix/Linux", "More complex API"],
    implementation:
      "Use node:net with named pipes (e.g., '\\\\.\\pipe\\chthonic-bridge')",
    recommended: true,
  },

  // Solution 3: HTTP/JSON-RPC Server
  jsonRpc: {
    name: "HTTP/JSON-RPC 2.0",
    pros: [
      "Language agnostic",
      "Well-defined protocol",
      "Easy debugging (curl/postman)",
    ],
    cons: ["Higher overhead than IPC", "Requires port binding"],
    implementation:
      "Create HTTP server with JSON-RPC endpoints for each chthonic command",
    recommended: false,
  },

  // Solution 4: WebSocket Bridge
  websocket: {
    name: "WebSocket Bridge",
    pros: [
      "Real-time bidirectional communication",
      "Supports multiplexing",
      "IDE-friendly (many IDEs support WS)",
    ],
    cons: ["HTTP upgrade overhead", "More complex than IPC"],
    implementation:
      "Bun native WebSocket server with message routing to chthonic CLI",
    recommended: false,
  },

  // Solution 5: stdin/stdout JSON Streaming
  stdio: {
    name: "stdio JSON Streaming",
    pros: [
      "Simplest implementation",
      "No extra dependencies",
      "Claude Code already uses this",
    ],
    cons: ["Single connection", "No multiplexing"],
    implementation: "Start chthonic process, send JSON lines via stdin",
    recommended: true,
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
// BRIDGE IMPLEMENTATION OPTIONS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Option A: Stdio Bridge (Simplest, Works Now)
 *
 * Flow:
 * 1. Claude Code sends request as JSON to stdin
 * 2. Bridge process spawns chthonic CLI
 * 3. Results returned as JSON to stdout
 * 4. Claude Code processes response
 */
class StdioBridge {
  async executeChthonic(command: string, args: string[]): Promise<Response> {
    const id = crypto.randomUUID();
    try {
      const proc = spawn("pwsh", [
        "-NoProfile",
        "-Command",
        `chthonic ${command} ${args.join(" ")}`,
      ]);

      let output = "";
      let error = "";

      proc.stdout.on("data", (data) => {
        output += data.toString();
      });
      proc.stderr.on("data", (data) => {
        error += data.toString();
      });

      return new Promise((resolve) => {
        proc.on("close", (code) => {
          resolve({
            id,
            status: code === 0 ? "success" : "error",
            data: output,
            error: error || undefined,
          });
        });
      });
    } catch (err) {
      return {
        id,
        status: "error",
        error: err instanceof Error ? err.message : String(err),
      };
    }
  }
}

/**
 * Option B: Named Pipe Bridge (Windows Native, Fast)
 *
 * Flow:
 * 1. Listen on \\.\pipe\chthonic-bridge
 * 2. Claude Code connects and sends JSON requests
 * 3. Bridge spawns chthonic in subprocess
 * 4. Results piped back through named pipe
 */
class NamedPipeBridge {
  private pipeName = "\\\\.\\pipe\\chthonic-bridge";

  async start(): Promise<void> {
    // Requires implementation with node:net or third-party library
    console.log(`Named pipe bridge would listen on: ${this.pipeName}`);
  }
}

/**
 * Option C: HTTP Server Bridge (Most Flexible)
 *
 * Flow:
 * 1. Start HTTP server on localhost:9999
 * 2. Claude Code sends POST /api/execute with JSON request
 * 3. Server spawns chthonic process
 * 4. Returns JSON response with results
 *
 * Example:
 *   POST http://localhost:9999/api/execute
 *   {"command": "status", "args": []}
 */
class HttpBridge {
  private port: number;

  constructor(port: number = 9999) {
    this.port = port;
  }

  async start(): Promise<void> {
    const server = Bun.serve({
      port: this.port,
      async fetch(req: Request) {
        if (req.method === "POST" && req.url.endsWith("/api/execute")) {
          const body = await req.json();
          const response = await this.executeChthonic(
            body.command,
            body.args
          );
          return new Response(JSON.stringify(response), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }

        return new Response("Not found", { status: 404 });
      },

      executeChthonic: async (command: string, args: string[]) => {
        // Implementation similar to StdioBridge
        return { status: "success", data: "placeholder" };
      },
    });

    console.log(`HTTP Bridge listening on http://localhost:${this.port}`);
  }
}

/**
 * Option D: WebSocket Bridge (Real-Time Bidirectional)
 *
 * Flow:
 * 1. Bun WebSocket server on ws://localhost:9999
 * 2. Claude Code WebSocket client connects
 * 3. Sends JSON request: {"cmd": "status"}
 * 4. Server responds with JSON: {"status": "success", "data": {...}}
 */
class WebSocketBridge {
  private port: number;

  constructor(port: number = 9999) {
    this.port = port;
  }

  async start(): Promise<void> {
    Bun.serve({
      port: this.port,
      fetch(req: Request, server: any) {
        if (server.upgrade(req)) {
          return;
        }
        return new Response("WebSocket bridge ready");
      },
      websocket: {
        message: async (ws: any, message: string) => {
          try {
            const req = JSON.parse(message);
            const response = await this.handleRequest(req);
            ws.send(JSON.stringify(response));
          } catch (err) {
            ws.send(
              JSON.stringify({
                status: "error",
                error: err instanceof Error ? err.message : String(err),
              })
            );
          }
        },
      },

      handleRequest: async (req: any) => ({
        status: "success",
        data: "placeholder",
      }),
    });

    console.log(`WebSocket Bridge listening on ws://localhost:${this.port}`);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// QUESTIONS FOR CLAUDE CODE
// ═══════════════════════════════════════════════════════════════════════════════

const CLAUDE_CODE_QUESTIONS = `
🤖 Questions for Claude Code IDE:

1. ARCHITECTURE SELECTION
   - Which IPC mechanism would work best for Claude Code ↔ Chthonic bridge?
   - Named pipes (Windows) vs HTTP vs WebSocket vs stdio?
   - What are the latency/throughput requirements?

2. INTEGRATION POINTS
   - How should Claude Code commands send requests to chthonic?
   - Should we create custom CLI tools in Claude Code that map to chthonic commands?
   - Can we use MCP protocol to expose chthonic tools directly?

3. CONTEXT SHARING
   - How can Claude Code share its session context with chthonic?
   - Should we sync file state bidirectionally?
   - What metadata should flow in both directions?

4. ERROR HANDLING
   - How to surface chthonic command failures in Claude Code?
   - Should errors interrupt the AI conversation or just log?
   - What retry logic would be appropriate?

5. PERFORMANCE
   - Maximum acceptable latency for command execution?
   - Should we batch multiple commands or execute serially?
   - How to handle long-running chthonic operations?

6. SECURITY
   - Should all chthonic commands be allowed, or create ACL?
   - How to prevent recursive loops (Claude Code → chthonic → Claude Code)?
   - What user context should bridge commands run under?
`;

console.log(CLAUDE_CODE_QUESTIONS);

// ═══════════════════════════════════════════════════════════════════════════════
// RECOMMENDATION: HYBRID APPROACH
// ═══════════════════════════════════════════════════════════════════════════════

const RECOMMENDED_SOLUTION = `
🎯 RECOMMENDED HYBRID SOLUTION:

Phase 1 (Immediate): stdio JSON Streaming
  ├─ Leverage existing Claude Code CLI
  ├─ Create command parser: "!chthonic <cmd> <args>"
  ├─ Route to BridgeExecutor
  └─ Return results as formatted messages

Phase 2 (Short-term): HTTP API Server
  ├─ Start HTTP bridge on startup
  ├─ Expose REST endpoints: /api/chthonic/*
  ├─ Support concurrent requests
  └─ Enable external tool integration

Phase 3 (Long-term): MCP Protocol Unification
  ├─ Use existing @chthonic MCP server (19 tools)
  ├─ Make all chthonic commands available as MCP tools
  ├─ Bidirectional context sync
  └─ Full IDE integration

DEFAULT IMPLEMENTATION: Phase 1 + Phase 2
  • Simple to implement (1-2 hours)
  • Works immediately with Claude Code
  • Scalable to full MCP integration
  • No breaking changes to existing setup
`;

console.log(RECOMMENDED_SOLUTION);

export { StdioBridge, NamedPipeBridge, HttpBridge, WebSocketBridge };
