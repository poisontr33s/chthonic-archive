#!/usr/bin/env pwsh

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: gemini-cli-wrapper.ps1
# ║ Module: Gemini CLI wrapper
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: UTILITY
# ║ Semantic ID: SCRIPT_GEMINI_CLI_WRAPPER_V1
# ║ Purpose: Wrap Gemini CLI to disable MCP discovery during Bun startup
# ║ Exports: (none)
# ║ Flags/Modes: -m/-p/-i/-u/-v/-h/-y/-c and -Arguments passthrough
# ║ Cross-References: (none)
# ╚════════════════════════════════════════════════════════════════════════════

# Gemini CLI Wrapper - Disable MCP crash on startup
# Bun is drop-in Node replacement with node_modules support
# Issue: Gemini CLI MCP discovery fails on startup → crash
# Fix: Set GEMINI_DISABLE_MCP env var before execution

param(
    [Alias("m")]
    [string]$Model,

    [Alias("p")]
    [string]$Prompt,

    [Alias("i")]
    [string]$PromptInteractive,

    [Alias("y")]
    [switch]$Yolo,

    [Alias("h")]
    [switch]$Help,

    [Alias("v")]
    [switch]$Version,

    [Alias("u")]
    [switch]$SelfUpdate,

    [Alias("c")]
    [switch]$CheckUpdate,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

# Disable MCP discovery to prevent Bun crash during startup
$env:GEMINI_DISABLE_MCP = "1"

function Get-GeminiEntrypoint {
    $entry = Join-Path $env:USERPROFILE ".bun\install\global\node_modules\@google\gemini-cli\dist\index.js"
    if (Test-Path $entry) {
        return $entry
    }
    return $null
}

function Test-GeminiExecutable {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    try {
        $null = & $Path --version 2>$null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Resolve-GeminiExecutable {
    $globalBunGemini = Join-Path $env:USERPROFILE ".bun\bin\gemini.exe"
    if ((Test-Path $globalBunGemini) -and (Test-GeminiExecutable -Path $globalBunGemini)) {
        return $globalBunGemini
    }

    return $null
}

function Test-LegacyGeminiDependency {
    $pkgPath = Join-Path (Get-Location) "package.json"
    if (-not (Test-Path $pkgPath)) {
        return
    }

    try {
        $pkg = Get-Content $pkgPath -Raw | ConvertFrom-Json
    } catch {
        return
    }

    $hasLegacyGemini =
        ($pkg.dependencies -and $pkg.dependencies.PSObject.Properties.Name -contains "gemini") -or
        ($pkg.devDependencies -and $pkg.devDependencies.PSObject.Properties.Name -contains "gemini")

    if ($hasLegacyGemini) {
        Write-Host "[gemini-wrapper] WARNING: Local package.json contains legacy npm package 'gemini' (not @google/gemini-cli)." -ForegroundColor Yellow
        Write-Host "[gemini-wrapper] Run: bun remove gemini" -ForegroundColor Yellow
    }
}

function Invoke-GeminiSelfUpdate {
    Write-Host "[gemini-wrapper] Updating Gemini CLI via Bun global lane..." -ForegroundColor Cyan
    # Keep node-gyp/native addon lanes deterministic on Windows.
    $prevMakeFlags = $env:MAKEFLAGS
    $prevMflags = $env:MFLAGS
    if ($env:MAKEFLAGS) { Remove-Item Env:MAKEFLAGS -ErrorAction SilentlyContinue }
    if ($env:MFLAGS) { Remove-Item Env:MFLAGS -ErrorAction SilentlyContinue }

    & bun add -g @google/gemini-cli@latest

    if ($null -ne $prevMakeFlags) { $env:MAKEFLAGS = $prevMakeFlags }
    if ($null -ne $prevMflags) { $env:MFLAGS = $prevMflags }
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Gemini CLI self-update failed (exit $LASTEXITCODE)."
        exit $LASTEXITCODE
    }

    $geminiExe = Resolve-GeminiExecutable
    $updated = $null
    if ($geminiExe) {
        $updated = & $geminiExe --version 2>$null
    } else {
        $entry = Get-GeminiEntrypoint
        if ($entry) {
            $updated = & bun $entry --version 2>$null
        }
    }
    if ($LASTEXITCODE -eq 0 -and $updated) {
        Write-Host "[gemini-wrapper] Updated Gemini CLI version: $updated" -ForegroundColor Green
    } else {
        Write-Host "[gemini-wrapper] Update completed. Run `~/.bun/bin/gemini.exe --version` (or `gemini --version`) to confirm." -ForegroundColor Yellow
    }
}

function Get-GeminiCurrentVersion {
    $geminiExe = Resolve-GeminiExecutable
    if ($geminiExe) {
        $raw = & $geminiExe --version 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $raw) {
            return $null
        }
        return ($raw | Select-Object -First 1).Trim()
    }

    $entry = Get-GeminiEntrypoint
    if (-not $entry) {
        return $null
    }
    $raw = & bun $entry --version 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $raw) {
        return $null
    }
    return ($raw | Select-Object -First 1).Trim()
}

function Get-GeminiLatestVersion {
    $raw = & bun pm view @google/gemini-cli version 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $raw) {
        return $null
    }
    $line = ($raw | Select-Object -First 1).Trim()
    if ($line -match '^\d+\.\d+\.\d+([\-+].*)?$') {
        return $line
    }
    return $null
}

function Invoke-GeminiUpdateCheck {
    $current = Get-GeminiCurrentVersion
    $latest = Get-GeminiLatestVersion

    if (-not $current) {
        Write-Host "[gemini-wrapper] Gemini CLI not found locally." -ForegroundColor Red
        Write-Host "[gemini-wrapper] Install: bun add -g @google/gemini-cli@latest" -ForegroundColor Yellow
        exit 1
    }
    if (-not $latest) {
        Write-Host "[gemini-wrapper] Could not query registry for latest version." -ForegroundColor Yellow
        Write-Host "[gemini-wrapper] Current version: $current" -ForegroundColor Cyan
        exit 0
    }

    $needsUpdate = $false
    try {
        $needsUpdate = ([version]$current -lt [version]$latest)
    } catch {
        # Non-standard SemVer labels: fallback to exact compare.
        $needsUpdate = ($current -ne $latest)
    }

    if ($needsUpdate) {
        Write-Host "[gemini-wrapper] Update available: $current -> $latest" -ForegroundColor Yellow
        Write-Host "[gemini-wrapper] Run: pwsh -NoProfile -File scripts/gemini-cli-wrapper.ps1 -u" -ForegroundColor Yellow
    } else {
        Write-Host "[gemini-wrapper] Up to date: $current" -ForegroundColor Green
    }
}

$cliArgs = @()

if ($PSBoundParameters.ContainsKey("Model")) {
    $cliArgs += @("-m", $Model)
}
if ($PSBoundParameters.ContainsKey("Prompt")) {
    $cliArgs += @("--prompt", $Prompt)
}
if ($PSBoundParameters.ContainsKey("PromptInteractive")) {
    $cliArgs += @("--prompt-interactive", $PromptInteractive)
}
if ($Yolo) {
    $cliArgs += "--yolo"
}
if ($Help) {
    $cliArgs += "--help"
}
if ($Version) {
    $cliArgs += "--version"
}
if ($Arguments) {
    $cliArgs += $Arguments
}

$positionalUpdate =
    ($Model -eq "update" -or $Model -eq "--update") -and
    -not $PSBoundParameters.ContainsKey("Prompt") -and
    -not $PSBoundParameters.ContainsKey("PromptInteractive") -and
    (-not $Arguments -or $Arguments.Count -eq 0)

$positionalCheck =
    ($Model -eq "check" -or $Model -eq "check-update" -or $Model -eq "--check-update") -and
    -not $PSBoundParameters.ContainsKey("Prompt") -and
    -not $PSBoundParameters.ContainsKey("PromptInteractive") -and
    (-not $Arguments -or $Arguments.Count -eq 0)

if ($CheckUpdate -or $positionalCheck -or ($Arguments -and $Arguments.Count -gt 0 -and ($Arguments[0] -in @("check", "check-update", "--check-update")))) {
    Test-LegacyGeminiDependency
    Invoke-GeminiUpdateCheck
    exit 0
}

if ($SelfUpdate -or $positionalUpdate -or ($Arguments -and $Arguments.Count -gt 0 -and $Arguments[0] -eq "update")) {
    Test-LegacyGeminiDependency
    Invoke-GeminiSelfUpdate
    exit 0
}

Test-LegacyGeminiDependency

$geminiExe = Resolve-GeminiExecutable
if ($geminiExe) {
    & $geminiExe @cliArgs
    exit $LASTEXITCODE
}

# Fallback execution via Bun global package path.
$geminiCliPath = Get-GeminiEntrypoint
if (-not (Test-Path $geminiCliPath)) {
    Write-Error "Gemini CLI not found. Checked: gemini.exe on PATH and $geminiCliPath"
    Write-Host "Reinstall with: bun install -g @google/gemini-cli" -ForegroundColor Yellow
    exit 1
}

& bun $geminiCliPath @cliArgs
