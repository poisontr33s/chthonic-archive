# Phase 2 Results — 2026-05-07

## Summary

**Phase 2 PASS.** Ren'Py 8.5.2 compiles, links, installs, and runs on uv-managed Python 3.14.4 + vcpkg-built native deps + MSVC 14.42 on Windows 11. The full lint pipeline (parser, compiler, validator, translation reporter) executes end-to-end against "The Question" demo project.

## Acceptance evidence

```
=== renpy.py the_question lint (with UTF-8 stdio) ===

The japanese translation contains 70 dialogue blocks, containing 71 words and
1,571 characters, for an average of 1.0 words and 22 characters per block.
[... 7 more translations reported ...]

The game contains 2 menus, 0 images, and 23 screens.

Lint is not a substitute for thorough testing. Remember to update Ren'Py
before releasing. New releases fix bugs and improve compatibility.
```

Exit code 0.

## Build artifacts

- 62 Cython `.pyd` files at `cp314-win_amd64` ABI in `vendor/renpy/renpy/**/*.pyd`
- One C extension `_renpy.cp314-win_amd64.pyd` at `vendor/renpy/`
- Editable install registered in lane venv (`uv pip list` shows `renpy 8.99.99 (editable: vendor/renpy)`)

## Patch series

7 patches, 282 LoC, all generated from real `git diff` against tag `8.5.2.26010301`:

```
patches/
├── 0001-relax-python-pin.patch          (pyproject.toml: requires-python relaxed)
├── 0002-setuplib-utf8-encoding.patch    (six open() calls -> encoding="utf-8")
├── 0003-windows-msvc-build-fixes.patch  (GCC->MSVC flags + vcpkg lib names + Win32 user32/shell32)
├── 0004-ffmedia-msvc-const-init.patch   (C2099 const-int initializer)
├── 0005-renpysound-msvc-vla-alloca.patch (C99 VLA -> _alloca on MSVC)
├── 0006-sdl-gfx-modern-msvc-lrint.patch (lrint shim gated on _MSC_VER < 1900)
└── 0007-init-add-dll-directory.patch   (os.add_dll_directory for vcpkg DLLs at runtime)
```

## Engineering observations

### Things that "just worked"

- Cython 3.2.4 lowering all 62 `.pyx` files to `.c` against Python 3.14 — no codegen issues. The probe 02 inline-bug we saw earlier never bit the production codepath.
- ffmpeg 8.1.1 ABI compatibility with Ren'Py 8.5.2's `ffmedia.c` — predicted as a major risk, surfaced as zero source patches needed beyond the C2099 const-init issue (which was unrelated to ffmpeg's ABI and would have hit any ffmpeg version).
- vcpkg overlay-port pattern combined with vcpkg-tool refresh — the architecture held cleanly. Old baseline (`821100d96`) keeps the rest of the install reproducible while ffmpeg-specific overlay sources from upstream HEAD.

### Things that surprised me

- **Windows DLL load on Python 3.8+**: Even with vcpkg's `bin/` on PATH and SDL2.dll resolvable via `Get-Command`, the `.pyd` couldn't find it at load time. Python 3.8+ explicitly excludes PATH from extension-module DLL search. Required `os.add_dll_directory()` registration. This is documented but easy to miss.
- **MSVC C99 VLA gap is still real in 2026**: `_MSC_VER` 1944 (VS 2022 17.12) still does not implement C99 variable-length arrays. Audio callback's runtime-sized stack arrays needed `_alloca` shim.
- **Console encoding mismatch survives every modernization**: PowerShell on Windows 11 still defaults to cp1252 for stdout. `print('﻿' + ...)` from `renpy.lint` killed the entire pipeline until `PYTHONIOENCODING=utf-8` was set. Documented gotcha for any Phase-3+ work that does Ren'Py output capture.
- **Ren'Py renders pygame_sdl2 absorbed in-tree**: My initial audit incorrectly called pygame_sdl2 a "barely-maintained outside fork." Reality (8.5.2): `renpy.pygame.*` is the namespace; the `renpy/pygame_sdl2` repo is now legacy. Phase 3 should target `renpy.pygame.display` for the Vulkan window-surface integration.

### What `-std=gnu99` warning means we did NOT do

setuplib unconditionally appends `-std=gnu99` to compile args. MSVC ignores it as `D9002`. The warning fires once per Cython module compiled (~40 times in our build). Harmless. Fixing requires either:
- Patch setuplib to drop the flag on Windows (easy)
- MSVC `/std:c11` (functional but mismatched semantically)

I chose to leave it as a non-blocker. Worth a patch 0008 if Phase 3 needs zero-warning builds, but it's not on the critical path.

## What this enables for Phase 3

Phase 3 (parallel `renpy.vk2.*` Vulkan renderer namespace) can now begin against a working 3.14 baseline. The `renpy.gl2.*` modules that will serve as the architectural template are all built and importable. The Vulkan SDK 1.4.341.1 is installed, glslc tested, vulkaninfo working, and the lane's RTX 4090 is the target GPU.

Phase 3 is not blocked on anything in Phase 1 or Phase 2.

## Reproducibility

From a fresh `chthonic-archive` checkout:

```pwsh
Set-Location apps\renpy-uv-py314
uv sync --group build --group probe
. .\scripts\Enter-RenPyBuildShell.ps1

# Phase 1 (one-time, ~30 min on first run, idempotent thereafter)
.\scripts\install-native-deps.ps1 -KeepGoing
pwsh -NoProfile -File .\probes\probe_04_vcpkg_pkgconfig.ps1   # expects 9/9 + 5/5 ffmpeg

# Phase 2 build
git -C vendor\renpy reset --hard 8.5.2.26010301
.\scripts\apply-patches.ps1
.\scripts\build-renpy.ps1 -SkipPatches

# Phase 2 acceptance
Set-Location vendor\renpy
$env:PYTHONIOENCODING = "utf-8"
uv run --project ..\.. python renpy.py the_question lint
```
