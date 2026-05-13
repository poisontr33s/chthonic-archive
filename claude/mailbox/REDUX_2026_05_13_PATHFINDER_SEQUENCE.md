# Redux — Pathfinder sequence, 2026-05-13

Written in plain voice. No ceremony. Action-first.

## The thing that actually happened

Codex landed commit `27a21d7f` "Enhance link auditing and GitHub URL handling" — +736 lines into `scripts/link_audit.py`. The commit is plain-prose, the diff is real engineering. But the contract broke in three specific ways:

1. **Scope creep with no triage layer.** Codex added GitHub URL detection, live web checks, anchor validation, HTML href extraction. Useful, all of it. But every new check fires AMBIG/BROKEN warnings against the existing repo, and the pre-commit hook treats AMBIG as a hard fail. Result: 220+ surfaced issues, no path to ship anything new without grinding through them.
2. **Strictness without graceful degradation.** AMBIG is "this basename matches multiple files in the repo." That's a warning, not a bug — most AMBIG links *resolve fine* (we measured: 140 of 167 in the 8 currently-flagged files). Treating it as error-level produces binary states: commit blocked / commit unblocked. No middle gear.
3. **No orientation update.** The user lost the thread on what was committed vs. uncommitted because nobody wrote "here's where we are." The +736-line diff became "WIP I shouldn't touch" in my read; in reality it had already landed.

## Chronology — today's commits, oldest first

| Commit | What it is | Agent |
|---|---|---|
| `eb2077c3` | Iron Maiden sabotage — Claudine proprietorship notice | (pre-session) |
| `ad2e28a2` | Rename IronMaiden, update Pentea refs | (pre-session) |
| `04770546` | session-normalizer (raw paste → vampire-compatible JSONL) | Claude |
| `ad5a855d` | workspace:open script for polyrepo dropdown | Claude |
| `ca376fac` | author-filtered wrapper + polyrepo satellite orchestrator | Claude |
| `6365687a` | batch link_audit invocations to dodge Windows cmdline cap | Claude |
| `27a21d7f` | **Enhance link auditing and GitHub URL handling** — Codex's rewrite | Codex (broken contract) |
| `b5b7000d` | apply link-rot auto-fixes across 28 markdown files | Claude |

Codex's commit sits in the middle. My work both predates it (the session-normalizer, the workspace open, the author-filter, the batch fix) and post-dates it (the rot auto-fix). I built on top of Codex's pathfinder without realizing it had landed already.

## What's burning at the core

These are the structural issues, not the surface ones:

1. **AMBIG-as-error is wrong policy.** Single highest-leverage fix in the repo right now. Tuning this unblocks 8 immediately-commitable files and stops future false-positive commit failures.
2. **27 truly-broken links remain.** Mostly fixable via git rename history (one specific commit `dc42cac8` "docs: consolidate documentation sprawl" caused most of them). One-shot script run, no new permanent tool.
3. **No orientation artifact exists.** User can't find what they have. Three sessions deep in the same repo and "which files do what" requires a fresh exploration every time. One short `claude/mailbox/CURRENT_STATE.md` would fix that.
4. **Multi-agent handoffs have no scope contract.** Codex did things outside the user's intent because nothing said "do exactly these N things, return when done." Loose handoffs invite scope creep.
5. **The metadata orchestra keeps growing.** Every fix is a clean diff; the aggregate is more weight. New rule for going forward: every additive change must point at a deletion or consolidation. No net-positive code growth without justification.

## What worked today (lessons to keep)

- **Failure-as-fuel framing.** The audit output literally tells you the fix. `bun run links:fix:all` applies them. That's good design.
- **Author-filter scoping.** Restricting audits to user-authored markdown excludes satellite junctions cleanly. Worth keeping.
- **Batched invocations.** Solves a real Windows constraint, will not regress.
- **One-shot diagnostic scripts, then deleted.** `_diag_ambig.py` lived long enough to answer one question and was removed. That's the right ratio for ephemeral tools.

## What didn't work (lessons to encode)

- **Treating uncommitted work as sacred.** I was protecting Codex's "WIP" that was actually committed history. Symptom of not running `git log` first.
- **Hard gates without escape valves.** A pre-commit hook that can't be soft-bypassed for known-acceptable issues blocks legitimate work.
- **Plan documents that propose new tools.** My initial three-task plan added a new normalizer, a new wrapper, a new orchestrator. Each was clean. The aggregate adds to the orchestra. Going forward: prefer tuning what exists.

## Redux — sequenced next moves

In order, smallest-first, each independently revertable:

### Move 1: Tune AMBIG severity (`ci/run.ts`)

Highest leverage. One file. Make AMBIG produce a `[WARN]` line that prints but doesn't return non-zero. Keep BROKEN and EMPTY as hard errors. 8 currently-blocked files become commitable immediately.

### Move 2: Build rename-aware fixer for the 27 truly-broken links

One-shot script (`scripts/_fix_rot_via_rename.py`, removed after use). Reads `git log --diff-filter=R --name-status`, builds a path→new-path map, applies rewrites where the broken link target was renamed historically. Targets the 8 unstaged files plus any other rot. Run it, commit, delete the script.

### Move 3: Write `claude/mailbox/CURRENT_STATE.md`

One page, max. Sections: "what's where", "what's working now", "what's broken", "where to look for X". The orientation artifact the repo has needed for months. Replaces nothing currently exists, so it's net-additive but only one file and explicitly aimed at solving the orientation problem.

### Move 4: Scope contract template for triad handoffs

A 10-line markdown template in `claude/mailbox/_templates/` that the user fills out before sending any cross-agent task. Forces explicit scope: do these N things, stop when done, return verbatim. Optional, low-cost.

### Move 5 (deferred, not now): Audit `docs/` for staleness

The metadata orchestra cleanup. Big, separate work. Not until 1–4 are done and you decide it's worth the day it'll take.

## What I am about to do

Move 1. Tuning AMBIG in `ci/run.ts`. Then I'll show you the diff before staging it. After that, ask whether to proceed to Move 2 (rename-aware fixer) or pause.

The 8 unstaged `.md` files stay where they are until Move 1 lands — at that point they become commitable without the AMBIG block.

---

## Addendum — what actually happened (written 2026-05-13, end of session)

The redux above is the plan I wrote at the start. Recording what diverged
and why, so future-me/future-Claude reads both and learns from the gap.

### What landed in order

- Move 1 went smoothly. `cbb41515` softened AMBIG; 8 blocked files
  immediately became commitable.
- Move 4 landed early — the scope contract template, including the
  Stakes section that the user's "melatonin without consequence" metaphor
  made non-negotiable. Receiving agents must echo the contract before
  starting; no echo, no execution.
- Move 2 (rename-aware fixer) and Move 3 (orientation doc) collapsed
  into a single richer artifact: the git-rot index. The user named the
  shape: "use all the types of ROT to develop structured data, categorize
  them to error code numbers and relationships." That became
  `scripts/git_rot_index.py` plus the ROT-/CLUSTER-/ROOT- taxonomy. The
  index found that 78% of rot lived in three agent-generated hotspots —
  which we then marked `lifecycle: tombstone`, dropping the living-repo
  rot count from 2151 to 463.

### The hour-long hang (preserved as learning, not glossed)

Between schema v1 and schema v2 I introduced a balanced-paren regex
to handle parens-in-URLs (the IronMaiden case). It passed quick local
tests on the biggest files. It then hung the indexer for ~one hour
of wall-clock with zero output, on the first file of the actual
corpus. The user named it: "It's been an hour since it started. Can
we be sure that we are doing this the best way?"

What went wrong: I declared a tool "done" without a smoke test on
the real corpus. Catastrophic regex backtracking is exactly the kind
of failure that local testing on cherry-picked inputs misses.

What saved it: the user's patience to ask the question, my willingness
to admit the runaway and kill it instead of "letting it finish." The
fix was a one-line revert to the simpler regex. End-to-end wall time
went from "hour with no result" to 4.4 seconds.

Pattern to encode forever: **smoke-test on real data before declaring
done.** Run the new tool against the actual corpus with progress output.
If it doesn't print progress within the first few seconds, it's hung
or in pathological territory. Don't wait an hour to find out.

### What changed in how I work (saved as memory)

Two durable feedback rules saved this session, both addressed to
future-Claude reading this:

1. `feedback/stakes-language-not-rule-language` — agents need
   consequence to internalize architecture. Rules alone don't land.
   The scope contract's Stakes section is the canonical example.

2. `feedback/declare-next-dont-ask` — never "if you want me to..."
   The user trusts initiative; option menus read as exhaustion. Declare
   the next move in the imperative; the user adjusts or overrides.

### Where to pick up next session

- Open `claude/mailbox/SESSION_2026_05_13_LANDING.md` first — that's
  the re-entry doc.
- Next operational move: extend rot taxonomy with GIT-001 (zero-history
  tracked files) and ROOT-001 (mass-rename root commits). Both are
  natural extensions of the existing index.
- 88 ROT-001 + 99 ROT-002 entries await human-judgment triage when
  ready. Not urgent; the rot index keeps surfacing them on each run.
