#!/usr/bin/env pwsh

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: copilot_clean.ps1
# ║ Module: Copilot CLI launcher profile
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: integration/copilot
# ║ Architectural Role: CLI profile shim (non-destructive)
# ║ Semantic ID: SCRIPT_COPILOT_CLEAN_V1
# ║ Purpose: Launch Copilot CLI with explicit flags/env (no hidden sabotage)
# ║ Exports: None (launcher script)
# ║ Flags/Modes: -DisableCustomAgents, -DisableBuiltinMcps, -DisableMcpServer, -NoCustomInstructions
# ║ Cross-References: .github/copilot-instructions.md, .github/pathstofiles.md
# ╚════════════════════════════════════════════════════════════════════════════

<#
.SYNOPSIS
  Launch GitHub Copilot CLI with explicit profile switches.

.DESCRIPTION
  Copilot CLI can discover custom agents from:
  - [repo]/.github/agents/*.md
  - [repo]/.claude/agents/*.md
  - ~/.claude/agents/*.md

  This repo intentionally contains `.claude/agents/` for Claude-lane workflows.
  By default, this launcher does NOT disable anything. Use switches to opt-out.

.USAGE
  pwsh -NoProfile -File scripts/copilot_clean.ps1 [switches...] [-- <copilot args...>]
#>

[CmdletBinding(PositionalBinding = $false)]
param(
  [switch]$DisableCustomAgents,
  [switch]$DisableBuiltinMcps,
  [string[]]$DisableMcpServer,
  [switch]$NoCustomInstructions,
  [switch]$RepairInsidersCopilotCli,
  [switch]$EnsureCopilotCli,
  [switch]$LocateCopilot,
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$CopilotArgs
)

function Test-CopilotCommand {
  param([string]$Path)

  if (-not (Test-Path $Path)) { return $false }

  # Avoid the VS Code Copilot extension wrapper script that can prompt npm install.
  if ($Path -match '(?i)globalStorage\\github\.copilot-chat\\copilotCli\\copilot\.ps1$') {
    return $false
  }

  # Only verify the file exists and is an executable — skip live --version probe
  # which spawns an extra process on every invocation and can fail on auth/network.
  return ($Path -match '\.exe$' -or (Get-Item $Path -ErrorAction SilentlyContinue)?.Extension -ne '.ps1')
}

function Get-CopilotPath {
  $candidates = @()

  $copilotCmd = Get-Command copilot -ErrorAction SilentlyContinue
  if ($copilotCmd) {
    if (-not ($copilotCmd.Path -match '(?i)globalStorage\\github\.copilot-chat\\copilotCli\\copilot\.ps1$')) {
      $candidates += $copilotCmd.Path
    } else {
      Write-Verbose "Ignoring hijack copilot shim at: $($copilotCmd.Path)"
    }
  }

  # Add known WinGet installation paths for Copilot CLI (portable zip installs).
  try {
    $wingetPaths = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Directory -Filter 'GitHub.Copilot*' -ErrorAction SilentlyContinue | ForEach-Object { Join-Path $_.FullName 'copilot.exe' }
    foreach ($wp in $wingetPaths) {
      if (Test-Path $wp) {
        $candidates += $wp
      }
    }
  } catch {
  }

  # Add known WinGet-side-channel paths using package metadata
  $alternatePaths = @(
    Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages\GitHub.Copilot.Prerelease_Microsoft.Winget.Source_8wekyb3d8bbwe\copilot.exe',
    Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages\GitHub.Copilot_Microsoft.Winget.Source_8wekyb3d8bbwe\copilot.exe'
  )
  foreach ($wp in $alternatePaths) {
    if (Test-Path $wp) { $candidates += $wp }
  }

  # Additional paths directly from where.exe (executable paths) and known install locations.
  try {
    $wherePaths = & where.exe copilot 2>$null | ForEach-Object { $_.Trim() } | Where-Object { $_ }
    foreach ($wp in $wherePaths) {
      if (-not ($wp -match '(?i)globalStorage\\github\.copilot-chat\\copilotCli\\copilot\.ps1$')) {
        $candidates += $wp
      }
    }
  } catch {
  }

  $knownPaths = @(
    "$env:LOCALAPPDATA\Programs\GitHub Copilot CLI\copilot.exe",
    "$env:ProgramFiles\GitHub Copilot CLI\copilot.exe",
    "$env:ProgramFiles(x86)\GitHub Copilot CLI\copilot.exe",
    "$env:USERPROFILE\.cargo\bin\copilot.exe"
  )
  $candidates += $knownPaths

  foreach ($p in $candidates | Select-Object -Unique) {
    if (Test-CopilotCommand -Path $p) { return $p }
  }

  return $null
}

function Install-CopilotCli {
  Write-Host "🚀 Attempting YOLO install: GitHub Copilot CLI" -ForegroundColor Cyan

  $wingetIds = @(
    'GitHub.Copilot.Prerelease',
    'GitHub.Copilot.CLI',
    'GitHub.Copilot',
    'GitHub.CopilotCLI'
  )

  if (Get-Command winget -ErrorAction SilentlyContinue) {
    foreach ($id in $wingetIds) {
      Write-Host "- Trying winget (winget source) install $id..." -ForegroundColor Gray
      $res = winget install --id $id --source winget --accept-package-agreements --accept-source-agreements --exact 2>&1
      # 0x8A150101 = already installed; treat as success
      if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq -1978335999) {
        Write-Host "✅ winget: $id is present (exit $LASTEXITCODE)" -ForegroundColor Green
        return
      }
      if ($res -match 'No package found|no applicable') {
        continue
      }
      Write-Host "⚠ winget install $id returned code $LASTEXITCODE" -ForegroundColor Yellow
    }
    Write-Warning "winget could not find a valid Copilot CLI package."
  }

  if (Get-Command choco -ErrorAction SilentlyContinue) {
    Write-Host "- Using choco install..." -ForegroundColor Gray
    choco install github-copilot-cli -y
    if ($LASTEXITCODE -eq 0) { return }
  }

  Write-Warning "Could not auto-install Copilot CLI: no matching winget package and choco failed or is unavailable. Please install manually."
}

function Ensure-CopilotShimDirectory {
  $shimDir = Join-Path $env:USERPROFILE 'bin'
  if (-not (Test-Path $shimDir)) {
    New-Item -ItemType Directory -Path $shimDir -Force | Out-Null
  }

  if (-not ($env:PATH -split ';' | Where-Object { $_.Trim() -ieq $shimDir })) {
    $newPath = "$shimDir;$env:PATH"
    [Environment]::SetEnvironmentVariable('PATH', $newPath, 'User')
    $env:PATH = $newPath
  }

  return $shimDir
}

function Set-CopilotCmdShim {
  param([string]$ExecutablePath)
  $shimDir = Ensure-CopilotShimDirectory
  $shimFile = Join-Path $shimDir 'copilot.cmd'
  $shimContent = "@echo off`n`"$ExecutablePath`" %*"
  Set-Content -Path $shimFile -Value $shimContent -Force
  Write-Host "✅ Copilot CMD shim created at $shimFile" -ForegroundColor Green
}

function Set-CopilotProfileShim {
  param([string]$ScriptPath)

  if (-not (Test-Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force | Out-Null
  }

  $shimMarker = '# copilot_clean ps1 shim (do not remove)'
  $shimCommand = @'
function copilot {
  $scriptPath = "'$ScriptPath'"
  if (Test-Path $scriptPath) { . $scriptPath }

  try {
    $path = Get-CopilotPath
    if (-not $path) {
      Write-Error 'Copilot CLI not found. Run scripts/copilot_clean.ps1 -EnsureCopilotCli first.'
      return
    }
    & $path @args
  } catch {
    Write-Error "Copilot failed: $($_.Exception.Message)"
  }
}
'@

  $profileLines = Get-Content -Path $PROFILE -ErrorAction SilentlyContinue
  $existingShim = $profileLines -contains $shimMarker

  if ($existingShim) {
    $newContent = $profileLines -replace '(?ms)# copilot_clean ps1 shim \(do not remove\).*?function copilot \{.*?\}', "$shimMarker`n$shimCommand"
    Set-Content -Path $PROFILE -Value $newContent -Force
    return
  }

  Add-Content -Path $PROFILE -Value "`n$shimMarker`n$shimCommand`n"
}

function Ensure-CopilotCli {
  $path = Get-CopilotPath
  if ($path) {
    Write-Host "✅ Copilot CLI already available at: $path" -ForegroundColor Green
    Set-CopilotProfileShim -ScriptPath (Join-Path $PSScriptRoot 'copilot_clean.ps1')
    return
  }

  Write-Host "⚠️ Copilot CLI not detected in environment. Running installer fallback..." -ForegroundColor Yellow
  Install-CopilotCli

  Start-Sleep -Seconds 3
  $path = Get-CopilotPath
  if ($path) {
    Write-Host "✅ Copilot CLI is now available at: $path" -ForegroundColor Green
    Set-CopilotProfileShim -ScriptPath (Join-Path $PSScriptRoot 'copilot_clean.ps1')
    Set-CopilotCmdShim -ExecutablePath $path
    return
  }

  Write-Error "❌ Copilot CLI still not found. Please install manually from https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli"
  throw "Copilot CLI not available"
}

function Repair-InsidersCopilotCli {
  Write-Host "🔧 Repairing Copilot CLI for VS Code Insiders path..." -ForegroundColor Cyan

  $appData = $env:APPDATA
  $stableScript = Join-Path $appData 'Code\User\globalStorage\github.copilot-chat\copilotCli\copilot.ps1'
  $insidersScript = Join-Path $appData 'Code - Insiders\User\globalStorage\github.copilot-chat\copilotCli\copilot.ps1'

  if (Test-Path $insidersScript) {
    Write-Host "✅ Insiders Copilot CLI already exists at: $insidersScript" -ForegroundColor Green
    return
  }

  if (-not (Test-Path $stableScript)) {
    Write-Warning "Stable Copilot CLI script not found at expected location: $stableScript"
    Write-Warning "Please install Copilot extension and run the extension's Copilot CLI setup first."
    return
  }

  $targetDir = Split-Path $insidersScript -Parent
  New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
  Copy-Item -Path $stableScript -Destination $insidersScript -Force
  Write-Host "✅ Copilot CLI script copied to Insiders path: $insidersScript" -ForegroundColor Green
}

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($DisableCustomAgents) {
  $env:CUSTOM_AGENTS = "false"
}

if ($EnsureCopilotCli) {
  Ensure-CopilotCli
  Write-Host "Done: Copilot CLI ensure mode (no invocation)." -ForegroundColor Cyan
  return 0
}

if ($RepairInsidersCopilotCli) {
  Repair-InsidersCopilotCli
  if (-not $DisableBuiltinMcps -and -not $NoCustomInstructions -and -not $DisableCustomAgents -and (-not $CopilotArgs -or $CopilotArgs.Count -eq 0)) {
    Write-Host "Done: Insiders Copilot CLI repair mode only (no invocation)." -ForegroundColor Cyan
    return 0
  }
}

if ($LocateCopilot) {
  $path = Get-CopilotPath
  if ($path) {
    Write-Output $path
    exit 0
  }
  Write-Error "No valid copilot path found."
  exit 1
}

$argsList = @()

if ($DisableBuiltinMcps) {
  $argsList += "--disable-builtin-mcps"
}

if ($DisableMcpServer) {
  foreach ($name in $DisableMcpServer) {
    if ($null -ne $name -and $name.Trim().Length -gt 0) {
      $argsList += "--disable-mcp-server"
      $argsList += $name
    }
  }
}

if ($NoCustomInstructions) {
  $argsList += "--no-custom-instructions"
}

if ($CopilotArgs) {
  $argsList += $CopilotArgs
}

$copilotPath = Get-CopilotPath
if (-not $copilotPath) {
  Write-Error "❌ Could not find a valid Copilot CLI executable; run with -EnsureCopilotCli first."
  exit 1
}

Write-Host "🔗 Executing Copilot CLI from: $copilotPath" -ForegroundColor Cyan
& "$copilotPath" @argsList
exit $LASTEXITCODE
