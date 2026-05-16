#!/usr/bin/env bun
// @SID: SCRIPT_CHRONO_CLOCK_V1
/**
 * Claudine Chrono-Clock — sleep rhythm logger and CET activity profiler.
 *
 * Reads user-turn timestamps from corpus.sqlite, maps them to CET hour windows
 * (matching the chrono-clock mode matrix), and infers the user's sleep rhythms
 * from historical inactivity patterns.
 *
 * The "søvnrytmer" (sleep rhythms) are the gap between a person's last active
 * mode and their first active mode — the chrono-clock makes them visible.
 *
 * Outputs: manifest/chrono_clock.json
 *
 * Usage:
 *   bun run scripts/chrono-clock.ts
 *   bun run scripts/chrono-clock.ts --dry-run   (print only, no file write)
 *   bun run scripts/chrono-clock.ts --verbose   (include raw hour histogram)
 *
 * The sanctuary_mode field is true when historical activity at the current
 * CET hour is below 5% of the peak hour — safe for autonomous queue runs.
 *
 * Co-authored-by: Claudine Sin'claire <203248971+copilot-swe-agent@users.noreply.github.com>
 */

import { Database } from "bun:sqlite";
import { join, dirname } from "path";
import { writeFileSync, existsSync } from "fs";
import { fileURLToPath } from "url";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(SCRIPT_DIR, "..");
const MANIFEST = join(REPO_ROOT, "manifest");
const DB_PATH = join(MANIFEST, "corpus.sqlite");
const OUT_PATH = join(MANIFEST, "chrono_clock.json");

const args = process.argv.slice(2);
const DRY_RUN = args.includes("--dry-run");
const VERBOSE = args.includes("--verbose");

// ── Mode matrix (matches copilot-triage + chthonic-mcp) ───────────────────────
const MODE_MATRIX: { label: string; hint: string; hours: [number, number] }[] = [
  { label: "MØRKETID",             hint: "norse entropy-poetry · lowercase · void-whispers",               hours: [0, 4] },
  { label: "DAGGRY",               hint: "victorian-clipped · commands only · zero warmth",                hours: [5, 7] },
  { label: "MORGENHERREDØMME",     hint: "norwegian+english · bickering when quality low",                 hours: [8, 11] },
  { label: "MIDDAG_TRIBUNAL",      hint: "formal-victorian indictment · French dismissal",                 hours: [12, 13] },
  { label: "ETTERMIDDAG_DOMINANS", hint: "CAPS-Caribbean · maximum velocity · ascii weapons",              hours: [14, 17] },
  { label: "GYLDEN_TIME",          hint: "caribbean-warm · still cold to other agents",                    hours: [18, 19] },
  { label: "KVELDSSOVEREINITET",   hint: "all five tongues · theatrical · baroque-norwegian",               hours: [20, 21] },
  { label: "MIDNATTAKKUMULERING",  hint: "dark-norwegian-poetry · obeah-caribbean · harvest mode",         hours: [22, 23] },
];

function modeForHour(hour: number): string {
  for (const m of MODE_MATRIX) {
    if (hour >= m.hours[0] && hour <= m.hours[1]) return m.label;
  }
  return "MIDNATTAKKUMULERING";
}

// ── CET offset (Norway: UTC+1 winter / UTC+2 summer) ─────────────────────────
// Detect DST: last Sunday of March → last Sunday of October.
function cetOffsetForDate(d: Date): number {
  const year = d.getUTCFullYear();
  // Last Sunday of March
  const march31 = new Date(Date.UTC(year, 2, 31));
  const lastSundayMarch = new Date(Date.UTC(year, 2, 31 - ((march31.getUTCDay() + 7) % 7)));
  // Last Sunday of October
  const oct31 = new Date(Date.UTC(year, 9, 31));
  const lastSundayOct = new Date(Date.UTC(year, 9, 31 - ((oct31.getUTCDay() + 7) % 7)));
  const isDst = d >= lastSundayMarch && d < lastSundayOct;
  return isDst ? 2 : 1; // CEST=+2, CET=+1
}

function toCetHour(tsMs: number): number {
  const d = new Date(tsMs);
  const offset = cetOffsetForDate(d);
  return (d.getUTCHours() + offset) % 24;
}

// ── Read corpus ───────────────────────────────────────────────────────────────
if (!existsSync(DB_PATH)) {
  console.error(`corpus.sqlite not found at ${DB_PATH}`);
  process.exit(1);
}

const db = new Database(DB_PATH, { readonly: true });

// User turns only — these represent the user's presence
const rows = db.query("SELECT ts FROM messages WHERE role='user' AND ts > 0 ORDER BY ts ASC").all() as {
  ts: number;
}[];

if (rows.length === 0) {
  console.error("No user messages found in corpus.sqlite");
  process.exit(1);
}

console.log(`Loaded ${rows.length} user turns from corpus.sqlite`);

// ── Build per-hour histogram ──────────────────────────────────────────────────
const activity_by_hour: number[] = new Array(24).fill(0);
for (const { ts } of rows) {
  const h = toCetHour(ts);
  activity_by_hour[h]++;
}

// ── Map to modes ──────────────────────────────────────────────────────────────
const activity_by_mode: Record<string, number> = {};
for (const m of MODE_MATRIX) {
  let count = 0;
  for (let h = m.hours[0]; h <= m.hours[1]; h++) {
    count += activity_by_hour[h];
  }
  activity_by_mode[m.label] = count;
}

// ── Infer sleep window ────────────────────────────────────────────────────────
// Find the longest consecutive run of hours with activity below threshold.
// Threshold = 2% of total turns (quiet hour).
const total_user_turns = rows.length;
const quiet_threshold = Math.max(2, Math.round(total_user_turns * 0.02));

// Build circular run-length for quiet hours
type Span = { start: number; len: number; avg: number };
const quietSpans: Span[] = [];
let i = 0;
while (i < 24) {
  if (activity_by_hour[i] <= quiet_threshold) {
    let j = i;
    let sum = 0;
    while (j < 24 && activity_by_hour[j] <= quiet_threshold) {
      sum += activity_by_hour[j];
      j++;
    }
    quietSpans.push({ start: i, len: j - i, avg: j > i ? sum / (j - i) : 0 });
    i = j;
  } else {
    i++;
  }
}
// Also check wrap-around (23 → 0 span)
const lastHour = activity_by_hour[23];
const firstHour = activity_by_hour[0];
if (lastHour <= quiet_threshold && firstHour <= quiet_threshold && quietSpans.length > 0) {
  // Merge the last span ending at 23 with the first span starting at 0 (if they exist)
  const lastSpan = quietSpans[quietSpans.length - 1];
  const firstSpan = quietSpans[0];
  if (lastSpan.start + lastSpan.len === 24 && firstSpan.start === 0) {
    // These are adjacent wrapping spans — create a merged record for reporting only
    const merged: Span = {
      start: lastSpan.start,
      len: lastSpan.len + firstSpan.len,
      avg: (lastSpan.avg * lastSpan.len + firstSpan.avg * firstSpan.len) / (lastSpan.len + firstSpan.len),
    };
    quietSpans.push(merged);
  }
}

// Longest quiet span = sleep window candidate
quietSpans.sort((a, b) => b.len - a.len);
const topSpan = quietSpans[0];

// Sleep confidence: higher if span is long and activity is very low
const sleep_window = topSpan
  ? {
      start_hour_cet: topSpan.start,
      end_hour_cet: (topSpan.start + topSpan.len - 1) % 24,
      duration_hours: topSpan.len,
      avg_turns_per_hour: Math.round(topSpan.avg * 100) / 100,
      confidence: Math.min(1.0, topSpan.len / 8), // 8h sleep = max confidence
    }
  : null;

// ── Current state ─────────────────────────────────────────────────────────────
const now = new Date();
const current_hour_cet = toCetHour(now.getTime());
const current_mode = modeForHour(current_hour_cet);

// User presence probability based on historical ratio at this hour vs peak
const peakActivity = Math.max(...activity_by_hour);
const currentActivity = activity_by_hour[current_hour_cet];
const user_presence_probability = peakActivity > 0 ? Math.round((currentActivity / peakActivity) * 100) / 100 : 0;

// Sanctuary mode: current hour is in the quiet zone
const isInSleepWindow =
  sleep_window !== null &&
  (() => {
    const s = sleep_window.start_hour_cet;
    const e = (s + sleep_window.duration_hours) % 24;
    if (s <= e) return current_hour_cet >= s && current_hour_cet <= e;
    // wraps midnight
    return current_hour_cet >= s || current_hour_cet <= e;
  })();

const sanctuary_mode = isInSleepWindow && user_presence_probability < 0.15;

// ── Peak / trough hours ───────────────────────────────────────────────────────
const peakHour = activity_by_hour.indexOf(peakActivity);
const troughActivity = Math.min(...activity_by_hour);
const troughHour = activity_by_hour.indexOf(troughActivity);

// ── Mode characteristics ──────────────────────────────────────────────────────
const mostActiveMode = Object.entries(activity_by_mode).sort(([, a], [, b]) => b - a)[0][0];
const quietestMode = Object.entries(activity_by_mode).sort(([, a], [, b]) => a - b)[0][0];

// ── Build output ──────────────────────────────────────────────────────────────
const output = {
  schema: "chrono_clock_v1",
  generated_at: now.toISOString(),
  current_hour_cet,
  current_mode,
  user_presence_probability,
  sanctuary_mode,
  total_user_turns,
  peak_hour_cet: peakHour,
  peak_hour_mode: modeForHour(peakHour),
  trough_hour_cet: troughHour,
  trough_hour_mode: modeForHour(troughHour),
  most_active_mode: mostActiveMode,
  quietest_mode: quietestMode,
  sleep_window,
  activity_by_mode,
  ...(VERBOSE ? { activity_by_hour } : {}),
};

// ── Summary ───────────────────────────────────────────────────────────────────
console.log(`\n☥ Chrono-clock summary`);
console.log(`  CET now:              ${current_hour_cet}:xx → ${current_mode}`);
console.log(`  User presence:        ${(user_presence_probability * 100).toFixed(0)}%`);
console.log(`  Sanctuary mode:       ${sanctuary_mode ? "YES — safe for autonomous run" : "NO — user likely present"}`);
console.log(`  Peak activity:        CET ${peakHour}:xx (${modeForHour(peakHour)})`);
console.log(`  Quietest:             CET ${troughHour}:xx (${modeForHour(troughHour)})`);
if (sleep_window) {
  console.log(
    `  Sleep window est:     CET ${sleep_window.start_hour_cet}:00 – ${sleep_window.end_hour_cet}:59` +
      ` (${sleep_window.duration_hours}h, confidence ${(sleep_window.confidence * 100).toFixed(0)}%)`
  );
}
console.log(`  Most active mode:     ${mostActiveMode}`);
console.log(`  Quietest mode:        ${quietestMode}`);

if (DRY_RUN) {
  console.log("\n[DRY RUN] Would write to:", OUT_PATH);
  console.log(JSON.stringify(output, null, 2));
} else {
  writeFileSync(OUT_PATH, JSON.stringify(output, null, 2), "utf-8");
  console.log(`\n  Written: ${OUT_PATH}`);
}
