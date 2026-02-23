# SESSION_HANDOFF — KCP Template Canonization Complete → Codex Batch Migration

## Scope
- Domain: `TEMPLE` (standards/governance)
- Objective: KCP-2.0 templates are ratified and parser-validated. Delegate KCP-3.0 through KCP-6.0 preparation and batch migration execution to Codex .5.3.

## Context

### KCP-2.0 Deliverables (COMPLETED by Claude)
All 4 canonical templates created and parser-validated:
- `docs/standards/templates/kcp_template.py` — `ast.parse()` PASSED
- `docs/standards/templates/kcp_template.ts` — `Bun.Transpiler.scan()` PASSED
- `docs/standards/templates/kcp_template.ps1` — `Get-Help` PASSED (Synopsis extracted)
- `docs/standards/templates/kcp_template.rs` — `rustc --edition 2021 --crate-type lib` PASSED

### Architecture (Irrevocable — KCP-1.0)
- Approach C: Stratified Metadata (Two-Stratum)
- Stratum 1 (Cartouche): Artifact Name, Wedjat-Quipu Spectrum, Temple-Ayllu Zone, Ogdoad-Ceque Radiance
- Stratum 2 (Khipu): @SID, @Shabti, @Heka-Ayni, @Ankh-Tinku, @Purpose
- Reference: `docs/standards/KCP_PROTOCOL_ONTOLOGY.md` (STD_KCP_ONTOLOGY_V1)

## Delegation Tasks for Codex .5.3

### TASK 1: KCP-3.0 — Python Consolidation (Pre-Scan)
- **Objective:** Audit all ~120 `.py` files for dual `@SID` instances (one in Cartouche envelope `║ Semantic ID:`, one in docstring `@SID:`)
- **Action:** Generate a manifest listing every `.py` file with its current header state:
  - `LEGACY` — old STD_V2 envelope, PMS-v3 docstring
  - `KCP-COMPLIANT` — full Cartouche + Khipu (matches template)
  - `HYBRID` — partial migration
  - `NONE` — no header at all
- **Output:** `codex/mailbox/KCP_3_0_PYTHON_AUDIT.json` with per-file classification
- **Gate:** Zero files classified as UNKNOWN

### TASK 2: KCP-4.0 — TypeScript Census
- **Objective:** Audit all ~62 `.ts/.tsx` files for existing header state
- **Action:** Same classification as TASK 1 (LEGACY/KCP-COMPLIANT/HYBRID/NONE)
- **Output:** `codex/mailbox/KCP_4_0_TYPESCRIPT_AUDIT.json`
- **Gate:** Zero files classified as UNKNOWN

### TASK 3: KCP-5.0 — PowerShell Census
- **Objective:** Audit all ~82 `.ps1` files for existing header state
- **Action:** Same classification as TASK 1
- **Output:** `codex/mailbox/KCP_5_0_POWERSHELL_AUDIT.json`
- **Gate:** Zero files classified as UNKNOWN

### TASK 4: KCP-6.0 — Rust Census
- **Objective:** Audit all ~15 `.rs` files for existing header state
- **Action:** Same classification as TASK 1
- **Output:** `codex/mailbox/KCP_6_0_RUST_AUDIT.json`
- **Gate:** Zero files classified as UNKNOWN

### TASK 5: Regex Validation Tool
- **Objective:** Build a standalone validation script using the regex patterns from `KCP_PROTOCOL_ONTOLOGY.md` §8 that can classify any file's header state
- **Action:** Create `scripts/kcp_header_classifier.py` using the canonical regex patterns (§8.1 Cartouche detection, §8.2 Khipu tag extraction, §8.3 Legacy detection)
- **Input:** File path or directory
- **Output:** JSON report with per-file classification
- **Gate:** Script passes `uv run python scripts/kcp_header_classifier.py --selftest`

## Priority
- TASK 5 first (the classifier tool), then TASKS 1-4 use it
- Each audit JSON must include: `file_path`, `classification`, `detected_fields`, `missing_fields`, `dual_sid` (boolean)

## Cross-References
- `docs/standards/KCP_PROTOCOL_ONTOLOGY.md` — §8 Regex Patterns (canonical)
- `docs/standards/KCP_ARCHITECTURE_RATIFICATION.md` — Approach C decision
- `docs/standards/templates/kcp_template.*` — The 4 canonical templates
- `docs/design/KCP_SESSION_CHECKPOINT.md` — Phase tracker
- `docs/design/SFS_WPTG_ITERATION_PLAN.md` — Full pipeline stages

## Handoff Metadata
- Origin: Claude (KCP-2.0 session)
- Destination: Codex .5.3
- Priority: NEXT (blocking KCP-3.0 through KCP-6.0 execution)
- Deadline: Before next Claude session
