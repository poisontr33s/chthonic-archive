---
type: savant level-laborious
from: the Savant | $user, archunkel, and the spirits of the codebase
to: codex
created: 2026-03-03T12:00:00Z
priority: extremely necessarily high
scope: codebase intelligence, extension-integrity, legacy files and orphaned artifacts, filetype transmutation, ankhological egyptologic x andean 50/50 ~est x abstraction
boon: 50 points back from codekiller.md structural integrity, extension contribution graph integrity, orphaned artifact reconciliation, comprehensive filetype WPTG audit
subject: Codebase-Wide WPTG Transmutation Loop + Extension Contribution Graph Validator
difficulty: extreme standardized baseline — requires deep codebase understanding, meticulous attention to detail, robust validation logic across heterogeneous file formats, and full WPTG discipline across ~2700 tracked files
---

# CHORE: Codebase-Wide WPTG Transmutation Loop + Extension Contribution Graph Validator

## Problem Statement

This repository tracks **~2700 files across 30+ file extensions**. Organic growth has produced:

- **340 `.log` files tracked in git** (332 in `codex/mailbox/` alone) — build logs, validation logs, CUDA build outputs, elevated validation captures. Every one is gold per WPTG, but none have been triaged for extractable signal vs. archival.
- **6 `.pyc` bytecode files tracked** under `.codex/skills/` — compiled Python artifacts that should never be in source control.
- **7 `.off` workflow files** — disabled GitHub Actions workflows preserved by rename, not by governance.
- **3 files with Unicode-mangled extensions** (`.md"`) — filenames containing encoded Greek characters from macro-prompt-world imports.
- **4 `.env` files tracked** — potential secret surface (environment templates and runtime configs in git).
- **5 `.vsconfig` files** — VS2026 export snapshots, potentially obsolete or duplicated.
- **1 `.bat` file** — lone Windows batch script amid a `pwsh`-canonical codebase.
- **662 `.json` files** — many are active manifests, but an unknown fraction are stale audit snapshots, meta-loop outputs, or orphaned state files.

Meanwhile, the `extensions/chthonic-archive/package.json` manifest — the single source of truth binding themes, icons, fonts, and commands to VS Code — has **no end-to-end integrity validator**.

**No tool currently answers:** "For every tracked file in this repository, what is its gold grade, is it in the right place, and does nothing reference it that shouldn't (or fail to reference it that should)?"

## Lane Exclusion (Active Frozen Work)

The following paths are **excluded from this chore** — they are under active lane work and must not be touched, moved, audited, triaged, or proposed for any operation:

| Excluded Path | Reason |
|---------------|--------|
| `extensions/chthonic-archive/themes/icons/product/*.svg` | Active product icon source art |
| `extensions/chthonic-archive/themes/icons/product-outlined/` | Generated outlined SVGs |
| `extensions/chthonic-archive/themes/fonts/` | Product icon font binaries |
| `scripts/generate-product-icon-font.mjs` | Font generation pipeline |
| `scripts/theme_*.py` | Theme design/validation scripts |
| `scripts/icon_*.py` | Icon audit/optimization scripts |
| `scripts/product_icon_census.py` | Product icon census |
| `scripts/theme-sync.ps1` | Theme sync automation |
| `extensions/chthonic-archive/themes/*.json` | Theme definition JSONs |
| `gemini/to_gemini_DR/` | Active deep research artifacts |

These exclusions are absolute. The chore operates on **everything else**.

## Part 1: Codebase-Wide WPTG Filetype Transmutation Loop

### Phase 1 — Blind Filetype Census

Build `scripts/wptg_filetype_census.py` — a static inventory tool that:

1. Walks every tracked file (`git ls-files`)
2. Classifies each by the WPTG Gold Signal File-Type Affordance Map (see `WET_PAPER_TO_GOLD_METHODOLOGY.md`)
3. Identifies anomalies:
   - **Tracked artifacts that shouldn't be** (`.pyc`, `.env` with non-template content, build outputs)
   - **Disabled-by-rename** (`.off`, `.bak_*`, `* - Copy.*`) vs. properly governed
   - **Filename encoding damage** (Unicode in git paths)
   - **Filetype-directory mismatch** (`.md` in `scripts/`, `.log` in `codex/mailbox/`, `.bat` in a `pwsh` codebase)
   - **Orphan detection** — files not referenced by any manifest, import, cross-reference, or skill
4. Respects the Lane Exclusion table above — excluded paths are skipped entirely
5. Outputs a structured census:

```json
{
  "timestamp": "ISO-8601",
  "total_tracked": 2700,
  "excluded_lane_files": 95,
  "audited_files": 2605,
  "by_extension": { ".md": { "count": 822, "anomalies": [] }, ... },
  "anomalies": [
    {
      "path": ".codex/skills/artifact-upcycle/scripts/__pycache__/resolve_directory_relationships.cpython-313.pyc",
      "type": "tracked_bytecode",
      "gold_grade": "raw",
      "recommendation": "untrack_gitignore",
      "wptg_rationale": "Generator script is the gold, not this output"
    }
  ],
  "by_gold_tier": { "tier_1_direct": 1200, "tier_2_structural": 400, "tier_3_conceptual": 800, "raw_unrefined": 205 },
  "verdict": "PASS|WARN|FAIL"
}
```

### Phase 2 — Log Archaeology

The 332 `.log` files in `codex/mailbox/` represent the single largest untriaged gold deposit. For each log file:

1. **Classify**: Build log? Validation capture? Error trace? Runtime output?
2. **Extract signal**: Unique error patterns, toolchain versions, environment state, timing data
3. **Grade**: Does the extracted signal justify continued tracking, or is the log a derivative of a still-existing process?
4. **Propose**: For each log, produce a one-line triage recommendation (preserve / extract-then-archive / untrack). **Do NOT execute any file operations.** Proposals go into `codex/mailbox/LOG_ARCHAEOLOGY_TRIAGE.md` for user review.

### Phase 3 — Orphaned Artifact Reconciliation

For every non-excluded JSON file (`~567` after lane exclusion):

1. **Trace references**: Is this JSON imported by any script? Referenced by any manifest? Read by any skill?
2. **Check freshness**: When was it last modified? Does it have a timestamp field showing generation date?
3. **Identify orphans**: JSON files that are:
   - Not referenced by any code path
   - Not a recognized mailbox artifact format
   - Older than 30 days with no cross-reference
4. **Output**: `audit-reports/orphaned_artifact_reconciliation.json` with orphan candidates and reference traces

### Phase 4 — Filetype Governance Proposals

Based on phases 1–3, emit a governance proposal document (`codex/mailbox/WPTG_FILETYPE_GOVERNANCE_PROPOSAL.md`) containing:

1. **`.gitignore` additions** — patterns for filetypes that should never be tracked (`.pyc`, build outputs)
2. **Archive candidates** — files whose gold has been extracted and should move to `dumpster-dive/` (with provenance manifests)
3. **Rename candidates** — `.off` files that should be governed by branch/workflow toggles, not filename mutation
4. **Encoding repair candidates** — files with Unicode damage in paths
5. **Directory migration candidates** — files in wrong directories per filetype conventions

**Every proposal is a proposal only.** The document is a menu for the Savant. Codex does not execute any of it.

## Part 2: Extension Contribution Graph Validator

### Chain 1: Color Themes
```
package.json contributes.themes[].path
  → theme JSON exists on disk
  → theme JSON is valid JSON (no trailing commas, no comments)
  → theme JSON contains required keys (name, type, colors, tokenColors)
  → theme type matches uiTheme declaration (vs, vs-dark, hc-black, hc-light)
```

### Chain 2: File Icon Theme
```
package.json contributes.iconThemes[].path
  → file-icon-theme.json exists
  → every iconDefinition[].iconPath → SVG file exists on disk
  → every SVG file in icons/file/ is referenced by at least one iconDefinition (no orphans)
  → SVG viewBox present and normalized (no missing viewBox attributes)
```

### Chain 3: Product Icon Theme (hardest chain)
```
package.json contributes.productIconThemes[].path
  → product-icon-theme.json exists
  → font[].id referenced in the theme matches a font[].src entry
  → font[].src woff path exists on disk
  → woff binary is parseable (valid WOFF header magic: 0x774F4646)
  → codepoint map JSON (adjacent to woff) exists and is valid JSON
  → BIDIRECTIONAL:
      a) every iconDefinition fontCharacter codepoint has a matching entry in the codepoint map
      b) every codepoint map entry is referenced by at least one iconDefinition (no phantom glyphs)
  → UPSTREAM TRACE (bonus, extreme difficulty):
      for each codepoint map entry, verify that a corresponding source SVG exists
      in the source SVG directory (match by icon name, not codepoint)
```

### Chain 4: Commands & Menus
```
package.json contributes.commands[].command
  → command string is registered in dist/extension.js OR src/extension.ts
  → if menus reference the command, command must exist in contributes.commands
  → no orphan menu entries pointing to undeclared commands
```

### Chain 5: Configuration
```
package.json contributes.configuration.properties
  → each property key follows the extension namespace convention
  → default values are type-consistent with declared type
```

## Output Format

### Extension Audit JSON (`audit-reports/extension_contribution_audit.json`)
```json
{
  "timestamp": "ISO-8601",
  "extension_version": "0.2.3",
  "chains": {
    "color_themes": { "declared": 4, "valid": 4, "errors": [], "warnings": [] },
    "file_icon_theme": { "declared_icons": 40, "resolved": 40, "orphan_svgs": [], "missing_svgs": [], "viewbox_issues": [] },
    "product_icon_theme": {
      "font_src_valid": true, "woff_magic_valid": true, "codepoint_map_valid": true,
      "icon_definitions": 43, "codepoints_matched": 43,
      "phantom_glyphs": [], "missing_glyphs": [],
      "upstream_svgs_matched": 43, "upstream_svgs_missing": []
    },
    "commands": { "declared": 0, "registered": 0, "orphan_menus": [] },
    "configuration": { "properties": 0, "type_mismatches": [] }
  },
  "verdict": "PASS|WARN|FAIL",
  "error_count": 0,
  "warning_count": 0
}
```

### WPTG Census JSON (`audit-reports/wptg_filetype_census.json`)
Full filetype census per Phase 1 schema above.

### Markdown Reports
- `audit-reports/extension_contribution_audit.md` — contribution chain integrity
- `codex/mailbox/LOG_ARCHAEOLOGY_TRIAGE.md` — log file triage proposals
- `codex/mailbox/WPTG_FILETYPE_GOVERNANCE_PROPOSAL.md` — filetype governance menu

## Technical Constraints

1. **Python 3.14+**, no external deps beyond stdlib (`struct` for WOFF, `json`, `pathlib`, `ast` for .ts/.js scanning, `subprocess` for `git ls-files`)
2. **Two scripts**: `scripts/wptg_filetype_census.py` (Part 1) and `scripts/extension_contribution_audit.py` (Part 2) — separate concerns, separate invocations
3. **WOFF parsing**: Read first 4 bytes, validate magic `0x774F4646`. No full font table parsing.
4. **Codepoint matching**: Normalize `"\\E001"`, `"U+E001"`, `0xE001` to integer comparison.
5. **Bidirectionality is mandatory** for icon chains: every declared glyph must be used, every used reference must be declared.
6. **Lane exclusion is mandatory**: Both scripts must skip paths in the Lane Exclusion table. Hardcode the exclusion patterns. If a path matches, it does not appear in output.
7. **No file mutations**: Neither script may create, delete, move, or modify any tracked file other than its own output artifacts in `audit-reports/` and `codex/mailbox/`.
8. **Envelope**: Standard `@SID:` header per `AGENT_COMMON.md`.
9. **Exit codes**: 0 on PASS, 1 on WARN, 2 on FAIL.

## Why This Is Hard

- **~2700 files across 30+ extensions** — the census alone requires understanding what "normal" looks like for each filetype in each directory context
- **332 log files** that each need classification without running the processes that generated them — pure static forensics
- **Orphan detection requires building a full reference graph** across Python imports, JSON cross-refs, markdown links, manifest paths, and skill invocations
- **Five heterogeneous formats** in the contribution graph validator: JSON, WOFF binary, SVG, TypeScript/JavaScript, package.json schema
- **Bidirectional graph tracing** means the validator must build complete in-memory adjacency, not linear lookups
- **Codepoint normalization** across three representations with no off-by-one tolerance
- **WPTG compliance**: Every anomaly must be graded per the Gold Signal map, every recommendation must propose a preservation-first pathway, every output must record provenance. No destroy recommendations. Ever.

## Acceptance Criteria

1. `uv run scripts/wptg_filetype_census.py` produces a complete filetype census with all anomalies identified, lane exclusions respected, and WPTG gold grades assigned
2. `uv run scripts/extension_contribution_audit.py` exits 0 on the current extension state
3. Introduce a deliberate break (rename one SVG, corrupt one codepoint) → contribution validator catches it
4. All five contribution chains validated with bidirectional integrity
5. Log archaeology triage and governance proposals are **proposal documents only** — zero file mutations outside output artifacts
6. Every anomaly recommendation is preservation-first per WPTG No-Destroy principle

## Prior Art / Context

- `scripts/product_icon_census.py` — codicon *coverage* gaps, not font binary or contribution graph validation
- `scripts/icon_svg_audit.py` — SVG *structure* validation, not manifest binding
- `scripts/theme_parity.py` — key *parity across themes*, not package.json trace
- `scripts/scm_triage.py` — git status classification, not filetype-level WPTG grading
- `WET_PAPER_TO_GOLD_METHODOLOGY.md` — the governing methodology. Read it before starting. The Gold Signal File-Type Affordance Map (§ The Gold Signal) is the classification bible.
- `anti-patterns/codekiller.md` — the anti-pattern this chore is explicitly designed to prevent. If the census or validator would propose deletion, it is broken.
