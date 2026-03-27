// @SID: SCRIPT_MCP_CHTHONIC_SERVER_V1
#!/usr/bin/env bun

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: mcp-chthonic-server.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ docs/CLAUDE_CODE_IDE_SETUP.md
// ║   └─◄ scripts/sentry_init.ts
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * Chthonic Polyglot MCP Server v3.3.0
 *
 * @SID           TOOL_MCP_CHTHONIC_SERVER_V3
 * @Shabti        MCP Server (stdio transport)
 * @Heka-Ayni     CONCEPT_MCP_POLYGLOT_UNIFIED
 * @Ankh-Tinku    STATE_MCP_CHTHONIC_ACTIVE
 * @Purpose       Bun-centric unified MCP server: polyglot toolchain (cargo,
 *                uv, gcc, gpp, go, ruby, git, bash, bun, make) + chthonic
 *                archive CLI (resolve, audit, map, analyze, compact, status,
 *                book, ssot, scan, validate_ssot, probe, report) + meta tools
 *                (polyglot_versions, claudine_env, meta_cli v3.3.0).
 *                Protocol: MCP 2024-11-05 (JSON-RPC 2.0
 *                over stdio).
 */

import { join, resolve } from "path";
import { SSOT_POINTER } from "./lib/ssot-paths";
import { existsSync } from "fs";
import { readdir, stat } from "fs/promises";
import { initSentry } from "./sentry_init";

// ═══════════════════════════════════════════════════════════════════════════════
// TYPE DEFINITIONS
// ═══════════════════════════════════════════════════════════════════════════════

interface MCPRequest {
  jsonrpc: "2.0";
  method: string;
  params?: Record<string, unknown>;
  id?: number | string;
}

interface MCPResponse {
  jsonrpc: "2.0";
  id?: number | string;
  result?: unknown;
  error?: { code: number; message: string; data?: unknown };
}

interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: {
    type: "object";
    properties: Record<string, unknown>;
    required: string[];
  };
}

interface ToolResult {
  success: boolean;
  output: string;
  exitCode: number;
  duration: number;
}

// ═══════════════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════════

const VERSION = "3.3.0";
const CHTHONIC_ROOT = process.env.CHTHONIC_ROOT ?? import.meta.dir.replace(/[\\/]scripts$/, "");
const CHTHONIC_SCRIPT = join(CHTHONIC_ROOT, "scripts", "chthonic.ps1");
const HOME = process.env.USERPROFILE ?? "";
const DEBUG = process.env.MCP_DEBUG === "1";

function log(msg: string): void {
  if (DEBUG) console.error(`[chthonic-mcp] ${msg}`);
}

// ═══════════════════════════════════════════════════════════════════════════════
// PATH RESOLUTION — Win11 Global Polyglot Paths
// ═══════════════════════════════════════════════════════════════════════════════

const RUBY_ROOT_CANDIDATES = [
  process.env.RUBY_ROOT,
  "C:\\Ruby40-x64",
  "D:\\Ruby40-x64",
  "C:\\Ruby35-x64",
  "D:\\Ruby35-x64",
  "C:\\Ruby34-x64",
  "D:\\Ruby34-x64",
  "C:\\Ruby33-x64",
  "D:\\Ruby33-x64",
  "C:\\Ruby32-x64",
  "D:\\Ruby32-x64",
  "C:\\Ruby31-x64",
  "D:\\Ruby31-x64",
].filter((value): value is string => Boolean(value));

function rubyToolchainCandidates(relativePath: string): string[] {
  return RUBY_ROOT_CANDIDATES.map((root) => join(root, relativePath));
}

const TOOL_PATHS: Record<string, string[]> = {
  bun: [process.execPath, join(HOME, ".bun", "bin", "bun.exe")],
  brush: [join(HOME, ".cargo", "bin", "brush.exe")],
  uv: [join(HOME, ".local", "bin", "uv.exe")],
  cargo: [join(HOME, ".cargo", "bin", "cargo.exe")],
  rustc: [join(HOME, ".cargo", "bin", "rustc.exe")],
  go: ["C:\\Go\\bin\\go.exe", "C:\\Program Files\\Go\\bin\\go.exe"],
  ruby: rubyToolchainCandidates(join("bin", "ruby.exe")),
  gcc: rubyToolchainCandidates(join("msys64", "ucrt64", "bin", "gcc.exe")),
  "g++": rubyToolchainCandidates(join("msys64", "ucrt64", "bin", "g++.exe")),
  git: ["C:\\Program Files\\Git\\cmd\\git.exe"],
  make: rubyToolchainCandidates(join("msys64", "usr", "bin", "make.exe")),
  bash: [...rubyToolchainCandidates(join("msys64", "usr", "bin", "bash.exe")), "C:\\msys64\\usr\\bin\\bash.exe"],
  mdbook: [join(HOME, ".cargo", "bin", "mdbook.exe")],
  ruff: [join(HOME, ".local", "bin", "ruff.exe")],
  biome: [
    join(CHTHONIC_ROOT, "node_modules", ".bin", "biome.cmd"),
    join(CHTHONIC_ROOT, "node_modules", ".bin", "biome"),
    join(HOME, ".bun", "bin", "biome.exe"),
  ],
  pwsh: ["C:\\Program Files\\PowerShell\\7\\pwsh.exe"],
};

function resolveToolPath(tool: string): string {
  const candidates = TOOL_PATHS[tool];
  if (candidates) {
    for (const p of candidates) {
      if (existsSync(p)) return p;
    }
  }
  return Bun.which(tool) ?? tool;
}

// ═══════════════════════════════════════════════════════════════════════════════
// BUN-CENTRIC TOOL EXECUTION — Bun.spawn with timeout and zombie protection
// ═══════════════════════════════════════════════════════════════════════════════

const activeProcesses = new Set<any>();

async function runTool(exe: string, args: string[], cwd?: string, timeoutMs: number = 180000): Promise<ToolResult> {
  const start = performance.now();
  const workDir = cwd ?? CHTHONIC_ROOT;

  log(`exec: ${exe} ${args.join(" ")} [cwd: ${workDir}] [timeout: ${timeoutMs}ms]`);

  let proc: any;
  let timer: Timer | undefined;

  try {
    proc = Bun.spawn([exe, ...args], {
      cwd: workDir,
      stdout: "pipe",
      stderr: "pipe",
      env: { ...process.env, FORCE_COLOR: "0", NO_COLOR: "1" },
    });

    activeProcesses.add(proc);

    // Timeout logic
    const timeoutPromise = new Promise<ToolResult>((_, reject) => {
      timer = setTimeout(() => {
        log(`process timeout exceeded: ${exe}`);
        if (proc) {
          try {
            proc.kill();
            log(`killed process ${proc.pid}`);
          } catch (e) {
            log(`failed to kill process: ${e}`);
          }
        }
        reject(new Error(`Execution timed out after ${timeoutMs}ms`));
      }, timeoutMs);
    });

    const executionPromise = (async () => {
      const [stdout, stderr] = await Promise.all([
        new Response(proc.stdout).text(),
        new Response(proc.stderr).text(),
      ]);

      const exitCode = await proc.exited;
      const duration = performance.now() - start;

      const output = [
        stdout.trim(),
        stderr.trim() ? `\n[stderr] ${stderr.trim()}` : "",
      ].join("");

      return { success: exitCode === 0, output, exitCode, duration };
    })();

    const result = await Promise.race([executionPromise, timeoutPromise]);
    if (timer) clearTimeout(timer);
    return result;

  } catch (e) {
    if (timer) clearTimeout(timer);
    const err = e instanceof Error ? e.message : String(e);
    return { success: false, output: `[error] ${err}`, exitCode: -1, duration: performance.now() - start };
  } finally {
    if (proc) activeProcesses.delete(proc);
  }
}

function cleanupProcesses() {
  if (activeProcesses.size > 0) {
    console.error(`[chthonic-mcp] cleaning up ${activeProcesses.size} active processes...`);
    for (const proc of activeProcesses) {
      try {
        proc.kill();
      } catch {}
    }
    activeProcesses.clear();
  }
}

process.on("SIGINT", () => {
  cleanupProcesses();
  process.exit(0);
});

process.on("SIGTERM", () => {
  cleanupProcesses();
  process.exit(0);
});

async function runPolyglotTool(tool: string, args: string[], timeoutMs?: number): Promise<string> {
  const exe = resolveToolPath(tool);
  const result = await runTool(exe, args, undefined, timeoutMs);
  return `cmd: ${exe} ${args.join(" ")}\n${result.output}`;
}

async function runChthonic(args: string[], timeoutMs?: number): Promise<string> {
  const pwsh = resolveToolPath("pwsh");
  // Individual argument escaping for safe PowerShell injection
  const escapedArgs = args.map(arg => {
    if (typeof arg !== "string") return String(arg);
    // If it has spaces or special chars and isn't already quoted, quote it
    if (/[ &()\[\]{}#^=%!~'"]/.test(arg)) {
      return `'${arg.replace(/'/g, "''")}'`;
    }
    return arg;
  }).join(" ");

  const cmd = `& "${CHTHONIC_SCRIPT}" ${escapedArgs}`;
  const result = await runTool(pwsh, ["-NoProfile", "-NoLogo", "-Command", cmd], undefined, timeoutMs);
  return result.output;
}

// ═══════════════════════════════════════════════════════════════════════════════
// MCP TOOL DEFINITIONS — 20 Tools (Polyglot + Archive + Meta)
// ═══════════════════════════════════════════════════════════════════════════════

const POLYGLOT_TOOLS: ToolDefinition[] = [
  { name: "cargo", description: "Run cargo (Rust build system) — build, test, run, clippy, etc.", inputSchema: { type: "object", properties: { args: { type: "array", items: { type: "string" }, default: ["build"], description: "Arguments to pass to cargo" } }, required: [] } },
  { name: "uv", description: "Run uv (Python package manager) — pip install, sync, lock, etc.", inputSchema: { type: "object", properties: { args: { type: "array", items: { type: "string" }, default: ["--version"], description: "Arguments to pass to uv" } }, required: [] } },
  { name: "bun_run", description: "Run bun (JS/TS runtime) — run, install, test, build, etc.", inputSchema: { type: "object", properties: { args: { type: "array", items: { type: "string" }, default: ["--version"], description: "Arguments to pass to bun" } }, required: [] } },
  { name: "gcc", description: "Run GCC compiler from MSYS2 UCRT64 toolchain.", inputSchema: { type: "object", properties: { args: { type: "array", items: { type: "string" }, default: ["--version"], description: "Arguments to pass to gcc" } }, required: [] } },
  { name: "gpp", description: "Run g++ compiler from MSYS2 UCRT64 toolchain.", inputSchema: { type: "object", properties: { args: { type: "array", items: { type: "string" }, default: ["--version"], description: "Arguments to pass to g++" } }, required: [] } },
  { name: "go_run", description: "Run go (Go compiler/runtime) — build, run, test, mod, etc.", inputSchema: { type: "object", properties: { args: { type: "array", items: { type: "string" }, default: ["version"], description: "Arguments to pass to go" } }, required: [] } },
  { name: "ruby", description: "Run Ruby interpreter with args.", inputSchema: { type: "object", properties: { args: { type: "array", items: { type: "string" }, default: ["--version"], description: "Arguments to pass to ruby" } }, required: [] } },
  { name: "git", description: "Run git with args — status, log, diff, commit, push, etc.", inputSchema: { type: "object", properties: { args: { type: "array", items: { type: "string" }, default: ["status"], description: "Arguments to pass to git" } }, required: [] } },
  { name: "bash", description: "Run bash (MSYS2) with args or script.", inputSchema: { type: "object", properties: { args: { type: "array", items: { type: "string" }, default: ["--version"], description: "Arguments to pass to bash" } }, required: [] } },
  { name: "brush", description: "Run Brush shell (Rust-based POSIX/bash-compatible shell) with args.", inputSchema: { type: "object", properties: { args: { type: "array", items: { type: "string" }, default: ["--version"], description: "Arguments to pass to brush" } }, required: [] } },
  { name: "make", description: "Run GNU make with args.", inputSchema: { type: "object", properties: { args: { type: "array", items: { type: "string" }, default: ["--version"], description: "Arguments to pass to make" } }, required: [] } },
];

const ARCHIVE_TOOLS: ToolDefinition[] = [
  { name: "chthonic_status", description: "Get polyglot environment status display with all tool versions.", inputSchema: { type: "object", properties: {}, required: [] } },
  { name: "chthonic_resolve", description: "Resolve Semantic IDs (@SID) to file paths. Use --list for all SIDs.", inputSchema: { type: "object", properties: { sid: { type: "string", description: "Semantic ID to resolve" }, list: { type: "boolean", description: "List all SIDs" }, json: { type: "boolean", description: "Output as JSON" } }, required: [] } },
  { name: "chthonic_new", description: "Scaffold new projects for the polyglot stack (uv, bun, cargo, go, ruby, azd).", inputSchema: { type: "object", properties: { profile: { type: "string", enum: ["uv-python-app", "uv-python-lib", "bun-react", "bun-react-tailwind", "bun-next", "cargo-rust-bin", "cargo-rust-lib", "go-basic", "ruby-gem", "azure-azd-template"], description: "Scaffold profile to use" }, destination: { type: "string", description: "Destination directory" }, module: { type: "string", description: "Optional module/template name for Go/Azure" }, dry_run: { type: "boolean", description: "Preview without creating files" }, json: { type: "boolean", description: "Output as JSON" } }, required: ["profile", "destination"] } },
  { name: "chthonic_ssot", description: "Query the SSOT loremaster control plane: queue, entity, section, drift, lineage.", inputSchema: { type: "object", properties: { action: { type: "string", enum: ["queue", "entity", "section", "drift", "lineage"], description: "SSOT loremaster action to run" }, query: { type: "string", description: "Entity or section query. For lineage, this filters by entity." }, write: { type: "string", description: "Optional output path for queue/lineage markdown" }, json: { type: "boolean", description: "Output as JSON" } }, required: ["action"] } },
  { name: "chthonic_workflow", description: "Run higher-level Chthonic workflow profiles: control-plane or toolchain-governance.", inputSchema: { type: "object", properties: { profile: { type: "string", enum: ["control-plane", "toolchain-governance"], description: "Workflow profile to run" }, write: { type: "boolean", description: "Persist report artifacts under dumpster-dive/intake/chthonic-workflows/" }, json: { type: "boolean", description: "Output report as JSON" } }, required: ["profile"] } },
  { name: "chthonic_audit", description: "Analyze root directory health, find stale/orphan files.", inputSchema: { type: "object", properties: { dry_run: { type: "boolean", description: "Preview without changes" }, json: { type: "boolean", description: "Output as JSON" } }, required: [] } },
  { name: "chthonic_map", description: "Generate codebase inventory and dependency map.", inputSchema: { type: "object", properties: { dry_run: { type: "boolean", description: "Preview without writing" }, json: { type: "boolean", description: "Output as JSON" } }, required: [] } },
  { name: "chthonic_analyze", description: "Frequency analysis of line patterns in a file.", inputSchema: { type: "object", properties: { file: { type: "string", description: "File to analyze" }, top: { type: "number", description: "Number of top patterns to show" }, json: { type: "boolean", description: "Output as JSON" } }, required: ["file"] } },
  { name: "chthonic_compact", description: "Compact markdown files using noise pattern removal.", inputSchema: { type: "object", properties: { file: { type: "string", description: "File to compact" }, dry_run: { type: "boolean", description: "Preview without changes" }, stats: { type: "boolean", description: "Show compaction statistics" } }, required: ["file"] } },
  { name: "chthonic_book", description: "Build/serve mdBook documentation site.", inputSchema: { type: "object", properties: { action: { type: "string", enum: ["build", "serve", "clean"], default: "build", description: "Action to perform" } }, required: [] } },
  { name: "chthonic_scan", description: "Scan the repository and return file statistics (legacy scanRepository ported).", inputSchema: { type: "object", properties: {}, required: [] } },
  { name: "chthonic_validate_ssot", description: `Validate SSOT (${SSOT_POINTER}) integrity via SHA-256 hash (legacy validateSSOT ported).`, inputSchema: { type: "object", properties: {}, required: [] } },
  { name: "toolchain_probe", description: "Run repo-local toolchain probe and write a deterministic manifest under dumpster-dive/intake/toolchain-probe/.", inputSchema: { type: "object", properties: { writeVscodeSnippet: { type: "boolean", default: false } }, required: [] } },
  { name: "overnight_report", description: "Run the Bun overnight daemon once to generate a report under dumpster-dive/intake/overnight-daemon/.", inputSchema: { type: "object", properties: { top: { type: "integer", minimum: 1, default: 20 }, maxTodo: { type: "integer", minimum: 1, default: 80 }, siphon: { type: "boolean", default: false }, classify: { type: "boolean", default: false, description: "Enable enhanced classification and complexity analysis" } }, required: [] } },
];

const META_TOOLS: ToolDefinition[] = [
  { name: "polyglot_versions", description: "Get all polyglot tool versions with paths (bun, rust, go, python, ruby, gcc, vulkan, etc).", inputSchema: { type: "object", properties: { includePaths: { type: "boolean", default: true, description: "Include full paths in output" } }, required: [] } },
  { name: "claudine_env", description: "Activate/verify the claudine polyglot environment. Returns environment status.", inputSchema: { type: "object", properties: { verify: { type: "boolean", default: true, description: "Verify environment is properly configured" } }, required: [] } },
  {
    name: "meta_cli",
    description: "Chthonic v3.3.0 Meta-CLI — unified polyglot development tool with domains: env, status, detect, ide (launch/detect/reset), mcp (start/stop/status), config (init/show/set), new, shell, workflow, audit, compact, resolve, map, analyze, book.",
    inputSchema: {
      type: "object",
      properties: {
        domain: {
          type: "string",
          description: "Domain: env, status, detect, ide, mcp, config, new, shell, workflow, ssot, audit, compact, resolve, map, analyze, book",
          enum: ["env", "status", "detect", "ide", "mcp", "config", "new", "shell", "workflow", "ssot", "audit", "compact", "resolve", "map", "analyze", "book", "extract"]
        },
        action: {
          type: "string",
          description: "Action within domain (e.g., 'launch' for ide, 'start' for mcp, 'init' for config). Optional for single-action domains."
        },
        args: {
          type: "array",
          items: { type: "string" },
          description: "Additional arguments to pass to the command"
        }
      },
      required: ["domain"]
    }
  },
];

const ALL_TOOLS: ToolDefinition[] = [...POLYGLOT_TOOLS, ...ARCHIVE_TOOLS, ...META_TOOLS];

// ═══════════════════════════════════════════════════════════════════════════════
// META TOOL IMPLEMENTATIONS
// ═══════════════════════════════════════════════════════════════════════════════

initSentry();

async function polyglotVersions(includePaths: boolean): Promise<string> {
  const checks = [
    { name: "bun", tool: "bun", args: ["--version"] },
    { name: "biome", tool: "biome", args: ["--version"] },
    { name: "uv", tool: "uv", args: ["--version"] },
    { name: "ruff", tool: "ruff", args: ["--version"] },
    { name: "cargo", tool: "cargo", args: ["--version"] },
    { name: "rustc", tool: "rustc", args: ["--version"] },
    { name: "go", tool: "go", args: ["version"] },
    { name: "ruby", tool: "ruby", args: ["--version"] },
    { name: "gcc", tool: "gcc", args: ["--version"] },
    { name: "g++", tool: "g++", args: ["--version"] },
    { name: "make", tool: "make", args: ["--version"] },
    { name: "git", tool: "git", args: ["--version"] },
    { name: "mdbook", tool: "mdbook", args: ["--version"] },
    { name: "bash", tool: "bash", args: ["--version"] },
  ];

  const lines: string[] = [`🔥💀⚓ CHTHONIC POLYGLOT v${VERSION}`, "═".repeat(50)];

  for (const c of checks) {
    const exe = resolveToolPath(c.tool);
    try {
      const result = await runTool(exe, c.args);
      const firstLine = result.output.split(/\r?\n/).find(l => l.trim()) ?? "not found";
      const where = includePaths ? ` → ${exe}` : "";
      lines.push(`  ${c.name}: ${firstLine.trim()}${where}`);
    } catch {
      lines.push(`  ${c.name}: not found`);
    }
  }

  if (process.env.VULKAN_SDK) {
    const ver = process.env.VULKAN_SDK.split(/[\\\/]/).pop();
    lines.push(`  vulkan: ${ver} → ${process.env.VULKAN_SDK}`);
  }

  lines.push("═".repeat(50));
  return lines.join("\n");
}

async function claudineEnv(verify: boolean): Promise<string> {
  if (!verify) return "claudine_env: verification skipped";

  const checks: string[] = [];

  if (existsSync(CHTHONIC_SCRIPT)) {
    checks.push(`✅ chthonic.ps1 found: ${CHTHONIC_SCRIPT}`);
  } else {
    checks.push(`❌ chthonic.ps1 NOT found: ${CHTHONIC_SCRIPT}`);
  }

  const keyTools = ["bun", "cargo", "uv", "go", "git"];
  for (const t of keyTools) {
    const path = resolveToolPath(t);
    if (existsSync(path)) {
      checks.push(`✅ ${t}: ${path}`);
    } else {
      checks.push(`⚠️ ${t}: not found in expected paths`);
    }
  }

  return `🔥💀⚓ CLAUDINE ENV STATUS\n${"─".repeat(40)}\n${checks.join("\n")}`;
}

async function chthonicScan(): Promise<string> {
  const files: { path: string; size: number }[] = [];

  async function walk(dir: string) {
    const entries = await readdir(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = join(dir, entry.name);
      if (entry.name === "node_modules" || entry.name === ".git" || entry.name === "target") continue;
      if (entry.isDirectory()) {
        await walk(fullPath);
      } else {
        const stats = await stat(fullPath);
        files.push({ path: fullPath.replace(CHTHONIC_ROOT, "").replace(/^[\\\/]/, ""), size: stats.size });
      }
    }
  }

  try {
    await walk(CHTHONIC_ROOT);
    const result = {
      repository: CHTHONIC_ROOT,
      file_count: files.length,
      files: files.slice(0, 50),
    };
    return JSON.stringify(result, null, 2);
  } catch (err) {
    return `Error scanning repository: ${err}`;
  }
}

function canonicalizeSSOT(text: string): string {
  text = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const lines = text.split("\n").map((line) => line.trimEnd());
  return lines.join("\n").normalize("NFC").trim();
}

async function chthonicValidateSSOT(): Promise<string> {
  const ssotPath = join(CHTHONIC_ROOT, SSOT_POINTER);
  try {
    const file = Bun.file(ssotPath);
    const content = await file.text();
    const canonical = canonicalizeSSOT(content);
    const hasher = new Bun.CryptoHasher("sha256");
    hasher.update(canonical);
    const digest = hasher.digest("hex");

    return JSON.stringify({
      status: "valid",
      path: ssotPath,
      size: file.size,
      lines: content.split("\n").length,
      hash: digest,
    }, null, 2);
  } catch (err: any) {
    return JSON.stringify({ status: "error", message: err.message }, null, 2);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// TOOL CALL HANDLER
// ═══════════════════════════════════════════════════════════════════════════════

const DIRECT_TOOL_MAP: Record<string, string> = {
  cargo: "cargo", uv: "uv", bun_run: "bun", brush: "brush", gcc: "gcc", gpp: "g++",
  go_run: "go", ruby: "ruby", git: "git", bash: "bash", make: "make"
};

async function handleToolCall(name: string, args: Record<string, unknown>): Promise<string> {
  log(`tool call: ${name} ${JSON.stringify(args)}`);

  if (name in DIRECT_TOOL_MAP) {
    const toolArgs = Array.isArray(args?.args) ? args.args as string[] : ["--version"];
    let timeout = 180000;
    if (name === "cargo") timeout = 600000; // 10m for Rust
    return runPolyglotTool(DIRECT_TOOL_MAP[name], toolArgs, timeout);
  }

  if (name === "polyglot_versions") return polyglotVersions(args?.includePaths !== false);
  if (name === "claudine_env") return claudineEnv(args?.verify !== false);
  if (name === "chthonic_scan") return chthonicScan();
  if (name === "chthonic_validate_ssot") return chthonicValidateSSOT();

  if (name === "toolchain_probe") {
    const pwsh = resolveToolPath("pwsh");
    const script = join(CHTHONIC_ROOT, "scripts", "probe_toolchain_path.ps1");
    const cmdArgs = ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script];
    if (args.writeVscodeSnippet) cmdArgs.push("-WriteVscodeSnippet");
    const result = await runTool(pwsh, cmdArgs, undefined, 300000);
    return result.output;
  }

  if (name === "overnight_report") {
    const bun = resolveToolPath("bun");
    const script = join(CHTHONIC_ROOT, "scripts", "overnight_daemon.ts");
    const top = args.top ?? 20;
    const maxTodo = args.maxTodo ?? 80;
    const cmdArgs = [script, "--top", String(top), "--maxTodo", String(maxTodo)];
    if (args.siphon) cmdArgs.push("--siphon");
    if (args.classify) cmdArgs.push("--classify");
    const result = await runTool(bun, cmdArgs, undefined, 600000);
    return result.output;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // CHTHONIC V3.0.0 META-CLI ROUTER — Domain/Action model
  // ═══════════════════════════════════════════════════════════════════════════
  if (name === "meta_cli") {
    const domain = args.domain as string;
    const action = args.action as string | undefined;
    const cmdArgs = Array.isArray(args.args) ? args.args as string[] : [];

    const allArgs: string[] = [];
    allArgs.push(domain);
    if (action) allArgs.push(action);
    allArgs.push(...cmdArgs);
    allArgs.push("-Json"); // PowerShell switch for JSON output

    log(`chthonic meta-CLI: ${allArgs.join(" ")}`);
    return await runChthonic(allArgs, 300000); // 5m default for meta-CLI
  }

  const cmdArgs: string[] = [];
  let timeout = 180000;

  switch (name) {
    case "chthonic_status": cmdArgs.push("status"); break;
    case "chthonic_resolve":
      cmdArgs.push("resolve");
      if (args.list) cmdArgs.push("--list");
      if (args.json) cmdArgs.push("--json");
      if (args.sid) cmdArgs.push(args.sid as string);
      break;
    case "chthonic_new": {
      cmdArgs.push("new");
      cmdArgs.push((args.profile as string) ?? "uv-python-app");
      if (args.destination) cmdArgs.push(args.destination as string);
      if (args.module) cmdArgs.push("--module", args.module as string);
      if (args.dry_run) cmdArgs.push("--dry-run");
      if (args.json) cmdArgs.push("--json");
      timeout = 600000;
      break;
    }
    case "chthonic_ssot": {
      cmdArgs.push("ssot");
      const action = (args.action as string | undefined) ?? "queue";
      cmdArgs.push(action);
      if (action === "entity" || action === "section") {
        if (args.query) cmdArgs.push(args.query as string);
      } else if (action === "lineage") {
        if (args.query) cmdArgs.push("--entity", args.query as string);
      }
      if (args.write) cmdArgs.push("--write", args.write as string);
      if (args.json) cmdArgs.push("--json");
      break;
    }
    case "chthonic_workflow": {
      cmdArgs.push("workflow");
      cmdArgs.push((args.profile as string) ?? "control-plane");
      if (args.write) cmdArgs.push("--write");
      if (args.json) cmdArgs.push("--json");
      timeout = 600000;
      break;
    }
    case "chthonic_audit":
      cmdArgs.push("audit");
      if (args.dry_run) cmdArgs.push("--dry-run");
      if (args.json) cmdArgs.push("--json");
      timeout = 300000;
      break;
    case "chthonic_map":
      cmdArgs.push("map");
      if (args.dry_run) cmdArgs.push("--dry-run");
      if (args.json) cmdArgs.push("--json");
      timeout = 300000;
      break;
    case "chthonic_analyze":
      cmdArgs.push("analyze");
      if (args.file) cmdArgs.push(args.file as string);
      if (args.top) cmdArgs.push("--top", String(args.top));
      if (args.json) cmdArgs.push("--json");
      break;
    case "chthonic_compact":
      cmdArgs.push("compact");
      if (args.file) cmdArgs.push(args.file as string);
      if (args.dry_run) cmdArgs.push("--dry-run");
      if (args.stats) cmdArgs.push("--stats");
      break;
    case "chthonic_book":
      cmdArgs.push("book");
      cmdArgs.push((args.action as string) ?? "build");
      timeout = 300000;
      break;
    default:
      return `Unknown tool: ${name}`;
  }

  return await runChthonic(cmdArgs, timeout);
}

// ═══════════════════════════════════════════════════════════════════════════════
// MCP PROTOCOL HANDLERS — JSON-RPC 2.0 over stdio
// ═══════════════════════════════════════════════════════════════════════════════

async function handleRequest(request: MCPRequest): Promise<MCPResponse> {
  const { method, params, id } = request;
  log(`request: ${method}`);

  switch (method) {
    case "initialize":
      return {
        jsonrpc: "2.0", id,
        result: {
          protocolVersion: "2024-11-05",
          capabilities: { tools: {} },
          serverInfo: { name: "chthonic-polyglot", version: VERSION }
        }
      };

    case "tools/list":
      return { jsonrpc: "2.0", id, result: { tools: ALL_TOOLS } };

    case "tools/call": {
      const { name, arguments: callArgs } = params as { name: string; arguments?: Record<string, unknown> };
      try {
        const result = await handleToolCall(name, callArgs ?? {});
        return { jsonrpc: "2.0", id, result: { content: [{ type: "text", text: result }] } };
      } catch (e) {
        const errMsg = e instanceof Error ? e.message : String(e);
        return { jsonrpc: "2.0", id, error: { code: -32000, message: `Tool execution failed: ${errMsg}` } };
      }
    }

    case "notifications/initialized":
      return { jsonrpc: "2.0" };

    default:
      return { jsonrpc: "2.0", id, error: { code: -32601, message: `Method not found: ${method}` } };
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// STDIO TRANSPORT — Bun-native stdin handling with proper async management
// ═══════════════════════════════════════════════════════════════════════════════

const decoder = new TextDecoder();
let buffer = "";
let pendingOps = 0;
let stdinClosed = false;

function checkExit(): void {
  if (stdinClosed && pendingOps === 0) {
    log("stdin closed and no pending ops, shutting down");
    process.exit(0);
  }
}

async function processLine(line: string): Promise<void> {
  if (!line.trim()) return;

  pendingOps++;
  try {
    const request = JSON.parse(line) as MCPRequest;
    const response = await handleRequest(request);
    if (response.id !== undefined || response.result !== undefined || response.error !== undefined) {
      process.stdout.write(JSON.stringify(response) + "\n");
    }
  } catch (e) {
    const errMsg = e instanceof Error ? e.message : String(e);
    log(`parse error: ${errMsg}`);
    process.stdout.write(JSON.stringify({ jsonrpc: "2.0", error: { code: -32700, message: `Parse error: ${errMsg}` } }) + "\n");
  } finally {
    pendingOps--;
    checkExit();
  }
}

process.stdin.on("data", (chunk: Buffer) => {
  buffer += decoder.decode(chunk);
  const lines = buffer.split("\n");
  buffer = lines.pop() ?? "";
  for (const line of lines) processLine(line);
});

process.stdin.on("end", () => {
  stdinClosed = true;
  log("stdin closed");
  checkExit();
});

// Startup
const toolCount = ALL_TOOLS.length;

// CLI Argument Handling (Introspection)
if (process.argv.includes("--list-tools")) {
  console.log(JSON.stringify(ALL_TOOLS, null, 2));
  process.exit(0);
}
if (process.argv.includes("--list-names-only")) {
  console.log(ALL_TOOLS.map(t => t.name).join("\n"));
  process.exit(0);
}
if (process.argv.includes("--version")) {
  console.log(`v${VERSION}`);
  process.exit(0);
}

console.error(`[chthonic-mcp] Server started v${VERSION} (${toolCount} tools: ${POLYGLOT_TOOLS.length} polyglot + ${ARCHIVE_TOOLS.length} archive + ${META_TOOLS.length} meta)`);
