#!/usr/bin/env bun
// @SID: CI_CHECK_GLSL_LINT_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/checks/glsl-lint.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ (Enforcement: staged assets/shaders/* files compile clean under glslangValidator)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ci/checks/glsl-lint.ts — validate GLSL shaders via glslangValidator (Vulkan SDK).
 *
 * Catches syntax/semantic shader errors at commit time instead of at the next
 * `cargo build` (shaderc runs the same compiler at build.rs time — see
 * build.rs's own `set_target_env(Vulkan, Vulkan1_3)`, mirrored here via
 * `--target-env vulkan1.3` so both compiles agree). Scoped to assets/shaders/
 * only (the sole place shader source lives in this repo).
 *
 * --staged: STRICT on both Added and Modified files (exit 1) — unlike most
 *   staged-scope checks in this registry, a shader compile error is a real
 *   defect regardless of whether the file is new or edited, not a style
 *   convention that only matters for newly-introduced code.
 * default:  Advisory scan of all tracked shader files (exit 0).
 *
 * Found via a reference-repo scouting pass (linear-mapping-rain.md Meta-track
 * M2): vscode-glsllint's entire "linter" is a thin wrapper around shelling out
 * to this same glslangValidator binary and parsing its stdout — this check
 * reuses that shape directly rather than porting the VS Code extension itself.
 */

import { spawnSync } from "child_process";
import { existsSync } from "fs";
import { resolve } from "path";

const STAGED = process.argv.includes("--staged");
const REPO_ROOT = resolve(import.meta.dir, "../..");
const SHADER_DIR = "assets/shaders/";
const TARGET_ENV = "vulkan1.3"; // must match build.rs's shaderc::EnvVersion::Vulkan1_3

const TARGET_EXTENSIONS = new Set([
  ".vert", ".frag", ".comp", ".geom", ".tesc", ".tese",
  ".rgen", ".rint", ".rahit", ".rchit", ".rmiss", ".rcall",
  ".mesh", ".task",
]);

function hasTargetExtension(f: string): boolean {
  const dot = f.lastIndexOf(".");
  return dot !== -1 && TARGET_EXTENSIONS.has(f.slice(dot));
}

function isShaderPath(rel: string): boolean {
  return rel.replace(/\\/g, "/").includes(SHADER_DIR) && hasTargetExtension(rel);
}

function getStagedFiles(diffFilter: string): string[] {
  const r = spawnSync(
    "git",
    ["diff", "--cached", "--name-only", `--diff-filter=${diffFilter}`],
    { encoding: "utf8", cwd: REPO_ROOT }
  );
  return (r.stdout ?? "")
    .split("\n")
    .filter(Boolean)
    .filter(isShaderPath)
    .map((f) => resolve(REPO_ROOT, f));
}

function getTrackedFiles(): string[] {
  const r = spawnSync("git", ["ls-files"], { encoding: "utf8", cwd: REPO_ROOT });
  return (r.stdout ?? "")
    .split("\n")
    .filter(Boolean)
    .filter(isShaderPath)
    .map((f) => resolve(REPO_ROOT, f));
}

function relPath(absPath: string): string {
  return absPath.replace(REPO_ROOT + "\\", "").replace(REPO_ROOT + "/", "");
}

type ValidateResult = { ok: boolean; toolMissing: boolean; diagnostics: string[] };

/** Runs glslangValidator on one file, parses ERROR/WARNING lines from its stdout. */
function validateFile(filePath: string): ValidateResult {
  const r = spawnSync("glslangValidator", ["--target-env", TARGET_ENV, filePath], {
    encoding: "utf8",
  });

  if (r.error && (r.error as NodeJS.ErrnoException).code === "ENOENT") {
    return { ok: true, toolMissing: true, diagnostics: [] };
  }

  const lines = (r.stdout ?? "").split("\n");
  const diagnostics = lines.filter((l) => /^(ERROR|WARNING):/.test(l.trim()));
  return { ok: r.status === 0, toolMissing: false, diagnostics };
}

let exitCode = 0;
let totalErrors = 0;
let toolMissing = false;

function report(files: string[], strict: boolean) {
  for (const f of files) {
    if (!existsSync(f)) continue;
    const result = validateFile(f);
    if (result.toolMissing) {
      toolMissing = true;
      continue;
    }
    if (!result.ok) {
      const tag = strict ? "✗ STRICT" : "⚠ advisory";
      const log = strict ? console.error : console.warn;
      log(`[glsl-lint] ${tag} ${relPath(f)}`);
      for (const d of result.diagnostics) log(`  ${d.trim()}`);
      totalErrors++;
      if (strict) exitCode = 1;
    }
  }
}

if (STAGED) {
  report(getStagedFiles("A"), true);
  report(getStagedFiles("M"), true);
} else {
  report(getTrackedFiles(), false);
}

if (toolMissing) {
  console.warn(
    "[glsl-lint] ⚠ glslangValidator not found on PATH (expected via Vulkan SDK) — skipped, not failed"
  );
} else if (totalErrors === 0) {
  console.log(
    STAGED
      ? "[glsl-lint] ✓ staged: all shaders compile clean"
      : "[glsl-lint] ✓ all tracked shaders compile clean"
  );
}

process.exit(exitCode);
