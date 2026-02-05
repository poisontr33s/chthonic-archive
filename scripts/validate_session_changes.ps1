#!/usr/bin/env pwsh
#Requires -Version 7.0

<#
.SYNOPSIS
    Validate session changes (Jan 17, 2026) - No regression, no resource bloat
.DESCRIPTION
    Tests all modifications made during integration session:
    - .gitignore allowlist (no unintended tracking)
    - Shell probe scripts (execution without side effects)
    - SSOT hash tool (accuracy validation)
    - MCP server (stdio protocol still functional)
    - GitHub Actions workflow (local simulation)
    - Resource overhead measurement
#>

$ErrorActionPreference = "Stop"
$results = @{
    Passed = @()
    Failed = @()
    Warnings = @()
}

function Test-Section {
    param(
        [string]$Name,
        [scriptblock]$Test
    )

    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    try {
        & $Test
        $results.Passed += $Name
        Write-Host "✓ PASS" -ForegroundColor Green
        return $true
    } catch {
        $results.Failed += "$Name`: $_"
        Write-Host "✗ FAIL: $_" -ForegroundColor Red
        return $false
    }
}

# ============================================================================
# TEST 1: .gitignore Integrity (No Unintended Tracking)
# ============================================================================
Test-Section ".gitignore Allowlist Integrity" {
    Write-Host "Testing allowlist pattern doesn't track build artifacts..."

    # Files that SHOULD be tracked (post-session)
    $shouldTrack = @(
        "scripts/shell_capabilities.ps1",
        "scripts/lint_shell_sovereignty.ps1",
        "scripts/bun_compliance_audit.py",
        "scripts/ssot_hash.py",
        ".github/INTEGRATION_MAP.md",
        "scripts/pause_agents.ps1"
    )

    # Files that SHOULD NOT be tracked (verify allowlist works)
    $shouldNotTrack = @(
        "node_modules/",
        "target/",
        "build/",
        ".venv/",
        "__pycache__/"
    )

    foreach ($file in $shouldTrack) {
        $tracked = git ls-files $file 2>$null
        if (-not $tracked) {
            throw "$file should be tracked but isn't"
        }
        Write-Host "  ✓ $file tracked" -ForegroundColor DarkGray
    }

    foreach ($pattern in $shouldNotTrack) {
        $tracked = git ls-files $pattern 2>$null | Select-Object -First 1
        if ($tracked) {
            throw "$pattern should NOT be tracked but is: $tracked"
        }
    }

    # Measure tracked file count (should be ~855, not thousands)
    $trackedCount = (git ls-files | Measure-Object -Line).Lines
    Write-Host "  Tracked files: $trackedCount" -ForegroundColor DarkGray

    if ($trackedCount -gt 1000) {
        $results.Warnings += ".gitignore may be leaking - $trackedCount files tracked (expected ~855)"
        Write-Host "  ⚠ Warning: High file count" -ForegroundColor Yellow
    }
}

# ============================================================================
# TEST 2: Shell Probe Scripts (Dry-Run Execution)
# ============================================================================
Test-Section "Shell Probe Scripts (Dry-Run)" {
    Write-Host "Testing canonical probe execution (read-only)..."

    # Test 1: shell_capabilities.ps1 (should output JSON)
    $probeOutput = & .\scripts\shell_capabilities.ps1 | ConvertFrom-Json

    if (-not $probeOutput.os) {
        throw "Probe missing 'os' field"
    }
    if (-not $probeOutput.pwsh_version) {
        throw "Probe missing 'pwsh_version' field"
    }

    Write-Host "  ✓ Probe returns valid JSON" -ForegroundColor DarkGray
    Write-Host "    OS: $($probeOutput.os)" -ForegroundColor DarkGray
    Write-Host "    PowerShell: $($probeOutput.pwsh_version)" -ForegroundColor DarkGray

    # Test 2: validate_shell_probe.ps1 (should validate without error)
    Write-Host "  Testing ABI validator..."
    & .\scripts\validate_shell_probe.ps1 *>&1 | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Shell probe validation failed (exit code: $LASTEXITCODE)"
    }

    Write-Host "  ✓ ABI validator passes" -ForegroundColor DarkGray

    # Test 3: lint_shell_sovereignty.ps1 (check for violations)
    Write-Host "  Testing shell sovereignty linter..."
    & .\scripts\lint_shell_sovereignty.ps1 *>&1 | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Shell sovereignty violations detected (exit code: $LASTEXITCODE)"
    }

    Write-Host "  ✓ Shell sovereignty clean" -ForegroundColor DarkGray
}

# ============================================================================
# TEST 3: SSOT Hash Tool (Accuracy & Determinism)
# ============================================================================
Test-Section "SSOT Hash Tool Accuracy" {
    Write-Host "Testing hash computation determinism..."

    # Compute hash twice - should be identical
    $hash1 = uv run scripts/ssot_hash.py
    Start-Sleep -Milliseconds 100
    $hash2 = uv run scripts/ssot_hash.py

    if ($hash1 -ne $hash2) {
        throw "Hash non-deterministic: $hash1 vs $hash2"
    }

    Write-Host "  ✓ Hash deterministic: $($hash1.Substring(0, 16))..." -ForegroundColor DarkGray

    # Test verification mode (should detect mismatch)
    Write-Host "  Testing verification mode..."
    $fakeHash = "0000000000000000000000000000000000000000000000000000000000000000"
    $verifyResult = uv run scripts/ssot_hash.py --verify $fakeHash 2>&1

    if ($LASTEXITCODE -eq 0) {
        throw "Verification should fail with fake hash but passed"
    }

    Write-Host "  ✓ Verification correctly detects drift" -ForegroundColor DarkGray
}

# ============================================================================
# TEST 4: Bun Compliance Audit (Dry-Run)
# ============================================================================
Test-Section "Bun Compliance Audit" {
    Write-Host "Testing bun compliance audit (dry-run)..."

    # Run audit in CI mode (strict)
    uv run scripts/bun_compliance_audit.py --ci *>&1 | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Bun compliance violations detected (exit code: $LASTEXITCODE)"
    }

    Write-Host "  ✓ Bun compliance validated" -ForegroundColor DarkGray
}

# ============================================================================
# TEST 5: MCP Server (Stdio Protocol)
# ============================================================================
Test-Section "MCP Server (Stdio Protocol)" {
    Write-Host "Testing MCP server initialization handshake..."

    if (-not (Test-Path "mcp/server.ts")) {
        $results.Warnings += "MCP server not found - skipping test"
        Write-Host "  ⚠ MCP server not found - skipping" -ForegroundColor Yellow
        return
    }

    # Proper stdio protocol test: initialize → tools/list → ping
    $initRequest = @'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
'@

    $toolsListRequest = @'
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
'@

    $pingRequest = @'
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"ping","arguments":{}}}
'@

    # Send all requests via stdio
    $allRequests = "$initRequest`n$toolsListRequest`n$pingRequest"

    $mcpOutput = $allRequests | bun run mcp/server.ts 2>&1 | Where-Object { $_ -notmatch '^\[MCP Server\]' }

    # Parse responses (should get 3 JSON-RPC responses)
    $responses = $mcpOutput | Where-Object { $_ -match '^\{' } | ForEach-Object { $_ | ConvertFrom-Json }

    if ($responses.Count -lt 2) {
        throw "MCP server returned insufficient responses (got $($responses.Count), expected at least 2)"
    }

    # Verify initialize response
    $initResponse = $responses | Where-Object { $_.id -eq 1 } | Select-Object -First 1
    if (-not $initResponse.result.serverInfo.name) {
        throw "MCP initialize response missing serverInfo"
    }

    Write-Host "  ✓ MCP server stdio protocol functional" -ForegroundColor DarkGray
    Write-Host "    Server: $($initResponse.result.serverInfo.name) v$($initResponse.result.serverInfo.version)" -ForegroundColor DarkGray
}

# ============================================================================
# TEST 6: Operational Mode Settings (No Side Effects)
# ============================================================================
Test-Section "Operational Mode Settings" {
    Write-Host "Verifying operational mode flags are passive..."

    $settings = Get-Content ".vscode/settings.json" -Raw | ConvertFrom-Json

    if ($settings.'chthonic.operationalMode' -ne 'essential') {
        throw "Operational mode should be 'essential', got: $($settings.'chthonic.operationalMode')"
    }

    if ($settings.'chthonic.allowCompetingAgents' -ne $false) {
        throw "allowCompetingAgents should be false"
    }

    Write-Host "  ✓ Settings configured correctly" -ForegroundColor DarkGray
    Write-Host "  ℹ These are passive metadata (no VS Code extension consuming them yet)" -ForegroundColor DarkGray
}

# ============================================================================
# TEST 7: Resource Overhead Measurement
# ============================================================================
Test-Section "Resource Overhead Analysis" {
    Write-Host "Measuring session resource impact..."

    # Measure script execution time
    $scriptTimes = @{}

    $measure = Measure-Command {
        & .\scripts\shell_capabilities.ps1 | Out-Null
    }
    $scriptTimes['shell_capabilities'] = $measure.TotalMilliseconds

    $measure = Measure-Command {
        uv run scripts/ssot_hash.py | Out-Null
    }
    $scriptTimes['ssot_hash'] = $measure.TotalMilliseconds

    # Check for overhead
    foreach ($scriptName in $scriptTimes.Keys) {
        $time = $scriptTimes[$scriptName]
        Write-Host "  ${scriptName}: $([math]::Round($time, 2))ms" -ForegroundColor DarkGray

        if ($time -gt 5000) {
            $results.Warnings += "${scriptName} execution slow ($time ms)"
        }
    }

    # Check file size bloat
    $integrationMapSize = (Get-Item ".github/INTEGRATION_MAP.md").Length / 1KB
    Write-Host "  INTEGRATION_MAP.md: $([math]::Round($integrationMapSize, 2)) KB" -ForegroundColor DarkGray

    if ($integrationMapSize -gt 50) {
        $results.Warnings += "INTEGRATION_MAP.md large ($integrationMapSize KB)"
    }
}

# ============================================================================
# TEST 8: GitHub Actions Workflow (Local Simulation)
# ============================================================================
Test-Section "GitHub Actions Workflow Simulation" {
    Write-Host "Simulating CI hard gates locally..."

    # Simulate each hard gate
    Write-Host "  [1/3] ABI contract validation..."
    & .\scripts\validate_shell_probe.ps1 *>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "ABI gate would fail" }

    Write-Host "  [2/3] Shell sovereignty enforcement..."
    & .\scripts\lint_shell_sovereignty.ps1 *>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Sovereignty gate would fail" }

    Write-Host "  [3/3] Bun compliance audit..."
    uv run scripts/bun_compliance_audit.py --ci *>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Bun compliance gate would fail" }

    Write-Host "  ✓ All 3 hard gates pass locally" -ForegroundColor DarkGray
}

# ============================================================================
# TEST 9: Git State Stability
# ============================================================================
Test-Section "Git State Stability" {
    Write-Host "Verifying clean working tree..."

    $status = git status --porcelain
    if ($status) {
        throw "Working tree not clean: $status"
    }

    Write-Host "  ✓ No uncommitted changes" -ForegroundColor DarkGray

    # Verify no untracked files from session
    $untracked = git status --porcelain | Where-Object { $_ -match '^\?\?' }
    if ($untracked) {
        $results.Warnings += "Untracked files detected: $untracked"
        Write-Host "  ⚠ Untracked files: $untracked" -ForegroundColor Yellow
    }
}

# ============================================================================
# SUMMARY
# ============================================================================
Write-Host "`n" -NoNewline
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor White
Write-Host "  VALIDATION SUMMARY" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor White

Write-Host "`nPassed: $($results.Passed.Count)" -ForegroundColor Green
foreach ($test in $results.Passed) {
    Write-Host "  ✓ $test" -ForegroundColor Green
}

if ($results.Failed.Count -gt 0) {
    Write-Host "`nFailed: $($results.Failed.Count)" -ForegroundColor Red
    foreach ($test in $results.Failed) {
        Write-Host "  ✗ $test" -ForegroundColor Red
    }
}

if ($results.Warnings.Count -gt 0) {
    Write-Host "`nWarnings: $($results.Warnings.Count)" -ForegroundColor Yellow
    foreach ($warning in $results.Warnings) {
        Write-Host "  ⚠ $warning" -ForegroundColor Yellow
    }
}

Write-Host "`n" -NoNewline
if ($results.Failed.Count -eq 0) {
    Write-Host "🎯 ALL VALIDATIONS PASSED" -ForegroundColor Green
    Write-Host "Session changes are stable and introduce no regressions." -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ VALIDATION FAILURES DETECTED" -ForegroundColor Red
    Write-Host "Session changes require remediation before deployment." -ForegroundColor Red
    exit 1
}

