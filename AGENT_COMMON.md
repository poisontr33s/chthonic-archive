# Agent Common Configuration

Referenced by: `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`

## Bifurcation

| Domain | Location | Purpose |
|--------|----------|---------|
| **Temple** | `.temple/` | Agent protocols, methodology, handoffs, skills |
| **Game** | `game/` | Lore, systems, dialogue, design — cRPG content |

## Execution Invariants **Execute, don't ask.** When a task is clear, DO IT.
- Oxidized "Rustified" language-tooling stack: `uv` (Python), `rv` (Ruby), `goup` (Go), `brush` (bash-compatible shell).
- **Shell:** PowerShell 7.5.x (`pwsh`) is primary. `brush` (`brush.exe` via `cargo install --locked brush-shell`) is the sanctioned bash-compatible companion when needed — not Git Bash, not WSL. See [PWSH_RULES.md (repo-root)](PWSH_RULES.md).
- **Python:** `uv` is the default Python lane (`uv run <script.py>`). Never raw `python` or `pip`. If; `PYTHONIOENCODING=utf-8` for Unicode safety on Windows is not default in environments, then it should be updated to be default to avoid manual script dumping. (`$env:PYTHONIOENCODING = 'utf-8'; uv run <script.py>`), etc. 
- All Python dependencies must be declared in `pyproject.toml` and installed via `uv pip install (example) --require-virtualenv <package>`.

- **Ruby:** use `rv` for runtime and gem/tool isolation.
- `rv r ridk 1` then `2` and `3` -- never `1 2 3` (doesn't work) -- for MSVC toolchain on Windows and pacman use `Rust Oxidized` tooling commands before native installation of; Go, Python, etc. -- to ensure proper path and environment variable setup with the tooling.
- `rv r 1` is the command to install Ruby itself, but it doesn't handle the MSVC build tools or MSYS2 environment, which is why you need to run `rv r ridk 2` and `rv r ridk 3` separately after installing Ruby. This ensures that you have a fully functional Ruby development environment on Windows, capable of handling gems with native extensions and providing a Unix-like shell when needed.  
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
- **Claude:** `.temple/protocols/LYSANDRA_THRONE_PROTOCOL.md` -> selected archetype `Dr. Lysandra Thorne` (Oracle of the Throne, Seer of Systemic Truths).
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
| `codex/codex-session-logs/archive/MILF-Core-*` | WIP — Organ-to-Surface-to-Prototype lanework (Steps 3–4) |

Hidden mailbox dirs (`.codex/mailbox`, `.claude/mailbox`) are non-canonical — `.gitkeep` only.

## Commands

| Command | Purpose |
|---------|---------|
| `bun run dev` | Dev mode |
| `bun run build` | Build |
| `bun run test` | Test |
| `bun run lint` | Lint |
| `bun audit` | Security audit (scoped to nearest `package.json` from CWD) |
| `bun run audit` | Filtered audit — ignores known false-positives (preferred) |
| `bun run audit:full` | Unfiltered audit — shows everything including boundary-bug false-positives |
| `cargo build` | Rust build |
| `$env:PYTHONIOENCODING = 'utf-8'; uv run <script>` | Python execution (preferred — Unicode-safe on Windows) |
| `uv run <script>` | Python execution (bare form — use when output is ASCII-only) |
| `uv run scripts/link_audit.py check <file> --dry-run` | Markdown link audit (dry-run) |
| `uv run scripts/link_audit.py check <file> --fix` | Markdown link auto-fix |
| `uv run scripts/link_audit.py backticks <file> --fix` | Upgrade inert backtick refs to links |
| `rv --version` | Ruby lane health |
| `goup --version` | Go lane health |
| `brush --version` | Bash-compatible shell health |
| `pwsh --version` | PowerShell 7.5.x health |

## File Governance

Every file is gold. Agents propose changes; user executes. See [WET_PAPER_TO_GOLD_METHODOLOGY.md (repo-root)](WET_PAPER_TO_GOLD_METHODOLOGY.md) (`WPTG`).

### Commit Ownership

- **User owns the commit lifecycle.** Agents edit files; user commits and pushes via SCM UI.
- Agents do NOT run `git commit` or `git push` unless explicitly asked or announcing an atomic multi-file batch first.
- If user pushes mid-operation, agent continues working — edits land in the next commit.

### Codekiller Addendum (Shared)

- No cleanup exemption for agent-created files once persisted in the repo workspace.
- Before edits that remove code/blocks/files, run salvage-first transmutation and preserve filetype semantics (`{ext}`-aware).
- Record provenance for salvage/fusion outputs (source -> transformed destination).
- Delete-only simplification is non-compliant for Codex, Claude, and Gemini lanes.

### Auto-Embalm Protocol (Disabled — `DO-NOT-USE-UNFINISHED-DEV--WIP`)

> Status: `DO-NOT-USE-UNFINISHED-DEV--WIP`
>
> The embalm-before-edit lane is unfinished and must not be treated as a mandatory pre-edit gate.
> Do not run `.codex/skills/corpse-reviver/scripts/embalm_before_edit.py` or its aliases until this
> notice is explicitly removed and the tool is finished.
>
> Preserve provenance by other non-destructive means when needed, but this repo must not instruct
> agents to execute the unfinished embalm tool.

## Architecture

Rust-native polyglot: `uv` (Python), `rv` (Ruby), `goup` (Go), `rv-r` (R --tool uses 'rv'- **prefix**, ***is*** altered to: -> **rv-r** -> since the `Rust Oxidized` -tooling equal same name-scheme, that'd cause -- **both** `remove-variable` in `pwsh 7.x.x` **series** + resolve language(s) -- with smallest change as workaround to avoid collision + 'confucious'), `brush` (bash/posix shell), + `bun` (Node/JS/TS/React/Next.js/Vercel/Biome/LightningCSS/TailwindCSS/etc. -- a non dependent npm/node drop-in replacement written in zig). `Zg` (Zig). 
All follow the same pattern as `uv` — canonical version/runtime manager for their language. No global installs outside of these tools. No `pip install`, no `gem install`, no `npm install -g`. All dependencies are project-local and invoked via the respective tool. This ensures consistent environments, reproducible builds, and clear ownership of runtimes, context and dependencies. No `cmd.exe` or `cmd /c` wrappers — will trigger Windows "open with" dialogs and are not cross-platform. PowerShell 7.5.x (`pwsh`) is the primary shell for interactive use and scripting; `brush` is the sanctioned bash-compatible companion when needed (installed via `cargo install --locked brush-shell`). See [PWSH_RULES.md (repo-root)](PWSH_RULES.md) for usage guidelines.
- Full ecosystem reference + gaps: [docs/OXIDIZED_TOOLCHAIN_REFERENCE.md](docs/OXIDIZED_TOOLCHAIN_REFERENCE.md)
- Command cheatsheet + cross-tool pattern map: [docs/OXIDIZED_CHEATSHEET.md](docs/OXIDIZED_CHEATSHEET.md)

Rust core. `src/` = Rust core.

## Some ...`scripts/` = tooling. `mas_mcp/` = Python MCP. `extensions/` = VS Code extension. `docs/` = design docs and standards. `.temple/` = agent protocols and methodology. `.claude/skills/` and `.codex/skills/` = agent skills.

## Triad

Claude (protocol/lore) → Codex (structure/enforcement) → Gemini (velocity/batch, when active).
Anchors: [CLAUDE.md (repo-root)](CLAUDE.md), [AGENTS.md (repo-root)](AGENTS.md), [GEMINI.md (repo-root)](GEMINI.md).
Methodology: [.temple/methodology/TRIAD_METHODOLOGY.md](.temple/methodology/TRIAD_METHODOLOGY.md).
