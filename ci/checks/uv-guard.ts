#!/usr/bin/env bun
// @SID: CI_CHECK_UV_GUARD_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/checks/uv-guard.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ (Enforcement: no bare python/python3 — use uv run)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ci/checks/uv-guard.ts — block bare python/python3 invocations.
 *
 * Scans .py, .sh, .ps1, .ts files for raw `python`/`python3` calls not
 * prefixed with `uv run`. This enforces the repo-wide mandate: all Python
 * execution flows through `uv run <script>`.
 *
 * --staged: STRICT on Added files (exit 1), advisory on Modified (exit 0).
 * default:  Advisory scan of all tracked scripts (exit 0).
 *
 * Allowances (not flagged):
 *   - Lines starting with # or // (comments)
 *   - Shebangs: #!/usr/bin/env python3
 *   - Lines containing `uv` (uv run python3, uv pip, etc.)
 *   - PowerShell <# block comments #>
 *   - sys.executable references
 *   - String-only mentions (import, require, etc.)
 */

import { spawnSync } from "child_process";
import { readFileSync, existsSync } from "fs";
import { resolve } from "path";

const STAGED = process.argv.includes("--staged");
const REPO_ROOT = resolve(import.meta.dir, "../..");

const TARGET_EXTENSIONS = new Set([".py", ".sh", ".ps1", ".ts"]);

const EXCLUDE_DIRS = new Set([
  "node_modules",
  "target",
  ".venv",
  "venv",
  ".git",
  "dist",
  ".output",
  "build",
  ".cache",
  "__pycache__",
  "dumpster-dive",
  ".deprecated",
  "artifacts",
  "confiscated_instructions",
]);

/** Skip the guard script itself and uv wrapper utilities. */
function isSelf(rel: string): boolean {
  return (
    rel.includes("uv-guard") ||
    rel.replace(/\\/g, "/").endsWith("ci/checks/uv-guard.ts")
  );
}

function hasTargetExtension(f: string): boolean {
  const dot = f.lastIndexOf(".");
  return dot !== -1 && TARGET_EXTENSIONS.has(f.slice(dot));
}

function isExcluded(rel: string): boolean {
  return rel.split(/[/\\]/).some((part) => EXCLUDE_DIRS.has(part));
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
    .filter(hasTargetExtension)
    .filter((f) => !isExcluded(f))
    .filter((f) => !isSelf(f))
    .map((f) => resolve(REPO_ROOT, f));
}

function getTrackedFiles(): string[] {
  const r = spawnSync("git", ["ls-files"], {
    encoding: "utf8",
    cwd: REPO_ROOT,
  });
  return (r.stdout ?? "")
    .split("\n")
    .filter(Boolean)
    .filter(hasTargetExtension)
    .filter((f) => !isExcluded(f))
    .filter((f) => !isSelf(f))
    .map((f) => resolve(REPO_ROOT, f));
}

/** Returns lines in the file that are bare python/python3 invocations. */
function checkFile(
  filePath: string
): Array<{ lineNo: number; line: string }> {
  let content: string;
  try {
    content = readFileSync(filePath, "utf8");
  } catch {
    return [];
  }

  const violations: Array<{ lineNo: number; line: string }> = [];
  const lines = content.split("\n");

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const stripped = line.trimStart();

    // Skip blank lines
    if (!stripped) continue;

    // Skip single-line comments (shell/Python/PowerShell)
    if (
      stripped.startsWith("#") ||
      stripped.startsWith("//") ||
      stripped.startsWith("<#")
    )
      continue;

    // Skip shebangs
    if (stripped.startsWith("#!/")) continue;

    // Skip lines that already use uv (uv run, uv pip, etc.)
    if (/\buv\b/.test(line)) continue;

    // Skip lines that are only string/comment references (import, require, etc.)
    // Heuristic: line contains python keyword but only in a string or import context
    if (
      /^\s*(import|from|require|#|\/\/|"python|'python|`python)/.test(line)
    )
      continue;

    // Detect violations:
    // 1. Bare shell invocation: line starts with python / python3 + space + arg
    const bareShell = /^\s*python3?\s+\S/.test(line);

    // 2. PowerShell ampersand-call: & python3? ...
    const psAmpersand = /&\s+python3?\b/.test(line);

    // 3. spawnSync/spawn/exec with "python"/"python3" as first argument
    const spawnCall =
      /(?:spawnSync|spawn|execSync|exec)\s*\(\s*["'`]python3?["'`]/.test(
        line
      );

    // 4. subprocess.run / subprocess.call / os.system with bare python
    const subprocessBare =
      /subprocess\.(run|call|Popen|check_output)\s*\(\s*\[?\s*["']python3?["']/.test(
        line
      );

    if (bareShell || psAmpersand || spawnCall || subprocessBare) {
      violations.push({ lineNo: i + 1, line: line.trimEnd() });
    }
  }

  return violations;
}

function relPath(absPath: string): string {
  return absPath
    .replace(REPO_ROOT + "\\", "")
    .replace(REPO_ROOT + "/", "");
}

let exitCode = 0;
let totalViolations = 0;

if (STAGED) {
  // Strict: Added files exit 1
  const added = getStagedFiles("A");
  for (const f of added) {
    if (!existsSync(f)) continue;
    const hits = checkFile(f);
    if (hits.length > 0) {
      console.error(`[uv-guard] ✗ STRICT ${relPath(f)}`);
      for (const h of hits) {
        console.error(`  line ${h.lineNo}: ${h.line}`);
      }
      totalViolations += hits.length;
      exitCode = 1;
    }
  }

  // Advisory: Modified files warn but don't fail
  const modified = getStagedFiles("M");
  for (const f of modified) {
    if (!existsSync(f)) continue;
    const hits = checkFile(f);
    if (hits.length > 0) {
      console.warn(`[uv-guard] ⚠ advisory ${relPath(f)}`);
      for (const h of hits) {
        console.warn(`  line ${h.lineNo}: ${h.line}`);
      }
      totalViolations += hits.length;
    }
  }

  if (totalViolations === 0) {
    console.log("[uv-guard] ✓ staged: no bare python invocations");
  }
} else {
  // Default: advisory scan of all tracked scripts (exit 0)
  const tracked = getTrackedFiles();
  for (const f of tracked) {
    if (!existsSync(f)) continue;
    const hits = checkFile(f);
    if (hits.length > 0) {
      console.warn(`[uv-guard] ⚠ advisory ${relPath(f)}`);
      for (const h of hits) {
        console.warn(`  line ${h.lineNo}: ${h.line}`);
      }
      totalViolations += hits.length;
    }
  }

  if (totalViolations === 0) {
    console.log("[uv-guard] ✓ no bare python invocations found");
  } else {
    console.warn(
      `[uv-guard] ⚠ ${totalViolations} advisory violation(s) — fix before committing new files`
    );
  }
}

process.exit(exitCode);
