#!/usr/bin/env pwsh
# @SID: EXT_INSTALL_HOOK_V1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
$hookTarget = Join-Path $repoRoot ".git/hooks/pre-commit"

$shim = @"
#!/bin/sh
# Chthonic pre-commit chain:
# 1) Existing Archive Guardian
# 2) Reflex Guard (Cargo dependency drift)
pwsh -NoProfile -File "scripts/hooks/pre-commit-guardian.ps1"
status=$?
if [ \$status -ne 0 ]; then
  exit \$status
fi
pwsh -NoProfile -File "extensions/reflex-guard/scripts/pre-commit.ps1"
exit \$?
"@

Set-Content -Path $hookTarget -Value $shim -Encoding UTF8 -NoNewline
Write-Host "Installed pre-commit hook chain at: $hookTarget"
Write-Host "  - scripts/hooks/pre-commit-guardian.ps1"
Write-Host "  - extensions/reflex-guard/scripts/pre-commit.ps1"

