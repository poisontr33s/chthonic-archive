import { ok, fail, type MCPRequest } from "./protocol.ts";
import { scanRepository } from "./tools/scanRepository.ts";
import { validateSSOT } from "./tools/validateSSOT.ts";
import { queryDependencyGraph } from "./tools/queryDependencyGraph.ts";

async function dispatch(req: MCPRequest): Promise<MCPResponse | null> {
  // Rule 1: Notifications have no id - never respond to them
  if (typeof req.id !== "number" && typeof req.id !== "string") {
    return null;
  }

  const { id, method, params = {} } = req;

  try {
    switch (method) {
      case "initialize":
        return ok(id, {
          protocolVersion: params.protocolVersion || "2024-11-05",
          serverInfo: {
            name: "chthonic-archive",
            version: "0.1.0",
          },
          capabilities: {
            tools: {},
          },
        });

      case "tools/list":
        return ok(id, {
          tools: [
            {
              name: "ping",
              description: "Ping the MCP server to verify connectivity",
              inputSchema: {
                type: "object",
                properties: {},
              },
            },
            {
              name: "scan_repository",
              description: "Scan the chthonic-archive repository and return file statistics",
              inputSchema: {
                type: "object",
                properties: {},
              },
            },
            {
              name: "validate_ssot_integrity",
              description: "Validate SSOT (.github/copilot-instructions.md) integrity via SHA-256 hash",
              inputSchema: {
                type: "object",
                properties: {},
              },
            },
            {
              name: "query_dependency_graph",
              description: "Query the dependency graph (supports: node <file>, dependencies <file>, dependents <file>, spectral <freq>, stats)",
              inputSchema: {
                type: "object",
                properties: {
                  query: {
                    type: "string",
                    description: "Query command: 'node <filename>', 'dependencies <filename>', 'dependents <filename>', 'spectral <RED|ORANGE|GOLD|BLUE|WHITE|INDIGO|VIOLET>', or 'stats'",
                  },
                },
                required: ["query"],
              },
            },
          ],
        });

      case "tools/call":
        const toolName = params.name;
        const toolArgs = params.arguments || {};

        switch (toolName) {
          case "ping":
            return ok(id, { content: [{ type: "text", text: JSON.stringify({ pong: true }, null, 2) }] });

          case "scan_repository":
            const scanResult = await scanRepository();
            return ok(id, { content: [{ type: "text", text: JSON.stringify(scanResult, null, 2) }] });

          case "validate_ssot_integrity":
            const validateResult = await validateSSOT();
            return ok(id, { content: [{ type: "text", text: JSON.stringify(validateResult, null, 2) }] });

          case "query_dependency_graph":
            const queryResult = await queryDependencyGraph(toolArgs.query || "stats");
            return ok(id, { content: [{ type: "text", text: queryResult }] });

          default:
            return fail(id, `Unknown tool: ${toolName}`, -32601);
        }

      default:
        return fail(id, `Method not found: ${method}`, -32601);
    }
  } catch (err: any) {
    return fail(id, err.message || "Internal error");
  }
}

async function main() {
  console.error("[MCP Server] Starting stdio server...");

  process.stdin.setEncoding("utf8");
  let buffer = "";

  for await (const chunk of process.stdin) {
    buffer += chunk;
    let idx;
    while ((idx = buffer.indexOf("\n")) !== -1) {
      const line = buffer.slice(0, idx).trim();
      buffer = buffer.slice(idx + 1);
      if (!line) continue;

      let req: MCPRequest;
      try {
        req = JSON.parse(line);
      } catch {
        // Parse error for malformed JSON - we can't even extract an id
        // Skip silently per MCP spec (can't respond without valid id)
        console.error("[MCP Server] Parse error:", line);
        continue;
      }

      const res = await dispatch(req);
      // Rule 2: Only write response if dispatch returned one (null = notification)
      if (res) {
        process.stdout.write(JSON.stringify(res) + "\n");
      }
    }
  }
}

main().catch((e) => {
  console.error("[MCP Server] Fatal error:", e);
  process.exit(1);
});
