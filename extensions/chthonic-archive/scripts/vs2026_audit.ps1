# @SID: EXT_VS2026_AUDIT_V1
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Strict
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-VsWherePath {
    $candidate = 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'
    if (Test-Path $candidate) {
        return $candidate
    }
    throw "vswhere.exe not found at '$candidate'"
}

function Get-VsInstance {
    param(
        [Parameter(Mandatory = $true)][string]$VsWhere,
        [Parameter(Mandatory = $true)][string]$ProductId
    )

    $raw = & $VsWhere -prerelease -latest -products $ProductId -format json
    if (-not $raw) {
        return $null
    }

    $parsed = $raw | ConvertFrom-Json
    if ($parsed -is [array]) {
        return $parsed[0]
    }

    return $parsed
}

function Get-InstalledPackageSet {
    param(
        [Parameter(Mandatory = $true)][string]$InstanceId
    )

    $statePath = Join-Path $env:ProgramData "Microsoft\VisualStudio\Packages\_Instances\$InstanceId\state.json"
    if (-not (Test-Path $statePath)) {
        return [System.Collections.Generic.HashSet[string]]::new()
    }

    $state = Get-Content -Path $statePath -Raw | ConvertFrom-Json
    $set = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($pkg in $state.selectedPackages) {
        [void]$set.Add([string]$pkg.id)
    }
    return $set
}

function Get-ConfigComponents {
    param(
        [Parameter(Mandatory = $true)][string]$ConfigPath
    )
    $cfg = Get-Content -Path $ConfigPath -Raw | ConvertFrom-Json
    return @($cfg.components)
}

function Get-MissingComponents {
    param(
        [Parameter(Mandatory = $true)][string[]]$Required,
        [Parameter(Mandatory = $true)][System.Collections.Generic.HashSet[string]]$Installed
    )

    $missing = New-Object System.Collections.Generic.List[string]
    foreach ($id in $Required) {
        if (-not $Installed.Contains($id)) {
            [void]$missing.Add($id)
        }
    }
    return $missing
}

function Convert-ToStringArray {
    param([Parameter()][object]$Value)
    if ($null -eq $Value) {
        return @()
    }
    if ($Value -is [string]) {
        return @([string]$Value)
    }
    if ($Value -is [System.Collections.IEnumerable]) {
        $items = New-Object System.Collections.Generic.List[string]
        foreach ($entry in $Value) {
            [void]$items.Add([string]$entry)
        }
        return @($items)
    }
    return @([string]$Value)
}

function Get-SafeCount {
    param([Parameter()][object]$Value)
    if ($null -eq $Value) {
        return 0
    }
    if ($Value -is [System.Collections.ICollection]) {
        return $Value.Count
    }
    if ($Value -is [string]) {
        return 1
    }
    if ($Value -is [System.Collections.IEnumerable]) {
        return @($Value).Count
    }
    return 1
}

function Resolve-LatestMsvcRoot {
    param(
        [Parameter(Mandatory = $true)][string]$InstallPath
    )

    $root = Join-Path $InstallPath 'VC\Tools\MSVC'
    if (-not (Test-Path $root)) {
        return $null
    }

    $latest = Get-ChildItem -Path $root -Directory | Sort-Object Name -Descending | Select-Object -First 1
    if (-not $latest) {
        return $null
    }
    return $latest.FullName
}

function Test-Binary {
    param([Parameter(Mandatory = $true)][string]$Path)
    return [pscustomobject]@{
        path = $Path
        exists = [bool](Test-Path $Path)
    }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$cfgRoot = Join-Path $repoRoot '.codex\visualStudioInstaller2026'
$proCfgPath = Join-Path $cfgRoot 'vs2026_pro_insiders.vsconfig'
$btCfgPath = Join-Path $cfgRoot 'vs2026_buildtools_lsl.vsconfig'

if (-not (Test-Path $proCfgPath)) {
    throw "Missing config: $proCfgPath"
}
if (-not (Test-Path $btCfgPath)) {
    throw "Missing config: $btCfgPath"
}

$vswhere = Resolve-VsWherePath
$proInstance = Get-VsInstance -VsWhere $vswhere -ProductId 'Microsoft.VisualStudio.Product.Professional'
$btInstance = Get-VsInstance -VsWhere $vswhere -ProductId 'Microsoft.VisualStudio.Product.BuildTools'

if (-not $proInstance) {
    throw 'Visual Studio Professional Insiders instance not found.'
}
if (-not $btInstance) {
    throw 'Visual Studio Build Tools Insiders instance not found.'
}

$proInstalled = Get-InstalledPackageSet -InstanceId ([string]$proInstance.instanceId)
$btInstalled = Get-InstalledPackageSet -InstanceId ([string]$btInstance.instanceId)

$proRequired = Get-ConfigComponents -ConfigPath $proCfgPath
$btRequired = Get-ConfigComponents -ConfigPath $btCfgPath

$proMissing = Get-MissingComponents -Required $proRequired -Installed $proInstalled
$btMissing = Get-MissingComponents -Required $btRequired -Installed $btInstalled
$proMissingItems = @(Convert-ToStringArray -Value $proMissing)
$btMissingItems = @(Convert-ToStringArray -Value $btMissing)

$proMsvc = Resolve-LatestMsvcRoot -InstallPath ([string]$proInstance.installationPath)
$btMsvc = Resolve-LatestMsvcRoot -InstallPath ([string]$btInstance.installationPath)

$sqlPackagePath = Join-Path ([string]$proInstance.installationPath) 'Common7\IDE\Extensions\Microsoft\SQLDB\DAC\SqlPackage.exe'
$binaryChecks = @(
    Test-Binary -Path (Join-Path $proMsvc 'bin\Hostx64\x64\cl.exe')
    Test-Binary -Path (Join-Path ([string]$proInstance.installationPath) 'VC\Tools\Llvm\x64\bin\clang-cl.exe')
    Test-Binary -Path (Join-Path ([string]$proInstance.installationPath) 'VC\Tools\Llvm\x64\bin\lld-link.exe')
    Test-Binary -Path (Join-Path ([string]$proInstance.installationPath) 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe')
    Test-Binary -Path (Join-Path ([string]$proInstance.installationPath) 'Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe')
    Test-Binary -Path 'C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\rc.exe'
    Test-Binary -Path $sqlPackagePath
    Test-Binary -Path (Join-Path $proMsvc 'lib\spectre\x64\libcmt.lib')
)

$missingBinaries = @($binaryChecks | Where-Object { -not $_.exists })
$missingBinaryCount = Get-SafeCount -Value $missingBinaries

$report = [pscustomobject]@{
    timestamp = (Get-Date).ToString('o')
    professional = [pscustomobject]@{
        instanceId = [string]$proInstance.instanceId
        installationPath = [string]$proInstance.installationPath
        installationVersion = [string]$proInstance.installationVersion
        missingRequiredComponents = @($proMissingItems)
    }
    buildTools = [pscustomobject]@{
        instanceId = [string]$btInstance.instanceId
        installationPath = [string]$btInstance.installationPath
        installationVersion = [string]$btInstance.installationVersion
        missingRequiredComponents = @($btMissingItems)
    }
    binaries = $binaryChecks
    summary = [pscustomobject]@{
        allRequiredComponentsPresent = (@($proMissingItems).Count -eq 0 -and @($btMissingItems).Count -eq 0)
        allCriticalBinariesPresent = ($missingBinaryCount -eq 0)
        missingComponentCount = (@($proMissingItems).Count + @($btMissingItems).Count)
        missingBinaryCount = $missingBinaryCount
    }
}

if ($Json) {
    $report | ConvertTo-Json -Depth 8
} else {
    Write-Host "VS 2026 audit @ $($report.timestamp)"
    Write-Host "Professional: $($report.professional.installationVersion) @ $($report.professional.installationPath)"
    Write-Host "BuildTools : $($report.buildTools.installationVersion) @ $($report.buildTools.installationPath)"
    Write-Host "Missing required components (Professional): $(@($proMissingItems).Count)"
    Write-Host "Missing required components (BuildTools): $(@($btMissingItems).Count)"
    Write-Host "Missing critical binaries: $($report.summary.missingBinaryCount)"
    if ($report.summary.missingBinaryCount -gt 0) {
        foreach ($row in $missingBinaries) {
            Write-Host " - $($row.path)"
        }
    }
}

if ($Strict -and -not ($report.summary.allRequiredComponentsPresent -and $report.summary.allCriticalBinariesPresent)) {
    exit 2
}
