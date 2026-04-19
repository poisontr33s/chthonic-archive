#!/usr/bin/env pwsh
# @SID: SCRIPT_INSTALL_HOOKS_V1
# Install git hooks from scripts/hooks/ into .git/hooks/
# Run once per clone: bun run hooks:install

$repoRoot = Split-Path $PSScriptRoot -Parent
$hookSrc  = Join-Path $PSScriptRoot "hooks"
$hookDst  = Join-Path $repoRoot ".git" "hooks"

if (-not (Test-Path $hookDst)) {
    Write-Error ".git/hooks/ not found. Are you in a git repository?"
    exit 1
}

Get-ChildItem -Path $hookSrc | ForEach-Object {
    $dst = Join-Path $hookDst $_.Name
    Copy-Item $_.FullName $dst -Force
    Write-Host "[hooks:install] Installed: .git/hooks/$($_.Name)"
}

Write-Host "[hooks:install] Done. $((Get-ChildItem $hookSrc).Count) hook(s) active."
