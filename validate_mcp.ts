#!/usr/bin/env bun
/**
 * MCP Smoke Suite - Via MCP Tool Call
 * 
 * Demonstrates calling run_smoke_suite through MCP protocol
 * This is the "automated" version - MCP server validates itself
 * 
 * Usage: bun run validate_mcp.ts
 */

const server = Bun.spawn(["bun", "run", "./mcp/server.ts"], {
  stdin: "pipe",
  stdout: "pipe",
  stderr: "inherit",
  cwd: import.meta.dir,
});

const requests = [
  { id: 1, method: "initialize", params: { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "validator", version: "1.0" } } },
  { id: 2, method: "tools/call", params: { name: "run_smoke_suite", arguments: {} } },
];

for (const req of requests) {
  server.stdin.write(JSON.stringify({ jsonrpc: "2.0", ...req }) + "\n");
}

const responses: any[] = [];
const decoder = new TextDecoder();

setTimeout(() => {
  server.kill();
  
  const smokeResp = responses.find(r => r.id === 2);
  if (!smokeResp?.result?.content?.[0]?.text) {
    console.error("❌ No smoke suite response received");
    process.exit(1);
  }
  
  const result = JSON.parse(smokeResp.result.content[0].text);
  
  console.log("\n" + "=".repeat(80));
  console.log(" ".repeat(25) + "MCP SERVER VALIDATION");
  console.log("=".repeat(80));
  console.log(`\nTimestamp: ${result.timestamp}`);
  console.log(`Total Validations: ${result.total_validations}`);
  console.log(`Passed: ${result.passed} | Failed: ${result.failed}`);
  console.log(`Overall: ${result.success ? "✅ SUCCESS" : "❌ FAILURE"}`);
  
  console.log("\nValidation Details:");
  result.validations.forEach((v: any, i: number) => {
    const icon = v.passed ? "✓" : "✗";
    const color = v.passed ? "\x1b[32m" : "\x1b[31m";
    const reset = "\x1b[0m";
    console.log(`${color}${icon}${reset} [${i + 1}/${result.total_validations}] ${v.name}`);
    
    if (v.details?.result && typeof v.details.result === 'object') {
      Object.entries(v.details.result).forEach(([k, val]) => {
        const display = typeof val === 'object' ? JSON.stringify(val) : val;
        console.log(`    ${k}: ${display}`);
      });
    }
    
    if (v.error) {
      console.log(`    ${color}Error: ${v.error}${reset}`);
    }
  });
  
  console.log("\n" + "=".repeat(80) + "\n");
  
  process.exit(result.success ? 0 : 1);
}, 4000);

for await (const chunk of server.stdout) {
  const lines = decoder.decode(chunk).trim().split("\n");
  for (const line of lines) {
    if (line && line.startsWith("{")) {
      try {
        const parsed = JSON.parse(line);
        if (parsed.id && parsed.result) responses.push(parsed);
      } catch {}
    }
  }
}
