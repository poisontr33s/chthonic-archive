#!/usr/bin/env pwsh

param(
    [switch]$SkipModify
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path $script:LogPath -Value $line
    Write-Host $line
}

function Get-VSWhereExe {
    $candidates = @(
        "C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe",
        "C:\Program Files\Microsoft Visual Studio\Installer\vswhere.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

function Get-InstanceStatePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ProductId,
        [switch]$Prerelease
    )

    $vswhere = Get-VSWhereExe
    if (-not $vswhere) {
        throw "vswhere.exe not found."
    }

    $args = @("-latest", "-products", $ProductId, "-format", "json")
    if ($Prerelease) { $args += "-prerelease" }

    $raw = & $vswhere @args 2>$null
    if (-not $raw) {
        return $null
    }

    $instances = $raw | ConvertFrom-Json
    if (-not $instances) {
        return $null
    }

    $instance = @($instances)[0]
    if (-not $instance.instanceId) {
        return $null
    }

    $statePath = Join-Path "C:\ProgramData\Microsoft\VisualStudio\Packages\_Instances" $instance.instanceId
    $statePath = Join-Path $statePath "state.json"
    if (Test-Path $statePath) {
        return $statePath
    }
    return $null
}

function Get-InstanceInstallPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ProductId,
        [switch]$Prerelease
    )

    $vswhere = Get-VSWhereExe
    if (-not $vswhere) {
        throw "vswhere.exe not found."
    }

    $args = @("-latest", "-products", $ProductId, "-property", "installationPath")
    if ($Prerelease) { $args += "-prerelease" }

    $path = & $vswhere @args 2>$null
    $value = ($path | Select-Object -First 1)
    if ($value -and (Test-Path $value)) {
        return $value.Trim()
    }
    return $null
}

function Get-PreferredIdeProductId {
    foreach ($product in @(
        "Microsoft.VisualStudio.Product.Professional",
        "Microsoft.VisualStudio.Product.Community",
        "Microsoft.VisualStudio.Product.Enterprise"
    )) {
        $state = Get-InstanceStatePath -ProductId $product -Prerelease
        if ($state) { return $product }
    }
    return $null
}

function Get-MissingComponents {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ConfigPath,
        [Parameter(Mandatory = $true)]
        [string]$StatePath
    )

    $config = Get-Content -Path $ConfigPath -Raw | ConvertFrom-Json
    $state = Get-Content -Path $StatePath -Raw | ConvertFrom-Json
    $selected = @($state.selectedPackages.id)
    $missing = @($config.components | Where-Object { $_ -notin $selected })
    return $missing
}

function Invoke-SetupModify {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SetupExe,
        [Parameter(Mandatory = $true)]
        [string]$InstallPath,
        [Parameter(Mandatory = $true)]
        [string]$ConfigPath
    )

    $args = @(
        "modify",
        "--installPath", $InstallPath,
        "--config", $ConfigPath,
        "--installWhileDownloading",
        "--passive",
        "--norestart"
    )

    Write-Log ("Running setup.exe {0}" -f ($args -join " "))
    & $SetupExe @args
    return $LASTEXITCODE
}

function Invoke-SetupInstall {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SetupExe,
        [Parameter(Mandatory = $true)]
        [string]$InstallPath,
        [Parameter(Mandatory = $true)]
        [string]$ConfigPath,
        [Parameter(Mandatory = $true)]
        [string]$ProductId,
        [Parameter(Mandatory = $true)]
        [string]$ChannelId
    )

    $args = @(
        "install",
        "--installPath", $InstallPath,
        "--channelId", $ChannelId,
        "--productId", $ProductId,
        "--config", $ConfigPath,
        "--installWhileDownloading",
        "--passive",
        "--norestart"
    )

    Write-Log ("Running setup.exe {0}" -f ($args -join " "))
    & $SetupExe @args
    return $LASTEXITCODE
}

function Wait-InstallerIdle {
    $deadline = (Get-Date).AddMinutes(30)
    do {
        $procs = Get-Process -Name "setup" -ErrorAction SilentlyContinue
        if (-not $procs) { return }
        Start-Sleep -Seconds 3
    } while ((Get-Date) -lt $deadline)

    Write-Log "Timeout waiting for setup.exe processes to exit."
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$setupExe = "C:\Program Files (x86)\Microsoft Visual Studio\Installer\setup.exe"
$configRoot = Join-Path $repoRoot ".codex\visualStudioInstaller2006"
$mailboxDir = Join-Path $repoRoot "codex\mailbox"

if (-not (Test-Path $setupExe)) {
    throw "setup.exe not found: $setupExe"
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$script:LogPath = Join-Path $mailboxDir "VS2026_ELEVATED_VALIDATE_${timestamp}.log"
New-Item -Path $script:LogPath -ItemType File -Force | Out-Null

Write-Log "Starting elevated VS/SSMS validation."
Write-Log ("SkipModify={0}" -f $SkipModify)

$ideProductId = Get-PreferredIdeProductId
if (-not $ideProductId) {
    # Default target if no IDE instance is present yet.
    $ideProductId = "Microsoft.VisualStudio.Product.Professional"
}
$ideInstallPath = Get-InstanceInstallPath -ProductId $ideProductId -Prerelease
if (-not $ideInstallPath) {
    $ideInstallPath = "C:\Program Files\Microsoft Visual Studio\18\Insiders"
}
$legacyIdeConfigPath = Join-Path $configRoot "visualStudio2026Insiders_11506.43\.vsconfig"
$professionalIdeConfigPath = Join-Path $configRoot "visualStudio2026InsidersProfessional_11506.43\.vsconfig"
$ideConfigPath = $legacyIdeConfigPath
if (
    $ideProductId -eq "Microsoft.VisualStudio.Product.Professional" -and
    (Test-Path $professionalIdeConfigPath)
) {
    $ideConfigPath = $professionalIdeConfigPath
}
$ideLaneName = switch ($ideProductId) {
    "Microsoft.VisualStudio.Product.Professional" { "professional" }
    "Microsoft.VisualStudio.Product.Community"   { "community" }
    "Microsoft.VisualStudio.Product.Enterprise"  { "enterprise" }
    default { "ide" }
}

$lanes = @(
    @{
        Name = "${ideLaneName}_insiders"
        ProductId = $ideProductId
        Prerelease = $true
        InstallPath = $ideInstallPath
        ConfigPath = $ideConfigPath
    },
    @{
        Name = "buildtools_insiders"
        ProductId = "Microsoft.VisualStudio.Product.BuildTools"
        Prerelease = $true
        InstallPath = "C:\Program Files (x86)\Microsoft Visual Studio\18\Insiders"
        ConfigPath = Join-Path $configRoot "visualStudio2026InsidersBuildtools_11506.43\.vsconfig"
        InstallIfMissing = $true
        ChannelId = "VisualStudio.18.Preview"
    },
    @{
        Name = "ssms22"
        ProductId = "Microsoft.VisualStudio.Product.Ssms"
        Prerelease = $false
        InstallPath = "C:\Program Files\Microsoft SQL Server Management Studio 22\Release"
        ConfigPath = Join-Path $configRoot "SQLServerManagementStudio22_23.3.0\.vsconfig"
        Optional = $true
        AllowComponentDrift = $true
    }
)

$results = @()
$hasFailures = $false

foreach ($lane in $lanes) {
    Write-Log ("Lane start: {0}" -f $lane.Name)

    if (-not (Test-Path $lane.ConfigPath)) {
        Write-Log ("Config missing: {0}" -f $lane.ConfigPath)
        $results += [pscustomobject]@{
            lane = $lane.Name
            status = "config_missing"
            pre_missing_count = $null
            post_missing_count = $null
            exit_code = $null
        }
        $hasFailures = $true
        continue
    }

    $exitCode = $null
    $statePath = Get-InstanceStatePath -ProductId $lane.ProductId -Prerelease:$lane.Prerelease

    if (
        -not $statePath -and
        -not $SkipModify -and
        $lane.ContainsKey("InstallIfMissing") -and
        $lane.InstallIfMissing
    ) {
        Write-Log ("Instance missing for {0}; installing lane first." -f $lane.ProductId)
        $installExit = Invoke-SetupInstall `
            -SetupExe $setupExe `
            -InstallPath $lane.InstallPath `
            -ConfigPath $lane.ConfigPath `
            -ProductId $lane.ProductId `
            -ChannelId $lane.ChannelId
        Write-Log ("setup.exe install exit code: {0}" -f $installExit)
        if ($installExit -ne 0) {
            $results += [pscustomobject]@{
                lane = $lane.Name
                status = "install_failed"
                pre_missing_count = $null
                post_missing_count = $null
                exit_code = $installExit
            }
            $hasFailures = $true
            continue
        }
        Wait-InstallerIdle
        $statePath = Get-InstanceStatePath -ProductId $lane.ProductId -Prerelease:$lane.Prerelease
    }

    if (-not $statePath) {
        Write-Log ("State missing for product: {0}" -f $lane.ProductId)
        $status = "instance_missing"
        if ($lane.ContainsKey("Optional") -and $lane.Optional) {
            $status = "skipped_missing_optional"
        }
        $results += [pscustomobject]@{
            lane = $lane.Name
            status = $status
            pre_missing_count = $null
            post_missing_count = $null
            exit_code = $null
        }
        if ($status -ne "skipped_missing_optional") {
            $hasFailures = $true
        }
        continue
    }

    $preMissing = Get-MissingComponents -ConfigPath $lane.ConfigPath -StatePath $statePath
    Write-Log ("Pre-check missing count: {0}" -f $preMissing.Count)

    if (-not $SkipModify) {
        $exitCode = Invoke-SetupModify -SetupExe $setupExe -InstallPath $lane.InstallPath -ConfigPath $lane.ConfigPath
        Write-Log ("setup.exe exit code: {0}" -f $exitCode)
        Wait-InstallerIdle
    }

    $postMissing = Get-MissingComponents -ConfigPath $lane.ConfigPath -StatePath $statePath
    Write-Log ("Post-check missing count: {0}" -f $postMissing.Count)

    $status = "ok"
    $laneAllowsDrift = $lane.ContainsKey("AllowComponentDrift") -and $lane.AllowComponentDrift
    $hasPostMissing = $postMissing.Count -gt 0
    if (($exitCode -ne $null -and $exitCode -ne 0) -or ($hasPostMissing -and -not $laneAllowsDrift)) {
        $status = "failed"
        $hasFailures = $true
    } elseif ($hasPostMissing -and $laneAllowsDrift) {
        $status = "drift_optional"
    }

    $results += [pscustomobject]@{
        lane = $lane.Name
        status = $status
        pre_missing_count = $preMissing.Count
        post_missing_count = $postMissing.Count
        exit_code = $exitCode
    }

    Write-Log ("Lane done: {0}" -f $lane.Name)
}

$statusJson = & pwsh -NoProfile -File (Join-Path $repoRoot "scripts\chthonic.ps1") status --json
$originsText = & pwsh -NoProfile -File (Join-Path $repoRoot "scripts\chthonic.ps1") doctor --origins

$summary = [pscustomobject]@{
    timestamp = (Get-Date).ToString("s")
    elevated_user = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    skip_modify = [bool]$SkipModify
    lanes = $results
    chthonic_status = ($statusJson | ConvertFrom-Json)
    log_path = $script:LogPath
}

$jsonOut = Join-Path $mailboxDir "VS2026_ELEVATED_VALIDATION_LATEST.json"
$mdOut = Join-Path $mailboxDir "VS2026_ELEVATED_VALIDATION_LATEST.md"

$summary | ConvertTo-Json -Depth 8 | Set-Content -Path $jsonOut -Encoding UTF8

$md = @()
$md += "# VS2026 Elevated Validation (Latest)"
$md += ""
$md += "- Timestamp: $($summary.timestamp)"
$md += "- Elevated User: $($summary.elevated_user)"
$md += "- Skip Modify: $($summary.skip_modify)"
$md += ('- Log: "{0}"' -f $summary.log_path)
$md += ""
$md += "## Lane Results"
$md += ""
foreach ($r in $results) {
    $md += "- [$($r.status)] $($r.lane): pre_missing=$($r.pre_missing_count), post_missing=$($r.post_missing_count), exit_code=$($r.exit_code)"
}
$md += ""
$md += "## chthonic status --json"
$md += ""
$md += '```json'
$md += ($statusJson | Out-String).TrimEnd()
$md += '```'
$md += ""
$md += "## chthonic doctor --origins"
$md += ""
$md += '```text'
$md += ($originsText | Out-String).TrimEnd()
$md += '```'

$md -join "`r`n" | Set-Content -Path $mdOut -Encoding UTF8

Write-Log ("Wrote JSON: {0}" -f $jsonOut)
Write-Log ("Wrote MD: {0}" -f $mdOut)
Write-Log "Validation complete."

if ($hasFailures) { exit 1 }
exit 0
