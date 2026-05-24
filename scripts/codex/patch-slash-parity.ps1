#!/usr/bin/env pwsh
#
# @SID: SCRIPT_PATCH_SLASH_PARITY_V1
# @Type: MAINTENANCE
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Patch Codex IDE webview bundle to add CLI-parity slash commands (v2)
#
# Patch Codex IDE webview bundle to add CLI-parity slash commands (v2)
# Target: function MJ() in index-B5Tvu0Eq.js
#
# v2 ARCHITECTURE:
#   - Aliases use MJ's a() helper to clone existing OJ-registered commands (inherit onSelect/Content)
#   - Direct entries use I.dispatchMessage() — the REAL webview→extension bridge
#     (imported from logger-DeWf6XmT.js as the MessageBridge singleton)
#   - "open-vscode-command" message type executes any VS Code command via extension host
#   - "show-settings" message type opens settings panel with section routing
#
# KEY FIX from v1: v1 used CustomEvent("codex:slash") which had NO listeners — dead on arrival.
# v2 uses I.dispatchMessage() which posts via acquireVsCodeApi().postMessage() to the extension host.

param(
    [switch]$DryRun,
    [switch]$Restore
)

$bundlePath = "$env:USERPROFILE\.vscode-insiders\extensions\openai.chatgpt-26.5313.41514-win32-x64\webview\assets\index-B5Tvu0Eq.js"
$backupPath = "$bundlePath.bak"

if ($Restore) {
    if (Test-Path $backupPath) {
        Copy-Item $backupPath $bundlePath -Force
        Write-Host "Restored from backup."
    } else {
        Write-Host "No backup found."
    }
    return
}

$c = [System.IO.File]::ReadAllText($bundlePath)

# Detection: find the original single alias line OR v1/v2 patch marker
$existingAlias = 'a(`agent`,`subagents`,`Subagents`,`Switch the active agent thread`);'
$v2Marker = 'a(`plan-mode`,`plan`,`Plan`,`Toggle plan mode`)'
$isOriginal = $c.Contains($existingAlias)
$isPatched = $c.Contains($v2Marker)

if (!$isOriginal -and !$isPatched) {
    Write-Host "ERROR: Bundle doesn't match expected patterns. May be a different version."
    return
}

if ($isPatched) {
    Write-Host "Bundle is already patched (v1 or v2). Use -Restore to revert first, then re-apply."
    return
}

# v2 replacement: 8 aliases via a() + 8 direct entries via I.dispatchMessage()
# Removed dead a(`agent`,`subagents`,...) — `agent` was never OJ-registered
$replacement = @'
a(`plan-mode`,`plan`,`Plan`,`Toggle plan mode`);a(`review-mode`,`review`,`Review`,`Review code changes`);a(`speed`,`fast`,`Fast`,`Toggle fast/quality speed mode`);a(`hotkey-window-new`,`new`,`New`,`Start a new conversation thread`);a(`hotkey-window-resume`,`resume`,`Resume`,`Resume a previous conversation`);a(`status`,`statusline`,`Statusline`,`Show session status information`);a(`personality`,`collab`,`Collab`,`Switch collaboration mode`);a(`feedback`,`bug-report`,`Bug Report`,`Submit feedback or report an issue`);let _pi={model:{id:`model`,title:`Model`,description:`Switch the active model`,onSelect:()=>{I.dispatchMessage(`show-settings`,{section:`model`})}},clear:{id:`clear`,title:`Clear`,description:`Start a new conversation`,onSelect:()=>{I.dispatchMessage(`open-vscode-command`,{command:`codex.command.newThread`})}},diff:{id:`diff`,title:`Diff`,description:`Show current changes as a diff`,onSelect:()=>{I.dispatchMessage(`open-vscode-command`,{command:`codex.command.toggleDiffPanel`})}},agent:{id:`agent`,title:`Agent`,description:`Open agent settings`,onSelect:()=>{I.dispatchMessage(`show-settings`,{section:`agent`})}},find:{id:`find`,title:`Find`,description:`Search within current thread`,onSelect:()=>{I.dispatchMessage(`open-vscode-command`,{command:`codex.command.findInThread`})}},terminal:{id:`terminal`,title:`Terminal`,description:`Toggle the terminal panel`,onSelect:()=>{I.dispatchMessage(`open-vscode-command`,{command:`codex.command.toggleTerminal`})}},skills:{id:`skills`,title:`Skills`,description:`Browse and manage skills`,onSelect:()=>{I.dispatchMessage(`open-vscode-command`,{command:`codex.command.openSkills`})}},tasks:{id:`tasks`,title:`Tasks`,description:`View and manage tasks`,onSelect:()=>{I.dispatchMessage(`open-vscode-command`,{command:`codex.command.manageTasks`})}}};for(let _pk of Object.values(_pi)){if(!r.has(_pk.id)&&!i.has(_pk.title.toLowerCase())){n.push(_pk);r.add(_pk.id);i.add(_pk.title.toLowerCase())}}
'@

$patched = $c.Replace($existingAlias, $replacement)

if ($patched -eq $c) {
    Write-Host "ERROR: Replacement failed — no change made."
    return
}

if ($DryRun) {
    Write-Host "DRY RUN — v2 patch preview:"
    Write-Host "  Delta: +$($replacement.Length - $existingAlias.Length) chars"
    Write-Host ""
    Write-Host "ALIASES (clone OJ commands via a() helper — inherit onSelect/Content):"
    Write-Host "  /plan       <- plan-mode"
    Write-Host "  /review     <- review-mode"
    Write-Host "  /fast       <- speed"
    Write-Host "  /new        <- hotkey-window-new"
    Write-Host "  /resume     <- hotkey-window-resume"
    Write-Host "  /statusline <- status"
    Write-Host "  /collab     <- personality"
    Write-Host "  /bug-report <- feedback"
    Write-Host ""
    Write-Host "DIRECT ENTRIES (I.dispatchMessage → extension host):"
    Write-Host "  /model    -> show-settings {section: model}"
    Write-Host "  /clear    -> codex.command.newThread"
    Write-Host "  /diff     -> codex.command.toggleDiffPanel"
    Write-Host "  /agent    -> show-settings {section: agent}"
    Write-Host "  /find     -> codex.command.findInThread"
    Write-Host "  /terminal -> codex.command.toggleTerminal"
    Write-Host "  /skills   -> codex.command.openSkills"
    Write-Host "  /tasks    -> codex.command.manageTasks"
    return
}

# Backup if not already backed up
if (!(Test-Path $backupPath)) {
    Copy-Item $bundlePath $backupPath -Force
    Write-Host "Backup created: $backupPath"
}

[System.IO.File]::WriteAllText($bundlePath, $patched)
Write-Host "v2 patch applied successfully."
Write-Host "  Original: $($c.Length) chars"
Write-Host "  Patched:  $($patched.Length) chars"
Write-Host "  Added: 8 aliases + 8 direct entries"
Write-Host ""
Write-Host "Reload VS Code Insiders (Developer: Reload Window) to activate."
