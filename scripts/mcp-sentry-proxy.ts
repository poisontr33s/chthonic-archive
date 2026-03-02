// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: mcp-sentry-proxy.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance: (standalone)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * MCP Sentry Proxy — VS Code stdio JSON-RPC 2.0
 *
 * @SID           TOOL_MCP_SENTRY_PROXY_V1
 * @Shabti        MCP Server (stdio transport)
 * @Heka-Ayni     CONCEPT_SENTRY_OBSERVABILITY
 * @Ankh-Tinku    STATE_SENTRY_PROXY_ACTIVE
 * @Purpose       VS Code-compatible MCP proxy for Sentry integration.
 */

// scripts/mcp-sentry-proxy.ts

import { createInterface } from "readline";
import fs from "fs";

const rl = createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

function reply(id: any, result?: any, error?: any) {
  const msg: any = { jsonrpc: "2.0", id };
  if (error) msg.error = error;
  else msg.result = result;
  process.stdout.write(JSON.stringify(msg) + "\n");
}

const SSOT_PATH = process.env.SSOT_PATH!;

function readSSOT() {
  try {
    return fs.readFileSync(SSOT_PATH, "utf8").slice(0, 4000);
  } catch (e) {
    return `ERROR reading SSOT: ${String(e)}`;
  }
}

rl.on("line", (line) => {
  let msg: any;
  try {
    msg = JSON.parse(line);
  } catch {
    return;
  }

  const { id, method, params } = msg;

  // REQUIRED
  if (method === "initialize") {
    reply(id, {
      protocolVersion: "2024-11-05",
      capabilities: {
        tools: {}
      },
      serverInfo: {
        name: "sentry-ssot-local",
        version: "0.1.0"
      }
    });
    return;
  }

  if (method === "initialized") {
    reply(id, null);
    return;
  }

  // REQUIRED
  if (method === "tools/list") {
    reply(id, {
      tools: [
        {
          name: "get_ssot",
          description: "Return SSOT text for Copilot grounding",
          inputSchema: {
            type: "object",
            properties: {}
          }
        }
      ]
    });
    return;
  }

  if (method === "tools/call") {
    if (params?.name === "get_ssot") {
      reply(id, {
        content: [
          {
            type: "text",
            text: readSSOT()
          }
        ]
      });
      return;
    }

    reply(id, null, {
      code: -32601,
      message: "Unknown tool"
    });
    return;
  }

  reply(id, null, {
    code: -32601,
    message: `Unknown method ${method}`
  });
});
