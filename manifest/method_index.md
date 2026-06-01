# Method index digest

Generated: 2026-05-31T22:05:22.287514+00:00
Window: last 60 days (since 2026-04-01)
Source: `manifest/method_index.json` (regenerate via `uv run scripts/method_index.py`)

Methodology: meta-lens that observes which methods cleared prior lens noise.
Compounds with `git_rot_index`, `dependabot_index`, `github_activity_index`.

## Summary

- Commits scanned: 772
- Methodful commits: 104
- Unclassified: 668
- Distinct method classes seen: 9

### By method (frequency)

- `anchor-correction`: 28
- `rust-constraint-bump`: 25
- `python-constraint-bump`: 16
- `npm-constraint-bump`: 12
- `uv-lock-upgrade`: 10
- `tombstone-mark`: 6
- `path-rename-followup`: 5
- `stub-creation`: 1
- `cargo-update`: 1

## Methods (priority: most-used first)

### `anchor-correction` — used 28x (conf 0.61)

- Noise class: `rot/L3-anchor`
- Last used: 2026-05-17
- Invocation: `fix link path or anchor (e.g., `../` -> `../../`)`
- Examples:
  - `ab8596fb` — fix(pointer): revert L4323 anchor — FA5 rejects HTML/line anchors
  - `6da07646` — fix(pointer): add L4323 line anchor to NAS reference link
  - `b6ce5dd5` — fix(rot): truth-up digest annotation + target-side lifecycle guard

### `rust-constraint-bump` — used 25x (conf 0.77)

- Noise class: `dependabot/rust-direct-pinned`
- Last used: 2026-05-31
- Invocation: `edit Cargo.toml dependency version, then cargo update`
- Examples:
  - `636fa991` — feat: add spread-value script for content-value analysis and deduplication
  - `ec51fbd1` — refactor: overhaul file extension classification and counting mechanism
  - `d368d027` — feat: add new bridges and remove obsolete SDK connection files

### `python-constraint-bump` — used 16x (conf 0.81)

- Noise class: `dependabot/pip-direct-pinned`
- Last used: 2026-05-27
- Invocation: `edit pyproject.toml dependency cap, then uv lock`
- Examples:
  - `0893aac7` — Add new dependencies for image processing and geometry manipulation
  - `79dab782` — feat(mcp): consolidate archaeology servers into chthonic-archive
  - `38410a7f` — feat(claudine-lora): C-G5 admitted — Unsloth stack on Windows Python 3.14 + CUDA 12.8

### `npm-constraint-bump` — used 12x (conf 0.63)

- Noise class: `dependabot/npm-direct-pinned`
- Last used: 2026-05-31
- Invocation: `edit package.json dependency version, then bun update`
- Examples:
  - `af05da79` — Update session drain timestamps and workspace hashes; enhance SSOT manifest structure
  - `c559a079` — feat: update pre-commit hook and package.json scripts for improved automation and verification
  - `3b6e15d2` — chore: update chthonic-archive to version 0.2.9 and add new FLUX commands and settings

### `uv-lock-upgrade` — used 10x (conf 0.95)

- Noise class: `dependabot/pip-transitive`
- Last used: 2026-05-17
- Invocation: `uv lock --upgrade-package <pkg>`
- Examples:
  - `84d1383d` — feat: update Named Agent Sovereignty rules and dependencies in copilot-instructions and uv.lock
  - `a7e0aa4b` — feat: add commands for managing Chthonic FLUX master secret
  - `f40d6819` — feat: integrate FluxService into chthonic-archive extension

### `tombstone-mark` — used 6x (conf 1.0)

- Noise class: `rot/L1-surface-cluster`
- Last used: 2026-05-14
- Invocation: `add `lifecycle: tombstone` to file frontmatter`
- Examples:
  - `a8f9d6f2` — fix(rot): true SSOT canon — .github/copilot-instructions.archive.md
  - `8bf359ee` — fix(rot): triage cluster — 3 tombstones + anchor-correction + ROT-008 suppression
  - `97096a6a` — fix(rot): tombstone the 2 ADR_RECOVERED.md files referencing deleted report

### `path-rename-followup` — used 5x (conf 0.8)

- Noise class: `rot/L4-lineage`
- Last used: 2026-05-28
- Invocation: `batch-update broken refs across multiple files (one logical move)`
- Examples:
  - `cfef8cd5` — Remove Agent Common Configuration Document
  - `af3cd781` — tune(pathfinder): AMBIG severity = warning, not error
  - `ab572948` — fix(pathfinder): apply link-rot auto-fixes across 28 markdown files

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
