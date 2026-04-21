#!/usr/bin/env pwsh
# @SID: SCRIPT_INSTALL_HOOKS_V1
# Install git hooks from scripts/hooks/ into .git/hooks/
# Run once per clone: bun run hooks:install
# Options: -Force (overwrite without prompting), -DryRun (report only, no writes)

param(
    [switch]$Force,
    [switch]$DryRun
)

$repoRoot = Split-Path $PSScriptRoot -Parent
$hookDst  = Join-Path $repoRoot ".git" "hooks"

# Post-merge hook: run bun install --frozen-lockfile if lockfile changed
$postMergeContent = @'
#!/usr/bin/env bash
if git diff-tree -r --name-only --no-commit-id ORIG_HEAD HEAD | grep -q 'bun.lockb'; then
  echo "[post-merge] lockfile changed — running bun install --frozen-lockfile"
  bun install --frozen-lockfile
fi
'@

$hooks = @{
    "pre-commit" = Join-Path $PSScriptRoot "pre-commit-hook.sh"
}

$inlineHooks = @{
    "post-merge" = $postMergeContent
}

if (-not (Test-Path $hookDst)) {
    Write-Error ".git/hooks/ not found. Are you in a git repository?"
    exit 1
}

# Report existing hooks before any writes
foreach ($name in @($hooks.Keys) + @($inlineHooks.Keys)) {
    $dst = Join-Path $hookDst $name
    if (Test-Path $dst) {
        Write-Host "[hooks:install] Existing: .git/hooks/$name"
    }
}

if ($DryRun) {
    Write-Host "[hooks:install] DryRun mode — no files written."
    foreach ($name in $hooks.Keys) {
        Write-Host "[hooks:install] Would install: .git/hooks/$name  (from $($hooks[$name]))"
    }
    foreach ($name in $inlineHooks.Keys) {
        Write-Host "[hooks:install] Would install: .git/hooks/$name  (inline)"
    }
    exit 0
}

foreach ($name in $hooks.Keys) {
    $src = $hooks[$name]
    $dst = Join-Path $hookDst $name
    if ((Test-Path $dst) -and -not $Force) {
        $ans = Read-Host "[hooks:install] Overwrite .git/hooks/$name? [y/N]"
        if ($ans -notmatch '^[Yy]') {
            Write-Host "[hooks:install] Skipped: $name"
            continue
        }
    }
    Copy-Item $src $dst -Force
    Write-Host "[hooks:install] Installed: .git/hooks/$name  (from $src)"
}

foreach ($name in $inlineHooks.Keys) {
    $dst = Join-Path $hookDst $name
    if ((Test-Path $dst) -and -not $Force) {
        $ans = Read-Host "[hooks:install] Overwrite .git/hooks/$name? [y/N]"
        if ($ans -notmatch '^[Yy]') {
            Write-Host "[hooks:install] Skipped: $name"
            continue
        }
    }
    $inlineHooks[$name] | Set-Content $dst -Encoding utf8NoBOM
    Write-Host "[hooks:install] Installed: .git/hooks/$name  (inline)"
}

Write-Host "[hooks:install] Done. $($hooks.Count + $inlineHooks.Count) hook(s) active."
