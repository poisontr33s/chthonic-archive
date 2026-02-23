#!/usr/bin/env bun

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: run_mcp_validation.ts
// ║ MCP client integration - Observatory communication layer
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Spectral Frequency: ORANGE
// ║ Architectural Role: 🔭 THE OBSERVATORY
// ║ Purpose: MCP validation runner - local testing and queries
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Cross-References (Bidirectional):
// ║  (Standalone file - no detected dependencies)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * MCP Validation Runner (Root-Level)
 *
 * Purpose: Local validation and parameterized queries against MCP server
 * Location: chthonic-archive/ (root)
 * Usage:
 *   bun run run_mcp_validation.ts                       # Baseline validation (7 checks)
 *   bun run run_mcp_validation.ts --node BLACKSMITH     # Custom dependency graph node query
 *   bun run run_mcp_validation.ts --spectral GOLD       # Custom spectral frequency query
 *   bun run run_mcp_validation.ts --dry-run             # Print requests without executing
 *   bun run run_mcp_validation.ts --ensure-claude-code  # Ensure Claude Code installed/running first (Win11)
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
 * Design: Boring, explicit, inspectable, operational.
 * No network, no CI, no remote dependencies.
 */

import { spawnSync } from "child_process";
import { mkdirSync } from "fs";

// Some tools (scan, probe) can take a few seconds on a large repo; keep runner deterministic but not brittle.
const TIMEOUT_MS = 15000;
// Server tool surface changes over time; keep validation stable by asserting a required subset exists.
const MIN_TOOL_COUNT = 10;
const REQUIRED_TOOLS = [
  "chthonic_status",
  "chthonic_scan",
  "chthonic_validate_ssot",
  "polyglot_versions",
  "meta_cli",
];

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
console.log(" ".repeat(25) + "MCP VALIDATION RUNNER");
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
    { jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "validation-runner", version: "1.0" } } },
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
// Repo moved the server implementation into scripts/ (no top-level mcp/ directory).
const server = Bun.spawn(["bun", "run", "scripts/mcp-chthonic-server.ts"], {
  stdin: "pipe",
  stdout: "pipe",
  stderr: "inherit",
  cwd: process.cwd(),
});

// Queue all requests (basic validation + optional custom query)
const requests = [
  { id: 1, method: "initialize", params: { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "validation-runner", version: "1.0" } } },
  { id: 2, method: "tools/list" },
  { id: 3, method: "tools/call", params: { name: "chthonic_status", arguments: {} } },
  { id: 4, method: "tools/call", params: { name: "chthonic_scan", arguments: {} } },
  { id: 5, method: "tools/call", params: { name: "chthonic_validate_ssot", arguments: {} } },
  { id: 6, method: "tools/call", params: { name: "meta_cli", arguments: {} } },
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
    name: `Tools list (min ${MIN_TOOL_COUNT})`,
    passed: tools.length >= MIN_TOOL_COUNT,
    details: { count: tools.length, tools: tools.map((t: any) => t.name) },
  });

  // Validation 3: Required tools present (subset check)
  const toolNames = tools.map((t: any) => t.name);
  const allPresent = REQUIRED_TOOLS.every(name => toolNames.includes(name));
  logResult({
    name: "Required tools present",
    passed: allPresent,
    details: {
      required: REQUIRED_TOOLS,
      found: toolNames,
      missing: REQUIRED_TOOLS.filter(n => !toolNames.includes(n))
    },
  });

  function getToolText(respId: number): string {
    const resp = responses.find(r => r.id === respId);
    const txt = resp?.result?.content?.[0]?.text;
    return typeof txt === "string" ? txt : "";
  }

  function okToolText(txt: string): boolean {
    const t = (txt || "").trim();
    return t.length > 0 && !t.startsWith("Unknown tool:");
  }

  // Validation 4: chthonic_status
  const statusText = getToolText(3);
  try {
    logResult({
      name: "chthonic_status",
      passed: okToolText(statusText),
      details: { tail: statusText.split(/\r?\n/).slice(-5).join("\\n") },
    });
  } catch (e) {
    logResult({
      name: "chthonic_status",
      passed: false,
      error: e instanceof Error ? e.message : String(e),
    });
  }

  // Validation 5: chthonic_scan
  const scanText = getToolText(4);
  try {
    logResult({
      name: "chthonic_scan",
      passed: okToolText(scanText),
      details: { tail: scanText.split(/\r?\n/).slice(-5).join("\\n") },
    });
  } catch (e) {
    logResult({
      name: "chthonic_scan",
      passed: false,
      error: e instanceof Error ? e.message : String(e),
    });
  }

  // Validation 6: chthonic_validate_ssot
  const ssotText = getToolText(5);
  try {
    logResult({
      name: "chthonic_validate_ssot",
      passed: okToolText(ssotText) && /valid/i.test(ssotText),
      details: { tail: ssotText.split(/\r?\n/).slice(-5).join("\\n") },
    });
  } catch (e) {
    logResult({
      name: "chthonic_validate_ssot",
      passed: false,
      error: e instanceof Error ? e.message : String(e),
    });
  }

  // Validation 7: meta_cli (should respond; exact payload intentionally not constrained)
  const metaText = getToolText(6);
  try {
    logResult({
      name: "meta_cli",
      passed: okToolText(metaText),
      details: { tail: metaText.split(/\r?\n/).slice(-5).join("\\n") },
    });
  } catch (e) {
    logResult({
      name: "meta_cli",
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

  // Emit a deterministic run artifact for orchestrator validation.
  try {
    mkdirSync("artifacts", { recursive: true });
    const runId = new Date().toISOString().replace(/[:.]/g, "-");
    const outPath = `artifacts/mcp_run_validation_${runId}.json`;
    Bun.write(outPath, JSON.stringify({
      schema_version: 1,
      generated_on: new Date().toISOString(),
      server: { name: "chthonic-polyglot", tool_count: tools.length },
      results,
      all_passed: allPassed,
    }, null, 2) + "\n");
    console.log(`Wrote artifact: ${outPath}`);
  } catch (e) {
    console.error(`Failed to write mcp_run artifact: ${e instanceof Error ? e.message : String(e)}`);
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
