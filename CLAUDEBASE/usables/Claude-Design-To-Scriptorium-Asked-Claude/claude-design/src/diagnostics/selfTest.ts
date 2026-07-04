// Claude Design — Self-Test
// A small instrument that probes the unknowns and reports them as a markdown doc.
// Runs the ledger from the architectural plan against actual runtime state.

import * as vscode from "vscode";
import { spawn } from "node:child_process";
import * as os from "node:os";
import * as path from "node:path";
import * as fs from "node:fs/promises";

type Result = { name: string; status: "ok" | "warn" | "miss" | "unknown"; detail: string };

export async function runSelfTest(ctx: vscode.ExtensionContext): Promise<void> {
  const results: Result[] = [];
  const t0 = Date.now();

  // --- ENVIRONMENT ---------------------------------------------------------
  results.push({ name: "platform",    status: "ok", detail: `${os.platform()} ${os.release()} · ${os.arch()}` });
  results.push({ name: "node",        status: "ok", detail: process.version });
  results.push({ name: "vscode",      status: "ok", detail: vscode.version });
  results.push({ name: "workspace",   status: vscode.workspace.workspaceFolders ? "ok" : "warn",
                 detail: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? "no folder open" });

  // --- CLI PRESENCE --------------------------------------------------------
  const cliPath = vscode.workspace.getConfiguration("claudeDesign").get<string>("cliPath", "claude");
  const cliVersion = await probeCommand(cliPath, ["--version"]);
  results.push({
    name: "claude CLI",
    status: cliVersion.ok ? "ok" : "miss",
    detail: cliVersion.ok ? cliVersion.stdout.trim() : "not on PATH — install Claude Code or `claude` CLI"
  });

  const bunVersion = await probeCommand("bun", ["--version"]);
  results.push({
    name: "bun",
    status: bunVersion.ok ? "ok" : "warn",
    detail: bunVersion.ok ? bunVersion.stdout.trim() : "not on PATH — only needed for development, not runtime"
  });

  // --- AUTH LIVENESS -------------------------------------------------------
  if (cliVersion.ok) {
    const ping = await probeCommand(cliPath, ["--print", "--output-format=json", "ping"], 8000);
    results.push({
      name: "auth liveness",
      status: ping.ok ? "ok" : "warn",
      detail: ping.ok ? "completion succeeded — Pro/Max quota reachable" : "completion failed — run `claude /login`"
    });
  } else {
    results.push({ name: "auth liveness", status: "unknown", detail: "skipped — CLI missing" });
  }

  // --- COMPANION EXTENSIONS ------------------------------------------------
  const claudeCode = vscode.extensions.getExtension("anthropic.claude-code");
  results.push({
    name: "Claude Code extension",
    status: claudeCode ? "ok" : "warn",
    detail: claudeCode ? `installed · v${claudeCode.packageJSON.version} · ${claudeCode.isActive ? "active" : "inactive"}` : "not installed — Claude Design works standalone"
  });

  // Probe Claude Code's exported API (forward-looking — Phase 0 contract 6).
  if (claudeCode && claudeCode.isActive) {
    const exp = claudeCode.exports;
    results.push({
      name: "Claude Code API surface",
      status: exp ? "ok" : "unknown",
      detail: exp ? `keys: ${Object.keys(exp).join(", ")}` : "no public exports yet — falling back to CLI subprocess"
    });
  }

  // --- WORKSPACE LAYOUT ----------------------------------------------------
  const ws = vscode.workspace.workspaceFolders?.[0]?.uri;
  if (ws) {
    for (const rel of ["designs", "assets", ".claude-design", "CLAUDE.md"]) {
      const target = vscode.Uri.joinPath(ws, rel);
      try {
        const stat = await vscode.workspace.fs.stat(target);
        results.push({ name: rel, status: "ok", detail: stat.type === vscode.FileType.Directory ? "directory" : `file · ${stat.size}B` });
      } catch {
        results.push({ name: rel, status: "miss", detail: "not present — created on first write" });
      }
    }
  }

  // --- LEDGER UNKNOWNS (probe; never assume) -------------------------------
  // Anthropic Labs design-metering API — does it exist yet?
  // We don't hit the network from a self-test; we just record the question.
  results.push({
    name: "Anthropic Labs design meter API",
    status: "unknown",
    detail: "no public endpoint observed at time of writing — status bar uses local heuristics"
  });

  results.push({
    name: "project-export → editor handoff",
    status: "unknown",
    detail: "no claude-design://import deep-link observed — Phase 2 importer reads dropped export files instead"
  });

  // --- RENDER --------------------------------------------------------------
  const took = Date.now() - t0;
  const md = renderMarkdown(results, took);
  const doc = await vscode.workspace.openTextDocument({ language: "markdown", content: md });
  await vscode.window.showTextDocument(doc, { preview: false });
}

function renderMarkdown(rows: Result[], tookMs: number): string {
  const icon = (s: Result["status"]) =>
    s === "ok" ? "✓" : s === "warn" ? "!" : s === "miss" ? "·" : "?";
  const lines: string[] = [];
  lines.push("# Claude Design — Self-Test");
  lines.push("");
  lines.push(`_${new Date().toISOString()} · completed in ${tookMs}ms_`);
  lines.push("");
  lines.push("| | check | detail |");
  lines.push("|---|---|---|");
  for (const r of rows) lines.push(`| ${icon(r.status)} | **${r.name}** | ${r.detail} |`);
  lines.push("");
  lines.push("## Legend");
  lines.push("- `✓` ok · everything responds as expected");
  lines.push("- `!` warn · works without it, better with it");
  lines.push("- `·` miss · absent · usually created on first write");
  lines.push("- `?` unknown · gated by an upstream surface we can't yet probe");
  lines.push("");
  lines.push("## Notes");
  lines.push("- This test never sends a chargeable completion beyond a single one-word ping.");
  lines.push("- The ledger entries (`?`) are intentional — they will flip to `✓` when Anthropic ships the corresponding surfaces.");
  return lines.join("\n");
}

function probeCommand(cmd: string, args: string[], timeoutMs = 4000):
  Promise<{ ok: boolean; stdout: string; stderr: string }> {
  return new Promise(resolve => {
    let stdout = "", stderr = "", done = false;
    const finish = (ok: boolean) => { if (!done) { done = true; resolve({ ok, stdout, stderr }); } };
    try {
      const child = spawn(cmd, args, { shell: process.platform === "win32" });
      const timer = setTimeout(() => { try { child.kill(); } catch {} finish(false); }, timeoutMs);
      child.stdout?.on("data", d => stdout += d);
      child.stderr?.on("data", d => stderr += d);
      child.on("error", () => { clearTimeout(timer); finish(false); });
      child.on("exit", code => { clearTimeout(timer); finish(code === 0); });
    } catch { finish(false); }
  });
}
