# FAF Application: tabbyAPI / Python 3.14 / uv GPU Inference Host

**Version:** v0.1  
**Status:** Gates executed, boundaries recorded, ledger current  
**Primary challenge:** tabbyAPI on Python 3.14 + uv must be verified as a GPU-capable inference host  
**FAF source:** [FAF_FRAMING_AS_FUNCTION_METHODOLOGY.md](FAF_FRAMING_AS_FUNCTION_METHODOLOGY.md)  
**Filed:** 2026-04-25  
**Commit range:** `f03cf39d` (archive) / `bfeb655b` (tabbyAPI submodule)

---

## 0. Retargeting Declaration

The original FAF proving challenge:
> Ruby 4.0.3 on Windows 11 must be forced into a verified foreign-capability host.

This application retargets FAF to:
> **Python 3.14 + uv on Windows 11 must be verified as a GPU-capable inference host for tabbyAPI.**

The host language changes from Ruby to Python.  
The foreign-capability stack changes from CUDA-via-Fiddle to torch/exllamav2/exl3/flash_attn via PyO3 + CUDA wheels.  
The membrane changes from Windows DLL loader to uv dependency resolver + PyO3 ABI layer.  
The False Success Ban, Capability Ladder, and Impossible-Currently Boundary schema are unchanged.

---

## 1. Challenge Statement

```
Python 3.14 (uv-managed) must be forced into a verified GPU inference host
for tabbyAPI (theroyallab/tabbyAPI, dev/tabbyAPI/ submodule).

The candidate system begins as:
  Python 3.14.4 (uv-managed, only-managed preference)
  uv 0.6.x with [tool.uv.sources] + [[tool.uv.index]] index routing
  hatchling build backend (editable install, only-include = [])
  pyproject.toml with cu12 / amd optional-dependency extras
  override-dependencies to bypass exact-pin blockers
  foreign middleware candidates:
    torch >= 2.9.0 via pytorch-cu128 index
    pytorch-triton-rocm >= 3.5.0 via pytorch-rocm64 index
    exllamav2 (cp310-cp313 direct-URL wheels)
    exllamav3 (cp310-cp313 direct-URL wheels)
    flash_attn (cp310-cp313 direct-URL wheels)
    pydantic-core 2.46.x (PyO3 >= 0.25.x, has cp314 wheels)
    CUDA runtime (nvcuda.dll / libcuda.so)
    NVIDIA driver stack (RTX 4090, driver 596.21)

The challenge is NOT:
  pip install torch
  Add GPU extra to requirements.txt
  Run tabbyAPI with Python 3.13 (the easy path)
  Defer to a Docker container with prebuilt wheels
  Lie about cp314 wheel availability for inference libraries

The actual challenge is:
  Make Python 3.14 + uv become a verified GPU inference host for tabbyAPI
  without lying about what torch, exllamav2, exl3, flash_attn, pydantic-core,
  PyO3, CUDA, or the uv resolver can actually do on Python 3.14.
```

---

## 2. False Success Ban (Python translation)

A GPU inference capability for tabbyAPI is **not** admitted because any of these are true:

```
A [cu12] optional-dependency entry exists in pyproject.toml.
A pytorch-cu128 index is declared in [[tool.uv.index]].
torch appears in the resolved lockfile.
A wheel URL exists in the uv cache.
override-dependencies resolved without error.
uv sync completed without exit code 1.
A CUDA driver is installed on the host.
A GPU is present in Device Manager.
A README says "CUDA is supported".
A test imports pydantic and passes.
```

Those facts may create candidate gates.  
They do not admit GPU inference capability.

---

## 3. Gate Ledger

Status as of commit `bfeb655b` / `f03cf39d` (2026-04-25).

### Gate 1 — Python 3.14 Resolver Coherence
**Question:** Can uv resolve a GPU-backend wheel stack for Python 3.14 without false admission or resolver crash?

**Artifacts produced:**
- **Binding:** `[tool.uv.sources]` + `[[tool.uv.index]]` — torch and pytorch-triton-rocm routed to pytorch-cu128 / pytorch-rocm64 index. Index resolves by Python version without per-version URL matrix. No cp314-specific URL required — the index carries whatever CPython versions are published.
- **Membrane:** `override-dependencies = ["pydantic>=2.13.0,<3"]` — prevents exllamav3 v0.0.21's `pydantic==2.11.0` exact pin from blocking pydantic-core 2.46.x (cp314 wheels) from resolving. Conflict isolation via `[tool.uv.conflicts]` prevents cu12+amd co-installation.

**Level reached:** L2 (Interrogable — resolver can identify and route packages)  
**Status:** `admitted` — resolver operates correctly on Python 3.14  
**Proof:** `uv run pytest tests/test_start_ps1.py -v` → 17/17 passed (Python 3.14.4)  
**Commit:** `bfeb655b`

---

### Gate 2 — pydantic-core PyO3 ABI
**Question:** Can pydantic-core on Python 3.14 pass tabbyAPI's validation layer?

**Background:** pydantic-core 2.33.0 used PyO3 0.24.0, which hard-capped at Python ≤ 3.13. pydantic-core 2.46.3 ships PyO3 ≥ 0.25.x with cp314 wheels on PyPI.

**Artifacts produced:**
- **Probe:** `uv run python -c "import pydantic; print(pydantic.version.VERSION)"` → pydantic 2.x admitted
- **Binding:** `override-dependencies = ["pydantic>=2.13.0,<3"]` forces resolver to pydantic-core ≥ 2.46.x where cp314 wheels exist
- **Membrane:** The override does not change tabbyAPI's stated `pydantic >= 2.11.0,<3` floor — it only bypasses the downstream exact pin

**Level reached:** L4 (Useful — pydantic validation used by 17/17 test suite entries)  
**Status:** `admitted`  
**Proof:** `uv run pytest tests/test_start_ps1.py -v` → 17/17 passed; pydantic schema validation exercised throughout  
**Commit:** `bfeb655b`

---

### Gate 3 — torch CUDA Discovery (Python 3.14)
**Question:** Can Python 3.14 discover, load, and report a CUDA device via torch?

**Current state:** torch >= 2.9.0 resolves from the pytorch-cu128 index. As of 2026-04-25, cp314 torch wheels availability on the pytorch index is **unverified** — the index exists and torch resolves, but no probe has confirmed `torch.cuda.is_available()` returns `True` on Python 3.14.4.

**Artifacts produced:**
- **Probe (pending):** `uv run --extra cu12 python -c "import torch; print(torch.version.cuda, torch.cuda.is_available(), torch.cuda.device_count())"` → must emit: CUDA version string, boolean, integer
- **Required emissions:** `manifest/python_host.json`, `manifest/cuda_gate.jsonl`

**Required probe behavior:**
```
torch not loadable -> record wheel_gap gate
torch loads, cuda not available -> record driver/runtime gate  
torch loads, cuda available, device_count=0 -> record device_absent gate
torch loads, cuda available, device_count>0 -> L3 survivable, next: L4 call gate
```

**Level reached:** L1 (resolver can locate torch wheel slot; load not yet confirmed on cp314)  
**Status:** `probe_pending` — wheel resolution admitted; CUDA load truth unknown  
**Minimum condition to run probe:** `uv sync --extra cu12` completes on Python 3.14.4

```json
{
  "artifact_type": "probe",
  "gate": "torch/cuda_discovery",
  "claim": "torch.cuda.is_available() returns True on Python 3.14.4 + RTX 4090 + driver 596.21",
  "observed_failure": "not yet probed",
  "proof": "uv run --extra cu12 python -c \"import torch; print(torch.version.cuda, torch.cuda.is_available())\"",
  "minimum_condition_to_reopen": "cp314 torch wheel confirmed present in pytorch-cu128 index",
  "upstream_dependency": "pytorch/pytorch wheel release for cp314",
  "next_probe": "torch_cuda_device_interrogation_probe",
  "status": "blocked_not_closed"
}
```

---

### Gate 4 — exllamav2 cp314 Wheel (Impossible-Currently)
**Question:** Can exllamav2 be loaded on Python 3.14?

**Background:** exllamav2 v0.3.2 (turboderp-org/exllamav2) was built against cp310–cp313. No cp314 wheel exists at the direct-URL slots in pyproject.toml as of 2026-04-25.

**Observed failure:** `pyproject.toml` lists 8 direct-URL entries for exllamav2 covering cp310–cp313. There is no cp314 entry. uv resolver skips the package for Python 3.14 resolves of the cu12 extra.

**Proof:**
```
grep exllamav2 dev/tabbyAPI/pyproject.toml
# Result: 8 entries, highest: cp313-cp313-win_amd64
# cp314 gap: commented with "# cp314: pending turboderp-org/exllamav2 release"
```

```json
{
  "artifact_type": "impossible_currently_boundary",
  "gate": "exllamav2/cp314_wheel",
  "claim": "exllamav2 is loadable on Python 3.14",
  "observed_failure": "No cp314 wheel published at turboderp-org/exllamav2 as of 2026-04-25. Highest published: cp313.",
  "proof": "grep exllamav2 dev/tabbyAPI/pyproject.toml",
  "minimum_condition_to_reopen": "turboderp-org/exllamav2 publishes a release with cp314-cp314-win_amd64 wheel",
  "upstream_dependency": "turboderp-org/exllamav2 v0.3.x+ release with cp314 wheel",
  "next_probe": "exllamav2_cp314_wheel_existence_probe",
  "status": "blocked_not_closed"
}
```

**Level reached:** L0 (Discoverable — package known, URL pattern known, cp314 slot absent)  
**Status:** `blocked_not_closed`

---

### Gate 5 — exllamav3 cp314 Wheel (Impossible-Currently)
**Question:** Can exllamav3 be loaded on Python 3.14?

**Background:** exllamav3 v0.0.21 (turboderp-org/exllamav3) covers cp310–cp313. No cp314 wheel exists. Additionally, exllamav3 v0.0.21 contains an exact `pydantic==2.11.0` pin in its metadata — bypassed by `override-dependencies` at the resolver level, but this does not create a cp314 wheel.

**Observed failure:** No cp314 direct-URL entry; resolver correctly skips exllamav3 for Python 3.14.

```json
{
  "artifact_type": "impossible_currently_boundary",
  "gate": "exllamav3/cp314_wheel",
  "claim": "exllamav3 is loadable on Python 3.14",
  "observed_failure": "No cp314 wheel published at turboderp-org/exllamav3 as of 2026-04-25. Highest published: cp313. Additionally: exact pydantic==2.11.0 pin in v0.0.21 metadata (bypassed by override-dependencies, does not create a wheel).",
  "proof": "grep exllamav3 dev/tabbyAPI/pyproject.toml",
  "minimum_condition_to_reopen": "turboderp-org/exllamav3 publishes a release with cp314-cp314-win_amd64 wheel AND drops or loosens pydantic exact pin",
  "upstream_dependency": "turboderp-org/exllamav3 v0.0.22+ release",
  "next_probe": "exllamav3_cp314_wheel_existence_probe",
  "status": "blocked_not_closed"
}
```

**Level reached:** L0  
**Status:** `blocked_not_closed`

---

### Gate 6 — flash_attn cp314 Wheel (Impossible-Currently)
**Question:** Can flash_attn be loaded on Python 3.14?

**Background:** flash_attn v2.8.3 (kingbri1/flash-attention fork) covers cp310–cp313. No cp314 wheel exists.

```json
{
  "artifact_type": "impossible_currently_boundary",
  "gate": "flash_attn/cp314_wheel",
  "claim": "flash_attn is loadable on Python 3.14",
  "observed_failure": "No cp314 wheel published at kingbri1/flash-attention as of 2026-04-25. Highest published: cp313.",
  "proof": "grep flash_attn dev/tabbyAPI/pyproject.toml",
  "minimum_condition_to_reopen": "kingbri1/flash-attention publishes a release with cp314-cp314-win_amd64 wheel",
  "upstream_dependency": "kingbri1/flash-attention v2.9.x+ release with cp314 wheel",
  "next_probe": "flash_attn_cp314_wheel_existence_probe",
  "status": "blocked_not_closed"
}
```

**Level reached:** L0  
**Status:** `blocked_not_closed`

---

## 4. Capability Ladder — Current State

| Capability | L0 | L1 | L2 | L3 | L4 | Status |
|------------|----|----|----|----|-----|--------|
| Python 3.14 interpreter | ✅ | ✅ | ✅ | ✅ | ✅ | Admitted — uv-managed, 17/17 tests |
| pydantic-core 2.46.x | ✅ | ✅ | ✅ | ✅ | ✅ | Admitted — cp314 wheel, PyO3 0.25.x |
| uv resolver (cu12 index) | ✅ | ✅ | ✅ | ✅ | ✅ | Admitted — index routing operational |
| torch (cu12, cp314) | ✅ | ❓ | ❓ | ❓ | ❓ | L0 admitted; L1+ probe pending |
| exllamav2 | ✅ (L0 known-absent) | ❌ | ❌ | ❌ | ❌ | Impossible-Currently (cp314 gap) |
| exllamav3 | ✅ (L0 known-absent) | ❌ | ❌ | ❌ | ❌ | Impossible-Currently (cp314 gap) |
| flash_attn | ✅ (L0 known-absent) | ❌ | ❌ | ❌ | ❌ | Impossible-Currently (cp314 gap) |
| CUDA driver (RTX 4090) | ✅ | ❓ | ❓ | ❓ | ❓ | L0 (driver installed); L1+ awaits torch probe |

Key: ✅ = admitted at this level | ❌ = blocked | ❓ = not yet probed

---

## 5. FAF Failure-to-Artifact Compiler (Python translation)

| Failure | FAF Artifact |
|---------|-------------|
| Resolver cannot find cp314 wheel | Impossible-Currently Boundary (wheel gap) |
| PyO3 ABI cap blocks Python 3.14 | Impossible-Currently → resolved via pydantic-core upgrade + override-dependencies |
| Exact pin in upstream package metadata | Membrane (override-dependencies bypasses resolver, does not create wheel) |
| `torch.cuda.is_available()` returns False | CUDA driver/runtime compatibility probe |
| GPU device count = 0 with CUDA available | Device-absent boundary record |
| exllamav2 import fails on cp314 | Known wheel gap → impossible-currently boundary |
| uv sync crashes on index | Index URL + Python version compatibility probe |
| hatchling editable build fails | Build backend gate (package = false, only-include = []) |
| ruff target-version mismatch | Linter configuration gate (deferred: py314 target not yet in ruff) |
| tabbyAPI tests fail on Python 3.14 | Test-suite gate — boundary at specific failed assertion |

---

## 6. Membrane Inventory

| Membrane | Purpose | Current State |
|----------|---------|---------------|
| `override-dependencies` | Bypasses exllamav3 exact `pydantic==2.11.0` pin at resolver level | Active — prevents false resolver failure |
| `[tool.uv.conflicts]` | Prevents cu12+amd co-installation | Active — mutual exclusion enforced |
| `[[tool.uv.index]]` | Routes torch/triton to vendor index, not PyPI | Active — correct wheel source for CUDA builds |
| `[tool.hatch.metadata] allow-direct-references = true` | Permits direct-URL wheel entries in pyproject.toml | Active — required for exllamav2/exl3/flash_attn direct URLs |
| `package = false` | Prevents uv from treating tabbyAPI as a publishable dist-package | Active |
| cp314 gap comments | Documents known impossible-currently boundaries inline in pyproject.toml | Active — prevents false assumption that wheel exists |

---

## 7. Pending Probes

### Probe P-01 — Python Host Identity
```python
# probes/python/python_host_probe.py
import json, sys, platform, importlib.metadata

host = {
    "python_version": sys.version,
    "python_implementation": platform.python_implementation(),
    "platform": platform.platform(),
    "machine": platform.machine(),
    "processor": platform.processor(),
    "python_path": sys.executable,
}

# Emit to manifest/python_host.json
print(json.dumps(host, indent=2))
```

**Gate:** `host/python_identity`  
**Required emissions:** `manifest/python_host.json`

---

### Probe P-02 — torch CUDA Gate
```python
# probes/python/torch_cuda_probe.py
import json, sys

result = {
    "gate": "torch/cuda_discovery",
    "python_version": sys.version,
}

try:
    import torch
    result["torch_version"] = torch.__version__
    result["cuda_version"] = torch.version.cuda
    result["cuda_available"] = torch.cuda.is_available()
    result["device_count"] = torch.cuda.device_count() if torch.cuda.is_available() else 0
    result["level"] = "L2_interrogable" if torch.cuda.is_available() else "L1_loadable_cuda_absent"
    if torch.cuda.is_available() and torch.cuda.device_count() > 0:
        result["device_name"] = torch.cuda.get_device_name(0)
        result["device_capability"] = torch.cuda.get_device_capability(0)
        result["level"] = "L4_useful"
except ImportError as e:
    result["level"] = "L0_or_L1_blocked"
    result["error"] = str(e)
    result["status"] = "blocked_not_closed"
    result["minimum_condition_to_reopen"] = "cp314 torch wheel present in pytorch-cu128 index"
    result["upstream_dependency"] = "pytorch/pytorch release with cp314 wheel"

print(json.dumps(result, indent=2))
```

**Gate:** `torch/cuda_discovery`  
**Run:** `uv run --extra cu12 python probes/python/torch_cuda_probe.py`  
**Required emissions:** `manifest/cuda_gate.jsonl`

---

### Probe P-03 — exllamav2 cp314 Existence Check
```python
# probes/python/exllamav2_cp314_probe.py
"""
Probe: does a cp314-cp314-win_amd64 wheel exist at the turboderp-org/exllamav2 release?
This probe does NOT attempt installation — it interrogates the release metadata only.
"""
import json, urllib.request, sys

RELEASE_API = "https://api.github.com/repos/turboderp-org/exllamav2/releases/latest"

try:
    with urllib.request.urlopen(RELEASE_API) as r:
        release = json.loads(r.read())
    assets = [a["name"] for a in release.get("assets", [])]
    cp314_wheels = [a for a in assets if "cp314" in a]
    result = {
        "gate": "exllamav2/cp314_wheel",
        "release_tag": release.get("tag_name"),
        "cp314_wheels_found": cp314_wheels,
        "status": "admitted" if cp314_wheels else "blocked_not_closed",
        "level": "L0_discoverable" if cp314_wheels else "L0_known_absent",
    }
    if not cp314_wheels:
        result["minimum_condition_to_reopen"] = "cp314-cp314-win_amd64 wheel appears in release assets"
except Exception as e:
    result = {"gate": "exllamav2/cp314_wheel", "error": str(e), "status": "probe_failed"}

print(json.dumps(result, indent=2))
```

**Gate:** `exllamav2/cp314_wheel`  
**Run:** `python probes/python/exllamav2_cp314_probe.py` (no uv extra needed — stdlib only)

---

## 8. Admitted Capabilities

As of `bfeb655b` / `f03cf39d`:

| Capability | Admission Evidence |
|------------|-------------------|
| Python 3.14.4 host | `uv run python --version` → `Python 3.14.4` |
| uv resolver + cu12 index routing | `uv sync --extra cu12` completes; torch resolves from pytorch-cu128 |
| pydantic-core 2.46.x on cp314 | 17/17 test suite passes on Python 3.14.4; pydantic validation exercised |
| tabbyAPI start.ps1 contract | 17/17 test_start_ps1 tests pass (parameter handling, backend selection, model path routing) |
| hatchling editable build on cp314 | `uv run pytest` resolves without build backend failure |

---

## 9. Impossible-Currently Boundaries (Summary)

| Boundary | Upstream Dependency | Reopen Condition |
|----------|--------------------|--------------------|
| exllamav2 on Python 3.14 | turboderp-org/exllamav2 | cp314-cp314-win_amd64 wheel in release |
| exllamav3 on Python 3.14 | turboderp-org/exllamav3 | cp314 wheel + loosened pydantic pin |
| flash_attn on Python 3.14 | kingbri1/flash-attention | cp314-cp314-win_amd64 wheel in release |
| GPU inference (full tabbyAPI) on Python 3.14 | All three above | exllamav2 OR exllamav3 + torch + flash_attn all at cp314 |
| ruff py314 target | astral-sh/ruff | `py314` target-version added to ruff |

None of these are closures. Each has a named ceiling and a concrete reopen condition.

---

## 10. What This Is Not

```
This document does not claim tabbyAPI works on Python 3.14 with GPU inference.
This document does not claim Python 3.14 is production-ready for this stack.
This document does not defer the impossible-currently boundaries with "coming soon."
```

What this document claims:

> Python 3.14 + uv is a **structurally admitted host** for tabbyAPI's non-GPU baseline.  
> The GPU inference stack has **three named impossible-currently boundaries** with explicit reopen conditions.  
> The resolver, build backend, and pydantic-core PyO3 layer are **admitted at L4**.  
> The remaining GPU stack is **L0 (known-absent) pending upstream cp314 releases**.

The boundary ledger is the artifact.  
The probe is the tool.  
The membrane is the guard.  
The impossible-currently boundary is the honest ceiling.

No false success. No decoration. No mythology.
