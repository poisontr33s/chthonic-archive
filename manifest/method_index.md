# Method index digest

Generated: 2026-05-14T04:31:13.489895+00:00
Window: last 60 days (since 2026-03-15)
Source: `manifest/method_index.json` (regenerate via `uv run scripts/method_index.py`)

Methodology: meta-lens that observes which methods cleared prior lens noise.
Compounds with `git_rot_index`, `dependabot_index`, `github_activity_index`.

## Summary

- Commits scanned: 763
- Methodful commits: 95
- Unclassified: 668
- Distinct method classes seen: 9

### By method (frequency)

- `anchor-correction`: 33
- `python-constraint-bump`: 21
- `rust-constraint-bump`: 14
- `npm-constraint-bump`: 9
- `uv-lock-upgrade`: 7
- `path-rename-followup`: 5
- `tombstone-mark`: 4
- `stub-creation`: 1
- `cargo-update`: 1

## Methods (priority: most-used first)

### `anchor-correction` — used 33x (conf 0.64)

- Noise class: `rot/L3-anchor`
- Last used: 2026-05-13
- Invocation: `fix link path or anchor (e.g., `../` -> `../../`)`
- Examples:
  - `145254a9` — feat(rot-index): L4 LINEAGE detector — ROOT-001 mass-delete ancestry
  - `770829a2` — fix(rot-index): GFM duplicate-suffix slugs + unified target_structure cache
  - `f8c05ab9` — feat(rot-index): L3 ANCHOR detectors — ROT-006 anchor_missing, ROT-007 line_anchor_stale

### `python-constraint-bump` — used 21x (conf 0.77)

- Noise class: `dependabot/pip-direct-pinned`
- Last used: 2026-05-10
- Invocation: `edit pyproject.toml dependency cap, then uv lock`
- Examples:
  - `38410a7f` — feat(claudine-lora): C-G5 admitted — Unsloth stack on Windows Python 3.14 + CUDA 12.8
  - `dca3cb67` — fix(embedding_explorer): address GHPR review comments
  - `1d594d4f` — G7+G0: sdnext_g0_probe, manifest, pyproject optimum update

### `rust-constraint-bump` — used 14x (conf 0.83)

- Noise class: `dependabot/rust-direct-pinned`
- Last used: 2026-05-02
- Invocation: `edit Cargo.toml dependency version, then cargo update`
- Examples:
  - `b4cd3468` — feat(vs_battery): add script for Visual Studio battery management and auditing
  - `f8d1131a` — V9: raw terminal mode (crossterm) + Ω-3 XP trail write
  - `1c073231` — feat(vulkan-lab): V6 cli-renderer scaffold — G1 headless instance + shader stubs

### `npm-constraint-bump` — used 9x (conf 0.64)

- Noise class: `dependabot/npm-direct-pinned`
- Last used: 2026-05-08
- Invocation: `edit package.json dependency version, then bun update`
- Examples:
  - `64ce45cf` — fix: update GPU specifications in epoch reference document
  - `827eae89` — feat: update version to 0.2.7 and add new command for selecting Claude Design Export
  - `144a1557` — fix: update version to 0.2.6 in package.json

### `uv-lock-upgrade` — used 7x (conf 1.0)

- Noise class: `dependabot/pip-transitive`
- Last used: 2026-05-14
- Invocation: `uv lock --upgrade-package <pkg>`
- Examples:
  - `150c7b10` — feat(workspace): add api_pool.ps1 script loading to launch workflow
  - `685a4311` — Refactor code structure and remove redundant sections for improved readability and maintainability
  - `b7746613` — feat(tools): add tool validation script and update toolchain reports

### `path-rename-followup` — used 5x (conf 0.8)

- Noise class: `rot/L4-lineage`
- Last used: 2026-05-13
- Invocation: `batch-update broken refs across multiple files (one logical move)`
- Examples:
  - `af3cd781` — tune(pathfinder): AMBIG severity = warning, not error
  - `ab572948` — fix(pathfinder): apply link-rot auto-fixes across 28 markdown files
  - `dc42cac8` — docs: consolidate documentation sprawl — 80 files reorganized

### `tombstone-mark` — used 4x (conf 1.0)

- Noise class: `rot/L1-surface-cluster`
- Last used: 2026-05-13
- Invocation: `add `lifecycle: tombstone` to file frontmatter`
- Examples:
  - `97096a6a` — fix(rot): tombstone the 2 ADR_RECOVERED.md files referencing deleted report
  - `5c60170c` — feat(rot-index): skip code-fences, 2 more tombstones, git_truth enrichment
  - `077302b2` — docs(session): landing page + redux addendum (hour-to-4s postmortem)

### `stub-creation` — used 1x (conf 1.0)

- Noise class: `rot/ROT-001-phantom-target`
- Last used: 2026-05-13
- Invocation: `create new file with `lifecycle: stub` frontmatter`
- Examples:
  - `9105bbe7` — fix(rot): SSOTIFICATION depth-bug fully resolved (15 broken -> 0)

### `cargo-update` — used 1x (conf 1.0)

- Noise class: `dependabot/rust-transitive`
- Last used: 2026-04-30
- Invocation: `cargo update -p <pkg> (in directory of Cargo.lock)`
- Examples:
  - `b4bbf0f6` — chore(vulkan-lab): remove cli-renderer target/ and Cargo.lock from tracking

## Catalog (defined, not yet observed in window)

- `bun-update` → addresses `dependabot/npm-transitive`
- `code-fence-fix` → addresses `rot/false-positive-code-block`
