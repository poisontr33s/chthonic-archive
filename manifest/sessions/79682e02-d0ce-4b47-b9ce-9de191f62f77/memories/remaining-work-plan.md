# Remaining Work Plan — 2026-04-19

## Completed
- ✅ Session memory created with full dep audit (dep-audit-2026-04-19.md)
- ✅ memory.md: Verified Outputs, Decision Log, Open Work ALL updated
- ✅ CLAUDE.md: Toolchain table updated (mise 2026.4.17, Rust 1.95.0, VS Installer 11709.129)
- ✅ DEPENDENCY_UPDATE_PLAN.md created with 7 branches (A-G)
- ✅ bincode-unmaintained stored to repo memory
- ✅ **Branch A COMPLETE**: mise 2026.4.17 (was current), Rust 1.94.1→1.95.0 (rust-toolchain.toml pin bumped), cargo check clean
- ✅ **Branch A User Updates**: winget fully current (0 pending), az 2.85.0, bicep 0.42.1, ruby 4.0.2+PRISM via rv 0.5.3, git 2.53.0, python 3.14.4, uv 0.11.6, bun 1.3.12, VS trio 11709.129
- ✅ **Branch B COMPLETE**: Root Cargo.toml tokio 1.50→1.52, cargo check clean (0.27s cached)

## Remaining Branches
- Branch C: Workspace deps (extensions/chthonic-archive/native/Cargo.toml) — tokio 1.44→1.52, shaderc 0.8→0.10, clap 4.5→4.6, reqwest 0.12→0.13, gix 0.71→0.81
- Branch D: Tool crates — ankh-forge clap 4.6.0→4.6.1, chthonic-cai crossterm 0.28→0.29
- Branch E: bincode migration (CRITICAL) — 2.0 unmaintained, evaluate wincode/postcard/rkyv
- Branch F: Solana/Anchor major upgrades — solana-sdk 2.3.1→4.0.1, anchor-lang 0.32.1→1.0.0
- Branch G: Rust game engine research

## Key Facts for Updates

### Decision Log entries to add:
| 2026-04-19 | Full dependency audit (13 Cargo.toml files, 80+ crates) | Audit-before-update discipline. Version divergences identified across 4 cross-Cargo.toml pairs. bincode found unmaintained — architectural impact on REM wire format. |
| 2026-04-19 | VS Installer trio updated (11612.153 → 11709.129) | SSMS 22.5.0, VS Community + Build Tools 2026 Insiders. .vsconfig exports at |

### CLAUDE.md toolchain updates needed:
- mise row: change "2026.3.12" → "2026.3.12 → update to 2026.4.17 pending"
- Rust row: add "(1.94.1 installed, 1.95.0 available)"

### Branching Plan Structure:
Branch A: Toolchain — mise self-update + rustup update stable
Branch B: Root Cargo.toml — bump winit/bevy_ecs/tokio/etc to latest patch
Branch C: Workspace deps (extensions/native) — tokio, shaderc, clap, reqwest, gix
Branch D: Tools deps — crossterm, clap normalization
Branch E: bincode migration (CRITICAL) — switch to wincode/postcard/rkyv (impacts REM wire format)
Branch F: Solana/Anchor major upgrades — 2.x→4.x / 0.32→1.0
Branch G: Rust game engine research — Bevy (full engine, VS Code extension exists) vs alternatives

### CRITICAL FINDING: bincode UNMAINTAINED
- v3.0.0 is tombstone (compiler error only)
- Workspace uses bincode 2.0 in: ankh-forge trail/granite.rs
- StoneEvent is the bincode wire type for REM .runestone format
- Hash scheme: SHA-256 of [zeroed_header ++ schema ++ spirv ++ payload_compressed]
- Migration would need to preserve wire compatibility or version the stone format
