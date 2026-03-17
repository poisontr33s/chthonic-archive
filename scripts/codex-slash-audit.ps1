#!/usr/bin/env pwsh
# Audit Codex IDE webview bundle for slash command registrations
$bundlePath = "C:\Users\eldno\.vscode-insiders\extensions\openai.chatgpt-26.5313.41514-win32-x64\webview\assets\index-B5Tvu0Eq.js"
$c = [System.IO.File]::ReadAllText($bundlePath)
Write-Host "=== Bundle size: $($c.Length) ==="

# Find all OJ( calls (useProvideSlashCommand)
$ojCalls = [regex]::Matches($c, 'OJ\(')
Write-Host "`n=== OJ() calls (useProvideSlashCommand): $($ojCalls.Count) ==="
foreach ($m in $ojCalls) {
    $idx = $m.Index
    $snippet = $c.Substring($idx, [Math]::Min(120, $c.Length - $idx))
    Write-Host "  @$idx : $snippet"
}

# Find function OJ definition
Write-Host "`n=== function OJ definition ==="
$ojDef = [regex]::Match($c, 'function OJ\([^)]*\)\{[^}]{0,500}')
if ($ojDef.Success) {
    Write-Host "  @$($ojDef.Index) : $($ojDef.Value)"
}

# Find the MJ function (slash command list)
Write-Host "`n=== function MJ definition ==="
$mjDef = [regex]::Match($c, 'function MJ\([^)]*\)\{[^}]{0,500}')
if ($mjDef.Success) {
    Write-Host "  @$($mjDef.Index) : $($mjDef.Value)"
}

# Find plan-mode and review-mode with context
Write-Host "`n=== plan-mode contexts ==="
$pm = [regex]::Matches($c, '.{0,40}plan-mode.{0,60}')
foreach ($m in $pm) { Write-Host "  $($m.Value)" }

Write-Host "`n=== review-mode contexts ==="
$rm = [regex]::Matches($c, '.{0,40}review-mode.{0,60}')
foreach ($m in $rm) { Write-Host "  $($m.Value)" }

# Find slashCommand context uses
Write-Host "`n=== slashCommand (camelCase) contexts ==="
$sc = [regex]::Matches($c, '.{0,30}slashCommand.{0,50}')
foreach ($m in $sc) { Write-Host "  $($m.Value)" }

# Find the slash command list/menu rendering
Write-Host "`n=== SlashCommandList pattern ==="
$scl = [regex]::Matches($c, '.{0,30}SlashCommandList.{0,50}')
foreach ($m in $scl) { Write-Host "  $($m.Value)" }
