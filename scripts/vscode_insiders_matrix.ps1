#!/usr/bin/env pwsh
#
# VS Code Insiders stability matrix runner.
#
# @SID: TOOL_VSCODE_INSIDERS_MATRIX_V1
# @Type: Utility
# @Spectrum: WHITE
# @Zone: THE GARDEN

param(
    [string]$OutRoot = "codex/mailbox",
    [string[]]$Skip = @(),
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    $dir = $PSScriptRoot
    while ($true) {
        if ((Test-Path (Join-Path $dir "pyproject.toml")) -and (Test-Path (Join-Path $dir "AGENTS.md"))) {
            return $dir
        }
        $parent = Split-Path -Parent $dir
        if ($parent -eq $dir) {
            throw "Could not locate repo root from $PSScriptRoot."
        }
        $dir = $parent
    }
}

function Invoke-StatusCase {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$CodeCmd,
        [Parameter(Mandatory = $true)][string[]]$Args,
        [Parameter(Mandatory = $true)][string]$BundleDir
    )

    $safeName = ($Name -replace "[^a-zA-Z0-9_-]", "_")
    $stdout = Join-Path $BundleDir ("matrix_" + $safeName + "_status.log")
    $stderr = Join-Path $BundleDir ("matrix_" + $safeName + "_status.err.log")
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $exitCode = 0

    try {
        $proc = Start-Process `
            -FilePath $CodeCmd `
            -ArgumentList $Args `
            -Wait `
            -PassThru `
            -NoNewWindow `
            -RedirectStandardOutput $stdout `
            -RedirectStandardError $stderr
        $exitCode = $proc.ExitCode
    } catch {
        $exitCode = -1
        $_ | Out-String | Set-Content -Path $stderr -Encoding UTF8
    } finally {
        $sw.Stop()
    }

    $text = ""
    if (Test-Path $stdout) {
        $text = Get-Content -Path $stdout -Raw -Encoding UTF8
    }

    $rendererCrashCount = @($text -split "`r?`n" | Where-Object { $_ -match "renderer process gone|reason: crashed" }).Count
    $gpuErrorCount = @($text -split "`r?`n" | Where-Object { $_ -match "SharedImageManager|GPU Log Messages|unavailable_software|gpu-process" }).Count
    $ptyHostCount = @($text -split "`r?`n" | Where-Object { $_ -match "pty-host|conpty-agent" }).Count

    $stabilityScore = 100 - ($rendererCrashCount * 25) - ($gpuErrorCount * 2)
    if ($stabilityScore -lt 0) { $stabilityScore = 0 }

    return [pscustomobject]@{
        case = $Name
        args = ($Args -join " ")
        exit_code = $exitCode
        elapsed_ms = [int]$sw.ElapsedMilliseconds
        renderer_crash_count = $rendererCrashCount
        gpu_error_count = $gpuErrorCount
        ptyhost_line_count = $ptyHostCount
        stability_score_100 = $stabilityScore
        stdout_path = $stdout
        stderr_path = $stderr
    }
}

$repoRoot = Get-RepoRoot
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$outDir = Join-Path $repoRoot (Join-Path $OutRoot ("VSCODE_INSIDERS_MATRIX_" + $timestamp))
New-Item -ItemType Directory -Path $outDir -Force | Out-Null

$code = Get-Command code-insiders -ErrorAction SilentlyContinue
if (-not $code) {
    throw "code-insiders command not found."
}

$tempUserData = Join-Path $env:TEMP ("vscode-insiders-clean-" + $timestamp)
New-Item -ItemType Directory -Path $tempUserData -Force | Out-Null

$cases = @(
    [ordered]@{ name = "baseline"; args = @("--status") },
    [ordered]@{ name = "disable_gpu"; args = @("--disable-gpu", "--status") },
    [ordered]@{ name = "disable_extensions"; args = @("--disable-extensions", "--status") },
    [ordered]@{ name = "clean_safe_mode"; args = @("--user-data-dir", $tempUserData, "--disable-extensions", "--disable-gpu", "--status") }
)
if ($Skip.Count -gt 0) {
    $cases = @($cases | Where-Object { $Skip -notcontains $_.name })
}

$results = @()
foreach ($c in $cases) {
    $results += (Invoke-StatusCase -Name $c.name -CodeCmd $code.Source -Args $c.args -BundleDir $outDir)
}

$winner = $results | Sort-Object `
    @{ Expression = "stability_score_100"; Descending = $true }, `
    @{ Expression = "renderer_crash_count"; Descending = $false }, `
    @{ Expression = "gpu_error_count"; Descending = $false } |
    Select-Object -First 1

$report = [ordered]@{
    schema_version = 1
    generated_on_utc = (Get-Date).ToUniversalTime().ToString("o")
    code_insiders_path = $code.Source
    temp_user_data_dir = $tempUserData
    results = $results
    recommended_mode = $winner
}

$jsonPath = Join-Path $outDir "matrix_report.json"
$mdPath = Join-Path $outDir "matrix_report.md"

$report | ConvertTo-Json -Depth 8 | Set-Content -Path $jsonPath -Encoding UTF8

if ($Json) {
    $report | ConvertTo-Json -Depth 8 | Write-Output
}

$md = @()
$md += "# VS Code Insiders Stability Matrix"
$md += ""
$md += "- Generated (UTC): " + $report.generated_on_utc
$md += ('- Code path: `{0}`' -f $report.code_insiders_path)
$md += ('- Temp user-data dir: `{0}`' -f $report.temp_user_data_dir)
$md += ""
$md += "## Results"
$md += ""
$md += "| Case | Exit | Renderer Crashes | GPU Errors | PTY Lines | Score/100 |"
$md += "|---|---:|---:|---:|---:|---:|"
foreach ($r in $results) {
    $md += ("| {0} | {1} | {2} | {3} | {4} | {5} |" -f $r.case, $r.exit_code, $r.renderer_crash_count, $r.gpu_error_count, $r.ptyhost_line_count, $r.stability_score_100)
}
$md += ""
$md += "## Recommended Mode"
$md += ""
$md += ('- Case: `{0}`' -f $winner.case)
$md += ('- Args: `{0}`' -f $winner.args)
$md += ('- Stability score: `{0}`' -f $winner.stability_score_100)
$md += ""
$md += "## Artifacts"
$md += ('- JSON: `{0}`' -f $jsonPath)
$md += ('- Bundle dir: `{0}`' -f $outDir)

$md -join "`n" | Set-Content -Path $mdPath -Encoding UTF8

Write-Host "Wrote matrix JSON: $jsonPath"
Write-Host "Wrote matrix Markdown: $mdPath"
