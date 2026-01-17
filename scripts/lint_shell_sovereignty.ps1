# scripts/lint_shell_sovereignty.ps1
# Fails if PowerShell is nested inside Bash (hard violation)

$ErrorActionPreference = "Stop"

$forbiddenPatterns = @(
    'Bash\s*\(\s*pwsh',
    'bash\s+-lc\s+["''].*pwsh',
    'Bash\s*\(\s*PowerShell'
)

# Scan specific directories only (avoid node_modules, .git, etc.)
$scanPaths = @('scripts', 'docs', '.github')
$files = @()

foreach ($path in $scanPaths) {
    if (Test-Path $path) {
        $files += Get-ChildItem -Path $path -Recurse -File -Include *.ps1,*.yml,*.yaml,*.md -ErrorAction SilentlyContinue
    }
}

$violations = @()

foreach ($file in $files) {
    $matches = Select-String -Path $file.FullName -Pattern $forbiddenPatterns
    foreach ($m in $matches) {
        # Skip markdown files with backtick-enclosed patterns (documentation examples)
        if ($file.Extension -eq '.md' -and $m.Line -match '`') {
            continue
        }

        $violations += [PSCustomObject]@{
            File = $file.FullName.Replace("$PWD\", "")
            Line = $m.LineNumber
            Text = $m.Line.Trim()
        }
    }
}

if ($violations.Count -gt 0) {
    Write-Host "`n✗ Shell sovereignty violation detected:" -ForegroundColor Red
    $violations | Format-Table -AutoSize
    exit 1
}

Write-Host "✓ Shell sovereignty check passed" -ForegroundColor Green
exit 0
