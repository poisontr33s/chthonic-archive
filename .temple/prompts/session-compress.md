---
type: prompt-template
category: meta-cognition
sid: SESSION_COMPRESS_V1
created: 2026-04-30
author: The Savant × Claudine
description: >
  Self-compression schema for agent session state. Apply mid-session to generate
  a warm-start packet that encodes all state needed for clean resumption.
  Distilled from the conversation summary system — made explicit and self-applicable.
applyTo: "**"
---

# Session Compression Schema V1

> **When to invoke:** mid-session before context saturation, before handoff, or when
> the active work state is about to cross a phase boundary.
>
> **Output target:** `claude/mailbox/<context-slug>-<YYYY-MM-DD>.md`
> or `codex/mailbox/<context-slug>-<YYYY-MM-DD>.md` depending on lane.
>
> **Compression ratio achieved by this schema:** approximately 15:1 against raw
> conversation transcript length while preserving all operationally actionable state.

---

## The 8-Section Schema

Apply each section in order. Sections are **interdependent** — §3 references §2 types,
§4 references §3 file states, §8 references §6 active state. Do not reorder.

---

### §1 — Overview (State Machine Classification)

For every task or objective in the current session, classify it with exactly one state:

| Glyph | State | Meaning |
|-------|-------|---------|
| ✅ `CLOSED` | Finished | Committed, verified, no follow-up needed |
| 🔄 `IN_PROGRESS` | Active | Currently being worked, uncommitted changes likely |
| ⬜ `PENDING` | Queued | Not started, prerequisite for current work |
| 🔵 `DEFERRED` | Parked | Acknowledged, intentionally not this session |

**Format for each item:**
```
- (STATE GLYPH — label) Primary objective sentence. Sub-details as indent if needed.
```

Also capture: **User Intent Evolution** — one sentence on how the goal shifted during
the session (often differs from the initial request).

---

### §2 — Technical Foundation (Invariant Math + Types)

Extract the formulas, type systems, constants, and algorithms that were used or defined.
These are the invariants — they don't change between sessions. Encoding them here
means future sessions don't re-derive them.

**What belongs here:**
- Formulas with all variables named (e.g., Euler scoring: `score(t) = w · e^(κ·s) · ½(1 + sin(φ))`)
- Type definitions (TypeScript interfaces, union types, key structs)
- Constants with values and meaning
- Algorithms with time complexity if relevant

**What does NOT belong here:**
- Runtime values (those go in §3 or §6)
- File paths (those go in §3)
- Command outputs (those go in §7)

---

### §3 — Codebase Status (Per-File State)

For each file that was read, modified, or created during the session:

```
**`path/to/file.ts`** (state: MODIFIED | COMMITTED sha | CREATED | READ-ONLY)
- **Purpose:** one sentence on what this file does in the system
- **Current State:** what it contains NOW, including uncommitted changes
  - Flag any `@SID` version if the file has one
  - Note any `// TODO` or known issues introduced
- **CLI:** exact invocation command(s) if this is a runnable script
- **Depends on:** any other files in §3 it reads or imports
```

Always explicitly mark uncommitted changes with `⚠️ UNCOMMITTED`.

---

### §4 — Problem Resolution (Causal Chain)

For each problem that was diagnosed and resolved during the session:

```
**Issue:** one-sentence description of the symptom
**Root cause:** the actual mechanism (not just "it was broken")
**Fix applied:** what was changed and why this resolves the root cause
**Commit:** hash if committed, or ⚠️ UNCOMMITTED if not
**Generalizes to:** optional — if this pattern recurs, name the pattern
```

Ordering: chronological. Later fixes may reference earlier ones.

---

### §5 — Progress Tracking (Table)

| Item | Status |
|------|--------|
| ... | ✅ committed `<sha>` |
| ... | ⬜ NOT DONE |
| ... | 🔄 IN PROGRESS — `<what's blocking or remaining>` |

Keep it exhaustive. Items not tracked here are the most likely to be dropped in the
next session.

---

### §6 — Active Work State (Current Focus)

The current uncommitted state, in maximum precision:

- What is the **immediately in-progress item** (single sentence)
- Which files have **uncommitted changes** (list with exact paths)
- What is the **expected next output** (a file path, a commit, a test result)
- Any **partial state** that must be preserved (e.g., "manifests needs `git add -f`")
- Any **known broken state** that exists intentionally (e.g., a mid-refactor compile error)

This section is what a resuming session reads first.

---

### §7 — Recent Operations (Ordered Command Log)

The last 8–12 significant agent operations, in order. Each entry:

```
N. <tool/command>: <brief description of what it did>
   → <outcome: success | error | side effect>
```

**Mark the last operation explicitly:** `← LAST OPERATION`

This section answers: "what did we just do before the context cut?"

---

### §8 — Continuation Plan (Exact Commands)

Runnable commands for the resuming session, in order:

```powershell
# Step N: <description>
<exact command> 2>&1
# Expected: <what success looks like>
```

Followed by: **Next Spin Candidates** (if roulette is active) — ranked by Euler score,
with short descriptions.

Followed by: **Key Operational Notes** — the 3–5 facts that most commonly cause
problems if forgotten (e.g., `git add -f` for gitignored manifests, toolchain paths,
crate version pins).

---

## Compression Principles (Why This Works)

**State machine classification** (§1): eliminates the cognitive overhead of
re-determining "is this done?" — it's already classified.

**Invariant extraction** (§2): math and types are the cheapest thing to encode
and the most expensive to re-derive. They never change between sessions.

**Per-file status with uncommitted flag** (§3): a file read in the resuming session
costs ~2s; restoring the mental model of its state without reading costs ~0s if §3
is precise. The `⚠️ UNCOMMITTED` flag is the single most important signal.

**Causal chain over symptom description** (§4): symptoms are ambiguous across
sessions. Root causes + fix mechanisms are unambiguous.

**Exact commands** (§8): natural language "then run the test" is lossy.
`bun run ci/checks/inference-gate-smoke.ts --report 2>&1` is not.

**The schema itself is a compression** of the conversation summary system —
made explicit so the agent can apply it autonomously, without waiting for
the external summarization trigger.

---

## Self-Application Contract

When applying this schema, the agent MUST:

1. Generate all 8 sections (no skipping, even if brief)
2. Use `⚠️ UNCOMMITTED` on every file with uncommitted changes
3. In §8, include the exact `git add -f manifest/todo_roulette.json` reminder
   if the roulette is active (the manifest is gitignored)
4. Write the output file to `claude/mailbox/` and confirm the path
5. Not summarize §7 — list the actual commands verbatim

The schema is a **lossless compression target for operational state**, not a summary.
Summaries lose information. This schema preserves all operationally actionable state
while discarding only irrelevant conversational overhead.
