#!/usr/bin/env pwsh
# @SID: SCRIPT_SFS_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: sfs.ps1
# ║ Module: Shell capabilities probe
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: PROBE (thin shim — delegates to shell_capabilities.ps1)
# ║ Purpose: Thin shim; all logic lives in shell_capabilities.ps1
# ║ Exports: (none — passes through from shell_capabilities.ps1)
# ║ Cross-References: scripts/shell_capabilities.ps1
# ╚════════════════════════════════════════════════════════════════════════════

# Thin shim: all logic now lives in shell_capabilities.ps1.
# This file retained for callers referencing sfs.ps1 directly.
& "$PSScriptRoot/shell_capabilities.ps1"

