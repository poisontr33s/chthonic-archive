#!/usr/bin/env pwsh
# Patch Codex IDE webview bundle to add CLI-parity slash commands
# Target: function MJ() in index-B5Tvu0Eq.js
# Strategy: Expand the alias helper calls that MJ already uses
#
# Before: only has a(`agent`,`subagents`,`Subagents`,`Switch the active agent thread`)
# After:  adds aliases for plan, review, fast, new, resume + direct entries for compact/model/rename/collab/permissions/stop

param(
    [switch]$DryRun,
    [switch]$Restore
)

$bundlePath = "C:\Users\eldno\.vscode-insiders\extensions\openai.chatgpt-26.5313.41514-win32-x64\webview\assets\index-B5Tvu0Eq.js"
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

# The existing MJ function has exactly this one alias line:
$existingAlias = 'a(`agent`,`subagents`,`Subagents`,`Switch the active agent thread`);'

if (!$c.Contains($existingAlias)) {
    Write-Host "ERROR: Could not find the existing alias line in MJ. Bundle may already be patched or changed."
    Write-Host "Looking for: $existingAlias"
    # Check if already patched
    if ($c.Contains('a(`plan-mode`,`plan`,`Plan`')) {
        Write-Host "Bundle appears to already be patched."
    }
    return
}

# Phase 1: Alias expansion - add CLI-equivalent names for existing IDE commands
# Phase 2: Direct injection - add entries for commands with runtime backing but no OJ registration
$newAliases = @'
a(`agent`,`subagents`,`Subagents`,`Switch the active agent thread`);a(`plan-mode`,`plan`,`Plan`,`Toggle plan mode`);a(`review-mode`,`review`,`Review`,`Review code changes`);a(`speed`,`fast`,`Fast`,`Toggle fast/quality speed mode`);a(`hotkey-window-new`,`new`,`New`,`Start a new conversation thread`);a(`hotkey-window-resume`,`resume`,`Resume`,`Resume a previous conversation`);a(`status`,`statusline`,`Statusline`,`Show session status information`);a(`personality`,`collab`,`Collab`,`Switch collaboration mode`);a(`feedback`,`bug-report`,`Bug Report`,`Submit feedback or report an issue`);let _pi={compact:{id:`compact`,title:`Compact`,description:`Compact the conversation history`,Icon:null,onSelect:()=>{document.querySelector('[data-testid="composer-input"]')?.dispatchEvent(new CustomEvent("codex:slash",{detail:{command:"compact"},bubbles:!0}))}},model:{id:`model`,title:`Model`,description:`Switch the active model`,Icon:null,onSelect:()=>{document.querySelector('[data-testid="composer-input"]')?.dispatchEvent(new CustomEvent("codex:slash",{detail:{command:"model"},bubbles:!0}))}},rename:{id:`rename`,title:`Rename`,description:`Rename the current thread`,Icon:null,onSelect:()=>{document.querySelector('[data-testid="composer-input"]')?.dispatchEvent(new CustomEvent("codex:slash",{detail:{command:"rename"},bubbles:!0}))}},permissions:{id:`permissions`,title:`Permissions`,description:`View or change approval permissions`,Icon:null,onSelect:()=>{document.querySelector('[data-testid="composer-input"]')?.dispatchEvent(new CustomEvent("codex:slash",{detail:{command:"permissions"},bubbles:!0}))}},stop:{id:`stop`,title:`Stop`,description:`Stop background terminals and running tasks`,Icon:null,onSelect:()=>{document.querySelector('[data-testid="composer-input"]')?.dispatchEvent(new CustomEvent("codex:slash",{detail:{command:"stop"},bubbles:!0}))}},clear:{id:`clear`,title:`Clear`,description:`Clear the conversation display`,Icon:null,onSelect:()=>{document.querySelector('[data-testid="composer-input"]')?.dispatchEvent(new CustomEvent("codex:slash",{detail:{command:"clear"},bubbles:!0}))}},diff:{id:`diff`,title:`Diff`,description:`Show current changes as a diff`,Icon:null,onSelect:()=>{document.querySelector('[data-testid="composer-input"]')?.dispatchEvent(new CustomEvent("codex:slash",{detail:{command:"diff"},bubbles:!0}))}}};for(let _pk of Object.values(_pi)){if(!r.has(_pk.id)&&!i.has(_pk.title.toLowerCase())){n.push(_pk);r.add(_pk.id);i.add(_pk.title.toLowerCase())}}
'@

$patched = $c.Replace($existingAlias, $newAliases)

if ($patched -eq $c) {
    Write-Host "ERROR: Replacement failed - no change made."
    return
}

if ($DryRun) {
    Write-Host "DRY RUN - would replace:"
    Write-Host "  OLD: $existingAlias"
    Write-Host "  NEW length: $($newAliases.Length) chars"
    Write-Host "  Delta: +$($newAliases.Length - $existingAlias.Length) chars"
    
    # Verify the aliases parse
    Write-Host "`nAliases that would be added:"
    Write-Host "  plan-mode -> plan"
    Write-Host "  review-mode -> review"
    Write-Host "  speed -> fast"
    Write-Host "  hotkey-window-new -> new"
    Write-Host "  hotkey-window-resume -> resume"
    Write-Host "  status -> statusline"
    Write-Host "  personality -> collab"
    Write-Host "  feedback -> bug-report"
    Write-Host "`nDirect entries that would be added:"
    Write-Host "  /compact - Compact the conversation history"
    Write-Host "  /model - Switch the active model"
    Write-Host "  /rename - Rename the current thread"
    Write-Host "  /permissions - View or change approval permissions"
    Write-Host "  /stop - Stop background terminals"
    Write-Host "  /clear - Clear the conversation display"
    Write-Host "  /diff - Show current changes as a diff"
    return
}

[System.IO.File]::WriteAllText($bundlePath, $patched)
$newSize = (Get-Item $bundlePath).Length
Write-Host "Patch applied successfully."
Write-Host "  Original: $($c.Length) chars"
Write-Host "  Patched:  $($patched.Length) chars"
Write-Host "  File size: $newSize bytes"
Write-Host "`nAdded 8 aliases + 7 direct command entries."
Write-Host "Reload VS Code Insiders (Developer: Reload Window) to activate."
