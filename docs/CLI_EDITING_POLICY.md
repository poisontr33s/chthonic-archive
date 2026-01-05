# CLI Editing Policy

**Purpose.** This file defines the single, enforced rule set for any automated or assistant-driven edits performed via the GitHub Copilot CLI, local scripts, or any other non-human actor. The policy preserves provenance, avoids silent editorialization, and treats the SSOT (single source of truth) as verifiable truth — never as content to be hidden.

---

## Core rules (mechanical only)

1. **EDIT SCOPE: Mechanical only.**
   * Edits must be mechanically scoped to explicit file paths and exact replacements.
   * Allowed: update a direct file reference from `old/path.ext` → `new/path.ext` when the new path exists.
   * Forbidden: global semantic searches and implicit judgement calls ("find every occurrence of 'smoke' and decide which to change").

2. **SSOT visibility**
   * SSOT references must remain fully visible in outputs, logs, and artifacts.
   * The CLI or any runner may not filter, redact, or suppress SSOT content.
   * The only validation gate for SSOT is `validate_ssot_integrity` (hash verification).

3. **Authority enforcement**
   * Authority checks occur at execution time via `validate_ssot_integrity`. The CLI must not attempt to pre-validate or rewrite authority rules.
   * Any remediation required by an SSOT mismatch must be surfaced as an explicit failure and treated as a manual remediation task.

4. **Documentation is a historical record**
   * Documentation may contain legacy terminology. Do not normalize or "clean" historical language unless file paths are broken or references are factually incorrect.
   * Renaming files ≠ rewriting history. Make path changes only when required and explicitly scoped.

5. **Audit trail**
   * All automated edits must produce an artifact capturing:
     - run_id (ISO8601)
     - edit scope (list of files changed)
     - exact change diff or patch
     - operator (human or CLI invocation string)
     - notes (reason)
   * Save artifacts under `artifacts/` and commit them when appropriate.

6. **Failure behavior**
   * On any ambiguity or potential semantic judgement, fail fast: do not apply edits.
   * The CLI must return a non-zero exit code and produce a human-readable explanation.

---

## Prompt preamble (use this verbatim when asking tooling to edit)

```
EDIT SCOPE: Mechanical only.

Rules:
- Do not editorialize.
- Do not normalize terminology.
- Do not suppress SSOT or historical references.
- Perform only mechanically necessary edits (broken paths, direct file references).

Example:
✅ Update references to old_filename.ts → new_filename.ts
❌ Search for all occurrences of "old" and decide which matter
```

---

## Governance and exceptions

* Exceptions to this policy must be approved and recorded by an explicit human sign-off (commit message that references the approval).
* This policy may be updated only by an explicit commit authored with a human operator signature and rationale.
