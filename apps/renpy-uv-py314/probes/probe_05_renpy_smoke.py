#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""Probe 05 - Phase 2 acceptance gate.

Verifies the lane-built Ren'Py 8.5.2 native runtime loads cleanly on
Python 3.14.4. Exercises a representative slice of the Cython .pyd files
across each subsystem (audio, gl2 renderer, pygame_sdl2 absorbed layer,
text shaping, display, encryption).

This is a load-only probe -- it imports modules without bootstrapping the
engine state machine. Full engine boot (renpy.bootstrap.bootstrap) needs
a project directory and a window; that's the next acceptance level.

Run:
    pwsh -NoProfile -Command ". scripts\Enter-RenPyBuildShell.ps1; uv run --project . probes\probe_05_renpy_smoke.py"
"""
from __future__ import annotations

import importlib
import sys
import os


# Representative subset of the 62 Cython .pyd modules we built. One module
# per subsystem so a single failure points cleanly at which layer broke.
MODULES = [
    # Core
    ("renpy",                       "Python package (no .pyd)"),
    ("_renpy",                      "core C extension (IMG_savepng, core.c)"),
    ("renpy.astsupport",            "Cython AST helpers"),
    ("renpy.cslots",                "Cython slot-class accelerator"),
    ("renpy.encryption",            "openssl ec_sign integration"),
    # Display + GL2 renderer (the part we want intact for Phase 3 Vulkan parallel)
    ("renpy.display.matrix",        "render-agnostic linear algebra"),
    ("renpy.display.render",        "scene graph rasterizer"),
    ("renpy.gl2.gl2draw",           "GL2 frame draw loop"),
    ("renpy.gl2.gl2mesh",           "GL2 mesh primitives"),
    ("renpy.gl2.gl2shader",         "GL2 shader compile/link"),
    ("renpy.gl2.gl2uniform",        "GL2 uniform binding"),
    ("renpy.gl2.assimp",            "assimp 3D model loader"),
    # Pygame_sdl2-absorbed layer
    ("renpy.pygame.error",          "SDL2 error wrapping"),
    ("renpy.pygame.display",        "SDL2 window/renderer"),
    ("renpy.pygame.surface",        "SDL2 surface ops"),
    ("renpy.pygame.image",          "SDL2_image, libpng, libjpeg-turbo"),
    # Text + Unicode
    ("renpy.text.textsupport",      "text layout primitives"),
    ("renpy.text.hbfont",           "harfbuzz + freetype font shaping"),
    ("renpy.text.bidi",             "fribidi bidirectional text"),
    # Audio (the ffmpeg-dependent module that drove the entire ffmpeg overlay-port detour)
    ("renpy.audio.renpysound",      "ffmpeg 8.1.1 + SDL2 audio mixer"),
    ("renpy.audio.filter",          "audio post-process filter"),
]


def main() -> int:
    print("=== Probe 05: Ren'Py native runtime smoke (Python {}) ===".format(
        sys.version.split()[0]))
    print()
    print(f"  RENPY_DEPS_INSTALL: {os.environ.get('RENPY_DEPS_INSTALL', '(unset)')}")
    print()

    ok = []
    fail = []
    for mod_name, desc in MODULES:
        try:
            m = importlib.import_module(mod_name)
        except Exception as exc:
            fail.append((mod_name, desc, type(exc).__name__, str(exc)[:160]))
            print(f"FAIL {mod_name:<35} {desc}")
            print(f"     -> {type(exc).__name__}: {exc}")
            continue
        # For .pyd-backed modules report the actual file path
        path = getattr(m, "__file__", "(no __file__)")
        if path and path != "(no __file__)":
            tag = ".pyd" if path.endswith(".pyd") else ".py"
            print(f"OK   {mod_name:<35} {tag} {desc}")
        else:
            print(f"OK   {mod_name:<35}      {desc}")
        ok.append(mod_name)

    print()
    print("=== Summary ===")
    print(f"  Loaded: {len(ok)} / {len(MODULES)}")
    if fail:
        print(f"  Failed: {len(fail)}")
        for mod_name, desc, et, msg in fail:
            print(f"    {mod_name}: {et}: {msg}")
        return 1

    print("PASS: Ren'Py native runtime loads on Python 3.14.4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
