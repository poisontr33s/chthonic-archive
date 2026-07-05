# Method index digest

Generated: 2026-07-04T07:08:53.311745+00:00
Window: last 60 days (since 2026-05-05)
Source: `manifest/method_index.json` (regenerate via `uv run scripts/method_index.py`)

Methodology: meta-lens that observes which methods cleared prior lens noise.
Compounds with `git_rot_index`, `dependabot_index`, `github_activity_index`.

## Summary

- Commits scanned: 534
- Methodful commits: 105
- Unclassified: 429
- Distinct method classes seen: 9

### By method (frequency)

- `rust-constraint-bump`: 33
- `anchor-correction`: 32
- `npm-constraint-bump`: 10
- `python-constraint-bump`: 10
- `uv-lock-upgrade`: 6
- `tombstone-mark`: 6
- `path-rename-followup`: 4
- `cargo-update`: 3
- `stub-creation`: 1

## Methods (priority: most-used first)

### `rust-constraint-bump` — used 33x (conf 0.77)

- Noise class: `dependabot/rust-direct-pinned`
- Last used: 2026-07-04
- Invocation: `edit Cargo.toml dependency version, then cargo update`
- Examples:
  - `813e5ba6` — feat(ci): stabilize pin-truth and verify host preflight
  - `70bb9d7d` — Update VS2026 Elevated Validation and related configurations
  - `dfc8f88a` — Updates

### `anchor-correction` — used 32x (conf 0.68)

- Noise class: `rot/L3-anchor`
- Last used: 2026-06-26
- Invocation: `fix link path or anchor (e.g., `../` -> `../../`)`
- Examples:
  - `a3ced40f` — - Refinements in few documents + Pruning
  - `ca2793d9` — feat(render): GPU profiling gate + WGS84 geodesy substrate + Ellipsoid Site 1
  - `84d0fb3f` — feat(render): physically coupled atmosphere and live weather spine (Rung 6: Stage 3A-C)

### `npm-constraint-bump` — used 10x (conf 0.68)

- Noise class: `dependabot/npm-direct-pinned`
- Last used: 2026-06-30
- Invocation: `edit package.json dependency version, then bun update`
- Examples:
  - `33acda9b` — chore: update toolchain doctor report and frontier landscape versions
  - `9fb318fb` — Add Bun SDK probe harness
  - `af6838d5` — feat(bathymetry): NOAA NCEI GeoTIFF pipeline + shader source ledger

### `python-constraint-bump` — used 10x (conf 0.94)

- Noise class: `dependabot/pip-direct-pinned`
- Last used: 2026-06-21
- Invocation: `edit pyproject.toml dependency cap, then uv lock`
- Examples:
  - `171e1b98` — feat(python): migrate cu128→cu132; torch 2.12.1 stable; drop nightly + environments lock
  - `97aef96b` — feat(python): complete modernization pass — all 5 blockers resolved
  - `c6c1160a` — fix(python): Clarify Step 5 tokenizers blocker — transformers hard runtime check

### `uv-lock-upgrade` — used 6x (conf 0.92)

- Noise class: `dependabot/pip-transitive`
- Last used: 2026-06-20
- Invocation: `uv lock --upgrade-package <pkg>`
- Examples:
  - `df80318a` — updates
  - `84d1383d` — feat: update Named Agent Sovereignty rules and dependencies in copilot-instructions and uv.lock
  - `a7e0aa4b` — feat: add commands for managing Chthonic FLUX master secret

### `tombstone-mark` — used 6x (conf 1.0)

- Noise class: `rot/L1-surface-cluster`
- Last used: 2026-05-14
- Invocation: `add `lifecycle: tombstone` to file frontmatter`
- Examples:
  - `a8f9d6f2` — fix(rot): true SSOT canon — .github/copilot-instructions.archive.md
  - `8bf359ee` — fix(rot): triage cluster — 3 tombstones + anchor-correction + ROT-008 suppression
  - `97096a6a` — fix(rot): tombstone the 2 ADR_RECOVERED.md files referencing deleted report

### `path-rename-followup` — used 4x (conf 0.8)

- Noise class: `rot/L4-lineage`
- Last used: 2026-06-03
- Invocation: `batch-update broken refs across multiple files (one logical move)`
- Examples:
  - `c19ecb8b` — Refactor character and lore paths; update schema audit and add new scripts
  - `cfef8cd5` — Remove Agent Common Configuration Document
  - `af3cd781` — tune(pathfinder): AMBIG severity = warning, not error

### `cargo-update` — used 3x (conf 1.0)

- Noise class: `dependabot/rust-transitive`
- Last used: 2026-06-28
- Invocation: `cargo update -p <pkg> (in directory of Cargo.lock)`
- Examples:
  - `82a0e5c8` — fixes
  - `fa9942ee` — - modernizing rust workspace and deps
  - `2895ddfc` — feat: update agent-client-protocol and github-copilot-sdk versions; add sdk currency comparison functionality to sourcer scripts

### `stub-creation` — used 1x (conf 1.0)

- Noise class: `rot/ROT-001-phantom-target`
- Last used: 2026-05-13
- Invocation: `create new file with `lifecycle: stub` frontmatter`
- Examples:
  - `9105bbe7` — fix(rot): SSOTIFICATION depth-bug fully resolved (15 broken -> 0)

## Catalog (defined, not yet observed in window)

- `bun-update` → addresses `dependabot/npm-transitive`
- `code-fence-fix` → addresses `rot/false-positive-code-block`
