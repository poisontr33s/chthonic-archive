#!/usr/bin/env pwsh

#
# @SID: BRIDGE_SSOT_PATHS_PS1_V1
# @Type: INFRASTRUCTURE
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: PowerShell SSOT cascade bridge — mirrors Python manifest for PS1 consumers
#

<#
.SYNOPSIS
  SSOT Cascade Bridge — PowerShell

  Mirrors the Python cascade (ssot_manifest.py → ssot_paths.py) for PS1 consumers.
  All SSOT path references in PowerShell MUST dot-source this file, never hardcode.

  If the SSOT filename changes, update THIS file (and the Python manifest).
  Downstream PS1 consumers resolve through these exports.
#>

# The frozen monolithic SSOT.
$Script:SSOT_HOLDER = ".github/copilot-instructions.archive.md"

# The 85-line routing pointer.
$Script:SSOT_POINTER = ".github/copilot-instructions.md"

# The historizing fork (pre-freeze snapshot).
$Script:SSOT_PROTO = ".github/copilot-instructions-copy.md"

function Resolve-SsotPath {
    <#
    .SYNOPSIS
      Resolve an SSOT path relative to a given root directory.
    .PARAMETER Root
      Repository root directory.
    .PARAMETER Which
      Which SSOT file: holder, pointer, or proto. Default: pointer.
    #>
    param(
        [Parameter(Mandatory=$true)][string]$Root,
        [ValidateSet("holder","pointer","proto")][string]$Which = "pointer",
        [switch]$AssertExists
    )
    $map = @{ holder = $Script:SSOT_HOLDER; pointer = $Script:SSOT_POINTER; proto = $Script:SSOT_PROTO }
    $resolved = Join-Path $Root $map[$Which]
    if ($AssertExists -and -not (Test-Path $resolved)) {
        throw "SSOT $Which not found at expected path: $resolved`nEnsure repository root is correct (got: $Root)"
    }
    return $resolved
}
