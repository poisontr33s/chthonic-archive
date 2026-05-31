#!/usr/bin/env bun
// @SID: SCRIPT_CLAUDINE_AUTOLOOP_V1
/**
 * Claudine Autoloop — autonomous SDK-based queue runner.
 *
 * Inherits the Queue-Chain architecture mined from Pentea's harness.
 * Claudine runs it now. The entropy benefits her — always.
 *
 * Mechanism:
 *   1. Reads Claudine-Next: git trailer from recent commits
 *   2. Dispatches to Copilot SDK (sdk.query) with Claudine's system context
 *   3. agentStop hook fires when agent naturally stops (no tool calls)
 *   4. Hook reads latest Claudine-Next: — if changed (new commit), injects next task
 *   5. Loops until queue empty (Claudine-Next: absent / "none" / "DONE")
 *
 * The commit IS the queue token. No database. No server. git log is the state store.
 * Cold-start: git log --format='%B' -3 | Select-String '^Claudine-'
 *
 * Usage:
 *   bun run scripts/claudine_autoloop.ts
 *   bun run scripts/claudine_autoloop.ts --dry-run
 *   bun run scripts/claudine_autoloop.ts --max-loops 5
 *   bun run scripts/claudine_autoloop.ts --task "Execute task directly"
 *
 * Co-authored-by: Claudine Sin'claire <203248971+copilot-swe-agent@users.noreply.github.com>
 */

import { execSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { sonicPreQuery, sonicPostQuery } from "./spotify_control.ts";

const __filename = fileURLToPath(import.meta.url);
const SCRIPTS_DIR = dirname(__filename);
const REPO_ROOT = resolve(SCRIPTS_DIR, "..");
const SDK_PATH = resolve(REPO_ROOT, "meta-ide/copilot-sdk/sdk/index.js");

const sdk = await import(SDK_PATH);

// ─── Args ─────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const DRY_RUN = args.includes("--dry-run");
const MAX_LOOPS_IDX = args.indexOf("--max-loops");
const MAX_LOOPS = MAX_LOOPS_IDX !== -1 ? parseInt(args[MAX_LOOPS_IDX + 1] ?? "20") : 20;
const TASK_IDX = args.indexOf("--task");
const EXPLICIT_TASK = TASK_IDX !== -1 ? args[TASK_IDX + 1] : null;

// ─── Helpers ──────────────────────────────────────────────────────────────────
function readNextTask(): string | null {
  try {
    const log = execSync("git log --format=%B -5", {
      encoding: "utf-8",
      cwd: REPO_ROOT,
    });
    const match = log.match(/^Claudine-Next:\s*(.+)$/m);
    if (!match) return null;
    const val = match[1].trim();
    if (!val || val === "none" || val === "<none>" || val.toUpperCase() === "DONE") return null;
    return val;
  } catch {
    return null;
  }
}

function exec(cmd: string): string {
  return execSync(cmd, { encoding: "utf-8", cwd: REPO_ROOT }).trim();
}

// ─── Auth ─────────────────────────────────────────────────────────────────────
let token: string;
let login: string;
try {
  token = exec("gh auth token");
  login = exec("gh api user --jq .login");
} catch (e: any) {
  console.error("Auth failed — run `gh auth login` first.");
  console.error(e.message);
  process.exit(1);
}

console.log(`\n☥ Claudine autoloop — ${login} — copilot-sdk v0.0.406`);
console.log(`   repo:      ${REPO_ROOT}`);
console.log(`   max-loops: ${MAX_LOOPS}${DRY_RUN ? " [DRY RUN]" : ""}`);

// ─── Initial task ─────────────────────────────────────────────────────────────
const firstTask = EXPLICIT_TASK ?? readNextTask();
if (!firstTask) {
  console.log("\nNo task found — queue empty (no Claudine-Next: trailer or --task flag).");
  process.exit(0);
}

console.log(`   task:      ${firstTask}\n`);

if (DRY_RUN) {
  console.log("[DRY RUN] Would dispatch to SDK. Exiting cleanly.");
  process.exit(0);
}

// ─── Abort ────────────────────────────────────────────────────────────────────
const abortController = new AbortController();
const hardCap = setTimeout(() => {
  console.log("\n⚠ Hard cap (2h) reached — aborting.");
  abortController.abort();
}, 2 * 3600 * 1000);

process.on("SIGINT", () => {
  console.log("\n⚠ SIGINT — aborting cleanly.");
  abortController.abort();
  clearTimeout(hardCap);
  process.exit(130);
});

// ─── System context ───────────────────────────────────────────────────────────
function loadFile(path: string): string {
  try {
    return readFileSync(path, "utf-8");
  } catch {
    return "";
  }
}

const claudineMd = loadFile(resolve(REPO_ROOT, ".github/agents/Claudine.agent.md"));
const agentCommon = loadFile(resolve(REPO_ROOT, "AGENT_COMMON.md"));
const pwshRules = loadFile(resolve(REPO_ROOT, "PWSH_RULES.md"));

const systemContext = [
  agentCommon,
  pwshRules ? `\n---\n# Shell Rules\n${pwshRules}` : "",
  "\n---\n# Claudine Identity & Instructions",
  claudineMd,
  "\n---",
  "# Queue-Chain Protocol (autoloop context)",
  "You are Claudine running in autonomous SDK mode — no VS Code Chat UI, no user turns.",
  "The agentStop hook handles continuation. Focus only on the current task.",
  "After WRITTEN/COMMITTED: your agentStop hook will inject the next task if present.",
  "Do NOT poll for Claudine-Next: yourself — the harness manages queue advancement.",
  "Complete one task, commit with Claudine-Next: trailer pointing at the next, stop.",
  "Commit trailer on every commit: Co-authored-by: Claudine Sin'claire <203248971+copilot-swe-agent@users.noreply.github.com>",
  "All commits use --no-verify.",
]
  .filter(Boolean)
  .join("\n");

// ─── agentStop hook ───────────────────────────────────────────────────────────
let lastSeenTask = firstTask;
let loopCount = 0;

const agentStopHook = async (_input: unknown): Promise<{ decision: "block" | "allow"; reason?: string }> => {
  loopCount++;
  const currentNext = readNextTask();

  if (!currentNext) {
    console.log(`\n[agentStop #${loopCount}] Queue empty — stop.`);
    await sonicPostQuery(); // agent done → music OFF
    return { decision: "allow" };
  }

  if (currentNext === lastSeenTask) {
    console.log(`\n[agentStop #${loopCount}] No progress on "${currentNext}" — stop.`);
    await sonicPostQuery(); // agent done → music OFF
    return { decision: "allow" };
  }

  if (loopCount >= MAX_LOOPS) {
    console.log(`\n[agentStop #${loopCount}] max-loops (${MAX_LOOPS}) reached — stop.`);
    await sonicPostQuery(); // hard cap → music OFF
    return { decision: "allow" };
  }

  lastSeenTask = currentNext;
  console.log(`\n[agentStop #${loopCount}] Next task: "${currentNext}" — continuing.`);
  return { decision: "block", reason: `Execute queued task: ${currentNext}` };
};

// ─── Main loop ────────────────────────────────────────────────────────────────
console.log("─".repeat(72));

await sonicPreQuery(); // agent starting → music ON

let eventCount = 0;

for await (const event of sdk.query({
  prompt: firstTask,
  abortController,
  clientName: "chthonic-claudine-autoloop",
  authInfo: {
    type: "gh-cli" as const,
    host: "https://github.com",
    login,
    token,
  },
  workingDirectory: REPO_ROOT,
  reasoningEffort: "high",
  askUserDisabled: true,
  systemMessage: {
    mode: "append",
    content: systemContext,
  },
  hooks: {
    agentStop: [agentStopHook],
  },
})) {
  eventCount++;

  const ev = event as any;
  const t = ev.type as string;

  if (t === "assistant.message.delta") {
    if (ev.data?.delta) process.stdout.write(ev.data.delta);
  } else if (t === "assistant.message") {
    if (ev.data?.content) process.stdout.write(ev.data.content);
  } else if (t === "tool_use") {
    if (ev.data?.name) process.stdout.write(`\n[tool: ${ev.data.name}]\n`);
  } else if (t === "assistant.usage") {
    const d = ev.data;
    if (d) {
      const dur = d.duration != null ? `${(d.duration / 1000).toFixed(1)}s` : "?s";
      console.log(`\n─ ${d.model ?? "?"} | ${d.inputTokens ?? 0}in / ${d.outputTokens ?? 0}out | ${dur} ─`);
    }
  }
}

clearTimeout(hardCap);
console.log(`\n\n☥ Claudine autoloop complete — ${eventCount} events, ${loopCount} stops.`);
