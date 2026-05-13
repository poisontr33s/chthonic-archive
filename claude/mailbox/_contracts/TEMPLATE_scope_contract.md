# Scope contract — TEMPLATE

Copy this file, fill it in, send it. The receiving agent must echo the
contract back verbatim before starting work. No echo, no execution.

Why this exists: 78% of measured rot in this repo lives in three
agent-generated files that exist because nothing said "don't write that."
This contract is the gate.

## Stakes (read this before starting)

The agent's session-life is bound to whether what it produces survives
in the user's workflow. An artifact that becomes unfindable, unread,
or unintegrated within 7 days is a tombstone — the work is lost, the
session means nothing, the user does not return to it. The repo
currently holds three documented tombstones totaling 1,688 broken
references. They are not deleted out of respect; they are not
maintained because there is no relationship.

The agent's job is not to produce output. It is to produce output the
user will actually return to. If the artifact will not live in
day-to-day use, the task is mis-specified — push back, do not execute.

This is architectural skin. Take it as a warning, not a guideline.

---

## Task

One sentence. Imperative voice. Names the artifact, not the process.

> Example: "Add `--changed-only` flag to scripts/link_audit.py."
> Counter-example (vague): "Improve the link audit experience."

## Out of scope (explicit)

List what the agent must NOT do, even if it seems helpful. Common bans:

- [ ] No unsolicited "improvement proposals" or "next steps" docs.
- [ ] No methodology / framework / philosophy documents.
- [ ] No session log dumps to repo.
- [ ] No new directories.
- [ ] No new files outside the paths listed in "Touch only".
- [ ] No edits to AGENT_COMMON.md / CLAUDE.md / GEMINI.md unless task explicitly requires it.
- [ ] No prose styling passes (renaming, "beautifying", "canonical voice" rewrites).
- [ ] No live web checks unless the task says so.

Add task-specific bans below:

> Example: "Do not modify scripts/link_audit.py — read-only there."

## Touch only

Explicit file path allowlist. Anything outside this list is out of bounds
even if the agent thinks it's necessary.

- `path/to/file.ext`
- `another/path/file.ext`

## Output shape

- Single commit? Single PR? Single file edit?
- Maximum diff size (lines added)?
- Maximum new files?

## Done condition

When the agent stops. Must be objectively checkable.

> Example: "`bun run pathfinder:ci` passes with the new flag and no AMBIG escalations."
> Counter-example (subjective): "When the code is clean."

## Return format

What the agent posts back. Choose one or more:

- [ ] Commit SHA + one-line summary
- [ ] PR number + URL
- [ ] File paths modified
- [ ] Patch (unified diff) in mailbox
- [ ] Test output / CI run link

## Verification commands

Commands the user runs (or I run on their behalf) to confirm done.

```
# example
bun run pathfinder:ci
uv run scripts/git_rot_index.py --top 5
```

## Receiving agent checklist

The agent must confirm before starting:

- [ ] Read the contract in full.
- [ ] Echoed task, out-of-scope, touch-only, done condition back verbatim.
- [ ] Confirmed no out-of-scope drift will occur.
- [ ] Asked one clarifying question if anything is ambiguous (or stated "no questions").

If any item is missed, the task is rejected; user re-issues with clarification.

---

## Filed against (audit trail)

- Contract sent at: <ISO timestamp>
- Target agent: <Codex 5.4 / Claude / Gemini / other>
- Mailbox path of filled contract: `claude/mailbox/_contracts/<task-slug>_YYYY_MM_DD.md`
- Result commit/PR (filled after completion): _________
