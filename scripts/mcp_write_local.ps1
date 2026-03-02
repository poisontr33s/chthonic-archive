#!/usr/bin/env pwsh
# Purpose: Generate a local, secret-bearing `.mcp.json` from the user's API pool/env.
#
# Why:
# - `.mcp.json` is intentionally ignored by git in this repo (whitelist .gitignore).
# - Claude Code / MCP clients often expect literal headers (not env interpolation).
# - This script keeps tokens out of committed files while restoring connectivity.
#
# Usage:
#   pwsh -NoProfile -File scripts/mcp_write_local.ps1
#   pwsh -NoProfile -File scripts/mcp_write_local.ps1 -LoadPool
#
# Notes:
# - Never commit `.mcp.json`.
# - Tokens are read from process env; use `.\scripts\api_pool.ps1 -Load` to populate.
#
# CANON
#   Prefer: pwsh -NoProfile -File scripts/claude_ide.ps1 write-mcp -GitHubMode <copilot|official>

param(
  [switch]$LoadPool,
  [ValidateSet("official","copilot")][string]$GitHubMode = "official",
  [switch]$IncludeCopilotFallback,
  [switch]$NoBootstrapGitHubOfficial
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($LoadPool) {
  .\scripts\api_pool.ps1 -Load | Out-Null
}

function Require-Env {
  param([Parameter(Mandatory=$true)][string]$Name)
  $v = [System.Environment]::GetEnvironmentVariable($Name, "Process")
  if ([string]::IsNullOrWhiteSpace([string]$v)) {
    throw "Missing env var: $Name (load via .\\scripts\\api_pool.ps1 -Load)"
  }
  return [string]$v
}

$gh = Require-Env -Name "GITHUB_TOKEN"
$hf = [System.Environment]::GetEnvironmentVariable("HUGGINGFACE_HUB_TOKEN", "Process")
if ([string]::IsNullOrWhiteSpace([string]$hf)) {
  $hf = [System.Environment]::GetEnvironmentVariable("HF_TOKEN", "Process")
}
if ([string]::IsNullOrWhiteSpace([string]$hf)) {
  throw "Missing env var: HUGGINGFACE_HUB_TOKEN (or HF_TOKEN) (load via .\\scripts\\api_pool.ps1 -Load)"
}

function Command-Exists {
  param([Parameter(Mandatory=$true)][string]$Name)
  return [bool](Get-Command -Name $Name -ErrorAction SilentlyContinue)
}

function Resolve-GitHubOfficialServer {
  # GitHub's official MCP server is github/github-mcp-server (Go + Docker).
  # Prefer Docker if available; else prefer a local binary; else optionally bootstrap via `go install`.
  #
  # Notes:
  # - The old npm server `@modelcontextprotocol/server-github` is not maintained; do not depend on it.
  # - We keep bootstrap optional so this script can be used in constrained environments.

  $tokenEnvName = "GITHUB_PERSONAL_ACCESS_TOKEN"

  if (Command-Exists -Name "docker") {
    return @{
      command = "docker"
      args = @(
        "run","-i","--rm",
        "-e",$tokenEnvName,
        "ghcr.io/github/github-mcp-server"
      )
      env = @{
        $tokenEnvName = $gh
      }
    }
  }

  # Prefer a repo-local tool bin so we don't depend on global PATH state.
  $binDir = Join-Path -Path (Get-Location) -ChildPath "scripts/bin"
  $exe = Join-Path -Path $binDir -ChildPath "github-mcp-server.exe"
  if (Test-Path -LiteralPath $exe) {
    return @{
      command = $exe
      args = @("stdio")
      env = @{
        $tokenEnvName = $gh
      }
    }
  }

  if (-not $NoBootstrapGitHubOfficial -and (Command-Exists -Name "go")) {
    New-Item -ItemType Directory -Force -Path $binDir | Out-Null
    # Install into scripts/bin for deterministic, repo-scoped execution.
    $env:GOBIN = $binDir
    # GitHub MCP server repo contains cmd/github-mcp-server. This compiles a native exe on Windows.
    go install "github.com/github/github-mcp-server/cmd/github-mcp-server@latest" | Out-Null
    if (Test-Path -LiteralPath $exe) {
      return @{
        command = $exe
        args = @("stdio")
        env = @{
          $tokenEnvName = $gh
        }
      }
    }
  }

  throw "GitHubMode=official requires Docker or a local github-mcp-server binary (or Go to bootstrap)."
}

$payload = @{
  mcpServers = @{
    # IMPORTANT:
    # "GitHub MCP" is NOT "Copilot MCP".
    #
    # - Official GitHub MCP: stdio server talking directly to GitHub APIs (recommended).
    # - Copilot MCP: Copilot-hosted HTTP MCP proxy (optional fallback).
    #
    # Default: official GitHub MCP (stdio) under the server name "github".
    github = if ($GitHubMode -eq "official") { Resolve-GitHubOfficialServer } else {
      # Copilot MCP proxy (HTTP). Only use if you explicitly want Copilot's endpoint.
      @{
        type = "http"
        url  = "https://api.githubcopilot.com/mcp/"
        headers = @{
          Authorization = "Bearer $gh"
        }
      }
    }
    huggingface = @{
      type = "http"
      url  = "https://huggingface.co/mcp"
      headers = @{
        Authorization = "Bearer $hf"
      }
    }
  }
}

if ($IncludeCopilotFallback -and $GitHubMode -eq "official") {
  # Optional: keep Copilot proxy as a distinct server name so it never masquerades as "github".
  $payload.mcpServers.github_copilot = @{
    type = "http"
    url  = "https://api.githubcopilot.com/mcp/"
    headers = @{
      Authorization = "Bearer $gh"
    }
  }
}

$json = $payload | ConvertTo-Json -Depth 10
Set-Content -Encoding utf8 -Path ".mcp.json" -Value $json
Write-Host "Wrote .mcp.json (local, ignored)."
