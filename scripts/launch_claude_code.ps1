#!/usr/bin/env pwsh

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: launch_claude_code.ps1
# ║ Module: Claude Code Launcher
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: orchestration/bootstrap
# ║ Architectural Role: Claude Code/Desktop installation and launch manager
# ║ Semantic ID: SCRIPT_LAUNCH_CLAUDE_CODE_V1
# ║ Purpose: Install/start Claude Code / Claude Desktop on Windows 11
# ║ Exports: None (launcher script)
# ║ Flags/Modes: -Force (skip running check), -WaitSeconds <int>
# ║ Cross-References: start_mcp_session.ps1
# ╚════════════════════════════════════════════════════════════════════════════
<#
 Usage: pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\launch_claude_code.ps1 [-Force] [-WaitSeconds 30]
#>

param(
  [switch]$Force,
  [int]$WaitSeconds = 30
)

function Log($m){ Write-Host "[launch_claude_code] $m" }

function ClaudeRunning {
  $names = @("claude","Claude","claude-code","claudeCode")
  foreach ($n in $names) {
    if (Get-Process -Name $n -ErrorAction SilentlyContinue) { return $true }
  }
  return $false
}

function Get-ClaudeCli {
  $cmd = Get-Command claude.exe -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($null -eq $cmd) { return $null }

  $version = $null
  try {
    $version = (& $cmd.Path --version 2>$null | Select-Object -First 1)
  } catch {
    $version = $null
  }

  return [pscustomobject]@{
    Path = $cmd.Path
    Version = $version
  }
}

function Get-ClaudeDesktopApp {
  $app = Get-StartApps | Where-Object { $_.Name -eq "Claude" } | Select-Object -First 1
  $pkg = Get-AppxPackage | Where-Object { $_.Name -eq "Claude" } | Select-Object -First 1

  return [pscustomobject]@{
    AppId = $app.AppID
    PackageVersion = $pkg.Version
    InstallLocation = $pkg.InstallLocation
    Installed = $null -ne $pkg
  }
}

function Get-ClaudeDesktopRuntime {
  $root = Join-Path $env:APPDATA "Claude\\claude-code"
  if (-not (Test-Path $root)) { return $null }

  $runtimeDir = Get-ChildItem $root -Directory |
    Sort-Object Name -Descending |
    Select-Object -First 1

  if ($null -eq $runtimeDir) { return $null }

  $exe = Join-Path $runtimeDir.FullName "claude.exe"
  if (-not (Test-Path $exe)) { return $null }

  return [pscustomobject]@{
    Path = $exe
    Version = $runtimeDir.Name
  }
}

function Get-ClaudeVsCodeRuntime {
  $roots = @(
    (Join-Path $env:USERPROFILE ".vscode-insiders\\extensions"),
    (Join-Path $env:USERPROFILE ".vscode\\extensions")
  )

  $candidates = foreach ($root in $roots) {
    if (-not (Test-Path $root)) { continue }
    Get-ChildItem $root -Directory |
      Where-Object { $_.Name -like "anthropic.claude-code-*" }
  }

  $selected = $candidates | Sort-Object Name -Descending | Select-Object -First 1
  if ($null -eq $selected) { return $null }

  $m = [regex]::Match($selected.Name, '^anthropic\.claude-code-(.+?)-win32-x64$')
  $version = if ($m.Success) { $m.Groups[1].Value } else { $selected.Name }

  return [pscustomobject]@{
    Path = $selected.FullName
    Version = $version
  }
}

function Launch-ClaudeDesktopApp {
  param(
    [Parameter(Mandatory = $true)][string]$AppId
  )

  Log "Launching Claude desktop app via shell:AppsFolder..."
  Start-Process explorer.exe "shell:AppsFolder\$AppId" | Out-Null
}

function Wait-ForClaude {
  param(
    [Parameter(Mandatory = $true)][int]$Seconds
  )

  for ($i = 0; $i -lt $Seconds; $i++) {
    Start-Sleep -Seconds 1
    if (ClaudeRunning) { return $true }
  }

  return $false
}

$winget = (Get-Command winget -ErrorAction SilentlyContinue) -ne $null
$cli = Get-ClaudeCli
$desktopApp = Get-ClaudeDesktopApp
$desktopRuntime = Get-ClaudeDesktopRuntime
$vscodeRuntime = Get-ClaudeVsCodeRuntime

Log ("Detected CLI: {0}" -f $(if ($cli) { "$($cli.Version) @ $($cli.Path)" } else { "not found" }))
Log ("Detected desktop app: {0}" -f $(if ($desktopApp.Installed) { "$($desktopApp.PackageVersion) @ $($desktopApp.InstallLocation)" } else { "not found" }))
Log ("Detected desktop runtime: {0}" -f $(if ($desktopRuntime) { "$($desktopRuntime.Version) @ $($desktopRuntime.Path)" } else { "not found" }))
Log ("Detected VS Code runtime: {0}" -f $(if ($vscodeRuntime) { "$($vscodeRuntime.Version) @ $($vscodeRuntime.Path)" } else { "not found" }))

if ($cli -and $vscodeRuntime -and $cli.Version -and $vscodeRuntime.Version -and ($cli.Version -notlike "*$($vscodeRuntime.Version)*")) {
  Log "Version skew detected between PATH CLI and VS Code runtime."
}

if ($desktopRuntime -and $cli -and $desktopRuntime.Version -ne $null -and $cli.Version -ne $null -and ($cli.Version -notlike "*$($desktopRuntime.Version)*")) {
  Log "Version skew detected between desktop runtime and PATH CLI."
}

if (-not $Force -and (ClaudeRunning)) {
  Log "Claude appears to be running."
  exit 0
}

# If the desktop app is installed but not running, launching it is the least destructive action.
if ($desktopApp.Installed -and $desktopApp.AppId) {
  Launch-ClaudeDesktopApp -AppId $desktopApp.AppId
  if (Wait-ForClaude -Seconds $WaitSeconds) {
    Log "Claude desktop app launched successfully."
    exit 0
  }
  Log "Desktop app launch did not surface a Claude process within $WaitSeconds seconds."
}

# A CLI install is sufficient for repo-local automation even if the desktop app is closed.
if ($cli) {
  Log "Claude CLI is installed and available. Treating installation lane as healthy."
  exit 0
}

if ($winget) {
  Log "Attempting winget install of Claude Code CLI..."
  # Anthropic's Windows CLI package id is Anthropic.ClaudeCode.
  & winget install -e --id Anthropic.ClaudeCode -h --accept-source-agreements --accept-package-agreements
  $cli = Get-ClaudeCli
  if ($cli) {
    Log "Claude Code CLI installed successfully."
    exit 0
  }
  Log "winget install did not produce a usable claude.exe on PATH."
}

$landing = "https://docs.anthropic.com/en/docs/claude-code/setup"
Log "Opening Claude Code setup docs for manual recovery: $landing"
Start-Process $landing | Out-Null
Log "Waiting $WaitSeconds seconds for manual install/sign-in..."
if (Wait-ForClaude -Seconds $WaitSeconds) {
  Log "Claude detected after manual recovery."
  exit 0
}

$cli = Get-ClaudeCli
if ($cli) {
  Log "Claude CLI detected after manual recovery."
  exit 0
}

Log "Claude was not detected after recovery attempts. Manual follow-up required."
exit 2

