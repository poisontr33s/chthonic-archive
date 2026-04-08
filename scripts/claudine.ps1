#!/usr/bin/env pwsh

# @SID: SCRIPT_CLAUDINE_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: claudine.ps1
# ║ Module: Legacy compatibility wrapper for chthonic
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: INFRASTRUCTURE
# ║ Semantic ID: SCRIPT_CLAUDINE_COMPAT_V1
# ║ Purpose: Preserve old claudine entrypoint while delegating to chthonic.ps1
# ║ Exports: (none)
# ║ Flags/Modes: -Action, -Args, -Quiet, -Json
# ║ Cross-References: scripts/chthonic.ps1, SCRIPTS_README.md
# ╚════════════════════════════════════════════════════════════════════════════

param(
    [Parameter(Position = 0)]
    [string]$Action = "env",

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args,

    [switch]$Quiet,
    [switch]$Json
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ChthonicScript = Join-Path $ScriptDir "chthonic.ps1"

if (-not (Test-Path $ChthonicScript)) {
    Write-Error "chthonic.ps1 not found at: $ChthonicScript"
    exit 1
}

function Get-ClaudineGuidePayload {
    try {
        $json = & $ChthonicScript "commands" "guide" "--json"
        if ($LASTEXITCODE -eq 0 -and $json) {
            return ($json | ConvertFrom-Json -ErrorAction Stop)
        }
    } catch {}

    return [pscustomobject]@{
        entrypoint = "claudine"
        default_action = "env"
        start_here = @(
            [pscustomobject]@{ command = "claudine start"; summary = "desktop-oriented overview" }
            [pscustomobject]@{ command = "claudine repair"; summary = "doctor dry-run guidance" }
        )
        domains = @()
        notes = @(
            "Claudine is the human-facing guide shell.",
            "Chthonic remains the execution shell."
        )
    }
}

function Show-ClaudineHelp {
    $guide = Get-ClaudineGuidePayload

    Write-Host "Usage: claudine [action] [args]"
    Write-Host ""
    Write-Host ("Default action: {0}" -f $guide.default_action)
    Write-Host ""
    Write-Host "Start Here:"
    foreach ($entry in $guide.start_here) {
        Write-Host ("  {0,-26} {1}" -f $entry.command, $entry.summary)
    }
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  claudine start"
    Write-Host "  claudine repair"
    Write-Host "  claudine status --json"
    foreach ($entry in $guide.domains | Select-Object -First 6) {
        Write-Host ("  {0}" -f $entry.suggested_command)
    }
    Write-Host ""
    Write-Host "Notes:"
    foreach ($note in $guide.notes) {
        Write-Host ("  - {0}" -f $note)
    }
}

# If Action used default and the first remaining token is actually the intended action
# (common for `--help`, `--version`, `--quiet` forms), normalize it.
if (-not $PSBoundParameters.ContainsKey("Action") -and $Args -and $Args.Count -gt 0) {
    $Action = $Args[0]
    if ($Args.Count -gt 1) {
        $Args = $Args[1..($Args.Count - 1)]
    } else {
        $Args = @()
    }
}

if ($Action -in @("--help", "-h", "help")) {
    Show-ClaudineHelp
    exit 0
}

if ($Action -in @("--version", "-v")) {
    & $ChthonicScript "--version"
    exit $LASTEXITCODE
}

switch ($Action) {
    "start" {
        & $ChthonicScript "status"
        exit $LASTEXITCODE
    }
    "repair" {
        & $ChthonicScript "doctor" "--dry-run"
        exit $LASTEXITCODE
    }
}

# Backward compatibility:
#   claudine --quiet
#   claudine --json
# should behave as env activation with flags.
if ($Action -match '^--') {
    if ($Action -in @("--quiet", "--json")) {
        $Args = @($Action) + $Args
        $Action = "env"
    } else {
        & $ChthonicScript $Action @Args
        exit $LASTEXITCODE
    }
}

$forward = @()
if ($Action) { $forward += $Action }
if ($Args) { $forward += $Args }
if ($Quiet -and -not ($forward -contains "--quiet")) { $forward += "--quiet" }
if ($Json -and -not ($forward -contains "--json")) { $forward += "--json" }

$env:CLAUDINE_COMPAT = "1"
$env:CLAUDINE_COMPAT_WRAPPER = $MyInvocation.MyCommand.Path
$env:CHTHONIC_SCRIPT = $ChthonicScript

& $ChthonicScript @forward
exit $LASTEXITCODE
