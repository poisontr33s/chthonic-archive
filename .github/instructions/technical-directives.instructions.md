# ☥ ARCHIVE GOVERNANCE: TECHNICAL DIRECTIVES ☥

> **Lineage-Position:** `Technical-Directives-Branch` — downstream vessel translating semantic lineage into operational doctrine.
> **Governance:** SSOT-L-H via [copilot-instructions.md](../copilot-instructions.md). Update-Protocol, Addressability, Enforcement-Hierarchy, No-Duplication constraint inherited — not repeated here.
> **Revised:** February 2026

---

> [!NOTE]
> This branch file houses the runtime-critical development conventions and environment-specific constraints.
> Offloaded from the SSOT to separate "Instructional Lore" from "Operational Directives."
> **Context Reference:** [copilot-instructions.md](../copilot-instructions.md#L6634) (§XIV - Development Conventions)

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

* **(`DEVELOPMENT CONVENTIONS SEALED`): → (`DEV-CONV-SLD`): 🔥**

**Date Added**: March 18, 2026
**Purpose**: Ensure assistance correctly invoke uv-managed Python, respect SSOT governance, and maintain version stability across the stack.

* **(`T-DECOR`)** *approves this structural addition. It serves comprehension.*

---
