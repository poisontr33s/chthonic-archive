import { ok, fail, type MCPRequest } from "./protocol.ts";
import { scanRepository } from "./tools/scanRepository.ts";
import { validateSSOT } from "./tools/validateSSOT.ts";
import { queryDependencyGraph } from "./tools/queryDependencyGraph.ts";

async function dispatch(req: MCPRequest) {
  const { id, method, params = {} } = req;

  try {
    switch (method) {
      case "ping":
        return ok(id, { pong: true });

      case "scan_repository":
        return ok(id, await scanRepository());

      case "validate_ssot_integrity":
        return ok(id, await validateSSOT());

      case "query_dependency_graph":
        return ok(id, await queryDependencyGraph(params.query || ""));

      default:
        return fail(id, `Unknown method: ${method}`);
    }
  } catch (err: any) {
    return fail(id, err.message || "Internal error");
  }
}

async function main() {
  console.error("[MCP Server] Starting stdio server...");

  for await (const line of console) {
    if (!line.trim()) continue;

    try {
      const req = JSON.parse(line);
      const res = await dispatch(req);
      console.log(JSON.stringify(res));
    } catch (err: any) {
      console.error("[MCP Server] Parse error:", err.message);
    }
  }
}

main();
