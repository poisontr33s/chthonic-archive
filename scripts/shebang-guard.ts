#!/usr/bin/env bun
// @SID: SCRIPT_SHEBANG_GUARD_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: shebang-guard.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ (Standalone — invoked by pre-commit hook and lint:shebang)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * shebang-guard.ts — Detects displaced shebangs in TypeScript, Python, and shell files.
 *
 * For .ts files: a "displaced shebang" is any file where:
 *   - Line 1 is NOT "#!/usr/bin/env bun"
 *   - Line 2 IS "#!/usr/bin/env bun"
 *
 * For .py files: checks that:
 *   - Line 1 is "#!/usr/bin/env python3" (if a shebang is present anywhere in first 3 lines)
 *   - Line 2 is a UTF-8 coding declaration (with or without spacing around -*-)
 *
 * For .sh files: checks that:
 *   - Line 1 is a valid bash shebang (#!/usr/bin/env bash or #!/bin/bash)
 *   - Displaced: shebang NOT on line 1, but IS on line 2
 *
 * Usage:
 *   bun run scripts/shebang-guard.ts           # check all tracked files
 *   bun run scripts/shebang-guard.ts --staged  # check only git-staged files
 *   bun run scripts/shebang-guard.ts --all     # check all files (inc. untracked)
 */

import { execSync } from "child_process";
import { readFileSync, readdirSync, statSync } from "fs";
import { resolve, join, relative } from "path";

const STAGED = process.argv.includes("--staged");
const ALL = process.argv.includes("--all");
const REPO_ROOT = resolve(import.meta.dir, "..");

// Files/dirs to exclude from --all scan
const EXCLUDE_DIRS = new Set(["node_modules", "target", "build", ".git", "__pycache__"]);
const SCAN_EXTENSIONS = new Set([".ts", ".py", ".sh"]);

function getStagedFiles(): string[] {
  try {
    const out = execSync("git diff --cached --name-only --diff-filter=ACM", {
      encoding: "utf8",
      cwd: REPO_ROOT,
    });
    return out
      .split("\n")
      .filter((f) => {
        if (!f.length) return false;
        const ext = f.slice(f.lastIndexOf("."));
        return (ext === ".ts" && !f.endsWith(".d.ts")) || ext === ".py" || ext === ".sh";
      })
      .map((f) => resolve(REPO_ROOT, f));
  } catch {
    return [];
  }
}

function getTrackedFiles(): string[] {
  try {
    const out = execSync("git ls-files", {
      encoding: "utf8",
      cwd: REPO_ROOT,
    });
    return out
      .split("\n")
      .filter((f) => {
        if (!f.length) return false;
        const ext = f.slice(f.lastIndexOf("."));
        return (ext === ".ts" && !f.endsWith(".d.ts")) || ext === ".py" || ext === ".sh";
      })
      .map((f) => resolve(REPO_ROOT, f));
  } catch {
    return [];
  }
}

function walkFiles(dir: string, found: string[] = []): string[] {
  let entries: string[];
  try {
    entries = readdirSync(dir);
  } catch {
    return found;
  }
  for (const entry of entries) {
    if (EXCLUDE_DIRS.has(entry)) continue;
    const full = join(dir, entry);
    let stat;
    try {
      stat = statSync(full);
    } catch {
      continue;
    }
    if (stat.isDirectory()) {
      walkFiles(full, found);
    } else {
      const ext = entry.slice(entry.lastIndexOf("."));
      if (SCAN_EXTENSIONS.has(ext) && !entry.endsWith(".d.ts")) {
        found.push(full);
      }
    }
  }
  return found;
}

const files: string[] = STAGED
  ? getStagedFiles()
  : ALL
  ? walkFiles(REPO_ROOT)
  : getTrackedFiles();

const TS_SHEBANG = "#!/usr/bin/env bun";
const PY_SHEBANG = "#!/usr/bin/env python3";
const PY_ENCODING_RE = /^#\s*-\*-\s*coding:\s*utf-8\s*-\*-/;
const SH_SHEBANGS = new Set(["#!/usr/bin/env bash", "#!/bin/bash", "#!/usr/bin/env sh", "#!/bin/sh"]);

const violations: { path: string; line1: string; issue: string }[] = [];

for (const absPath of files) {
  let content: string;
  try {
    content = readFileSync(absPath, "utf8");
  } catch {
    continue;
  }
  const lines = content.split("\n");
  if (lines.length < 2) continue;
  const line1 = lines[0].trimEnd();
  const line2 = lines[1].trimEnd();
  const ext = absPath.slice(absPath.lastIndexOf("."));

  if (ext === ".ts") {
    // Displaced: shebang NOT on line 1, shebang IS on line 2
    if (line1 !== TS_SHEBANG && line2 === TS_SHEBANG) {
      violations.push({ path: relative(REPO_ROOT, absPath), line1, issue: "displaced shebang (line 2)" });
    }
  } else if (ext === ".py") {
    const hasPyShebangAnywhere = [line1, line2, (lines[2] ?? "").trimEnd()].some((l) => l === PY_SHEBANG);
    if (hasPyShebangAnywhere) {
      if (line1 !== PY_SHEBANG && line2 === PY_SHEBANG) {
        violations.push({ path: relative(REPO_ROOT, absPath), line1, issue: "displaced shebang (line 2)" });
      } else if (line1 === PY_SHEBANG && !PY_ENCODING_RE.test(line2)) {
        violations.push({ path: relative(REPO_ROOT, absPath), line1, issue: `missing encoding on line 2 (got: "${line2.slice(0, 40)}")` });
      }
    }
  } else if (ext === ".sh") {
    const hasSh = SH_SHEBANGS.has(line1) || SH_SHEBANGS.has(line2);
    if (hasSh && !SH_SHEBANGS.has(line1) && SH_SHEBANGS.has(line2)) {
      violations.push({ path: relative(REPO_ROOT, absPath), line1, issue: "displaced shebang (line 2)" });
    }
  }
}

if (violations.length > 0) {
  console.error(`\n[shebang-guard] \u274C ${violations.length} file(s) with shebang violations:\n`);
  for (const v of violations) {
    console.error(`  ${v.path}`);
    console.error(`    line 1: "${v.line1.slice(0, 72)}"`);
    console.error(`    issue:  ${v.issue}`);
  }
  console.error(`
Fix: \u23E9 move shebang to line 1.
     .ts: #!/usr/bin/env bun
     .py: #!/usr/bin/env python3 on line 1, # -*- coding: utf-8 -*- on line 2.
     .sh: #!/usr/bin/env bash on line 1.
     All content (@SID:, envelope blocks) comes AFTER.
`);
  process.exit(1);
} else {
  const scope = STAGED ? "staged" : ALL ? "all" : "tracked";
  console.log(`[shebang-guard] \u2713 No shebang violations in ${files.length} ${scope} file(s)`);
  process.exit(0);
}
