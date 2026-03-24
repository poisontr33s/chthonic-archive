---
type: policy
category: skill
skill: artifact-upcycle
status: active
description: Core invariants and action definitions for artifact upcycling
---

# Upcycling Policy & Invariants

**Authority:** `artifact-upcycle` Skill
**Status:** ACTIVE
**Enforcement:** Strict (embedded in `artifact_upcycle.py`)

## 1. Core Invariants (Non-Negotiable)

1.  **Safety First:** Default execution mode is **DRY-RUN**. Mutation requires explicit `--apply` flag.
2.  **Lossless Operations:** Never delete a file without first archiving it to `dumpster-dive/` or a dedicated archive path.
3.  **Atomic Progression:** Perform **one action per pass** per file.
    *   *Why?* Prevents compounding errors and allows diff review between steps.
    *   *Order:* `normalize` -> `header` -> `links` -> `content` -> `archive`.

## 2. Potency & Fate

Files are judged by **Potency Score** (0-100):
*   **High (>70):** Core Artifacts (Code, Documentation). **Action:** Polish & Standardize.
*   **Mid (20-70):** Context/Data. **Action:** Validate & Link.
*   **Low (<20):** Noise/Logs. **Action:** Archive.

## 3. Action Definitions

| Action | Trigger | Outcome |
| :--- | :--- | :--- |
| `normalize_name` | Spaces, uppercase, non-standard chars | Rename to `snake_case` or `kebab-case`. |
| `add_header` | Missing frontmatter/docstring | Inject minimal metadata header. |
| `repair_links` | Broken MD links (`] (`) | Fix syntax errors. |
| `extract_todos` | `TODO`/`FIXME` presence | Extract to task list (do not remove). |
| `archive` | Low potency | Move to `dumpster-dive/archive`. |
| `pass` | Compliant file | No action. |
