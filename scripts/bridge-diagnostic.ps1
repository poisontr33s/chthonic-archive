#!/usr/bin/env pwsh
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: bridge-diagnostic.ps1
# ║ Module: Bridge diagnostic
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: DIAGNOSTIC
# ║ Semantic ID: SCRIPT_BRIDGE_DIAGNOSTIC_V1
# ║ Purpose: Diagnose Claude↔Chthonic bridge processes and endpoints
# ║ Exports: (none)
# ║ Flags/Modes: (none)
# ║ Cross-References: scripts/bridge-server.ts
# ╚════════════════════════════════════════════════════════════════════════════

# 🔥💀⚓ Bridge Diagnostic & Test Script

Write-Host "
╔════════════════════════════════════════════════════════════════════════════
║  Claude Code ↔ Chthonic Bridge - Diagnostic
╚════════════════════════════════════════════════════════════════════════════
" -ForegroundColor Cyan

# 1. CHECK if bridge processes are running
Write-Host "`n📊 Checking Bridge Status..." -ForegroundColor Yellow
$bunProc = Get-Process "bun" -ErrorAction SilentlyContinue
if ($bunProc) {
    Write-Host "✅ Bun process found (Bridge may be running)" -ForegroundColor Green
    $bunProc | Select-Object Id, Name, CPU, Memory | Format-Table
} else {
    Write-Host "❌ No Bun process found" -ForegroundColor Red
    Write-Host "   Start with: bun run scripts/bridge-server.ts" -ForegroundColor Yellow
}

# 2. CHECK if port 8888 is listening
Write-Host "`n🔌 Port 8888 Status..." -ForegroundColor Yellow
$netstat = netstat -ano 2>/dev/null | Select-String ":8888" | Select-Object -First 1
if ($netstat) {
    Write-Host "✅ Port 8888 is listening" -ForegroundColor Green
    Write-Host "   $netstat" -ForegroundColor DarkGray
} else {
    Write-Host "❌ Port 8888 is not listening" -ForegroundColor Red
    Write-Host "   Bridge HTTP server is not running" -ForegroundColor Yellow
}

# 3. TEST bridge endpoint (non-blocking)
Write-Host "`n🧪 Testing Bridge Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest "http://localhost:8888/status" `
        -TimeoutSec 2 `
        -ErrorAction Stop

    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Bridge HTTP server is responding" -ForegroundColor Green
        $data = $response.Content | ConvertFrom-Json
        Write-Host "   Version: $($data.version)" -ForegroundColor DarkCyan
        Write-Host "   Port: $($data.port)" -ForegroundColor DarkCyan
        Write-Host "   Root: $($data.chthonic_root)" -ForegroundColor DarkCyan
    } else {
        Write-Host "⚠️  Unexpected status code: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Bridge endpoint not responding" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor DarkGray
}

# 4. CHECK chthonic CLI
Write-Host "`n🔗 Chthonic CLI Check..." -ForegroundColor Yellow
try {
    $result = & chthonic status 2>&1 | Select-Object -First 3
    if ($result) {
        Write-Host "✅ Chthonic CLI is working" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Chthonic CLI returned empty" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Chthonic CLI error..." -ForegroundColor Red
}

# 5. SHOW available files
Write-Host "`n📁 Bridge Implementation Files..." -ForegroundColor Yellow
$files = @(
    "scripts/bridge-server.ts",
    "scripts/claude-chthonic-plugin.ts",
    "scripts/claude-chthonic-bridge.ts",
    "CLAUDE_CODE_BRIDGE_ARCHITECTURE.md"
)

foreach ($file in $files) {
    $path = Join-Path "C:\Users\erdno\chthonic-archive" $file
    if (Test-Path $path) {
        $size = (Get-Item $path).Length
        Write-Host "   ✅ $file ($([Math]::Round($size/1KB))KB)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $file (missing)" -ForegroundColor Red
    }
}

Write-Host "
╔════════════════════════════════════════════════════════════════════════════
║  QUICK START
╚════════════════════════════════════════════════════════════════════════════

1️⃣  Start the Bridge Server:
    bun run scripts/bridge-server.ts

2️⃣  In a new terminal, test it:
    curl http://localhost:8888/status

3️⃣  Execute a chthonic command:
    curl -X POST http://localhost:8888/execute \
      -H 'Content-Type: application/json' \
      -d '{\"command\":\"status\",\"args\":[]}'

4️⃣  In Claude Code:
    Use the Bridge to execute commands and get results
    See: scripts/claude-chthonic-plugin.ts

" -ForegroundColor Cyan

