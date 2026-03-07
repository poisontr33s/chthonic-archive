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
2. `.temple/architecture/copilot-instructions.archive.md`
3. `.github/codex-satellites/*.md`
4. `.github/copilot-instructions-copy.md`

## Surface Roles

- Primary canon:
  `.github/copilot-instructions.archive.md`
  This is the live SSOT archive for canon repair, law adjudication, and benchmarking.

- Synced mirror:
  `.temple/architecture/copilot-instructions.archive.md`
  This may mirror the primary archive for architectural use, but it does not outrank the primary archive.

- Derived satellites:
  `.github/codex-satellites/*.md`
  These are downstream lenses and registries. They inherit from the primary archive and should not silently redefine canon.

- Frozen proto backup:
  `.github/copilot-instructions-copy.md`
  This is backup or archaeology residue unless explicitly promoted for a specific forensic task. It is not a live canon source by default.

## Operational Rule

1. Canon edits land in the primary archive first.
2. Verify the primary archive with `scripts/ssot_loremaster.py`.
3. Sync the `.temple` mirror if the change is load-bearing.
4. Update satellites if the change affects registries, hierarchy tables, or downstream law.
5. Leave the proto backup untouched unless the task is explicitly archaeological.

## Drift Rule

Drift audits must separate:

- load-bearing drift:
  hierarchy tables, designation rows, invocation syntax, SSOT declarations, registry entries

- contextual shorthand:
  prose, narrative explanation, internal component references, legacy quotations

Only load-bearing drift is an immediate canon blocker.
