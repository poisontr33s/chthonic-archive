#!/usr/bin/env bun
// @SID: memory-ingester — ingests global /memories/*.md into corpus memory_snapshots
// Reads from VS Code Copilot Chat globalStorage memory-tool/memories/ directory.
// Stores as sessionId='_global_' so they're queryable via corpus MCP.
//
// Usage:
//   bun run scripts/memory-ingester.ts              # ingest global memories
//   bun run scripts/memory-ingester.ts --dry-run    # show what would be ingested
//   bun run scripts/memory-ingester.ts --verbose    # show per-file status

import { Database } from "bun:sqlite";
import { existsSync, readdirSync, readFileSync } from "fs";
import { join } from "path";
import * as os from "os";

const args = process.argv.slice(2);
const dryRun = args.includes("--dry-run");
const verbose = args.includes("--verbose");

const appdata = process.env["APPDATA"] ?? join(os.homedir(), "AppData", "Roaming");
const globalMemoriesDir = join(
  appdata,
  "Code - Insiders",
  "User",
  "globalStorage",
  "github.copilot-chat",
  "memory-tool",
  "memories"
);

const manifestDir = join(import.meta.dir, "..", "manifest");
const corpusPath  = join(manifestDir, "corpus.sqlite");

const GLOBAL_SESSION_ID = "_global_";

function log(msg: string) { console.log(msg); }
function vlog(msg: string) { if (verbose) console.log(msg); }

if (!existsSync(globalMemoriesDir)) {
  console.error(`❌ Global memories dir not found: ${globalMemoriesDir}`);
  process.exit(1);
}

if (!existsSync(corpusPath)) {
  console.error(`❌ Corpus not found: ${corpusPath}`);
  console.error(`   Run: bun run session:corpus first`);
  process.exit(1);
}

const files = readdirSync(globalMemoriesDir).filter(f =>
  f.endsWith(".md") || f.endsWith(".json") || f.endsWith(".txt")
);

if (files.length === 0) {
  log("⚠️  No memory files found in global memories directory");
  process.exit(0);
}

log(`📂 Found ${files.length} global memory file(s) in:\n   ${globalMemoriesDir}`);

if (dryRun) {
  log("\n[dry-run] Would ingest:");
  for (const f of files) {
    const bytes = readFileSync(join(globalMemoriesDir, f)).length;
    log(`  ${f} (${bytes} bytes)`);
  }
  process.exit(0);
}

const db = new Database(corpusPath);

// Ensure _global_ session row exists (synthetic session for global memories)
db.run(`
  INSERT OR IGNORE INTO sessions (sessionId, startTime, workspaceHash, turns, intent, ingestedAt)
  VALUES ('${GLOBAL_SESSION_ID}', '2000-01-01T00:00:00.000Z', 'global', 0, 'Global user memory files', datetime('now'))
`);

const capturedAt = new Date().toISOString();

const upsert = db.prepare(`
  INSERT INTO memory_snapshots (sessionId, filename, content, capturedAt)
  VALUES (?, ?, ?, ?)
  ON CONFLICT DO UPDATE SET content=excluded.content, capturedAt=excluded.capturedAt
`);

// SQLite doesn't have ON CONFLICT without a unique index — ensure one exists
db.run(`
  CREATE UNIQUE INDEX IF NOT EXISTS idx_mem_session_file
  ON memory_snapshots(sessionId, filename)
`);

let ingested = 0;
let skipped = 0;

db.transaction(() => {
  for (const f of files) {
    const filePath = join(globalMemoriesDir, f);
    let content = "";
    try {
      content = readFileSync(filePath, "utf8");
    } catch (e) {
      vlog(`  ⚠️  skip ${f}: read error`);
      skipped++;
      continue;
    }
    upsert.run(GLOBAL_SESSION_ID, f, content, capturedAt);
    vlog(`  ✅ ${f} (${content.length} bytes)`);
    ingested++;
  }
})();

db.close();

log(`\n✅ Ingested ${ingested} global memory file(s) → memory_snapshots (sessionId='${GLOBAL_SESSION_ID}')`);
if (skipped > 0) log(`   ⚠️  Skipped ${skipped} file(s) due to read errors`);
log(`\n   Query: bun run scripts/session-query.ts --sql "SELECT filename, LENGTH(content) AS bytes FROM memory_snapshots WHERE sessionId='_global_'"`);
