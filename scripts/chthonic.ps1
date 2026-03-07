#!/usr/bin/env pwsh

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: chthonic.ps1
# ║ Module: Unified polyglot CLI router
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: INFRASTRUCTURE
# ║ Semantic ID: SCRIPT_CHTHONIC_V1
# ║ Purpose: Unified META-CLI for polyglot tooling and repo operations
# ║ Exports: (none)
# ║ Flags/Modes: -Command, -CmdArgs, -Quiet, -Json
# ║ Cross-References: (none)
# ╚════════════════════════════════════════════════════════════════════════════

param(
    [Parameter(Position = 0)]
    [string]$Command,
    
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CmdArgs,
    
    [switch]$Quiet,
    [switch]$Json
)

$VERSION = "3.3.0"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$REPO_ROOT = Split-Path -Parent $SCRIPT_DIR
$LIB_DIR = Join-Path $SCRIPT_DIR "lib"
$STATE_DIR = Join-Path $env:USERPROFILE ".chthonic"
$CONFIG_FILE = Join-Path $STATE_DIR "config.json"
$SERVICES_FILE = Join-Path $STATE_DIR "services.json"

# ═══════════════════════════════════════════════════════════════════════════════
# POLYGLOT PATHS - ALL GLOBAL NATIVE INSTALLATIONS (Win11)
# ═══════════════════════════════════════════════════════════════════════════════

# Resolve rv-managed Ruby bin directory (highest installed version).
function Get-RvRubyBinDir {
    $rvRubies = Join-Path $env:APPDATA "rv\rubies"
    if (-not (Test-Path $rvRubies)) { return $null }

    $latest = Get-ChildItem $rvRubies -Directory |
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
    $devkitRoots = @(
        "C:\Ruby40-x64",
        "D:\Ruby40-x64",
        "C:\Ruby35-x64",
        "D:\Ruby35-x64"
    )

    foreach ($root in $devkitRoots) {
        if (Test-Path (Join-Path $root "msys64\ucrt64\bin\gcc.exe")) {
            return $root
        }
    }

    return $null
}

function Get-DevKitPaths {
    $root = Get-RubyDevKitRoot
    if (-not $root) { return @() }

    return @(
        (Join-Path $root "msys64\ucrt64\bin"),
        (Join-Path $root "msys64\usr\bin")
    )
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

    $rvExeCmd = Get-CommandResolution -Name "rv.exe"
    $rvwCmd = Get-CommandResolution -Name "rvw"
    $targetCommand = $null
    if ($rvExeCmd) {
        $targetCommand = "rv.exe"
    } elseif ($rvwCmd) {
        $targetCommand = "rvw"
    }
    if (-not $targetCommand) {
        $result.reason = "rv.exe/rvw not found"
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

# rv-managed Ruby (exclusive ownership per ANNO manifest)
if ($rvRubyBin) {
    $defaultPolyglotPaths += $rvRubyBin
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

function Show-StatusBanner {
    # Compact one-liner version probes grouped by manager
    $W = "White"; $C = "Cyan"; $D = "DarkGray"; $R = "Red"
    function ver($cmd) { try { $v = (& $cmd 2>$null); if ($v) { return ($v -split "`n")[0] } } catch {}; return $null }

    Write-Host "CHTHONIC v$VERSION" -ForegroundColor $C -NoNewline
    Write-Host " | " -ForegroundColor $D -NoNewline
    Write-Host "$REPO_ROOT" -ForegroundColor $W
    Write-Host ("="*72) -ForegroundColor $D

    # rv -> Ruby
    $rubyVer = ver { ruby -e "print RUBY_VERSION" }
    $rvwVer = ver { rvw --version }; if ($rvwVer -match '(\d+\.\d+\.\d+)') { $rvwVer = $matches[1] } else { $rvwVer = $null }
    $rvMeta = Get-CommandResolution -Name "rv"
    $rvVer = $null
    if ($rvMeta -and $rvMeta.Type -ne "Alias") {
        $rvProbe = ver { rv --version }
        if ($rvProbe -match '(\d+\.\d+\.\d+)') { $rvVer = $matches[1] }
    }
    if (-not $rvVer -and $rvwVer) { $rvVer = $rvwVer }
    Write-Host "  rv    " -NoNewline -ForegroundColor $C
    if ($rubyVer) { Write-Host "ruby $rubyVer" -NoNewline -ForegroundColor $W } else { Write-Host "ruby ?" -NoNewline -ForegroundColor $R }
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
    $goupVer = ver { goup --version }; if ($goupVer -match '(\d+\.\d+\.\d+)') { $goupVer = $matches[1] } else { $goupVer = $null }
    Write-Host "  go    " -NoNewline -ForegroundColor $C
    if ($goVer) { Write-Host "go $goVer" -NoNewline -ForegroundColor $W } else { Write-Host "go ?" -NoNewline -ForegroundColor $R }
    if ($goupVer) { Write-Host "  goup $goupVer" -NoNewline -ForegroundColor $D }
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

function Show-Help {
@"

Usage: chthonic [--version] [--help] <domain> [<action>] [<args>]

  env [--quiet]           Activate polyglot environment
  claudine [--quiet]      Alias to env (shell compatibility lane)
  status [--json]         Show tool + manager versions (verbose)
  trend [--json]          Rustification trend tracker (GitHub + endoflife cross-ref)
  oversight [--json]      Hierarchical upcycle oversight stack (single LATEST output)
  doctor [--fix] [--json] Check versions + EOL via endoflife.date; --fix upgrades
  doctor --dry-run        Simulate --fix without executing anything
  doctor --origins        Show install methodology per tool (path + origin + wrappers)
  detect                  Detect IDE and environment context

  ide launch|detect|reset IDE management
  mcp start|stop|status   MCP + bridge services
  poe account|models|probe|chat|sdk-probe|audit  Poe account routing + Poe lanes
  config init|show|set    Configuration (~/.chthonic/)
  shell brush|pwsh|bash|probe  Experimental shell lane + shell capability probe
  ssot queue|entity|section|drift|lineage  SSOT loremaster control plane

  audit|compact|extract|resolve|map|analyze  Archive tools (uv run)
  book [serve|build]      mdBook documentation

  --version               Show version
  --help                  Show this help (without status banner)
  --quiet                 Suppress output

"@
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
    
    # Canon markers for the active Chthonic environment.
    # Keep the older Claudine markers mirrored for compatibility during transition.
    $env:CHTHONIC_ACTIVATED = "1"
    $env:CHTHONIC_VERSION = $VERSION
    $env:CLAUDINE_ACTIVATED = "1"
    $env:CLAUDINE_VERSION = $VERSION
    $env:CHTHONIC_REPO_ROOT = $REPO_ROOT
    
    if (-not $Quiet) {
        if ($rvBinding -and $rvBinding.applied) {
            Write-Host "  rv alias remapped: $($rvBinding.rv_before) -> $($rvBinding.rv_after)" -ForegroundColor DarkGray
            if ($rvBinding.rvar_after) {
                Write-Host "  Remove-Variable preserved via: $($rvBinding.rvar_after)" -ForegroundColor DarkGray
            }
        }
        Show-PolyglotStatus
    }
}

function Show-PolyglotStatus {
    param([switch]$Json)
    
    # Collect tool versions
    $tools = @{}
    $tools['orchestrator_ssot'] = 'chthonic'
    $tools['orchestration_mode'] = 'polyglot_router'
    $tools['research_ingest_role'] = 'supplemental_input'
    $tools['unified_overlay_optional'] = 'mise'
    $tools['handler_ruby'] = 'rv (rvw wrapper optional)'
    $tools['handler_python'] = 'uv'
    $tools['handler_rust'] = 'rustup/cargo'
    $tools['handler_go'] = 'goup'
    $tools['handler_js'] = 'bun'
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
    try { $tools['python'] = (uv run python --version 2>&1) -replace 'Python\s*','' } catch { $tools['python'] = 'not found' }
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
        $claudeOut = (& claude --version 2>$null)
        if (($claudeOut -join "`n") -match '(\d+\.\d+\.\d+)') {
            $tools['claude'] = $matches[1]
        } elseif ($claudeOut) {
            $tools['claude'] = ($claudeOut | Select-Object -First 1).ToString().Trim()
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

    $claudeMeta = Get-CommandResolution -Name "claude"
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
            if ((Get-CommandResolution -Name "rv.exe") -or (Get-CommandResolution -Name "rvw")) {
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
            "mdbook", "git", "gcc", "make", "claude", "brush"
        )

        Write-StatusSection -Title "Commands" -Tools $tools -Keys @(
            "chthonic_cmd", "chthonic_binding",
            "claudine_cmd", "claudine_binding",
            "claude_cmd", "brush_cmd", "rv_cmd", "rv_binding", "rv_binding_reason",
            "rvar_cmd", "mise", "mise_cmd"
        )

        Write-StatusSection -Title "Platform" -Tools $tools -Keys @(
            "code-insiders", "az", "bicep", "sqlcmd", "sqlpackage", "ssms",
            "msvc_cl", "msbuild", "clang", "vs_ide", "vs_professional",
            "vs_community", "vs_enterprise", "vs_buildtools", "vulkan"
        )

        Write-StatusSection -Title "Routing Metadata" -Tools $tools -Keys @(
            "orchestrator_ssot", "orchestration_mode", "manager_model",
            "unified_overlay_optional", "handler_ruby", "handler_python",
            "handler_rust", "handler_go", "handler_js", "handler_shell", "uv_tool_lane",
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
            "ruby"       { $v = ruby -e "print RUBY_VERSION" 2>$null; return $v }
            "python"     {
                $v = try { uv run python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>$null } catch { $null }
                if ($v) { return $v }
                $py = try { python --version 2>$null } catch { $null }
                if ($py -match 'Python\s+(\d+\.\d+\.\d+)') { return $matches[1] }
                return $null
            }
            "bun"        { return (bun --version 2>$null) }
            "brush"      {
                $v = brush --version 2>$null
                if ($v -match '^brush\s+(\d+\.\d+\.\d+)') { return $matches[1] }
                return $v
            }
            "rust"       { $v = rustc -V 2>$null; if ($v -match '(\d+\.\d+\.\d+)') { return $matches[1] }; return $null }
            "go"         {
                # Try PATH first, then goup-managed Go
                $v = try { go version 2>$null } catch { $null }
                if (-not $v) {
                    $goupGo = Join-Path $env:USERPROFILE ".goup\current\bin\go.exe"
                    if (Test-Path $goupGo) { $v = & $goupGo version 2>$null }
                }
                if ($v -match 'go(\d+\.\d+\.\d+)') { return $matches[1] }; return $null
            }
            "nodejs"     { $v = node --version 2>$null; if ($v -match '(\d+\.\d+\.\d+)') { return $matches[1] }; return $null }
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
#   Ruby/Python: explicit pin (rvw ruby pin / uv python pin)
#   Go/Rust/Bun: implicit pin (goup install auto-defaults, rustup stays stable, bun is single binary)
$global:DoctorFixMap = @{
    ruby   = @{
        Upgrade = { param($ver) rvw ruby install $ver; rvw ruby pin $ver }; UpgradeDesc = "rvw ruby install && pin"
        Install = { param($ver) cargo install rv; rvw ruby install $ver; rvw ruby pin $ver }; InstallDesc = "cargo install rv && rvw ruby install && pin"
    }
    python = @{
        Upgrade = {
            param($ver)
            uv python install $ver
            uv python pin $ver
        }; UpgradeDesc = "uv python install && uv python pin"
        Install = {
            param($ver)
            if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
                irm https://astral.sh/uv/install.ps1 | iex
            }
            uv python install $ver
            uv python pin $ver
        }; InstallDesc = "install uv (if missing) && uv python install && uv python pin"
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
        Upgrade = { rustup update stable }; UpgradeDesc = "rustup update stable"
        Install = { irm https://sh.rustup.rs -useb | iex }; InstallDesc = "irm rustup.rs | iex"
    }
    go     = @{
        Upgrade = { param($ver) goup install "=$ver" }; UpgradeDesc = "goup install"
        Install = { goup install stable }; InstallDesc = "goup install stable"
    }
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
        @{ Name = "ruby";    Cmd = "ruby";    Method = "rvw (cargo install rv)";    Ecosystem = "cargo" },
        @{ Name = "python";  Cmd = "uv";      Method = "irm astral.sh/uv";          Ecosystem = "uv" },
        @{ Name = "bun";     Cmd = "bun";     Method = "irm bun.sh";                Ecosystem = "bun" },
        @{ Name = "rust";    Cmd = "rustc";   Method = "rustup (irm rustup.rs)";     Ecosystem = "cargo" },
        @{ Name = "go";      Cmd = "go";      Method = "goup (cargo install goup-rs)"; Ecosystem = "cargo" }
    )

    # Secondary tools
    $secondary = @(
        @{ Name = "rv";      Cmd = $null;     Method = "PowerShell binding (alias collision guard)"; Ecosystem = "local"; Resolver = { Get-CommandDisplayFlexible -Name "rv" } },
        @{ Name = "rvw";     Cmd = "rvw";     Method = "rv wrapper (ruby lane)"; Ecosystem = "cargo" },
        @{ Name = "mise";    Cmd = "mise";    Method = "optional unified overlay (not SSOT)"; Ecosystem = "local" },
        @{ Name = "goup";    Cmd = "goup";    Method = "GH release binary"; Ecosystem = "cargo" },
        @{ Name = "cargo";   Cmd = "cargo";   Method = "rustup toolchain"; Ecosystem = "cargo" },
        @{ Name = "rustup";  Cmd = "rustup";  Method = "rustup manager"; Ecosystem = "cargo" },
        @{ Name = "brush";   Cmd = "brush";   Method = "cargo install brush-shell"; Ecosystem = "cargo" },
        @{ Name = "biome";   Cmd = "biome";   Method = "bun add -g";    Ecosystem = "bun" },
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
        @{ Path = "~/.bun/bin/";     Label = "bun ecosystem (bun, biome, codex, gemini)" },
        @{ Path = "~/.cargo/bin/";   Label = "cargo ecosystem (rustc, rustup, mdbook, rv, goup)" },
        @{ Path = "~/.goup/";        Label = "goup-managed Go versions (go.dev source)" },
        @{ Path = "%APPDATA%\rv\";   Label = "rv-managed Ruby versions" }
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

    Write-Host ""
    Write-Host "CHTHONIC DOCTOR v$VERSION" -ForegroundColor Cyan -NoNewline
    Write-Host " | endoflife.date" -ForegroundColor DarkGray
    Write-Host ("="*72) -ForegroundColor DarkGray

    foreach ($check in $checks) {
        $installed = Get-InstalledVersion $check.Name

        # Skip optional tools that aren't installed
        if ($check.Optional -and -not $installed) { continue }

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
                } else {
                    $badge = "current"
                }
            } else {
                $badge = "current"
            }
        } else {
            $badge = "no API data"
        }

        # Display line
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

    Write-Host ("="*72) -ForegroundColor DarkGray
    $currentCount = ($results.Count -gt 0) ? ($results | Where-Object { $_.status -eq "current" }).Count : (($checks | ForEach-Object { $_.Name }) | Where-Object { $_ -notin ($fixable.Tool) }).Count
    $checkedCount = $checks.Count - ($checks | Where-Object { $_.Optional -and -not (Get-InstalledVersion $_.Name) }).Count
    $fixCount = $fixable.Count
    $okCount = $checkedCount - $fixCount
    Write-Host "  $okCount/$checkedCount current" -NoNewline -ForegroundColor $(if ($fixCount -eq 0) { "Green" } else { "Yellow" })
    if ($fixCount -gt 0) {
        Write-Host "  |  $fixCount fixable" -NoNewline -ForegroundColor Yellow
        Write-Host "  (--dry-run | --fix)" -NoNewline -ForegroundColor DarkGray
    }
    Write-Host "  | endoflife.date" -ForegroundColor DarkGray
    Write-Host ""

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

    if ($Json) {
        $jsonResults = $checks | ForEach-Object {
            $inst = Get-InstalledVersion $_.Name
            if ($_.Optional -and -not $inst) { return }
            @{ tool = $_.Name; manager = $_.Manager; installed = $inst }
        }
        Write-Output (ConvertTo-Json $jsonResults -Depth 5)
    }
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
        exit 0
    }
    "claudine" {
        # Compatibility alias for existing shell/profile wrappers.
        $quietFlag = $HasQuietFlag
        Invoke-PolyglotActivation -Quiet:$quietFlag
        exit 0
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
                Write-Host 'chthonic ide <action>'
                Write-Host "  launch [path]    - Launch Claude Code IDE"
                Write-Host "  detect           - Check IDE status"
                Write-Host "  reset            - Reset IDE configuration"
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
                Write-Host 'chthonic mcp <action>'
                Write-Host "  start      - Start MCP services"
                Write-Host "  stop       - Stop MCP services"
                Write-Host "  status     - Check service status"
                Write-Host "  logs       - Tail service logs"
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
                Write-Host 'chthonic config <action>'
                Write-Host "  init       - Initialize configuration"
                Write-Host "  show       - Display configuration"
                Write-Host '  set <k> <v> - Set configuration value'
                exit 0
            }
        }
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
                if ($RemainingArgs.Count -ge 2 -and $RemainingArgs[0] -eq "--cmd") {
                    & $brushExe -c $RemainingArgs[1]
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
                Write-Host 'chthonic shell <action>'
                Write-Host "  probe           - show detected shell lanes"
                Write-Host "  brush [args...] - launch Brush"
                Write-Host "  brush --cmd <c> - run one Brush command"
                Write-Host "  pwsh [args...]  - launch PowerShell 7"
                Write-Host "  pwsh --cmd <c>  - run one PowerShell command"
                Write-Host "  bash [args...]  - launch Git/MSYS2 Bash"
                Write-Host "  bash --cmd <c>  - run one Bash command"
                exit 0
            }
        }
    }

    "ssot" {
        if (-not $Action) {
            Write-Host 'chthonic ssot <action>'
            Write-Host "  queue [--write <path>] [--json]"
            Write-Host "  entity <name> [--json]"
            Write-Host "  section <query> [--json]"
            Write-Host "  drift [--json]"
            Write-Host "  lineage [--entity <name>] [--write <path>] [--json]"
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
    { $_ -in "audit", "compact", "extract", "resolve", "map", "analyze" } {
        $exitCode = Invoke-ArchiveCommand -Cmd $Domain -CmdArgs @($Action) + $RemainingArgs
        exit $exitCode
    }
    
    # Gemini CLI - disable MCP to avoid startup crash
    "gemini" {
        $env:GEMINI_DISABLE_MCP = "1"
        & pwsh (Join-Path $SCRIPT_DIR "gemini-cli-wrapper.ps1") @CmdArgs
        exit $LASTEXITCODE
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
