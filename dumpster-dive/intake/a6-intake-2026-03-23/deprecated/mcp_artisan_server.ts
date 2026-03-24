#!/usr/bin/env bun

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: mcp_artisan_server.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ scripts/sentry_init.ts
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * MCP Artisan Server (Bun-centric, stdio)
 *
 * @SID           TOOL_MCP_ARTISAN_SERVER_V1
 * @Shabti        CLI Script (deprecated)
 * @Heka-Ayni     CONCEPT_MCP_POLYGLOT_TOOLS
 * @Ankh-Tinku    STATE_MCP_ARTISAN_DEPRECATED
 * @Purpose       Provide deterministic, repo-local "artisan tools" invocable
 *                via MCP over stdio transport. Avoids profiles/activation
 *                scripts/network. Prefers absolute paths for toolchains.
 */

import { join, resolve } from "path";
import { existsSync } from "fs";
import { initSentry } from "./sentry_init";

type Json = null | boolean | number | string | Json[] | { [k: string]: Json };

type RpcRequest = {
  jsonrpc: "2.0";
  id?: Json;
  method: string;
  params?: any;
};

type ToolSpec = {
  name: string;
  description: string;
  inputSchema: Json;
};

type ToolCallResult = {
  content: Array<{ type: "text"; text: string }>;
  isError?: boolean;
};

const SERVER_INFO = { name: "chthonic-artisan", version: "0.1.0" };
const PROTOCOL_VERSION = "2024-11-05";

initSentry();

function send(obj: any) {
  process.stdout.write(JSON.stringify(obj) + "\n");
}

function ok(id: any, result: any) {
  send({ jsonrpc: "2.0", id, result });
}

function err(id: any, code: number, message: string, data?: any) {
  send({ jsonrpc: "2.0", id, error: { code, message, data } });
}

function textResult(text: string, isError?: boolean): ToolCallResult {
  return { content: [{ type: "text", text }], isError };
}

function envPath(...parts: string[]) {
  const p = join(...parts);
  return p;
}

function firstExistingPath(paths: string[]): string | null {
  for (const p of paths) {
    if (existsSync(p)) return p;
  }
  return null;
}

function resolveRepoRoot(): string {
  // The script lives in <repo>/scripts. Resolve upwards.
  return resolve(import.meta.dir, "..");
}

function resolvePwsh(): string {
  return (
    firstExistingPath([
      "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
      "C:\\Program Files\\PowerShell\\7-preview\\pwsh.exe",
    ]) ??
    firstExistingPath(["C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"]) ??
    "pwsh.exe"
  );
}

function resolveToolExe(kind: "bun" | "uv" | "cargo" | "rustc" | "go" | "ruby" | "gcc" | "g++" | "git"): string {
  const home = process.env.USERPROFILE ?? "";

  const candidates: Record<string, string[]> = {
    bun: [process.execPath, envPath(home, ".bun", "bin", "bun.exe")],
    uv: [envPath(home, ".local", "bin", "uv.exe")],
    cargo: [envPath(home, ".cargo", "bin", "cargo.exe")],
    rustc: [envPath(home, ".cargo", "bin", "rustc.exe")],
    go: ["C:\\Go\\bin\\go.exe", "C:\\Program Files\\Go\\bin\\go.exe"],
    ruby: ["C:\\Ruby34-x64\\bin\\ruby.exe"],
    gcc: ["C:\\Ruby34-x64\\msys64\\ucrt64\\bin\\gcc.exe"],
    "g++": ["C:\\Ruby34-x64\\msys64\\ucrt64\\bin\\g++.exe"],
    git: ["C:\\Program Files\\Git\\cmd\\git.exe"],
  };

  const picked = firstExistingPath(candidates[kind] ?? []);
  if (picked) return picked;

  // Last resort: PATH lookup.
  const which = Bun.which(kind);
  return which ?? kind;
}

function resolveBashExe(): string {
  const picked = firstExistingPath([
    "C:\\Ruby34-x64\\msys64\\usr\\bin\\bash.exe",
    "C:\\msys64\\usr\\bin\\bash.exe",
    "C:\\Windows\\System32\\bash.exe",
  ]);
  if (picked) return picked;
  return Bun.which("bash") ?? "bash";
}

async function runCommand(cmd: string, args: string[], cwd: string) {
  const proc = Bun.spawn([cmd, ...args], {
    cwd,
    stdout: "pipe",
    stderr: "pipe",
    env: process.env,
  });

  const [out, errText] = await Promise.all([
    new Response(proc.stdout).text(),
    new Response(proc.stderr).text(),
  ]);
  const exitCode = await proc.exited;

  return { out, err: errText, exitCode };
}

const TOOLS: ToolSpec[] = [
  {
    name: "toolchain_probe",
    description:
      "Run repo-local toolchain probe and write a deterministic manifest under dumpster-dive/intake/toolchain-probe/.",
    inputSchema: {
      type: "object",
      properties: {
        writeVscodeSnippet: { type: "boolean", default: false },
      },
      additionalProperties: false,
    },
  },
  {
    name: "overnight_report",
    description:
      "Run the Bun overnight daemon once to generate a report under dumpster-dive/intake/overnight-daemon/.",
    inputSchema: {
      type: "object",
      properties: {
        top: { type: "integer", minimum: 1, default: 20 },
        maxTodo: { type: "integer", minimum: 1, default: 80 },
        siphon: { type: "boolean", default: false },
      },
      additionalProperties: false,
    },
  },
  {
    name: "cargo",
    description: "Run cargo with args in the repo root (stdout/stderr captured).",
    inputSchema: {
      type: "object",
      properties: {
        args: { type: "array", items: { type: "string" }, default: ["build"] },
      },
      required: ["args"],
      additionalProperties: false,
    },
  },
  {
    name: "uv",
    description: "Run uv with args in the repo root (stdout/stderr captured).",
    inputSchema: {
      type: "object",
      properties: {
        args: { type: "array", items: { type: "string" }, default: ["python", "list", "--only-installed"] },
      },
      required: ["args"],
      additionalProperties: false,
    },
  },
  {
    name: "gcc",
    description: "Run gcc from RubyInstaller MSYS2 UCRT toolchain with args.",
    inputSchema: {
      type: "object",
      properties: {
        args: { type: "array", items: { type: "string" }, default: ["--version"] },
      },
      required: ["args"],
      additionalProperties: false,
    },
  },
  {
    name: "gpp",
    description: "Run g++ from RubyInstaller MSYS2 UCRT toolchain with args.",
    inputSchema: {
      type: "object",
      properties: {
        args: { type: "array", items: { type: "string" }, default: ["--version"] },
      },
      required: ["args"],
      additionalProperties: false,
    },
  },
  {
    name: "go",
    description: "Run go with args (from a known install path when available).",
    inputSchema: {
      type: "object",
      properties: {
        args: { type: "array", items: { type: "string" }, default: ["version"] },
      },
      required: ["args"],
      additionalProperties: false,
    },
  },
  {
    name: "ruby",
    description: "Run ruby with args.",
    inputSchema: {
      type: "object",
      properties: {
        args: { type: "array", items: { type: "string" }, default: ["--version"] },
      },
      required: ["args"],
      additionalProperties: false,
    },
  },
  {
    name: "git",
    description: "Run git with args.",
    inputSchema: {
      type: "object",
      properties: {
        args: { type: "array", items: { type: "string" }, default: ["--version"] },
      },
      required: ["args"],
      additionalProperties: false,
    },
  },
  {
    name: "bash",
    description: "Run bash with args (prefers RubyInstaller MSYS2 bash).",
    inputSchema: {
      type: "object",
      properties: {
        args: { type: "array", items: { type: "string" }, default: ["--version"] },
      },
      required: ["args"],
      additionalProperties: false,
    },
  },
  {
    name: "polyglot_versions",
    description: "Return a compact version snapshot for bun/uv/python/cargo/rustc/go/ruby/git/gcc/g++/bash.",
    inputSchema: {
      type: "object",
      properties: {
        includePaths: { type: "boolean", default: true },
      },
      additionalProperties: false,
    },
  },
];

async function toolchainProbe(writeVscodeSnippet: boolean): Promise<ToolCallResult> {
  const repoRoot = resolveRepoRoot();
  const pwsh = resolvePwsh();
  const script = join(repoRoot, "scripts", "probe_toolchain_path.ps1");

  const args = [
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    script,
  ];
  if (writeVscodeSnippet) args.push("-WriteVscodeSnippet");

  const res = await runCommand(pwsh, args, repoRoot);
  const text = [
    `exit: ${res.exitCode}`,
    res.out.trimEnd(),
    res.err ? `\n[stderr]\n${res.err.trimEnd()}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  return textResult(text, res.exitCode !== 0);
}

async function overnightReport(top: number, maxTodo: number, siphon: boolean): Promise<ToolCallResult> {
  const repoRoot = resolveRepoRoot();
  const bun = resolveToolExe("bun");
  const script = join(repoRoot, "scripts", "overnight_daemon.ts");

  const args = [script, "--top", String(top), "--maxTodo", String(maxTodo)];
  if (siphon) args.push("--siphon");

  const res = await runCommand(bun, args, repoRoot);
  const text = [
    `exit: ${res.exitCode}`,
    res.out.trimEnd(),
    res.err ? `\n[stderr]\n${res.err.trimEnd()}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  return textResult(text, res.exitCode !== 0);
}

async function cargoRun(args: string[]): Promise<ToolCallResult> {
  const repoRoot = resolveRepoRoot();
  const cargo = resolveToolExe("cargo");
  const res = await runCommand(cargo, args, repoRoot);

  const text = [
    `cmd: ${cargo} ${args.join(" ")}`,
    `exit: ${res.exitCode}`,
    res.out.trimEnd(),
    res.err ? `\n[stderr]\n${res.err.trimEnd()}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  return textResult(text, res.exitCode !== 0);
}

async function uvRun(args: string[]): Promise<ToolCallResult> {
  const repoRoot = resolveRepoRoot();
  const uv = resolveToolExe("uv");
  const res = await runCommand(uv, args, repoRoot);

  const text = [
    `cmd: ${uv} ${args.join(" ")}`,
    `exit: ${res.exitCode}`,
    res.out.trimEnd(),
    res.err ? `\n[stderr]\n${res.err.trimEnd()}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  return textResult(text, res.exitCode !== 0);
}

async function gccRun(args: string[]): Promise<ToolCallResult> {
  const repoRoot = resolveRepoRoot();
  const gcc = resolveToolExe("gcc");
  const res = await runCommand(gcc, args, repoRoot);

  const text = [
    `cmd: ${gcc} ${args.join(" ")}`,
    `exit: ${res.exitCode}`,
    res.out.trimEnd(),
    res.err ? `\n[stderr]\n${res.err.trimEnd()}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  return textResult(text, res.exitCode !== 0);
}

async function gppRun(args: string[]): Promise<ToolCallResult> {
  const repoRoot = resolveRepoRoot();
  const gpp = resolveToolExe("g++");
  const res = await runCommand(gpp, args, repoRoot);

  const text = [
    `cmd: ${gpp} ${args.join(" ")}`,
    `exit: ${res.exitCode}`,
    res.out.trimEnd(),
    res.err ? `\n[stderr]\n${res.err.trimEnd()}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  return textResult(text, res.exitCode !== 0);
}

async function goRun(args: string[]): Promise<ToolCallResult> {
  const repoRoot = resolveRepoRoot();
  const go = resolveToolExe("go");
  const res = await runCommand(go, args, repoRoot);

  const text = [
    `cmd: ${go} ${args.join(" ")}`,
    `exit: ${res.exitCode}`,
    res.out.trimEnd(),
    res.err ? `\n[stderr]\n${res.err.trimEnd()}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  return textResult(text, res.exitCode !== 0);
}

async function rubyRun(args: string[]): Promise<ToolCallResult> {
  const repoRoot = resolveRepoRoot();
  const ruby = resolveToolExe("ruby");
  const res = await runCommand(ruby, args, repoRoot);

  const text = [
    `cmd: ${ruby} ${args.join(" ")}`,
    `exit: ${res.exitCode}`,
    res.out.trimEnd(),
    res.err ? `\n[stderr]\n${res.err.trimEnd()}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  return textResult(text, res.exitCode !== 0);
}

async function gitRun(args: string[]): Promise<ToolCallResult> {
  const repoRoot = resolveRepoRoot();
  const git = resolveToolExe("git");
  const res = await runCommand(git, args, repoRoot);

  const text = [
    `cmd: ${git} ${args.join(" ")}`,
    `exit: ${res.exitCode}`,
    res.out.trimEnd(),
    res.err ? `\n[stderr]\n${res.err.trimEnd()}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  return textResult(text, res.exitCode !== 0);
}

async function bashRun(args: string[]): Promise<ToolCallResult> {
  const repoRoot = resolveRepoRoot();
  const bash = resolveBashExe();
  const res = await runCommand(bash, args, repoRoot);

  const text = [
    `cmd: ${bash} ${args.join(" ")}`,
    `exit: ${res.exitCode}`,
    res.out.trimEnd(),
    res.err ? `\n[stderr]\n${res.err.trimEnd()}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  return textResult(text, res.exitCode !== 0);
}

async function polyglotVersions(includePaths: boolean): Promise<ToolCallResult> {
  const repoRoot = resolveRepoRoot();

  const checks: Array<{ name: string; cmd: string; args: string[] }> = [
    { name: "bun", cmd: resolveToolExe("bun"), args: ["--version"] },
    { name: "uv", cmd: resolveToolExe("uv"), args: ["--version"] },
    { name: "python", cmd: Bun.which("python") ?? "python", args: ["--version"] },
    { name: "python3.13", cmd: Bun.which("python3.13") ?? "python3.13", args: ["--version"] },
    { name: "python314", cmd: Bun.which("python314") ?? "python314", args: ["--version"] },
    { name: "cargo", cmd: resolveToolExe("cargo"), args: ["--version"] },
    { name: "rustc", cmd: resolveToolExe("rustc"), args: ["--version"] },
    { name: "go", cmd: resolveToolExe("go"), args: ["version"] },
    { name: "ruby", cmd: resolveToolExe("ruby"), args: ["--version"] },
    { name: "git", cmd: resolveToolExe("git"), args: ["--version"] },
    { name: "gcc", cmd: resolveToolExe("gcc"), args: ["--version"] },
    { name: "g++", cmd: resolveToolExe("g++"), args: ["--version"] },
    { name: "bash", cmd: resolveBashExe(), args: ["--version"] },
  ];

  const lines: string[] = [];
  for (const c of checks) {
    const res = await runCommand(c.cmd, c.args, repoRoot);
    const firstLine = (res.out || res.err).split(/\r?\n/).find((l) => l.trim().length > 0) ?? "";
    const where = includePaths ? ` (${c.cmd})` : "";
    lines.push(`${c.name}${where}: ${firstLine.trim()}`);
  }

  return textResult(lines.join("\n"));
}

async function handleToolCall(name: string, args: any): Promise<ToolCallResult> {
  switch (name) {
    case "toolchain_probe":
      return toolchainProbe(Boolean(args?.writeVscodeSnippet));
    case "overnight_report":
      return overnightReport(Number(args?.top ?? 20), Number(args?.maxTodo ?? 80), Boolean(args?.siphon));
    case "cargo":
      return cargoRun(Array.isArray(args?.args) ? args.args : ["build"]);
    case "uv":
      return uvRun(Array.isArray(args?.args) ? args.args : ["python", "list", "--only-installed"]);
    case "gcc":
      return gccRun(Array.isArray(args?.args) ? args.args : ["--version"]);
    case "gpp":
      return gppRun(Array.isArray(args?.args) ? args.args : ["--version"]);
    case "go":
      return goRun(Array.isArray(args?.args) ? args.args : ["version"]);
    case "ruby":
      return rubyRun(Array.isArray(args?.args) ? args.args : ["--version"]);
    case "git":
      return gitRun(Array.isArray(args?.args) ? args.args : ["--version"]);
    case "bash":
      return bashRun(Array.isArray(args?.args) ? args.args : ["--version"]);
    case "polyglot_versions":
      return polyglotVersions(Boolean(args?.includePaths ?? true));
    default:
      return textResult(`Unknown tool: ${name}`, true);
  }
}

async function handleMessage(msg: RpcRequest) {
  const { id, method } = msg;

  try {
    if (method === "initialize") {
      ok(id, {
        protocolVersion: PROTOCOL_VERSION,
        capabilities: { tools: {} },
        serverInfo: SERVER_INFO,
      });
      return;
    }

    if (method === "tools/list") {
      ok(id, { tools: TOOLS });
      return;
    }

    if (method === "tools/call") {
      const name = msg.params?.name;
      const args = msg.params?.arguments ?? {};
      if (typeof name !== "string") {
        err(id, -32602, "Invalid params: expected params.name");
        return;
      }
      const result = await handleToolCall(name, args);
      ok(id, result);
      return;
    }

    // Notifications we can ignore.
    if (method.startsWith("notifications/")) {
      return;
    }

    // Basic ping support (some clients call it).
    if (method === "ping") {
      ok(id, {});
      return;
    }

    err(id, -32601, `Method not found: ${method}`);
  } catch (e) {
    err(id, -32000, "Server error", e instanceof Error ? e.message : String(e));
  }
}

// Stdio JSONL loop (newline-delimited JSON-RPC)
let buf = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => {
  buf += chunk;
  for (;;) {
    const idx = buf.indexOf("\n");
    if (idx < 0) break;
    const line = buf.slice(0, idx).trim();
    buf = buf.slice(idx + 1);
    if (!line) continue;
    let msg: RpcRequest;
    try {
      msg = JSON.parse(line);
    } catch {
      // Ignore malformed lines.
      continue;
    }
    void handleMessage(msg);
  }
});
