#!/usr/bin/env pwsh
# @SID: SCRIPT_SHELL_CAPABILITIES_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: shell_capabilities.ps1
# ║ Module: Shell Environment Probe
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: diagnostic/passive
# ║ Architectural Role: Environment introspection for automation agents
# ║ Purpose: Minimal, deterministic shell/environment probe (ABI-stable)
# ║ Exports: JSON report { os, pwsh_version, bash, bun, cargo, uv, git,
# ║        claude, path[] }
# ║ Flags/Modes: None (pure read-only probe)
# ║ Cross-References: polyglot_env.ps1, probe_toolchain_path.ps1
# ╚════════════════════════════════════════════════════════════════════════════
# ABI-stable: do not add logic/branching/validation/side-effects

$report = [ordered]@{}

# OS + shell
$report.os = (Get-CimInstance Win32_OperatingSystem).Caption
$report.pwsh_version = $PSVersionTable.PSVersion.ToString()

# Tool presence (paths or null)
$report.bash   = (Get-Command bash   -ErrorAction SilentlyContinue)?.Source
$report.bun    = (Get-Command bun    -ErrorAction SilentlyContinue)?.Source
$report.cargo  = (Get-Command cargo  -ErrorAction SilentlyContinue)?.Source
$report.uv     = (Get-Command uv     -ErrorAction SilentlyContinue)?.Source
$report.git    = (Get-Command git    -ErrorAction SilentlyContinue)?.Source
$report.gh     = (Get-Command gh     -ErrorAction SilentlyContinue)?.Source
$report.claude = (Get-Command claude -ErrorAction SilentlyContinue)?.Source

# PATH snapshot (process-local, ordered)
$report.path = [Environment]::GetEnvironmentVariable("PATH", "Process") -split ';' | Where-Object { $_ -and $_.Trim() -ne '' }

# Emit JSON only
$report | ConvertTo-Json -Depth 4

