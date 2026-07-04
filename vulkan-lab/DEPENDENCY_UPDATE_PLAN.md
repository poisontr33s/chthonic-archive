# Dependency Update Plan — 2026-04-19

> Audited: 13 Cargo.toml files, 80+ crate entries, all toolchain components.
> Classification: 7 branches, ordered by risk and dependency chain.

---

## Branch A — Toolchain Updates (Safe, Independent) ✅ COMPLETE

**Risk:** LOW | **Effort:** 5 min | **Dependencies:** None

| Component | Previous | Actual | Method |
|-----------|----------|--------|--------|
| mise | 2026.3.12 | **2026.4.17** | `mise self-update` (was already current) |
| Rust stable | 1.94.1 | **1.95.0** | `rustup toolchain install 1.95.0` + bumped `rust-toolchain.toml` pin |

**Verified:** `cargo check` — clean build, 0 warnings, 24.6s on 1.95.0.
**Note:** `rustup upgrade` alone was insufficient — `rust-toolchain.toml` pinned `channel = "1.94.1"`. Pin updated to `"1.95.0"`.

### User-Performed Updates (2026-04-19) ✅

winget upgrade + rv — all non-VS-Installer packages brought to latest stable.

| Component | Version | Source | Notes |
|-----------|---------|--------|-------|
| Azure CLI | **2.85.0** | winget | `az version` confirmed |
| Bicep CLI | **0.42.1** | winget | `bicep --version` confirmed |
| Ruby (Full DevKit) | **4.0.2** +PRISM x64-mingw-ucrt | rv | Latest stable policy. Only installed version. |
| rv | **0.5.3** | — | Ruby version manager |
| Git | **2.53.0.windows.3** | winget | — |
| Python | **3.14.4** | winget/uv | — |
| uv | **0.11.6** | winget | Python package manager |
| Bun | **1.3.12** | winget | — |
| VS Installer trio | **11709.129** | VS Installer | VS Community + Build Tools 2026 Insiders. SSMS 22.5.0. |
| winget remaining | **0 upgrades pending** | `winget list --upgrade-available` | Clean sweep confirmed |

---

## Branch B — Root Cargo.toml Patch Bumps (Safe) ✅ COMPLETE

**Risk:** LOW | **Effort:** 1 min | **Dependencies:** Branch A
**File:** `Cargo.toml` (repo root)

| Crate | Previous | Actual | Breaking? |
|-------|----------|--------|-----------|
| tokio | 1.50 | **1.52** | No — bumped, resolves to 1.52.1 |
| winit | 0.30 | 0.30 | No (SemVer range already pulls 0.30.13) |
| bevy_ecs | 0.18 | 0.18 | No (SemVer range already pulls 0.18.1) |
| glam | 0.32 | 0.32 | No (SemVer range already pulls 0.32.1) |
| rand | 0.10 | 0.10 | No (SemVer range already pulls 0.10.1) |
| env_logger | 0.11 | 0.11 | No (SemVer range already pulls 0.11.10) |
| thiserror | 2.0 | 2.0 | No (SemVer range already pulls 2.0.18) |

**Verified:** `cargo check` — 0 warnings, 0.27s (cached).

---

## Branch C — Workspace Deps Harmonization (Medium Risk) ✅ COMPLETE

**Risk:** MEDIUM | **Effort:** 30 min | **Dependencies:** Branch A
**Files:** `extensions/chthonic-archive/native/Cargo.toml` (workspace root), `chthonic-daemon/Cargo.toml`, `chthonic-daemon/src/reactor.rs`

| Crate | Previous | Actual | Breaking? | Fix |
|-------|----------|--------|-----------|-----|
| tokio | 1.44 | **1.52** | No | — |
| clap | 4.5 | **4.6** | No | — |
| shaderc | 0.8 | **0.10** | **Yes** | `Compiler::new()` / `CompileOptions::new()` return `Result` not `Option` → replaced `.ok_or_else()` with `.context()` in reactor.rs |
| reqwest | 0.12 | **0.13** | **Yes** | Feature `rustls-tls` renamed to `rustls` in 0.13 → updated Cargo.toml |
| gix | 0.71 | **0.79** | No | 0.81 blocked: gix-hash 0.23.0 has non-exhaustive match errors on Rust 1.95.0. Parked at 0.79. |

**Verified:** `cargo check -p chthonic-daemon -p tensor-runtime-host -p chthonic-synapse-schema -p synapse-node -p xtask` — 0 errors, 0.89s.

### OpenSSL 4.0.0 Forward-Fix ✅ RESOLVED (2026-04-19)

- `C:\Program Files\OpenSSL-Win64` contains **OpenSSL 4.0.0** (released 2026-04-14).
- `openssl-sys` v0.9.113 (crates.io) only supports OpenSSL 1.1.0, 1.1.1, or 3.x.
- This broke **`entropy-ledger-host`** (Solana SDK → secp256r1 → openssl).
- **Not caused by Branch C.** Solana was already broken against OpenSSL 4.0.0.

**Resolution applied — git patch from upstream master:**

PR [rust-openssl#2591](https://github.com/sfackler/rust-openssl/pull/2591) ("openssl 4 support") merged 2026-04-16 but not yet released to crates.io.

1. **`[patch.crates-io]`** in `extensions/chthonic-archive/native/Cargo.toml`:
   - `openssl`, `openssl-sys` → `git = "https://github.com/rust-openssl/rust-openssl.git", branch = "master"` (commit `0b41e793`)
   - Resolves: openssl 0.10.77, openssl-sys 0.9.113, openssl-macros 0.1.1 (all from git)
   - openssl-sys build script confirmed: `version: 4_0_0`, cfg flags `ossl340`, `ossl350`
2. **MSVC linker pin** in `.cargo/config.toml`:
   - Ruby rv's MSYS2 `link.exe` (Unix hardlink utility) shadowed MSVC `link.exe` on PATH
   - Pinned `[target.x86_64-pc-windows-msvc] linker` to MSVC 14.51.36231
3. **OPENSSL env vars** (User scope):
   - `OPENSSL_DIR=C:\Program Files\OpenSSL-Win64`
   - `OPENSSL_LIB_DIR=C:\Program Files\OpenSSL-Win64\lib\VC\x64\MD`
   - `OPENSSL_INCLUDE_DIR=C:\Program Files\OpenSSL-Win64\include`

**Verified:** `cargo check -p entropy-ledger-host -p chthonic-daemon -p tensor-runtime-host -p xtask` — 0 errors, 5.85s.

**TODO:** Remove `[patch.crates-io]` block once `openssl-sys ≥ 0.9.114` ships with native OpenSSL 4.0 support on crates.io.

---

## Branch D — Tool Crate Updates (Low Risk, Independent)

**Risk:** LOW | **Effort:** 10 min | **Dependencies:** Branch A
**Files:** `tools/ankh-forge/Cargo.toml`, `tools/chthonic-cai/Cargo.toml`

| Crate | File | Current | Target | Notes |
|-------|------|---------|--------|-------|
| clap | ankh-forge | 4.6.0 | 4.6.1 | Patch bump |
| clap | chthonic-cai | "4" | "4" | Already using SemVer range |
| crossterm | chthonic-cai | 0.28 | 0.29 | Minor bump — check terminal API changes |

**Action:** Bump ankh-forge clap to 4.6.1. Bump chthonic-cai crossterm to 0.29.
**Verify:** `cargo check` in each tool directory.

---

## Branch E — bincode Migration (CRITICAL)

**Risk:** HIGH | **Effort:** 2-4 hours | **Dependencies:** None (architectural)

### Situation
- **bincode is unmaintained.** v3.0.0 on crates.io is a tombstone release containing only a compiler error.
- Development ceased due to doxxing/harassment incident.
- ankh-forge uses bincode 2.0 for REM wire format (StoneEvent encoding in `trail/granite.rs`).
- The REM hash scheme (`SHA-256` of `[zeroed_header ++ schema ++ spirv ++ payload_compressed]`) depends on bincode 2.0 serialization.

### Migration Candidates (recommended by bincode maintainer)

| Crate | Compatibility | Tradeoff |
|-------|--------------|----------|
| **wincode** | Bincode-compatible fork | Drop-in replacement, lowest migration cost |
| **postcard** | Similar spirit, different wire format | Requires re-encoding all existing stones |
| **rkyv** | Zero-copy deserialization | Best performance, largest API change |

### Recommended Path
1. **Evaluate wincode first** — if it's a true drop-in, wire format stays unchanged.
2. If wincode is insufficient, evaluate postcard with a versioned stone format (v2 header flag).
3. rkyv only if building new stone format from scratch.

**Decision required before action.** This affects the REM specification.

---

## Branch F — Solana / Anchor Major Upgrades (HIGH Risk)

**Risk:** VERY HIGH | **Effort:** 8-16 hours | **Dependencies:** None (self-contained)

| Crate | Current | Target | Delta |
|-------|---------|--------|-------|
| solana-sdk | 2.3.1 | 4.0.1 | **2 major versions** |
| anchor-lang | 0.32.1 | 1.0.0 | **Major version (0.x → 1.0)** |
| anchor-client | 0.32.1 | 1.0.0 | Same |

### Assessment Required
- Solana SDK 4.0 is a full API restructure — not a bump.
- Anchor 1.0.0 hit stable after years in 0.x — likely significant API changes.
- These crates are in the workspace (`extensions/chthonic-archive/native/`) but the Solana chain RPG components may not be actively compiled.

### Recommended Path
1. Assess which workspace members actually depend on solana-sdk/anchor-lang.
2. If those members are dormant, defer the upgrade.
3. If active, create dedicated branch with integration tests.

---

## Branch G — Rust Game Engine Research (NEW)

**Risk:** N/A (research only) | **Effort:** 2-4 hours

**Objective:** Find a Rust game engine that:
- Integrates with VS Code Insiders (similar to Unity/Godot editor plugins)
- Supports Vulkan rendering
- Allows programmatic sideloading/hot-reload

### Top Candidates to Evaluate
1. **Bevy** — ECS-first, Vulkan via wgpu, hot-reload in progress, VS Code extension exists (`bevy_vscode`), most active Rust game engine ecosystem
2. **Fyrox** — Scene editor (like Godot), Vulkan support, less mainstream
3. **Ambient** — Wasm-first runtime, multiplayer-focused
4. **Macroquad/Miniquad** — Lightweight, less editor support

### Evaluation Criteria
- VS Code Insiders integration depth
- Vulkan backend quality (ash/wgpu/raw)
- Hot-reload / live-coding support
- ECS compatibility with existing `bevy_ecs 0.18` in root Cargo.toml

---

## Execution Order (Choose Your Path)

```
A ─→ B ─→ (safe ground)
 ╲
  └→ C ─→ D ─→ (workspace aligned)
                 ╲
                  └→ E (bincode decision gate)

F ─→ (independent, park if dormant)
G ─→ (independent, research lane)
```

**Recommended sequence:** A → B → D → C → E → (F if needed) → G

- **A** clears toolchain debt (5 min).
- **B** aligns root deps (10 min).
- **D** aligns tools (10 min, can parallel with B).
- **C** is the real work — workspace harmonization (30 min).
- **E** is a decision gate, not a sprint.
- **F** is deferred unless Solana members are active.
- **G** is a separate research thread.
