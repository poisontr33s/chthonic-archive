#!/usr/bin/env pwsh
# @SID: SCRIPT_INSTALL_HOOKS_V1
# Install git hooks from scripts/hooks/ into .git/hooks/
# Run once per clone: bun run hooks:install

$repoRoot = Split-Path $PSScriptRoot -Parent
$hookDst  = Join-Path $repoRoot ".git" "hooks"

$hooks = @{
    "pre-commit" = Join-Path $PSScriptRoot "pre-commit-hook.sh"
}

if (-not (Test-Path $hookDst)) {
    Write-Error ".git/hooks/ not found. Are you in a git repository?"
    exit 1
}

foreach ($name in $hooks.Keys) {
    $src = $hooks[$name]
    $dst = Join-Path $hookDst $name
    Copy-Item $src $dst -Force
    Write-Host "[hooks:install] Installed: .git/hooks/$name  (from $src)"
}

Write-Host "[hooks:install] Done. $($hooks.Count) hook(s) active."
