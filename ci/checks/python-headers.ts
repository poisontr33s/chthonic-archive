#!/usr/bin/env bun
// @SID: CI_CHECK_PYTHON_HEADERS_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/checks/python-headers.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ci/checks/python-headers.ts — Python canonical header enforcement.
 *
 * Validates .py files for Metabolic Standard v3 headers:
 *   Line 1: #!/usr/bin/env python3
 *   Line 2: #-*- coding: utf-8 -*- (or #-*- coding: utf-8 -*-)
 *
 * Behavior:
 *   --staged  STRICT on Added files (exit 1). Advisory on Modified (exit 0).
 *   (default) Scan all tracked .py files — advisory report only (exit 0).
 *
 * Usage:
 *   bun run ci/checks/python-headers.ts           # audit all tracked files
 *   bun run ci/checks/python-headers.ts --staged  # pre-commit check
 */

import { execSync } from "child_process";
import { readFileSync } from "fs";
import { resolve } from "path";

const STAGED = process.argv.includes("--staged");
const REPO_ROOT = resolve(import.meta.dir, "../..");

const EXPECTED_SHEBANG = "#!/usr/bin/env python3";
// Both variants accepted:  #-*- coding: utf-8 -*-   and   # -*- coding: utf-8 -*-
const ENCODING_RE = /^#\s*-\*-\s*coding:\s*utf-8\s*-\*-/;

const EXCLUDE_DIRS = new Set([
  "node_modules", "target", "build", ".git", "__pycache__",
  ".venv", "venv", ".uv",
]);

function getPyFiles(diffFilter: string): string[] {
  try {
    const out = execSync(
      `git diff --cached --name-only --diff-filter=${diffFilter}`,
      { encoding: "utf8", cwd: REPO_ROOT }
    );
    return out
      .split("\n")
      .filter((f) => f.endsWith(".py") && f.trim().length > 0)
      .filter((f) => !EXCLUDE_DIRS.has(f.split("/")[0]))
      .map((f) => resolve(REPO_ROOT, f));
  } catch {
    return [];
  }
}

function getTrackedPyFiles(): string[] {
  try {
    const out = execSync("git ls-files", { encoding: "utf8", cwd: REPO_ROOT });
    return out
      .split("\n")
      .filter((f) => f.endsWith(".py") && f.trim().length > 0)
      .filter((f) => !EXCLUDE_DIRS.has(f.split("/")[0]))
      .map((f) => resolve(REPO_ROOT, f));
  } catch {
    return [];
  }
}

// Distinguishes CLI scripts (need shebang + encoding) from importable library modules
// (no shebang expected — invoked via `python -m pkg` or `import`). Heuristic:
//   - Library (false): __init__.py OR path contains /src/ (package source root)
//   - CLI by convention (true): path under scripts/ or probes/
//   - CLI by signal (true): has `if __name__ == "__main__":` block
//   - Default when ambiguous: treat as CLI (conservative — flag potential drift)
function isCliScript(absPath: string, content: string): boolean {
  const normalized = absPath.replace(/\\/g, "/");
  const basename = normalized.split("/").pop() ?? "";

  if (basename === "__init__.py") return false;
  if (/\/src\//.test(normalized)) return false;

  if (/\/(scripts|probes)\//.test(normalized)) return true;
  if (/^if\s+__name__\s*==\s*['"]__main__['"]/m.test(content)) return true;

  return true;
}

function checkFile(absPath: string): string[] {
  let content: string;
  try {
    content = readFileSync(absPath, "utf8");
  } catch {
    return [];
  }

  // Strip CR for CRLF-encoded files before comparison
  const lines = content.split("\n").map((l) => l.replace(/\r$/, ""));
  const line1 = lines[0] ?? "";
  const line2 = lines[1] ?? "";
  const issues: string[] = [];

  const isCli = isCliScript(absPath, content);

  // Library modules (e.g. __init__.py, files in */src/*) are exempt from
  // shebang + encoding enforcement — they're imported, not executed.
  // Exception: if a library carries a partial encoding declaration, flag malformations.
  if (isCli) {
    if (line1 !== EXPECTED_SHEBANG) {
      issues.push(`Line 1: expected '${EXPECTED_SHEBANG}', got '${line1.slice(0, 70)}'`);
    }
    if (!ENCODING_RE.test(line2)) {
      issues.push(
        `Line 2: expected encoding declaration, got '${line2.slice(0, 70)}'`
      );
    }
  } else {
    const top5 = lines.slice(0, 5);
    const encLine = top5.find((l) => l.startsWith("#") && /coding/.test(l));
    if (encLine && !ENCODING_RE.test(encLine)) {
      issues.push(
        `Encoding declaration malformed (library): got '${encLine.slice(0, 70)}'`
      );
    }
  }
  return issues;
}

function relPath(abs: string): string {
  return abs.replace(REPO_ROOT + "/", "").replace(REPO_ROOT + "\\", "");
}

if (STAGED) {
  // Added files: STRICT (exit 1 on violation — new files must comply)
  const addedFiles = getPyFiles("A");
  const addedViolations: { file: string; issues: string[] }[] = [];
  for (const f of addedFiles) {
    const issues = checkFile(f);
    if (issues.length) addedViolations.push({ file: relPath(f), issues });
  }

  // Modified files: ADVISORY (exit 0, just report)
  const modifiedFiles = getPyFiles("CM");
  const modifiedViolations: { file: string; issues: string[] }[] = [];
  for (const f of modifiedFiles) {
    const issues = checkFile(f);
    if (issues.length) modifiedViolations.push({ file: relPath(f), issues });
  }

  if (modifiedViolations.length > 0) {
    console.log(
      `[python-headers] ℹ ${modifiedViolations.length} modified file(s) have non-canonical headers (advisory):`
    );
    for (const v of modifiedViolations) {
      console.log(`  ${v.file}`);
    }
  }

  if (addedViolations.length === 0) {
    const total = addedFiles.length + modifiedFiles.length;
    console.log(
      `[python-headers] ✓ No header violations in ${total} staged .py file(s)`
    );
    process.exit(0);
  } else {
    console.error(
      `[python-headers] ✗ ${addedViolations.length} new file(s) missing canonical headers:`
    );
    for (const v of addedViolations) {
      console.error(`  ${v.file}:`);
      for (const issue of v.issues) {
        console.error(`    - ${issue}`);
      }
    }
    console.error(
      `\n  Fix: Line 1 = '#!/usr/bin/env python3'  |  Line 2 = '# -*- coding: utf-8 -*-'`
    );
    console.error(
      `  Library modules (__init__.py, *.py inside */src/*) are exempt from the shebang check.`
    );
    process.exit(1);
  }
} else {
  // Default: full tracked audit, advisory (exit 0)
  const files = getTrackedPyFiles();
  const violations: { file: string; issues: string[] }[] = [];
  for (const f of files) {
    const issues = checkFile(f);
    if (issues.length) violations.push({ file: relPath(f), issues });
  }

  if (violations.length === 0) {
    console.log(
      `[python-headers] ✓ No header violations in ${files.length} tracked .py file(s)`
    );
  } else {
    console.log(
      `[python-headers] ℹ ${violations.length}/${files.length} tracked .py file(s) have non-canonical headers:`
    );
    for (const v of violations) {
      console.log(`  ${v.file}: ${v.issues.join(" | ")}`);
    }
    console.log(
      `\n  These are advisory. Run 'bun run ci:check python-headers' to audit.`
    );
  }
  process.exit(0);
}
