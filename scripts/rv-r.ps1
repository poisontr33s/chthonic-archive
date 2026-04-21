#!/usr/bin/env pwsh
# @SID: SCRIPT_RV_R_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: rv-r.ps1
# ║ Module: R rv wrapper
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: UTILITY
# ║ Semantic ID: SCRIPT_R_RV_WRAPPER_V1
# ║ Purpose: Route R package-manager calls to an isolated A2-ai/rv install
# ║ Exports: (none)
# ║ Flags/Modes: passthrough only
# ║ Cross-References: docs/OXIDIZED_POLYGLOT_SURFACE.md
# ╚════════════════════════════════════════════════════════════════════════════

[CmdletBinding(PositionalBinding = $false)]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

function Get-RRvExecutable {
    $defaultCandidate = Join-Path $env:USERPROFILE ".r-rv\bin\rv.exe"
    if (Test-Path -Path $defaultCandidate -PathType Leaf) {
        return $defaultCandidate
    }

    $candidates = @()

    if ($env:R_RV_BIN) {
        $candidates += $env:R_RV_BIN
    }

    if ($env:R_RV_HOME) {
        $candidates += @(
            (Join-Path $env:R_RV_HOME "rv.exe"),
            (Join-Path $env:R_RV_HOME "rv")
        )
    }

    $candidates += @(
        (Join-Path $env:USERPROFILE ".r-rv\bin\rv.exe"),
        (Join-Path $env:USERPROFILE ".r-rv\bin\rv")
    )

    foreach ($candidate in ($candidates | Where-Object { $_ } | Select-Object -Unique)) {
        if (Test-Path -Path $candidate -PathType Leaf) {
            return $candidate
        }
    }

    return $null
}

$rrv = Get-RRvExecutable
if (-not $rrv) {
    Write-Error @"
R rv wrapper could not find the A2-ai/rv executable.

This repo reserves bare 'rv' for the Ruby lane.
To use the Rust-native R package manager, install it in an isolated location and set one of:
  - R_RV_BIN  = full path to rv(.exe)
  - R_RV_HOME = directory that contains rv(.exe)

Suggested dedicated root:
  $env:USERPROFILE\.r-rv\bin\rv.exe
"@
    exit 1
}

& $rrv @Arguments
exit $LASTEXITCODE
