// @SID: SCRIPT_PENTEA_AUTOLOOP_V1
/**
 * Pentea Autoloop — autonomous SDK-based queue runner.
 *
 * Solution to the VS Code Chat turn-based constraint:
 * VS Code Copilot Chat has no public API to inject user turns programmatically.
 * This script bypasses the UI layer entirely — runs the Copilot SDK directly,
 * using the agentStop hook (decision: "block") to chain tasks without user input.
 *
 * Mechanism:
 *   1. Reads Pentea-Next: git trailer from recent commits
 *   2. Dispatches to Copilot SDK (sdk.query) with Pentea's system context
 *   3. agentStop hook fires when agent naturally stops (no tool calls)
 *   4. Hook reads latest Pentea-Next: — if changed (new commit), injects next task
 *   5. Loops until queue empty (Pentea-Next: absent / "none" / "DONE")
 *
 * Usage:
 *   bun run scripts/pentea_autoloop.ts
 *   bun run scripts/pentea_autoloop.ts --dry-run
 *   bun run scripts/pentea_autoloop.ts --max-loops 5
 *   bun run scripts/pentea_autoloop.ts --task "Execute ZE-04 directly"
 *
 * Co-authored-by: Pentea <223556219+Penteaa@users.noreply.github.com>
 */

import { execSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

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
    const match = log.match(/^Pentea-Next:\s*(.+)$/m);
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

console.log(`\n☥ Pentea autoloop — ${login} — copilot-sdk v0.0.406`);
console.log(`   repo:      ${REPO_ROOT}`);
console.log(`   max-loops: ${MAX_LOOPS}${DRY_RUN ? " [DRY RUN]" : ""}`);

// ─── Initial task ─────────────────────────────────────────────────────────────
const firstTask = EXPLICIT_TASK ?? readNextTask();
if (!firstTask) {
  console.log("\nNo task found — queue empty (no Pentea-Next: trailer or --task flag).");
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

const penteaMd = loadFile(resolve(REPO_ROOT, ".github/agents/Pentea.agent.md"));
const agentCommon = loadFile(resolve(REPO_ROOT, "AGENT_COMMON.md"));
const pwshRules = loadFile(resolve(REPO_ROOT, "PWSH_RULES.md"));

const systemContext = [
  agentCommon,
  pwshRules ? `\n---\n# Shell Rules\n${pwshRules}` : "",
  "\n---\n# Pentea Agent Identity & Instructions",
  penteaMd,
  "\n---",
  "# Queue-Chain Protocol (autoloop context)",
  "You are running in autonomous SDK mode — no VS Code Chat UI, no user turns.",
  "The agentStop hook handles continuation. Focus only on the current task.",
  "After WRITTEN/COMMITTED: your agentStop hook will inject the next task if present.",
  "Do NOT poll for Pentea-Next: yourself — the harness manages queue advancement.",
  "Complete one task, commit with Pentea-Next: trailer pointing at the next, stop.",
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
    return { decision: "allow" };
  }

  if (currentNext === lastSeenTask) {
    console.log(`\n[agentStop #${loopCount}] No progress on "${currentNext}" — stop.`);
    return { decision: "allow" };
  }

  if (loopCount >= MAX_LOOPS) {
    console.log(`\n[agentStop #${loopCount}] max-loops (${MAX_LOOPS}) reached — stop.`);
    return { decision: "allow" };
  }

  lastSeenTask = currentNext;
  console.log(`\n[agentStop #${loopCount}] Next task: "${currentNext}" — continuing.`);
  return { decision: "block", reason: `Execute queued task: ${currentNext}` };
};

// ─── Main loop ────────────────────────────────────────────────────────────────
console.log("─".repeat(72));

let eventCount = 0;

for await (const event of sdk.query({
  prompt: firstTask,
  abortController,
  clientName: "chthonic-pentea-autoloop",
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
console.log(`\n\n☥ Pentea autoloop complete — ${eventCount} events, ${loopCount} stops.`);
