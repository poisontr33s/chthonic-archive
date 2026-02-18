[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('version', 'drift', 'publish')]
    [string]$Mode
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-SqlPackagePath {
    $candidates = @()
    if ($env:SQL_DEV_KIT_PATH) {
        $candidates += (Join-Path $env:SQL_DEV_KIT_PATH 'SqlPackage.exe')
    }

    $candidates += @(
        'C:\Program Files\Microsoft Visual Studio\18\Insiders\Common7\IDE\Extensions\Microsoft\SQLDB\DAC\SqlPackage.exe',
        'C:\Program Files (x86)\Microsoft Visual Studio\18\Insiders\Common7\IDE\Extensions\Microsoft\SQLDB\DAC\SqlPackage.exe',
        'C:\Program Files\Microsoft SQL Server Management Studio 21\Common7\IDE\Extensions\Microsoft\SQLDB\DAC\SqlPackage.exe',
        'C:\Program Files (x86)\Microsoft SQL Server Management Studio 21\Common7\IDE\Extensions\Microsoft\SQLDB\DAC\SqlPackage.exe',
        'C:\Program Files\Microsoft SQL Server Management Studio 20\Common7\IDE\Extensions\Microsoft\SQLDB\DAC\SqlPackage.exe',
        'C:\Program Files (x86)\Microsoft SQL Server Management Studio 20\Common7\IDE\Extensions\Microsoft\SQLDB\DAC\SqlPackage.exe',
        'C:\Program Files\Microsoft SQL Server Management Studio 19\Common7\IDE\Extensions\Microsoft\SQLDB\DAC\SqlPackage.exe',
        'C:\Program Files (x86)\Microsoft SQL Server Management Studio 19\Common7\IDE\Extensions\Microsoft\SQLDB\DAC\SqlPackage.exe'
    )

    foreach ($candidate in $candidates | Select-Object -Unique) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw 'SqlPackage.exe not found. Ensure VS 2026 SQLDB DAC or SSMS DACFX tooling is installed.'
}

function Require-Env {
    param([Parameter(Mandatory = $true)][string]$Name)
    $value = [Environment]::GetEnvironmentVariable($Name)
    if ([string]::IsNullOrWhiteSpace($value)) {
        throw "Required environment variable '$Name' is not set."
    }
    return $value
}

$sqlPackage = Resolve-SqlPackagePath

switch ($Mode) {
    'version' {
        & $sqlPackage /Version
        break
    }
    'drift' {
        $dacpac = Require-Env -Name 'SQL_DACPAC_PATH'
        $target = Require-Env -Name 'SQL_TARGET_CONNECTION'
        $output = [Environment]::GetEnvironmentVariable('SQL_DRIFT_OUTPUT')
        if ([string]::IsNullOrWhiteSpace($output)) {
            $output = '.chthonic/sql/drift.xml'
        }
        $outputDir = Split-Path -Path $output -Parent
        if ($outputDir) {
            New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
        }
        & $sqlPackage /Action:DriftReport /SourceFile:$dacpac /TargetConnectionString:$target /OutputPath:$output
        break
    }
    'publish' {
        $dacpac = Require-Env -Name 'SQL_DACPAC_PATH'
        $target = Require-Env -Name 'SQL_TARGET_CONNECTION'
        & $sqlPackage /Action:Publish /SourceFile:$dacpac /TargetConnectionString:$target
        break
    }
}
