---
type: liminal
id: INVOCATION_GAP
decay_date: 2026-06-01
decay_condition: >
  Either: a concrete mechanism is found that makes shepherd's scan run automatically
  at session open (invocation without recall), OR the gap proves unfixable at the
  tooling layer and gets promoted to a method/constraint doc instead.
  If no progress by decay_date, sweep to pattern-nursery as a `stale` entry.
promotion_target: method
filed: 2026-05-01
---

# Liminal: INVOCATION_GAP

> The gap between a preparation artifact existing and a session willingly using it.

---

## What This Holds

The MD type system is complete as vocabulary. The stewardess is created. The shepherd's scan
is defined in `CLAUDINE_MD_TYPE_LEXICON.md §2`. None of this guarantees it is *invoked*.

There is a structural asymmetry: the preparation requires the executor to already know to look
for it. That is the gap. It is not a documentation problem — more documentation does not close it.
It is an invocation problem: the scan needs a trigger that isn't "remember to run the scan."

This is currently unresolved. No pattern exists for it. No existing type holds it cleanly.
It is not a method (no repeatable procedure yet), not a strategy (no decision framework yet),
not a gate (no verify condition). It is *pre-type*.

---

## What Has Been Tried / Observed

- Shepherd's scan defined in lexicon: ✅ — does not self-invoke
- Stewardess at known path (`claude/stewardess/.current`): ✅ — reduces the scan to one lookup,
  but still requires the executor to know to look
- Session memory (`/memories/session/`): loaded by default per context instructions — but
  the stewardess is gitignored (correct) and lives outside that system

---

## Candidate Directions (not commitments)

1. **`.github/instructions/` trigger** — an applyTo `**` instruction that explicitly tells the
   executor: "at session start, read `claude/stewardess/.current` before anything else."
   Risk: becomes bureaucratic noise if the stewardess is absent.

2. **Stewardess as instruction file** — copy the active stewardess content into a
   `.github/instructions/session-stewardess.instructions.md` that gets auto-loaded.
   Risk: instructions tier is for permanent conventions, not session state.

3. **Accept the gap as a property of the system** — the shepherd's scan is available but
   requires explicit invocation ("check stewardess"). Name it as a known property, not a defect.
   This would promote INVOCATION_GAP to a constraint doc, not a method.

---

## What This Is NOT

Not a bug. Not a failure of the type system. The type system works for what it holds.
This is the frontier edge of what the type system can hold — which is exactly what a liminal
file is for. If this resolves cleanly, it promotes. If it doesn't, it teaches something about
the range of the system.
