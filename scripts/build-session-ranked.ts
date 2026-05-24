#!/usr/bin/env bun
// @SID: SCRIPT_SESSION_RANKED_G6_V1
// ============================================================
// build-session-ranked — G6 boomerang closer
//
// Builds the session_ranked composite score table in corpus.sqlite
// and emits manifest/session_ranked_index.json for consumption by
// tools/chthonic-mcp (SystemMessageTransform).
//
// Inputs:
//   manifest/sessions_index.json       → session metadata + startTime
//   manifest/session_blood.json        → per-session turns/edits/commands
//   manifest/gpu_scores_*.json         → per-turn semanticScore arrays
//
// Score formula (composite = recency × semantic_blend):
//   recency       = exp(-λ × days_since_start)   λ = ln(2)/7  (half-life 7d)
//   semantic      = 0.5 × avg_semantic + 0.3 × max_semantic
//                 + 0.1 × ln(turns+1) + 0.1 × ln(edits+1)
//   composite     = recency × semantic
//
// Usage:
//   bun run scripts/build-session-ranked.ts
//   bun run scripts/build-session-ranked.ts --dry-run   (no DB write)
// ============================================================

import { Database } from "bun:sqlite";
import { join, dirname } from "path";
import { existsSync, readdirSync, readFileSync, writeFileSync } from "fs";
import { fileURLToPath } from "url";

// ── Paths ─────────────────────────────────────────────────────────────────────

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const MANIFEST = join(SCRIPT_DIR, "..", "manifest");
const DB_PATH = join(MANIFEST, "corpus.sqlite");
const RANKED_OUT = join(MANIFEST, "session_ranked_index.json");

// ── Constants ─────────────────────────────────────────────────────────────────

const LAMBDA = Math.LN2 / 7; // half-life 7 days → decay = exp(-ln(2)/7 × days)
const NOW_MS = Date.now();

// ── Types ─────────────────────────────────────────────────────────────────────

interface SessionIndexEntry {
  sessionId: string;
  startTime: string;
  archivedAt?: string;
  turns?: number;
  workspaceName?: string;
  workspaceHash?: string;
  copilotVersion?: string;
  lines?: number;
}

interface BloodEntry {
  sessionId: string;
  turns: number;
  fileEditCount: number;
  commandCount: number;
  codeBlockCount: number;
  sessionIntent?: string;
}

interface GpuScore {
  turn: number;
  semanticScore: number;
  clusterLabel?: number;
  cosineSimilarityToCentroid?: number;
}

interface GpuScoresFile {
  sessionId: string;
  scoredTurns: GpuScore[];
}

interface RankedSession {
  rank: number;
  sessionId: string;
  composite: number;
  recency: number;
  avgSemantic: number;
  maxSemantic: number;
  turns: number;
  edits: number;
  commands: number;
  startTime: string;
  workspaceName: string;
  intent: string;
}

// ── Loaders ───────────────────────────────────────────────────────────────────

function loadJson<T>(path: string): T {
  const raw = readFileSync(path, "utf8");
  return JSON.parse(raw) as T;
}

function loadGpuScores(manifest: string): Map<string, GpuScore[]> {
  const map = new Map<string, GpuScore[]>();
  for (const fname of readdirSync(manifest)) {
    const m = fname.match(/^gpu_scores_([0-9a-f]{8})\.json$/);
    if (!m) continue;
    try {
      const file = loadJson<GpuScoresFile>(join(manifest, fname));
      // Key by first 8 chars of the embedded sessionId (matches the filename prefix)
      const prefix = (file.sessionId ?? "").slice(0, 8) || m[1];
      map.set(prefix, Array.isArray(file.scoredTurns) ? file.scoredTurns : []);
    } catch {
      // malformed file — skip silently
    }
  }
  return map;
}

// ── Score engine ──────────────────────────────────────────────────────────────

function computeRanked(
  sessions: SessionIndexEntry[],
  bloodMap: Map<string, BloodEntry>,
  gpuMap: Map<string, GpuScore[]>
): RankedSession[] {
  const scored = sessions.map((s) => {
    // Recency decay
    const startMs = new Date(s.startTime).getTime();
    const days = (NOW_MS - startMs) / 86_400_000;
    const recency = Math.exp(-LAMBDA * days);

    // Semantic signals
    const prefix = s.sessionId.slice(0, 8);
    const scores = gpuMap.get(prefix) ?? [];
    const validScores = scores.filter(
      (x) => typeof x.semanticScore === "number" && !isNaN(x.semanticScore)
    );
    const avgSemantic =
      validScores.length > 0
        ? validScores.reduce((a, b) => a + b.semanticScore, 0) / validScores.length
        : 0;
    const maxSemantic =
      validScores.length > 0
        ? Math.max(...validScores.map((x) => x.semanticScore))
        : 0;

    // Activity signals from blood drain
    const blood = bloodMap.get(s.sessionId);
    const turns = blood?.turns ?? s.turns ?? 0;
    const edits = blood?.fileEditCount ?? 0;
    const commands = blood?.commandCount ?? 0;

    // Composite
    const semanticBlend =
      0.5 * avgSemantic +
      0.3 * maxSemantic +
      0.1 * Math.log(turns + 1) +
      0.1 * Math.log(edits + 1);
    const composite = recency * semanticBlend;

    return {
      rank: 0,
      sessionId: s.sessionId,
      composite: parseFloat(composite.toFixed(4)),
      recency: parseFloat(recency.toFixed(4)),
      avgSemantic: parseFloat(avgSemantic.toFixed(4)),
      maxSemantic: parseFloat(maxSemantic.toFixed(4)),
      turns,
      edits,
      commands,
      startTime: s.startTime,
      workspaceName: s.workspaceName ?? "unknown",
      intent: blood?.sessionIntent ?? "",
    } satisfies RankedSession;
  });

  return scored
    .sort((a, b) => b.composite - a.composite)
    .map((r, i) => ({ ...r, rank: i + 1 }));
}

// ── DB writer ─────────────────────────────────────────────────────────────────

function writeToDb(ranked: RankedSession[]): void {
  if (!existsSync(DB_PATH)) {
    console.warn(`[G6] corpus.sqlite not found at ${DB_PATH} — skipping DB write`);
    return;
  }

  const db = new Database(DB_PATH);

  // Shadow table backing the VIEW
  db.run(`
    CREATE TABLE IF NOT EXISTS session_ranked_data (
      sessionId     TEXT PRIMARY KEY,
      rank          INTEGER NOT NULL,
      composite     REAL    NOT NULL,
      recency       REAL    NOT NULL,
      avg_semantic  REAL    NOT NULL,
      max_semantic  REAL    NOT NULL,
      turns         INTEGER NOT NULL DEFAULT 0,
      edits         INTEGER NOT NULL DEFAULT 0,
      commands      INTEGER NOT NULL DEFAULT 0,
      intent        TEXT    NOT NULL DEFAULT '',
      built_at      TEXT    NOT NULL
    )
  `);

  // G6 perf: indexes for warmstart-selection queries (ORDER BY composite DESC / rank).
  // Without these, session-truncator.ts --top mode scans linearly.
  db.run(`CREATE INDEX IF NOT EXISTS session_ranked_data_composite_idx
            ON session_ranked_data(composite DESC)`);
  db.run(`CREATE INDEX IF NOT EXISTS session_ranked_data_rank_idx
            ON session_ranked_data(rank)`);

  // Upsert all ranked rows
  const upsert = db.prepare(`
    INSERT OR REPLACE INTO session_ranked_data
      (sessionId, rank, composite, recency, avg_semantic, max_semantic,
       turns, edits, commands, intent, built_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  const now = new Date().toISOString();
  for (const r of ranked) {
    upsert.run(
      r.sessionId,
      r.rank,
      r.composite,
      r.recency,
      r.avgSemantic,
      r.maxSemantic,
      r.turns,
      r.edits,
      r.commands,
      r.intent,
      now
    );
  }

  // Drop + recreate VIEW (idempotent)
  db.run("DROP VIEW IF EXISTS session_ranked");
  db.run(`
    CREATE VIEW session_ranked AS
      SELECT
        s.sessionId,
        s.startTime,
        s.workspaceHash,
        s.workspaceName,
        s.copilotVersion,
        s.turns         AS corpus_turns,
        s.intent        AS corpus_intent,
        sd.rank,
        sd.composite,
        sd.recency,
        sd.avg_semantic,
        sd.max_semantic,
        sd.turns        AS blood_turns,
        sd.edits,
        sd.commands,
        sd.intent       AS score_intent,
        sd.built_at
      FROM sessions s
      JOIN session_ranked_data sd USING (sessionId)
      ORDER BY sd.rank
  `);

  db.close();
  console.log(`[G6] corpus.sqlite updated — session_ranked VIEW + session_ranked_data table (${ranked.length} rows)`);
}

// ── Main ──────────────────────────────────────────────────────────────────────

function main(): void {
  const dryRun = process.argv.includes("--dry-run");

  // Load inputs
  const sessions = loadJson<SessionIndexEntry[]>(join(MANIFEST, "sessions_index.json"));
  const bloodArr = loadJson<BloodEntry[]>(join(MANIFEST, "session_blood.json"));
  const bloodMap = new Map(bloodArr.map((b) => [b.sessionId, b]));
  const gpuMap = loadGpuScores(MANIFEST);

  console.log(
    `[G6] Inputs: ${sessions.length} sessions · ${bloodArr.length} blood entries · ${gpuMap.size} gpu_scores files`
  );

  const ranked = computeRanked(sessions, bloodMap, gpuMap);

  // Emit manifest JSON
  const out = {
    schema_version: "1",
    generated_at: new Date().toISOString(),
    lambda_halflife_days: 7,
    session_count: ranked.length,
    sessions: ranked,
  };

  if (!dryRun) {
    writeFileSync(RANKED_OUT, JSON.stringify(out, null, 2), "utf8");
    console.log(`[G6] manifest/session_ranked_index.json written — top: ${ranked[0]?.sessionId} (composite: ${ranked[0]?.composite})`);

    writeToDb(ranked);
  } else {
    console.log("[G6] --dry-run: no files written");
    console.log("[G6] Top 5:");
    for (const r of ranked.slice(0, 5)) {
      console.log(`  #${r.rank} ${r.sessionId} composite=${r.composite} recency=${r.recency} avgSem=${r.avgSemantic} turns=${r.turns}`);
    }
  }
}

main();
