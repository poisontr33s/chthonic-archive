# Session Reference: 2026-01-17 Cleanup & Tooling

<!--
================================================================================
SEMANTIC IDENTITY (Anchor & Signal Protocol)
================================================================================
@SID:           SESSION_DOC_2026_01_17_CLEANUP
@Type:          SessionDoc
@Context:       Hygiene / Tooling
@Spawned:       TOOL_SESSION_EXTRACTOR_V1, TOOL_ROOT_AUDIT_V1
================================================================================
-->

> **Navigation:** [CLAUDE.md (repo-root)](../../../CLAUDE.md) | [SSOT](../../../.github/copilot-instructions.md) | Scripts

**Session Purpose:** Claude Code upgrade check, config cleanup, and session extraction tooling.

---

## File Registry (Anchor & Signal Protocol)

### Semantic Identity Map

| @SID | Type | Path (Current) | Purpose |
|------|------|----------------|---------|
| `TOOL_SESSION_EXTRACTOR_V1` | Script | [`scripts/extract_session_value.py`](../../../scripts/extract_session_value.py) | Session JSONL extractor |
| `TOOL_ROOT_AUDIT_V1` | Script | [`scripts/../scripts/rootdir_health_audit.py`](../../../scripts/rootdir_health_audit.py) | Root directory auditor |
| `TOOL_SID_RESOLVER_V1` | Script | `scripts/resolve_sid.py` | Semantic ID resolver |
| `TOOL_CODEBASE_MAPPER_V1` | Script | [`scripts/../scripts/map_codebase.py`](../../../scripts/map_codebase.py) | Cartography tool |
| `SESSION_DOC_2026_01_17_CLEANUP` | SessionDoc | [`docs/SESSION_2026-01-17_CLEANUP.md`](./SESSION_2026-01-17_CLEANUP.md) | This session map |
| `STATE_ROOTDIR_HEALTH` | State | [`docs/ROOTDIR_HEALTH.md`](../../../docs/ROOTDIR_HEALTH.md) | Health audit output |
| `REPORT_TRUTH_STEWARDSHIP_2026_01_17` | Report | [`docs/SESSION_2026_01_17_TRUTH_STEWARDSHIP.md`](../../../docs/SESSION_2026_01_17_TRUTH_STEWARDSHIP.md) | Truth validation log |
| `STATE_CODEBASE_INVENTORY` | State | [`docs/CODEBASE_INVENTORY.md`](../../../docs/CODEBASE_INVENTORY.md) | Inventory & proposal |
| `DOC_SRC_README` | Documentation | `src/README.md` | Source directory readme |
| `DOC_SCRIPTS_README` | Documentation | `scripts/README.md` | Scripts directory readme |
| `REPORT_META_REVIEW_2026_01_17` | Report | [`docs/SESSION_2026_01_17_META_REVIEW.md`](../../../docs/SESSION_2026_01_17_META_REVIEW.md) | Validation certificate |

### Cross-Reference Graph (SID-Based)

```
SESSION_DOC_2026_01_17_CLEANUP
  ├─► spawned: TOOL_SESSION_EXTRACTOR_V1
  │     └─► @SessionOrigin: SESSION_DOC_2026_01_17_CLEANUP
  ├─► spawned: TOOL_ROOT_AUDIT_V1
  │     ├─► @SessionOrigin: SESSION_DOC_2026_01_17_CLEANUP
  │     └─► @Emits: STATE_ROOTDIR_HEALTH
  ├─► spawned: TOOL_SID_RESOLVER_V1
  │     ├─► @SessionOrigin: SESSION_DOC_2026_01_17_CLEANUP
  │     └─► @Implements: PROTOCOL_ANCHOR_SIGNAL
  ├─► spawned: TOOL_CODEBASE_MAPPER_V1
  │     ├─► @SessionOrigin: SESSION_DOC_2026_01_17_CLEANUP
  │     └─► @Emits: STATE_CODEBASE_INVENTORY
  ├─► emitted: STATE_ROOTDIR_HEALTH
  ├─► emitted: REPORT_TRUTH_STEWARDSHIP_2026_01_17
  ├─► emitted: STATE_CODEBASE_INVENTORY
  └─► emitted: REPORT_META_REVIEW_2026_01_17
```

**Resolution:** Run `uv run scripts/resolve_sid.py` to rebuild `../data/indices/../data/indices/sid_index.json`

**Protocol:** Files reference by `@SID`, not path. Paths are resolvable via `../../ankh_index.json` or future `ankh://` URI scheme.

**Invariant:** Every `@SID` declared MUST resolve to exactly one file. Moving files updates the resolver, not the references.

---

## Tasks Completed

- [x] **Theme Fix:** Validated and fixed `chthonic-archive-theme.json` invalid keys
- [x] **Session Extraction:** Created `scripts/extract_session_value.py` to prevent data loss
- [x] **Architecture Shift:** Implemented Anchor & Signal Protocol (`@SID`) to decouple reference from location
- [x] **Tool Stabilization:** Refactored audit/mapping tools to use **State Files** instead of logs
- [x] **Inventory Cleanup:** Created standardized `docs/README.md` and indexed valid files
- [x] **Tool Robustness:** Updated `../scripts/../scripts/map_codebase.py` and `../scripts/../scripts/rootdir_health_audit.py` with `--dry-run` and error handling
- [x] **Migration:** Moved 9 root Python files and 1 TypeScript file to `scripts/` to clean the root directory.

## Next Steps

1. **Theme Packaging:** Revisit theme extension packaging with clean JSON

---

## Files Modified

| File | Change |
|------|--------|
| None | No existing files modified |

---

## Files Deleted (Cleanup)

### From `~/.claude/` (Claude Code config)

| Location | Count | Reason |
|----------|-------|--------|
| `~/.claude/projects/c--Users-erdno-chthonic-archive/*.jsonl` | 13 | Empty session files (0 bytes) |
| `~/.claude/todos/*.json` | 33 | Empty todo stubs (2 bytes each) |
| `~/.claude/projects/C--Users-erdno/` | 1 dir | Orphan project folder |

### From repo root (temporary, then deleted)

| File | Reason |
|------|--------|
| `session-archive-85edc6a3.jsonl` | Copied for review, deleted (redundant) |
| `session-extracted.md` | Test output, deleted (redundant) |

---

## Install Paths Verified

| Path | Type | Status |
|------|------|--------|
| `~/.local/bin/claude.exe` | Official `iex` installer | ✓ Primary (v2.1.9) |
| VSCode extension | Managed by VSCode | ✓ Separate |
| `%APPDATA%/npm/.../claude-code` | npm global | ✗ Removed |
| `~/.bun/.../claude-code` | bun global | ✗ Removed |

---

## Tool Quick Reference

### `scripts/extract_session_value.py`

```bash
# Dry run (stats only)
uv run scripts/extract_session_value.py session.jsonl --dry-run

# Extract with redundancy check
uv run scripts/extract_session_value.py session.jsonl out.md --check-redundancy docs/

# JSON output
uv run scripts/extract_session_value.py session.jsonl --format json

# Full debug
uv run scripts/extract_session_value.py session.jsonl --debug --log debug.log
```

**Classification Tags:** `architecture`, `fix`, `feature`, `config`, `performance`, `security`, `test`, `docs`, `dependency`, `governance`, `shell`, `general`

---

## Session Decisions

| Decision | Rationale |
|----------|-----------|
| Delete redundant session archive | 100% overlap with existing `docs/` |
| Keep extraction script | Reusable for future analysis |
| Use official `iex` installer only | Single PATH source |
| Bidirectional file references | Prevents stray file cascades |

---

## Convention: Session File Hygiene

To prevent stray files:

1. **Every session creates ONE session doc** in `docs/SESSION_YYYY-MM-DD_<topic>.md`
2. **Every file created MUST be registered** in the session doc's File Registry
3. **Scripts MUST have header metadata** pointing back to their session doc
4. **Temporary files** are documented even if deleted
5. **Root directory is for project-level files only** — session artifacts go in `docs/` or `scripts/`

### Template for new scripts:

```python
#!/usr/bin/env python3
"""
script_name.py — Brief Description

================================================================================
FILE METADATA
================================================================================
Created:        YYYY-MM-DD
Session Doc:    docs/SESSION_YYYY-MM-DD_<topic>.md
Related Files:  [list other files from same session]
Category:       <Tooling|Analysis|Automation|...>
================================================================================
"""
```

---

## Related Documentation

| Document | Relationship |
|----------|--------------|
| [CLAUDE.md (repo-root)](../../../CLAUDE.md) | Project-level Claude Code instructions |
| [`docs/PWSH_RULES.md`](../../../PWSH_RULES.md) | Shell execution rules referenced by script |
| [`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md) | SSOT governance |

---

*Generated: 2026-01-17 | Session ID: 5b1b3de9*
