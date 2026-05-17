#!/usr/bin/env bun

// @SID: SCRIPT_GIT_CHRONICLE_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: git-chronicle.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🏴‍☠️ THE CROW'S NEST
// ║ Ogdoad-Ceque Radiance: (feeds mcp-github-archaeology → github_chronicle)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * git-chronicle.ts — Chronological Git + GitHub issue/PR timeline
 *
 * @SID           TOOL_GIT_CHRONICLE_V1
 * @Shabti        CLI + MCP data provider
 * @Purpose       Merge git commits + GitHub issues + GitHub PRs into a single
 *                chronological stream from repo creation to now.
 *                Emits manifest/git_chronicle.json (machine) and
 *                manifest/git_chronicle.md (human digest).
 *
 * Usage:
 *   bun run scripts/git-chronicle.ts                     # full timeline
 *   bun run scripts/git-chronicle.ts --repo owner/name   # explicit repo
 *   bun run scripts/git-chronicle.ts --no-md             # JSON only
 *   bun run scripts/git-chronicle.ts --limit 500         # cap commits
 *   bun run scripts/git-chronicle.ts --since 2024-01-01  # from date (ISO)
 *   bun run scripts/git-chronicle.ts --summary           # compact stdout digest
 *
 * Env:
 *   CHRONICLE_REPO  — override repo (owner/name)
 *   MANIFEST_DIR    — override manifest output directory
 */

import { $ } from "bun";
import { mkdir, writeFile } from "fs/promises";
import { resolve } from "path";

// ── Types ─────────────────────────────────────────────────────────────────────

type EventType =
  | "commit"
  | "issue_opened"
  | "issue_closed"
  | "issue_reopened"
  | "pr_opened"
  | "pr_merged"
  | "pr_closed"
  | "pr_reopened";

interface TimelineEvent {
  type: EventType;
  timestamp: string; // ISO 8601
  id: string; // hash for commits, "issue-N" / "pr-N" for others
  title: string;
  author: string;
  url: string;
  // commit-specific
  hash?: string;
  short_hash?: string;
  refs?: string; // branch/tag decorations
  // issue/pr-specific
  number?: number;
  state?: "open" | "closed" | "merged";
  labels?: string[];
  body_summary?: string; // first 200 chars of body
}

interface ChronicleOutput {
  generated_at: string;
  repo: string;
  total_events: number;
  commit_count: number;
  issue_count: number;
  pr_count: number;
  first_event: string | null;
  last_event: string | null;
  events: TimelineEvent[];
}

// ── GitHub API ────────────────────────────────────────────────────────────────

async function ghToken(): Promise<string> {
  const result = await $`gh auth token`.text();
  return result.trim();
}

async function ghFetch<T>(path: string, token: string): Promise<T> {
  const res = await fetch(`https://api.github.com${path}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "chthonic-archive/git-chronicle",
    },
  });
  if (!res.ok) {
    throw new Error(`GitHub API ${path} → HTTP ${res.status}: ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

async function ghFetchAll<T>(
  basePath: string,
  token: string,
  maxPages = 100
): Promise<T[]> {
  const all: T[] = [];
  let page = 1;
  while (page <= maxPages) {
    const sep = basePath.includes("?") ? "&" : "?";
    const batch = await ghFetch<T[]>(
      `${basePath}${sep}per_page=100&page=${page}`,
      token
    );
    if (!batch || !batch.length) break;
    all.push(...batch);
    if (batch.length < 100) break;
    page++;
  }
  return all;
}

// ── Git log ───────────────────────────────────────────────────────────────────

interface RawCommit {
  hash: string;
  short_hash: string;
  timestamp: string;
  author: string;
  subject: string;
  refs: string;
}

async function getCommits(opts: {
  limit: number;
  since?: string;
  repoRoot: string;
}): Promise<RawCommit[]> {
  const sep = "|||";
  const fmt = `%H${sep}%h${sep}%aI${sep}%an${sep}%s${sep}%D`;
  const args = [`--format=${fmt}`, `--no-walk=unsorted`];

  // --no-walk can't be combined with --all for full history; use log --all
  const sinceArg = opts.since ? `--after=${opts.since}` : "";
  const limitArg = `--max-count=${opts.limit}`;

  let raw: string;
  try {
    if (opts.since) {
      raw = await $`git -C ${opts.repoRoot} log --all --format=${fmt} ${sinceArg} ${limitArg}`.text();
    } else {
      raw = await $`git -C ${opts.repoRoot} log --all --format=${fmt} ${limitArg}`.text();
    }
  } catch {
    // fallback: current branch only
    raw = await $`git -C ${opts.repoRoot} log --format=${fmt} ${limitArg}`.text();
  }

  const commits: RawCommit[] = [];
  for (const line of raw.trim().split("\n")) {
    if (!line.trim()) continue;
    const parts = line.split(sep);
    if (parts.length < 5) continue;
    commits.push({
      hash: parts[0].trim(),
      short_hash: parts[1].trim(),
      timestamp: parts[2].trim(),
      author: parts[3].trim(),
      subject: parts[4].trim(),
      refs: (parts[5] || "").trim(),
    });
  }
  // git log is newest-first; reverse to chronological ascending
  return commits.reverse();
}

// ── GitHub issues + PRs ───────────────────────────────────────────────────────

type RawIssue = Record<string, unknown>;

function summarizeBody(body: unknown): string {
  if (!body || typeof body !== "string") return "";
  return body.replace(/\r?\n/g, " ").trim().slice(0, 200);
}

function toIssueEvents(issues: RawIssue[]): TimelineEvent[] {
  const events: TimelineEvent[] = [];
  for (const issue of issues) {
    const num = issue.number as number;
    const isPR = !!(issue.pull_request as unknown);
    if (isPR) continue; // PRs come via /pulls endpoint

    const title = issue.title as string;
    const author = ((issue.user as Record<string, unknown>)?.login as string) ?? "ghost";
    const labels = ((issue.labels as Array<Record<string, unknown>>) ?? []).map(
      (l) => l.name as string
    );
    const url = issue.html_url as string;
    const body_summary = summarizeBody(issue.body);

    // opened event
    events.push({
      type: "issue_opened",
      timestamp: issue.created_at as string,
      id: `issue-${num}`,
      title,
      author,
      url,
      number: num,
      state: "open",
      labels,
      body_summary,
    });

    // closed event (if applicable)
    if (issue.state === "closed" && issue.closed_at) {
      events.push({
        type: "issue_closed",
        timestamp: issue.closed_at as string,
        id: `issue-${num}-closed`,
        title: `[closed] ${title}`,
        author,
        url,
        number: num,
        state: "closed",
        labels,
      });
    }
  }
  return events;
}

function toPREvents(prs: RawIssue[]): TimelineEvent[] {
  const events: TimelineEvent[] = [];
  for (const pr of prs) {
    const num = pr.number as number;
    const title = pr.title as string;
    const author = ((pr.user as Record<string, unknown>)?.login as string) ?? "ghost";
    const labels = ((pr.labels as Array<Record<string, unknown>>) ?? []).map(
      (l) => l.name as string
    );
    const url = pr.html_url as string;
    const body_summary = summarizeBody(pr.body);

    // opened event
    events.push({
      type: "pr_opened",
      timestamp: pr.created_at as string,
      id: `pr-${num}`,
      title,
      author,
      url,
      number: num,
      state: "open",
      labels,
      body_summary,
    });

    // merged or closed
    if (pr.merged_at) {
      events.push({
        type: "pr_merged",
        timestamp: pr.merged_at as string,
        id: `pr-${num}-merged`,
        title: `[merged] ${title}`,
        author,
        url,
        number: num,
        state: "merged",
        labels,
      });
    } else if (pr.state === "closed" && pr.closed_at) {
      events.push({
        type: "pr_closed",
        timestamp: pr.closed_at as string,
        id: `pr-${num}-closed`,
        title: `[closed] ${title}`,
        author,
        url,
        number: num,
        state: "closed",
        labels,
      });
    }
  }
  return events;
}

// ── Merge + sort ──────────────────────────────────────────────────────────────

function mergeChronologically(
  commits: RawCommit[],
  issues: RawIssue[],
  prs: RawIssue[]
): TimelineEvent[] {
  const commitEvents: TimelineEvent[] = commits.map((c) => ({
    type: "commit" as const,
    timestamp: c.timestamp,
    id: c.hash,
    title: c.subject,
    author: c.author,
    url: "",
    hash: c.hash,
    short_hash: c.short_hash,
    refs: c.refs || undefined,
  }));

  const issueEvents = toIssueEvents(issues);
  const prEvents = toPREvents(prs);

  const all = [...commitEvents, ...issueEvents, ...prEvents];
  all.sort((a, b) => {
    const ta = new Date(a.timestamp).getTime();
    const tb = new Date(b.timestamp).getTime();
    return ta - tb;
  });

  return all;
}

// ── Markdown digest ───────────────────────────────────────────────────────────

function renderMarkdown(output: ChronicleOutput): string {
  const lines: string[] = [
    `# Git Chronicle — ${output.repo}`,
    ``,
    `> Generated: ${output.generated_at}`,
    `> Events: ${output.total_events} (${output.commit_count} commits · ${output.issue_count} issue events · ${output.pr_count} PR events)`,
    `> Span: ${output.first_event ?? "—"} → ${output.last_event ?? "—"}`,
    ``,
    `---`,
    ``,
  ];

  for (const e of output.events) {
    const ts = e.timestamp.replace("T", " ").replace(/\.\d+Z$/, "Z").slice(0, 19) + "Z";
    const labelStr = e.labels?.length ? ` [${e.labels.join(", ")}]` : "";
    const refsStr = e.refs ? ` *(${e.refs})*` : "";

    switch (e.type) {
      case "commit":
        lines.push(`- \`${ts}\` 🔨 **${e.short_hash}** ${e.title}${refsStr} — *${e.author}*`);
        break;
      case "issue_opened":
        lines.push(`- \`${ts}\` 🐛 **#${e.number}** opened: ${e.title}${labelStr} — *${e.author}*`);
        break;
      case "issue_closed":
        lines.push(`- \`${ts}\` ✅ **#${e.number}** closed: ${e.title.replace("[closed] ", "")}`);
        break;
      case "pr_opened":
        lines.push(`- \`${ts}\` 🔀 **#${e.number}** PR opened: ${e.title}${labelStr} — *${e.author}*`);
        break;
      case "pr_merged":
        lines.push(`- \`${ts}\` ⛵ **#${e.number}** PR merged: ${e.title.replace("[merged] ", "")}`);
        break;
      case "pr_closed":
        lines.push(`- \`${ts}\` ❌ **#${e.number}** PR closed: ${e.title.replace("[closed] ", "")}`);
        break;
    }
  }

  return lines.join("\n");
}

// ── Detect repo ───────────────────────────────────────────────────────────────

async function detectRepo(repoRoot: string): Promise<string> {
  try {
    const remote = await $`git -C ${repoRoot} remote get-url origin`.text();
    const url = remote.trim();
    // Parse owner/repo from ssh or https remote
    const sshMatch = url.match(/github\.com[:/]([^/]+\/[^/.]+)(?:\.git)?$/);
    if (sshMatch) return sshMatch[1];
    const httpsMatch = url.match(/github\.com\/([^/]+\/[^/.]+?)(?:\.git)?$/);
    if (httpsMatch) return httpsMatch[1];
  } catch { /* ignore */ }
  return "poisontr33s/chthonic-archive";
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);

  let repo = process.env.CHRONICLE_REPO ?? "";
  let limit = 2000;
  let since: string | undefined;
  let emitMd = true;
  let summaryMode = false;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--repo" && args[i + 1]) repo = args[++i];
    else if (args[i] === "--limit" && args[i + 1]) limit = parseInt(args[++i], 10);
    else if (args[i] === "--since" && args[i + 1]) since = args[++i];
    else if (args[i] === "--no-md") emitMd = false;
    else if (args[i] === "--summary") summaryMode = true;
  }

  const repoRoot = resolve(import.meta.dir, "..");
  const manifestDir = process.env.MANIFEST_DIR
    ? process.env.MANIFEST_DIR
    : resolve(repoRoot, "manifest");

  await mkdir(manifestDir, { recursive: true });

  if (!repo) {
    repo = await detectRepo(repoRoot);
  }

  const [owner, repoName] = repo.split("/");
  if (!owner || !repoName) {
    console.error(`Invalid repo format: ${repo}. Expected owner/name.`);
    process.exit(1);
  }

  console.error(`[chronicle] repo: ${repo}`);
  console.error(`[chronicle] fetching git log (limit=${limit})...`);

  const commits = await getCommits({ limit, since, repoRoot });
  console.error(`[chronicle] ${commits.length} commits fetched`);

  let token: string;
  try {
    token = await ghToken();
  } catch {
    console.error("[chronicle] gh auth not available — GitHub events skipped");
    token = "";
  }

  let issues: RawIssue[] = [];
  let prs: RawIssue[] = [];

  if (token) {
    console.error(`[chronicle] fetching issues...`);
    try {
      issues = await ghFetchAll<RawIssue>(
        `/repos/${owner}/${repoName}/issues?state=all&sort=created&direction=asc`,
        token
      );
      // Filter out pull requests (issues endpoint returns both)
      issues = issues.filter((i) => !(i.pull_request as unknown));
      console.error(`[chronicle] ${issues.length} issues fetched`);
    } catch (e) {
      console.error(`[chronicle] issues fetch failed: ${e}`);
    }

    console.error(`[chronicle] fetching PRs...`);
    try {
      prs = await ghFetchAll<RawIssue>(
        `/repos/${owner}/${repoName}/pulls?state=all&sort=created&direction=asc`,
        token
      );
      console.error(`[chronicle] ${prs.length} PRs fetched`);
    } catch (e) {
      console.error(`[chronicle] PRs fetch failed: ${e}`);
    }
  }

  const events = mergeChronologically(commits, issues, prs);

  const issueEventCount = events.filter((e) => e.type.startsWith("issue")).length;
  const prEventCount = events.filter((e) => e.type.startsWith("pr")).length;

  const output: ChronicleOutput = {
    generated_at: new Date().toISOString(),
    repo,
    total_events: events.length,
    commit_count: commits.length,
    issue_count: issueEventCount,
    pr_count: prEventCount,
    first_event: events[0]?.timestamp ?? null,
    last_event: events[events.length - 1]?.timestamp ?? null,
    events,
  };

  const jsonPath = resolve(manifestDir, "git_chronicle.json");
  await writeFile(jsonPath, JSON.stringify(output, null, 2), "utf-8");
  console.error(`[chronicle] wrote ${jsonPath}`);

  if (emitMd) {
    const md = renderMarkdown(output);
    const mdPath = resolve(manifestDir, "git_chronicle.md");
    await writeFile(mdPath, md, "utf-8");
    console.error(`[chronicle] wrote ${mdPath}`);
  }

  if (summaryMode) {
    // Compact stdout summary — last 30 events
    const tail = output.events.slice(-30);
    console.log(`## Git Chronicle — ${repo} (last ${tail.length} events)`);
    console.log(`Total: ${output.total_events} | Span: ${output.first_event} → ${output.last_event}`);
    console.log();
    for (const e of tail) {
      const ts = e.timestamp.slice(0, 10);
      if (e.type === "commit") {
        console.log(`${ts} 🔨 ${e.short_hash} ${e.title} (${e.author})`);
      } else if (e.type === "issue_opened") {
        console.log(`${ts} 🐛 #${e.number} ${e.title} (${e.author})`);
      } else if (e.type === "issue_closed") {
        console.log(`${ts} ✅ #${e.number} closed`);
      } else if (e.type === "pr_opened") {
        console.log(`${ts} 🔀 PR#${e.number} ${e.title} (${e.author})`);
      } else if (e.type === "pr_merged") {
        console.log(`${ts} ⛵ PR#${e.number} merged`);
      } else if (e.type === "pr_closed") {
        console.log(`${ts} ❌ PR#${e.number} closed`);
      }
    }
  } else {
    // Default: print JSON summary to stdout
    console.log(JSON.stringify({
      repo: output.repo,
      total_events: output.total_events,
      commit_count: output.commit_count,
      issue_count: output.issue_count,
      pr_count: output.pr_count,
      first_event: output.first_event,
      last_event: output.last_event,
      json_path: jsonPath,
    }, null, 2));
  }
}

main().catch((e) => {
  console.error(`[chronicle] fatal: ${e}`);
  process.exit(1);
});
