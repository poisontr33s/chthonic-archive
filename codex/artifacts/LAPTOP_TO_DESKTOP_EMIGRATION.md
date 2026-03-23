---
type: runbook
category: migration
created: 2026-03-23
status: active
---

# Laptop to Desktop Emigration

## Purpose

This is the distilled workstation-emigration playbook from the 2026-03-22 to 2026-03-23 recovery and standardization pass.

It exists to preserve:
- the order that worked
- the dead ends that wasted time
- the exact lane repairs that turned the host verifier green
- the sequence to reuse on the next machine without rediscovering the same failures

## Current Winning State

As of 2026-03-23, the desktop host is aligned enough that the archive host verifier reports green for:
- Rust
- Ruby
- Go
- JavaScript
- Solana
- Anchor
- WASM
- SQL / infra lane detection

Environment repairs that matter:
- PowerShell 7.6.0 is the active shell lane
- Ruby is standardized on `rv` `ruby-4.0.2`
- `brush` is usable on Windows with repo/global compatibility rescue
- Go is standardized through `goup`
- `mise` is standardized through Cargo ownership
- native MSVC + Vulkan + CUDA stack is callable
- `OpenSSL` is bound for MSVC cargo builds
- `solana`, `agave-install`, `avm`, and `anchor` are visible in fresh shells
- `R 4.5.3`, `Rscript`, `rv-r 0.19.0`, `zv 0.9.2`, and `zig 0.15.2` are visible in fresh shells

## Canonical Order

Do the migration in this order.

### 1. Stabilize the shell first

- Get PowerShell onto one active lane before touching language managers.
- Remove split-brain launcher state before trusting terminal behavior.
- Prefer one canonical `pwsh` path and make VS Code / Windows Terminal follow it.

### 2. Normalize Ruby before anything that depends on MSYS2

- Install one Ruby under `rv`.
- Pin one version.
- Rebuild DevKit in sequence:
  - `rv r ridk install 1`
  - `rv r ridk install 3`
- Treat old `C:\Ruby*` trees as salvage only, not runtime dependencies.

### 3. Repair command visibility in raw shells

- Do not trust profile-only activation if repo verifiers run in bare non-profile shells.
- Make `ruby`, `ridk`, `gcc`, `make`, and `pacman` resolve from the active `rv` lane in user `PATH`.
- Keep the PowerShell profile helper, but do not rely on it as the only path repair.

### 4. Fix brush after Ruby, not before

- `brush` on Windows is not pure bash and not pure POSIX.
- First ensure `MSYS2_HOME` points at the active `rv` DevKit tree.
- Then restore `PATH` from Windows `Path` and alias `bash` / `sh` to the MSYS2 executables.

### 5. Bind graphics / native build surfaces

- Verify MSVC, Vulkan SDK, `glslc`, `dxc`, CUDA, and TensorRT/cuDNN before chasing renderer bugs.
- Expose the host stack through repo tasks and scripts so the machine state is callable, not implicit.

### 6. Repair native crypto before blaming Cargo

- If `openssl-sys` fails on MSVC, do not assume Visual Studio solved it.
- Bind a real Windows OpenSSL installation and persist:
  - `OPENSSL_DIR`
  - `OPENSSL_INCLUDE_DIR`
  - `OPENSSL_LIB_DIR`
  - `OPENSSL_NO_VENDOR=1`
- Keep `VCPKG_ROOT` valid, but do not assume vcpkg alone will save the lane.

### 7. Install Solana / Anchor after OpenSSL

- The official Agave installer wanted elevation in this session.
- The non-admin winning path was the official prebuilt Windows Agave bundle extracted into a user-scoped path.
- Install `avm`, then `avm install latest`, then `avm use latest`.
- Persist both the Agave bundle `bin` and `.avm\bin` into user `PATH`.

### 8. Run the repo verifier only after all path-sensitive lanes are persisted

- Verify with a fresh environment merge, not a profile-inflated shell only.
- If the verifier is red, fix the lane, then rerun immediately.

### 9. Expose the repaired state through the control surface

- Add high-level `chthonic` commands for:
  - toolchain hierarchy
  - host verification
  - migration/session memory recall
  - R lane
  - Zig lane
- Keep `claudine` as the compatibility wrapper, but make it advertise the same strategic surfaces.

## What Worked

- Using `rv` as the single Ruby owner and quarantining/purging old `C:\Ruby*` state.
- Rebuilding DevKit one stage at a time instead of `1 2 3` in one shot.
- Making raw user `PATH` reflect the active Ruby, not just the PowerShell profile.
- Treating `brush` as a Windows hybrid shell that needs explicit `PATH` and `bash` rescue.
- Installing `OpenSSL 3.6.1 (64-bit)` for Windows and binding Cargo to it with user env vars.
- Using the official Agave release bundle directly when the admin installer path was blocked.
- Letting `avm` fall back from symlink to copy on Windows when symlink privileges were absent.
- Standardizing `mise` to Cargo ownership after confirming both Cargo and WinGet lanes existed.
- Removing `.avm\bin` from user `PATH` so Windows stops preferring the extensionless `avm` file over `avm.exe`.
- Keeping the R runtime current as unmanaged while centering `rv-r` as the first-class R package lane.
- Verifying every lane immediately after mutation instead of trusting install output.
- Surfacing the winning state through `chthonic toolchain ...` and `chthonic memory ...` instead of relying on chat recall.

## Do Not Repeat

- Do not assume Visual Studio or VS Installer automatically provisions a usable `OpenSSL` lane for Cargo.
- Do not rely on Cygwin/MSYS Perl to build vendored OpenSSL for MSVC Rust crates.
- Do not leave stale `C:\Ruby*` or old `rv` quarantine paths in `PATH`.
- Do not rely on profile-only shell mutation if repo verifiers execute in non-profile shells.
- Do not treat `brush --posix` as a real pure-POSIX guarantee on Windows.
- Do not use `goup update go`, `goup install go`, or similar fake verbs; they are parsed as versions and fail.
- Do not expect the official Agave Windows installer to succeed unelevated through restricted automation lanes.
- Do not stop at “tool installed” if `where.exe <tool>` still fails in a fresh shell.
- Do not keep duplicate ownership of the same manager when one lane already wins cleanly (`mise` cargo vs WinGet was resolved in favor of Cargo here).
- Do not leave extensionless `avm` ahead of `avm.exe` in user `PATH`; on this host that produced the Win11 “choose app to open avm” dialog.
- Do not assume `R` in PowerShell refers to the R runtime; it collides with `Invoke-History` unless the shell or wrapper lane repairs it.

## Recovery Patterns

### If Ruby works only in profile-loaded shells

- Persist the active `rv` Ruby bin and `msys64` bins into user `PATH`.
- Then rerun `ruby --version` and `ridk version` in a fresh non-profile shell.

### If `entropy-ledger-host` fails on `openssl-sys`

- Install a real Windows OpenSSL dev package.
- Point Cargo at the MSVC import libs under the OpenSSL install.
- Verify with `cargo check -p entropy-ledger-host` before touching code.

### If Agave installer demands admin

- Use the official prebuilt Windows release bundle.
- Extract it to a user-scoped release directory.
- Add its `bin` to user `PATH`.
- Verify `solana --version` and `agave-install --version`.

### If `avm` cannot symlink on Windows

- Copy fallback is acceptable.
- What matters is `anchor --version` resolving in a fresh shell afterward.

### If `avm` opens the Win11 "choose app" dialog

- Check `where.exe avm`.
- If an extensionless file under `.avm\bin\avm` is shadowing `.cargo\bin\avm.exe`, remove `.avm\bin` from user `PATH`.
- Keep `.cargo\bin\avm.exe` as the canonical command owner.

### If `R` exists but PowerShell still treats it as history

- `R` collides with `Invoke-History` in PowerShell.
- Prefer:
  - `Rscript --version`
  - explicit `R.exe`
  - `chthonic env` / profile lane to apply the alias repair

## Verification Set

Run these in a fresh non-profile shell after a migration:

```powershell
pwsh --version
where.exe ruby
ruby --version
ridk version
Rscript --version
pwsh -NoProfile -File scripts/rv-r.ps1 --version
where.exe zig
zig version
where.exe go
go version
where.exe solana
solana --version
where.exe agave-install
agave-install --version
where.exe avm
where.exe anchor
anchor --version
cargo check --workspace
cargo check --manifest-path extensions/chthonic-archive/native/Cargo.toml
bun run scripts/verify-host.ts
```

## Chthonic Control Surface

These commands are the durable recall layer for the repaired workstation:

```powershell
.\scripts\chthonic.ps1 toolchain hierarchy
.\scripts\chthonic.ps1 toolchain verify
.\scripts\chthonic.ps1 toolchain scan --json
.\scripts\chthonic.ps1 toolchain paths
.\scripts\chthonic.ps1 memory map
.\scripts\chthonic.ps1 memory migration
.\scripts\chthonic.ps1 memory session
```

Compatibility wrapper:

```powershell
.\scripts\claudine.ps1 toolchain hierarchy
.\scripts\claudine.ps1 memory session
```

## Strategic Next Steps

Once the host is green, the next hierarchy is:

1. Normalize native manifest versions in `extensions/chthonic-archive/native/Cargo.toml`.
2. Continue graphics/runtime binding:
   - HLSL consumer path
   - dialogue/systems content loading
   - tensor runtime behavior beyond DLL discovery
3. Keep toolchain memory in canonical docs, not scattered chat memory.

## Source Notes

Official references used in the winning path:
- Agave CLI install: <https://docs.anza.xyz/cli/install>
- Anchor AVM reference: <https://www.anchor-lang.com/docs/references/avm>
