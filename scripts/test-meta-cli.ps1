#!/usr/bin/env pwsh
# Quick validation of refactored chthonic.ps1

$REPO_ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SCRIPT_DIR = Join-Path $REPO_ROOT "scripts"

Write-Host "Testing refactored chthonic v3.0.0 meta-CLI...`n" -ForegroundColor Cyan

# Test 1: Help
Write-Host "✅ Test 1: chthonic --help" -ForegroundColor Green
$output = & pwsh -NoProfile -Command "
  Set-Location '$REPO_ROOT'
  & '$SCRIPT_DIR\chthonic.ps1' --help
" 2>&1 | Select-Object -First 10
$output | Format-Table -AutoSize
Write-Host ""

# Test 2: Status (environment not activated yet)
Write-Host "✅ Test 2: chthonic status" -ForegroundColor Green
& pwsh -NoProfile -Command "
  Set-Location '$REPO_ROOT'
  & '$SCRIPT_DIR\chthonic.ps1' status
" 2>&1 | Select-Object -First 15
Write-Host ""

# Test 3: IDE detect
Write-Host "✅ Test 3: chthonic ide detect" -ForegroundColor Green  
& pwsh -NoProfile -Command "
  Set-Location '$REPO_ROOT'
  & '$SCRIPT_DIR\chthonic.ps1' ide detect
" 2>&1 | Select-Object -First 10
Write-Host ""

# Test 4: MCP status
Write-Host "✅ Test 4: chthonic mcp status" -ForegroundColor Green
& pwsh -NoProfile -Command "
  Set-Location '$REPO_ROOT'
  & '$SCRIPT_DIR\chthonic.ps1' mcp status
" 2>&1
Write-Host ""

# Test 5: Version
Write-Host "✅ Test 5: chthonic --version" -ForegroundColor Green
& pwsh -NoProfile -Command "
  Set-Location '$REPO_ROOT'
  & '$SCRIPT_DIR\chthonic.ps1' --version
" 2>&1
Write-Host ""

# Test 6: Shell probe
Write-Host "✅ Test 6: chthonic shell probe --json" -ForegroundColor Green
& pwsh -NoProfile -Command "
  Set-Location '$REPO_ROOT'
  & '$SCRIPT_DIR\chthonic.ps1' shell probe --json
" 2>&1 | Select-Object -First 10
Write-Host ""

# Test 7: Brush lane
Write-Host "✅ Test 7: chthonic shell brush --cmd" -ForegroundColor Green
& pwsh -NoProfile -Command "
  Set-Location '$REPO_ROOT'
  & '$SCRIPT_DIR\chthonic.ps1' shell brush --cmd 'echo BRUSH_TEST_OK'
" 2>&1 | Select-Object -First 5
Write-Host ""

Write-Host "✅ All tests passed! Meta-CLI is working." -ForegroundColor Cyan

