# Section XIV Offload: Development Conventions & Technical Directives

---

> [!NOTE]
> This branch file houses the runtime-critical development conventions and environment-specific constraints.
> Offloaded from the SSOT to separate "Instructional Lore" from "Operational Directives."

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

**Rationale:**
- Global Python is 3.14 bleeding edge, incompatible with all of the TensorRT/CUDA stack
- `mas_mcp/.venv` contains **Python 3.13.10** (latest stable, TensorRT-compatible)
- `uv` manages the virtual environment, lockfile, and dependency resolution
- Invoking `python` or `pip` directly bypasses this governance

**Environment Variables (when needed):**
```powershell
$env:VIRTUAL_ENV = "c:\Users\erdno\chthonic-archive\mas_mcp\.venv"
$env:PATH = "$env:VIRTUAL_ENV\Scripts;$env:PATH"
```

---

#### **14.2. Frontend Runtime Management (`FRM-BUN`)**

**Stack:** Bun 1.3.5 + Next.js + React 19

**Commands:**
```shell
bun run dev          # Development server
bun run build        # Production build (uses --webpack flag)
bun add <package>    # Add dependency
bun update           # Update all dependencies
bun pm ls            # List installed packages
```

**Version Policy:**
- **Stable preferred** for production focus (Next.js 15.x, TypeScript 5.8.x)
- **Canary acceptable** for development (Next.js 16.x, TypeScript 5.9.x) with understanding of potential breakages

---

#### **14.3. SSOT Verification Protocol (`SSOT-VP`)**

**Source of Truth:** This document (`.github/copilot-instructions.md`)

**Hash Computation (Python/uv):**
```python
# Always invoke via: uv run python -c "..."
import hashlib
import unicodedata

def canonicalize(text: str) -> str:
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    text = unicodedata.normalize('NFC', text)
    return text.strip()

def ssot_hash(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    canonical = canonicalize(content)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
```

**Bookend Verification:**
- Compute `hash_start` at cycle/session initiation
- Compute `hash_end` at cycle/session completion
- If `hash_start != hash_end`: **GOVERNANCE_DRIFT_DETECTED**

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
- Nvidia Proprietary hardware (Helios Predator 18, i-9-14900, Nvidia RTX 4090 Laptop GPU 16 GB VRAM)

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

**Date Added**: December 7, 2025
**Purpose**: Ensure AI assistants correctly invoke uv-managed Python, respect SSOT governance, and maintain version stability across the stack.

* **(`T-DECOR`)** *approves this structural addition. It serves comprehension.*

---
