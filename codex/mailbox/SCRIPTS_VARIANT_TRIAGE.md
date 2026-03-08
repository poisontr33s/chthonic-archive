---
type: mailbox-report
created: 2026-03-08
subject: scripts-variant-triage
---

# Scripts Variant Triage

## Census Reality

The chore frontmatter estimated `255` tracked script files. The live tree is larger:

| Metric | Count |
|---|---:|
| Total files under `scripts/` | `393` |
| Python | `168` |
| PowerShell | `89` |
| TypeScript | `31` |
| Markdown | `16` |
| JSON | `28` |
| Tracked `.pyc` under `scripts/` | `49` |

This matters because the variant problem is mixed with generated debris and embedded docs, not just handwritten script families.

## Header Compliance

### Python (`168` files)

| Check | Passing | Failing |
|---|---:|---:|
| Shebang `#!/usr/bin/env python3` | `168` | `0` |
| UTF-8 coding line | `168` | `0` |
| `@SID` present | `166` | `2` |
| `@Type` present | `14` | `154` |
| PEP 723 `/// script` block absent | `168` | `0` |

Critical Python misses:

- `scripts/aws/claude_opus46_invoke.py` — missing `@SID`, missing `@Type`
- `scripts/aws/claude_opus46_large_context.py` — missing `@SID`, missing `@Type`

### PowerShell (`89` files)

| Check | Passing | Failing |
|---|---:|---:|
| Has shebang | `88` | `1` |
| Has `@SID` or equivalent envelope field | `7` | `82` |
| Has `@Type` or equivalent envelope field | `5` | `84` |

High-priority compliant exemplars already showing the target standard:

- `scripts/chthonic.ps1`
- `scripts/claudine.ps1`
- `scripts/ssot_crc_selector.ps1`
- `scripts/ssot_outline_extractor.ps1`
- `scripts/ssot_registry_query.ps1`
- `scripts/ssot_tier_query.ps1`
- `scripts/vscode_insiders_matrix.ps1`
- `scripts/vscode_terminal_crash_doctor.ps1`

These should be the envelope model for the wider `.ps1` surface.

## Variant Families

### `decorator_cross_ref_*`

| File | Size Profile | Distinct Signal |
|---|---|---|
| `decorator_cross_ref_enhanced.py` | medium | AST proof-of-concept, circular dependency detection, earlier multi-format synthesis |
| `decorator_cross_ref_maximum.py` | large | unified DCRP v1 lane, master index generation, `--inject` branch, pre-production consolidation |
| `decorator_cross_ref_production.py` | large | production DCRP v3.1, argparse, `--dry-run`, `--watch`, TypeScript resolver, Bun alias support |

Assessment:
- `production` is the strongest surviving host.
- `maximum` still contains integration logic and master-index framing worth preserving.
- `enhanced` is mostly an earlier AST-heavy proving layer.

Proposal:
- Upcycle into a single canonical script with `--mode enhanced|maximum|production` semantics if this family is reopened.
- Preserve both earlier files as provenance or regression fixtures until that merge is executed.

### `hf_*`

| File | Role | Merge Judgment |
|---|---|---|
| `hf_discovery.py` | generic Hub discovery into artifacts | distinct |
| `hf_gemma_probe.py` | targeted Gemma shortlist + mailbox emission | distinct |
| `hf_model_scout.py` | mistral.rs-aware model ranking | distinct |
| `hf_prep.py` | environment and dependency readiness | distinct |
| `hf_probe.py` | auth probe | distinct |
| `hf_refiner.py` | inference/refinement loop | distinct |

Assessment:
- This family is not redundant. It is a toolkit.
- Consolidation here would lose task separation.

### `claude_*` + `claudine.ps1`

| File | Role | Keep / Fold |
|---|---|---|
| `claude_ide.ps1` | canonical Claude IDE entrypoint | keep as front door |
| `claude_healthcheck.ps1` | deterministic health artifact | keep as sub-lane |
| `claude_crossover.ps1` | Codex → Claude packet emission | keep |
| `claude_ide_settings_generate.ps1` | generated overlay writer | keep |
| `claude_insiders_selfheal.ps1` | repair lane | keep |
| `claude_plugin_ensure.ps1` | idempotent plugin enable wrapper | keep |
| `claude_profile.ps1` | profile launcher | keep |
| `claudine.ps1` | compatibility wrapper into `chthonic.ps1` | keep as wrapper |

Assessment:
- The family is satellite-heavy but coherent.
- The correct long-term move is not deletion; it is to continue making `claude_ide.ps1` the choke point and keep satellites thin.

### `ssot_*`

| File | Role | Keep / Fold |
|---|---|---|
| `ssot_crc_selector.ps1` | CRC suggestion | keep |
| `ssot_outline_extractor.ps1` | outline + index regeneration | keep |
| `ssot_registry_query.ps1` | registry query | keep |
| `ssot_tier_query.ps1` | tier query | keep |

Assessment:
- These are still meaningful, but they are now adjacent to the newer `ssot_loremaster.py`.
- Future consolidation target is `chthonic ssot ...`, not immediate removal.

## `.md` Files Living In `scripts/`

These should relocate out of `scripts/` into `docs/` or `audit-reports/`:

1. `scripts/BUN_COMPLIANCE_AUDIT.md`
2. `scripts/BUN_COMPLIANCE_DEPLOYMENT.md`
3. `scripts/CLAUDE_CODE_INTEGRATION.md`
4. `scripts/epistemograph_schema_design.md`
5. `scripts/hf_token_policy.md`
6. `scripts/PROBE_VARIANT_AUDIT.md`
7. `scripts/scanner_approval.md`
8. `scripts/scanner_v1.1_fixes.md`
9. `scripts/scanner_validation_FAILED.md`
10. `scripts/scanner_validation_PASSED_v1.1.1.md`
11. `scripts/schema_validation_report.md`
12. `scripts/aws/README.md`

Keep in place as deprecated-lane docs:

- `scripts/.deprecated/mcp_legacy/INTEGRATION_GUIDE.md`
- `scripts/.deprecated/mcp_legacy/OPTION_A_STATUS.md`
- `scripts/.deprecated/mcp_legacy/README.md`

## Consolidation Proposals

1. Treat `decorator_cross_ref_production.py` as the surviving canonical lane if this family is revisited.
2. Preserve `enhanced` and `maximum` as provenance until a mode-merged replacement exists.
3. Do **not** merge the `hf_*` family; the split is functional.
4. Continue consolidating Claude entry through `claude_ide.ps1`, not through deletion of satellite scripts.
5. Move markdown docs out of `scripts/` so the executable surface stops masquerading as a documentation shelf.
6. Add an ignore strategy for the `49` generated `.pyc` files under `scripts/` if they are not intentionally versioned.

## Census Notes

- The widest true compliance gap is not missing shebangs. It is missing `@Type` coverage on both Python and PowerShell.
- The widest false-family noise comes from generated `.pyc` and `.meta.json` files showing up as family members.
- The variant problem is therefore part governance and part artifact hygiene, not only code duplication.
