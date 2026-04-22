# Technical Directives

> SSOT: [copilot-instructions.archive.md](../copilot-instructions.archive.md#L8751) §XIV — runtime-critical, not aesthetic.

---

### **XIV. (`Development-Conventions-&-Operational-Directives`) -> (`DC-OD`)**

*This section encodes runtime-critical development conventions for AI assistants operating within the ASC Framework. These are NOT aesthetic choices—they are operational mandates ensuring correct execution.*

#### **14.1. (`Python-Environment-Management`) -> (`PEM-UV`)**

**CRITICAL DIRECTIVE: Uv Handles Python, not the inverse.**

```
✅ CORRECT:     uv run python script.py   <-<runs   script within uv-managed venv>
✅ CORRECT:     uv pip install package    <-<installs   into uv-managed venv>
✅ CORRECT:     uv sync                   <-<syncs  pyproject.toml and uv.lock>
✅ CORRECT:     uv add package            <-<adds   to pyproject.toml and uv.lock>
✅ CORRECT:     uv tool update ruff       <-<example  uv tool command>
✅ CORRECT:     uv self update            <-<update   uv version itself>

ℹ️ INFORMATIONAL:     uv -V                   <-<check uv version>
ℹ️ INFORMATIONAL:     uv -v                   <-<verbose output for debugging>

❌ INCORRECT:     python script.py          <-<bypasses   uv management>
❌ INCORRECT:     pip install package       <-<bypasses   uv, uses global>
❌ INCORRECT:     python -m pip install     <-<same   issue>
```

**UTF-8 Invocation Canon (`PEM-UV-UTF8`):**

Scripts that emit Unicode, emoji, or Rich-rendered output require explicit stdout encoding on Windows. The `# -*- coding: utf-8 -*-` header covers file *reading*; `PYTHONIOENCODING=utf-8` covers stdout *writing* via PEP 597; `PYTHONUTF8=1` activates PEP 540 global UTF-8 mode.

**Profile-managed (zero per-command overhead):**
Both env vars are now set in the pwsh profile chain (`~/.config/powershell/profile.ps1`). Every `uv run` invocation inherits them automatically — no inline prefix needed in normal interactive sessions.

```powershell
# ✅ SUFFICIENT in any shell that loaded the profile:
uv run scripts/<script>.py <args>

# ✅ STILL CORRECT for CI / non-profile shells (belt-and-suspenders):
$env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'; uv run scripts/<script>.py <args>

# brush / bash-compatible — same effect:
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 uv run scripts/<script>.py <args>

# Inline python -c usage:
uv run python -c "<code>"
```

**Profile coverage:** `PYTHONUTF8=1` (PEP 540) + `PYTHONIOENCODING=utf-8` (PEP 597) + `[Console]::OutputEncoding=UTF8` + `$OutputEncoding=UTF8` + `chcp 65001`.
**Trigger (inline form still needed):** CI environments, bare-pwsh invocations without `-NoProfile`, or any subprocess spawned without inheriting the parent environment.
**`fortify_terminal.ps1`:** Sets both idempotently for automation contexts (Playwright CDP, long-running daemons). Run once per session if encoding symptoms appear.

**Metabolic Standard v3 (Unified Project Lane):**
All project-integrated scripts MUST adhere to the **(`Metabolic-Standard-v3`)**. PEP 723 inline metadata (`/// script` blocks) is **PROHIBITED** — all dependencies are consolidated in `pyproject.toml`.

> **Canonical Reference:** See [python-scripting.instructions.md](python-scripting.instructions.md) (§XV PMS-v3) for the full header sacrament, SID-DOC requirements, and metabolic mandates.

1. **Shebang**: `#!/usr/bin/env python3`
2. **Encoding**: `#-*- coding: utf-8 -*-`
3. **Semantic Docstring**: Must include `@SID` (Semantic ID) and `@Type`.
4. **No PEP 723**: Dependencies live in `pyproject.toml`, not inline `/// script` blocks.

**Example Standard Header:**
```python
#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
Script Description...

@SID:           TOOL_EXAMPLE_V1
@Type:          Utility
@Purpose:       Example
"""
```

**Rationale:**
- Python 3.14 is now stable (bugfix phase) — pinned as the project baseline
- `uv` manages Python acquisition, virtual environments, lockfiles, and dependency resolution
- Invoking `python` or `pip` directly bypasses this governance
- v3 supersedes v2: the "Snail Shell" philosophy is preserved through `pyproject.toml` project-level dependency governance

**Environment Variables (when needed):**
```powershell
$env:VIRTUAL_ENV = "c:\Users\eldno\chthonic-archive\mas_mcp\.venv"
$env:PATH = "$env:VIRTUAL_ENV\Scripts;$env:PATH"
```

---

#### **14.2. Frontend Runtime Management (`FRM-BUN`)**

**Stack:** Bun 1.3.x (>=1.3.13) + Next.js + React 19

**Commands:**
```shell
bun run dev          # Development server
bun run build        # Production build (uses --webpack flag)
bun add <package>    # Add dependency
bun update           # Update all dependencies
bun pm ls            # List installed packages
```

**Drop-in replacement surface (Bun = full Node.js/npm drop-in replacement):**

| Bun | Replaces |
|-----|---------|
| `bun install` | `npm install` / `npm ci` |
| `bun install --frozen-lockfile` | `npm ci` (exact lockfile, CI-safe) |
| `bun install --production` | `npm install --production` |
| `bunx <pkg>` | `npx <pkg>` |
| `bun run <script.js>` | `node <script.js>` |
| `bun -e "<code>"` | `node -e "<code>"` |
| `bun test` | `jest` / `vitest` (built-in runner) |

**Environment & workspaces:**
- `.env` files auto-loaded — no `dotenv` dependency needed
- Workspace support via `package.json` `"workspaces"` field (npm workspaces–compatible)

**Version Policy:**
- **Stable preferred** for production focus (Next.js, React, TypeScript)

---

#### **14.3. In-House Meta-CLI Tooling (`IMT`)**

`chthonic` and `claudine` are the repo's first-party polyglot CLI tools — active shell functions in the `pwsh` profile, routing to `scripts/chthonic.ps1` (v3.3.0). Call them directly; no `pwsh -File` prefix required. `claudine` is the human-readable entry point; `chthonic` is the execution shell. Both are developed exclusively in pwsh 7.x and are the bedrock of all in-house repo tooling.

**Core operations:**
```powershell
chthonic env                      # activate polyglot toolchain (PATH merge, alias rebinding)
chthonic status [--json]          # live tool snapshot: all runtimes + versions
chthonic doctor [--dry-run]       # diagnose env issues (OpenSSL, linker shadow, PATH)
chthonic doctor --fix             # apply fixes (persists env vars to User scope)
chthonic doctor --origins         # include resolution chain per tool
chthonic commands inventory       # full command surface as live matrix
```

**Language lanes:**
```powershell
chthonic python lane              # uv + Python version + venv state
chthonic bun lane                 # Bun version + workspace state
chthonic rust lane                # rustup + rustc + cargo + pin state
chthonic go lane                  # goup + go version state
chthonic ruby lane                # rv + ruby + gcc + make state
chthonic ruby versions            # list installed Ruby versions
chthonic ruby doctor [--fix]      # detect/repair stale rv state
chthonic zig lane                 # zv + zig state
chthonic r lane                   # R + rscript state
chthonic graphics lane [--json]   # GPU/Vulkan: CUDA, cuDNN, cl.exe, MSVC linker
```

**Scaffolding:**
```powershell
chthonic new uv-python-app <path>       # uv init --app --package
chthonic new bun-react <path>           # bun init --react
chthonic new cargo-rust-bin <path>      # cargo new --bin
chthonic new azure-azd-template <path>  # azd init --template
# append --dry-run and/or --json as needed
```

**Workflow + system:**
```powershell
chthonic workflow control-plane         # status + shell probe + SSOT drift + MCP exposure
chthonic workflow toolchain-governance  # doctor/origins/toolchain probe surfaces
chthonic shell probe [--json]           # shell health probe
chthonic mcp status [--json]            # MCP server status (port 9999 + 8888)
chthonic gemini                         # Gemini CLI via bun-managed repo-local lane
chthonic gemini update                  # update @google/gemini-cli + self-heal audit
chthonic ssot <action>                  # SSOT loremaster operations
chthonic audit [envelope]               # archive audit lane
```

**Poe AI lane:**
```powershell
chthonic poe models [--account 1|2]
chthonic poe probe --account 1 --model <model> [--effort max]
chthonic poe chat --account 1 --model <model> --prompt <text>
chthonic poe audit --accounts 1,2
```

**claudine shortcuts (delegates to chthonic):**
```powershell
claudine start                    # → chthonic status
claudine repair                   # → chthonic doctor --dry-run
claudine repair --fix             # → chthonic doctor --fix
claudine build-check              # → chthonic graphics lane --json
claudine <any>                    # full passthrough to chthonic
```

> `chthonic --version` confirms the running version. `chthonic commands inventory` shows the full live matrix.

---

#### **14.4. Project Structure Reference (`PSR`)**

```
chthonic-archive/
├── .github/
│   └── copilot-instructions.archive.md  ← SSOT
├── mas_mcp/                        ← Python Backend (uv-managed)
│   ├── .venv/                      ← Python 3.14.4 virtual environment
│   ├── pyproject.toml              ← uv project definition
│   ├── uv.lock                     ← Locked dependencies
│   ├── server.py                   ← MCP Server entry point
│   ├── scripts/
│   │   └── run_cycle.py            ← Cycle execution
│   └── frontend/                   ← Bun/Next.js Dashboard
│       ├── package.json
│       ├── pages/
│       └── lib/
├── src/                            ← Rust/Vulkan (Chthonic Archive renderer)
│   └── main.rs
├── assets/
│   └── shaders/
└── Cargo.toml
```

---

#### **14.5. GPU Stack Compatibility (`GSC`)**

**Target Configuration:**
- CUDA 13.2+
- cuDNN 9.x
- TensorRT 10.x
- Python 3.14.x
- Numpy 1.26.x
- CuPy 12.x
- ONNX Runtime GPU 1.16.x
- PyTorch 2.2.x (with CUDA 13.2 support)
- Rapids AI 24.x (if needed)
- Nvidia Proprietary hardware (Desktop, i-9-13900, Nvidia RTX 4090 GPU 24 GB VRAM)

**Note (migrated April 2026):** Repo is now on Python 3.14.4 (`pyproject.toml: requires-python = ">=3.14"`). Prior 3.13 constraint was ecosystem-driven (TensorRT/CuPy/ONNX). Validate GPU library wheels against 3.14 before adding new ML dependencies.

**Validation:**
```powershell
# From mas_mcp directory:
uv run python -c "import cupy; print(cupy.cuda.runtime.getDeviceCount())"
```

---

#### **14.6. (`Runtime-Selection-for-Browser-Automation`) -> (`RSBA`)**

**DIRECTIVE (Updated — Bun 1.3.12):** Prefer `Bun.WebView` (Chrome backend) for browser automation. `child_process.spawn` + Playwright via Bun still broken on Windows.

```
✅ PREFERRED:   Bun.WebView({ backend: { type: "chrome" } })  <-<CDP direct, no Named Pipes, Bun-native>
✅ FALLBACK:    node tests/playwright_suite.js                 <-<forces Node.js libuv IPC>
✅ FALLBACK:    "test:e2e": "node tests/e2e_runner.js"         <-<package.json script>
✅ ALTERNATIVE: MCP Server (Node-based, containerized)         <-<bypasses Named Pipes entirely>

❌ BROKEN:      bun run tests/playwright_suite.js              <-<Bun child_process.spawn + Named Pipes = hang>
❌ BROKEN:      bunx playwright test                            <-<same Named Pipes failure>
```

**Bun.WebView Chrome backend (why it works):**
- Uses Chrome DevTools Protocol (CDP) over TCP — NOT Windows Named Pipes
- Auto-detects installed Chrome/Chromium or accepts a custom `executablePath`
- No Playwright, no `child_process.spawn` — entirely Bun-native I/O
- Cross-platform: WebKit (macOS default), Chrome (Windows/Linux)
- Available since Bun 1.3.12 — this is the revisit gate resolved

```typescript
// Bun.WebView — canonical form for browser automation on Windows
const view = new Bun.WebView({
  url: "https://example.com",
  backend: { type: "chrome" },       // required on Windows (no WKWebView)
  headless: true,                    // omit for visible window
});
const page = await view.open();
// CDP-based: evaluate JS, screenshot, navigate, intercept requests
```

**`child_process.spawn` issue (still present, unchanged):**
- Bun's Zig-based I/O has incomplete Windows Named Pipes fidelity vs. Node's `libuv`
- Symptoms: hangs at "Launching Chromium...", `ENOENT` on pipe paths, zombie browser processes
- Playwright requires Named Pipes for browser process IPC → use Node.js for Playwright-specific needs

**Hybrid Runtime Pattern (updated):**

| **Task** | **Runtime** | **Rationale** |
|----------|------------|---------------|
| Package management (`bun install`) | **Bun** | Speed advantage (global cache) |
| Script dispatch (`bun run`) | **Bun** | Fast task execution |
| Browser automation (CDP/headless) | **Bun.WebView** | Native, no IPC fragility (Bun 1.3.12+) |
| Playwright-specific suites | **Node.js** | Playwright requires Named Pipes; use `node` runner |
| MCP servers | **Node.js or Docker** | Bypass IPC fragility entirely |

**Revisit Gate:** ✅ RESOLVED — Bun 1.3.12 `Bun.WebView` (Chrome backend, CDP-direct) is the resolution. Update Playwright suites incrementally to `Bun.WebView` as bandwidth allows.

---

#### **14.7. (`Adaptive-Assessment-Systems`) -> (`AAS`)**

**CRITICAL DIRECTIVE: No assessment value is final. All ore ratings are hypotheses.**

**Canon Rule:**
ALL assessment systems MUST be adaptive. Baseline ratings are refined through measured observation of outcomes.

**Mechanism:**
1. **Cluster profiling:** Group assessed items by category (backup, candidate, recovered, legacy)
2. **Aggregate statistics:** Track `avg_ore`, `avg_extractable`, `yield_rate` per cluster
3. **Dynamic downgrade:** New item in cluster C → adjust baseline using `cluster_avg`
4. **Learning rate:** Each assessment updates cluster statistics

**Audit Trail (Mandatory):**
Every assessment MUST log:
```
baseline_ore:        (hypothesis)
cluster_influence:   (if applicable)
adjusted_ore:        (final value)
reasoning:           (why adjustment was made)
```

**Validation:** Audit trail MUST be preserved to enable rollback and analysis of assessment history.

**Status:** Mandatory for any system that repeatedly assesses similar items.

---

#### **14.8. (`Feedback-Driven-Adaptive-Learning`) -> (`FDAL`)**

**CRITICAL DIRECTIVE: Systems that predict MUST measure predictions against reality.**

**Mechanism:**
1. **Predict:** Assess inputs; generate expected outcome
2. **Observe:** Capture actual outcome (success/failure/error type)
3. **Compare:** Identify mismatches between prediction and observation
4. **Integrate:** Incorporate mismatches into future heuristics

**Metric Definitions (Non-Overlapping):**

| **Metric** | **Definition** |
|-----------|---------------|
| `outcomes_total` | Count of distinct events observed in a cycle |
| `outcomes_matched` | Events where prediction agreed with observation |
| `outcomes_error` | Events where prediction disagreed with observation |
| **Invariant** | `outcomes_matched + outcomes_error = outcomes_total` |
| `learning_rate` | `outcomes_error / outcomes_total` ∈ [0, 1] — proportion of errors per cycle |

**Thresholds:**

| **Range** | **Interpretation** |
|----------|-------------------|
| < 0.10 | System stagnant — audit heuristics |
| 0.10–0.50 | Normal adaptation |
| 0.50–0.80 | High integration — healthy |
| > 0.80 | Chaotic — stabilize or reset |

**Validation:**
- Error integration MUST be traceable (audit trail per absorbed error)
- Predictions and outcomes MUST be persisted for post-hoc analysis
- Rollback: If batch integration introduces instability, revert to prior heuristic state

**Status:** Mandatory for any system that makes outcome predictions.

---

#### **14.9. Language Runtime Version Floors (`LRVF`)**

Current verified runtime floors for non-primary toolchains:

| Runtime | Floor | Installed | Manager | Config |
|---------|-------|-----------|---------|--------|
| Zig | `0.16.0` | `0.16.0` (2026-04-13 stable) | `zv use stable` | `zig-toolchain.toml` |
| R | `4.5` | `4.5.3` (2026-03-11 ucrt) | — | `rproject.toml` |
| R packages | — | current | `rv-r upgrade` | `rproject.toml` |

**Zig:** pinned in `zig-toolchain.toml` (`channel = "0.16.0"`). Upgrade via `zv use stable`. Verify with `zig version`.

**R:** `rproject.toml` floor is `r_version = "4.5"` (minor-level floor). R packages managed via `rv-r` (`rv-r sync`, `rv-r add <pkg>`, `rv-r upgrade`). `rv-r` is the prefixed alias — bare `rv` in PWSH 7.x resolves to `Remove-Variable` (builtin alias collision) and also conflicts with the Ruby version manager (`rv` from spinel). Verify runtime with `Rscript --version`.

---

* **(`DEVELOPMENT CONVENTIONS SEALED`): → (`DEV-CONV-SLD`): 🔥**

**Date Added**: March 18, 2026 | **Last Amended**: April 2026 (Cycle 2: §14.9 LRVF — Zig 0.16.0 + R 4.5.3 floors)
**Purpose**: Ensure assistance correctly invoke uv-managed Python, respect SSOT governance, and maintain version stability across the stack.

* **(`T-DECOR`)** *approves this structural addition. It serves comprehension.*

---
