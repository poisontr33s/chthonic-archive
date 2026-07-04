# chthonic-cai

Gamified Copilot CLI companion. Wraps `gh copilot suggest/explain` with live XP tracking rendered via a crossterm TUI.

## Status

**Tier-1 verified (2026-06-28).** E2E passed: REPL loop → trail write → XP persist. All 6 dependencies at latest stable. No toxic prototyping markers in source.

## What it does

- Wraps `gh copilot suggest` (default) or `gh copilot explain` (`-e` flag).
- Targets: `shell`, `gh`, or `git` (`-t` flag, default: `shell`).
- Live XP prompt in the terminal title bar and input line: level, XP bar, session delta.
- Writes each query and each response as NDJSON trail events (same schema as `Add-TrailEvent` in the chthonic PowerShell profile).
- Persists XP state to `xp-state.json` in the parent of the trail directory.

## How XP works

Formula mirrors `chthonic-xp.ps1` exactly:

```
base XP: artifact=10, decision=8, diagnostic=5, memory=4, recovery=15, snapshot=3, meta=5
bonus: epoch-close=+45, git_commit=+5, wiring=+3
priority multiplier: p1=1.5×, p2=1.0×, p3/missing=0.75×
level = floor(sqrt(xp / 10))
```

Each cai query earns diagnostic (5) + artifact (10) = 15 base XP, multiplied by priority 0.75 = 12 XP per turn (at default priority 3).

## Install

```powershell
cargo install --path tools/chthonic-cai --bin cai
```

This puts `cai.exe` in `~/.cargo/bin/`, which is on PATH if Rust is installed.

## Usage

```powershell
# Suggest mode (default)
cai

# Explain mode
cai -e

# Target git instead of shell
cai -t git

# Override trail directory
cai --trail C:\path\to\trail

# Help
cai --help
```

## Terminal support

The TUI uses crossterm with ANSI/VT on Windows 10+. On Windows, the binary explicitly sets the console codepage to UTF-8 (65001) before the REPL loop so that box-drawing bar elements and Unicode render correctly in the console buffer.

## Source

- `src/main.rs` — REPL loop, gh copilot dispatch, crossterm TUI
- `src/xp.rs` — XP engine, level math, trail ingestion, state persistence
- `src/trail.rs` — NDJSON append writer

## Dependencies

| crate | version | latest stable |
|---|---|---|
| anyhow | 1.0.102 | 1.0.102 |
| clap | 4.6.1 | 4.6.1 |
| crossterm | 0.29.0 | 0.29.0 |
| serde | 1.0.228 | 1.0.228 |
| serde_json | 1.0.150 | 1.0.150 |
| chrono | 0.4.45 | 0.4.45 |

All dependencies pinned to latest stable as of 2026-06-28.
