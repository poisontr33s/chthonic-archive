#!/usr/bin/env pwsh
# @SID: FORGE_IDE_DETECTION_V1
# 🔥💀⚓ Claude Code IDE Detection & Setup Diagnostic

Write-Host "
╔════════════════════════════════════════════════════════════════════════════
║  Claude Code IDE Detection & Extension Check
╚════════════════════════════════════════════════════════════════════════════
" -ForegroundColor Cyan

# 1. Find VS Code installations
Write-Host "`n🔍 Searching for VS Code installations..." -ForegroundColor Yellow

$vscodeLocations = @(
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Microsoft VS Code",
    "C:\Program Files\Microsoft VS Code",
    "C:\Program Files (x86)\Microsoft VS Code",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Microsoft VS Code Insiders"
)

$foundIDEs = @()

foreach ($location in $vscodeLocations) {
    if (Test-Path "$location\Code.exe") {
        $foundIDEs += @{
            Name = "VS Code"
            Path = $location
            Exe = "$location\Code.exe"
        }
        Write-Host "✅ Found: VS Code at $location" -ForegroundColor Green
    }
    elseif (Test-Path "$location\Code - Insiders.exe") {
        $foundIDEs += @{
            Name = "VS Code Insiders"
            Path = $location
            Exe = "$location\Code - Insiders.exe"
        }
        Write-Host "✅ Found: VS Code Insiders at $location" -ForegroundColor Green
    }
}

# Check PATH
$codeCmd = Get-Command code -ErrorAction SilentlyContinue
$codeInsidersCmd = Get-Command code-insiders -ErrorAction SilentlyContinue

if ($codeInsidersCmd) {
    Write-Host "✅ 'code-insiders' command available: $($codeInsidersCmd.Source)" -ForegroundColor Green
    $foundIDEs += @{
        Name = "VS Code Insiders (PATH)"
        Path = Split-Path $codeInsidersCmd.Source
        Exe = $codeInsidersCmd.Source
        Command = "code-insiders"
    }
}
if ($codeCmd) {
    Write-Host "✅ 'code' command available: $($codeCmd.Source)" -ForegroundColor Green
    $foundIDEs += @{
        Name = "VS Code (PATH)"
        Path = Split-Path $codeCmd.Source
        Exe = $codeCmd.Source
        Command = "code"
    }
}

if ($foundIDEs.Count -eq 0) {
    Write-Host "❌ No VS Code installation found" -ForegroundColor Red
    Write-Host "   Install from: https://code.visualstudio.com" -ForegroundColor Yellow
    exit 1
}

# 2. Check for Claude Code extension
Write-Host "`n📦 Checking for Claude Code extensions..." -ForegroundColor Yellow

$extensionsPath = "$env:APPDATA\Code - Insiders\User\globalStorage\github.copilot-chat"
if (Test-Path $extensionsPath) {
    Write-Host "✅ Found copilot extensions directory at: $extensionsPath" -ForegroundColor Green

    # List installed extensions
    $extensions = @(
        "$env:APPDATA\Code - Insiders\extensions"
    )

    foreach ($extDir in $extensions) {
        if (Test-Path $extDir) {
            $claudeExts = Get-ChildItem $extDir -Filter "*claude*" -ErrorAction SilentlyContinue
            if ($claudeExts) {
                Write-Host "✅ Claude-related extensions found:" -ForegroundColor Green
                foreach ($ext in $claudeExts) {
                    Write-Host "   - $($ext.Name)" -ForegroundColor DarkGreen
                }
            }
        }
    }
} else {
    Write-Host "⚠️  No copilot extensions directory found" -ForegroundColor Yellow
    Write-Host "   Extensions may not be installed yet" -ForegroundColor DarkGray
}

# 3. Check if VS Code is currently running
Write-Host "`n🔄 Checking if VS Code is running..." -ForegroundColor Yellow

$runningVSCode = Get-Process code* -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match "^code" }

if ($runningVSCode) {
    Write-Host "✅ VS Code is running:" -ForegroundColor Green
    foreach ($proc in $runningVSCode) {
        Write-Host "   - $($proc.Name) (PID: $($proc.Id))" -ForegroundColor DarkGreen
    }
} else {
    Write-Host "⚠️  VS Code is not currently running" -ForegroundColor Yellow
    Write-Host "   Start VS Code before launching Claude Code IDE" -ForegroundColor DarkGray
}

# 4. Check IP/Port accessibility
Write-Host "`n🔗 Checking network accessibility..." -ForegroundColor Yellow

try {
    $tcpTest = Test-NetConnection localhost -Port 9999 -ErrorAction SilentlyContinue -WarningAction SilentlyContinue
    if ($tcpTest.TcpTestSucceeded) {
        Write-Host "✅ Port 9999 is accessible (potential IDE server)" -ForegroundColor Green
    } else {
        Write-Host "ℹ️  Port 9999 not open (normal on first launch)" -ForegroundColor DarkCyan
    }
} catch {
    Write-Host "ℹ️  Network check not available" -ForegroundColor DarkGray
}

# 5. Provide fix recommendations
Write-Host "
╔════════════════════════════════════════════════════════════════════════════
║  FIX CHECKLIST
╚════════════════════════════════════════════════════════════════════════════
" -ForegroundColor Cyan

$fixes = @(
    @{
        Check = "VS Code installed"
        Status = if ($foundIDEs.Count -gt 0) { "✅" } else { "❌" }
        Fix = "Download from https://code.visualstudio.com"
    },
    @{
        Check = "VS Code running"
        Status = if ($runningVSCode) { "✅" } else { "⚠️ " }
        Fix = "Start VS Code or VS Code Insiders"
    },
    @{
        Check = "Claude Code extension"
        Status = if (Test-Path "$env:APPDATA\Code - Insiders\extensions" ) { "✅" } else { "?" }
        Fix = "Install from Extensions marketplace: @anthropic-ai/claude-code"
    },
    @{
        Check = "ANTHROPIC_API_KEY"
        Status = if ($env:ANTHROPIC_API_KEY) { "✅" } else { "❌" }
        Fix = "Add to .env.local or environment variables"
    }
)

foreach ($check in $fixes) {
    Write-Host "$($check.Status) $($check.Check)" -ForegroundColor $(if ($check.Status -eq "✅") { "Green" } else { "Yellow" })
    if ($check.Status -ne "✅") {
        Write-Host "   → $($check.Fix)" -ForegroundColor DarkGray
    }
}

# 6. Show how to proceed
Write-Host "
╔════════════════════════════════════════════════════════════════════════════
║  HOW TO FIX IDE DETECTION
╚════════════════════════════════════════════════════════════════════════════

1️⃣  Ensure VS Code (or Insiders) is running:
    code-insiders .
    or
    code .

2️⃣  Make sure Claude Code extension is installed:
    - In VS Code: Extensions → Search 'Claude Code'
    - Install: @anthropic-ai/claude-code

3️⃣  Verify API key is set:
   Add to .env.local:
    ANTHROPIC_API_KEY=sk_your_key_here

4️⃣  Launch Claude Code with explicit IDE path:
    bun run scripts/mcp-chthonic-server.ts

5️⃣  Or use the wrapper:
    chthonic claude-ide

6️⃣  Once IDE is detected, you should see:
    ✅ Claude Code IDE Connected
    ✅ Access to: 19 chthonic tools
    ✅ Full polyglot environment context

TROUBLESHOOTING:
- If still no IDE found, restart VS Code completely
- Check that you're in the correct workspace
- Verify the Claude Code extension is enabled
- Run this diagnostic again: pwsh scripts/ide-detection.ps1

" -ForegroundColor Cyan

Write-Host "Diagnostic complete. Ready to launch Claude Code IDE." -ForegroundColor Green

