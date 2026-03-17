#!/usr/bin/env pwsh
# Deep audit of OJ/MJ functions and slash command IDs in Codex webview bundle
$bundlePath = "C:\Users\eldno\.vscode-insiders\extensions\openai.chatgpt-26.5313.41514-win32-x64\webview\assets\index-B5Tvu0Eq.js"
$c = [System.IO.File]::ReadAllText($bundlePath)

# Extract function MJ fully - find it and grab until next function definition
$mjIdx = $c.IndexOf('function MJ(')
Write-Host "=== function MJ (slash command list/alias handler) @ $mjIdx ==="
# Grab a generous chunk - it's minified so the function should be relatively compact
$chunk = $c.Substring($mjIdx, [Math]::Min(2000, $c.Length - $mjIdx))
# Find the end of the function by counting braces
$depth = 0; $end = 0
for ($j = $chunk.IndexOf('{'); $j -lt $chunk.Length; $j++) {
    if ($chunk[$j] -eq '{') { $depth++ }
    elseif ($chunk[$j] -eq '}') { $depth--; if ($depth -eq 0) { $end = $j + 1; break } }
}
Write-Host $chunk.Substring(0, $end)
Write-Host ""

# Extract function OJ (useProvideSlashCommand) 
$ojIdx = $c.IndexOf('function OJ(')
Write-Host "=== function OJ (useProvideSlashCommand) @ $ojIdx ==="
$chunk2 = $c.Substring($ojIdx, [Math]::Min(2000, $c.Length - $ojIdx))
$depth = 0; $end = 0
for ($j = $chunk2.IndexOf('{'); $j -lt $chunk2.Length; $j++) {
    if ($chunk2[$j] -eq '{') { $depth++ }
    elseif ($chunk2[$j] -eq '}') { $depth--; if ($depth -eq 0) { $end = $j + 1; break } }
}
Write-Host $chunk2.Substring(0, $end)
Write-Host ""

# Now extract each OJ call's ID by going to each offset and extracting the id field
Write-Host "=== All registered slash command IDs ==="
$ojCalls = [regex]::Matches($c, 'OJ\(')
foreach ($m in $ojCalls) {
    $idx = $m.Index
    $snippet = $c.Substring($idx, [Math]::Min(300, $c.Length - $idx))
    # Try to extract id from the snippet
    $idMatch = [regex]::Match($snippet, 'id:[`"'']([^`"'']+)[`"'']')
    if ($idMatch.Success) {
        Write-Host "  /$($idMatch.Groups[1].Value)"
    } else {
        # It's a variable call like OJ(i) or OJ(e) - look at what was built before
        $preSnippet = $c.Substring([Math]::Max(0, $idx - 300), 300)
        $idFromVar = [regex]::Match($preSnippet, 'id:[`"'']([^`"'']+)[`"'']')
        if ($idFromVar.Success) {
            # Get all id matches and take the last one (closest to OJ call)
            $allIds = [regex]::Matches($preSnippet, 'id:[`"'']([^`"'']+)[`"'']')
            $lastId = $allIds[$allIds.Count - 1]
            Write-Host "  /$($lastId.Groups[1].Value) (variable)"
        } else {
            Write-Host "  /??? (OJ call at $idx with unresolved ID)"
        }
    }
}

# Check app-scope file for protocol-level commands
Write-Host "`n=== app-scope-DIqwQRLP.js command patterns ==="
$appScope = [System.IO.File]::ReadAllText("C:\Users\eldno\.vscode-insiders\extensions\openai.chatgpt-26.5313.41514-win32-x64\webview\assets\app-scope-DIqwQRLP.js")
Write-Host "app-scope size: $($appScope.Length)"
$protoCommands = [regex]::Matches($appScope, '(slash|command|compact|rename|model|permissions|experimental|agent|subagent).{0,40}')
Write-Host "Protocol command-like patterns: $($protoCommands.Count)"
foreach ($m in ($protoCommands | Select-Object -First 20)) {
    Write-Host "  $($m.Value)"
}
