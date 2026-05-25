#!/usr/bin/env bun
// @SID: SCRIPT_VERIFY_RESCUE_SHIM_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: verify-rescue-shim.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ (Verifies wiring of chthonic-rescue.ts + git-chthonic.cmd + .vscode/settings.json)
// ║   └─◄ (Compounds [[reference-ci-autofix-gate]] V1.5 — closes the false-positive gap)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * verify-rescue-shim.ts — One-command smoke test for V1.5 wiring.
 *
 * Existence-of-fix-isn't-proof-of-fix. This script exercises each layer of
 * the V1.5 rescue chain in an isolated sandbox (tmp dir, no impact on the
 * real repo) and reports PASS/FAIL per assertion. The conductor runs it
 * once after wiring changes; the output is the testimony.
 *
 * Tested layers:
 *   1. Shim file exists + is CRLF-encoded (cmd.exe parser requirement)
 *   2. Rescue script exists + bun can execute it
 *   3. .vscode/settings.json git.path points to the shim
 *   4. Shim's dynamic REAL_GIT lookup resolves to a working git
 *   5. Shim with `commit` arg in any position triggers rescue
 *   6. Shim with non-commit subcommand skips rescue (silent passthrough)
 *   7. Rescue acts on orphan-gitlink + nothing-else-staged state
 *   8. Rescue silent on no-op (no orphans)
 *   9. End-to-end: VS Code's exact invocation pattern (--file - stdin) lands in ONE attempt
 *
 * V1.8 — live mode is now exclusive (was a verifier false-positive):
 *   V1.7's --live ran sandbox tests AND the log check. Problem: the sandbox
 *   tests invoke the shim via `cmd /c shim ...` (to test arg-scanning, etc.),
 *   which writes entries to the very log --live then reads. Result: --live
 *   could PASS just from verifier-self-traffic, with the misleading label
 *   "from VS Code." Now --live SKIPS the sandbox tests and only checks the
 *   log — so a PASS in --live mode means entries came from SOMETHING that
 *   wasn't this verifier (VS Code being the expected source).
 *
 * Three exclusive modes (per [[feedback-false-positive-avoidance]]):
 *   bun run scripts/verify-rescue-shim.ts              # sandbox tests only
 *   bun run scripts/verify-rescue-shim.ts --live       # log check only (no sandbox)
 *   bun run scripts/verify-rescue-shim.ts --reset-log  # truncate log + exit
 *
 * Post-VS-Code-update verification procedure:
 *   1. bun run scripts/verify-rescue-shim.ts --reset-log
 *   2. Do any git op in VS Code (commit click, refresh source-control panel)
 *   3. bun run scripts/verify-rescue-shim.ts --live
 *   4. PASS with entries containing `-c user.useConfigOnly=true` → VS Code IS using shim
 */

import { spawnSync, execSync } from "child_process";
import {
  existsSync,
  readFileSync,
  mkdirSync,
  rmSync,
  writeFileSync,
  statSync,
  truncateSync,
} from "fs";
import { resolve, join } from "path";
import { tmpdir } from "os";

const REPO_ROOT = resolve(import.meta.dir, "..");
const SHIM_PATH = join(REPO_ROOT, "scripts", "git-chthonic.cmd");
const RESCUE_PATH = join(REPO_ROOT, "scripts", "chthonic-rescue.ts");
const VSCODE_SETTINGS = join(REPO_ROOT, ".vscode", "settings.json");
const SHIM_LOG = join(REPO_ROOT, ".git", "chthonic-rescue-shim.log");

const LIVE_CHECK = process.argv.includes("--live");
const RESET_LOG = process.argv.includes("--reset-log");

// --reset-log is exclusive: truncate the log and exit. Running other tests
// would re-pollute it with verifier-self-traffic and defeat the purpose.
if (RESET_LOG) {
  if (existsSync(SHIM_LOG)) {
    truncateSync(SHIM_LOG, 0);
    console.log(`[verify] truncated ${SHIM_LOG}`);
  } else {
    console.log(`[verify] log not present at ${SHIM_LOG} (nothing to reset)`);
  }
  console.log("Next: do any git op in VS Code, then `bun run scripts/verify-rescue-shim.ts --live`");
  process.exit(0);
}

// --live is exclusive: read the log and report. Sandbox tests would pollute
// the log with verifier-self-traffic and create false-positive PASSes (this
// was V1.7's flaw — V1.8 makes the modes mutually exclusive).
if (LIVE_CHECK) {
  console.log("\n═══ shim invocation log (--live mode) ═══\n");
  if (!existsSync(SHIM_LOG)) {
    console.log(`✗ FAIL  log not found at ${SHIM_LOG}`);
    console.log(`        Shim has never been invoked since this repo. Either:`);
    console.log(`        - VS Code is using the default git binary (settings.json git.path not picked up)`);
    console.log(`        - Or no git op has happened since the workspace opened`);
    console.log(`        Try: reload VS Code window, do any git op, re-run --live.`);
    process.exit(1);
  }
  const content = readFileSync(SHIM_LOG, "utf8");
  const lines = content.split("\n").filter(Boolean);
  if (lines.length === 0) {
    console.log(`✗ FAIL  log is empty (was reset; nothing invoked since)`);
    console.log(`        Click commit in VS Code, or refresh source-control panel, then re-run --live.`);
    process.exit(1);
  }
  const stat = statSync(SHIM_LOG);
  const ageMin = (Date.now() - stat.mtimeMs) / 60000;
  // Filter for VS-Code-pattern entries (have -c user.useConfigOnly=true or
  // are commit/status/log/etc subcommands typical of VS Code's git extension).
  // Verifier's own entries DO match these patterns (which is the false-positive
  // risk), but in --live mode the verifier has NOT polluted the log this run.
  const vsCodePattern = lines.filter((l) => /-c\s+user\.useConfigOnly=true/.test(l));
  console.log(`✓ PASS  ${lines.length} log entries; most recent ${ageMin.toFixed(1)} min ago`);
  console.log(`        ${vsCodePattern.length} entries match VS Code's invocation pattern (-c user.useConfigOnly=true)`);
  console.log(`        last 5 entries:`);
  for (const l of lines.slice(-5)) {
    console.log(`          ${l.trim()}`);
  }
  if (ageMin > 60) {
    console.log(`\n⚠ WARNING  log is stale (${ageMin.toFixed(0)} min old) — recent git ops aren't hitting the shim.`);
    process.exit(1);
  }
  if (vsCodePattern.length === 0) {
    console.log(`\n⚠ WARNING  no entries match VS Code's invocation pattern. Either VS Code isn't using the shim,`);
    console.log(`            or you haven't triggered a commit-class operation since the last reset.`);
  }
  process.exit(0);
}

const results: { name: string; ok: boolean; detail: string }[] = [];

function check(name: string, fn: () => string | null): void {
  try {
    const detail = fn();
    if (detail === null) {
      results.push({ name, ok: true, detail: "ok" });
    } else {
      results.push({ name, ok: false, detail });
    }
  } catch (e) {
    results.push({ name, ok: false, detail: `EXCEPTION: ${(e as Error).message}` });
  }
}

// Layer 1: shim exists + CRLF
check("shim file exists", () => existsSync(SHIM_PATH) ? null : `missing: ${SHIM_PATH}`);
check("shim has CRLF line endings (cmd.exe parser requirement)", () => {
  const buf = readFileSync(SHIM_PATH);
  // Find first newline; must be 0x0D 0x0A
  for (let i = 0; i < buf.length - 1; i++) {
    if (buf[i] === 0x0a) {
      if (i > 0 && buf[i - 1] === 0x0d) return null;
      return `first \\n at offset ${i} not preceded by \\r — LF-only, cmd.exe will fail to parse`;
    }
  }
  return "no newlines found";
});

// Layer 2: rescue script + bun
check("rescue script exists", () => existsSync(RESCUE_PATH) ? null : `missing: ${RESCUE_PATH}`);
check("bun can execute rescue script (--help-like probe)", () => {
  // Run rescue in repo root with --silent; should exit 0 (nothing to rescue here)
  const r = spawnSync("bun", ["run", RESCUE_PATH, "--silent"], {
    encoding: "utf8",
    cwd: REPO_ROOT,
    shell: false,
  });
  if (r.status !== 0) return `rescue exit ${r.status}: ${r.stderr?.trim()}`;
  if ((r.stdout ?? "").trim().length > 0) {
    return `--silent mode produced output (should be silent on no-op): ${r.stdout.trim()}`;
  }
  return null;
});

// Layer 3: .vscode/settings.json git.path
check(".vscode/settings.json wires git.path to the shim", () => {
  if (!existsSync(VSCODE_SETTINGS)) return `missing: ${VSCODE_SETTINGS}`;
  const content = readFileSync(VSCODE_SETTINGS, "utf8");
  // settings.json is JSONC (comments + trailing commas) — VS Code parses it
  // permissively; strict JSON.parse rejects it. Regex-match the key + value
  // instead of full parse. Match: "git.path": "<some-value>"
  // Skip lines that are commented out (line starts with optional whitespace + //).
  const lines = content.split("\n");
  let active_line: string | null = null;
  for (const l of lines) {
    if (/^\s*\/\//.test(l)) continue; // skip commented-out lines
    if (/"git\.path"\s*:/.test(l)) {
      active_line = l;
      break;
    }
  }
  if (!active_line) return "git.path key absent (or only present in commented-out lines)";
  const value_match = active_line.match(/"git\.path"\s*:\s*"([^"]+)"/);
  if (!value_match) return `git.path line found but value unparseable: ${active_line.trim()}`;
  const gitPath = value_match[1];
  if (!gitPath.includes("git-chthonic.cmd")) {
    return `git.path = ${gitPath} — does not reference git-chthonic.cmd`;
  }
  return null;
});

// Layer 4: shim's dynamic git lookup
check("shim's dynamic REAL_GIT lookup finds a working git", () => {
  // Invoke shim with --version; should return git version
  const r = spawnSync("cmd", ["/c", SHIM_PATH, "--version"], {
    encoding: "utf8",
    cwd: REPO_ROOT,
  });
  if (r.status !== 0) return `shim --version exit ${r.status}: ${r.stderr?.trim()}`;
  if (!(r.stdout ?? "").includes("git version")) {
    return `shim --version output unexpected: ${r.stdout?.trim()}`;
  }
  return null;
});

// Layer 5+6: arg-scanning. Need isolated sandbox.
const sandbox = join(tmpdir(), `v15-verify-${process.pid}`);
function setupSandbox(): void {
  if (existsSync(sandbox)) rmSync(sandbox, { recursive: true, force: true });
  mkdirSync(sandbox, { recursive: true });
  const run = (cmd: string, args: string[], cwd: string) => {
    const r = spawnSync(cmd, args, { cwd, encoding: "utf8" });
    if (r.status !== 0) {
      throw new Error(`${cmd} ${args.join(" ")} failed in ${cwd}: ${r.stderr}`);
    }
  };
  run("git", ["init", "-q"], sandbox);
  run("git", ["config", "user.email", "verify@chthonic.local"], sandbox);
  run("git", ["config", "user.name", "verify"], sandbox);
  writeFileSync(join(sandbox, "a.txt"), "init\n");
  run("git", ["add", "a.txt"], sandbox);
  run("git", ["commit", "-q", "-m", "init"], sandbox);
}

function addOrphanGitlink(): string {
  const inner = join(sandbox, "orphan_inner");
  mkdirSync(inner, { recursive: true });
  const run = (cmd: string, args: string[], cwd: string) => {
    const r = spawnSync(cmd, args, { cwd, encoding: "utf8" });
    if (r.status !== 0) throw new Error(`${cmd} ${args.join(" ")} failed: ${r.stderr}`);
  };
  run("git", ["init", "-q"], inner);
  run("git", ["config", "user.email", "i@i.local"], inner);
  run("git", ["config", "user.name", "i"], inner);
  writeFileSync(join(inner, "inner.txt"), "init\n");
  run("git", ["add", "inner.txt"], inner);
  run("git", ["commit", "-q", "-m", "inner init"], inner);
  const sha = execSync("git rev-parse HEAD", { cwd: inner, encoding: "utf8" }).trim();
  writeFileSync(join(inner, "inner.txt"), "init\nmore\n");
  run("git", ["update-index", "--add", "--cacheinfo", `160000,${sha},orphan_inner`], sandbox);
  run("git", ["commit", "-q", "-m", "register orphan"], sandbox);
  return sha;
}

try {
  setupSandbox();

  check("shim with `commit` in middle of args triggers rescue (orphan-gitlink case)", () => {
    addOrphanGitlink();
    // Mimic VS Code's invocation pattern with -c flags BEFORE commit
    const r = spawnSync("cmd", [
      "/c", SHIM_PATH,
      "-c", "user.useConfigOnly=true",
      "commit", "--allow-empty-message", "-m", "shim verify test",
    ], { encoding: "utf8", cwd: sandbox });
    if (r.status !== 0) {
      return `shim commit exit ${r.status}: stderr=${r.stderr?.trim()} stdout=${r.stdout?.trim()}`;
    }
    // Verify the commit actually landed with the deletion
    const log = spawnSync("git", ["log", "-1", "--format=%H %s", "--", "orphan_inner"], {
      encoding: "utf8", cwd: sandbox,
    });
    if (!(log.stdout ?? "").includes("shim verify test")) {
      return `commit did not land or did not include orphan_inner deletion: ${log.stdout?.trim()}`;
    }
    return null;
  });

  // Reset sandbox for next test
  rmSync(sandbox, { recursive: true, force: true });
  setupSandbox();

  check("shim with non-commit subcommand skips rescue (passthrough)", () => {
    addOrphanGitlink();
    const before = spawnSync("git", ["status", "-s", "--ignore-submodules=none"], {
      encoding: "utf8", cwd: sandbox,
    }).stdout?.trim();
    // Invoke a NON-commit subcommand; should NOT trigger rescue
    spawnSync("cmd", ["/c", SHIM_PATH, "status", "-s"], {
      encoding: "utf8", cwd: sandbox,
    });
    const after = spawnSync("git", ["status", "-s", "--ignore-submodules=none"], {
      encoding: "utf8", cwd: sandbox,
    }).stdout?.trim();
    if (before !== after) {
      return `non-commit subcommand modified index! before='${before}' after='${after}'`;
    }
    return null;
  });

  rmSync(sandbox, { recursive: true, force: true });
  setupSandbox();

  check("rescue silent on no-op (no orphans present)", () => {
    // No orphans; staged file present
    writeFileSync(join(sandbox, "fresh.txt"), "x\n");
    spawnSync("git", ["add", "fresh.txt"], { cwd: sandbox });
    const r = spawnSync("bun", ["run", RESCUE_PATH, "--silent"], {
      encoding: "utf8", cwd: sandbox,
    });
    if (r.status !== 0) return `rescue exit ${r.status}`;
    if ((r.stdout ?? "").trim().length > 0) {
      return `--silent mode produced output: ${r.stdout.trim()}`;
    }
    return null;
  });

  rmSync(sandbox, { recursive: true, force: true });
  setupSandbox();

  check("E2E: VS Code's exact invocation pattern (--file - via stdin) lands ONE-attempt", () => {
    addOrphanGitlink();
    // VS Code uses: git -c user.useConfigOnly=true commit --quiet --allow-empty-message --file -
    // Pipe message via stdin
    const r = spawnSync("cmd", [
      "/c", SHIM_PATH,
      "-c", "user.useConfigOnly=true",
      "commit", "--quiet", "--allow-empty-message", "--file", "-",
    ], {
      encoding: "utf8",
      cwd: sandbox,
      input: "stdin-fed commit message\n",
    });
    if (r.status !== 0) {
      return `--file - path exit ${r.status}: stderr=${r.stderr?.trim()} stdout=${r.stdout?.trim()}`;
    }
    const log = spawnSync("git", ["log", "-1", "--format=%s"], {
      encoding: "utf8", cwd: sandbox,
    });
    if (!(log.stdout ?? "").includes("stdin-fed")) {
      return `commit did not include stdin message: ${log.stdout?.trim()}`;
    }
    return null;
  });
} finally {
  if (existsSync(sandbox)) rmSync(sandbox, { recursive: true, force: true });
}

// V1.8 live-check is exclusive: the sandbox tests above invoke the shim
// (test #4 etc.) which pollutes the log — that pollution made the V1.7
// --live PASS vacuously. So in --live mode we skip sandbox tests entirely
// (the early-exit below is unreachable because --live is checked first;
// retained as defensive guard).

// Report
console.log("\n═══ rescue-shim wiring verification ═══\n");
let failed = 0;
for (const r of results) {
  const tag = r.ok ? "✓ PASS" : "✗ FAIL";
  console.log(`  ${tag}  ${r.name}`);
  if (!r.ok) {
    console.log(`           └─ ${r.detail}`);
    failed++;
  }
}
console.log("");
console.log("Live wiring (VS Code → shim) NOT checked by this mode. To verify:");
console.log("  1. bun run scripts/verify-rescue-shim.ts --reset-log     # clean baseline");
console.log("  2. Do any git op in VS Code (commit click, source-control refresh)");
console.log("  3. bun run scripts/verify-rescue-shim.ts --live          # log-only check");
console.log("");
if (failed === 0) {
  console.log(`✓ ALL ${results.length} assertions passed.`);
  process.exit(0);
} else {
  console.log(`✗ ${failed}/${results.length} assertions failed. Wiring is NOT clean.`);
  process.exit(1);
}
