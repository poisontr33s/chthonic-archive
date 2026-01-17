# scripts/shell_capabilities.ps1
# Purpose: minimal, deterministic shell/environment probe for automation agents
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
$report.claude = (Get-Command claude -ErrorAction SilentlyContinue)?.Source

# PATH snapshot (process-local, ordered)
$report.path = [Environment]::GetEnvironmentVariable("PATH", "Process") -split ';' | Where-Object { $_ -and $_.Trim() -ne '' }

# Emit JSON only
$report | ConvertTo-Json -Depth 4
