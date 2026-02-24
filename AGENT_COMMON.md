# Agent Common Configuration

Referenced by: `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`

## Bifurcation

| Domain | Location | Purpose |
|--------|----------|---------|
| **Temple** | `.temple/` | Agent protocols, methodology, handoffs, skills |
| **Game** | `game/` | Lore, systems, dialogue, design — cRPG content |

Rule: "Is this TEMPLE or GAME?" before creating anything.

## Execution Invariants

- **Shell:** PowerShell 7+ (`pwsh`). Never bash on Windows. See [PWSH_RULES.md](PWSH_RULES.md).
- **Python:** `uv` is the default Python lane (`uv run <script.py>`). Never raw `python` or `pip`.
- **Ruby:** use `rv` for runtime and gem/tool isolation.
- **Go:** use `goup` for Go runtime ownership.
- **JS/TS:** prefer `bun` for extension scripts; 
- **Rust:** `cargo build`
- **cmd.exe:** Never. No `cmd /c` wrappers. Will trigger Windows "open with" dialogs.
- **Platform:** Windows 11, VS Code Insiders, repo root = working dir.
- **Git EOL:** LF via `.gitattributes`. `core.autocrlf=false`.
- **Dependency SSOT:** `pyproject.toml` (Python), `Gemfile`/`.ruby-version` (Ruby), `go.mod` (Go), `package.json` (JS/TS), `Cargo.toml` (Rust).

## Canonical Paths

| Path | Purpose |
|------|---------|
| `.codex/skills` | Codex skills |
| `.claude/skills` | Claude skills |
| `codex/mailbox` | Codex mailbox (active) |
| `claude/mailbox` | Claude mailbox (active) |
| `.temple/protocols/` | Agent protocols |
| `.temple/methodology/` | Shared methodology |
| `.temple/handoffs/` | Inter-agent handoffs |

Hidden mailbox dirs (`.codex/mailbox`, `.claude/mailbox`) are non-canonical — `.gitkeep` only.

## Commands

| Command | Purpose |
|---------|---------|
| `bun run dev` | Dev mode |
| `bun run build` | Build |
| `bun run test` | Test |
| `bun run lint` | Lint |
| `cargo build` | Rust build |
| `uv run <script>` | Python execution |
| `rv --version` | Ruby lane health |
| `goup --version` | Go lane health |
| `fnm --version` / `volta --version` | Node lane health |

## File Governance

Every file is gold. Agents propose changes; user executes. See [WET_PAPER_TO_GOLD_METHODOLOGY.md](WET_PAPER_TO_GOLD_METHODOLOGY.md) (`WPTG`).

### Codekiller Addendum (Shared)

- No cleanup exemption for agent-created files once persisted in the repo workspace.
- Before edits that remove code/blocks/files, run salvage-first transmutation and preserve filetype semantics (`{ext}`-aware).
- Record provenance for salvage/fusion outputs (source -> transformed destination).
- Delete-only simplification is non-compliant for Codex, Claude, and Gemini lanes.

## Architecture

Rust-native polyglot: `uv` (Python), `rv` (Ruby), `goup` (Go), + `bun` is a "batteries included" drop-in-node-replacement ex. native; (Node/JS/TS/REACT/NEXT.JS/TAILWINDCSS/LIGHTNINGCSS/etc.). Rust core. `src/` = Rust core. 

## Some ...`scripts/` = tooling. `mas_mcp/` = Python MCP. `extensions/` = VS Code extension. `docs/` = design docs and standards. `.temple/` = agent protocols and methodology. `.claude/skills/` and `.codex/skills/` = agent skills.

## Triad

Claude (protocol/lore) → Codex (structure/enforcement) → Gemini (velocity/batch).
Anchors: [CLAUDE.md](CLAUDE.md), [AGENTS.md](AGENTS.md), [GEMINI.md](GEMINI.md).
Methodology: [.temple/methodology/TRIAD_METHODOLOGY.md](.temple/methodology/TRIAD_METHODOLOGY.md).
