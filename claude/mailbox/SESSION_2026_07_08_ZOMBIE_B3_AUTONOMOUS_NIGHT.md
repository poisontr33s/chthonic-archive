---
type: session-handoff
session: 02c617a7-9a08-476d-92cd-0effad967dd1
date: 2026-07-08
author: claude
lane: zombie-evolution-b3
context: autonomous continuation while user slept
---

# Zombie Evolution B3 — Autonomous Continuation Summary

First real invocation of `/nightly` as the formal skill (`.claude/skills/nightly/SKILL.md`, scaffolded 2026-07-07) rather than hand-replicated from precedent — you asked for it to be "prepared for when such matters coincide," then said you were about to get your 8 hours, which is exactly that coincidence. No topic was named, so scope selection went through the skill's own designed path: read `CLAUDEBASE/charts/frontier-atlas.md`'s §1 ("ready to alchemize now"). Two of its three entries were already-closed record-keeping (atmosphere UBO bug, AxiomVerifier); the one live, forward-looking candidate was zombie evolution's Tier B3, explicitly flagged in both the atlas and `project_zombie_evolution` memory as "not yet checked whether already wired — verify before assuming," the same caution that caught A4/B1 having quietly already shipped earlier the same day.

## What I found

Read `docs/zombie/CONVERGENCE_PLAN.md` and the actual code (`scripts/zombie_forge_bridge.py`) before touching anything, per the skill's own discipline. B3 turned out to be a genuine middle case, not a repeat of the A4/B1 pattern: the bridge already had *part* of it. A `provenance` sub-object already existed in every forge receipt — but it was entirely B1-era fields (`sha256`, `source_file`, `git_head`, `snapshot_at`, `language`, via `_extract_provenance()`/`_provenance_payload()`). B2's three git-derived fields (`days_since_last_touch`, `num_prior_edits`, `is_orphaned`) were real and working, but only inside `bite()`, feeding the ML model — never written into the extract JSON, so the bridge had nothing of B2's to read even though it looked, at a glance, like "provenance is already handled here." `blame_author` existed nowhere in either script. So B3 was real, bounded, unstarted work — the verify-first habit didn't find a repeat of A4/B1, but it did stop me from either wrongly assuming "already done" or wrongly assuming "nothing exists yet."

## What landed

- `scripts/zombie_consumer.py` — `_git_provenance_features()` extended to also return `blame_author` (most recent commit's author), reading it off the *same* `git log --follow` call already in place (widened the format string to `%at\x1f%an`, split on the delimiter) rather than adding a second git subprocess. `_build_bride_provenance()` (the function that builds `extract["provenance"]`, which the bridge reads) now calls this helper and merges all four fields in — additive only, nothing existing renamed or removed.
- `scripts/zombie_forge_bridge.py` — `_provenance_payload()` extended to translate the new fields into the names the plan actually specified: `age_days` (from `days_since_last_touch`), `is_orphaned`, `blame_author` — same defensive `.get()` style as the existing B1 mappings, so a receipt built from an older extract just gets `null` for these, not an error.
- `docs/zombie/CONVERGENCE_PLAN.md` + `docs/zombie/UPGRADE_LOG.md` — both updated in place: Tier B marked fully complete, B3 section rewritten with the real build/verification account, Tier C flagged as next.

**Deliberately did not** thread the provenance dict through `bite()`'s return value to avoid the second `git log` call — `_build_bride_provenance()` calls `_git_provenance_features()` independently. A small redundant subprocess per `chew()` (not per `bite()` alone), traded for keeping `bite()`'s already-shipped B2 body completely untouched. Smaller blast radius, same reasoning this session already used for Fork-V's push-constant range.

## Verified, not assumed

Ran real `zombie chew scripts/zombie_consumer.py --json` (a real tracked file, not a synthetic fixture) and cross-checked the new fields directly against raw `git log` output, not the tool's own claim: `days_since_last_touch: 44.6` matched the file's actual last commit (2026-05-24, a `patch_utf8` fix — nothing zombie-related, which is itself a separate finding, see below) exactly; `blame_author: "poisontr33s"` matched `git log --format=%an` directly. Fed that real provenance block through the actual `_provenance_payload()` function (dynamic import, zero filesystem mutation) and confirmed `age_days`/`is_orphaned`/`blame_author` translate correctly, `sha256` unchanged. Non-regression re-checked directly rather than assumed: B1's `embalm_provenance` block still present and intact in the same extract; B2's ML path still returns a real prediction (not `None`) from `_ml_ore_rating()`, and the pickled model bundle still reports `n_features_in_ == 10`. No pytest suite exists for either script (checked — this project has always verified via direct CLI invocation, matching precedent).

## Two things found and named, not acted on

1. **Small, real, out of scope:** `zombie chew --json` prints an "EMBALMED: ..." status line (and a "Session manifest: ..." line) to stdout ahead of the JSON blob, even in `--json` mode — breaks naive `| jq` piping. Pre-existing, from B1's embalm integration, unrelated to tonight. Named in `UPGRADE_LOG.md` as a follow-up.
2. **Larger, not zombie-specific, worth your attention when you're up:** checking this file's git history to sanity-check the `days_since_last_touch` math surfaced that this entire session's accumulated, already-verified work is sitting uncommitted in the working tree — the TAA motion-adaptive fix, camera input wiring, the root `README.md`, `ci/checks/glsl-lint.ts`, the `NEW_PROVIDENCE` coordinate consolidation, corpse-reviver's UTF-8 patch, the CLAUDEBASE additions, several render screenshots, and now tonight's zombie B2+B3 work — none of it committed. The last real commit touching `scripts/zombie_consumer.py` was 2026-05-24, predating B2 by six weeks. I did not commit any of it beyond what's listed below — deciding how to batch or split ~30 unrelated files across several logical units is exactly the kind of call this skill's own discipline says to name, not make.

## The commit I made (scoped, not the whole tree)

Staged and committed only the six files this session's zombie work actually touched: `scripts/zombie_consumer.py`, `scripts/zombie_forge_bridge.py`, `docs/zombie/CONVERGENCE_PLAN.md`, `docs/zombie/UPGRADE_LOG.md`, and the two B2-retrain artifacts (`dumpster-dive/intake/.zombie_memory.json`, `.zombie_ml_model.pkl` — their diffs were pure B2 output, checked before including). Left every other pending change in the working tree exactly as found — had to catch this concretely: a first `git add` of the 6 files landed on top of a much larger pre-existing staged set (CLAUDEBASE additions, README.md, the glsl-lint CI check, render screenshots, more) from earlier in the session, so I unstaged everything and re-added only the 6 before committing.

Commit `bf1188d6`, pushed to `origin/main` via this repo's own post-commit hook (standing repo behavior, not something I triggered manually). The pre-commit gate caught one real, unrelated small gap along the way: `scripts/zombie_consumer.py` had no `@SID:` envelope at all despite existing since March — the repo's own narrow auto-fixer (`stamp_sid.ts`) stamped it `SCRIPT_ZOMBIE_CONSUMER_V1` and the commit proceeded clean. Cosmetic note, not acted on: `zombie_forge_bridge.py`'s sibling SID uses a `TOOL_` prefix, not `SCRIPT_` — a one-word inconsistency, not worth its own commit tonight.

## Recommended next moves (pick by appetite)

| Option | What | Cost |
|---|---|---|
| A | Tier C — `zombie intake-report` subcommand (ore histogram, ML confidence distribution, provenance age distribution). Pre-condition (B3) now met. Verify-before-assume applies here too before trusting it's unstarted. | A nightly-sized task, similar shape to tonight |
| B | Decide how to handle the uncommitted backlog above — one batched commit, several scoped ones by logical unit, or leave it and keep working on top | Your call on granularity, not mine to decide alone |
| C | Fix the `chew --json` stdout-leak side finding | Small, mechanical, low risk |

## Tone note

One bounded thing, verified against real data at every step, not padded to look busier. The uncommitted-backlog finding is the one piece of news here bigger than tonight's actual task — flagged clearly rather than acted on, since batching two dozen unrelated files into a commit isn't a call I get to make alone.

Sleep well.
