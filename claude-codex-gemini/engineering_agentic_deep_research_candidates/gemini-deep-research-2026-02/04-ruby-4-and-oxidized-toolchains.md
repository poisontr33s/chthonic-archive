---
type: deep-research-output
source: claude-codex-gemini/sessionANDresearch.md (lines 1319-1538)
researcher: gemini-pro-3
created: 2026-02-12
topic: ruby-4-oxidized-toolchains
---

# Research 4: Ruby 4.0.x and Oxidized Toolchains on Windows 11

## Executive Summary

Ruby 4.0.1 (Jan 2026) brings ZJIT (Rust-based experimental JIT), Ruby Box isolation, and Ractor improvements. The ecosystem is being "oxidized" — rv (Rust Ruby manager inspired by uv), uutils coreutils, and brush (Rust bash shell). Win11 support is now first-class via Microsoft Store and winget.

## Ruby 4.0.1 Timeline

| Version | Date | Status |
|---------|------|--------|
| Ruby 4.0.0 | 2025-12-25 | Stable (30th anniversary release) |
| **Ruby 4.0.1** | 2026-01-13 | Current stable |
| Ruby 4.0.2 | 2026-03 (planned) | Upcoming |
| EOL | 2029-03-31 | 3-year support window |

## JIT Compilers: YJIT vs ZJIT

| Spec | YJIT (Stable) | ZJIT (Experimental) |
|------|--------------|-------------------|
| Language | C + Rust | **Pure Rust** |
| Compilation Unit | Basic Blocks | Methods |
| IR | Template-based | **SSA-based** |
| Enable Flag | `--yjit` | `--zjit` |
| Rust Requirement | — | Rust 1.85.0+ |
| Production Ready | ✅ Since 3.1 | Target: Ruby 4.1 |

ZJIT enables: global value numbering, register spilling, dead code elimination, method inlining, side-exits back to interpreter.

## Windows 11 Installation

```powershell
# Microsoft Store (no admin required)
# Available at: https://apps.microsoft.com/detail/xpfmdnmb4dq2wl

# Or via winget
winget install "Ruby 4.0"

# Includes: irb, gem, bundler, rake — auto-added to PATH
# MSYS2-Devkit still needed for C-extension gems
```

### RubyInstaller-4.0.1-1 Changes
- First-time support for MSYS2 **clang64** environment (LLVM toolchain)
- Removed legacy `libgcc_s_seh-1.dll`
- x64 and ARM64 ONLY — no more 32-bit

## rv: The Rust Ruby Manager (Like uv for Ruby)

| Feature | rv Capability |
|---------|-------------|
| Version Management | Replaces rbenv/rvm — installs in <1 second |
| Dependency Resolution | Replaces Bundler — `rv clean-install` |
| Tool Isolation | `rv tool install` — isolated envs per gem |
| One-off Execution | `rvx` — like npx for Ruby |
| Script Metadata | PEP 723-style inline deps in Ruby files |

- **Developer:** Spinel.coop (includes Bundler/RubyGems/rbenv maintainers)
- **Current:** v0.4.3 — macOS 14+ and Linux (glibc 2.35+)
- **Windows:** On roadmap, actively developing

## Oxidized Shell/Coreutils

### brush (Rust Bash Shell)
- Full POSIX + bash compatibility
- 1,400+ compatibility tests against bash
- Modern: syntax highlighting, auto-suggestions (via reedline)
- Async: tokio runtime for high concurrency
- **Win11 status:** Experimental (Linux/macOS primary)

### uutils coreutils (Rust GNU Replacement)
- Cross-platform Rust rewrite of GNU coreutils
- `tr` command: now faster than GNU (was 2.1x slower → now faster)
- Selected to replace GNU coreutils in Ubuntu 25.10
- **Win11 status:** Cross-platform ✅

## Ruby Box (Experimental)

Process-level isolation for Ruby code:
```ruby
# Enable: RUBY_BOX=1
box = Ruby::Box.new
# Classes, modules, global variables, monkey patches isolated within box
```

Use cases: blue-green testing, safe monkey patching, dependency conflict resolution.

## Ractor Updates (Concurrency)

- New `Ractor::Port` class replaces deprecated `Ractor.yield` / `Ractor#take`
- Lock-free hash sets for symbol table and frozen strings
- Per-Ractor allocation counters (reduces CPU cache contention)
- Moving closer to leaving experimental status

## Relevance to Chthonic Archive

| Feature | Impact on Our Stack |
|---------|-------------------|
| Ruby 4.0.1 via winget | Easy upgrade — `winget install "Ruby 4.0"` |
| ZJIT | Future perf gains for any Ruby scripts in repo |
| rv | When Win support lands, replaces our rbenv setup |
| uutils coreutils | Potential replacement for MSYS2 coreutils |
| brush | Future bash replacement on Win11 (when stable) |

**Priority: LOW** — Informational. Ruby is not a primary lane in the current overnight daemon pipeline, but good to know the ecosystem is modernizing rapidly.
