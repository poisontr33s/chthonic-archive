# Session landing — 2026-05-13

Short. Designed to be re-read in three weeks and still make sense.
Open this first when you come back to this thread.

## What happened today

A drift was caught and dissolved. Codex's pathfinder rewrite (commit
`27a21d7f`, +736 lines) had landed during a prior session with a
broken contract — useful capability bundled with over-strict gating
that blocked your commits. You came back, named the problem, and
switched lanes to Claude Code. From there we worked the redux.

## What's live now (with commit SHAs)

The work is real and committed; you can `git show <SHA>` to see any of these.

| Commit | What landed |
|---|---|
| `04770546` | scripts/session_normalize.py — raw paste → vampire-compatible JSONL |
| `ad5a855d` | `bun run workspace:open` — opens the polyrepo dropdown |
| `ca376fac` | scripts/link_audit_author.py — author-filtered + satellite orchestrator |
| `6365687a` | wrapper batches paths to dodge Windows cmdline cap |
| `b5b7000d` | apply link-rot auto-fixes across 28 markdown files |
| `cbb41515` | AMBIG severity = warning, not error (unblocks commits) |
| `44e6ad03` | git-rot index v2 + scope contract w/ stakes + 3 tombstones |
| `1ab5dfa2` | this landing page + redux addendum (postmortem of hour-to-4s) |
| `d905b8a4` | code-fence skip + 2 more tombstones + git_truth enrichment |
| `b7ff32c9` | ADR_RECOVERED.md tombstones (deletion-cluster fix, -20 refs) |
| `61e865e5` | SSOTIFICATION depth-bug resolved + 2 stub mailbox docs |
| `484f6a49` | suppress ROT-003 false positives by default (161 → 38 entries) |
| `5fa8b97a` | Gitological Ladder taxonomy — L1..L4 depth model |

## How to use what we built

### Want fresh diagnosis of repo rot
```
uv run scripts/git_rot_index.py
# writes manifest/git_rot_index.json + manifest/git_rot_index.md (digest)
# 4.4s end-to-end on this repo
```

### Want to hand off work to Codex / Gemini / another Claude
Copy `claude/mailbox/_contracts/TEMPLATE_scope_contract.md`, fill it in,
send it. Receiving agent must echo the contract back before starting.
No echo, no execution. This is the gate that didn't exist before.

### Want to mark a file as graveyard (acknowledged-dead)
Add to the file's YAML frontmatter:
```yaml
---
lifecycle: tombstone
tombstone_marked_at: YYYY-MM-DD
tombstone_reason: |
  Why it's dead. One paragraph.
---
```
The rot index and the CI pathfinder both honor this. File stays in
the repo; it stops counting against the living signal.

### Want the chronology of today's work
Read `claude/mailbox/REDUX_2026_05_13_PATHFINDER_SEQUENCE.md`.

## What we learned (preserved as durable memory)

- Stakes-language, not rule-language. Agents need consequence to
  internalize architecture. "Be helpful" doesn't land; "or this becomes
  a tombstone" does. Saved at `memory/feedback_stakes_not_rules.md`.
- Declare next, don't ask. "If you want me to..." shifts decision
  burden onto someone who trusts initiative. Saved at
  `memory/feedback_declare_next.md`.
- No more layers in chthonic-archive — prefer navigating existing
  tools to building new. The rot index is the exception: it
  consolidates orientation across multiple existing signals.
- Smoke-test before declaring done. The hour-long indexer hang
  (2026-05-13) happened because I introduced a clever balanced-paren
  regex without running it over the actual corpus. The fix was a
  one-line revert. Real-data test on every new tool before sign-off.

## Session arc — how rot collapsed

The data-led lane the user invoked carried itself, each rung surfacing
the next:

```
[2,151 baseline]   raw session-start rot count
   ↓
[ 463 ]  3 hotspot files marked lifecycle: tombstone
   ↓
[ 196 ]  code-fence skip + 2 more tombstones + git_truth enrichment
   ↓
[ 176 ]  ADR_RECOVERED.md deletion-cluster collapsed via tombstones
   ↓
[ 168 ]  SSOTIFICATION depth-bug: 8 of 15 links fixed
   ↓
[ 161 ]  SSOTIFICATION remaining 7: stub-created the 2 phantom targets
   ↓
[  38 ]  ROT-003 false positives suppressed by default
```

~98% reduction across one session. The remaining 38 are real work-list,
not noise: 12 ROT-001 typos/hallucinations, 16 ROT-002 basename-ambig
broken refs, 10 ROT-008 placeholder literals in skill templates.

## The Gitological Ladder (taxonomy you named)

The ROT codes aren't flat — they describe symptoms at different depths.
The 5fa8b97a commit made this explicit in the schema:

```
L4 LINEAGE   structural / causational (CLUSTER-001/002, ROOT-001)
L3 ANCHOR    positional / semantic (ROT-006, ROT-007)  [detectors pending]
L2 VIRTUAL   namespace / collision (ROT-003, ROT-004)
L1 SURFACE   raw symptoms (ROT-001/002/005/008)    ← where indexer lives now
```

Tombstone lifecycle is orthogonal — cuts across all levels.

## What's burning right now (open threads)

- 38 real entries in the default rot index, all L1 SURFACE. Per-file
  triage when ready. Not urgent.
- L3 detectors (ROT-006 anchor miss, ROT-007 line anchor stale) — slots
  exist in the taxonomy, code doesn't yet.
- L4 detector (ROOT-001 mass-rename ancestry) — slot exists, code
  doesn't yet. Would trace broken-link clusters back to the single
  historical commit that broke them (like `dc42cac8` did with the docs/
  consolidation).
- Two stubs at `claude/mailbox/BOUNTY_00000031_STEWARD_AUDIT.md` and
  `claude/mailbox/FORGE_PIPELINE_DEV_PLAN.md` exist as placeholders.
  Their planned content is still TBD.
- Iron Maiden / Pentea work was alive in WIP at session start; the
  in-flight changes had already landed in `27a21d7f` and `ad2e28a2`.
  No remaining WIP from that lane.

## What I'm carrying forward

Next operational move when you come back: build the L3 and L4 detectors
the ladder has slots for. The L1 indexer is mature; the next ladder
rungs are the natural extensions.

You don't need to remember any of this to re-enter. Just open this file.

The adventure continues.
