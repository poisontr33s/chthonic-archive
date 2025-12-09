# GPU Environment Documentation

## Environment Specification

**Validated Configuration (December 2025):**
- **Python:** 3.13.10
- **CuPy:** 13.6.0 with CUDA runtime 12090
- **ONNX Runtime:** Providers: TensorRT, CUDA, CPU
- **Virtual Environment:** `mas_mcp/.venv`

---

## Critical Path: NVRTC DLL Loading

CuPy requires NVRTC (NVIDIA Runtime Compiler) for JIT compilation. On Windows, the DLL search path must include the CUDA Toolkit bin directory.

**Fix applied in `milf_genesis_v2.py`:**
```python
# CUDA path for NVRTC JIT compilation
if os.name == "nt":
    cuda_path = os.environ.get("CUDA_PATH")
    if cuda_path:
        cuda_bin = os.path.join(cuda_path, "bin")
        if os.path.isdir(cuda_bin):
            os.add_dll_directory(cuda_bin)
```

This **must** run before `import cupy`.

---

## GPU Venv Pinning

The genesis engine validates the correct Python environment:

**Environment Variable:**
```powershell
$env:MAS_MCP_GPU_PY = "c:\Users\erdno\chthonic-archive\mas_mcp\.venv\Scripts\python.exe"
```

**Validation at startup:**
```python
GPU_VENV_PATH = Path(__file__).parent / ".venv" / "Scripts" / "python.exe"

if sys.executable and not sys.executable.lower().endswith(str(GPU_VENV_PATH).lower()):
    print(f"⚠️ GPU venv mismatch: expected {GPU_VENV_PATH}, got {sys.executable}")
```

---

## Provider Enforcement

The genesis engine requires GPU providers (TensorRT or CUDA):

```python
if ONNX_AVAILABLE:
    gpu_providers = [p for p in ONNX_PROVIDERS if "CUDA" in p or "TensorRT" in p]
    if not gpu_providers and os.environ.get("GENESIS_STRICT_GPU"):
        raise RuntimeError("GENESIS_STRICT_GPU=1 but no GPU providers available")
```

---

## CuPy Warm-up

First CuPy operation has ~18ms JIT overhead. Pre-warm at module load:

```python
if GPU_AVAILABLE:
    try:
        _ = cp.ones((1,), dtype=cp.float32)
        GPU_WARMED = True
        print("✅ GPU warmed")
    except Exception as e:
        print(f"⚠️ GPU warm-up failed: {e}")
```

---

## Performance Targets

| Metric | Target | Measured |
|--------|--------|----------|
| Cold start latency | ≤ 20 ms | 18-20 ms |
| Warm synthesis latency | ≤ 1.0 ms | 0.2-0.6 ms |
| Acceptance rate | 18-28% | ~20% |
| GPU utilization | ≥ 95% | 100% |

---

## Runbook: Nightly Genesis

### 1. Environment Pin (PowerShell)
```powershell
$env:MAS_MCP_GPU_PY = "$PWD\mas_mcp\.venv\Scripts\python.exe"
```

### 2. Sanity Check
```powershell
& $env:MAS_MCP_GPU_PY -c "import onnxruntime as ort; import cupy as cp; print(ort.get_available_providers()); cp.ones((1,), dtype=cp.float32); print('GPU warmed')"
```

### 3. Run Background Cycle
```powershell
& $env:MAS_MCP_GPU_PY -c "from milf_genesis_v2 import BackgroundGenesisService; from pathlib import Path; s=BackgroundGenesisService(Path('../.github/copilot-instructions.md'), Path('genesis_artifacts')); print(s.run_cycle(target_accepts=25))"
```

---

## VRAM Management

The engine includes a VRAM watchdog:
- Threshold: 75% usage triggers backoff
- On exceed: Free CuPy memory pool blocks
- Fallback: TensorRT-only path if CuPy allocations fail

---

## Validation Policy

Default thresholds (tunable via `VALIDATION_POLICY` dict):

| Parameter | Default | Range |
|-----------|---------|-------|
| `novelty_min_distance` | 0.04 | 0.035-0.045 |
| `epsilon_derivation` | 0.005 | 0.004-0.005 |
| `redundancy_ceiling` | 0.8 | - |
| `safety_max_risk` | 0.5 | - |
| `recursion_depth_max` | 3 | 3-4 |
| `timebox_s` | 600 | 10 min |
| `vram_backoff_threshold` | 0.75 | 75% |

---

## Artifact Structure

Each synthesis cycle writes:
```
genesis_artifacts/
└── YYYYMMDD_HHMMSS/
    └── {genesis_hash}/
        ├── entity.json
        ├── validation.json
        ├── environment.json
        └── index.json  (with SHA-256 for all files)
```

---

## Troubleshooting

### NVRTC not found
```
FileNotFoundError: nvrtc-builtins64_***.dll
```
**Fix:** Ensure `CUDA_PATH` is set and `os.add_dll_directory()` runs before CuPy import.

### GPU venv mismatch warning
```
⚠️ GPU venv mismatch: expected .venv\Scripts\python.exe, got ...
```
**Fix:** Run from the correct virtual environment or set `MAS_MCP_GPU_PY`.

### VRAM backoff
```
⚠️ VRAM usage 78% exceeds threshold - backing off
```
**Fix:** Reduce batch size or restart to clear memory pool.

### Zero-delta stall
```
⚠️ ZERO-DELTA STALL: index.json unchanged, skipping commit
```
**Info:** The synthesis cycle produced identical output. Thresholds may be too strict.
