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

## What's burning right now (open threads)

- 88 truly-broken markdown links (ROT-001 in the rot index) — no
  rename-history match, no auto-fix possible. Some are typos, some
  point to files that were deleted (not moved). Manual triage when
  ready.
- 99 truly-ambiguous links (ROT-002) — basename collisions where the
  audit can't pick the right target. Human judgment per link.
- Three pre-existing graveyards (tombstones) are now named but not
  yet curated. Each is preserved as historical attempt; what they
  tried to be lives in their frontmatter `tombstone_reason`.
- Iron Maiden / Pentea work was alive in WIP at session start; the
  in-flight changes had already landed in `27a21d7f` and `ad2e28a2`.
  No remaining WIP from that lane.

## What I'm carrying forward

Next operational move when you come back: extend the rot taxonomy
with GIT-001 (zero-history tracked files — files committed once and
never touched again, likely abandoned), and ROOT-001 (mass-rename
roots — trace clusters of broken links to the single historical
commit that moved their targets). Both are extensions of the existing
index, not new tools. Both surface "structural truth from git" the
way you described.

You don't need to remember any of this to re-enter. Just open this
file.

The adventure continues.
