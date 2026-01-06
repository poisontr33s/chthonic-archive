# scripts/validate_probe.ps1
# Wrapper for probe validation with advisory style checks
# CRITICAL: ABI enforcement delegated to validate_shell_probe.ps1

param(
    [string]$ProbePath = ".\scripts\shell_capabilities.ps1"
)

Write-Host "`n=== Probe Validation Suite ===" -ForegroundColor Cyan
Write-Host "Target: $ProbePath`n"

# ============================================================================
# HARD GATE: ABI Contract Enforcement
# ============================================================================
Write-Host "[REQUIRED] Running ABI contract validation..." -ForegroundColor Cyan

& pwsh -NoProfile -File .\scripts\validate_shell_probe.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n✗ ABI contract validation FAILED" -ForegroundColor Red
    Write-Host "  The probe violates the canonical contract." -ForegroundColor Red
    Write-Host "  See scripts/validate_shell_probe.ps1 for details." -ForegroundColor Yellow
    exit $LASTEXITCODE
}

Write-Host "✓ ABI contract validation PASSED`n" -ForegroundColor Green

# ============================================================================
# ADVISORY: Style and Quality Checks (non-blocking)
# ============================================================================
Write-Host "[ADVISORY] Running optional style checks..." -ForegroundColor Yellow
Write-Host "(These checks provide recommendations but do not block CI)`n" -ForegroundColor DarkGray

# Advisory Check 1: Code ratio
Write-Host "  Code ratio analysis..." -NoNewline
$content = Get-Content $ProbePath
$total = $content.Count
$comments = ($content | Where-Object { $_ -match '^\s*#' }).Count
$blank = ($content | Where-Object { $_ -match '^\s*$' }).Count
$code = $total - $comments - $blank
$codeRatio = [math]::Round($code / $total, 2)

if ($codeRatio -ge 0.70) {
    Write-Host " $codeRatio (high density)" -ForegroundColor Green
} else {
    Write-Host " $codeRatio (lower density - more documentation)" -ForegroundColor Yellow
}

# Advisory Check 2: JSON output test
Write-Host "  JSON execution test..." -NoNewline
try {
    $json = & $ProbePath 2>$null | ConvertFrom-Json
    if ($json.pwsh_version -and $json.os -and $json.path) {
        Write-Host " valid (all required fields present)" -ForegroundColor Green
    } else {
        Write-Host " partial (some fields missing)" -ForegroundColor Yellow
    }
} catch {
    Write-Host " failed (invalid JSON)" -ForegroundColor Red
}

# Advisory Check 3: Upcycle audit (if available)
Write-Host "  Upcycle audit scan..." -NoNewline
try {
    $auditResult = uv run python scripts\upcycle_audit.py $ProbePath --candidates-only 2>$null | ConvertFrom-Json
    if ($auditResult.results.Count -eq 0) {
        Write-Host " clean" -ForegroundColor Green
    } else {
        $flags = $auditResult.results[0].flags -join ", "
        Write-Host " flagged: $flags" -ForegroundColor Yellow
        Write-Host "    (Note: probe is explicitly exempt from these heuristics)" -ForegroundColor DarkGray
    }
} catch {
    Write-Host " skipped (uv/audit unavailable)" -ForegroundColor DarkGray
}

# ============================================================================
# Summary
# ============================================================================
Write-Host "`n=== Result ===" -ForegroundColor Cyan
Write-Host "✓ Probe is ABI-compliant and approved for use" -ForegroundColor Green
Write-Host "  Canonical hash: 6D6782ED8FFC4BF434D2A7108A0F3BACF13C3B40CC5C8F00F53CB789A96D9DF8" -ForegroundColor DarkGray
Write-Host "  Advisory checks completed (non-blocking)" -ForegroundColor DarkGray

exit 0
