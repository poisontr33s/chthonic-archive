---
type: mailbox-report
created: 2026-03-08
subject: root-archaeology
---

# Root Archaeology Report

## Overview

The root stale-file set is not a trash heap. It is a mixed archaeological layer containing:

- superseded SSOT surgery utilities,
- one-off MCP / CLI test captures,
- theme audit outputs,
- session-transcript derivatives,
- and a live broken-reference scan.

Several of these files are already referenced from [CROSS_REFERENCE_TRIPTYCH.md](c:/Users/erdno/chthonic-archive/docs/protocols/CROSS_REFERENCE_TRIPTYCH.md), so relocation must be treated as a governed follow-up, not a blind move.

## Inventory

| File | Grade | Proposed Destination | Notes |
|---|---|---|---|
| `strip_ssot.py` | DUPLICATE | `scripts/.deprecated/root-ssot-tools/` | v1 copy-oriented SSOT stripper; stale target path |
| `strip_ssot_v2.py` | DUPLICATE | `scripts/.deprecated/root-ssot-tools/` | later variant, still copy-oriented and stale |
| `strip_post_ssot.py` | EXTRACT | `scripts/.deprecated/root-ssot-tools/` | broader offload logic; preserve for archaeology |
| `get_hash.py` | EXTRACT | `scripts/.deprecated/root-ssot-tools/` | compact canonical hash utility |
| `claude_test.py` | ARCHIVE | `dumpster-dive/forge/anvil/root-tests/` | one-off Bedrock integration probe |
| `purify_ssot.py` | EXTRACT | `scripts/.deprecated/root-ssot-tools/` | explicit SSOT purification lane; stale path assumptions |
| `cargo_test.json` | ARCHIVE | `audit-reports/root-mcp/` | single cargo MCP probe payload |
| `meta_cli_test.json` | ARCHIVE | `audit-reports/root-mcp/` | legacy meta-cli probe payload |
| `status_test.json` | ARCHIVE | `audit-reports/root-mcp/` | stale v3.0.0 status snapshot |
| `validate_test.json` | ARCHIVE | `audit-reports/root-mcp/` | validation payload |
| `kcp_batch1_verify.json` | DUPLICATE | `audit-reports/root-mcp/` | empty file; no live signal |
| `stage2_1_audit.json` | ARCHIVE | `audit-reports/theme-stage2_1/` | earlier icon collision report |
| `stage2_1_final_audit.json` | EXTRACT | `audit-reports/theme-stage2_1/` | final theme audit worth preserving |
| `stage2_1_recolor_audit.json` | ARCHIVE | `audit-reports/theme-stage2_1/` | intermediate recolor pass |
| `stage2_1_round3_audit.json` | EXTRACT | `audit-reports/theme-stage2_1/` | zero-collision round |
| `challenge_task_session_context_truncted.md_pretty.md` | EXTRACT | `docs/sessions/` | readable archaeological session rendering |
| `challenge_task_session_context_truncted.md_resume.md` | EXTRACT | `docs/sessions/` | compact resume packet |
| `challenge_task_session_context_truncted.md_structured.txt` | ARCHIVE | `docs/sessions/` | raw structured transcript derivative |
| `broken-refs.json` | EXTRACT | `audit-reports/link-audit/` | still valuable broken-link scan |
| `server_debug.json` | ARCHIVE | `audit-reports/root-mcp/` | older MCP server tool listing |

Expected by handoff but already relocated:

| File | Current Status |
|---|---|
| `strip_broken_headers.py` | already lives in `scripts/` |

## Cross-References Discovered

Load-bearing references already exist in:

- [CROSS_REFERENCE_TRIPTYCH.md](docs/protocols/CROSS_REFERENCE_TRIPTYCH.md)
- [CONTEXT_SURGERY_2026_02_10.md](codex/mailbox/ACTUAL-WORKING-HANDOFFS/CONTEXT_SURGERY_2026_02_10.md)
- `RELATIONSHIP_AUDIT_CODEBASE_LATEST.json`
- `RELATIONSHIP_AUDIT_CODEBASE_POSTCHECK.json`

That means relocation must be paired with reference repair, especially for:

- `strip_ssot.py`
- `strip_ssot_v2.py`
- `strip_post_ssot.py`
- `purify_ssot.py`
- `broken-refs.json`
- the three challenge-task transcript derivatives

## Proposed User Actions

1. Move SSOT-surgery root scripts into a single deprecated archaeology subdirectory under `scripts/`.
2. Move raw MCP/test payloads into `audit-reports/root-mcp/`.
3. Move `stage2_1_*` theme audits into a dedicated `audit-reports/theme-stage2_1/`.
4. Move the challenge-task session derivatives into `docs/sessions/`.
5. Update the explicit references in `CROSS_REFERENCE_TRIPTYCH.md` after relocation.
