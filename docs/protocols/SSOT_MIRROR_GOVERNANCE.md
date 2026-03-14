---
title: "SSOT Mirror Governance"
type: protocol
status: active-wip
created: 2026-03-07
scope: ssot-mirror-authority
---

# SSOT Mirror Governance

## Purpose

Distinguish the live canon archive from synced mirrors, derived satellites, and backup residue so name-law and lore-law do not drift through accidental source confusion.

## Authority Order

1. `.github/copilot-instructions.archive.md`
2. `.github/codex-satellites/*.md`
3. `.github/copilot-instructions-copy.md`

> **Note (2026-03-14):** `.temple/architecture/copilot-instructions.archive.md` and `.github/instructions/copilot-instructions.archive.md` were deleted as redundant clones. No mirrors are maintained. Single SSOT only.

## Surface Roles

- Primary canon:
  `.github/copilot-instructions.archive.md`
  This is the sole live SSOT archive for canon repair, law adjudication, and benchmarking. No mirrors or synced copies exist.

- Derived satellites:
  `.github/codex-satellites/*.md`
  These are downstream lenses and registries. They inherit from the primary archive and should not silently redefine canon.

- Frozen proto backup:
  `.github/copilot-instructions-copy.md`
  This is backup or archaeology residue unless explicitly promoted for a specific forensic task. It is not a live canon source by default.

## Operational Rule

1. Canon edits land in the primary archive only.
2. Verify the primary archive with `scripts/ssot_loremaster.py`.
3. Update satellites if the change affects registries, hierarchy tables, or downstream law.
4. Leave the proto backup untouched unless the task is explicitly archaeological.

## Drift Rule

Drift audits must separate:

- load-bearing drift:
  hierarchy tables, designation rows, invocation syntax, SSOT declarations, registry entries

- contextual shorthand:
  prose, narrative explanation, internal component references, legacy quotations

Only load-bearing drift is an immediate canon blocker.
