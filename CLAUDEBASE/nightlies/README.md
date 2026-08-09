# CLAUDEBASE/nightlies — the `/nightly` ledger

What `.claude/skills/nightly/SKILL.md` produces every time it runs, structured for
deterministic lookup and cross-run analysis — distinct from the narrative landing
docs in `claude/mailbox/SESSION_*_AUTONOMOUS_NIGHT.md`, which stay the human-readable
account of *what happened and why*. This folder answers a different question:
across every run so far, what's the shape of the history, and how well is this
actually using the window it's given?

## Structure

- `LEDGER.md` — one row per run, append-only, newest at the bottom. The at-a-glance
  surface: date, who invoked it, how long it took, what happened, whether the skill
  itself improved. Read this first when asking "how's `/nightly` doing overall."
- `records/<date>_<lane-slug>.md` — one structured record per run. Frontmatter
  carries the machine-legible fields (trigger, outcome, duration, commits,
  self-improvement); a short paragraph underneath orients a human without needing
  the full mailbox narrative. Links back to the mailbox landing doc for the
  complete account.

## Why a separate folder from `claude/mailbox/`

The mailbox landing doc is prose, written once, for one reader, about one run — it
doesn't compound. This folder is the opposite: small, structured, consistent fields
across every run, built specifically so a later run (or a later *you*) can look back
across all of them at once — which lanes get picked, whether verification holds,
whether the self-improvement loop (`SKILL.md` §7) is actually firing, whether the
8-hour window is being used well or padded. Compounding needs a deterministic,
consistent place to compound *into* — this is that place. The mailbox doc isn't
replaced; it's the detail this folder points back to.

## Schema (mostly invariant — see note)

Per-run record frontmatter:

```yaml
schema_version: 3
date: YYYY-MM-DD
run_id: <short slug, matches the record filename's date+lane>
trigger: user-invoked | claude-autonomous
mode: default | creative | daytime   # see SKILL.md §1 for what each mode changes
lane: <short-topic-slug>
atlas_source: <where the task came from, or "user-named">
outcome: shipped | stopped-short | partial
verification: pass | fail | not-applicable
commits:
  - hash: <hash>
    kind: feature | meta | mixed   # feature = delivers the requested task; meta = this skill's own design/scaffolding/self-correction; mixed = both landed in one commit (§7 says fix a found gap in the same invocation, which can bundle the two)
landing_doc: claude/mailbox/SESSION_..._AUTONOMOUS_NIGHT.md   # may be empty — see SKILL.md §4; most runs don't warrant one
self_improvement:
  found: true | false
  summary: <one line, omit if false>
duration:
  start: <ISO timestamp, or "not recorded">
  end: <ISO timestamp, or "not recorded">
  elapsed: <human-readable, or "not recorded">
```

**"Mostly invariant"** — this schema should stay stable across runs so rows stay
comparable; that's the whole point of a ledger. But `/nightly` is itself meant to
improve every run (`SKILL.md` §7) — if a real run genuinely needs a new field, add
it, bump `schema_version`, and note the change here. Stability is the default, not
a wall.

**v1 → v2 (2026-07-08, same night as v1):** added `mode`, the same night `--mode`
itself was added to `SKILL.md` §1. All records were still same-day and
self-authored at that point, so the 3 existing ones were updated in place to v2
with `mode: default` rather than left at a permanently-orphaned v1 shape — a real
future schema change, once external records exist that shouldn't be silently
rewritten, gets a note here instead of an in-place edit.

**v2 → v3 (2026-07-09):** `commits` changed from a flat hash list to `{hash, kind}`
objects (`feature` | `meta` | `mixed`), per `SKILL.md` §7's third retrospective
question — the user asked for cost/value scrutiny against real Claude usage-panel
data (weekly usage breakdown by skill), and a flat commit list can't show the
feature-vs-meta ratio without manually re-deriving it from `git log` each time,
which is exactly what happened to produce this change. Doing that re-derivation
also surfaced two real, separate mistakes in the existing records, fixed in the
same pass: the `zombie-b3` record had over-attributed two commits to itself
(`801e9438`/`51fd78ff`) that actually landed in a later, separate conversational
turn, not this invocation's own scope — see that record's own correction note; and
the `zombie-c1` record's `commits` field had been left empty outright, filled in
now with `acec176a` (classified `mixed`, since it bundles the feature work with a
§7-triggered `SKILL.md` fix). Same in-place-update reasoning as v1→v2 for the
schema-shape change itself: all four records were still self-authored, same short
arc, so backfilled directly rather than left at v2 — but the *content* corrections
(not just the shape change) are real fixes to real errors, not a mechanical migration.

## Both-ways requirement

This ledger gets filled out identically whether the user invokes `/nightly` directly
or Claude does — the `trigger` field records which, but nothing about the logging
process changes based on who typed the command. See `.claude/skills/nightly/SKILL.md`
§5.

## Retroactively backfilled entries

The first three ledger rows (DSL Phase 0, A-C-A live correspondence, zombie B3) all
predate this folder's existence — backfilled 2026-07-08 from their mailbox landing
docs and `git log`, not invented. Fields the source material didn't capture (mainly
`duration` — nothing timestamped these runs' start/end before tonight) are marked
`not recorded`, not guessed. `self_improvement` for the first two is marked
not-applicable rather than false — both predate `SKILL.md` §7 existing at all, so
there was no retrospective step to have found or missed anything.
