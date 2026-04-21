# ☥ ARCHIVE GOVERNANCE: DEV CONVENTIONS ☥

* **(`Codex-Brahmanica-Perfectus`/`GOVERNANCE`): = (`SSOT-Metadata`): = (`Single-Source-Of-Truth-Lineage-Heritage`): ☥ (`SSOT-L-H`):**
  * **(`Maintainer`): = (`The-Savant`/`Creator`/`User`/`Architect-Of-Apex-Synthesis-Core`)**
  * **(`Status`): = (`Operational-Perpetual-Evolution`/`ET-S`/`Integrated`/`Permanently-Living-Document`)**
  * **(`Last-Sealed`/`Conceptual-Sealing-Event`):** *January 2026* **(`Bounty-Hunt-Sync`) ☥** *Applied after Living Memory enrichment loop.*
  * **(`Lineage-Position`): = (`Dev-Conventions-Branch`) ☥** *This **(`Downstream-Vessel`)** translates **(`Semantic-Lineage`)** into **(`Operational-Doctrine`)**. It consumes **(`ANKH`)**-descended meaning; it does not define **(`ANKH`)**-core.*
  * **(`Update-Protocol`):** *All substantive edits flow through **(`SSOT`)** ☥ Branch files reference **(`Never-Duplicate`) ☥ (`Hash-Verification`)** per **(`☥XIV.3`)**.*
  * **(`Addressability`):** *Line-number ranges + section titles **(`☥I-XVI`)**. **(`HTML`)**-anchors rejected per **(`FA☥`)**☥ (**(`Ornamental-Integrity`)**) supersedes machine convenience.*
  * **(`Enforcement-Hierarchy`): ☥ (`The-Decorator`/`Tier 0.5`) ☥ (`Triumvirate`/`Tier 1`) ☥ (`Prime-Factions`/`Tier 2`) ☥ (`Branch-Instructions`) ☥ (`External-Tools`/`Implementations`)**
  * **(`Hard-Constraint`): ☥ (`No-Content-Duplication`)** *across **(`.github/instructions/*.instructions.md`)** ☥ branch files are declarative manifests, not replicas.*

---

## Development Conventions & Operational Directives

**Authority:** [copilot-instructions.md](../copilot-instructions.md#L6634) (┬ºXIV)
**Purpose:** Runtime-critical development conventions for AI assistants
**Status:** Operational reference (NOT mythological doctrine)

---

## Python Environment Management (`PEM-UV`)

**CRITICAL DIRECTIVE: Uv Handles Python, not the inverse.**

```
CORRECT:     uv run python script.py   runs script within uv-managed venv
CORRECT:     uv pip install package    installs into uv-managed venv
CORRECT:     uv sync                   syncs pyproject.toml and uv.lock
CORRECT:     uv add package            adds to pyproject.toml and uv.lock
CORRECT:     uv tool update ruff       example uv tool command
CORRECT:     uv self update            update uv version itself

INFORMATIONAL:     uv -V                   check uv version
INFORMATIONAL:     uv -v                   verbose output for debugging

INCORRECT:     python script.py          bypasses uv management
INCORRECT:     pip install package       bypasses uv, uses global
INCORRECT:     python -m pip install     same issue
```

**Rationale:**
- Python 3.14 is now stable (bugfix phase) — pinned as the project baseline
- `uv` manages Python acquisition, virtual environments, lockfiles, and dependency resolution
- `uv` manages the virtual environment, lockfile, and dependency resolution
- Invoking `python` or `pip` directly bypasses this governance, if `pip` or others are required *then:*
  - **->** `uv pip` **->** *"'pipping' the* **`pip`** *with* **`uv`**"

**Environment Variables (when needed):**
```powershell
$env:VIRTUAL_ENV = "c:\Users\eldno\chthonic-archive\mas_mcp\.venv"
$env:PATH = "$env:VIRTUAL_ENV\Scripts;$env:PATH"
```

---

## Frontend Runtime Management (`FRM-BUN`)

**Stack:** Bun 1.x.x + Next.js + React xx.x + TypeScript x.x.x

**Commands:**
```
bun run dev          # Development server
bun run build        # Production build (uses --webpack flag)
bun add <package>    # Add dependency
bun update           # Update all dependencies
bun pm ls            # List installed packages
```

**Version Policy:**
- **Stable preferred** for production focus (Next.js xx.x, TypeScript x.x.x)
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
| **Ceremonial** | `$validate$` syntax (┬º10.6) | Magistra Bibliotheca Perfecta | Human-executable | READS SSOT, validates against 13-checkpoint matrix |
| **Programmatic** | `ssot_hash()` | Python/uv script | Drift detection | READS SSOT, computes canonical hash for change detection |
| **Probe** | `Discover-SSOT-Treasure.ps1` | PowerShell (frozen) | Structural audit | READS SSOT, scans for signals/markers (read-only) |

**Critical Governance:**
1. **SSOT is SOURCE, never TARGET:** All validation tools READ from SSOT. No external artifact may ALTER SSOT content.
2. **Downstream-only artifacts:** Any JSON, schema, or report generated from SSOT is DERIVATIVE. If SSOT changes, derivatives are obsoleteÔÇönot vice versa.
3. **Frozen probe status:** `scripts/Discover-SSOT-Treasure.ps1` is designated FROZEN. Modifications require explicit unfreezing authorization.

**Ceremonial vs Programmatic Validation:**

| **Aspect** | **`$validate$` (┬º10.6)** | **`ssot_hash()`** |
|------------|--------------------------|-------------------|
| **Purpose** | Verify operational compliance with SSOT checkpoints | Detect unauthorized SSOT modifications |
| **Frequency** | Per-operation (invoked via `$magistra$` syntax) | Per-session (bookend verification) |
| **Output** | Spectral frequency (PURE-WHITE ÔåÆ OBSIDIAN) | SHA-256 hash (drift detection) |
| **Human-readable** | Ô£à Yes (ornate/minimal visual modes) | ÔØî No (programmatic comparison only) |
| **FA Correlation** | Ô£à Yes (checkpointÔåÆFA mapping) | ÔØî No (content-agnostic) |

**Validation Escalation Path:**
1. `$validate$` checkpoint failure ÔåÆ Spectral frequency degrades ÔåÆ Corrective action per ┬º10.6.5
2. `ssot_hash()` mismatch ÔåÆ GOVERNANCE_DRIFT_DETECTED ÔåÆ Session invalidation, SSOT restoration required
3. Both failures ÔåÆ Existential threat ÔåÆ Emergency protocols (┬º10.7.5 ╬öEXIST activation)

**External Tool Governance:**
- **mas_mcp/schemas/*.json** ÔÇö If present, these are DEPRECATED downstream artifacts; SSOT entity data lives in ┬º4.3.3.1 WHR Validation Matrix
- **ankh_index.json** ÔÇö Coordinate map artifact (read-only)
- **curriculum_core_v1.json** ÔÇö Legacy artifact; curriculum data authority resides in SSOT

---

## Project Structure Reference (`PSR`)

```
chthonic-archive/
Ôö£ÔöÇÔöÇ .github/
Ôöé   Ôö£ÔöÇÔöÇ copilot-instructions.md    ÔåÉ SSOT
Ôöé   ÔööÔöÇÔöÇ instructions/              ÔåÉ Operational directives (this file)
Ôö£ÔöÇÔöÇ mas_mcp/                        ÔåÉ Python Backend (uv-managed)
Ôöé   Ôö£ÔöÇÔöÇ .venv/                      ÔåÉ Python 3.14.4 virtual environment
Ôöé   Ôö£ÔöÇÔöÇ pyproject.toml              ÔåÉ uv project definition
Ôöé   Ôö£ÔöÇÔöÇ uv.lock                     ÔåÉ Locked dependencies
Ôöé   Ôö£ÔöÇÔöÇ server.py                   ÔåÉ MCP Server entry point
Ôöé   Ôö£ÔöÇÔöÇ scripts/
Ôöé   Ôöé   ÔööÔöÇÔöÇ run_cycle.py            ÔåÉ Cycle execution
Ôöé   ÔööÔöÇÔöÇ frontend/                   ÔåÉ Bun/Next.js Dashboard
Ôöé       Ôö£ÔöÇÔöÇ package.json
Ôöé       Ôö£ÔöÇÔöÇ pages/
Ôöé       ÔööÔöÇÔöÇ lib/
Ôö£ÔöÇÔöÇ src/                            ÔåÉ Rust/Vulkan (Chthonic Archive renderer)
Ôöé   ÔööÔöÇÔöÇ main.rs
Ôö£ÔöÇÔöÇ assets/
Ôöé   ÔööÔöÇÔöÇ shaders/
ÔööÔöÇÔöÇ Cargo.toml
```

---

## GPU Stack Compatibility (`GSC`)

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

**Date Extracted:** January 22, 2026
**Purpose:** Ensure AI assistants correctly invoke uv-managed Python, respect SSOT governance, and maintain version stability across the stack.
