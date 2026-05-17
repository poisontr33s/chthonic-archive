#!/usr/bin/env bun

// @SID: SCRIPT_MCP_GITHUB_ARCHAEOLOGY_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: mcp-github-archaeology.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🏴‍☠️ THE CROW'S NEST
// ║ Ogdoad-Ceque Radiance: (compound — feeds copilot-triage Rust layer)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * GitHub Archaeology MCP Server
 *
 * @SID           TOOL_MCP_GITHUB_ARCHAEOLOGY_V1
 * @Shabti        MCP Server (stdio transport)
 * @Purpose       Exposes structured GitHub PR/issue triage tools to Copilot.
 *                Three tools:
 *                  1. github_pr_triage       — list open PRs with full triage data
 *                  2. github_pr_analyze      — deep-dive a single PR
 *                  3. github_archaeology_report — emit manifest/pr_triage_report.json
 *
 * @Layer         A — passive data surface (Copilot calls us)
 * @Pair          tools/copilot-triage/ (Layer B — Rust binary drives Copilot sessions)
 *
 * Usage (stdio MCP, registered in .vscode/mcp.json):
 *   bun run scripts/mcp-github-archaeology.ts
 *
 * Env:
 *   ARCHAEOLOGY_REPO  — default: poisontr33s/Restructure-MCP-Orchestration
 *   MANIFEST_DIR      — override manifest output dir
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { $ } from "bun";
import { mkdir, writeFile } from "fs/promises";
import { existsSync } from "fs";
import { resolve } from "path";

// ── Config ────────────────────────────────────────────────────────────────────

const DEFAULT_REPO = "poisontr33s/Restructure-MCP-Orchestration";
const MANIFEST_DIR = process.env.MANIFEST_DIR
  ? process.env.MANIFEST_DIR
  : resolve(import.meta.dir, "..", "manifest");

// ── GitHub API helpers ────────────────────────────────────────────────────────

async function ghToken(): Promise<string> {
  const result = await $`gh auth token`.text();
  return result.trim();
}

async function ghApi<T>(path: string, token: string): Promise<T> {
  const res = await fetch(`https://api.github.com${path}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "chthonic-archive/mcp-github-archaeology",
    },
  });
  if (!res.ok) {
    throw new Error(
      `GitHub API ${path} → HTTP ${res.status}: ${await res.text()}`
    );
  }
  return res.json() as Promise<T>;
}

// Paginate through all pages of a list endpoint
async function ghApiAll<T>(basePath: string, token: string): Promise<T[]> {
  const all: T[] = [];
  let page = 1;
  while (true) {
    const sep = basePath.includes("?") ? "&" : "?";
    const batch = await ghApi<T[]>(
      `${basePath}${sep}per_page=100&page=${page}`,
      token
    );
    if (!batch.length) break;
    all.push(...batch);
    if (batch.length < 100) break;
    page++;
  }
  return all;
}

// ── Triage data builders ──────────────────────────────────────────────────────

interface PRSummary {
  number: number;
  title: string;
  state: string;
  draft: boolean;
  author: string;
  created_at: string;
  updated_at: string;
  age_days: number;
  labels: string[];
  head_ref: string;
  base_ref: string;
  mergeable: string | null;
  mergeable_state: string | null;
  review_decision: string | null;
  files_changed: number;
  additions: number;
  deletions: number;
  checks_status: string;
  url: string;
}

interface PRDetail extends PRSummary {
  body: string | null;
  commits: number;
  changed_files: string[];
  review_threads: ReviewThread[];
  checks: CheckRun[];
  conflicts: boolean;
}

interface ReviewThread {
  id: number;
  resolved: boolean;
  comments: number;
  path: string | null;
}

interface CheckRun {
  name: string;
  status: string;
  conclusion: string | null;
  url: string;
}

async function buildPRSummary(
  pr: Record<string, unknown>,
  token: string,
  owner: string,
  repo: string
): Promise<PRSummary> {
  const number = pr.number as number;
  const createdAt = new Date(pr.created_at as string);
  const ageDays = Math.floor(
    (Date.now() - createdAt.getTime()) / (1000 * 60 * 60 * 24)
  );

  // Fetch check runs for the head SHA
  let checksStatus = "unknown";
  try {
    const sha = (pr.head as Record<string, unknown>).sha as string;
    const checksData = await ghApi<{ check_runs: Array<Record<string, unknown>> }>(
      `/repos/${owner}/${repo}/commits/${sha}/check-runs`,
      token
    );
    const runs = checksData.check_runs;
    if (runs.length === 0) {
      checksStatus = "no_checks";
    } else {
      const failed = runs.filter(
        (r) => r.conclusion === "failure" || r.conclusion === "timed_out"
      );
      const pending = runs.filter(
        (r) => r.status === "in_progress" || r.status === "queued"
      );
      if (failed.length > 0) checksStatus = "failing";
      else if (pending.length > 0) checksStatus = "pending";
      else checksStatus = "passing";
    }
  } catch {
    checksStatus = "fetch_failed";
  }

  return {
    number,
    title: pr.title as string,
    state: pr.state as string,
    draft: (pr.draft as boolean) ?? false,
    author: ((pr.user as Record<string, unknown>)?.login as string) ?? "unknown",
    created_at: pr.created_at as string,
    updated_at: pr.updated_at as string,
    age_days: ageDays,
    labels: ((pr.labels as Array<Record<string, unknown>>) ?? []).map(
      (l) => l.name as string
    ),
    head_ref: (pr.head as Record<string, unknown>).ref as string,
    base_ref: (pr.base as Record<string, unknown>).ref as string,
    mergeable: (pr.mergeable as string | null) ?? null,
    mergeable_state: (pr.mergeable_state as string | null) ?? null,
    review_decision: (pr.review_decision as string | null) ?? null,
    files_changed: (pr.changed_files as number) ?? 0,
    additions: (pr.additions as number) ?? 0,
    deletions: (pr.deletions as number) ?? 0,
    checks_status: checksStatus,
    url: pr.html_url as string,
  };
}

// ── MCP Server ────────────────────────────────────────────────────────────────

const server = new Server(
  { name: "github-archaeology", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "github_pr_triage",
      description:
        "List all open pull requests for a GitHub repo with full triage data: " +
        "age, labels, checks status, mergeable state, review decision, diff size. " +
        "Returns structured JSON suitable for prioritization and batch decisions.",
      inputSchema: {
        type: "object",
        properties: {
          repo: {
            type: "string",
            description: `GitHub repo in owner/name format. Default: ${DEFAULT_REPO}`,
          },
          state: {
            type: "string",
            enum: ["open", "closed", "all"],
            description: "PR state filter. Default: open",
          },
          sort_by: {
            type: "string",
            enum: ["age_desc", "age_asc", "updated", "checks"],
            description: "Sort order for results. Default: age_desc (oldest first)",
          },
        },
      },
    },
    {
      name: "github_pr_analyze",
      description:
        "Deep analysis of a single pull request: full diff stats, changed file paths, " +
        "review threads (resolved/unresolved), CI check details, merge conflict status, PR body. " +
        "Use after github_pr_triage to investigate specific PRs.",
      inputSchema: {
        type: "object",
        required: ["number"],
        properties: {
          number: {
            type: "number",
            description: "Pull request number",
          },
          repo: {
            type: "string",
            description: `GitHub repo in owner/name format. Default: ${DEFAULT_REPO}`,
          },
        },
      },
    },
    {
      name: "github_archaeology_report",
      description:
        "Generate a complete archaeology report across all open PRs and write it to " +
        "manifest/pr_triage_report.json. Returns the report path and a summary. " +
        "The report is machine-readable input for tools/copilot-triage (Layer B Rust binary).",
      inputSchema: {
        type: "object",
        properties: {
          repo: {
            type: "string",
            description: `GitHub repo in owner/name format. Default: ${DEFAULT_REPO}`,
          },
        },
      },
    },
    {
      name: "github_chronicle",
      description:
        "Build a unified chronological timeline of ALL git commits, GitHub issues, and " +
        "GitHub PRs from the beginning of the repo to now. Events are sorted by timestamp " +
        "ascending (oldest first). Writes manifest/git_chronicle.json and " +
        "manifest/git_chronicle.md. Returns timeline stats and the path to the manifest.",
      inputSchema: {
        type: "object",
        properties: {
          repo: {
            type: "string",
            description: `GitHub repo in owner/name format. Default: ${DEFAULT_REPO}`,
          },
          limit: {
            type: "number",
            description: "Max number of git commits to include. Default: 2000",
          },
          since: {
            type: "string",
            description: "Only include events after this ISO date, e.g. 2024-01-01",
          },
          summary_mode: {
            type: "boolean",
            description: "Return a compact last-30-events text summary instead of stats JSON. Default: false",
          },
        },
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const repo = (args?.repo as string | undefined) ?? DEFAULT_REPO;
  const [owner, repoName] = repo.split("/");

  if (!owner || !repoName) {
    throw new Error(`Invalid repo format: "${repo}" — expected owner/name`);
  }

  let token: string;
  try {
    token = await ghToken();
  } catch (e) {
    throw new Error(
      `gh auth token failed — run 'gh auth login' first: ${e instanceof Error ? e.message : String(e)}`
    );
  }

  // ── Tool: github_pr_triage ─────────────────────────────────────────────────
  if (name === "github_pr_triage") {
    const state = (args?.state as string | undefined) ?? "open";
    const sortBy = (args?.sort_by as string | undefined) ?? "age_desc";

    const prs = await ghApiAll<Record<string, unknown>>(
      `/repos/${owner}/${repoName}/pulls?state=${state}`,
      token
    );

    const summaries: PRSummary[] = await Promise.all(
      prs.map((pr) => buildPRSummary(pr, token, owner, repoName))
    );

    // Sort
    if (sortBy === "age_desc") summaries.sort((a, b) => b.age_days - a.age_days);
    else if (sortBy === "age_asc") summaries.sort((a, b) => a.age_days - b.age_days);
    else if (sortBy === "updated")
      summaries.sort(
        (a, b) =>
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      );
    else if (sortBy === "checks") {
      const order: Record<string, number> = {
        failing: 0,
        pending: 1,
        passing: 2,
        no_checks: 3,
        unknown: 4,
        fetch_failed: 5,
      };
      summaries.sort(
        (a, b) => (order[a.checks_status] ?? 9) - (order[b.checks_status] ?? 9)
      );
    }

    const text = JSON.stringify({ repo, total: summaries.length, prs: summaries }, null, 2);
    return { content: [{ type: "text", text }] };
  }

  // ── Tool: github_pr_analyze ────────────────────────────────────────────────
  if (name === "github_pr_analyze") {
    const number = args?.number as number;
    if (!number) throw new Error("number is required");

    // Fetch PR detail (includes mergeable, review_decision)
    const pr = await ghApi<Record<string, unknown>>(
      `/repos/${owner}/${repoName}/pulls/${number}`,
      token
    );
    const summary = await buildPRSummary(pr, token, owner, repoName);

    // Files changed
    let changedFiles: string[] = [];
    try {
      const files = await ghApiAll<Record<string, unknown>>(
        `/repos/${owner}/${repoName}/pulls/${number}/files`,
        token
      );
      changedFiles = files.map((f) => f.filename as string);
    } catch { /* non-fatal */ }

    // Review threads via GraphQL (REST gives reviews, not threads)
    let reviewThreads: ReviewThread[] = [];
    try {
      const reviews = await ghApiAll<Record<string, unknown>>(
        `/repos/${owner}/${repoName}/pulls/${number}/reviews`,
        token
      );
      // Map review comments as pseudo-threads (REST limitation — GraphQL would be cleaner)
      const comments = await ghApiAll<Record<string, unknown>>(
        `/repos/${owner}/${repoName}/pulls/${number}/comments`,
        token
      );
      // Group by in_reply_to_id to approximate threads
      const threads = new Map<number, Array<Record<string, unknown>>>();
      for (const c of comments) {
        const rootId = (c.in_reply_to_id as number | null) ?? (c.id as number);
        const bucket = threads.get(rootId) ?? [];
        bucket.push(c);
        threads.set(rootId, bucket);
      }
      reviewThreads = Array.from(threads.entries()).map(([id, thread]) => ({
        id,
        resolved: false, // REST API doesn't expose resolved state directly
        comments: thread.length,
        path: (thread[0]?.path as string | null) ?? null,
      }));
    } catch { /* non-fatal */ }

    // CI checks
    let checks: CheckRun[] = [];
    try {
      const sha = (pr.head as Record<string, unknown>).sha as string;
      const checksData = await ghApi<{
        check_runs: Array<Record<string, unknown>>;
      }>(`/repos/${owner}/${repoName}/commits/${sha}/check-runs`, token);
      checks = checksData.check_runs.map((r) => ({
        name: r.name as string,
        status: r.status as string,
        conclusion: (r.conclusion as string | null) ?? null,
        url: (r.html_url as string) ?? "",
      }));
    } catch { /* non-fatal */ }

    const detail: PRDetail = {
      ...summary,
      body: (pr.body as string | null) ?? null,
      commits: (pr.commits as number) ?? 0,
      changed_files: changedFiles,
      review_threads: reviewThreads,
      checks,
      conflicts: pr.mergeable === false,
    };

    return {
      content: [{ type: "text", text: JSON.stringify(detail, null, 2) }],
    };
  }

  // ── Tool: github_archaeology_report ───────────────────────────────────────
  if (name === "github_archaeology_report") {
    const prs = await ghApiAll<Record<string, unknown>>(
      `/repos/${owner}/${repoName}/pulls?state=open`,
      token
    );

    const summaries: PRSummary[] = await Promise.all(
      prs.map((pr) => buildPRSummary(pr, token, owner, repoName))
    );
    summaries.sort((a, b) => b.age_days - a.age_days);

    const failing = summaries.filter((p) => p.checks_status === "failing");
    const clean = summaries.filter(
      (p) => p.checks_status === "passing" && p.mergeable !== false
    );
    const stale = summaries.filter((p) => p.age_days > 30);

    const report = {
      generated_at: new Date().toISOString(),
      repo,
      summary: {
        total_open: summaries.length,
        failing_checks: failing.length,
        merge_ready: clean.length,
        stale_30d: stale.length,
        draft: summaries.filter((p) => p.draft).length,
      },
      triage: {
        immediate_action: failing.map((p) => ({ number: p.number, title: p.title, reason: "failing_checks" })),
        merge_candidates: clean.map((p) => ({ number: p.number, title: p.title, age_days: p.age_days })),
        stale_candidates: stale.map((p) => ({
          number: p.number,
          title: p.title,
          age_days: p.age_days,
          reason: "stale > 30d",
        })),
      },
      all_prs: summaries,
    };

    // Ensure manifest dir exists
    if (!existsSync(MANIFEST_DIR)) {
      await mkdir(MANIFEST_DIR, { recursive: true });
    }

    const outputPath = resolve(MANIFEST_DIR, "pr_triage_report.json");
    await writeFile(outputPath, JSON.stringify(report, null, 2), "utf-8");

    const summary = `Archaeology report written → ${outputPath}
Repo: ${repo}
Open PRs: ${report.summary.total_open}
Failing checks: ${report.summary.failing_checks}
Merge-ready: ${report.summary.merge_ready}
Stale (>30d): ${report.summary.stale_30d}
Draft: ${report.summary.draft}`;

    return {
      content: [
        {
          type: "text",
          text: summary,
        },
      ],
    };
  }

  // ── Tool: github_chronicle ────────────────────────────────────────────────
  if (name === "github_chronicle") {
    const limit = (args?.limit as number | undefined) ?? 2000;
    const since = (args?.since as string | undefined) ?? "";
    const summaryMode = (args?.summary_mode as boolean | undefined) ?? false;

    const scriptPath = resolve(import.meta.dir, "git-chronicle.ts");
    const scriptArgs = [
      `--repo`, repo,
      `--limit`, String(limit),
      ...(since ? [`--since`, since] : []),
      ...(summaryMode ? [`--summary`] : [`--no-md`]),
    ];

    let output = "";
    let stderr = "";
    try {
      const proc = Bun.spawn(["bun", "run", scriptPath, ...scriptArgs], {
        stdout: "pipe",
        stderr: "pipe",
        cwd: resolve(import.meta.dir, ".."),
      });
      const [stdoutText, stderrText] = await Promise.all([
        new Response(proc.stdout).text(),
        new Response(proc.stderr).text(),
      ]);
      await proc.exited;
      output = stdoutText;
      stderr = stderrText;
    } catch (e) {
      throw new Error(`git-chronicle failed: ${e instanceof Error ? e.message : String(e)}`);
    }

    const logLines = stderr.trim().split("\n").slice(-6).join("\n");
    const text = summaryMode
      ? output
      : `${output}\n\nProgress log:\n${logLines}`;

    return { content: [{ type: "text", text: text.trim() }] };
  }

  throw new Error(`Unknown tool: ${name}`);
});

// ── Start ─────────────────────────────────────────────────────────────────────

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("GitHub Archaeology MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal:", error);
  process.exit(1);
});
