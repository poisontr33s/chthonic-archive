#!/usr/bin/env pwsh
#
# API key gap reporter (no secrets).
#
# @SID: TOOL_API_KEY_GAP_REPORT_V1
# @Type: Utility
# @Spectrum: WHITE
# @Zone: THE GARDEN

param(
    [string]$OutRoot = "codex/mailbox",
    [string]$RegistryPath = "docs/standards/API_PROVIDER_REGISTRY.json",
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-RepoRoot {
    if ($PSScriptRoot) {
        return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
    }
    throw "Unable to resolve repo root: PSScriptRoot unavailable."
}

function Has-NonEmpty {
    param([AllowNull()][string]$Value)
    return -not [string]::IsNullOrWhiteSpace([string]$Value)
}

function To-Bool {
    param(
        [AllowNull()]$Value,
        [bool]$Default = $false
    )
    if ($null -eq $Value) {
        return $Default
    }
    if ($Value -is [bool]) {
        return [bool]$Value
    }
    $text = ([string]$Value).Trim().ToLowerInvariant()
    switch ($text) {
        "true" { return $true }
        "1" { return $true }
        "yes" { return $true }
        "y" { return $true }
        "false" { return $false }
        "0" { return $false }
        "no" { return $false }
        "n" { return $false }
        default { return $Default }
    }
}

function Get-IacRank {
    param([AllowNull()][string]$Level)
    $normalized = ([string]$Level).Trim().ToLowerInvariant()
    switch ($normalized) {
        "high" { return 3 }
        "medium" { return 2 }
        "low" { return 1 }
        default { return 0 }
    }
}

function Get-EffectiveSource {
    param(
        [bool]$InPool,
        [bool]$InProcess,
        [bool]$InUser
    )
    if ($InPool) { return "pool" }
    if ($InProcess) { return "process_env" }
    if ($InUser) { return "user_env" }
    return "none"
}

function Get-Recommendation {
    param(
        [bool]$Required,
        [bool]$OAuthAlternative,
        [AllowNull()][string]$IacViability
    )
    if ($Required) {
        return "Acquire now, store in secret manager, and automate runtime injection."
    }
    if ($OAuthAlternative) {
        return "OAuth-supported lane available; mint only if direct API lane is needed."
    }
    $normalized = ([string]$IacViability).Trim().ToLowerInvariant()
    if ($normalized -eq "high") {
        return "Acquire when needed; IaC automation is straightforward."
    }
    if ($normalized -eq "medium") {
        return "Acquire manually, then automate distribution and rotation."
    }
    if ($normalized -eq "low") {
        return "Manual acquisition and handling required; automate only downstream usage."
    }
    return "Optional lane. Acquire based on roadmap priority."
}

function Escape-MarkdownCell {
    param([AllowNull()][string]$Value)
    $text = [string]$Value
    return $text.Replace("|", "\|")
}

function Resolve-PathForRepo {
    param(
        [string]$RepoRoot,
        [string]$PathValue
    )
    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return $PathValue
    }
    return (Join-Path $RepoRoot $PathValue)
}

function Load-Registry {
    param([string]$AbsolutePath)
    if (-not (Test-Path -Path $AbsolutePath)) {
        throw "Registry file not found: $AbsolutePath"
    }

    $raw = Get-Content -Path $AbsolutePath -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $raw.keys) {
        throw "Registry schema invalid at $AbsolutePath (missing 'keys')."
    }

    $normalizedKeys = @()
    foreach ($entry in @($raw.keys)) {
        $keyName = [string]$entry.key
        if (-not (Has-NonEmpty $keyName)) {
            continue
        }

        $provider = [string]$entry.provider
        $purpose = [string]$entry.purpose
        $authMode = [string]$entry.auth_mode
        $acquireUrl = [string]$entry.acquire_url
        $iacViability = [string]$entry.iac_viability
        $iacNote = [string]$entry.iac_note

        if (-not (Has-NonEmpty $provider)) { $provider = "Unknown" }
        if (-not (Has-NonEmpty $purpose)) { $purpose = "Not specified" }
        if (-not (Has-NonEmpty $authMode)) { $authMode = "api_key" }
        if (-not (Has-NonEmpty $acquireUrl)) { $acquireUrl = "-" }
        if (-not (Has-NonEmpty $iacViability)) { $iacViability = "unknown" }
        if (-not (Has-NonEmpty $iacNote)) { $iacNote = "-" }

        $normalizedKeys += [pscustomobject][ordered]@{
            key = $keyName
            provider = $provider
            purpose = $purpose
            required = To-Bool -Value $entry.required -Default $false
            auth_mode = $authMode
            oauth_alternative = To-Bool -Value $entry.oauth_alternative -Default $false
            acquire_url = $acquireUrl
            iac_viability = $iacViability
            iac_note = $iacNote
        }
    }

    return [ordered]@{
        schema_version = $raw.schema_version
        generated_note = $raw.generated_note
        keys = $normalizedKeys
    }
}

$repoRoot = Get-RepoRoot
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$outDir = Join-Path $repoRoot $OutRoot
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$registryAbsolutePath = Resolve-PathForRepo -RepoRoot $repoRoot -PathValue $RegistryPath
$registryData = Load-Registry -AbsolutePath $registryAbsolutePath

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

$rows = @()
foreach ($entry in @($registryData.keys)) {
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
    $iacRank = Get-IacRank -Level $entry.iac_viability
    $recommendation = Get-Recommendation -Required ([bool]$entry.required) -OAuthAlternative ([bool]$entry.oauth_alternative) -IacViability $entry.iac_viability

    $rows += [pscustomobject][ordered]@{
        key = $k
        provider = $entry.provider
        purpose = $entry.purpose
        required = [bool]$entry.required
        auth_mode = $entry.auth_mode
        oauth_alternative = [bool]$entry.oauth_alternative
        iac_viability = $entry.iac_viability
        iac_note = $entry.iac_note
        iac_rank = $iacRank
        available = $available
        in_pool = $inPool
        in_process_env = $inProcess
        in_user_env = $inUser
        effective_source = (Get-EffectiveSource -InPool $inPool -InProcess $inProcess -InUser $inUser)
        acquire_url = $entry.acquire_url
        recommendation = $recommendation
    }
}

$missing = @($rows | Where-Object { -not $_.available })
$missingRequired = @($rows | Where-Object { -not $_.available -and $_.required })
$missingOptional = @($rows | Where-Object { -not $_.available -and -not $_.required })

$acquisitionQueue = @(
    $missing |
        Sort-Object `
            @{ Expression = { if ($_.required) { 0 } else { 1 } }; Ascending = $true }, `
            @{ Expression = { $_.iac_rank }; Descending = $true }, `
            @{ Expression = { $_.provider }; Ascending = $true }, `
            @{ Expression = { $_.key }; Ascending = $true }
)

$providerCoverage = @()
foreach ($group in ($rows | Group-Object -Property provider)) {
    $providerCoverage += [pscustomobject][ordered]@{
        provider = $group.Name
        total_keys = @($group.Group).Count
        available_keys = @($group.Group | Where-Object { $_.available }).Count
        missing_keys = @($group.Group | Where-Object { -not $_.available }).Count
        has_any_key = (@($group.Group | Where-Object { $_.available }).Count -gt 0)
    }
}

$report = [ordered]@{
    schema_version = 2
    generated_on_utc = (Get-Date).ToUniversalTime().ToString("o")
    registry_path = $registryAbsolutePath
    pool_path = $poolPath
    total_keys = $rows.Count
    available_keys = (@($rows | Where-Object { $_.available })).Count
    missing_keys = $missing.Count
    missing_required_keys = $missingRequired.Count
    missing_optional_keys = $missingOptional.Count
    providers_total = @($providerCoverage).Count
    providers_with_any_key = @($providerCoverage | Where-Object { $_.has_any_key }).Count
    providers_without_any_key = @($providerCoverage | Where-Object { -not $_.has_any_key }).Count
    keys = $rows
    provider_coverage = $providerCoverage
    acquisition_queue = @(
        $acquisitionQueue | ForEach-Object {
            [pscustomobject][ordered]@{
                key = $_.key
                provider = $_.provider
                required = $_.required
                auth_mode = $_.auth_mode
                oauth_alternative = $_.oauth_alternative
                iac_viability = $_.iac_viability
                acquire_url = $_.acquire_url
                recommendation = $_.recommendation
            }
        }
    )
}

$jsonPath = Join-Path $outDir ("API_KEY_GAP_REPORT_" + $timestamp + ".json")
$mdPath = Join-Path $outDir ("API_KEY_GAP_REPORT_" + $timestamp + ".md")
$envTemplatePath = Join-Path $outDir ("API_KEY_ENV_TEMPLATE_" + $timestamp + ".env")

$report | ConvertTo-Json -Depth 8 | Set-Content -Path $jsonPath -Encoding UTF8

$md = @()
$md += "# API Key Gap Report"
$md += ""
$md += "- Generated (UTC): " + $report.generated_on_utc
$md += ('- Total keys checked: `{0}`' -f $report.total_keys)
$md += ('- Available: `{0}`' -f $report.available_keys)
$md += ('- Missing: `{0}`' -f $report.missing_keys)
$md += ('- Missing required: `{0}`' -f $report.missing_required_keys)
$md += ('- Missing optional: `{0}`' -f $report.missing_optional_keys)
$md += ('- Providers with any key: `{0}/{1}`' -f $report.providers_with_any_key, $report.providers_total)
$md += ('- Registry path: `{0}`' -f $report.registry_path)
$md += ('- Env template: `{0}`' -f $envTemplatePath)
$md += ""
$md += "## Key Matrix"
$md += ""
$md += "| Key | Provider | Required | Available | Auth Mode | OAuth Alt | IaC | Source | In Pool | In Process | In User Env | Acquire URL |"
$md += "|---|---|---:|---:|---|---:|---|---|---:|---:|---:|---|"
foreach ($k in $rows) {
    $md += ("| {0} | {1} | {2} | {3} | {4} | {5} | {6} | {7} | {8} | {9} | {10} | {11} |" -f `
        (Escape-MarkdownCell -Value $k.key), `
        (Escape-MarkdownCell -Value $k.provider), `
        $k.required, `
        $k.available, `
        (Escape-MarkdownCell -Value $k.auth_mode), `
        $k.oauth_alternative, `
        (Escape-MarkdownCell -Value $k.iac_viability), `
        (Escape-MarkdownCell -Value $k.effective_source), `
        $k.in_pool, `
        $k.in_process_env, `
        $k.in_user_env, `
        (Escape-MarkdownCell -Value $k.acquire_url))
}
$md += ""
$md += "## Missing Required Keys"
if ($missingRequired.Count -eq 0) {
    $md += "- None."
} else {
    foreach ($m in $missingRequired) {
        $md += "1. " + $m.key + " (" + $m.provider + ", IaC=" + $m.iac_viability + ") -> " + $m.acquire_url
    }
}
$md += ""
$md += "## IaC-Weighted Acquisition Queue (Required First)"
if ($acquisitionQueue.Count -eq 0) {
    $md += "- None."
} else {
    foreach ($q in $acquisitionQueue) {
        $md += "1. " + $q.key + " (" + $q.provider + ", required=" + $q.required + ", IaC=" + $q.iac_viability + ") -> " + $q.acquire_url
        $md += "   - " + $q.recommendation
    }
}
$md += ""
$md += "## Provider Coverage"
$md += ""
$md += "| Provider | Total Keys | Available | Missing | Has Any Key |"
$md += "|---|---:|---:|---:|---:|"
foreach ($p in $providerCoverage | Sort-Object -Property provider) {
    $md += ("| {0} | {1} | {2} | {3} | {4} |" -f (Escape-MarkdownCell -Value $p.provider), $p.total_keys, $p.available_keys, $p.missing_keys, $p.has_any_key)
}

$md -join "`n" | Set-Content -Path $mdPath -Encoding UTF8

$envTemplate = @()
$envTemplate += "# API key template (no secrets)."
$envTemplate += "# Generated (UTC): $($report.generated_on_utc)"
$envTemplate += "# Fill and load via your preferred secret manager or local secure pool."
$envTemplate += ""
$envTemplate += "# Missing keys first (priority order)."
if ($acquisitionQueue.Count -eq 0) {
    $envTemplate += "# None."
} else {
    foreach ($item in $acquisitionQueue) {
        $envTemplate += ("# {0} | provider={1} | required={2} | auth={3} | iac={4}" -f $item.key, $item.provider, $item.required, $item.auth_mode, $item.iac_viability)
        $envTemplate += ("# acquire: {0}" -f $item.acquire_url)
        $envTemplate += ("{0}=" -f $item.key)
        $envTemplate += ""
    }
}
$envTemplate += "# Existing keys already available in current machine context."
foreach ($existing in ($rows | Where-Object { $_.available } | Sort-Object -Property key)) {
    $envTemplate += ("# {0} already available ({1})" -f $existing.key, $existing.effective_source)
}
$envTemplate -join "`n" | Set-Content -Path $envTemplatePath -Encoding UTF8

Write-Host "Wrote JSON report: $jsonPath"
Write-Host "Wrote Markdown report: $mdPath"
Write-Host "Wrote env template: $envTemplatePath"

if ($Json) {
    $report | ConvertTo-Json -Depth 8
}
