#!/usr/bin/env bun
// @SID: CI_CHECK_DSL_CONFORMANCE_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/checks/dsl-conformance.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: AMETHYST
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ scripts/dsl_iteration_check.py        (the gate this wraps)
// ║   └─◄ .chthonic/grammar/chthonic.peg        (canonical Phase-0 grammar)
// ║   └─◄ manifest/dsl_iteration_history.ndjson (regression baseline)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * CI_CHECK_DSL_CONFORMANCE_V1 — Chthonic DSL Phase-0 grammar regression gate.
 *
 * Wraps scripts/dsl_iteration_check.py in --dry-run (regression check only, no
 * ledger mutation — so the gate never dirties the working tree mid-commit) and
 * propagates its exit code:
 *   0  no regression vs last ledger row
 *   1  regression: coverage_drop / pattern_pass_drop / parse_rate_drop / shadow_rise / plateau
 *   2  a smoke/audit subprocess failed (build/parse broken)
 *
 * The ledger itself is sealed by DELIBERATE runs of dsl_iteration_check.py
 * (without --dry-run) — improving coverage or adding patterns is an explicit act,
 * not a side effect of the gate. Marked slow (cargo release build + full-SSOT
 * coverage scan), so it runs under `--full`, not every fast pre-commit.
 */

import { spawnSync } from "child_process";
import { resolve } from "path";

const REPO_ROOT = resolve(import.meta.dir, "..", "..");

const r = spawnSync("uv", ["run", "scripts/dsl_iteration_check.py", "--dry-run"], {
  encoding: "utf8",
  cwd: REPO_ROOT,
  env: { ...process.env, PYTHONUTF8: "1" },
});

const out = ((r.stdout ?? "") + (r.stderr ?? "")).trim();
if (out) console.log(out);

process.exit(r.status ?? 1);
