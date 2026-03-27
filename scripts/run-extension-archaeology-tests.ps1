#!/usr/bin/env pwsh
#
# @SID: SCRIPT_RUN_EXTENSION_ARCHAEOLOGY_TESTS_V1
# @Type: VALIDATION
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Set-StrictMode -Version Latest
#

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$testFiles = Get-ChildItem "dumpster-dive/forge/extension-archaeology/diagnostics-tests" -Filter "*.test.ts" |
    Sort-Object Name |
    ForEach-Object { $_.FullName }

if (-not $testFiles) {
    Write-Error "No extension archaeology test files found."
    exit 1
}

& bun test @testFiles
exit $LASTEXITCODE
