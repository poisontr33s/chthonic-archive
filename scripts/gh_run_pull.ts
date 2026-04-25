#!/usr/bin/env bun
// @SID: GH_RUN_PULL_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ scripts/gh_run_pull.ts
// ║ Pull GitHub Actions run data into manifest/gh_runs/ for CI membrane use.
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Reads recent workflow runs via `gh` CLI. Writes structured JSON to
// ║ manifest/gh_runs/ where the CI smoke check and future agents can read it.
// ║
// ║ This is the upstream extension of the Probe-Manifest-CI-Membrane pattern:
// ║   GitHub Actions runs → manifest/gh_runs/*.json → ci/checks reads manifests
// ║
// ║ Flags:
// ║   --limit <n>     Number of runs to fetch (default: 20)
// ║   --workflow <w>  Filter to specific workflow name/file (optional)
// ║   --jobs          Fetch job-level details for each run (slower)
// ║   --logs <id>     Fetch failure log for a specific run ID
// ║   --report        Print index JSON to stdout and exit
// ║   --json          Alias for --report
// ║
// ║ Output:
// ║   manifest/gh_runs/index.json       — summary of recent runs
// ║   manifest/gh_runs/<run_id>.json    — per-run detail (with --jobs)
// ║   manifest/gh_runs/failures.json    — failed runs summary (always written)
// ╚════════════════════════════════════════════════════════════════════════════

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "fs";
import { resolve } from "path";
import { execSync, spawnSync } from "child_process";

const REPO_ROOT = resolve(import.meta.dir, "..");
const GH_RUNS_DIR = resolve(REPO_ROOT, "manifest", "gh_runs");
const REPO = "poisontr33s/chthonic-archive";

const args = process.argv.slice(2);
const flag = (name: string) => args.includes(name);
const opt = (name: string): string | null => {
  const i = args.indexOf(name);
  return i !== -1 && i + 1 < args.length ? args[i + 1] : null;
};

const LIMIT = Number(opt("--limit") ?? "20");
const WORKFLOW_FILTER = opt("--workflow");
const FETCH_JOBS = flag("--jobs");
const LOGS_RUN_ID = opt("--logs");
const REPORT = flag("--report") || flag("--json");

// ── Types ─────────────────────────────────────────────────────────────────────

interface GhRun {
  databaseId: number;
  name: string;
  status: string;
  conclusion: string | null;
  createdAt: string;
  updatedAt: string;
  headSha: string;
  headBranch: string;
  event: string;
  url: string;
  workflowName?: string;
  workflowDatabaseId?: number;
  displayTitle?: string;
}

interface GhJobStep {
  name: string;
  status: string;
  conclusion: string | null;
  number: number;
  startedAt: string | null;
  completedAt: string | null;
}

interface GhJob {
  databaseId: number;
  name: string;
  status: string;
  conclusion: string | null;
  startedAt: string;
  completedAt: string | null;
  steps: GhJobStep[];
}

interface RunDetail {
  run_id: number;
  fetched_at: string;
  summary: GhRun;
  jobs?: GhJob[];
  failure_steps?: { job: string; step: string; conclusion: string }[];
}

interface RunIndex {
  repo: string;
  generated: string;
  limit: number;
  total_fetched: number;
  workflow_filter: string | null;
  runs: GhRun[];
  failure_summary: {
    total: number;
    by_workflow: Record<string, number>;
    recent_failures: { id: number; name: string; created: string; sha: string }[];
  };
  success_rate: number;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function gh(...ghArgs: string[]): unknown {
  const result = spawnSync("gh", ghArgs, {
    encoding: "utf-8",
    env: { ...process.env },
  });
  if (result.status !== 0) {
    const errMsg = result.stderr?.trim() ?? "(no stderr)";
    throw new Error(`gh ${ghArgs.slice(0, 3).join(" ")} failed: ${errMsg}`);
  }
  return JSON.parse(result.stdout);
}

function ensureDir(dir: string): void {
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
}

// ── Fetch runs ────────────────────────────────────────────────────────────────

function fetchRuns(): GhRun[] {
  const runArgs = [
    "run", "list",
    "--repo", REPO,
    "--limit", String(LIMIT),
    "--json", "databaseId,name,status,conclusion,createdAt,updatedAt,headSha,headBranch,event,url,workflowName,workflowDatabaseId,displayTitle",
  ];
  if (WORKFLOW_FILTER) {
    runArgs.push("--workflow", WORKFLOW_FILTER);
  }
  return gh(...runArgs) as GhRun[];
}

function fetchJobs(runId: number): GhJob[] {
  try {
    const jobs = gh(
      "run", "view", String(runId),
      "--repo", REPO,
      "--json", "jobs",
    ) as { jobs: GhJob[] };
    return jobs.jobs ?? [];
  } catch {
    return [];
  }
}

function fetchFailureLog(runId: number): string {
  const result = spawnSync("gh", ["run", "view", String(runId), "--repo", REPO, "--log-failed"], {
    encoding: "utf-8",
    env: { ...process.env },
  });
  return result.stdout?.trim() ?? result.stderr?.trim() ?? "(no log)";
}

// ── Main ──────────────────────────────────────────────────────────────────────

// Handle --logs mode: fetch and print failure log for a run
if (LOGS_RUN_ID) {
  console.log(`Fetching failure log for run ${LOGS_RUN_ID}...`);
  const log = fetchFailureLog(Number(LOGS_RUN_ID));
  console.log(log);
  process.exit(0);
}

console.error(`[gh-run-pull] Fetching last ${LIMIT} runs from ${REPO}...`);
ensureDir(GH_RUNS_DIR);

let runs: GhRun[];
try {
  runs = fetchRuns();
} catch (e: any) {
  console.error(`[gh-run-pull] FAILED to fetch runs: ${e.message}`);
  process.exit(1);
}

console.error(`[gh-run-pull] ${runs.length} runs fetched.`);

// Compute failure summary
const concluded = runs.filter((r) => r.status === "completed");
const failed = concluded.filter((r) => r.conclusion === "failure" || r.conclusion === "timed_out");
const byWorkflow: Record<string, number> = {};
for (const r of failed) {
  const wf = r.workflowName ?? r.name ?? "unknown";
  byWorkflow[wf] = (byWorkflow[wf] ?? 0) + 1;
}
const successRate =
  concluded.length > 0
    ? Math.round(((concluded.length - failed.length) / concluded.length) * 100)
    : 100;

// Fetch per-run job details if requested
if (FETCH_JOBS) {
  console.error(`[gh-run-pull] Fetching job details for ${runs.length} runs...`);
  for (const run of runs) {
    const jobs = fetchJobs(run.databaseId);
    const failureSteps = jobs.flatMap((j) =>
      (j.steps ?? [])
        .filter((s) => s.conclusion === "failure")
        .map((s) => ({ job: j.name, step: s.name, conclusion: s.conclusion ?? "failure" }))
    );
    const detail: RunDetail = {
      run_id: run.databaseId,
      fetched_at: new Date().toISOString(),
      summary: run,
      jobs,
      failure_steps: failureSteps,
    };
    const detailPath = resolve(GH_RUNS_DIR, `${run.databaseId}.json`);
    writeFileSync(detailPath, JSON.stringify(detail, null, 2));
    console.error(`  wrote ${run.databaseId}.json (${jobs.length} jobs, ${failureSteps.length} failed steps)`);
  }
}

// Build index
const index: RunIndex = {
  repo: REPO,
  generated: new Date().toISOString(),
  limit: LIMIT,
  total_fetched: runs.length,
  workflow_filter: WORKFLOW_FILTER,
  runs,
  failure_summary: {
    total: failed.length,
    by_workflow: byWorkflow,
    recent_failures: failed.slice(0, 5).map((r) => ({
      id: r.databaseId,
      name: r.workflowName ?? r.name,
      created: r.createdAt,
      sha: r.headSha.substring(0, 8),
    })),
  },
  success_rate: successRate,
};

// Write index
const indexPath = resolve(GH_RUNS_DIR, "index.json");
writeFileSync(indexPath, JSON.stringify(index, null, 2));
console.error(`[gh-run-pull] ✓ Wrote manifest/gh_runs/index.json`);

// Write failures separately (always, even without --jobs)
const failuresPath = resolve(GH_RUNS_DIR, "failures.json");
writeFileSync(failuresPath, JSON.stringify({
  generated: new Date().toISOString(),
  total_failed: failed.length,
  success_rate: successRate,
  by_workflow: byWorkflow,
  failures: failed,
}, null, 2));
console.error(`[gh-run-pull] ✓ Wrote manifest/gh_runs/failures.json`);

if (REPORT) {
  console.log(JSON.stringify(index, null, 2));
} else {
  // Summary to stdout
  console.log(`[gh-run-pull] runs=${runs.length} concluded=${concluded.length} failed=${failed.length} success_rate=${successRate}%`);
  if (Object.keys(byWorkflow).length > 0) {
    for (const [wf, count] of Object.entries(byWorkflow).sort((a, b) => b[1] - a[1])) {
      console.log(`  ✗ ${wf}: ${count} failure(s)`);
    }
  }
}
