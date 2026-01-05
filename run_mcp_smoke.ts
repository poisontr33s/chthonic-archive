#!/usr/bin/env bun
/**
 * MCP Smoke Suite Runner (Root-Level)
 * 
 * Purpose: One-command validation of MCP server baseline + all 4 tools
 * Location: chthonic-archive/ (root)
 * Usage: 
 *   bun run run_mcp_smoke.ts                       # Default validation (7 tests)
 *   bun run run_mcp_smoke.ts --node BLACKSMITH     # Custom dependency graph node query
 *   bun run run_mcp_smoke.ts --spectral GOLD       # Custom spectral frequency query
 *   bun run run_mcp_smoke.ts --dry-run             # Print requests without executing
 *   bun run run_mcp_smoke.ts --ensure-claude-code  # Ensure Claude Code installed/running first (Win11)
 * 
 * Validates:
 *   1. Server spawns and responds to initialize
 *   2. tools/list returns 4 tools (ping, scan_repository, validate_ssot_integrity, query_dependency_graph)
 *   3. Each tool executes successfully
 *   4. Responses match expected structure
 * 
 * Exit codes:
 *   0 = All validations passed
 *   1 = One or more validations failed
 * 
 * Design: Boring, explicit, inspectable, disposable.
 * No network, no CI, no remote dependencies.
 */

import { spawnSync } from "child_process";

const TIMEOUT_MS = 5000;
const EXPECTED_TOOL_COUNT = 4;
const EXPECTED_TOOLS = ["ping", "scan_repository", "validate_ssot_integrity", "query_dependency_graph"];

// Parse CLI arguments
const args = process.argv.slice(2);
let customQuery: string | null = null;
let dryRun = false;
let ensureClaudeCode = false;

for (let i = 0; i < args.length; i++) {
  if (args[i] === "--node" && args[i + 1]) {
    customQuery = `node ${args[i + 1]}`;
    i++;
  } else if (args[i] === "--spectral" && args[i + 1]) {
    customQuery = `spectral ${args[i + 1]}`;
    i++;
  } else if (args[i] === "--dependencies" && args[i + 1]) {
    customQuery = `dependencies ${args[i + 1]}`;
    i++;
  } else if (args[i] === "--dependents" && args[i + 1]) {
    customQuery = `dependents ${args[i + 1]}`;
    i++;
  } else if (args[i] === "--dry-run") {
    dryRun = true;
  } else if (args[i] === "--ensure-claude-code") {
    ensureClaudeCode = true;
  }
}

// Ensure Claude Code installed/running if requested (Win11 only)
function ensureClaude() {
  if (process.platform !== "win32") {
    console.log("--ensure-claude-code only supported on Windows (skipping).");
    return;
  }
  console.log("Ensuring Claude Code is installed & running...");
  const ps = spawnSync("powershell.exe", [
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "scripts\\launch_claude_code.ps1"
  ], { stdio: "inherit" });
  
  if (ps.status !== 0) {
    throw new Error(`launch_claude_code.ps1 failed with exit ${ps.status}`);
  }
  console.log("Claude Code ensured.\n");
}

if (ensureClaudeCode) {
  ensureClaude();
}

interface TestResult {
  name: string;
  passed: boolean;
  error?: string;
  details?: Record<string, unknown>;
}

const results: TestResult[] = [];

function logResult(result: TestResult): void {
  const status = result.passed ? "✓" : "✗";
  const color = result.passed ? "\x1b[32m" : "\x1b[31m";
  const reset = "\x1b[0m";
  console.log(`${color}${status}${reset} ${result.name}`);
  if (result.error) console.log(`  Error: ${result.error}`);
  if (result.details) {
    Object.entries(result.details).forEach(([k, v]) => 
      console.log(`  ${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`)
    );
  }
  results.push(result);
}

console.log("\n" + "=".repeat(80));
console.log(" ".repeat(25) + "MCP SMOKE SUITE RUNNER");
console.log(" ".repeat(28) + "chthonic-archive");
if (customQuery) {
  console.log(" ".repeat(22) + `Custom query: ${customQuery}`);
}
if (dryRun) {
  console.log(" ".repeat(30) + "(DRY RUN MODE)");
}
console.log("=".repeat(80) + "\n");

// Dry-run mode: print requests without executing
if (dryRun) {
  const requests = [
    { jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "smoke-runner", version: "1.0" } } },
    { jsonrpc: "2.0", id: 2, method: "tools/list" },
    { jsonrpc: "2.0", id: 3, method: "tools/call", params: { name: "ping", arguments: {} } },
    { jsonrpc: "2.0", id: 4, method: "tools/call", params: { name: "scan_repository", arguments: {} } },
    { jsonrpc: "2.0", id: 5, method: "tools/call", params: { name: "validate_ssot_integrity", arguments: {} } },
    { jsonrpc: "2.0", id: 6, method: "tools/call", params: { name: "query_dependency_graph", arguments: { query: customQuery || "stats" } } },
  ];
  
  console.log("The following JSON-RPC requests would be sent to the MCP server:\n");
  requests.forEach((req, idx) => {
    console.log(`[Request ${idx + 1}]`);
    console.log(JSON.stringify(req, null, 2));
    console.log();
  });
  
  console.log("Dry-run complete. No server spawned, no execution performed.");
  console.log("Run without --dry-run to execute validations.\n");
  process.exit(0);
}

// Spawn MCP server
const server = Bun.spawn(["bun", "run", "./mcp/server.ts"], {
  stdin: "pipe",
  stdout: "pipe",
  stderr: "inherit",
  cwd: import.meta.dir,
});

// Queue all requests (basic validation + optional custom query)
const requests = [
  { id: 1, method: "initialize", params: { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "smoke-runner", version: "1.0" } } },
  { id: 2, method: "tools/list" },
  { id: 3, method: "tools/call", params: { name: "ping", arguments: {} } },
  { id: 4, method: "tools/call", params: { name: "scan_repository", arguments: {} } },
  { id: 5, method: "tools/call", params: { name: "validate_ssot_integrity", arguments: {} } },
  { id: 6, method: "tools/call", params: { name: "query_dependency_graph", arguments: { query: customQuery || "stats" } } },
];

// Write all requests immediately
for (const req of requests) {
  server.stdin.write(JSON.stringify({ jsonrpc: "2.0", ...req }) + "\n");
}

// Collect responses
const responses: any[] = [];
const decoder = new TextDecoder();

setTimeout(() => {
  server.kill();
  
  // Validation 1: Initialize response
  const initResp = responses.find(r => r.id === 1);
  logResult({
    name: "Server initialize",
    passed: !!initResp?.result?.protocolVersion,
    details: { protocolVersion: initResp?.result?.protocolVersion },
  });
  
  // Validation 2: Tool list count
  const toolsResp = responses.find(r => r.id === 2);
  const tools = toolsResp?.result?.tools || [];
  logResult({
    name: `Tools list (expect ${EXPECTED_TOOL_COUNT})`,
    passed: tools.length === EXPECTED_TOOL_COUNT,
    details: { count: tools.length, tools: tools.map((t: any) => t.name) },
  });
  
  // Validation 3: All expected tools present
  const toolNames = tools.map((t: any) => t.name);
  const allPresent = EXPECTED_TOOLS.every(name => toolNames.includes(name));
  logResult({
    name: "All expected tools present",
    passed: allPresent,
    details: { 
      expected: EXPECTED_TOOLS, 
      found: toolNames,
      missing: EXPECTED_TOOLS.filter(n => !toolNames.includes(n))
    },
  });
  
  // Validation 4: ping tool
  const pingResp = responses.find(r => r.id === 3);
  try {
    const pingResult = pingResp?.result?.content?.[0]?.text ? JSON.parse(pingResp.result.content[0].text) : null;
    logResult({
      name: "ping",
      passed: pingResult?.pong === true,
      details: { result: pingResult },
    });
  } catch (e) {
    logResult({
      name: "ping",
      passed: false,
      error: e instanceof Error ? e.message : String(e),
    });
  }
  
  // Validation 5: scan_repository
  const scanResp = responses.find(r => r.id === 4);
  try {
    const scanResult = scanResp?.result?.content?.[0]?.text ? JSON.parse(scanResp.result.content[0].text) : null;
    logResult({
      name: "scan_repository",
      passed: typeof scanResult?.file_count === 'number' && scanResult.file_count > 0,
      details: { 
        file_count: scanResult?.file_count,
        repository: scanResult?.repository
      },
    });
  } catch (e) {
    logResult({
      name: "scan_repository",
      passed: false,
      error: e instanceof Error ? e.message : String(e),
    });
  }
  
  // Validation 6: validate_ssot_integrity
  const ssotResp = responses.find(r => r.id === 5);
  try {
    const ssotResult = ssotResp?.result?.content?.[0]?.text ? JSON.parse(ssotResp.result.content[0].text) : null;
    logResult({
      name: "validate_ssot_integrity",
      passed: ssotResult?.status === "valid" && !!ssotResult?.hash,
      details: { 
        status: ssotResult?.status,
        hash: ssotResult?.hash?.substring(0, 16) + "...",
        size: ssotResult?.size
      },
    });
  } catch (e) {
    logResult({
      name: "validate_ssot_integrity",
      passed: false,
      error: e instanceof Error ? e.message : String(e),
    });
  }
  
  // Validation 7: query_dependency_graph (custom or stats)
  const depResp = responses.find(r => r.id === 6);
  try {
    const depResult = depResp?.result?.content?.[0]?.text ? JSON.parse(depResp.result.content[0].text) : null;
    
    if (customQuery) {
      // Custom query validation - check for valid response (not error)
      const hasError = depResult && depResult.error;
      const validResponse = depResult && !hasError && (
        (customQuery.startsWith("node") && (depResult.id || depResult.node)) ||
        (customQuery.startsWith("dependencies") && Array.isArray(depResult.dependencies)) ||
        (customQuery.startsWith("dependents") && Array.isArray(depResult.dependents)) ||
        (customQuery.startsWith("spectral") && Array.isArray(depResult.nodes))
      );
      
      logResult({
        name: `query_dependency_graph (${customQuery})`,
        passed: !!validResponse,
        details: depResult ? {
          query: customQuery,
          result_keys: Object.keys(depResult).join(", "),
          sample: customQuery.startsWith("spectral") 
            ? { node_count: depResult.nodes?.length, first: depResult.nodes?.[0]?.id }
            : customQuery.startsWith("node")
            ? { id: depResult.id || depResult.node?.id, spectral_freq: depResult.spectral_freq || depResult.node?.spectral_freq }
            : { count: Array.isArray(depResult.dependencies) ? depResult.dependencies.length : depResult.dependents?.length }
        } : {},
        error: hasError ? depResult.error : undefined,
      });
    } else {
      // Default stats validation
      logResult({
        name: "query_dependency_graph (stats)",
        passed: typeof depResult?.total_nodes === 'number' && depResult.total_nodes > 0,
        details: { 
          total_nodes: depResult?.total_nodes,
          total_hyperedges: depResult?.total_hyperedges,
          spectral_frequencies: Object.keys(depResult?.spectral_distribution || {}).length
        },
      });
    }
  } catch (e) {
    logResult({
      name: "query_dependency_graph",
      passed: false,
      error: e instanceof Error ? e.message : String(e),
    });
  }
  
  // Summary
  const passCount = results.filter(r => r.passed).length;
  const totalCount = results.length;
  const allPassed = passCount === totalCount;
  
  console.log("\n" + "=".repeat(80));
  const summaryColor = allPassed ? "\x1b[32m" : "\x1b[31m";
  const reset = "\x1b[0m";
  console.log(`${summaryColor}RESULTS: ${passCount}/${totalCount} validations passed${reset}`);
  console.log("=".repeat(80) + "\n");
  
  if (!allPassed) {
    console.log("Failed validations:");
    results.filter(r => !r.passed).forEach(r => {
      console.log(`  - ${r.name}${r.error ? `: ${r.error}` : ''}`);
    });
    console.log();
  }
  
  process.exit(allPassed ? 0 : 1);
}, TIMEOUT_MS);

// Stream response collector
for await (const chunk of server.stdout) {
  const lines = decoder.decode(chunk).trim().split("\n");
  for (const line of lines) {
    if (line && line.startsWith("{")) {
      try {
        const parsed = JSON.parse(line);
        if (parsed.id && parsed.result) responses.push(parsed);
      } catch {
        // Ignore malformed lines
      }
    }
  }
}
