# Agent Common Configuration

Referenced by: `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`

## Bifurcation

| Domain | Location | Purpose |
|--------|----------|---------|
| **Temple** | `.temple/` | Agent protocols, methodology, handoffs, skills |
| **Game** | `game/` | Lore, systems, dialogue, design — cRPG content |

## Execution Invariants **Execute, don't ask.** When a task is clear, DO IT.
- Oxidized "Rustified" language-tooling stack: `uv` (Python), `rv` (Ruby), `goup` (Go), `brush` (bash-compatible shell).
- **Shell:** PowerShell 7.6.x (`pwsh`) is primary. `brush` (`brush.exe` via `cargo install --locked brush-shell`) is the sanctioned bash-compatible companion when needed — not Git Bash, not WSL. See [PWSH_RULES.md (repo-root)](PWSH_RULES.md).
- **Python:** `uv` is the default Python lane (`uv run <script.py>`). Never raw `python` or `pip`. If; `PYTHONIOENCODING=utf-8` for Unicode safety on Windows is not default in environments, then it should be updated to be default to avoid manual script dumping. (`$env:PYTHONIOENCODING = 'utf-8'; uv run <script.py>`), etc. 
- All Python dependencies must be declared in `pyproject.toml` and installed via `uv pip install (example) --require-virtualenv <package>`.

- **Ruby:** use `rv` for runtime and gem/tool isolation.
  - Install a Ruby version: `rv ruby install ruby-4.0.3` (downloads RubyInstaller + embedded MSYS2).
  - Pin repo version: `rv ruby pin 4.0.3` (writes `.ruby-version`).
  - MSYS2 devkit components (run once after install, separately — combined args don't work): `rv r ridk install 1` → `rv r ridk install 2` → `rv r ridk install 3`. Component 1 = MSYS2 base, 2 = system update, 3 = MINGW toolchain (gcc, required for native gems).
  - Run with ruby on PATH: `rv r <cmd>` (e.g. `rv r bundle install`, `rv r gem list`).
  - Config anchors: `.ruby-version` (version pin, tracked), `Gemfile`/`Gemfile.lock` (deps + runtime constraint, tracked), `.bundle/config` (vendor path isolation, tracked — equivalent to `uv.toml`'s `python-preference = "only-managed"`). No `rv.toml` exists — rv config surface is intentionally minimal.
  - No bare `gem install`. Frozen lockfile install: `rv ci`. Dev install (allows lockfile updates): `rv r bundle install`. Run gem CLI without bundle: `rvx <gem>`. Isolated global tool: `rv tool install <gem>`.
  - **ZJIT+YJIT native Windows (BUILT ✅):** Ruby 4.0.3 with ZJIT and YJIT compiled natively on Windows 11 via MSYS2 UCRT64. Key fixes required: (1) `mingw-w64-ucrt-x86_64-rust` (GNU rustc, not MSVC) to produce `libruby.a`; (2) empty sentinel `.o` in `defs/jit.mk` mingw branch to bypass COFF PE `_tls_used` TLS partial-link failure; (3) `--whole-archive libruby.a` in SOLIBS+RUSTLIBS; (4) `-lntdll -luserenv` for Rust std NT APIs; (5) `-Wl,--allow-multiple-definition` for `lgamma_r` conflict; (6) `jit.c rb_jit_mark_writable` must use `VirtualAlloc(MEM_COMMIT, PAGE_READWRITE)` not `VirtualProtect` (reserved-only pages can't be VirtualProtect'd). Installed at `%APPDATA%\rv\rubies\ruby-4.0.3-zjit\`. Pinned: `rv ruby pin 4.0.3-zjit`. Run: `rv r ruby --zjit -e "puts RubyVM::ZJIT.enabled?"` → `true`. Build script: `build/ruby-zjit/build.sh` (invoke via MSYS2 bash). Known issue: `socket.so`, `bigdecimal`, `json/parser` bundled gem exts fail to build (GCC 15 symbol/declaration conflicts unrelated to ZJIT) — causes `RubyGems not loaded` warning; core functionality unaffected.
- **Go:** use `goup` for Go runtime ownership.
- **JS/TS:** prefer `bun` for extension scripts.
  - **Shebang rule (CRITICAL — recurring bug):** `#!/usr/bin/env bun` MUST be **line 1** of any CLI `.ts` script. All other content (`// @SID:`, comments, envelope blocks) comes AFTER the shebang. Library modules (non-CLI, `src/` files imported but not executed directly) omit the shebang entirely.
  - **Anti-pattern (causes Bun SyntaxError — this is why shebangs keep breaking):**
    ```typescript
    // @SID: SCRIPT_XXX_V1  ← ❌ NEVER put any comment before shebang
    #!/usr/bin/env bun       ← ❌ Bun SyntaxError: shebang must be line 1
    ```
  - **Correct form:**
    ```typescript
    #!/usr/bin/env bun       ← ✅ Line 1, always first
    // @SID: SCRIPT_XXX_V1  ← ✅ Line 2+, after shebang
    ```
  - **Lint:** `bun run lint:shebang` checks all tracked `.ts` files. Run before committing new scripts.
- **Rust:** `cargo build`
- **Polyglot CLI extras (Rust-native, `~/.cargo/bin`):** Prefer these over legacy equivalents in agent commands:

  | Tool | Replaces | Notes |
  |------|----------|-------|
  | `rg` (ripgrep) | `grep` / `Select-String` | gitignore-aware, no alias needed |
  | `bat` | `cat` | `bat --style=plain` for raw output in scripts; no PS name collision |
  | `fd` | `find` | `fd <pattern>` from cwd by default |
  | `delta` | `diff` | syntax-highlighted pager; set as git pager |
  | `hyperfine` | `time` | `hyperfine 'cmd1' 'cmd2'` |
  | `tokei` | `cloc` | `tokei .` — LOC by language |
  | `xh` | `curl`/`httpie` | `xh GET https://...`; HTTPie-compatible syntax |

  Not installed (add via `cargo install` if needed): `eza`/`lsd` (ls), `dust` (du), `procs` (ps).

  **pwsh alias map (collision-only):** `rv` → `rvw.exe` (Ruby manager, displaces PS built-in `rv = Remove-Variable`). `rvar` → `Remove-Variable` (preserves displaced built-in). All other Rust CLI tools (`bat`, `rg`, `fd`, `delta`, `hyperfine`, `tokei`, `xh`) have no same-name PS collision — use directly. Ruby devkit (MSYS2 ucrt64 gcc/make): gated by default; `Enable-RubyDevKit` / `Disable-RubyDevKit` toggle per-session.

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
| `bun run ci:staged` | Local pre-commit gate: shebang, script metadata, uv usage, blessing, Markdown links, and offline GitHub/GFM URL shapes |
| `bun run ignore:audit` | Detect source-shaped files hidden by allowlist `.gitignore` rules |
| `uv run scripts/link_audit.py check <file> --dry-run` | Markdown link audit (dry-run) |
| `uv run scripts/link_audit.py check <file> --fix` | Markdown link auto-fix |
| `bun run links:audit` | Markdown link audit for files changed vs HEAD |
| `bun run links:fix` | Markdown link auto-fix for files changed vs HEAD |
| `bun run pathfinder:audit` | Alias for the upgraded Markdown path/heading-anchor/line-link audit |
| `bun run pathfinder:gfm` | Pathfinder audit including same-repo GitHub/GFM HTTP URL shapes, bare GitHub URLs, and README media refs |
| `bun run pathfinder:gfm:online` | Pathfinder GitHub/GFM audit with live HTTP checks for GitHub pages/issues/assets |
| `uv run scripts/link_audit.py backticks <file> --fix` | Upgrade inert backtick refs to links |
| `rv ruby list` | Ruby lane health (lists installed + active version) |
| `rv ci` | Install ruby deps from lockfile, frozen (= `uv sync --frozen`) |
| `rv r bundle install` | Install ruby deps, allows lockfile updates (dev use only) |
| `rv r bundle exec rubocop` | Ruby lint + style (= `uv run ruff check`) |
| `rv r bundle exec rubocop -A` | Ruby lint autocorrect (= `uv run ruff check --fix`) |
| `rvx <gem> [args]` | Run gem CLI without project bundle (= `uvx`) |
| `rv tool install <gem>` | Install gem as isolated global tool (= `uv tool install`) |
| `rv r bundle exec ruby -e "require 'minitest/autorun'"` | Run ruby tests (= `uv run pytest`) |
| `goup --version` | Go lane health |
| `brush --version` | Bash-compatible shell health |
| `pwsh --version` | PowerShell 7.6.x health |
| `bun upgrade` | Upgrade bun itself (self-hosted, no winget needed) |
| `chthonic gemini update` | Update Gemini CLI + self-heal audit in both scopes (canonical path) |

## File Governance

Every file is gold. Agents propose changes; user executes. See [WET_PAPER_TO_GOLD_METHODOLOGY.md (repo-root)](WET_PAPER_TO_GOLD_METHODOLOGY.md) (`WPTG`).

### Commit Ownership

- **User owns the commit lifecycle.** Agents edit files; user commits and pushes via SCM UI.
- Agents do NOT run `git commit` or `git push` unless explicitly asked or announcing an atomic multi-file batch first.
- Before a commit, run `bun run ci:staged` or install hooks with `bun run hooks:install`; `pathfinder` is wired into that staged gate, including offline GitHub/GFM URL shape checks.
- Use `bun run pathfinder:gfm` for GitHub-rendered README/link sweeps; use `bun run pathfinder:gfm:online` only when network-backed issue/asset checks are intentionally needed.
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
All follow the same pattern as `uv` — canonical version/runtime manager for their language. No global installs outside of these tools. No `pip install`, no `gem install`, no `npm install -g`. All dependencies are project-local and invoked via the respective tool. This ensures consistent environments, reproducible builds, and clear ownership of runtimes, context and dependencies. No `cmd.exe` or `cmd /c` wrappers — will trigger Windows "open with" dialogs and are not cross-platform. PowerShell 7.6.x (`pwsh`) is the primary shell for interactive use and scripting; `brush` is the sanctioned bash-compatible companion when needed (installed via `cargo install --locked brush-shell`). See [PWSH_RULES.md (repo-root)](PWSH_RULES.md) for usage guidelines.
- Polyglot toolchain surface (reference + cheatsheet + meta-CLI sync): [docs/reference/OXIDIZED_POLYGLOT_SURFACE.md](docs/reference/OXIDIZED_POLYGLOT_SURFACE.md)

Rust core. `src/` = Rust core.

## Some ...`scripts/` = tooling. `mas_mcp/` = Python MCP. `extensions/` = VS Code extension. `docs/` = design docs and standards. `.temple/` = agent protocols and methodology. `.claude/skills/` and `.codex/skills/` = agent skills.

## Triad

Claude (protocol/lore) → Codex (structure/enforcement) → Gemini (velocity/batch, when active).
Anchors: [CLAUDE.md (repo-root)](CLAUDE.md), [AGENTS.md (repo-root)](AGENTS.md), [GEMINI.md (repo-root)](GEMINI.md).
Methodology: [.temple/methodology/TRIAD_METHODOLOGY.md](.temple/methodology/TRIAD_METHODOLOGY.md).

## Triumvirate Version Policy

### Gemini CLI (Bun-managed)

- **Canonical update command:** `chthonic gemini update` — updates both `~/package.json` (home-dir global workspace) and `repo/package.json` (repo workspace), then self-heals `bun audit` in both scopes via `Repair-WorkspaceAudit`.
- **Never:** `bun update @google/gemini-cli` bare — skips audit repair and may strand CVEs.
- **Version spec:** `^0.x.x` (caret) in both `package.json` files — allows minor/patch auto-bump, blocks major.
- **Installed binary:** `node_modules\.bin\gemini.exe` (both scopes).

### Bun Audit Invariant (Dual-Scope)

`bun audit` scopes to the nearest `package.json` from CWD. Two workspaces require independent audit:

| Scope | CWD | `package.json` |
|-------|-----|---------------|
| Home | `C:\Users\eldno` | `~/package.json` — global gemini install |
| Repo | `C:\Users\eldno\chthonic-archive` | repo `package.json` |

- Both MUST be clean simultaneously. Passing one but failing the other is a failure.
- `overrides` do NOT cascade between parent/child workspaces — each carries its own block.
- `Repair-WorkspaceAudit` in `chthonic.ps1` handles both automatically during `chthonic gemini update`.

### Adversarial Lockfile Hardening

After any `bun update` or `bun install`, adversaries can attempt to invalidate the clean state by:
1. Running `bun audit` from `~/` (home scope — catches gemini transitive CVEs not in repo overrides)
2. Modifying nested `package.json` in subfolders to introduce their own lockfile

Defense: the `overrides` block is the only durable fix. `bunfig.toml [audit] ignore` is silently unimplemented in bun ≤1.3.12 — do not rely on it.

### `bunfig.toml` Audit Ignore — NOT IMPLEMENTED

`[audit] ignore = ["GHSA-..."]` is parsed but NOT applied in bun 1.3.12 audit output. Do not add suppress entries expecting them to work.

### MCP Status per Agent

| Agent | MCP Status |
|-------|-----------|
| Claude | Active via VS Code extension MCP config |
| Codex | N/A — OpenAI API |
| Gemini | `GEMINI_DISABLE_MCP=1` set in wrapper — prophylactic disable pending interactive validation |

Re-enable gate: remove `GEMINI_DISABLE_MCP=1` from `scripts/gemini-cli-wrapper.ps1` line 57 only after running an interactive Gemini session confirming all 6 MCP servers (`chthonic-archive-sync` ext) do not crash.

### Skill Parity Contract

Format differences per SDK are correct by design. Coverage should be equivalent across agents:
- Claude skills: `.claude/skills/`
- Codex skills: `.codex/skills/`
- Gemini skills: `.gemini/extensions/chthonic-archive-sync/skills/`

Agent-specific skills (e.g., Gemini `triad-velocity-lane`) are acceptable where the agent has a unique capability. Document deliberate asymmetry in the relevant AGENTS.md or GEMINI.md.
Market context for external skill patterns is tracked in [docs/reference/AGENT_SKILLS_MARKET_SURVEY.md](docs/reference/AGENT_SKILLS_MARKET_SURVEY.md); it is reference material, not a replacement for local skill-creator rules.

### Bun 1.3.12 Notable Features (runtime baseline)

| Feature | Relevance |
|---------|-----------|
| `Bun.WebView` (Chrome backend) | **RSBA gate resolved** — native CDP browser automation on Windows, no Named Pipes |
| `Bun.cron()` | In-process cron scheduler — alternative to `overnight_daemon.ts` external scheduler |
| `using` / `await using` | TC39 Explicit Resource Management — native in JSC; use in new TS code |
| `Bun.Glob.scan()` Windows | Kernel-level `NtQueryDirectoryFile` filtering — 2.4× faster glob patterns |
| `bun upgrade` | Self-upgrade command (no winget required) |
