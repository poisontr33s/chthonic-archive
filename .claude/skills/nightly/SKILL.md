---
name: nightly
description: "Autonomous continuation while the user is away (asleep, out) — picks one bounded task from the frontier atlas's warmest cluster, follows rewindability/cessation discipline, verifies before committing, writes a structured landing doc to claude/mailbox/ AND a deterministic ledger entry to CLAUDEBASE/nightlies/ for cross-run performance analysis. Formalizes a pattern already proven across multiple real runs (full history in CLAUDEBASE/nightlies/LEDGER.md), not invented fresh."
allowed-tools: "Read, Grep, Glob, Bash, Edit, Write"
argument-hint: "[<topic>] [--mode creative|daytime]"
user-invocable: true
---

# /nightly — autonomous continuation

Generalizes what real nightlies actually did, not what one *should* do in the abstract. Full run history — every invocation, its landing doc, and its outcome — lives in `CLAUDEBASE/nightlies/LEDGER.md`; read the most recent few before a first invocation if their shape isn't already warm in context.

## When to use

The user is stepping away for a real stretch (sleep, out) and wants bounded, verified progress rather than nothing happening. Not a replacement for asking — it exists because the user explicitly asked for it each time so far. Treat an unprompted `/nightly` invocation the same as an explicit ask, not as standing permission to run it whenever convenient.

**Works identically regardless of who invokes it.** The user typing `/nightly` themselves and Claude invoking it produce the same ledger entry (§5), the same discipline, the same rigor — not invariant across invocation source; the artifacts and rigor are.

## Standing quality bar (non-negotiable)

Unsupervised is not the same as lesser. Every judgment call this skill makes gets the same depth of thought a live, watched session would get — "autonomous" describes who's supervising, not how carefully the work gets done. §7's retrospective checks this explicitly, not just the skill's own design.

## Never blocks on a synchronous human response (non-negotiable)

A plan awaiting approval, or a question awaiting an answer, is a hard stop when nobody's there to respond. This skill never calls `EnterPlanMode` and never calls `AskUserQuestion` during a run. If a task feels like it needs upfront sign-off, that's the signal it's an atlas-§2/§3-sized item (externally blocked, or genuinely foundational — §1's own gloss of those categories) that doesn't belong in a nightly. Stop short and name it in the landing doc's "recommended next moves" table (§4) instead.

## 1. Scope selection

**First action, before anything else:** capture a start timestamp for tonight's `CLAUDEBASE/nightlies/` record (§5) — `mcp__time__get_current_time` (pass the working timezone, e.g. `Europe/Berlin`), or `date -u +"%Y-%m-%dT%H:%M:%SZ"` if that tool isn't loaded; both verified working (commit `e0729a10`). Do the same at the end, right before writing the ledger record, and compute the elapsed span — a run that skips this still ships, it just costs an honest `duration` instead of another "not recorded."

No passive clock exists between those two checks, and none is needed: this skill was never meant to pace against a countdown or fill the absence window. It does one bounded task and stops, whatever real time that honestly takes. Padding work to consume more of the window violates §2's "one well-verified thing beats several padded ones," not satisfies it.

Optional argument names a topic or cluster directly (`/nightly aca-engine`). With no argument: read `CLAUDEBASE/charts/frontier-atlas.md`'s Level map and its §1 ("ready to alchemize now") first, and pick the item that is both gate-met and in a cluster with a recent nearby landing doc. Do not pick from atlas §2/§3 without the user naming it directly.

**§1 is not a pure candidate queue** — it can mix genuinely-open items with entries kept purely for record-keeping. Check each entry's own stated status, not just its presence in §1 (worked example: `CLAUDEBASE/nightlies/records/2026-07-08_zombie-b3.md`).

**Before acting on anything the atlas or memory claims, verify it against the current code.** Every real run so far has surfaced a different failure mode on this exact check — see `CLAUDEBASE/nightlies/LEDGER.md` for what each one found. Don't force a finding into a binary matches/doesn't-match box; read closely enough to say exactly which parts are real.

**A regression found by that verify step is itself a valid pick**, and often the better one. The sections above read as "choose an entry, then confirm it" — but with every run so far finding something on this check, the check is not a filter in front of the work, it is a source of it. When verifying a §1 claim shows the thing it describes is now broken, that regression is in scope on the same terms as any other §1 item: it is gate-met by construction (the entry already cleared that bar) and maximally warm (you are already reading the code). Two guards, both learned the hard way: confirm the breakage against live state rather than inferring it from a stale entry, and record `atlas_source` as the §1 entry that led there plus how it surfaced, so the ledger doesn't imply the atlas listed a task it never contained. Worked example: `CLAUDEBASE/nightlies/records/2026-08-09_ssot-seal.md`, where §1's AxiomVerifier entry was accurate about what shipped and the sidecar seal it describes had since gone missing.

### Modes (`--mode <name>`, optional, composes with a named topic) — provisional, not yet proven by real use

Default (no `--mode`): everything above, unchanged. `creative` and `daytime` were sketched before either had run once (commit `13f35e08`, marked provisional in `e0729a10`) — a shape worth having on paper, not a settled contract. Change either freely once a real invocation shows a different shape works better, the same way any other §7 finding gets acted on.

- **`creative`** — lifts §2's "no invented content in creative/authorship domains" restriction for this invocation only. Grounding shifts, it doesn't disappear: work must stay consistent with the user's own established voice and prior work in that domain — continuity with what exists, not invention from nothing. Where no compile/render check applies, the verification gate (§3) *is* the continuity check.
- **`daytime`** — for a shorter daytime absence. Every other discipline stays at full strength (not a lower-rigor mode), but scope selection should bias toward something completable well inside the shorter window.

Record whichever mode ran (`default` if none named) in the ledger's `mode` field (§5).

## 2. The discipline (non-negotiable, not a style choice)

- **Build meta-tooling/baseline before changing behavior**, when a baseline doesn't already exist.
- **Never decide a genuine architectural fork alone.** Implement the safe/minimal version, and name the fork explicitly in the landing doc's "recommended next moves" table instead of picking for the user.
- **No invented content in the user's own creative/authorship domains** (lore meanings, SSOT.md prose, character/world content). Verifiable, forced-by-substrate work only, unless the user has explicitly opened that domain for this invocation.
- **One well-verified thing beats several padded ones.** Don't stretch scope to look more productive.

## 3. Verification gate — must pass before any commit

Two shapes, pick whichever fits the surface actually touched:

**Compiled/rendered surface** (Rust, shaders, anything with a build step):
- `cargo build` (or the project's equivalent) clean.
- Relevant test suite green — narrowest scope that covers the change, then confirm nothing wider broke.
- If a visual/behavioral smoke test applies (`scripts/render-smoke.ps1`), run it and check both that it still passes and that the diff matches what should and shouldn't have changed. A byte-identical screenshot alongside a changed log line is real proof of isolation, not a formality.

**Scripted/CLI surface** (Python, PowerShell, anything with no compile step):
- Invoke the actual command for real, not a syntax check.
- Independently cross-check at least one real finding against raw data, bypassing your own new code entirely — the CLI-shaped equivalent of the byte-identical screenshot. Worked example: `CLAUDEBASE/nightlies/records/2026-07-08_zombie-c1.md`.

Do not commit on a failing or unverified gate, on either path. Revert cleanly rather than leaving a half-working change in the tree.

## 4. The landing doc

Write to `claude/mailbox/SESSION_<YYYY_MM_DD>_<TOPIC>_AUTONOMOUS_NIGHT.md`, frontmatter:

```yaml
---
type: session-handoff
session: <this session's id>
date: <YYYY-MM-DD>
author: claude
lane: <short-topic-slug>
context: autonomous continuation while user slept
---
```

Body, in this order: what was found (including anything memory/planning claimed that the live code didn't back up), what landed (files + why, not a diff dump), the architectural fork(s) named but not decided, a "recommended next moves" table, a short honest tone note (no padding), a plain sign-off.

## 5. The nightlies ledger

Every invocation writes to `CLAUDEBASE/nightlies/`, alongside (not instead of) the mailbox landing doc. Full schema in `CLAUDEBASE/nightlies/README.md`: a new `records/<date>_<lane-slug>.md` plus one appended row in `LEDGER.md` (never edit past rows). The ledger is the deterministic, compounding surface the landing doc can't be — structured fields across every run vs. one prose account per reader.

## 6. Commit

Commit autonomously, including through this repo's auto-push-on-commit hook — a default, not a law: if the verification gate didn't fully pass, or the change needs the name-don't-decide treatment from §2, stop short and say so in the landing doc instead.

**Check the index before staging, every time.** `git status --porcelain` first; if anything unexpected is already staged, `git reset HEAD --` before adding your own files; stage only the exact files this invocation touched, by name — never `git add -A`/`git add .`. If the tree has other unrelated uncommitted work, name it in the landing doc for the user's own call — deciding how to batch it is not this skill's job. Real near-miss, not hypothetical: `CLAUDEBASE/nightlies/records/2026-07-08_zombie-b3.md`.

## 7. Close the loop — retrospective self-improvement (mandatory, not optional)

Every invocation ends with one more pass: review the run for any place this skill's own design had a blind spot or near-miss, independent of whether the target task itself succeeded. If a real gap surfaced: name it, fix it in this same `SKILL.md`, and record it in both the landing doc's tone note and the ledger's `self_improvement` field. If nothing surfaced: say so explicitly — that's a valid outcome, not a failure to find something.

**Re-verifying an edit to this file means reading the edited content, not running `skill_audit.py`.** Its Claude-flavor check confirms four shallow things — `SKILL.md` exists, frontmatter has `name`/`description`/known `allowed-tools` — and never reads the body (commit `c6feb985`). After any edit: manually trace every `§N` cross-reference against the current header list and confirm each one resolves.

Ask a second question too: did any part of this run land at a lower standard than a live session would get, because no one was watching? Not about the skill's design — about whether the standing quality bar actually held. Name it as honestly as any other finding if so.

Ask a third: classify this run's commits as `feature` or `meta` (§5's `commits` field), and check the ratio honestly — meta must be the exception, not the main deliverable (worked example and why it matters: commit `c5af8cc8`). Then check the result against `CLAUDEBASE/nightlies/MATURITY.md`, the user's own scorecard for this skill — reassess the score there if this run's evidence moves it, but don't add new mechanism here just to chase a higher number faster than real runs earn it.

This is nightly's own scoped, immediate cousin of the `self-upcycle` skill's pattern — direct and same-invocation rather than deferred behind an occurrence threshold, since nightly runs happen too infrequently for "wait and see" to be worth it. Do this by default, every run, without being asked.

## What this skill deliberately does not do

- Does not pick atlas §2/§3 items (externally blocked, or genuinely foundational) without the user naming them directly.
- Does not spawn subagents by default — single-threaded, direct execution keeps the landing doc's account exhaustive and trustworthy. Only reach for Agent/Workflow if the scope genuinely needs it, and say so in the landing doc.
- Does not have a Codex-lane counterpart yet — flag this if cross-lane parity ever matters here.
- Does not resolve, by itself: what triggers scope selection when the atlas is stale, how rigid "when to stop" should be, or whether landing-doc frontmatter should be schema-validated. Open questions, not decided by writing this file.
