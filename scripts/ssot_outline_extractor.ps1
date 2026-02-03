<#
# ╔════════════════════════════════════════════════════════════════════════════╗
# ║ THE DECORATOR'S BLESSING: ssot_outline_extractor.ps1                      ║
# ║ Module: SSOT outline extractor                                            ║
# ╠════════════════════════════════════════════════════════════════════════════╣
# ║ Spectral Frequency: WHITE                                                 ║
# ║ Architectural Role: SSOT                                                  ║
# ║ Semantic ID: SCRIPT_SSOT_OUTLINE_EXTRACTOR_V1                              ║
# ║ Purpose: Extract SSOT outline and update structural index                 ║
# ║ Exports: (none)                                                           ║
# ║ Flags/Modes: -OutputJson, -Section, -Acronym, -UpdateIndex                 ║
# ║ Cross-References: .github/instructions/ssot-toolbox.instructions.md        ║
# ╚════════════════════════════════════════════════════════════════════════════╝
#>

<#
.SYNOPSIS
    SSOT Outline Extractor - Generates live outline from copilot-instructions.md headers
.DESCRIPTION
    Extracts markdown headers with line numbers, providing the same view as VS Code's Outline panel.
    Run this to regenerate the index after SSOT edits.
    
    ⚠️ AUTO-UPDATE RULE: After ANY edit to copilot-instructions.md, run:
       .\ssot_outline_extractor.ps1 -UpdateIndex
    
    This keeps SSOT_STRUCTURAL_INDEX.json synchronized.
    See: .github/instructions/ssot-toolbox.instructions.md for full toolbox docs.
.USAGE
    .\ssot_outline_extractor.ps1                    # Full outline to console
    .\ssot_outline_extractor.ps1 -OutputJson        # Output as JSON
    .\ssot_outline_extractor.ps1 -Section "FA1"     # Search for specific section
    .\ssot_outline_extractor.ps1 -Acronym "DCRP"    # Find acronym location
    .\ssot_outline_extractor.ps1 -UpdateIndex       # MANDATORY after SSOT edits
#>

param(
    [switch]$OutputJson,
    [string]$Section,
    [string]$Acronym,
    [switch]$UpdateIndex
)

$SSOTPath = Join-Path $PSScriptRoot "..\copilot-instructions.md"
$IndexPath = Join-Path $PSScriptRoot "SSOT_STRUCTURAL_INDEX.json"

if (-not (Test-Path $SSOTPath)) {
    Write-Error "SSOT not found at: $SSOTPath"
    exit 1
}

# Extract all headers with line numbers
$headers = New-Object System.Collections.ArrayList
$lineNum = 0
$content = Get-Content $SSOTPath

foreach ($line in $content) {
    $lineNum++
    
    # Check if line starts with ## ### or ####
    if ($line.StartsWith("##")) {
        # Count the hash marks
        $hashCount = 0
        for ($i = 0; $i -lt $line.Length -and $line[$i] -eq '#'; $i++) {
            $hashCount++
        }
        
        # Only process ## to #### (levels 2-4)
        if ($hashCount -ge 2 -and $hashCount -le 4) {
            $level = $hashCount
            $rawTitle = $line.Substring($hashCount).Trim()
            
            # Clean up bold markers
            $title = $rawTitle.Replace("**", "").Replace("``", "")
            
            # Extract acronyms in parentheses using simple regex
            $acronyms = New-Object System.Collections.ArrayList
            $acroPattern = [regex]"\(([A-Z][A-Z0-9_-]+)\)"
            $acroMatches = $acroPattern.Matches($title)
            foreach ($m in $acroMatches) {
                [void]$acronyms.Add($m.Groups[1].Value)
            }
            
            $entry = [PSCustomObject]@{
                Line = $lineNum
                Level = $level
                Title = $title.Trim()
                Acronyms = ($acronyms | Select-Object -Unique) -join ", "
                Indent = ("  " * ($level - 2))
            }
            [void]$headers.Add($entry)
        }
    }
}

# Filter by section search
if ($Section) {
    $headers = $headers | Where-Object { $_.Title -match $Section }
}

# Filter by acronym
if ($Acronym) {
    $headers = $headers | Where-Object { $_.Acronyms -match $Acronym -or $_.Title -match $Acronym }
}

# Output
if ($OutputJson) {
    $headers | ConvertTo-Json -Depth 3
} else {
    Write-Host ""
    Write-Host "SSOT OUTLINE - $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -ForegroundColor Cyan
    Write-Host "   Source: $SSOTPath" -ForegroundColor DarkGray
    Write-Host "   Total Headers: $($headers.Count)" -ForegroundColor DarkGray
    Write-Host ("-" * 80) -ForegroundColor DarkGray
    
    foreach ($h in $headers) {
        $lineStr = "{0,5}" -f $h.Line
        $acroStr = ""
        if ($h.Acronyms) { $acroStr = " [$($h.Acronyms)]" }
        
        $color = "DarkGray"
        if ($h.Level -eq 2) { $color = "Yellow" }
        elseif ($h.Level -eq 3) { $color = "White" }
        elseif ($h.Level -eq 4) { $color = "Gray" }
        
        Write-Host "$lineStr | $($h.Indent)$($h.Title)$acroStr" -ForegroundColor $color
    }
    
    Write-Host ("-" * 80) -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "Quick commands:" -ForegroundColor Green
    Write-Host "   .\ssot_outline_extractor.ps1 -Section 'FA1'     # Find FA1 sections" -ForegroundColor DarkGray
    Write-Host "   .\ssot_outline_extractor.ps1 -Acronym 'DCRP'    # Find DCRP" -ForegroundColor DarkGray
    Write-Host "   .\ssot_outline_extractor.ps1 -OutputJson        # JSON format" -ForegroundColor DarkGray
}

# Update the static index if requested
if ($UpdateIndex) {
    Write-Host ""
    Write-Host "Updating SSOT_STRUCTURAL_INDEX.json..." -ForegroundColor Yellow
    
    $indexData = [ordered]@{
        _WARNING = "AUTO-GENERATED FILE - Do not edit manually. Regenerate via: .\ssot_outline_extractor.ps1 -UpdateIndex"
        _toolbox = ".github/instructions/ssot-toolbox.instructions.md"
        _source = ".github/copilot-instructions.md"
        _generated = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        total_lines = $lineNum
        headers = @($headers | ForEach-Object {
            @{
                line = $_.Line
                level = $_.Level
                title = $_.Title
                acronyms = $_.Acronyms
            }
        })
    }
    
    $indexData | ConvertTo-Json -Depth 4 | Set-Content $IndexPath -Encoding UTF8
    Write-Host "Index updated at: $IndexPath" -ForegroundColor Green
}
