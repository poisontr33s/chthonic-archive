# Technical Directives

> SSOT: [copilot-instructions.md](../copilot-instructions.md#L6634) §XIV — runtime-critical, not aesthetic.

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

Scripts that emit Unicode, emoji, or Rich-rendered output require explicit stdout encoding on Windows. The `# -*- coding: utf-8 -*-` header covers file *reading*; `PYTHONIOENCODING=utf-8` covers stdout *writing*. Set it universally — no downside.

```powershell
# PowerShell (pwsh) — canonical form for this repo:
✅ PREFERRED:   $env:PYTHONIOENCODING = 'utf-8'; uv run scripts/<script>.py <args>

# brush / bash-compatible — same effect:
✅ PREFERRED:   PYTHONIOENCODING=utf-8 uv run scripts/<script>.py <args>

# Inline python -c usage (e.g., one-shot data extraction):
✅ CORRECT:     $env:PYTHONIOENCODING = 'utf-8'; uv run python -c "<code>"
```

**Trigger:** any script that uses `rich`, produces emoji/box-drawing characters, or pipes output through `| head` / `2>&1` on Windows.
**Universal lock:** set for all `uv run` invocations — safe to apply unconditionally.

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
$env:VIRTUAL_ENV = "c:\Users\erdno\chthonic-archive\mas_mcp\.venv"
$env:PATH = "$env:VIRTUAL_ENV\Scripts;$env:PATH"
```

---

#### **14.2. Frontend Runtime Management (`FRM-BUN`)**

**Stack:** Bun 1.3.x (>=1.3.11) + Next.js + React 19

**Commands:**
```shell
bun run dev          # Development server
bun run build        # Production build (uses --webpack flag)
bun add <package>    # Add dependency
bun update           # Update all dependencies
bun pm ls            # List installed packages
```

**Version Policy:**
- **Stable preferred** for production focus (Next.js, React, TypeScript)

---

#### **14.4. Project Structure Reference (`PSR`)**

```
chthonic-archive/
├── .github/
│   └── copilot-instructions.md    ← SSOT (This Document)
├── mas_mcp/                        ← Python Backend (uv-managed)
│   ├── .venv/                      ← Python 3.13.10 virtual environment
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
- CUDA 12.4+ <<- & (CUDA 13.1.x (but NOT FULLY SUPPORTED) -> by Uv's CPython's 3.13.x stack)
- cuDNN 9.x
- TensorRT 10.x
- Python 3.13.x (NOT 3.14)
- Numpy 1.26.x
- CuPy 12.x
- ONNX Runtime GPU 1.16.x
- PyTorch 2.2.x (with CUDA 12.4 support)
- Rapids AI 24.x (if needed)
- Nvidia Proprietary hardware (Desktop, i-9-13900, Nvidia RTX 4090 GPU 24 GB VRAM)

**Why Python 3.13?**
- TensorRT wheels are not yet available for Python 3.14
- CuPy CUDA bindings require 3.13 or earlier
- ONNX Runtime GPU requires 3.13 for stable operation
- It's just too new; ecosystem not yet caught up

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

* **(`DEVELOPMENT CONVENTIONS SEALED`): → (`DEV-CONV-SLD`): 🔥**

**Date Added**: March 18, 2026 | **Last Amended**: March 27, 2026 (Cycle 1: §14.6 RSBA, §14.7 AAS, §14.8 FDAL)
**Purpose**: Ensure assistance correctly invoke uv-managed Python, respect SSOT governance, and maintain version stability across the stack.

* **(`T-DECOR`)** *approves this structural addition. It serves comprehension.*

---
