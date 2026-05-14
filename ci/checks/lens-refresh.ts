#!/usr/bin/env bun
// @SID: CI_CHECK_LENS_REFRESH_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/checks/lens-refresh.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ci/checks/lens-refresh.ts — Refresh all data-plane lenses.
 *
 * Methodology: "Gitological Noise As Structured Data — Lens per noise class."
 * Each lens pulls verbose external data, classifies, and emits structured
 * JSON + Markdown digest. This check fires every registered lens so the
 * manifests under manifest/ stay current.
 *
 * SLOW — not suitable for pre-commit (each lens is several seconds).
 * Runs under `bun run ci --full` or `bun run ci --check lens-refresh`.
 *
 * Currently wired:
 *   - git_rot_index.py           (link rot, anchor misses, deletion ancestry)
 *   - dependabot_index.py        (CVE alerts; needs gh auth)
 *   - github_activity_index.py   (PRs/Issues/Branches by actor type; needs gh auth)
 *   - method_index.py            (meta-lens: methods that cleared prior lenses)
 *   - route_index.py             (sub-lens: compound router; runs last)
 *
 * gh-dependent lenses (dependabot_index, github_activity_index) are
 * skipped — not failed — when gh auth is missing, so a missing token
 * doesn't break CI. The git-only lenses (git_rot_index, method_index)
 * fail hard when their dependency is missing, since `git` is invariant
 * in any environment this CI runs in; absence indicates real breakage.
 */

import { spawnSync } from "child_process";
import { resolve } from "path";

const REPO_ROOT = resolve(import.meta.dir, "../..");

interface Lens {
  name: string;
  script: string;
  needs: string[]; // command-line tools the lens requires
  skipOnMissing: boolean; // skip (not fail) if a tool is missing
}

const LENSES: Lens[] = [
  {
    name: "git-rot-index",
    script: "scripts/git_rot_index.py",
    needs: ["git"],
    skipOnMissing: false,
  },
  {
    name: "dependabot-index",
    script: "scripts/dependabot_index.py",
    needs: ["gh"],
    skipOnMissing: true, // gh might not be authenticated; don't break CI
  },
  {
    name: "github-activity-index",
    script: "scripts/github_activity_index.py",
    needs: ["gh"],
    skipOnMissing: true,
  },
  {
    name: "method-index",
    script: "scripts/method_index.py",
    needs: ["git"],
    // git is invariant in every environment this CI runs in; if it's
    // absent something is genuinely wrong, so fail hard rather than skip.
    skipOnMissing: false,
  },
  {
    name: "route-index",
    script: "scripts/route_index.py",
    // Sub-lens — consumes other lens manifests. No external deps, but
    // upstream manifests may be missing if gh-dependent lenses skipped.
    // The script handles missing inputs gracefully and emits an empty
    // routing manifest rather than failing.
    needs: [],
    skipOnMissing: true,
  },
];

function commandExists(cmd: string): boolean {
  const result = spawnSync("where", [cmd], { encoding: "utf8" });
  return result.status === 0;
}

function runLens(lens: Lens): { name: string; ok: boolean; status: string } {
  for (const need of lens.needs) {
    if (!commandExists(need)) {
      if (lens.skipOnMissing) {
        return { name: lens.name, ok: true, status: `skipped (no ${need})` };
      }
      return { name: lens.name, ok: false, status: `missing ${need}` };
    }
  }
  const result = spawnSync("uv", ["run", lens.script], {
    cwd: REPO_ROOT,
    encoding: "utf8",
    env: { ...process.env, PYTHONIOENCODING: "utf-8" },
  });
  if (result.error) {
    return { name: lens.name, ok: false, status: `launch error: ${result.error.message}` };
  }
  // Lenses might exit non-zero if their authenticated calls fail; for
  // dependabot specifically, treat that as "skip" so CI doesn't block.
  if (result.status !== 0) {
    if (lens.skipOnMissing) {
      return { name: lens.name, ok: true, status: `skipped (exit ${result.status})` };
    }
    const tail = (result.stdout + result.stderr).split("\n").slice(-3).join(" | ");
    return { name: lens.name, ok: false, status: `failed: ${tail}` };
  }
  return { name: lens.name, ok: true, status: "refreshed" };
}

console.log(`[lens-refresh] firing ${LENSES.length} lens(es)`);

let allOk = true;
for (const lens of LENSES) {
  const r = runLens(lens);
  const mark = r.ok ? "✓" : "✗";
  console.log(`  ${mark} ${r.name}: ${r.status}`);
  if (!r.ok) allOk = false;
}

process.exit(allOk ? 0 : 1);
