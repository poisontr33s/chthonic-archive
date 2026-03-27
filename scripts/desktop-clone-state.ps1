#!/usr/bin/env pwsh
#
# @SID: SCRIPT_DESKTOP_CLONE_STATE_V1
# @Type: UTILITY
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Export, restore, or verify a high-fidelity Chthonic desktop-clone state package.
#

<#
.SYNOPSIS
  Export, restore, or verify a high-fidelity Chthonic desktop-clone state package.

.DESCRIPTION
  Captures the user-level VS Code Insiders state, AI agent state, selected auth/config
  files, user-scope env vars, and the full repository working copy including .git.

  Export writes a portable package to a destination outside the repository by default.
  Restore replays that package onto another Windows user profile.

  For the closest possible "exact clone", close VS Code Insiders, Claude, Codex, and
  related shells before export/restore. Use -AllowLiveCapture only when you accept the
  risk of copying files that are still changing.

.USAGE
  pwsh -NoProfile -File scripts/desktop-clone-state.ps1 -Mode Export
  pwsh -NoProfile -File scripts/desktop-clone-state.ps1 -Mode Export -DryRun
  pwsh -NoProfile -File scripts/desktop-clone-state.ps1 -Mode Export -PackageRoot D:\transfer\clone
  pwsh -NoProfile -File scripts/desktop-clone-state.ps1 -Mode Restore -PackageRoot D:\transfer\clone
  pwsh -NoProfile -File scripts/desktop-clone-state.ps1 -Mode Restore -PackageRoot D:\transfer\clone -DryRun
  pwsh -NoProfile -File scripts/desktop-clone-state.ps1 -Mode Restore -PackageRoot D:\transfer\clone -StrictMirror
  pwsh -NoProfile -File scripts/desktop-clone-state.ps1 -Mode Verify -PackageRoot D:\transfer\clone
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Export", "Restore", "Verify")]
    [string]$Mode,

    [string]$PackageRoot,

    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),

    [string]$RestoreRepoRoot = $HOME,

    [string[]]$OnlyComponents,

    [string[]]$ExcludeComponents,

    [switch]$AllowLiveCapture,

    [switch]$StrictMirror,

    [switch]$CompressPackage,

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$script:SelfScriptPath = $PSCommandPath

function Write-Section {
    param([Parameter(Mandatory = $true)][string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Info {
    param([Parameter(Mandatory = $true)][string]$Message)
    Write-Host "  $Message" -ForegroundColor DarkGray
}

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Format-ByteSize {
    param([Parameter(Mandatory = $true)][double]$Bytes)

    if ($Bytes -ge 1TB) { return "{0:N2} TB" -f ($Bytes / 1TB) }
    if ($Bytes -ge 1GB) { return "{0:N2} GB" -f ($Bytes / 1GB) }
    if ($Bytes -ge 1MB) { return "{0:N2} MB" -f ($Bytes / 1MB) }
    if ($Bytes -ge 1KB) { return "{0:N2} KB" -f ($Bytes / 1KB) }
    return "{0:N0} B" -f $Bytes
}

function Get-PathStats {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][ValidateSet("file", "directory")][string]$Kind
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return @{
            exists = $false
            bytes = [int64]0
            file_count = 0
        }
    }

    if ($Kind -eq "file") {
        $item = Get-Item -LiteralPath $Path
        return @{
            exists = $true
            bytes = [int64]$item.Length
            file_count = 1
        }
    }

    $measure = Get-ChildItem -LiteralPath $Path -Recurse -Force -File -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum

    return @{
        exists = $true
        bytes = [int64]$measure.Sum
        file_count = [int]$measure.Count
    }
}

function Resolve-NormalizedPath {
    param([Parameter(Mandatory = $true)][string]$Path)
    return [System.IO.Path]::GetFullPath($Path)
}

function Test-PathWithin {
    param(
        [Parameter(Mandatory = $true)][string]$Parent,
        [Parameter(Mandatory = $true)][string]$Child
    )

    $parentFull = (Resolve-NormalizedPath -Path $Parent).TrimEnd('\') + '\'
    $childFull = (Resolve-NormalizedPath -Path $Child).TrimEnd('\') + '\'
    return $childFull.StartsWith($parentFull, [System.StringComparison]::OrdinalIgnoreCase)
}

function Get-DefaultPackageRoot {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    return Join-Path $HOME "Desktop\chthonic-desktop-clone-$stamp"
}

function Test-RobocopySuccess {
    param([int]$ExitCode)
    return $ExitCode -le 7
}

function Invoke-RobocopyTransfer {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [switch]$Mirror
    )

    Ensure-Directory -Path $Destination

    $args = @(
        $Source,
        $Destination,
        "/COPY:DAT",
        "/DCOPY:DAT",
        "/R:1",
        "/W:1",
        "/XJ",
        "/FFT",
        "/NP",
        "/NFL",
        "/NDL",
        "/NJH",
        "/NJS"
    )

    if ($Mirror) {
        $args += "/MIR"
    } else {
        $args += "/E"
    }

    & robocopy @args | Out-Null
    $exitCode = $LASTEXITCODE
    if (-not (Test-RobocopySuccess -ExitCode $exitCode)) {
        throw "robocopy failed for `"$Source`" -> `"$Destination`" with exit code $exitCode"
    }
}

function Copy-PortableFile {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    Ensure-Directory -Path (Split-Path -Parent $Destination)
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

function Get-ProfileComponents {
    $components = @()

    $profileMap = @{
        "ps-profile-currenthost" = $PROFILE.CurrentUserCurrentHost
        "ps-profile-allhosts"    = $PROFILE.CurrentUserAllHosts
    }

    foreach ($key in ($profileMap.Keys | Sort-Object)) {
        $path = $profileMap[$key]
        if ([string]::IsNullOrWhiteSpace($path)) {
            continue
        }

        $normalized = Resolve-NormalizedPath -Path $path
        $payloadRel = "home\profiles\$([System.IO.Path]::GetFileName($normalized))"

        $components += [ordered]@{
            id = $key
            kind = "file"
            source = $normalized
            payload_rel = $payloadRel
            target_root = "literal"
            target_rel = $normalized
            required = $false
            description = "PowerShell profile snapshot"
        }
    }

    return $components
}

function Get-CloneComponents {
    param([Parameter(Mandatory = $true)][string]$SourceRepoRoot)

    $repoFull = Resolve-NormalizedPath -Path $SourceRepoRoot
    $repoLeaf = Split-Path -Leaf $repoFull

    $components = @(
        [ordered]@{
            id = "vscode-user"
            kind = "directory"
            source = Resolve-NormalizedPath -Path (Join-Path $env:APPDATA "Code - Insiders\User")
            payload_rel = "appdata\Code - Insiders\User"
            target_root = "appdata"
            target_rel = "Code - Insiders\User"
            required = $true
            description = "VS Code Insiders user state"
        },
        [ordered]@{
            id = "vscode-extensions"
            kind = "directory"
            source = Resolve-NormalizedPath -Path (Join-Path $HOME ".vscode-insiders\extensions")
            payload_rel = "home\.vscode-insiders\extensions"
            target_root = "home"
            target_rel = ".vscode-insiders\extensions"
            required = $true
            description = "Installed VS Code Insiders extensions"
        },
        [ordered]@{
            id = "agents"
            kind = "directory"
            source = Resolve-NormalizedPath -Path (Join-Path $HOME ".agents")
            payload_rel = "home\.agents"
            target_root = "home"
            target_rel = ".agents"
            required = $false
            description = "Agent skill home"
        },
        [ordered]@{
            id = "claude"
            kind = "directory"
            source = Resolve-NormalizedPath -Path (Join-Path $HOME ".claude")
            payload_rel = "home\.claude"
            target_root = "home"
            target_rel = ".claude"
            required = $false
            description = "Claude local state"
        },
        [ordered]@{
            id = "codex"
            kind = "directory"
            source = Resolve-NormalizedPath -Path (Join-Path $HOME ".codex")
            payload_rel = "home\.codex"
            target_root = "home"
            target_rel = ".codex"
            required = $false
            description = "Codex local state"
        },
        [ordered]@{
            id = "chthonic-home"
            kind = "directory"
            source = Resolve-NormalizedPath -Path (Join-Path $HOME ".chthonic")
            payload_rel = "home\.chthonic"
            target_root = "home"
            target_rel = ".chthonic"
            required = $false
            description = "API pool and Chthonic home state"
        },
        [ordered]@{
            id = "github-cli"
            kind = "directory"
            source = Resolve-NormalizedPath -Path (Join-Path $env:APPDATA "GitHub CLI")
            payload_rel = "appdata\GitHub CLI"
            target_root = "appdata"
            target_rel = "GitHub CLI"
            required = $false
            description = "GitHub CLI config and hosts"
        },
        [ordered]@{
            id = "gitconfig"
            kind = "file"
            source = Resolve-NormalizedPath -Path (Join-Path $HOME ".gitconfig")
            payload_rel = "home\.gitconfig"
            target_root = "home"
            target_rel = ".gitconfig"
            required = $false
            description = "Global git config"
        },
        [ordered]@{
            id = "git-credentials"
            kind = "file"
            source = Resolve-NormalizedPath -Path (Join-Path $HOME ".git-credentials")
            payload_rel = "home\.git-credentials"
            target_root = "home"
            target_rel = ".git-credentials"
            required = $false
            description = "Stored HTTPS git credentials"
        },
        [ordered]@{
            id = "repo"
            kind = "directory"
            source = $repoFull
            payload_rel = "repo\$repoLeaf"
            target_root = "repo-root"
            target_rel = $repoLeaf
            required = $true
            description = "Full repository working copy including .git"
        }
    )

    $components += Get-ProfileComponents
    return $components
}

function Filter-Components {
    param(
        [Parameter(Mandatory = $true)][object[]]$Components,
        [string[]]$Only,
        [string[]]$Exclude
    )

    $result = $Components

    if ($Only -and $Only.Count -gt 0) {
        $wanted = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        foreach ($item in $Only) {
            [void]$wanted.Add($item)
        }
        $result = @($result | Where-Object { $wanted.Contains([string]$_.id) })
    }

    if ($Exclude -and $Exclude.Count -gt 0) {
        $blocked = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
        foreach ($item in $Exclude) {
            [void]$blocked.Add($item)
        }
        $result = @($result | Where-Object { -not $blocked.Contains([string]$_.id) })
    }

    return $result
}

function Get-TargetRootPath {
    param(
        [Parameter(Mandatory = $true)][ValidateSet("home", "appdata", "literal", "repo-root")][string]$Kind,
        [Parameter(Mandatory = $true)][string]$RepoRestoreBase
    )

    switch ($Kind) {
        "home" { return $HOME }
        "appdata" { return $env:APPDATA }
        "literal" { return "" }
        "repo-root" { return $RepoRestoreBase }
    }
}

function Get-LiveProcessReport {
    $patterns = @(
        "*Code*Insiders*",
        "*claude*",
        "*codex*",
        "*chatgpt*",
        "*openai*"
    )

    $matches = @(
        Get-Process -ErrorAction SilentlyContinue |
            Where-Object {
                $name = $_.ProcessName
                $isMatch = $false
                foreach ($pattern in $patterns) {
                    if ($name -like $pattern) {
                        $isMatch = $true
                        break
                    }
                }
                $isMatch
            } |
            Sort-Object ProcessName |
            Select-Object -Property ProcessName, Id
    )

    return $matches
}

function Assert-LiveCapturePolicy {
    param(
        [Parameter(Mandatory = $true)][string]$CurrentMode,
        [switch]$Bypass
    )

    $live = Get-LiveProcessReport
    if (-not $live -or $live.Count -eq 0) {
        return $live
    }

    if ($Bypass) {
        Write-Host "warning: live processes detected during $CurrentMode; capture may be non-identical." -ForegroundColor Yellow
        foreach ($proc in $live) {
            Write-Host ("  {0} ({1})" -f $proc.ProcessName, $proc.Id) -ForegroundColor Yellow
        }
        return $live
    }

    $lines = $live | ForEach-Object { "{0} ({1})" -f $_.ProcessName, $_.Id }
    throw "$CurrentMode requires a quiet state for exactness. Close these processes or rerun with -AllowLiveCapture:`n$($lines -join [Environment]::NewLine)"
}

function Get-PortableEnvEntries {
    $prefixes = @(
        "GITHUB_",
        "HF_",
        "HUGGINGFACE_",
        "OPENAI_",
        "ANTHROPIC_",
        "GOOGLE_",
        "GEMINI_",
        "POE_"
    )

    $explicit = @(
        "GITHUB_TOKEN",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "HF_TOKEN",
        "HUGGINGFACE_HUB_TOKEN",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY"
    )

    $userVars = [Environment]::GetEnvironmentVariables("User")
    $processVars = [Environment]::GetEnvironmentVariables("Process")
    $names = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

    foreach ($name in $explicit) {
        [void]$names.Add($name)
    }

    foreach ($source in @($userVars, $processVars)) {
        foreach ($name in $source.Keys) {
            foreach ($prefix in $prefixes) {
                if ([string]$name -like "$prefix*") {
                    [void]$names.Add([string]$name)
                    break
                }
            }
        }
    }

    $entries = @()
    foreach ($name in (@($names) | Sort-Object)) {
        $userValue = [string][Environment]::GetEnvironmentVariable($name, "User")
        $processValue = [string][Environment]::GetEnvironmentVariable($name, "Process")

        if (-not [string]::IsNullOrWhiteSpace($userValue)) {
            $entries += [ordered]@{
                name = $name
                value = $userValue
                source = "User"
            }
            continue
        }

        if (-not [string]::IsNullOrWhiteSpace($processValue)) {
            $entries += [ordered]@{
                name = $name
                value = $processValue
                source = "Process"
            }
        }
    }

    return $entries
}

function Get-ThemeState {
    $userSettingsPath = Join-Path $env:APPDATA "Code - Insiders\User\settings.json"
    if (-not (Test-Path -LiteralPath $userSettingsPath)) {
        return $null
    }

    try {
        $settings = Get-Content -LiteralPath $userSettingsPath -Raw | ConvertFrom-Json
        return @{
            color_theme = $settings.'workbench.colorTheme'
            icon_theme = $settings.'workbench.iconTheme'
            product_icon_theme = $settings.'workbench.productIconTheme'
        }
    } catch {
        return @{
            parse_error = [string]$_
        }
    }
}

function Get-RepoMetadataSummary {
    param([Parameter(Mandatory = $true)][string]$SourceRepoRoot)

    Push-Location $SourceRepoRoot
    try {
        $status = git status --short --branch
        $branches = git branch -vv
        $remotes = git remote -v
        $stashList = git stash list
        $head = git rev-parse HEAD

        $stashes = @()
        if (-not [string]::IsNullOrWhiteSpace($stashList)) {
            $lines = @($stashList -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
            foreach ($line in $lines) {
                if ($line -match '^(stash@\{\d+\}):\s+(.*)$') {
                    $stashes += [ordered]@{
                        ref = $Matches[1]
                        description = $Matches[2]
                    }
                }
            }
        }

        return @{
            head = $head
            status = $status
            branches = $branches
            remotes = $remotes
            stash_list = $stashList
            stash_count = $stashes.Count
            stashes = $stashes
        }
    }
    finally {
        Pop-Location
    }
}

function Export-EnvPayload {
    param([Parameter(Mandatory = $true)][string]$PayloadRoot)

    $envDir = Join-Path $PayloadRoot "env"
    Ensure-Directory -Path $envDir

    $entries = @(Get-PortableEnvEntries)
    $jsonPath = Join-Path $envDir "user-env.json"
    $scriptPath = Join-Path $envDir "Set-UserEnv.ps1"

    $entries | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $jsonPath -Encoding utf8NoBOM

    $scriptLines = @(
        "#!/usr/bin/env pwsh",
        "Set-StrictMode -Version Latest",
        '$ErrorActionPreference = "Stop"',
        '$envFile = Join-Path $PSScriptRoot "user-env.json"',
        '$entries = Get-Content -LiteralPath $envFile -Raw | ConvertFrom-Json',
        'foreach ($entry in $entries) {',
        '    [Environment]::SetEnvironmentVariable([string]$entry.name, [string]$entry.value, "User")',
        '}',
        'Write-Host "ok: restored user env vars (restart VS Code Insiders to pick them up)." -ForegroundColor Green'
    )
    Set-Content -LiteralPath $scriptPath -Value $scriptLines -Encoding utf8NoBOM

    return @{
        count = $entries.Count
        names = @($entries | ForEach-Object { $_.name })
        json_path = $jsonPath
        script_path = $scriptPath
    }
}

function Export-RepoMetadata {
    param(
        [Parameter(Mandatory = $true)][string]$SourceRepoRoot,
        [Parameter(Mandatory = $true)][string]$PayloadRoot
    )

    $gitDir = Join-Path $PayloadRoot "git"
    Ensure-Directory -Path $gitDir

    $summary = Get-RepoMetadataSummary -SourceRepoRoot $SourceRepoRoot

    Set-Content -LiteralPath (Join-Path $gitDir "status.txt") -Value $summary.status -Encoding utf8NoBOM
    Set-Content -LiteralPath (Join-Path $gitDir "branches.txt") -Value $summary.branches -Encoding utf8NoBOM
    Set-Content -LiteralPath (Join-Path $gitDir "remotes.txt") -Value $summary.remotes -Encoding utf8NoBOM
    Set-Content -LiteralPath (Join-Path $gitDir "stash-list.txt") -Value $summary.stash_list -Encoding utf8NoBOM
    Set-Content -LiteralPath (Join-Path $gitDir "head.txt") -Value $summary.head -Encoding utf8NoBOM

    $stashes = @()
    if ($summary.stashes.Count -gt 0) {
        Push-Location $SourceRepoRoot
        try {
            foreach ($stash in $summary.stashes) {
                $ref = [string]$stash.ref
                $desc = [string]$stash.description
                $safeName = $ref.Replace("{", "").Replace("}", "").Replace("@", "").Replace(":", "-")
                $patchPath = Join-Path $gitDir "$safeName.patch"
                $patch = git stash show -p $ref
                Set-Content -LiteralPath $patchPath -Value $patch -Encoding utf8NoBOM
                $stashes += [ordered]@{
                    ref = $ref
                    description = $desc
                    patch = [System.IO.Path]::GetFileName($patchPath)
                }
            }
        }
        finally {
            Pop-Location
        }
    }

    return @{
        head = $summary.head
        stash_count = $stashes.Count
        stashes = $stashes
    }
}

function Copy-ComponentIntoPackage {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Component,
        [Parameter(Mandatory = $true)][string]$PackagePayloadRoot
    )

    $source = [string]$Component.source
    $payloadPath = Join-Path $PackagePayloadRoot ([string]$Component.payload_rel)

    if (-not (Test-Path -LiteralPath $source)) {
        return @{
            id = $Component.id
            status = "missing"
            source = $source
            payload = $payloadPath
            description = $Component.description
        }
    }

    Write-Info ("copying {0}" -f $Component.id)
    if ($Component.kind -eq "directory") {
        Invoke-RobocopyTransfer -Source $source -Destination $payloadPath
    } else {
        Copy-PortableFile -Source $source -Destination $payloadPath
    }

    return @{
        id = $Component.id
        status = "copied"
        source = $source
        payload = $payloadPath
        description = $Component.description
    }
}

function Restore-ComponentFromPackage {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Component,
        [Parameter(Mandatory = $true)][string]$PackagePayloadRoot,
        [Parameter(Mandatory = $true)][string]$RepoRestoreBase,
        [switch]$Mirror
    )

    $payloadPath = Join-Path $PackagePayloadRoot ([string]$Component.payload_rel)
    if (-not (Test-Path -LiteralPath $payloadPath)) {
        return @{
            id = $Component.id
            status = "missing-payload"
            payload = $payloadPath
        }
    }

    $targetRoot = Get-TargetRootPath -Kind $Component.target_root -RepoRestoreBase $RepoRestoreBase
    if ($Component.target_root -eq "literal") {
        $targetPath = [string]$Component.target_rel
    } else {
        $targetPath = Join-Path $targetRoot ([string]$Component.target_rel)
    }

    Write-Info ("restoring {0}" -f $Component.id)
    if ($Component.kind -eq "directory") {
        Invoke-RobocopyTransfer -Source $payloadPath -Destination $targetPath -Mirror:$Mirror
    } else {
        Copy-PortableFile -Source $payloadPath -Destination $targetPath
    }

    return @{
        id = $Component.id
        status = "restored"
        payload = $payloadPath
        target = $targetPath
    }
}

function Write-RestoreNotes {
    param(
        [Parameter(Mandatory = $true)][string]$PackagePath,
        [Parameter(Mandatory = $true)][string]$ScriptName
    )

    $notes = @(
        "Chthonic desktop clone package",
        "",
        "Recommended restore:",
        "pwsh -NoProfile -File .\$ScriptName -Mode Restore -PackageRoot `"$PackagePath`"",
        "",
        "For the closest possible mirror, close VS Code Insiders, Claude, Codex, and related shells first.",
        "Add -StrictMirror if you want directory payloads to purge extra destination files."
    )

    Set-Content -LiteralPath (Join-Path $PackagePath "RESTORE_COMMANDS.txt") -Value $notes -Encoding utf8NoBOM
}

function Invoke-ExportDryRun {
    param(
        [Parameter(Mandatory = $true)][string]$DestinationPackageRoot,
        [Parameter(Mandatory = $true)][string]$SourceRepoRoot,
        [Parameter(Mandatory = $true)][object[]]$ComponentSelection
    )

    $packageRoot = Resolve-NormalizedPath -Path $DestinationPackageRoot
    $repoFull = Resolve-NormalizedPath -Path $SourceRepoRoot
    $payloadRoot = Join-Path $packageRoot "payload"
    $issues = @()

    if (Test-PathWithin -Parent $repoFull -Child $packageRoot) {
        $issues += "PackageRoot is inside the repository and a real export would be blocked."
    }

    if (Test-Path -LiteralPath $packageRoot) {
        $issues += "PackageRoot already exists and a real export would be blocked."
    }

    $live = Get-LiveProcessReport
    $selected = @($ComponentSelection)
    $componentResults = @()
    [int64]$totalBytes = 0
    [int64]$totalFiles = 0

    foreach ($component in $selected) {
        $source = [string]$component.source
        $payloadPath = Join-Path $payloadRoot ([string]$component.payload_rel)
        $stats = Get-PathStats -Path $source -Kind ([string]$component.kind)
        $status = if ($stats.exists) { "would-copy" } else { "missing" }

        if ($stats.exists) {
            $totalBytes += $stats.bytes
            $totalFiles += $stats.file_count
        }

        $componentResults += [ordered]@{
            id = $component.id
            status = $status
            kind = $component.kind
            source = $source
            payload = $payloadPath
            bytes = $stats.bytes
            file_count = $stats.file_count
            description = $component.description
        }
    }

    $envEntries = @(Get-PortableEnvEntries)
    $repoSummary = Get-RepoMetadataSummary -SourceRepoRoot $repoFull
    $themeState = Get-ThemeState

    Write-Section "Dry Run: Export"
    Write-Info ("package root: {0}" -f $packageRoot)
    Write-Info ("repo root: {0}" -f $repoFull)
    Write-Info ("selected components: {0}" -f $selected.Count)
    Write-Info ("estimated payload: {0} across {1} files" -f (Format-ByteSize -Bytes $totalBytes), $totalFiles)
    Write-Info ("env vars to capture: {0}" -f $envEntries.Count)
    Write-Info ("repo HEAD: {0}" -f $repoSummary.head)
    Write-Info ("stash patches to export: {0}" -f $repoSummary.stash_count)

    if ($themeState) {
        Write-Info ("themes: color=`"{0}`" icon=`"{1}`" product=`"{2}`"" -f $themeState.color_theme, $themeState.icon_theme, $themeState.product_icon_theme)
    }

    if ($live.Count -gt 0) {
        Write-Host "warning: live processes detected; an exact real export would require closing them or using -AllowLiveCapture." -ForegroundColor Yellow
        foreach ($proc in $live) {
            Write-Host ("  {0} ({1})" -f $proc.ProcessName, $proc.Id) -ForegroundColor Yellow
        }
    }

    if ($issues.Count -gt 0) {
        Write-Host "blockers:" -ForegroundColor Yellow
        foreach ($issue in $issues) {
            Write-Host ("  - {0}" -f $issue) -ForegroundColor Yellow
        }
    }

    Write-Section "Components"
    foreach ($result in $componentResults) {
        $sizeText = Format-ByteSize -Bytes $result.bytes
        Write-Host ("  [{0}] {1} :: {2} :: {3} :: {4}" -f $result.status, $result.id, $result.kind, $sizeText, $result.source)
    }

    if ($repoSummary.stashes.Count -gt 0) {
        Write-Section "Stashes"
        foreach ($stash in $repoSummary.stashes) {
            Write-Host ("  {0} :: {1}" -f $stash.ref, $stash.description)
        }
    }

    Write-Section "Dry Run Result"
    if ($issues.Count -eq 0) {
        Write-Host "Export simulation completed with no hard blockers." -ForegroundColor Green
    } else {
        Write-Host "Export simulation found blockers that would stop a real export." -ForegroundColor Yellow
    }
}

function Invoke-RestoreDryRun {
    param(
        [Parameter(Mandatory = $true)][string]$SourcePackageRoot,
        [Parameter(Mandatory = $true)][string]$SourceRepoRoot
    )

    $packageRoot = Resolve-NormalizedPath -Path $SourcePackageRoot
    $issues = @()

    if (-not (Test-Path -LiteralPath $packageRoot)) {
        throw "PackageRoot does not exist: $packageRoot"
    }

    $manifest = Import-Manifest -PackagePath $packageRoot
    $componentSourceRoot = if ($manifest.source.repo_root) { [string]$manifest.source.repo_root } else { $SourceRepoRoot }
    $components = Get-CloneComponents -SourceRepoRoot $componentSourceRoot
    $selected = Filter-Components -Components $components -Only $OnlyComponents -Exclude $ExcludeComponents
    $payloadRoot = Join-Path $packageRoot "payload"
    $live = Get-LiveProcessReport
    $restoreResults = @()
    [int64]$totalBytes = 0
    [int64]$totalFiles = 0

    foreach ($component in $selected) {
        $payloadPath = Join-Path $payloadRoot ([string]$component.payload_rel)
        $stats = Get-PathStats -Path $payloadPath -Kind ([string]$component.kind)
        $targetRoot = Get-TargetRootPath -Kind $component.target_root -RepoRestoreBase $RestoreRepoRoot
        $targetPath = if ($component.target_root -eq "literal") {
            [string]$component.target_rel
        } else {
            Join-Path $targetRoot ([string]$component.target_rel)
        }

        $status = if ($stats.exists) { "would-restore" } else { "missing-payload" }
        if ($stats.exists) {
            $totalBytes += $stats.bytes
            $totalFiles += $stats.file_count
        } else {
            $issues += "Missing payload for component `"$($component.id)`": $payloadPath"
        }

        $restoreResults += [ordered]@{
            id = $component.id
            status = $status
            kind = $component.kind
            payload = $payloadPath
            target = $targetPath
            bytes = $stats.bytes
            file_count = $stats.file_count
        }
    }

    $envFile = Join-Path $payloadRoot "env\user-env.json"
    $envEntries = @()
    if (Test-Path -LiteralPath $envFile) {
        $envEntries = @(Get-Content -LiteralPath $envFile -Raw | ConvertFrom-Json)
    } else {
        $issues += "Missing env payload: $envFile"
    }

    Write-Section "Dry Run: Restore"
    Write-Info ("package root: {0}" -f $packageRoot)
    Write-Info ("restore repo root base: {0}" -f (Resolve-NormalizedPath -Path $RestoreRepoRoot))
    Write-Info ("selected components: {0}" -f $selected.Count)
    Write-Info ("payload to restore: {0} across {1} files" -f (Format-ByteSize -Bytes $totalBytes), $totalFiles)
    Write-Info ("env vars to restore: {0}" -f $envEntries.Count)
    Write-Info ("strict mirror: {0}" -f [bool]$StrictMirror)

    if ($live.Count -gt 0) {
        Write-Host "warning: live processes detected; an exact real restore would require closing them or using -AllowLiveCapture." -ForegroundColor Yellow
        foreach ($proc in $live) {
            Write-Host ("  {0} ({1})" -f $proc.ProcessName, $proc.Id) -ForegroundColor Yellow
        }
    }

    if ($issues.Count -gt 0) {
        Write-Host "blockers:" -ForegroundColor Yellow
        foreach ($issue in $issues) {
            Write-Host ("  - {0}" -f $issue) -ForegroundColor Yellow
        }
    }

    Write-Section "Components"
    foreach ($result in $restoreResults) {
        $sizeText = Format-ByteSize -Bytes $result.bytes
        Write-Host ("  [{0}] {1} :: {2} :: {3} -> {4}" -f $result.status, $result.id, $result.kind, $sizeText, $result.target)
    }

    Write-Section "Dry Run Result"
    if ($issues.Count -eq 0) {
        Write-Host "Restore simulation completed with no hard blockers." -ForegroundColor Green
    } else {
        Write-Host "Restore simulation found blockers that would stop or degrade a real restore." -ForegroundColor Yellow
    }
}

function Export-ClonePackage {
    param(
        [Parameter(Mandatory = $true)][string]$DestinationPackageRoot,
        [Parameter(Mandatory = $true)][string]$SourceRepoRoot,
        [object[]]$ComponentSelection
    )

    $packageRoot = Resolve-NormalizedPath -Path $DestinationPackageRoot
    $repoFull = Resolve-NormalizedPath -Path $SourceRepoRoot

    if (Test-PathWithin -Parent $repoFull -Child $packageRoot) {
        throw "PackageRoot must live outside the repository so the repo copy can remain exact without recursion."
    }

    if (Test-Path -LiteralPath $packageRoot) {
        throw "PackageRoot already exists: $packageRoot"
    }

    $live = Assert-LiveCapturePolicy -CurrentMode "Export" -Bypass:$AllowLiveCapture

    $payloadRoot = Join-Path $packageRoot "payload"
    $manifestRoot = Join-Path $packageRoot "manifest"
    Ensure-Directory -Path $packageRoot
    Ensure-Directory -Path $payloadRoot
    Ensure-Directory -Path $manifestRoot

    $selected = @($ComponentSelection)
    Write-Section "Exporting components"
    $componentResults = @()
    foreach ($component in $selected) {
        $componentResults += Copy-ComponentIntoPackage -Component $component -PackagePayloadRoot $payloadRoot
    }

    Write-Section "Exporting env vars"
    $envPayload = Export-EnvPayload -PayloadRoot $payloadRoot
    Write-Info ("captured {0} user/process env vars" -f $envPayload.count)

    Write-Section "Exporting git metadata"
    $repoMetadata = Export-RepoMetadata -SourceRepoRoot $repoFull -PayloadRoot $payloadRoot
    Write-Info ("captured repo HEAD {0}" -f $repoMetadata.head)
    Write-Info ("captured {0} stash patch(es)" -f $repoMetadata.stash_count)

    $scriptName = [System.IO.Path]::GetFileName($script:SelfScriptPath)
    Copy-PortableFile -Source $script:SelfScriptPath -Destination (Join-Path $packageRoot $scriptName)
    Write-RestoreNotes -PackagePath $packageRoot -ScriptName $scriptName

    $themeState = Get-ThemeState

    $manifest = [ordered]@{
        version = 1
        created_at = (Get-Date).ToString("o")
        machine = @{
            computer_name = $env:COMPUTERNAME
            user_name = $env:USERNAME
        }
        source = @{
            repo_root = $repoFull
            package_root = $packageRoot
            live_capture = [bool]$AllowLiveCapture
            live_processes = @($live | ForEach-Object { "{0} ({1})" -f $_.ProcessName, $_.Id })
        }
        repo = @{
            leaf = Split-Path -Leaf $repoFull
            restore_root_default = $RestoreRepoRoot
            head = $repoMetadata.head
            stash_count = $repoMetadata.stash_count
        }
        env = @{
            names = $envPayload.names
            count = $envPayload.count
        }
        theme_state = $themeState
        selected_components = @($selected | ForEach-Object { $_.id })
        component_results = $componentResults
    }

    $manifestPath = Join-Path $manifestRoot "clone-manifest.json"
    $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8NoBOM

    if ($CompressPackage) {
        Write-Section "Compressing package"
        $zipPath = "$packageRoot.zip"
        if (Test-Path -LiteralPath $zipPath) {
            Remove-Item -LiteralPath $zipPath -Force
        }
        Compress-Archive -Path $packageRoot -DestinationPath $zipPath -Force
        Write-Info ("archive written to {0}" -f $zipPath)
    }

    Write-Section "Export complete"
    Write-Host $packageRoot -ForegroundColor Green
}

function Import-Manifest {
    param([Parameter(Mandatory = $true)][string]$PackagePath)

    $manifestPath = Join-Path $PackagePath "manifest\clone-manifest.json"
    if (-not (Test-Path -LiteralPath $manifestPath)) {
        throw "Missing manifest: $manifestPath"
    }

    return Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json -AsHashtable
}

function Restore-ClonePackage {
    param(
        [Parameter(Mandatory = $true)][string]$SourcePackageRoot,
        [Parameter(Mandatory = $true)][string]$SourceRepoRoot
    )

    $packageRoot = Resolve-NormalizedPath -Path $SourcePackageRoot
    $manifest = Import-Manifest -PackagePath $packageRoot
    $live = Assert-LiveCapturePolicy -CurrentMode "Restore" -Bypass:$AllowLiveCapture

    $componentSourceRoot = if ($manifest.source.repo_root) { [string]$manifest.source.repo_root } else { $SourceRepoRoot }
    $components = Get-CloneComponents -SourceRepoRoot $componentSourceRoot
    $selected = Filter-Components -Components $components -Only $OnlyComponents -Exclude $ExcludeComponents
    $payloadRoot = Join-Path $packageRoot "payload"

    Write-Section "Restoring components"
    $restoreResults = @()
    foreach ($component in $selected) {
        $restoreResults += Restore-ComponentFromPackage -Component $component -PackagePayloadRoot $payloadRoot -RepoRestoreBase $RestoreRepoRoot -Mirror:$StrictMirror
    }

    $envFile = Join-Path $payloadRoot "env\user-env.json"
    if (Test-Path -LiteralPath $envFile) {
        Write-Section "Restoring env vars"
        $entries = Get-Content -LiteralPath $envFile -Raw | ConvertFrom-Json
        foreach ($entry in $entries) {
            [Environment]::SetEnvironmentVariable([string]$entry.name, [string]$entry.value, "User")
        }
        Write-Info ("restored {0} env vars" -f @($entries).Count)
    }

    $restoreSummary = [ordered]@{
        restored_at = (Get-Date).ToString("o")
        package_root = $packageRoot
        strict_mirror = [bool]$StrictMirror
        live_capture = [bool]$AllowLiveCapture
        live_processes = @($live | ForEach-Object { "{0} ({1})" -f $_.ProcessName, $_.Id })
        results = $restoreResults
        source_manifest = $manifest
    }

    $summaryPath = Join-Path $packageRoot "manifest\restore-summary.json"
    $restoreSummary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $summaryPath -Encoding utf8NoBOM

    Write-Section "Restore complete"
    Write-Host "Desktop clone replayed. Restart VS Code Insiders to load restored env vars and state." -ForegroundColor Green
}

function Verify-ClonePackage {
    param([Parameter(Mandatory = $true)][string]$SourcePackageRoot)

    $packageRoot = Resolve-NormalizedPath -Path $SourcePackageRoot
    $manifest = Import-Manifest -PackagePath $packageRoot

    Write-Section "Package summary"
    Write-Host ("Package: {0}" -f $packageRoot) -ForegroundColor Green
    Write-Info ("Created: {0}" -f $manifest.created_at)
    Write-Info ("Machine: {0}\{1}" -f $manifest.machine.computer_name, $manifest.machine.user_name)
    Write-Info ("Repo head: {0}" -f $manifest.repo.head)
    Write-Info ("Stashes: {0}" -f $manifest.repo.stash_count)
    Write-Info ("Env vars: {0}" -f $manifest.env.count)

    Write-Section "Components"
    foreach ($result in $manifest.component_results) {
        Write-Host ("  [{0}] {1}" -f $result.status, $result.id)
    }

    $required = @(
        "payload\env\user-env.json",
        "payload\git\status.txt",
        "manifest\clone-manifest.json"
    )
    foreach ($item in $required) {
        $path = Join-Path $packageRoot $item
        if (-not (Test-Path -LiteralPath $path)) {
            throw "Package verification failed: missing $path"
        }
    }

    Write-Section "Verification complete"
    Write-Host "Package structure is valid." -ForegroundColor Green
}

if ([string]::IsNullOrWhiteSpace($PackageRoot)) {
    $PackageRoot = Get-DefaultPackageRoot
}

switch ($Mode) {
    "Export" {
        $resolvedRepoRoot = Resolve-NormalizedPath -Path $RepoRoot
        $components = Get-CloneComponents -SourceRepoRoot $resolvedRepoRoot
        $selectedComponents = Filter-Components -Components $components -Only $OnlyComponents -Exclude $ExcludeComponents
        if (-not $selectedComponents -or $selectedComponents.Count -eq 0) {
            throw "No components selected. Check -OnlyComponents / -ExcludeComponents values."
        }
        if ($DryRun) {
            Invoke-ExportDryRun -DestinationPackageRoot $PackageRoot -SourceRepoRoot $resolvedRepoRoot -ComponentSelection $selectedComponents
        } else {
            Export-ClonePackage -DestinationPackageRoot $PackageRoot -SourceRepoRoot $resolvedRepoRoot -ComponentSelection $selectedComponents
        }
    }
    "Restore" {
        if ($DryRun) {
            Invoke-RestoreDryRun -SourcePackageRoot $PackageRoot -SourceRepoRoot $RepoRoot
        } else {
            Restore-ClonePackage -SourcePackageRoot $PackageRoot -SourceRepoRoot $RepoRoot
        }
    }
    "Verify" {
        Verify-ClonePackage -SourcePackageRoot $PackageRoot
    }
}
