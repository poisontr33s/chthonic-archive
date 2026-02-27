#!/usr/bin/env pwsh
#
# VS Code Insiders terminal crash doctor.
#
# @SID: TOOL_VSCODE_TERMINAL_CRASH_DOCTOR_V1
# @Type: Utility
# @Spectrum: WHITE
# @Zone: THE GARDEN

param(
    [string]$OutRoot = "codex/mailbox",
    [switch]$SkipSmokeTests,
    [switch]$SkipLogCollection,
    [switch]$SkipApiDoctor,
    [switch]$SkipCodeStatus
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

function To-HexCode {
    param([int]$Code)
    return ("0x{0:X8}" -f ($Code -band 0xffffffff))
}

function Get-CrashMeaning {
    param([int]$Code)
    switch ($Code) {
        -1073741819 { return "Access violation (STATUS_ACCESS_VIOLATION)" } # 0xC0000005
        -2147483645 { return "Breakpoint trap / abort (STATUS_BREAKPOINT)" } # 0x80000003
        default { return "Unknown / needs symbolized dump analysis" }
    }
}

function Parse-CrashCodesFromLines {
    param([string[]]$Lines)
    $codes = @()
    $pattern = [regex]'(?:exit code|code:\s*)(-?\d+)'
    foreach ($line in @($Lines)) {
        foreach ($m in $pattern.Matches([string]$line)) {
            $raw = $m.Groups[1].Value
            $parsed = 0
            if ([int]::TryParse($raw, [ref]$parsed)) {
                $codes += $parsed
            }
        }
    }
    return @($codes)
}

function Build-CrashCodeDescriptors {
    param([int[]]$Codes)
    $descriptors = @()
    foreach ($code in @($Codes | Sort-Object -Unique)) {
        $descriptors += [ordered]@{
            decimal = $code
            hex = (To-HexCode -Code $code)
            meaning = (Get-CrashMeaning -Code $code)
        }
    }
    return $descriptors
}

function Invoke-PwshProbe {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$PwshPath,
        [Parameter(Mandatory = $true)][string[]]$ArgumentList,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string]$BundleDir
    )

    $stdoutPath = Join-Path $BundleDir ("probe_" + $Name + "_stdout.log")
    $stderrPath = Join-Path $BundleDir ("probe_" + $Name + "_stderr.log")
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $exitCode = 0

    try {
        $proc = Start-Process `
            -FilePath $PwshPath `
            -ArgumentList $ArgumentList `
            -WorkingDirectory $WorkingDirectory `
            -Wait `
            -PassThru `
            -NoNewWindow `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath
        $exitCode = $proc.ExitCode
    } catch {
        $exitCode = -1
        $_ | Out-String | Set-Content -Path $stderrPath -Encoding UTF8
    } finally {
        $sw.Stop()
    }

    return [ordered]@{
        name = $Name
        args = ($ArgumentList -join " ")
        cwd = $WorkingDirectory
        exit_code = $exitCode
        exit_hex = (To-HexCode -Code $exitCode)
        elapsed_ms = [int]$sw.ElapsedMilliseconds
        stdout_path = $stdoutPath
        stderr_path = $stderrPath
    }
}

function Get-LatestInsidersLogDir {
    $logsRoot = Join-Path $env:APPDATA "Code - Insiders\logs"
    if (-not (Test-Path $logsRoot)) {
        return $null
    }
    $dirs = Get-ChildItem -Path $logsRoot -Directory |
        Sort-Object LastWriteTime -Descending
    foreach ($d in $dirs) {
        $hasAnyFile = Get-ChildItem -Path $d.FullName -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($hasAnyFile) {
            return $d
        }
    }
    return ($dirs | Select-Object -First 1)
}

function Collect-InsidersLogs {
    param(
        [Parameter(Mandatory = $true)][string]$BundleDir
    )

    $latest = Get-LatestInsidersLogDir
    if (-not $latest) {
        return [ordered]@{
            found = $false
            reason = "No Code - Insiders logs directory found."
            source_dir = $null
            copied_files = @()
            crash_hits = @()
        }
    }

    $dest = Join-Path $BundleDir "insiders_logs"
    New-Item -ItemType Directory -Path $dest -Force | Out-Null

    $patterns = @(
        "*terminal*.log",
        "*ptyhost*.log",
        "*window*.log",
        "*renderer*.log",
        "*main*.log",
        "*sharedprocess*.log",
        "*exthost*.log"
    )

    $files = @()
    foreach ($pattern in $patterns) {
        $files += Get-ChildItem -Path $latest.FullName -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue
    }
    $files = @($files | Sort-Object FullName -Unique)
    if ($files.Count -eq 0) {
        $files = @(Get-ChildItem -Path $latest.FullName -Recurse -File -Filter "*.log" -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 200)
    }

    $copied = @()
    foreach ($f in $files) {
        $relative = $f.FullName.Substring($latest.FullName.Length).TrimStart('\', '/')
        $target = Join-Path $dest $relative
        $targetDir = Split-Path -Parent $target
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        Copy-Item -Path $f.FullName -Destination $target -Force
        $copied += $target
    }

    $patternsHit = @(
        "terminated with exit code",
        "0xC0000005",
        "STATUS_ACCESS_VIOLATION",
        "access violation",
        "renderer process gone",
        "reason: crashed",
        "pty host exited",
        "pty host terminated"
    )

    $hits = @()
    if ($copied.Count -gt 0) {
        $select = Select-String -Path $copied -Pattern $patternsHit -SimpleMatch -ErrorAction SilentlyContinue
        foreach ($h in $select | Select-Object -First 250) {
            $hits += [ordered]@{
                path = $h.Path
                line = $h.LineNumber
                text = $h.Line.Trim()
            }
        }
    }

    return [ordered]@{
        found = $true
        source_dir = $latest.FullName
        copied_files = $copied
        crash_hits = $hits
    }
}

function Get-SettingStatus {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path $Path)) {
        return [ordered]@{ path = $Path; exists = $false; terminal_log_level = $null }
    }
    $raw = Get-Content -Path $Path -Raw -Encoding UTF8
    $match = [regex]::Match($raw, '"terminal\.integrated\.logLevel"\s*:\s*"([^"]+)"')
    $level = $null
    if ($match.Success) {
        $level = $match.Groups[1].Value
    }
    return [ordered]@{
        path = $Path
        exists = $true
        terminal_log_level = $level
    }
}

function Invoke-CodeStatus {
    param(
        [Parameter(Mandatory = $true)][string]$BundleDir
    )

    $codeCmd = Get-Command code-insiders -ErrorAction SilentlyContinue
    if (-not $codeCmd) {
        return [ordered]@{
            available = $false
            reason = "code-insiders command not found."
        }
    }

    $outPath = Join-Path $BundleDir "code_insiders_status.log"
    $errPath = Join-Path $BundleDir "code_insiders_status.err.log"
    $exitCode = 0

    try {
        $proc = Start-Process `
            -FilePath $codeCmd.Source `
            -ArgumentList @("--status") `
            -Wait `
            -PassThru `
            -NoNewWindow `
            -RedirectStandardOutput $outPath `
            -RedirectStandardError $errPath
        $exitCode = $proc.ExitCode
    } catch {
        $exitCode = -1
        $_ | Out-String | Set-Content -Path $errPath -Encoding UTF8
    }

    $summary = [ordered]@{
        available = $true
        cmd = $codeCmd.Source
        exit_code = $exitCode
        stdout_path = $outPath
        stderr_path = $errPath
        renderer_crash_lines = @()
        gpu_error_lines = @()
    }

    if (Test-Path $outPath) {
        $text = Get-Content -Path $outPath -Raw -Encoding UTF8
        $summary.renderer_crash_lines = @($text -split "`r?`n" | Where-Object { $_ -match "renderer process gone|reason: crashed|code:\s*-" } | Select-Object -First 25)
        $summary.gpu_error_lines = @($text -split "`r?`n" | Where-Object { $_ -match "GPU Log Messages|SharedImageManager|gpu-process|SwiftShader|unavailable_software" } | Select-Object -First 40)
    }

    return $summary
}

function Classify-ProbeFindings {
    param([Parameter(Mandatory = $true)]$Probes)

    $lookup = @{}
    foreach ($p in $Probes) {
        $lookup[$p.name] = $p
    }

    $noProfile = $lookup["no_profile"]
    $profileRepo = $lookup["with_profile_repo"]
    $profileTemp = $lookup["with_profile_temp"]

    if (($noProfile.exit_code -eq 0) -and ($profileTemp.exit_code -eq 0) -and ($profileRepo.exit_code -ne 0)) {
        return "Profile path is stable outside repo but unstable inside repo. Focus on repo-triggered profile hooks (chthonic env auto-activation)."
    }
    if (($noProfile.exit_code -eq 0) -and (($profileRepo.exit_code -ne 0) -or ($profileTemp.exit_code -ne 0))) {
        return "NoProfile succeeds while profile-mode fails. Root cause is startup profile logic, module imports, or aliases."
    }
    if ($noProfile.exit_code -ne 0) {
        return "NoProfile probe failed. Focus on pwsh binary/runtime, native module crashes, or system-level corruption."
    }
    return "Smoke tests passed. If VS Code still crashes, focus on VS Code terminal host/extension/GPU path with trace logs."
}

$repoRoot = Get-RepoRoot
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$bundleDir = Join-Path $repoRoot (Join-Path $OutRoot ("VSCODE_TERMINAL_TRIAGE_" + $timestamp))
New-Item -ItemType Directory -Path $bundleDir -Force | Out-Null

$pwshPath = (Get-Command pwsh -ErrorAction Stop).Source
$workspaceSettings = Join-Path $repoRoot ".vscode/settings.json"
$userSettings = Join-Path $env:APPDATA "Code - Insiders\User\settings.json"

$report = [ordered]@{
    schema_version = 1
    generated_on_utc = (Get-Date).ToUniversalTime().ToString("o")
    crash_signature = [ordered]@{
        decimal = -1073741819
        hex = (To-HexCode -Code -1073741819)
        meaning = "Access violation (STATUS_ACCESS_VIOLATION)"
    }
    host = [ordered]@{
        computer_name = $env:COMPUTERNAME
        os_version = [System.Environment]::OSVersion.VersionString
        pwsh_path = $pwshPath
        pwsh_version = $PSVersionTable.PSVersion.ToString()
    }
    vscode = [ordered]@{
        code_insiders_cmd = (Get-Command code-insiders -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
        workspace_settings = (Get-SettingStatus -Path $workspaceSettings)
        user_settings = (Get-SettingStatus -Path $userSettings)
        status = $null
    }
    probes = @()
    findings = @()
    log_collection = $null
    api_doctor = $null
    detected_crash_codes = @()
    next_steps = @()
}

if (-not $SkipSmokeTests) {
    $probeNoProfile = Invoke-PwshProbe `
        -Name "no_profile" `
        -PwshPath $pwshPath `
        -ArgumentList @("-NoLogo", "-NoProfile", "-Command", '$PSVersionTable.PSVersion.ToString(); exit 0') `
        -WorkingDirectory $repoRoot `
        -BundleDir $bundleDir
    $probeRepo = Invoke-PwshProbe `
        -Name "with_profile_repo" `
        -PwshPath $pwshPath `
        -ArgumentList @("-NoLogo", "-Command", '$PSVersionTable.PSVersion.ToString(); exit 0') `
        -WorkingDirectory $repoRoot `
        -BundleDir $bundleDir
    $probeTemp = Invoke-PwshProbe `
        -Name "with_profile_temp" `
        -PwshPath $pwshPath `
        -ArgumentList @("-NoLogo", "-Command", '$PSVersionTable.PSVersion.ToString(); exit 0') `
        -WorkingDirectory $env:TEMP `
        -BundleDir $bundleDir

    $report.probes = @($probeNoProfile, $probeRepo, $probeTemp)
    $report.findings += (Classify-ProbeFindings -Probes $report.probes)
}

if (-not $SkipLogCollection) {
    $report.log_collection = Collect-InsidersLogs -BundleDir $bundleDir
    if ($report.log_collection.found -and ($report.log_collection.crash_hits.Count -gt 0)) {
        $report.findings += "Crash signatures detected in latest Insiders logs. Inspect crash_hits in JSON report."
    }
}

if (-not $SkipApiDoctor) {
    $apiDoctorScript = Join-Path $repoRoot ".codex/skills/api-manager/scripts/api_manager.ps1"
    if (Test-Path $apiDoctorScript) {
        $apiDoctorOut = Join-Path $bundleDir "api_doctor.log"
        $apiDoctorErr = Join-Path $bundleDir "api_doctor.err.log"
        $apiExit = 0
        try {
            $proc = Start-Process -FilePath $pwshPath `
                -ArgumentList @("-NoLogo", "-NoProfile", "-File", $apiDoctorScript, "-Doctor") `
                -WorkingDirectory $repoRoot `
                -Wait `
                -PassThru `
                -NoNewWindow `
                -RedirectStandardOutput $apiDoctorOut `
                -RedirectStandardError $apiDoctorErr
            $apiExit = $proc.ExitCode
        } catch {
            $apiExit = -1
            $_ | Out-String | Set-Content -Path $apiDoctorErr -Encoding UTF8
        }

        $report.api_doctor = [ordered]@{
            script = $apiDoctorScript
            exit_code = $apiExit
            stdout_path = $apiDoctorOut
            stderr_path = $apiDoctorErr
        }
    }
}

if (-not $SkipCodeStatus) {
    $report.vscode.status = Invoke-CodeStatus -BundleDir $bundleDir
    if ($report.vscode.status.available -and $report.vscode.status.renderer_crash_lines.Count -gt 0) {
        $report.findings += "code-insiders --status shows renderer crash lines; prioritize GPU/renderer stabilization path."
    }
}

$crashCodeLines = @()
if ($report.log_collection -and $report.log_collection.crash_hits) {
    $crashCodeLines += @($report.log_collection.crash_hits | ForEach-Object { [string]$_.text })
}
if ($report.vscode.status -and $report.vscode.status.available -and $report.vscode.status.renderer_crash_lines) {
    $crashCodeLines += @($report.vscode.status.renderer_crash_lines | ForEach-Object { [string]$_ })
}
$detectedCodes = Parse-CrashCodesFromLines -Lines $crashCodeLines
$report.detected_crash_codes = Build-CrashCodeDescriptors -Codes $detectedCodes
if ($report.detected_crash_codes.Count -gt 0) {
    $codesLabel = (@($report.detected_crash_codes | ForEach-Object { "$($_.decimal) ($($_.hex))" }) -join ", ")
    $report.findings += ("Detected crash codes: " + $codesLabel)
}

$report.next_steps += @(
    "Inside VS Code Insiders, run: Developer: Set Log Level... -> Trace.",
    "Inside VS Code Insiders, run: Terminal: Set Log Level... -> Trace.",
    'Set terminal profile to no-profile during stabilization: args ["-NoProfile", "-NoLogo"].',
    "Start Insiders once with --disable-gpu and compare crash frequency.",
    "Start Insiders once with --disable-extensions and compare crash frequency.",
    "If no-profile is stable, re-enable profile incrementally and isolate crashing hook."
)

$jsonPath = Join-Path $bundleDir "triage_report.json"
$mdPath = Join-Path $bundleDir "triage_report.md"

$report | ConvertTo-Json -Depth 12 | Set-Content -Path $jsonPath -Encoding UTF8

$probeLines = @()
if ($report.probes.Count -gt 0) {
    foreach ($p in $report.probes) {
        $probeLines += ("| {0} | {1} | {2} | {3} |" -f $p.name, $p.exit_code, $p.exit_hex, $p.elapsed_ms)
    }
}

$logHits = 0
if ($report.log_collection -and $report.log_collection.crash_hits) {
    $logHits = $report.log_collection.crash_hits.Count
}

$md = @()
$md += "# VS Code Terminal Crash Doctor Report"
$md += ""
$md += "- Generated (UTC): " + $report.generated_on_utc
$md += '- Crash signature: `-1073741819` (`0xC0000005`, access violation)'
$md += ('- pwsh: `{0}` version `{1}`' -f $report.host.pwsh_path, $report.host.pwsh_version)
$md += ""
$md += "## Probe Matrix"
$md += ""
$md += "| Probe | Exit | Hex | Elapsed ms |"
$md += "|---|---:|---|---:|"
if ($probeLines.Count -gt 0) {
    $md += $probeLines
} else {
    $md += "| (skipped) | - | - | - |"
}
$md += ""
$md += "## Findings"
foreach ($f in $report.findings) {
    $md += "- " + $f
}
if ($report.findings.Count -eq 0) {
    $md += "- No findings generated."
}
$md += ""
$md += "## Logs"
if ($report.log_collection -and $report.log_collection.found) {
    $md += ('- Source log dir: `{0}`' -f $report.log_collection.source_dir)
    $md += ('- Copied log files: `{0}`' -f $report.log_collection.copied_files.Count)
    $md += ('- Crash-pattern hits: `{0}`' -f $logHits)
} else {
    $md += "- No Insiders logs found."
}
$md += ""
$md += "## Detected Crash Codes"
if ($report.detected_crash_codes.Count -gt 0) {
    foreach ($c in $report.detected_crash_codes) {
        $md += ('- `{0}` (`{1}`): {2}' -f $c.decimal, $c.hex, $c.meaning)
    }
} else {
    $md += "- None detected from current bundle/status lines."
}
$md += ""
$md += "## Code Status"
if ($report.vscode.status -and $report.vscode.status.available) {
    $md += ('- code-insiders --status exit: `{0}`' -f $report.vscode.status.exit_code)
    $md += ('- Renderer crash lines: `{0}`' -f $report.vscode.status.renderer_crash_lines.Count)
    $md += ('- GPU error lines: `{0}`' -f $report.vscode.status.gpu_error_lines.Count)
} else {
    $md += "- code-insiders --status unavailable."
}
$md += ""
$md += "## Next Steps"
foreach ($s in $report.next_steps) {
    $md += "1. " + $s
}
$md += ""
$md += "## Artifacts"
$md += ('- JSON: `{0}`' -f $jsonPath)
if ($report.api_doctor -and $report.api_doctor.stdout_path) {
    $md += ('- API doctor log: `{0}`' -f $report.api_doctor.stdout_path)
}
$md += ('- Bundle dir: `{0}`' -f $bundleDir)

$md -join "`n" | Set-Content -Path $mdPath -Encoding UTF8

Write-Host "Wrote triage bundle: $bundleDir"
Write-Host "Wrote JSON report: $jsonPath"
Write-Host "Wrote Markdown report: $mdPath"
