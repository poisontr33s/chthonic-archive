# Ruby/ZJIT Devkit State — 2026-04-23

## Current rv state (rv 0.5.3)
- `.ruby-version` pins: `4.0.3-zjit`
- Installed: `ruby-4.0.3` (full) + `ruby-4.0.3-zjit` (bin-only stub)
- Active ruby: `ruby 4.0.3 (2026-04-21) +PRISM [x64-mingw-ucrt]`

## zjit install is a stub — CRITICAL GAP
- `ruby-4.0.3-zjit/` has ONLY `bin/` — no `lib/`, `include/`, `msys64/`, `share/`
- `rbconfig` fails to load (no stdlib)
- `prism` fails to load (no stdlib)
- RubyGems not loaded
- `ridk` not present (no MSYS2 devkit layer)

## Standard ruby-4.0.3 install is COMPLETE
Has: `bin/`, `include/`, `lib/`, `msys64/`, `packages/`, `ridk_use/`, `share/`, `LICENSE.txt`
- Has MSYS2 devkit (`msys64/`)
- Has ridk (MSYS2 devkit manager)
- Has Prism (built-in since Ruby 3.3, default parser in 4.0)

## ZJIT verification
- `ruby --zjit -e "puts 'zjit active'"` → works (just runs the stub exe)
- But the zjit binary has NO stdlib support — can't require anything

## What's needed for full zjit+devkit lane
Option A: rv installs zjit as a bare binary — need to symlink/copy stdlib from standard 4.0.3 OR
Option B: Use standard `ruby-4.0.3` (which has MSYS2) + `--zjit` flag (ZJIT is compiled into the binary regardless)
Option C: Build from source with full MSYS2 devkit under zjit variant

## rv ruby install surface (v0.5.3)
Commands: list, pin, dir, find, install, uninstall
- `rv ruby install` — installs pinned version
- No `list --available` (that flag doesn't exist)
- `rv r ridk` → ridk not found (only in standard install, not zjit stub)

## .toml state
- `rust-toolchain.toml` present
- `zig-toolchain.toml` present  
- `rproject.toml` present
- No ruby-specific pyproject-style toml (rv uses .ruby-version)

## Podman context
- User mentioned "version compiled via podman" — need to check for Dockerfile/podman files with ruby build context
