#!/usr/bin/env bun
// @SID: SESSION_COMPRESS_V1_CLI

/**
 * session_compress.ts — Chthonic Archive warm-start packet generator
 * Schema V1: compact summary of a VS Code Copilot Chat .jsonl transcript.
 *
 * Usage:
 *   bun run scripts/session_compress.ts [options]
 *
 * Options:
 *   --input  <path>   Transcript .jsonl path (default: VSCODE_TARGET_SESSION_LOG env var)
 *   --output <path>   Write JSON output to file (default: stdout)
 *   --md              Also emit a markdown summary alongside the JSON output
 *   --max-turns <N>   Include at most N turns in the packet (default: 50)
 *   --truncate <N>    Truncate message content to N chars (default: 300)
 *
 * Self-applicable:
 *   VSCODE_TARGET_SESSION_LOG=<transcript.jsonl> bun run scripts/session_compress.ts --output manifest/session_warmstart.json --md
 */

import { createReadStream } from "node:fs";
import { createInterface } from "node:readline";
import { writeFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

// ─── Schema V1 types ───────────────────────────────────────────────────────────

interface SessionMeta {
  id: string;
  started: string;
  ended: string;
  duration_ms: number;
  producer: string;
  copilot_version: string;
  vscode_version: string;
}

interface TurnRecord {
  turn_index: number;
  turn_start: string;
  user_prompt: string | null;
  assistant_summary: string | null;
  tools: string[];
  tool_count: number;
}

interface ArtifactLog {
  files_read: string[];
  files_written: string[];
  terminal_commands: string[];
  commits: string[];
}

interface SessionCompressV1 {
  schema: "session-compress/v1";
  generated_at: string;
  session: SessionMeta;
  stats: {
    total_turns: number;
    user_messages: number;
    tool_calls: number;
    tool_call_failures: number;
    duration_human: string;
  };
  tool_inventory: { name: string; count: number }[];
  turns: TurnRecord[];
  artifacts: ArtifactLog;
}

// ─── Helpers ───────────────────────────────────────────────────────────────────

function trunc(s: string | null | undefined, n: number): string | null {
  if (!s) return null;
  const flat = s.replace(/\s+/g, " ").trim();
  return flat.length > n ? flat.slice(0, n) + "…" : flat;
}

function durationHuman(ms: number): string {
  const h = Math.floor(ms / 3_600_000);
  const m = Math.floor((ms % 3_600_000) / 60_000);
  const s = Math.floor((ms % 60_000) / 1_000);
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function extractFilePath(args: Record<string, unknown>): string | null {
  for (const k of ["filePath", "path", "file_path", "outputPath", "uri"]) {
    if (typeof args[k] === "string") return args[k] as string;
  }
  return null;
}

function extractCommand(args: Record<string, unknown>): string | null {
  if (typeof args["command"] === "string") {
    return (args["command"] as string).slice(0, 120);
  }
  // execution_subagent uses "query"
  if (typeof args["query"] === "string") {
    return (args["query"] as string).slice(0, 120);
  }
  return null;
}

// ─── Core compressor ──────────────────────────────────────────────────────────

async function compress(options: {
  input: string;
  maxTurns: number;
  truncate: number;
}): Promise<SessionCompressV1> {
  const { input, maxTurns, truncate } = options;

  let sessionMeta: SessionMeta = {
    id: "unknown",
    started: "",
    ended: "",
    duration_ms: 0,
    producer: "unknown",
    copilot_version: "unknown",
    vscode_version: "unknown",
  };

  const turns: TurnRecord[] = [];
  const toolCounts = new Map<string, number>();
  const artifacts: ArtifactLog = {
    files_read: [],
    files_written: [],
    terminal_commands: [],
    commits: [],
  };

  let userMessages = 0;
  let toolCalls = 0;
  let toolFailures = 0;
  let lastTimestamp = "";
  let turnIndex = 0;

  let currentTurn: TurnRecord | null = null;
  let pendingUserPrompt: string | null = null;

  const rl = createInterface({
    input: createReadStream(input, { encoding: "utf-8" }),
    crlfDelay: Infinity,
  });

  for await (const line of rl) {
    if (!line.trim()) continue;

    let event: Record<string, unknown>;
    try {
      event = JSON.parse(line);
    } catch {
      continue;
    }

    const type = event.type as string;
    const data = ((event.data ?? {}) as Record<string, unknown>);
    const ts = event.timestamp as string;
    if (ts) lastTimestamp = ts;

    switch (type) {
      case "session.start": {
        sessionMeta = {
          id: (data.sessionId as string) ?? "unknown",
          started: ts ?? "",
          ended: "",
          duration_ms: 0,
          producer: (data.producer as string) ?? "unknown",
          copilot_version: (data.copilotVersion as string) ?? "unknown",
          vscode_version: (data.vscodeVersion as string) ?? "unknown",
        };
        break;
      }

      case "user.message": {
        userMessages++;
        const content = (data.content as string) ?? "";
        pendingUserPrompt = trunc(content, truncate);
        break;
      }

      case "assistant.turn_start": {
        currentTurn = {
          turn_index: turnIndex++,
          turn_start: ts ?? lastTimestamp,
          user_prompt: pendingUserPrompt,
          assistant_summary: null,
          tools: [],
          tool_count: 0,
        };
        pendingUserPrompt = null;
        break;
      }

      case "assistant.message": {
        if (currentTurn) {
          const content = (data.content as string) ?? "";
          const reasoning = (data.reasoningText as string) ?? "";
          const text = content.trim().length > 0 ? content : reasoning;
          currentTurn.assistant_summary = trunc(text, truncate);
        }
        break;
      }

      case "tool.execution_start": {
        toolCalls++;
        const toolName = (data.toolName as string) ?? "unknown";
        const args = ((data.arguments ?? {}) as Record<string, unknown>);

        toolCounts.set(toolName, (toolCounts.get(toolName) ?? 0) + 1);

        if (currentTurn) {
          if (!currentTurn.tools.includes(toolName)) {
            currentTurn.tools.push(toolName);
          }
          currentTurn.tool_count++;
        }

        // Artifact extraction — classify by tool name
        const isRead =
          toolName === "read_file" ||
          toolName === "mcp_filesystem_read_file" ||
          toolName === "mcp_filesystem_read_multiple_files" ||
          toolName === "mcp_filesystem_read_text_file";
        const isWrite =
          toolName === "create_file" ||
          toolName === "replace_string_in_file" ||
          toolName === "multi_replace_string_in_file" ||
          toolName === "mcp_filesystem_write_file" ||
          toolName === "mcp_filesystem_edit_file";
        const isTerminal =
          toolName === "run_in_terminal" ||
          toolName === "send_to_terminal" ||
          toolName === "execution_subagent" ||
          toolName === "mcp_chthonic-v3_bash";

        if (isRead) {
          const fp = extractFilePath(args);
          if (fp && !artifacts.files_read.includes(fp)) artifacts.files_read.push(fp);
        } else if (isWrite) {
          const fp = extractFilePath(args);
          if (fp && !artifacts.files_written.includes(fp)) artifacts.files_written.push(fp);
        } else if (isTerminal) {
          const cmd = extractCommand(args);
          if (cmd) {
            artifacts.terminal_commands.push(cmd);
            // Detect committed hash from git commit commands
            if (/\bgit\b.*\bcommit\b/.test(cmd)) {
              const hashMatch = cmd.match(/\b([0-9a-f]{7,40})\b/);
              if (hashMatch) artifacts.commits.push(hashMatch[1]);
            }
          }
        }
        break;
      }

      case "tool.execution_complete": {
        if (data.success === false) toolFailures++;
        break;
      }

      case "assistant.turn_end": {
        if (currentTurn) {
          if (turns.length < maxTurns) {
            turns.push(currentTurn);
          }
          currentTurn = null;
        }
        break;
      }
    }
  }

  // Finalize session metadata
  sessionMeta.ended = lastTimestamp;
  if (sessionMeta.started && lastTimestamp) {
    sessionMeta.duration_ms =
      new Date(lastTimestamp).getTime() - new Date(sessionMeta.started).getTime();
  }

  // Build tool inventory, sorted descending by count
  const toolInventory = Array.from(toolCounts.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);

  // Deduplicate and cap artifact lists
  const cap = (arr: string[], n = 50) => [...new Set(arr)].slice(0, n);
  artifacts.files_read = cap(artifacts.files_read);
  artifacts.files_written = cap(artifacts.files_written);
  artifacts.terminal_commands = cap(artifacts.terminal_commands, 30);
  artifacts.commits = cap(artifacts.commits, 20);

  return {
    schema: "session-compress/v1",
    generated_at: new Date().toISOString(),
    session: sessionMeta,
    stats: {
      total_turns: turnIndex,
      user_messages: userMessages,
      tool_calls: toolCalls,
      tool_call_failures: toolFailures,
      duration_human: durationHuman(sessionMeta.duration_ms),
    },
    tool_inventory: toolInventory,
    turns,
    artifacts,
  };
}

// ─── Markdown emitter ─────────────────────────────────────────────────────────

function toMarkdown(packet: SessionCompressV1): string {
  const { session, stats, tool_inventory, turns, artifacts } = packet;

  const lines: string[] = [
    `# Session Compress — Schema V1 Warm-Start Packet`,
    ``,
    `> **Session ID:** \`${session.id}\``,
    `> **Producer:** ${session.producer} (${session.copilot_version} / VS Code ${session.vscode_version})`,
    `> **Started:** ${session.started}`,
    `> **Duration:** ${stats.duration_human}`,
    `> **Generated:** ${packet.generated_at}`,
    ``,
    `## Stats`,
    ``,
    `| Field | Value |`,
    `|-------|-------|`,
    `| Turns | ${stats.total_turns} |`,
    `| User messages | ${stats.user_messages} |`,
    `| Tool calls | ${stats.tool_calls} (${stats.tool_call_failures} failed) |`,
    ``,
    `## Tool Inventory (top 15)`,
    ``,
    `| Tool | Count |`,
    `|------|-------|`,
    ...tool_inventory.slice(0, 15).map((t) => `| \`${t.name}\` | ${t.count} |`),
    ``,
    `## Artifacts`,
    ``,
    `**Files written (${artifacts.files_written.length}):**`,
    ...artifacts.files_written.map((f) => `- \`${f}\``),
    ``,
    `**Files read (${artifacts.files_read.length}):**`,
    ...artifacts.files_read.slice(0, 20).map((f) => `- \`${f}\``),
    ``,
    `**Terminal commands (last 10):**`,
    ...artifacts.terminal_commands.slice(-10).map((c) => `- \`${c.replace(/`/g, "'")}\``),
    ``,
    `**Git commits detected:**`,
    ...artifacts.commits.map((c) => `- \`${c}\``),
    ``,
    `## Turn Log (last ${Math.min(turns.length, 10)} of ${turns.length})`,
    ``,
  ];

  for (const t of turns.slice(-10)) {
    lines.push(`### Turn ${t.turn_index}`);
    lines.push(`*${t.turn_start}* — ${t.tool_count} tool calls`);
    if (t.user_prompt) lines.push(``, `**User:** ${t.user_prompt}`);
    if (t.assistant_summary) lines.push(``, `**Assistant:** ${t.assistant_summary}`);
    if (t.tools.length > 0) lines.push(``, `**Tools:** \`${t.tools.join("`, `")}\``);
    lines.push(``);
  }

  return lines.join("\n");
}

// ─── CLI entrypoint ───────────────────────────────────────────────────────────

const argv = process.argv.slice(2);

function flagVal(f: string): string | null {
  const i = argv.indexOf(f);
  return i >= 0 && i + 1 < argv.length ? argv[i + 1] : null;
}

const inputArg = flagVal("--input") ?? process.env["VSCODE_TARGET_SESSION_LOG"] ?? null;
const outputArg = flagVal("--output") ?? null;
const emitMd = argv.includes("--md");
const maxTurns = parseInt(flagVal("--max-turns") ?? "50", 10);
const truncateN = parseInt(flagVal("--truncate") ?? "300", 10);

if (argv.includes("--help") || argv.includes("-h")) {
  console.log(`session_compress.ts — Chthonic Archive warm-start packet generator (Schema V1)

Usage:
  bun run scripts/session_compress.ts [options]

Options:
  --input  <path>   Transcript .jsonl path (default: VSCODE_TARGET_SESSION_LOG env var)
  --output <path>   Write JSON output to file (default: stdout)
  --md              Also emit a markdown summary to <output>.md (requires --output)
  --max-turns <N>   Max turns to include in packet (default: 50)
  --truncate <N>    Truncate message text to N chars (default: 300)
  --help, -h        Show this help

Self-applicable example:
  bun run scripts/session_compress.ts \\
    --input "C:/path/to/transcript.jsonl" \\
    --output manifest/session_warmstart.json \\
    --md
`);
  process.exit(0);
}

if (!inputArg) {
  console.error(
    "Error: No input provided. Use --input <path> or set VSCODE_TARGET_SESSION_LOG."
  );
  process.exit(1);
}

const inputPath = resolve(inputArg);

if (!existsSync(inputPath)) {
  console.error(`Error: Input file not found: ${inputPath}`);
  process.exit(1);
}

console.error(`[session_compress] Parsing: ${inputPath}`);
const packet = await compress({ input: inputPath, maxTurns, truncate: truncateN });
console.error(
  `[session_compress] Done — ${packet.stats.total_turns} turns, ${packet.stats.tool_calls} tool calls, ${packet.stats.duration_human}`
);

const json = JSON.stringify(packet, null, 2);

if (outputArg) {
  writeFileSync(outputArg, json, "utf-8");
  console.error(`[session_compress] JSON: ${outputArg}`);
  if (emitMd) {
    const mdPath = outputArg.replace(/\.json$/, "") + ".md";
    writeFileSync(mdPath, toMarkdown(packet), "utf-8");
    console.error(`[session_compress] Markdown: ${mdPath}`);
  }
} else {
  process.stdout.write(json + "\n");
  if (emitMd) {
    console.error("[session_compress] --md requires --output to be specified.");
  }
}
