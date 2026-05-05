#!/usr/bin/env bun
// @SID: SESSION_TRUNCATOR_V1_G9
//
// SESSION TRUNCATION ENGINE — G9 gate
// ─────────────────────────────────────────────────────────────────────────────
// Architecture:
//
//   JSONL transcript → corpus.sqlite (session-corpus.ts / G1)
//   corpus.sqlite    → SCORED TURNS  (this file / G9)
//   SCORED TURNS     → COMPACT PACKET  (warm-start for next session / G10)
//
// The corpus already has all turn data structured. The truncation algorithm
// works AGAINST THE DB — no raw JSONL parsing needed.
//
// Turn classification tiers (the scoring spine):
//   T0 ANCHOR  — file edits, commits, resolved errors            → always kept
//   T1 SIGNAL  — code blocks ≥ 10 lines, successful tool chains  → top-K kept
//   T2 CONTEXT — architectural keywords in user/assistant turns  → scored
//   T3 NOISE   — retries, failed tool calls, acknowledgements    → filtered out
//
// GPU acceleration (hardware-accelerated middleware):
//   Phase A (TS):    structural scoring from DB columns (instant)
//   Phase B (Python): Qwen/Qwen3-Embeddings via CUDA for semantic density scoring
//                     invoked via `uv run probes/python/session_gpu_scorer.py`
//                     RTX 4090 → ~2ms per 128-token chunk, flash_attn attention
//   Phase C (future): abstractive summarization via tabbyAPI LLM inference
//
// Output: manifest/session_compaction_<id>.json
//   + manifest/session_warmstart_<id>.md   ← paste-ready warm-start prompt
//
// Usage:
//   bun run scripts/session-truncator.ts                        # all sessions
//   bun run scripts/session-truncator.ts --session <id>        # one session
//   bun run scripts/session-truncator.ts --top 5               # 5 densest sessions
//   bun run scripts/session-truncator.ts --ratio 0.2           # keep 20% of turns
//   bun run scripts/session-truncator.ts --no-gpu              # skip embedding phase
//   bun run scripts/session-truncator.ts --warmstart           # write .md warmstart packet
//   bun run scripts/session-truncator.ts --report              # JSON gate report to stdout

import { existsSync, mkdirSync, readFileSync, writeFileSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { Database } from "bun:sqlite";

// ─────────────────────────────────────────────────────────────
// CLI args
// ─────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const sessionArgIdx  = args.indexOf("--session");
const targetSession  = sessionArgIdx >= 0 ? args[sessionArgIdx + 1] : null;
const topArgIdx      = args.indexOf("--top");
const topN           = topArgIdx >= 0 ? parseInt(args[topArgIdx + 1], 10) : null;
const ratioArgIdx    = args.indexOf("--ratio");
const keepRatio      = ratioArgIdx >= 0 ? parseFloat(args[ratioArgIdx + 1]) : 0.25;
const noGpu          = args.includes("--no-gpu");
const warmstart      = args.includes("--warmstart");
const reportMode     = args.includes("--report");
const verbose        = args.includes("--verbose");

const repoRoot    = resolve(join(import.meta.dir, ".."));
const manifestDir = join(repoRoot, "manifest");
const corpusPath  = join(manifestDir, "corpus.sqlite");
const gpuScorer   = join(repoRoot, "probes", "python", "session_gpu_scorer.py");

if (!existsSync(corpusPath)) {
    console.error(`corpus.sqlite not found at ${corpusPath}`);
    process.exit(1);
}

// ─────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────
interface SessionRow {
    sessionId: string;
    startTime: string | null;
    turns: number;
    intent: string | null;
    topic: string | null;
    ingestedAt: string | null;
}

interface TurnScore {
    turn: number;
    tier: 0 | 1 | 2 | 3;     // T0=ANCHOR … T3=NOISE
    structuralScore: number;   // from DB columns (no GPU)
    semanticScore: number;     // from GPU embeddings (filled in Phase B)
    totalScore: number;
    signals: string[];         // human-readable evidence
}

interface CompactionOutput {
    sessionId: string;
    sessionIntent: string | null;
    totalTurns: number;
    keptTurns: number;
    compressionRatio: number;
    gpuAccelerated: boolean;
    structuralAnchors: number;
    signalTurns: number;
    noiseTurns: number;
    topFiles: string[];
    topTools: string[];
    commits: string[];
    anchoredEdits: { turn: number; file: string; tool: string }[];
    anchoredCmds: { turn: number; command: string; goal: string | null }[];
    highValueBlocks: { turn: number; lang: string; lines: number; preview: string }[];
    keptTurnNums: number[];
    gpuScoreManifest: string | null;    // path to Phase B output if GPU ran
    generatedAt: string;
    gateVersion: "G9.0";
}

// ─────────────────────────────────────────────────────────────
// Corpus queries
// ─────────────────────────────────────────────────────────────
function queryCorpus<T extends Record<string, unknown>>(
    db: Database,
    sql: string,
    params: unknown[] = [],
): T[] {
    return db.prepare(sql).all(...params) as T[];
}

function querySingle<T extends Record<string, unknown>>(
    db: Database,
    sql: string,
    params: unknown[] = [],
): T | null {
    return (db.prepare(sql).get(...params) as T | null);
}

// ─────────────────────────────────────────────────────────────
// Phase A: Structural scoring (DB-only, CPU, instant)
// ─────────────────────────────────────────────────────────────

// Architectural decision keywords — presence in intent/tool args bumps score
const ARCH_KEYWORDS = [
    "gate", "architecture", "design", "schema", "protocol", "doctrine",
    "canal", "refactor", "pivot", "bootstrap", "migrate", "build",
    "error", "fail", "fix", "resolve", "commit", "push", "deploy",
    "ssot", "corpus", "satellite", "vampire", "vulkan",
];

function scoreSessionStructural(
    db: Database,
    sessionId: string,
    totalTurns: number,
): Map<number, TurnScore> {
    const scores = new Map<number, TurnScore>();
    const init = (turn: number): TurnScore => {
        if (!scores.has(turn)) {
            scores.set(turn, { turn, tier: 3, structuralScore: 0, semanticScore: 0, totalScore: 0, signals: [] });
        }
        return scores.get(turn)!;
    };

    // File edits → T0 ANCHOR (+15)
    const edits = queryCorpus<{ turn: number; filePath: string; tool: string }>(
        db, "SELECT turn, filePath, tool FROM file_edits WHERE sessionId = ?", [sessionId],
    );
    for (const e of edits) {
        const s = init(e.turn);
        s.structuralScore += 15;
        s.tier = 0;
        s.signals.push(`file_edit: ${e.filePath} via ${e.tool}`);
    }

    // Commits → T0 ANCHOR (+20)
    const commits = queryCorpus<{ turn: number; sha: string }>(
        db, "SELECT turn, sha FROM commit_refs WHERE sessionId = ?", [sessionId],
    );
    for (const c of commits) {
        const s = init(c.turn);
        s.structuralScore += 20;
        s.tier = 0;
        s.signals.push(`commit: ${c.sha}`);
    }

    // Terminal cmds → T1 SIGNAL (+5), failed then retried → more weight
    const cmds = queryCorpus<{ turn: number; command: string; goal: string | null }>(
        db, "SELECT turn, command, goal FROM terminal_cmds WHERE sessionId = ? ORDER BY turn", [sessionId],
    );
    for (const c of cmds) {
        const s = init(c.turn);
        s.structuralScore += 5;
        if (s.tier > 1) s.tier = 1;
        const txt = (c.command + " " + (c.goal ?? "")).toLowerCase();
        const archHit = ARCH_KEYWORDS.some(kw => txt.includes(kw));
        if (archHit) {
            s.structuralScore += 3;
            s.signals.push(`arch_cmd: ${c.command.slice(0, 60)}`);
        } else {
            s.signals.push(`cmd: ${c.command.slice(0, 60)}`);
        }
    }

    // Code blocks → T1 SIGNAL, larger = higher score (cap at +12)
    const blocks = queryCorpus<{ turn: number; lang: string; lines: number; preview: string }>(
        db, "SELECT turn, lang, lines, preview FROM code_blocks WHERE sessionId = ? ORDER BY lines DESC", [sessionId],
    );
    for (const b of blocks) {
        const s = init(b.turn);
        const lineBonus = Math.min(b.lines / 10, 12);
        s.structuralScore += lineBonus;
        if (s.tier > 1) s.tier = 1;
        s.signals.push(`code(${b.lang},${b.lines}L): ${b.preview?.slice(0, 40)}`);
    }

    // Tool calls — successful ones with large result content = SIGNAL
    const tools = queryCorpus<{ turn: number; toolName: string; success: number; argsJson: string | null }>(
        db, "SELECT turn, toolName, success, argsJson FROM tool_calls WHERE sessionId = ? ORDER BY turn", [sessionId],
    );

    // Group by turn for chained tool detection
    const toolsByTurn = new Map<number, typeof tools>();
    for (const t of tools) {
        if (!toolsByTurn.has(t.turn)) toolsByTurn.set(t.turn, []);
        toolsByTurn.get(t.turn)!.push(t);
    }

    for (const [turn, turnTools] of toolsByTurn) {
        const s = init(turn);
        const allSuccess = turnTools.every(t => t.success === 1);
        const failCount = turnTools.filter(t => t.success === 0).length;

        if (allSuccess && turnTools.length >= 3) {
            // Long successful tool chain = SIGNAL
            s.structuralScore += 6;
            if (s.tier > 1) s.tier = 1;
            s.signals.push(`tool_chain(${turnTools.length}): ${turnTools.map(t => t.toolName).join("→")}`);
        } else if (failCount > 0 && turnTools.length === failCount) {
            // Pure failure turn = lean toward NOISE
            s.structuralScore -= 3;
            if (s.tier === 3) s.tier = 3;
            s.signals.push(`failed_tools(${failCount})`);
        } else if (turnTools.length > 0) {
            s.structuralScore += 2;
            if (s.tier > 2) s.tier = 2;
            s.signals.push(`tools(${turnTools.length})`);
        }
    }

    // Memory snapshots — no turn column in schema; count only for session-level bookkeeping
    // (capturedAt-based; cannot anchor to a specific turn — skip per-turn boost)

    // Finalize tier based on final score for unclassified turns
    // Turns with no signal at all remain T3 (noise)
    for (const [, s] of scores) {
        s.totalScore = s.structuralScore; // semantic will add in Phase B
        if (s.structuralScore > 18) s.tier = 0;
        else if (s.structuralScore > 8) s.tier = Math.min(s.tier, 1) as 0 | 1;
        else if (s.structuralScore > 3) s.tier = Math.min(s.tier, 2) as 0 | 1 | 2;
    }

    return scores;
}

// ─────────────────────────────────────────────────────────────
// Phase B: GPU semantic scoring
// ─────────────────────────────────────────────────────────────
interface GpuScoreResult {
    sessionId: string;
    scoredTurns: Array<{ turn: number; semanticScore: number; clusterLabel: number }>;
    embeddingModel: string;
    device: string;
    durationMs: number;
}

function runGpuScorer(sessionId: string, outPath: string): GpuScoreResult | null {
    if (!existsSync(gpuScorer)) {
        if (verbose) console.warn(`  [GPU] scorer not found at ${gpuScorer} — skipping Phase B`);
        return null;
    }
    const result = spawnSync(
        "uv",
        ["run", gpuScorer, "--session", sessionId, "--corpus", corpusPath, "--out", outPath],
        { encoding: "utf8", timeout: 240_000 },
    );
    if (result.status !== 0) {
        if (verbose) console.warn("  [GPU] scorer failed:", result.stderr?.slice(0, 200));
        return null;
    }
    try {
        return JSON.parse(readFileSync(outPath, "utf8")) as GpuScoreResult;
    } catch {
        return null;
    }
}

// ─────────────────────────────────────────────────────────────
// Compaction: select turns to keep
// ─────────────────────────────────────────────────────────────
function selectKeptTurns(
    scores: Map<number, TurnScore>,
    totalTurns: number,
    ratio: number,
): number[] {
    const targetCount = Math.max(
        10,
        Math.ceil(totalTurns * ratio),
    );

    const allScored = [...scores.values()].sort((a, b) => b.totalScore - a.totalScore);

    // Always keep all T0 anchors
    const anchors = allScored.filter(s => s.tier === 0).map(s => s.turn);
    const remaining = targetCount - anchors.length;

    if (remaining <= 0) {
        return anchors.sort((a, b) => a - b);
    }

    // Fill with T1/T2 by score
    const signals = allScored
        .filter(s => s.tier === 1 || s.tier === 2)
        .slice(0, remaining)
        .map(s => s.turn);

    return [...new Set([...anchors, ...signals])].sort((a, b) => a - b);
}

// ─────────────────────────────────────────────────────────────
// Warm-start packet generator
// ─────────────────────────────────────────────────────────────
function generateWarmStart(output: CompactionOutput, db: Database): string {
    const lines: string[] = [
        `# Session Warm-Start — ${output.sessionId.slice(0, 8)}`,
        `> Compacted ${output.totalTurns} turns → ${output.keptTurns} (${(output.compressionRatio * 100).toFixed(0)}% kept)`,
        `> GPU-accelerated: ${output.gpuAccelerated}  |  Generated: ${output.generatedAt}`,
        "",
        "## Session Intent",
        output.sessionIntent ?? "(unknown)",
        "",
    ];

    if (output.commits.length > 0) {
        lines.push("## Commits This Session");
        for (const sha of output.commits) {
            lines.push(`- \`${sha}\``);
        }
        lines.push("");
    }

    if (output.anchoredEdits.length > 0) {
        lines.push("## Files Edited");
        const grouped = new Map<string, string[]>();
        for (const e of output.anchoredEdits) {
            if (!grouped.has(e.file)) grouped.set(e.file, []);
            grouped.get(e.file)!.push(e.tool);
        }
        for (const [file, tools] of grouped) {
            const shortPath = file.split(/[\\/]/).slice(-3).join("/");
            lines.push(`- \`${shortPath}\` (${[...new Set(tools)].join(", ")})`);
        }
        lines.push("");
    }

    if (output.anchoredCmds.length > 0) {
        lines.push("## Key Terminal Commands");
        for (const c of output.anchoredCmds.slice(0, 12)) {
            const goal = c.goal ? ` # ${c.goal}` : "";
            lines.push(`- \`${c.command.slice(0, 80)}${goal}\``);
        }
        lines.push("");
    }

    if (output.highValueBlocks.length > 0) {
        lines.push("## High-Value Code Blocks");
        for (const b of output.highValueBlocks.slice(0, 6)) {
            lines.push(`- **${b.lang}** (${b.lines}L, turn ${b.turn}): ${b.preview?.slice(0, 80)}`);
        }
        lines.push("");
    }

    if (output.topTools.length > 0) {
        lines.push("## Tool Usage Pattern");
        lines.push(output.topTools.map(t => `\`${t}\``).join(" · "));
        lines.push("");
    }

    lines.push("## Structural Breakdown");
    lines.push(`- T0 Anchors: ${output.structuralAnchors} (commits, edits, memory writes)`);
    lines.push(`- T1/T2 Signal: ${output.signalTurns} (code blocks, tool chains, commands)`);
    lines.push(`- T3 Noise filtered: ${output.noiseTurns} (retries, acks, failed calls)`);

    return lines.join("\n");
}

// ─────────────────────────────────────────────────────────────
// Main: process one session
// ─────────────────────────────────────────────────────────────
async function truncateSession(db: Database, session: SessionRow): Promise<CompactionOutput> {
    const { sessionId, turns: totalTurns, intent, topic } = session;
    const sessionIntent = topic ?? intent;

    if (verbose) console.log(`\n  Processing ${sessionId.slice(0, 8)}… (${totalTurns} turns)`);

    // Phase A: structural scoring
    const scores = scoreSessionStructural(db, sessionId, totalTurns);
    if (verbose) console.log(`  Phase A: scored ${scores.size} instrumented turns`);

    // Phase B: GPU semantic scoring
    let gpuScoreManifest: string | null = null;
    let gpuAccelerated = false;

    if (!noGpu) {
        const gpuOutPath = join(manifestDir, `gpu_scores_${sessionId.slice(0, 8)}.json`);
        const gpuResult = runGpuScorer(sessionId, gpuOutPath);
        if (gpuResult) {
            gpuAccelerated = true;
            gpuScoreManifest = gpuOutPath;
            if (verbose) console.log(`  Phase B: GPU scored ${gpuResult.scoredTurns.length} turns via ${gpuResult.device} (model=${gpuResult.embeddingModel})`);
            // Merge GPU semantic scores into existing structural entries
            for (const gs of gpuResult.scoredTurns) {
                if (scores.has(gs.turn)) {
                    const s = scores.get(gs.turn)!;
                    s.semanticScore = gs.semanticScore;
                    s.totalScore = s.structuralScore + s.semanticScore;
                }
            }
            // Admit semantic-only turns: high semantic score turns that have no structural signal
            // These are typically rich user messages or unique reasoning turns with no tool calls
            const SEMANTIC_ADMIT_THRESHOLD = 7.0;
            let admittedSemanticOnly = 0;
            for (const gs of gpuResult.scoredTurns) {
                if (!scores.has(gs.turn) && gs.semanticScore >= SEMANTIC_ADMIT_THRESHOLD) {
                    scores.set(gs.turn, {
                        turn: gs.turn,
                        tier: 2,  // T2 CONTEXT — semantically unique but no structural anchor
                        structuralScore: 0,
                        semanticScore: gs.semanticScore,
                        totalScore: gs.semanticScore,
                        signals: [`semantic_only: score=${gs.semanticScore.toFixed(2)}`],
                    });
                    admittedSemanticOnly++;
                }
            }
            if (verbose && admittedSemanticOnly > 0)
                console.log(`  Phase B: admitted ${admittedSemanticOnly} semantic-only turns (score ≥ ${SEMANTIC_ADMIT_THRESHOLD})`);
        }
    }

    // Finalize totals for turns with no GPU score
    for (const [, s] of scores) {
        if (s.totalScore === 0) s.totalScore = s.structuralScore;
    }

    // Select kept turns
    const keptTurns = selectKeptTurns(scores, totalTurns, keepRatio);

    // Build output artifacts
    const allScored = [...scores.values()];
    const anchors   = allScored.filter(s => s.tier === 0);
    const signals   = allScored.filter(s => s.tier === 1 || s.tier === 2);
    const noise     = allScored.filter(s => s.tier === 3);

    const edits = queryCorpus<{ turn: number; filePath: string; tool: string }>(
        db, "SELECT turn, filePath, tool FROM file_edits WHERE sessionId = ? ORDER BY turn", [sessionId],
    );
    const cmds = queryCorpus<{ turn: number; command: string; goal: string | null }>(
        db, "SELECT turn, command, goal FROM terminal_cmds WHERE sessionId = ? ORDER BY turn", [sessionId],
    );
    const blocks = queryCorpus<{ turn: number; lang: string; lines: number; preview: string }>(
        db, "SELECT turn, lang, lines, preview FROM code_blocks WHERE sessionId = ? ORDER BY lines DESC", [sessionId],
    );
    const commits = queryCorpus<{ sha: string }>(
        db, "SELECT sha FROM commit_refs WHERE sessionId = ?", [sessionId],
    );

    // Top files from edits
    const fileCounts = new Map<string, number>();
    for (const e of edits) {
        fileCounts.set(e.filePath, (fileCounts.get(e.filePath) ?? 0) + 1);
    }
    const topFiles = [...fileCounts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([f]) => f);

    // Top tools from tool_calls
    const toolCounts = new Map<string, number>();
    const allTools = queryCorpus<{ toolName: string }>(
        db, "SELECT toolName FROM tool_calls WHERE sessionId = ?", [sessionId],
    );
    for (const t of allTools) {
        toolCounts.set(t.toolName, (toolCounts.get(t.toolName) ?? 0) + 1);
    }
    const topTools = [...toolCounts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 8)
        .map(([t]) => t);

    const output: CompactionOutput = {
        sessionId,
        sessionIntent,
        totalTurns,
        keptTurns: keptTurns.length,
        compressionRatio: keptTurns.length / Math.max(totalTurns, 1),
        gpuAccelerated,
        structuralAnchors: anchors.length,
        signalTurns: signals.length,
        noiseTurns: noise.length,
        topFiles,
        topTools,
        commits: commits.map(c => c.sha),
        anchoredEdits: edits.map(e => ({ turn: e.turn, file: e.filePath, tool: e.tool })),
        anchoredCmds: cmds.map(c => ({ turn: c.turn, command: c.command, goal: c.goal })),
        highValueBlocks: blocks.slice(0, 20).map(b => ({
            turn: b.turn, lang: b.lang, lines: b.lines, preview: b.preview,
        })),
        keptTurnNums: keptTurns,
        gpuScoreManifest,
        generatedAt: new Date().toISOString(),
        gateVersion: "G9.0",
    };

    // Write compaction manifest
    const compactionPath = join(manifestDir, `session_compaction_${sessionId.slice(0, 8)}.json`);
    writeFileSync(compactionPath, JSON.stringify(output, null, 2), "utf8");
    if (verbose) console.log(`  → ${compactionPath}`);

    // Write warm-start packet
    if (warmstart) {
        const wsContent = generateWarmStart(output, db);
        const wsPath = join(manifestDir, `session_warmstart_${sessionId.slice(0, 8)}.md`);
        writeFileSync(wsPath, wsContent, "utf8");
        if (verbose) console.log(`  → ${wsPath}`);
    }

    return output;
}

// ─────────────────────────────────────────────────────────────
// Entry
// ─────────────────────────────────────────────────────────────
const db = new Database(corpusPath, { readonly: true });

let sessions: SessionRow[];
if (targetSession) {
    const row = querySingle<SessionRow>(
        db, "SELECT sessionId, startTime, turns, intent, topic, ingestedAt FROM sessions WHERE sessionId = ?",
        [targetSession],
    );
    if (!row) {
        console.error(`Session not found: ${targetSession}`);
        process.exit(1);
    }
    sessions = [row];
} else {
    sessions = queryCorpus<SessionRow>(
        db,
        "SELECT sessionId, startTime, turns, intent, topic, ingestedAt FROM sessions ORDER BY turns DESC",
    );
    if (topN !== null) sessions = sessions.slice(0, topN);
}

if (sessions.length === 0) {
    console.error("No sessions in corpus.");
    process.exit(1);
}

console.log(`\nSession Truncator G9.0 — ${sessions.length} session(s) | ratio=${keepRatio} | gpu=${!noGpu}`);

const results: CompactionOutput[] = [];
for (const s of sessions) {
    try {
        const out = await truncateSession(db, s);
        results.push(out);
        if (!reportMode) {
            const pct = (out.compressionRatio * 100).toFixed(0);
            const gpu = out.gpuAccelerated ? " [GPU]" : "";
            console.log(
                `  ${s.sessionId.slice(0, 8)}  ${out.totalTurns.toString().padStart(5)} turns → ${out.keptTurns.toString().padStart(4)} kept (${pct}%)${gpu}`,
            );
        }
    } catch (e) {
        console.error(`  ERROR ${s.sessionId.slice(0, 8)}: ${String(e)}`);
    }
}

db.close();

if (reportMode) {
    console.log(JSON.stringify({
        gate: "G9.0",
        status: results.length > 0 ? "admitted" : "failed",
        sessions: results.map(r => ({
            sessionId: r.sessionId,
            totalTurns: r.totalTurns,
            keptTurns: r.keptTurns,
            compressionRatio: r.compressionRatio,
            gpuAccelerated: r.gpuAccelerated,
            structuralAnchors: r.structuralAnchors,
        })),
        averageCompressionRatio: results.reduce((a, r) => a + r.compressionRatio, 0) / results.length,
    }, null, 2));
} else {
    const avg = results.reduce((a, r) => a + r.compressionRatio, 0) / results.length;
    console.log(`\n  Done. Avg compression: ${(avg * 100).toFixed(0)}% kept.`);
    console.log(`  Manifests: manifest/session_compaction_<id>.json`);
    if (warmstart) console.log(`  Warm-start packets: manifest/session_warmstart_<id>.md`);
}
