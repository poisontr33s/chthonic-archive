<!--
================================================================================
SEMANTIC IDENTITY (Anchor & Signal Protocol)
================================================================================
@SID:           PROTOCOL_ANCHOR_SIGNAL
@Type:          Protocol
@Context:       System Architecture
@Implements:    STABILIZATION_POLICY
@Emits:         GOVERNANCE_DOCTRINE
@SessionOrigin: SESSION_DOC_2026_01_17_CLEANUP
================================================================================
-->

# Anchor & Signal Protocol (ASP)
> **Hierarchical Governance for Autonomous Repository Stewardship**

## 1. The Prime Directive: Entropy Reduction
**Objective:** Eliminate "Timestamp-and-Register" loops where every action creates a new file that must be manually registered, creating exponential maintenance debt.
**Rule:** We prefer **State Files** (Overwrite) over **Log Files** (Append/New).

## 2. The Semantic Identity Layer (@SID)
Files are referenced by **Identity**, not **Location**.
- **The Signal:** A unique identifier in the file header.
  - Syntax: `@SID: UNIQUE_NAME`
- **The Anchor:** The `sid_index.json` map that links Signal → Filepath.
- **The Invariant:** One SID = One File.

## 3. The Loop-Breaking Policy
**Problem:** Hardcoded output paths or timestamped filenames cause scripts to create new debris every run.
**Solution:** Dynamic Output Resolution.
1.  **Scan:** Tool checks `docs/` for any file containing the target `@SID` (e.g., `STATE_ROOTDIR_HEALTH`).
2.  **Resolve:**
    *   *If Found:* Update that file in-place (preserving the user's chosen filename).
    *   *If Missing:* Create the default file (e.g., `docs/ROOTDIR_HEALTH.md`).
3.  **Result:** Tools are idempotent. Running them 100 times produces 1 updated artifact, not 100 logs.

## 4. Hierarchy of Artifacts

### Tier 1: The State (Truth)
*Managed by Tools, Updated In-Place*
- `STATE_CODEBASE_INVENTORY` (Inventory)
- `STATE_ROOTDIR_HEALTH` (Audit)

### Tier 2: The Anchors (Identity)
*Managed by Humans/Agents, Stable*
- `DOC_SRC_README` (Folder Identity)
- `DOC_DOCS_README` (Folder Identity)
- `PROTOCOL_ANCHOR_SIGNAL` (This Document)

### Tier 3: The Tools (Execution)
*Aware of Tier 1 & 2 via SID Resolution*
- `TOOL_SID_RESOLVER_V1` (The Backbone)
- `TOOL_CODEBASE_MAPPER_V1` (The Surveyor)
- `TOOL_ROOT_AUDIT_V1` (The Auditor)

## 5. Agent Operational Rules (The "Don't Break It" List)
1.  **Never Hardcode Paths** for inputs. Use `resolve_sid.py --resolve SID`.
2.  **Never Create Timestamps** in filenames for status reports.
3.  **Always Check SIDs** before creating new files to avoid duplication.
4.  **Always Re-Run Resolver** (`uv run scripts/resolve_sid.py`) after moving or creating files.
