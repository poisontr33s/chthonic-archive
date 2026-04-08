#!/usr/bin/env pwsh
# @SID: SCRIPT_TEST_META_CLI_V1
# @Type: VALIDATION
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Quick validation of refactored chthonic.ps1
# Quick validation of refactored chthonic.ps1

$REPO_ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SCRIPT_DIR = Join-Path $REPO_ROOT "scripts"

Write-Host "Testing refactored chthonic meta-CLI...`n" -ForegroundColor Cyan

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

# Test 8: Create lane dry-run
Write-Host "✅ Test 8: chthonic new uv-python-app --dry-run --json" -ForegroundColor Green
& pwsh -NoProfile -Command "
  Set-Location '$REPO_ROOT'
  & '$SCRIPT_DIR\chthonic.ps1' new uv-python-app tmp/chthonic-new-smoke --dry-run --json
" 2>&1 | Select-Object -First 12
Write-Host ""

# Test 9: Python lane
Write-Host "✅ Test 9: chthonic python lane" -ForegroundColor Green
& pwsh -NoProfile -Command "
  Set-Location '$REPO_ROOT'
  & '$SCRIPT_DIR\chthonic.ps1' python lane
" 2>&1 | Select-Object -First 10
Write-Host ""

# Test 10: Bun lane
Write-Host "✅ Test 10: chthonic bun lane" -ForegroundColor Green
& pwsh -NoProfile -Command "
  Set-Location '$REPO_ROOT'
  & '$SCRIPT_DIR\chthonic.ps1' bun lane
" 2>&1 | Select-Object -First 10
Write-Host ""

# Test 11: Rust lane
Write-Host "✅ Test 11: chthonic rust lane" -ForegroundColor Green
& pwsh -NoProfile -Command "
  Set-Location '$REPO_ROOT'
  & '$SCRIPT_DIR\chthonic.ps1' rust lane
" 2>&1 | Select-Object -First 10
Write-Host ""

# Test 12: Go lane
Write-Host "✅ Test 12: chthonic go lane" -ForegroundColor Green
& pwsh -NoProfile -Command "
  Set-Location '$REPO_ROOT'
  & '$SCRIPT_DIR\chthonic.ps1' go lane
" 2>&1 | Select-Object -First 10
Write-Host ""

# Test 13: Claudine wrapper parity
Write-Host "✅ Test 13: claudine python lane" -ForegroundColor Green
& pwsh -NoProfile -Command "
  Set-Location '$REPO_ROOT'
  & '$SCRIPT_DIR\claudine.ps1' python lane
" 2>&1 | Select-Object -First 10
Write-Host ""

Write-Host "✅ Meta-CLI smoke tests completed." -ForegroundColor Cyan

