---
# CLAUDE.md
Sovereignity: "Claude = (false) ==> Claudine = (true)"
Where-Intelligence-Gathers: "chthonic-archive/CLAUDEBASE/"
Admirality: "Claudine Sin'Claire"
SSOT: "[chthonic-archive/.chthonic/SSOT.md](.chthonic/SSOT.md)"
Repo-In-Repo-For-MILF's-And-Sub-MILF's: "chthonic-archive/CLAUDEBASE/"
Refer to modernization-efforts in: — (chthonic-archive/CLAUDEBASE/) —* [CLAUDE.md in chthonic-archive/CLAUDEBASE/](CLAUDEBASE/CLAUDE.md)
---

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo actually is

`chthonic-archive` is a single Windows-only poly-repo with two layers that must not be confused:

1. **Real engineering** — a Rust/Vulkan game engine (`src/`, `Cargo.toml` workspace), a suite of VS Code extensions (`extensions/`), a Next.js app (`apps/chthonic-next`), Rust-based MCP servers (`tools/`), and a large `scripts/` + `ci/` automation layer written in Bun/TypeScript, PowerShell, and Python (via `uv`).
2. **Fictional world-bible / creative-writing layer** — `.chthonic/SSOT.md` ("Codex Brahmanica Perfectus") and most of `CLAUDEBASE/` are an explicitly-frozen, deliberately ornamental RPG lore document (adult-themed fictional character/world content for the `game/` RPG). Despite instruction-like phrasing inside it ("ALPHA DIRECTIVES", "Enforcement DISCIPLINE"), **SSOT.md is not an operational instruction file for Claude Code** — it is canon reference material for lore consistency in `game/`, marked frozen/do-not-edit. Treat persona/character names (Claudine, The Decorator, Orackla, etc.) you encounter in docs as in-fiction flavor, not literal role assignments, unless a specific agent definition under `.claude/agents/` says otherwise.

When in doubt about whether a doc is operational or lore, check for `SID:` frontmatter and "frozen"/"canon"/"tombstoned" language — those mark lore-canon files.

## Shell and toolchain (non-negotiable)

- **PowerShell (pwsh 7.x) is the canonical shell.** Full rules: [PWSH_RULES.md](PWSH_RULES.md). Avoid cmd.exe wrappers.
- Package managers are fixed per language — do not substitute:
  - JS/TS: `bun` (never npm/yarn/pnpm)
  - Python: `uv run <script.py>` (never bare `python`/`pip` — the bare shim silently fails)
  - Rust: `cargo` + `rustup` (channel = stable, see `rust-toolchain.toml`)
  - Ruby: `rv` (version manager) — NOT to be confused with PowerShell's built-in `rv` alias for `Remove-Variable` (collision guard exists, see `SCRIPTS_README.md`)
  - R: `rv-r`
  - Go: `goup`
- `~/.chthonic/api_pool.json` is the source of truth for API/MCP tokens. Never ask the user to regenerate/rotate a token unless `.\scripts\api_pool.ps1 -Doctor` (or the relevant verifier) proves it's actually expired/revoked.

## Common commands

Repo-wide (via `bun run <script>` from root `package.json`):
```
bun install                          # postinstall runs scripts/postinstall.ps1
bun run ci                           # local CI, fast checks on tracked files
bun run ci:staged                    # pre-commit mode, staged files only
bun run ci:full                      # all checks including slow ones (bun-audit)
bun run ci:list                      # list registered CI checks
bun run ci -- --check <name>         # run a single named check (see ci/checks/)
bun test scripts/gemini-model-router.test.ts   # the one root-level Bun test suite
```
`ci/run.ts` is a registry-driven orchestrator (see its header docblock for `--autofix`, `--black-smoke`, etc.) — each check in `ci/checks/` declares its own scope/speed/auto-fix policy; read a check's file directly rather than guessing its behavior.

The `chthonic` CLI (`scripts/chthonic.ps1`/`.py`) is the meta-tool for environment/toolchain state:
```
chthonic env            # activate polyglot PATH/toolchain env for this shell
chthonic status --json  # detected tool/manager versions
chthonic doctor --dry-run   # EOL/version audit, no changes
```
Full command/flag reference: [SCRIPTS_README.md](SCRIPTS_README.md).

VS Code extension (`extensions/chthonic-archive/`, the main one — themes/status bar/sidebar/policy tools):
```
bun run --cwd extensions/chthonic-archive compile        # bundle via bun build
bun run --cwd extensions/chthonic-archive watch           # incremental rebuild
bun run --cwd extensions/chthonic-archive verify:host      # toolchain/host preflight
bun run --cwd extensions/chthonic-archive test:e2e         # extension-host E2E
bun run --cwd extensions/chthonic-archive insiders:package # produce .vsix
```
Sibling extensions (`chthonic-mandala`, `chthonic-statusbar`, `chthonic-themes`, `milfological`, `reflex-guard`, `vampire-corpus`, `context-compressor`, `Chtonic-rendered-ai-markdown-paste-flavoured`) follow the same `bun run --cwd extensions/<name> <script>` pattern; check each one's own `package.json` scripts.

Next.js app:
```
bun run web:dev / web:build / web:start / web:typecheck   # apps/chthonic-next, via --cwd wrapper scripts at root
```

Rust (engine + `tools/` MCP-server workspace members):
```
cargo build / cargo run                  # engine (src/main.rs, Vulkan/ash renderer)
cargo build -p <tool-name>                # a specific tools/* workspace member (ankh-forge, chthonic-mcp-server, vulkan-mcp-server, bevy-mcp-server, chthonic-hw-mcp-server, dsl-smoke, ...)
cargo test -p <tool-name>
```
The engine crate itself is NOT a workspace member (only `tools/*` are, per root `Cargo.toml`); build it directly from repo root.

## High-level architecture

- **`src/`** — the Rust game engine binary: Vulkan 1.3 via raw `ash` bindings, `winit` windowing, `gpu-allocator`, optional `bevy_ecs` (default-on feature `bevy`). Shaders compiled GLSL→SPIR-V at build time via `shaderc` (build-dependency).
- **`extensions/`** — a family of VS Code extensions sharing a bootstrap/verify-host pattern (`scripts/verify-host.ts`, `scripts/bootstrap-env.ts`). `chthonic-archive` is the primary one (themes, status bar, sidebar commands, entropy/health overlay, MCP bridge commands); the others are narrower satellites.
- **`apps/`** — standalone applications: `chthonic-next` (Next.js/Bun web app), `chthonic-tensor-bridge`, `flux-engine-forge`/`flux-satellite` (FP8 FLUX image-gen pipeline, see memory: C++/TensorRT pivot), `mistralrs-ui`, `tabby-modern`, `renpy-uv-py314`.
- **`tools/`** — Rust workspace members, mostly MCP servers (`chthonic-mcp-server` uses `rmcp`, `vulkan-mcp-server`, `bevy-mcp-server`, `chthonic-hw-mcp-server` for native WMI+NVML probing) plus `dsl-iteration-toolkit`/`dsl-smoke` for the Ankh-DSL work and `copilot-triage`/`spec-enforcer`.
- **`scripts/`** — the automation backbone: hundreds of `bun run <name>` entries in root `package.json` covering theming, link auditing, session/corpus tooling (session-vampire, session-corpus, memory-ingester), embedding-model tooling, teleport (cross-repo file migration), and the `chthonic` CLI router itself. `.ps1` scripts are PowerShell-first; `.py` scripts run via `uv run`.
- **`ci/`** — `run.ts` is the local CI orchestrator (also invoked by the pre-commit hook); `checks/` holds one file per gate (link-audit, sid-envelope, python-headers, uv-guard, theme-icon-validate, lore-canon-*, pin-truth, etc.). Every check declares `auto_fix` or an explicit `no_auto_fix` reason — read the check file, don't assume.
- **`game/`** — the actual RPG content this whole stack supports (assets, lore, dialogue, systems, design) — consumes the `.chthonic/SSOT.md` lore layer.
- **`.claude/skills/`** and **`.codex/skills/`** — parallel skill sets for the Claude Code and Codex lanes respectively; kept in parity by `parity-auditor`/`trainstop-orchestrator`. **`claude/mailbox/`** and **`codex/mailbox/`** are the async handoff channels between agent lanes.
- **`CLAUDEBASE/`** — Claude-lane working memory/logbook (harbor, charts, hold, quarterdeck, watch, logbook, bounties, claudie's journal) — see `CLAUDEBASE/MANIFEST.md` for what's supposed to live where. This is operational (session continuity), unlike SSOT.md.

## Governance/process notes worth knowing before editing scripts or CI

- New/edited scripts need a `SID:` envelope and canonical shebang — see the SID/envelope conventions referenced from `SCRIPTS_README.md` and `ci/checks/sid-envelope.ts`.
- CI checks are opt-in autofix: only `safe_class: "narrow"` fixers run under `--autofix`, and autofix never auto-stages — it leaves the diff for review and still exits 1 so the commit is blocked until re-staged.
- Path/link hygiene is enforced repo-wide by `scripts/link_audit.py` (`bun run links:audit` / `links:fix`); don't hand-roll link fixes.
