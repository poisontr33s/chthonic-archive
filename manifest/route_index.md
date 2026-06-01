# Route index digest

Generated: 2026-05-31T22:05:22.516727+00:00
Source: `manifest/route_index.json` (regenerate via `uv run scripts/route_index.py`)

Sub-lens: compound router over the 4 observation lenses.
For each open noise item, names the method-class that clears it
and the suggested invocation. Auto-applicable methods can be
fired with `--apply`; others are propose-only (need user decision).

## Summary

- Routes computed: 6
- Total noise items routed: 202
- Auto-applicable routes: 1

## Routes (most items first)

### `anchor-correction` — 87 items (propose-only)

- Noise class: `rot/L3-anchor`
- Frequency prior (from method_index): 28x
- Suggested invocation: `fix link path or anchor (e.g., `../` -> `../../`)`
- Sample sources: .github/INTEGRATION_MAP.md, .github/SESSION_RESUME.md, .github/SSOT_EVOLUTION_1.0_TO_1.5_BLUEPRINT.md, .github/STRUCTURAL_INTEGRITY_ANALYSIS.md, .github/VALIDATION_REPORT.md...

### `stub-creation-or-tombstone` — 68 items (propose-only)

- Noise class: `rot/ROT-001-phantom-target`
- Frequency prior (from method_index): 1x
- Suggested invocation: `create new file with `lifecycle: stub` frontmatter`
- Sample sources: .github/agents/Chthonic-Archivist.agent.md, .github/instructions/ankh-workflow.instructions.md, .temple/protocols/SESSION_2026_05_24_25_REDUX.md, claude-codex-gemini/triadic-session-context/BUN_SEGFAULT_2026_02_01.md, claude/mailbox/CODEX_HANDOFF_FLUX_VISIBILITY_STATUSBAR_2026_05_15.md...

### `rust-constraint-bump` — 24 items (propose-only)

- Noise class: `dependabot/rust-direct-pinned`
- Frequency prior (from method_index): 25x
- Suggested invocation: `edit Cargo.toml dependency version, then cargo update`
- Packages (11): atty, curve25519-dalek, ed25519-dalek, gix, gix-fs, gix-pack, gix-transport, openssl, quinn-proto, rand...

### `uv-lock-upgrade` — 10 items (auto-applicable)

- Noise class: `dependabot/pip-transitive`
- Frequency prior (from method_index): 10x
- Suggested invocation: `uv lock --upgrade-package <pkg>`
- Packages (4): diffusers, diskcache, idna, pillow

### `python-constraint-bump` — 8 items (propose-only)

- Noise class: `dependabot/pip-direct-pinned`
- Frequency prior (from method_index): 16x
- Suggested invocation: `edit pyproject.toml dependency cap, then uv lock`
- Packages (3): flask-cors, gradio, idna

### `npm-constraint-bump` — 5 items (propose-only)

- Noise class: `dependabot/npm-direct-pinned`
- Frequency prior (from method_index): 12x
- Suggested invocation: `edit package.json dependency version, then bun update`
- Packages (1): postcss
