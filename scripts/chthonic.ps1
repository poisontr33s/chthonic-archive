#!/usr/bin/env pwsh

# @SID: SCRIPT_CHTHONIC_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: chthonic.ps1
# ║ Module: Unified polyglot CLI router
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: INFRASTRUCTURE
# ║ Semantic ID: SCRIPT_CHTHONIC_V1
# ║ Purpose: Unified META-CLI for polyglot tooling and repo operations
# ║ Exports: (none)
# ║ Flags/Modes: -Command, -CmdArgs, -Quiet, -Json.
# ║ Cross-References: (claudine.ps1)
# ╚════════════════════════════════════════════════════════════════════════════

param(
    [Parameter(Position = 0)]
    [string]$Command,
    
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CmdArgs,
    
    [switch]$Quiet,
    [switch]$Json,

    [switch]$NoExit
)

$ErrorActionPreference = 'Stop'

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$REPO_ROOT   = Split-Path -Parent $SCRIPT_DIR
try {
    $pkg = Get-Content (Join-Path $REPO_ROOT 'package.json') -Raw | ConvertFrom-Json
    $VERSION = if ($pkg.version) { $pkg.version } else { "3.3.0" }
} catch {
    $VERSION = "3.3.0"  # fallback if package.json is missing or malformed
}
$LIB_DIR = Join-Path $SCRIPT_DIR "lib"
$STATE_DIR = Join-Path $env:USERPROFILE ".chthonic"
$CONFIG_FILE = Join-Path $STATE_DIR "config.json"
$SERVICES_FILE = Join-Path $STATE_DIR "services.json"
$script:CommandSurfaceJsonPayload = $null

function Complete-ChthonicCommand {
    param([int]$Code = 0)

    if ($NoExit) {
        return $Code
    }

    exit $Code
}

# ═══════════════════════════════════════════════════════════════════════════════
# POLYGLOT PATHS - ALL GLOBAL NATIVE INSTALLATIONS (Win11)
# ═══════════════════════════════════════════════════════════════════════════════

# Resolve rv-managed Ruby from rv itself, then fall back to managed ruby-* directories only.
function Get-RvExePath {
    foreach ($name in @("rvw", "rv.exe", "rv")) {
        $cmd = Get-CommandResolution -Name $name
        if (-not $cmd) { continue }

        if ($cmd.Path) { return $cmd.Path }
        if ($cmd.Definition -and (Test-Path $cmd.Definition)) { return $cmd.Definition }
    }

    return $null
}

function Get-RvRubyExePath {
    $rvExe = Get-RvExePath
    if (-not $rvExe) { return $null }

    try {
        $rubyExe = (& $rvExe ruby find 2>$null | Select-Object -First 1)
        if ($rubyExe) {
            $resolved = $rubyExe.ToString().Trim()
            if ($resolved -and (Test-Path $resolved)) {
                return $resolved
            }
        }
    } catch {}

    return $null
}

function Get-RvRubyBinDir {
    $rubyExe = Get-RvRubyExePath
    if ($rubyExe) {
        return (Split-Path $rubyExe -Parent)
    }

    $rvRubies = Join-Path $env:APPDATA "rv\rubies"
    if (-not (Test-Path $rvRubies)) { return $null }

    $latest = Get-ChildItem $rvRubies -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "ruby-*" } |
        Sort-Object Name -Descending |
        Select-Object -First 1
    if ($latest) {
        $bin = Join-Path $latest.FullName "bin"
        if (Test-Path $bin) { return $bin }
    }
    return $null
}

# Resolve the best available RubyInstaller DevKit root (for MSYS2/UCRT64 toolchain).
# Note: rv manages Ruby versions; RubyInstaller provides the DevKit (gcc, make, etc.).
function Get-RubyDevKitRoot {
    $rubyExe = Get-RvRubyExePath
    if ($rubyExe) {
        $rubyRoot = Split-Path (Split-Path $rubyExe -Parent) -Parent
        $rvDevkit = Join-Path $rubyRoot "msys64\ucrt64\bin\gcc.exe"
        if (Test-Path $rvDevkit) {
            return $rubyRoot
        }
    }

    $rvRubies = Join-Path $env:APPDATA "rv\rubies"
    if (Test-Path $rvRubies) {
        foreach ($root in (Get-ChildItem $rvRubies -Directory -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -like "ruby-*" } |
                Sort-Object Name -Descending)) {
            $candidate = Join-Path $root.FullName "msys64\ucrt64\bin\gcc.exe"
            if (Test-Path $candidate) {
                return $root.FullName
            }
        }
    }

    return $null
}

function Get-BrushRepoRcPath {
    $candidate = Join-Path $SCRIPT_DIR "brush_repo.rc"
    if (Test-Path $candidate) { return $candidate }
    return $null
}

function Get-FnmNodeExePath {
    $fnmRoot = Join-Path $env:APPDATA "fnm\node-versions"
    if (-not (Test-Path $fnmRoot)) { return $null }

    $latest = Get-ChildItem $fnmRoot -Directory -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending |
        Select-Object -First 1
    if (-not $latest) { return $null }

    $nodeExe = Join-Path $latest.FullName "installation\node.exe"
    if (Test-Path $nodeExe) { return $nodeExe }
    return $null
}

function Get-RExePath {
    $rRoot = "C:\Program Files\R"
    if (-not (Test-Path $rRoot)) { return $null }

    $latest = Get-ChildItem $rRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "R-*" } |
        Sort-Object Name -Descending |
        Select-Object -First 1
    if (-not $latest) { return $null }

    foreach ($candidate in @(
        (Join-Path $latest.FullName "bin\x64\R.exe"),
        (Join-Path $latest.FullName "bin\R.exe")
    )) {
        if (Test-Path $candidate) { return $candidate }
    }

    return $null
}

function Get-RScriptExePath {
    $rExe = Get-RExePath
    if (-not $rExe) { return $null }

    $candidate = Join-Path (Split-Path -Parent $rExe) "Rscript.exe"
    if (Test-Path $candidate) { return $candidate }
    return $null
}

function Get-RRvExePath {
    foreach ($candidate in @(
        (Join-Path $env:USERPROFILE ".r-rv\bin\rv.exe"),
        (Join-Path $env:USERPROFILE ".r-rv\bin\rv")
    )) {
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

function Get-RRvScriptPath {
    $candidate = Join-Path $SCRIPT_DIR "rv-r.ps1"
    if (Test-Path $candidate) { return $candidate }
    return $null
}

function Get-RigExePath {
    foreach ($candidate in @(
        "C:\Program Files\rig\rig.exe",
        (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\rig.exe")
    )) {
        if ($candidate -and (Test-Path $candidate)) { return $candidate }
    }
    return $null
}

function Get-ZvExePath {
    foreach ($candidate in @(
        (Join-Path $env:USERPROFILE ".zv\bin\zv.exe"),
        (Join-Path $env:USERPROFILE ".zv\bin\zv")
    )) {
        if (Test-Path $candidate) { return $candidate }
    }

    try {
        $cmd = Get-Command zv -ErrorAction Stop
        if ($cmd.Source -and (Test-Path $cmd.Source)) { return $cmd.Source }
    } catch {}

    return $null
}

function Get-ZigExePath {
    foreach ($candidate in @(
        (Join-Path $env:USERPROFILE ".zv\bin\zig.exe"),
        (Join-Path $env:USERPROFILE ".zv\bin\zig")
    )) {
        if (Test-Path $candidate) { return $candidate }
    }

    try {
        $cmd = Get-Command zig -ErrorAction Stop
        if ($cmd.Source -and (Test-Path $cmd.Source)) { return $cmd.Source }
    } catch {}

    return $null
}

function Get-MSVCLinkerPath {
    # Resolve the MSVC link.exe path from the same VS install that provides cl.exe.
    $clExe = Get-VSClExePath
    if ($clExe) {
        $linkExe = Join-Path (Split-Path -Parent $clExe) "link.exe"
        if (Test-Path $linkExe) { return $linkExe }
    }
    return $null
}

function Get-DevKitPaths {
    $root = Get-RubyDevKitRoot
    if (-not $root) { return @() }

    $paths = @(
        (Join-Path $root "msys64\ucrt64\bin")   # gcc, make, pkg-config — always safe
    )

    # GUARD: msys64\usr\bin contains a Unix link.exe (hardlink utility) that fatally
    # shadows MSVC's linker when both are on PATH. Only include usr\bin when MSVC
    # toolchain is NOT present — otherwise Cargo builds fail with:
    #   /usr/bin/link: extra operand '...\symbols.o'
    $msvcLinker = Get-MSVCLinkerPath
    if (-not $msvcLinker) {
        $paths += (Join-Path $root "msys64\usr\bin")
    }

    return $paths
}

function Get-OpenSSLStatus {
    $dir = $env:OPENSSL_DIR
    $libDir = $env:OPENSSL_LIB_DIR
    $incDir = $env:OPENSSL_INCLUDE_DIR

    $version = $null
    $opensslExe = $null
    if ($dir) {
        $candidate = Join-Path $dir "bin\openssl.exe"
        if (Test-Path $candidate) { $opensslExe = $candidate }
    }
    if (-not $opensslExe) {
        try { $opensslExe = (Get-Command openssl -ErrorAction Stop).Source } catch {}
    }

    if ($opensslExe) {
        try {
            $out = & $opensslExe version 2>$null
            if ($out -match 'OpenSSL\s+([0-9]+\.[0-9]+\.[0-9]+)') {
                $version = $matches[1]
            }
        } catch {}
    }

    $major = if ($version -match '^(\d+)') { [int]$matches[1] } else { $null }
    $envPersisted = [bool]([Environment]::GetEnvironmentVariable('OPENSSL_DIR', 'User'))

    # Mitigation chain for OpenSSL version gap (E2) and env drift (E3).
    # M1: [patch.crates-io] openssl-sys git override in Cargo.toml
    # M2: OPENSSL env vars persisted to User scope
    # M3: Invoke-PolyglotActivation auto-set (session fallback)
    $mitigations = @()
    $cargoTomlPath = Join-Path $REPO_ROOT "extensions\chthonic-archive\native\Cargo.toml"
    $hasCargoPatch = $false
    if (Test-Path $cargoTomlPath) {
        $cargoContent = Get-Content $cargoTomlPath -Raw
        if ($cargoContent -match 'openssl-sys\s*=\s*\{.*git') {
            $hasCargoPatch = $true
            $mitigations += [pscustomobject]@{
                id     = "M1"
                name   = "[patch.crates-io] openssl-sys git"
                active = $true
                value  = "master branch (pre-0.9.114)"
            }
        }
    }
    if ($envPersisted) {
        $mitigations += [pscustomobject]@{
            id     = "M2"
            name   = "OPENSSL env vars (User scope)"
            active = $true
            value  = $dir
        }
    }
    $opensslAutoSetDir = "C:\Program Files\OpenSSL-Win64"
    if ((Test-Path $opensslAutoSetDir) -and -not $envPersisted) {
        $mitigations += [pscustomobject]@{
            id     = "M3"
            name   = "PolyglotActivation auto-set (session only)"
            active = $true
            value  = $opensslAutoSetDir
        }
    }

    $needsPatch = $major -ge 4
    $mitigated = (-not $needsPatch) -or (($mitigations | Where-Object { $_.active }).Count -gt 0)
    $effective = if (-not $needsPatch) { "compatible" }
                elseif ($hasCargoPatch -and $envPersisted) { "fully mitigated" }
                elseif ($hasCargoPatch) { "patched (env drift risk)" }
                elseif ($envPersisted) { "env set (no cargo patch)" }
                else { "vulnerable" }

    return [pscustomobject]@{
        version        = $version
        major          = $major
        dir            = $dir
        lib_dir        = $libDir
        include_dir    = $incDir
        dir_exists     = [bool]($dir -and (Test-Path $dir))
        lib_dir_exists = [bool]($libDir -and (Test-Path $libDir))
        inc_dir_exists = [bool]($incDir -and (Test-Path $incDir))
        env_persisted  = $envPersisted
        has_cargo_patch = $hasCargoPatch
        mitigations    = $mitigations
        mitigated      = $mitigated
        effective      = $effective
    }
}

function Get-LinkerShadowStatus {
    $msvcLinker = Get-MSVCLinkerPath
    $resolvedFirst = $null
    $shadow = $false
    $linkResults = @()

    try {
        $linkResults = @(where.exe link.exe 2>$null)
        if ($linkResults.Count -gt 0) {
            $resolvedFirst = $linkResults[0]
            if ($resolvedFirst -and $resolvedFirst -notlike '*VC\Tools\MSVC*') {
                $shadow = $true
            }
        }
    } catch {}

    # Mitigation chain: evaluate all active defenses against linker shadow.
    # M1: .cargo/config.toml linker pin (bypasses PATH entirely)
    # M2: CARGO_TARGET env var (session-level override)
    # M3: Get-DevKitPaths guard (prevents chthonic from adding usr\bin)
    $mitigations = @()
    $cargoConfigPath = Join-Path $REPO_ROOT "extensions\chthonic-archive\native\.cargo\config.toml"
    $cargoConfigLinker = $null
    if (Test-Path $cargoConfigPath) {
        $configContent = Get-Content $cargoConfigPath -Raw
        if ($configContent -match 'linker\s*=\s*"([^"]+)"') {
            $cargoConfigLinker = $matches[1]
            $mitigations += [pscustomobject]@{
                id     = "M1"
                name   = ".cargo/config.toml linker pin"
                active = $true
                value  = $cargoConfigLinker
            }
        }
    }
    $cargoEnvLinker = $env:CARGO_TARGET_X86_64_PC_WINDOWS_MSVC_LINKER
    if ($cargoEnvLinker) {
        $mitigations += [pscustomobject]@{
            id     = "M2"
            name   = "CARGO_TARGET env var"
            active = $true
            value  = $cargoEnvLinker
        }
    }
    # M3 is structural — it's in Get-DevKitPaths. Report if MSVC is present (guard would activate).
    if ($msvcLinker) {
        $mitigations += [pscustomobject]@{
            id     = "M3"
            name   = "Get-DevKitPaths PATH guard"
            active = $true
            value  = "usr\bin excluded when MSVC present"
        }
    }

    $mitigated = ($mitigations | Where-Object { $_.active }).Count -gt 0
    $effective = if ($shadow -and $mitigated) { "mitigated" }
                elseif ($shadow) { "vulnerable" }
                else { "clear" }

    return [pscustomobject]@{
        msvc_linker        = $msvcLinker
        resolved_first     = $resolvedFirst
        shadow             = $shadow
        all_results        = $linkResults
        cargo_config_linker = $cargoConfigLinker
        mitigations        = $mitigations
        mitigated          = $mitigated
        effective          = $effective
    }
}

function Get-VSWhereExe {
    $candidates = @(
        "C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe",
        "C:\Program Files\Microsoft Visual Studio\Installer\vswhere.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }
    return $null
}

function Get-VSInstallationPath {
    param([string]$ProductId = "*")
    $vswhere = Get-VSWhereExe
    if (-not $vswhere) { return $null }
    try {
        $out = & $vswhere -latest -prerelease -products $ProductId -property installationPath 2>$null
        $path = ($out | Select-Object -First 1)
        if ($path -and (Test-Path $path)) { return $path }
    } catch {}
    return $null
}

function Get-VSProductVersion {
    param([string]$ProductId = "*")
    $vswhere = Get-VSWhereExe
    if (-not $vswhere) { return $null }
    try {
        $out = & $vswhere -latest -prerelease -products $ProductId -property installationVersion 2>$null
        $ver = ($out | Select-Object -First 1)
        if ($ver) { return $ver.Trim() }
    } catch {}
    return $null
}

function Get-VSIdeProductIds {
    return @(
        "Microsoft.VisualStudio.Product.Professional",
        "Microsoft.VisualStudio.Product.Community",
        "Microsoft.VisualStudio.Product.Enterprise"
    )
}

function Get-VisualStudioVersion {
    $versions = @()
    $products = @()
    $products += Get-VSIdeProductIds
    $products += "Microsoft.VisualStudio.Product.BuildTools"

    foreach ($product in $products) {
        $v = Get-VSProductVersion -ProductId $product
        if ($v) { $versions += $v }
    }
    if (-not $versions) { return $null }

    $parsed = @()
    foreach ($v in $versions) {
        try {
            $parsed += [pscustomobject]@{ Raw = $v; Sem = [version]$v }
        } catch {
            $parsed += [pscustomobject]@{ Raw = $v; Sem = $null }
        }
    }

    $withSem = $parsed | Where-Object { $_.Sem }
    if ($withSem) {
        return ($withSem | Sort-Object Sem -Descending | Select-Object -First 1).Raw
    }
    return ($versions | Sort-Object -Descending | Select-Object -First 1)
}

function Get-AzureCliVersion {
    try {
        $raw = az version --output json 2>$null
        if (-not $raw) { return $null }
        $obj = $raw | ConvertFrom-Json
        $ver = $obj.'azure-cli'
        if ($ver) { return "$ver".Trim() }
    } catch {}
    return $null
}

function Get-VSInstallationRoots {
    $roots = @()
    $products = @()
    $products += Get-VSIdeProductIds
    $products += "Microsoft.VisualStudio.Product.BuildTools"

    foreach ($product in $products) {
        $root = Get-VSInstallationPath -ProductId $product
        if ($root) { $roots += $root }
    }

    # Fallbacks for 2026 Insiders layouts if vswhere metadata is stale.
    foreach ($fallback in @(
        "C:\Program Files\Microsoft Visual Studio\18\Insiders",
        "C:\Program Files (x86)\Microsoft Visual Studio\18\Insiders"
    )) {
        if (Test-Path $fallback) { $roots += $fallback }
    }

    return $roots | Select-Object -Unique
}

function Get-VSClExePath {
    foreach ($root in (Get-VSInstallationRoots)) {
        $msvcRoot = Join-Path $root "VC\Tools\MSVC"
        if (-not (Test-Path $msvcRoot)) { continue }

        $versions = Get-ChildItem $msvcRoot -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending
        foreach ($v in $versions) {
            $cl = Join-Path $v.FullName "bin\Hostx64\x64\cl.exe"
            if (Test-Path $cl) { return $cl }
        }
    }
    return $null
}

function Get-VSMsBuildExePath {
    foreach ($root in (Get-VSInstallationRoots)) {
        $msbuild = Join-Path $root "MSBuild\Current\Bin\MSBuild.exe"
        if (Test-Path $msbuild) { return $msbuild }
    }
    return $null
}

function Get-VSClangBinDir {
    foreach ($root in (Get-VSInstallationRoots)) {
        $clang = Join-Path $root "VC\Tools\Llvm\bin\clang.exe"
        if (Test-Path $clang) { return (Split-Path -Parent $clang) }
    }
    return $null
}

function Get-AzureCliBinDir {
    foreach ($candidate in @(
        "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin",
        "C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin"
    )) {
        if (Test-Path (Join-Path $candidate "az.cmd")) { return $candidate }
    }
    return $null
}

function Find-WinGetPackageExePath {
    param(
        [string]$PackagePrefix,
        [string]$ExeName
    )

    $wgRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    if (-not (Test-Path $wgRoot)) { return $null }

    $pkg = Get-ChildItem $wgRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "$PackagePrefix*" } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if (-not $pkg) { return $null }

    $exe = Get-ChildItem $pkg.FullName -Recurse -File -Filter $ExeName -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($exe) { return $exe.FullName }

    return $null
}

function Get-BicepExePath {
    try {
        $path = (Get-Command bicep -ErrorAction Stop).Source
        if ($path -and (Test-Path $path)) { return $path }
    } catch {}

    foreach ($candidate in @(
        "C:\Program Files\Bicep CLI\bicep.exe",
        "C:\Program Files\Microsoft\Bicep CLI\bicep.exe",
        (Find-WinGetPackageExePath -PackagePrefix "Microsoft.Bicep_" -ExeName "bicep.exe")
    )) {
        if ($candidate -and (Test-Path $candidate)) { return $candidate }
    }
    return $null
}

function Get-SqlCmdExePath {
    try {
        $path = (Get-Command sqlcmd -ErrorAction Stop).Source
        if ($path -and (Test-Path $path)) { return $path }
    } catch {}

    foreach ($candidate in @(
        "C:\Program Files\sqlcmd\sqlcmd.exe",
        "C:\Program Files\sqlcmd\bin\sqlcmd.exe",
        (Find-WinGetPackageExePath -PackagePrefix "Microsoft.Sqlcmd_" -ExeName "sqlcmd.exe")
    )) {
        if ($candidate -and (Test-Path $candidate)) { return $candidate }
    }
    return $null
}

function Get-SqlPackageExePath {
    try {
        $path = (Get-Command sqlpackage -ErrorAction Stop).Source
        if ($path -and (Test-Path $path)) { return $path }
    } catch {}

    foreach ($candidate in @(
        "C:\Program Files\Microsoft SQL Server\170\DAC\bin\SqlPackage.exe",
        "C:\Program Files\Microsoft SQL Server\160\DAC\bin\SqlPackage.exe",
        (Find-WinGetPackageExePath -PackagePrefix "Microsoft.SqlPackage_" -ExeName "SqlPackage.exe")
    )) {
        if ($candidate -and (Test-Path $candidate)) { return $candidate }
    }
    return $null
}

function Get-BicepBinDir {
    $exe = Get-BicepExePath
    if ($exe) { return (Split-Path -Parent $exe) }
    return $null
}

function Get-SqlCmdBinDir {
    $exe = Get-SqlCmdExePath
    if ($exe) { return (Split-Path -Parent $exe) }
    return $null
}

function Get-SqlPackageBinDir {
    $exe = Get-SqlPackageExePath
    if ($exe) { return (Split-Path -Parent $exe) }
    return $null
}

function Get-VulkanBinDir {
    if (-not $env:VULKAN_SDK) { return $null }
    $bin = Join-Path $env:VULKAN_SDK "Bin"
    if (Test-Path $bin) { return $bin }
    return $null
}

function Get-SsmsInstallationPath {
    $vswhere = Get-VSWhereExe
    if (-not $vswhere) { return $null }
    try {
        $out = & $vswhere -latest -products Microsoft.VisualStudio.Product.Ssms -property installationPath 2>$null
        $path = ($out | Select-Object -First 1)
        if ($path -and (Test-Path $path)) { return $path }
    } catch {}
    return $null
}

function Get-SsmsVersion {
    $vswhere = Get-VSWhereExe
    if (-not $vswhere) { return $null }
    try {
        $out = & $vswhere -latest -products Microsoft.VisualStudio.Product.Ssms -property installationVersion 2>$null
        $ver = ($out | Select-Object -First 1)
        if ($ver) { return $ver.Trim() }
    } catch {}
    return $null
}

# Resolve a command in a way that is robust to aliases/functions.
function Get-CommandResolution {
    param([Parameter(Mandatory = $true)][string]$Name)

    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) { return $null }

    $type = [string]$cmd.CommandType
    $path = $null
    $display = $null

    switch ($type) {
        "Alias" {
            $resolved = $cmd.ResolvedCommand
            if ($resolved) {
                if ($resolved.Source -and (Test-Path $resolved.Source)) {
                    $path = $resolved.Source
                } elseif ($resolved.Definition -and (Test-Path $resolved.Definition)) {
                    $path = $resolved.Definition
                }
            }
            if (-not $path -and $cmd.Definition -and (Test-Path $cmd.Definition)) {
                $path = $cmd.Definition
            }
            if (-not $path) {
                $target = if ($cmd.Definition) { $cmd.Definition } else { "(unresolved)" }
                $display = "alias -> $target"
            }
        }
        "Function" {
            $target = $null
            # Common wrapper pattern used by this workspace profile:
            #   & $global:CHTHONIC_SCRIPT [args...]
            if ($cmd.Definition -match '\$global:CHTHONIC_SCRIPT') {
                try {
                    $scriptVar = Get-Variable -Name CHTHONIC_SCRIPT -Scope Global -ErrorAction Stop
                    $scriptPath = [string]$scriptVar.Value
                    if ($scriptPath -and (Test-Path $scriptPath)) {
                        $target = $scriptPath
                    }
                } catch {}
            }
            if (-not $target -and $cmd.Definition -match '\$global:CHTHONIC_CLAUDE_EXE') {
                try {
                    $claudeVar = Get-Variable -Name CHTHONIC_CLAUDE_EXE -Scope Global -ErrorAction Stop
                    $claudePath = [string]$claudeVar.Value
                    if ($claudePath -and (Test-Path $claudePath)) {
                        $target = $claudePath
                    }
                } catch {}
            }

            if ($target) {
                $path = $target
                $display = "function wrapper -> $target"
            } else {
                $snippet = ($cmd.Definition -replace '\s+', ' ').Trim()
                if ($snippet.Length -gt 84) { $snippet = $snippet.Substring(0, 84) + "..." }
                $display = "function -> $snippet"
            }
        }
        default {
            if ($cmd.Source -and (Test-Path $cmd.Source)) {
                $path = $cmd.Source
            } elseif ($cmd.Definition -and (Test-Path $cmd.Definition)) {
                $path = $cmd.Definition
            } elseif ($cmd.Definition) {
                $display = "$type -> $($cmd.Definition)"
            } else {
                $display = $type
            }
        }
    }

    if (-not $display) {
        $display = if ($path) { $path } else { $type }
    }

    return [pscustomobject]@{
        Name = $Name
        Type = $type
        Path = $path
        Display = $display
    }
}

function Get-CommandPathFlexible {
    param([Parameter(Mandatory = $true)][string]$Name)
    $meta = Get-CommandResolution -Name $Name
    if ($meta -and $meta.Path) { return $meta.Path }
    return $null
}

function Get-CommandDisplayFlexible {
    param([Parameter(Mandatory = $true)][string]$Name)
    $meta = Get-CommandResolution -Name $Name
    if (-not $meta) { return $null }
    if ($meta.Path) { return $meta.Path }
    return $meta.Display
}

function Get-ClaudineScriptPath {
    $candidate = Join-Path $SCRIPT_DIR "claudine.ps1"
    if (Test-Path $candidate) { return $candidate }
    return $null
}

function Ensure-RvCommandBinding {
    # PowerShell reserves `rv` as alias for Remove-Variable.
    # In this workspace, `rv` should target Ruby version management when available.
    $result = [ordered]@{
        applied = $false
        reason = $null
        rv_before = $null
        rv_after = $null
        rvar_after = $null
    }

    $rvBefore = Get-CommandResolution -Name "rv"
    if ($rvBefore) {
        $result.rv_before = if ($rvBefore.Path) { $rvBefore.Path } else { $rvBefore.Display }
    }

    $rvCmd = Get-CommandResolution -Name "rv"
    $rvExeCmd = Get-CommandResolution -Name "rv.exe"
    $rvwCmd = Get-CommandResolution -Name "rvw"
    $targetCommand = $null
    if ($rvCmd -and $rvCmd.Type -ne "Alias") {
        $targetCommand = "rv"
    } elseif ($rvExeCmd) {
        $targetCommand = "rv.exe"
    } elseif ($rvwCmd) {
        $targetCommand = "rvw"
    }
    if (-not $targetCommand) {
        $result.reason = "rv/rv.exe/rvw not found"
        return [pscustomobject]$result
    }

    $isShadowedByRemoveVariable = $false
    if ($rvBefore -and $rvBefore.Type -eq "Alias" -and $rvBefore.Display -eq "alias -> Remove-Variable") {
        $isShadowedByRemoveVariable = $true
    }

    if (-not $isShadowedByRemoveVariable) {
        $result.reason = "rv already bound to non-Remove-Variable command"
        $rvAfter = Get-CommandResolution -Name "rv"
        if ($rvAfter) { $result.rv_after = if ($rvAfter.Path) { $rvAfter.Path } else { $rvAfter.Display } }
        return [pscustomobject]$result
    }

    try {
        if (-not (Get-Alias -Name rvar -ErrorAction SilentlyContinue)) {
            Set-Alias -Name rvar -Value Remove-Variable -Scope Global -Force
        }
        Set-Alias -Name rv -Value $targetCommand -Scope Global -Force
        $result.applied = $true
        $result.reason = "rv alias redirected to $targetCommand"
    } catch {
        $result.reason = "failed to set alias: $($_.Exception.Message)"
    }

    $rvAfter = Get-CommandResolution -Name "rv"
    if ($rvAfter) {
        $result.rv_after = if ($rvAfter.Path) { $rvAfter.Path } else { $rvAfter.Display }
    }
    $rvarAfter = Get-CommandResolution -Name "rvar"
    if ($rvarAfter) {
        $result.rvar_after = if ($rvarAfter.Path) { $rvarAfter.Path } else { $rvarAfter.Display }
    }

    return [pscustomobject]$result
}

function Ensure-RCommandBinding {
    $result = [ordered]@{
        applied = $false
        reason = $null
        r_before = $null
        r_after = $null
        rhistory_after = $null
    }

    $rBefore = Get-CommandResolution -Name "R"
    if ($rBefore) {
        $result.r_before = if ($rBefore.Path) { $rBefore.Path } else { $rBefore.Display }
    }

    $rExe = Get-RExePath
    if (-not $rExe) {
        $result.reason = "R runtime not found"
        return [pscustomobject]$result
    }

    $isShadowedByInvokeHistory = $false
    if ($rBefore -and $rBefore.Type -eq "Alias" -and $rBefore.Display -eq "alias -> Invoke-History") {
        $isShadowedByInvokeHistory = $true
    }

    if (-not $isShadowedByInvokeHistory) {
        $result.reason = "R already bound to non-Invoke-History command"
        $rAfter = Get-CommandResolution -Name "R"
        if ($rAfter) { $result.r_after = if ($rAfter.Path) { $rAfter.Path } else { $rAfter.Display } }
        return [pscustomobject]$result
    }

    try {
        if (-not (Get-Alias -Name rhistory -ErrorAction SilentlyContinue)) {
            Set-Alias -Name rhistory -Value Invoke-History -Scope Global -Force
        }
        Set-Alias -Name R -Value $rExe -Scope Global -Force
        $result.applied = $true
        $result.reason = "R alias redirected to $rExe"
    } catch {
        $result.reason = "failed to set alias: $($_.Exception.Message)"
    }

    $rAfter = Get-CommandResolution -Name "R"
    if ($rAfter) {
        $result.r_after = if ($rAfter.Path) { $rAfter.Path } else { $rAfter.Display }
    }
    $rhistoryAfter = Get-CommandResolution -Name "rhistory"
    if ($rhistoryAfter) {
        $result.rhistory_after = if ($rhistoryAfter.Path) { $rhistoryAfter.Path } else { $rhistoryAfter.Display }
    }

    return [pscustomobject]$result
}

function Get-SystemRegistrationPaths {
    $paths = @()

    # Git remains a required system baseline for repo operations.
    $paths += "C:\Program Files\Git\cmd"

    $azBin = Get-AzureCliBinDir
    if ($azBin) { $paths += $azBin }

    $bicepBin = Get-BicepBinDir
    if ($bicepBin) { $paths += $bicepBin }

    $sqlcmdBin = Get-SqlCmdBinDir
    if ($sqlcmdBin) { $paths += $sqlcmdBin }

    $sqlpackageBin = Get-SqlPackageBinDir
    if ($sqlpackageBin) { $paths += $sqlpackageBin }

    $vulkanBin = Get-VulkanBinDir
    if ($vulkanBin) { $paths += $vulkanBin }

    $clExe = Get-VSClExePath
    if ($clExe) { $paths += (Split-Path -Parent $clExe) }

    $msbuildExe = Get-VSMsBuildExePath
    if ($msbuildExe) { $paths += (Split-Path -Parent $msbuildExe) }

    $clangBin = Get-VSClangBinDir
    if ($clangBin) { $paths += $clangBin }

    return $paths | Where-Object { $_ } | Select-Object -Unique
}

$rvRubyBin = Get-RvRubyBinDir
$devkitPaths = Get-DevKitPaths
$systemRegistrationPaths = Get-SystemRegistrationPaths

# Default polyglot paths (fallback when config.json is missing)
$defaultPolyglotPaths = @(
    # Native user binaries (uv + standalone CLIs like claude)
    "$env:USERPROFILE\.local\bin",

    # Bun (JS/TS runtime + Biome)
    "$env:USERPROFILE\.bun\bin",

    # Rust (rustup managed) + Cargo tools (includes rv, rvw)
    "$env:USERPROFILE\.cargo\bin",

# Go (goup-managed, user-space)
    "$env:USERPROFILE\.goup\current\bin",
    "$env:USERPROFILE\go\bin"
)

# Zig (zv-managed)
$defaultPolyglotPaths += "$env:USERPROFILE\.zv\bin"

# R package manager lane (A2-ai/rv, kept isolated from Ruby rv)
$defaultPolyglotPaths += "$env:USERPROFILE\.r-rv\bin"

# rv-managed Ruby (exclusive ownership per ANNO manifest)
if ($rvRubyBin) {
    $defaultPolyglotPaths += $rvRubyBin
}

# R runtime lane (current unmanaged install)
$rExePath = Get-RExePath
if ($rExePath) {
    $defaultPolyglotPaths += (Split-Path -Parent $rExePath)
}

# DevKit toolchain (gcc, make) from RubyInstaller's MSYS2
$defaultPolyglotPaths += $devkitPaths

# System registrations (Git, Azure CLI, Vulkan, VS native toolchain)
$defaultPolyglotPaths += $systemRegistrationPaths

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

function Get-PolyglotPaths {
    $basePaths = $null

    if (Test-Path $CONFIG_FILE) {
        try {
            $cfg = Get-Content $CONFIG_FILE -Raw | ConvertFrom-Json
            if ($cfg.PolyglotPaths -and $cfg.PolyglotPaths.Count -gt 0) {
                $basePaths = @($cfg.PolyglotPaths)
            }
        } catch {
            # Fall back to defaults if config is unreadable
        }
    }

    if (-not $basePaths) {
        $basePaths = @($defaultPolyglotPaths)
    }

    # Always append live system registrations (VS/Azure/Vulkan/Git), even with custom config.
    $merged = @($basePaths + $systemRegistrationPaths) | Where-Object { $_ }
    return $merged | Select-Object -Unique
}

function Get-FreshMergedPath {
    $segments = @()
    foreach ($scope in @("User", "Machine")) {
        $raw = [Environment]::GetEnvironmentVariable("Path", $scope)
        if ([string]::IsNullOrWhiteSpace($raw)) { continue }
        $segments += ($raw -split ';' | Where-Object { $_ })
    }
    return ($segments | Select-Object -Unique) -join ';'
}

function Get-ChthonicStrategicDocs {
    return @(
        [pscustomobject]@{
            key = "migration"
            title = "Laptop to Desktop Emigration"
            path = (Join-Path $REPO_ROOT "codex\artifacts\LAPTOP_TO_DESKTOP_EMIGRATION.md")
            commands = @(
                "toolchain hierarchy",
                "toolchain verify",
                "toolchain paths",
                "r lane",
                "zig lane"
            )
        }
        [pscustomobject]@{
            key = "next"
            title = "Codex Next"
            path = (Join-Path $REPO_ROOT "codex\NEXT.md")
            commands = @(
                "memory session",
                "commands counts",
                "commands inventory"
            )
        }
        [pscustomobject]@{
            key = "cheatsheet"
            title = "Oxidized Polyglot Surface"
            path = (Join-Path $REPO_ROOT "docs\OXIDIZED_POLYGLOT_SURFACE.md")
            commands = @(
                "memory map",
                "toolchain hierarchy",
                "commands inventory"
            )
        }
    )
}

function Get-ChthonicSemanticMetadata {
    return @{
        env = [pscustomobject]@{
            guide = "Activate the repo's in-house desktop toolchain shell."
            operator = "Session-scoped PATH/binding activation."
            capability = [pscustomobject]@{
                observe = @("effective command bindings", "current lane visibility")
                change = @("current shell environment only")
                limits = @("does not install toolchains", "does not rewrite repo pins")
                pins = @()
                retention = "No version mutation; session activation only."
            }
        }
        status = [pscustomobject]@{
            guide = "See what is actually available on this machine right now."
            operator = "Read-only machine + toolchain state snapshot."
            capability = [pscustomobject]@{
                observe = @("manager versions", "resolved command paths", "platform bindings")
                change = @()
                limits = @("observation only")
                pins = @()
                retention = "Read-only."
            }
        }
        doctor = [pscustomobject]@{
            guide = "Check what is outdated, what is pinned, and what can be fixed safely."
            operator = "Version/EOL drift analysis plus bounded upgrade/install vectors."
            capability = [pscustomobject]@{
                observe = @("installed versions", "repo pins", "endoflife.date targets", "optional missing lanes")
                change = @("manager-driven upgrades when --fix is used")
                limits = @("does not upgrade every language blindly", "respects repo pins such as rust-toolchain.toml and .python-version", "cannot install versions a manager does not publish")
                pins = @(".python-version", "rust-toolchain.toml")
                retention = "Most managers retain installed versions; bun replaces the active binary."
            }
        }
        toolchain = [pscustomobject]@{
            guide = "Inspect the intended toolchain hierarchy before changing the desktop."
            operator = "Control-plane summary for lane ownership and command resolution."
            capability = [pscustomobject]@{
                observe = @("tool ownership", "path resolution", "lane hierarchy")
                change = @("verifier/scan commands only when invoked")
                limits = @("not a universal installer", "hierarchy is descriptive unless an action subcommand is called")
                pins = @("toolchain config files when present")
                retention = "Mostly observational; delegated actions follow underlying tool semantics."
            }
        }
        python = [pscustomobject]@{
            guide = "One-line Python + uv state."
            operator = "Reports active interpreter path, uv version, and repo pin."
            capability = [pscustomobject]@{
                observe = @("uv", "active python", ".python-version")
                change = @()
                limits = @("lane view only; use doctor/new for mutation")
                pins = @(".python-version")
                retention = "uv python upgrade <series> upgrades within the lane; old patches remain in the store until uv python uninstall is run."
            }
        }
        bun = [pscustomobject]@{
            guide = "One-line Bun + Node state."
            operator = "Reports bun binary and detectable Node runtime."
            capability = [pscustomobject]@{
                observe = @("bun", "node")
                change = @()
                limits = @("lane view only", "Node may be absent even when bun is present")
                pins = @()
                retention = "bun is a single active binary."
            }
        }
        rust = [pscustomobject]@{
            guide = "One-line Rust toolchain state."
            operator = "Reports rustup, rustc, cargo, and toolchain pin."
            capability = [pscustomobject]@{
                observe = @("rustup", "rustc", "cargo", "rust-toolchain.toml")
                change = @()
                limits = @("lane view only; doctor handles bounded upgrade logic")
                pins = @("rust-toolchain.toml")
                retention = "rustup retains toolchains/components unless pruned."
            }
        }
        go = [pscustomobject]@{
            guide = "One-line Go + goup state."
            operator = "Reports goup and active Go runtime path."
            capability = [pscustomobject]@{
                observe = @("goup", "go")
                change = @()
                limits = @("lane view only")
                pins = @()
                retention = "goup keeps versions and switches the current link."
            }
        }
        ruby = [pscustomobject]@{
            guide = "One-line Ruby lane plus a richer Ruby management surface."
            operator = "Reports rv-managed Ruby plus DevKit and tool inventory."
            capability = [pscustomobject]@{
                observe = @("rv", "ruby", "gcc", "make", "pacman", "installed Ruby tools")
                change = @("rv Ruby installs/upgrades through explicit ruby subcommands")
                limits = @("lane view only unless a Ruby action is chosen")
                pins = @("rv ruby pin")
                retention = "rv installs versions side-by-side."
            }
        }
        r = [pscustomobject]@{
            guide = "One-line R runtime + rv-r package lane."
            operator = "Reports unmanaged R runtime and repo wrapper state."
            capability = [pscustomobject]@{
                observe = @("R", "Rscript", "rv-r")
                change = @()
                limits = @("runtime manager intentionally none")
                pins = @()
                retention = "Read-only lane view."
            }
        }
        zig = [pscustomobject]@{
            guide = "One-line Zig + zv state."
            operator = "Reports manager and active Zig runtime."
            capability = [pscustomobject]@{
                observe = @("zv", "zig")
                change = @()
                limits = @("lane view only")
                pins = @()
                retention = "zv-managed runtimes are retained in manager storage."
            }
        }
    }
}

function Get-ChthonicCommandCatalog {
    $catalog = @(
        [pscustomobject]@{
            domain = "env"
            mode = "canonical"
            summary = "Activate polyglot environment"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @()
        }
        [pscustomobject]@{
            domain = "status"
            mode = "canonical"
            summary = "Show tool + manager versions"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @()
        }
        [pscustomobject]@{
            domain = "trend"
            mode = "canonical"
            summary = "Rustification trend tracker"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @()
        }
        [pscustomobject]@{
            domain = "oversight"
            mode = "canonical"
            summary = "Hierarchical upcycle oversight stack"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @()
        }
        [pscustomobject]@{
            domain = "doctor"
            mode = "canonical"
            summary = "Check versions + origins + EOL state"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @()
        }
        [pscustomobject]@{
            domain = "detect"
            mode = "canonical"
            summary = "Detect IDE and environment context"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @()
        }
        [pscustomobject]@{
            domain = "toolchain"
            mode = "canonical"
            summary = "High-level verified toolchain control plane"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "hierarchy"; aliases = @("status", "lane"); summary = "ordered lane hierarchy + current command resolution" }
                [pscustomobject]@{ name = "verify"; aliases = @(); summary = "run extension host verifier in a fresh env merge" }
                [pscustomobject]@{ name = "scan"; aliases = @(); summary = "run toolpool scan in the extension lane" }
                [pscustomobject]@{ name = "paths"; aliases = @(); summary = "show resolved command ownership/paths" }
            )
        }
        [pscustomobject]@{
            domain = "memory"
            mode = "canonical"
            summary = "Strategic runbooks + session wisdom"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "map"; aliases = @("status", "list"); summary = "show strategic doc map + linked commands" }
                [pscustomobject]@{ name = "migration"; aliases = @(); summary = "show migration runbook anchors" }
                [pscustomobject]@{ name = "next"; aliases = @(); summary = "show current waypoint anchors" }
                [pscustomobject]@{ name = "cheatsheet"; aliases = @(); summary = "show cheatsheet anchors" }
                [pscustomobject]@{ name = "session"; aliases = @("wisdom"); summary = "synthesize the current winning state + command surface" }
            )
        }
        [pscustomobject]@{
            domain = "commands"
            mode = "canonical"
            summary = "Count and audit the live command surface"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "inventory"; aliases = @("matrix", "surface"); summary = "show domains, actions, compatibility watch, and wrapper reach" }
                [pscustomobject]@{ name = "counts"; aliases = @(); summary = "show command/subcommand totals without flags or open-ended args" }
                [pscustomobject]@{ name = "guide"; aliases = @(); summary = "show human-facing guide output from the semantic core" }
            )
        }
        [pscustomobject]@{
            domain = "ruby"
            mode = "canonical"
            summary = "Ruby lane via rv + RubyGems"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "versions"; aliases = @("rubies", "list"); summary = "list installed/available Rubies" }
                [pscustomobject]@{ name = "tools"; aliases = @("tool-list", "installed"); summary = "list rv-installed Ruby CLI tools" }
                [pscustomobject]@{ name = "lane"; aliases = @("status"); summary = "Ruby lane summary (rv + ruby + gcc + make + pacman)" }
                [pscustomobject]@{ name = "doctor"; aliases = @(); summary = "detect/repair stale rv Ruby state" }
                [pscustomobject]@{ name = "upgrade"; aliases = @("install-latest", "latest"); summary = "install latest stable Ruby if newer" }
                [pscustomobject]@{ name = "search"; aliases = @(); summary = "search RubyGems.org" }
                [pscustomobject]@{ name = "install"; aliases = @(); summary = "install via rv tool install" }
            )
        }
        [pscustomobject]@{
            domain = "python"
            mode = "canonical"
            summary = "Python runtime + uv lane"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "lane"; aliases = @("status"); summary = "uv + active Python runtime + pin state" }
            )
        }
        [pscustomobject]@{
            domain = "bun"
            mode = "canonical"
            summary = "Bun runtime + Node lane"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "lane"; aliases = @("status"); summary = "bun + active Node runtime state" }
            )
        }
        [pscustomobject]@{
            domain = "rust"
            mode = "canonical"
            summary = "Rust toolchain lane"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "lane"; aliases = @("status"); summary = "rustup + rustc + cargo + toolchain pin" }
            )
        }
        [pscustomobject]@{
            domain = "go"
            mode = "canonical"
            summary = "Go runtime + goup lane"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "lane"; aliases = @("status"); summary = "goup + active Go runtime state" }
            )
        }
        [pscustomobject]@{
            domain = "r"
            mode = "canonical"
            summary = "R runtime + rv-r package lane"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "lane"; aliases = @("status"); summary = "current unmanaged R runtime + rv-r state" }
            )
        }
        [pscustomobject]@{
            domain = "zig"
            mode = "canonical"
            summary = "Zig runtime + zv lane"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "lane"; aliases = @("status"); summary = "zv + active zig state" }
            )
        }
        [pscustomobject]@{
            domain = "graphics"
            mode = "canonical"
            summary = "GPU / Vulkan / shader / MSVC lane snapshot"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "lane"; aliases = @("status"); summary = "GPU / Vulkan / shader / MSVC lane snapshot" }
            )
        }
        [pscustomobject]@{
            domain = "poe"
            mode = "canonical"
            summary = "Poe account routing + Poe lanes"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "account"; aliases = @(); summary = "shell-local account routing + mapping" }
                [pscustomobject]@{ name = "models"; aliases = @(); summary = "list models" }
                [pscustomobject]@{ name = "probe"; aliases = @(); summary = "run transport probe + mailbox emission" }
                [pscustomobject]@{ name = "chat"; aliases = @(); summary = "run a chat request" }
                [pscustomobject]@{ name = "sdk-probe"; aliases = @(); summary = "probe fastapi-poe SDK lane" }
                [pscustomobject]@{ name = "audit"; aliases = @(); summary = "audit Poe transport state" }
            )
        }
        [pscustomobject]@{
            domain = "ide"
            mode = "canonical"
            summary = "IDE management"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "launch"; aliases = @(); summary = "launch Claude Code IDE" }
                [pscustomobject]@{ name = "detect"; aliases = @(); summary = "check IDE status" }
                [pscustomobject]@{ name = "reset"; aliases = @(); summary = "reset IDE configuration" }
            )
        }
        [pscustomobject]@{
            domain = "mcp"
            mode = "canonical"
            summary = "MCP + bridge services"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "start"; aliases = @(); summary = "start MCP services" }
                [pscustomobject]@{ name = "stop"; aliases = @(); summary = "stop MCP services" }
                [pscustomobject]@{ name = "status"; aliases = @(); summary = "check service status" }
                [pscustomobject]@{ name = "logs"; aliases = @(); summary = "tail service logs" }
            )
        }
        [pscustomobject]@{
            domain = "config"
            mode = "canonical"
            summary = "Configuration (~/.chthonic/)"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "init"; aliases = @(); summary = "initialize configuration" }
                [pscustomobject]@{ name = "show"; aliases = @(); summary = "display configuration" }
                [pscustomobject]@{ name = "set"; aliases = @(); summary = "set configuration value" }
            )
        }
        [pscustomobject]@{
            domain = "new"
            mode = "canonical"
            summary = "Scaffold polyglot projects"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "uv-python-app"; aliases = @(); summary = "uv init --app --package" }
                [pscustomobject]@{ name = "uv-python-lib"; aliases = @(); summary = "uv init --lib --package" }
                [pscustomobject]@{ name = "bun-react"; aliases = @(); summary = "bun init --react" }
                [pscustomobject]@{ name = "bun-react-tailwind"; aliases = @(); summary = "bun init --react=tailwind" }
                [pscustomobject]@{ name = "bun-next"; aliases = @(); summary = "bun create next-app" }
                [pscustomobject]@{ name = "cargo-rust-bin"; aliases = @(); summary = "cargo new --bin" }
                [pscustomobject]@{ name = "cargo-rust-lib"; aliases = @(); summary = "cargo new --lib" }
                [pscustomobject]@{ name = "go-basic"; aliases = @(); summary = "go mod init + main.go" }
                [pscustomobject]@{ name = "ruby-gem"; aliases = @(); summary = "bundle gem" }
                [pscustomobject]@{ name = "azure-azd-template"; aliases = @(); summary = "azd init --template" }
            )
        }
        [pscustomobject]@{
            domain = "workflow"
            mode = "canonical"
            summary = "Higher-level orchestrated profiles"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "control-plane"; aliases = @(); summary = "validate status, shell probe, ssot queue/drift/lineage, MCP tool exposure" }
                [pscustomobject]@{ name = "toolchain-governance"; aliases = @(); summary = "validate doctor/origins/toolchain probe surfaces" }
            )
        }
        [pscustomobject]@{
            domain = "shell"
            mode = "canonical"
            summary = "Experimental shell lane + capability probe"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "probe"; aliases = @(); summary = "show detected shell lanes" }
                [pscustomobject]@{ name = "brush"; aliases = @(); summary = "launch Brush" }
                [pscustomobject]@{ name = "pwsh"; aliases = @(); summary = "launch PowerShell 7" }
                [pscustomobject]@{ name = "bash"; aliases = @(); summary = "launch Bash" }
            )
        }
        [pscustomobject]@{
            domain = "ssot"
            mode = "canonical"
            summary = "SSOT loremaster control plane"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "queue"; aliases = @(); summary = "show SSOT queue" }
                [pscustomobject]@{ name = "entity"; aliases = @(); summary = "lookup entity" }
                [pscustomobject]@{ name = "section"; aliases = @(); summary = "lookup section" }
                [pscustomobject]@{ name = "drift"; aliases = @(); summary = "show drift" }
                [pscustomobject]@{ name = "lineage"; aliases = @(); summary = "show lineage" }
            )
        }
        [pscustomobject]@{
            domain = "book"
            mode = "canonical"
            summary = "mdBook documentation lane"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "build"; aliases = @(); summary = "build docs" }
                [pscustomobject]@{ name = "serve"; aliases = @(); summary = "serve docs" }
                [pscustomobject]@{ name = "clean"; aliases = @(); summary = "clean docs" }
            )
        }
        [pscustomobject]@{
            domain = "gemini"
            mode = "canonical"
            summary = "Gemini CLI workspace dep (bun-managed repo-local lane)"
            preferred_surface = $null
            claudine_passthrough = $true
            actions = @(
                [pscustomobject]@{ name = "update"; aliases = @("upgrade"); summary = "update Gemini CLI to latest in both home-dir and repo workspaces; validates bun audit in both scopes" }
            )
        }
        [pscustomobject]@{
            domain = "claudine"
            mode = "compatibility"
            summary = "Compatibility alias to env"
            preferred_surface = "chthonic env"
            claudine_passthrough = $true
            actions = @()
        }
        [pscustomobject]@{
            domain = "audit"
            mode = "compatibility"
            summary = "Single-word archive compatibility route"
            preferred_surface = "keep stable; do not expand beyond archive routing"
            claudine_passthrough = $true
            actions = @()
        }
        [pscustomobject]@{
            domain = "compact"
            mode = "compatibility"
            summary = "Single-word archive compatibility route"
            preferred_surface = "keep stable; do not expand beyond archive routing"
            claudine_passthrough = $true
            actions = @()
        }
        [pscustomobject]@{
            domain = "extract"
            mode = "compatibility"
            summary = "Single-word archive compatibility route"
            preferred_surface = "keep stable; do not expand beyond archive routing"
            claudine_passthrough = $true
            actions = @()
        }
        [pscustomobject]@{
            domain = "resolve"
            mode = "compatibility"
            summary = "Single-word archive compatibility route"
            preferred_surface = "keep stable; do not expand beyond archive routing"
            claudine_passthrough = $true
            actions = @()
        }
        [pscustomobject]@{
            domain = "map"
            mode = "compatibility"
            summary = "Single-word archive compatibility route"
            preferred_surface = "keep stable; do not expand beyond archive routing"
            claudine_passthrough = $true
            actions = @()
        }
        [pscustomobject]@{
            domain = "analyze"
            mode = "compatibility"
            summary = "Single-word archive compatibility route"
            preferred_surface = "keep stable; do not expand beyond archive routing"
            claudine_passthrough = $true
            actions = @()
        }
        [pscustomobject]@{
            domain = "claude-ide"
            mode = "compatibility"
            summary = "Legacy alias to ide launch"
            preferred_surface = "chthonic ide launch"
            claudine_passthrough = $true
            actions = @()
        }
    )

    $semantic = Get-ChthonicSemanticMetadata
    return @($catalog | ForEach-Object {
        $entrySemantic = if ($semantic.ContainsKey($_.domain)) { $semantic[$_.domain] } else {
            [pscustomobject]@{
                guide = $_.summary
                operator = $_.summary
                capability = [pscustomobject]@{
                    observe = @()
                    change = @()
                    limits = @()
                    pins = @()
                    retention = "Not specified."
                }
            }
        }
        [pscustomobject]@{
            domain = $_.domain
            mode = $_.mode
            summary = $_.summary
            preferred_surface = $_.preferred_surface
            claudine_passthrough = $_.claudine_passthrough
            actions = $_.actions
            guide = $entrySemantic.guide
            operator = $entrySemantic.operator
            capability = $entrySemantic.capability
        }
    })
}

function Get-ChthonicCommandSurfacePayload {
    $catalog = @(Get-ChthonicCommandCatalog)
    $canonicalDomains = @($catalog | Where-Object { $_.mode -eq "canonical" })
    $compatibilityDomains = @($catalog | Where-Object { $_.mode -eq "compatibility" })

    $canonicalFormCount = (($canonicalDomains | ForEach-Object {
        if ($_.actions.Count -gt 0) { $_.actions.Count } else { 1 }
    }) | Measure-Object -Sum).Sum

    $compatibilityFormCount = (($compatibilityDomains | ForEach-Object {
        if ($_.actions.Count -gt 0) { $_.actions.Count } else { 1 }
    }) | Measure-Object -Sum).Sum

    $actionAliasCount = (($catalog | ForEach-Object {
        @($_.actions | ForEach-Object { @($_.aliases).Count })
    }) | Measure-Object -Sum).Sum

    if ($null -eq $actionAliasCount) { $actionAliasCount = 0 }

    $domains = @($catalog | ForEach-Object {
        $actionNames = @($_.actions | ForEach-Object { $_.name })
        $actionAliases = @($_.actions | ForEach-Object { $_.aliases } | Where-Object { $_ })

        [pscustomobject]@{
            domain = $_.domain
            mode = $_.mode
            summary = $_.summary
            preferred_surface = $_.preferred_surface
            claudine_passthrough = $_.claudine_passthrough
            action_count = $_.actions.Count
            action_names = @($actionNames)
            action_aliases = @($actionAliases)
        }
    })

    $compatibilityWatch = @($domains |
        Where-Object { $_.mode -eq "compatibility" } |
        Sort-Object domain |
        ForEach-Object {
            [pscustomobject]@{
                domain = $_.domain
                summary = $_.summary
                preferred_surface = $_.preferred_surface
            }
        }
    )

    $directFormCount = $canonicalFormCount + $compatibilityFormCount

    return [pscustomobject]@{
        summary = [pscustomobject]@{
            canonical_domains = $canonicalDomains.Count
            compatibility_domains = $compatibilityDomains.Count
            canonical_documented_forms = $canonicalFormCount
            direct_documented_forms = $directFormCount
            nested_action_aliases = $actionAliasCount
            claudine_forwarded_forms = $directFormCount
            claudine_default_forms = 1
            combined_entrypoint_reach = ($directFormCount * 2) + 1
            counting_scope = "domains + documented actions; flags and open-ended free-form args are not counted"
        }
        domains = @($domains | Sort-Object @{ Expression = { if ($_.mode -eq "canonical") { 0 } else { 1 } } }, domain)
        compatibility_watch = @($compatibilityWatch)
    }
}

function Write-ChthonicCommandSurfaceSummary {
    param(
        [Parameter(Mandatory = $true)]$Summary,
        [string]$Indent = "  "
    )

    Write-Host ("{0}surface" -f $Indent) -ForegroundColor Cyan
    Write-Host ("{0}  canonical domains      {1}" -f $Indent, $Summary.canonical_domains) -ForegroundColor White
    Write-Host ("{0}  compatibility domains  {1}" -f $Indent, $Summary.compatibility_domains) -ForegroundColor White
    Write-Host ("{0}  canonical forms        {1}" -f $Indent, $Summary.canonical_documented_forms) -ForegroundColor White
    Write-Host ("{0}  direct forms total     {1}" -f $Indent, $Summary.direct_documented_forms) -ForegroundColor White
    Write-Host ("{0}  action aliases         {1}" -f $Indent, $Summary.nested_action_aliases) -ForegroundColor White
    Write-Host ("{0}  claudine forwards      {1}" -f $Indent, $Summary.claudine_forwarded_forms) -ForegroundColor White
    Write-Host ("{0}  claudine default       {1}" -f $Indent, $Summary.claudine_default_forms) -ForegroundColor White
    Write-Host ("{0}  combined reach         {1}" -f $Indent, $Summary.combined_entrypoint_reach) -ForegroundColor White
    Write-Host ("{0}  scope                  {1}" -f $Indent, $Summary.counting_scope) -ForegroundColor DarkGray
}

function Write-ChthonicCapabilityContract {
    param(
        [Parameter(Mandatory = $true)]$Entry,
        [string]$Indent = "  "
    )

    Write-Host ("{0}{1}" -f $Indent, $Entry.domain) -ForegroundColor Cyan
    Write-Host ("{0}  guide     {1}" -f $Indent, $Entry.guide) -ForegroundColor White
    Write-Host ("{0}  operator  {1}" -f $Indent, $Entry.operator) -ForegroundColor DarkGray
    if ($Entry.capability.observe.Count -gt 0) {
        Write-Host ("{0}  observes  {1}" -f $Indent, ($Entry.capability.observe -join ", ")) -ForegroundColor DarkGray
    }
    if ($Entry.capability.change.Count -gt 0) {
        Write-Host ("{0}  changes   {1}" -f $Indent, ($Entry.capability.change -join ", ")) -ForegroundColor DarkGray
    }
    if ($Entry.capability.limits.Count -gt 0) {
        Write-Host ("{0}  limits    {1}" -f $Indent, ($Entry.capability.limits -join "; ")) -ForegroundColor Yellow
    }
    if ($Entry.capability.pins.Count -gt 0) {
        Write-Host ("{0}  pins      {1}" -f $Indent, ($Entry.capability.pins -join ", ")) -ForegroundColor DarkGray
    }
    Write-Host ("{0}  retains   {1}" -f $Indent, $Entry.capability.retention) -ForegroundColor DarkGray
}

function Get-ChthonicGuidePayload {
    $focusDomains = @("env", "status", "doctor", "python", "rust", "go", "bun", "toolchain", "memory")
    $catalog = @($focusDomains | ForEach-Object {
        Get-ChthonicCatalogDomain -Domain $_
    } | Where-Object { $_ })

    $startHere = @(
        [pscustomobject]@{
            command = "claudine start"
            summary = "desktop-oriented overview of what is actually bound right now"
        }
        [pscustomobject]@{
            command = "claudine repair"
            summary = "safe doctor dry-run before changing the desktop state"
        }
        [pscustomobject]@{
            command = "chthonic env"
            summary = "activate the in-house desktop toolchain shell"
        }
    )

    $domains = @($catalog | ForEach-Object {
        [pscustomobject]@{
            domain = $_.domain
            guide = $_.guide
            operator = $_.operator
            limits = @($_.capability.limits)
            pins = @($_.capability.pins)
            suggested_command = if ($_.domain -in @("env", "status", "doctor")) {
                "claudine $($_.domain)"
            } else {
                "claudine $($_.domain) lane"
            }
        }
    })

    return [pscustomobject]@{
        entrypoint = "claudine"
        default_action = "env"
        start_here = $startHere
        domains = $domains
        notes = @(
            "Claudine is the human-facing guide shell; chthonic is the execution shell.",
            "Use `chthonic commands inventory` for the full operator matrix.",
            "Guide output is generated from the semantic core, not a separate domain list."
        )
    }
}

function Write-ChthonicGuide {
    param([Parameter(Mandatory = $true)]$GuidePayload)

    Write-Host ""
    Write-Host "CHTHONIC GUIDE" -ForegroundColor Cyan
    Write-Host ("="*72) -ForegroundColor DarkGray
    Write-Host "  start here" -ForegroundColor Cyan
    foreach ($entry in $GuidePayload.start_here) {
        Write-Host ("    {0,-26} {1}" -f $entry.command, $entry.summary) -ForegroundColor White
    }
    Write-Host ""
    Write-Host "  domains" -ForegroundColor Cyan
    foreach ($entry in $GuidePayload.domains) {
        Write-Host ("    {0,-12} {1}" -f $entry.domain, $entry.guide) -ForegroundColor White
        Write-Host ("      use: {0}" -f $entry.suggested_command) -ForegroundColor DarkGray
        if ($entry.limits.Count -gt 0) {
            Write-Host ("      limits: {0}" -f ($entry.limits -join "; ")) -ForegroundColor DarkGray
        }
        if ($entry.pins.Count -gt 0) {
            Write-Host ("      pins: {0}" -f ($entry.pins -join ", ")) -ForegroundColor DarkGray
        }
    }
    Write-Host ""
    Write-Host "  notes" -ForegroundColor Cyan
    foreach ($note in $GuidePayload.notes) {
        Write-Host ("    - {0}" -f $note) -ForegroundColor DarkGray
    }
    Write-Host ("="*72) -ForegroundColor DarkGray
    Write-Host ""
}

function Get-ChthonicCatalogDomain {
    param([Parameter(Mandatory = $true)][string]$Domain)
    return (Get-ChthonicCommandCatalog | Where-Object { $_.domain -eq $Domain } | Select-Object -First 1)
}

function Format-ChthonicActionLabel {
    param($Action)
    $label = [string]$Action.name
    if ($Action.aliases -and $Action.aliases.Count -gt 0) {
        $label += "|" + (($Action.aliases | ForEach-Object { [string]$_ }) -join "|")
    }
    return $label
}

function Show-DomainCatalogHelp {
    param(
        [Parameter(Mandatory = $true)][string]$Domain,
        [string]$EntryPoint = "chthonic"
    )

    $entry = Get-ChthonicCatalogDomain -Domain $Domain
    if (-not $entry) {
        Write-Host "$EntryPoint $Domain" -ForegroundColor Yellow
        return
    }

    Write-Host "$EntryPoint $($entry.domain) <action>" -ForegroundColor White
    Write-Host "  $($entry.summary)" -ForegroundColor DarkGray

    if ($entry.mode -eq "compatibility" -and $entry.preferred_surface) {
        Write-Host "  preferred surface: $($entry.preferred_surface)" -ForegroundColor DarkGray
    }

    if ($entry.actions.Count -eq 0) {
        Write-Host "  (no nested documented actions)" -ForegroundColor DarkGray
        return
    }

    foreach ($action in $entry.actions) {
        Write-Host ("  {0,-24} {1}" -f (Format-ChthonicActionLabel -Action $action), $action.summary) -ForegroundColor White
    }
}

function Show-CommandCatalogHelp {
    $payload = Get-ChthonicCommandSurfacePayload
    $canonical = @($payload.domains | Where-Object { $_.mode -eq "canonical" })
    $compatibility = @($payload.compatibility_watch)

    Write-Host ""
    Write-Host "Usage: chthonic [--version] [--help] <domain> [<action>] [<args>]" -ForegroundColor White
    Write-Host ""
    Write-Host "Canonical Domains" -ForegroundColor Cyan
    foreach ($domain in $canonical) {
        $actionPreview = if ($domain.action_names.Count -gt 0) { $domain.action_names -join "|" } else { "[direct]" }
        Write-Host ("  {0,-12} {1,-36} {2}" -f $domain.domain, $actionPreview, $domain.summary) -ForegroundColor White
    }
    Write-Host ""
    Write-Host "Compatibility Domains" -ForegroundColor Cyan
    foreach ($domain in $compatibility) {
        Write-Host ("  {0,-12} {1}" -f $domain.domain, $domain.preferred_surface) -ForegroundColor DarkGray
    }
    Write-Host ""
    Write-ChthonicCommandSurfaceSummary -Summary $payload.summary
    Write-Host ""
    Write-Host "Start Here" -ForegroundColor Cyan
    Write-Host "  chthonic env               - activate the in-house desktop toolchain shell" -ForegroundColor DarkGray
    Write-Host "  chthonic status            - see what is actually available right now" -ForegroundColor DarkGray
    Write-Host "  claudine doctor --dry-run  - see what the doctor can fix versus only observe" -ForegroundColor DarkGray
    Write-Host "  chthonic python lane       - one-line Python + uv state" -ForegroundColor DarkGray
    Write-Host "  chthonic rust lane         - one-line rustup/rustc/cargo + pin state" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "Notes" -ForegroundColor Cyan
    Write-Host "  --help is the human-facing catalog; `commands inventory` is the full matrix." -ForegroundColor DarkGray
    Write-Host "  Use `chthonic commands inventory` for the full live matrix." -ForegroundColor DarkGray
    Write-Host "  Use `claudine commands counts` to verify wrapper reach from the legacy entrypoint." -ForegroundColor DarkGray
    Write-Host ""
}

function Get-MarkdownHeadings {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [int]$Limit = 12
    )

    if (-not (Test-Path -LiteralPath $Path)) { return @() }

    return @(
        Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue |
            Where-Object { $_ -match '^(#+)\s+(.+)$' } |
            Select-Object -First $Limit |
            ForEach-Object {
                [pscustomobject]@{
                    level = ($matches[1]).Length
                    text = $matches[2].Trim()
                }
            }
    )
}

function Get-MarkdownSectionText {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Heading
    )

    if (-not (Test-Path -LiteralPath $Path)) { return $null }

    $lines = Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue
    if (-not $lines) { return $null }

    $startIndex = -1
    $startLevel = $null
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^(#+)\s+(.+)$') {
            $level = ($matches[1]).Length
            $title = $matches[2].Trim()
            if ($title -eq $Heading) {
                $startIndex = $i
                $startLevel = $level
                break
            }
        }
    }

    if ($startIndex -lt 0) { return $null }

    $buffer = New-Object System.Collections.Generic.List[string]
    for ($i = $startIndex; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($i -gt $startIndex -and $line -match '^(#+)\s+(.+)$') {
            $level = ($matches[1]).Length
            if ($level -le $startLevel) { break }
        }
        $buffer.Add($line)
    }

    return ($buffer -join "`n").Trim()
}

function Invoke-ExtensionToolingCommand {
    param(
        [Parameter(Mandatory = $true)][string]$ScriptRelativePath,
        [string[]]$Args = @()
    )

    $extensionRoot = Join-Path $REPO_ROOT "extensions\chthonic-archive"
    $scriptPath = Join-Path $extensionRoot $ScriptRelativePath
    if (-not (Test-Path -LiteralPath $scriptPath)) {
        return [pscustomobject]@{
            ExitCode = 1
            Output = @("Missing script: $scriptPath")
        }
    }

    $oldPath = $env:Path
    $env:Path = Get-FreshMergedPath
    Push-Location $extensionRoot
    try {
        $output = & bun run $ScriptRelativePath @Args 2>&1
        return [pscustomobject]@{
            ExitCode = $LASTEXITCODE
            Output = @($output | ForEach-Object { [string]$_ })
        }
    }
    finally {
        Pop-Location
        $env:Path = $oldPath
    }
}

function Get-ToolchainHierarchyPayload {
    $oldPath = $env:Path
    $env:Path = Get-FreshMergedPath
    try {
        $commands = @(
            "pwsh", "rv", "ruby", "gcc", "make", "pacman", "uv", "bun",
            "cargo", "rustup", "go", "goup", "brush", "solana",
            "agave-install", "avm", "anchor", "mise", "zv", "zig",
            "r", "rscript", "rv-r"
        ) | ForEach-Object {
            $meta = Get-CommandResolution -Name $_
            $resolvedPath = if ($meta) { if ($meta.Path) { $meta.Path } else { $meta.Display } } else { $null }

            if ($_ -eq "rv" -and (-not $resolvedPath -or $resolvedPath -eq "alias -> Remove-Variable")) {
                $rvExe = Get-RvExePath
                if ($rvExe) { $resolvedPath = $rvExe }
            }

            if ($_ -eq "go" -and -not $resolvedPath) {
                $goupGo = Join-Path $env:USERPROFILE ".goup\current\bin\go.exe"
                if (Test-Path $goupGo) { $resolvedPath = $goupGo }
            }

            if ($_ -eq "zv" -and -not $resolvedPath) {
                $zvExe = Get-ZvExePath
                if ($zvExe) { $resolvedPath = $zvExe }
            }

            if ($_ -eq "zig" -and -not $resolvedPath) {
                $zigExe = Get-ZigExePath
                if ($zigExe) { $resolvedPath = $zigExe }
            }

            if ($_ -eq "r") {
                $rExe = Get-RExePath
                if ($rExe) { $resolvedPath = $rExe }
            }

            if ($_ -eq "rscript") {
                $rscriptExe = Get-RScriptExePath
                if ($rscriptExe) { $resolvedPath = $rscriptExe }
            }

            if ($_ -eq "rv-r") {
                $rrvScript = Get-RRvScriptPath
                if ($rrvScript) { $resolvedPath = $rrvScript }
            }

            $resolvedVersion = Get-InstalledVersion $_
            if ($_ -eq "avm" -and -not $resolvedVersion -and $resolvedPath) {
                $resolvedVersion = "installed"
            }

            [pscustomobject]@{
                name = $_
                path = $resolvedPath
                version = $resolvedVersion
            }
        }

        $docs = @(Get-ChthonicStrategicDocs | ForEach-Object {
            [pscustomobject]@{
                key = $_.key
                title = $_.title
                path = $_.path
                exists = (Test-Path -LiteralPath $_.path)
                headings = @(Get-MarkdownHeadings -Path $_.path -Limit 8)
            }
        })

        return [pscustomobject]@{
            shell = [pscustomobject]@{
                path = (Get-FreshMergedPath)
                fresh_shell_required = $true
            }
            ordered_phases = @(
                "stabilize shell",
                "normalize ruby + devkit",
                "repair raw-shell path visibility",
                "repair brush windows hybrid lane",
                "bind graphics + native build surfaces",
                "bind openssl for native cargo",
                "bind solana + anchor",
                "publish r + zig control lanes",
                "rerun verifier in fresh env"
            )
            commands = @($commands)
            docs = @($docs)
            command_surface = (Get-ChthonicCommandSurfacePayload).summary
        }
    }
    finally {
        $env:Path = $oldPath
    }
}

function Invoke-ToolchainMeta {
    param(
        [string]$ToolchainAction,
        [string[]]$ToolchainArgs,
        [switch]$Json
    )

    switch ($ToolchainAction) {
        { $_ -in $null, "", "hierarchy", "status", "lane" } {
            $payload = Get-ToolchainHierarchyPayload
            if ($Json) {
                Write-Host (ConvertTo-Json $payload -Depth 8)
                return 0
            }

            Write-Host ""
            Write-Host "CHTHONIC TOOLCHAIN HIERARCHY" -ForegroundColor Cyan
            Write-Host ("="*72) -ForegroundColor DarkGray
            Write-Host "  phases" -ForegroundColor Cyan
            for ($i = 0; $i -lt $payload.ordered_phases.Count; $i++) {
                Write-Host ("    {0}. {1}" -f ($i + 1), $payload.ordered_phases[$i]) -ForegroundColor White
            }
            Write-Host ""
            Write-Host "  commands" -ForegroundColor Cyan
            foreach ($command in $payload.commands) {
                $version = if ($command.version) { $command.version } else { "unresolved" }
                $path = if ($command.path) { $command.path } else { "not found" }
                $color = if ($command.path) { "White" } else { "Red" }
                Write-Host ("    {0,-14} {1,-18} {2}" -f $command.name, $version, $path) -ForegroundColor $color
            }
            Write-Host ""
            Write-Host "  memory" -ForegroundColor Cyan
            foreach ($doc in $payload.docs) {
                Write-Host ("    {0,-12} {1}" -f $doc.key, $doc.path) -ForegroundColor White
            }
            Write-ChthonicCommandSurfaceSummary -Summary $payload.command_surface -Indent "  "
            Write-Host ("="*72) -ForegroundColor DarkGray
            Write-Host ""
            return 0
        }
        "scan" {
            $result = Invoke-ExtensionToolingCommand -ScriptRelativePath "scripts/toolpool-scan.ts" -Args $ToolchainArgs
            if ($result.Output) { $result.Output | ForEach-Object { Write-Host $_ } }
            return $result.ExitCode
        }
        "verify" {
            $result = Invoke-ExtensionToolingCommand -ScriptRelativePath "scripts/verify-host.ts" -Args $ToolchainArgs
            if ($result.Output) { $result.Output | ForEach-Object { Write-Host $_ } }
            return $result.ExitCode
        }
        "paths" {
            $payload = Get-ToolchainHierarchyPayload
            if ($Json) {
                Write-Host (ConvertTo-Json $payload.commands -Depth 6)
                return 0
            }
            Write-Host ""
            Write-Host "CHTHONIC TOOLCHAIN PATHS" -ForegroundColor Cyan
            Write-Host ("="*72) -ForegroundColor DarkGray
            foreach ($command in $payload.commands) {
                $path = if ($command.path) { $command.path } else { "not found" }
                $color = if ($command.path) { "White" } else { "Red" }
                Write-Host ("  {0,-14} {1}" -f $command.name, $path) -ForegroundColor $color
            }
            Write-Host ("="*72) -ForegroundColor DarkGray
            Write-Host ""
            return 0
        }
        default {
            Write-Host "chthonic toolchain <action>"
            Write-Host "  hierarchy         - ordered lane hierarchy + current command resolution"
            Write-Host "  verify            - run extension host verifier in a fresh env merge"
            Write-Host "  scan              - run toolpool scan in the extension lane"
            Write-Host "  paths             - show resolved command ownership/paths"
            return 0
        }
    }
}

function Invoke-MemoryLane {
    param(
        [string]$MemoryAction,
        [string[]]$MemoryArgs,
        [switch]$Json
    )

    $docs = @(Get-ChthonicStrategicDocs | ForEach-Object {
        [pscustomobject]@{
            key = $_.key
            title = $_.title
            path = $_.path
            exists = (Test-Path -LiteralPath $_.path)
            commands = @($_.commands)
            headings = @(Get-MarkdownHeadings -Path $_.path -Limit 10)
        }
    })

    switch ($MemoryAction) {
        { $_ -in $null, "", "map", "status", "list" } {
            if ($Json) {
                Write-Host (ConvertTo-Json $docs -Depth 6)
                return 0
            }
            Write-Host ""
            Write-Host "CHTHONIC MEMORY MAP" -ForegroundColor Cyan
            Write-Host ("="*72) -ForegroundColor DarkGray
            foreach ($doc in $docs) {
                Write-Host ("  {0,-12} {1}" -f $doc.key, $doc.path) -ForegroundColor White
                foreach ($heading in $doc.headings | Select-Object -First 5) {
                    Write-Host ("    - {0}" -f $heading.text) -ForegroundColor DarkGray
                }
                if ($doc.commands.Count -gt 0) {
                    Write-Host ("    commands: {0}" -f ($doc.commands -join ", ")) -ForegroundColor Cyan
                }
            }
            Write-ChthonicCommandSurfaceSummary -Summary (Get-ChthonicCommandSurfacePayload).summary -Indent "  "
            Write-Host ("="*72) -ForegroundColor DarkGray
            Write-Host ""
            return 0
        }
        { $_ -in "migration", "next", "cheatsheet" } {
            $doc = $docs | Where-Object { $_.key -eq $MemoryAction } | Select-Object -First 1
            if (-not $doc) {
                Write-Error "Unknown memory document: $MemoryAction"
                return 1
            }

            if ($Json) {
                Write-Host (ConvertTo-Json $doc -Depth 6)
                return 0
            }

            Write-Host ""
            Write-Host ("CHTHONIC MEMORY: {0}" -f $doc.title.ToUpperInvariant()) -ForegroundColor Cyan
            Write-Host ("="*72) -ForegroundColor DarkGray
            Write-Host ("  path     {0}" -f $doc.path) -ForegroundColor White
            Write-Host "  headings" -ForegroundColor Cyan
            foreach ($heading in $doc.headings) {
                Write-Host ("    - {0}" -f $heading.text) -ForegroundColor DarkGray
            }
            if ($doc.commands.Count -gt 0) {
                Write-Host "  commands" -ForegroundColor Cyan
                foreach ($command in $doc.commands) {
                    Write-Host ("    - {0}" -f $command) -ForegroundColor DarkGray
                }
            }
            Write-Host ("="*72) -ForegroundColor DarkGray
            Write-Host ""
            return 0
        }
        { $_ -in "session", "wisdom" } {
            $migrationPath = (Get-ChthonicStrategicDocs | Where-Object { $_.key -eq "migration" } | Select-Object -First 1).path
            $nextPath = (Get-ChthonicStrategicDocs | Where-Object { $_.key -eq "next" } | Select-Object -First 1).path

            $payload = [pscustomobject]@{
                winning_state = Get-MarkdownSectionText -Path $migrationPath -Heading "Current Winning State"
                canonical_order = Get-MarkdownSectionText -Path $migrationPath -Heading "Canonical Order"
                what_worked = Get-MarkdownSectionText -Path $migrationPath -Heading "What Worked"
                do_not_repeat = Get-MarkdownSectionText -Path $migrationPath -Heading "Do Not Repeat"
                strategic_next_steps = Get-MarkdownSectionText -Path $migrationPath -Heading "Strategic Next Steps"
                toolchain_overlay = Get-MarkdownSectionText -Path $nextPath -Heading "Toolchain Overlay (2026-03-23)"
                pending_work = Get-MarkdownSectionText -Path $nextPath -Heading "Pending Work"
                command_surface = (Get-ChthonicCommandSurfacePayload).summary
            }

            if ($Json) {
                Write-Host (ConvertTo-Json $payload -Depth 6)
                return 0
            }

            Write-Host ""
            Write-Host "CHTHONIC SESSION WISDOM" -ForegroundColor Cyan
            Write-Host ("="*72) -ForegroundColor DarkGray
            foreach ($entry in @(
                @{ label = "Winning State"; text = $payload.winning_state },
                @{ label = "Canonical Order"; text = $payload.canonical_order },
                @{ label = "What Worked"; text = $payload.what_worked },
                @{ label = "Do Not Repeat"; text = $payload.do_not_repeat },
                @{ label = "Strategic Next Steps"; text = $payload.strategic_next_steps },
                @{ label = "Toolchain Overlay"; text = $payload.toolchain_overlay },
                @{ label = "Pending Work"; text = $payload.pending_work }
            )) {
                if (-not $entry.text) { continue }
                Write-Host ("  {0}" -f $entry.label) -ForegroundColor Cyan
                $entry.text -split "`n" | ForEach-Object { Write-Host ("    {0}" -f $_) -ForegroundColor $(if ($_ -match '^#') { "White" } else { "DarkGray" }) }
                Write-Host ""
            }
            Write-ChthonicCommandSurfaceSummary -Summary $payload.command_surface -Indent "  "
            Write-Host ("="*72) -ForegroundColor DarkGray
            Write-Host ""
            return 0
        }
        default {
            Write-Host "chthonic memory <action>"
            Write-Host "  map               - show strategic doc map"
            Write-Host "  migration         - show migration runbook anchors"
            Write-Host "  next              - show current waypoint anchors"
            Write-Host "  cheatsheet        - show cheatsheet anchors"
            Write-Host "  session|wisdom    - synthesize this session's winning patterns"
            return 0
        }
    }
}

function Invoke-CommandSurface {
    param(
        [string]$CommandAction,
        [string[]]$CommandArgs,
        [switch]$Json
    )

    $script:CommandSurfaceJsonPayload = $null
    $payload = Get-ChthonicCommandSurfacePayload

    switch ($CommandAction) {
        { $_ -in $null, "", "inventory", "matrix", "surface" } {
            if ($Json) {
                $script:CommandSurfaceJsonPayload = ConvertTo-Json $payload -Depth 8
                return 0
            }

            Write-Host ""
            Write-Host "CHTHONIC COMMAND INVENTORY" -ForegroundColor Cyan
            Write-Host ("="*72) -ForegroundColor DarkGray
            Write-ChthonicCommandSurfaceSummary -Summary $payload.summary -Indent "  "
            Write-Host ""
            Write-Host "  domains" -ForegroundColor Cyan
            foreach ($domain in $payload.domains) {
                $modeColor = if ($domain.mode -eq "canonical") { "White" } else { "Yellow" }
                $actionsText = if ($domain.action_count -gt 0) { $domain.action_count } else { 0 }
                $wrapperText = if ($domain.claudine_passthrough) { "yes" } else { "no" }

                Write-Host ("    {0,-12} " -f $domain.domain) -NoNewline -ForegroundColor Cyan
                Write-Host ("{0,-13}" -f $domain.mode) -NoNewline -ForegroundColor $modeColor
                Write-Host (" actions={0,-2} claudine={1}" -f $actionsText, $wrapperText) -ForegroundColor DarkGray
                Write-Host ("      {0}" -f $domain.summary) -ForegroundColor DarkGray
                if ($domain.action_names.Count -gt 0) {
                    Write-Host ("      actions: {0}" -f ($domain.action_names -join ", ")) -ForegroundColor White
                }
                if ($domain.action_aliases.Count -gt 0) {
                    Write-Host ("      aliases: {0}" -f ($domain.action_aliases -join ", ")) -ForegroundColor DarkGray
                }
                if ($domain.preferred_surface) {
                    Write-Host ("      prefer: {0}" -f $domain.preferred_surface) -ForegroundColor DarkGray
                }
            }
            Write-Host ""
            Write-Host "  compatibility watch" -ForegroundColor Cyan
            foreach ($entry in $payload.compatibility_watch) {
                Write-Host ("    {0,-12} {1}" -f $entry.domain, $entry.summary) -ForegroundColor Yellow
                if ($entry.preferred_surface) {
                    Write-Host ("      prefer: {0}" -f $entry.preferred_surface) -ForegroundColor DarkGray
                }
            }
            Write-Host ("="*72) -ForegroundColor DarkGray
            Write-Host ""
            return 0
        }
        "counts" {
            if ($Json) {
                $script:CommandSurfaceJsonPayload = ConvertTo-Json $payload.summary -Depth 6
                return 0
            }

            Write-Host ""
            Write-Host "CHTHONIC COMMAND COUNTS" -ForegroundColor Cyan
            Write-Host ("="*72) -ForegroundColor DarkGray
            Write-ChthonicCommandSurfaceSummary -Summary $payload.summary -Indent "  "
            Write-Host ("="*72) -ForegroundColor DarkGray
            Write-Host ""
            return 0
        }
        "guide" {
            $guide = Get-ChthonicGuidePayload
            if ($Json) {
                $script:CommandSurfaceJsonPayload = ConvertTo-Json $guide -Depth 8
                return 0
            }
            Write-ChthonicGuide -GuidePayload $guide
            return 0
        }
        "contract" {
            $target = if ($CommandArgs.Count -gt 0) { $CommandArgs[0] } else { $null }
            if (-not $target) {
                Write-Host "chthonic commands contract <domain>" -ForegroundColor Yellow
                return 1
            }
            $entry = Get-ChthonicCatalogDomain -Domain $target
            if (-not $entry) {
                Write-Host "Unknown domain: $target" -ForegroundColor Red
                return 1
            }
            if ($Json) {
                $script:CommandSurfaceJsonPayload = ConvertTo-Json $entry -Depth 8
                return 0
            }
            Write-Host ""
            Write-Host "CHTHONIC COMMAND CONTRACT" -ForegroundColor Cyan
            Write-Host ("="*72) -ForegroundColor DarkGray
            Write-ChthonicCapabilityContract -Entry $entry -Indent "  "
            Write-Host ("="*72) -ForegroundColor DarkGray
            Write-Host ""
            return 0
        }
        default {
            Write-Host "chthonic commands <action>"
            Write-Host "  inventory|matrix  - show domains, subcommands, compatibility watch, wrapper reach"
            Write-Host "  counts            - show command/subcommand totals"
            Write-Host "  guide             - show human-facing guide output from the semantic core"
            Write-Host "  contract <domain> - show guide/operator/capability contract for one domain"
            return 0
        }
    }
}

function Show-StatusBanner {
    # Compact one-liner version probes grouped by manager
    $W = "White"; $C = "Cyan"; $D = "DarkGray"; $R = "Red"
    function ver($cmd) { try { $v = (& $cmd 2>$null); if ($v) { return ($v -split "`n")[0] } } catch {}; return $null }

    $oldPath = $env:Path
    $env:Path = Get-FreshMergedPath
    try {
        Write-Host "CHTHONIC v$VERSION" -ForegroundColor $C -NoNewline
        Write-Host " | " -ForegroundColor $D -NoNewline
        Write-Host "$REPO_ROOT" -ForegroundColor $W
        Write-Host ("="*72) -ForegroundColor $D

        # rv -> Ruby
        $rubyVer = ver { ruby -e "print RUBY_VERSION" }
        $rubyJitTag = $null
        try { $rubyCmd = Get-Command ruby -ErrorAction SilentlyContinue; if ($rubyCmd -and $rubyCmd.Source -match 'zjit') { $rubyJitTag = '+zjit' } } catch {}
        $rvwVer = ver { rvw --version }; if ($rvwVer -match '(\d+\.\d+\.\d+)') { $rvwVer = $matches[1] } else { $rvwVer = $null }
        $rvMeta = Get-CommandResolution -Name "rv"
        $rvVer = $null
        if ($rvMeta -and $rvMeta.Type -ne "Alias") {
            $rvProbe = ver { rv --version }
            if ($rvProbe -match '(\d+\.\d+\.\d+)') { $rvVer = $matches[1] }
        }
        if (-not $rvVer -and $rvwVer) { $rvVer = $rvwVer }
        Write-Host "  rv    " -NoNewline -ForegroundColor $C
        if ($rubyVer) { Write-Host "ruby $rubyVer$rubyJitTag" -NoNewline -ForegroundColor $W } else { Write-Host "ruby ?" -NoNewline -ForegroundColor $R }
        if ($rvVer) { Write-Host "  rv $rvVer" -NoNewline -ForegroundColor $D }
        if ($rvwVer) { Write-Host "  rvw $rvwVer" -NoNewline -ForegroundColor $D }

        # DevKit (gcc)
        $gccVer = ver { gcc -dumpfullversion }
        if ($gccVer) { Write-Host "  gcc $gccVer" -NoNewline -ForegroundColor $D }
        Write-Host ""

        # uv -> Python
        $pyVer = ver { uv run python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" }
        if (-not $pyVer) {
            $pyVerRaw = ver { python --version }
            if ($pyVerRaw -match 'Python\s+(\d+\.\d+\.\d+)') { $pyVer = $matches[1] }
        }
        $uvVer = ver { uv --version }; if ($uvVer -match '(\d+\.\d+\.\d+)') { $uvVer = $matches[1] } else { $uvVer = $null }
        $ruffVer = ver { ruff --version }; if ($ruffVer -match '(\d+\.\d+\.\d+)') { $ruffVer = $matches[1] } else { $ruffVer = $null }
        Write-Host "  uv    " -NoNewline -ForegroundColor $C
        if ($pyVer) { Write-Host "python $pyVer" -NoNewline -ForegroundColor $W } else { Write-Host "python ?" -NoNewline -ForegroundColor $R }
        if ($uvVer) { Write-Host "  uv $uvVer" -NoNewline -ForegroundColor $D }
        if ($ruffVer) { Write-Host "  ruff $ruffVer" -NoNewline -ForegroundColor $D }
        Write-Host ""

        # bun -> JS/TS
        $bunVer = ver { bun --version }
        $biomeVer = ver { biome --version }; if ($biomeVer) { $biomeVer = $biomeVer -replace 'Version:\s*','' }
        Write-Host "  bun   " -NoNewline -ForegroundColor $C
        if ($bunVer) { Write-Host "bun $bunVer" -NoNewline -ForegroundColor $W } else { Write-Host "bun ?" -NoNewline -ForegroundColor $R }
        if ($biomeVer) { Write-Host "  biome $biomeVer" -NoNewline -ForegroundColor $D }
        Write-Host "  (sql, react, test, bundle built-in)" -ForegroundColor $D

        # rustup -> Rust
        $rustVer = ver { rustc -V }; if ($rustVer) { $rustVer = ($rustVer -split ' ')[1] }
        $rustupVer = ver { rustup --version }; if ($rustupVer -match '(\d+\.\d+\.\d+)') { $rustupVer = $matches[1] } else { $rustupVer = $null }
        $cargoVer = ver { cargo --version }; if ($cargoVer -match '(\d+\.\d+\.\d+)') { $cargoVer = $matches[1] } else { $cargoVer = $null }
        Write-Host "  rust  " -NoNewline -ForegroundColor $C
        if ($rustVer) { Write-Host "rustc $rustVer" -NoNewline -ForegroundColor $W } else { Write-Host "rustc ?" -NoNewline -ForegroundColor $R }
        if ($rustupVer) { Write-Host "  rustup $rustupVer" -NoNewline -ForegroundColor $D }
        if ($cargoVer) { Write-Host "  cargo $cargoVer" -NoNewline -ForegroundColor $D }
        $mdbookVer = ver { mdbook --version }; if ($mdbookVer -match '(\d+\.\d+\.\d+)') { $mdbookVer = $matches[1] } else { $mdbookVer = $null }
        if ($mdbookVer) { Write-Host "  mdbook $mdbookVer" -NoNewline -ForegroundColor $D }
        Write-Host ""

        # Go (try PATH, then goup)
        $goVer = ver { go version }
        if (-not $goVer) { $goupGo = Join-Path $env:USERPROFILE ".goup\current\bin\go.exe"; if (Test-Path $goupGo) { $goVer = ver { & $goupGo version } } }
        if ($goVer -match 'go(\d+\.\d+\.\d+)') { $goVer = $matches[1] } else { $goVer = $null }
        $goupVer = ver { goup --version }
        if (($goupVer -join "`n") -match '(\d+\.\d+\.\d+)') { $goupVer = $matches[1] } else { $goupVer = $null }
        $miseVer = ver { mise --version }; if ($miseVer -match '(\d+\.\d+\.\d+)') { $miseVer = $matches[1] } else { $miseVer = $null }
        Write-Host "  go    " -NoNewline -ForegroundColor $C
        if ($goVer) { Write-Host "go $goVer" -NoNewline -ForegroundColor $W } else { Write-Host "go ?" -NoNewline -ForegroundColor $R }
        if ($goupVer) { Write-Host "  goup $goupVer" -NoNewline -ForegroundColor $D }
        if ($miseVer) { Write-Host "  mise $miseVer" -NoNewline -ForegroundColor $D }
        Write-Host ""

        # Zig + R
        $zvVer = ver { zv --version }; if ($zvVer -match '(\d+\.\d+\.\d+)') { $zvVer = $matches[1] } else { $zvVer = $null }
        $zigVer = ver { zig version }; if ($zigVer -match '([0-9][^\s]+)') { $zigVer = $matches[1] } else { $zigVer = $null }
        $rVer = $null
        $rExe = Get-RExePath
        if ($rExe) {
            try {
                $rOut = & $rExe --version 2>&1
                if (($rOut -join "`n") -match 'R version (\d+\.\d+\.\d+)') { $rVer = $matches[1] }
            } catch {}
        }
        $rrvVer = $null
        $rrvExe = Get-RRvExePath
        if ($rrvExe) {
            try {
                $rrvOut = & $rrvExe --version 2>$null
                if (($rrvOut -join "`n") -match '(\d+\.\d+\.\d+)') { $rrvVer = $matches[1] }
            } catch {}
        }
        Write-Host "  alt   " -NoNewline -ForegroundColor $C
        if ($zigVer) { Write-Host "zig $zigVer" -NoNewline -ForegroundColor $W } else { Write-Host "zig ?" -NoNewline -ForegroundColor $R }
        if ($zvVer) { Write-Host "  zv $zvVer" -NoNewline -ForegroundColor $D }
        if ($rVer) { Write-Host "  R $rVer" -NoNewline -ForegroundColor $W } else { Write-Host "  R ?" -NoNewline -ForegroundColor $R }
        if ($rrvVer) { Write-Host "  rv-r $rrvVer" -NoNewline -ForegroundColor $D }
        Write-Host ""

        # Chain / ecosystem managers
        $solanaVer = $null
        try {
            $solanaOut = & solana --version 2>$null
            if (($solanaOut -join "`n") -match 'solana-cli\s+([0-9][^\s]+)') { $solanaVer = $matches[1] }
        } catch {}
        $agaveVer = $null
        try {
            $agaveOut = & agave-install --version 2>$null
            if (($agaveOut -join "`n") -match 'agave-install\s+([0-9][^\s]+)') { $agaveVer = $matches[1] }
        } catch {}
        $anchorVer = $null
        try {
            $anchorOut = & anchor --version 2>$null
            if (($anchorOut -join "`n") -match 'anchor-cli\s+([0-9][^\s]+)') { $anchorVer = $matches[1] }
        } catch {}
        Write-Host "  chain " -NoNewline -ForegroundColor $C
        if ($solanaVer) { Write-Host "solana $solanaVer" -NoNewline -ForegroundColor $W } else { Write-Host "solana ?" -NoNewline -ForegroundColor $R }
        if ($agaveVer) { Write-Host "  agave $agaveVer" -NoNewline -ForegroundColor $D }
        if ($anchorVer) { Write-Host "  anchor $anchorVer" -NoNewline -ForegroundColor $D }
        Write-Host ""

        # AI CLI lane (standalone + shell wrappers)
        $claudeMeta = Get-CommandResolution -Name "claude"
        $claudineMeta = Get-CommandResolution -Name "claudine"
        $claudeVer = ver { claude --version }
        if ($claudeVer -match '(\d+\.\d+\.\d+)') { $claudeVer = $matches[1] }
        Write-Host "  ai    " -NoNewline -ForegroundColor $C
        if ($claudeMeta) {
            if ($claudeVer) {
                Write-Host "claude $claudeVer" -NoNewline -ForegroundColor $W
            } else {
                Write-Host "claude" -NoNewline -ForegroundColor $W
            }
        } else {
            Write-Host "claude ?" -NoNewline -ForegroundColor $R
        }
        if ($claudineMeta) {
            Write-Host "  claudine $($claudineMeta.Type.ToLower())" -NoNewline -ForegroundColor $D
        }
        Write-Host ""

        # Cloud + data tooling
        $azVer = Get-AzureCliVersion
        $ssmsVer = Get-SsmsVersion
        Write-Host "  cloud " -NoNewline -ForegroundColor $C
        if ($azVer) { Write-Host "az $azVer" -NoNewline -ForegroundColor $W } else { Write-Host "az ?" -NoNewline -ForegroundColor $R }
        if ($ssmsVer) { Write-Host "  ssms $ssmsVer" -NoNewline -ForegroundColor $D }
        Write-Host ""

        # Infra line
        $gitVer = ver { git --version }; if ($gitVer) { $gitVer = ($gitVer -replace 'git version\s*','') -replace '\.windows.*','' }
        $vulkanVer = if ($env:VULKAN_SDK -match '(\d+\.\d+\.\d+)') { $matches[1] } else { $null }
        $clExe = Get-VSClExePath
        $clVer = $null
        if ($clExe) {
            try {
                $clOut = & $clExe /Bv 2>$null
                if ($clOut -match 'Compiler Version ([0-9\.]+)') { $clVer = $matches[1] }
            } catch {}
            if (-not $clVer) { $clVer = "ready" }
        }
        $msbuildExe = Get-VSMsBuildExePath
        $msbuildVer = $null
        if ($msbuildExe) {
            try {
                $msbuildOut = & $msbuildExe -version -nologo 2>$null
                if ($msbuildOut) { $msbuildVer = (($msbuildOut | Select-Object -Last 1).ToString().Trim()) }
            } catch {}
        }
        $clangBin = Get-VSClangBinDir
        $clangVer = $null
        if ($clangBin) {
            try {
                $clangOut = & (Join-Path $clangBin "clang.exe") --version 2>$null
                if ($clangOut -and $clangOut[0] -match 'clang version ([0-9\.]+)') { $clangVer = $matches[1] }
            } catch {}
        }
        Write-Host "  sys   " -NoNewline -ForegroundColor $C
        Write-Host "git $gitVer" -NoNewline -ForegroundColor $D
        if ($vulkanVer) { Write-Host "  vulkan $vulkanVer" -NoNewline -ForegroundColor $D }
        if ($clVer) { Write-Host "  cl $clVer" -NoNewline -ForegroundColor $D }
        if ($msbuildVer) { Write-Host "  msbuild $msbuildVer" -NoNewline -ForegroundColor $D }
        if ($clangVer) { Write-Host "  clang $clangVer" -NoNewline -ForegroundColor $D }
        Write-Host ""
        Write-Host ("="*72) -ForegroundColor $D
    }
    finally {
        $env:Path = $oldPath
    }
}

function Show-Help {
    Show-CommandCatalogHelp
}

function Format-StatusKeyLabel {
    param([Parameter(Mandatory = $true)][string]$Key)

    return (($Key -replace '_', ' ') + ":").PadRight(28)
}

function Write-StatusSection {
    param(
        [Parameter(Mandatory = $true)][string]$Title,
        [Parameter(Mandatory = $true)][hashtable]$Tools,
        [Parameter(Mandatory = $true)][string[]]$Keys
    )

    Write-Host "  $Title" -ForegroundColor Cyan
    foreach ($key in $Keys) {
        if (-not $Tools.ContainsKey($key)) { continue }

        $value = [string]$Tools[$key]
        $label = Format-StatusKeyLabel -Key $key
        $valueColor = if ($value -eq "not found") { "Red" } else { "White" }

        Write-Host "    $label" -NoNewline -ForegroundColor DarkGray
        Write-Host $value -ForegroundColor $valueColor
    }
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# ENVIRONMENT & SERVICE DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

function Get-EnvironmentContext {
    # Detect if running in VS Code or standalone
    $context = @{
        IsVSCode = $false
        IsCI = $env:CI -eq "true"
        IsWSL = $false
        Terminal = $env:TERM_PROGRAM
        Shell = $PROFILE.Split('\')[-1]
    }
    
    # Check for VS Code integrated terminal
    if ($env:TERM_PROGRAM -eq "vscode" -or $PSVersionTable.Platform -eq "Unix" -and (Test-Path "/.wsl")) {
        $context.IsVSCode = $true
    }
    
    # Check for WSL
    if ((Test-Path "/func/version") -or (Test-Path "/proc/version")) {
        $context.IsWSL = $true
    }
    
    return $context
}

function Get-ServiceStatus {
    $status = @{
        MCP = $null
        Bridge = $null
        Timestamp = Get-Date
    }
    
    # Check MCP server (port 9999)
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:9999/health" -TimeoutSec 1 -ErrorAction SilentlyContinue
        $status.MCP = "running"
    }
    catch {
        $status.MCP = "stopped"
    }
    
    # Check bridge server (port 8888)
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8888/status" -TimeoutSec 1 -ErrorAction SilentlyContinue
        $status.Bridge = "running"
    }
    catch {
        $status.Bridge = "stopped"
    }
    
    return $status
}

# ═══════════════════════════════════════════════════════════════════════════════
# IDE MANAGEMENT (consolidated from launch-claude-ide.ps1)
# ═══════════════════════════════════════════════════════════════════════════════

function Invoke-IDELaunch {
    param([string]$WorkspacePath = $REPO_ROOT)
    
    $ideExecutable = if (Get-Command code-insiders -ErrorAction SilentlyContinue) {
        "code-insiders"
    } elseif (Get-Command code -ErrorAction SilentlyContinue) {
        "code"
    } else {
        Write-Error "❌ VS Code not found in PATH"
        return 1
    }
    
    # Verify Claude Code extension
    $extensionPath = "$env:APPDATA\Code - Insiders\User\extensions"
    if (-not (Test-Path $extensionPath) -or -not (Get-ChildItem $extensionPath -Filter "*claude*" -ErrorAction SilentlyContinue)) {
        Write-Host "⚠️  Claude Code extension not found. Install it:" -ForegroundColor Yellow
        Write-Host "   Extensions → Search 'Claude Code' → Install @anthropic-ai/claude-code" -ForegroundColor Gray
    }
    
    # Launch Claude Code with full endpoint
    Push-Location $WorkspacePath
    try {
        Write-Host "🚀 Launching Claude Code IDE from: $WorkspacePath" -ForegroundColor Cyan
        Write-Host "   IDE: $ideExecutable" -ForegroundColor Gray
        & $ideExecutable "$WorkspacePath" 2>&1 | Out-Null
        
        # Give IDE time to start before returning
        Start-Sleep -Milliseconds 500
        return 0
    }
    catch {
        Write-Error "Failed to launch IDE: $_"
        return 1
    }
    finally {
        Pop-Location
    }
}

function Invoke-IDEDetect {
    param([switch]$Json)
    
    $status = @{}
    $status['vscode_command'] = if (Get-Command code-insiders -ErrorAction SilentlyContinue) { 'code-insiders' } elseif (Get-Command code -ErrorAction SilentlyContinue) { 'code' } else { 'not found' }
    $processes = Get-Process -Name '*Code*' -ErrorAction SilentlyContinue
    $status['running_instances'] = $processes.Count
    $copilotDir = "$env:APPDATA\Code - Insiders\User\globalStorage\github.copilot-chat"
    $status['copilot_configured'] = Test-Path $copilotDir
    
    if ($Json) {
        Write-Output (ConvertTo-Json $status -Compress)
        return
    }
    
    Write-Host "`nIDE Detection & Diagnostic" -ForegroundColor Cyan
    Write-Host ("="*60) -ForegroundColor DarkGray
    
    # Check VS Code installation
    $ideAvailable = @()
    if (Get-Command code-insiders -ErrorAction SilentlyContinue) {
        $ideAvailable += "code-insiders"
    }
    if (Get-Command code -ErrorAction SilentlyContinue) {
        $ideAvailable += "code"
    }
    
    if ($ideAvailable.Count -eq 0) {
        Write-Host "❌ VS Code not found in PATH" -ForegroundColor Red
        return 1
    }
    
    Write-Host "✅ VS Code available: $($ideAvailable -join ', ')" -ForegroundColor Green
    
    # Check running instances
    $running = Get-Process -Name "*code*" -ErrorAction SilentlyContinue | Measure-Object
    Write-Host "✅ Running instances: $($running.Count)" -ForegroundColor Green
    
    # Check extensions
    $extPath = "$env:APPDATA\Code - Insiders\User\extensions"
    if (Test-Path $extPath) {
        $claudeExt = Get-ChildItem $extPath -Filter "*claude*" -ErrorAction SilentlyContinue
        if ($claudeExt) {
            Write-Host "✅ Claude Code extension: installed" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️  Claude Code extension: not installed" -ForegroundColor Yellow
        }
    }
    
    # Check Copilot
    $copilotPath = "$env:APPDATA\Code - Insiders\User\globalStorage\github.copilot-chat"
    if (Test-Path $copilotPath) {
        Write-Host "✅ GitHub Copilot: configured" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  GitHub Copilot: not configured" -ForegroundColor Yellow
    }
    
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
    return 0
}

# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE MANAGEMENT (MCP + Bridge)
# ═══════════════════════════════════════════════════════════════════════════════

function Invoke-MCPStart {
    $context = Get-EnvironmentContext
    Write-Host "🚀 Starting MCP Services..." -ForegroundColor Cyan
    
    # Check if bridge server already running
    $bridgeRunning = Get-ServiceStatus | Select-Object -ExpandProperty Bridge
    if ($bridgeRunning -eq "running") {
        Write-Host "✅ Bridge server already running (port 8888)" -ForegroundColor Green
        return 0
    }
    
    # Start bridge server in background
    Write-Host "   Starting bridge server..." -ForegroundColor Gray
    $job = Start-Job -ScriptBlock {
        param($ScriptDir)
        Set-Location $ScriptDir
        & bun run "bridge-server.ts" 2>&1
    } -ArgumentList $SCRIPT_DIR
    
    Start-Sleep -Seconds 1
    
    $status = Get-ServiceStatus
    Write-Host "✅ Bridge: $($status.Bridge)" -ForegroundColor Green
    Write-Host "✅ Services ready for VS Code Copilot @chthonic" -ForegroundColor Green
    
    return 0
}

function Invoke-MCPStop {
    Write-Host "🛑 Stopping MCP Services..." -ForegroundColor Yellow
    
    Get-Job | Where-Object { $_.Name -like "*bridge*" -or $_.Command -like "*bridge*" } | Stop-Job -PassThru | Remove-Job
    
    Write-Host "✅ Services stopped" -ForegroundColor Green
    return 0
}

function Invoke-MCPStatus {
    param([switch]$Json)
    
    $status = Get-ServiceStatus
    
    if ($Json) {
        Write-Output (ConvertTo-Json @{'bridge_server' = $status.Bridge} -Compress)
        return
    }
    
    Write-Host "`nService Status" -ForegroundColor Cyan
    Write-Host ("="*60) -ForegroundColor DarkGray
    Write-Host "  Bridge Server   " -NoNewline -ForegroundColor Gray
    $color = if ($status.Bridge -eq "running") { "Green" } else { "Red" }
    Write-Host $status.Bridge -ForegroundColor $color
    Write-Host ""
    
    return 0
}



function Invoke-PolyglotActivation {
    param([switch]$Quiet)
    
    # Build clean PATH with polyglot tools at front
    $existingPath = $env:Path -split ';' | Where-Object { $_ }
    
    # Add polyglot paths that exist
    $activePaths = @()
    foreach ($p in (Get-PolyglotPaths)) {
        if (Test-Path $p) {
            $activePaths += $p
        }
    }
    
    # Set PATH with polyglot tools first
    $env:Path = ($activePaths + $existingPath | Select-Object -Unique) -join ';'

    # Resolve `rv` collision with PowerShell's built-in Remove-Variable alias.
    # Apply only when shadowed and a Ruby manager command is available.
    $rvBinding = Ensure-RvCommandBinding
    if ($rvBinding) {
        $env:CHTHONIC_RV_BINDING = if ($rvBinding.rv_after) { $rvBinding.rv_after } else { "unresolved" }
        $env:CHTHONIC_RV_BINDING_REASON = if ($rvBinding.reason) { $rvBinding.reason } else { "" }
    }

    # Resolve `R` collision with PowerShell's Invoke-History alias.
    $rBinding = Ensure-RCommandBinding
    if ($rBinding) {
        $env:CHTHONIC_R_BINDING = if ($rBinding.r_after) { $rBinding.r_after } else { "unresolved" }
        $env:CHTHONIC_R_BINDING_REASON = if ($rBinding.reason) { $rBinding.reason } else { "" }
    }
    
    # Go environment (goup-managed)
    $goupCurrent = Join-Path $env:USERPROFILE ".goup\current"
    if (Test-Path $goupCurrent) { $env:GOROOT = $goupCurrent }
    $env:GOPATH = "$env:USERPROFILE\go"
    
    # Ruby DevKit (MSYS2 toolchain from RubyInstaller, used by rv's Ruby for native gems)
    $devkitRoot = Get-RubyDevKitRoot
    if ($devkitRoot) {
        $msys2Root = Join-Path $devkitRoot "msys64"
        if (Test-Path $msys2Root) {
            $env:RI_DEVKIT = $msys2Root
            $env:RIDK_PREFIX = $msys2Root
            $env:MSYS2_HOME = $msys2Root
        }
    }
    
    # OpenSSL (required for native Cargo builds with openssl-sys).
    # Auto-set when OpenSSL-Win64 exists and vars are unset — prevents env drift across terminals.
    $opensslDir = "C:\Program Files\OpenSSL-Win64"
    if ((Test-Path $opensslDir) -and -not $env:OPENSSL_DIR) {
        $env:OPENSSL_DIR = $opensslDir
        $env:OPENSSL_LIB_DIR = Join-Path $opensslDir "lib\VC\x64\MD"
        $env:OPENSSL_INCLUDE_DIR = Join-Path $opensslDir "include"
    }
    
    # Canon markers for the active Chthonic environment.
    # Keep the older Claudine markers mirrored for compatibility during transition.
    $env:CHTHONIC_ACTIVATED = "1"
    $env:CHTHONIC_VERSION = $VERSION
    $env:CLAUDINE_ACTIVATED = "1"
    $env:CLAUDINE_VERSION = $VERSION
    $env:CHTHONIC_REPO_ROOT = $REPO_ROOT
    
    # Idempotent git hook installation (silent, no-op if already installed)
    $hookInstaller = Join-Path $REPO_ROOT "scripts" "hooks" "install-hooks.ps1"
    $hookTarget = Join-Path $REPO_ROOT ".git" "hooks" "pre-commit"
    if ((Test-Path $hookInstaller) -and -not (Test-Path $hookTarget)) {
        & pwsh -NoProfile -File $hookInstaller 2>$null
    }
    
    if (-not $Quiet) {
        if ($rvBinding -and $rvBinding.applied) {
            Write-Host "  rv alias remapped: $($rvBinding.rv_before) -> $($rvBinding.rv_after)" -ForegroundColor DarkGray
            if ($rvBinding.rvar_after) {
                Write-Host "  Remove-Variable preserved via: $($rvBinding.rvar_after)" -ForegroundColor DarkGray
            }
        }
        if ($rBinding -and $rBinding.applied) {
            Write-Host "  R alias remapped: $($rBinding.r_before) -> $($rBinding.r_after)" -ForegroundColor DarkGray
            if ($rBinding.rhistory_after) {
                Write-Host "  Invoke-History preserved via: $($rBinding.rhistory_after)" -ForegroundColor DarkGray
            }
        }
    }
}

function Show-PolyglotStatus {
    param([switch]$Json)
    
    # Collect tool versions
    $tools = @{}
    $tools['orchestrator_ssot'] = 'chthonic'
    $tools['orchestration_mode'] = 'polyglot_router'
    $tools['research_ingest_role'] = 'supplemental_input'
    $tools['unified_overlay_optional'] = 'mise/proto'
    $tools['handler_ruby'] = 'rv (rvw wrapper optional)'
    $tools['handler_python'] = 'uv'
    $tools['handler_rust'] = 'rustup/cargo'
    $tools['handler_go'] = 'goup'
    $tools['handler_js'] = 'bun'
    $tools['handler_zig'] = 'zv'
    $tools['handler_node'] = 'fnm (optional Node version lane)'
    $tools['handler_r'] = 'unmanaged runtime (rig not installed — R 4.5.3 ucrt installed externally)'
    $tools['handler_r_packages'] = 'rv-r (A2-ai/rv — rproject.toml + rv.lock)'
    $tools['uv_tool_lane'] = 'python,ruff,cmake,ninja'
    $tools['rv'] = 'not found'
    $rvMetaStatus = Get-CommandResolution -Name "rv"
    if ($rvMetaStatus -and $rvMetaStatus.Type -ne "Alias") {
        try {
            $rvOut = (rv --version 2>$null)
            if (($rvOut -join "`n") -match '(\d+\.\d+\.\d+)') {
                $tools['rv'] = $matches[1]
            } else {
                $tools['rv'] = (($rvOut | Select-Object -First 1).ToString().Trim())
            }
        } catch {}
    }
    try {
        $rvwOut = (rvw --version 2>$null)
        if (($rvwOut -join "`n") -match '(\d+\.\d+\.\d+)') {
            $tools['rvw'] = $matches[1]
        } else {
            $tools['rvw'] = (($rvwOut | Select-Object -First 1).ToString().Trim())
        }
    } catch { $tools['rvw'] = 'not found' }
    if ($tools['rv'] -eq 'not found' -and $tools['rvw'] -ne 'not found') {
        $tools['rv'] = $tools['rvw']
    }
    if ($rvMetaStatus) {
        $tools['rv_cmd'] = if ($rvMetaStatus.Path) { $rvMetaStatus.Path } else { $rvMetaStatus.Display }
    } else {
        $tools['rv_cmd'] = 'not found'
    }
    $rvarMetaStatus = Get-CommandResolution -Name "rvar"
    if ($rvarMetaStatus) {
        $tools['rvar_cmd'] = if ($rvarMetaStatus.Path) { $rvarMetaStatus.Path } else { $rvarMetaStatus.Display }
    } else {
        $tools['rvar_cmd'] = 'not found'
    }
    try { $tools['bun'] = (bun --version 2>$null) -replace 'Bun\s+','' -split ' ' | Select-Object -First 1 } catch { $tools['bun'] = 'not found' }
    try { $tools['biome'] = ((biome --version 2>$null) -split '\n')[0] -replace 'Version:\s*','' } catch { $tools['biome'] = 'not found' }
    try { $tools['cargo'] = ((cargo --version 2>$null) -split ' ')[1] } catch { $tools['cargo'] = 'not found' }
    try { $tools['rust'] = (rustc --version 2>$null) -replace 'rustc\s*','' } catch { $tools['rust'] = 'not found' }
    try { $tools['rustup'] = ((rustup --version 2>$null) -split ' ')[1] } catch { $tools['rustup'] = 'not found' }
    try { $tools['go'] = (go version 2>$null) -replace 'go version go','' } catch { $tools['go'] = 'not found' }
    try {
        $goupOut = (goup --version 2>$null)
        if (($goupOut -join "`n") -match '(\d+\.\d+\.\d+)') {
            $tools['goup'] = $matches[1]
        } else {
            $tools['goup'] = (($goupOut | Select-Object -First 1).ToString().Trim())
        }
    } catch { $tools['goup'] = 'not found' }
    try {
        $zvExe = Get-ZvExePath
        if ($zvExe) {
            $zvOut = & $zvExe --version 2>$null
            if (($zvOut -join "`n") -match '(\d+\.\d+\.\d+)') {
                $tools['zv'] = $matches[1]
            } else {
                $tools['zv'] = (($zvOut | Select-Object -First 1).ToString().Trim())
            }
        } else {
            $tools['zv'] = 'not found'
        }
    } catch { $tools['zv'] = 'not found' }
    try {
        $zigExe = Get-ZigExePath
        if ($zigExe) {
            $zigOut = & $zigExe version 2>$null
            $tools['zig'] = (($zigOut | Select-Object -First 1).ToString().Trim())
        } else {
            $tools['zig'] = 'not found'
        }
    } catch { $tools['zig'] = 'not found' }
    try {
        $fnmOut = (fnm --version 2>$null)
        if (($fnmOut -join "`n") -match '(\d+\.\d+\.\d+)') {
            $tools['fnm'] = $matches[1]
        } elseif ($fnmOut) {
            $tools['fnm'] = (($fnmOut | Select-Object -First 1).ToString().Trim())
        } else {
            $tools['fnm'] = 'not found'
        }
    } catch { $tools['fnm'] = 'not found' }
    try {
        $nodeOut = $null
        try { $nodeOut = (node --version 2>$null) } catch {}
        if (-not $nodeOut) {
            $fnmNode = Get-FnmNodeExePath
            if ($fnmNode) { $nodeOut = (& $fnmNode --version 2>&1) }
        }
        if (($nodeOut -join "`n") -match 'v?(\d+\.\d+\.\d+)') {
            $tools['node'] = $matches[1]
        } elseif ($nodeOut) {
            $tools['node'] = (($nodeOut | Select-Object -First 1).ToString().Trim())
        } else {
            $tools['node'] = 'not found'
        }
    } catch { $tools['node'] = 'not found' }
    try {
        $uvPython = $null
        try { $uvPython = (uv python find 2>$null | Select-Object -First 1) } catch {}
        if ($uvPython -and (Test-Path $uvPython)) {
            $tools['python'] = ((& $uvPython --version 2>$null) -replace 'Python\s*','').Trim()
            $tools['python_cmd'] = $uvPython
            if ($uvPython.StartsWith($REPO_ROOT, [System.StringComparison]::OrdinalIgnoreCase)) {
                $tools['python_origin'] = 'workspace_venv'
            } else {
                $tools['python_origin'] = 'uv_managed_global'
            }
        } else {
            $tools['python'] = 'not found'
        }
    } catch { $tools['python'] = 'not found' }
    if ($tools['go'] -eq 'not found') {
        $goupGo = Join-Path $env:USERPROFILE ".goup\current\bin\go.exe"
        if (Test-Path $goupGo) {
            try { $tools['go'] = (& $goupGo version 2>$null) -replace 'go version go','' } catch {}
        }
    }
    if ($tools['python'] -eq 'not found') {
        try {
            $pyRaw = (python --version 2>&1)
            if ($pyRaw) { $tools['python'] = ($pyRaw -replace 'Python\s*','') }
        } catch {}
    }
    if (-not $tools.ContainsKey('python_cmd')) {
        $pythonMeta = Get-CommandResolution -Name "python"
        if ($pythonMeta -and $pythonMeta.Path) {
            $tools['python_cmd'] = $pythonMeta.Path
            $tools['python_origin'] = 'path_fallback'
        }
    }
    try { $tools['ruff'] = (ruff --version 2>$null) -replace 'ruff\s*','' } catch { $tools['ruff'] = 'not found' }
    try { $tools['uv'] = ((uv --version 2>$null) -split ' ')[1] } catch { $tools['uv'] = 'not found' }
    try { $tools['ruby'] = (ruby --version 2>$null) -replace 'ruby\s*','' } catch { $tools['ruby'] = 'not found' }
    try { $tools['gcc'] = ((gcc --version 2>$null) -split '\n')[0] -replace '.*\s(\d+\.\d+\.\d+)','$1' } catch { $tools['gcc'] = 'not found' }
    try { $tools['make'] = (make --version 2>$null | Select-Object -First 1) -replace 'GNU Make\s*','' } catch { $tools['make'] = 'not found' }
    try { $tools['git'] = (git --version 2>$null) -replace 'git version\s*','' } catch { $tools['git'] = 'not found' }
    try { $tools['mdbook'] = (mdbook --version 2>$null) -replace 'mdbook\s*v?','' } catch { $tools['mdbook'] = 'not found' }
    try {
        $miseOut = (mise --version 2>$null)
        if (($miseOut -join "`n") -match '(\d+\.\d+\.\d+)') {
            $tools['mise'] = $matches[1]
        } else {
            $tools['mise'] = (($miseOut | Select-Object -First 1).ToString().Trim())
        }
    } catch { $tools['mise'] = 'not found' }
    try {
        $protoOut = (proto --version 2>$null)
        if (($protoOut -join "`n") -match '(\d+\.\d+\.\d+)') {
            $tools['proto'] = $matches[1]
        } elseif ($protoOut) {
            $tools['proto'] = (($protoOut | Select-Object -First 1).ToString().Trim())
        } else {
            $tools['proto'] = 'not found'
        }
    } catch { $tools['proto'] = 'not found' }
    try {
        $rExe = Get-RExePath
        if ($rExe) {
            $rOut = (& $rExe --version 2>&1)
        } else {
            $rOut = $null
        }
        if (($rOut -join "`n") -match 'R version (\d+\.\d+\.\d+)') {
            $tools['r'] = $matches[1]
        } elseif ($rOut) {
            $tools['r'] = (($rOut | Select-Object -First 1).ToString().Trim())
        } else {
            $tools['r'] = 'not found'
        }
    } catch { $tools['r'] = 'not found' }
    try {
        $rscriptExe = Get-RScriptExePath
        if ($rscriptExe) {
            $rscriptOut = (& $rscriptExe --version 2>&1)
            if (($rscriptOut -join "`n") -match 'version (\d+\.\d+\.\d+)') {
                $tools['rscript'] = $matches[1]
            } else {
                $tools['rscript'] = (($rscriptOut | Select-Object -First 1).ToString().Trim())
            }
        } else {
            $tools['rscript'] = 'not found'
        }
    } catch { $tools['rscript'] = 'not found' }
    try {
        $rrvExe = Get-RRvExePath
        if ($rrvExe) {
            $rrvOut = (& $rrvExe --version 2>$null)
            if (($rrvOut -join "`n") -match '(\d+\.\d+\.\d+)') {
                $tools['rv_r'] = $matches[1]
            } else {
                $tools['rv_r'] = (($rrvOut | Select-Object -First 1).ToString().Trim())
            }
        } else {
            $tools['rv_r'] = 'not found'
        }
    } catch { $tools['rv_r'] = 'not found' }
    try {
        $pacmanOut = (& pacman --version 2>$null)
        if (($pacmanOut -join "`n") -match 'Pacman v(\d+\.\d+\.\d+)') {
            $tools['pacman'] = $matches[1]
        } elseif ($pacmanOut) {
            $tools['pacman'] = (($pacmanOut | Select-Object -First 1).ToString().Trim())
        } else {
            $tools['pacman'] = 'not found'
        }
    } catch { $tools['pacman'] = 'not found' }
    $msys2Home = if ($env:MSYS2_HOME) {
        $env:MSYS2_HOME
    } else {
        $root = Get-RubyDevKitRoot
        if ($root) {
            $candidate = Join-Path $root "msys64"
            if (Test-Path $candidate) { $candidate } else { $null }
        } else {
            $null
        }
    }
    $tools['msys2_home'] = if ($msys2Home) { $msys2Home } else { 'not found' }
    $azVer = Get-AzureCliVersion
    $tools['az'] = if ($azVer) { $azVer } else { 'not found' }

    $bicepExe = Get-BicepExePath
    if ($bicepExe) {
        try {
            $bicepOut = & $bicepExe --version 2>$null
            if (($bicepOut -join "`n") -match '(\d+\.\d+\.\d+)') {
                $tools['bicep'] = $matches[1]
            } else {
                $tools['bicep'] = $bicepExe
            }
        } catch {
            $tools['bicep'] = $bicepExe
        }
    } else {
        $tools['bicep'] = 'not found'
    }

    $sqlcmdExe = Get-SqlCmdExePath
    if ($sqlcmdExe) {
        try {
            $sqlcmdOut = & $sqlcmdExe --version 2>$null
            if (-not $sqlcmdOut) { $sqlcmdOut = & $sqlcmdExe -? 2>$null }
            if (($sqlcmdOut -join "`n") -match '(\d+\.\d+\.\d+)') {
                $tools['sqlcmd'] = $matches[1]
            } else {
                $tools['sqlcmd'] = $sqlcmdExe
            }
        } catch {
            $tools['sqlcmd'] = $sqlcmdExe
        }
    } else {
        $tools['sqlcmd'] = 'not found'
    }

    $sqlpackageExe = Get-SqlPackageExePath
    if ($sqlpackageExe) {
        try {
            $sqlpackageOut = & $sqlpackageExe /Version 2>$null
            if (($sqlpackageOut -join "`n") -match '(\d+\.\d+\.\d+(\.\d+)?)') {
                $tools['sqlpackage'] = $matches[1]
            } else {
                $tools['sqlpackage'] = $sqlpackageExe
            }
        } catch {
            $tools['sqlpackage'] = $sqlpackageExe
        }
    } else {
        $tools['sqlpackage'] = 'not found'
    }

    try { $tools['code-insiders'] = ((code-insiders --version 2>$null) -split '\n')[0] } catch { $tools['code-insiders'] = 'not found' }
    if (-not $tools['code-insiders']) { $tools['code-insiders'] = 'not found' }
    try {
        $claudeCmd = $null
        $claudeMeta = Get-CommandResolution -Name "claude"
        if ($claudeMeta -and $claudeMeta.Path) {
            $claudeCmd = $claudeMeta.Path
        } else {
            $claudeExeMeta = Get-CommandResolution -Name "claude.exe"
            if ($claudeExeMeta -and $claudeExeMeta.Path) { $claudeCmd = $claudeExeMeta.Path }
        }
        if ($claudeCmd) {
            $claudeOut = (& $claudeCmd --version 2>&1)
            if (($claudeOut -join "`n") -match '(\d+\.\d+\.\d+)') {
                $tools['claude'] = $matches[1]
            } elseif (($claudeOut -join "`n") -match 'Module not found') {
                $tools['claude'] = 'broken_shim'
            } elseif ($claudeOut) {
                $tools['claude'] = ($claudeOut | Select-Object -First 1).ToString().Trim()
            } else {
                $tools['claude'] = 'not found'
            }
        } else {
            $tools['claude'] = 'not found'
        }
    } catch {
        $tools['claude'] = 'not found'
    }
    try {
        $brushOut = (& brush --version 2>$null)
        if (($brushOut -join "`n") -match '^brush\s+([0-9][^\s]*)') {
            $tools['brush'] = $matches[1]
        } elseif ($brushOut) {
            $tools['brush'] = ($brushOut | Select-Object -First 1).ToString().Trim()
        } else {
            $tools['brush'] = 'not found'
        }
    } catch {
        $tools['brush'] = 'not found'
    }
    try {
        $geminiPkgPath = Join-Path $REPO_ROOT "node_modules\@google\gemini-cli\package.json"
        if (Test-Path $geminiPkgPath) {
            $geminiPkg = Get-Content $geminiPkgPath -Raw | ConvertFrom-Json
            $tools['gemini'] = $geminiPkg.version
        } else {
            $tools['gemini'] = 'not found'
        }
    } catch {
        $tools['gemini'] = 'not found'
    }

    $claudeMeta = Get-CommandResolution -Name "claude"
    if (-not $claudeMeta) {
        $claudeMeta = Get-CommandResolution -Name "claude.exe"
    }
    if ($claudeMeta) {
        $tools['claude_cmd'] = if ($claudeMeta.Path) { $claudeMeta.Path } else { $claudeMeta.Display }
    } else {
        $tools['claude_cmd'] = 'not found'
    }
    $brushMeta = Get-CommandResolution -Name "brush"
    if ($brushMeta) {
        $tools['brush_cmd'] = if ($brushMeta.Path) { $brushMeta.Path } else { $brushMeta.Display }
    } else {
        $tools['brush_cmd'] = 'not found'
    }
    $geminiExe = Join-Path $REPO_ROOT "node_modules\.bin\gemini.exe"
    $tools['gemini_cmd'] = if (Test-Path $geminiExe) { $geminiExe } else { 'not found' }

    $claudineMeta = Get-CommandResolution -Name "claudine"
    $claudineScriptPath = Get-ClaudineScriptPath
    if ($claudineScriptPath) {
        $tools['claudine_cmd'] = $claudineScriptPath
    } elseif ($claudineMeta) {
        $tools['claudine_cmd'] = if ($claudineMeta.Path) { $claudineMeta.Path } else { $claudineMeta.Display }
    } else {
        $tools['claudine_cmd'] = 'not found'
    }
    if ($claudineMeta) {
        $claudineBinding = if ($claudineMeta.Type -in @("Function", "Alias")) {
            $claudineMeta.Display
        } elseif ($claudineMeta.Path) {
            $claudineMeta.Path
        } else {
            $claudineMeta.Display
        }
        if ($claudineBinding -and $claudineBinding -ne $tools['claudine_cmd']) {
            $tools['claudine_binding'] = $claudineBinding
        }
    }
    $chthonicMeta = Get-CommandResolution -Name "chthonic"
    $chthonicScriptPath = Join-Path $SCRIPT_DIR "chthonic.ps1"
    if (Test-Path $chthonicScriptPath) {
        $tools['chthonic_cmd'] = $chthonicScriptPath
    } elseif ($chthonicMeta) {
        $tools['chthonic_cmd'] = if ($chthonicMeta.Path) { $chthonicMeta.Path } else { $chthonicMeta.Display }
    } elseif ($PSCommandPath -and (Test-Path $PSCommandPath)) {
        $tools['chthonic_cmd'] = $PSCommandPath
    } else {
        $tools['chthonic_cmd'] = 'not found'
    }
    if ($chthonicMeta) {
        $chthonicBinding = if ($chthonicMeta.Type -in @("Function", "Alias")) {
            $chthonicMeta.Display
        } elseif ($chthonicMeta.Path) {
            $chthonicMeta.Path
        } else {
            $chthonicMeta.Display
        }
        if ($chthonicBinding -and $chthonicBinding -ne $tools['chthonic_cmd']) {
            $tools['chthonic_binding'] = $chthonicBinding
        }
    }
    $miseMeta = Get-CommandResolution -Name "mise"
    if ($miseMeta) {
        $tools['mise_cmd'] = if ($miseMeta.Path) { $miseMeta.Path } else { $miseMeta.Display }
    } else {
        $tools['mise_cmd'] = 'not found'
    }
    $fnmMeta = Get-CommandResolution -Name "fnm"
    if ($fnmMeta) {
        $tools['fnm_cmd'] = if ($fnmMeta.Path) { $fnmMeta.Path } else { $fnmMeta.Display }
    } else {
        $tools['fnm_cmd'] = 'not found'
    }
    $protoMeta = Get-CommandResolution -Name "proto"
    if ($protoMeta) {
        $tools['proto_cmd'] = if ($protoMeta.Path) { $protoMeta.Path } else { $protoMeta.Display }
    } else {
        $tools['proto_cmd'] = 'not found'
    }
    $zvMeta = Get-CommandResolution -Name "zv"
    if ($zvMeta) {
        $tools['zv_cmd'] = if ($zvMeta.Path) { $zvMeta.Path } else { $zvMeta.Display }
    } else {
        $zvExe = Get-ZvExePath
        $tools['zv_cmd'] = if ($zvExe) { $zvExe } else { 'not found' }
    }
    $zigMeta = Get-CommandResolution -Name "zig"
    if ($zigMeta) {
        $tools['zig_cmd'] = if ($zigMeta.Path) { $zigMeta.Path } else { $zigMeta.Display }
    } else {
        $zigExe = Get-ZigExePath
        $tools['zig_cmd'] = if ($zigExe) { $zigExe } else { 'not found' }
    }
    $nodeMeta = Get-CommandResolution -Name "node"
    if ($nodeMeta) {
        $tools['node_cmd'] = if ($nodeMeta.Path) { $nodeMeta.Path } else { $nodeMeta.Display }
    } else {
        $fnmNode = Get-FnmNodeExePath
        $tools['node_cmd'] = if ($fnmNode) { $fnmNode } else { 'not found' }
    }
    $rMeta = Get-CommandResolution -Name "R.exe"
    if ($rMeta) {
        $tools['r_cmd'] = if ($rMeta.Path) { $rMeta.Path } else { $rMeta.Display }
    } else {
        $rExe = Get-RExePath
        $tools['r_cmd'] = if ($rExe) { $rExe } else { 'not found' }
    }
    $rscriptMeta = Get-CommandResolution -Name "Rscript"
    if ($rscriptMeta) {
        $tools['rscript_cmd'] = if ($rscriptMeta.Path) { $rscriptMeta.Path } else { $rscriptMeta.Display }
    } else {
        $rscriptExe = Get-RScriptExePath
        $tools['rscript_cmd'] = if ($rscriptExe) { $rscriptExe } else { 'not found' }
    }
    $rrvScript = Get-RRvScriptPath
    $tools['rv_r_cmd'] = if ($rrvScript) { $rrvScript } else { 'not found' }
    $pacmanMeta = Get-CommandResolution -Name "pacman"
    if ($pacmanMeta) {
        $tools['pacman_cmd'] = if ($pacmanMeta.Path) { $pacmanMeta.Path } else { $pacmanMeta.Display }
    } else {
        $tools['pacman_cmd'] = 'not found'
    }
    if ($tools['mise'] -eq 'not found') {
        $tools['manager_model'] = 'explicit_managers(chthonic_ssot)'
    } else {
        $tools['manager_model'] = 'hybrid(chthonic_ssot+mise_overlay)'
    }
    $rvBindingState = "not set"
    $rvBindingReason = "not set"
    if ($rvMetaStatus) {
        if ($rvMetaStatus.Path -and (Split-Path -Leaf $rvMetaStatus.Path).ToLower() -eq "rv.exe") {
            $rvBindingState = $rvMetaStatus.Path
            $rvBindingReason = "rv mapped to rv.exe in current shell"
        } elseif ($rvMetaStatus.Path -and (Split-Path -Leaf $rvMetaStatus.Path).ToLower() -eq "rvw.exe") {
            $rvBindingState = $rvMetaStatus.Path
            $rvBindingReason = "rv mapped to rvw in current shell"
        } elseif ($rvMetaStatus.Display -eq "alias -> rv.exe") {
            $rvBindingState = "alias -> rv.exe"
            $rvBindingReason = "rv mapped to rv.exe in current shell"
        } elseif ($rvMetaStatus.Display -eq "alias -> rvw") {
            $rvBindingState = "alias -> rvw"
            $rvBindingReason = "rv mapped to rvw in current shell"
        } elseif ($rvMetaStatus.Display -eq "alias -> Remove-Variable") {
            $rvBindingState = "alias -> Remove-Variable"
            $rvRScript = Join-Path $SCRIPT_DIR "rv-r.ps1"
            $hasRvExe = (Get-CommandResolution -Name "rv.exe") -or (Get-CommandResolution -Name "rvw")
            if ($hasRvExe -and (Test-Path $rvRScript)) {
                $rvBindingReason = "accepted by design; R handled via rv-r, Remove-Variable unused"
            } elseif ($hasRvExe) {
                $rvBindingReason = "not applied in current shell; run 'chthonic env' to apply collision guard"
            } else {
                $rvBindingReason = "rv unavailable; collision guard cannot be applied"
            }
        } else {
            $rvBindingState = if ($rvMetaStatus.Path) { $rvMetaStatus.Path } else { $rvMetaStatus.Display }
            $rvBindingReason = "rv bound to non-default command"
        }
    }
    $tools['rv_binding'] = $rvBindingState
    $tools['rv_binding_reason'] = $rvBindingReason

    $rBindingState = "not set"
    $rBindingReason = "not set"
    $rAliasMeta = Get-CommandResolution -Name "R"
    if ($rAliasMeta) {
        if ($rAliasMeta.Path) {
            $rBindingState = $rAliasMeta.Path
            $rBindingReason = "R mapped to runtime command in current shell"
        } elseif ($rAliasMeta.Display -eq "alias -> Invoke-History") {
            $rBindingState = "alias -> Invoke-History"
            $rRvRScript = Join-Path $SCRIPT_DIR "rv-r.ps1"
            if (Test-Path $rRvRScript) {
                $rBindingReason = "accepted by design; R accessed via rv-r"
            } elseif (Get-RExePath) {
                $rBindingReason = "not applied in current shell; run 'chthonic env' to apply collision guard"
            } else {
                $rBindingReason = "R runtime unavailable; collision guard cannot be applied"
            }
        } else {
            $rBindingState = $rAliasMeta.Display
            $rBindingReason = "R bound to non-default command"
        }
    }
    $tools['r_binding'] = $rBindingState
    $tools['r_binding_reason'] = $rBindingReason

    $clExe = Get-VSClExePath
    if ($clExe) {
        try {
            $clOut = & $clExe /Bv 2>$null
            if ($clOut -match 'Compiler Version ([0-9\.]+)') {
                $tools['msvc_cl'] = $matches[1]
            } else {
                $tools['msvc_cl'] = (Split-Path -Parent $clExe)
            }
        } catch {
            $tools['msvc_cl'] = (Split-Path -Parent $clExe)
        }
    } else {
        $tools['msvc_cl'] = 'not found'
    }

    $msbuildExe = Get-VSMsBuildExePath
    if ($msbuildExe) {
        try {
            $msbuildOut = & $msbuildExe -version -nologo 2>$null
            if ($msbuildOut) {
                $tools['msbuild'] = (($msbuildOut | Select-Object -Last 1).ToString().Trim())
            } else {
                $tools['msbuild'] = $msbuildExe
            }
        } catch {
            $tools['msbuild'] = $msbuildExe
        }
    } else {
        $tools['msbuild'] = 'not found'
    }

    $clangBin = Get-VSClangBinDir
    if ($clangBin) {
        try {
            $clangOut = & (Join-Path $clangBin "clang.exe") --version 2>$null
            if ($clangOut -and $clangOut[0] -match 'clang version ([0-9\.]+)') {
                $tools['clang'] = $matches[1]
            } else {
                $tools['clang'] = $clangBin
            }
        } catch {
            $tools['clang'] = $clangBin
        }
    } else {
        $tools['clang'] = 'not found'
    }

    $ssmsVer = Get-SsmsVersion
    $tools['ssms'] = if ($ssmsVer) { $ssmsVer } else { 'not found' }
    $vsProfessionalVer = Get-VSProductVersion -ProductId "Microsoft.VisualStudio.Product.Professional"
    $vsCommunityVer = Get-VSProductVersion -ProductId "Microsoft.VisualStudio.Product.Community"
    $vsEnterpriseVer = Get-VSProductVersion -ProductId "Microsoft.VisualStudio.Product.Enterprise"
    $vsBuildToolsVer = Get-VSProductVersion -ProductId "Microsoft.VisualStudio.Product.BuildTools"
    $vsIdeVer = $null
    foreach ($candidate in @($vsProfessionalVer, $vsCommunityVer, $vsEnterpriseVer)) {
        if ($candidate) { $vsIdeVer = $candidate; break }
    }
    $tools['vs_ide'] = if ($vsIdeVer) { $vsIdeVer } else { "not found" }
    $tools['vs_professional'] = if ($vsProfessionalVer) { $vsProfessionalVer } else { "not found" }
    $tools['vs_community'] = if ($vsCommunityVer) { $vsCommunityVer } else { "not found" }
    $tools['vs_enterprise'] = if ($vsEnterpriseVer) { $vsEnterpriseVer } else { "not found" }
    $tools['vs_buildtools'] = if ($vsBuildToolsVer) { $vsBuildToolsVer } else { "not found" }
    if ($env:VULKAN_SDK -match '(\d+\.\d+\.\d+\.\d+)') { $tools['vulkan'] = $matches[1] } else { $tools['vulkan'] = 'not found' }
    $tools['workspace'] = $REPO_ROOT
    $tools['handler_shell'] = 'pwsh primary, brush experimental, bash fallback'
    
    # Output as JSON or human-readable
    if ($Json) {
        Write-Output (ConvertTo-Json $tools -Compress -Depth 5)
    } else {
        Write-Host "`nCHTHONIC POLYGLOT ENVIRONMENT v$VERSION" -ForegroundColor Cyan
        Write-Host ("="*60) -ForegroundColor DarkGray

        Write-StatusSection -Title "Toolchain" -Tools $tools -Keys @(
            "ruby", "rv", "rvw", "python", "uv", "ruff",
            "bun", "biome", "go", "goup", "cargo", "rust", "rustup",
            "zig", "zv", "r", "rscript", "rv_r",
            "mdbook", "git", "gcc", "make", "claude", "brush", "gemini"
        )

        Write-StatusSection -Title "Commands" -Tools $tools -Keys @(
            "chthonic_cmd", "chthonic_binding",
            "claudine_cmd", "claudine_binding",
            "claude_cmd", "brush_cmd", "gemini_cmd", "rv_cmd", "rv_binding", "rv_binding_reason",
            "rvar_cmd", "r_cmd", "rscript_cmd", "rv_r_cmd",
            "r_binding", "r_binding_reason", "zv_cmd", "zig_cmd", "mise", "mise_cmd"
        )

        Write-StatusSection -Title "Platform" -Tools $tools -Keys @(
            "code-insiders", "az", "bicep", "sqlcmd", "sqlpackage", "ssms",
            "msvc_cl", "msbuild", "clang", "vs_ide", "vs_professional",
            "vs_community", "vs_enterprise", "vs_buildtools", "vulkan"
        )

        Write-StatusSection -Title "Routing Metadata" -Tools $tools -Keys @(
            "orchestrator_ssot", "orchestration_mode", "manager_model",
            "unified_overlay_optional", "handler_ruby", "handler_python",
            "handler_rust", "handler_go", "handler_js", "handler_zig", "handler_r",
            "handler_r_packages", "handler_shell", "uv_tool_lane",
            "research_ingest_role"
        )

        Write-Host ("="*60) -ForegroundColor DarkGray
        Write-Host "  Workspace:" -NoNewline -ForegroundColor DarkGray
        Write-Host " $REPO_ROOT" -ForegroundColor White
        Write-Host ("="*60) -ForegroundColor DarkGray
        Write-Host ""
    }
}

function Invoke-ArchiveCommand {
    param([string]$Cmd, [string[]]$CmdArgs)
    
    $scriptMap = @{
        "audit"   = "audit.py"
        "compact" = "compact.py"
        "extract" = "extract.py"
        "resolve" = "resolve.py"
        "map"     = "map.py"
        "analyze" = "analyze.py"
    }
    
    if ($scriptMap.ContainsKey($Cmd)) {
        # Resolve relative file paths to absolute before changing directory
        $resolvedArgs = @()
        for ($i = 0; $i -lt $CmdArgs.Count; $i++) {
            $arg = $CmdArgs[$i]
            if ($arg -match '^-') {
                # Flag or option — pass through
                $resolvedArgs += $arg
            }
            elseif (Test-Path $arg) {
                # Existing file/directory — resolve to absolute
                $resolvedArgs += (Resolve-Path $arg).Path
            }
            else {
                # Not a path or doesn't exist — pass through as-is
                $resolvedArgs += $arg
            }
        }
        Push-Location $SCRIPT_DIR
        try {
            & uv run python -m "lib.$($Cmd)" @resolvedArgs
            return $LASTEXITCODE
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Error "Unknown command: $Cmd"
        Write-Host "Run 'chthonic --help' for usage." -ForegroundColor Yellow
        return 1
    }
}

function Invoke-RustificationTrend {
    param([string[]]$Args)

    Push-Location $REPO_ROOT
    try {
        & uv run scripts/rustification_trend_tracker.py @Args
        return $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
}

function Invoke-OversightUpcycle {
    param([string[]]$Args)

    Push-Location $REPO_ROOT
    try {
        & uv run scripts/oversight_upcycle.py @Args
        return $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
}

function Invoke-SsotLoremaster {
    param(
        [string]$Action,
        [string[]]$ActionArgs,
        [switch]$Json
    )

    $scriptPath = Join-Path $SCRIPT_DIR "ssot_loremaster.py"
    if (-not (Test-Path -LiteralPath $scriptPath)) {
        return [PSCustomObject]@{
            ExitCode = 1
            Output = @("Missing script: $scriptPath")
        }
    }

    $validActions = @("queue", "entity", "section", "drift", "lineage")
    if ($Action -notin $validActions) {
        return [PSCustomObject]@{
            ExitCode = 1
            Output = @(
                "chthonic ssot <action>",
                "  queue [--write <path>] [--json]",
                "  entity <name> [--json]",
                "  section <query> [--json]",
                "  drift [--json]",
                "  lineage [--entity <name>] [--write <path>] [--json]"
            )
        }
    }

    $resolvedArgs = New-Object System.Collections.Generic.List[string]
    $expectWritePath = $false

    foreach ($arg in $ActionArgs) {
        if ($expectWritePath) {
            $resolvedPath = if ([System.IO.Path]::IsPathRooted($arg)) {
                $arg
            } else {
                (Join-Path $REPO_ROOT $arg)
            }
            $resolvedArgs.Add($resolvedPath)
            $expectWritePath = $false
            continue
        }

        $resolvedArgs.Add($arg)
        if ($arg -eq "--write") {
            $expectWritePath = $true
        }
    }

    if ($Json -and -not ($resolvedArgs -contains "--json")) {
        $resolvedArgs.Add("--json")
    }

    Push-Location $REPO_ROOT
    try {
        $output = & uv run $scriptPath $Action @($resolvedArgs.ToArray()) 2>&1
        return [PSCustomObject]@{
            ExitCode = $LASTEXITCODE
            Output = @($output | ForEach-Object { [string]$_ })
        }
    }
    finally {
        Pop-Location
    }
}

function Invoke-ShellProbe {
    param([switch]$Json)

    $shells = @(
        [PSCustomObject]@{ name = "pwsh";  path = (Get-CommandPathFlexible -Name "pwsh");  version = $null; note = "primary control-plane host" },
        [PSCustomObject]@{ name = "brush"; path = (Get-CommandPathFlexible -Name "brush"); version = $null; note = "experimental rust shell lane" },
        [PSCustomObject]@{ name = "bash";  path = (Get-CommandPathFlexible -Name "bash");  version = $null; note = "fallback POSIX lane" }
    )

    foreach ($shell in $shells) {
        if (-not $shell.path) { continue }
        try {
            switch ($shell.name) {
                "pwsh"  { $shell.version = ((& $shell.path -NoLogo -NoProfile -Command '$PSVersionTable.PSVersion.ToString()' 2>$null) | Select-Object -First 1).ToString().Trim() }
                "brush" { $shell.version = (((& $shell.path --version 2>$null) | Select-Object -First 1).ToString().Trim() -replace '^brush\s+', '') }
                "bash"  { $shell.version = (((& $shell.path --version 2>$null) | Select-Object -First 1).ToString().Trim()) }
            }
        } catch {
            if (-not $shell.version) { $shell.version = "unresolved" }
        }
    }

    if ($Json) {
        Write-Output (ConvertTo-Json $shells -Compress -Depth 5)
        return
    }

    Write-Host ""
    Write-Host "CHTHONIC SHELL PROBE" -ForegroundColor Cyan
    Write-Host ("="*60) -ForegroundColor DarkGray
    foreach ($shell in $shells) {
        $status = if ($shell.path) { $shell.path } else { "not found" }
        $color = if ($shell.path) { "White" } else { "Red" }
        Write-Host ("  " + $shell.name.PadRight(8)) -NoNewline -ForegroundColor Gray
        Write-Host (($shell.version ?? "not found").PadRight(24)) -NoNewline -ForegroundColor $color
        Write-Host $status -ForegroundColor DarkGray
    }
    Write-Host ("="*60) -ForegroundColor DarkGray
    Write-Host ""
}

function Invoke-ChthonicWorkflow {
    param(
        [string]$Profile,
        [string[]]$WorkflowArgs,
        [switch]$Json
    )

    $scriptPath = Join-Path $SCRIPT_DIR "chthonic_workflow.py"
    if (-not (Test-Path -LiteralPath $scriptPath)) {
        return [PSCustomObject]@{
            ExitCode = 1
            Output = @("Missing script: $scriptPath")
        }
    }

    $validProfiles = @("control-plane", "toolchain-governance")
    if ($Profile -notin $validProfiles) {
        return [PSCustomObject]@{
            ExitCode = 1
            Output = @(
                "chthonic workflow <profile>",
                "  control-plane         - validate status, shell probe, ssot queue/drift/lineage, MCP tool exposure",
                "  toolchain-governance  - validate doctor/origins/toolchain probe surfaces"
            )
        }
    }

    $resolvedArgs = @()
    if ($Json -and -not ($WorkflowArgs -contains "--json")) {
        $resolvedArgs += "--json"
    }
    $resolvedArgs += $WorkflowArgs

    Push-Location $REPO_ROOT
    try {
        $output = & uv run $scriptPath $Profile @resolvedArgs 2>&1
        return [PSCustomObject]@{
            ExitCode = $LASTEXITCODE
            Output = @($output | ForEach-Object { [string]$_ })
        }
    }
    finally {
        Pop-Location
    }
}

function Invoke-ChthonicNew {
    param(
        [string]$Profile,
        [string[]]$CreateArgs,
        [switch]$Json
    )

    $scriptPath = Join-Path $SCRIPT_DIR "chthonic_new.py"
    if (-not (Test-Path -LiteralPath $scriptPath)) {
        return [PSCustomObject]@{
            ExitCode = 1
            Output = @("Missing script: $scriptPath")
        }
    }

    Push-Location $REPO_ROOT
    try {
        $resolvedArgs = @()
        if ($Json -and -not ($CreateArgs -contains "--json")) { $resolvedArgs += "--json" }
        $resolvedArgs += $CreateArgs
        $output = & uv run $scriptPath $Profile @resolvedArgs 2>&1
        return [PSCustomObject]@{
            ExitCode = $LASTEXITCODE
            Output = @($output | ForEach-Object { [string]$_ })
        }
    }
    finally {
        Pop-Location
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# DOCTOR - endoflife.date API integration
# ═══════════════════════════════════════════════════════════════════════════════

function Get-EndOfLifeData {
    param([string]$Product)
    try {
        return Invoke-RestMethod -Uri "https://endoflife.date/api/$Product.json" -TimeoutSec 5 -ErrorAction Stop
    } catch { return $null }
}

function Get-InstalledVersion {
    param([string]$Tool)
    try {
        switch ($Tool) {
            "pwsh"       {
                $pwshExe = Get-CommandPathFlexible -Name "pwsh"
                if (-not $pwshExe) { return $null }
                $v = & $pwshExe -NoLogo -NoProfile -Command '$PSVersionTable.PSVersion.ToString()' 2>$null
                if ($v -match '(\d+\.\d+\.\d+)') { return $matches[1] }
                return $null
            }
            "ruby"       {
                $v = ruby -e "print RUBY_VERSION" 2>$null
                try { $rubyCmd = Get-Command ruby -ErrorAction SilentlyContinue; if ($rubyCmd -and $rubyCmd.Source -match 'zjit') { return "$v+zjit" } } catch {}
                return $v
            }
            "python"     {
                $v = $null
                try {
                    $uvPython = (uv python find --system 2>$null | Select-Object -First 1)
                    if ($uvPython -and (Test-Path $uvPython)) {
                        $v = & $uvPython --version 2>$null
                    }
                } catch { $v = $null }
                if ($v -match 'Python\s+(\d+\.\d+\.\d+)') { return $matches[1] }
                $py = try { python --version 2>$null } catch { $null }
                if ($py -match 'Python\s+(\d+\.\d+\.\d+)') { return $matches[1] }
                return $null
            }
            "uv"         { $v = uv --version 2>$null; if ($v -match '(\d+\.\d+\.\d+)') { return $matches[1] }; return $null }
            "bun"        { return (bun --version 2>$null) }
            "brush"      {
                $v = brush --version 2>$null
                if ($v -match '^brush\s+(\d+\.\d+\.\d+)') { return $matches[1] }
                return $v
            }
            "rust"       { $v = rustc -V 2>$null; if ($v -match '(\d+\.\d+\.\d+)') { return $matches[1] }; return $null }
            "cargo"      { $v = cargo --version 2>$null; if ($v -match '(\d+\.\d+\.\d+)') { return $matches[1] }; return $null }
            "rustup"     { $v = rustup --version 2>$null; if ($v -match '(\d+\.\d+\.\d+)') { return $matches[1] }; return $null }
            "go"         {
                # Try PATH first, then goup-managed Go
                $v = try { go version 2>$null } catch { $null }
                if (-not $v) {
                    $goupGo = Join-Path $env:USERPROFILE ".goup\current\bin\go.exe"
                    if (Test-Path $goupGo) { $v = & $goupGo version 2>$null }
                }
                if ($v -match 'go(\d+\.\d+\.\d+)') { return $matches[1] }; return $null
            }
            "goup"       {
                $v = goup --version 2>$null
                if (($v -join "`n") -match '(\d+\.\d+\.\d+)') { return $matches[1] }
                return $null
            }
            "rv"         {
                $rvExe = Get-RvExePath
                if (-not $rvExe) { return $null }
                $v = & $rvExe --version 2>$null
                if ($v -match '(\d+\.\d+\.\d+)') { return $matches[1] }
                return $null
            }
            "nodejs"     {
                $v = $null
                try { $v = node --version 2>$null } catch {}
                if (-not $v) {
                    $fnmNode = Get-FnmNodeExePath
                    if ($fnmNode) { $v = & $fnmNode --version 2>&1 }
                }
                if ($v -match '(\d+\.\d+\.\d+)') { return $matches[1] }
                return $null
            }
            "fnm"        { $v = fnm --version 2>$null; if ($v -match '(\d+\.\d+\.\d+)') { return $matches[1] }; return $null }
            "proto"      { $v = proto --version 2>$null; if ($v -match '(\d+\.\d+\.\d+)') { return $matches[1] }; return $null }
            "mise"       { $v = mise --version 2>$null; if ($v -match '(\d+\.\d+\.\d+)') { return $matches[1] }; return $null }
            "solana"     { $v = solana --version 2>$null; if ($v -match 'solana-cli\s+([0-9][^\s]+)') { return $matches[1] }; return $null }
            "agave-install" { $v = agave-install --version 2>$null; if ($v -match 'agave-install\s+([0-9][^\s]+)') { return $matches[1] }; return $null }
            "anchor"     { $v = anchor --version 2>$null; if ($v -match 'anchor-cli\s+([0-9][^\s]+)') { return $matches[1] }; return $null }
            "avm"        { return $null }
            "zv"         {
                $zvExe = Get-ZvExePath
                if (-not $zvExe) { return $null }
                $v = & $zvExe --version 2>$null
                if ($v -match '(\d+\.\d+\.\d+)') { return $matches[1] }
                return $null
            }
            "zig"        {
                $zigExe = Get-ZigExePath
                if (-not $zigExe) { return $null }
                $v = & $zigExe version 2>$null
                if ($v -match '([0-9][^\s]+)') { return $matches[1] }
                return $null
            }
            "gcc"        { $v = gcc --version 2>$null; if (($v -join "`n") -match '(\d+\.\d+\.\d+)') { return $matches[1] }; return $null }
            "make"       { $v = make --version 2>$null; if (($v -join "`n") -match 'GNU Make\s*([0-9][^\s]*)') { return $matches[1] }; return $null }
            "pacman"     { $v = pacman --version 2>$null; if (($v -join "`n") -match 'Pacman v(\d+\.\d+\.\d+)') { return $matches[1] }; return $null }
            "rig"        {
                $rigExe = Get-RigExePath
                if (-not $rigExe) { return $null }
                $v = & $rigExe --version 2>$null
                if ($v -match '(\d+\.\d+\.\d+)') { return $matches[1] }
                return $null
            }
            "r"          {
                $rExe = Get-RExePath
                if (-not $rExe) { return $null }
                $v = & $rExe --version 2>&1
                if (($v -join "`n") -match 'R version (\d+\.\d+\.\d+)') { return $matches[1] }
                return $null
            }
            "rscript"    {
                $rscriptExe = Get-RScriptExePath
                if (-not $rscriptExe) { return $null }
                $v = & $rscriptExe --version 2>&1
                if (($v -join "`n") -match 'version (\d+\.\d+\.\d+)') { return $matches[1] }
                return $null
            }
            "rv-r"       {
                $rrvExe = Get-RRvExePath
                if (-not $rrvExe) { return $null }
                $v = & $rrvExe --version 2>$null
                if (($v -join "`n") -match '(\d+\.\d+\.\d+)') { return $matches[1] }
                return $null
            }
            "postgresql" {
                $v = psql --version 2>$null; if ($v -match '(\d+\.\d+)') { return $matches[1] }; return $null
            }
            "dotnet"     { $v = dotnet --version 2>$null; return $v }
            "azurecli"   { return (Get-AzureCliVersion) }
            "visualstudio" { return (Get-VisualStudioVersion) }
            "ssms" {
                return (Get-SsmsVersion)
            }
            "windows"    {
                $build = [System.Environment]::OSVersion.Version
                return "$($build.Major).$($build.Minor).$($build.Build)"
            }
            default      { return $null }
        }
    } catch { return $null }
}

function Compare-Versions {
    param([string]$Installed, [string]$Latest)
    if (-not $Installed -or -not $Latest) { return $null }
    try {
        $i = [version]$Installed
        $l = [version]$Latest
        return $i.CompareTo($l)
    } catch { return $null }
}

# Fix command map: tool -> { Upgrade (tool present), Install (tool missing) }
# All vectors use native installers — zero winget dependency.
# Pin policy: install + pin in one atomic operation where supported.
#   Ruby/Python: explicit pin (rv ruby pin / uv python pin)
#   Go/Rust/Bun: implicit pin (goup install auto-defaults, rustup stays stable, bun is single binary)
$global:DoctorFixMap = @{
    ruby   = @{
        Upgrade = { param($ver) rv ruby install $ver; rv ruby pin $ver }; UpgradeDesc = "rv ruby install && pin"
        Install = { param($ver) if (-not (Get-Command rvw -ErrorAction SilentlyContinue)) { irm https://rv.dev/install.ps1 | iex }; rv ruby install $ver; rv ruby pin $ver }; InstallDesc = "install rv.dev (if missing) && rv ruby install && pin"
    }
    python = @{
        Upgrade = {
            param($ver)
            # Extract series (e.g. "3.14" from "3.14.4") for uv python upgrade
            $series = ($ver -replace '\.\d+$', '')
            $env:UV_PYTHON_INSTALL_BIN = "0"
            uv python upgrade $series
            # uv always creates a minor-version junction alias after upgrade (by design,
            # not a bug — used for venv patch transparency). Remove it so `uv python list`
            # stays clean. Junction removal is safe: only the pointer is deleted, not contents.
            $junctionPath = "$env:APPDATA\uv\python\cpython-$series-windows-x86_64-none"
            if ((Test-Path $junctionPath) -and ((Get-Item $junctionPath -Force).LinkType -eq 'Junction')) {
                [System.IO.Directory]::Delete($junctionPath)
            }
        }; UpgradeDesc = "uv python upgrade <series>"
        Install = {
            param($ver)
            if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
                irm https://astral.sh/uv/install.ps1 | iex
            }
            $series = ($ver -replace '\.\d+$', '')
            $env:UV_PYTHON_INSTALL_BIN = "0"
            uv python upgrade $series
            $junctionPath = "$env:APPDATA\uv\python\cpython-$series-windows-x86_64-none"
            if ((Test-Path $junctionPath) -and ((Get-Item $junctionPath -Force).LinkType -eq 'Junction')) {
                [System.IO.Directory]::Delete($junctionPath)
            }
        }; InstallDesc = "install uv (if missing) && uv python upgrade <series>"
    }
    bun    = @{
        Upgrade = { bun upgrade }; UpgradeDesc = "bun upgrade"
        Install = { irm bun.sh/install.ps1 | iex }; InstallDesc = "irm bun.sh/install.ps1 | iex"
    }
    brush  = @{
        Upgrade = { cargo install --locked brush-shell }; UpgradeDesc = "cargo install --locked brush-shell"
        Install = { cargo install --locked brush-shell }; InstallDesc = "cargo install --locked brush-shell"
    }
    rust   = @{
        Upgrade = {
            param($ver)
            # Check for rust-toolchain.toml override
            $toolchainToml = Join-Path (Get-Location) "rust-toolchain.toml"
            if (Test-Path $toolchainToml) {
                $content = Get-Content $toolchainToml -Raw
                if ($content -match 'channel\s*=\s*"([^"]+)"') {
                    $pinned = $matches[1]
                    if ($pinned -ne "stable" -and $pinned -ne "nightly" -and $pinned -ne "beta") {
                        Write-Host "  !! rust-toolchain.toml pins channel = `"$pinned`"" -ForegroundColor Yellow
                        $newContent = $content -replace "channel\s*=\s*`"$([regex]::Escape($pinned))`"", "channel = `"$ver`""
                        Set-Content $toolchainToml $newContent -NoNewline
                        Write-Host "  -> updated rust-toolchain.toml channel to `"$ver`"" -ForegroundColor Green
                        rustup toolchain install $ver
                        return
                    }
                }
            }
            rustup update stable
        }; UpgradeDesc = "rustup update stable"
        Install = { irm https://sh.rustup.rs -useb | iex }; InstallDesc = "irm rustup.rs | iex"
    }
    go     = @{
        Upgrade = { param($ver) goup install "=$ver" }; UpgradeDesc = "goup install"
        Install = { goup install stable }; InstallDesc = "goup install stable"
    }
}

function Get-DoctorPinState {
    $pins = @()

    if (Test-Path ".python-version") {
        $pyPin = Get-Content ".python-version" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($pyPin) {
            $pins += [pscustomobject]@{
                name = ".python-version"
                value = $pyPin
                effect = "Python upgrades pin uv to the requested version when install succeeds."
            }
        }
    }

    if (Test-Path "rust-toolchain.toml") {
        $toolchainToml = Get-Content "rust-toolchain.toml" -Raw -ErrorAction SilentlyContinue
        if ($toolchainToml -match 'channel\s*=\s*"([^"]+)"') {
            $pins += [pscustomobject]@{
                name = "rust-toolchain.toml"
                value = $matches[1]
                effect = "Rust upgrades follow the pinned channel in rust-toolchain.toml."
            }
        }
    }

    return @($pins)
}

function Get-DoctorRetentionNotes {
    return @(
        [pscustomobject]@{ manager = "rv"; note = "installs new Ruby versions alongside older ones until you prune them manually." }
        [pscustomobject]@{ manager = "uv"; note = "upgrades Python within the same series lane (uv python upgrade 3.14); old patch versions may remain in the store until pruned with uv python uninstall." }
        [pscustomobject]@{ manager = "goup"; note = "keeps Go versions in its store and switches the active current link." }
        [pscustomobject]@{ manager = "rustup"; note = "keeps toolchains/components in rustup home; updates do not delete older channels automatically." }
        [pscustomobject]@{ manager = "bun"; note = "is a single runtime binary; upgrade replaces the active bun install rather than managing side-by-side versions." }
    )
}

# Origin map: where each tool actually lives and how it was installed.
# Resolved dynamically from Get-Command to stay accurate.
function Show-Origins {
    $W = "White"; $C = "Cyan"; $D = "DarkGray"; $R = "Red"; $G = "Green"

    Write-Host ""
    Write-Host "CHTHONIC ORIGINS v$VERSION" -ForegroundColor $C
    Write-Host ("="*72) -ForegroundColor $D

    # Core ANNO-managed tools
    $tools = @(
        @{ Name = "ruby";    Cmd = "ruby";    Method = "rv (irm rv.dev/install.ps1)";     Ecosystem = "cargo" },
        @{ Name = "python";  Cmd = "uv";      Method = "irm astral.sh/uv";          Ecosystem = "uv" },
        @{ Name = "bun";     Cmd = "bun";     Method = "irm bun.sh";                Ecosystem = "bun" },
        @{ Name = "rust";    Cmd = "rustc";   Method = "rustup (irm rustup.rs)";     Ecosystem = "cargo" },
        @{ Name = "go";      Cmd = "go";      Method = "goup (cargo install goup-rs)"; Ecosystem = "cargo" }
    )

    # Secondary tools
    $secondary = @(
        @{ Name = "rv";      Cmd = $null;     Method = "primary Ruby lane"; Ecosystem = "local"; Resolver = { Get-CommandDisplayFlexible -Name "rv" } },
        @{ Name = "rvw";     Cmd = "rvw";     Method = "fallback rv wrapper"; Ecosystem = "cargo" },
        @{ Name = "fnm";     Cmd = "fnm";     Method = "winget/cargo (Fast Node Manager)"; Ecosystem = "system" },
        @{ Name = "node";    Cmd = $null;     Method = "fnm-managed Node runtime"; Ecosystem = "system"; Resolver = { Get-FnmNodeExePath } },
        @{ Name = "mise";    Cmd = "mise";    Method = "optional unified overlay (not SSOT)"; Ecosystem = "system" },
        @{ Name = "proto";   Cmd = "proto";   Method = "cargo install proto_cli"; Ecosystem = "cargo" },
        @{ Name = "zv";      Cmd = $null;     Method = "Zig version manager"; Ecosystem = "cargo"; Resolver = { Get-ZvExePath } },
        @{ Name = "zig";     Cmd = $null;     Method = "zv-managed Zig runtime"; Ecosystem = "cargo"; Resolver = { Get-ZigExePath } },
        @{ Name = "R";       Cmd = $null;     Method = "current R runtime (manager intentionally none)"; Ecosystem = "system"; Resolver = { Get-RExePath } },
        @{ Name = "Rscript"; Cmd = $null;     Method = "current R helper (manager intentionally none)"; Ecosystem = "system"; Resolver = { Get-RScriptExePath } },
        @{ Name = "rv-r";    Cmd = $null;     Method = "A2-ai/rv via repo wrapper"; Ecosystem = "local"; Resolver = { Get-RRvScriptPath } },
        @{ Name = "goup";    Cmd = "goup";    Method = "GH release binary"; Ecosystem = "cargo" },
        @{ Name = "cargo";   Cmd = "cargo";   Method = "rustup toolchain"; Ecosystem = "cargo" },
        @{ Name = "rustup";  Cmd = "rustup";  Method = "rustup manager"; Ecosystem = "cargo" },
        @{ Name = "brush";   Cmd = "brush";   Method = "cargo install brush-shell"; Ecosystem = "cargo" },
        @{ Name = "pacman";  Cmd = $null;     Method = "MSYS2 package manager (RubyInstaller DevKit)"; Ecosystem = "system"; Resolver = {
            $root = Get-RubyDevKitRoot
            if ($root) {
                $pacman = Join-Path $root "msys64\usr\bin\pacman.exe"
                if (Test-Path $pacman) { return $pacman }
            }
            return $null
        } },
        @{ Name = "msys2";   Cmd = $null;     Method = "RubyInstaller DevKit / MSYS2 root"; Ecosystem = "system"; Resolver = {
            $root = Get-RubyDevKitRoot
            if ($root) {
                $home = Join-Path $root "msys64"
                if (Test-Path $home) { return $home }
            }
            return $null
        } },
        @{ Name = "biome";   Cmd = "biome";   Method = "repo bun dependency or curated global tool";    Ecosystem = "bun" },
        @{ Name = "ruff";    Cmd = "ruff";    Method = "uv tool";       Ecosystem = "uv" },
        @{ Name = "cmake";   Cmd = "cmake";   Method = "uv tool";       Ecosystem = "uv" },
        @{ Name = "ninja";   Cmd = "ninja";   Method = "uv tool";       Ecosystem = "uv" },
        @{ Name = "mdbook";  Cmd = "mdbook";  Method = "cargo install"; Ecosystem = "cargo" },
        @{ Name = "git";     Cmd = "git";     Method = "native installer"; Ecosystem = "system" },
        @{ Name = "gcc";     Cmd = "gcc";     Method = "MSYS2 (RubyInstaller)"; Ecosystem = "system" },
        @{ Name = "az";      Cmd = "az";      Method = "Azure CLI MSI"; Ecosystem = "system" },
        @{ Name = "bicep";   Cmd = "bicep";   Method = "winget (Microsoft.Bicep)"; Ecosystem = "system"; Resolver = { Get-BicepExePath } },
        @{ Name = "sqlcmd";  Cmd = "sqlcmd";  Method = "winget (Microsoft.Sqlcmd)"; Ecosystem = "system"; Resolver = { Get-SqlCmdExePath } },
        @{ Name = "sqlpackage"; Cmd = "sqlpackage"; Method = "winget (Microsoft.SqlPackage)"; Ecosystem = "system"; Resolver = { Get-SqlPackageExePath } },
        @{ Name = "cl";      Cmd = "cl";      Method = "Visual Studio 2026 C++ toolchain"; Ecosystem = "system"; Resolver = { Get-VSClExePath } },
        @{ Name = "msbuild"; Cmd = "msbuild"; Method = "Visual Studio 2026 Build Tools"; Ecosystem = "system"; Resolver = { Get-VSMsBuildExePath } },
        @{ Name = "clang";   Cmd = "clang";   Method = "Visual Studio 2026 LLVM toolset"; Ecosystem = "system"; Resolver = {
            $bin = Get-VSClangBinDir
            if ($bin) { Join-Path $bin "clang.exe" } else { $null }
        } },
        @{ Name = "glslc";   Cmd = "glslc";   Method = "Vulkan SDK";    Ecosystem = "system" },
        @{ Name = "ssms";    Cmd = $null;     Method = "SSMS (Visual Studio Installer)"; Ecosystem = "system"; Resolver = { Get-SsmsInstallationPath } },
        @{ Name = "claude";  Cmd = $null;     Method = "standalone CLI"; Ecosystem = "local"; Resolver = { Get-CommandDisplayFlexible -Name "claude" } },
        @{ Name = "claudine"; Cmd = $null;    Method = "shell wrapper (chthonic env)"; Ecosystem = "local"; Resolver = {
            $resolved = Get-CommandDisplayFlexible -Name "claudine"
            if ($resolved) { return $resolved }
            return (Get-ClaudineScriptPath)
        } },
        @{ Name = "gemini";   Cmd = $null;    Method = "bun-managed workspace dep (repo-local)"; Ecosystem = "bun"; Resolver = {
            $geminiExe = Join-Path $REPO_ROOT "node_modules\.bin\gemini.exe"
            if (Test-Path $geminiExe) { return $geminiExe }
            return $null
        } }
    )

    $ecoColors = @{ "uv" = "Magenta"; "bun" = "Yellow"; "cargo" = "Red"; "system" = "DarkGray"; "local" = "Green" }

    foreach ($section in @(@{ Label = "CORE"; Items = $tools }, @{ Label = "TOOLS"; Items = $secondary })) {
        foreach ($t in $section.Items) {
            $path = $null
            if ($t.ContainsKey("Resolver") -and $t.Resolver) {
                try { $path = & $t.Resolver } catch {}
            }
            if (-not $path -and $t.Cmd) {
                $path = Get-CommandPathFlexible -Name $t.Cmd
            }
            # Fallback: goup-managed Go when not in PATH
            if (-not $path -and $t.Name -eq "go") {
                $goupGo = Join-Path $env:USERPROFILE ".goup\current\bin\go.exe"
                if (Test-Path $goupGo) { $path = $goupGo }
            }
            if (-not $path -and $t.Name -eq "az") {
                $azBin = Get-AzureCliBinDir
                if ($azBin) { $path = Join-Path $azBin "az.cmd" }
            }
            $short = if ($path) {
                $path -replace [regex]::Escape($env:USERPROFILE), '~' -replace [regex]::Escape($env:APPDATA), '%APPDATA%'
            } else { "(not found)" }

            $nameStr = $t.Name.PadRight(10)
            $pathStr = $short.PadRight(44)
            $ecoColor = if ($ecoColors[$t.Ecosystem]) { $ecoColors[$t.Ecosystem] } else { $D }

            Write-Host "  $nameStr" -NoNewline -ForegroundColor $W
            if ($path) {
                Write-Host "$pathStr" -NoNewline -ForegroundColor $D
            } else {
                Write-Host "$pathStr" -NoNewline -ForegroundColor $R
            }
            Write-Host " $($t.Method)" -ForegroundColor $ecoColor
        }
        if ($section.Label -eq "CORE") {
            Write-Host "  $("-"*68)" -ForegroundColor $D
        }
    }

    # Directory taxonomy
    Write-Host ("="*72) -ForegroundColor $D
    $dirs = @(
        @{ Path = "~/.local/bin/";   Label = "user local bin (uv + standalone CLIs)" },
        @{ Path = "~/.bun/bin/";     Label = "bun runtime bin (bun/bunx; ambient shims are not authoritative for repo CLIs)" },
        @{ Path = "~/.cargo/bin/";   Label = "cargo ecosystem (rustc, rustup, mdbook, rv, goup)" },
        @{ Path = "~/.goup/";        Label = "goup-managed Go versions (go.dev source)" },
        @{ Path = "%APPDATA%\rv\";   Label = "rv-managed Ruby versions" },
        @{ Path = "%LOCALAPPDATA%\fnm\"; Label = "fnm-managed Node versions" }
    )

    $profileDir = Split-Path -Parent $PROFILE
    if ($profileDir) {
        $dirs += @{ Path = $profileDir; Label = "PowerShell profile wrappers (e.g., claudine function)" }
    }

    $azBinDir = Get-AzureCliBinDir
    if ($azBinDir) {
        $dirs += @{ Path = $azBinDir; Label = "Azure CLI (az)" }
    }

    $bicepBinDir = Get-BicepBinDir
    if ($bicepBinDir) {
        $dirs += @{ Path = $bicepBinDir; Label = "Bicep CLI (winget)" }
    }

    $sqlcmdBinDir = Get-SqlCmdBinDir
    if ($sqlcmdBinDir) {
        $dirs += @{ Path = $sqlcmdBinDir; Label = "Sqlcmd Tools (winget)" }
    }

    $sqlpackageBinDir = Get-SqlPackageBinDir
    if ($sqlpackageBinDir) {
        $dirs += @{ Path = $sqlpackageBinDir; Label = "SqlPackage (winget)" }
    }

    $vsBuild = Get-VSInstallationPath -ProductId "Microsoft.VisualStudio.Product.BuildTools"
    if ($vsBuild) {
        $dirs += @{ Path = $vsBuild; Label = "Visual Studio Build Tools 2026 (Insiders)" }
    }

    $vsProfessional = Get-VSInstallationPath -ProductId "Microsoft.VisualStudio.Product.Professional"
    if ($vsProfessional) {
        $dirs += @{ Path = $vsProfessional; Label = "Visual Studio Professional 2026 (Insiders)" }
    }

    $vsCommunity = Get-VSInstallationPath -ProductId "Microsoft.VisualStudio.Product.Community"
    if ($vsCommunity) {
        $dirs += @{ Path = $vsCommunity; Label = "Visual Studio Community 2026 (Insiders)" }
    }

    $vsEnterprise = Get-VSInstallationPath -ProductId "Microsoft.VisualStudio.Product.Enterprise"
    if ($vsEnterprise) {
        $dirs += @{ Path = $vsEnterprise; Label = "Visual Studio Enterprise 2026 (Insiders)" }
    }

    foreach ($dir in $dirs) {
        Write-Host "  $($dir.Path)" -NoNewline -ForegroundColor $C
        Write-Host "  $($dir.Label)" -ForegroundColor $D
    }
    Write-Host ("="*72) -ForegroundColor $D
    Write-Host ""
}

function Invoke-Doctor {
    param([switch]$Json, [switch]$Fix, [switch]$DryRun, [switch]$Origins)

    if ($Origins) { Show-Origins; return }

    # Tools: [display, endoflife.date product, ANNO manager, optional=skips if not installed]
    $checks = @(
        @{ Name = "ruby";       Product = "ruby";       Manager = "rv" },
        @{ Name = "python";     Product = "python";     Manager = "uv" },
        @{ Name = "bun";        Product = "bun";        Manager = "bun" },
        @{ Name = "brush";      Product = "brush-shell"; Manager = "cargo"; Optional = $true },
        @{ Name = "rust";       Product = "rust";       Manager = "rustup" },
        @{ Name = "go";         Product = "go";         Manager = "goup" },
        @{ Name = "visualstudio"; Product = "visual-studio"; Manager = "vs"; Optional = $true },
        @{ Name = "nodejs";     Product = "nodejs";     Manager = "bun"; Optional = $true },
        @{ Name = "postgresql";  Product = "postgresql"; Manager = "system"; Optional = $true },
        @{ Name = "dotnet";     Product = "dotnet";     Manager = "system"; Optional = $true }
    )

    $results = @()
    $fixable = @()
    $skippedOptional = @()

    if (-not $Json) {
        Write-Host ""
        Write-Host "CHTHONIC DOCTOR v$VERSION" -ForegroundColor Cyan -NoNewline
        Write-Host " | endoflife.date" -ForegroundColor DarkGray
        Write-Host ("="*72) -ForegroundColor DarkGray
    }

    foreach ($check in $checks) {
        $installed = Get-InstalledVersion $check.Name

        # Skip optional tools that aren't installed
        if ($check.Optional -and -not $installed) {
            $skippedOptional += $check.Name
            continue
        }

        $eolData = Get-EndOfLifeData $check.Product

        $latest = $null
        $eolDate = $null
        $badge = ""
        $fixTarget = $null

        if ($eolData -and $eolData.Count -gt 0) {
            $installedCycle = $null
            $latestCycle = $eolData[0]

            if ($installed -match '^(\d+\.\d+)') {
                $installedMajorMinor = $matches[1]
                $installedCycle = $eolData | Where-Object {
                    $installed -like "$($_.cycle)*" -or $installedMajorMinor -eq $_.cycle
                } | Select-Object -First 1
            }

            $latest = $latestCycle.latest
            $latestCycleVer = $latestCycle.cycle

            if (-not $installedCycle) { $installedCycle = $latestCycle }

            # EOL check
            $eolDate = $installedCycle.eol
            $isEol = $false
            $daysLeft = $null
            if ($eolDate -and $eolDate -ne $false -and $eolDate -is [string]) {
                try {
                    $eolParsed = [datetime]::Parse($eolDate)
                    $isEol = $eolParsed -lt (Get-Date)
                    $daysLeft = ($eolParsed - (Get-Date)).Days
                } catch {}
            }

            $cmp = Compare-Versions $installed $installedCycle.latest
            $cmpGlobal = Compare-Versions $installed $latest

            if ($isEol) {
                $badge = "EOL"
                $fixTarget = $latest
            } elseif ($daysLeft -and $daysLeft -lt 180) {
                $badge = "EOL in ${daysLeft}d"
                $fixTarget = $latest
            } elseif ($cmpGlobal -and $cmpGlobal -lt 0) {
                if ($installed -and $installedMajorMinor -ne $latestCycleVer) {
                    $badge = "upgrade $latestCycleVer"
                    $fixTarget = $latest
                } elseif ($cmp -and $cmp -lt 0) {
                    $badge = "patch $($installedCycle.latest)"
                    $fixTarget = $installedCycle.latest
                    # Guard: uv-managed lanes — endoflife.date publishes a version before
                    # python-build-standalone builds it. Verify the patch is in uv's index.
                    if ($check.Manager -eq "uv" -and $fixTarget) {
                        $uvIdx = (uv python list --all-versions 2>$null) -join "`n"
                        if ($uvIdx -notmatch "cpython-$([regex]::Escape($fixTarget))-") {
                            $badge = "current"
                            $fixTarget = $null
                        }
                    }
                } else {
                    $badge = "current"
                }
            } else {
                $badge = "current"
            }
        } else {
            $badge = "no API data"
        }

        $results += [pscustomobject]@{
            tool = $check.Name
            manager = $check.Manager
            installed = $installed
            latest = $latest
            badge = $badge
            eol = $eolDate
            fix_target = $fixTarget
            auto_fix = [bool]$global:DoctorFixMap[$check.Name]
            optional = [bool]$check.Optional
        }

        # Display line
        if ($Json) { continue }
        $mgr = $check.Manager.PadRight(6)
        $name = $check.Name.PadRight(10)
        $instStr = if ($installed) { $installed.PadRight(12) } else { "(missing)".PadRight(12) }

        Write-Host "  $mgr " -NoNewline -ForegroundColor Cyan
        Write-Host "$name " -NoNewline -ForegroundColor White
        Write-Host "$instStr " -NoNewline -ForegroundColor White

        switch -Wildcard ($badge) {
            "current"   { Write-Host $badge -ForegroundColor Green }
            "EOL"       { Write-Host "$badge  (eol: $eolDate)" -NoNewline -ForegroundColor Red }
            "EOL in*"   { Write-Host "$badge  (eol: $eolDate)" -NoNewline -ForegroundColor Yellow }
            "patch*"    { Write-Host $badge -NoNewline -ForegroundColor Yellow }
            "upgrade*"  { Write-Host "$badge available (latest: $latest)" -NoNewline -ForegroundColor Yellow }
            default     { Write-Host $badge -ForegroundColor DarkGray }
        }

        # Show fix/install command hint
        $fixInfo = $global:DoctorFixMap[$check.Name]
        $isMissing = -not $installed
        if ($isMissing -and $fixInfo -and $fixInfo.InstallDesc) {
            Write-Host "  -> $($fixInfo.InstallDesc)" -ForegroundColor DarkGray
            $fixable += @{ Tool = $check.Name; Target = $latest; Mode = "install"; FixInfo = $fixInfo }
        } elseif ($fixTarget -and $fixInfo) {
            Write-Host "  -> $($fixInfo.UpgradeDesc) $fixTarget" -ForegroundColor DarkGray
            $fixable += @{ Tool = $check.Name; Target = $fixTarget; Mode = "upgrade"; FixInfo = $fixInfo }
        } elseif ($badge -ne "current" -and $badge -ne "no API data") {
            Write-Host ""
        }
    }

    $currentCount = ($results.Count -gt 0) ? ($results | Where-Object { $_.status -eq "current" }).Count : (($checks | ForEach-Object { $_.Name }) | Where-Object { $_ -notin ($fixable.Tool) }).Count
    $checkedCount = $checks.Count - ($checks | Where-Object { $_.Optional -and -not (Get-InstalledVersion $_.Name) }).Count
    $fixCount = $fixable.Count
    $okCount = $checkedCount - $fixCount
    $pins = @(Get-DoctorPinState)
    $retentionNotes = @(Get-DoctorRetentionNotes)

    if (-not $Json) {
        Write-Host ("="*72) -ForegroundColor DarkGray
        Write-Host "  $okCount/$checkedCount current" -NoNewline -ForegroundColor $(if ($fixCount -eq 0) { "Green" } else { "Yellow" })
        if ($fixCount -gt 0) {
            Write-Host "  |  $fixCount fixable" -NoNewline -ForegroundColor Yellow
            Write-Host "  (--dry-run | --fix)" -NoNewline -ForegroundColor DarkGray
        }
        Write-Host "  | endoflife.date" -ForegroundColor DarkGray
        Write-Host ""

        # ── Infrastructure checks (linker shadow, OpenSSL) ──
        Write-Host "INFRASTRUCTURE" -ForegroundColor Cyan
        Write-Host ("="*72) -ForegroundColor DarkGray

        $linkerStatus = Get-LinkerShadowStatus
        Write-Host "  link.exe  " -NoNewline -ForegroundColor Cyan
        switch ($linkerStatus.effective) {
            "clear" {
                Write-Host "ok" -NoNewline -ForegroundColor Green
                if ($linkerStatus.resolved_first) {
                    Write-Host " — $($linkerStatus.resolved_first)" -ForegroundColor DarkGray
                } else { Write-Host "" }
            }
            "mitigated" {
                Write-Host "SHADOWED → mitigated" -ForegroundColor Yellow
                Write-Host "            raw PATH: $($linkerStatus.resolved_first)" -ForegroundColor DarkGray
                foreach ($m in $linkerStatus.mitigations) {
                    Write-Host "            [$($m.id)] $($m.name): $($m.value)" -ForegroundColor DarkGray
                }
            }
            "vulnerable" {
                Write-Host "SHADOWED → VULNERABLE" -ForegroundColor Red
                Write-Host "            raw PATH: $($linkerStatus.resolved_first)" -ForegroundColor DarkGray
                Write-Host "            expected MSVC: $($linkerStatus.msvc_linker)" -ForegroundColor DarkGray
                Write-Host "            no active mitigations — cargo builds will fail" -ForegroundColor Red
            }
        }

        $openssl = Get-OpenSSLStatus
        Write-Host "  openssl   " -NoNewline -ForegroundColor Cyan
        if ($openssl.version) {
            $opensslBadge = "v$($openssl.version)"
            switch ($openssl.effective) {
                "compatible"              { Write-Host "$opensslBadge" -ForegroundColor Green }
                "fully mitigated"         { Write-Host "$opensslBadge → fully mitigated" -ForegroundColor Green }
                "patched (env drift risk)" { Write-Host "$opensslBadge → patched" -NoNewline -ForegroundColor Green; Write-Host " (env drift risk — run doctor --fix)" -ForegroundColor Yellow }
                "env set (no cargo patch)" { Write-Host "$opensslBadge → env set" -NoNewline -ForegroundColor Yellow; Write-Host " (missing [patch.crates-io])" -ForegroundColor Red }
                "vulnerable"              { Write-Host "$opensslBadge → VULNERABLE" -ForegroundColor Red }
            }
            if (-not $openssl.dir_exists) {
                Write-Host "            OPENSSL_DIR missing or invalid: $($openssl.dir)" -ForegroundColor Red
            }
            foreach ($m in $openssl.mitigations) {
                Write-Host "            [$($m.id)] $($m.name): $($m.value)" -ForegroundColor DarkGray
            }
        } else {
            Write-Host "not found" -ForegroundColor DarkGray
        }
        Write-Host ""

        Write-Host "DOCTOR MODEL" -ForegroundColor Cyan
        Write-Host ("="*72) -ForegroundColor DarkGray
        Write-Host "  auto-fix managers   rv, uv, bun, rustup, goup, cargo(brush)" -ForegroundColor White
        Write-Host "  observed-only       visualstudio, dotnet, optional system lanes" -ForegroundColor DarkGray
        if ($skippedOptional.Count -gt 0) {
            Write-Host ("  skipped optional    {0}" -f ($skippedOptional -join ", ")) -ForegroundColor DarkGray
        }
        if ($pins.Count -gt 0) {
            Write-Host "  repo pins" -ForegroundColor Cyan
            foreach ($pin in $pins) {
                Write-Host ("    - {0} = {1}" -f $pin.name, $pin.value) -ForegroundColor White
                Write-Host ("      {0}" -f $pin.effect) -ForegroundColor DarkGray
            }
        }
        Write-Host "  retention" -ForegroundColor Cyan
        foreach ($note in $retentionNotes) {
            Write-Host ("    - {0}: {1}" -f $note.manager, $note.note) -ForegroundColor DarkGray
        }
        Write-Host ("="*72) -ForegroundColor DarkGray
        Write-Host ""
    }

    # --fix / --dry-run mode: execute or simulate upgrades and installs
    if (($Fix -or $DryRun) -and $fixable.Count -gt 0) {
        if ($DryRun) {
            Write-Host "DRY RUN — no changes will be made" -ForegroundColor Magenta
        } else {
            Write-Host "APPLYING FIXES" -ForegroundColor Cyan
        }
        Write-Host ("="*72) -ForegroundColor DarkGray
        foreach ($f in $fixable) {
            if ($f.Mode -eq "install") {
                $desc = "$($f.FixInfo.InstallDesc) $($f.Target)"
                Write-Host "  $($f.Tool): $desc" -ForegroundColor Yellow
                if ($DryRun) {
                    Write-Host "  -> would install (skipped)" -ForegroundColor Magenta
                } else {
                    try {
                        & $f.FixInfo.Install $f.Target
                        if ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE) {
                            Write-Host "  -> installed" -ForegroundColor Green
                        } else {
                            Write-Host "  -> failed (exit $LASTEXITCODE)" -ForegroundColor Red
                        }
                    } catch {
                        Write-Host "  -> error: $_" -ForegroundColor Red
                    }
                }
            } else {
                $desc = "$($f.FixInfo.UpgradeDesc) $($f.Target)"
                Write-Host "  $($f.Tool): $desc" -ForegroundColor Yellow
                if ($DryRun) {
                    Write-Host "  -> would upgrade (skipped)" -ForegroundColor Magenta
                } else {
                    try {
                        & $f.FixInfo.Upgrade $f.Target
                        if ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE) {
                            Write-Host "  -> done" -ForegroundColor Green
                        } else {
                            Write-Host "  -> failed (exit $LASTEXITCODE)" -ForegroundColor Red
                        }
                    } catch {
                        Write-Host "  -> error: $_" -ForegroundColor Red
                    }
                }
            }
        }
        Write-Host ("="*72) -ForegroundColor DarkGray
        Write-Host ""
    } elseif ($Fix -or $DryRun) {
        Write-Host "Nothing to fix — all current." -ForegroundColor Green
        Write-Host ""
    }

    # Infrastructure fixes (OpenSSL env var persistence)
    if ($Fix -or $DryRun) {
        $openssl = Get-OpenSSLStatus
        if ($openssl.version -and -not $openssl.env_persisted -and $openssl.dir_exists) {
            Write-Host "INFRASTRUCTURE FIX" -ForegroundColor Cyan
            Write-Host ("="*72) -ForegroundColor DarkGray
            $opensslVars = @{
                OPENSSL_DIR         = $openssl.dir
                OPENSSL_LIB_DIR     = Join-Path $openssl.dir "lib\VC\x64\MD"
                OPENSSL_INCLUDE_DIR = Join-Path $openssl.dir "include"
            }
            foreach ($k in $opensslVars.Keys) {
                $v = $opensslVars[$k]
                Write-Host "  $k = $v" -ForegroundColor Yellow
                if ($DryRun) {
                    Write-Host "  -> would persist to User scope (skipped)" -ForegroundColor Magenta
                } else {
                    [Environment]::SetEnvironmentVariable($k, $v, 'User')
                    Set-Item "env:$k" $v
                    Write-Host "  -> persisted to User scope" -ForegroundColor Green
                }
            }
            Write-Host ("="*72) -ForegroundColor DarkGray
            Write-Host ""
        }
    }

    if ($Json) {
        $payload = [pscustomobject]@{
            version = $VERSION
            provider = "endoflife.date"
            summary = [pscustomobject]@{
                checked = $checkedCount
                current = $okCount
                fixable = $fixCount
                skipped_optional = @($skippedOptional)
            }
            model = [pscustomobject]@{
                auto_fix_managers = @("rv", "uv", "bun", "rustup", "goup", "cargo(brush)")
                observed_only = @("visualstudio", "dotnet", "optional system lanes")
                repo_pins = $pins
                retention = $retentionNotes
            }
            checks = $results
            planned_fixes = @($fixable | ForEach-Object {
                [pscustomobject]@{
                    tool = $_.Tool
                    target = $_.Target
                    mode = $_.Mode
                    description = if ($_.Mode -eq "install") { $_.FixInfo.InstallDesc } else { $_.FixInfo.UpgradeDesc }
                }
            })
            infrastructure = [pscustomobject]@{
                linker = (Get-LinkerShadowStatus)
                openssl = (Get-OpenSSLStatus)
            }
        }
        Write-Output (ConvertTo-Json $payload -Depth 8)
    }
}

function Get-RvToolsDir {
    return (Join-Path $env:APPDATA "rv\tools")
}

function Get-RubyInstalledVersions {
    $rubyRoot = Join-Path $env:APPDATA "rv\rubies"
    if (-not (Test-Path $rubyRoot)) { return @() }

    return Get-ChildItem $rubyRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "ruby-*" } |
        Sort-Object Name |
        ForEach-Object {
            [pscustomobject]@{
                name = $_.Name
                path = $_.FullName
                zjit = [bool]($_.Name -match 'zjit')
            }
        }
}

function Get-RubyReleaseCachePath {
    $releaseRoot = Join-Path $env:LOCALAPPDATA "rv\ruby-v0\releases"
    foreach ($candidate in @(
        (Join-Path $releaseRoot "rubyinstaller2.json")
    )) {
        if (Test-Path $candidate) { return $candidate }
    }

    $latest = Get-ChildItem $releaseRoot -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($latest) { return $latest.FullName }
    return $null
}

function Get-RubyLatestStableVersion {
    $cachePath = Get-RubyReleaseCachePath
    if (-not $cachePath) { return $null }

    try {
        $payload = Get-Content $cachePath -Raw | ConvertFrom-Json
        $assets = $payload.release.assets
        $versions = @()
        foreach ($asset in $assets) {
            if ($asset.name -match '^ruby-(\d+\.\d+\.\d+)\.x64\.7z$') {
                try {
                    $versions += [pscustomobject]@{
                        raw = $matches[1]
                        sem = [version]$matches[1]
                    }
                } catch {}
            }
        }
        if (-not $versions) { return $null }
        return ($versions | Sort-Object sem -Descending | Select-Object -First 1).raw
    } catch {
        return $null
    }
}

function Get-RubyCurrentVersion {
    try {
        return (& ruby -e "print RUBY_VERSION" 2>$null | Select-Object -First 1).ToString().Trim()
    } catch {
        return $null
    }
}

function Get-RubyProblemDirs {
    $rubyRoot = Join-Path $env:APPDATA "rv\rubies"
    if (-not (Test-Path $rubyRoot)) { return @() }

    return Get-ChildItem $rubyRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "rubyinstaller-*" -or $_.Name -like "_hold_rubyinstaller-*" } |
        Sort-Object Name
}

function Get-RubyInterpreterMetadataIssues {
    $interpRoot = Join-Path $env:LOCALAPPDATA "rv\ruby-v0\interpreters"
    if (-not (Test-Path $interpRoot)) { return @() }

    return Get-ChildItem $interpRoot -File -ErrorAction SilentlyContinue |
        ForEach-Object {
            try {
                $raw = Get-Content $_.FullName -Raw | ConvertFrom-Json
                $path = "$($raw.path)"
                $issue = $null
                if (-not (Test-Path $path)) {
                    $issue = "path_missing"
                } elseif ($path -match 'rubyinstaller-\d+\.\d+\.\d+-\d+-x64') {
                    $issue = "installer_named_path"
                }
                if ($issue) {
                    [pscustomobject]@{
                        file = $_.FullName
                        path = $path
                        issue = $issue
                    }
                }
            } catch {}
        } | Where-Object { $_ }
}

function Get-RubyInstalledTools {
    $toolsDir = Get-RvToolsDir
    if (-not (Test-Path $toolsDir)) { return @() }

    return Get-ChildItem $toolsDir -Directory -ErrorAction SilentlyContinue |
        Sort-Object Name |
        ForEach-Object {
            $name = $_.Name
            $tool = $name
            $version = $null
            if ($name -match '^(.*)@([^@]+)$') {
                $tool = $matches[1]
                $version = $matches[2]
            }
            [pscustomobject]@{
                gem = $tool
                version = $version
                path = $_.FullName
            }
        }
}

function Invoke-RubyDoctor {
    param([switch]$Json, [switch]$Fix)

    $currentVersion = Get-RubyCurrentVersion
    $currentPath = $null
    try { $currentPath = (& rv ruby find 2>$null | Select-Object -First 1).ToString().Trim() } catch {}
    $jitBuild = if ($currentPath -and $currentPath -match 'zjit') { "zjit" } else { "standard" }
    # zjit build: socket.so/bigdecimal/json/parser load failures are expected and non-fatal
    $zjitKnownWarnings = $jitBuild -eq "zjit"
    $latestStable = Get-RubyLatestStableVersion
    $problemDirs = @(Get-RubyProblemDirs)
    $interpreterIssues = @(Get-RubyInterpreterMetadataIssues)

    if ($Fix) {
        $rvHome = Join-Path $env:APPDATA "rv"
        $quarantineRoot = Join-Path $rvHome "quarantine"
        New-Item -ItemType Directory -Force -Path $quarantineRoot | Out-Null

        foreach ($dir in $problemDirs) {
            if ($dir.FullName -notlike "$quarantineRoot*") {
                $dest = Join-Path $quarantineRoot ($dir.Name + "_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
                Move-Item $dir.FullName $dest -Force
            }
        }

        $interpRoot = Join-Path $env:LOCALAPPDATA "rv\ruby-v0\interpreters"
        $interpQuarantine = Join-Path $env:LOCALAPPDATA "rv\ruby-v0\interpreters-quarantine"
        New-Item -ItemType Directory -Force -Path $interpQuarantine | Out-Null
        foreach ($issue in $interpreterIssues) {
            if (Test-Path $issue.file) {
                Move-Item $issue.file (Join-Path $interpQuarantine (Split-Path $issue.file -Leaf)) -Force
            }
        }

        $problemDirs = @(Get-RubyProblemDirs)
        $interpreterIssues = @(Get-RubyInterpreterMetadataIssues)
    }

    $status = if ($currentVersion -and $latestStable) {
        try {
            if ([version]$currentVersion -ge [version]$latestStable) { "current" } else { "upgrade_available" }
        } catch { "unknown" }
    } else {
        "unknown"
    }

    $payload = [pscustomobject]@{
        manager = "rv"
        manager_version = (Get-InstalledVersion "rv")
        current_version = $currentVersion
        current_path = $currentPath
        jit_build = $jitBuild
        zjit_known_warnings_expected = $zjitKnownWarnings
        latest_stable = $latestStable
        status = $status
        problem_dirs = @($problemDirs | ForEach-Object {
            [pscustomobject]@{ name = $_.Name; path = $_.FullName }
        })
        interpreter_issues = @($interpreterIssues)
    }

    if ($Json) {
        Write-Output (ConvertTo-Json $payload -Depth 6)
        return 0
    }

    Write-Host ""
    Write-Host "CHTHONIC RUBY DOCTOR" -ForegroundColor Cyan
    Write-Host ("="*72) -ForegroundColor DarkGray
    Write-Host "  rv            " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($payload.manager_version) { $payload.manager_version } else { "not found" })) -ForegroundColor White
    Write-Host "  current       " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($payload.current_version) { $payload.current_version } else { "not found" })) -ForegroundColor White
    Write-Host "  latest stable " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($payload.latest_stable) { $payload.latest_stable } else { "unknown" })) -ForegroundColor White
    Write-Host "  status        " -NoNewline -ForegroundColor Cyan
    Write-Host $payload.status -ForegroundColor $(if ($payload.status -eq "current") { "Green" } else { "Yellow" })
    Write-Host "  jit build     " -NoNewline -ForegroundColor Cyan
    Write-Host $payload.jit_build -ForegroundColor $(if ($payload.jit_build -eq "zjit") { "Green" } else { "White" })
    if ($payload.zjit_known_warnings_expected) {
        Write-Host "  note: socket.so/bigdecimal/json/parser load warnings are expected in zjit build (non-fatal)" -ForegroundColor DarkYellow
    }
    Write-Host "  problem dirs  " -NoNewline -ForegroundColor Cyan
    Write-Host $payload.problem_dirs.Count -ForegroundColor White
    foreach ($item in $payload.problem_dirs) {
        Write-Host "    - $($item.path)" -ForegroundColor DarkGray
    }
    Write-Host "  interp issues " -NoNewline -ForegroundColor Cyan
    Write-Host $payload.interpreter_issues.Count -ForegroundColor White
    foreach ($issue in $payload.interpreter_issues) {
        Write-Host "    - $($issue.issue): $($issue.path)" -ForegroundColor DarkGray
    }
    Write-Host ""
    return 0
}

function Invoke-RubyUpgrade {
    param([switch]$Json)

    $latestStable = Get-RubyLatestStableVersion
    $currentVersion = Get-RubyCurrentVersion

    if (-not $latestStable) {
        Write-Error "Could not resolve latest stable Ruby version from rv cache."
        return 1
    }

    if ($currentVersion -and $currentVersion -eq $latestStable) {
        if ($Json) {
            Write-Output (ConvertTo-Json @{
                action = "noop"
                current = $currentVersion
                latest_stable = $latestStable
                reason = "already_current"
            } -Depth 4)
        } else {
            Write-Host "Ruby already current: $currentVersion" -ForegroundColor Green
        }
        return 0
    }

    & rv ruby install $latestStable
    return $LASTEXITCODE
}

function Invoke-RubyVersions {
    param([switch]$Json)

    if ($Json) {
        $activePath = $null
        $activeVersion = $null
        $managerVersion = $null
        try { $activePath = (& rv ruby find 2>$null | Select-Object -First 1).ToString().Trim() } catch {}
        try { $activeVersion = (& ruby -e "print RUBY_VERSION" 2>$null | Select-Object -First 1).ToString().Trim() } catch {}
        try {
            $rvOut = (rv --version 2>$null)
            if (($rvOut -join "`n") -match '(\d+\.\d+\.\d+)') { $managerVersion = $matches[1] }
        } catch {}

        $payload = [pscustomobject]@{
            manager = "rv"
            manager_version = $managerVersion
            active_ruby = $activeVersion
            active_path = $activePath
            installed = @(Get-RubyInstalledVersions)
        }
        Write-Output (ConvertTo-Json $payload -Depth 5)
        return
    }

    & rv ruby list
}

function Invoke-RubyTools {
    param([switch]$Json)

    if ($Json) {
        $payload = [pscustomobject]@{
            manager = "rv"
            tools = @(Get-RubyInstalledTools)
        }
        Write-Output (ConvertTo-Json $payload -Depth 5)
        return
    }

    & rv tool list
}

function Invoke-RubyLane {
    param([switch]$Json)

    $rvVersion = $null
    try {
        $rvOut = (rv --version 2>$null)
        if (($rvOut -join "`n") -match '(\d+\.\d+\.\d+)') { $rvVersion = $matches[1] }
    } catch {}

    $rubyVersion = Get-InstalledVersion "ruby"
    $rubyPath = $null
    try { $rubyPath = (& rv ruby find 2>$null | Select-Object -First 1).ToString().Trim() } catch {}

    $gccVersion = $null
    try {
        $gccOut = & gcc --version 2>$null
        if (($gccOut -join "`n") -match '(\d+\.\d+\.\d+)') { $gccVersion = $matches[1] }
    } catch {}

    $makeVersion = $null
    try { $makeVersion = (((make --version 2>$null) | Select-Object -First 1) -replace 'GNU Make\s*','').Trim() } catch {}

    $pacmanVersion = $null
    try {
        $out = & pacman --version 2>$null
        if (($out -join "`n") -match 'Pacman v(\d+\.\d+\.\d+)') { $pacmanVersion = $matches[1] }
    } catch {}

    $msys2Home = if ($env:MSYS2_HOME) {
        $env:MSYS2_HOME
    } else {
        $root = Get-RubyDevKitRoot
        if ($root) {
            $candidate = Join-Path $root "msys64"
            if (Test-Path $candidate) { $candidate } else { $null }
        } else { $null }
    }

    # JIT probe — detect zjit build and query enabled state (2>$null silences RubyGems load warnings)
    $jitBuild = if ($rubyPath -and $rubyPath -match 'zjit') { "zjit" } else { "standard" }
    $zjitEnabled = $false
    $yjitEnabled = $false
    if ($jitBuild -eq "zjit" -and $rubyPath -and (Test-Path $rubyPath)) {
        try {
            $zjitOut = (& $rubyPath --zjit -e "print (RubyVM::ZJIT.enabled? rescue false)" 2>$null)
            $zjitEnabled = "$zjitOut".Trim() -eq 'true'
        } catch {}
        try {
            $yjitOut = (& $rubyPath --yjit -e "print (RubyVM::YJIT.enabled? rescue false)" 2>$null)
            $yjitEnabled = "$yjitOut".Trim() -eq 'true'
        } catch {}
    }

    $payload = [pscustomobject]@{
        manager = [pscustomobject]@{
            name = "rv"
            version = $rvVersion
        }
        runtime = [pscustomobject]@{
            ruby = $rubyVersion
            ruby_path = $rubyPath
        }
        jit = [pscustomobject]@{
            build = $jitBuild
            zjit_enabled = $zjitEnabled
            yjit_enabled = $yjitEnabled
        }
        toolchain = [pscustomobject]@{
            gcc = $gccVersion
            make = $makeVersion
            pacman = $pacmanVersion
            msys2_home = $msys2Home
        }
        tools = @(Get-RubyInstalledTools)
    }

    if ($Json) {
        Write-Output (ConvertTo-Json $payload -Depth 6)
        return
    }

    Write-Host ""
    Write-Host "CHTHONIC RUBY LANE" -ForegroundColor Cyan
    Write-Host ("="*72) -ForegroundColor DarkGray
    Write-Host "  rv       " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($payload.manager.version) { $payload.manager.version } else { "not found" })) -ForegroundColor White
    Write-Host "  ruby     " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($payload.runtime.ruby) { $payload.runtime.ruby } else { "not found" })) -NoNewline -ForegroundColor White
    if ($payload.runtime.ruby_path) {
        Write-Host "  $($payload.runtime.ruby_path)" -ForegroundColor DarkGray
    } else {
        Write-Host ""
    }
    Write-Host "  jit      " -NoNewline -ForegroundColor Cyan
    $jitBuildLabel = $payload.jit.build
    $zjitTag = if ($payload.jit.zjit_enabled) { "ZJIT:on" } else { "ZJIT:off" }
    $yjitTag = if ($payload.jit.yjit_enabled) { "YJIT:on" } else { "YJIT:off" }
    $jitColor = if ($payload.jit.zjit_enabled -or $payload.jit.yjit_enabled) { "Green" } else { "DarkGray" }
    Write-Host "$jitBuildLabel  $zjitTag  $yjitTag" -ForegroundColor $jitColor
    Write-Host "  gcc      " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($payload.toolchain.gcc) { $payload.toolchain.gcc } else { "not found" })) -NoNewline -ForegroundColor White
    Write-Host "  make " -NoNewline -ForegroundColor DarkGray
    Write-Host ($(if ($payload.toolchain.make) { $payload.toolchain.make } else { "not found" })) -NoNewline -ForegroundColor White
    Write-Host "  pacman " -NoNewline -ForegroundColor DarkGray
    Write-Host ($(if ($payload.toolchain.pacman) { $payload.toolchain.pacman } else { "not found" })) -ForegroundColor White
    Write-Host "  msys2    " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($payload.toolchain.msys2_home) { $payload.toolchain.msys2_home } else { "not found" })) -ForegroundColor DarkGray
    Write-Host "  tools    " -NoNewline -ForegroundColor Cyan
    Write-Host ($payload.tools.Count) -ForegroundColor White
    foreach ($tool in $payload.tools) {
        Write-Host "    - $($tool.gem)" -NoNewline -ForegroundColor White
        if ($tool.version) {
            Write-Host " @$($tool.version)" -ForegroundColor DarkGray
        } else {
            Write-Host ""
        }
    }
    Write-Host ""
}

function Invoke-PythonLane {
    param([switch]$Json)

    $pythonVersion = Get-InstalledVersion "python"
    $uvVersion = Get-InstalledVersion "uv"
    $pythonPath = $null
    try {
        $uvPython = (uv python find 2>$null | Select-Object -First 1)
        if ($uvPython -and (Test-Path $uvPython)) {
            $pythonPath = $uvPython
        }
    } catch {}
    if (-not $pythonPath) {
        try {
            $pythonCmd = Get-Command python -ErrorAction Stop
            if ($pythonCmd.Source -and (Test-Path $pythonCmd.Source)) { $pythonPath = $pythonCmd.Source }
        } catch {}
    }

    $payload = [pscustomobject]@{
        manager = [pscustomobject]@{
            uv = $uvVersion
            uv_path = (Get-CommandPathFlexible -Name "uv")
        }
        runtime = [pscustomobject]@{
            python = $pythonVersion
            python_path = $pythonPath
            pin = if (Test-Path ".python-version") { (Get-Content ".python-version" -ErrorAction SilentlyContinue | Select-Object -First 1) } else { $null }
        }
    }

    if ($Json) {
        Write-Output (ConvertTo-Json $payload -Depth 5)
        return
    }

    Write-Host ""
    Write-Host "CHTHONIC PYTHON LANE" -ForegroundColor Cyan
    Write-Host ("="*72) -ForegroundColor DarkGray
    Write-Host "  uv       " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($uvVersion) { $uvVersion } else { "not found" })) -NoNewline -ForegroundColor White
    if ($payload.manager.uv_path) { Write-Host "  $($payload.manager.uv_path)" -ForegroundColor DarkGray } else { Write-Host "" }
    Write-Host "  python   " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($pythonVersion) { $pythonVersion } else { "not found" })) -NoNewline -ForegroundColor White
    if ($pythonPath) { Write-Host "  $pythonPath" -ForegroundColor DarkGray } else { Write-Host "" }
    if ($payload.runtime.pin) {
        Write-Host "  pin      " -NoNewline -ForegroundColor Cyan
        Write-Host $payload.runtime.pin -ForegroundColor DarkGray
    }
    Write-Host ""
}

function Repair-WorkspaceAudit {
    # Parse bun audit output, auto-update overrides in package.json, re-install, re-audit.
    # Returns $true if workspace is clean (either initially or after auto-patch).
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$WorkspaceDir,
        [Parameter(Mandatory)][string]$Label
    )
    Push-Location $WorkspaceDir
    try {
        $auditLines = @(& bun audit 2>&1)
        $auditStr   = $auditLines -join "`n"

        if ($auditStr -match "No vulnerabilities found") {
            Write-Host "  ✅ $Label`: CLEAN" -ForegroundColor Green
            return $true
        }

        Write-Host "  ⚠️  $Label`: vulnerabilities found — auto-patching overrides..." -ForegroundColor Yellow
        $auditLines | Where-Object { $_ -match '^\s+\S' -or ($_ -match '^@?[a-z]' -and $_ -match '<|>=') } |
            ForEach-Object { Write-Host "     $_" -ForegroundColor DarkYellow }

        $pkgJsonPath = Join-Path $WorkspaceDir "package.json"
        if (-not (Test-Path $pkgJsonPath)) {
            Write-Host "  ❌ $Label`: no package.json found at $WorkspaceDir — cannot auto-patch" -ForegroundColor Red
            return $false
        }
        $pkg = Get-Content $pkgJsonPath -Raw | ConvertFrom-Json
        if (-not $pkg.PSObject.Properties['overrides']) {
            $pkg | Add-Member -MemberType NoteProperty -Name 'overrides' -Value ([PSCustomObject]@{}) -Force
        }

        # Collect (package → minSafeVersion) pairs; keep highest min-safe per package
        $needed = @{}
        foreach ($line in $auditLines) {
            # Only process vulnerability-range lines (start with package name, no leading space)
            if ($line -notmatch '^(@?[a-z0-9][a-z0-9_@/.-]*)\s+') { continue }
            $pkgName = $matches[1].Trim()
            $spec    = $null

            if ($line -match '<=\s*([0-9][0-9a-z.-]*)') {
                # Vulnerable up to and including version — need strictly greater
                $spec = ">$($matches[1].Trim())"
            } elseif ($line -match '<([0-9][0-9a-z.-]*)') {
                # Exclusive upper bound — that version is the minimum safe (exact pin)
                $spec = $matches[1].Trim()
            }

            if (-not $spec) { continue }

            # Keep the higher minimum when the same package appears more than once
            if ($needed.ContainsKey($pkgName)) {
                try {
                    $curVer  = [version]($needed[$pkgName] -replace '^[>= ]+', '')
                    $newVer  = [version]($spec -replace '^[>= ]+', '')
                    if ($newVer -gt $curVer) { $needed[$pkgName] = $spec }
                } catch { $needed[$pkgName] = $spec }
            } else {
                $needed[$pkgName] = $spec
            }
        }

        if ($needed.Count -eq 0) {
            Write-Host "  ❌ $Label`: could not parse vulnerability lines — manual remediation required" -ForegroundColor Red
            return $false
        }

        foreach ($kv in $needed.GetEnumerator()) {
            $pkg.overrides | Add-Member -MemberType NoteProperty -Name $kv.Key -Value $kv.Value -Force
            Write-Host "    + override: $($kv.Key) $($kv.Value)" -ForegroundColor DarkYellow
        }

        Set-Content $pkgJsonPath (ConvertTo-Json $pkg -Depth 20) -Encoding utf8NoBOM
        Write-Host "  → bun install (applying $($needed.Count) new overrides)..." -ForegroundColor DarkGray
        & bun install 2>&1 | Out-Null

        $recheck = @(& bun audit 2>&1) -join ""
        if ($recheck -match "No vulnerabilities found") {
            Write-Host "  ✅ $Label`: CLEAN after auto-patch" -ForegroundColor Green
            return $true
        }
        Write-Host "  ❌ $Label`: still dirty after auto-patch — manual remediation required" -ForegroundColor Red
        return $false
    } finally {
        Pop-Location
    }
}

function Invoke-GeminiUpdate {
    [CmdletBinding()]
    param()

    Write-Host ""
    Write-Host "GEMINI CLI VERSION POLICY" -ForegroundColor Cyan
    Write-Host ("="*72) -ForegroundColor DarkGray

    # Read currently installed version from repo node_modules
    $repoGeminiPkg = Join-Path $REPO_ROOT "node_modules\@google\gemini-cli\package.json"
    $installedVersion = $null
    if (Test-Path $repoGeminiPkg) {
        try {
            $pkgJson = Get-Content $repoGeminiPkg -Raw | ConvertFrom-Json
            $installedVersion = $pkgJson.version
        } catch {}
    }
    Write-Host "  Installed (repo node_modules): " -NoNewline -ForegroundColor White
    Write-Host ($(if ($installedVersion) { $installedVersion } else { "not found" })) -ForegroundColor $(if ($installedVersion) { "Green" } else { "Red" })

    # Fetch preview version from npm registry (preview dist-tag is the active lane)
    $latestVersion = $null
    try {
        $resp = Invoke-RestMethod "https://registry.npmjs.org/@google%2Fgemini-cli/preview" -TimeoutSec 10
        $latestVersion = $resp.version
    } catch {
        Write-Warning "Could not fetch preview from npm registry: $($_.Exception.Message)"
    }
    Write-Host "  Preview   (npm registry):      " -NoNewline -ForegroundColor White
    if ($latestVersion) {
        $versionColor = if ($installedVersion -and ($latestVersion -eq $installedVersion)) { "Green" } else { "Yellow" }
        Write-Host $latestVersion -ForegroundColor $versionColor
    } else {
        Write-Host "unavailable" -ForegroundColor Red
    }

    Write-Host ""
    if ($latestVersion -and $installedVersion -and ($latestVersion -ne $installedVersion)) {
        Write-Host "  → Updating @google/gemini-cli $installedVersion → $latestVersion in both workspaces..." -ForegroundColor Cyan
        # bun add @preview resolves the dist-tag and writes the exact version to package.json
        # preserves overrides block; does NOT use --latest (stable) tag
        Push-Location $REPO_ROOT
        & bun add -D "@google/gemini-cli@preview"
        Pop-Location
        Push-Location $env:USERPROFILE
        & bun add "@google/gemini-cli@preview"
        Pop-Location
        Write-Host ""
    } else {
        Write-Host "  ✅ Already at preview." -ForegroundColor Green
        Write-Host ""
    }

    # Self-healing audit: detect new transitive vulns from updated gemini-cli deps,
    # auto-patch overrides in package.json, re-install, re-verify in BOTH scopes.
    Write-Host "  → Audit + self-heal (repo scope)..." -ForegroundColor DarkGray
    $repoClean = Repair-WorkspaceAudit -WorkspaceDir $REPO_ROOT -Label "Repo"

    Write-Host "  → Audit + self-heal (home scope ~)..." -ForegroundColor DarkGray
    $homeClean = Repair-WorkspaceAudit -WorkspaceDir $env:USERPROFILE -Label "Home (~)"

    Write-Host ""
    if ($repoClean -and $homeClean) {
        Write-Host "  ✅ Gemini version policy: CLEAN across all scopes." -ForegroundColor Green
    } else {
        Write-Host "  ❌ Gemini version policy: auto-patch failed. See output above." -ForegroundColor Red
        Write-Host "     Manual fix: update 'overrides' in package.json then run 'bun install'." -ForegroundColor DarkGray
    }
    Write-Host ""
}

function Invoke-BunLane {
    param([switch]$Json)

    $bunVersion = Get-InstalledVersion "bun"
    $bunPath = Get-CommandPathFlexible -Name "bun"
    $nodeVersion = Get-InstalledVersion "nodejs"
    $nodePath = Get-FnmNodeExePath

    $payload = [pscustomobject]@{
        manager = [pscustomobject]@{
            bun = $bunVersion
            bun_path = $bunPath
        }
        runtime = [pscustomobject]@{
            node = $nodeVersion
            node_path = $nodePath
        }
    }

    if ($Json) {
        Write-Output (ConvertTo-Json $payload -Depth 5)
        return
    }

    Write-Host ""
    Write-Host "CHTHONIC BUN LANE" -ForegroundColor Cyan
    Write-Host ("="*72) -ForegroundColor DarkGray
    Write-Host "  bun      " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($bunVersion) { $bunVersion } else { "not found" })) -NoNewline -ForegroundColor White
    if ($bunPath) { Write-Host "  $bunPath" -ForegroundColor DarkGray } else { Write-Host "" }
    Write-Host "  node     " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($nodeVersion) { $nodeVersion } else { "not found" })) -NoNewline -ForegroundColor White
    if ($nodePath) { Write-Host "  $nodePath" -ForegroundColor DarkGray } else { Write-Host "" }
    Write-Host ""
}

function Invoke-RustLane {
    param([switch]$Json)

    $rustVersion = Get-InstalledVersion "rust"
    $cargoVersion = Get-InstalledVersion "cargo"
    $rustupVersion = Get-InstalledVersion "rustup"
    $rustToolchainPin = $null
    if (Test-Path "rust-toolchain.toml") {
        $content = Get-Content "rust-toolchain.toml" -Raw
        if ($content -match 'channel\s*=\s*"([^"]+)"') {
            $rustToolchainPin = $matches[1]
        }
    }

    $payload = [pscustomobject]@{
        manager = [pscustomobject]@{
            rustup = $rustupVersion
            rustup_path = (Get-CommandPathFlexible -Name "rustup")
        }
        runtime = [pscustomobject]@{
            rustc = $rustVersion
            rustc_path = (Get-CommandPathFlexible -Name "rustc")
            cargo = $cargoVersion
            cargo_path = (Get-CommandPathFlexible -Name "cargo")
            toolchain_pin = $rustToolchainPin
        }
    }

    if ($Json) {
        Write-Output (ConvertTo-Json $payload -Depth 5)
        return
    }

    Write-Host ""
    Write-Host "CHTHONIC RUST LANE" -ForegroundColor Cyan
    Write-Host ("="*72) -ForegroundColor DarkGray
    Write-Host "  rustup   " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($rustupVersion) { $rustupVersion } else { "not found" })) -NoNewline -ForegroundColor White
    if ($payload.manager.rustup_path) { Write-Host "  $($payload.manager.rustup_path)" -ForegroundColor DarkGray } else { Write-Host "" }
    Write-Host "  rustc    " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($rustVersion) { $rustVersion } else { "not found" })) -NoNewline -ForegroundColor White
    if ($payload.runtime.rustc_path) { Write-Host "  $($payload.runtime.rustc_path)" -ForegroundColor DarkGray } else { Write-Host "" }
    Write-Host "  cargo    " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($cargoVersion) { $cargoVersion } else { "not found" })) -ForegroundColor White
    if ($rustToolchainPin) {
        Write-Host "  pin      " -NoNewline -ForegroundColor Cyan
        Write-Host $rustToolchainPin -ForegroundColor DarkGray
    }
    Write-Host ""
}

function Invoke-GoLane {
    param([switch]$Json)

    $goVersion = Get-InstalledVersion "go"
    $goupVersion = Get-InstalledVersion "goup"
    $goPath = $null
    try {
        $goCmd = Get-Command go -ErrorAction Stop
        if ($goCmd.Source -and (Test-Path $goCmd.Source)) { $goPath = $goCmd.Source }
    } catch {}
    if (-not $goPath) {
        $candidate = Join-Path $env:USERPROFILE ".goup\current\bin\go.exe"
        if (Test-Path $candidate) { $goPath = $candidate }
    }

    $payload = [pscustomobject]@{
        manager = [pscustomobject]@{
            goup = $goupVersion
            goup_path = (Get-CommandPathFlexible -Name "goup")
        }
        runtime = [pscustomobject]@{
            go = $goVersion
            go_path = $goPath
        }
    }

    if ($Json) {
        Write-Output (ConvertTo-Json $payload -Depth 5)
        return
    }

    Write-Host ""
    Write-Host "CHTHONIC GO LANE" -ForegroundColor Cyan
    Write-Host ("="*72) -ForegroundColor DarkGray
    Write-Host "  goup     " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($goupVersion) { $goupVersion } else { "not found" })) -NoNewline -ForegroundColor White
    if ($payload.manager.goup_path) { Write-Host "  $($payload.manager.goup_path)" -ForegroundColor DarkGray } else { Write-Host "" }
    Write-Host "  go       " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($goVersion) { $goVersion } else { "not found" })) -NoNewline -ForegroundColor White
    if ($goPath) { Write-Host "  $goPath" -ForegroundColor DarkGray } else { Write-Host "" }
    Write-Host ""
}

function Invoke-RLane {
    param([switch]$Json)

    $rVersion = Get-InstalledVersion "r"
    $rscriptVersion = Get-InstalledVersion "rscript"
    $rrvVersion = Get-InstalledVersion "rv-r"
    $rPath = Get-RExePath
    $rscriptPath = Get-RScriptExePath
    $rrvPath = Get-RRvScriptPath

    $payload = [pscustomobject]@{
        manager = [pscustomobject]@{
            current = "rv-r (packages)"
            note    = "R runtime has no version manager (rig not installed)"
        }
        runtime = [pscustomobject]@{
            r = $rVersion
            r_path = $rPath
            rscript = $rscriptVersion
            rscript_path = $rscriptPath
        }
        packages = [pscustomobject]@{
            rv_r = $rrvVersion
            rv_r_wrapper = $rrvPath
            rv_r_home = (Join-Path $env:USERPROFILE ".r-rv")
        }
        shell = [pscustomobject]@{
            r_binding = $env:CHTHONIC_R_BINDING
            r_binding_reason = $env:CHTHONIC_R_BINDING_REASON
        }
    }

    if ($Json) {
        Write-Output (ConvertTo-Json $payload -Depth 6)
        return
    }

    Write-Host ""
    Write-Host "CHTHONIC R LANE" -ForegroundColor Cyan
    Write-Host ("="*72) -ForegroundColor DarkGray
    Write-Host "  manager  " -NoNewline -ForegroundColor Cyan
    Write-Host "rv-r (packages)" -NoNewline -ForegroundColor White
    Write-Host "  R runtime unmanaged — rig not installed" -ForegroundColor DarkGray
    Write-Host "  R        " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($rVersion) { $rVersion } else { "not found" })) -NoNewline -ForegroundColor White
    if ($rPath) { Write-Host "  $rPath" -ForegroundColor DarkGray } else { Write-Host "" }
    Write-Host "  Rscript  " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($rscriptVersion) { $rscriptVersion } else { "not found" })) -NoNewline -ForegroundColor White
    if ($rscriptPath) { Write-Host "  $rscriptPath" -ForegroundColor DarkGray } else { Write-Host "" }
    Write-Host "  rv-r     " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($rrvVersion) { $rrvVersion } else { "not found" })) -NoNewline -ForegroundColor White
    if ($rrvPath) { Write-Host "  $rrvPath" -ForegroundColor DarkGray } else { Write-Host "" }
    if ($payload.shell.r_binding_reason) {
        Write-Host "  binding  " -NoNewline -ForegroundColor Cyan
        Write-Host $payload.shell.r_binding_reason -ForegroundColor DarkGray
    }
    Write-Host ""
}

function Invoke-ZigLane {
    param([switch]$Json)

    $zvVersion = Get-InstalledVersion "zv"
    $zigVersion = Get-InstalledVersion "zig"
    $zvPath = Get-ZvExePath
    $zigPath = Get-ZigExePath

    $payload = [pscustomobject]@{
        manager = [pscustomobject]@{
            zv = $zvVersion
            zv_path = $zvPath
        }
        runtime = [pscustomobject]@{
            zig = $zigVersion
            zig_path = $zigPath
        }
    }

    if ($Json) {
        Write-Output (ConvertTo-Json $payload -Depth 5)
        return
    }

    Write-Host ""
    Write-Host "CHTHONIC ZIG LANE" -ForegroundColor Cyan
    Write-Host ("="*72) -ForegroundColor DarkGray
    Write-Host "  zv       " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($zvVersion) { $zvVersion } else { "not found" })) -NoNewline -ForegroundColor White
    if ($zvPath) { Write-Host "  $zvPath" -ForegroundColor DarkGray } else { Write-Host "" }
    Write-Host "  zig      " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($zigVersion) { $zigVersion } else { "not found" })) -NoNewline -ForegroundColor White
    if ($zigPath) { Write-Host "  $zigPath" -ForegroundColor DarkGray } else { Write-Host "" }
    Write-Host ""
}

function Get-DirectorySizeBytes {
    param([string]$Path)

    if (-not (Test-Path $Path)) { return $null }

    try {
        return (Get-ChildItem -LiteralPath $Path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
    } catch {
        return $null
    }
}

function Get-GraphicsShaderSources {
    $roots = @(
        (Join-Path $REPO_ROOT "assets\shaders"),
        (Join-Path $REPO_ROOT "extensions\chthonic-archive\native\chthonic-daemon\src\shaders")
    )

    $sources = @()
    foreach ($root in $roots) {
        if (-not (Test-Path $root)) { continue }
        $sources += Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
            [pscustomobject]@{
                root = $root
                name = $_.Name
                path = $_.FullName
                ext = $_.Extension
            }
        }
    }

    return @($sources | Sort-Object path)
}

function Get-HlslShaderSources {
    $root = Join-Path $REPO_ROOT "assets\shaders\hlsl"
    if (-not (Test-Path $root)) { return @() }

    return @(
        Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
            [pscustomobject]@{
                root = $root
                name = $_.Name
                path = $_.FullName
                ext = $_.Extension
            }
        } | Sort-Object path
    )
}

function Invoke-GraphicsLane {
    param([switch]$Json)

    $glslcPath = Get-CommandPathFlexible -Name "glslc"
    $glslcVersion = $null
    if ($glslcPath) {
        try {
            $glslcOut = & $glslcPath --version 2>$null
            if ($glslcOut) {
                $glslcVersion = ($glslcOut | Select-Object -First 1).ToString().Trim()
            }
        } catch {}
    }

    $dxcPath = Get-CommandPathFlexible -Name "dxc"
    $dxcVersion = $null
    if ($dxcPath) {
        try {
            $dxcOut = & $dxcPath -help 2>$null
            $dxcVersion = (($dxcOut | Where-Object { $_ -match '^Version:' } | Select-Object -First 1).ToString().Trim())
        } catch {}
    }

    $nvccPath = Get-CommandPathFlexible -Name "nvcc"
    $nvccVersion = $null
    if ($nvccPath) {
        try {
            $nvccOut = & $nvccPath --version 2>$null
            if (($nvccOut -join "`n") -match 'release\s+([0-9]+\.[0-9]+),\s+V([0-9][^\s]+)') {
                $nvccVersion = "CUDA $($matches[1]) / nvcc $($matches[2])"
            }
        } catch {}
    }

    $clPath = Get-VSClExePath
    $msbuildPath = Get-VSMsBuildExePath
    $vsInsiders = Get-VSInstallationPath -ProductId "Microsoft.VisualStudio.Product.Community"
    $devenvPath = if ($vsInsiders) {
        $candidate = Join-Path $vsInsiders "Common7\IDE\devenv.exe"
        if (Test-Path $candidate) { $candidate } else { $null }
    } else { $null }

    $cudnnDirs = @(
        Get-ChildItem "C:\Program Files\NVIDIA\CUDNN" -Directory -ErrorAction SilentlyContinue |
            Sort-Object Name |
            ForEach-Object { $_.FullName }
    )

    $tensorRtDirs = @(
        Get-ChildItem "C:\Program Files\NVIDIA" -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like "TensorRT*" } |
            Sort-Object Name |
            ForEach-Object { $_.FullName }
    )

    $cacheTargets = @(
        [pscustomobject]@{ name = "DXCache"; path = (Join-Path $env:LOCALAPPDATA "NVIDIA\DXCache") },
        [pscustomobject]@{ name = "GLCache"; path = (Join-Path $env:LOCALAPPDATA "NVIDIA\GLCache") },
        [pscustomobject]@{ name = "ComputeCache"; path = (Join-Path $env:LOCALAPPDATA "NVIDIA\ComputeCache") },
        [pscustomobject]@{ name = "D3DSCache"; path = (Join-Path $env:LOCALAPPDATA "D3DSCache") }
    ) | ForEach-Object {
        [pscustomobject]@{
            name = $_.name
            path = $_.path
            exists = Test-Path $_.path
            size_bytes = Get-DirectorySizeBytes $_.path
        }
    }

    $shaderSources = @(Get-GraphicsShaderSources)
    $hlslSources = @(Get-HlslShaderSources)
    $cudaProbeSource = Join-Path $REPO_ROOT "native\cuda\chthonic_probe.cu"
    $videoControllers = @(
        Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue |
            Select-Object Name, DriverVersion, AdapterRAM
    )

    $systemInfo = Get-CimInstance Win32_ComputerSystem -ErrorAction SilentlyContinue |
        Select-Object Manufacturer, Model, TotalPhysicalMemory

    $linkerStatus = Get-LinkerShadowStatus
    $opensslStatus = Get-OpenSSLStatus

    $payload = [pscustomobject]@{
        host = [pscustomobject]@{
            manufacturer = $systemInfo.Manufacturer
            model = $systemInfo.Model
            total_physical_memory = $systemInfo.TotalPhysicalMemory
        }
        gpu = [pscustomobject]@{
            controllers = $videoControllers
            nvidia_smi_driver = $null
            cuda_driver_version = $null
        }
        graphics = [pscustomobject]@{
            vulkan_sdk = $env:VULKAN_SDK
            glslc_path = $glslcPath
            glslc_version = $glslcVersion
            dxc_path = $dxcPath
            dxc_version = $dxcVersion
        }
        compute = [pscustomobject]@{
            nvcc_path = $nvccPath
            nvcc_version = $nvccVersion
            cuda_path = $env:CUDA_PATH
            cudnn_dirs = $cudnnDirs
            tensorrt_dirs = $tensorRtDirs
        }
        msvc = [pscustomobject]@{
            cl_path = $clPath
            msbuild_path = $msbuildPath
            devenv_path = $devenvPath
            link_path = $linkerStatus.resolved_first
            linker_shadow = $linkerStatus.shadow
            linker_effective = $linkerStatus.effective
            linker_mitigations = $linkerStatus.mitigations
            cargo_config_linker = $linkerStatus.cargo_config_linker
        }
        openssl = [pscustomobject]@{
            version = $opensslStatus.version
            major = $opensslStatus.major
            effective = $opensslStatus.effective
            mitigations = $opensslStatus.mitigations
            dir = $opensslStatus.dir
            lib_dir = $opensslStatus.lib_dir
            include_dir = $opensslStatus.include_dir
            dir_exists = $opensslStatus.dir_exists
            env_persisted = $opensslStatus.env_persisted
            has_cargo_patch = $opensslStatus.has_cargo_patch
        }
        shaders = [pscustomobject]@{
            source_count = $shaderSources.Count
            sources = $shaderSources
            hlsl_source_count = $hlslSources.Count
            hlsl_sources = $hlslSources
        }
        caches = $cacheTargets
        repo = [pscustomobject]@{
            vs_dir_exists = (Test-Path (Join-Path $REPO_ROOT ".vs"))
            vscode_dir_exists = (Test-Path (Join-Path $REPO_ROOT ".vscode"))
            cmake_lists_exists = (Test-Path (Join-Path $REPO_ROOT "CMakeLists.txt"))
            cmake_presets_exists = (Test-Path (Join-Path $REPO_ROOT "CMakePresets.json"))
            cuda_probe_exists = (Test-Path $cudaProbeSource)
            tensor_runtime_host_exists = (Test-Path (Join-Path $REPO_ROOT "extensions\chthonic-archive\native\tensor-runtime-host\Cargo.toml"))
        }
    }

    try {
        $nvidiaOut = & nvidia-smi 2>$null
        if (($nvidiaOut -join "`n") -match 'Driver Version:\s*([0-9\.]+)\s+CUDA Version:\s*([0-9\.]+)') {
            $payload.gpu.nvidia_smi_driver = $matches[1]
            $payload.gpu.cuda_driver_version = $matches[2]
        }
    } catch {}

    if ($Json) {
        Write-Output (ConvertTo-Json $payload -Depth 8)
        return
    }

    Write-Host ""
    Write-Host "CHTHONIC GRAPHICS LANE" -ForegroundColor Cyan
    Write-Host ("="*72) -ForegroundColor DarkGray
    Write-Host "  host     " -NoNewline -ForegroundColor Cyan
    Write-Host ("{0} / {1}" -f $payload.host.manufacturer, $payload.host.model) -ForegroundColor White
    Write-Host "  gpu      " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($payload.gpu.controllers.Count -gt 0) { $payload.gpu.controllers[0].Name } else { "not found" })) -ForegroundColor White
    Write-Host "  vulkan   " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($payload.graphics.vulkan_sdk) { $payload.graphics.vulkan_sdk } else { "not found" })) -ForegroundColor White
    Write-Host "  glslc    " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($payload.graphics.glslc_version) { $payload.graphics.glslc_version } else { "not found" })) -ForegroundColor White
    Write-Host "  dxc      " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($payload.graphics.dxc_version) { $payload.graphics.dxc_version } else { "not found" })) -ForegroundColor White
    Write-Host "  nvcc     " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($payload.compute.nvcc_version) { $payload.compute.nvcc_version } else { "not found" })) -ForegroundColor White
    Write-Host "  msvc     " -NoNewline -ForegroundColor Cyan
    Write-Host ($(if ($payload.msvc.cl_path) { $payload.msvc.cl_path } else { "not found" })) -ForegroundColor DarkGray
    Write-Host "  linker   " -NoNewline -ForegroundColor Cyan
    switch ($payload.msvc.linker_effective) {
        "clear"      { Write-Host ($(if ($payload.msvc.link_path) { $payload.msvc.link_path } else { "not found" })) -ForegroundColor DarkGray }
        "mitigated"  { Write-Host "shadow → mitigated" -NoNewline -ForegroundColor Yellow; Write-Host " ($($payload.msvc.cargo_config_linker))" -ForegroundColor DarkGray }
        "vulnerable" { Write-Host "SHADOWED → VULNERABLE" -NoNewline -ForegroundColor Red; Write-Host (" — {0}" -f $payload.msvc.link_path) -ForegroundColor DarkGray }
    }
    Write-Host "  openssl  " -NoNewline -ForegroundColor Cyan
    if ($payload.openssl.version) {
        $badge = "v$($payload.openssl.version)"
        switch ($payload.openssl.effective) {
            "compatible"              { Write-Host $badge -ForegroundColor Green }
            "fully mitigated"         { Write-Host "$badge → mitigated" -ForegroundColor Green }
            "patched (env drift risk)" { Write-Host "$badge → patched" -NoNewline -ForegroundColor Green; Write-Host " (env drift)" -ForegroundColor Yellow }
            "env set (no cargo patch)" { Write-Host "$badge → env only" -NoNewline -ForegroundColor Yellow; Write-Host " (no patch)" -ForegroundColor Red }
            "vulnerable"              { Write-Host "$badge → VULNERABLE" -ForegroundColor Red }
        }
    } else {
        Write-Host "not found" -ForegroundColor DarkGray
    }
    Write-Host "  shaders  " -NoNewline -ForegroundColor Cyan
    Write-Host $payload.shaders.source_count -ForegroundColor White
    foreach ($shader in $payload.shaders.sources) {
        Write-Host "    - $($shader.path)" -ForegroundColor DarkGray
    }
    Write-Host "  hlsl     " -NoNewline -ForegroundColor Cyan
    Write-Host $payload.shaders.hlsl_source_count -ForegroundColor White
    foreach ($shader in $payload.shaders.hlsl_sources) {
        Write-Host "    - $($shader.path)" -ForegroundColor DarkGray
    }
    Write-Host "  caches   " -NoNewline -ForegroundColor Cyan
    Write-Host $payload.caches.Count -ForegroundColor White
    foreach ($cache in $payload.caches) {
        Write-Host ("    - {0}: {1}" -f $cache.name, $(if ($cache.exists) { $cache.size_bytes } else { "missing" })) -ForegroundColor DarkGray
    }
    Write-Host "  cmake    " -NoNewline -ForegroundColor Cyan
    Write-Host ("Lists={0} Presets={1} CudaProbe={2} TensorHost={3}" -f $payload.repo.cmake_lists_exists, $payload.repo.cmake_presets_exists, $payload.repo.cuda_probe_exists, $payload.repo.tensor_runtime_host_exists) -ForegroundColor White
    Write-Host ""
}

function Invoke-RubySearch {
    param([string[]]$RubyArgs, [switch]$Json)

    $queryParts = @()
    $limit = 10
    for ($i = 0; $i -lt $RubyArgs.Count; $i++) {
        switch ($RubyArgs[$i]) {
            "--limit" {
                if ($i + 1 -lt $RubyArgs.Count) {
                    $limit = [int]$RubyArgs[$i + 1]
                    $i++
                }
            }
            default {
                if (-not $RubyArgs[$i].StartsWith("--")) { $queryParts += $RubyArgs[$i] }
            }
        }
    }

    $query = ($queryParts -join " ").Trim()
    if (-not $query) {
        Write-Host "Usage: chthonic ruby search <query> [--limit N]" -ForegroundColor Yellow
        return 1
    }

    $uri = "https://rubygems.org/api/v1/search.json?query=$([uri]::EscapeDataString($query))"
    $results = @((Invoke-RestMethod -Uri $uri -TimeoutSec 10 -ErrorAction Stop)) | Select-Object -First $limit

    if ($Json) {
        Write-Output (ConvertTo-Json $results -Depth 5)
        return 0
    }

    Write-Host ""
    Write-Host "RUBYGEMS SEARCH: $query" -ForegroundColor Cyan
    Write-Host ("="*72) -ForegroundColor DarkGray
    foreach ($item in $results) {
        $name = "$($item.name)@$($item.version)"
        $downloads = if ($item.downloads) { $item.downloads } else { 0 }
        Write-Host "  $name" -NoNewline -ForegroundColor White
        Write-Host "  downloads=$downloads" -ForegroundColor DarkGray
        if ($item.info) {
            Write-Host "    $($item.info)" -ForegroundColor Gray
        }
    }
    Write-Host ""
    return 0
}

function Invoke-RubyInstall {
    param([string[]]$RubyArgs)

    $gem = $null
    $server = "https://rubygems.org"
    $force = $false

    for ($i = 0; $i -lt $RubyArgs.Count; $i++) {
        switch ($RubyArgs[$i]) {
            "--server" {
                if ($i + 1 -lt $RubyArgs.Count) {
                    $server = $RubyArgs[$i + 1]
                    $i++
                }
            }
            "--rubygems" { $server = "https://rubygems.org" }
            "--coop"     { $server = "https://gem.coop/" }
            "--force"    { $force = $true }
            default {
                if (-not $RubyArgs[$i].StartsWith("--") -and -not $gem) {
                    $gem = $RubyArgs[$i]
                }
            }
        }
    }

    if (-not $gem) {
        Write-Host "Usage: chthonic ruby install <gem[@version]> [--rubygems|--coop|--server URL] [--force]" -ForegroundColor Yellow
        return 1
    }

    $invokeArgs = @("tool", "install", $gem, "--gem-server", $server)
    if ($force) { $invokeArgs += "--force" }
    & rv @invokeArgs
    return $LASTEXITCODE
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN DISPATCH - Meta CLI (Domain/Action Model)
# ═══════════════════════════════════════════════════════════════════════════════

# Normalize unbound raw tokens so forms like `chthonic --help` and
# accidental dashed inputs like `chthonic -uv` can be handled explicitly.
if ($args -and $args.Count -gt 0) {
    if (-not $Command) {
        $Command = $args[0]
        if ($args.Count -gt 1) {
            $CmdArgs = @($CmdArgs + $args[1..($args.Count - 1)])
        }
    } else {
        $CmdArgs = @($CmdArgs + $args)
    }
}

# Parse domain/action if provided
$Domain = $Command
$Action = if ($CmdArgs.Count -gt 0) { $CmdArgs[0] } else { $null }
$RemainingArgs = if ($CmdArgs.Count -gt 1) { $CmdArgs[1..($CmdArgs.Count-1)] } else { @() }
$AllArgs = @()
if ($Action) { $AllArgs += $Action }
if ($RemainingArgs) { $AllArgs += $RemainingArgs }
$HasJsonFlag = $Json -or ($AllArgs -contains "--json")
$HasQuietFlag = $Quiet -or ($AllArgs -contains "--quiet") -or ($AllArgs -contains "-q")

# Top-level commands (backward compatible)
switch ($Domain) {
    "--version" {
        Write-Host "chthonic v$VERSION"
        exit 0
    }
    { $_ -in "--help", "-h", "help" } {
        Show-Help
        exit 0
    }
    { $_ -in $null, "" } {
        Show-StatusBanner
        Show-Help
        exit 0
    }
    
    # Environment Domain
    "env" {
        $quietFlag = $HasQuietFlag
        Invoke-PolyglotActivation -Quiet:$quietFlag
        Complete-ChthonicCommand 0
        return
    }
    "claudine" {
        # Compatibility alias for existing shell/profile wrappers.
        $quietFlag = $HasQuietFlag
        Invoke-PolyglotActivation -Quiet:$quietFlag
        Complete-ChthonicCommand 0
        return
    }
    "status" {
        Show-PolyglotStatus -Json:$HasJsonFlag
        exit 0
    }
    "trend" {
        $exitCode = Invoke-RustificationTrend -Args $CmdArgs
        exit $exitCode
    }
    "oversight" {
        $exitCode = Invoke-OversightUpcycle -Args $CmdArgs
        exit $exitCode
    }
    "doctor" {
        $fixFlag = ($AllArgs -contains "--fix") -or ($AllArgs -contains "-f")
        $dryRunFlag = $AllArgs -contains "--dry-run"
        $jsonFlag = $HasJsonFlag
        $originsFlag = $AllArgs -contains "--origins"
        Invoke-Doctor -Json:$jsonFlag -Fix:$fixFlag -DryRun:$dryRunFlag -Origins:$originsFlag
        exit 0
    }
    "detect" {
        if ($HasJsonFlag) {
            Invoke-IDEDetect -Json:$true
            exit 0
        }
        $exitCode = Invoke-IDEDetect -Json:$false
        exit $exitCode
    }
    "toolchain" {
        $exitCode = Invoke-ToolchainMeta -ToolchainAction $Action -ToolchainArgs $RemainingArgs -Json:$HasJsonFlag
        exit $exitCode
    }
    "memory" {
        $exitCode = Invoke-MemoryLane -MemoryAction $Action -MemoryArgs $RemainingArgs -Json:$HasJsonFlag
        exit $exitCode
    }
    "commands" {
        $exitCode = Invoke-CommandSurface -CommandAction $Action -CommandArgs $RemainingArgs -Json:$HasJsonFlag
        if ($HasJsonFlag -and $script:CommandSurfaceJsonPayload) {
            Write-Output $script:CommandSurfaceJsonPayload
            $script:CommandSurfaceJsonPayload = $null
        }
        exit $exitCode
    }
    "ruby" {
        switch ($Action) {
            { $_ -in $null, "", "lane", "status" } {
                Invoke-RubyLane -Json:$HasJsonFlag
                exit 0
            }
            { $_ -in "versions", "rubies", "list" } {
                Invoke-RubyVersions -Json:$HasJsonFlag
                exit 0
            }
            { $_ -in "tools", "tool-list", "installed" } {
                Invoke-RubyTools -Json:$HasJsonFlag
                exit 0
            }
            "doctor" {
                $fixFlag = ($AllArgs -contains "--fix") -or ($AllArgs -contains "-f")
                $exitCode = Invoke-RubyDoctor -Json:$HasJsonFlag -Fix:$fixFlag
                exit $exitCode
            }
            { $_ -in "upgrade", "install-latest", "latest" } {
                $exitCode = Invoke-RubyUpgrade -Json:$HasJsonFlag
                exit $exitCode
            }
            "search" {
                $exitCode = Invoke-RubySearch -RubyArgs $RemainingArgs -Json:$HasJsonFlag
                exit $exitCode
            }
            "install" {
                $exitCode = Invoke-RubyInstall -RubyArgs $RemainingArgs
                exit $exitCode
            }
            default {
                Write-Host 'chthonic ruby <action>'
                Write-Host "  versions            - list installed/available Rubies"
                Write-Host "  tools               - list rv-installed Ruby CLI tools"
                Write-Host "  lane                - Ruby lane summary (rv + ruby + gcc + make + pacman)"
                Write-Host "  doctor [--fix]      - detect/repair stale rv Ruby state"
                Write-Host "  upgrade             - install latest stable Ruby if newer; no-op if already current"
                Write-Host "  search <query>      - search RubyGems.org"
                Write-Host "  install <gem>       - install via rv tool install (defaults to RubyGems.org)"
                Write-Host "    flags: --rubygems | --coop | --server <url> | --force"
                exit 0
            }
        }
    }
    "python" {
        switch ($Action) {
            { $_ -in $null, "", "lane", "status" } {
                Invoke-PythonLane -Json:$HasJsonFlag
                exit 0
            }
            default {
                Show-DomainCatalogHelp -Domain "python"
                exit 0
            }
        }
    }
    "bun" {
        switch ($Action) {
            { $_ -in $null, "", "lane", "status" } {
                Invoke-BunLane -Json:$HasJsonFlag
                exit 0
            }
            default {
                Show-DomainCatalogHelp -Domain "bun"
                exit 0
            }
        }
    }
    "rust" {
        switch ($Action) {
            { $_ -in $null, "", "lane", "status" } {
                Invoke-RustLane -Json:$HasJsonFlag
                exit 0
            }
            default {
                Show-DomainCatalogHelp -Domain "rust"
                exit 0
            }
        }
    }
    "go" {
        switch ($Action) {
            { $_ -in $null, "", "lane", "status" } {
                Invoke-GoLane -Json:$HasJsonFlag
                exit 0
            }
            default {
                Show-DomainCatalogHelp -Domain "go"
                exit 0
            }
        }
    }
    "r" {
        switch ($Action) {
            { $_ -in $null, "", "lane", "status" } {
                Invoke-RLane -Json:$HasJsonFlag
                exit 0
            }
            default {
                Show-DomainCatalogHelp -Domain "r"
                exit 0
            }
        }
    }
    "zig" {
        switch ($Action) {
            { $_ -in $null, "", "lane", "status" } {
                Invoke-ZigLane -Json:$HasJsonFlag
                exit 0
            }
            default {
                Show-DomainCatalogHelp -Domain "zig"
                exit 0
            }
        }
    }
    "graphics" {
        switch ($Action) {
            { $_ -in $null, "", "lane", "status" } {
                Invoke-GraphicsLane -Json:$HasJsonFlag
                exit 0
            }
            default {
                Show-DomainCatalogHelp -Domain "graphics"
                exit 0
            }
        }
    }
    "poe" {
        $poeAccountScript = Join-Path $SCRIPT_DIR "poe_account.ps1"
        $poeLaneScript = Join-Path $SCRIPT_DIR "poe_lane.py"
        $poeSdkScript = Join-Path $SCRIPT_DIR "poe_sdk_lane.py"
        $poeAuditScript = Join-Path $SCRIPT_DIR "poe_transport_audit.py"

        switch ($Action) {
            "account" {
                if (-not (Test-Path -LiteralPath $poeAccountScript)) {
                    Write-Error "Missing script: $poeAccountScript"
                    exit 1
                }
                & pwsh -NoProfile -File $poeAccountScript @RemainingArgs
                exit $LASTEXITCODE
            }
            "models" {
                if (-not (Test-Path -LiteralPath $poeLaneScript)) {
                    Write-Error "Missing script: $poeLaneScript"
                    exit 1
                }
                & uv run $poeLaneScript --mode models @RemainingArgs
                exit $LASTEXITCODE
            }
            "probe" {
                if (-not (Test-Path -LiteralPath $poeLaneScript)) {
                    Write-Error "Missing script: $poeLaneScript"
                    exit 1
                }
                & uv run $poeLaneScript --mode probe --emit-mailbox @RemainingArgs
                exit $LASTEXITCODE
            }
            "chat" {
                if (-not (Test-Path -LiteralPath $poeLaneScript)) {
                    Write-Error "Missing script: $poeLaneScript"
                    exit 1
                }
                & uv run $poeLaneScript --mode chat @RemainingArgs
                exit $LASTEXITCODE
            }
            "sdk-probe" {
                if (-not (Test-Path -LiteralPath $poeSdkScript)) {
                    Write-Error "Missing script: $poeSdkScript"
                    exit 1
                }
                & uv run --with fastapi-poe $poeSdkScript --emit-mailbox @RemainingArgs
                exit $LASTEXITCODE
            }
            "audit" {
                if (-not (Test-Path -LiteralPath $poeAuditScript)) {
                    Write-Error "Missing script: $poeAuditScript"
                    exit 1
                }
                & uv run $poeAuditScript --emit-mailbox @RemainingArgs
                exit $LASTEXITCODE
            }
            default {
                Write-Host "chthonic poe <action>"
                Write-Host "  account -Account 1|2 [-MapOpenAICompat] [-Doctor] [-Model <model>] (shell-local)"
                Write-Host "  models [--account 1|2] [--limit 40]"
                Write-Host "  probe [--account 1|2] [--model <model>] [--prompt <text>] [--effort max] [--emit-mailbox] [--mailboxes codex|claude|codex,claude]"
                Write-Host "  chat [--account 1|2] --model <model> --prompt <text> [--effort max]"
                Write-Host "  sdk-probe [--account 1|2] [--bot <bot>] [--prompt <text>] [--effort max] [--mailboxes codex|claude|codex,claude]"
                Write-Host "  audit [--accounts 1,2] [--control-model claude-sonnet-4.5] [--target-bot app-creator] [--mailboxes codex,claude]"
                exit 0
            }
        }
    }
    
    # IDE Domain (nested commands)
    "ide" {
        switch ($Action) {
            "launch" {
                $path = if ($RemainingArgs.Count -gt 0) { $RemainingArgs[0] } else { $REPO_ROOT }
                $exitCode = Invoke-IDELaunch -WorkspacePath $path
                exit $exitCode
            }
            "detect" {
                if ($HasJsonFlag) {
                    Invoke-IDEDetect -Json:$true
                    exit 0
                }
                $exitCode = Invoke-IDEDetect -Json:$false
                exit $exitCode
            }
            "reset" {
                Write-Host "🔄 Resetting IDE configuration..." -ForegroundColor Yellow
                Remove-Item "$env:APPDATA\Code - Insiders\User\globalStorage\*claude*" -Recurse -Force -ErrorAction SilentlyContinue
                Write-Host "✅ IDE configuration reset. Reinstall Claude Code extension." -ForegroundColor Green
                exit 0
            }
            default {
                Show-DomainCatalogHelp -Domain "ide"
                exit 0
            }
        }
    }
    
    # Service/MCP Domain (nested commands)
    "mcp" {
        switch ($Action) {
            "start" {
                $exitCode = Invoke-MCPStart
                exit $exitCode
            }
            "stop" {
                $exitCode = Invoke-MCPStop
                exit $exitCode
            }
            "status" {
                if ($HasJsonFlag) {
                    Invoke-MCPStatus -Json:$true
                    exit 0
                }
                $exitCode = Invoke-MCPStatus -Json:$false
                exit $exitCode
            }
            "logs" {
                Write-Host "📋 Service logs..." -ForegroundColor Gray
                Get-Job | Where-Object { $_.Name -like "*bridge*" } | ForEach-Object {
                    Write-Host "Job: $($_.Name)" -ForegroundColor Cyan
                    Receive-Job -Job $_
                }
                exit 0
            }
            default {
                Show-DomainCatalogHelp -Domain "mcp"
                exit 0
            }
        }
    }
    
    # Config Domain
    "config" {
        if (-not (Test-Path $STATE_DIR)) {
            New-Item -ItemType Directory -Path $STATE_DIR -Force | Out-Null
        }
        
        switch ($Action) {
            "init" {
                Write-Host "⚙️  Initializing chthonic configuration..." -ForegroundColor Cyan
                $config = @{
                    Version = $VERSION
                    RepoRoot = $REPO_ROOT
                    Created = (Get-Date).ToString()
                    Features = @("polyglot", "mcp", "ide", "archive")
                }
                $config | ConvertTo-Json | Set-Content $CONFIG_FILE
                Write-Host "✅ Config created: $CONFIG_FILE" -ForegroundColor Green
                exit 0
            }
            "show" {
                if (Test-Path $CONFIG_FILE) {
                    Get-Content $CONFIG_FILE | ConvertFrom-Json | Format-Table -AutoSize
                } else {
                    Write-Host "No configuration file. Run: chthonic config init" -ForegroundColor Yellow
                }
                exit 0
            }
            "set" {
                # chthonic config set <key> <value>
                if ($RemainingArgs.Count -lt 2) {
                    Write-Host 'Usage: chthonic config set <key> <value>' -ForegroundColor Yellow
                    exit 1
                }
                Write-Host "⚙️  Set config: $($RemainingArgs[0]) = $($RemainingArgs[1])" -ForegroundColor Cyan
                exit 0
            }
            default {
                Show-DomainCatalogHelp -Domain "config"
                exit 0
            }
        }
    }

    "new" {
        if (-not $Action) {
            Write-Host 'chthonic new <profile> <path>'
            Write-Host "  uv-python-app        - uv init --app --package"
            Write-Host "  uv-python-lib        - uv init --lib --package"
            Write-Host "  bun-react            - bun init --react"
            Write-Host "  bun-react-tailwind   - bun init --react=tailwind"
            Write-Host "  bun-next             - bun create next-app"
            Write-Host "  cargo-rust-bin       - cargo new --bin"
            Write-Host "  cargo-rust-lib       - cargo new --lib"
            Write-Host "  go-basic             - go mod init + main.go"
            Write-Host "  ruby-gem             - bundle gem"
            Write-Host "  azure-azd-template   - azd init --template (requires azd)"
            Write-Host "  add --dry-run, --verify, and/or --json as needed"
            exit 0
        }
        $result = Invoke-ChthonicNew -Profile $Action -CreateArgs $RemainingArgs -Json:$HasJsonFlag
        if ($result.Output) {
            $result.Output | ForEach-Object { Write-Output $_ }
        }
        exit $result.ExitCode
    }

    "workflow" {
        if (-not $Action) {
            Write-Host 'chthonic workflow <profile>'
            Write-Host "  control-plane         - validate status, shell probe, ssot queue/drift/lineage, MCP tool exposure"
            Write-Host "  toolchain-governance  - validate doctor/origins/toolchain probe surfaces"
            Write-Host "  add --write to persist report artifacts; --dry-run to preview steps; --list to enumerate profiles"
            exit 0
        }
        $result = Invoke-ChthonicWorkflow -Profile $Action -WorkflowArgs $RemainingArgs -Json:$HasJsonFlag
        if ($result.Output) {
            $result.Output | ForEach-Object { Write-Output $_ }
        }
        exit $result.ExitCode
    }

    "shell" {
        switch ($Action) {
            "probe" {
                Invoke-ShellProbe -Json:$HasJsonFlag
                exit 0
            }
            "brush" {
                $brushExe = Get-CommandPathFlexible -Name "brush"
                if (-not $brushExe) {
                    Write-Error "brush not found on PATH"
                    exit 1
                }
                $brushRc = Get-BrushRepoRcPath
                if ($RemainingArgs.Count -ge 2 -and $RemainingArgs[0] -eq "--cmd") {
                    if ($brushRc) {
                        & $brushExe -i --rcfile $brushRc -c $RemainingArgs[1]
                    } else {
                        & $brushExe -c $RemainingArgs[1]
                    }
                } elseif ($RemainingArgs.Count -eq 0 -and $brushRc) {
                    & $brushExe -i --rcfile $brushRc
                } else {
                    & $brushExe @RemainingArgs
                }
                exit $LASTEXITCODE
            }
            "pwsh" {
                $pwshExe = Get-CommandPathFlexible -Name "pwsh"
                if (-not $pwshExe) {
                    Write-Error "pwsh not found on PATH"
                    exit 1
                }
                if ($RemainingArgs.Count -ge 2 -and $RemainingArgs[0] -eq "--cmd") {
                    & $pwshExe -NoLogo -Command $RemainingArgs[1]
                } else {
                    & $pwshExe @RemainingArgs
                }
                exit $LASTEXITCODE
            }
            "bash" {
                $bashExe = Get-CommandPathFlexible -Name "bash"
                if (-not $bashExe) {
                    Write-Error "bash not found on PATH"
                    exit 1
                }
                if ($RemainingArgs.Count -ge 2 -and $RemainingArgs[0] -eq "--cmd") {
                    & $bashExe -lc $RemainingArgs[1]
                } else {
                    & $bashExe @RemainingArgs
                }
                exit $LASTEXITCODE
            }
            default {
                Show-DomainCatalogHelp -Domain "shell"
                exit 0
            }
        }
    }

    "ssot" {
        if (-not $Action) {
            Show-DomainCatalogHelp -Domain "ssot"
            exit 0
        }
        $result = Invoke-SsotLoremaster -Action $Action -ActionArgs $RemainingArgs -Json:$HasJsonFlag
        if ($result.Output) {
            $result.Output | ForEach-Object { Write-Output $_ }
        }
        exit $result.ExitCode
    }
    
    # Book Domain
    "book" {
        Push-Location $REPO_ROOT
        try {
            $subCmd = if ($Action) { $Action } else { "build" }
            switch ($subCmd) {
                "build" { & mdbook build }
                "serve" { & mdbook serve --open }
                "clean" { & mdbook clean }
                default { & mdbook $subCmd $RemainingArgs }
            }
            exit $LASTEXITCODE
        }
        finally {
            Pop-Location
        }
    }
    
    # Backward compatibility: single-word archive commands
    "audit" {
        if ($Action -eq "envelope") {
            $envelopeScript = Join-Path $REPO_ROOT "scripts" "envelope_census.py"
            if (-not (Test-Path -LiteralPath $envelopeScript)) {
                Write-Error "Missing script: $envelopeScript"
                exit 1
            }
            & uv run $envelopeScript @RemainingArgs
            exit $LASTEXITCODE
        }
        $exitCode = Invoke-ArchiveCommand -Cmd $Domain -CmdArgs @($Action) + $RemainingArgs
        exit $exitCode
    }
    { $_ -in "compact", "extract", "resolve", "map", "analyze" } {
        $exitCode = Invoke-ArchiveCommand -Cmd $Domain -CmdArgs @($Action) + $RemainingArgs
        exit $exitCode
    }
    
    # Gemini CLI — bun-managed repo-local lane with version policy
    "gemini" {
        switch ($Action) {
            { $_ -in "update", "upgrade" } {
                Invoke-GeminiUpdate
                exit 0
            }
            default {
                # MCP disabled prophylactically; all 6 server scripts confirmed present.
                # Remove GEMINI_DISABLE_MCP once interactive MCP session validates all servers.
                $env:GEMINI_DISABLE_MCP = "1"
                & pwsh (Join-Path $SCRIPT_DIR "gemini-cli-wrapper.ps1") @CmdArgs
                exit $LASTEXITCODE
            }
        }
    }
    
    # Claude-IDE backward compatibility (legacy)
    "claude-ide" {
        $exitCode = Invoke-IDELaunch -WorkspacePath $REPO_ROOT
        exit $exitCode
    }
    
    # Unknown command
    default {
        if ($Domain -and -not ($Domain -match '^-')) {
            # Try as archive command
            $exitCode = Invoke-ArchiveCommand -Cmd $Domain -CmdArgs @($Action) + $RemainingArgs
            exit $exitCode
        }
        else {
            if ($Domain) {
                Write-Host "Unknown option: $Domain" -ForegroundColor Red
                Write-Host "Use --help for usage, or run `chthonic status` / `claudine status` for structured output." -ForegroundColor Yellow
                Write-Host ""
            }
            Show-Help
            exit 1
        }
    }
}





