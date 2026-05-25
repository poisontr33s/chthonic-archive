#!/usr/bin/env bun
// @SID: SCRIPT_CHTHONIC_RESCUE_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: chthonic-rescue.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ (Pre-flight to git-chthonic.cmd shim — runs BEFORE git's commit snapshot)
// ║   └─◄ (Backstop in ci/run.ts V1.4 — same logic in pre-commit hook path)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * chthonic-rescue.ts — Standalone idempotent rescue for commit-impedance states.
 *
 * The structural problem this solves (V1.4 → V1.5 escalation):
 *   Git's commit-content snapshot is taken BEFORE the pre-commit hook runs.
 *   Hook-side `git rm --cached` of orphan gitlinks persists in the index but
 *   git ignores it for THAT commit attempt — "nothing to commit, working tree
 *   clean" aborts the commit. Second commit attempt picks up the staged
 *   deletion. Result: two-attempt commits for the orphan-gitlink case.
 *
 * V1.5 fix: this script runs BEFORE `git commit` is invoked (via the
 * git-chthonic.cmd shim wired to VS Code's git.path), so the rescue is in
 * the index when git takes its snapshot. One-attempt commits.
 *
 * Idempotency contract:
 *   - Detects only the "orphan gitlink" case (160000-mode in HEAD, no
 *     .gitmodules registration, dirty contents) — the bounded class V1.4
 *     also rescues. Proper submodules with .gitmodules are NEVER touched.
 *   - Silent on no-op (no output when nothing to rescue) — must not pollute
 *     every git commit invocation.
 *   - Exit 0 always — the shim continues to real git regardless.
 *   - Working-tree directories untouched; only index entries removed.
 *
 * Usage:
 *   bun run scripts/chthonic-rescue.ts           # verbose (manual invocation)
 *   bun run scripts/chthonic-rescue.ts --silent  # silent on no-op (shim mode)
 */

import { spawnSync } from "child_process";

// Use CWD (the workspace root when invoked from VS Code's git shim, or the
// directory the conductor runs the script from for manual invocation). Avoid
// hardcoding the script's parent directory — that would make the script
// always rescue chthonic-archive regardless of caller context, which breaks
// isolated testing and any future use in sibling repos.
const REPO_ROOT = process.cwd();
const SILENT = process.argv.includes("--silent");

function log(msg: string): void {
  if (!SILENT) console.log(msg);
}

function findOrphanGitlinks(): string[] {
  // Lowercase-`m ` ONLY — git's specific submodule-content-modified signal.
  // Capital ` M ` matches any modified-in-working-tree file (caught a pre-ship
  // bug in V1.4 where ci/run.ts itself got captured as "orphan gitlink"). The
  // 160000-mode verification below is a second-layer guard against regex drift.
  const status = spawnSync("git", ["status", "-s", "--ignore-submodules=none"], {
    encoding: "utf8",
    cwd: REPO_ROOT,
  });
  const lines = (status.stdout ?? "").split("\n").filter(Boolean);
  const dirty_paths = lines
    .filter((l) => /^\sm\s/.test(l) && l.length > 3)
    .map((l) => l.slice(3).trim());
  if (dirty_paths.length === 0) return [];

  // Verify each path is actually a 160000-mode gitlink in HEAD.
  const verified: string[] = [];
  for (const p of dirty_paths) {
    const ls = spawnSync("git", ["ls-tree", "HEAD", p], {
      encoding: "utf8",
      cwd: REPO_ROOT,
    });
    if ((ls.stdout ?? "").trim().startsWith("160000 ")) {
      verified.push(p);
    }
  }
  if (verified.length === 0) return [];

  // Orphan = NOT registered in .gitmodules. Proper submodules are excluded.
  const gm = spawnSync("git", ["config", "-f", ".gitmodules", "-l"], {
    encoding: "utf8",
    cwd: REPO_ROOT,
  });
  const gm_content = gm.stdout ?? "";
  return verified.filter(
    (p) => !gm_content.includes(`path=${p}`) && !gm_content.includes(`= ${p}`),
  );
}

function hasStagedContent(): boolean {
  // ACMRTD includes deletions (D) — covers the case where rescue already ran
  // and we're checking on a subsequent invocation. If anything is staged,
  // skip rescue entirely (don't over-reach into a commit with other content).
  const r = spawnSync(
    "git",
    ["diff", "--cached", "--name-only", "--diff-filter=ACMRTD"],
    { encoding: "utf8", cwd: REPO_ROOT },
  );
  return (r.stdout ?? "").split("\n").filter(Boolean).length > 0;
}

// Main: detect + rescue
const staged_has_content = hasStagedContent();
if (staged_has_content) {
  // Conductor is committing real content; do nothing.
  process.exit(0);
}

const orphans = findOrphanGitlinks();
if (orphans.length === 0) {
  // Nothing to rescue. Silent in shim mode.
  log("[rescue] no orphan gitlinks detected — nothing to rescue");
  process.exit(0);
}

log(`[rescue] ${orphans.length} orphan gitlink(s) detected with nothing else staged.`);
log(`[rescue]   These have 160000-mode entries in HEAD but no .gitmodules registration.`);
log(`[rescue]   Pre-staging removal so the commit can land in ONE attempt:`);
for (const p of orphans) {
  log(`[rescue]     - ${p}`);
}

const rm_result = spawnSync("git", ["rm", "--cached", ...orphans], {
  encoding: "utf8",
  cwd: REPO_ROOT,
});

if (rm_result.status === 0) {
  log(`[rescue]   ✓ Index updated. Working-tree directories untouched.`);
  log(`[rescue]   Undo before commit: git reset HEAD ${orphans.join(" ")}`);
} else {
  log(`[rescue]   ✗ rm --cached failed (exit ${rm_result.status}):`);
  log(((rm_result.stderr ?? "") + (rm_result.stdout ?? "")).trim());
}

process.exit(0);
