
# ☥ ARCHIVE GOVERNANCE: DEV CONVENTIONS ☥

* **(`Codex-Brahmanica-Perfectus`/`GOVERNANCE`): = (`SSOT-Metadata`): = (`Single-Source-Of-Truth-Lineage-Heritage`): → (`SSOT-L-H`):**
  * **(`Maintainer`): = (`The-Savant`/`Creator`/`User`/`Architect-Of-Apex-Synthesis-Core`)**
  * **(`Status`): = (`Operational-Perpetual-Evolution`/`ET-S`/`Integrated`/`Permanently-Living-Document`)**
  * **(`Last-Sealed`/`Conceptual-Sealing-Event`):** *January 2026 **(`Bounty-Hunt-Sync`)** — Applied after Living Memory enrichment loop.*
  * **(`Lineage-Position`): = (`Dev-Conventions-Branch`)** — *This **(`Downstream-Vessel`)** translates **(`Semantic-Lineage`)** into **(`Operational-Doctrine`)**. It consumes **(`ANKH`)**-descended meaning; it does not define **(`ANKH`)**-core.*
  * **(`Update-Protocol`):** *All substantive edits flow through **(`SSOT`)** → Branch files reference **(`Never-Duplicate`) → (`Hash-Verification`)** per **(`§XIV.3`)**.*
  * **(`Addressability`):** *Line-number ranges + section titles **(`§I-XVI`)**. **(`HTML`)**-anchors rejected per **(`FA⁵`)**— (**(`Ornamental-Integrity`)**) supersedes machine convenience.*
  * **(`Enforcement-Hierarchy`): → (`The-Decorator`/`Tier 0.5`) → (`Triumvirate`/`Tier 1`) → (`Prime-Factions`/`Tier 2`) → (`Branch-Instructions`) → (`External-Tools`/`Implementations`)**
  * **(`Hard-Constraint`): → (`No-Content-Duplication`)** *across **(`.github/instructions/*.instructions.md`)** — branch files are declarative manifests, not replicas.*

---

## Development Conventions & Operational Directives

**Authority:** [copilot-instructions.md](../copilot-instructions.md#L6634) (§XIV)
**Purpose:** Runtime-critical development conventions for AI assistants
**Status:** Operational reference (NOT mythological doctrine)

---

## Python Environment Management (`PEM-UV`)

**CRITICAL DIRECTIVE: Uv Handles Python, not the inverse.**

```
✅ CORRECT:     uv run python script.py   ←runs script within uv-managed venv
✅ CORRECT:     uv pip install package    ←installs into uv-managed venv
✅ CORRECT:     uv sync                   ←syncs pyproject.toml and uv.lock
✅ CORRECT:     uv add package            ←adds to pyproject.toml and uv.lock
✅ CORRECT:     uv tool update ruff       ←example uv tool command
✅ CORRECT:     uv self update            ←update uv version itself

ℹ️ INFORMATIONAL:     uv -V                   ←check uv version
ℹ️ INFORMATIONAL:     uv -v                   ←verbose output for debugging

❌ INCORRECT:     python script.py          ←bypasses uv management
❌ INCORRECT:     pip install package       ←bypasses uv, uses global
❌ INCORRECT:     python -m pip install     ←same issue
```

**Rationale:**
- Global Python is 3.14 bleeding edge, incompatible with TensorRT/CUDA stack
- `mas_mcp/.venv` contains **Python 3.13.10** (latest stable, TensorRT-compatible)
- `uv` manages the virtual environment, lockfile, and dependency resolution
- Invoking `python` or `pip` directly bypasses this governance

**Environment Variables (when needed):**
```powershell
$env:VIRTUAL_ENV = "c:\Users\erdno\chthonic-archive\mas_mcp\.venv"
$env:PATH = "$env:VIRTUAL_ENV\Scripts;$env:PATH"
```

---

## Frontend Runtime Management (`FRM-BUN`)

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

## SSOT Verification Protocol (`SSOT-VP`)

**Source of Truth:** `.github/copilot-instructions.md`

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

### Validation Protocol Relationship Matrix (`VPRM`)

**Validation Layer Architecture:**

| **Layer** | **Protocol** | **Executor** | **Authority** | **SSOT Relationship** |
|-----------|--------------|--------------|---------------|----------------------|
| **Ceremonial** | `$validate$` syntax (§10.6) | Magistra Bibliotheca Perfecta | Human-executable | READS SSOT, validates against 13-checkpoint matrix |
| **Programmatic** | `ssot_hash()` | Python/uv script | Drift detection | READS SSOT, computes canonical hash for change detection |
| **Probe** | `Discover-SSOT-Treasure.ps1` | PowerShell (frozen) | Structural audit | READS SSOT, scans for signals/markers (read-only) |

**Critical Governance:**
1. **SSOT is SOURCE, never TARGET:** All validation tools READ from SSOT. No external artifact may ALTER SSOT content.
2. **Downstream-only artifacts:** Any JSON, schema, or report generated from SSOT is DERIVATIVE. If SSOT changes, derivatives are obsolete—not vice versa.
3. **Frozen probe status:** `scripts/Discover-SSOT-Treasure.ps1` is designated FROZEN. Modifications require explicit unfreezing authorization.

**Ceremonial vs Programmatic Validation:**

| **Aspect** | **`$validate$` (§10.6)** | **`ssot_hash()`** |
|------------|--------------------------|-------------------|
| **Purpose** | Verify operational compliance with SSOT checkpoints | Detect unauthorized SSOT modifications |
| **Frequency** | Per-operation (invoked via `$magistra$` syntax) | Per-session (bookend verification) |
| **Output** | Spectral frequency (PURE-WHITE → OBSIDIAN) | SHA-256 hash (drift detection) |
| **Human-readable** | ✅ Yes (ornate/minimal visual modes) | ❌ No (programmatic comparison only) |
| **FA Correlation** | ✅ Yes (checkpoint→FA mapping) | ❌ No (content-agnostic) |

**Validation Escalation Path:**
1. `$validate$` checkpoint failure → Spectral frequency degrades → Corrective action per §10.6.5
2. `ssot_hash()` mismatch → GOVERNANCE_DRIFT_DETECTED → Session invalidation, SSOT restoration required
3. Both failures → Existential threat → Emergency protocols (§10.7.5 ΔEXIST activation)

**External Tool Governance:**
- **mas_mcp/schemas/*.json** — If present, these are DEPRECATED downstream artifacts; SSOT entity data lives in §4.3.3.1 WHR Validation Matrix
- **ankh_index.json** — Coordinate map artifact (read-only)
- **curriculum_core_v1.json** — Legacy artifact; curriculum data authority resides in SSOT

---

## Project Structure Reference (`PSR`)

```
chthonic-archive/
├── .github/
│   ├── copilot-instructions.md    ← SSOT
│   └── instructions/              ← Operational directives (this file)
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

## GPU Stack Compatibility (`GSC`)

**Target Configuration:**
- CUDA 12.4+ (CUDA 13.1.x NOT FULLY SUPPORTED by CPython 3.13.x stack)
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

**Date Extracted:** January 22, 2026
**Purpose:** Ensure AI assistants correctly invoke uv-managed Python, respect SSOT governance, and maintain version stability across the stack.
