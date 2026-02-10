# CONTEXT SURGERY HANDOFF — 2026-02-10

**From:** Copilot CLI (Senior Steward session)
**To:** Codex (IDE agent)
**Priority:** READ BEFORE ACTING

---

## What Changed

5 files in `.github/instructions/` were renamed from `.instructions.md` → `.reference.md` to stop them from being auto-loaded into every agent session.

### Renamed Files

| Old Name | New Name |
|----------|----------|
| `mathematical-engines.instructions.md` | `mathematical-engines.reference.md` |
| `magistra-logic.instructions.md` | `magistra-logic.reference.md` |
| `asc-entity-generation.instructions.md` | `asc-entity-generation.reference.md` |
| `behavioral-scenarios.instructions.md` | `behavioral-scenarios.reference.md` |
| `reference-appendix.instructions.md` | `reference-appendix.reference.md` |

### Updated Cross-References

- `.github/pathstofiles.md` — Updated with Tier 1/Tier 2 distinction
- `.github/copilot-instructions.md` — Updated with context budget rules

### NOT Updated (Historical — Leave As-Is)

- `copilot-instructions.archive.md`, `copilot-instructions-copy.md` (archive snapshots)
- `strip_ssot*.py`, `purify_ssot.py` (utility scripts with embedded old names)
- `SSOTI_FIED_SESSION_LOG.md` (historical session log)
- `PHASE4_LINK_VALIDATION_2026_02_01.json` (validation snapshot)
- `broken-refs.json` (old reference scan)

---

## Why

~154K chars (~38K tokens) were being auto-loaded before any conversation. This caused token resets after 2-3 messages in the IDE. After surgery: ~54K chars (~13K tokens). That's a 65% reduction.

---

## Standing Order for Codex

**DO NOT:**
- Create new `.instructions.md` files without explicit user approval
- Rename `.reference.md` files back to `.instructions.md`
- "Fix" things that are working — this includes the current Tier 1/Tier 2 split
- Attempt to re-consolidate or re-structure instruction files

**DO:**
- Reference `.reference.md` files on-demand when their content is needed
- Respect the context budget: ≤6 Tier 1 files, ≤35K chars total auto-loaded
- If you need entity generation, validation, or math engine protocols, read the `.reference.md` file explicitly

---

## Verification

After this handoff, the auto-loaded `.instructions.md` files should be exactly:
1. `ankh-workflow.instructions.md` (3.1K)
2. `autopsy-protocol.instructions.md` (2.3K)
3. `project-workflow.instructions.md` (5.9K)
4. `python-scripting.instructions.md` (5.8K)
5. `ssot-toolbox.instructions.md` (8.0K)
6. `technical-directives.instructions.md` (8.1K)

Total: ~33.2K chars. If you see more than 6 `.instructions.md` files, something drifted.
