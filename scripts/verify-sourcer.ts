#!/usr/bin/env bun
// @SID: SCRIPT_VERIFY_SOURCER_V1

/**
 * verify-sourcer — E2E smoke test for mcp-sourcer (The Sourcer MCP face).
 *
 * Spawns the server as a real MCP client and asks it the questions that matter:
 * a known-canon entity must come back ROOTED with sources; The Sourcer must come
 * back ORPHAN; the orphan list must contain her. Proves the whole chain end to end:
 * bun -> mcp-sourcer -> uv -> ssot_loremaster.py -> SSOT, plus the citation manifest.
 *
 * Run:  bun run scripts/verify-sourcer.ts
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const REPO_ROOT = process.cwd();
let pass = 0;
let fail = 0;

function check(name: string, cond: boolean, detail = ""): void {
  if (cond) {
    pass++;
    console.log(`  PASS  ${name}`);
  } else {
    fail++;
    console.log(`  FAIL  ${name}${detail ? "  — " + detail : ""}`);
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function body(res: any): any {
  if (res?.isError) throw new Error("tool returned isError: " + res.content?.[0]?.text);
  return JSON.parse(res.content[0].text);
}

const transport = new StdioClientTransport({
  command: process.execPath, // the bun binary running this script
  args: ["run", "scripts/mcp-sourcer.ts"],
  cwd: REPO_ROOT,
  env: process.env as Record<string, string>,
});
const client = new Client({ name: "verify-sourcer", version: "1.0.0" }, { capabilities: {} });

try {
  await client.connect(transport);

  const tools = await client.listTools();
  const names = tools.tools.map((t) => t.name).sort();
  check("4 tools listed", names.length === 4, names.join(","));
  check("exposes sourcer_check", names.includes("sourcer_check"));

  // The question-mark on a known-canon entity: must be ROOTED with real sources.
  const ora = body(
    await client.callTool({ name: "sourcer_check", arguments: { name: "Orackla Nocticula" } }),
  );
  check("Orackla ROOTED", ora.rooted === true, String(ora.verdict));
  check("Orackla cites sources", (ora.hit_count ?? 0) > 0, `hits=${ora.hit_count}`);

  // The orphan, asked of the canon: must be ORPHAN.
  const src = body(
    await client.callTool({ name: "sourcer_check", arguments: { name: "Sourcer" } }),
  );
  check("Sourcer ORPHAN", src.rooted === false, String(src.verdict));

  // The Sourcer finds herself in the orphan list.
  const orphans = body(await client.callTool({ name: "sourcer_orphans", arguments: {} }));
  check(
    "orphans include the_sourcer",
    JSON.stringify(orphans).includes("the_sourcer"),
    `count=${orphans.orphan_count}`,
  );

  // The roster reflects the rooted four and the SSOT organ set.
  const roster = body(await client.callTool({ name: "sourcer_roster", arguments: {} }));
  check("roster rooted >= 4", (roster.summary?.rooted ?? 0) >= 4, `rooted=${roster.summary?.rooted}`);
  check(
    "roster carries SSOT organs",
    Array.isArray(roster.canonical_organs) && roster.canonical_organs.length > 20,
    `organs=${roster.canonical_organs?.length}`,
  );

  // Section search finds a known heading.
  const sec = body(await client.callTool({ name: "sourcer_section", arguments: { query: "Triumvirate" } }));
  check("section search returns hits", Array.isArray(sec) && sec.length > 0, `len=${Array.isArray(sec) ? sec.length : "n/a"}`);
} finally {
  await client.close();
}

console.log(`\nverify-sourcer: ${pass} PASS, ${fail} FAIL`);
process.exit(fail === 0 ? 0 : 1);
