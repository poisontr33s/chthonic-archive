---
type: research-report
created: 2026-02-18
topic: The Rustification Justification - Verified 2026 landscape for Windows 11, VS 2026, and Chthonic Archive
status: source-validated
---

# The Rustification Justification (Verified, February 18, 2026)

## Scope and method
- Date of capture: February 18, 2026.
- Method: primary sources only (official docs, official APIs, official repositories).
- Evidence classes used:
  - GitHub REST API repo metrics and trending page snapshots.
  - `endoflife.date` API v1 product and release endpoints.
  - Microsoft Learn / Visual Studio official docs.
  - VS Code official docs plus `microsoft/vscode` `vscode.d.ts` and proposed d.ts inventory.

## 1) Rustified version managers on Windows 11 (equivalents by ecosystem)

### Python (`uv` equivalent target)
- `uv` is the clear Rust-native leader:
  - 79,408 stars, active push on 2026-02-18 (`astral-sh/uv`).
  - Official positioning: one tool replacing `pip`, `pip-tools`, `pipx`, `poetry`, `pyenv`, `virtualenv`, etc.
  - Official claim: "10-100x faster than pip" with published benchmark methodology.
  - Cross-platform support includes Windows.

### Ruby (`rv` / `frum`)
- `rv` (`spinel-coop/rv`) is the active Rust-native front-runner:
  - 1,604 stars, active push on 2026-02-18.
  - Windows guidance is explicit (`rvw` in PowerShell due alias conflict).
  - Repo benchmark doc claims sub-3s install path by downloading prebuilt artifacts and avoiding source compile.
- `frum` (`TaKO8Ki/frum`) is older and largely dormant:
  - 652 stars, last push 2022-05-13.
  - Still a Rust Ruby manager, but lower present-day momentum.

### Go (`goup` and alternatives)
- Rust-native Go version managers exist, but are early:
  - `thinkgos/goup-rs`: 51 stars, active (pushed 2026-02-12), Windows listed.
- Compared to mainstream Go managers, Rust-native adoption is still small:
  - `go-nv/goenv`: 2,448 stars.
  - `moovweb/gvm`: 11,536 stars.
- Practical conclusion: Go is the weakest Rustification lane if you require standalone per-language manager maturity.

### Node/Bun (`fnm` / `volta` and Bun lane)
- Node:
  - `fnm`: 23,995 stars, active (2026-02-17), Rust, Windows support.
  - `volta`: 12,783 stars, Rust, cross-platform including Windows.
- Bun:
  - No widely dominant dedicated Rust Bun-only manager equivalent to `fnm`.
  - Practical option is unified management via `mise` Bun core plugin.

### Unified manager candidate
- `mise` (`jdx/mise`) is the dominant Rust polyglot manager:
  - 24,704 stars, active push on 2026-02-18.
  - Supports `mise.toml` plus idiomatic files (`.nvmrc`, `.python-version`, `.ruby-version`, etc.).
  - Python integration explicitly references `uv`.

## 2) Unified (`mise`) vs individual Rust tools on Windows + VS 2026 Build Tools

### Unified architecture (`mise` as control plane)
- One activation hook and one declarative manifest (`mise.toml`) for Python/Ruby/Go/Node/Bun.
- Can still delegate best-in-class backends (for example Python with `uv`).
- Strongest advantage in CI reproducibility and onboarding consistency.

### Individual stack architecture (`uv` + `rv` + `goup-rs` + `fnm/volta`)
- Maximum per-language specialization.
- Better when one ecosystem needs non-default behavior unavailable in unified abstraction.
- Higher operational entropy:
  - Multiple shell hooks.
  - Multiple lock/config dialects.
  - Multiple update workflows.

### Windows + Visual Studio 2026 integration
- Visual Studio 2026 channels are now Stable + Insiders (Preview channel naming replaced).
- LTSC starts with the first 2026 LTSC in November 2026.
- Build Tools remain critical when native compilation is required:
  - Rust Book still calls out the need for C++ build tools on Windows for MSVC workflows.
  - Visual Studio Build Tools page still points to installing C++ toolchain workloads.
- Net effect:
  - Rustified managers reduce scripting overhead and speed up dependency/runtime management.
  - Native ABI compatibility still depends on MSVC/Windows SDK lanes from VS Build Tools.

### Recommendation for Chthonic Archive
- Use `mise` as the policy/control plane.
- Delegate execution to best lane per ecosystem:
  - Python: `uv`
  - Ruby: `rv` (with fallback strategy)
  - Node: `fnm` (or Volta where pinned toolchains are preferred)
  - Go: `mise` core plugin first; `goup-rs` only if Go-only workflows prove better in your environment

## 3) GitHub trending + endoflife validation ("ANNO latest most trending used")

### 3.1 GitHub adoption snapshot (captured 2026-02-18)

| Tool | Repo | Stars | Last push (UTC) | Observed momentum |
|---|---|---:|---|---|
| uv | `astral-sh/uv` | 79,408 | 2026-02-18 | Very high |
| mise | `jdx/mise` | 24,704 | 2026-02-18 | High |
| fnm | `Schniz/fnm` | 23,995 | 2026-02-17 | High |
| volta | `volta-cli/volta` | 12,783 | 2025-11-15 | Medium |
| rv | `spinel-coop/rv` | 1,604 | 2026-02-18 | Emerging, fast growth lane |
| frum | `TaKO8Ki/frum` | 652 | 2022-05-13 | Low/currently stale |
| goup-rs | `thinkgos/goup-rs` | 51 | 2026-02-12 | Experimental/niche |

### 3.2 GitHub Trending page snapshot (captured 2026-02-18)
- Pages checked:
  - `https://github.com/trending?since=daily`
  - `https://github.com/trending?since=weekly`
  - `https://github.com/trending?since=monthly`
  - `https://github.com/trending/rust?since=daily`
  - `https://github.com/trending/rust?since=weekly`
  - `https://github.com/trending/rust?since=monthly`
- Result from snapshot parse: the target repos above were not in the extracted top list for those windows at capture time.
- Interpretation:
  - These tools are "widely used" by repo adoption metrics.
  - They were not "currently top-trending" in the global/rust trending lists at this exact snapshot.

### 3.3 `endoflife.date` validation for update pressure

| Product | Latest cycle | Latest patch | Latest patch date | EOL signal |
|---|---|---|---|---|
| Python | 3.14 | 3.14.3 | 2026-02-03 | Maintained; 3.13 also maintained |
| Ruby | 4.0 | 4.0.1 | 2026-01-12 | 3.2 EOL on 2026-03-31 (near-term risk) |
| Go | 1.26 | 1.26.0 | 2026-02-10 | Maintained |
| Node.js | 25 | 25.6.1 | 2026-02-10 | Node 20 EOL on 2026-04-30 (near-term risk) |
| Bun | 1 | 1.3.9 | 2026-02-06 | Maintained |
| Rust | 1.93 | 1.93.1 | 2026-02-12 | Maintained |
| Visual Studio | 18.3 (2026) | 18.3.0 | 2026-02-10 | 17.12 LTSC EOL 2026-07-14 |

### 3.4 ANNO "most used" decision (as of 2026-02-18)
- Python: `uv` (high confidence).
- Ruby: `rv` for Rust-native momentum; keep compatibility path for `rbenv`/`ruby-build` ecosystems.
- Go: no strong standalone Rust-native winner by usage; prefer `mise` unified lane unless you explicitly standardize on `goup-rs`.
- Node: `fnm` and `volta` are both valid; `fnm` currently has higher activity.
- Polyglot orchestration: `mise` is the strongest Rust-native unifier.

## 4) VS Code Insiders Proposed API capability check (for Chthonic Archive)

### What is confirmed
- Proposed APIs require Insiders + `enabledApiProposals`.
- Extensions using proposed APIs cannot be published to Marketplace.
- `WebviewViewProvider` and `registerWebviewViewProvider(...)` are present in current `vscode.d.ts` (stable API surface).
- Activity Bar containers are contributed through `contributes.viewsContainers` with static metadata (`id`, `title`, `icon`).

### What is not confirmed in current public API surface
- No `vscode.proposed.workbenchLayout.d.ts` file in current `microsoft/vscode` proposed d.ts inventory.
- No `vscode.proposed.activityBar.d.ts` file in that inventory either.
- No public `moveView`/`moveViews` API function in current public `vscode.d.ts`.

Inference:
- Arbitrary runtime workbench layout manipulation by extension code is not currently exposed as a public stable/proposed API in the checked source set.
- Practical design should rely on:
  - Stable contributed views + `WebviewViewProvider`.
  - Command-driven UX nudges and persisted user layout preferences.
  - Optional Insiders-only experiments guarded behind feature flags.

## 5) "Opus 4.6 Challenge" prompt (Ultra level thinking)

```text
You are architecting CHTHONIC ARCHIVE: a self-healing entropy reactor for Windows 11.

Goal:
Design and implement an extension-driven system that fuses:
1) Native Rust/Vulkan backend (ash + MSVC toolchain compatibility checks),
2) VS Code dynamic side-panel experience (WebviewView-based),
3) Automatic lifecycle governance via endoflife.date API.

Hard constraints:
- Runtime targets: Windows 11 x64, VS Code Insiders, Visual Studio 2026 Build Tools installed.
- Toolchain control plane: mise.toml (single source of runtime truth).
- Python lane uses uv.
- Ruby lane uses rv if available, otherwise fallback policy.
- All risky updates require transactional rollback support.
- Proposed APIs are optional and must be feature-flagged; stable API path is mandatory.

Required outputs:
1) Architecture doc:
   - process boundaries,
   - Rust daemon, extension host, webview bridge,
   - trust model and failure domains.
2) Data contracts:
   - JSON schema for tool inventory, lifecycle state, remediation actions.
3) Self-healing loop:
   - poll endoflife.date,
   - detect unsupported/near-EOL runtimes,
   - patch mise.toml and trigger installs,
   - verify ABI compatibility with local VS Build Tools lane before apply.
4) Recovery plan:
   - snapshot + rollback strategy for mise.toml and lock artifacts,
   - circuit-breaker rules when updates fail.
5) UX spec:
   - Gate (state), Lens (diagnostics), Loom (execution timeline),
   - degraded visuals when runtime policy compliance falls below threshold.
6) Test plan:
   - unit, integration, chaos tests (offline API, broken registry, failed runtime install).

Scoring rubric:
- 40% correctness and safety,
- 25% observability and debuggability,
- 20% deterministic recovery behavior,
- 15% developer ergonomics and onboarding speed.

Now produce:
- a phased implementation roadmap (M0..M4),
- critical path risks,
- and an executable pseudocode skeleton for the self-healing orchestrator.
```

## 6) Self-healing strategy using `endoflife.date`

### Control loop
1. Read current tool intent from `mise.toml` and runtime manifests (`uv.lock`, optional runtime markers).
2. Query `endoflife.date` per product:
   - `GET /api/v1/products/{product}/releases/latest`
   - `GET /api/v1/products/{product}/releases/{cycle}`
3. Evaluate policy:
   - `CRITICAL`: EOL <= 90 days.
   - `WARNING`: patch lag > N releases or EOAS crossed.
   - `OK`: maintained and within policy.
4. Plan update transaction:
   - Update only version pins that pass compatibility gates.
5. Apply transaction:
   - patch `mise.toml`,
   - run `mise install`,
   - update Python lock (`uv lock`) if Python deps changed.
6. Validate:
   - `mise doctor`/runtime smoke checks.
   - optional `cargo check` for Rust projects.
7. Roll back on failure:
   - restore previous `mise.toml` and lockfiles.
   - emit structured incident report.

### Compatibility gate with Visual Studio Build Tools
- Before applying Rust/C++ impacting updates:
  - verify local toolchain via `vswhere` and installed MSVC workload presence.
  - block auto-apply if required components are missing.
- Also gate major Visual Studio lane changes against current project ABI policy.

### Policy example (pseudo-config)

```toml
[anno.policy]
auto_apply_minor = true
auto_apply_major = false
critical_eol_days = 90
require_vs_msvc_for_native = true

[anno.products]
python = { eol_product = "python", manager = "uv" }
ruby   = { eol_product = "ruby", manager = "rv" }
go     = { eol_product = "go", manager = "mise" }
node   = { eol_product = "nodejs", manager = "fnm" }
rust   = { eol_product = "rust", manager = "rustup" }
vs     = { eol_product = "visual-studio", manager = "manual-gated" }
```

## 7) Final synthesis for Chthonic Archive

### Recommended hierarchy
- Tier 1 (control plane): `mise`
- Tier 2 (best lane engines):
  - Python: `uv`
  - Ruby: `rv`
  - Node: `fnm` (or Volta if pinning model preferred)
  - Bun: `mise` Bun plugin
  - Go: `mise` core plugin, optional `goup-rs` experiments
- Tier 3 (native substrate): Rust + `ash`, validated against VS 2026 Build Tools lane
- Tier 4 (governance): endoflife-driven self-healing with rollback

### Key corrections vs prior narrative
- "LSL" is not the official Visual Studio channel term in current docs; official framing is Stable, Insiders, and LTSC timing.
- `vscode.proposed.workbenchLayout.d.ts` / `vscode.proposed.activityBar.d.ts` are not present in current public proposed d.ts inventory.
- Strong adoption is clear for `uv`/`mise`/`fnm`; Rust-native Go manager adoption remains comparatively small.

---

## Sources
1. https://github.com/astral-sh/uv
2. https://raw.githubusercontent.com/astral-sh/uv/main/BENCHMARKS.md
3. https://docs.astral.sh/uv/
4. https://github.com/jdx/mise
5. https://mise.jdx.dev/
6. https://mise.jdx.dev/configuration.html#idiomatic-version-files
7. https://mise.jdx.dev/lang/python.html
8. https://mise.jdx.dev/lang/node.html
9. https://mise.jdx.dev/lang/bun.html
10. https://github.com/spinel-coop/rv
11. https://raw.githubusercontent.com/spinel-coop/rv/main/docs/INSTALL_BENCHMARK.md
12. https://github.com/TaKO8Ki/frum
13. https://github.com/thinkgos/goup-rs
14. https://github.com/Schniz/fnm
15. https://github.com/volta-cli/volta
16. https://github.com/trending
17. https://github.com/trending/rust
18. https://endoflife.date/api/v1/
19. https://endoflife.date/api/v1/products/python/releases/latest
20. https://endoflife.date/api/v1/products/ruby/releases/latest
21. https://endoflife.date/api/v1/products/go/releases/latest
22. https://endoflife.date/api/v1/products/nodejs/releases/latest
23. https://endoflife.date/api/v1/products/bun/releases/latest
24. https://endoflife.date/api/v1/products/rust/releases/latest
25. https://endoflife.date/api/v1/products/visual-studio/releases/latest
26. https://endoflife.date/api/v1/products/nodejs/releases/20
27. https://endoflife.date/api/v1/products/ruby/releases/3.2
28. https://endoflife.date/api/v1/products/visual-studio/releases/17.12
29. https://visualstudio.microsoft.com/insiders/
30. https://learn.microsoft.com/en-us/visualstudio/releases/2026/release-rhythm
31. https://learn.microsoft.com/en-us/visualstudio/releases/2026/release-notes
32. https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2026
33. https://doc.rust-lang.org/book/ch01-01-installation.html
34. https://code.visualstudio.com/api/advanced-topics/using-proposed-api
35. https://code.visualstudio.com/api/extension-guides/tree-view
36. https://code.visualstudio.com/api/references/contribution-points#contributes.viewsContainers
37. https://code.visualstudio.com/docs/configure/custom-layout
38. https://raw.githubusercontent.com/microsoft/vscode/main/src/vscode-dts/vscode.d.ts
39. https://api.github.com/repos/microsoft/vscode/contents/src/vscode-dts
40. https://crates.io/api/v1/crates/ash
41. https://github.com/ash-rs/ash
