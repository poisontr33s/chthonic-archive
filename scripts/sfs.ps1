#!/usr/bin/env pwsh
# @SID: SCRIPT_SFS_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: sfs.ps1
# ║ Module: Shell capabilities probe
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: PROBE
# ║ Semantic ID: SCRIPT_SFS_V1
# ║ Purpose: Emit ABI-stable environment probe as JSON
# ║ Exports: (none)
# ║ Flags/Modes: (none)
# ║ Cross-References: scripts/shell_capabilities.ps1
# ╚════════════════════════════════════════════════════════════════════════════

# scripts/shell_capabilities.ps1
# Minimal environment probe — ABI-stable, no branching, no side effects.
# Output: single JSON object to STDOUT.

$report = [ordered]@{
    timestamp        = (Get-Date).ToString("o")
    script_path      = $MyInvocation.MyCommand.Path
    os               = (Get-CimInstance Win32_OperatingSystem).Caption
    pwsh_version     = $PSVersionTable.PSVersion.ToString()
    pwsh_edition     = $PSVersionTable.PSEdition
    bash_path        = (Get-Command bash   -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
    bun_path         = (Get-Command bun    -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
    cargo_path       = (Get-Command cargo  -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
    uv_path          = (Get-Command uv     -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
    gh_path          = (Get-Command gh     -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
    git_path         = (Get-Command git    -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
    claude_path      = (Get-Command claude -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
    process_path_env = [Environment]::GetEnvironmentVariable("PATH","Process") -split ';'
}

$report | ConvertTo-Json -Depth 6

