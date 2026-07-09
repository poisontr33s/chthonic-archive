#!/usr/bin/env bun

// @SID: CI_RUNNER_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/run.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ (Standalone — local CI orchestrator, called by pre-commit hook)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ci/run.ts — Registry-driven local CI orchestrator for chthonic-archive.
 *
 * Each check declares scope (staged | always) and speed (fast | slow).
 * Checks run in parallel. Exits 1 if any check fails.
 *
 * Usage:
 *   bun run ci/run.ts                        # all fast checks (tracked files)
 *   bun run ci/run.ts --staged               # staged-only checks (pre-commit mode)
 *   bun run ci/run.ts --staged --autofix     # staged + auto-attempt narrow fixes on failure
 *   bun run ci/run.ts --full                 # all checks including slow (bun-audit)
 *   bun run ci/run.ts --check shebang        # single named check
 *   bun run ci/run.ts --list                 # list registered checks
 *   bun run ci/run.ts --autofix-list         # list checks with registered auto-fix
 *   bun run ci/run.ts --black-smoke          # health fingerprint: run all checks, surface
 *                                            #   advisory/warning/degraded states as
 *                                            #   manifest/black_smoke_report.json. Exits 0
 *                                            #   always (reporting, not a gate). Composes
 *                                            #   with --staged / --full to scope the run.
 *
 * --autofix opt-in contract (per GOVERNANCE_RECONCILIATION_ENGINE_V1_CLAUDE §VI):
 *   - Only runs for checks whose registry entry declares auto_fix
 *   - Only attempts safe_class="narrow" fixers (semantic/destructive fixes excluded by design)
 *   - Does NOT auto-stage the resulting modification — conductor reviews the delta and re-stages
 *   - Reports working-tree delta via `git diff --stat` so the modification trail is visible
 *   - Exit 1 even after successful fix, so commit is blocked until conductor re-stages
 */

import { spawn, spawnSync } from "child_process";
import { mkdirSync, writeFileSync } from "fs";
import { resolve } from "path";

const REPO_ROOT = resolve(import.meta.dir, "..");

type CheckScope = "staged" | "always";
type CheckSpeed = "fast" | "slow";

type AutoFixSafetyClass = "narrow" | "destructive";

type AutoFix = {
  // Command to invoke (bare command, not `bun run` wrapper — that's per-script convention)
  command: string;
  args: string[];
  // Env vars to merge in (e.g., PYTHONUTF8=1 for uv-run Python tools)
  env?: Record<string, string>;
  // Safety classification — only "narrow" fixers run under --autofix
  safe_class: AutoFixSafetyClass;
  // Human description of what the fixer does
  description: string;
};

// Deliberate exclusion — check could theoretically have an auto-fix but doesn't,
// for one of these reasons. Surfaced via --autofix-list so the conductor sees
// the full landscape: what's fixable AND what's deliberately manual + why.
type NoAutoFixReason = {
  reason:
    | "semantic"          // fix requires conductor judgment (SID naming, allowlist choice)
    | "destructive"       // fix could break things (package upgrades, force-renames)
    | "no_tool"           // no canonical fix tool exists in repo
    | "wrong_layer"       // fix tooling exists but doesn't address this check's failure mode
    | "read_only_health"; // check is read-only health probe; no fix concept applies
  explanation: string;
  manual_remediation?: string;
};

type Check = {
  name: string;
  aliases?: string[];
  script: string;
  scope: CheckScope;
  speed: CheckSpeed;
  description: string;
  auto_fix?: AutoFix;
  no_auto_fix?: NoAutoFixReason;
};

const CHECKS: Check[] = [
  {
    name: "shebang",
    script: "scripts/shebang-guard.ts",
    scope: "staged",
    speed: "fast",
    description: "Displaced shebangs in .ts/.sh/.rb files (bun SyntaxError guard)",
    auto_fix: {
      command: "bun",
      args: ["run", "scripts/fix_envelope.ts", "--shebang", "--staged"],
      safe_class: "narrow",
      description: "Relocate a displaced shebang (line 2 → line 1) in staged .ts/.sh/.rb files via fix_envelope.ts. (.py shebang+encoding stays owned by the python-headers fixer, fix_headers.py — not duplicated.)",
    },
  },
  {
    name: "python-headers",
    script: "ci/checks/python-headers.ts",
    scope: "staged",
    speed: "fast",
    description: "Python canonical headers: shebang + UTF-8 encoding line",
    auto_fix: {
      command: "uv",
      args: ["run", "scripts/fix_headers.py", "scripts/"],
      env: { PYTHONUTF8: "1" },
      safe_class: "narrow",
      description: "Enforce canonical shebang + encoding on header-bearing files in scripts/ via fix_headers.py (handles .py / .ps1 / .sh by extension). V1.1 scope-correction: fix_headers.py default is repo-wide which over-fixes ~50 files in probes/apps/dumpster-dive/extensions/. Gate restricts to scripts/. For broader fixing, invoke fix_headers.py directly with desired paths.",
    },
  },
  {
    name: "sid-envelope",
    script: "ci/checks/sid-envelope.ts",
    scope: "staged",
    speed: "fast",
    description: "@SID identity on staged scripts/ci .ts/.py (Added/Copied/Modified) — ALL_CAPS DOMAIN_NAME_V<n> shape",
    auto_fix: {
      command: "bun",
      args: ["run", "scripts/stamp_sid.ts", "--staged"],
      safe_class: "narrow",
      description: "Stamp a path-derived ALL_CAPS DOMAIN_NAME_V1 @SID into staged scripts/ci .ts/.py files that are missing or malformed (CI_CHECK_* / CI_* / LIB_* / SCRIPT_* by directory; filename → UPPER_SNAKE). Each derived SID is self-verified against the gate's own shape regex before write. Does NOT auto-stage — conductor reviews the derived domain prefix, refines if a more precise domain fits, then re-stages. Supersedes the PS1-only scripts/lib/stamp_sid.py, which couldn't handle .ts/.py.",
    },
  },
  {
    name: "uv-guard",
    script: "ci/checks/uv-guard.ts",
    scope: "staged",
    speed: "fast",
    description: "No bare python/python3 invocations — use uv run",
    auto_fix: {
      command: "bun",
      args: ["run", "scripts/fix_envelope.ts", "--uv-run", "--staged"],
      safe_class: "narrow",
      description: "Prepend `uv run` to line-leading bare python/python3 (and `& python`) in staged .sh/.ps1 SHELL files via fix_envelope.ts — the safe subset. Bare python inside .py/.ts (docstring usage examples, spawn/subprocess arg arrays) is NOT auto-rewritten (would corrupt docs / need restructuring) and stays manual; only Added files block, and --no-verify covers that rare case.",
    },
  },
  {
    name: "glsl-lint",
    script: "ci/checks/glsl-lint.ts",
    scope: "staged",
    speed: "fast",
    description: "GLSL shader compile validation via glslangValidator (assets/shaders/*)",
    no_auto_fix: {
      reason: "semantic",
      explanation: "A GLSL compile error or warning reflects an actual defect or ambiguity in the shader's own logic — fixing it requires understanding what the shader is supposed to do, not a mechanical text transform. No safe auto-fix concept applies to compiler diagnostics.",
      manual_remediation: "Read the glslangValidator output line (file:line: message). Fix the GLSL source directly, then re-run `bun run ci -- --check glsl-lint` (cargo build's own shaderc step re-validates the same way at build.rs time).",
    },
  },
  {
    name: "ignored-source",
    aliases: ["autoignore", "gitignore"],
    script: "ci/checks/ignored-source.ts",
    scope: "staged",
    speed: "fast",
    description: "Ignored source-shaped files in managed roots (allowlist .gitignore drift)",
    no_auto_fix: {
      reason: "semantic",
      explanation: "Resolution requires a conductor decision: either add a narrow `!path` allowlist entry to .gitignore (per docs/reference/GITIGNORE_ALLOWLIST_DISCIPLINE.md), move the file to an already-allowed source lane, OR confirm the file should genuinely stay ignored and delete it. Auto-adding allowlist entries silently broadens the gitignore contract.",
      manual_remediation: "Run `git check-ignore -v <path>` to see which rule matches. Then either: (a) add narrow `!path` allowlist + any required parent-dir allowlists to .gitignore, (b) move the file into an existing allowlisted directory, or (c) delete the file if it's debris. Deliberately NOT auto-fixed: auto-editing the allowlist .gitignore contract or force-adding unrelated files would be unsafe. This gate scans repo-wide managed roots (not just your staged set), so if it blocks a commit on unrelated state, `git commit --no-verify` is the sanctioned escape.",
    },
  },
  {
    name: "blessing-gate",
    script: "ci/checks/blessing-gate.ts",
    scope: "staged",
    speed: "fast",
    description: "Script envelope drift (canonize_blessing) + radiance cross-ref validation",
    auto_fix: {
      command: "uv",
      args: ["run", "scripts/canonize_blessing.py", "--target", "scripts", "--apply"],
      env: { PYTHONUTF8: "1" },
      safe_class: "narrow",
      description: "Apply canonical Decorator's Blessing envelope to drifted .py files in scripts/ via canonize_blessing.py --apply. V1 covers scripts/ target only; other blessing-gate targets (mas_mcp/, ankh_atlas/, .codex/, .temple/) require manual canonization.",
    },
  },
  {
    name: "homepath-portability",
    aliases: ["homepath", "eldno-guard"],
    script: "ci/checks/homepath-portability.ts",
    scope: "staged",
    speed: "fast",
    description: "Literal C:\\Users\\<name>\\ paths baked into staged scripts/configs instead of resolved dynamically (stale=foreign machine, smell=current-but-fragile)",
    no_auto_fix: {
      reason: "semantic",
      explanation: "The correct replacement depends on intent — home-relative ({{env.USERPROFILE}} / $env:USERPROFILE / os.homedir()) vs repo-relative ({{config_root}} / import.meta.dir) — not a mechanical username swap. A blind fixer risks silently producing a DIFFERENT wrong value: this repo's own CHTHONIC_NVIDIA_STACK fix (2026-07-04) needed a different relative depth than its three sibling vars purely because someone traced where the real target file actually lived. That trace doesn't mechanize.",
      manual_remediation: "Read the flagged line. Decide: does this path mean 'wherever the current user's home is' (rewrite to the home-relative primitive for that file's language) or 'wherever this repo is checked out' (rewrite to the repo-relative primitive)? For `stale` findings specifically, also check whether the file is a cache/report artifact that should just be deleted/regenerated rather than edited (see project_mise_slab_monorepo_wiring memory for the worked example).",
    },
  },
  {
    name: "pin-truth",
    aliases: ["pins", "version-pins"],
    script: "ci/checks/pin-truth.ts",
    scope: "staged",
    speed: "fast",
    description: "Version declaration truth membrane: distinguish exact pins, ranges, floating channels, and contradictory latest/current/stable claims",
    no_auto_fix: {
      reason: "semantic",
      explanation: "A version contradiction is a law/intent problem, not a mechanical edit: the right repair may be changing a comment from 'latest' to 'pinned', changing a pin to a floating channel, or moving live-upstream facts into a dated source ledger. CI must not choose that policy silently.",
      manual_remediation: "Read each flagged line. If the file is meant to pin, say pinned/range and remove latest/current/stable language. If it is meant to float, use the resolver's floating token (`latest`, `stable`, etc.) instead of a concrete version. If the line records upstream state, move it to a dated research ledger and cite the source.",
    },
  },
  {
    name: "pathfinder",
    aliases: ["link-audit"],
    script: "ci/checks/link-audit.ts",
    scope: "staged",
    speed: "fast",
    description: "Markdown paths, heading/line anchors, offline GitHub/GFM URL shapes, and staged renames",
    auto_fix: {
      command: "uv",
      args: ["run", "scripts/link_audit.py", "scan", "--fix"],
      env: { PYTHONUTF8: "1" },
      safe_class: "narrow",
      description: "Auto-resolve broken/disambiguatable markdown links across the repo via link_audit.py scan --fix. Fixes only unique-match cases; ambiguous links remain for conductor judgment.",
    },
  },
  {
    name: "bun-audit",
    script: "ci/checks/bun-audit.ts",
    scope: "always",
    speed: "slow",
    description: "Dependency security audit via bun audit (slow — full mode only)",
    no_auto_fix: {
      reason: "destructive",
      explanation: "Auto-fixing would require `bun update <pkg>` which can introduce breaking changes via SemVer minor/major bumps. Vulnerability remediation needs conductor judgment on which packages to upgrade vs. accept-risk vs. patch.",
      manual_remediation: "Read the audit report. For high-severity issues, `bun update <pkg>` (single package) and run tests. For broader vulns, consider `bun update` repo-wide but verify nothing breaks. Dependabot PRs on the GitHub side often handle this automatically.",
    },
  },
  {
    name: "inference-gates",
    script: "ci/checks/inference-gate-smoke.ts",
    scope: "always",
    speed: "fast",
    description: "Python 3.14 GPU inference gate ladder status (reads manifest/*.json)",
    no_auto_fix: {
      reason: "read_only_health",
      explanation: "Read-only health probe reading manifest/*.json. Failures indicate upstream gate state changes; no in-repo fix concept applies.",
    },
  },
  {
    name: "terminal-hook",
    script: "ci/checks/terminal-hook-smoke.ts",
    scope: "always",
    speed: "fast",
    description: "Terminal session hook health (JSONL merge regression gate + stale _patch:true detector)",
    no_auto_fix: {
      reason: "read_only_health",
      explanation: "Read-only health probe over session JSONL files. Failures indicate hook regression; remediation is in the hook source (not in this check's scope).",
    },
  },
  {
    name: "gh-runs",
    script: "ci/checks/gh-run-smoke.ts",
    scope: "always",
    speed: "fast",
    description: "GitHub Actions run health membrane (reads manifest/gh_runs/index.json — exits 0 if absent)",
    no_auto_fix: {
      reason: "read_only_health",
      explanation: "Read-only health probe over CI run history. Failures indicate upstream workflow regressions; fix is in .github/workflows/ source.",
    },
  },
  {
    name: "ankh-triple-abstraction",
    script: "ci/checks/ankh-triple-abstraction.ts",
    scope: "always",
    speed: "fast",
    description: "ANKH triple abstraction probe (WHR:MAX conformance + entity topology + compression ratio)",
    no_auto_fix: {
      reason: "read_only_health",
      explanation: "Read-only conformance probe. Failures indicate entity-topology drift requiring semantic adjustment, not mechanical fix.",
    },
  },
  {
    name: "lens-refresh",
    script: "ci/checks/lens-refresh.ts",
    scope: "always",
    speed: "slow",
    description: "Refresh all data-plane lenses (git_rot_index, dependabot_index) — Gitological Noise As Structured Data",
    no_auto_fix: {
      reason: "wrong_layer",
      explanation: "This check IS itself a refresh — there's no separate fix tool. To re-run, invoke `bun run ci/run.ts --check lens-refresh` directly. If it fails repeatedly, the underlying lens script (scripts/refresh-lenses.ps1 or scripts/<lens>_index.py) needs inspection.",
      manual_remediation: "Run `bun run ci/run.ts --check lens-refresh` standalone. If it still fails, check scripts/refresh-lenses.ps1 and the individual scripts/*_index.py producers.",
    },
  },
  // Lore canon membranes (2026-05-27) — methodizes the sample→extract→validate→surface
  // pattern applied during the character JSON refinement lane. character-schema is the
  // contract gate; lore-canon-paths enforces directory shape; organ-canon-citation
  // anchors against SSOT §295-326; lore-canon-refs catches stale cross-references;
  // canon-drift-snapshot writes the time-series memory.
  {
    name: "character-schema",
    aliases: ["char-schema"],
    script: "ci/checks/character-schema.ts",
    scope: "staged",
    speed: "fast",
    description: "JSON Schema validation for game/lore/characters/**/*.json against character.schema.json",
    no_auto_fix: {
      reason: "semantic",
      explanation: "Schema violations need human authoring — missing fields, type mismatches, and renamed keys all encode meaning. The schema is a contract, not a template; auto-filling would write semantically wrong content.",
      manual_remediation: "Read the failing field-path from the output (e.g. 'at lore.relationship_dynamics'). Open the character JSON and either add the missing field with appropriate content OR (if the schema is wrong) update character.schema.json with rationale.",
    },
  },
  {
    name: "lore-canon-paths",
    aliases: ["lore-paths"],
    script: "ci/checks/lore-canon-paths.ts",
    scope: "staged",
    speed: "fast",
    description: "Filesystem-shape membrane: <organ>/T<tier>/<character_id>.json matches file content",
    no_auto_fix: {
      reason: "semantic",
      explanation: "When path and content disagree, the resolution is a semantic judgment: was the file moved to the wrong dir (move it back) or was the content edited and not propagated (move the file to match new content)? Mechanical move could shadow real drift.",
      manual_remediation: "Read the failure: it reports `expected_path` derived from the file's organ+tier+character_id fields. Either `git mv` the file to the expected path, or edit the file's organ/tier/character_id fields to match its actual location.",
    },
  },
  {
    name: "organ-canon-citation",
    aliases: ["organ-citation"],
    script: "ci/checks/organ-canon-citation.ts",
    scope: "always",
    speed: "fast",
    description: "Each character's organ field must be in SSOT §295-326 Organ-Level Entity Canon (or use _deferred_organ sentinel)",
    no_auto_fix: {
      reason: "semantic",
      explanation: "Adding a new organ requires updating SSOT first (a semantic act — promoting an organ into the canonical table). Auto-allowing arbitrary organs would erode the SSOT anchor.",
      manual_remediation: "Two options: (a) place the character at _deferred_organ/T<tier>/ until SSOT promotes the organ, OR (b) add a new row to SSOT §295-326's Organ-Level Entity Canon table under the appropriate tier, then re-run this check. Option (b) is a real canon change — keep it deliberate.",
    },
  },
  {
    name: "lore-canon-refs",
    aliases: ["lore-refs"],
    script: "ci/checks/lore-canon-refs.ts",
    scope: "staged",
    speed: "fast",
    description: "Stale-path drift: flat game/lore/characters/<id>.json refs that no longer resolve to current tracked character files",
    no_auto_fix: {
      reason: "no_tool",
      explanation: "V1 surfaces stale refs but does not rewrite them. It derives canonical targets from the current git-tracked game/lore/characters tree, so the check follows today's file layout instead of a fixed historical list.",
      manual_remediation: "Each failure line reports `<file>:<line>  <stale-ref>` and, when available, `-> <current-canonical-path>`. Replace the stale ref with that target. If no target is shown, the ref points at no current tracked character file and needs author judgment.",
    },
  },
  {
    name: "canon-drift-snapshot",
    aliases: ["canon-history"],
    script: "ci/checks/canon-drift-snapshot.ts",
    scope: "always",
    speed: "fast",
    description: "Memory tier — append a time-series row to manifest/canon_drift_history.ndjson summarizing membrane manifests",
    no_auto_fix: {
      reason: "read_only_health",
      explanation: "Read-only history writer. Reads the four membrane manifests, summarizes, appends one ndjson row. Cannot fail except on missing manifests (in which case the snapshot is partial and labeled so). Building the diary IS the work; there is no fix concept.",
    },
  },
  {
    name: "spread-freshness",
    aliases: ["spread"],
    script: "ci/checks/spread-freshness.ts",
    scope: "always",
    speed: "fast",
    description: "Surface the polyglot spread-index headline (project count, snipe/sweep/noise, native-stack, age). Read-only by default; --max-age-days <N> opts into strict freshness gating.",
    no_auto_fix: {
      reason: "read_only_health",
      explanation: "Read-only health probe over manifest/spread_index.json. Surfaces shape + age; doesn't enforce. The refresh action is `bun run scripts/spread-sweep.ts --summary` — that's the conductor's call, not the gate's. Strict mode (--max-age-days N) is opt-in and lives in the check invocation, not the registry, so daily CI passes don't false-positive on conductor-paced sweeps.",
    },
  },
  // DSL Phase-0 grammar regression gate (2026-05-31) — methodizes the
  // hypothesize→measure→gate loop that took coverage 81%→98%. Runs the
  // iteration-check (smoke + audit + full + coverage% + pattern conformance) in
  // --dry-run and propagates its exit code. Slow (cargo release + full-SSOT scan),
  // so it lives in --full CI, not every fast pre-commit.
  {
    name: "dsl-conformance",
    aliases: ["dsl", "dsl-gate"],
    script: "ci/checks/dsl-conformance.ts",
    scope: "always",
    speed: "slow",
    description: "Chthonic DSL Phase-0 grammar regression gate — coverage% + pattern conformance vs ledger baseline (dsl_iteration_check.py --dry-run)",
    no_auto_fix: {
      reason: "semantic",
      explanation: "On regression the fix is to revert or rework the grammar/SSOT delta that dropped coverage or broke a conformance pattern — a judgment call (the change may be an intentional redesign needing a new ledger baseline + adjusted patterns.json). The check output names the regression class (coverage_drop / pattern_pass_drop / parse_rate_drop / shadow_rise). The ledger is sealed only by deliberate non-dry runs, never by this gate.",
      manual_remediation: "Read the regression class from the output. If unintended: `git revert` the grammar change or fix it. If intended: run `uv run scripts/dsl_iteration_check.py` (no --dry-run) to seal a new baseline + add/adjust the relevant patterns in .chthonic/grammar/patterns.json, then re-commit.",
    },
  },
  // Orphan-check registration (2026-07-04) — four fully-written gate scripts from
  // the May gate-ladder era (one never committed) that no session ever wired into
  // this registry. All four verified green before registration. Fable ruling:
  // CLAUDEBASE/harbor/2026-07-04-ci-gate-architecture-fable-handoff.md
  {
    name: "claudine-lora",
    aliases: ["lora-smoke", "claudine-lora-smoke"],
    script: "ci/checks/claudine-lora-smoke.ts",
    scope: "always",
    speed: "fast",
    description: "Claudine LoRA gate ladder status (C-G4..C-G6 — reads training-gate manifests)",
    no_auto_fix: {
      reason: "read_only_health",
      explanation: "Read-only probe over the Claudine LoRA training-gate manifests. Failures reflect upstream training-lane state; no in-repo fix concept applies.",
    },
  },
  {
    name: "federation-contract",
    aliases: ["federation", "federation-contract-validate"],
    script: "ci/checks/federation-contract-validate.ts",
    scope: "always",
    speed: "fast",
    description: "Terminal-history drain ↔ corpus federation contract (drain format, federation keys, schema compat)",
    no_auto_fix: {
      reason: "read_only_health",
      explanation: "Read-only contract probe over the terminal-history drain DB and corpus schema. Failures indicate drain/corpus drift; remediation lives in the corpus tooling, not this check.",
    },
  },
  {
    name: "session-truncation",
    aliases: ["g9", "session-truncation-gate"],
    script: "ci/checks/session-truncation-gate.ts",
    scope: "always",
    speed: "fast",
    description: "G9 session-truncation gate — structural+GPU scoring status over drained sessions",
    no_auto_fix: {
      reason: "read_only_health",
      explanation: "Read-only scoring probe over the drained session corpus. Failures indicate truncation-quality regression; remediation is in the drain/scoring pipeline.",
    },
  },
  {
    name: "theme-icons",
    aliases: ["icons", "theme-icon-validate"],
    script: "ci/checks/theme-icon-validate.ts",
    scope: "always",
    speed: "fast",
    description: "File icon theme integrity: iconPath existence, definition/reference closure, chthonic-themes sync (sha256)",
    no_auto_fix: {
      reason: "semantic",
      explanation: "Icon failures encode an authoring judgment — a missing icon file vs a dead definition vs a sync drift each resolve differently (add the asset, remove the definition, or re-run the theme sync). Mechanical deletion/creation would guess at intent.",
      manual_remediation: "Read the failing check name (parse / iconPath / dead-definition / sync). Author the fix via the theme-system skill lane (extensions/chthonic-archive/themes/), then re-run `bun run ci/run.ts --check theme-icons`.",
    },
  },
];

const STAGED = process.argv.includes("--staged");
const FULL = process.argv.includes("--full");
const BLACK_SMOKE = process.argv.includes("--black-smoke");
const LIST = process.argv.includes("--list");
const AUTOFIX = process.argv.includes("--autofix");
const HEAL = process.argv.includes("--heal");
const AUTOFIX_LIST = process.argv.includes("--autofix-list");
const CHECK_IDX = process.argv.indexOf("--check");
const SINGLE = CHECK_IDX !== -1 ? process.argv[CHECK_IDX + 1] : null;

if (LIST) {
  console.log("[ci] Registered checks:\n");
  for (const c of CHECKS) {
    const scope = c.scope.padEnd(7);
    const speed = c.speed.padEnd(5);
    let tag = "";
    if (c.auto_fix) tag = " [autofix]";
    else if (c.no_auto_fix) tag = ` [manual: ${c.no_auto_fix.reason}]`;
    console.log(`  ${c.name.padEnd(24)} [${scope}/${speed}]${tag}  ${c.description}`);
  }
  console.log(`\nFlags:`);
  console.log(`  --staged              Run only staged-scope checks (pre-commit mode)`);
  console.log(`  --full                Include slow checks (bun-audit etc.)`);
  console.log(`  --check <name>        Run a single check (by name or alias)`);
  console.log(`  --autofix             On any failure with registered auto_fix, attempt the fix and report delta`);
  console.log(`  --autofix-list        Show all checks: fix command if registered, or explanation if deliberately manual`);
  console.log(`  --autofix-show <name> Show full registry detail for a single check`);
  console.log(`  --black-smoke         Health fingerprint: all checks + advisory surface → manifest/black_smoke_report.json (exits 0)`);
  console.log(`  --list                This output`);
  process.exit(0);
}

const AUTOFIX_SHOW_IDX = process.argv.indexOf("--autofix-show");
const AUTOFIX_SHOW = AUTOFIX_SHOW_IDX !== -1 ? process.argv[AUTOFIX_SHOW_IDX + 1] : null;

if (AUTOFIX_SHOW) {
  const c = CHECKS.find((x) => x.name === AUTOFIX_SHOW || x.aliases?.includes(AUTOFIX_SHOW));
  if (!c) {
    console.error(`[ci] Unknown check: "${AUTOFIX_SHOW}". Run --list for available checks.`);
    process.exit(1);
  }
  console.log(`[ci] ${c.name}\n`);
  console.log(`  scope:       ${c.scope}`);
  console.log(`  speed:       ${c.speed}`);
  console.log(`  description: ${c.description}`);
  console.log(`  script:      ${c.script}`);
  if (c.auto_fix) {
    console.log(`\n  AUTO-FIX REGISTERED [${c.auto_fix.safe_class}]`);
    console.log(`    command: ${c.auto_fix.command} ${c.auto_fix.args.join(" ")}`);
    if (c.auto_fix.env) console.log(`    env:     ${JSON.stringify(c.auto_fix.env)}`);
    console.log(`    purpose: ${c.auto_fix.description}`);
  } else if (c.no_auto_fix) {
    console.log(`\n  NO AUTO-FIX (deliberate) [reason: ${c.no_auto_fix.reason}]`);
    console.log(`    explanation: ${c.no_auto_fix.explanation}`);
    if (c.no_auto_fix.manual_remediation) {
      console.log(`    manual:      ${c.no_auto_fix.manual_remediation}`);
    }
  } else {
    console.log(`\n  (no auto_fix and no no_auto_fix declared — registry gap)`);
  }
  process.exit(0);
}

if (AUTOFIX_LIST) {
  const withFix = CHECKS.filter((c) => c.auto_fix);
  const withoutFix = CHECKS.filter((c) => c.no_auto_fix);
  const unspecified = CHECKS.filter((c) => !c.auto_fix && !c.no_auto_fix);

  console.log("[ci] Auto-fix registry — comprehensive view\n");

  console.log(`=== AUTOMATIC (${withFix.length} check(s) — runnable via --autofix) ===\n`);
  if (withFix.length === 0) {
    console.log("  (none registered)\n");
  } else {
    for (const c of withFix) {
      const af = c.auto_fix!;
      console.log(`  ${c.name.padEnd(24)} [${af.safe_class}]`);
      console.log(`    command: ${af.command} ${af.args.join(" ")}`);
      console.log(`    purpose: ${af.description}`);
      console.log();
    }
  }

  console.log(`=== MANUAL ONLY (${withoutFix.length} check(s) — deliberate non-auto-fix) ===\n`);
  if (withoutFix.length === 0) {
    console.log("  (none classified)\n");
  } else {
    for (const c of withoutFix) {
      const nf = c.no_auto_fix!;
      console.log(`  ${c.name.padEnd(24)} [reason: ${nf.reason}]`);
      console.log(`    ${nf.explanation}`);
      if (nf.manual_remediation) {
        console.log(`    Manual fix: ${nf.manual_remediation}`);
      }
      console.log();
    }
  }

  if (unspecified.length > 0) {
    console.log(`=== REGISTRY GAP (${unspecified.length} check(s) — no auto_fix and no no_auto_fix declared) ===\n`);
    for (const c of unspecified) {
      console.log(`  ${c.name}`);
    }
    console.log();
  }

  process.exit(0);
}

function selectChecks(): Check[] {
  if (SINGLE) {
    const found = CHECKS.find((c) => c.name === SINGLE || c.aliases?.includes(SINGLE));
    if (!found) {
      console.error(`[ci] ✗ Unknown check: "${SINGLE}". Run --list for available checks.`);
      process.exit(1);
    }
    return [found];
  }
  if (STAGED) return CHECKS.filter((c) => c.scope === "staged");
  // --full and standalone --black-smoke both run the complete registry.
  // --black-smoke --staged narrows to staged scope (handled above).
  if (FULL || (BLACK_SMOKE && !STAGED)) return CHECKS;
  return CHECKS.filter((c) => c.speed === "fast");
}

function runCheck(check: Check): Promise<{ name: string; ok: boolean; output: string }> {
  const scriptPath = resolve(REPO_ROOT, check.script);
  const args: string[] = STAGED ? ["--staged"] : [];

  return new Promise((res) => {
    const child = spawn("bun", ["run", scriptPath, ...args], {
      cwd: REPO_ROOT,
      env: { ...process.env },
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (d: Buffer) => { stdout += d.toString(); });
    child.stderr.on("data", (d: Buffer) => { stderr += d.toString(); });
    child.on("error", (e: Error) => res({ name: check.name, ok: false, output: e.message }));
    child.on("close", (code: number | null) => {
      const output = (stdout + stderr).trim();
      res({ name: check.name, ok: (code ?? 1) === 0, output });
    });
  });
}

function gitWorkingTreeDiffStat(): string {
  const r = spawnSync("git", ["diff", "--stat"], { encoding: "utf8", cwd: REPO_ROOT });
  return (r.stdout ?? "").trim();
}

type AutoFixResult = {
  name: string;
  attempted: boolean;
  fix_command: string;
  fix_output: string;
  fix_exit: number;
  delta_before: string;
  delta_after: string;
  changed: boolean;
};

function runAutoFix(check: Check): AutoFixResult {
  const af = check.auto_fix;
  if (!af) {
    return {
      name: check.name,
      attempted: false,
      fix_command: "",
      fix_output: "[autofix] no auto_fix registered for this check",
      fix_exit: 0,
      delta_before: "",
      delta_after: "",
      changed: false,
    };
  }
  if (af.safe_class !== "narrow") {
    return {
      name: check.name,
      attempted: false,
      fix_command: `${af.command} ${af.args.join(" ")}`,
      fix_output: `[autofix] safe_class=${af.safe_class} not in narrow allowlist — manual fix only`,
      fix_exit: 0,
      delta_before: "",
      delta_after: "",
      changed: false,
    };
  }

  const fix_command = `${af.command} ${af.args.join(" ")}`;
  const delta_before = gitWorkingTreeDiffStat();
  const env = { ...process.env, ...(af.env ?? {}) };
  const r = spawnSync(af.command, af.args, {
    encoding: "utf8",
    cwd: REPO_ROOT,
    env,
  });
  const fix_output = ((r.stdout ?? "") + (r.stderr ?? "")).trim();
  const fix_exit = r.status ?? 1;
  const delta_after = gitWorkingTreeDiffStat();
  const changed = delta_before !== delta_after;
  return {
    name: check.name,
    attempted: true,
    fix_command,
    fix_output,
    fix_exit,
    delta_before,
    delta_after,
    changed,
  };
}

const selected = selectChecks();
const modeLabel = STAGED ? "--staged" : FULL ? "--full" : SINGLE ? `--check ${SINGLE}` : "default";

// Async git helper shared by the landscape functions — lets stagedFileLandscape and
// submoduleLandscape run concurrently via Promise.all instead of blocking serially.
function gitOut(args: string[]): Promise<string> {
  return new Promise((res) => {
    const child = spawn("git", args, { cwd: REPO_ROOT });
    let out = "";
    child.stdout.on("data", (d: Buffer) => { out += d.toString(); });
    child.on("close", () => res(out));
    child.on("error", () => res(""));
  });
}

// Surface the staged file landscape in the banner so vacuous passes are visible
// (3 gitlink changes + 7 checks all "passing" with 0 files inspected = not a real pass).
// Each registered check has a narrow file-type scope; if staged content doesn't match
// any scope, the gate yawns silently. The breakdown below makes the gap obvious.
async function stagedFileLandscape(): Promise<{ count: number; ext_summary: string; files: string[] }> {
  if (!STAGED) return { count: -1, ext_summary: "", files: [] };
  const stdout = await gitOut(["diff", "--cached", "--name-only", "--diff-filter=ACMRT"]);
  const files = stdout.split("\n").filter(Boolean);
  const ext_counts: Record<string, number> = {};
  for (const f of files) {
    const dot = f.lastIndexOf(".");
    const slash = Math.max(f.lastIndexOf("/"), f.lastIndexOf("\\"));
    const ext = dot > slash ? f.slice(dot) : "(no-ext/gitlink)";
    ext_counts[ext] = (ext_counts[ext] || 0) + 1;
  }
  const ext_summary = Object.entries(ext_counts)
    .sort((a, b) => b[1] - a[1])
    .map(([e, c]) => `${e}:${c}`)
    .join(" ");
  return { count: files.length, ext_summary, files };
}

// V1.3 — also surface dirty-submodule and orphan-gitlink landscape.
// Worked precedent: conductor saw 3 "M" entries in VS Code Source Control panel
// (tabbyAPI, sd-candidates/a1111, sd-candidates/sdnext) but the gate reported
// staged: 0 because those were modified-submodule-CONTENTS (` m ` in
// git status -s --ignore-submodules=none), not staged-gitlink-POINTER-changes.
// VS Code conflates the two; this banner separates them.
async function submoduleLandscape(): Promise<{ dirty_count: number; orphan_count: number; entries: { path: string; orphan: boolean }[] }> {
  if (!STAGED) return { dirty_count: 0, orphan_count: 0, entries: [] };
  const statusOut = await gitOut(["status", "-s", "--ignore-submodules=none"]);
  // Parse ` m <path>` ONLY — lowercase-m is git's specific submodule-content-modified
  // signal. Capital ` M ` matches any modified-in-working-tree file (NOT just submodules),
  // and matching it caused a pre-ship test failure where ci/run.ts (a regular .ts file
  // with working-tree changes) got captured as an "orphan gitlink" and rm-cached.
  // Lowercase-m only + 160000-mode verification below = bounded to actual gitlinks.
  const lines = statusOut.split("\n").filter(Boolean);
  const dirty_paths = lines
    .filter((l) => /^\sm\s/.test(l) && l.length > 3)
    .map((l) => l.slice(3).trim());
  if (dirty_paths.length === 0) return { dirty_count: 0, orphan_count: 0, entries: [] };

  // Sanity check: verify each path is actually a gitlink (160000 mode in HEAD).
  // Defends against any future regex drift or unexpected status code surfacing
  // non-submodule paths through the lowercase-m filter.
  // Batch: one ls-tree call for all paths (was N sequential subprocesses).
  // git ls-tree HEAD -- p1 p2 ... returns only entries for those paths.
  // Also fetch .gitmodules concurrently — both are independent index reads.
  const [lsOut, gmOut] = await Promise.all([
    gitOut(["ls-tree", "HEAD", "--", ...dirty_paths]),
    gitOut(["config", "-f", ".gitmodules", "-l"]),
  ]);

  const gitlinkSet = new Set(
    lsOut
      .split("\n")
      .filter((line) => line.startsWith("160000 "))
      .map((line) => line.split("\t")[1]?.trim() ?? "")
      .filter(Boolean)
  );
  const verified_paths = dirty_paths.filter((p) => gitlinkSet.has(p));
  if (verified_paths.length === 0) return { dirty_count: 0, orphan_count: 0, entries: [] };

  // Check .gitmodules for each — orphan if not registered
  const gm_content = gmOut; // empty string if .gitmodules missing
  const entries = verified_paths.map((p) => ({
    path: p,
    orphan: !gm_content.includes(`path=${p}`) && !gm_content.includes(`= ${p}`),
  }));
  return {
    dirty_count: entries.length,
    orphan_count: entries.filter((e) => e.orphan).length,
    entries,
  };
}

const [staged, submods] = await Promise.all([stagedFileLandscape(), submoduleLandscape()]);
const stagedBanner =
  STAGED && staged.count >= 0
    ? ` | staged: ${staged.count} file(s)${staged.ext_summary ? ` [${staged.ext_summary}]` : ""}`
    : "";
const submodBanner =
  STAGED && submods.dirty_count > 0
    ? ` | dirty-submodules: ${submods.dirty_count}${submods.orphan_count > 0 ? ` (orphan-gitlinks: ${submods.orphan_count})` : ""}`
    : "";
console.log(`[ci] ${selected.length} check(s) | mode: ${modeLabel}${stagedBanner}${submodBanner}\n`);

if (STAGED && staged.count === 0 && submods.dirty_count > 0) {
  const orphans = submods.entries.filter((x) => x.orphan);
  const non_orphans = submods.entries.filter((x) => !x.orphan);

  // V1.4 AUTO-RESCUE: when staged=0 AND there are orphan gitlinks (broken state:
  // 160000 mode entries in HEAD with no .gitmodules registration), auto-`git rm
  // --cached` them. This stages a deletion at the index layer (bypassing .gitignore
  // which often also blocks these paths), giving the commit something to land.
  // Working-tree directories are untouched. The orphan-gitlink governance gap is
  // resolved as a side effect. Reversible via `git reset HEAD <path>` before commit.
  // Per user intent (2026-05-25): "commit on my free will when files are adding up
  // regardless what files they are." Narrow trigger — only fires when (a) nothing
  // else is staged, (b) the dirty submodules are orphan (no .gitmodules). Proper
  // submodules with .gitmodules are NEVER auto-rescued; they get guidance only.
  if (orphans.length > 0) {
    console.log(`[ci] AUTO-RESCUE: ${orphans.length} orphan-gitlink(s) detected with nothing else staged.`);
    console.log(`[ci]   These have 160000-mode entries in HEAD but no .gitmodules registration — broken state.`);
    console.log(`[ci]   Staging their removal from the index so the commit can land:`);
    for (const e of orphans) {
      console.log(`[ci]     - ${e.path}`);
    }
    const rm_result = spawnSync("git", ["rm", "--cached", ...orphans.map((x) => x.path)], {
      encoding: "utf8",
      cwd: REPO_ROOT,
    });
    if (rm_result.status === 0) {
      console.log(`[ci]   ✓ Removed from index. Working-tree directories untouched.`);
      console.log(`[ci]   Commit will proceed with the staged deletion(s) as content.`);
      console.log(`[ci]   Undo this rescue before commit: git reset HEAD ${orphans.map((x) => x.path).join(" ")}`);
    } else {
      console.log(`[ci]   ✗ rm --cached failed (exit ${rm_result.status}):`);
      console.log(((rm_result.stderr ?? "") + (rm_result.stdout ?? "")).trim());
    }
    console.log();
  }

  // Non-orphan dirty submodules (proper .gitmodules registration, just inner dirt):
  // These can't be auto-rescued because the .gitmodules contract is intact and the
  // inner work needs an inner commit to advance the gitlink. Print guidance only.
  if (non_orphans.length > 0) {
    console.log(`[ci] ℹ ${non_orphans.length} dirty submodule(s) cannot be auto-rescued (proper .gitmodules entries — governance is intact, inner work needs inner commit):`);
    for (const e of non_orphans) {
      console.log(`[ci]     - ${e.path}`);
    }
    console.log(`[ci]   To advance these gitlinks:  cd <submodule>; git commit; cd ..; git add <path>`);
    console.log();
  }
}

const results = await Promise.all(selected.map(runCheck));

let failed = 0;
for (const r of results) {
  if (r.output) console.log(r.output);
  if (!r.ok) {
    failed++;
    console.error(`[ci] ✗ ${r.name} FAILED`);
  }
}

console.log();
if (failed === 0) {
  console.log(`[ci] ✓ All ${selected.length} check(s) passed`);
}

if (BLACK_SMOKE) {
  // Advisory pattern scanner — captures any line that signals a non-clean
  // (but non-fatal) state: informational markers, warnings, degraded status.
  const ADV = [/ℹ/, /⚠/, /advisory/i, /degraded/i];

  type BsSig = {
    check: string;
    exit_ok: boolean;
    advisory_lines: string[];
    degraded: boolean;
  };

  const MANIFEST_DIR = resolve(REPO_ROOT, "manifest");
  const sigs: BsSig[] = [];
  for (const r of results) {
    const lines = r.output.split("\n");
    const advisory_lines = lines.filter((l) => ADV.some((p) => p.test(l)));
    const degraded = lines.some((l) => /degraded/i.test(l));
    if (!r.ok || advisory_lines.length > 0) {
      sigs.push({ check: r.name, exit_ok: r.ok, advisory_lines, degraded });
    }
  }

  const report = {
    generated_at: new Date().toISOString(),
    mode: STAGED ? "--staged" : FULL ? "--full" : "--black-smoke",
    total_checks: selected.length,
    failed,
    with_advisories: sigs.filter((s) => s.exit_ok && s.advisory_lines.length > 0).length,
    degraded_count: sigs.filter((s) => s.degraded).length,
    signatures: sigs,
  };

  mkdirSync(MANIFEST_DIR, { recursive: true });
  writeFileSync(resolve(MANIFEST_DIR, "black_smoke_report.json"), JSON.stringify(report, null, 2));

  console.log(`\n[black-smoke] ${sigs.length} check(s) with advisory/failure surface:`);
  if (sigs.length === 0) {
    console.log("  (clean — no advisory or degraded states detected)");
  } else {
    for (const s of sigs) {
      const icon = !s.exit_ok ? "✗" : s.degraded ? "⚠" : "ℹ";
      const tags = [s.degraded ? "DEGRADED" : null, s.advisory_lines.length > 0 ? `${s.advisory_lines.length} advisory` : null].filter(Boolean).join(" ");
      console.log(`  ${icon} ${s.check}${tags ? `  [${tags}]` : ""}`);
      // Print up to 3 advisory lines as preview
      for (const line of s.advisory_lines.slice(0, 3)) {
        console.log(`      ${line.trim()}`);
      }
      if (s.advisory_lines.length > 3) {
        console.log(`      ... (${s.advisory_lines.length - 3} more — see manifest/black_smoke_report.json)`);
      }
    }
  }
  console.log(`[black-smoke] report → manifest/black_smoke_report.json`);
  process.exit(0); // reporting mode — never a gate
}

if (failed === 0) process.exit(0);

console.error(`[ci] ✗ ${failed}/${selected.length} check(s) failed`);

if (HEAL) {
  // Self-heal mode — the pre-commit hook runs this so a single VS Code commit button-press
  // lands the fix without a terminal. For each failing check with a registered NARROW
  // auto-fix: run it, re-stage ONLY the originally-staged paths (never `git add -u`, so
  // unrelated working-tree edits are never swept into the commit), re-verify, and proceed
  // if clean. Genuinely-manual failures (no narrow auto_fix, or a fix that changed nothing)
  // still block — with their remediation printed.
  const stagedBefore = spawnSync("git", ["diff", "--cached", "--name-only"], { encoding: "utf8", cwd: REPO_ROOT })
    .stdout.split("\n")
    .filter(Boolean);

  let anyFixed = false;
  for (const r of results) {
    if (r.ok) continue;
    const check = selected.find((c) => c.name === r.name);
    if (check?.auto_fix && check.auto_fix.safe_class === "narrow") {
      console.log(`[heal] ${r.name} → ${check.auto_fix.command} ${check.auto_fix.args.join(" ")}`);
      const af = runAutoFix(check);
      if (af.fix_output) console.log(af.fix_output.split("\n").map((l) => `  ${l}`).join("\n"));
      if (af.changed) anyFixed = true;
    }
  }

  if (anyFixed) {
    if (stagedBefore.length > 0) spawnSync("git", ["add", "--", ...stagedBefore], { cwd: REPO_ROOT });
    const reResults = await Promise.all(selected.map(runCheck));
    for (const r of reResults) if (r.output) console.log(r.output);
    const stillFailed = reResults.filter((r) => !r.ok);
    if (stillFailed.length === 0) {
      console.log(`\n[heal] ✓ auto-fixed + re-staged; all checks pass — commit proceeding.`);
      process.exit(0);
    }
    console.error(`\n[heal] ✗ ${stillFailed.length} check(s) still failing after auto-fix:`);
    for (const r of stillFailed) {
      const c = selected.find((x) => x.name === r.name);
      console.error(`  • ${r.name}${c?.no_auto_fix?.manual_remediation ? ` — ${c.no_auto_fix.manual_remediation}` : ""}`);
    }
    process.exit(1);
  }

  console.error(`\n[heal] no auto-fix changed anything — manual remediation required:`);
  for (const r of results) {
    if (r.ok) continue;
    const c = selected.find((x) => x.name === r.name);
    const hint = c?.no_auto_fix?.manual_remediation ?? (c?.auto_fix ? "(auto-fix ran but produced no change)" : "(no auto-fix registered)");
    console.error(`  • ${r.name} — ${hint}`);
  }
  process.exit(1);
}

if (!AUTOFIX) {
  process.exit(1);
}

// --autofix branch: attempt registered narrow-class fixes for each failed check
console.log(`\n[autofix] --autofix flag detected; attempting registered narrow-class fixes for ${failed} failure(s)...\n`);

let attempted = 0;
let changed = 0;
const fix_summaries: AutoFixResult[] = [];

for (const r of results) {
  if (r.ok) continue;
  const check = selected.find((c) => c.name === r.name);
  if (!check) continue;
  const af_result = runAutoFix(check);
  fix_summaries.push(af_result);
  if (!af_result.attempted) {
    console.log(`[autofix] ${r.name}: ${af_result.fix_output}`);
    continue;
  }
  attempted++;
  console.log(`[autofix] ${r.name} → ${af_result.fix_command}`);
  if (af_result.fix_exit !== 0) {
    console.log(`[autofix] ${r.name}: fix command exited ${af_result.fix_exit}`);
  }
  if (af_result.changed) {
    changed++;
    console.log(`[autofix] ${r.name}: working-tree CHANGED`);
  } else {
    console.log(`[autofix] ${r.name}: fix command produced no working-tree delta`);
  }
  console.log();
}

if (attempted === 0) {
  console.error(`\n[autofix] No registered narrow-class fixes for any failure. Manual remediation required.`);
  process.exit(1);
}

if (changed === 0) {
  console.error(`\n[autofix] Attempted ${attempted} fix(es); none produced a working-tree change. Manual remediation required.`);
  process.exit(1);
}

console.log(`\n[autofix] Summary: ${attempted} fix(es) attempted, ${changed} produced working-tree changes.`);
console.log(`[autofix] Working-tree delta (post-fix):`);
const final_delta = gitWorkingTreeDiffStat();
if (final_delta) {
  console.log(final_delta.split("\n").map((l) => `  ${l}`).join("\n"));
} else {
  console.log(`  (none)`);
}
console.log(`\n[autofix] Next conductor step:`);
console.log(`  1. Review the working-tree delta above (or run: git diff)`);
console.log(`  2. If satisfied, re-stage: git add -u  (or specific files)`);
console.log(`  3. Re-attempt commit. The pre-commit guard will re-run all checks against the new staged set.`);
console.log(`\n[autofix] Per GOVERNANCE_RECONCILIATION_ENGINE_V1_CLAUDE §VI: auto-fix does NOT auto-stage. The modification trail stays visible. The conductor's keen disposes.`);

// Still exit 1 — the commit is blocked until the conductor re-stages.
process.exit(1);

