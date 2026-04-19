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
 * shebang-guard.ts — Detects displaced shebangs in TypeScript files.
 *
 * A "displaced shebang" is any .ts file where:
 *   - Line 1 is NOT "#!/usr/bin/env bun"
 *   - Line 2 IS "#!/usr/bin/env bun"
 *
 * This is caused by agents placing // @SID: or other comments on line 1,
 * pushing the shebang to line 2. Bun treats this as a SyntaxError.
 *
 * Usage:
 *   bun run scripts/shebang-guard.ts           # check all tracked .ts files
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

function getStagedTsFiles(): string[] {
  try {
    const out = execSync("git diff --cached --name-only --diff-filter=ACM", {
      encoding: "utf8",
      cwd: REPO_ROOT,
    });
    return out
      .split("\n")
      .filter((f) => f.endsWith(".ts") && !f.endsWith(".d.ts") && f.length > 0)
      .map((f) => resolve(REPO_ROOT, f));
  } catch {
    return [];
  }
}

function getTrackedTsFiles(): string[] {
  try {
    const out = execSync("git ls-files", {
      encoding: "utf8",
      cwd: REPO_ROOT,
    });
    return out
      .split("\n")
      .filter((f) => f.endsWith(".ts") && !f.endsWith(".d.ts") && f.length > 0)
      .map((f) => resolve(REPO_ROOT, f));
  } catch {
    return [];
  }
}

function walkTs(dir: string, found: string[] = []): string[] {
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
      walkTs(full, found);
    } else if (entry.endsWith(".ts") && !entry.endsWith(".d.ts")) {
      found.push(full);
    }
  }
  return found;
}

const files: string[] = STAGED
  ? getStagedTsFiles()
  : ALL
  ? walkTs(REPO_ROOT)
  : getTrackedTsFiles();

const violations: { path: string; line1: string }[] = [];

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
  // Displaced: shebang NOT on line 1, shebang IS on line 2
  if (line1 !== "#!/usr/bin/env bun" && line2 === "#!/usr/bin/env bun") {
    violations.push({ path: relative(REPO_ROOT, absPath), line1 });
  }
}

if (violations.length > 0) {
  console.error(`\n[shebang-guard] \u274C ${violations.length} file(s) with displaced shebangs:\n`);
  for (const v of violations) {
    console.error(`  ${v.path}`);
    console.error(`    line 1: "${v.line1.slice(0, 72)}"`);
  }
  console.error(`
Fix: \u23E9 move #!/usr/bin/env bun to line 1.
     All content (// @SID:, envelope blocks) comes AFTER the shebang.
     Library modules (non-CLI src/ files) omit the shebang entirely.
`);
  process.exit(1);
} else {
  const scope = STAGED ? "staged" : ALL ? "all" : "tracked";
  console.log(`[shebang-guard] \u2713 No displaced shebangs in ${files.length} ${scope} .ts file(s)`);
  process.exit(0);
}
