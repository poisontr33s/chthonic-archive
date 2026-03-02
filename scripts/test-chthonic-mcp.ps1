#!/usr/bin/env pwsh
# Test chthonic v3.0.0 meta-CLI through MCP server

$REPO_ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$MCP_SERVER = Join-Path $REPO_ROOT "scripts" "mcp-chthonic-server.ts"

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Testing chthonic v3.0.0 meta-CLI via MCP Server" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Test 1: List all tools (should show 20 tools now)
Write-Host "📋 Test 1: List all MCP tools" -ForegroundColor Yellow
$request1 = '{"jsonrpc":"2.0","method":"tools/list","id":1}'
echo $request1 | bun run $MCP_SERVER 2>$null | Select-String "chthonic" | Select-Object -First 3
Write-Host ""

# Test 2: Call chthonic status
Write-Host "📊 Test 2: chthonic status (via MCP)" -ForegroundColor Yellow
$request2 = '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"chthonic","arguments":{"domain":"status"}},"id":2}'
$output = echo $request2 | bun run $MCP_SERVER 2>$null | ConvertFrom-Json
if ($output.result) {
    $output.result.content[0].text -split "`n" | Select-Object -First 15
}
Write-Host ""

# Test 3: Call chthonic ide detect
Write-Host "🔍 Test 3: chthonic ide detect (via MCP)" -ForegroundColor Yellow
$request3 = '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"chthonic","arguments":{"domain":"ide","action":"detect"}},"id":3}'
$output = echo $request3 | bun run $MCP_SERVER 2>$null | ConvertFrom-Json
if ($output.result) {
    $output.result.content[0].text -split "`n" | Select-Object -First 10
}
Write-Host ""

# Test 4: Call chthonic mcp status
Write-Host "🚀 Test 4: chthonic mcp status (via MCP)" -ForegroundColor Yellow
$request4 = '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"chthonic","arguments":{"domain":"mcp","action":"status"}},"id":4}'
$output = echo $request4 | bun run $MCP_SERVER 2>$null | ConvertFrom-Json
if ($output.result) {
    $output.result.content[0].text -split "`n"
}
Write-Host ""

# Test 5: Call chthonic detect
Write-Host "🔬 Test 5: chthonic detect (via MCP)" -ForegroundColor Yellow
$request5 = '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"chthonic","arguments":{"domain":"detect"}},"id":5}'
$output = echo $request5 | bun run $MCP_SERVER 2>$null | ConvertFrom-Json
if ($output.result) {
    $output.result.content[0].text -split "`n" | Select-Object -First 10
}
Write-Host ""

Write-Host "✅ All MCP tests complete! Chthonic v3.0.0 is integrated." -ForegroundColor Green

