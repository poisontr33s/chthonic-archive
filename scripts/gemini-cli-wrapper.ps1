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
# ║ Flags/Modes: -m/-p/-i/-u/-v/-h/-y and -Arguments passthrough
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

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

# Disable MCP discovery to prevent Bun crash during startup
$env:GEMINI_DISABLE_MCP = "1"

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

    $updated = & gemini --version 2>$null
    if ($LASTEXITCODE -eq 0 -and $updated) {
        Write-Host "[gemini-wrapper] Updated Gemini CLI version: $updated" -ForegroundColor Green
    } else {
        Write-Host "[gemini-wrapper] Update completed. Run `gemini --version` to confirm." -ForegroundColor Yellow
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

if ($SelfUpdate -or $positionalUpdate -or ($Arguments -and $Arguments.Count -gt 0 -and $Arguments[0] -eq "update")) {
    Test-LegacyGeminiDependency
    Invoke-GeminiSelfUpdate
    exit 0
}

Test-LegacyGeminiDependency

$geminiCmd = Get-Command gemini -ErrorAction SilentlyContinue
if ($geminiCmd -and $geminiCmd.Source) {
    & $geminiCmd.Source @cliArgs
    exit $LASTEXITCODE
}

# Fallback execution via Bun global package path.
$geminiCliPath = Join-Path $env:USERPROFILE ".bun\install\global\node_modules\@google\gemini-cli\dist\index.js"
if (-not (Test-Path $geminiCliPath)) {
    Write-Error "Gemini CLI not found. Checked: gemini.exe on PATH and $geminiCliPath"
    Write-Host "Reinstall with: bun install -g @google/gemini-cli" -ForegroundColor Yellow
    exit 1
}

& bun $geminiCliPath @cliArgs
