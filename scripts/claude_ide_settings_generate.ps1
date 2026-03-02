#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Generate a minimal Claude Code settings overlay for IDE-launched sessions.

.WHY
  Claude Code can blow past the model context window purely from System/Tools
  when too many MCP servers and plugins are enabled. VS Code launching makes
  this worse because "everything on" tends to be the default.

  This script generates a small, deterministic settings overlay file that the
  IDE wrapper can inject via `claude --settings <file>`.

.OUTPUT
  Writes `.claude/ide.settings.generated.json` (workspace-local).

.NOTES
  - This file must not contain secrets (no tokens/headers).
  - It is an overlay: it should reduce scope, not redefine your entire config.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$outPath = Join-Path $repoRoot ".claude/ide.settings.generated.json"

function Has-EnvVar {
  param([Parameter(Mandatory = $true)][string]$Name)
  $v = [System.Environment]::GetEnvironmentVariable($Name, "Process")
  return -not [string]::IsNullOrWhiteSpace([string]$v)
}

function Try-ReadJsonFile {
  param([Parameter(Mandatory = $true)][string]$Path)
  if (-not (Test-Path $Path)) { return $null }
  try { return (Get-Content $Path -Raw | ConvertFrom-Json) } catch { return $null }
}

$workspaceMcp = Try-ReadJsonFile -Path (Join-Path $repoRoot ".vscode/mcp.json")
$rootMcp = Try-ReadJsonFile -Path (Join-Path $repoRoot ".mcp.json")

function Has-McpServerName {
  param([Parameter(Mandatory = $true)][string]$Name)
  if ($rootMcp -and $rootMcp.mcpServers -and $rootMcp.mcpServers.$Name) { return $true }
  if ($workspaceMcp -and $workspaceMcp.servers -and $workspaceMcp.servers.$Name) { return $true }
  return $false
}

function Is-Truthy {
  param([string]$Value)
  if ([string]::IsNullOrWhiteSpace($Value)) { return $false }
  switch ($Value.Trim().ToLowerInvariant()) {
    "1" { return $true }
    "true" { return $true }
    "yes" { return $true }
    "on" { return $true }
    default { return $false }
  }
}

function Get-McpServerNames {
  $names = @()
  if ($rootMcp -and $rootMcp.mcpServers) { $names += @($rootMcp.mcpServers.PSObject.Properties.Name) }
  if ($workspaceMcp -and $workspaceMcp.servers) { $names += @($workspaceMcp.servers.PSObject.Properties.Name) }
  return @($names | Sort-Object -Unique)
}

$fullContext = Is-Truthy ([System.Environment]::GetEnvironmentVariable("CLAUDE_IDE_FULL_CONTEXT", "Process"))
$knownMcpServers = Get-McpServerNames

if ($fullContext) {
  # Opt-in mode for users who explicitly want richer IDE context.
  $enabledMcpjsonServers = @()
  if (Has-McpServerName -Name "github") { $enabledMcpjsonServers += "github" }
  if ((Has-McpServerName -Name "huggingface") -and ((Has-EnvVar -Name "HF_TOKEN") -or (Has-EnvVar -Name "HUGGINGFACE_HUB_TOKEN"))) {
    $enabledMcpjsonServers += "huggingface"
  }

  $overlay = [ordered]@{
    enableAllProjectMcpServers = $false
    enabledMcpjsonServers = $enabledMcpjsonServers
    enabledPlugins = [ordered]@{
      "github@claude-plugins-official" = $true
      "chthonic-tools@chthonic-local" = $true
    }
    alwaysThinkingEnabled = $false
    effortLevel = "low"
  }
} else {
  # Default for IDE sessions: minimize automatic System/Tools context.
  $overlay = [ordered]@{
    enableAllProjectMcpServers = $false
    enabledMcpjsonServers = @()
    disabledMcpjsonServers = $knownMcpServers
    enabledPlugins = [ordered]@{
      "github@claude-plugins-official" = $false
      "chthonic-tools@chthonic-local" = $false
    }
    alwaysThinkingEnabled = $false
    effortLevel = "low"
  }
}

$json = ($overlay | ConvertTo-Json -Depth 10)
New-Item -ItemType Directory -Force -Path (Split-Path $outPath -Parent) | Out-Null
Set-Content -Path $outPath -Value $json -Encoding utf8 -NoNewline

Write-Host $outPath
