#!/usr/bin/env bun

// @SID: G9_SESSION_TRUNCATION_GATE_SMOKE_V1
//
// CI smoke check for G9 — Session Truncation Engine
// Reads manifest/session_compaction_*.json (written by session-truncator.ts)
// Does NOT re-run the truncator. Fast, idempotent, manifest-driven.
//
// Exit codes:
//   0 = gate admitted (at least one session compacted, compression ratio sane)
//   1 = gate failed (no manifests, zero sessions, or implausible ratios)
//
// Usage:
//   bun run ci/checks/session-truncation-gate.ts
//   bun run ci/checks/session-truncation-gate.ts --report   # JSON to stdout

import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

const args = process.argv.slice(2);
const reportMode = args.includes("--report");

const repoRoot    = join(import.meta.dir, "..", "..");
const manifestDir = join(repoRoot, "manifest");

interface CompactionManifest {
    sessionId: string;
    sessionIntent: string | null;
    totalTurns: number;
    keptTurns: number;
    compressionRatio: number;
    gpuAccelerated: boolean;
    structuralAnchors: number;
    signalTurns: number;
    noiseTurns: number;
    gateVersion: string;
    generatedAt: string;
}

// ── Read all compaction manifests ─────────────────────────────
const manifestFiles = existsSync(manifestDir)
    ? readdirSync(manifestDir).filter(f => f.startsWith("session_compaction_") && f.endsWith(".json"))
    : [];

const manifests: CompactionManifest[] = [];
const parseErrors: string[] = [];

for (const f of manifestFiles) {
    try {
        const raw = readFileSync(join(manifestDir, f), "utf8");
        manifests.push(JSON.parse(raw) as CompactionManifest);
    } catch (e) {
        parseErrors.push(`${f}: ${String(e)}`);
    }
}

// ── Gate logic ────────────────────────────────────────────────
const issues: string[] = [];

if (manifests.length === 0) {
    issues.push("No session_compaction_*.json manifests found — run: bun run truncate");
}

for (const m of manifests) {
    if (m.compressionRatio > 1.0 || m.compressionRatio < 0) {
        issues.push(`${m.sessionId.slice(0, 8)}: implausible compressionRatio=${m.compressionRatio}`);
    }
    if (m.keptTurns > m.totalTurns) {
        issues.push(`${m.sessionId.slice(0, 8)}: keptTurns(${m.keptTurns}) > totalTurns(${m.totalTurns})`);
    }
    if (m.structuralAnchors < 0) {
        issues.push(`${m.sessionId.slice(0, 8)}: negative structuralAnchors`);
    }
}

if (parseErrors.length > 0) {
    issues.push(...parseErrors.map(e => `parse error: ${e}`));
}

const gpuSessions    = manifests.filter(m => m.gpuAccelerated).length;
const avgRatio        = manifests.length > 0
    ? manifests.reduce((a, m) => a + m.compressionRatio, 0) / manifests.length
    : 0;
const totalTurnsAll   = manifests.reduce((a, m) => a + m.totalTurns, 0);
const keptTurnsAll    = manifests.reduce((a, m) => a + m.keptTurns, 0);
const status          = issues.length === 0 ? "admitted" : "failed";

// ── Output ────────────────────────────────────────────────────
if (reportMode) {
    console.log(JSON.stringify({
        gate: "G9.0",
        status,
        sessions: manifests.length,
        gpuAcceleratedSessions: gpuSessions,
        averageCompressionRatio: parseFloat(avgRatio.toFixed(3)),
        totalTurnsAcrossCorpus: totalTurnsAll,
        keptTurnsAcrossCorpus: keptTurnsAll,
        issues,
        manifests: manifests.map(m => ({
            sessionId: m.sessionId,
            totalTurns: m.totalTurns,
            keptTurns: m.keptTurns,
            compressionRatio: m.compressionRatio,
            gpuAccelerated: m.gpuAccelerated,
            structuralAnchors: m.structuralAnchors,
            gateVersion: m.gateVersion,
            generatedAt: m.generatedAt,
        })),
    }, null, 2));
} else {
    const icon = status === "admitted" ? "✓" : "✗";
    console.log(`G9 Session-Truncation — ${icon} ${status.toUpperCase()}`);
    console.log(`  sessions: ${manifests.length}  gpu: ${gpuSessions}  avgRatio: ${(avgRatio * 100).toFixed(0)}%`);
    console.log(`  turns: ${totalTurnsAll} total → ${keptTurnsAll} kept`);
    if (issues.length > 0) {
        for (const issue of issues) {
            console.log(`  ! ${issue}`);
        }
    }
}

process.exit(issues.length > 0 ? 1 : 0);
