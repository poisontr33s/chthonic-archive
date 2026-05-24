#!/usr/bin/env pwsh
#
# @SID: SCRIPT_AUDIT_BUNDLE_V1
# @Type: VALIDATION
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Unified Codex bundle audit — replaces slash-audit.ps1 and slash-deep-audit.ps1
#
# Unified Codex bundle audit — replaces slash-audit.ps1 and slash-deep-audit.ps1
# Usage:
#   .\scripts\codex\audit-bundle.ps1              # Quick summary
#   .\scripts\codex\audit-bundle.ps1 -Deep        # Full extraction
#   .\scripts\codex\audit-bundle.ps1 -Parity      # Parity matrix check

param(
    [switch]$Deep,
    [switch]$Parity
)

$extRoot = "$env:USERPROFILE\.vscode-insiders\extensions\openai.chatgpt-26.5313.41514-win32-x64"
$bundlePath = "$extRoot\webview\assets\index-B5Tvu0Eq.js"
$appScopePath = "$extRoot\webview\assets\app-scope-DIqwQRLP.js"
$extensionPath = "$extRoot\out\extension.js"

if (!(Test-Path $bundlePath)) {
    Write-Host "ERROR: Bundle not found at $bundlePath" -ForegroundColor Red
    Write-Host "Extension may have updated — locate the new index-*.js file."
    return
}

$c = [System.IO.File]::ReadAllText($bundlePath)
$backupExists = Test-Path "$bundlePath.bak"
$isV2 = $c.Contains('I.dispatchMessage')
$hasV2Marker = $c.Contains('Toggle plan mode')

Write-Host "=== Codex Bundle Audit ===" -ForegroundColor Cyan
Write-Host "  Bundle: $($c.Length) chars"
Write-Host "  Backup: $(if ($backupExists) { 'Yes' } else { 'No' })"
Write-Host "  Patch:  $(if ($hasV2Marker -and $isV2) { 'v2 (active)' } elseif ($hasV2Marker) { 'v1 (dead)' } else { 'None' })" -ForegroundColor $(if ($hasV2Marker -and $isV2) { 'Green' } else { 'Yellow' })

# --- OJ Registry ---
$ojCalls = [regex]::Matches($c, 'OJ\(')
Write-Host "`n=== OJ-Registered Commands: $($ojCalls.Count) ===" -ForegroundColor Cyan
$ojIds = @()
foreach ($m in $ojCalls) {
    $idx = $m.Index
    $after = $c.Substring($idx, [Math]::Min(400, $c.Length - $idx))
    $idM = [regex]::Match($after, 'id:[`"]([^`"]+)[`"]')
    if ($idM.Success) {
        $ojIds += $idM.Groups[1].Value
    } else {
        $before = $c.Substring([Math]::Max(0, $idx - 800), 800)
        $allBefore = [regex]::Matches($before, 'id:[`"]([^`"]+)[`"]')
        if ($allBefore.Count -gt 0) {
            $ojIds += $allBefore[$allBefore.Count - 1].Groups[1].Value
        } else {
            $ojIds += "??@$idx"
        }
    }
}
foreach ($id in $ojIds) { Write-Host "  /$id" }

# --- MJ Aliases ---
$mjIdx = $c.IndexOf('function MJ(')
$aliasRegion = $c.Substring($mjIdx + 200, 3000)
$aliases = [regex]::Matches($aliasRegion, 'a\([`"]([^`"]+)[`"]\s*,\s*[`"]([^`"]+)[`"]\s*,\s*[`"]([^`"]+)[`"]')
Write-Host "`n=== MJ Aliases: $($aliases.Count) ===" -ForegroundColor Cyan
foreach ($m in $aliases) {
    Write-Host "  /$($m.Groups[2].Value) <- $($m.Groups[1].Value) ($($m.Groups[3].Value))"
}

# --- Direct Entries ---
$directEntries = [regex]::Matches($aliasRegion, '\{id:[`"]([^`"]+)[`"],title:[`"]([^`"]+)[`"],description:[`"]([^`"]+)[`"]')
Write-Host "`n=== Direct Entries: $($directEntries.Count) ===" -ForegroundColor Cyan
foreach ($m in $directEntries) {
    Write-Host "  /$($m.Groups[1].Value) - $($m.Groups[3].Value)"
}

$totalSlash = $ojIds.Count + $aliases.Count + $directEntries.Count
Write-Host "`n  Total slash surface: $totalSlash" -ForegroundColor Green

if ($Deep) {
    Write-Host "`n=== Deep: MJ Function ===" -ForegroundColor Yellow
    $chunk = $c.Substring($mjIdx, 2000)
    $depth = 0; $end = 0
    for ($j = $chunk.IndexOf('{'); $j -lt $chunk.Length; $j++) {
        if ($chunk[$j] -eq '{') { $depth++ }
        elseif ($chunk[$j] -eq '}') { $depth--; if ($depth -eq 0) { $end = $j + 1; break } }
    }
    Write-Host $chunk.Substring(0, $end)

    Write-Host "`n=== Deep: OJ Function ===" -ForegroundColor Yellow
    $ojIdx = $c.IndexOf('function OJ(')
    $chunk2 = $c.Substring($ojIdx, 2000)
    $depth = 0; $end = 0
    for ($j = $chunk2.IndexOf('{'); $j -lt $chunk2.Length; $j++) {
        if ($chunk2[$j] -eq '{') { $depth++ }
        elseif ($chunk2[$j] -eq '}') { $depth--; if ($depth -eq 0) { $end = $j + 1; break } }
    }
    Write-Host $chunk2.Substring(0, $end)

    if (Test-Path $appScopePath) {
        $as = [System.IO.File]::ReadAllText($appScopePath)
        $cmds = [regex]::Matches($as, 'codex\.command\.([a-zA-Z]+)')
        $seen = @{}; foreach ($m in $cmds) { $seen[$m.Groups[1].Value] = $true }
        Write-Host "`n=== Deep: codex.command.* ($($seen.Count)) ===" -ForegroundColor Yellow
        $seen.Keys | Sort-Object | ForEach-Object { Write-Host "  codex.command.$_" }
    }

    # Dispatch message types
    $dms = [regex]::Matches($c, 'I\.dispatchMessage\([`"]([^`"]+)[`"]')
    $dmSeen = @{}; foreach ($m in $dms) { $dmSeen[$m.Groups[1].Value] = $true }
    Write-Host "`n=== Deep: dispatchMessage Types ($($dmSeen.Count)) ===" -ForegroundColor Yellow
    $dmSeen.Keys | Sort-Object | ForEach-Object { Write-Host "  $_" }

    # Extension host message handlers
    if (Test-Path $extensionPath) {
        $ec = [System.IO.File]::ReadAllText($extensionPath)
        $ovc = $ec.IndexOf('open-vscode-command')
        if ($ovc -gt 0) {
            $region = $ec.Substring([Math]::Max(0, $ovc - 3000), 12000)
            $cases = [regex]::Matches($region, 'case"([^"]+)"')
            Write-Host "`n=== Deep: extension.js handleMessage Cases ($($cases.Count)) ===" -ForegroundColor Yellow
            foreach ($m in $cases) { Write-Host "  $($m.Groups[1].Value)" }
        }
    }
}

if ($Parity) {
    Write-Host "`n=== Parity Check ===" -ForegroundColor Yellow

    # What's patched
    $patchedAliases = @{}
    foreach ($m in $aliases) { $patchedAliases[$m.Groups[2].Value] = $m.Groups[1].Value }
    $patchedDirect = @{}
    foreach ($m in $directEntries) { $patchedDirect[$m.Groups[1].Value] = $m.Groups[3].Value }

    # codex.command.* that have no slash surface
    if (Test-Path $appScopePath) {
        $as = [System.IO.File]::ReadAllText($appScopePath)
        $allCmds = [regex]::Matches($as, 'codex\.command\.([a-zA-Z]+)')
        $cmdSet = @{}; foreach ($m in $allCmds) { $cmdSet[$m.Groups[1].Value] = $true }

        # Check which commands already have a slash entry
        $coveredCmds = @('newThread', 'toggleDiffPanel', 'findInThread', 'toggleTerminal', 'openSkills', 'manageTasks', 'feedback', 'personalitySettings')
        $uncovered = @()
        foreach ($cmd in ($cmdSet.Keys | Sort-Object)) {
            if ($coveredCmds -notcontains $cmd) {
                $uncovered += $cmd
            }
        }

        Write-Host "`n  Unexploited codex.command.* ($($uncovered.Count)):" -ForegroundColor Red
        foreach ($cmd in $uncovered) { Write-Host "    codex.command.$cmd" }
    }

    # show-settings sections
    $sections = [regex]::Matches($c, 'section:[`"]([^`"]+)[`"]')
    $secSeen = @{}; foreach ($m in $sections) { $secSeen[$m.Groups[1].Value] = $true }
    $coveredSections = @('model', 'agent')
    $uncoveredSecs = $secSeen.Keys | Where-Object { $coveredSections -notcontains $_ }
    if ($uncoveredSecs) {
        Write-Host "`n  Unexploited show-settings sections:" -ForegroundColor Red
        foreach ($s in $uncoveredSecs) { Write-Host "    $s" }
    }

    # CLI-only gaps
    Write-Host "`n  CLI-only commands (no IDE path found):" -ForegroundColor Red
    Write-Host "    /compact  — server-initiated only (context-compaction protocol)"
    Write-Host "    /undo     — telemetry event exists, no command surface"
    Write-Host "    /history  — thread overlay is closest proxy"
    Write-Host "    /rename   — thread/name/updated protocol, no trigger"

    Write-Host ""
    Write-Host "  Total coverage: $totalSlash slash commands active" -ForegroundColor Green
    Write-Host "  Potential additions: ~$($uncovered.Count + 4 + $uncoveredSecs.Count) more" -ForegroundColor Yellow
}
