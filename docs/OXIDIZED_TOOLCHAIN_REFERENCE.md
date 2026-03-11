---
sid: DOC_OXIDIZED_TOOLCHAIN_REFERENCE
title: Oxidized Toolchain Reference — Rust-Native Language Managers
type: reference
status: canonical
created: 2026-03-11
updated: 2026-03-11 (sweep 2 — R/Lua/PHP/Elixir/Zig/Zed/EOL API)
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
>
> **Win11 column note:** Any pure-Rust crate compiles to `.exe` via `cargo install`. "No Win11 support" means the maintainer doesn't test on Windows — not that it doesn't work. The compilation probe is the real test. See §OxidizedIndex for the verified-registry approach.

---

## Current Stack (Installed)

| Tool | Domain | Replaces | Update Command | Windows 11 |
|------|--------|----------|----------------|------------|
| **uv** | Python versions + packages | pyenv + pip + virtualenv | `uv self update` | ✅ native |
| **rv** | Ruby versions + gems | rbenv + bundler | `rv selfupdate` | ✅ native |
| **goup** | Go versions | manual SDK install | `goup upgrade` | ✅ native (symlink, needs Dev Mode) |
| **bun** | JS/TS runtime + packages | node + npm/nvm | `bun upgrade` | ✅ native |
| **cargo / rustup** | Rust toolchain | — (canonical) | `rustup update` | ✅ native |
| **brush** | Bash-compatible shell | Git Bash / WSL bash | `cargo install --locked brush-shell` | ✅ native (.exe) |

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

**Horse-Market note:** mise and proto are both active and competing. mise has the larger plugin ecosystem; proto has the cleaner architecture and the MCP server integration. Neither is clearly dominant yet.

---

### Shells (Rust-native)

| Tool | What it is | GitHub | Win11 | vs. brush |
|------|-----------|--------|-------|-----------|
| **brush** *(installed)* | Full bash/POSIX reimplementation in Rust | [reubeno/brush](https://github.com/reubeno/brush) | ✅ experimental | Bash-compatible — runs `.bashrc`, aliases, bash scripts unchanged |
| **Nushell** | Structured data shell — every output is a typed table | [nushell/nushell](https://github.com/nushell/nushell) | ✅ native | NOT POSIX-compatible. Different philosophy. Complementary to brush, not competing. |
| **Fish** | UX-focused shell with autocomplete | [fish-shell/fish-shell](https://github.com/fish-shell/fish-shell) | Partial (WSL) | Rewritten in Rust 2024–2025. Limited Win11 native support. |

---

### Extended Language Coverage (Sweep 2 — 2026-03-11)

### R Language

Two distinct Rust tools — different roles:

| Tool | Role | GitHub | Win11 | Status |
|------|------|--------|-------|--------|
| **rig** (r-lib) | R **version** manager — installs/removes/configures R versions | [r-lib/rig](https://github.com/r-lib/rig) | ✅ native (installer, Scoop, WinGet, Chocolatey) | Active, production-ready |
| **rv** (A2-ai) | R **package** manager — declarative package install (like uv for R) | [A2-ai/rv](https://github.com/A2-ai/rv) | Unconfirmed (bash install script) | Active, v0.19.0 Mar 2026 |

Note: `spinel-coop/rv` = Ruby version manager. `A2-ai/rv` = R package manager. `r-lib/rig` = R version manager. Three tools, one name collision.

### Zig

| Tool | GitHub | Win11 | Notes |
|------|--------|-------|-------|
| **zv** | [weezy20/zv](https://github.com/weezy20/zv) | ✅ (PowerShell installer) | Written in Rust, supports `.zigversion` file, inline `zig +<version>` syntax. v0.9.2 Jan 2026. |

`zigup` (marler8997) = written in Zig. `zvm` (tristanisham) = written in Go. Only `zv` is Rust.

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
