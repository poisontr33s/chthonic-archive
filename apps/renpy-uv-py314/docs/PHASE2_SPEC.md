# Phase 2 Spec — Ren'Py source build on Python 3.14

Status: **planned** (Phase 1 must complete first).
Acceptance gate: a vanilla Ren'Py "The Question" demo project launches against the 3.14-built `renpy` binary and the `gl2` renderer initializes without errors.

## 2.1 Vendoring strategy

Submodule under `apps/renpy-uv-py314/vendor/renpy/`, pinned to **`8.5.2.26010301`** (the latest stable tag). `vendor/` is git-ignored at the lane level so the submodule reference lives only in `.gitmodules` of the chthonic-archive root, not in committed working copies of upstream Ren'Py code.

```
apps/renpy-uv-py314/
├── vcpkg.json                     # Phase 1
├── vendor/
│   └── renpy/                     # submodule pinned to 8.5.2.26010301
├── patches/
│   └── 0001-relax-python-pin.patch
├── scripts/
│   ├── Enter-RenPyBuildShell.ps1  # Phase 1 (already exists)
│   ├── apply-patches.ps1          # Phase 2 — applies patches/ to vendor/renpy
│   └── build-renpy.ps1            # Phase 2 — orchestrates full build
└── probes/
    └── probe_05_renpy_build.ps1   # Phase 2 acceptance gate
```

Submodule add command (run once, from chthonic-archive root):
```pwsh
git submodule add https://github.com/renpy/renpy.git apps/renpy-uv-py314/vendor/renpy
git -C apps/renpy-uv-py314/vendor/renpy checkout 8.5.2.26010301
```

## 2.2 Overlay patches (not direct edits)

The submodule stays unmodified. Patches in `patches/` are applied at build time and reverted on `git restore`. This keeps the lane shippable as a clean diff against upstream and makes future Ren'Py releases easy to track.

### Patch 0001 — relax python pin

```diff
--- a/pyproject.toml
+++ b/pyproject.toml
@@
-requires-python = "==3.12.*"
+requires-python = ">=3.12,<3.15"
```

That single line is the *entire* hard ceiling identified in the audit. After applying, Ren'Py's pyproject.toml allows installation against 3.14. If we hit Cython codegen issues we treat them as bug reports back to Cython upstream — they have explicit `Programming Language :: Python :: 3.14` classifier as of 3.2.4 so any failure is a regression, not a known limitation.

### Patch 0002 — skip renpysound when ffmpeg is absent (forced by Phase 1 ffmpeg waiver)

Phase 1 documented why ffmpeg cannot be installed at baseline `821100d96` (delisted MSYS2 package). Until that's resolved (overlay port or baseline bump), Phase 2 must build without `renpy.audio.renpysound`. The patch makes that Cython module conditional on libavformat being resolvable via pkg-config.

```diff
--- a/setup.py
+++ b/setup.py
@@
-    cython(
-        "renpy.audio.renpysound",
-        [ "src/renpysound_core.c", "src/ffmedia.c" ],
-        compile_args=[ "-Wno-deprecated-declarations" ] if ("RENPY_FFMPEG_NO_DEPRECATED_DECLARATIONS" in os.environ) else [ ],
-        packages="libavformat libavcodec libavutil libswresample libswscale sdl2")
+    # Phase 2 ffmpeg-optional: skip renpysound if libavformat isn't available
+    # via pkg-config. Audio falls back to SDL_mixer-only path. Re-enable by
+    # installing ffmpeg and rebuilding.
+    try:
+        setuplib.parse_cflags([ "pkg-config", "--cflags", "libavformat" ])
+        _has_ffmpeg = True
+    except Exception:
+        _has_ffmpeg = False
+
+    if _has_ffmpeg:
+        cython(
+            "renpy.audio.renpysound",
+            [ "src/renpysound_core.c", "src/ffmedia.c" ],
+            compile_args=[ "-Wno-deprecated-declarations" ] if ("RENPY_FFMPEG_NO_DEPRECATED_DECLARATIONS" in os.environ) else [ ],
+            packages="libavformat libavcodec libavutil libswresample libswscale sdl2")
+    else:
+        print("WARNING: renpy.audio.renpysound skipped (no libavformat). Audio falls back to SDL.", file=sys.stderr)
```

Acceptance change: in Phase 2's "The Question" smoke test, full audio playback is replaced with "engine boots and renders without crash on missing renpysound import" — Ren'Py's audio module is graceful about missing backends. If the import path of renpy.audio.audio assumes renpysound exists unconditionally, write `patch 0003-renpysound-import-guard.patch` as well.

### Patch candidates that may surface during Phase 2 build

These are **anticipated**, not pre-authored. We only write them if the build surfaces a real issue:

- **PEP 657 traceback fields**: 3.11+ added `co_qualname` etc. on code objects. Ren'Py's `renpy.execution` may use deprecated `co_lnotab`. If 3.14 finally removed it, write a forward-compat shim.
- **`ast` module changes**: Python 3.14 deprecates a few `ast.*` constants. Ren'Py's `renpy.ast` may need import updates.
- **Distutils removal**: Ren'Py 8.5.2 may still import `distutils` somewhere (the upstream pyproject.toml lists `setuptools` so likely already migrated, but we verify).
- **Cython-emitted code**: if any `.c` output references private CPython API that 3.14 changed, we patch the `.pyx` (not the generated `.c`).

Each survives or dies on its own merit; we don't pre-patch.

## 2.3 Build orchestration (`scripts/build-renpy.ps1`)

The build script does, in order:

1. Verify `Enter-RenPyBuildShell.ps1` was sourced (`cl.exe`, `pkgconf` on PATH).
2. Verify `vcpkg_installed/x64-windows/lib/pkgconfig/` has all 14 .pc files (run probe_04).
3. `git -C vendor/renpy reset --hard 8.5.2.26010301` (snap to clean state).
4. `git -C vendor/renpy apply ../../patches/0001-relax-python-pin.patch` (apply patch overlay).
5. `uv pip install -e vendor/renpy --no-build-isolation` from inside the lane's `.venv`.
   - `--no-build-isolation` is critical: build must use *our* venv's Cython 3.2.4 and the vcvars64-sourced MSVC, not a fresh build env vcpkg cannot reach.
6. Verify the install: `uv run python -c "import renpy; print(renpy.__version__)"`.
7. Verify Cython modules loaded: `uv run python -c "import renpy.gl2.gl2draw; import renpy.pygame.display; print('ok')"`.

## 2.4 Smoke test — "The Question"

Ren'Py ships a canonical demo project. After install, point Ren'Py's launcher at it and verify:

```pwsh
cd vendor/renpy
uv run python renpy.py the_question
```

`gl2` renderer initializes, window opens at the default resolution, the demo plays through the first scene and accepts input.

If the demo runs to completion: **Phase 2 passes**.

If `gl2` fails to initialize but the launcher loads: **partial pass** — the engine boots on 3.14, only the renderer surface needs Phase 3 attention sooner.

If the launcher fails to import: **Phase 2 fails** — root-cause the import error, write the appropriate patch, retry.

## 2.5 Failure-mode escape hatches

In priority order:

1. **Cython codegen issue under 3.14** → bisect to identify which `renpy.*` module breaks. File against Cython upstream with minimal repro. Workaround: pin Cython to master (likely fix lands fast) or fall back to 3.13.13 by editing `.python-version`.
2. **MSVC ABI mismatch** → vcpkg builds with MSVC 14.42, our build runs MSVC 14.42. `cl --version` should match. If a transitive vcpkg port pinned an older MSVC, bump triplet to `x64-windows-static-md` and rebuild.
3. **Native lib symbol mismatch** → ffmpeg ABI change between vcpkg's 6.1.1 and what Ren'Py's `renpysound_core.c` expects. Patch the `.c` file via `patches/0002-ffmpeg6-compat.patch` if needed; Ren'Py may already handle this since 8.5.x is recent.
4. **Submodule reachability** → `vendor/renpy/` is git-ignored at lane level but the submodule reference lives in repo root `.gitmodules`. CI/fresh checkout needs `git submodule update --init --recursive`.

## 2.6 What Phase 2 deliberately does NOT do

- No renderer changes. `renpy.gl2.*` keeps working as-is (or doesn't, in which case we surface the issue but don't fix it here).
- No NVIDIA/Vulkan integration. That's Phase 3.
- No installer/distribution work. We're building a working dev install, not a redistributable.
- No upstream PR. We collect the patch overlay first, validate it works, then *consider* upstreaming once it has soak time.

## 2.7 Time estimate

- Submodule add + patch authoring: **1 hour**
- First build attempt (likely surfaces 1–3 patches needed): **2–4 hours**
- Patch debug + retry cycles: **4–12 hours** depending on what surfaces
- "The Question" verification: **30 min**

Realistic target: a Phase-2-passing build within **1–2 working days** of focused effort, assuming Phase 1 install completes cleanly. Multiply by 2 if ffmpeg ABI surfaces patches.
