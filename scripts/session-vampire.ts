#!/usr/bin/env bun
// @SID: session-vampire — drain structured artifacts from mirrored Copilot Chat sessions
// Reads manifest/sessions/*/transcript.jsonl + memories/*.md (mirrored by session-watcher)
// Extracts: file edits, terminal commands, code blocks, session intent, commit refs, memory files
// Writes: manifest/sessions/*/drain.json + manifest/session_blood.json (cross-session index)
//
// Artifact taxonomy (native Copilot storage per session):
//   transcript.jsonl   — full event log (user/assistant turns, tool calls)
//   debug.jsonl        — telemetry spans (session_start, copilot/vscode versions)
//   models.json        — model catalog available at session time
//   memories/*.md      — in-session agent memory writes (highest signal: working state)
//   [NOT mirrored] chat-session-resources/<call-id>/content.txt|json  — raw tool payloads (too large)
//   [NOT mirrored] codebase-external.sqlite  — global workspace embedding index
//
// Usage:
//   bun run scripts/session-vampire.ts                       # drain all sessions
//   bun run scripts/session-vampire.ts --session <id>        # drain one session
//   bun run scripts/session-vampire.ts --blood               # cross-session report
//   bun run scripts/session-vampire.ts --extract edits       # hottest files across all sessions
//   bun run scripts/session-vampire.ts --extract commands    # all terminal commands
//   bun run scripts/session-vampire.ts --extract code        # all code blocks
//   bun run scripts/session-vampire.ts --extract memories    # all memory files by session

import { readFileSync, existsSync, writeFileSync, readdirSync, statSync } from "fs";
import { join } from "path";

const args = process.argv.slice(2);
const bloodMode = args.includes("--blood");
const sessionArgIdx = args.indexOf("--session");
const targetSession = sessionArgIdx >= 0 ? args[sessionArgIdx + 1] : null;
const extractArgIdx = args.indexOf("--extract");
const extractMode = extractArgIdx >= 0 ? args[extractArgIdx + 1] : null;
const verbose = args.includes("--verbose");

const manifestDir = join(import.meta.dir, "..", "manifest");
const sessionsDir = join(manifestDir, "sessions");
const bloodPath = join(manifestDir, "session_blood.json");

// ─────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────

interface JEntry {
  type: string;
  data: Record<string, unknown>;
}

interface FileEdit {
  tool: string;
  filePath: string;
  turn: number;
}

interface TerminalCommand {
  command: string;
  explanation?: string;
  goal?: string;
  turn: number;
}

interface CodeBlock {
  lang: string;
  lines: number;
  preview: string;
  turn: number;
}

interface SessionDrain {
  sessionId: string;
  drainedAt: string;
  sourcePath: string;
  sessionIntent: string;
  turns: number;
  userMessages: number;
  assistantMessages: number;
  fileEdits: FileEdit[];
  terminalCommands: TerminalCommand[];
  codeBlocks: CodeBlock[];
  toolCallSummary: Record<string, number>;
  commitRefs: string[];
  memoryFiles: string[]; // filenames under memories/ (from memory-tool, mirrored by session-watcher)
}

interface BloodEntry {
  sessionId: string;
  drainedAt: string;
  sessionIntent: string;
  turns: number;
  fileEditCount: number;
  commandCount: number;
  codeBlockCount: number;
  memoryFileCount: number;
  topFiles: string[];
  topTools: string[];
}

// ─────────────────────────────────────────────────────────────
// Parsing helpers
// ─────────────────────────────────────────────────────────────

function asObj(v: unknown): Record<string, unknown> {
  if (!v) return {};
  if (typeof v === "string") { try { return JSON.parse(v) as Record<string, unknown>; } catch { return {}; } }
  if (typeof v === "object" && !Array.isArray(v)) return v as Record<string, unknown>;
  return {};
}

function extractCodeBlocks(content: string, turn: number): CodeBlock[] {
  const blocks: CodeBlock[] = [];
  const re = /```([^\n`]*)\n([\s\S]*?)```/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(content)) !== null) {
    const lang = m[1]?.trim() ?? "";
    const body = m[2] ?? "";
    if (body.trim().length < 3) continue; // skip empty fences
    blocks.push({ lang, lines: body.split("\n").length, preview: body.slice(0, 80).replace(/\n/g, "↵"), turn });
  }
  return blocks;
}

function extractCommits(content: string): string[] {
  // short git SHAs (7-12 hex chars) surrounded by word boundaries — common in commit messages
  const re = /\b([0-9a-f]{7,12})\b/g;
  const found: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(content)) !== null) found.push(m[1]);
  return [...new Set(found)];
}

function basename(p: string): string {
  return p.replace(/\\/g, "/").split("/").pop() ?? p;
}

// ─────────────────────────────────────────────────────────────
// Drain one session
// ─────────────────────────────────────────────────────────────

function drainSession(sessionId: string): SessionDrain | null {
  const tPath = join(sessionsDir, sessionId, "transcript.jsonl");
  if (!existsSync(tPath)) return null;

  let raw: string | null = null;
  try { raw = readFileSync(tPath, "utf8"); } catch { return null; }
  if (!raw) return null;

  const fileEdits: FileEdit[] = [];
  const terminalCommands: TerminalCommand[] = [];
  const codeBlocks: CodeBlock[] = [];
  const toolCallSummary: Record<string, number> = {};
  const commitRefs: string[] = [];
  let sessionIntent = "";
  let userMessages = 0;
  let assistantMessages = 0;
  let turnIdx = 0;

  for (const line of raw.split("\n")) {
    if (!line.trim()) continue;
    let entry: JEntry;
    try { entry = JSON.parse(line) as JEntry; } catch { continue; }
    const { type, data } = entry;

    if (type === "user.message") {
      userMessages++;
      turnIdx++;
      const content = String(data?.content ?? data?.text ?? "");
      if (!sessionIntent && content.trim()) {
        sessionIntent = content.slice(0, 150).replace(/\s+/g, " ").trim();
      }
    } else if (type === "assistant.message") {
      assistantMessages++;
      turnIdx++;
      const content = String(data?.content ?? data?.text ?? "");
      if (content) {
        codeBlocks.push(...extractCodeBlocks(content, turnIdx));
        commitRefs.push(...extractCommits(content));
      }
    } else if (type === "tool.execution_start") {
      const toolName = String(data?.toolName ?? data?.name ?? "");
      if (!toolName) continue;
      toolCallSummary[toolName] = (toolCallSummary[toolName] ?? 0) + 1;
      const args = asObj(data?.arguments);

      if (toolName === "replace_string_in_file" || toolName === "create_file") {
        const fp = String(args.filePath ?? args.path ?? "");
        if (fp) fileEdits.push({ tool: toolName, filePath: fp, turn: turnIdx });
      } else if (toolName === "multi_replace_string_in_file") {
        const reps = args.replacements as Array<{ filePath?: string }> | undefined;
        const seen = new Set<string>();
        if (Array.isArray(reps)) {
          for (const r of reps) {
            const fp = String(r.filePath ?? "");
            if (fp && !seen.has(fp)) { seen.add(fp); fileEdits.push({ tool: toolName, filePath: fp, turn: turnIdx }); }
          }
        }
      } else if (toolName === "run_in_terminal" || toolName === "execute_command") {
        const cmd = String(args.command ?? args.cmd ?? "");
        if (cmd) terminalCommands.push({
          command: cmd.slice(0, 250),
          explanation: args.explanation ? String(args.explanation) : undefined,
          goal: args.goal ? String(args.goal) : undefined,
          turn: turnIdx,
        });
      }
    }
  }

  // Collect mirrored memory files
  const memoriesDir = join(sessionsDir, sessionId, "memories");
  const memoryFiles: string[] = existsSync(memoriesDir)
    ? readdirSync(memoriesDir).filter(f => f.endsWith(".md") || f.endsWith(".json")).sort()
    : [];

  return {
    sessionId,
    drainedAt: new Date().toISOString(),
    sourcePath: tPath,
    sessionIntent,
    turns: userMessages + assistantMessages,
    userMessages,
    assistantMessages,
    fileEdits,
    terminalCommands,
    codeBlocks,
    toolCallSummary,
    commitRefs: [...new Set(commitRefs)],
    memoryFiles,
  };
}

// ─────────────────────────────────────────────────────────────
// All sessions
// ─────────────────────────────────────────────────────────────

function allSessionIds(): string[] {
  if (!existsSync(sessionsDir)) return [];
  return readdirSync(sessionsDir).filter(d => existsSync(join(sessionsDir, d, "transcript.jsonl")));
}

function drainAll(ids: string[]): SessionDrain[] {
  const results: SessionDrain[] = [];
  for (const id of ids) {
    const drain = drainSession(id);
    if (!drain) continue;
    const outPath = join(sessionsDir, id, "drain.json");
    writeFileSync(outPath, JSON.stringify(drain, null, 2), "utf8");
    if (verbose) {
      console.log(`  🩸 ${id.slice(0, 8)}  turns=${drain.turns}  edits=${drain.fileEdits.length}  cmds=${drain.terminalCommands.length}  blocks=${drain.codeBlocks.length}`);
    }
    results.push(drain);
  }
  return results;
}

function buildBlood(drains: SessionDrain[]) {
  const blood: BloodEntry[] = drains.map(d => {
    const fileCounts: Record<string, number> = {};
    for (const e of d.fileEdits) fileCounts[e.filePath] = (fileCounts[e.filePath] ?? 0) + 1;
    const topFiles = Object.entries(fileCounts).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([p]) => p);
    const topTools = Object.entries(d.toolCallSummary).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([t]) => t);
    return {
      sessionId: d.sessionId,
      drainedAt: d.drainedAt,
      sessionIntent: d.sessionIntent,
      turns: d.turns,
      fileEditCount: d.fileEdits.length,
      commandCount: d.terminalCommands.length,
      codeBlockCount: d.codeBlocks.length,
      memoryFileCount: d.memoryFiles.length,
      topFiles,
      topTools,
    };
  });
  writeFileSync(bloodPath, JSON.stringify(blood, null, 2), "utf8");
}

// ─────────────────────────────────────────────────────────────
// --blood report
// ─────────────────────────────────────────────────────────────

function showBlood() {
  if (!existsSync(bloodPath)) {
    console.error("No blood yet. Run session-vampire without --blood first.");
    process.exit(1);
  }
  const blood = JSON.parse(readFileSync(bloodPath, "utf8")) as BloodEntry[];
  const total = blood.reduce((acc, b) => ({ edits: acc.edits + b.fileEditCount, cmds: acc.cmds + b.commandCount }), { edits: 0, cmds: 0 });
  const totalMem = blood.reduce((acc, b) => acc + (b.memoryFileCount ?? 0), 0);
  console.log(`\n🩸 SESSION BLOOD — ${blood.length} sessions · ${total.edits} total edits · ${total.cmds} terminal commands · ${totalMem} memory files\n`);
  for (const b of [...blood].sort((a, z) => z.turns - a.turns)) {
    const sid = b.sessionId.slice(0, 8);
    const files = b.topFiles.slice(0, 3).map(basename).join(", ");
    console.log(`  ${sid}  turns=${String(b.turns).padStart(4)}  edits=${String(b.fileEditCount).padStart(3)}  cmds=${String(b.commandCount).padStart(3)}`);
    if (b.sessionIntent) console.log(`           ${b.sessionIntent.slice(0, 100)}`);
    if (files) console.log(`           → ${files}`);
    if ((b.memoryFileCount ?? 0) > 0) console.log(`           💾 ${b.memoryFileCount} memory file(s)`);
  }
  console.log();
}

// ─────────────────────────────────────────────────────────────
// --extract mode
// ─────────────────────────────────────────────────────────────

function showExtract(mode: string) {
  const ids = targetSession ? [targetSession] : allSessionIds();

  if (mode === "edits") {
    const fileCounts: Record<string, number> = {};
    let total = 0;
    for (const id of ids) {
      const drain = drainSession(id);
      if (!drain) continue;
      for (const e of drain.fileEdits) { fileCounts[e.filePath] = (fileCounts[e.filePath] ?? 0) + 1; total++; }
    }
    const sorted = Object.entries(fileCounts).sort((a, b) => b[1] - a[1]);
    console.log(`\n✏️  FILE EDITS — ${total} total across ${ids.length} sessions\n`);
    for (const [fp, n] of sorted) {
      console.log(`  ${String(n).padStart(3)}×  ${fp}`);
    }
    console.log();
  } else if (mode === "commands") {
    console.log(`\n$ TERMINAL COMMANDS\n`);
    for (const id of ids) {
      const drain = drainSession(id);
      if (!drain?.terminalCommands.length) continue;
      console.log(`  ── ${id.slice(0, 8)} ──`);
      for (const c of drain.terminalCommands) {
        const goal = c.goal ? ` [${c.goal}]` : "";
        console.log(`    ${c.command.slice(0, 120)}${goal}`);
      }
    }
    console.log();
  } else if (mode === "code") {
    let total = 0;
    for (const id of ids) {
      const drain = drainSession(id);
      if (!drain?.codeBlocks.length) continue;
      for (const b of drain.codeBlocks) {
        total++;
        const label = (b.lang ? `[${b.lang}]` : "[?]").padEnd(14);
        console.log(`${label} ${String(b.lines).padStart(3)}L  ${b.preview.slice(0, 60)}`);
      }
    }
    console.log(`\n${total} code blocks total`);
  } else if (mode === "memories") {
    console.log(`\n💾 MEMORY FILES\n`);
    let total = 0;
    for (const id of ids) {
      const memoriesDir = join(sessionsDir, id, "memories");
      if (!existsSync(memoriesDir)) continue;
      const files = readdirSync(memoriesDir).filter(f => f.endsWith(".md") || f.endsWith(".json")).sort();
      if (!files.length) continue;
      console.log(`  ── ${id.slice(0, 8)} ──`);
      for (const f of files) {
        const size = (() => { try { return statSync(join(memoriesDir, f)).size; } catch { return 0; } })();
        console.log(`    ${f.padEnd(40)} ${String(size).padStart(7)}B`);
        total++;
      }
    }
    console.log(`\n${total} memory file(s) total`);
  } else {
    console.error(`Unknown extract mode: ${mode}. Use: edits | commands | code | memories`);
    process.exit(1);
  }
}

// ─────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────

if (bloodMode) {
  showBlood();
} else if (extractMode) {
  showExtract(extractMode);
} else {
  const ids = targetSession ? [targetSession] : allSessionIds();
  if (!verbose) process.stdout.write(`session-vampire: draining ${ids.length} session(s)...`);
  const drains = drainAll(ids);
  // roll up blood from all existing drain.json files (not just this run)
  const allDrains = allSessionIds().map(id => {
    const p = join(sessionsDir, id, "drain.json");
    if (!existsSync(p)) return null;
    try { return JSON.parse(readFileSync(p, "utf8")) as SessionDrain; } catch { return null; }
  }).filter((d): d is SessionDrain => d !== null);
  buildBlood(allDrains);
  if (!verbose) console.log(` done. ${drains.length} drained → manifest/session_blood.json`);
}
