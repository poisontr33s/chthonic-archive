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
schema_version: 2
date: YYYY-MM-DD
run_id: <short slug, matches the record filename's date+lane>
trigger: user-invoked | claude-autonomous
mode: default | creative | daytime   # see SKILL.md §1 for what each mode changes
lane: <short-topic-slug>
atlas_source: <where the task came from, or "user-named">
outcome: shipped | stopped-short | partial
verification: pass | fail | not-applicable
commits: [<hash>, ...]
landing_doc: claude/mailbox/SESSION_..._AUTONOMOUS_NIGHT.md
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
