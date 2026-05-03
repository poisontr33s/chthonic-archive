# OpenSSL Investigation — 2026-04-21

## Critical Finding
- **PR #2591 "openssl 4 support" MERGED into rust-openssl master 3 days ago** (commit 1fc51ef)
- Added `Version::Openssl4xx`, const-qualified return types, `SSL_OP_IGNORE_UNEXPECTED_EOF`
- BUT: **No crates.io release yet** — latest is still openssl-sys 0.9.113 (2026-04-12)
- openssl-sys 0.9.113 does NOT support OpenSSL 4.0 (only bumped aws-lc-sys)

## System OpenSSL State
- `C:\Program Files\OpenSSL-Win64\` — 4.0.0 installed via winget
- 4 User env vars (OPENSSL_DIR, _LIB_DIR, _INCLUDE_DIR, _NO_VENDOR) — **REMOVED** in previous session
- Ruby rv bundled: OpenSSL 3.6.0 (rv\rubies\ruby-4.0.2\msys64)
- Git bundled: OpenSSL 3.5.5
- winget available: 3.6.2, 3.6.1, 3.6.0, 3.5.4, 4.0.0

## Universal Lane Options
1. **Install 3.6.2 via winget** — replaces 4.0.0 at same path, simplest for now
2. **vcpkg managed 3.x** — parallel to 4.0, controlled path
3. **Wait for openssl-sys 0.9.114** — imminent but unknown ETA
4. **Git patch openssl-sys** — fragile, temporary

## Decision
- The RIGHT lane: Install 3.6.2 to get immediate builds working
- When 0.9.114 releases with 4.0 support, can upgrade back
- entropy-ledger-host (Solana) is the only crate needing system OpenSSL
- Non-Solana workspace already builds clean without any OpenSSL

## Execution Plan (READY TO PRESENT)
### Recommended: winget downgrade 4.0.0 → 3.6.2
1. `winget install ShiningLight.OpenSSL --version 3.6.2 --force`
   - Installs to `C:\Program Files\OpenSSL-Win64\` (same path, overwrites 4.0.0)
2. Set User env var: `OPENSSL_DIR = C:\Program Files\OpenSSL-Win64`
3. Verify: `cd extensions/chthonic-archive/native && cargo check -p entropy-ledger-host`
4. Document in vulkan-lab/DEPENDENCY_UPDATE_PLAN.md

### Why this is the RIGHT universal lane:
- openssl-sys 0.9.113 (latest) supports 1.0.2 through 3.x ONLY
- OpenSSL 4.0.0 support merged to master (PR#2591, 3 days ago) but NOT released
- When openssl-sys 0.9.114 releases → can winget upgrade back to 4.0.0
- Ruby/rv has own bundled OpenSSL 3.6.0 (unaffected by system)
- Git has own bundled OpenSSL 3.5.5 (unaffected by system)
- VS 2026 Insiders doesn't bundle a standalone OpenSSL
- 3.6.2 is the latest 3.x LTS series — maximum compatibility

### Current env state:
- 4 User env vars REMOVED (OPENSSL_DIR, _LIB_DIR, _INCLUDE_DIR, _NO_VENDOR)
- CWD should be extensions/chthonic-archive/native/ for cargo checks
- Non-Solana cargo check already passes (verified in Branch C)
- Perl check was in-progress (needed for vendored option — secondary)

## Branch C Status (from previous sessions)
- Workspace: `extensions/chthonic-archive/native/`
- tokio 1.44→1.52, clap 4.5→4.6, shaderc 0.8→0.10, gix 0.71→0.79
- chthonic-daemon: reqwest 0.12→0.13, rustls-tls→rustls
- reactor.rs: shaderc API fix (ok_or_else→context)
- Non-Solana cargo check: CLEAN (0.89s)

## Remaining Branches After OpenSSL
- Branch D: ankh-forge clap 4.6.0→4.6.1, chthonic-cai crossterm 0.28→0.29
- Branch E: bincode decision gate (POISON PILL — do NOT upgrade to 3.0.0)
- Branch F: Solana/Anchor majors (defer)
- Branch G: Rust game engine research
