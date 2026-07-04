# Ren'Py on uv-managed Python 3.14.4 — Architecture & Phased Plan

Author: Claudine (Lysandra Thorne archetype, Truth-Chain) — 2026-05-07
Working directory: `apps/renpy-uv-py314/`

## 1. Audited ground truth (no speculation)

| Artifact | Verified state |
|---|---|
| Ren'Py latest stable | **8.5.2** (tag `8.5.2.26010301`, released 2026-01-04) |
| Ren'Py master version string | `8.99.99` (development) |
| Ren'Py `pyproject.toml` Python pin | **`requires-python = "==3.12.*"`** — the single hard ceiling |
| Cython use | In-tree, all native modules under `renpy.*` (gl2, pygame, text, audio, uguu, gl2.assimp, gl2.live2dmodel) |
| `pygame_sdl2` standalone fork | **Absorbed** into `renpy.pygame.*` namespace upstream. The `renpy/pygame_sdl2` repo is now legacy. |
| Renderer | SDL2 + OpenGL via `renpy.gl2.*`. **No Vulkan, no NGX/DLSS/DLAA, no TensorRT.** |
| Native C deps (pkg-config) | sdl2, SDL2_image, libpng, libjpeg, freetype2, harfbuzz, fribidi, libavformat, libavcodec, libavutil, libswresample, libswscale, openssl, assimp |
| Python 3.14 latest | **3.14.4** (released 2026-04-07, stable bugfix, EOL 2030-10) |
| Python 3.13 latest | 3.13.13 (stable; safer fallback if 3.14 surfaces blockers) |
| Cython latest | **3.2.4** (released 2026-01-04). Has explicit `Programming Language :: Python :: 3.14` classifier. |
| uv on this host | 0.11.8 (2026-04-27). Both 3.14.4 and 3.13.13 already installed. |
| Vulkan SDK on this host | **1.4.341.1** with glslc + vulkaninfo working |
| GPU | RTX 4090 (vulkaninfo dump archived at repo root: `VP_VULKANINFO_NVIDIA_GeForce_RTX_4090_596_21_0_0.json`) |

## 2. Empirical probe results (this host, 2026-05-07)

- **Probe 01 (env):** Python 3.14.4, MSC v.1944, GIL enabled, `Py_GIL_DISABLED=0`, `cp314-win_amd64` ABI tag. Standard build, not free-threaded.
- **Probe 02 (Cython):** `cythonize()` lowers a .pyx to a 320KB .c file successfully. `cython_inline()` crashes with a threadlocal init bug — not on the Ren'Py codepath, but a useful signal that 3.14 support is fresh.
- **Probe 03 (native deps):** All 14 pkg-config packages MISS. Ninja 1.13, CMake 4.3.2, git 2.54 are present. **MSVC `cl` not on PATH in this shell** — needs `vcvars64.bat` sourced or VS Developer PowerShell. Vulkan SDK + glslc + vulkaninfo all present. CUDA_PATH unset.

## 3. The ceiling, named precisely

There is **one** hard ceiling and **three** layered soft ceilings.

**Hard:** Ren'Py master pins `requires-python = "==3.12.*"`. That's a one-line patch upstream — but it's also a signal that 3.14 has not been validated by the maintainer.

**Soft 1 (Windows native deps):** No pkg-config-aware native dep manifest exists for Windows. Linux uses distro packages, macOS uses brew, but Windows builds Ren'Py from source rarely.

**Soft 2 (Renderer):** `renpy.gl2.*` is OpenGL-only. There is no Vulkan, NGX, DLSS, DLAA, or TensorRT integration anywhere in the engine. The 4090 runs as a fast OpenGL card.

**Soft 3 (Cython 3.14 freshness):** Cython 3.2.4 has the classifier but our probe surfaced a real inline-path bug. Production cythonize works; bug surface area on edge codepaths is unknown.

## 4. Gates-as-opportunities reframing

| Gate | Reframe |
|---|---|
| `requires-python = "==3.12.*"` pin | A one-line patch is a low-cost upstream contribution. Validating 3.14 cleanly = potential PR with measurable value to the Ren'Py community. |
| Windows native deps absent | **vcpkg** is the manifest-driven answer. A `vcpkg.json` declaring all 14 deps becomes the reproducible Windows-port artifact. This standardizes a missing piece of the Ren'Py-on-Windows-from-source story. |
| SDL2 + GL-only renderer | Ren'Py already has a pluggable renderer namespace (`gl2`, `uguu`). Add `renpy.vk2.*` as a **parallel** namespace, not a replacement. Reuse the `gl2mesh`/`gl2shader`/`gl2uniform` abstractions — they are renderer-agnostic in shape. |
| No NGX / DLSS / DLAA | DLSS3 + DLAA are render-target compositor passes. They plug in *after* a Vulkan path exists. Phase them after Phase 3, not blocking it. |
| No TensorRT | Orthogonal to the engine. Only matters if game logic does on-device ML inference. Decouple it. |
| Cython 3.2.4 inline bug | Free upstream contribution. Filing the repro is 30 minutes of work and earns a fix back. |

## 5. Phased execution plan

### Phase 0 — uv tooling lane (this commit) ✅

**Goal:** Stand up an isolated uv project at `apps/renpy-uv-py314/` that holds the build context and probes for Ren'Py-on-3.14, without modifying upstream Ren'Py at all. Probes prove what works on this host today.

**Deliverables (done):**
- `pyproject.toml` pinned `==3.14.*` with build/docs/dev/probe groups
- `.python-version` → 3.14.4
- `probes/probe_01_environment.py` — interpreter + ABI baseline
- `probes/probe_02_cython.py` — `cythonize()` smoke test on this Python
- `probes/probe_03_native_deps.ps1` — pkg-config + Vulkan SDK + tools inventory

**Run:** `uv sync --group build --group probe && uv run probes/probe_01_environment.py`

### Phase 1 — Reproducible Windows native-dep manifest ✅ PASS (with ffmpeg waiver)

**Acceptance gate result (2026-05-07):** `probe_04_vcpkg_pkgconfig.ps1` returned **PASS: 9 / 9 required**. ffmpeg's 5 .pc files (libavformat, libavcodec, libavutil, libswresample, libswscale) are formally waived — see addendum below.

**Installed versions (vcpkg manifest @ baseline 821100d96):**
- sdl2 2.30.5 · SDL2_image 2.8.2 · libpng 1.6.43 · libjpeg-turbo 3.0.3 · freetype2 26.1.20 · harfbuzz 9.0.0 · fribidi 1.0.13 · openssl 3.3.1 · assimp 5.4.1 · pkgconf 2.2.0 · zlib 1.3.1

**ffmpeg waiver — root cause and resolution path:**
At baseline `821100d96`, ffmpeg's vcpkg port calls `vcpkg_acquire_msys` to fetch `msys2-file-5.45-1-x86_64.pkg.tar.zst`. That specific MSYS2 package version has been delisted from every mirror (404 across mirror.msys2.org, repo.msys2.org, mirror.yandex.ru, mirrors.tuna.tsinghua.edu.cn, mirrors.ustc.edu.cn, mirror.selfnet.de). It's a *baseline staleness* gate, not a code issue.

Two fixes available, both deferred to Phase 1+:
1. **Bump vcpkg baseline** to a commit from late 2025 / early 2026 (current upstream HEAD: `6b07d2d37`). Lowest effort, but cascades version shifts to other ports — would force rebuild of everything we just installed.
2. **Overlay port** with a custom ffmpeg recipe pinned to a current MSYS2 set, in `vcpkg-overlay-ports/ffmpeg/`. Surgical, no other ports affected.

**Why not block Phase 1 on it:** ffmpeg is needed by exactly one Cython module in Ren'Py: `renpy.audio.renpysound`. Phase 2 patches Ren'Py's setup.py to skip that module if libavformat is absent — see PHASE2_SPEC.md §2.2 patch 0002. Audio playback degrades to silent/SDL-mixer fallback in the resulting build; everything else (rendering, text, scripting, Live2D, GL2 shaders) works untouched.

**Goal:** Make all 14 pkg-config packages available with consistent versions, in a way that a fresh checkout can rebuild from scratch.

**Stewardship decisions taken (no further user input required):**

- **vcpkg, manifest mode** for the lane (instead of MSYS2). Reason: MSVC ABI match for the Python C extensions Ren'Py builds. Lane manifest at `apps/renpy-uv-py314/vcpkg.json` is the single source of truth; install lands in `vcpkg_installed/x64-windows/` (lane-local, not the user's global `C:\Users\eldno\vcpkg\installed\`).
- **Reuse the existing `C:\Users\eldno\vcpkg`** as `VCPKG_ROOT` rather than bootstrapping a new clone. Pinned baseline: `821100d967e1737d96414a308e3f7cbe0d1abf18`.
- **Ren'Py vendoring via git submodule** (Phase 2 — when we get there) under `vendor/renpy/` with overlay patches in `patches/`.
- **Python 3.14.4 only**, no 3.13 fallback unless Cython codegen blocks. Probe 02 already shows `cythonize()` works on 3.14.

**Deliverables (committed):**
- `vcpkg.json` — 12 direct deps (pkgconf, zlib, libpng, libjpeg-turbo, freetype, fribidi, openssl, harfbuzz, sdl2, sdl2-image, assimp, ffmpeg). Default features only — port-version-specific feature names rejected at this baseline, defaults already cover what we need.
- `scripts/Enter-RenPyBuildShell.ps1` — sources `vcvars64.bat` (VS 2022 BuildTools at `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\...`), sets `VCPKG_ROOT`, `VCPKG_DEFAULT_TRIPLET=x64-windows`, and `PKG_CONFIG_PATH` to the lane's vcpkg-installed pkgconfig dir. Dot-source it: `. .\scripts\Enter-RenPyBuildShell.ps1`.
- `scripts/install-native-deps.ps1` — manifest-mode install runner. `-DryRun`, `-OnlyDownloads`, `-KeepGoing` flags.
- `scripts/check-install-status.ps1` — non-blocking status checker that walks `vcpkg_installed/x64-windows/lib/pkgconfig/` and reports which deps are present.
- `probes/probe_04_vcpkg_pkgconfig.ps1` — Phase 1 acceptance gate.

**Dry-run resolved (validated 2026-05-07):**

12 direct + 16 transitive = 28 packages. Direct (with versions vcpkg picked at the pinned baseline):

| Port | Version | Features |
|---|---|---|
| pkgconf | 2.2.0 | core |
| zlib | 1.3.1 | core |
| libpng | 1.6.43#2 | core |
| libjpeg-turbo | 3.0.3 | core |
| freetype | 2.13.2#1 | brotli, bzip2, **png**, **zlib** (defaults already include png+zlib) |
| fribidi | 1.0.13 | core |
| openssl | 3.3.1#1 | core |
| harfbuzz | 9.0.0 | **freetype** (default) |
| sdl2 | 2.30.5#1 | core |
| sdl2-image | 2.8.2#2 | core (PNG/JPEG already wired in core at this version) |
| assimp | 5.4.2 | core |
| ffmpeg | 6.1.1#11 | avcodec, avdevice, avfilter, avformat, swresample, swscale |

Transitive: brotli, bzip2, draco, jhasse-poly2tri, kubazip, minizip, polyclipping, pugixml, rapidjson, stb, utfcpp + 5 vcpkg helpers.

**Real install kicked off in background.** Logs streaming to `apps/renpy-uv-py314/vcpkg-install.log`. Expected duration on this 4090 host: 30–90 min, dominated by ffmpeg (last in the build order).

**Acceptance gate:** `pwsh -NoProfile -File probes/probe_04_vcpkg_pkgconfig.ps1` returns `PASS` with all 14 pkg-config names resolving.

**Risk surfaces still on the board:**
- Some transitive ports (e.g. `polyclipping` from sourceforge) have download mirrors that occasionally hiccup. `-KeepGoing` is set so a single port failure doesn't tank the whole install.
- ffmpeg compile is the long pole. If it fails, all the other deps are still installed and Phase 2 can attempt a build with a stub for the ffmpeg-dependent renpy modules (`renpy.audio.renpysound`).

### Phase 2 — Ren'Py source build on Python 3.14 ✅ PASS (twice: 8.5.2/3.14.4 and 8.5.3/3.14.5)

**Acceptance gate result (2026-05-07, Ren'Py 8.5.2 + Python 3.14.4):** The full Ren'Py compiler/parser/linter pipeline ran end-to-end on Python 3.14.4.

**Bump validated (2026-06-03, Ren'Py 8.5.3 + Python 3.14.5):** Of 7 patches, 6 apply byte-identical to 8.5.3; only patch 0001 needed a 4-character rewrite (`>=3.12.8,<3.13` → `>=3.12.8,<3.15`) since upstream itself moved the pin from `==3.12.*` to `>=3.12.8,<3.13` in commit "Restrict allowed Pythons to >= 3.12.8". 174 upstream commits land between 8.5.2 and 8.5.3 including urllib3 upgrade, audio/video improvements, focus/drag fixes, sphinx-tabs added as a dep. Full rebuild took 45.84s; `lint the_question` exits 0 with identical translation analysis output. Bump dependency `legacy-cgi 2.6.4` covers the entire PEP 594 stdlib-removal surface (single `import cgi` in `launcher/game/webserver.py:11`; nothing else in the codebase imports any other removed-stdlib module). `python renpy.py the_question lint` parsed all `.rpy` source, validated 70 dialogue blocks across 8 translations (japanese, korean, malay, russian, spanish, schinese, tchinese, ukrainian), analyzed 2 menus and 23 screens, and exited 0.

**62 Cython `.pyd` modules** built with `cp314-win_amd64` ABI tag covering: `_renpy`, `astsupport`, `cslots`, `style`, `encryption`, `lexersupport`, `pydict`, `tfd`, all `display.*` (matrix, render, accelerator, quaternion), all `gl2.*` (10 modules including `assimp`), all `pygame.*` (the absorbed pygame_sdl2 layer), all `text.*` (textsupport, hbfont with harfbuzz+freetype, bidi with fribidi, ftfont, texwrap), `audio.renpysound` (full ffmpeg 8.1.1 pipeline) and `audio.filter`, all `styledata.*` style accelerators, `uguu.*` GL helpers.

**Patches applied (7, 282 LoC total):**

| # | Patch | What |
|---|---|---|
| 0001 | `relax-python-pin.patch` | `pyproject.toml`: `requires-python` `==3.12.*` → `>=3.12,<3.15` |
| 0002 | `setuplib-utf8-encoding.patch` | `scripts/setuplib.py`: explicit `encoding="utf-8"` on six `open()` calls (Windows default cp1252 chokes on UTF-8 source content) |
| 0003 | `windows-msvc-build-fixes.patch` | `setup.py`: GCC→MSVC compile flags (`-Wno-unused-function` → `/wd4505`, drop `-fno-strict-aliasing`); POSIX→vcpkg lib names (`png`→`libpng16`, `z`→`zlib`, `assimp`→`assimp-vc143-mt`); add `user32` + `shell32` for Win32 dialogs |
| 0004 | `ffmedia-msvc-const-init.patch` | `src/ffmedia.c`: replace `const int FRAME_PADDING = ROW_ALIGNMENT / 4` with `#define`-derived constant (MSVC C2099: const int isn't a constant expr in C) |
| 0005 | `renpysound-msvc-vla-alloca.patch` | `src/renpysound_core.c`: C99 VLAs in audio callback → `_alloca` macro on MSVC, native VLA on GCC |
| 0006 | `sdl-gfx-modern-msvc-lrint.patch` | `src/pygame/SDL_gfxPrimitives.c`: gate `lrint` shim on `_MSC_VER < 1900` (modern MSVC ships intrinsic, redefining triggers C2169) |
| 0007 | `init-add-dll-directory.patch` | `renpy/__init__.py`: `os.add_dll_directory($RENPY_DEPS_INSTALL/bin)` so the cp314 `.pyd` files locate vcpkg's SDL2.dll, ffmpeg DLLs, freetype.dll etc. (Python 3.8+ no longer searches PATH for extension-module DLLs) |

**Boundary signals (warnings tolerated):**
- `cl: Command line warning D9002: ignoring unknown option '-std=gnu99'` — setuplib unconditionally passes `-std=gnu99`. Ignored by MSVC. Not worth a patch; fixing requires deeper setuplib refactor and the warning is harmless.
- Several `C4244 possible loss of data` warnings on `double`→`float` conversions in renpysound_core. Pre-existing in upstream code; not regressions.

**Build orchestration:**
- `scripts/Enter-RenPyBuildShell.ps1` is the entry: sources `vcvars64.bat`, sets `VCPKG_ROOT`/`VCPKG_DEFAULT_TRIPLET`, prepends vcpkg's `bin`/`tools/pkgconf` to `PATH`, prepends vcpkg's `include`/`include/SDL2`/`lib` to `INCLUDE`/`LIB`, sets `RENPY_DEPS_INSTALL`.
- `scripts/apply-patches.ps1` resets `vendor/renpy` to `8.5.2.26010301` and applies all `patches/*.patch` in lexical order with `git apply --check --3way`.
- `scripts/build-renpy.ps1` validates prereqs, computes `RENPY_CFLAGS`/`RENPY_LDFLAGS` via `pkgconf` (bypasses Ren'Py's literal `pkg-config` invocation), then runs `uv pip install -e .` against `vendor/renpy/` and runs the smoke test.

**Acceptance command (reproducible):**
```pwsh
Set-Location apps\renpy-uv-py314\vendor\renpy
. ..\..\scripts\Enter-RenPyBuildShell.ps1
$env:PYTHONIOENCODING = "utf-8"
uv run --project ..\.. python renpy.py the_question lint
# Expected: lint report ending "Lint is not a substitute for thorough testing."
```

**What we did NOT pretend:**
- The engine has not yet opened a window or rendered a frame on this build. `lint` is a non-graphical compiler/parser pass. Phase 3 prep would do an actual `python renpy.py the_question` and confirm the GL2 renderer initializes and the title screen renders. That's a one-command extension of Phase 2 once we want it.
- Audio playback isn't tested either — the `renpy.audio.renpysound` `.pyd` builds and links against ffmpeg 8.1.1, but actual mixing under load needs a real session. ffmpeg 8.1.1 vs Ren'Py 8.5.2's 5/6-era ffmedia.c compiled cleanly with patch 0004; a runtime ABI bug could still surface on first audio playback.
- No upstream PR yet. Reasonable next move (independent of Phase 3): submit patches 0001 + 0002 + 0006 to Ren'Py. Patches 0003/0004/0005/0007 are more invasive and worth soak time first.

**Goal:** Compile vanilla `renpy/renpy@master` against Python 3.14.4 with a one-line pyproject patch.

**Approach:**
1. `git submodule add` upstream `renpy/renpy` at 8.5.2 tag into `vendor/renpy/`.
2. Apply a single `requires-python = ">=3.12,<3.15"` patch via overlay (don't modify the submodule directly — keep it as a `patches/0001-relax-python-pin.patch` file).
3. Source vcvars64 via `Enter-VsDevShell` in an automated build script.
4. `uv pip install -e vendor/renpy/` from inside the lane's venv.
5. Run Ren'Py's own self-tests against the resulting build.

**Acceptance gate:** A canonical Ren'Py "The Question" demo project launches from the 3.14-built renpy and the gl2 renderer initializes without errors.

**Failure escape:** If 3.14-specific Cython codegen issues hit, fall back to 3.13.13 first (still ahead of upstream's 3.12 pin, lower risk surface). 3.13 → 3.14 retry once Cython 3.2.5+ ships.

### Phase 3 — Parallel Vulkan renderer namespace `renpy.vk2.*`

**Goal:** Add Vulkan as a sibling renderer to `renpy.gl2.*`, selectable at runtime via Ren'Py's existing `config.gl2` style preference.

**Approach (architectural, not "rip-and-replace"):**
1. Mirror `renpy.gl2.*` module structure into `renpy.vk2.*`: vk2draw, vk2texture, vk2mesh*, vk2polygon, vk2model, vk2shader, vk2uniform.
2. Reuse `renpy.display.matrix` (already renderer-agnostic) and the mesh/uniform/quaternion math.
3. Use `Vulkan-Hpp` from the SDK we already have at `C:\VulkanSDK\1.4.341.1`.
4. SDL2 has Vulkan window support via `SDL_Vulkan_CreateSurface` — no SDL2→SDL3 migration required for a first pass.
5. Compile shaders via `glslc` → SPIR-V at build time, embed via `xxd`-style bytes-includes.

**Acceptance gate:** `renpy.display.gl2.gl2draw` and `renpy.display.vk2.vk2draw` both render the same Ren'Py "The Question" scene with visually equivalent output. A/B switch via launcher flag.

**Why this is achievable from the gl2 starting point:** `renpy.gl2.gl2mesh`, `gl2shader`, `gl2uniform` are already renderer-API-thin abstractions. The shape of the abstraction is right; only the implementation calls Vulkan instead of GL.

### Phase 4 — NVIDIA RTX integrations (DLAA → DLSS3 → optional)

**Goal:** Layer DLAA and DLSS3 onto the vk2 renderer as a post-process pass.

**Approach:**
- Integrate **NGX SDK** (DLSS/DLAA) — separate download, requires NVIDIA developer signup.
- DLAA is the right entry point: anti-aliasing on native resolution. Cheap perceptual win on a 2D engine if the user runs at 4K.
- DLSS3 adds Frame Generation but is most valuable for sub-native-rendered 3D. For Ren'Py 2D it's marginal.

**Acceptance gate:** vk2 renderer has a configurable `dlaa = True` toggle that engages NGX DLAA on the framebuffer.

**Skip-criterion:** If the game stays purely 2D + Live2D, DLAA helps perceptually but DLSS/Frame-Gen does not. Decide per-project whether Phase 4 is worth the SDK integration.

### Phase 5 — TensorRT (decoupled track)

**Goal:** Only if the game performs on-device ML inference (e.g., voice synthesis, generative dialogue, learned NPC behavior).

**Approach:** TensorRT is a separate Python module loaded inside the game's Python script blocks. It does not touch the renderer. Use `tensorrt` Python wheels published on the NGC index.

**Note:** This phase is independent of phases 1–4 and can run in parallel with any of them.

## 6. Decision points before we proceed

Before Phase 1 starts, I need explicit go-aheads on three things:

1. **vcpkg vs MSYS2 for native deps?** vcpkg integrates cleanly with MSVC and CMake; MSYS2 is more Linux-flavored but mismatches MSVC ABI for embedding into a Python C extension. Recommendation: vcpkg. The lane's pyproject can stay clean-room standalone.
2. **Vendor renpy as submodule or as a `uv` source dep?** Submodule gives reproducible patches; uv source-dep gives cleaner dep graph. Recommendation: submodule under `vendor/renpy/`, `vendor/` git-ignored.
3. **3.14 only, or 3.13→3.14 stepped?** Recommendation: try 3.14 first because that's what you asked for. If we hit Cython codegen issues, the 3.13.13 escape hatch is one `.python-version` edit away.

## 7. What I will not pretend

- Phase 3 (Vulkan renderer) is a **multi-week** effort even with `gl2` as a template. Probably 200–400 hours of focused work for a competent graphics programmer. I will not call it a weekend project.
- Phase 4 (DLSS) on a 2D VN engine is mostly a marketing flex. DLAA is the part with real perceptual value. Be honest about that with yourself before committing time.
- Cython 3.2.4 is the *first* Cython release with formal 3.14 support. Bugs will surface. We will report them.

## 8. What this commit gives you

You can already inspect the boundary by running:

```pwsh
Set-Location C:\Users\eldno\chthonic-archive\apps\renpy-uv-py314
uv sync --group build --group probe
uv run probes/probe_01_environment.py
uv run --group build probes/probe_02_cython.py
pwsh -NoProfile -File probes/probe_03_native_deps.ps1
```

The first three probes establish what we're looking at. Phase 1 begins with `vcpkg.json` authoring once you confirm vcpkg as the answer to native-dep provisioning.
