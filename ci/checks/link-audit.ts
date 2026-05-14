#!/usr/bin/env bun
// @SID: CI_CHECK_LINK_AUDIT_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/checks/link-audit.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ (Enforcement: Pathfinder markdown path/anchor/line links)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ci/checks/link-audit.ts - Pathfinder local CI wrapper for scripts/link_audit.py.
 *
 * --staged: Audit staged markdown files and staged renames.
 * default:  Audit markdown files changed vs HEAD.
 *
 * The Python tool owns markdown semantics; this wrapper only narrows the file
 * set so pre-commit stays fast and runs in the same lane as the shebang guard.
 * GitHub/GFM URL shape checks are offline; live issue/asset checks stay opt-in.
 */

import { existsSync, readFileSync } from "fs";
import { resolve } from "path";
import { spawnSync } from "child_process";

const STAGED = process.argv.includes("--staged");
const REPO_ROOT = resolve(import.meta.dir, "../..");

function gitLines(args: string[]): string[] {
  const result = spawnSync("git", args, {
    cwd: REPO_ROOT,
    encoding: "utf8",
  });
  if (result.status !== 0) return [];
  return (result.stdout ?? "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function isMarkdownPath(rel: string): boolean {
  return rel.toLowerCase().endsWith(".md");
}

// Lifecycle values that exclude a file from active link auditing.
// - tombstone: dead artifact, preserved for history
// - ssot-canon: macro-prompt-world / frozen unabridged source from which
//   slimmed downstream files are derived. Scanning refs on the SSOT
//   itself inverts the dependency direction (downstream inherits from
//   here; the SSOT does not depend on them).
const EXCLUDED_LIFECYCLES = new Set(["tombstone", "ssot-canon"]);

function isTombstone(rel: string): boolean {
  // Honor `lifecycle: <value>` in YAML frontmatter for any value in
  // EXCLUDED_LIFECYCLES. Name kept for backwards compatibility — the
  // predicate now covers both tombstones (dead) and ssot-canon (frozen
  // macro-prompt source). See manifest/git_rot_index.md for the taxonomy.
  // Frontmatter sits in the first ~30 lines if present.
  try {
    const abs = resolve(REPO_ROOT, rel);
    const head = readFileSync(abs, { encoding: "utf8" }).split("\n").slice(0, 30);
    let inFrontmatter = false;
    for (const line of head) {
      if (line.trim() === "---") {
        if (inFrontmatter) return false;
        inFrontmatter = true;
        continue;
      }
      if (inFrontmatter) {
        const m = line.match(/^\s*lifecycle\s*:\s*([\w-]+)/);
        if (m && EXCLUDED_LIFECYCLES.has(m[1])) {
          return true;
        }
      }
    }
  } catch {
    // Unreadable file: don't claim excluded, let audit handle it.
  }
  return false;
}

function existingMarkdown(paths: string[]): string[] {
  return paths
    .filter(isMarkdownPath)
    .filter((rel) => existsSync(resolve(REPO_ROOT, rel)))
    .filter((rel) => {
      if (isTombstone(rel)) {
        console.log(`[pathfinder] skipping tombstone: ${rel}`);
        return false;
      }
      return true;
    });
}

function hasStagedRenames(): boolean {
  return gitLines(["diff", "--cached", "--name-status", "--diff-filter=R"]).length > 0;
}

function runLinkAudit(label: string, args: string[]): boolean {
  const result = spawnSync("uv", ["run", "scripts/link_audit.py", ...args], {
    cwd: REPO_ROOT,
    encoding: "utf8",
    env: { ...process.env, PYTHONIOENCODING: "utf-8" },
  });

  const output = ((result.stdout ?? "") + (result.stderr ?? "")).trim();
  if (output) console.log(output);

  if (result.error) {
    console.error(`[pathfinder] ${label}: failed to launch uv: ${result.error.message}`);
    return false;
  }

  // Severity policy: BROKEN and EMPTY are hard errors. AMBIG / LINE / ANCHOR /
  // DIR / LABEL are warnings — print them, but don't block the commit. The
  // audit tool itself stays strict for diagnostic runs; this wrapper softens
  // only the gate. Rationale: a 2026-05-13 triage showed 140 of 167 AMBIG
  // flags resolve to real files (basename collisions, not actual breakage).
  const hasHardError = /\[BROKEN\]|\[EMPTY\]/.test(output);
  if (hasHardError) {
    console.error(`[pathfinder] ${label}: failed (broken/empty links present)`);
    return false;
  }
  if (result.status !== 0) {
    // Non-zero exit but no BROKEN/EMPTY in output — likely AMBIG-only.
    // Print a banner so the user knows softening kicked in.
    if (/\[AMBIG\]|\[LINE\]|\[ANCHOR\]|\[DIR\]|\[LABEL\]/.test(output)) {
      console.warn(`[pathfinder] ${label}: warnings present (AMBIG/LINE/ANCHOR/DIR/LABEL) — not blocking`);
      return true;
    }
    console.error(`[pathfinder] ${label}: failed (exit ${result.status}, no severity markers in output)`);
    return false;
  }
  return true;
}

let ok = true;

if (STAGED) {
  const staged = existingMarkdown(
    gitLines(["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
  );

  if (staged.length > 0) {
    ok = runLinkAudit("staged markdown", ["scan", "--dry-run", "--github-links", "--paths", ...staged]) && ok;
  } else {
    console.log("[pathfinder] staged markdown: no files");
  }

  if (hasStagedRenames()) {
    ok = runLinkAudit("staged renames", ["renames", "--staged", "--dry-run"]) && ok;
  } else {
    console.log("[pathfinder] staged renames: none");
  }
} else {
  ok = runLinkAudit("changed markdown", ["scan", "--changed", "--dry-run", "--github-links"]) && ok;
}

process.exit(ok ? 0 : 1);
