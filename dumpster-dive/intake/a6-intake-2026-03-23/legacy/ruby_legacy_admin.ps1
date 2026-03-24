#!/usr/bin/env pwsh

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ruby_legacy_admin.ps1
# ║ Module: Toolchain PATH probe
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: PROBE
# ║ Semantic ID: SCRIPT_PROBE_TOOLCHAIN_PATH_V1
# ║ Purpose: Probe toolchain paths and emit curated PATH outputs
# ║ Exports: (none)
# ║ Flags/Modes: -ExtraRoots, -OutRoot, -ApplyToSession, -WriteVscodeSnippet
# ║ Cross-References: dumpster-dive/intake/toolchain-probe/
# ╚════════════════════════════════════════════════════════════════════════════

[CmdletBinding()]
param(
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'

function Test-IsAdmin {
    $current = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($current)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-RvExePath {
    foreach ($candidate in @(
        (Join-Path $env:USERPROFILE '.cargo\bin\rvw.exe'),
        (Join-Path $env:USERPROFILE '.cargo\bin\rv.exe')
    )) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Get-RvRubyInfo {
    $rvExe = Get-RvExePath
    if (-not $rvExe) {
        return [pscustomobject]@{
            rv_exe = $null
            ruby_path = $null
            rv_version = $null
            ruby_version = $null
            msys2_path = $null
        }
    }

    $rubyPath = $null
    $rubyVersion = $null
    $rvVersion = $null
    $msys2Path = $null

    try { $rvVersion = (& $rvExe --version | Select-Object -First 1).Trim() } catch {}
    try { $rubyPath = (& $rvExe ruby find 2>$null | Select-Object -First 1).ToString().Trim() } catch {}
    try { $rubyVersion = (& $rvExe r ruby -v 2>$null | Select-Object -First 1).Trim() } catch {}
    try {
        $ridkLines = & $rvExe r ridk version 2>$null
        foreach ($line in $ridkLines) {
            if ($line -match '^\s*path:\s*(.+msys64)\s*$') {
                $msys2Path = $matches[1].Trim()
            }
        }
    } catch {}

    return [pscustomobject]@{
        rv_exe = $rvExe
        ruby_path = $rubyPath
        rv_version = $rvVersion
        ruby_version = $rubyVersion
        msys2_path = $msys2Path
    }
}

function Format-Bytes {
    param([Nullable[long]]$Bytes)

    if ($null -eq $Bytes) { return 'unknown' }

    $value = [double]$Bytes
    foreach ($unit in @('B', 'KB', 'MB', 'GB', 'TB')) {
        if ($value -lt 1024 -or $unit -eq 'TB') {
            return ('{0:N2} {1}' -f $value, $unit)
        }
        $value /= 1024
    }
}

function Get-DirectorySize {
    param([string]$Path)

    if (-not (Test-Path $Path)) { return $null }

    try {
        return (Get-ChildItem $Path -Recurse -File -Force -ErrorAction Stop | Measure-Object -Property Length -Sum).Sum
    } catch {
        try {
            return (Get-ChildItem $Path -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        } catch {
            return $null
        }
    }
}

function Get-RubyPathEntries {
    param([string]$Scope)

    $pathValue = [Environment]::GetEnvironmentVariable('Path', $Scope)
    if (-not $pathValue) { return @() }

    return @(
        $pathValue -split ';' |
            Where-Object { $_ -match 'Ruby|rv\\rubies|msys64' } |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ }
    )
}

function Get-LegacyRoots {
    return @(
        Get-ChildItem 'C:\' -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like 'Ruby*' } |
            Sort-Object Name |
            ForEach-Object {
                [pscustomobject]@{
                    path = $_.FullName
                    exists = $true
                    size_bytes = Get-DirectorySize $_.FullName
                    top_level = @(
                        Get-ChildItem $_.FullName -Force -ErrorAction SilentlyContinue |
                            Select-Object -First 10 -ExpandProperty Name
                    )
                }
            }
    )
}

function Get-QuarantineRoots {
    $base = Join-Path $env:APPDATA 'rv\quarantine'
    if (-not (Test-Path $base)) { return @() }

    return @(
        Get-ChildItem $base -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like 'legacy-pre-rv-*' } |
            Sort-Object Name -Descending |
            ForEach-Object {
                [pscustomobject]@{
                    path = $_.FullName
                    size_bytes = Get-DirectorySize $_.FullName
                    entries = @(
                        Get-ChildItem $_.FullName -Force -ErrorAction SilentlyContinue |
                            Select-Object -ExpandProperty Name
                    )
                }
            }
    )
}

function Get-RubyUninstallEntries {
    $roots = @(
        'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall',
        'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall',
        'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
    )

    $entries = foreach ($root in $roots) {
        foreach ($item in Get-ChildItem $root -ErrorAction SilentlyContinue) {
            try {
                $props = Get-ItemProperty $item.PSPath -ErrorAction Stop
                if (($props.DisplayName -match 'Ruby|MSYS2') -or ($props.InstallLocation -match '^C:\\Ruby')) {
                    [pscustomobject]@{
                        key = $item.PSPath
                        display_name = $props.DisplayName
                        display_version = $props.DisplayVersion
                        install_location = $props.InstallLocation
                        uninstall_string = $props.UninstallString
                    }
                }
            } catch {}
        }
    }

    return @($entries | Sort-Object display_name, install_location)
}

function Get-BundleTkConfig {
    $configPath = Join-Path $env:USERPROFILE '.bundle\config'
    if (-not (Test-Path $configPath)) {
        return [pscustomobject]@{
            path = $configPath
            value = $null
        }
    }

    $value = $null
    foreach ($line in Get-Content $configPath -ErrorAction SilentlyContinue) {
        if ($line -match '^BUNDLE_BUILD__TK:\s*"(.*)"\s*$') {
            $value = $matches[1]
        }
    }

    return [pscustomobject]@{
        path = $configPath
        value = $value
    }
}

function Get-LegacyUserGemHomes {
    $root = Join-Path $env:USERPROFILE '.gem\ruby'
    if (-not (Test-Path $root)) { return @() }

    return @(
        Get-ChildItem $root -Directory -ErrorAction SilentlyContinue |
            Sort-Object Name |
            ForEach-Object {
                [pscustomobject]@{
                    path = $_.FullName
                    size_bytes = Get-DirectorySize $_.FullName
                    gems = @(
                        Get-ChildItem (Join-Path $_.FullName 'specifications') -Filter *.gemspec -ErrorAction SilentlyContinue |
                            Select-Object -ExpandProperty BaseName |
                            Sort-Object
                    )
                }
            }
    )
}

function Get-ProcessesUsingRoot {
    param([string]$Root)

    if (-not (Test-Path $Root)) { return @() }

    return @(
        Get-Process -ErrorAction SilentlyContinue |
            ForEach-Object {
                try {
                    if ($_.Path -and $_.Path.StartsWith($Root, [System.StringComparison]::OrdinalIgnoreCase)) {
                        [pscustomobject]@{
                            name = $_.ProcessName
                            id = $_.Id
                            path = $_.Path
                        }
                    }
                } catch {}
            }
    )
}

function Remove-DeadMachineRubyPathEntries {
    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    if (-not $machinePath) { return @() }

    $removed = [System.Collections.Generic.List[string]]::new()
    $kept = foreach ($entry in ($machinePath -split ';')) {
        if (-not $entry) { continue }
        if ($entry -match '^[A-Za-z]:\\Ruby[^\\]*\\bin$' -and -not (Test-Path $entry)) {
            $removed.Add($entry) | Out-Null
            continue
        }
        $entry
    }

    if ($removed.Count -gt 0) {
        [Environment]::SetEnvironmentVariable('Path', ($kept -join ';'), 'Machine')
    }

    return @($removed)
}

function Remove-StaleMsys2Entries {
    param([string]$ActiveMsys2Path)

    $removed = [System.Collections.Generic.List[string]]::new()
    $regBase = 'HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall'

    foreach ($entry in Get-RubyUninstallEntries) {
        if ($entry.display_name -ne 'MSYS2') { continue }
        if (-not $entry.install_location) { continue }
        if ($ActiveMsys2Path -and $entry.install_location -eq $ActiveMsys2Path) { continue }
        if (Test-Path $entry.install_location) { continue }

        $subkey = $entry.key -replace '^Microsoft\.PowerShell\.Core\\Registry::', ''
        $subkey = $subkey -replace '^HKEY_CURRENT_USER\\', 'HKCU\'
        if ($subkey -like "$regBase\*") {
            & reg.exe delete $subkey /f | Out-Null
            $removed.Add($subkey) | Out-Null
        }
    }

    return @($removed)
}

function Move-ToQuarantine {
    param(
        [string]$SourcePath,
        [string]$QuarantineRoot
    )

    if (-not (Test-Path $SourcePath)) {
        return [pscustomobject]@{
            source = $SourcePath
            action = 'skip_missing'
            destination = $null
            error = $null
        }
    }

    $leaf = Split-Path $SourcePath -Leaf
    $destination = Join-Path $QuarantineRoot ($leaf + '_elevated')
    $suffix = 1
    while (Test-Path $destination) {
        $destination = Join-Path $QuarantineRoot ($leaf + "_elevated_$suffix")
        $suffix += 1
    }

    try {
        Move-Item -LiteralPath $SourcePath -Destination $destination -Force
        return [pscustomobject]@{
            source = $SourcePath
            action = 'moved'
            destination = $destination
            error = $null
        }
    } catch {
        return [pscustomobject]@{
            source = $SourcePath
            action = 'failed'
            destination = $destination
            error = $_.Exception.Message
        }
    }
}

function Add-ReportLine {
    param([string]$Text = '')
    $script:Report.Add($Text) | Out-Null
}

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$reportDir = Join-Path $env:APPDATA 'rv\reports'
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$reportPath = Join-Path $reportDir "ruby-legacy-admin-$stamp.md"
$script:Report = [System.Collections.Generic.List[string]]::new()

$isAdmin = Test-IsAdmin
$rvInfo = Get-RvRubyInfo
$legacyRoots = Get-LegacyRoots
$quarantineRoots = Get-QuarantineRoots
$rubyEntries = Get-RubyUninstallEntries
$bundleTk = Get-BundleTkConfig
$legacyUserGems = Get-LegacyUserGemHomes
$ruby34Processes = Get-ProcessesUsingRoot 'C:\Ruby34-x64'

$actions = [System.Collections.Generic.List[object]]::new()
if ($Apply) {
    if (-not $isAdmin) {
        throw 'Apply mode requires an elevated PowerShell session.'
    }

    $applyQuarantineRoot = Join-Path $env:APPDATA ("rv\quarantine\legacy-pre-rv-elevated-$stamp")
    New-Item -ItemType Directory -Force -Path $applyQuarantineRoot | Out-Null

    foreach ($item in @('C:\Ruby27-x64', 'C:\Ruby34-x64')) {
        $actions.Add((Move-ToQuarantine -SourcePath $item -QuarantineRoot $applyQuarantineRoot)) | Out-Null
    }

    $removedMachinePaths = Remove-DeadMachineRubyPathEntries
    if ($removedMachinePaths.Count -gt 0) {
        $actions.Add([pscustomobject]@{
            source = 'MachinePath'
            action = 'removed_entries'
            destination = $null
            error = ($removedMachinePaths -join '; ')
        }) | Out-Null
    }

    $removedKeys = Remove-StaleMsys2Entries -ActiveMsys2Path $rvInfo.msys2_path
    if ($removedKeys.Count -gt 0) {
        $actions.Add([pscustomobject]@{
            source = 'Registry'
            action = 'removed_keys'
            destination = $null
            error = ($removedKeys -join '; ')
        }) | Out-Null
    }

    $legacyRoots = Get-LegacyRoots
    $quarantineRoots = Get-QuarantineRoots
    $rubyEntries = Get-RubyUninstallEntries
    $ruby34Processes = Get-ProcessesUsingRoot 'C:\Ruby34-x64'
}

Add-ReportLine '# Ruby Legacy Admin Report'
Add-ReportLine
Add-ReportLine ("Generated: {0}" -f (Get-Date).ToString('yyyy-MM-dd HH:mm:ss zzz'))
Add-ReportLine ("Mode: {0}" -f $(if ($Apply) { 'apply' } else { 'audit' }))
Add-ReportLine ("Elevated: {0}" -f $isAdmin)
Add-ReportLine
Add-ReportLine '## Active rv Lane'
Add-ReportLine ("- rv executable: {0}" -f $(if ($rvInfo.rv_exe) { $rvInfo.rv_exe } else { 'not found' }))
Add-ReportLine ("- rv version: {0}" -f $(if ($rvInfo.rv_version) { $rvInfo.rv_version } else { 'unknown' }))
Add-ReportLine ("- ruby path: {0}" -f $(if ($rvInfo.ruby_path) { $rvInfo.ruby_path } else { 'unknown' }))
Add-ReportLine ("- ruby version: {0}" -f $(if ($rvInfo.ruby_version) { $rvInfo.ruby_version } else { 'unknown' }))
Add-ReportLine ("- msys2 path: {0}" -f $(if ($rvInfo.msys2_path) { $rvInfo.msys2_path } else { 'unknown' }))
Add-ReportLine
Add-ReportLine '## PATH Residue'
foreach ($scope in @('User', 'Machine')) {
    $entries = Get-RubyPathEntries -Scope $scope
    Add-ReportLine ("### {0}" -f $scope)
    if ($entries.Count -eq 0) {
        Add-ReportLine '- none'
    } else {
        foreach ($entry in $entries) {
            Add-ReportLine ("- {0}" -f $entry)
        }
    }
}
Add-ReportLine
Add-ReportLine '## Bundler'
Add-ReportLine ("- config: {0}" -f $bundleTk.path)
Add-ReportLine ("- build.tk: {0}" -f $(if ($bundleTk.value) { $bundleTk.value } else { 'not set' }))
Add-ReportLine
Add-ReportLine '## Legacy User Gem Homes'
if ($legacyUserGems.Count -eq 0) {
    Add-ReportLine '- none'
} else {
    foreach ($gemHome in $legacyUserGems) {
        Add-ReportLine ("- {0} ({1})" -f $gemHome.path, (Format-Bytes $gemHome.size_bytes))
        if ($gemHome.gems.Count -gt 0) {
            Add-ReportLine ("  gems: {0}" -f ($gemHome.gems -join ', '))
        }
    }
}
Add-ReportLine
Add-ReportLine '## Legacy Roots'
if ($legacyRoots.Count -eq 0) {
    Add-ReportLine '- none'
} else {
    foreach ($root in $legacyRoots) {
        Add-ReportLine ("- {0} ({1})" -f $root.path, (Format-Bytes $root.size_bytes))
        if ($root.top_level.Count -gt 0) {
            Add-ReportLine ("  top-level: {0}" -f ($root.top_level -join ', '))
        }
    }
}
Add-ReportLine
Add-ReportLine '## Quarantine'
if ($quarantineRoots.Count -eq 0) {
    Add-ReportLine '- none'
} else {
    foreach ($root in $quarantineRoots) {
        Add-ReportLine ("- {0} ({1})" -f $root.path, (Format-Bytes $root.size_bytes))
        if ($root.entries.Count -gt 0) {
            Add-ReportLine ("  entries: {0}" -f ($root.entries -join ', '))
        }
    }
}
Add-ReportLine
Add-ReportLine '## Registry Entries'
if ($rubyEntries.Count -eq 0) {
    Add-ReportLine '- none'
} else {
    foreach ($entry in $rubyEntries) {
        Add-ReportLine ("- {0} {1}" -f $entry.display_name, $(if ($entry.display_version) { "($($entry.display_version))" } else { '' }))
        Add-ReportLine ("  install: {0}" -f $entry.install_location)
        Add-ReportLine ("  key: {0}" -f $entry.key)
    }
}
Add-ReportLine
Add-ReportLine '## Processes Using C:\Ruby34-x64'
if ($ruby34Processes.Count -eq 0) {
    Add-ReportLine '- none found'
} else {
    foreach ($proc in $ruby34Processes) {
        Add-ReportLine ("- {0} [{1}] {2}" -f $proc.name, $proc.id, $proc.path)
    }
}

if ($Apply) {
    Add-ReportLine
    Add-ReportLine '## Apply Actions'
    if ($actions.Count -eq 0) {
        Add-ReportLine '- no actions were needed'
    } else {
        foreach ($action in $actions) {
            Add-ReportLine ("- {0}: {1}" -f $action.source, $action.action)
            if ($action.destination) {
                Add-ReportLine ("  destination: {0}" -f $action.destination)
            }
            if ($action.error) {
                Add-ReportLine ("  detail: {0}" -f $action.error)
            }
        }
    }
}

$reportText = $script:Report -join [Environment]::NewLine
Set-Content -Path $reportPath -Value $reportText -Encoding utf8
Write-Host "Ruby legacy report: $reportPath" -ForegroundColor Cyan
Write-Host $reportText
try {
    Invoke-Item $reportPath
} catch {}
