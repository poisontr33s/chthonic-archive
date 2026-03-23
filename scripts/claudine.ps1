#!/usr/bin/env pwsh

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

function Show-ClaudineHelp {
@"
Usage: claudine [action] [args]

Default action: env

Examples:
  claudine
  claudine --quiet
  claudine status --json
  claudine doctor --origins
  claudine commands counts
  claudine commands inventory
  claudine toolchain hierarchy
  claudine toolchain verify
  claudine r lane
  claudine zig lane
  claudine memory migration
  claudine memory session

Notes:
  - This wrapper delegates to scripts/chthonic.ps1.
  - It forwards the full chthonic command surface, plus bare claudine => env.
  - Use claudine commands inventory to audit the current forwarded domains and counts.
  - All advanced logic and manager handling lives in chthonic.
"@
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
