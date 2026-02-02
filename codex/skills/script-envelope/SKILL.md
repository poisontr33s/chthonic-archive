---
name: "script-envelope"
description: "Standardize script headers by adding a deterministic metadata envelope (SID, purpose, exports, cross-references), normalize shebangs, and document flags/modes. Use when upcycling or hardening scripts for self-describing, agent-ready maintenance."
---

# Script-Envelope Skill

Create or repair a **metadata envelope** at the top of scripts so each file is self-describing, predictable, and aligned with repo conventions. This skill is deterministic and non-random.

## Core rule

When a script is targeted for standardization, add or repair its envelope using the **first applicable** action below, then report the artifact.

## Deterministic workflow

1. **Pre-flight**: Validate target exists and is within repo boundaries.
2. **Classify**: Determine file type and language (e.g., .py, .ps1, .ts, .rs).
3. **Select action (first applicable)**:
   - Add a metadata envelope if missing.
   - Repair malformed envelope width/formatting.
   - Normalize shebang (language-appropriate).
   - Add missing SID/purpose/exports/flags sections.
4. **Apply minimal safe change**.
5. **Report artifact path + diff summary**.

## Invariants

- One action per pass.
- No random creative output.
- No menus or option lists.
- Never delete existing content.
- Preserve original code semantics.

## Envelope fields (minimum)

- **Semantic ID (SID)**
- **Purpose**
- **Exports**
- **Cross-References (if any)**
- **Flags/Modes (if any)**

## Canonicalization rules

- Deduplicate to a single envelope block.
- Enforce fixed field order (see `references/envelope-template.md`).
- Normalize text to NFC before width calculation and compute width from the longest interior line + 2 spaces of padding using Unicode display width (wcswidth).
- Pad all interior lines to the computed width.
- Replace malformed or partial envelopes entirely.

## Shebang normalization

- Python: `#!/usr/bin/env python3`
- PowerShell: `#!/usr/bin/env pwsh` (only if script is intended for direct execution)
- Keep existing shebang if toolchain depends on it.

## References

Use the checklist and templates:
- `references/checklist.md`
- `references/envelope-template.md`

## Script

Use `scripts/script_envelope.py` only as a skeleton for future automation; do not execute unless explicitly requested.
