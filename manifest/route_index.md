# Route index digest

Generated: 2026-05-14T05:44:07.031321+00:00
Source: `manifest/route_index.json` (regenerate via `uv run scripts/route_index.py`)

Sub-lens: compound router over the 4 observation lenses.
For each open noise item, names the method-class that clears it
and the suggested invocation. Auto-applicable methods can be
fired with `--apply`; others are propose-only (need user decision).

## Summary

- Routes computed: 6
- Total noise items routed: 64
- Auto-applicable routes: 1

## Routes (most items first)

### `rust-constraint-bump` — 23 items (propose-only)

- Noise class: `dependabot/rust-direct-pinned`
- Frequency prior (from method_index): 14x
- Suggested invocation: `edit Cargo.toml dependency version, then cargo update`
- Packages (11): atty, curve25519-dalek, ed25519-dalek, gix, gix-fs, gix-pack, gix-transport, openssl, quinn-proto, rand...

### `anchor-correction` — 15 items (propose-only)

- Noise class: `rot/L3-anchor`
- Frequency prior (from method_index): 36x
- Suggested invocation: `fix link path or anchor (e.g., `../` -> `../../`)`
- Sample sources: .github/instructions/agent-priority-protocol.md, .github/instructions/asc-entity-generation.reference.md, .github/instructions/behavioral-scenarios.reference.md, .github/instructions/dcrp-operational-guide.md, .github/instructions/dev-conventions.reference.md...

### `stub-creation-or-tombstone` — 9 items (propose-only)

- Noise class: `rot/ROT-001-phantom-target`
- Frequency prior (from method_index): 1x
- Suggested invocation: `create new file with `lifecycle: stub` frontmatter`
- Sample sources: .github/agents/IronMaiden.agent.md, claude/mailbox/archive/series/SESSION_HANDOFF/SESSION_HANDOFF_2026_03_01_WPTG_SFS_LANE_TRANSFER_TO_CODEX.md, codex/codex-session-logs/archive/MILF-Core-META.md, docs/archive/reports/TRUE_MISSING_FILES_REVIEW.md, docs/archive/sessions/DEVELOPMENT_STATE.md...

### `python-constraint-bump` — 7 items (propose-only)

- Noise class: `dependabot/pip-direct-pinned`
- Frequency prior (from method_index): 21x
- Suggested invocation: `edit pyproject.toml dependency cap, then uv lock`
- Packages (2): flask-cors, gradio

### `uv-lock-upgrade` — 7 items (auto-applicable)

- Noise class: `dependabot/pip-transitive`
- Frequency prior (from method_index): 7x
- Suggested invocation: `uv lock --upgrade-package <pkg>`
- Packages (2): diskcache, pillow

### `npm-constraint-bump` — 3 items (propose-only)

- Noise class: `dependabot/npm-direct-pinned`
- Frequency prior (from method_index): 9x
- Suggested invocation: `edit package.json dependency version, then bun update`
- Packages (1): postcss
