<!--
================================================================================
SEMANTIC IDENTITY (Anchor & Signal Protocol)
================================================================================
@SID:           DOC_HANDOFF_TO_CLAUDE
@Type:          Handoff
@Context:       Agent Coordination
@UpdateFrequency: On-Demand
@SessionOrigin: SESSION_DOC_2026_01_17_CLEANUP
================================================================================
-->

# Handoff to Claude Code: 2026-01-17

> **Status:** `STABLE`
> **Topology:** `MAPPED`
> **Tools:** `ROBUST`

## Executive Summary
This session successfully transitioned the repository from ad-hoc file management to a rigorous **Anchor & Signal Protocol (@SID)**. We eliminated "entropy loops" caused by timestamped log files and stabilized the core tooling infrastructure. The root directory has been cleaned, and all automation tools now support `--dry-run` and error resilience.

---

## 1. Architectural Upgrades

### A. Anchor & Signal Protocol (@SID)
**Rule:** Files are referenced by Semantic Identity, NOT filepath.
**Mechanism:** `scripts/resolve_sid.py` scans content for `@SID: NAME` headers.
**Benefit:** Files can be moved (e.g., from root to `scripts/`) without breaking automation.

**Usage:**
```bash
# Resolve a tool's current location
uv run scripts/resolve_sid.py --resolve TOOL_ROOT_AUDIT_V1

# Rebuild index after moving files
uv run scripts/resolve_sid.py
```

### B. State Files vs. Logs
**Rule:** Automation tools must output to **State Files** (overwriting in-place) rather than timestamped logs.
**Benefit:** Prevents "infinite maintenance loops" where a new log file triggers a new audit, which creates a new log file...

| Old Pattern | New Pattern | SID |
|-------------|-------------|-----|
| `logs/audit_20260117.md` | `docs/ROOTDIR_HEALTH.md` | `STATE_ROOTDIR_HEALTH` |
| `docs/inventory_v2.md` | `docs/CODEBASE_INVENTORY.md` | `STATE_CODEBASE_INVENTORY` |

### C. Standardized Folder Identity
**Rule:** Every directory in `scripts/`, `src/`, and `docs/` must have a `README.md` defining:
1. **Purpose**
2. **Contents**
3. **Ownership** (Steward Tool)

---

## 2. Stabilized Toolchain

| Tool | SID | Purpose | Status |
|------|-----|---------|--------|
| `scripts/rootdir_health_audit.py` | `TOOL_ROOT_AUDIT_V1` | Audits root dir hygiene | ✅ Robust (--dry-run) |
| `scripts/map_codebase.py` | `TOOL_CODEBASE_MAPPER_V1` | Generates inventory | ✅ Robust (--dry-run) |
| `scripts/resolve_sid.py` | `TOOL_SID_RESOLVER_V1` | Manages @SID index | ✅ Robust (--dry-run) |
| `scripts/extract_session_value.py` | `TOOL_SESSION_EXTRACTOR_V1` | Parses session logs | ✅ Beta |

**Standard CLI Contract:**
All tools MUST support:
- `--dry-run`: Preview changes without writing.
- `--json`: Machine-readable output.
- Error Handling: `try/catch` blocks for file I/O.

---

## 3. Lessons Learned (The "Dirty" Session)

### A. Migration Hazards
**Lesson:** Moving scripts breaks relative imports and `subprocess` calls immediately.
**Mitigation:**
1. Update internal `Path(__file__)` references (e.g., `parent.parent`).
2. Update subprocess calls to new paths.
3. **Validation:** Run the script immediately after move.

### B. The "No Match Found" Edit Error
**Lesson:** AI `edit` tools are extremely sensitive to whitespace/context mismatches.
**Mitigation:** Always `view` the target lines *immediately before* editing to ensure exact context match. Do not rely on memory or partial reads.

### C. VS Code Theme Constraints
**Lesson:** `theme.json` files cannot contain comments or non-standard keys (`$schema_comment`), or VS Code will silently fail to load them.
**Status:** `chthonic-archive-theme.json` is fixed but needs packaging.

---

## 4. Next Actions for Claude Code

1. **Theme Packaging:**
   - The theme JSON is clean.
   - Task: Package it into a `.vsix` or finalized extension structure.

2. **Standardized README Expansion:**
   - `docs/`, `src/`, `scripts/` are done.
   - Task: Expand this to `mas_mcp/` and `dumpster-dive/` using `TOOL_CODEBASE_MAPPER_V1` inventory.

3. **Continue Migration:**
   - Root is cleaner (76 files down from 85).
   - Task: Evaluate `*.json` files in root for migration to `assets/` or `config/`.

---

**Signed:** *The Steward of Session 2026-01-17*
