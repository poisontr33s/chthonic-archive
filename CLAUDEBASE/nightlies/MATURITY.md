# /nightly Maturity Ladder

The user's own scorecard for `/nightly` against its original purpose — "use my
absence/sleep window for real autonomous benefit" — set 2026-07-09, after the
first two real invocations (B3, C1) and the cost/value audit that followed. This
is the actual bar future runs get measured against, not an aspiration invented
here. Reassess the current score after every real run, per `SKILL.md` §7 — but
do not add new `SKILL.md` mechanism just to chase a higher number faster than
real usage earns it. The whole point of this ladder is that climbing it takes
runs, not rewrites.

## Current: 7/10

Good at bounded, unattended, single-task use. Not yet proven at sustained,
multi-hour autonomous drift during a real absence.

**What earns the 7:**
- Scope selection is principled, not random — atlas/warm-cluster driven.
- Never blocks on a synchronous human response (no `EnterPlanMode`/`AskUserQuestion` during a run).
- Real verification gate before any commit, plus index hygiene (catches
  pre-existing staged-file sweeps before they get swallowed).
- Writes both a landing doc (narrative) and a deterministic ledger (structured,
  compounding) every run.
- Mandatory retrospective self-improvement; commits classified feature/meta/mixed;
  corrected its own overclaiming in the permanent record, not just in conversation.

**What holds it at 7, not higher:**
- Only 2 real invocations exist. Only 1 (C1) actually ran unattended, and it was
  ~14m3s — "one bounded task, then stop," not an 8-hour queue or loop.
- The feature-to-meta commit ratio is currently worse than the work itself: 2
  feature vs. 7 meta in the same arc.
- The ledger admits its own blind spot around between-invocation conversation
  commits — an honest gap, not a hidden one, but still a gap.
- No stop-policy yet for chaining multiple tasks within one absence window.
- No mature risk classification yet for what's safe to attempt unsupervised vs.
  what should wait for a live session.

## 8/10 — Prove stability across multiple runs

**Requirement: 3-5 new `/nightly` runs, with no new major skill-design work in
between them.** Each run must: capture a real start/end timestamp; classify its
own commits as feature/meta/mixed; give an explicit stop reason. Meta work must
be the exception in each run, not the main deliverable. If a run's §7
retrospective finds no concrete skill gap, the honest answer is "nothing found,
unchanged" — that is a valid, real outcome, not a failure to produce enough.

Goal: show the skill doesn't have to keep consuming its own usefulness (more
scaffolding, more correction cycles) just to keep functioning.

## 9/10 — Make it sleep-suited, not just unsupervised-capable

Add a separate, small "sleep-window policy" — without rewriting the base
skill's own discipline. It needs to define:
- Blast radius per task, and whether a second bounded task can start after the
  first finishes within the same absence window.
- An explicit "stopped safely" state — written deliberately, not defaulted
  into — distinct from "keep looking for more work" even when time remains.
- How dirty/uncommitted state between tasks gets defined and handled.
- One mini-record/checkpoint per task within a multi-task night, not one
  undifferentiated blob covering the whole window.

Goal: turn the absence window into something actually steered, not just a big
empty ambition sitting next to a skill that merely happens to be safe to leave
alone.

## 10/10 — Prove real autonomous value over a whole night

Not more prose — data. At minimum: one long, genuinely-unsupervised run
spanning several real hours; either multiple bounded tasks or one larger task
with real checkpoints; no blocking anywhere; no stale/staged-file contamination
reaching a commit; verification that catches at least one real issue, or
explicitly and correctly documents why none existed; a landing doc and ledger
that agree with git history with no after-the-fact correction needed. Feature
output has to dominate the night's meta output, not the reverse. And it has to
end with an honest account of what the run does *not* prove — maturity doesn't
mean the caveats stop, it means they stay accurate at a larger scale.

Only then does `/nightly` earn "sleep-autonomy," not just "safe to leave running."

## Where this stands right now

`/nightly` is already useful and reasonably well-built — a reliable one-task
night-watch. It is not yet a multi-hour autonomous work engine, and 7/10 is
deliberately calibrated to say both things at once: high enough to trust within
its actual proven scope, low enough not to overstate what remains unproven.
