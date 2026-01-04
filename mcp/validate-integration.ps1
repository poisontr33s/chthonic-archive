# MCP Integration Validation Script
# Run this after restarting Claude Desktop to verify end-to-end integration

Write-Host "=== MCP Client Integration Validation ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify Claude Desktop config
Write-Host "[1/5] Verifying Claude Desktop configuration..." -ForegroundColor Yellow
$claudeConfigPath = "$env:APPDATA\Claude\claude_desktop_config.json"

if (Test-Path $claudeConfigPath) {
    $config = Get-Content $claudeConfigPath | ConvertFrom-Json
    if ($config.mcpServers.'chthonic-archive') {
        Write-Host "  ✓ chthonic-archive server configured" -ForegroundColor Green
        Write-Host "  Command: $($config.mcpServers.'chthonic-archive'.command)" -ForegroundColor Gray
        Write-Host "  Args: $($config.mcpServers.'chthonic-archive'.args -join ' ')" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ chthonic-archive server NOT found in config" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ✗ Claude Desktop config not found" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Verify server can start
Write-Host "[2/5] Testing server startup..." -ForegroundColor Yellow
$testProcess = Start-Process -FilePath "bun" -ArgumentList "run", "mcp/server.ts" -NoNewWindow -PassThru -RedirectStandardInput "NUL" -RedirectStandardOutput "test-output.txt" -RedirectStandardError "test-error.txt"
Start-Sleep -Seconds 1

if ($testProcess.HasExited) {
    Write-Host "  ✗ Server exited immediately" -ForegroundColor Red
    Get-Content "test-error.txt" | Write-Host -ForegroundColor Red
    exit 1
} else {
    Write-Host "  ✓ Server started successfully" -ForegroundColor Green
    $testProcess.Kill()
    Start-Sleep -Milliseconds 500
}

Remove-Item "test-output.txt", "test-error.txt" -ErrorAction SilentlyContinue
Write-Host ""

# Step 3: Verify MCP manifest
Write-Host "[3/5] Validating MCP manifest..." -ForegroundColor Yellow
$manifestPath = "mcp/mcp.json"

if (Test-Path $manifestPath) {
    $manifest = Get-Content $manifestPath | ConvertFrom-Json
    Write-Host "  ✓ Manifest exists" -ForegroundColor Green
    Write-Host "  Name: $($manifest.name)" -ForegroundColor Gray
    Write-Host "  Version: $($manifest.version)" -ForegroundColor Gray
    Write-Host "  Tools: $($manifest.tools.Count)" -ForegroundColor Gray
    
    foreach ($tool in $manifest.tools) {
        Write-Host "    - $($tool.name)" -ForegroundColor Gray
    }
} else {
    Write-Host "  ✗ Manifest not found" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 4: Run local test suite
Write-Host "[4/5] Running local test suite..." -ForegroundColor Yellow
$testResult = bun test mcp/server.test.ts 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ All tests passing" -ForegroundColor Green
    # Extract test count from output
    $testLine = $testResult | Select-String "pass"
    if ($testLine) {
        Write-Host "  $testLine" -ForegroundColor Gray
    }
} else {
    Write-Host "  ✗ Tests failed" -ForegroundColor Red
    Write-Host $testResult -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 5: Provide next steps
Write-Host "[5/5] Integration readiness check" -ForegroundColor Yellow
Write-Host "  ✓ Configuration validated" -ForegroundColor Green
Write-Host "  ✓ Server operational" -ForegroundColor Green
Write-Host "  ✓ Manifest valid" -ForegroundColor Green
Write-Host "  ✓ Tests passing" -ForegroundColor Green

Write-Host ""
Write-Host "=== Next Steps ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Restart Claude Desktop:" -ForegroundColor White
Write-Host "   - Quit completely (Alt+F4 or File → Quit)" -ForegroundColor Gray
Write-Host "   - Relaunch Claude Desktop" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Verify server appears in MCP provider list" -ForegroundColor White
Write-Host ""
Write-Host "3. Test tools from Claude Desktop chat:" -ForegroundColor White
Write-Host ""
Write-Host "   Test 1 (Ping):" -ForegroundColor Yellow
Write-Host "   'Can you ping the chthonic-archive MCP server?'" -ForegroundColor Gray
Write-Host "   Expected: {`"pong`": true}" -ForegroundColor DarkGray
Write-Host ""
Write-Host "   Test 2 (Repository Scan):" -ForegroundColor Yellow
Write-Host "   'Scan the chthonic-archive repository and tell me how many files exist.'" -ForegroundColor Gray
Write-Host "   Expected: ~44,207 files found" -ForegroundColor DarkGray
Write-Host ""
Write-Host "   Test 3 (SSOT Validation):" -ForegroundColor Yellow
Write-Host "   'Validate the SSOT integrity for chthonic-archive.'" -ForegroundColor Gray
Write-Host "   Expected: Status valid, hash 49ef091b..." -ForegroundColor DarkGray
Write-Host ""
Write-Host "4. If all tools invoke successfully:" -ForegroundColor White
Write-Host "   - Document results in docs/MCP_AUTONOMOUS_PREREQUISITES.md" -ForegroundColor Gray
Write-Host "   - Update mcp/README.md with integration status" -ForegroundColor Gray
Write-Host "   - Commit validation results" -ForegroundColor Gray
Write-Host "   - Option A complete ✓" -ForegroundColor Green
Write-Host ""
Write-Host "=== Troubleshooting ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "If server doesn't appear in Claude Desktop:" -ForegroundColor Yellow
Write-Host "  - Check Claude Desktop logs (Help → View Logs)" -ForegroundColor Gray
Write-Host "  - Verify bun is in PATH: bun --version" -ForegroundColor Gray
Write-Host "  - Test manual invocation: echo '{`"id`":1,`"method`":`"ping`"}' | bun run mcp/server.ts" -ForegroundColor Gray
Write-Host ""
Write-Host "If tools fail:" -ForegroundColor Yellow
Write-Host "  - Verify working directory is repository root" -ForegroundColor Gray
Write-Host "  - Check .github/copilot-instructions.md exists" -ForegroundColor Gray
Write-Host "  - Re-run validation: bun test mcp/server.test.ts" -ForegroundColor Gray
Write-Host ""
Write-Host "=== Validation Complete ===" -ForegroundColor Cyan
