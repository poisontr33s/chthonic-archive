# renpy-uv-py314

Ren'Py 8.5.x → uv-managed Python 3.14.4 → RTX 4090 / Vulkan 1.4 build lane.

Architecture, ceiling analysis, and phased plan: [docs/PLAN.md](docs/PLAN.md).
Phase 2 specification: [docs/PHASE2_SPEC.md](docs/PHASE2_SPEC.md).
Initial empirical probe results: [docs/PROBE_RESULTS_2026_05_07.md](docs/PROBE_RESULTS_2026_05_07.md).

## Quickstart

```pwsh
# 0. From the lane root
Set-Location apps\renpy-uv-py314

# 1. Hydrate the uv environment (Python 3.14.4, Cython 3.2.4, etc.)
uv sync --group build --group probe

# 2. Verify the interpreter and Cython codegen work on 3.14
uv run probes/probe_01_environment.py
uv run --group build probes/probe_02_cython.py

# 3. Enter the build shell (sources MSVC vcvars64 + sets VCPKG_ROOT + PKG_CONFIG_PATH)
. .\scripts\Enter-RenPyBuildShell.ps1

# 4. Inventory native deps that vcpkg has provisioned so far
pwsh -NoProfile -File .\probes\probe_03_native_deps.ps1

# 5. Install Ren'Py's native deps via vcpkg manifest mode (long-running, 30–90 min)
.\scripts\install-native-deps.ps1 -KeepGoing

# 6. Watch progress in another shell while it runs
.\scripts\check-install-status.ps1 -Tail 12

# 7. Phase 1 acceptance gate (after install completes)
pwsh -NoProfile -File .\probes\probe_04_vcpkg_pkgconfig.ps1
```

## Decisions taken (no longer in question)

- **vcpkg manifest mode**, not MSYS2 — MSVC ABI clean for Python C extensions.
- **Reuse `C:\Users\eldno\vcpkg`** as `VCPKG_ROOT`, baseline pinned to `821100d96`.
- **Submodule** vendor for renpy at `vendor/renpy/` (git-ignored at lane level).
- **Python 3.14.4 only.** 3.13.13 stays as one-line escape hatch via `.python-version`.

## Known constraints

- Ren'Py master `pyproject.toml` pins `requires-python = "==3.12.*"` — single-line patch in `patches/0001-relax-python-pin.patch` (Phase 2).
- Ren'Py renderer is `renpy.gl2.*` (OpenGL only). No Vulkan/DLSS/DLAA/TensorRT exists upstream — Phase 3 adds `renpy.vk2.*` as a parallel namespace.
- Cython 3.2.4 has a real bug in its `cython_inline()` threadlocal init on 3.14. Doesn't affect Ren'Py (uses `cythonize()`), but it's a canary that 3.14 support is fresh.
