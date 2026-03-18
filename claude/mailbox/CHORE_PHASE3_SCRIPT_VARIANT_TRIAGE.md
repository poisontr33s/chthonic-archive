# CHORE Phase 3: Script Variant Triage

**Date:** 2026-03-18
**Phase:** CHORE Phase 3 — Script Family Normalization
**Status:** TRIAGED — awaiting approval for .bak purge + version consolidation

---

## Summary

`scripts/` contains ~280 files. This triage identifies **7 variant families** with clear duplication and recommends canonical variants. Git history preserves all prior states — `.bak` files are redundant.

---

## Family 1: `chthonic.ps1` Backup Chain

| File | Size | Action |
|------|------|--------|
| `chthonic.ps1` | 136,129 | **CANONICAL** — keep |
| `chthonic.ps1.bak-20260316-181658` | 131,049 | ❌ DELETE — git tracks this |
| `chthonic.ps1.bak-20260316-185259` | 131,310 | ❌ DELETE — git tracks this |
| `chthonic.ps1.bak-20260316-190744` | 131,573 | ❌ DELETE — git tracks this |
| `chthonic.ps1.bak-20260316-193348` | 135,242 | ❌ DELETE — git tracks this |
| `chthonic.ps1.bak-20260316-193439` | 135,242 | ❌ DELETE — git tracks this |
| `chthonic.ps1.bak-20260316-193628` | 136,129 | ❌ DELETE — identical to canonical |

**Savings:** ~800KB of redundant backups. All states exist in git history (commit chain from 2026-03-16 session).

---

## Family 2: `probe_toolchain_path.ps1` Backup Chain

| File | Size | Action |
|------|------|--------|
| `probe_toolchain_path.ps1` | 7,467 | **CANONICAL** — keep |
| `probe_toolchain_path.ps1.bak-20260316-184959` | 6,384 | ❌ DELETE — git tracks this |
| `probe_toolchain_path.ps1.bak-20260316-185111` | 6,619 | ❌ DELETE — git tracks this |
| `probe_toolchain_path.ps1.bak-20260316-193348` | 6,663 | ❌ DELETE — git tracks this |
| `probe_toolchain_path.ps1.bak-20260316-193439` | 6,663 | ❌ DELETE — git tracks this |

**Savings:** ~26KB. Same rationale.

---

## Family 3: `decorator_cross_ref` Variant Trio

| File | Size | Action |
|------|------|--------|
| `decorator_cross_ref_enhanced.py` | 40,195 | 🔍 REVIEW — intermediate variant? |
| `decorator_cross_ref_maximum.py` | 65,463 | 🔍 REVIEW — appears to be fullest variant |
| `decorator_cross_ref_production.py` | 62,656 | 🔍 REVIEW — "production" tag suggests canonical intent |
| `decorator_scanner.py` | 13,414 | **KEEP** — different tool (scanner vs generator) |

**Decision needed:** Which variant is canonical? `_production` name implies production-readiness. `_maximum` is 3KB larger. Recommend diff analysis to determine if `_maximum` is a superset of `_production`, then consolidate to one + archive the others.

---

## Family 4: `build_epistemograph` Version Pair

| File | Size | Action |
|------|------|--------|
| `build_epistemograph.py` | 23,941 | ⚠️ SUPERSEDED — v1.0, likely stale |
| `build_epistemograph_v1.1.py` | 29,175 | **CANONICAL** — v1.1 is latest |

**Recommendation:** Rename `build_epistemograph_v1.1.py` → `build_epistemograph.py` (drop version suffix, git tracks versions). Archive old v1.0.

---

## Family 5: `local_refiner` Version Pair

| File | Size | Action |
|------|------|--------|
| `local_refiner.py` | 14,009 | ⚠️ SUPERSEDED — v1.0 |
| `local_refiner_v2.py` | 23,618 | **CANONICAL** — v2 (10KB larger, presumably more complete) |

**Recommendation:** Same as epistemograph — rename v2 → canonical, archive v1.

---

## Family 6: `ssot_registry_query` Version Pair

| File | Size | Action |
|------|------|--------|
| `ssot_registry_query.ps1` | 6,284 | ⚠️ SUPERSEDED — original |
| `ssot_registry_query_v2.ps1` | 6,076 | **CANONICAL** — v2 (slightly smaller, presumably refined) |

**Recommendation:** Consolidate. Check if v2 imports differ before renaming.

---

## Family 7: `wptg_repeatable_cycle` + LEGACY

| File | Size | Action |
|------|------|--------|
| `wptg_repeatable_cycle.py` | 53,325 | **CANONICAL** — active |
| `wpth_repeatable_cycle_LEGACY` | 20,113 | ❌ DELETE — explicitly tagged LEGACY, no extension |

**Savings:** 20KB. LEGACY tag is unambiguous.

---

## Non-Variant Families (Functional Clusters, All Canonical)

These are functional clusters — not duplicates. Each file serves a distinct purpose:

| Family | Files | Total Size | Notes |
|--------|-------|-----------|-------|
| `hf_*` | 8 | ~111KB | HuggingFace tooling (discovery/probe/refine/rank) — distinct purposes |
| `claude_*` | 11 | ~72KB | Claude integration (bridge/plugin/health/IDE) — distinct tools |
| `ssot_*` | 10 | ~92KB | SSOT toolbox (hash/query/extract/immunity) — each does different thing |
| `theme_*` | 9 | ~93KB | Theme pipeline (audit/contrast/coverage/scaffold/promote) — pipeline stages |
| `icon_*` | 6 | ~106KB | Icon pipeline (census/audit/optimize/scaffold/surface) — pipeline stages |
| `mailbox_*` | 6 | ~50KB | Mailbox operations (compact/handoff/manifest/polish/rotate/scribe) |
| `validate_*` | 9 | ~54KB | Validators (distinct targets: probe, meta, headers, docs, sessions, shell) |
| `run_*` | 19 | ~76KB | Launchers/wrappers — each starts different tool |
| `mcp_*` / `mcp-*` | 6 | ~69KB | MCP infrastructure (server/client/proxy/inject) |
| `vscode_*` | 6 | ~140KB | VS Code tooling (hardener/autopsy/matrix/audit/crash) |
| `poe_*` | 5 | ~81KB | Poe integration (account/API/lane/SDK/transport) |

---

## Total Savings from Delete Candidates

| Category | Files | Size Freed |
|----------|-------|-----------|
| `.bak` files (Family 1+2) | 10 | ~826KB |
| LEGACY files (Family 7) | 1 | ~20KB |
| **Subtotal (safe deletes)** | **11** | **~846KB** |
| Version consolidation (Families 3-6) | 4-6 | ~100-170KB (after diff analysis) |
| **Total potential** | **15-17** | **~1MB** |

---

## Approval Required

1. **Immediate (safe):** Delete 10 `.bak` files + 1 LEGACY file (11 files, ~846KB) — git preserves all history
2. **After diff analysis:** Consolidate decorator_cross_ref, epistemograph, local_refiner, ssot_registry_query variants
3. **Future:** Consider whether `_tmp_inventory_output.txt` (0 bytes) should be removed
