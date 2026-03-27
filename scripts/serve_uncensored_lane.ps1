#!/usr/bin/env pwsh
#
# @SID: SCRIPT_SERVE_UNCENSORED_LANE_V1
# @Type: RUNNER
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Launch llama_cpp.server from the latest uncensored lane runtime manifest.
#

# Launch llama_cpp.server from the latest uncensored lane runtime manifest.
param(
    [ValidateSet("strict_json", "code", "unrestricted")]
    [string]$Lane = "strict_json",

    [string]$RuntimeFile = "claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_LATEST.json",

    [string]$ServerHost = "127.0.0.1",
    [int]$Port = 8000,
    [int]$NCtx = 8192,
    [int]$NGpuLayers = -1,
    [switch]$DryRun,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ExtraArgs
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimePath = if ([System.IO.Path]::IsPathRooted($RuntimeFile)) {
    $RuntimeFile
} else {
    Join-Path $repoRoot $RuntimeFile
}

if (-not (Test-Path $runtimePath)) {
    Write-Error "Runtime manifest missing: $runtimePath. Run: uv run scripts/uncensored_lane_steward.py"
    exit 1
}

try {
    $manifest = Get-Content -Raw $runtimePath | ConvertFrom-Json -Depth 10
} catch {
    Write-Error "Failed to parse runtime manifest: $runtimePath"
    exit 1
}

$laneNode = $manifest.lanes.$Lane
if (-not $laneNode) {
    Write-Error "Lane '$Lane' not found in runtime manifest: $runtimePath"
    exit 1
}

$modelPath = [string]$laneNode.model_file
if (-not $modelPath) {
    Write-Error "Lane '$Lane' has no model_file in runtime manifest: $runtimePath"
    exit 1
}
if (-not (Test-Path $modelPath)) {
    Write-Error "Lane '$Lane' model file missing: $modelPath"
    exit 1
}

$uvArgs = @(
    "run",
    "python",
    "-m",
    "llama_cpp.server",
    "--model",
    $modelPath,
    "--host",
    $ServerHost,
    "--port",
    $Port.ToString(),
    "--n_ctx",
    $NCtx.ToString(),
    "--n_gpu_layers",
    $NGpuLayers.ToString(),
    "--chat_format",
    "chatml"
)

if ($ExtraArgs) {
    $uvArgs += $ExtraArgs
}

Write-Host "[Chthonic LLM] lane=$Lane" -ForegroundColor Cyan
Write-Host "  model=$modelPath" -ForegroundColor Gray
Write-Host "  endpoint=http://$ServerHost`:$Port/v1" -ForegroundColor Gray
Write-Host "  quant=$($laneNode.quant_tag)" -ForegroundColor Gray

if ($DryRun) {
    $joined = $uvArgs | ForEach-Object {
        if ($_ -match "\s") { '"' + $_ + '"' } else { $_ }
    }
    Write-Host "Dry run command:" -ForegroundColor Yellow
    Write-Host ("uv " + ($joined -join " ")) -ForegroundColor Yellow
    exit 0
}

& uv @uvArgs
exit $LASTEXITCODE
