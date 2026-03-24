---
sid: DOC_OXIDIZED_TOOLCHAIN_REFERENCE
title: Oxidized Toolchain Reference — Rust-Native Language Managers
type: reference
status: canonical
created: 2026-03-11
updated: 2026-03-16 (rationale cross-link + naming canon for rv/rig/zv + local install validation + rig cleanup + zv install + rv-r install)
authors:
  - Claude
audience:
  - all
tags:
  - toolchain
  - rust-native
  - oxidized
  - version-managers
  - polyglot
---

<!--
@SID:    DOC_OXIDIZED_TOOLCHAIN_REFERENCE
@Type:   Reference
@Context: Toolchain / Version Management
-->

# Oxidized Toolchain Reference

> Rust-native ("Oxidized") language/runtime managers for the chthonic-archive polyglot stack.
> Pattern: each replaces a legacy ecosystem tool with a single compiled native binary.
> Primary shell: pwsh 7.5.x. Bash companion: brush (eliminates shell-script OS discrepancies).
> Rationale: [OXIDIZED_TOOLCHAIN_RATIONALE.md](OXIDIZED_TOOLCHAIN_RATIONALE.md)
>
> **Win11 column note:** Any pure-Rust crate compiles to `.exe` via `cargo install`. "No Win11 support" means the maintainer doesn't test on Windows — not that it doesn't work. The compilation probe is the real test. See §OxidizedIndex for the verified-registry approach.

---

## Current Stack (Installed Here)

| Tool | Domain | Replaces | Update Command | Windows 11 |
|------|--------|----------|----------------|------------|
| **uv** | Python versions + packages | pyenv + pip + virtualenv | `uv self update` | ✅ native |
| **rv** | Ruby versions + gems | rbenv + bundler | `rv selfupdate` | ✅ native |
| **goup** | Go versions | manual SDK install | `goup upgrade` | ✅ native (symlink, needs Dev Mode) |
| **bun** | JS/TS runtime + packages | node + npm/nvm | `bun upgrade` | ✅ native |
| **cargo / rustup** | Rust toolchain | — (canonical) | `rustup update` | ✅ native |
| **brush** | Bash-compatible shell | Git Bash / WSL bash | `cargo install --locked brush-shell` | ✅ native (.exe) |
| **zv** | Zig versions | manual Zig SDK installs | reinstall via upstream release / installer | ✅ native |

Validated locally on this workstation:

- `uv 0.10.10`
- `rv 0.5.3`
- `goup 0.16.10`
- `bun 1.3.10`
- `cargo 1.94.0`
- `brush 0.3.0`
- `zv 0.9.2`
- `rv-r -> rv 0.19.0`

Not currently installed on this workstation:

- `rig`

---

## Naming Canon

Use these names consistently in this repo:

- `rv` = Ruby manager
- `rig` = R version manager
- `R rv` / `rv-r` = the A2-ai R package manager when discussed in docs
- `zv` = Rust-native Zig version manager

This avoids the `rv` binary-name collision between the Ruby lane and the separate R package manager.
Repo wrapper: `scripts/rv-r.ps1`

---

## Ecosystem Map — All Rust-Native Managers

### Node.js Version Managers (beyond bun)

bun is a runtime replacement, not a Node version switcher. For projects requiring a specific system Node:

| Tool | What it does | GitHub | Win11 | Status |
|------|-------------|--------|-------|--------|
| **fnm** | Fast Node Manager — switches Node version globally or per-shell | [Schniz/fnm](https://github.com/Schniz/fnm) | ✅ native, pwsh support | Active |
| **Volta** | Pins Node/npm/yarn per-project via `package.json` | [volta-cli/volta](https://github.com/volta-cli/volta) | ✅ MSI installer | Active |

**Recommendation:** fnm for global Node switching; Volta if per-project pinning in `package.json` is needed.

---

### Polyglot Managers (one tool, all languages)

| Tool | Domain | GitHub | Win11 | Notes |
|------|--------|--------|-------|-------|
| **mise** (formerly rtx) | Python, Node, Ruby, Go, Java, PHP, .NET, + 500+ via asdf plugins | [jdx/mise](https://github.com/jdx/mise) | ✅ experimental but functional | Single replacement for uv+rv+goup+fnm. Also manages env vars and task running. Tradeoff: less language-native than single-purpose tools. |
| **proto** (moonrepo) | Bun, Deno, Go, Node, Python, Rust, + WASM plugins | [moonrepo/proto](https://github.com/moonrepo/proto) | ✅ first-class | Cleaner plugin architecture than mise (WASM vs shell scripts). Ships `proto mcp` — MCP server so AI agents can query/manage toolchains directly. Newer, less plugin-rich. |
| **pkgx** | Polyglot runtime execution and package bootstrap | [pkgxdev/pkgx](https://github.com/pkgxdev/pkgx) | Unconfirmed locally | Executes tools on demand with minimal permanent system mutation. Strong fit for ephemeral multi-language workflows. |
| **vfox** | Cross-language version manager | [version-fox/vfox](https://github.com/version-fox/vfox) | Unconfirmed locally | Polyglot manager in the same problem space as mise/proto, with plugin-driven language support. |
| **vmr** | Polyglot version manager | research-candidate | Unconfirmed locally | Mentioned in the larger Rustification research set; not yet validated in this repo. |

**Horse-Market note:** mise and proto are the currently grounded references here. `pkgx`, `vfox`, and `vmr` belong to the same architectural class, but they are not yet the repo’s primary canonical picks.

---

### Shells (Rust-native)

| Tool | What it is | GitHub | Win11 | vs. brush |
|------|-----------|--------|-------|-----------|
| **brush** *(installed)* | Full bash/POSIX reimplementation in Rust | [reubeno/brush](https://github.com/reubeno/brush) | ✅ experimental | Bash-compatible — runs `.bashrc`, aliases, bash scripts unchanged |
| **Nushell** | Structured data shell — every output is a typed table | [nushell/nushell](https://github.com/nushell/nushell) | ✅ native | NOT POSIX-compatible. Different philosophy. Complementary to brush, not competing. |
| **Fish** | UX-focused shell with autocomplete | [fish-shell/fish-shell](https://github.com/fish-shell/fish-shell) | Partial (WSL) | Rewritten in Rust 2024–2025. Limited Win11 native support. |

`brush` matters here because it is not just a shell replacement. It is a Rust-native compatibility substrate for Bash/POSIX workflows on Win11, with built-in command coverage, shell-script portability, and a safer implementation profile than legacy C shells.

---

### Extended Language Coverage (Sweep 2 — 2026-03-11)

### R Language

Two distinct Rust tools — different roles:

| Tool | Role | GitHub | Win11 | Status |
|------|------|--------|-------|--------|
| **rig** (r-lib) | R **version** manager — installs/removes/configures R versions | [r-lib/rig](https://github.com/r-lib/rig) | ✅ native (installer, Scoop, WinGet, Chocolatey) | Active, production-ready |
| **R rv** (A2-ai) | R **package** manager — declarative package install (like uv for R) | [A2-ai/rv](https://github.com/A2-ai/rv) | ✅ native (Windows zip installed via repo wrapper) | Active, v0.19.0 |

Note: `spinel-coop/rv` = Ruby version manager. `A2-ai/rv` = R package manager. `r-lib/rig` = R version manager. Three tools, one name collision. In this repo, keep `rv` reserved for Ruby and use `R rv` / `rv-r` when referring to the R package manager in prose. If you need an execution path, use `scripts/rv-r.ps1`.

R-specific architectural note: `R rv` shifts R package management toward an explicit lockfile model via `rproject.toml` and an `.rv` project environment, instead of relying purely on post-facto snapshotting.

### Zig

| Tool | GitHub | Win11 | Notes |
|------|--------|-------|-------|
| **zv** | [weezy20/zv](https://github.com/weezy20/zv) | ✅ (PowerShell installer) | Written in Rust, supports `.zigversion` file, inline `zig +<version>` syntax. v0.9.2 Jan 2026. |

`zigup` (marler8997) = written in Zig. `zvm` (tristanisham) = written in Go. Only `zv` is Rust.

Zig-specific architectural note: `zv` follows the rustup-style proxy model, using `.zigversion` for project-aware version switching and reducing manual PATH gymnastics.

### Node.js (additional — beyond fnm/Volta)

| Tool | GitHub | Win11 | Notes |
|------|--------|-------|-------|
| **snm** | [numToStr/snm](https://github.com/numToStr/snm) | Unconfirmed | Rust-native Node version manager, 109 stars |
| **bum** | [owenizedd/bum](https://github.com/owenizedd/bum) | Unconfirmed | Rust-native Bun version manager (manages bun versions, not Node), 238 stars |

### Godot

| Tool | GitHub | Win11 | Notes |
|------|--------|-------|-------|
| **gdvm** | [adalinesimonian/gdvm](https://github.com/adalinesimonian/gdvm) | Likely (Rust cross-platform) | Godot Engine version manager in Rust, 64 stars |

### Ruby (additional — beyond rv/spinel-coop)

| Tool | GitHub | Win11 | Notes |
|------|--------|-------|-------|
| **frum** | [TaKO8Ki/frum](https://github.com/TaKO8Ki/frum) | Unconfirmed | Rust-native Ruby version manager, 653 stars — predates rv |

### Gaps — Languages with NO Rust-native manager

| Language | Status | Practical path |
|----------|--------|----------------|
| **Lua** | No Rust-native version manager. `lux` (nvim-neorocks) is a Rust Lua *package* manager, not version manager | mise asdf plugin |
| **PHP** | `phpup` ([masan4444/phpup](https://github.com/masan4444/phpup)) exists but Windows WIP, low maintenance | mise asdf plugin |
| **Elixir / Erlang** | No Rust-native manager | mise asdf plugin |
| **Crystal** | No Rust-native manager | mise asdf plugin |
| **Java/JVM / Kotlin** | No Rust-native manager | mise or proto (plugin wraps SDKMAN-style tooling) |
| **.NET** | No Rust-native manager | mise plugin or Microsoft dotnet-install |
| **R (version)** | `rig` (Rust, Win11 native) ✅ — gap is now closed | rig |
| **Zig** | `zv` (Rust, Win11 native) ✅ — gap is now closed | zv |

---

### Rust-Enhanced Infrastructure Beyond Version Managers

The Rustification pattern is broader than version management. These are not all "toolchain managers," but they matter because they show the same architectural migration at adjacent layers of the stack.

Validation note:

- existence and role checked against official project repos or official project docs on 2026-03-16
- the table below is an example set, not an exhaustive canon
- the repo treats these as validated reference examples, not as new mandatory lanes

| Ecosystem / Tool | Role | Notes |
|------------------|------|-------|
| **brush** | Bash/POSIX shell | Rust-native shell/runtime substrate for Win11 Bash-compatible workflows. |
| **mlua** | Lua interop/bindings | Safe Rust bridge to the Lua runtime; useful reference for embeddable scripting lanes. |
| **Wirefilter** | Embedded rules/filter engine | Cloudflare example of Rust as a safe embedded interpreter substrate. |
| **Cobalt** | COBOL compiler | Example of Rust pushing into legacy enterprise compiler/toolchain territory. |
| **Mago** | PHP formatter/linter/static analysis | Example of Rust replacing slow self-hosted tooling in a dynamic-language ecosystem. |
| **Explorer** | Elixir dataframe backend over Polars | Example of Rust acceleration under a high-level host VM. |
| **jlrs** | Julia ↔ Rust bridge | Example of Rust orchestrating scientific compute interop instead of replacing the host language. |
| **Mojo** | Rust-influenced language design | Not written in Rust, but materially influenced by Rust’s ownership/borrowing model. |

Practical reading: the same force that produces `uv`, `rv`, `zv`, and `brush` also produces Rust-native static analyzers, compilers, embedders, and runtime bridges.

---

### Scientific / Conda Ecosystem

| Tool | What it is | GitHub | Win11 |
|------|-----------|--------|-------|
| **pixi** | Project-scoped environment manager over conda-forge (Python, R, C++, 30K+ packages) | [prefix-dev/pixi](https://github.com/prefix-dev/pixi) | ✅ native |

Not a version switcher — it manages per-project environments like a Rust-native conda/mamba. Relevant if ML work requires mixed Python + C++ + R environments.

---

## Boomerang — Conceptual Note

**What it is:** Boomerang Tasks is the colloquial name for **Orchestrator Mode** in Roo Code (VS Code extension, [RooCodeInc/Roo-Code](https://github.com/RooCodeInc/Roo-Code)). It implements a parent/child task delegation pattern:

1. Orchestrator analyzes the task → calls `new_task` tool with mode + explicit context
2. Child subtask runs in **isolated context window** (no implicit context inheritance)
3. Child completes → returns summary back to parent ("boomerangs")
4. Parent resumes with summary, spawns next child if needed

**Relevance to this stack:** Boomerang is Roo Code-specific — it only works inside that VS Code extension. Claude Code CLI and Codex Agent mode are not Roo Code. However, the **pattern** is identical to the Claude → Codex → Gemini triad: orchestrator delegates, collects results, continues. Boomerang is the community reference term for that orchestration pattern.

**Not a tool to install** — just a pattern name worth knowing when reading community discussions about multi-agent AI workflows.

---

## EndOfLife.date API

**Base URL:** `https://endoflife.date/api/`
**Auth:** None required. Rate limit: CDN-level (static JSON, effectively unlimited for light use).
**OpenAPI spec:** https://endoflife.date/docs/api/v1/

### Endpoints

```
GET /api/all.json                    # All tracked product slugs (~380+ products)
GET /api/{product}.json              # All release cycles for a product
GET /api/{product}/{cycle}.json      # Single cycle details
GET /api/v1/products                 # Same as all.json via v1
GET /api/v1/categories               # Product categories
```

### Response shape (per cycle)

```json
{
  "cycle": "3.12",
  "releaseDate": "2023-10-02",
  "eol": "2028-10-02",
  "latest": "3.12.9",
  "latestReleaseDate": "2025-02-04",
  "lts": false,
  "link": "https://www.python.org/downloads/release/python-3129/"
}
```

### Language coverage

| Language | Tracked | Slug |
|----------|---------|------|
| Python | ✅ | `python` |
| Ruby | ✅ | `ruby` |
| PHP | ✅ | `php` |
| Go | ✅ | `go` |
| Node.js | ✅ | `nodejs` |
| Rust | ✅ | `rust` |
| Elixir | ✅ | `elixir` |
| Erlang | ✅ | `erlang` |
| Lua | ✅ | `lua` |
| R | ❌ | not tracked |
| Zig | ❌ | not tracked |
| Crystal | ❌ | not tracked |

**Usable for version currency checks:** Yes. Renovate bot uses it as a datasource. SDK clients exist for JS, Python, Ruby: [oapicf/endoflife.date-api-clients](https://github.com/oapicf/endoflife.date-api-clients).

---

## API / Tracking — Current Landscape

No single API indexes Rust-native toolchain managers specifically. The three programmatic access points:

| Source | API? | Coverage |
|--------|------|----------|
| **GitHub Search API** | ✅ | `q=topic:version-manager+language:rust` — most complete, returns repos with that topic tag |
| **crates.io API** | ✅ partial | `/api/v1/crates?keyword=version-manager` — keyword match, incomplete |
| **lib.rs** | ❌ browse only | No version-manager subcategory exists |
| **awesome-version-managers** | ❌ README only | [bernardoduarte/awesome-version-managers](https://github.com/bernardoduarte/awesome-version-managers) — marks Rust tools with 🦀, but not exhaustive |
| **awesome-rust** | ❌ README only | No version manager section |
| **phmullins/oxidation** | ❌ README only | Rust CLI tools list, no version manager category |
| **endoflife.date** | ✅ | Tracks EOL per language version — pairs well with a version manager index |

---

## Concept: OxidizedIndex — A Tool for This Problem

The gap is real: there is no structured, queryable index of Rust-native toolchain managers organized by language domain, with version currency and Windows support signals. Building one is tractable.

### What it would do

1. **Crawl** — GitHub Search API (`topic:version-manager language:rust`) + crates.io keyword search + awesome-version-managers list → deduplicated candidate set
2. **Classify** — per candidate: language domain, tool type (version manager / package manager / shell / runtime), Windows support (from README/CI matrix), maintenance status (last commit, open issues, release recency)
3. **Enrich** — cross-reference against endoflife.date: for each language domain, fetch the latest stable version and EOL date → flag tools that are managing languages with imminent EOL cycles
4. **Output** — structured JSON/TOML manifest: `{ language, tool, github_url, rust: true, win11: true|false|partial, status, latest_managed_version, eol_date }`
5. **Compare** — for each language, rank alternatives by stars + recency + Windows support

### Minimal viable shape

```
oxidized-index/
├── src/
│   ├── crawl.rs       # GitHub API + crates.io + static lists
│   ├── classify.rs    # README/CI matrix parsing for Windows signal
│   ├── enrich.rs      # endoflife.date cross-reference
│   └── report.rs      # JSON/Markdown/TOML output
├── data/
│   └── known.toml     # Seed list (hand-curated, this doc's contents)
└── output/
    └── index.json     # Generated — queryable manifest
```

### Data sources it would combine

| Source | Via |
|--------|-----|
| GitHub repo metadata | GitHub REST API (no auth for public repos, rate-limited) |
| Crate metadata | crates.io API |
| Curated seed | `data/known.toml` (from this doc) |
| EOL/latest version | endoflife.date API |
| Windows support signal | README parse + GitHub Actions matrix (`windows-latest` runner presence) |

### The Windows-Native Collapse

The "Win11 support" column in the table above is a **Horse-Market signal** — it reflects the maintainer's test environment, not actual compilability. The real situation:

1. Any pure-Rust crate compiles to `.exe` via `cargo install <crate>` or `cargo build --release` on Win11 with the MSVC or GNU toolchain — no additional effort.
2. `brush` (already installed) eliminates shell-script compatibility issues for tools that ship Unix-only install scripts. Run the install script inside `brush` and it works.
3. Therefore: "no Win11 support" for a Rust-native tool means "the maintainer doesn't test on Windows" — not "it doesn't work." The compilation probe is the real test.

This collapses the evaluation criterion from "does it have a Win11 badge" to "does `cargo install <crate>` succeed and does the core workflow function." Far fewer tools are actually blocked than the surface signals suggest.

### Horse-Market Condition in This Space

The toolchain manager ecosystem exhibits the Horse-Market pattern at two levels:

**Level 1 — Discovery:** Stars, download counts, and "Win11 support" badges are surface signals. `frum` (653 stars, Ruby) has been dormant for years. `zv` (33 stars, Zig) is actively maintained. Stars are a discovery-velocity metric, not a quality metric.

**Level 2 — The index itself:** A naive OxidizedIndex that scrapes and re-encodes these surface signals would just move the Horse-Market problem one level up — you'd have a structured index of unreliable signals. The actual ground truth is: does the binary compile, does it read `.tool-versions` / language-specific version files correctly, does it integrate with the project-local version pinning workflow.

**The AD02 (Tinku) fix:** The index needs a *compilation probe* layer, not just a metadata layer. For each candidate tool, the probe would:
- `cargo install <crate>` — does it compile cleanly on Win11?
- Run the tool's `--version` command — does it execute?
- Run the tool's list/install command against a known version — does the core workflow function?

This turns the index from a curated list into a **verified registry** — the difference between a horse market and a veterinary certificate.

### Richer Implementation: OxidizedIndex v2

```
oxidized-index/
├── src/
│   ├── crawl.rs        # GitHub API + crates.io + static seed
│   ├── classify.rs     # Domain, type, maintenance signals
│   ├── probe.rs        # cargo install + smoke test per tool (NEW)
│   ├── enrich.rs       # endoflife.date cross-reference
│   └── report.rs       # JSON/TOML/Markdown output
├── data/
│   ├── known.toml      # Seed list (hand-curated — this doc's contents)
│   └── probes.toml     # Per-tool smoke test commands
├── output/
│   ├── index.json      # Full manifest with probe results
│   └── verified.json   # Subset: tools that passed compilation probe
└── README.md
```

The `probes.toml` per-tool smoke test:
```toml
[[tool]]
crate = "phpup"
domain = "php"
smoke_test = ["phpup", "list"]
version_file = ".php-version"

[[tool]]
crate = "zv"
domain = "zig"
smoke_test = ["zv", "--version"]
version_file = ".zigversion"
```

**Output shape** (per tool in `verified.json`):
```json
{
  "crate": "phpup",
  "domain": "php",
  "compiled": true,
  "smoke_passed": true,
  "version_file": ".php-version",
  "eol_latest": "8.4.4",
  "eol_date": "2028-12-31",
  "stars": 56,
  "last_commit": "2024-11-03",
  "win11_claimed": false,
  "win11_verified": true
}
```

The `win11_verified: true` despite `win11_claimed: false` is the Horse-Market correction — ground truth over surface signal.

### Where it fits in this repo

Claude lane `L` task — spec first, implementation second. Seed data already exists as this document.

**Delegation path when ready:**
- Claude: spec + `data/known.toml` + `data/probes.toml` seed
- Codex: implement `src/` in Rust — crawl + classify + enrich + report; probe layer is a separate phase
- Gemini: periodic sweep runs to refresh `output/index.json` nightly (daemon-compatible)
- Overnight daemon: could consume `output/index.json` as a toolchain currency feed

---

*Authored: 2026-03-11. Sweep 1 + Sweep 2. Sources: official repos, GitHub topics API, lib.rs, crates.io, awesome-version-managers, endoflife.date API docs.*
