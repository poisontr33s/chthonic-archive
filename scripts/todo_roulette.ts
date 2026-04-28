#!/usr/bin/env bun
// @SID: TODO_ROULETTE_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ scripts/todo_roulette.ts
// ║
// ║ TODOI Roulette — Euler-weighted task selection engine.
// ║
// ║ The "I" is Euler's imaginary unit. Every task carries a spin-vector in
// ║ complex urgency-space:
// ║
// ║   score(task) = w · e^(κ·s) · ½(1 + sin(φ))
// ║
// ║   w  = base weight (1–10, set at creation)
// ║   s  = staleness in days (time since created or last spun)
// ║   κ  = growth constant (0.07 — ~7% urgency gain per idle day)
// ║   φ  = phase angle derived from tag cluster (0…2π)
// ║
// ║ Magnitude = √(Re² + Im²)  where Re = score, Im = score·sin(φ)
// ║ Display: score ∠ φ°  (polar form — the spin signature)
// ║
// ║ Selection: tasks become roulette arcs proportional to their score.
// ║ A uniform random point on the wheel chooses the winner.
// ║
// ║ Usage:
// ║   bun run scripts/todo_roulette.ts --spin              (default)
// ║   bun run scripts/todo_roulette.ts --add "title" [--tag ssot] [--weight 5]
// ║   bun run scripts/todo_roulette.ts --complete <id>
// ║   bun run scripts/todo_roulette.ts --list
// ║   bun run scripts/todo_roulette.ts --list --all        (include completed)
// ║   bun run scripts/todo_roulette.ts --report
// ║   bun run scripts/todo_roulette.ts --dry-run           (spin without recording)
// ╚════════════════════════════════════════════════════════════════════════════

import { existsSync, readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import { randomUUID } from "crypto";

// ── Constants ─────────────────────────────────────────────────────────────────

const MANIFEST_PATH = join(import.meta.dir, "..", "manifest", "todo_roulette.json");
const KAPPA = 0.07; // exponential growth constant per idle day

/** Tag families → phase angle arc (radians, 0…2π) */
const TAG_PHASE: Record<string, number> = {
  ssot:      0,
  entity:    Math.PI / 6,
  lore:      Math.PI / 3,
  infra:     Math.PI / 2,
  build:     (2 * Math.PI) / 3,
  ci:        (5 * Math.PI) / 6,
  game:      Math.PI,
  narrative: (7 * Math.PI) / 6,
  session:   (3 * Math.PI) / 2,
  handoff:   (5 * Math.PI) / 3,
  debt:      (11 * Math.PI) / 6,
  default:   Math.PI / 4, // fallback
};

// ── Types ─────────────────────────────────────────────────────────────────────

interface TodoEntry {
  id: string;
  title: string;
  body?: string;
  tags: string[];
  created: string;
  last_spun?: string;
  completed?: string;
  weight: number; // 1–10
  origin: "manual" | "session" | "git-trailer";
  spin_count: number;
}

interface Manifest {
  version: "1";
  created: string;
  last_spun?: string;
  total_spins: number;
  entries: TodoEntry[];
}

interface SpinResult {
  task: TodoEntry;
  score: number;
  phase_rad: number;
  phase_deg: number;
  magnitude: number;
  spin_vector: string; // e.g. "12.41 ∠ 47.3°"
  staleness_days: number;
  wheel_arc_pct: number; // % of wheel this task owned
}

// ── Manifest I/O ──────────────────────────────────────────────────────────────

function loadManifest(): Manifest {
  if (!existsSync(MANIFEST_PATH)) {
    return {
      version: "1",
      created: new Date().toISOString(),
      total_spins: 0,
      entries: [],
    };
  }
  return JSON.parse(readFileSync(MANIFEST_PATH, "utf-8")) as Manifest;
}

function saveManifest(m: Manifest): void {
  const dir = join(import.meta.dir, "..", "manifest");
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  writeFileSync(MANIFEST_PATH, JSON.stringify(m, null, 2), "utf-8");
}

// ── Euler Spin Engine ─────────────────────────────────────────────────────────

function stalenessDays(entry: TodoEntry): number {
  const anchor = entry.last_spun ?? entry.created;
  return (Date.now() - new Date(anchor).getTime()) / (1000 * 60 * 60 * 24);
}

function phaseAngle(tags: string[]): number {
  if (tags.length === 0) return TAG_PHASE.default;
  // Average phase of all matching tags (circular mean)
  let sinSum = 0;
  let cosSum = 0;
  for (const tag of tags) {
    const phi = TAG_PHASE[tag] ?? TAG_PHASE.default;
    sinSum += Math.sin(phi);
    cosSum += Math.cos(phi);
  }
  return Math.atan2(sinSum / tags.length, cosSum / tags.length);
}

function eulerScore(entry: TodoEntry): { score: number; phi: number; staleness: number } {
  const s = stalenessDays(entry);
  const phi = phaseAngle(entry.tags);
  // score = w · e^(κ·s) · ½(1 + sin(φ))
  const score = entry.weight * Math.exp(KAPPA * s) * 0.5 * (1 + Math.sin(phi));
  return { score, phi, staleness: s };
}

function spinVector(score: number, phi: number): { magnitude: number; label: string } {
  // Treat score as Re, score·sin(φ) as Im
  const re = score;
  const im = score * Math.sin(phi);
  const magnitude = Math.sqrt(re * re + im * im);
  const deg = ((phi * 180) / Math.PI + 360) % 360;
  return {
    magnitude,
    label: `${magnitude.toFixed(2)} ∠ ${deg.toFixed(1)}°`,
  };
}

function weightedRandom(scores: number[]): number {
  const total = scores.reduce((a, b) => a + b, 0);
  if (total === 0) return Math.floor(Math.random() * scores.length);
  let cursor = Math.random() * total;
  for (let i = 0; i < scores.length; i++) {
    cursor -= scores[i];
    if (cursor <= 0) return i;
  }
  return scores.length - 1;
}

function spin(manifest: Manifest): SpinResult | null {
  const active = manifest.entries.filter((e) => !e.completed);
  if (active.length === 0) return null;

  const scored = active.map((e) => {
    const { score, phi, staleness } = eulerScore(e);
    return { entry: e, score, phi, staleness };
  });

  const scores = scored.map((s) => s.score);
  const totalScore = scores.reduce((a, b) => a + b, 0);
  const idx = weightedRandom(scores);
  const winner = scored[idx];
  const sv = spinVector(winner.score, winner.phi);

  return {
    task: winner.entry,
    score: winner.score,
    phase_rad: winner.phi,
    phase_deg: ((winner.phi * 180) / Math.PI + 360) % 360,
    magnitude: sv.magnitude,
    spin_vector: sv.label,
    staleness_days: winner.staleness,
    wheel_arc_pct: totalScore > 0 ? (winner.score / totalScore) * 100 : 100,
  };
}

// ── Display ───────────────────────────────────────────────────────────────────

function renderWheel(results: Array<{ entry: TodoEntry; score: number }>, winner: TodoEntry): void {
  const total = results.reduce((a, b) => a + b.score, 0);
  const sorted = [...results].sort((a, b) => b.score - a.score).slice(0, 8);
  console.log("\n  ┌─ Wheel (top 8) ──────────────────────────────────────┐");
  for (const r of sorted) {
    const pct = total > 0 ? (r.score / total) * 100 : 0;
    const bar = "█".repeat(Math.round(pct / 3)).padEnd(33, "░");
    const marker = r.entry.id === winner.id ? " ◀ LANDED" : "";
    console.log(`  │ ${bar} ${pct.toFixed(1).padStart(5)}%${marker}`);
    const title = r.entry.title.length > 46 ? r.entry.title.slice(0, 43) + "…" : r.entry.title;
    console.log(`  │   ${title}`);
  }
  console.log("  └──────────────────────────────────────────────────────┘");
}

function renderResult(r: SpinResult): void {
  const tags = r.task.tags.length ? r.task.tags.map((t) => `#${t}`).join(" ") : "(no tags)";
  console.log(`\n  ╔══ TODOI ROULETTE — SPIN RESULT ═══════════════════════╗`);
  console.log(`  ║`);
  console.log(`  ║  ${r.task.title}`);
  console.log(`  ║`);
  console.log(`  ║  id       : ${r.task.id}`);
  console.log(`  ║  tags     : ${tags}`);
  console.log(`  ║  weight   : ${r.task.weight}/10`);
  console.log(`  ║  staleness: ${r.staleness_days.toFixed(1)}d`);
  console.log(`  ║  spin vec : ${r.spin_vector}   (e^(iφ) form)`);
  console.log(`  ║  arc      : ${r.wheel_arc_pct.toFixed(1)}% of wheel`);
  if (r.task.body) {
    console.log(`  ║`);
    const bodyLines = r.task.body.split("\n").slice(0, 4);
    for (const line of bodyLines) {
      console.log(`  ║  ${line}`);
    }
  }
  console.log(`  ║`);
  console.log(`  ╚════════════════════════════════════════════════════════╝\n`);
}

// ── Commands ──────────────────────────────────────────────────────────────────

function cmdSpin(args: string[]): void {
  const dryRun = args.includes("--dry-run");
  const manifest = loadManifest();
  const active = manifest.entries.filter((e) => !e.completed);

  if (active.length === 0) {
    console.log("\n  Wheel is empty — add tasks with --add.\n");
    process.exit(0);
  }

  const result = spin(manifest);
  if (!result) {
    console.log("\n  No tasks to spin.\n");
    process.exit(0);
  }

  // Compute all scores for wheel render
  const allScored = active.map((e) => {
    const { score } = eulerScore(e);
    return { entry: e, score };
  });

  renderWheel(allScored, result.task);
  renderResult(result);

  if (!dryRun) {
    // Record the spin
    const entryIdx = manifest.entries.findIndex((e) => e.id === result.task.id);
    if (entryIdx >= 0) {
      manifest.entries[entryIdx].last_spun = new Date().toISOString();
      manifest.entries[entryIdx].spin_count = (manifest.entries[entryIdx].spin_count ?? 0) + 1;
    }
    manifest.last_spun = new Date().toISOString();
    manifest.total_spins = (manifest.total_spins ?? 0) + 1;
    saveManifest(manifest);
    console.log(`  [recorded — spin #${manifest.total_spins}]\n`);
  } else {
    console.log("  [dry-run — not recorded]\n");
  }
}

function cmdAdd(args: string[]): void {
  const titleIdx = args.findIndex((a) => a === "--add") + 1;
  if (titleIdx === 0 || titleIdx >= args.length) {
    console.error("  Usage: --add <title> [--tag <tag>] [--weight <1-10>] [--body <text>]");
    process.exit(1);
  }
  const title = args[titleIdx];

  const tagIdx = args.indexOf("--tag");
  const tag = tagIdx >= 0 && tagIdx + 1 < args.length ? args[tagIdx + 1] : null;

  const weightIdx = args.indexOf("--weight");
  const weight =
    weightIdx >= 0 && weightIdx + 1 < args.length ? parseInt(args[weightIdx + 1], 10) : 5;

  const bodyIdx = args.indexOf("--body");
  const body = bodyIdx >= 0 && bodyIdx + 1 < args.length ? args[bodyIdx + 1] : undefined;

  const originIdx = args.indexOf("--origin");
  const origin =
    originIdx >= 0 && originIdx + 1 < args.length
      ? (args[originIdx + 1] as TodoEntry["origin"])
      : "manual";

  const entry: TodoEntry = {
    id: randomUUID().split("-")[0], // short 8-char id
    title,
    tags: tag ? [tag] : [],
    created: new Date().toISOString(),
    weight: Math.min(10, Math.max(1, weight)),
    origin,
    spin_count: 0,
    ...(body ? { body } : {}),
  };

  const manifest = loadManifest();
  manifest.entries.push(entry);
  saveManifest(manifest);

  const { score, phi } = eulerScore(entry);
  const sv = spinVector(score, phi);
  console.log(`\n  Added: [${entry.id}] "${entry.title}"`);
  console.log(`  tags: ${entry.tags.join(", ") || "none"}  weight: ${entry.weight}  spin-vec: ${sv.label}\n`);
}

function cmdComplete(args: string[]): void {
  const idx = args.indexOf("--complete");
  if (idx < 0 || idx + 1 >= args.length) {
    console.error("  Usage: --complete <id>");
    process.exit(1);
  }
  const id = args[idx + 1];
  const manifest = loadManifest();
  const entry = manifest.entries.find((e) => e.id === id || e.id.startsWith(id));
  if (!entry) {
    console.error(`  No task found matching id: ${id}`);
    process.exit(1);
  }
  entry.completed = new Date().toISOString();
  saveManifest(manifest);
  console.log(`\n  ✓ Completed: [${entry.id}] "${entry.title}"\n`);
}

function cmdList(args: string[]): void {
  const showAll = args.includes("--all");
  const manifest = loadManifest();
  const entries = showAll ? manifest.entries : manifest.entries.filter((e) => !e.completed);

  if (entries.length === 0) {
    console.log("\n  No tasks.\n");
    return;
  }

  // Sort by euler score descending (active) or completed time (done)
  const scored = entries.map((e) => {
    if (e.completed) return { entry: e, score: 0, sv: "completed" };
    const { score, phi } = eulerScore(e);
    const sv = spinVector(score, phi);
    return { entry: e, score, sv: sv.label };
  });
  scored.sort((a, b) => b.score - a.score);

  console.log(`\n  ─── TODOI Manifest (${entries.length} tasks${showAll ? ", all" : ", active"}) ───\n`);
  for (const { entry, score, sv } of scored) {
    const done = entry.completed ? " ✓" : "";
    const s = entry.completed ? "  " : stalenessDays(entry).toFixed(0).padStart(3) + "d";
    const tags = entry.tags.length ? entry.tags.map((t) => `#${t}`).join(" ") : "";
    console.log(`  [${entry.id}] ${s}  w:${entry.weight}  ${sv.padEnd(18)} ${entry.title}${done}  ${tags}`);
  }
  console.log();
}

function cmdReport(args: string[]): void {
  const manifest = loadManifest();
  const active = manifest.entries.filter((e) => !e.completed);
  const done = manifest.entries.filter((e) => !!e.completed);

  const scored = active.map((e) => {
    const { score, phi, staleness } = eulerScore(e);
    const sv = spinVector(score, phi);
    return {
      id: e.id,
      title: e.title,
      tags: e.tags,
      weight: e.weight,
      staleness_days: +staleness.toFixed(2),
      score: +score.toFixed(4),
      spin_vector: sv.label,
      magnitude: +sv.magnitude.toFixed(4),
      spin_count: e.spin_count,
    };
  });
  scored.sort((a, b) => b.score - a.score);

  const report = {
    generated: new Date().toISOString(),
    total_spins: manifest.total_spins,
    active: scored.length,
    completed: done.length,
    top_task: scored[0] ?? null,
    tasks: scored,
  };

  console.log(JSON.stringify(report, null, 2));
}

// ── Entry ─────────────────────────────────────────────────────────────────────

const args = process.argv.slice(2);

if (args.includes("--add")) {
  cmdAdd(args);
} else if (args.includes("--complete")) {
  cmdComplete(args);
} else if (args.includes("--list")) {
  cmdList(args);
} else if (args.includes("--report")) {
  cmdReport(args);
} else {
  // Default: spin (respects --dry-run)
  cmdSpin(args);
}
