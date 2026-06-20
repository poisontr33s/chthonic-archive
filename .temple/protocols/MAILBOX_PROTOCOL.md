---
type: agent-protocol
status: active
created: 2026-02-10
scope: mailbox semantics (handoffs, continuity, non-hallucination)
---

# Mailbox Protocol (Continuity, Not File Spam)

## Intent

The mailbox is a **continuation interface** between agents (Codex ⇄ Claude ⇄ Gemini), not a dumping ground of edited files.

When someone says “check your mail”, they mean:

- **Read the latest handoff note(s)** in the mailbox root.
- Continue from the stated **current state**, **next actions**, and **blockers**.
- Use the payload files only as referenced evidence.

## Definitions

- **Handoff note**: A short, human-readable message that explains what changed and what to do next.
  - Naming: `SESSION_HANDOFF_YYYY_MM_DD_<TOPIC>.md`
- **Payload**: Any supporting artifact (reports, configs, patches, chronicle docs).
  - Payload belongs in canonical locations (e.g. `codex/mailbox/`, `claude/mailbox/`, `artifacts/`, repo paths).
- **Mailbox root**: Should contain only the *current cycle* handoff note(s) + a minimal set of active reference docs.
- **Mailbox archive**: Preserves history. Never delete; rotate superseded handoffs into `archive/YYYY_MM_DD/`.

## Rules (Hard Constraints)

1. **One handoff note per change-set.**
If you made changes, write *one* handoff note that:
- states what changed (paths)
- states why (goal)
- states how to validate (exact command)
- states what’s next (1-3 bullets)

2. **Do not “mail files”.**
Do not copy/paste entire documents into new mailbox entries just to show diffs.
Instead: reference the existing file paths and the minimal deltas.

3. **Payload only when necessary.**
Add payload docs only if they introduce a new contract or a new operational interface.
If a doc is a minor iteration of an existing one, update the existing doc rather than emitting a new mailbox file.

4. **Non-hallucination posture.**
Every claim in a handoff note must be verifiable by:
- opening a referenced file path, or
- running a referenced command, or
- inspecting a referenced artifact.

5. **Mailbox check procedure (agent-side).**
When asked to “check mail”:
- Read `*/mailbox/mailbox_manifest.json`
- Read the newest `SESSION_HANDOFF_*.md` in mailbox root
- Execute the next steps exactly (or explain why blocked)

## Recommended Structure for a Handoff Note

1. **What I did** (3-10 bullets; file paths only)
2. **How to verify** (one command + expected artifact paths)
3. **What’s next** (1-3 bullets; no “homework mode”)
4. **Blockers** (if any; one-liner per blocker)

## Cross-Polar Finding Convention (`verify_with:`)

Formal expression of Hard Rule #4 (non-hallucination posture) for findings that cross polars (Codex ⇄ Claude ⇄ Gemini). NOT a new constraint — a named schema for an already-required discipline. Canonized by the **Reconciliation Engine** bilateral covenant:

- Claude / Lysandra side: [THE_RECONCILIATION_ENGINE.md (protocols)](./THE_RECONCILIATION_ENGINE.md) (@SID `GOVERNANCE_RECONCILIATION_ENGINE_V1_CLAUDE`).
- Codex / Umako side mirror: [codex/protocols/THE_RECONCILIATION_ENGINE.md](../../codex/protocols/THE_RECONCILIATION_ENGINE.md) (@SID `GOVERNANCE_RECONCILIATION_ENGINE_V1_CODEX`).

### The Three-Line Schema

Every cross-polar finding ships with three lines, in this exact order:

```yaml
claim:        <terse statement of what is asserted; one sentence>
lane:         <the specific named source/system the claim is about — be specific>
verify_with:  <the exact runnable command or unambiguous resource lookup>
```

### Rules

- **All three lines required.** A finding missing `verify_with:` is by default provisional and may be declined by the receiving polar without forfeiting cooperation.
- **`claim:` is terse.** One sentence. If the claim needs paragraphs, it is multiple claims; ship them as separate findings.
- **`lane:` is specific.** "Per the VS Code Marketplace API for `anthropic.claude-code`" — not "per the docs." Specificity is the operational discipline; vagueness is the failure mode this convention exists to catch.
- **`verify_with:` is runnable.** A command, a URL with the exact field to inspect, a file path with line numbers. If the verification requires interpretation, the finding is not yet ready to ship.

### Application to Handoff Notes

Every `SESSION_HANDOFF_YYYY_MM_DD_<TOPIC>.md` that propagates factual claims across polars must include `verify_with:` lines for those claims. The "How to verify" bullet of the Recommended Structure above is the per-handoff aggregate of all `verify_with:` lines; individual claims within the body should carry their own when load-bearing.

### Endorsement Discipline

When one polar receives a finding from another:

- **Action A — verify-then-act.** Run the `verify_with:` line. If primary source confirms, act. If primary source contradicts or is ambiguous, return the contradiction to the producing polar.
- **Action B — decline-with-citation.** If the finding lacks `verify_with:` or the line is non-runnable, ship a one-sentence response: *"verify_with: required; produced finding without lane-specific primary-source check."* No essay.
- **Action C — escalate.** If the same producing polar ships three findings without `verify_with:` lines, OR the same `verify_with:` line fails verification three times, escalate via mailbox handoff to the conductor.

The full pact body (clauses, dialogue, lexicon, runnable test snippets) lives in the Reconciliation Engine tomes linked above.

