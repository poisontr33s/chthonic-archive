#!/usr/bin/env bun
/**
 * MCP Smoke Suite Runner (Root-Level)
 * 
 * Purpose: One-command validation of MCP server baseline + all 4 tools
 * Location: chthonic-archive/ (root)
 * Usage: bun run run_mcp_smoke.ts
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

const TIMEOUT_MS = 5000;
const EXPECTED_TOOL_COUNT = 4;
const EXPECTED_TOOLS = ["ping", "scan_repository", "validate_ssot_integrity", "query_dependency_graph"];

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
console.log("=".repeat(80) + "\n");

// Spawn MCP server
const server = Bun.spawn(["bun", "run", "./mcp/server.ts"], {
  stdin: "pipe",
  stdout: "pipe",
  stderr: "inherit",
  cwd: import.meta.dir,
});

// Queue all requests
const requests = [
  { id: 1, method: "initialize", params: { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "smoke-runner", version: "1.0" } } },
  { id: 2, method: "tools/list" },
  { id: 3, method: "tools/call", params: { name: "ping", arguments: {} } },
  { id: 4, method: "tools/call", params: { name: "scan_repository", arguments: {} } },
  { id: 5, method: "tools/call", params: { name: "validate_ssot_integrity", arguments: {} } },
  { id: 6, method: "tools/call", params: { name: "query_dependency_graph", arguments: { query: "stats" } } },
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
  
  // Validation 7: query_dependency_graph
  const depResp = responses.find(r => r.id === 6);
  try {
    const depResult = depResp?.result?.content?.[0]?.text ? JSON.parse(depResp.result.content[0].text) : null;
    logResult({
      name: "query_dependency_graph (stats)",
      passed: typeof depResult?.total_nodes === 'number' && depResult.total_nodes > 0,
      details: { 
        total_nodes: depResult?.total_nodes,
        total_hyperedges: depResult?.total_hyperedges,
        spectral_frequencies: Object.keys(depResult?.spectral_distribution || {}).length
      },
    });
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
