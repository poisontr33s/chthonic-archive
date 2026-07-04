#!/usr/bin/env pwsh
#
# @SID: SCRIPT_MCP_WRITE_LOCAL_V2
# @Type: INFRASTRUCTURE
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Generate local MCP config from the API pool without refreshing tokens.
#
<#
.SYNOPSIS
  Generate or inspect local `.mcp.json` from `~/.chthonic/api_pool.json`.

.WHY
  IDE/plugin updates may rewrite MCP JSON, but the tokens do not belong to the
  IDE config. The API pool is the durable source of truth. This script copies
  existing token values from the pool into local MCP config because current MCP
  clients commonly require literal HTTP Authorization headers.

.CONTRACT
  - Never mints, refreshes, rotates, or regenerates tokens.
  - Never prints token values.
  - `.mcp.json` is local/ignored and may contain generated bearer headers.
  - Manual token renewal happens only when a token is actually expired/revoked.

.USAGE
  pwsh -NoProfile -File scripts/mcp_write_local.ps1
  pwsh -NoProfile -File scripts/mcp_write_local.ps1 -Mock
  pwsh -NoProfile -File scripts/mcp_write_local.ps1 -GitHubMode copilot -List
  pwsh -NoProfile -File scripts/mcp_write_local.ps1 -List
#>

param(
  [switch]$LoadPool,
  [switch]$NoLoadPool,
  [switch]$Mock,
  [switch]$List,
  [ValidateSet("official","copilot")][string]$GitHubMode = "copilot",
  [switch]$IncludeCopilotFallback,
  [switch]$NoBootstrapGitHubOfficial
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$MockMode = $PSBoundParameters.ContainsKey("Mock") -or ([string]$MyInvocation.Line -match '(?i)(^|\s)-Mock(\s|$)')

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
Push-Location $repoRoot
try {
  function Get-ApiPoolPath {
    $dir = Join-Path $HOME ".chthonic"
    return Join-Path $dir "api_pool.json"
  }

  function Normalize-Token {
    param([AllowEmptyString()][string]$Value = "")
    $v = ([string]$Value).Trim()
    if ($v.StartsWith("<") -and $v.EndsWith(">") -and $v.Length -ge 3) {
      $v = $v.Substring(1, $v.Length - 2).Trim()
    }
    if ($v -match '^(?i)Bearer\s+') {
      $v = ($v -replace '^(?i)Bearer\s+', '').Trim()
    }
    return $v
  }

  function Read-PoolEnv {
    $path = Get-ApiPoolPath
    $map = @{}
    if (Test-Path -LiteralPath $path) {
      $json = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
      if ($json.env) {
        foreach ($prop in $json.env.PSObject.Properties) {
          $map[$prop.Name] = Normalize-Token -Value ([string]$prop.Value)
        }
      }
    }
    return $map
  }

  function Get-Token {
    param(
      [Parameter(Mandatory=$true)][hashtable]$Pool,
      [Parameter(Mandatory=$true)][string[]]$Names
    )
    foreach ($name in $Names) {
      $envVal = [System.Environment]::GetEnvironmentVariable($name, "Process")
      $envVal = Normalize-Token -Value $envVal
      if (-not [string]::IsNullOrWhiteSpace($envVal)) { return $envVal }

      if ($Pool.ContainsKey($name)) {
        $poolVal = Normalize-Token -Value ([string]$Pool[$name])
        if (-not [string]::IsNullOrWhiteSpace($poolVal)) { return $poolVal }
      }
    }
    return ""
  }

  function Get-OptionalEnvValue {
    param(
      [Parameter(Mandatory=$true)][hashtable]$Pool,
      [Parameter(Mandatory=$true)][string[]]$Names
    )
    $value = Get-Token -Pool $Pool -Names $Names
    if ([string]::IsNullOrWhiteSpace($value)) { return $null }
    return $value
  }

  function Require-Token {
    param(
      [Parameter(Mandatory=$true)][hashtable]$Pool,
      [Parameter(Mandatory=$true)][string[]]$Names,
      [Parameter(Mandatory=$true)][string]$Purpose
    )
    $value = Get-Token -Pool $Pool -Names $Names
    if ([string]::IsNullOrWhiteSpace($value)) {
      throw "Missing token for ${Purpose}: $($Names -join ' or '). Add it to ~/.chthonic/api_pool.json."
    }
    return $value
  }

  function Resolve-CommandPath {
    param(
      [Parameter(Mandatory=$true)][string]$Preferred,
      [Parameter(Mandatory=$true)][string]$FallbackName
    )
    if (Test-Path -LiteralPath $Preferred) { return (Resolve-Path -LiteralPath $Preferred).Path }
    $cmd = Get-Command -Name $FallbackName -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($cmd -and $cmd.Source) { return $cmd.Source }
    return $FallbackName
  }

  function Command-Exists {
    param([Parameter(Mandatory=$true)][string]$Name)
    return [bool](Get-Command -Name $Name -ErrorAction SilentlyContinue)
  }

  function New-BunServer {
    param(
      [Parameter(Mandatory=$true)][string]$Script,
      [string[]]$ExtraArgs = @(),
      [hashtable]$EnvVars
    )
    $server = @{
      type = "stdio"
      command = Resolve-CommandPath -Preferred (Join-Path $HOME ".bun\bin\bun.exe") -FallbackName "bun"
      args = @("run", (Join-Path $repoRoot $Script)) + $ExtraArgs
      cwd = $repoRoot
    }
    if ($EnvVars) { $server["env"] = $EnvVars }
    return $server
  }

  function Resolve-GitHubOfficialServer {
    param([Parameter(Mandatory=$true)][string]$Token)

    $tokenEnvName = "GITHUB_PERSONAL_ACCESS_TOKEN"
    if (Command-Exists -Name "docker") {
      return @{
        type = "stdio"
        command = "docker"
        args = @("run","-i","--rm","-e",$tokenEnvName,"ghcr.io/github/github-mcp-server")
        env = @{ $tokenEnvName = $Token }
      }
    }

    $binDir = Join-Path -Path $repoRoot -ChildPath "scripts/bin"
    $exe = Join-Path -Path $binDir -ChildPath "github-mcp-server.exe"
    if (Test-Path -LiteralPath $exe) {
      return @{
        type = "stdio"
        command = $exe
        args = @("stdio")
        env = @{ $tokenEnvName = $Token }
      }
    }

    if (-not $NoBootstrapGitHubOfficial -and (Command-Exists -Name "go")) {
      New-Item -ItemType Directory -Force -Path $binDir | Out-Null
      $env:GOBIN = $binDir
      go install "github.com/github/github-mcp-server/cmd/github-mcp-server@latest" | Out-Null
      if (Test-Path -LiteralPath $exe) {
        return @{
          type = "stdio"
          command = $exe
          args = @("stdio")
          env = @{ $tokenEnvName = $Token }
        }
      }
    }

    throw "GitHubMode=official requires Docker, scripts/bin/github-mcp-server.exe, or Go bootstrap."
  }

  function New-McpPayload {
    param([Parameter(Mandatory=$true)][hashtable]$Pool)

    $gh = Require-Token -Pool $Pool -Names @("GITHUB_TOKEN","GH_TOKEN","GITHUB_PERSONAL_ACCESS_TOKEN","GITHUB_PAT") -Purpose "GitHub MCP"
    $hf = Require-Token -Pool $Pool -Names @("HUGGINGFACE_HUB_TOKEN","HF_TOKEN") -Purpose "Hugging Face MCP"
    $ncbiKey = Get-OptionalEnvValue -Pool $Pool -Names @("NCBI_API_KEY")
    $ncbiAdminEmail = Get-OptionalEnvValue -Pool $Pool -Names @("NCBI_ADMIN_EMAIL","NCBI_EMAIL")

    $bunx = Resolve-CommandPath -Preferred (Join-Path $HOME ".bun\bin\bunx.exe") -FallbackName "bunx"
    $uv   = Resolve-CommandPath -Preferred (Join-Path $HOME ".local\bin\uv.exe")  -FallbackName "uv"
    $uvx  = Resolve-CommandPath -Preferred (Join-Path $HOME ".local\bin\uvx.exe") -FallbackName "uvx"
    $masDir = Join-Path $repoRoot "mas_mcp"
    $chthonicExe = Join-Path $repoRoot "target\release\chthonic-mcp-server.exe"
    $fsRoots = @(
      $repoRoot,
      (Join-Path $env:USERPROFILE "PsychoNoir-Kontrapunkt"),
      (Join-Path $env:USERPROFILE "Restructure-MCP-Orchestration"),
      (Join-Path $env:USERPROFILE "Claudine_Supreme-Polyglot-Git-Cli-Lsp-Repo-Clone-Engineering-Bun-Technique"),
      (Join-Path $env:USERPROFILE "git-dump-lfs-holder-we-it-takes"),
      (Join-Path $env:USERPROFILE "psychonoir-kontrapunkt-large-file-holder")
    )

    $servers = [ordered]@{
      # --- Chthonic core (Claude Code lane; not present in the VS Code set) ---
      game = New-BunServer -Script "scripts/mcp-game.ts"
      sourcer = New-BunServer -Script "scripts/mcp-sourcer.ts"
      ssot = New-BunServer -Script "scripts/mcp-ssot.ts"
      sonic = New-BunServer -Script "scripts/mcp-sonic.ts"
      corpus = New-BunServer -Script "scripts/corpus-mcp.ts"
      "cocoindex-code" = @{
        type = "stdio"
        command = Resolve-CommandPath -Preferred (Join-Path $HOME ".local\bin\ccc.exe") -FallbackName "ccc"
        args = @("mcp")
      }
      # --- GitHub: Bearer (Claude Code needs it) + all-toolsets/insiders headers ---
      github = if ($GitHubMode -eq "official") {
        Resolve-GitHubOfficialServer -Token $gh
      } else {
        @{
          type = "http"
          url = "https://api.githubcopilot.com/mcp/"
          headers = @{
            Authorization = "Bearer $gh"
            "X-MCP-Toolsets" = "all"
            "X-MCP-Insiders" = "true"
          }
        }
      }
      huggingface = @{
        type = "http"
        url = "https://huggingface.co/mcp"
        headers = @{ Authorization = "Bearer $hf" }
      }
      ncbi = New-BunServer -Script "scripts/mcp-ncbi.ts"
      # --- VS Code parity set (workspaceFolder->repoRoot; bun/bunx/uv/uvx->absolute; HF env-token->pool) ---
      browser = New-BunServer -Script "scripts/mcp-browser.ts"
      "bun-docs" = @{ type = "http"; url = "https://bun.com/docs/mcp" }
      "microsoft-docs" = @{ type = "http"; url = "https://learn.microsoft.com/api/mcp" }
      "asc-injector" = New-BunServer -Script "scripts/mcp-asc-injector.ts" -EnvVars @{ SSOT_PATH = ".chthonic/SSOT.md" }
      # chthonic-v3: Rust rmcp port (target/release) when built; bun fallback otherwise (no-delete).
      # Build with: cargo build --release -p chthonic-mcp-server
      "chthonic-v3" = if (Test-Path $chthonicExe) {
        @{ type = "stdio"; command = $chthonicExe; args = @(); cwd = $repoRoot; env = @{ CHTHONIC_ROOT = $repoRoot } }
      } else {
        New-BunServer -Script "scripts/mcp-chthonic-server.ts" -EnvVars @{ CHTHONIC_ROOT = $repoRoot }
      }
      bevy = @{
        type = "stdio"
        command = Join-Path $repoRoot "target\debug\bevy-mcp-server.exe"
        args = @()
      }
      vulkan = @{
        type = "stdio"
        command = Join-Path $repoRoot "target\debug\vulkan-mcp-server.exe"
        args = @()
      }
      workiq = @{
        type = "stdio"
        command = $bunx
        args = @("--bun","-y","@microsoft/workiq@latest","mcp")
      }
      "mas-mcp" = @{
        type = "stdio"
        command = $uv
        args = @("run","--quiet","--directory",$masDir,"python","-m","server")
        cwd = $repoRoot
      }
      filesystem = New-BunServer -Script "scripts/mcp-filesystem.ts" -ExtraArgs $fsRoots
      context7 = @{ type = "http"; url = "https://mcp.context7.com/mcp" }
      "github-archaeology" = New-BunServer -Script "scripts/mcp-github-archaeology.ts" -EnvVars @{ ARCHAEOLOGY_REPO = "poisontr33s/Restructure-MCP-Orchestration" }
      "sequential-thinking" = @{
        type = "stdio"
        command = $bunx
        args = @("--bun","-y","@modelcontextprotocol/server-sequential-thinking")
      }
      memory = @{
        type = "stdio"
        command = $bunx
        args = @("--bun","-y","@modelcontextprotocol/server-memory")
      }
      fetch = @{
        type = "stdio"
        command = $uvx
        args = @("mcp-server-fetch")
        env = @{ PYTHONIOENCODING = "utf-8" }
      }
      time = @{
        type = "stdio"
        command = $uvx
        args = @("mcp-server-time")
      }
      git = @{
        type = "stdio"
        command = $uvx
        args = @("mcp-server-git","--repository",$repoRoot)
      }
    }

    if ($ncbiKey) {
      $servers.ncbi.env = @{}
      $servers.ncbi.env["NCBI_API_KEY"] = $ncbiKey
    }
    if ($ncbiAdminEmail) {
      if (-not $servers.ncbi.ContainsKey("env")) { $servers.ncbi.env = @{} }
      $servers.ncbi.env["NCBI_ADMIN_EMAIL"] = $ncbiAdminEmail
      $servers.ncbi.env["NCBI_EMAIL"] = $ncbiAdminEmail
    }

    if ($IncludeCopilotFallback -and $GitHubMode -eq "official") {
      $servers.github_copilot = @{
        type = "http"
        url = "https://api.githubcopilot.com/mcp/"
        headers = @{ Authorization = "Bearer $gh" }
      }
    }

    return @{ mcpServers = $servers }
  }

  function Test-HasAuthorizationHeader {
    param([Parameter(Mandatory=$true)]$Server)
    $headers = $null
    if ($Server -is [System.Collections.IDictionary]) {
      if ($Server.Contains("headers")) { $headers = $Server["headers"] }
    } else {
      $headersProp = $Server.PSObject.Properties["headers"]
      if ($headersProp) { $headers = $headersProp.Value }
    }
    if (-not $headers) { return $false }

    if ($headers -is [System.Collections.IDictionary]) {
      if (-not $headers.Contains("Authorization")) { return $false }
      return -not [string]::IsNullOrWhiteSpace([string]$headers["Authorization"])
    }

    $prop = $headers.PSObject.Properties["Authorization"]
    return ($null -ne $prop -and -not [string]::IsNullOrWhiteSpace([string]$prop.Value))
  }

  function Get-ServerValue {
    param(
      [Parameter(Mandatory=$true)]$Server,
      [Parameter(Mandatory=$true)][string]$Name
    )
    if ($Server -is [System.Collections.IDictionary]) {
      if ($Server.Contains($Name)) { return [string]$Server[$Name] }
      return ""
    }
    $prop = $Server.PSObject.Properties[$Name]
    if ($prop) { return [string]$prop.Value }
    return ""
  }

  function Write-McpList {
    param([Parameter(Mandatory=$true)]$Payload)
    $rows = @()
    if ($Payload.mcpServers -is [System.Collections.IDictionary]) {
      foreach ($name in $Payload.mcpServers.Keys) {
        $server = $Payload.mcpServers[$name]
        $rows += [pscustomobject]@{
          Name = [string]$name
          Type = Get-ServerValue -Server $server -Name "type"
          Command = Get-ServerValue -Server $server -Name "command"
          Url = Get-ServerValue -Server $server -Name "url"
          HasAuthorizationHeader = (Test-HasAuthorizationHeader -Server $server)
        }
      }
    } else {
      foreach ($prop in $Payload.mcpServers.PSObject.Properties) {
        $server = $prop.Value
        $rows += [pscustomobject]@{
          Name = $prop.Name
          Type = Get-ServerValue -Server $server -Name "type"
          Command = Get-ServerValue -Server $server -Name "command"
          Url = Get-ServerValue -Server $server -Name "url"
          HasAuthorizationHeader = (Test-HasAuthorizationHeader -Server $server)
        }
      }
    }
    $rows | Format-Table -AutoSize
  }

  function Get-ExistingMcpPayload {
    $path = Join-Path $repoRoot ".mcp.json"
    if (-not (Test-Path -LiteralPath $path)) { return $null }
    return Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
  }

  function Assert-ExpectedMcpNames {
    param([Parameter(Mandatory=$true)]$Payload)
    $expected = @(
      "game","sourcer","ssot","sonic","corpus","cocoindex-code","github","huggingface","ncbi",
      "browser","bun-docs","microsoft-docs","asc-injector","chthonic-v3","bevy","vulkan","workiq","mas-mcp",
      "filesystem","context7","github-archaeology","sequential-thinking","memory","fetch","time","git"
    )
    $actual = @()
    if ($Payload.mcpServers -is [System.Collections.IDictionary]) {
      $actual = @($Payload.mcpServers.Keys)
    } else {
      $actual = @($Payload.mcpServers.PSObject.Properties.Name)
    }
    $missing = @($expected | Where-Object { $actual -notcontains $_ })
    if ($missing.Count -gt 0) {
      throw "Generated MCP payload missing expected server(s): $($missing -join ', ')"
    }
  }

  if ($List -and -not $MockMode) {
    $existing = Get-ExistingMcpPayload
    if ($existing) {
      Write-McpList -Payload $existing
      exit 0
    }
  }

  if (-not $NoLoadPool) {
    . "$repoRoot\scripts\api_pool.ps1" -Load -Quiet
  } elseif ($LoadPool) {
    . "$repoRoot\scripts\api_pool.ps1" -Load -Quiet
  }

  $pool = Read-PoolEnv
  $payload = New-McpPayload -Pool $pool
  Assert-ExpectedMcpNames -Payload ([pscustomobject]$payload)

  if ($MockMode) {
    Write-Host "mock ok: MCP payload builds from API pool; .mcp.json was not written."
    Write-McpList -Payload ([pscustomobject]$payload)
    exit 0
  }

  if ($List) {
    Write-McpList -Payload ([pscustomobject]$payload)
    exit 0
  }

  $payload | ConvertTo-Json -Depth 12 | Set-Content -Encoding utf8 -Path ".mcp.json"
  Write-Host "Wrote .mcp.json from API pool (local, ignored; values not printed)."
  Write-McpList -Payload ([pscustomobject]$payload)
  exit 0
} finally {
  Pop-Location
}
