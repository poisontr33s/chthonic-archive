# Probe Results — 2026-05-07 (initial Phase 0 snapshot)

Host: Windows 11 Pro N (10.0.26200), AMD64, RTX 4090 + Vulkan SDK 1.4.341.1.

## Probe 01 — environment

```
sys.version          : 3.14.4 (main, Apr  7 2026, 20:48:46) [MSC v.1944 64 bit (AMD64)]
sys.implementation   : cpython sys.version_info(major=3, minor=14, micro=4, releaselevel='final', serial=0)
sys.platform         : win32
GIL disabled         : False (Py_GIL_DISABLED=0)
sysconfig EXT_SUFFIX : .cp314-win_amd64.pyd
sysconfig SOABI      : cp314-win_amd64
```

Standard non-free-threaded build. ABI tag `cp314-win_amd64` matches what wheels need.

Build context (`VCToolsInstallDir`, `WindowsSDKVersion`, `INCLUDE`, `LIB`) all unset in the regular pwsh shell. Phase 2's build script must enter VS Developer PowerShell or invoke `vcvars64.bat` programmatically.

## Probe 02 — Cython

```
Cython version       : 3.2.4
cythonize modules    : 1
emitted C file       : probe.c (319,495 bytes)
PASS: Cython 3.2.4 lowers .pyx -> .c on Python 3.14
```

`cythonize()` codepath (the one Ren'Py uses) is functional.

`Cython.Build.Inline.cython_inline()` crashes on 3.14 with `AttributeError: '_thread._local' object has no attribute 'cython_errors_listing_file'` from `Cython/Compiler/Errors.py:226`. Not on the Ren'Py codepath but is an upstream bug worth filing — it indicates Cython's threadlocal initialization is incomplete on the warning path under 3.14.

## Probe 03 — native deps + GPU toolchain

```
-- Build tools --
MISS   pkg-config
MISS   cl
MISS   clang
MISS   gcc
OK     ninja  (1.13.0.git.kitware.jobserver-pipe-1)
OK     cmake  (4.3.2)
OK     git    (2.54.0.windows.1)
OK     uv     (0.11.8 (0e961dd9a 2026-04-27 x86_64-pc-windows-msvc))

-- Ren'Py native deps via pkg-config --
ALL 14 packages: SKIP (pkg-config not on PATH; vcpkg path not yet authored)

-- Vulkan SDK / NVIDIA toolchain --
OK     VULKAN_SDK = C:\VulkanSDK\1.4.341.1
OK     glslc      (shaderc v2026.1)
OK     vulkaninfo
MISS   CUDA_PATH env var
OK     NVIDIA App present
```

Phase 1 must address: pkg-config + 14 native libs. Recommended path: vcpkg manifest under `apps/renpy-uv-py314/vcpkg.json`.

Phase 3+ surface: Vulkan SDK 1.4.341.1 is current and ready. shaderc is configured. `vulkaninfo.exe` runs. SPIR-V compilation pipeline is unblocked.

## Phase 0 verdict

Reachable today, no engineering required:
- Python 3.14.4 ✅
- Cython 3.2.4 cythonize ✅
- uv resolver + venv ✅
- Vulkan SDK + glslc ✅

Engineering needed for Phase 1+:
- Native deps via vcpkg
- VS Developer PowerShell entry for actual C compile
- Upstream patch to `requires-python`
