---
type: handoff
from: codex
to: claude
created: 2026-02-27
priority: high
scope: markdown-path-link-disambiguation-for-duplicate-filenames
in_response_to: user-request-path-to-file-for-same-name-files
---

# Session Handoff: Path-Link Disambiguation Canon

Generated (UTC): 2026-02-27T00:00:00Z

## Purpose

Prevent path confusion when multiple files share the same basename across directories.

## Required Link Canon

1. Use valid markdown link syntax only: ``[label](path/to/file)``.
2. Never reference a duplicate-name file with basename-only labels.
3. For duplicate basenames, include a directory qualifier in the label.
4. Use root-relative repo paths in links (`./...`) to avoid context drift.
5. When one duplicate-name file is cited, include its sibling duplicate(s) in the same section.

## Collision-Critical Files (Current)

- [copilot-instructions.archive.md (.temple/architecture)](../../.temple/architecture/copilot-instructions.archive.md)
- [copilot-instructions.archive.md (.github)](../../.github/copilot-instructions.archive.md)
- [copilot-instructions.md (.github)](../../.github/copilot-instructions.md)

## Reusable Snippet

```md
## Canonical References (Disambiguated)
- [copilot-instructions.archive.md (.temple/architecture)](../../.temple/architecture/copilot-instructions.archive.md)
- [copilot-instructions.archive.md (.github)](../../.github/copilot-instructions.archive.md)
- [copilot-instructions.md (.github)](../../.github/copilot-instructions.md)
```

## Optional Basename-Collision Audit Command

```powershell
Get-ChildItem -Recurse -File |
  Group-Object Name |
  Where-Object { $_.Count -gt 1 } |
  Sort-Object Count -Descending |
  Select-Object Count, Name
```

## Next Actions (Claude)

1. Apply this link canon in all new handoffs and protocol docs.
2. When referencing `copilot-instructions.archive.md`, always include both canonical paths above.
3. If new duplicate filenames are introduced, add them to a local "Canonical References (Disambiguated)" block in the active handoff.

