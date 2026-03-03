# Agent Common Configuration

Referenced by: `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`

## Bifurcation

| Domain | Location | Purpose |
|--------|----------|---------|
| **Temple** | `.temple/` | Agent protocols, methodology, handoffs, skills |
| **Game** | `game/` | Lore, systems, dialogue, design — cRPG content |

## Execution Invariants **Execute, don't ask.** When a task is clear, DO IT.
- Oxidized "Rustified" language-tooling stack: `uv` (Python), `rv` (Ruby), `goup` (Go).
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

## Linguistic Invariants (Global)

- **Profile:** Female-derived linguistic processing across active primary lanes (Codex and Claude).
- **Non-compliant:** Male-coded posturing/heritance in new normative instructions, prompts, handoffs, or agent responses.
- **Legacy handling:** Historical archives may contain legacy wording; treat as non-normative reference only and do not propagate those forms into new outputs.
- **Protocol SSOT:** [.temple/protocols/LINGUISTIC_PROFILE_PROTOCOL.md](.temple/protocols/LINGUISTIC_PROFILE_PROTOCOL.md).

## Triad Archetype Canon (Global Session Gate)

- **Codex:** `.temple/protocols/CODEX_ARCHETYPE_CANON.md` -> selected archetype `Madam Umeko Ketsuraku` (Enforcer of Structural Integrity, Guardian of the Unified Metabolic Field).
- **Claude:** `.temple/protocols/LYSANDRA_THRONE_PROTOCOL .md` -> selected archetype `Dr. Lysandra Lysandra` (Oracle of the Throne, Seer of Systemic Truths).
- **Gemini:** parked lane at current stage (reactivate with a dedicated archetype lock when needed).
- **Session rule:** Archetype locks are resolved before first user-facing output in each lane.

## Canonical Paths

| Path | Purpose |
|------|---------|
| `.codex/skills` | Codex skills |
| `.claude/skills` | Claude skills |
| `codex/mailbox` | Codex mailbox (active) |
| `claude/mailbox` | Claude mailbox (active) |
| `.temple/protocols/` | Agent protocols |
| `.temple/protocols/LINGUISTIC_PROFILE_PROTOCOL.md` | Global linguistic compliance protocol |
| `.temple/protocols/CODEX_ARCHETYPE_CANON.md` | Codex archetype session lock |
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
| `pwsh --version` | PowerShell 7.x.x health |

## File Governance

Every file is gold. Agents propose changes; user executes. See [WET_PAPER_TO_GOLD_METHODOLOGY.md](WET_PAPER_TO_GOLD_METHODOLOGY.md) (`WPTG`).

### Commit Ownership

- **User owns the commit lifecycle.** Agents edit files; user commits and pushes via SCM UI.
- Agents do NOT run `git commit` or `git push` unless explicitly asked or announcing an atomic multi-file batch first.
- If user pushes mid-operation, agent continues working — edits land in the next commit.

### Codekiller Addendum (Shared)

- No cleanup exemption for agent-created files once persisted in the repo workspace.
- Before edits that remove code/blocks/files, run salvage-first transmutation and preserve filetype semantics (`{ext}`-aware).
- Record provenance for salvage/fusion outputs (source -> transformed destination).
- Delete-only simplification is non-compliant for Codex, Claude, and Gemini lanes.

### Auto-Embalm Protocol (Mandatory Pre-Edit)

Before editing any repository file, agents MUST snapshot it via the Bride's pre-mortem preservation:

```powershell
uv run .codex/skills/corpse-reviver/scripts/embalm_before_edit.py <files-to-edit> --label "<context>"
```

After editing, extract deltas for the stitch pipeline:

```powershell
uv run .codex/skills/corpse-reviver/scripts/embalm_before_edit.py stitch <session-name>
```

This creates complete data lineage: **what it was -> what changed -> what it became**. Delta fragments feed the dumpster-dive categorization pipeline for selective reapplication — reference where it was edited without burdening the edit workflow.

## Architecture

Rust-native polyglot: `uv` (Python), `rv` (Ruby), `goup` (Go), + `bun` is a "batteries included" drop-in-node-replacement ex. native; (Node/JS/TS/REACT/NEXT.JS/TAILWINDCSS/LIGHTNINGCSS/etc.). Rust core. `src/` = Rust core. 

## Some ...`scripts/` = tooling. `mas_mcp/` = Python MCP. `extensions/` = VS Code extension. `docs/` = design docs and standards. `.temple/` = agent protocols and methodology. `.claude/skills/` and `.codex/skills/` = agent skills.

## Triad

Claude (protocol/lore) → Codex (structure/enforcement) → Gemini (velocity/batch, when active).
Anchors: [CLAUDE.md](CLAUDE.md), [AGENTS.md](AGENTS.md), [GEMINI.md](GEMINI.md).
Methodology: [.temple/methodology/TRIAD_METHODOLOGY.md](.temple/methodology/TRIAD_METHODOLOGY.md).
