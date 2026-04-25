#!/usr/bin/env bun
// @SID: GH_RUN_SMOKE_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ ci/checks/gh-run-smoke.ts
// ║ CI membrane gate for GitHub Actions run manifest data.
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Reads manifest/gh_runs/index.json (produced by scripts/gh_run_pull.ts).
// ║ Reports workflow health: failure rates, persistent failures, success rate.
// ║
// ║ Flags:
// ║   --report   Print full JSON report to stdout and exit
// ║   --strict   Exit 1 if pentea-cloud-dispatch.yml has any failures in index
// ║
// ║ Exit codes:
// ║   0 — healthy, absent (no manifest yet), or within thresholds
// ║   1 — persistent failures detected (--strict mode), or manifest corrupt
// ╚════════════════════════════════════════════════════════════════════════════

import { existsSync, readFileSync } from "fs";
import { resolve } from "path";

const REPO_ROOT = resolve(import.meta.dir, "../..");
const INDEX_PATH = resolve(REPO_ROOT, "manifest", "gh_runs", "index.json");
const FAILURES_PATH = resolve(REPO_ROOT, "manifest", "gh_runs", "failures.json");

const STRICT = process.argv.includes("--strict");
const REPORT = process.argv.includes("--report");

// ── Types (must match gh_run_pull.ts index shape) ─────────────────────────────

interface RunIndex {
  repo: string;
  generated: string;
  limit: number;
  total_fetched: number;
  workflow_filter: string | null;
  runs: { databaseId: number; workflowName?: string; name: string; conclusion: string | null; createdAt: string; headBranch: string }[];
  failure_summary: {
    total: number;
    by_workflow: Record<string, number>;
    recent_failures: { id: number; name: string; created: string; sha: string }[];
  };
  success_rate: number;
}

interface SmokeResult {
  status: "healthy" | "absent" | "degraded" | "critical";
  generated_at: string;
  manifest_path: string;
  manifest_present: boolean;
  manifest_age_minutes: number | null;
  total_runs: number;
  success_rate: number;
  failure_count: number;
  by_workflow: Record<string, number>;
  dispatch_workflow_failures: number;
  dispatch_consecutive_fail: boolean;
  recent_failures: { id: number; name: string; created: string; sha: string }[];
  notes: string[];
}

// ── Main ──────────────────────────────────────────────────────────────────────

const result: SmokeResult = {
  status: "absent",
  generated_at: new Date().toISOString(),
  manifest_path: INDEX_PATH,
  manifest_present: false,
  manifest_age_minutes: null,
  total_runs: 0,
  success_rate: 100,
  failure_count: 0,
  by_workflow: {},
  dispatch_workflow_failures: 0,
  dispatch_consecutive_fail: false,
  recent_failures: [],
  notes: [],
};

if (!existsSync(INDEX_PATH)) {
  result.notes.push("manifest/gh_runs/index.json not found — run: bun run scripts/gh_run_pull.ts");
  if (REPORT) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log("✓ gh-run-smoke: manifest absent (run gh_run_pull.ts to populate)");
  }
  process.exit(0);
}

// Parse index
let index: RunIndex;
try {
  index = JSON.parse(readFileSync(INDEX_PATH, "utf-8"));
} catch (e: any) {
  result.status = "critical";
  result.notes.push(`Failed to parse index.json: ${e.message}`);
  if (REPORT) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.error(`✗ gh-run-smoke: index.json corrupt — ${e.message}`);
  }
  process.exit(1);
}

result.manifest_present = true;

// Compute manifest age
const manifestMs = new Date(index.generated).getTime();
const ageMs = Date.now() - manifestMs;
result.manifest_age_minutes = Math.round(ageMs / 60000);

result.total_runs = index.total_fetched;
result.success_rate = index.success_rate;
result.failure_count = index.failure_summary.total;
result.by_workflow = index.failure_summary.by_workflow;
result.recent_failures = index.failure_summary.recent_failures;

// Pentea dispatch workflow specific check
const DISPATCH_WF = ".github/workflows/pentea-cloud-dispatch.yml";
const DISPATCH_WF_SHORT = "Pentea Cloud Dispatch";
const dispatchFails =
  (index.failure_summary.by_workflow[DISPATCH_WF] ?? 0) +
  (index.failure_summary.by_workflow[DISPATCH_WF_SHORT] ?? 0);
result.dispatch_workflow_failures = dispatchFails;

// Check if ALL pentea-cloud-dispatch runs in the index are failures
const dispatchRuns = index.runs.filter(
  (r) => (r.workflowName ?? r.name) === DISPATCH_WF || (r.workflowName ?? r.name) === DISPATCH_WF_SHORT
);
const allDispatchFailed =
  dispatchRuns.length > 0 && dispatchRuns.every((r) => r.conclusion === "failure" || r.conclusion === "timed_out");
result.dispatch_consecutive_fail = allDispatchFailed;

// Status
if (allDispatchFailed && dispatchFails > 0) {
  result.status = "critical";
  result.notes.push(
    `pentea-cloud-dispatch.yml has failed on ALL ${dispatchFails} run(s) in manifest — workflow needs repair`
  );
} else if (result.success_rate < 50) {
  result.status = "degraded";
  result.notes.push(`Overall success rate is ${result.success_rate}% — check Dependabot Updates failures`);
} else {
  result.status = "healthy";
}

if (result.manifest_age_minutes > 60) {
  result.notes.push(
    `Manifest is ${result.manifest_age_minutes} minutes old — re-run: bun run scripts/gh_run_pull.ts`
  );
}

// Output
if (REPORT) {
  console.log(JSON.stringify(result, null, 2));
} else {
  const icon = result.status === "healthy" ? "✓" : result.status === "degraded" ? "⚠" : "✗";
  const dispatchMsg = dispatchFails > 0 ? ` dispatch_failures=${dispatchFails}` : "";
  console.log(
    `${icon} gh-run-smoke: status=${result.status} runs=${result.total_runs} success_rate=${result.success_rate}%${dispatchMsg}`
  );
  for (const note of result.notes) {
    console.log(`  → ${note}`);
  }
}

// Exit code
if (STRICT && (result.dispatch_consecutive_fail || result.status === "critical")) {
  process.exit(1);
}

process.exit(0);
