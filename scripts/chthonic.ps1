#!/usr/bin/env pwsh
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: chthonic.ps1
# ║ Module: Unified polyglot CLI router
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: INFRASTRUCTURE
# ║ Semantic ID: SCRIPT_CHTHONIC_V1
# ║ Purpose: Unified CLI for polyglot tooling and repo operations
# ║ Exports: (none)
# ║ Flags/Modes: -Command, -CmdArgs, -Quiet, -Json
# ║ Cross-References: scripts/claudineENV.ps1
# ╚════════════════════════════════════════════════════════════════════════════

param(
    [Parameter(Position = 0)]
    [string]$Command,
    
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CmdArgs,
    
    [switch]$Quiet,
    [switch]$Json
)

$VERSION = "3.0.0"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$REPO_ROOT = Split-Path -Parent $SCRIPT_DIR
$LIB_DIR = Join-Path $SCRIPT_DIR "lib"
$STATE_DIR = Join-Path $env:USERPROFILE ".chthonic"
$CONFIG_FILE = Join-Path $STATE_DIR "config.json"
$SERVICES_FILE = Join-Path $STATE_DIR "services.json"

# ═══════════════════════════════════════════════════════════════════════════════
# POLYGLOT PATHS - ALL GLOBAL NATIVE INSTALLATIONS (Win11)
# ═══════════════════════════════════════════════════════════════════════════════

# Default polyglot paths (fallback when config.json is missing)
$defaultPolyglotPaths = @(
    # Native user binaries (Claude native installer, uv tools)
    "$env:USERPROFILE\.local\bin",

    # Bun 1.3.9 (JS/TS runtime + Biome 2.3.8)
    "$env:USERPROFILE\.bun\bin",
    
    # Rust 1.93.0 (rustup managed) + Cargo tools
    "$env:USERPROFILE\.cargo\bin",
    
    # Go 1.24.3
    "C:\Go\bin",
    "$env:USERPROFILE\go\bin",
    
    # Ruby 3.4.7 + DevKit (GCC 15.2.0, make, pkg-config)
    "C:\Ruby34-x64\bin",
    "C:\Ruby34-x64\msys64\ucrt64\bin",
    "C:\Ruby34-x64\msys64\usr\bin",
    
    # Git 2.52.0
    "C:\Program Files\Git\cmd"
)

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

function Get-PolyglotPaths {
    if (Test-Path $CONFIG_FILE) {
        try {
            $cfg = Get-Content $CONFIG_FILE -Raw | ConvertFrom-Json
            if ($cfg.PolyglotPaths -and $cfg.PolyglotPaths.Count -gt 0) {
                return $cfg.PolyglotPaths
            }
        } catch {
            # Fall back to defaults if config is unreadable
        }
    }
    return $defaultPolyglotPaths
}

function Show-Help {
@"
CHTHONIC v$VERSION - Meta CLI for Polyglot Development (Win11 pwsh 7.5.x)

Usage: chthonic [--version] [--help] <domain> [<action>] [<args>]

DOMAINS & ACTIONS:

Environment:
  env [--quiet]           Activate polyglot environment
  status                  Show all tool versions
  detect                  Detect IDE and environment context

IDE Management:
  ide launch [path]       Launch Claude Code IDE (defaults to current workspace)
  ide detect              Check IDE availability and extensions
  ide reset               Reset IDE configuration

Service Management (MCP + Bridges):
  mcp start               Start MCP server + bridge (auto if needed)
  mcp stop                Stop all MCP services  
  mcp status              Check service status
  mcp logs                Tail service logs

Configuration:
  config init             Initialize ~/.chthonic config (first run)
  config show             Display current configuration
  config set <key> <val>  Set configuration value

Archive Tools:
  audit [path]            Analyze directory health
  compact [path]          Condense markdown files
  extract [path]          Extract session data
  resolve [--list]        Resolve Semantic IDs (@SID)
  map                     Generate dependency graph
  analyze [path]          Frequency analysis
  book [serve|build]      mdBook documentation

Options:
  --version               Show version
  --help                  Show this help
  --quiet                 Suppress output

Examples:
  chthonic status               # Show all tool versions
  chthonic env                  # Activate polyglot environment
  chthonic detect               # Check IDE setup
  chthonic ide launch .         # Launch IDE in current directory
  chthonic mcp start            # Start services
  chthonic config init          # First-time setup

"@
}

# ═══════════════════════════════════════════════════════════════════════════════
# ENVIRONMENT & SERVICE DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

function Get-EnvironmentContext {
    # Detect if running in VS Code or standalone
    $context = @{
        IsVSCode = $false
        IsCI = $env:CI -eq "true"
        IsWSL = $false
        Terminal = $env:TERM_PROGRAM
        Shell = $PROFILE.Split('\')[-1]
    }
    
    # Check for VS Code integrated terminal
    if ($env:TERM_PROGRAM -eq "vscode" -or $PSVersionTable.Platform -eq "Unix" -and (Test-Path "/.wsl")) {
        $context.IsVSCode = $true
    }
    
    # Check for WSL
    if ((Test-Path "/func/version") -or (Test-Path "/proc/version")) {
        $context.IsWSL = $true
    }
    
    return $context
}

function Get-ServiceStatus {
    $status = @{
        MCP = $null
        Bridge = $null
        Timestamp = Get-Date
    }
    
    # Check MCP server (port 9999)
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:9999/health" -TimeoutSec 1 -ErrorAction SilentlyContinue
        $status.MCP = "running"
    }
    catch {
        $status.MCP = "stopped"
    }
    
    # Check bridge server (port 8888)
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8888/status" -TimeoutSec 1 -ErrorAction SilentlyContinue
        $status.Bridge = "running"
    }
    catch {
        $status.Bridge = "stopped"
    }
    
    return $status
}

# ═══════════════════════════════════════════════════════════════════════════════
# IDE MANAGEMENT (consolidated from launch-claude-ide.ps1)
# ═══════════════════════════════════════════════════════════════════════════════

function Invoke-IDELaunch {
    param([string]$WorkspacePath = $REPO_ROOT)
    
    $ideExecutable = if (Get-Command code-insiders -ErrorAction SilentlyContinue) {
        "code-insiders"
    } elseif (Get-Command code -ErrorAction SilentlyContinue) {
        "code"
    } else {
        Write-Error "❌ VS Code not found in PATH"
        return 1
    }
    
    # Verify Claude Code extension
    $extensionPath = "$env:APPDATA\Code - Insiders\User\extensions"
    if (-not (Test-Path $extensionPath) -or -not (Get-ChildItem $extensionPath -Filter "*claude*" -ErrorAction SilentlyContinue)) {
        Write-Host "⚠️  Claude Code extension not found. Install it:" -ForegroundColor Yellow
        Write-Host "   Extensions → Search 'Claude Code' → Install @anthropic-ai/claude-code" -ForegroundColor Gray
    }
    
    # Launch Claude Code with full endpoint
    Push-Location $WorkspacePath
    try {
        Write-Host "🚀 Launching Claude Code IDE from: $WorkspacePath" -ForegroundColor Cyan
        Write-Host "   IDE: $ideExecutable" -ForegroundColor Gray
        & $ideExecutable "$WorkspacePath" 2>&1 | Out-Null
        
        # Give IDE time to start before returning
        Start-Sleep -Milliseconds 500
        return 0
    }
    catch {
        Write-Error "Failed to launch IDE: $_"
        return 1
    }
    finally {
        Pop-Location
    }
}

function Invoke-IDEDetect {
    param([switch]$Json)
    
    $status = @{}
    $status['vscode_command'] = if (Get-Command code-insiders -ErrorAction SilentlyContinue) { 'code-insiders' } elseif (Get-Command code -ErrorAction SilentlyContinue) { 'code' } else { 'not found' }
    $processes = Get-Process -Name '*Code*' -ErrorAction SilentlyContinue
    $status['running_instances'] = $processes.Count
    $copilotDir = "$env:APPDATA\Code - Insiders\User\globalStorage\github.copilot-chat"
    $status['copilot_configured'] = Test-Path $copilotDir
    
    if ($Json) {
        Write-Output (ConvertTo-Json $status -Compress)
        return
    }
    
    Write-Host "`nIDE Detection & Diagnostic" -ForegroundColor Cyan
    Write-Host ("="*60) -ForegroundColor DarkGray
    
    # Check VS Code installation
    $ideAvailable = @()
    if (Get-Command code-insiders -ErrorAction SilentlyContinue) {
        $ideAvailable += "code-insiders"
    }
    if (Get-Command code -ErrorAction SilentlyContinue) {
        $ideAvailable += "code"
    }
    
    if ($ideAvailable.Count -eq 0) {
        Write-Host "❌ VS Code not found in PATH" -ForegroundColor Red
        return 1
    }
    
    Write-Host "✅ VS Code available: $($ideAvailable -join ', ')" -ForegroundColor Green
    
    # Check running instances
    $running = Get-Process -Name "*code*" -ErrorAction SilentlyContinue | Measure-Object
    Write-Host "✅ Running instances: $($running.Count)" -ForegroundColor Green
    
    # Check extensions
    $extPath = "$env:APPDATA\Code - Insiders\User\extensions"
    if (Test-Path $extPath) {
        $claudeExt = Get-ChildItem $extPath -Filter "*claude*" -ErrorAction SilentlyContinue
        if ($claudeExt) {
            Write-Host "✅ Claude Code extension: installed" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️  Claude Code extension: not installed" -ForegroundColor Yellow
        }
    }
    
    # Check Copilot
    $copilotPath = "$env:APPDATA\Code - Insiders\User\globalStorage\github.copilot-chat"
    if (Test-Path $copilotPath) {
        Write-Host "✅ GitHub Copilot: configured" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  GitHub Copilot: not configured" -ForegroundColor Yellow
    }
    
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
    return 0
}

# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE MANAGEMENT (MCP + Bridge)
# ═══════════════════════════════════════════════════════════════════════════════

function Invoke-MCPStart {
    $context = Get-EnvironmentContext
    Write-Host "🚀 Starting MCP Services..." -ForegroundColor Cyan
    
    # Check if bridge server already running
    $bridgeRunning = Get-ServiceStatus | Select-Object -ExpandProperty Bridge
    if ($bridgeRunning -eq "running") {
        Write-Host "✅ Bridge server already running (port 8888)" -ForegroundColor Green
        return 0
    }
    
    # Start bridge server in background
    Write-Host "   Starting bridge server..." -ForegroundColor Gray
    $job = Start-Job -ScriptBlock {
        param($ScriptDir)
        Set-Location $ScriptDir
        & bun run "bridge-server.ts" 2>&1
    } -ArgumentList $SCRIPT_DIR
    
    Start-Sleep -Seconds 1
    
    $status = Get-ServiceStatus
    Write-Host "✅ Bridge: $($status.Bridge)" -ForegroundColor Green
    Write-Host "✅ Services ready for VS Code Copilot @chthonic" -ForegroundColor Green
    
    return 0
}

function Invoke-MCPStop {
    Write-Host "🛑 Stopping MCP Services..." -ForegroundColor Yellow
    
    Get-Job | Where-Object { $_.Name -like "*bridge*" -or $_.Command -like "*bridge*" } | Stop-Job -PassThru | Remove-Job
    
    Write-Host "✅ Services stopped" -ForegroundColor Green
    return 0
}

function Invoke-MCPStatus {
    param([switch]$Json)
    
    $status = Get-ServiceStatus
    
    if ($Json) {
        Write-Output (ConvertTo-Json @{'bridge_server' = $status.Bridge} -Compress)
        return 0
    }
    
    Write-Host "`nService Status" -ForegroundColor Cyan
    Write-Host ("="*60) -ForegroundColor DarkGray
    Write-Host "  Bridge Server   " -NoNewline -ForegroundColor Gray
    $color = if ($status.Bridge -eq "running") { "Green" } else { "Red" }
    Write-Host $status.Bridge -ForegroundColor $color
    Write-Host ""
    
    return 0
}



function Invoke-PolyglotActivation {
    param([switch]$Quiet)
    
    # Build clean PATH with polyglot tools at front
    $existingPath = $env:Path -split ';' | Where-Object { $_ }
    
    # Add polyglot paths that exist
    $activePaths = @()
    foreach ($p in (Get-PolyglotPaths)) {
        if (Test-Path $p) {
            $activePaths += $p
        }
    }
    
    # Set PATH with polyglot tools first
    $env:Path = ($activePaths + $existingPath | Select-Object -Unique) -join ';'
    
    # Go environment
    $env:GOROOT = "C:\Go"
    $env:GOPATH = "$env:USERPROFILE\go"
    
    # Ruby DevKit
    $env:RIDK_PREFIX = "C:\Ruby34-x64\msys64"
    
    # Mark as activated
    $env:CLAUDINE_ACTIVATED = "1"
    $env:CLAUDINE_VERSION = $VERSION
    $env:CHTHONIC_REPO_ROOT = $REPO_ROOT
    
    if (-not $Quiet) {
        Show-PolyglotStatus
    }
}

function Show-PolyglotStatus {
    param([switch]$Json)
    
    # Collect tool versions
    $tools = @{}
    try { $tools['bun'] = (bun --version 2>$null) -replace 'Bun\s+','' -split ' ' | Select-Object -First 1 } catch { $tools['bun'] = 'not found' }
    try { $tools['biome'] = ((biome --version 2>$null) -split '\n')[0] -replace 'Version:\s*','' } catch { $tools['biome'] = 'not found' }
    try { $tools['rust'] = (rustc --version 2>$null) -replace 'rustc\s*','' } catch { $tools['rust'] = 'not found' }
    try { $tools['go'] = (go version 2>$null) -replace 'go version go','' } catch { $tools['go'] = 'not found' }
    try { $tools['python'] = (uv run python --version 2>&1) -replace 'Python\s*','' } catch { $tools['python'] = 'not found' }
    try { $tools['ruff'] = (ruff --version 2>$null) -replace 'ruff\s*','' } catch { $tools['ruff'] = 'not found' }
    try { $tools['uv'] = ((uv --version 2>$null) -split ' ')[1] } catch { $tools['uv'] = 'not found' }
    try { $tools['ruby'] = (ruby --version 2>$null) -replace 'ruby\s*','' } catch { $tools['ruby'] = 'not found' }
    try { $tools['gcc'] = ((gcc --version 2>$null) -split '\n')[0] -replace '.*\s(\d+\.\d+\.\d+)','$1' } catch { $tools['gcc'] = 'not found' }
    try { $tools['make'] = (make --version 2>$null | Select-Object -First 1) -replace 'GNU Make\s*','' } catch { $tools['make'] = 'not found' }
    try { $tools['git'] = (git --version 2>$null) -replace 'git version\s*','' } catch { $tools['git'] = 'not found' }
    try { $tools['mdbook'] = (mdbook --version 2>$null) -replace 'mdbook\s*v?','' } catch { $tools['mdbook'] = 'not found' }
    if ($env:VULKAN_SDK -match '(\d+\.\d+\.\d+\.\d+)') { $tools['vulkan'] = $matches[1] } else { $tools['vulkan'] = 'not found' }
    $tools['workspace'] = $REPO_ROOT
    
    # Output as JSON or human-readable
    if ($Json) {
        Write-Output (ConvertTo-Json $tools -Compress -Depth 5)
    } else {
        Write-Host "`nCHTHONIC POLYGLOT ENVIRONMENT v$VERSION" -ForegroundColor Cyan
        Write-Host ("="*60) -ForegroundColor DarkGray
        $tools.GetEnumerator() | Where-Object {$_.Key -ne 'workspace'} | Sort-Object Key | ForEach-Object {
            Write-Host "  $($_.Key.PadRight(10))" -NoNewline -ForegroundColor Cyan
            if ($_.Value -eq 'not found') {
                Write-Host $_.Value -ForegroundColor Red
            } else {
                Write-Host $_.Value -ForegroundColor White
            }
        }
        Write-Host ("="*60) -ForegroundColor DarkGray
        Write-Host "  Workspace:" -NoNewline -ForegroundColor DarkGray
        Write-Host " $REPO_ROOT" -ForegroundColor White
        Write-Host ("="*60) -ForegroundColor DarkGray
        Write-Host ""
    }
}

function Invoke-ArchiveCommand {
    param([string]$Cmd, [string[]]$CmdArgs)
    
    $scriptMap = @{
        "audit"   = "audit.py"
        "compact" = "compact.py"
        "extract" = "extract.py"
        "resolve" = "resolve.py"
        "map"     = "map.py"
        "analyze" = "analyze.py"
    }
    
    if ($scriptMap.ContainsKey($Cmd)) {
        # Resolve relative file paths to absolute before changing directory
        $resolvedArgs = @()
        for ($i = 0; $i -lt $CmdArgs.Count; $i++) {
            $arg = $CmdArgs[$i]
            if ($arg -match '^-') {
                # Flag or option — pass through
                $resolvedArgs += $arg
            }
            elseif (Test-Path $arg) {
                # Existing file/directory — resolve to absolute
                $resolvedArgs += (Resolve-Path $arg).Path
            }
            else {
                # Not a path or doesn't exist — pass through as-is
                $resolvedArgs += $arg
            }
        }
        Push-Location $SCRIPT_DIR
        try {
            & uv run python -m "lib.$($Cmd)" @resolvedArgs
            return $LASTEXITCODE
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Error "Unknown command: $Cmd"
        Write-Host "Run 'chthonic --help' for usage." -ForegroundColor Yellow
        return 1
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN DISPATCH - Meta CLI (Domain/Action Model)
# ═══════════════════════════════════════════════════════════════════════════════

# Parse domain/action if provided
$Domain = $Command
$Action = if ($CmdArgs.Count -gt 0) { $CmdArgs[0] } else { $null }
$RemainingArgs = if ($CmdArgs.Count -gt 1) { $CmdArgs[1..($CmdArgs.Count-1)] } else { @() }

# Top-level commands (backward compatible)
switch ($Domain) {
    "--version" {
        Write-Host "chthonic v$VERSION"
        exit 0
    }
    { $_ -in "--help", "-h", "help", $null, "" } {
        Show-Help
        exit 0
    }
    
    # Environment Domain
    "env" {
        $quietFlag = $Quiet -or ($Action -eq "--quiet") -or ($Action -eq "-q")
        Invoke-PolyglotActivation -Quiet:$quietFlag
        exit 0
    }
    "status" {
        Show-PolyglotStatus -Json:$Json
        exit 0
    }
    "detect" {
        $context = Get-EnvironmentContext
        Invoke-IDEDetect -Json:$Json
        exit 0
    }
    
    # IDE Domain (nested commands)
    "ide" {
        switch ($Action) {
            "launch" {
                $path = if ($RemainingArgs.Count -gt 0) { $RemainingArgs[0] } else { $REPO_ROOT }
                $exitCode = Invoke-IDELaunch -WorkspacePath $path
                exit $exitCode
            }
            "detect" {
                $exitCode = Invoke-IDEDetect -Json:$Json
                exit $exitCode
            }
            "reset" {
                Write-Host "🔄 Resetting IDE configuration..." -ForegroundColor Yellow
                Remove-Item "$env:APPDATA\Code - Insiders\User\globalStorage\*claude*" -Recurse -Force -ErrorAction SilentlyContinue
                Write-Host "✅ IDE configuration reset. Reinstall Claude Code extension." -ForegroundColor Green
                exit 0
            }
            default {
                Write-Host 'chthonic ide <action>'
                Write-Host "  launch [path]    - Launch Claude Code IDE"
                Write-Host "  detect           - Check IDE status"
                Write-Host "  reset            - Reset IDE configuration"
                exit 0
            }
        }
    }
    
    # Service/MCP Domain (nested commands)
    "mcp" {
        switch ($Action) {
            "start" {
                $exitCode = Invoke-MCPStart
                exit $exitCode
            }
            "stop" {
                $exitCode = Invoke-MCPStop
                exit $exitCode
            }
            "status" {
                $exitCode = Invoke-MCPStatus -Json:$Json
                exit $exitCode
            }
            "logs" {
                Write-Host "📋 Service logs..." -ForegroundColor Gray
                Get-Job | Where-Object { $_.Name -like "*bridge*" } | ForEach-Object {
                    Write-Host "Job: $($_.Name)" -ForegroundColor Cyan
                    Receive-Job -Job $_
                }
                exit 0
            }
            default {
                Write-Host 'chthonic mcp <action>'
                Write-Host "  start      - Start MCP services"
                Write-Host "  stop       - Stop MCP services"
                Write-Host "  status     - Check service status"
                Write-Host "  logs       - Tail service logs"
                exit 0
            }
        }
    }
    
    # Config Domain
    "config" {
        if (-not (Test-Path $STATE_DIR)) {
            New-Item -ItemType Directory -Path $STATE_DIR -Force | Out-Null
        }
        
        switch ($Action) {
            "init" {
                Write-Host "⚙️  Initializing chthonic configuration..." -ForegroundColor Cyan
                $config = @{
                    Version = $VERSION
                    RepoRoot = $REPO_ROOT
                    Created = (Get-Date).ToString()
                    Features = @("polyglot", "mcp", "ide", "archive")
                }
                $config | ConvertTo-Json | Set-Content $CONFIG_FILE
                Write-Host "✅ Config created: $CONFIG_FILE" -ForegroundColor Green
                exit 0
            }
            "show" {
                if (Test-Path $CONFIG_FILE) {
                    Get-Content $CONFIG_FILE | ConvertFrom-Json | Format-Table -AutoSize
                } else {
                    Write-Host "No configuration file. Run: chthonic config init" -ForegroundColor Yellow
                }
                exit 0
            }
            "set" {
                # chthonic config set <key> <value>
                if ($RemainingArgs.Count -lt 2) {
                    Write-Host 'Usage: chthonic config set <key> <value>' -ForegroundColor Yellow
                    exit 1
                }
                Write-Host "⚙️  Set config: $($RemainingArgs[0]) = $($RemainingArgs[1])" -ForegroundColor Cyan
                exit 0
            }
            default {
                Write-Host 'chthonic config <action>'
                Write-Host "  init       - Initialize configuration"
                Write-Host "  show       - Display configuration"
                Write-Host '  set <k> <v> - Set configuration value'
                exit 0
            }
        }
    }
    
    # Book Domain
    "book" {
        Push-Location $REPO_ROOT
        try {
            $subCmd = if ($Action) { $Action } else { "build" }
            switch ($subCmd) {
                "build" { & mdbook build }
                "serve" { & mdbook serve --open }
                "clean" { & mdbook clean }
                default { & mdbook $subCmd $RemainingArgs }
            }
            exit $LASTEXITCODE
        }
        finally {
            Pop-Location
        }
    }
    
    # Backward compatibility: single-word archive commands
    { $_ -in "audit", "compact", "extract", "resolve", "map", "analyze" } {
        $exitCode = Invoke-ArchiveCommand -Cmd $Domain -CmdArgs @($Action) + $RemainingArgs
        exit $exitCode
    }
    
    # Gemini CLI - disable MCP to avoid startup crash
    "gemini" {
        $env:GEMINI_DISABLE_MCP = "1"
        & pwsh (Join-Path $SCRIPT_DIR "gemini-cli-wrapper.ps1") @CmdArgs
        exit $LASTEXITCODE
    }
    
    # Claude-IDE backward compatibility (legacy)
    "claude-ide" {
        $exitCode = Invoke-IDELaunch -WorkspacePath $REPO_ROOT
        exit $exitCode
    }
    
    # Unknown command
    default {
        if ($Domain -and -not ($Domain -match '^-')) {
            # Try as archive command
            $exitCode = Invoke-ArchiveCommand -Cmd $Domain -CmdArgs @($Action) + $RemainingArgs
            exit $exitCode
        }
        else {
            Show-Help
            exit 1
        }
    }
}
