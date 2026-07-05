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
import { COMMON_SKIP_DIRS } from "./common_bloat_and_vendored";

const STAGED = process.argv.includes("--staged");
const FIX = process.argv.includes("--fix");
const REPO_ROOT = resolve(import.meta.dir, "../..");
const PASSIVE_MARKDOWN_PREFIXES = ["confiscated_instructions/"];
const INTERNAL_SKIP_DIRS = COMMON_SKIP_DIRS;

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

function normalizeRel(rel: string): string {
  return rel.replace(/\\/g, "/");
}

function isPassiveMarkdown(rel: string): boolean {
  const normalized = normalizeRel(rel);
  return PASSIVE_MARKDOWN_PREFIXES.some((prefix) => normalized.startsWith(prefix));
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
      // Strip UTF-8 BOM if present (some files are saved with BOM by editors).
      const clean = line.replace(/^﻿/, "");
      if (clean.trim() === "---") {
        if (inFrontmatter) return false;
        inFrontmatter = true;
        continue;
      }
      if (inFrontmatter) {
        const m = clean.match(/^\s*lifecycle\s*:\s*([\w-]+)/);
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

function isInternalSkip(rel: string): boolean {
  const normalized = normalizeRel(rel);
  return INTERNAL_SKIP_DIRS.some((dir) => normalized.startsWith(dir));
}

function existingMarkdown(paths: string[]): string[] {
  let passiveCount = 0;
  let internalSkipCount = 0;
  const active = paths
    .filter(isMarkdownPath)
    .filter((rel) => existsSync(resolve(REPO_ROOT, rel)))
    .filter((rel) => {
      if (isPassiveMarkdown(rel)) {
        passiveCount += 1;
        return false;
      }
      if (isInternalSkip(rel)) {
        internalSkipCount += 1;
        return false;
      }
      return true;
    })
    .filter((rel) => {
      if (isTombstone(rel)) {
        console.log(`[pathfinder] skipping tombstone: ${rel}`);
        return false;
      }
      return true;
    });

  if (passiveCount > 0) {
    console.log(`[pathfinder] skipping ${passiveCount} passive markdown file(s)`);
  }
  if (internalSkipCount > 0) {
    console.log(`[pathfinder] skipping ${internalSkipCount} internal-skip markdown file(s)`);
  }
  return active;
}

function hasStagedRenames(): boolean {
  const renames = gitLines(["diff", "--cached", "--name-status", "--diff-filter=R"]);
  let actionable = 0;
  let passive = 0;

  for (const line of renames) {
    const parts = line.split("\t");
    if (parts.length < 3) continue;
    const oldPath = normalizeRel(parts[1] ?? "");
    const newPath = normalizeRel(parts[2] ?? "");
    if (isPassiveMarkdown(oldPath) || isPassiveMarkdown(newPath)) {
      passive += 1;
    } else {
      actionable += 1;
    }
  }

  if (passive > 0) {
    console.log(`[pathfinder] staged renames: ${passive} passive confiscation rename(s) ignored`);
  }
  return actionable > 0;
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
  const changed = existingMarkdown(
    gitLines(["diff", "--name-only", "HEAD"])
  );
  if (changed.length > 0) {
    const args = ["scan", "--github-links", "--paths", ...changed];
    if (FIX) args.push("--fix");
    else args.push("--dry-run");
    ok = runLinkAudit("changed markdown", args) && ok;
  } else {
    console.log("[pathfinder] changed markdown: no files (after tombstone filtering)");
  }
}

process.exit(ok ? 0 : 1);
