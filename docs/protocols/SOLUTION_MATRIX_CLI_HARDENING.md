# Solution Matrix — CLI Error Path → Fix Surface

> Generated: 2026-04-19  
> Source: OpenSSL 4.0 / rv linker / PATH pollution problem trail  
> Target: `chthonic.ps1` (v3.3.0) + `claudine.ps1` (compat wrapper)

---

## §1 — Error Pathology Catalog

Five distinct error paths discovered during the OpenSSL 4.0 forward-fix trail. Each has a unique root cause, detection signature, and fix surface inside the CLI.

| ID | Error Path | Root Cause | Detection Signature | Blast Radius |
|----|-----------|-----------|---------------------|--------------|
| **E1** | MSVC linker shadow | rv MSYS2 `usr/bin/link.exe` (Unix hardlink) shadows MSVC `link.exe` on PATH | `/usr/bin/link: extra operand` in cargo build output | All `cargo build` on `x86_64-pc-windows-msvc` target |
| **E2** | OpenSSL version gap | openssl-sys crate doesn't support system OpenSSL 4.0.0 | `unsupported OpenSSL version: 40000000` in build script stderr | Any crate depending on openssl-sys (Solana → secp256r1 → openssl) |
| **E3** | OpenSSL env var drift | OPENSSL_DIR / _LIB_DIR / _INCLUDE_DIR unset or stale | openssl-sys build script can't find headers/libs; emits `Could not find directory of OpenSSL installation` | Same as E2 — openssl-sys dependents |
| **E4** | DevKit PATH injection order | `Get-DevKitPaths` appends `msys64\ucrt64\bin` + `msys64\usr\bin` without guarding MSVC tool collision | `where.exe link.exe` returns rv's link.exe first despite MSVC dirs being registered | Silent — produces E1 only when cargo tries to link |
| **E5** | Env var non-persistence | `$env:VAR` changes in one terminal don't persist; VS Code spawns fresh shells | Build works in one terminal, fails in next fresh terminal | Any env-dependent build path (OPENSSL_*, VULKAN_SDK, CUDA_PATH) |

---

## §2 — Solution Matrix

Maps each error path to its fix location in the chthonic/claudine CLI surface.

### Matrix Key

- **Detect** = new diagnostic check (doctor / status / lane)
- **Guard** = preventive code in PATH assembly or env setup
- **Fix** = `--fix` auto-remediation action
- **Report** = output in status/lane/JSON payload

| Error | Fix Type | CLI Surface | Function | Change Description |
|-------|----------|-------------|----------|--------------------|
| **E1** | Guard | `env` | `Get-DevKitPaths` | Filter `msys64\usr\bin\link.exe` from DevKit paths when MSVC `cl.exe` dir is on PATH |
| **E1** | Detect | `doctor` | `Invoke-Doctor` | New check: `link.exe` PATH resolution — warn if non-MSVC link.exe wins |
| **E1** | Report | `graphics lane` | `Invoke-GraphicsLane` | Add `linker_path` + `linker_shadow` fields to `msvc` payload |
| **E1** | Report | `toolchain paths` | `Invoke-ToolchainMeta` | Show effective `link.exe` resolution in paths output |
| **E2** | Detect | `doctor` | `Invoke-Doctor` | New check: OpenSSL major version vs openssl-sys supported range |
| **E2** | Report | `graphics lane` | `Invoke-GraphicsLane` | Add `openssl` section: installed version, header path, lib path |
| **E2** | Report | `rust lane` | `Invoke-RustLane` | Show Cargo.toml `[patch.crates-io]` status for openssl-sys |
| **E3** | Guard | `env` | `Invoke-PolyglotActivation` | Set OPENSSL_DIR/LIB_DIR/INCLUDE_DIR if OpenSSL-Win64 exists and vars are unset |
| **E3** | Detect | `doctor` | `Invoke-Doctor` | Check OPENSSL env vars present + point to valid directories |
| **E3** | Fix | `doctor --fix` | `Invoke-Doctor` | Persist missing OPENSSL env vars to User scope |
| **E4** | Guard | `env` | `Get-PolyglotPaths` | Insert MSVC tools dir **before** DevKit paths in assembled PATH |
| **E4** | Detect | `toolchain verify` | `Invoke-ToolchainMeta` | Assert `link.exe` resolves to MSVC, not Unix link |
| **E5** | Guard | `env` | `Invoke-PolyglotActivation` | Write critical env vars to User scope (not just `$env:`) when `--persist` flag is used |
| **E5** | Report | `status` | `Show-PolyglotStatus` | Show which build-critical env vars are session-only vs persisted |

---

## §3 — Implementation Lanes

### Lane 1: PATH Guard (E1 + E4) — `Get-DevKitPaths` + `Get-PolyglotPaths`

**Problem**: DevKit paths (`msys64\ucrt64\bin`, `msys64\usr\bin`) are appended without checking for MSVC tool collisions. The `usr\bin` dir contains a Unix `link.exe` that shadows the MSVC linker.

**Fix location**: `chthonic.ps1` lines 254–260 (`Get-DevKitPaths`) and 776–815 (default path assembly)

**Implementation**:
```powershell
# In Get-DevKitPaths: when MSVC cl.exe is registered, exclude usr\bin entirely
# or filter out the specific collision. The ucrt64\bin (gcc, make) is safe.
function Get-DevKitPaths {
    $root = Get-RubyDevKitRoot
    if (-not $root) { return @() }

    $paths = @(
        (Join-Path $root "msys64\ucrt64\bin")  # gcc, make, pkg-config — always safe
    )

    # Only include msys64\usr\bin if MSVC link.exe is NOT on PATH.
    # usr\bin contains Unix link.exe which fatally shadows MSVC's linker.
    $msvcLinker = Get-MSVCLinkerPath
    if (-not $msvcLinker) {
        $paths += (Join-Path $root "msys64\usr\bin")
    }
    # else: MSVC is present — usr\bin is hazardous, skip it

    return $paths
}
```

**Ordering fix** in `$defaultPolyglotPaths` assembly:
```powershell
# System registrations (MSVC, Vulkan, Git, Azure CLI) BEFORE DevKit
$defaultPolyglotPaths += $systemRegistrationPaths  # <- MSVC cl.exe dir
$defaultPolyglotPaths += $devkitPaths               # <- gcc, safe subset
```
Already in this order — the issue is `usr\bin` inclusion, not ordering.

### Lane 2: OpenSSL Detection (E2 + E3) — `Invoke-Doctor` + `Invoke-GraphicsLane`

**Problem**: No visibility into OpenSSL version, env var state, or cargo patch status.

**Fix location**: New `openssl` check block in `Invoke-Doctor`, new fields in `Invoke-GraphicsLane`

**Implementation**:
```powershell
function Get-OpenSSLStatus {
    $dir = $env:OPENSSL_DIR
    $libDir = $env:OPENSSL_LIB_DIR
    $incDir = $env:OPENSSL_INCLUDE_DIR

    $version = $null
    $headerVersion = $null

    # Check for openssl.exe on PATH or in OPENSSL_DIR
    $opensslExe = $null
    if ($dir) {
        $candidate = Join-Path $dir "bin\openssl.exe"
        if (Test-Path $candidate) { $opensslExe = $candidate }
    }
    if (-not $opensslExe) {
        $opensslExe = (Get-Command openssl -ErrorAction SilentlyContinue).Source
    }

    if ($opensslExe) {
        try {
            $out = & $opensslExe version 2>$null
            if ($out -match 'OpenSSL\s+([0-9]+\.[0-9]+\.[0-9]+)') {
                $version = $matches[1]
            }
        } catch {}
    }

    # Parse opensslv.h for compile-time version
    if ($incDir) {
        $headerFile = Join-Path $incDir "openssl\opensslv.h"
        if (Test-Path $headerFile) {
            $content = Get-Content $headerFile -Raw
            if ($content -match 'OPENSSL_VERSION_TEXT\s+"OpenSSL\s+([0-9]+\.[0-9]+\.[0-9]+)') {
                $headerVersion = $matches[1]
            }
        }
    }

    return [pscustomobject]@{
        version         = $version
        header_version  = $headerVersion
        major           = if ($version -match '^(\d+)') { [int]$matches[1] } else { $null }
        dir             = $dir
        lib_dir         = $libDir
        include_dir     = $incDir
        dir_exists      = [bool]($dir -and (Test-Path $dir))
        lib_dir_exists  = [bool]($libDir -and (Test-Path $libDir))
        inc_dir_exists  = [bool]($incDir -and (Test-Path $incDir))
        env_persisted   = [bool]([Environment]::GetEnvironmentVariable('OPENSSL_DIR', 'User'))
    }
}
```

**Doctor check**:
```powershell
# In Invoke-Doctor, after the existing $checks loop:
$openssl = Get-OpenSSLStatus
if ($openssl.version) {
    $badge = "current"
    if ($openssl.major -ge 4) {
        # Check if [patch.crates-io] openssl-sys is present
        $cargoToml = Join-Path $REPO_ROOT "extensions\chthonic-archive\native\Cargo.toml"
        $hasPatch = (Get-Content $cargoToml -Raw) -match 'openssl-sys\s*=\s*\{.*git'
        if (-not $hasPatch) {
            $badge = "UNSUPPORTED by openssl-sys (needs git patch or ≥0.9.114)"
        } else {
            $badge = "patched (git master)"
        }
    }
    if (-not $openssl.env_persisted) {
        $badge += " | env vars NOT persisted"
    }
}
```

### Lane 3: Env Persistence (E3 + E5) — `Invoke-PolyglotActivation`

**Problem**: `chthonic env` sets `$env:` (session) only. Critical build vars vanish in new terminals.

**Fix location**: `Invoke-PolyglotActivation` (line 2638)

**Implementation**: Add `--persist` flag to `chthonic env`:
```powershell
# In Invoke-PolyglotActivation, after DevKit env vars:
# OpenSSL (required for native Cargo builds with openssl-sys)
$opensslDir = "C:\Program Files\OpenSSL-Win64"
if ((Test-Path $opensslDir) -and -not $env:OPENSSL_DIR) {
    $env:OPENSSL_DIR = $opensslDir
    $env:OPENSSL_LIB_DIR = Join-Path $opensslDir "lib\VC\x64\MD"
    $env:OPENSSL_INCLUDE_DIR = Join-Path $opensslDir "include"
}
```

### Lane 4: Linker Reporting (E1) — `Invoke-GraphicsLane`

**Problem**: `graphics lane` reports `cl.exe` and `MSBuild` but NOT `link.exe`. The linker shadow is invisible.

**Fix location**: `Invoke-GraphicsLane` (line 5208), `$payload.msvc` section

**Implementation**: Add to `msvc` payload:
```powershell
$msvcLinkerResolved = $null
$linkerShadow = $false
try {
    $linkResults = @(where.exe link.exe 2>$null)
    $msvcLinkerResolved = $linkResults | Select-Object -First 1
    if ($msvcLinkerResolved -and $msvcLinkerResolved -notlike '*VC\Tools\MSVC*') {
        $linkerShadow = $true
    }
} catch {}

# Add to $payload.msvc:
msvc = [pscustomobject]@{
    cl_path         = $clPath
    msbuild_path    = $msbuildPath
    devenv_path     = $devenvPath
    link_path       = $msvcLinkerResolved        # NEW
    linker_shadow   = $linkerShadow              # NEW
    cargo_config_linker = $cargoConfigLinker      # NEW — from .cargo/config.toml
}
```

---

## §4 — Claudine Surface (Human-Facing Additions)

Claudine delegates to chthonic. New user-facing commands:

| Claudine | Chthonic | Purpose |
|----------|----------|---------|
| `claudine repair` | `chthonic doctor --dry-run` | Already exists — will inherit new OpenSSL + linker checks |
| `claudine repair --fix` | `chthonic doctor --fix` | Will inherit new OpenSSL env var persistence fix |
| `claudine build-check` | `chthonic graphics lane --json` | **NEW**: Quick pre-build sanity (linker, OpenSSL, MSVC) |
| `claudine env --persist` | `chthonic env --persist` | **NEW**: Persist critical build env vars to User scope |

Implementation in `claudine.ps1` — add to the switch block:
```powershell
"build-check" {
    & $ChthonicScript "graphics" "lane" "--json"
    exit $LASTEXITCODE
}
```

---

## §5 — Execution Priority (Long-Horizon)

Ordered by blast radius × frequency of encounter:

| Priority | Lane | Error(s) | Effort | Impact |
|----------|------|----------|--------|--------|
| **P0** | PATH Guard | E1, E4 | 30 min | Prevents ALL linker shadow failures — the most common build-breaker |
| **P1** | OpenSSL env auto-set | E3 | 15 min | Eliminates env drift across fresh terminals |
| **P2** | Doctor checks | E1, E2, E3 | 45 min | Diagnostic visibility — catches problems before builds fail |
| **P3** | Graphics lane reporting | E1, E2 | 30 min | Structured JSON payload for agent consumption |
| **P4** | Claudine wrappers | — | 15 min | Human-facing access to the above |

Total estimated implementation surface: ~2.5 hours across 4 lanes.

---

## §6 — Files Modified

| File | Changes |
|------|---------|
| `scripts/chthonic.ps1` | `Get-DevKitPaths` guard, `Get-OpenSSLStatus`, doctor checks, graphics lane fields, env persistence |
| `scripts/claudine.ps1` | `build-check` route, `--persist` passthrough |
| `.cargo/config.toml` | Already done — linker pin (defensive backstop, kept even after P0 guard) |

---

## §7 — Removal Criteria

| Workaround | Remove When |
|------------|-------------|
| `[patch.crates-io]` openssl-sys git | openssl-sys ≥ 0.9.114 ships on crates.io |
| `.cargo/config.toml` linker pin | rv is uninstalled OR rv stops bundling MSYS2 usr/bin on PATH |
| `Get-DevKitPaths` usr/bin exclusion | rv is uninstalled (but safe to keep — zero cost) |
| OPENSSL env var auto-set in `env` | Never (system OpenSSL may change paths on upgrade) |

---

## §4 — Mitigation Chain Architecture

### Problem: Detection-Mitigation Asymmetry

Raw diagnostic output ("SHADOWED") reports error existence without evaluating whether active defenses neutralize the risk. This produces false urgency — the system flags a problem that the codebase already handles.

### Three-Layer Model

Each infrastructure error path carries an ordered set of defense mechanisms. The effective state is the residual risk after evaluating all active mitigations.

| Layer | Mechanism | Applied at | Survives session restart? |
|---|---|---|---|
| L1 | Config file pin (`.cargo/config.toml`) | Cargo invocation | Yes — checked into repo |
| L2 | Env var (User scope) | Shell startup | Yes — persisted to registry |
| L3 | Code guard (PATH filter) | Activation function | Yes — embedded in script |

### Effective State Enum

Each check reports one of five states:

| State | Meaning | Display color |
|---|---|---|
| `clear` / `compatible` | No problem exists | Green |
| `mitigated` / `fully mitigated` | Problem exists, all active defenses neutralize it | Yellow→Green |
| `patched (env drift risk)` | Cargo patch active, env vars missing (build works, IDE may not) | Yellow |
| `env set (no cargo patch)` | Env vars set but no Cargo patch — partial mitigation | Yellow+Red |
| `vulnerable` | Problem exists, no active defenses | Red |

### Linker Mitigation Chain (E1)

```
M1: .cargo/config.toml linker pin  — bypasses PATH resolution entirely
M2: CARGO_TARGET_*_LINKER env var  — session-scoped override
M3: Get-DevKitPaths PATH guard     — prevents msys64\usr\bin from entering PATH
```

When M1 is active: effective = `mitigated` (shadow exists on PATH but Cargo never calls it).  
When only M3 active: effective = `mitigated` (shadow never enters PATH).  
When neither: effective = `vulnerable`.

### OpenSSL Mitigation Chain (E2/E3)

```
M1: [patch.crates-io] openssl-sys git  — bypasses crates.io version gate entirely
M2: OPENSSL env vars persisted (User)  — survives session restart
M3: PolyglotActivation auto-set        — session fallback when vars missing
```

When M1+M2 active: effective = `fully mitigated`.  
When M1 only: effective = `patched (env drift risk)`.  
When M2+M3 only: effective = `env set (no cargo patch)`.  
When none: effective = `vulnerable`.

### CLI Surface

- `chthonic doctor` INFRASTRUCTURE section — per-check effective state + active mitigation list
- `chthonic graphics lane --json` — `msvc.linker_effective`, `msvc.linker_mitigations`, `openssl.effective`, `openssl.mitigations`
- `claudine repair --fix` — delegates to `chthonic doctor --fix` to persist User-scope env vars

---

## §5 — Branch D: Tool Crate Dependency Updates (2026-04-19)

Completed as part of the same dependency update trail. All bumps verified clean against the mitigation chain — doctor post-update still reports `linker: mitigated`, `openssl: fully mitigated`.

### ankh-forge (`tools/ankh-forge/Cargo.toml`)

| Crate | Before | After | Risk | API impact |
|---|---|---|---|---|
| clap | 4.6.0 | 4.6.1 | patch | none |
| zstd | 0.13 | 0.13.3 | patch | none |
| sha2 | 0.10 | 0.11 | semver-minor | `Sha256::new()` / `.update()` / `.finalize().into()` — stable |
| lz4_flex | 0.11 | 0.13 | semver-minor | `block::compress()` — stable; GPU feature only |
| bincode | 2.0 | **SKIPPED** | POISON | v3.0.0 is unmaintained with compiler errors — do not upgrade |

### chthonic-cai (`tools/chthonic-cai/Cargo.toml`)

| Crate | Before | After | Risk | API impact |
|---|---|---|---|---|
| crossterm | 0.28 | 0.29 | semver-minor | execute!, SetForegroundColor, Print, ResetColor, SetTitle, Color::* — all stable; breaking changes in 0.29 are in Event/KeyCode which this codebase does not use |

### Verification

- `cargo check -p ankh-forge` — clean, 27.86s
- `cargo check -p chthonic-cai` — clean, 3.90s
- `cargo check -p entropy-ledger-host -p chthonic-daemon -p tensor-runtime-host -p xtask` — clean
- `chthonic doctor` post-update — INFRASTRUCTURE section unchanged, mitigations intact

### Removal Criteria

| Workaround | Remove when |
|---|---|
| `[patch.crates-io]` openssl-sys git | openssl-sys ≥ 0.9.114 ships on crates.io |
| `.cargo/config.toml` linker pin | rv stops bundling MSYS2 `link.exe`, or rv is removed from the toolchain |
| OPENSSL env vars (User scope) | Remove when patch is removed and openssl-sys finds headers natively |
