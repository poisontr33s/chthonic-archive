# Ankhological Workflow Instructions

These instructions govern how we operate inside this repository.

They are procedural, not doctrinal.
They reference files, not concepts.

---

## Primary Reading Order (Mandatory)

When operating in this repository, we read in this order:

1. `dumpster-dive/intake/templates/intake-checklist.md`
2. `dumpster-dive/intake/templates/manifest-template.yml`
3. `dumpster-dive/intake/templates/lineage-*-template/main.md`

We do not infer workflow from SSOT documents.
We follow file-declared structure only.

---

## Coordination Rule (Global)

When a file states:

**"Awaiting sovereign population (Lineage X)"**

This means:

→ Lineage X must populate its own  
`lineage-X-template/manifest.yml` and `main.md`.

This is an instruction, not a waiting state.

---

## File Interconnection Rule

Some files declare a `refs` block.

This block lists related files only.
It does not assign authority.
It does not imply execution order unless stated in the checklist.

---

## What We Do Not Do

- We do not invent workflow from prose
- We do not infer intent from SSOT
- We do not modify frozen tools
- We do not act across lineage boundaries

---

## Ground Truth

If instructions conflict:
- Checklist > Instructions > Templates
- Files override memory
- Structure overrides interpretation
