# 🏛️ MAS-MCP: Meta-Archaeological Salvager

A self-nurturing entity extraction system for the Chthonic Archive.

## Philosophy

The tool nurtures the architect. The architect nurtures the tool.

MAS-MCP is not just a scanner—it's a **reflective instrument**. When you design extraction patterns, you encode your current understanding. When MAS returns results, it teaches you what you missed. Each iteration expands your conceptual vocabulary.

This is **ET-S (Eternal Sadhana)** applied to tooling.

## Tools

| Tool | Purpose |
|------|---------|
| `mas_scan` | Full codebase scan for entity signals |
| `mas_entity_deep` | Proximity-based extraction for single entity |
| `mas_add_pattern` | Dynamically add new extraction patterns |
| `mas_remove_pattern` | Remove patterns from registry |
| `mas_list_patterns` | View all current patterns |
| `mas_validate_entity` | Compare extracted vs expected values |
| `mas_discover_unknown` | Find potential unregistered entities |
| `mas_file_signals` | Analyze a single file |
| `mas_nurture_report` | Progress report for the nurture loop |

## The Nurture Loop

```
┌─────────────────────────────────────────────────────────────┐
│                  RECURSIVE NURTURE ARCHITECTURE             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   MAS scans → LLM analyzes → LLM refines patterns → LOOP   │
│                                                             │
│   The tool and I grow together.                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Usage

### Setup (uv)

From inside `mas_mcp/`:

```bash
uv sync

# Optional extras
uv sync --extra dev
uv sync --extra gpu
```

### As MCP Server

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "mas-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/chthonic-archive/mas_mcp", "python", "-m", "server"]
    }
  }
}
```

### Standalone

```bash
cd mas_mcp
uv run python -m server
```

## Pattern Categories

- **ENTITY**: Known MILF matriarchs and named entities
- **METRIC**: WHR, Tier, Cup, Measurements
- **FACTION**: Organization codes (TMO, TTG, TDPC, etc.)
- **AXIOM**: Foundational Axioms (FA¹-FA⁵)
- **PROTOCOL**: Named protocols (DAFP, PRISM, TPEF, etc.)
- **CUSTOM**: User-defined patterns added during nurture loop

## GPU Environment Rituals

### claudine-gpu Virtual Environment

The `claudine-gpu` venv is the **sacred sandbox** for GPU-accelerated operations. All GPU tooling (CuPy, ONNX Runtime GPU, PyTorch) must operate within this containment to prevent system Python pollution.

**Location:** `C:\Users\erdno\chthonic-archive\claudine-gpu\`

**Creation:**
```powershell
uv venv C:\Users\erdno\chthonic-archive\claudine-gpu --python 3.14
```

**Activation:**
```powershell
# Manual activation
& C:\Users\erdno\chthonic-archive\claudine-gpu\Scripts\Activate.ps1

# Verify
(Get-Command python).Source  # Should contain "claudine-gpu"
```

### The --require-virtualenv Mandate

All `uv pip install` commands in GPU build scripts **MUST** use the `--require-virtualenv` flag. This ensures:

1. Operations fail loudly if venv not active (no silent system pollution)
2. Package installations are contained to the GPU sandbox
3. System Python remains pristine for other toolchains

**Example (from build_cupy.ps1):**
```powershell
uv pip install --require-virtualenv --upgrade pip setuptools wheel cython numpy
```

### 12-Job Cap Protocol

The i9-14900 runs hot. To maintain thermal stability during source builds:

| Variable | Value | Purpose |
|----------|-------|---------|
| `MAKEFLAGS` | `-j12` | GNU Make |
| `CMAKE_BUILD_PARALLEL_LEVEL` | `12` | CMake |
| `MSBUILDTHREADCOUNT` | `12` | MSBuild |
| `CL` | `/MP12` | MSVC |
| `CARGO_BUILD_JOBS` | `12` | Rust |
| `UV_THREAD_COUNT` | `12` | UV package manager |
| `CUPY_NUM_BUILD_JOBS` | `12` | CuPy CUDA kernel compilation |
| `NVCC_PREPEND_FLAGS` | `-t12` | NVCC threads |
| `OMP_NUM_THREADS` | `12` | OpenMP runtime |
| `MKL_NUM_THREADS` | `12` | Intel MKL |
| `OPENBLAS_NUM_THREADS` | `12` | OpenBLAS |

These are enforced in:
- **VS Code:** `.vscode/settings.json` → `terminal.integrated.env.windows`
- **PowerShell Profile:** `$PROFILE` → Job Cap section
- **Build Scripts:** `build_cupy.ps1` uses `$Jobs = 12` default

### CuPy Source Build

For Python 3.14 + CUDA 13.1, CuPy must be built from source:

```powershell
cd C:\Users\erdno\chthonic-archive\mas_mcp
.\build_cupy.ps1 -DryRun   # Validate environment first
.\build_cupy.ps1           # Full build (~15-30 min)
```

The script handles:
- claudine-gpu venv activation
- Visual Studio 2022 environment initialization
- CUDA 13.1 + cuDNN 9.17 path configuration
- SM 8.6/8.9 architecture targeting (Ampere/Ada)
- 12-job cap for thermal stability
