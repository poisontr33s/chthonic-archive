#!/usr/bin/env pwsh

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: chthonic.ps1
# ║ Module: Unified polyglot CLI router
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: INFRASTRUCTURE
# ║ Semantic ID: SCRIPT_CHTHONIC_V1
# ║ Purpose: Unified META-CLI for polyglot tooling and repo operations
# ║ Exports: (none)
# ║ Flags/Modes: -Command, -CmdArgs, -Quiet, -Json
# ║ Cross-References: (none)
# ╚════════════════════════════════════════════════════════════════════════════

param(
    [Parameter(Position = 0)]
    [string]$Command,
    
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CmdArgs,
    
    [switch]$Quiet,
    [switch]$Json
)

$VERSION = "3.2.0"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$REPO_ROOT = Split-Path -Parent $SCRIPT_DIR
$LIB_DIR = Join-Path $SCRIPT_DIR "lib"
$STATE_DIR = Join-Path $env:USERPROFILE ".chthonic"
$CONFIG_FILE = Join-Path $STATE_DIR "config.json"
$SERVICES_FILE = Join-Path $STATE_DIR "services.json"

# ═══════════════════════════════════════════════════════════════════════════════
# POLYGLOT PATHS - ALL GLOBAL NATIVE INSTALLATIONS (Win11)
# ═══════════════════════════════════════════════════════════════════════════════

# Resolve rv-managed Ruby bin directory (highest installed version).
function Get-RvRubyBinDir {
    $rvRubies = Join-Path $env:APPDATA "rv\rubies"
    if (-not (Test-Path $rvRubies)) { return $null }

    $latest = Get-ChildItem $rvRubies -Directory |
        Sort-Object Name -Descending |
        Select-Object -First 1
    if ($latest) {
        $bin = Join-Path $latest.FullName "bin"
        if (Test-Path $bin) { return $bin }
    }
    return $null
}

# Resolve the best available RubyInstaller DevKit root (for MSYS2/UCRT64 toolchain).
# Note: rv manages Ruby versions; RubyInstaller provides the DevKit (gcc, make, etc.).
function Get-RubyDevKitRoot {
    $devkitRoots = @(
        "C:\Ruby40-x64",
        "D:\Ruby40-x64",
        "C:\Ruby35-x64",
        "D:\Ruby35-x64"
    )

    foreach ($root in $devkitRoots) {
        if (Test-Path (Join-Path $root "msys64\ucrt64\bin\gcc.exe")) {
            return $root
        }
    }

    return $null
}

function Get-DevKitPaths {
    $root = Get-RubyDevKitRoot
    if (-not $root) { return @() }

    return @(
        (Join-Path $root "msys64\ucrt64\bin"),
        (Join-Path $root "msys64\usr\bin")
    )
}

$rvRubyBin = Get-RvRubyBinDir
$devkitPaths = Get-DevKitPaths

# Default polyglot paths (fallback when config.json is missing)
$defaultPolyglotPaths = @(
    # Native user binaries (Claude native installer, uv tools)
    "$env:USERPROFILE\.local\bin",

    # Bun (JS/TS runtime + Biome)
    "$env:USERPROFILE\.bun\bin",

    # Rust (rustup managed) + Cargo tools (includes rv, rvw)
    "$env:USERPROFILE\.cargo\bin",

    # Go (goup-managed, user-space)
    "$env:USERPROFILE\.goup\current\bin",
    "$env:USERPROFILE\go\bin"
)

# rv-managed Ruby (exclusive ownership per ANNO manifest)
if ($rvRubyBin) {
    $defaultPolyglotPaths += $rvRubyBin
}

# DevKit toolchain (gcc, make) from RubyInstaller's MSYS2
$defaultPolyglotPaths += $devkitPaths

# Git
$defaultPolyglotPaths += @(
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

function Show-StatusBanner {
    # Compact one-liner version probes grouped by manager
    $W = "White"; $C = "Cyan"; $D = "DarkGray"; $R = "Red"
    function ver($cmd) { try { $v = (& $cmd 2>$null); if ($v) { return ($v -split "`n")[0] } } catch {}; return $null }

    Write-Host "CHTHONIC v$VERSION" -ForegroundColor $C -NoNewline
    Write-Host " | " -ForegroundColor $D -NoNewline
    Write-Host "$REPO_ROOT" -ForegroundColor $W
    Write-Host ("="*72) -ForegroundColor $D

    # rv -> Ruby
    $rubyVer = ver { ruby -e "print RUBY_VERSION" }
    Write-Host "  rv    " -NoNewline -ForegroundColor $C
    if ($rubyVer) { Write-Host "ruby $rubyVer" -NoNewline -ForegroundColor $W } else { Write-Host "ruby ?" -NoNewline -ForegroundColor $R }

    # DevKit (gcc)
    $gccVer = ver { gcc -dumpfullversion }
    if ($gccVer) { Write-Host "  gcc $gccVer" -NoNewline -ForegroundColor $D }
    Write-Host ""

    # uv -> Python
    $pyVer = ver { uv run python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" }
    $uvVer = ver { uv --version }; if ($uvVer -match '(\d+\.\d+\.\d+)') { $uvVer = $matches[1] } else { $uvVer = $null }
    $ruffVer = ver { ruff --version }; if ($ruffVer -match '(\d+\.\d+\.\d+)') { $ruffVer = $matches[1] } else { $ruffVer = $null }
    Write-Host "  uv    " -NoNewline -ForegroundColor $C
    if ($pyVer) { Write-Host "python $pyVer" -NoNewline -ForegroundColor $W } else { Write-Host "python ?" -NoNewline -ForegroundColor $R }
    if ($uvVer) { Write-Host "  uv $uvVer" -NoNewline -ForegroundColor $D }
    if ($ruffVer) { Write-Host "  ruff $ruffVer" -NoNewline -ForegroundColor $D }
    Write-Host ""

    # bun -> JS/TS
    $bunVer = ver { bun --version }
    $biomeVer = ver { biome --version }; if ($biomeVer) { $biomeVer = $biomeVer -replace 'Version:\s*','' }
    Write-Host "  bun   " -NoNewline -ForegroundColor $C
    if ($bunVer) { Write-Host "bun $bunVer" -NoNewline -ForegroundColor $W } else { Write-Host "bun ?" -NoNewline -ForegroundColor $R }
    if ($biomeVer) { Write-Host "  biome $biomeVer" -NoNewline -ForegroundColor $D }
    Write-Host "  (sql, react, test, bundle built-in)" -ForegroundColor $D

    # rustup -> Rust
    $rustVer = ver { rustc -V }; if ($rustVer) { $rustVer = ($rustVer -split ' ')[1] }
    Write-Host "  rust  " -NoNewline -ForegroundColor $C
    if ($rustVer) { Write-Host "rustc $rustVer" -NoNewline -ForegroundColor $W } else { Write-Host "rustc ?" -NoNewline -ForegroundColor $R }
    $mdbookVer = ver { mdbook --version }; if ($mdbookVer -match '(\d+\.\d+\.\d+)') { $mdbookVer = $matches[1] } else { $mdbookVer = $null }
    if ($mdbookVer) { Write-Host "  mdbook $mdbookVer" -NoNewline -ForegroundColor $D }
    Write-Host ""

    # Go (try PATH, then goup)
    $goVer = ver { go version }
    if (-not $goVer) { $goupGo = Join-Path $env:USERPROFILE ".goup\current\bin\go.exe"; if (Test-Path $goupGo) { $goVer = ver { & $goupGo version } } }
    if ($goVer -match 'go(\d+\.\d+\.\d+)') { $goVer = $matches[1] } else { $goVer = $null }
    Write-Host "  go      " -NoNewline -ForegroundColor $C
    if ($goVer) { Write-Host "go $goVer" -ForegroundColor $W } else { Write-Host "go ?" -ForegroundColor $R }

    # Infra line
    $gitVer = ver { git --version }; if ($gitVer) { $gitVer = ($gitVer -replace 'git version\s*','') -replace '\.windows.*','' }
    $vulkanVer = if ($env:VULKAN_SDK -match '(\d+\.\d+\.\d+)') { $matches[1] } else { $null }
    Write-Host "  sys   " -NoNewline -ForegroundColor $C
    Write-Host "git $gitVer" -NoNewline -ForegroundColor $D
    if ($vulkanVer) { Write-Host "  vulkan $vulkanVer" -NoNewline -ForegroundColor $D }
    Write-Host ""
    Write-Host ("="*72) -ForegroundColor $D
}

function Show-Help {
@"

Usage: chthonic [--version] [--help] <domain> [<action>] [<args>]

  env [--quiet]           Activate polyglot environment
  status [--json]         Show all tool versions (verbose)
  doctor [--fix] [--json] Check versions + EOL via endoflife.date; --fix upgrades
  doctor --dry-run        Simulate --fix without executing anything
  doctor --origins        Show install methodology per tool (path + origin)
  detect                  Detect IDE and environment context

  ide launch|detect|reset IDE management
  mcp start|stop|status   MCP + bridge services
  config init|show|set    Configuration (~/.chthonic/)

  audit|compact|extract|resolve|map|analyze  Archive tools (uv run)
  book [serve|build]      mdBook documentation

  --version               Show version
  --help                  Show this help (without status banner)
  --quiet                 Suppress output

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
        return
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
    
    # Go environment (goup-managed)
    $goupCurrent = Join-Path $env:USERPROFILE ".goup\current"
    if (Test-Path $goupCurrent) { $env:GOROOT = $goupCurrent }
    $env:GOPATH = "$env:USERPROFILE\go"
    
    # Ruby DevKit (MSYS2 toolchain from RubyInstaller, used by rv's Ruby for native gems)
    $devkitRoot = Get-RubyDevKitRoot
    if ($devkitRoot) {
        $msys2Root = Join-Path $devkitRoot "msys64"
        if (Test-Path $msys2Root) {
            $env:RI_DEVKIT = $msys2Root
            $env:RIDK_PREFIX = $msys2Root
            $env:MSYS2_HOME = $msys2Root
        }
    }
    
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
# DOCTOR - endoflife.date API integration
# ═══════════════════════════════════════════════════════════════════════════════

function Get-EndOfLifeData {
    param([string]$Product)
    try {
        return Invoke-RestMethod -Uri "https://endoflife.date/api/$Product.json" -TimeoutSec 5 -ErrorAction Stop
    } catch { return $null }
}

function Get-InstalledVersion {
    param([string]$Tool)
    try {
        switch ($Tool) {
            "ruby"       { $v = ruby -e "print RUBY_VERSION" 2>$null; return $v }
            "python"     { return (uv run python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>$null) }
            "bun"        { return (bun --version 2>$null) }
            "rust"       { $v = rustc -V 2>$null; if ($v -match '(\d+\.\d+\.\d+)') { return $matches[1] }; return $null }
            "go"         {
                # Try PATH first, then goup-managed Go
                $v = try { go version 2>$null } catch { $null }
                if (-not $v) {
                    $goupGo = Join-Path $env:USERPROFILE ".goup\current\bin\go.exe"
                    if (Test-Path $goupGo) { $v = & $goupGo version 2>$null }
                }
                if ($v -match 'go(\d+\.\d+\.\d+)') { return $matches[1] }; return $null
            }
            "nodejs"     { $v = node --version 2>$null; if ($v -match '(\d+\.\d+\.\d+)') { return $matches[1] }; return $null }
            "postgresql" {
                $v = psql --version 2>$null; if ($v -match '(\d+\.\d+)') { return $matches[1] }; return $null
            }
            "dotnet"     { $v = dotnet --version 2>$null; return $v }
            "windows"    {
                $build = [System.Environment]::OSVersion.Version
                return "$($build.Major).$($build.Minor).$($build.Build)"
            }
            default      { return $null }
        }
    } catch { return $null }
}

function Compare-Versions {
    param([string]$Installed, [string]$Latest)
    if (-not $Installed -or -not $Latest) { return $null }
    try {
        $i = [version]$Installed
        $l = [version]$Latest
        return $i.CompareTo($l)
    } catch { return $null }
}

# Fix command map: tool -> { Upgrade (tool present), Install (tool missing) }
# All vectors use native installers — zero winget dependency.
# Pin policy: install + pin in one atomic operation where supported.
#   Ruby/Python: explicit pin (rvw ruby pin / uv python pin)
#   Go/Rust/Bun: implicit pin (goup install auto-defaults, rustup stays stable, bun is single binary)
$global:DoctorFixMap = @{
    ruby   = @{
        Upgrade = { param($ver) rvw ruby install $ver; rvw ruby pin $ver }; UpgradeDesc = "rvw ruby install && pin"
        Install = { param($ver) cargo install rv; rvw ruby install $ver; rvw ruby pin $ver }; InstallDesc = "cargo install rv && rvw ruby install && pin"
    }
    python = @{
        Upgrade = {
            param($ver)
            uv python install $ver
            uv python pin $ver
        }; UpgradeDesc = "uv python install && uv python pin"
        Install = {
            param($ver)
            if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
                irm https://astral.sh/uv/install.ps1 | iex
            }
            uv python install $ver
            uv python pin $ver
        }; InstallDesc = "install uv (if missing) && uv python install && uv python pin"
    }
    bun    = @{
        Upgrade = { bun upgrade }; UpgradeDesc = "bun upgrade"
        Install = { irm bun.sh/install.ps1 | iex }; InstallDesc = "irm bun.sh/install.ps1 | iex"
    }
    rust   = @{
        Upgrade = { rustup update stable }; UpgradeDesc = "rustup update stable"
        Install = { irm https://sh.rustup.rs -useb | iex }; InstallDesc = "irm rustup.rs | iex"
    }
    go     = @{
        Upgrade = { param($ver) goup install "=$ver" }; UpgradeDesc = "goup install"
        Install = { goup install stable }; InstallDesc = "goup install stable"
    }
}

# Origin map: where each tool actually lives and how it was installed.
# Resolved dynamically from Get-Command to stay accurate.
function Show-Origins {
    $W = "White"; $C = "Cyan"; $D = "DarkGray"; $R = "Red"; $G = "Green"

    Write-Host ""
    Write-Host "CHTHONIC ORIGINS v$VERSION" -ForegroundColor $C
    Write-Host ("="*72) -ForegroundColor $D

    # Core ANNO-managed tools
    $tools = @(
        @{ Name = "ruby";    Cmd = "ruby";    Method = "rv (cargo install rv)";     Ecosystem = "cargo" },
        @{ Name = "python";  Cmd = "uv";      Method = "irm astral.sh/uv";          Ecosystem = "uv" },
        @{ Name = "bun";     Cmd = "bun";     Method = "irm bun.sh";                Ecosystem = "bun" },
        @{ Name = "rust";    Cmd = "rustc";   Method = "rustup (irm rustup.rs)";     Ecosystem = "cargo" },
        @{ Name = "go";      Cmd = "go";      Method = "goup (cargo install goup-rs)"; Ecosystem = "cargo" }
    )

    # Secondary tools
    $secondary = @(
        @{ Name = "goup";    Cmd = "goup";    Method = "GH release binary"; Ecosystem = "cargo" },
        @{ Name = "biome";   Cmd = "biome";   Method = "bun add -g";    Ecosystem = "bun" },
        @{ Name = "ruff";    Cmd = "ruff";    Method = "uv tool";       Ecosystem = "uv" },
        @{ Name = "cmake";   Cmd = "cmake";   Method = "uv tool";       Ecosystem = "uv" },
        @{ Name = "ninja";   Cmd = "ninja";   Method = "uv tool";       Ecosystem = "uv" },
        @{ Name = "mdbook";  Cmd = "mdbook";  Method = "cargo install"; Ecosystem = "cargo" },
        @{ Name = "git";     Cmd = "git";     Method = "native installer"; Ecosystem = "system" },
        @{ Name = "gcc";     Cmd = "gcc";     Method = "MSYS2 (RubyInstaller)"; Ecosystem = "system" },
        @{ Name = "glslc";   Cmd = "glslc";   Method = "Vulkan SDK";    Ecosystem = "system" },
        @{ Name = "claude";  Cmd = "claude";  Method = "standalone";    Ecosystem = "uv" }
    )

    $ecoColors = @{ "uv" = "Magenta"; "bun" = "Yellow"; "cargo" = "Red"; "system" = "DarkGray" }

    foreach ($section in @(@{ Label = "CORE"; Items = $tools }, @{ Label = "TOOLS"; Items = $secondary })) {
        foreach ($t in $section.Items) {
            $path = try { (Get-Command $t.Cmd -ErrorAction Stop).Source } catch { $null }
            # Fallback: goup-managed Go when not in PATH
            if (-not $path -and $t.Name -eq "go") {
                $goupGo = Join-Path $env:USERPROFILE ".goup\current\bin\go.exe"
                if (Test-Path $goupGo) { $path = $goupGo }
            }
            $short = if ($path) {
                $path -replace [regex]::Escape($env:USERPROFILE), '~' -replace [regex]::Escape($env:APPDATA), '%APPDATA%'
            } else { "(not found)" }

            $nameStr = $t.Name.PadRight(10)
            $pathStr = $short.PadRight(44)
            $ecoColor = if ($ecoColors[$t.Ecosystem]) { $ecoColors[$t.Ecosystem] } else { $D }

            Write-Host "  $nameStr" -NoNewline -ForegroundColor $W
            if ($path) {
                Write-Host "$pathStr" -NoNewline -ForegroundColor $D
            } else {
                Write-Host "$pathStr" -NoNewline -ForegroundColor $R
            }
            Write-Host " $($t.Method)" -ForegroundColor $ecoColor
        }
        if ($section.Label -eq "CORE") {
            Write-Host "  $("-"*68)" -ForegroundColor $D
        }
    }

    # Directory taxonomy
    Write-Host ("="*72) -ForegroundColor $D
    $dirs = @(
        @{ Path = "~/.local/bin/";   Label = "uv ecosystem (uv, ruff, cmake, ninja, claude)" },
        @{ Path = "~/.bun/bin/";     Label = "bun ecosystem (bun, biome, codex, gemini)" },
        @{ Path = "~/.cargo/bin/";   Label = "cargo ecosystem (rustc, rustup, mdbook, rv, goup)" },
        @{ Path = "~/.goup/";        Label = "goup-managed Go versions (go.dev source)" },
        @{ Path = "%APPDATA%\rv\";   Label = "rv-managed Ruby versions" }
    )
    foreach ($dir in $dirs) {
        Write-Host "  $($dir.Path.PadRight(20))" -NoNewline -ForegroundColor $C
        Write-Host $dir.Label -ForegroundColor $D
    }
    Write-Host ("="*72) -ForegroundColor $D
    Write-Host ""
}

function Invoke-Doctor {
    param([switch]$Json, [switch]$Fix, [switch]$DryRun, [switch]$Origins)

    if ($Origins) { Show-Origins; return }

    # Tools: [display, endoflife.date product, ANNO manager, optional=skips if not installed]
    $checks = @(
        @{ Name = "ruby";       Product = "ruby";       Manager = "rv" },
        @{ Name = "python";     Product = "python";     Manager = "uv" },
        @{ Name = "bun";        Product = "bun";        Manager = "bun" },
        @{ Name = "rust";       Product = "rust";       Manager = "rustup" },
        @{ Name = "go";         Product = "go";         Manager = "goup" },
        @{ Name = "nodejs";     Product = "nodejs";     Manager = "bun"; Optional = $true },
        @{ Name = "postgresql";  Product = "postgresql"; Manager = "system"; Optional = $true },
        @{ Name = "dotnet";     Product = "dotnet";     Manager = "system"; Optional = $true }
    )

    $results = @()
    $fixable = @()

    Write-Host ""
    Write-Host "CHTHONIC DOCTOR v$VERSION" -ForegroundColor Cyan -NoNewline
    Write-Host " | endoflife.date" -ForegroundColor DarkGray
    Write-Host ("="*72) -ForegroundColor DarkGray

    foreach ($check in $checks) {
        $installed = Get-InstalledVersion $check.Name

        # Skip optional tools that aren't installed
        if ($check.Optional -and -not $installed) { continue }

        $eolData = Get-EndOfLifeData $check.Product

        $latest = $null
        $eolDate = $null
        $badge = ""
        $fixTarget = $null

        if ($eolData -and $eolData.Count -gt 0) {
            $installedCycle = $null
            $latestCycle = $eolData[0]

            if ($installed -match '^(\d+\.\d+)') {
                $installedMajorMinor = $matches[1]
                $installedCycle = $eolData | Where-Object {
                    $installed -like "$($_.cycle)*" -or $installedMajorMinor -eq $_.cycle
                } | Select-Object -First 1
            }

            $latest = $latestCycle.latest
            $latestCycleVer = $latestCycle.cycle

            if (-not $installedCycle) { $installedCycle = $latestCycle }

            # EOL check
            $eolDate = $installedCycle.eol
            $isEol = $false
            $daysLeft = $null
            if ($eolDate -and $eolDate -ne $false -and $eolDate -is [string]) {
                try {
                    $eolParsed = [datetime]::Parse($eolDate)
                    $isEol = $eolParsed -lt (Get-Date)
                    $daysLeft = ($eolParsed - (Get-Date)).Days
                } catch {}
            }

            $cmp = Compare-Versions $installed $installedCycle.latest
            $cmpGlobal = Compare-Versions $installed $latest

            if ($isEol) {
                $badge = "EOL"
                $fixTarget = $latest
            } elseif ($daysLeft -and $daysLeft -lt 180) {
                $badge = "EOL in ${daysLeft}d"
                $fixTarget = $latest
            } elseif ($cmpGlobal -and $cmpGlobal -lt 0) {
                if ($installed -and $installedMajorMinor -ne $latestCycleVer) {
                    $badge = "upgrade $latestCycleVer"
                    $fixTarget = $latest
                } elseif ($cmp -and $cmp -lt 0) {
                    $badge = "patch $($installedCycle.latest)"
                    $fixTarget = $installedCycle.latest
                } else {
                    $badge = "current"
                }
            } else {
                $badge = "current"
            }
        } else {
            $badge = "no API data"
        }

        # Display line
        $mgr = $check.Manager.PadRight(6)
        $name = $check.Name.PadRight(10)
        $instStr = if ($installed) { $installed.PadRight(12) } else { "(missing)".PadRight(12) }

        Write-Host "  $mgr " -NoNewline -ForegroundColor Cyan
        Write-Host "$name " -NoNewline -ForegroundColor White
        Write-Host "$instStr " -NoNewline -ForegroundColor White

        switch -Wildcard ($badge) {
            "current"   { Write-Host $badge -ForegroundColor Green }
            "EOL"       { Write-Host "$badge  (eol: $eolDate)" -NoNewline -ForegroundColor Red }
            "EOL in*"   { Write-Host "$badge  (eol: $eolDate)" -NoNewline -ForegroundColor Yellow }
            "patch*"    { Write-Host $badge -NoNewline -ForegroundColor Yellow }
            "upgrade*"  { Write-Host "$badge available (latest: $latest)" -NoNewline -ForegroundColor Yellow }
            default     { Write-Host $badge -ForegroundColor DarkGray }
        }

        # Show fix/install command hint
        $fixInfo = $global:DoctorFixMap[$check.Name]
        $isMissing = -not $installed
        if ($isMissing -and $fixInfo -and $fixInfo.InstallDesc) {
            Write-Host "  -> $($fixInfo.InstallDesc)" -ForegroundColor DarkGray
            $fixable += @{ Tool = $check.Name; Target = $latest; Mode = "install"; FixInfo = $fixInfo }
        } elseif ($fixTarget -and $fixInfo) {
            Write-Host "  -> $($fixInfo.UpgradeDesc) $fixTarget" -ForegroundColor DarkGray
            $fixable += @{ Tool = $check.Name; Target = $fixTarget; Mode = "upgrade"; FixInfo = $fixInfo }
        } elseif ($badge -ne "current" -and $badge -ne "no API data") {
            Write-Host ""
        }
    }

    Write-Host ("="*72) -ForegroundColor DarkGray
    $currentCount = ($results.Count -gt 0) ? ($results | Where-Object { $_.status -eq "current" }).Count : (($checks | ForEach-Object { $_.Name }) | Where-Object { $_ -notin ($fixable.Tool) }).Count
    $checkedCount = $checks.Count - ($checks | Where-Object { $_.Optional -and -not (Get-InstalledVersion $_.Name) }).Count
    $fixCount = $fixable.Count
    $okCount = $checkedCount - $fixCount
    Write-Host "  $okCount/$checkedCount current" -NoNewline -ForegroundColor $(if ($fixCount -eq 0) { "Green" } else { "Yellow" })
    if ($fixCount -gt 0) {
        Write-Host "  |  $fixCount fixable" -NoNewline -ForegroundColor Yellow
        Write-Host "  (--dry-run | --fix)" -NoNewline -ForegroundColor DarkGray
    }
    Write-Host "  | endoflife.date" -ForegroundColor DarkGray
    Write-Host ""

    # --fix / --dry-run mode: execute or simulate upgrades and installs
    if (($Fix -or $DryRun) -and $fixable.Count -gt 0) {
        if ($DryRun) {
            Write-Host "DRY RUN — no changes will be made" -ForegroundColor Magenta
        } else {
            Write-Host "APPLYING FIXES" -ForegroundColor Cyan
        }
        Write-Host ("="*72) -ForegroundColor DarkGray
        foreach ($f in $fixable) {
            if ($f.Mode -eq "install") {
                $desc = "$($f.FixInfo.InstallDesc) $($f.Target)"
                Write-Host "  $($f.Tool): $desc" -ForegroundColor Yellow
                if ($DryRun) {
                    Write-Host "  -> would install (skipped)" -ForegroundColor Magenta
                } else {
                    try {
                        & $f.FixInfo.Install $f.Target
                        if ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE) {
                            Write-Host "  -> installed" -ForegroundColor Green
                        } else {
                            Write-Host "  -> failed (exit $LASTEXITCODE)" -ForegroundColor Red
                        }
                    } catch {
                        Write-Host "  -> error: $_" -ForegroundColor Red
                    }
                }
            } else {
                $desc = "$($f.FixInfo.UpgradeDesc) $($f.Target)"
                Write-Host "  $($f.Tool): $desc" -ForegroundColor Yellow
                if ($DryRun) {
                    Write-Host "  -> would upgrade (skipped)" -ForegroundColor Magenta
                } else {
                    try {
                        & $f.FixInfo.Upgrade $f.Target
                        if ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE) {
                            Write-Host "  -> done" -ForegroundColor Green
                        } else {
                            Write-Host "  -> failed (exit $LASTEXITCODE)" -ForegroundColor Red
                        }
                    } catch {
                        Write-Host "  -> error: $_" -ForegroundColor Red
                    }
                }
            }
        }
        Write-Host ("="*72) -ForegroundColor DarkGray
        Write-Host ""
    } elseif ($Fix -or $DryRun) {
        Write-Host "Nothing to fix — all current." -ForegroundColor Green
        Write-Host ""
    }

    if ($Json) {
        $jsonResults = $checks | ForEach-Object {
            $inst = Get-InstalledVersion $_.Name
            if ($_.Optional -and -not $inst) { return }
            @{ tool = $_.Name; manager = $_.Manager; installed = $inst }
        }
        Write-Output (ConvertTo-Json $jsonResults -Depth 5)
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN DISPATCH - Meta CLI (Domain/Action Model)
# ═══════════════════════════════════════════════════════════════════════════════

# Parse domain/action if provided
$Domain = $Command
$Action = if ($CmdArgs.Count -gt 0) { $CmdArgs[0] } else { $null }
$RemainingArgs = if ($CmdArgs.Count -gt 1) { $CmdArgs[1..($CmdArgs.Count-1)] } else { @() }
$AllArgs = @()
if ($Action) { $AllArgs += $Action }
if ($RemainingArgs) { $AllArgs += $RemainingArgs }
$HasJsonFlag = $Json -or ($AllArgs -contains "--json")
$HasQuietFlag = $Quiet -or ($AllArgs -contains "--quiet") -or ($AllArgs -contains "-q")

# Top-level commands (backward compatible)
switch ($Domain) {
    "--version" {
        Write-Host "chthonic v$VERSION"
        exit 0
    }
    { $_ -in "--help", "-h", "help" } {
        Show-Help
        exit 0
    }
    { $_ -in $null, "" } {
        Show-StatusBanner
        Show-Help
        exit 0
    }
    
    # Environment Domain
    "env" {
        $quietFlag = $HasQuietFlag
        Invoke-PolyglotActivation -Quiet:$quietFlag
        exit 0
    }
    "status" {
        Show-PolyglotStatus -Json:$HasJsonFlag
        exit 0
    }
    "doctor" {
        $fixFlag = ($AllArgs -contains "--fix") -or ($AllArgs -contains "-f")
        $dryRunFlag = $AllArgs -contains "--dry-run"
        $jsonFlag = $HasJsonFlag
        $originsFlag = $AllArgs -contains "--origins"
        Invoke-Doctor -Json:$jsonFlag -Fix:$fixFlag -DryRun:$dryRunFlag -Origins:$originsFlag
        exit 0
    }
    "detect" {
        if ($HasJsonFlag) {
            Invoke-IDEDetect -Json:$true
            exit 0
        }
        $exitCode = Invoke-IDEDetect -Json:$false
        exit $exitCode
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
                if ($HasJsonFlag) {
                    Invoke-IDEDetect -Json:$true
                    exit 0
                }
                $exitCode = Invoke-IDEDetect -Json:$false
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
                if ($HasJsonFlag) {
                    Invoke-MCPStatus -Json:$true
                    exit 0
                }
                $exitCode = Invoke-MCPStatus -Json:$false
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
