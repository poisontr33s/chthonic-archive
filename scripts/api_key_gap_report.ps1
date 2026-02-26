#!/usr/bin/env pwsh
#
# API key gap reporter (no secrets).
#
# @SID: TOOL_API_KEY_GAP_REPORT_V1
# @Type: Utility
# @Spectrum: WHITE
# @Zone: THE GARDEN

param(
    [string]$OutRoot = "codex/mailbox"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    $dir = (Get-Location).Path
    while ($true) {
        if ((Test-Path (Join-Path $dir "pyproject.toml")) -and (Test-Path (Join-Path $dir "AGENTS.md"))) {
            return $dir
        }
        $parent = Split-Path -Parent $dir
        if ($parent -eq $dir) {
            throw "Could not locate repo root from current directory."
        }
        $dir = $parent
    }
}

function Has-NonEmpty {
    param([AllowNull()][string]$Value)
    return -not [string]::IsNullOrWhiteSpace([string]$Value)
}

$repoRoot = Get-RepoRoot
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$outDir = Join-Path $repoRoot $OutRoot
New-Item -ItemType Directory -Path $outDir -Force | Out-Null

$poolPath = Join-Path $env:USERPROFILE ".chthonic\api_pool.json"
$poolEnv = @{}
if (Test-Path $poolPath) {
    try {
        $poolRaw = Get-Content -Path $poolPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($poolRaw.env) {
            foreach ($prop in $poolRaw.env.PSObject.Properties) {
                $poolEnv[$prop.Name] = [string]$prop.Value
            }
        }
    } catch {
        # Keep poolEnv empty when parse fails.
    }
}

$registry = @(
    [ordered]@{ key = "OPENAI_API_KEY"; provider = "OpenAI"; purpose = "Codex/OpenAI API"; acquire_url = "https://platform.openai.com/api-keys" },
    [ordered]@{ key = "GITHUB_TOKEN"; provider = "GitHub"; purpose = "GitHub API + gh workflows"; acquire_url = "https://github.com/settings/tokens" },
    [ordered]@{ key = "GEMINI_API_KEY"; provider = "Google AI Studio"; purpose = "Gemini API lanes"; acquire_url = "https://aistudio.google.com/apikey" },
    [ordered]@{ key = "POE_API_KEY"; provider = "Poe"; purpose = "Poe unified API lane"; acquire_url = "https://poe.com/api_key" },
    [ordered]@{ key = "POE_API_KEY_1"; provider = "Poe"; purpose = "Poe account 1 lane"; acquire_url = "https://poe.com/api_key" },
    [ordered]@{ key = "POE_API_KEY_2"; provider = "Poe"; purpose = "Poe account 2 lane"; acquire_url = "https://poe.com/api_key" },
    [ordered]@{ key = "HUGGINGFACE_HUB_TOKEN"; provider = "Hugging Face"; purpose = "HF model/API lanes"; acquire_url = "https://huggingface.co/settings/tokens" },
    [ordered]@{ key = "HF_TOKEN"; provider = "Hugging Face"; purpose = "Legacy HF env override"; acquire_url = "https://huggingface.co/settings/tokens" }
)

$rows = @()
foreach ($entry in $registry) {
    $k = $entry.key
    $poolValue = $null
    if ($poolEnv.ContainsKey($k)) {
        $poolValue = $poolEnv[$k]
    }
    $processValue = [Environment]::GetEnvironmentVariable($k, "Process")
    $userValue = [Environment]::GetEnvironmentVariable($k, "User")

    $inPool = Has-NonEmpty $poolValue
    $inProcess = Has-NonEmpty $processValue
    $inUser = Has-NonEmpty $userValue
    $available = ($inPool -or $inProcess -or $inUser)

    $rows += [ordered]@{
        key = $k
        provider = $entry.provider
        purpose = $entry.purpose
        available = $available
        in_pool = $inPool
        in_process_env = $inProcess
        in_user_env = $inUser
        acquire_url = $entry.acquire_url
    }
}

$missing = @($rows | Where-Object { -not $_.available })

$report = [ordered]@{
    schema_version = 1
    generated_on_utc = (Get-Date).ToUniversalTime().ToString("o")
    pool_path = $poolPath
    total_keys = $rows.Count
    available_keys = (@($rows | Where-Object { $_.available })).Count
    missing_keys = $missing.Count
    keys = $rows
}

$jsonPath = Join-Path $outDir ("API_KEY_GAP_REPORT_" + $timestamp + ".json")
$mdPath = Join-Path $outDir ("API_KEY_GAP_REPORT_" + $timestamp + ".md")

$report | ConvertTo-Json -Depth 8 | Set-Content -Path $jsonPath -Encoding UTF8

$md = @()
$md += "# API Key Gap Report"
$md += ""
$md += "- Generated (UTC): " + $report.generated_on_utc
$md += ('- Total keys checked: `{0}`' -f $report.total_keys)
$md += ('- Available: `{0}`' -f $report.available_keys)
$md += ('- Missing: `{0}`' -f $report.missing_keys)
$md += ""
$md += "## Key Matrix"
$md += ""
$md += "| Key | Provider | Available | In Pool | In Process | In User Env | Acquire URL |"
$md += "|---|---|---:|---:|---:|---:|---|"
foreach ($k in $rows) {
    $md += ("| {0} | {1} | {2} | {3} | {4} | {5} | {6} |" -f $k.key, $k.provider, $k.available, $k.in_pool, $k.in_process_env, $k.in_user_env, $k.acquire_url)
}
$md += ""
$md += "## Missing Keys (Priority Acquisition Queue)"
if ($missing.Count -eq 0) {
    $md += "- None."
} else {
    foreach ($m in $missing) {
        $md += "1. " + $m.key + " -> " + $m.acquire_url
    }
}

$md -join "`n" | Set-Content -Path $mdPath -Encoding UTF8

Write-Host "Wrote JSON report: $jsonPath"
Write-Host "Wrote Markdown report: $mdPath"
