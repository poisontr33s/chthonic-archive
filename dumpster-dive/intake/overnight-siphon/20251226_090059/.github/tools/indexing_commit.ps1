[CmdletBinding()]
param(
    # Glob patterns (repo-relative) that are allowed to be staged/committed.
    [string[]]$AllowPatterns = @(
        '.github/copilot-instructions.md',
        '.github/instructions/**',
        '.github/tools/**',
        'dev/overnight_refactor_mode.md'
    ),

    # Commit message to use when -Execute is set.
    [string]$CommitMessage = 'Indexing allowlist commit',

    # Actually stage + commit. Without this switch, the script only reports what it would do.
    [switch]$Execute
)

$ErrorActionPreference = 'Stop'

function Resolve-GitExe {
    $candidates = @(
        "$env:ProgramFiles\Git\cmd\git.exe",
        "$env:ProgramFiles\Git\bin\git.exe",
        "$env:ProgramFiles(x86)\Git\cmd\git.exe",
        "$env:LocalAppData\Programs\Git\cmd\git.exe"
    ) | Where-Object { $_ -and (Test-Path $_) }

    if ($candidates.Count -gt 0) {
        return $candidates[0]
    }

    $where = "$env:WINDIR\System32\where.exe"
    if (Test-Path $where) {
        $found = & $where git 2>$null
        if ($found) {
            return ($found | Select-Object -First 1)
        }
    }

    throw 'git.exe not found (checked common install locations and where.exe).'
}

function Convert-GlobToRegex {
    param([Parameter(Mandatory = $true)][string]$Glob)

    $g = $Glob.Trim()
    if (-not $g) {
        return $null
    }

    # Normalize separators to '/' for matching.
    $g = $g -replace '\\', '/'

    # Escape regex metacharacters, then restore glob operators.
    $rx = [regex]::Escape($g)

    # Support ** (any path segments), * (single segment), ? (single char)
    $rx = $rx -replace '\\\*\\\*', '.*'
    $rx = $rx -replace '\\\*', '[^/]*'
    $rx = $rx -replace '\\\?', '.'

    return "^$rx$"
}

$git = Resolve-GitExe

$repoRoot = (& $git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
    throw 'Not inside a git repository (git rev-parse --show-toplevel returned empty).'
}

Push-Location $repoRoot
try {
    $allowRegexes = @(
        foreach ($p in $AllowPatterns) {
            $r = Convert-GlobToRegex -Glob $p
            if ($r) { $r }
        }
    )

    if ($allowRegexes.Count -eq 0) {
        throw 'AllowPatterns is empty after normalization.'
    }

    $status = & $git status --porcelain
    if (-not $status) {
        Write-Host 'Working tree clean.' -ForegroundColor Green
        exit 0
    }

    $changed = @(
        foreach ($line in $status) {
            if (-not $line) { continue }
            if ($line.Length -lt 4) { continue }

            $pathPart = $line.Substring(3).Trim()

            # Handle rename format: "R  old -> new"
            if ($pathPart -match '\s->\s') {
                $pathPart = ($pathPart -split '\s->\s')[-1]
            }

            $rel = $pathPart -replace '\\', '/'
            if ($rel) { $rel }
        }
    ) | Select-Object -Unique

    $allowedChanged = New-Object System.Collections.Generic.List[string]
    $blockedChanged = New-Object System.Collections.Generic.List[string]

    foreach ($p in $changed) {
        $isAllowed = $false
        foreach ($rx in $allowRegexes) {
            if ($p -match $rx) {
                $isAllowed = $true
                break
            }
        }

        if ($isAllowed) {
            $allowedChanged.Add($p)
        } else {
            $blockedChanged.Add($p)
        }
    }

    if ($blockedChanged.Count -gt 0) {
        Write-Host 'Blocked changes detected (outside allowlist):' -ForegroundColor Yellow
        $blockedChanged | Sort-Object | ForEach-Object { Write-Host "  $_" }
        Write-Host ''
        Write-Host 'Allowed patterns:' -ForegroundColor DarkGray
        $AllowPatterns | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
        Write-Host ''
        Write-Host 'Refusing to stage/commit while blocked changes exist.' -ForegroundColor Yellow
        exit 2
    }

    if ($allowedChanged.Count -eq 0) {
        Write-Host 'No changed files match allowlist.' -ForegroundColor DarkGray
        exit 0
    }

    Write-Host 'Allowed changed files:' -ForegroundColor Green
    $allowedChanged | Sort-Object | ForEach-Object { Write-Host "  $_" }

    if (-not $Execute) {
        Write-Host ''
        Write-Host "(Dry-run) Re-run with -Execute to stage + commit with message: $CommitMessage" -ForegroundColor DarkGray
        exit 0
    }

    foreach ($p in ($allowedChanged | Sort-Object)) {
        & $git add -- $p
    }

    # If nothing is staged, do not error.
    $staged = & $git diff --cached --name-only
    if (-not $staged) {
        Write-Host 'Nothing staged; nothing to commit.' -ForegroundColor DarkGray
        exit 0
    }

    & $git commit -m $CommitMessage
}
finally {
    Pop-Location
}
