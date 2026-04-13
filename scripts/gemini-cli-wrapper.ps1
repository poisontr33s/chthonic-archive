#!/usr/bin/env pwsh
# @SID: SCRIPT_GEMINI_CLI_WRAPPER_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: gemini-cli-wrapper.ps1
# ║ Module: Gemini CLI wrapper
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: UTILITY
# ║ Semantic ID: SCRIPT_GEMINI_CLI_WRAPPER_V1
# ║ Purpose: Wrap Gemini CLI from the repo-local Bun lane and disable MCP discovery during startup
# ║ Exports: (none)
# ║ Flags/Modes: -m/-p/-i/-u/-v/-h/-y/-c/-r and -Arguments passthrough
# ║ Cross-References: (none)
# ╚════════════════════════════════════════════════════════════════════════════

# Gemini CLI Wrapper - repo-local lane
# This repo treats Gemini CLI as a workspace dependency under node_modules,
# not as a global Bun/npm install under ~/.bun or ~/node_modules.
# Issue: Gemini CLI MCP discovery fails on startup → crash
# Fix: Set GEMINI_DISABLE_MCP env var before execution

[CmdletBinding(PositionalBinding = $false)]
param(
    [Alias("m")]
    [string]$Model,

    [Alias("p")]
    [string]$Prompt,

    [Alias("i")]
    [string]$PromptInteractive,

    [Alias("y")]
    [switch]$Yolo,

    [Alias("h")]
    [switch]$Help,

    [Alias("v")]
    [switch]$Version,

    [Alias("u")]
    [switch]$SelfUpdate,

    [Alias("c")]
    [switch]$CheckUpdate,

    [Alias("r")]
    [switch]$Repair,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

# MCP discovery enabled — all 6 mcpServers in .gemini/settings.json are active.
# Belt: chthonic-archive-sync extension provides GEMINI.md context injection only (no spawned servers).
# If a specific MCP server crashes, gemini logs the failure but continues.
# To temporarily disable: set $env:GEMINI_DISABLE_MCP = "1" before invoking.

# IDE companion wiring: auto-detect VS Code Insiders ancestor PID so gemini can find its
# port file via the official GEMINI_CLI_IDE_PID override (bypasses process-tree walk).
# Only sets if not already overridden by the caller.
function Get-VsCodeInsidersPid {
    try {
        $processMap = @{}
        Get-CimInstance Win32_Process -Property ProcessId, ParentProcessId, Name -EA SilentlyContinue |
            ForEach-Object { $processMap[[int]$_.ProcessId] = $_ }

        $current = $processMap[$PID]
        $depth = 0
        $lastCodePid = $null
        while ($current -and $depth -lt 32) {
            if ($current.Name -match '^Code\s*-\s*Insiders\.exe$') {
                $lastCodePid = $current.ProcessId  # keep walking — want the root VS Code window
            }
            $current = $processMap[[int]$current.ParentProcessId]
            $depth++
        }
        return $lastCodePid
    } catch {
        # Non-fatal — IDE wiring is best-effort
    }
    return $null
}

if (-not $env:GEMINI_CLI_IDE_PID) {
    $ideParentPid = Get-VsCodeInsidersPid
    if ($ideParentPid) {
        $env:GEMINI_CLI_IDE_PID = [string]$ideParentPid
    }
}

# Serializable snapshot of the current VS Code session topology.
# Call before updating VS Code to capture baseline; compare after restart to verify lane integrity.
# Output is a PSObject — pipe to ConvertTo-Json for machine-readable storage.
# Survives updates: post-restart, RootPid changes but structure is identical.
function Export-VsCodeSession {
    [CmdletBinding()]
    param()
    try {
        $map = @{}
        Get-CimInstance Win32_Process -Property ProcessId, ParentProcessId, Name, CommandLine -EA SilentlyContinue |
            ForEach-Object { $map[[int]$_.ProcessId] = $_ }

        $rootPid = Get-VsCodeInsidersPid

        # Extension host = Code-Insiders child of root that is our direct ancestor
        $extHostPid = $null
        if ($rootPid) {
            $cur = $PID
            while ($cur -and $map[$cur]) {
                $p = $map[$cur]
                if ($p.Name -match '^Code\s*-\s*Insiders\.exe$' -and [int]$p.ParentProcessId -eq $rootPid) {
                    $extHostPid = [int]$p.ProcessId
                    break
                }
                $cur = [int]$p.ParentProcessId
            }
        }

        # VS Code version from crashpad child command line annotation
        $vsVersion = 'unknown'
        if ($rootPid) {
            $crashpad = $map.Values |
                Where-Object { $_.Name -match '^Code' -and $_.CommandLine -like '*crashpad-handler*' -and [int]$_.ParentProcessId -eq $rootPid } |
                Select-Object -First 1
            if ($crashpad -and $crashpad.CommandLine -match '_version=([0-9.]+)') { $vsVersion = $Matches[1] }
        }

        # Staged update installer detection (Inno Setup child of root window)
        $updateInstaller = $map.Values |
            Where-Object { $_.Name -like 'CodeSetup-insider*.exe' -and [int]$_.ParentProcessId -eq $rootPid } |
            Select-Object -First 1
        $updateHash = $null
        if ($updateInstaller -and $updateInstaller.Name -match 'CodeSetup-insider-([0-9a-f]+)\.exe') {
            $updateHash = $Matches[1]
        }

        # IDE companion port file (written by extension host; named with root VS Code ppid)
        $portFileDir  = "$env:TEMP\gemini\ide"
        $portFileGlob = "gemini-ide-server-$rootPid-*.json"
        $portFile     = $null
        if ($rootPid -and (Test-Path $portFileDir -EA SilentlyContinue)) {
            $portFile = Get-ChildItem $portFileDir -Filter $portFileGlob -EA SilentlyContinue |
                Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
        }

        return [PSCustomObject]@{
            CapturedAt       = [datetime]::UtcNow.ToString('o')
            VSCodeVersion    = $vsVersion
            RootPid          = $rootPid
            ExtensionHostPid = $extHostPid
            ShellPid         = $PID
            PortFilePath     = $portFile
            PortFilePattern  = if ($rootPid) { Join-Path $portFileDir $portFileGlob } else { $null }
            UpdateStaged     = [bool]$updateInstaller
            UpdateHash       = $updateHash
        }
    } catch {
        return [PSCustomObject]@{ Error = $_.Exception.Message }
    }
}

function Get-IsHeadlessInvocation {
    param(
        [string[]]$CliArgs
    )

    foreach ($arg in $CliArgs) {
        if ($arg -in @("-p", "--prompt", "--prompt-interactive", "--output-format", "--output-format=json", "--output-format=text")) {
            return $true
        }

        if ($arg.StartsWith("--prompt=") -or $arg.StartsWith("--output-format=")) {
            return $true
        }
    }

    return $false
}

function Get-IsInformationalInvocation {
    param(
        [string[]]$CliArgs
    )

    foreach ($arg in $CliArgs) {
        if ($arg -in @("--version", "--help")) {
            return $true
        }
    }

    return $false
}

function Get-RepoRoot {
    if ($PSScriptRoot) {
        return (Split-Path -Parent $PSScriptRoot)
    }

    if ($PSCommandPath) {
        return (Split-Path -Parent (Split-Path -Parent $PSCommandPath))
    }

    throw "Unable to resolve repo root for gemini-cli-wrapper.ps1"
}

function Get-RepoNodeModulesRoot {
    return (Join-Path (Get-RepoRoot) "node_modules")
}

function Get-GeminiRegistryPath {
    return (Join-Path (Get-RepoRoot) ".gemini\local-model-registry.json")
}

function Get-GeminiRouterScriptPath {
    return (Join-Path (Get-RepoRoot) "scripts\gemini-model-router.ts")
}

function Get-GeminiDeclaredSpecifier {
    $packageJsonPath = Join-Path (Get-RepoRoot) "package.json"
    if (-not (Test-Path $packageJsonPath)) {
        return "@latest"
    }

    try {
        $pkg = Get-Content $packageJsonPath -Raw | ConvertFrom-Json
    } catch {
        return "@latest"
    }

    $specifier = $null
    if ($pkg.devDependencies -and $pkg.devDependencies.'@google/gemini-cli') {
        $specifier = [string]$pkg.devDependencies.'@google/gemini-cli'
    } elseif ($pkg.dependencies -and $pkg.dependencies.'@google/gemini-cli') {
        $specifier = [string]$pkg.dependencies.'@google/gemini-cli'
    }

    if ([string]::IsNullOrWhiteSpace($specifier)) {
        return "@latest"
    }

    $specifier = $specifier.Trim()
    if ($specifier -match 'nightly') { return "@nightly" }
    if ($specifier -match 'preview') { return "@preview" }
    return "@latest"
}

function Get-GeminiExecutablePath {
    foreach ($candidate in @(
        (Join-Path (Get-RepoNodeModulesRoot) ".bin\gemini"),
        (Join-Path (Get-RepoNodeModulesRoot) ".bin\gemini.cmd"),
        (Join-Path (Get-RepoNodeModulesRoot) ".bin\gemini.exe")
    )) {
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

function Get-GeminiPackageRoot {
    $candidates = @(
        (Join-Path (Get-RepoNodeModulesRoot) "@google\gemini-cli")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Get-GeminiShimMetadataPath {
    return (Join-Path (Get-RepoNodeModulesRoot) ".bin\gemini.bunx")
}

function Get-GeminiEntrypoint {
    $packageRoot = Get-GeminiPackageRoot
    if (-not $packageRoot) {
        return $null
    }

    $packageJsonPath = Join-Path $packageRoot "package.json"
    if (Test-Path $packageJsonPath) {
        try {
            $packageJson = Get-Content $packageJsonPath -Raw | ConvertFrom-Json
            $candidateScripts = @()
            if ($packageJson.bin) {
                if ($packageJson.bin -is [string]) {
                    $candidateScripts += $packageJson.bin
                } elseif ($packageJson.bin.PSObject.Properties.Name -contains "gemini") {
                    $candidateScripts += $packageJson.bin.gemini
                } elseif ($packageJson.bin.PSObject.Properties.Count -gt 0) {
                    $candidateScripts += $packageJson.bin.PSObject.Properties[0].Value
                }
            }
            if ($packageJson.main) {
                $candidateScripts += $packageJson.main
            }

            foreach ($candidateScript in ($candidateScripts | Where-Object { $_ } | Select-Object -Unique)) {
                $entry = Join-Path $packageRoot $candidateScript
                if (Test-Path $entry) {
                    return $entry
                }
            }
        } catch {
            # Fall back to the known Gemini dist path below.
        }
    }

    $fallback = Join-Path $packageRoot "dist\index.js"
    if (Test-Path $fallback) {
        return $fallback
    }

    return $null
}

function Get-GeminiShimMetadata {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        return $null
    }

    try {
        $bytes = [System.IO.File]::ReadAllBytes($Path)
    } catch {
        return $null
    }

    if ($bytes.Length -lt 14) {
        return $null
    }

    $binLength = [BitConverter]::ToInt32($bytes, $bytes.Length - 10)
    $launcherLength = [BitConverter]::ToInt32($bytes, $bytes.Length - 6)
    $flags = [BitConverter]::ToUInt16($bytes, $bytes.Length - 2)
    $separatorLength = 4
    $expectedLength = $binLength + $separatorLength + $launcherLength + 10

    if ($binLength -lt 0 -or $launcherLength -lt 0 -or $expectedLength -ne $bytes.Length) {
        return $null
    }

    if ($bytes[$binLength] -ne 0x22 -or $bytes[$binLength + 1] -ne 0x00 -or $bytes[$binLength + 2] -ne 0x00 -or $bytes[$binLength + 3] -ne 0x00) {
        return $null
    }

    $pathBytes = New-Object byte[] $binLength
    [Array]::Copy($bytes, 0, $pathBytes, 0, $binLength)
    $launcherBytes = New-Object byte[] $launcherLength
    [Array]::Copy($bytes, $binLength + $separatorLength, $launcherBytes, 0, $launcherLength)

    return [pscustomobject]@{
        Path = $Path
        PathBytes = $pathBytes
        Launcher = [System.Text.Encoding]::Unicode.GetString($launcherBytes)
        Version = ($flags -shr 3)
        Flags = $flags
        HasShebang = (($flags -band 0b100) -ne 0)
        IsNode = (($flags -band 0b010) -ne 0)
        IsNodeOrBun = (($flags -band 0b001) -ne 0)
    }
}

function Get-NormalizedGeminiLauncher {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Launcher
    )

    if ($Launcher -match '^-S node(?:\s+(?<args>.*))?$') {
        $args = $Matches["args"]
        if ([string]::IsNullOrEmpty($args)) {
            return "bun "
        }
        return "bun $args"
    }

    return $null
}

function Get-BunShimVersion {
    $candidatePaths = @(
        (Join-Path $env:USERPROFILE ".bun\bin\codex.bunx"),
        (Join-Path $env:USERPROFILE ".bun\bin\biome.bunx")
    )

    foreach ($candidatePath in $candidatePaths) {
        if (-not (Test-Path $candidatePath)) {
            continue
        }

        try {
            $candidateBytes = [System.IO.File]::ReadAllBytes($candidatePath)
        } catch {
            continue
        }

        if ($candidateBytes.Length -lt 2) {
            continue
        }

        $rawFlags = [BitConverter]::ToUInt16($candidateBytes, $candidateBytes.Length - 2)
        if ($rawFlags -ne 0) {
            return ($rawFlags -shr 3)
        }
    }

    return 5478
}

function Write-GeminiShimMetadata {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [byte[]]$PathBytes,

        [Parameter(Mandatory = $true)]
        [string]$Launcher,

        [Parameter(Mandatory = $true)]
        [int]$Version
    )

    $separator = [byte[]](0x22, 0x00, 0x00, 0x00)
    $launcherBytes = [System.Text.Encoding]::Unicode.GetBytes($Launcher)
    $flags = [uint16](($Version -shl 3) -bor 0b101)
    $updatedBytes = New-Object byte[] ($PathBytes.Length + $separator.Length + $launcherBytes.Length + 10)

    [Array]::Copy($PathBytes, 0, $updatedBytes, 0, $PathBytes.Length)
    [Array]::Copy($separator, 0, $updatedBytes, $PathBytes.Length, $separator.Length)
    [Array]::Copy($launcherBytes, 0, $updatedBytes, $PathBytes.Length + $separator.Length, $launcherBytes.Length)
    [Array]::Copy([BitConverter]::GetBytes([int]$PathBytes.Length), 0, $updatedBytes, $PathBytes.Length + $separator.Length + $launcherBytes.Length, 4)
    [Array]::Copy([BitConverter]::GetBytes([int]$launcherBytes.Length), 0, $updatedBytes, $PathBytes.Length + $separator.Length + $launcherBytes.Length + 4, 4)
    [Array]::Copy([BitConverter]::GetBytes($flags), 0, $updatedBytes, $PathBytes.Length + $separator.Length + $launcherBytes.Length + 8, 2)

    [System.IO.File]::WriteAllBytes($Path, $updatedBytes)
}

function Get-GeminiRelativeEntrypoint {
    $entry = Get-GeminiEntrypoint
    if (-not $entry) {
        return $null
    }

    $fullEntry = [System.IO.Path]::GetFullPath($entry)
    $repoNodeModules = [System.IO.Path]::GetFullPath((Get-RepoNodeModulesRoot))

    if ($fullEntry.StartsWith($repoNodeModules, [System.StringComparison]::OrdinalIgnoreCase)) {
        $relative = $fullEntry.Substring($repoNodeModules.Length).TrimStart('\', '/')
        return (".\node_modules\$relative").Replace('/', '\')
    }

    return $null
}

function Repair-GeminiWindowsShim {
    param(
        [switch]$Quiet
    )

    if (-not $IsWindows) {
        return $false
    }

    $metadataPath = Get-GeminiShimMetadataPath
    $metadata = Get-GeminiShimMetadata -Path $metadataPath
    if ($metadata) {
        $normalizedLauncher = Get-NormalizedGeminiLauncher -Launcher $metadata.Launcher
        if (-not $normalizedLauncher) {
            return $false
        }

        Write-GeminiShimMetadata -Path $metadataPath -PathBytes $metadata.PathBytes -Launcher $normalizedLauncher -Version $metadata.Version
        if (-not $Quiet) {
            Write-Host "[gemini-wrapper] Repaired Windows Bun shim metadata: $metadataPath" -ForegroundColor Cyan
        }
        return $true
    }

    return $false
}

function Test-GeminiExecutable {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    try {
        & $Path --version *> $null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Resolve-GeminiExecutable {
    Repair-GeminiWindowsShim -Quiet | Out-Null

    $repoGemini = Get-GeminiExecutablePath
    if ($repoGemini -and (Test-GeminiExecutable -Path $repoGemini)) {
        return $repoGemini
    }

    return $null
}

function Test-LegacyGeminiDependency {
    $pkgPath = Join-Path (Get-Location) "package.json"
    if (-not (Test-Path $pkgPath)) {
        return
    }

    try {
        $pkg = Get-Content $pkgPath -Raw | ConvertFrom-Json
    } catch {
        return
    }

    $hasLegacyGemini =
        ($pkg.dependencies -and $pkg.dependencies.PSObject.Properties.Name -contains "gemini") -or
        ($pkg.devDependencies -and $pkg.devDependencies.PSObject.Properties.Name -contains "gemini")

    if ($hasLegacyGemini) {
        Write-Host "[gemini-wrapper] WARNING: Local package.json contains legacy npm package 'gemini' (not @google/gemini-cli)." -ForegroundColor Yellow
        Write-Host "[gemini-wrapper] Run: bun remove gemini" -ForegroundColor Yellow
    }
}

function Set-GeminiModelArg {
    param(
        [string[]]$ExistingArgs,
        [string]$ModelName
    )

    $cleaned = @()
    for ($index = 0; $index -lt $ExistingArgs.Count; $index++) {
        $arg = $ExistingArgs[$index]
        if ($arg -eq "-m" -or $arg -eq "--model") {
            $index++
            continue
        }
        if ($arg.StartsWith("--model=")) {
            continue
        }
        $cleaned += $arg
    }

    return @("-m", $ModelName) + $cleaned
}

function Invoke-GeminiRouterSync {
    $routerScript = Get-GeminiRouterScriptPath
    if (-not (Test-Path $routerScript)) {
        return
    }

    & bun run $routerScript sync --write *> $null
}

function Get-GeminiRouterDecision {
    param(
        [string[]]$CliArgs,
        [bool]$Headless
    )

    $routerScript = Get-GeminiRouterScriptPath
    if (-not (Test-Path $routerScript)) {
        return $null
    }

    $argsJson = $CliArgs | ConvertTo-Json -Compress
    $mode = if ($Headless) { "headless" } else { "interactive" }
    $raw = & bun run $routerScript resolve --mode $mode --args-json $argsJson

    if ($LASTEXITCODE -ne 0 -or -not $raw) {
        return $null
    }

    return ($raw | Out-String | ConvertFrom-Json)
}

function Test-GeminiCompatRetryableError {
    param(
        [string]$Text,
        [object]$Decision
    )

    if (-not $Decision) {
        return $false
    }

    $matchers = @($Decision.fallbackMatchers)
    if ($matchers.Count -eq 0) {
        return $false
    }

    $textToCheck = ($Text ?? "").ToLowerInvariant()
    foreach ($matcher in $matchers) {
        if (-not $matcher) {
            continue
        }

        if ($textToCheck.Contains(([string]$matcher).ToLowerInvariant())) {
            return $true
        }
    }

    return $false
}

function Write-GeminiCompatNotice {
    param(
        [string]$Message
    )

    [Console]::Error.WriteLine($Message)
}

function Invoke-GeminiCommandCapture {
    param(
        [string[]]$CliArgs
    )

    $geminiExe = Resolve-GeminiExecutable
    $merged = @()

    if ($geminiExe) {
        $merged = & $geminiExe @CliArgs 2>&1
    } else {
        $entry = Get-GeminiEntrypoint
        if (-not $entry) {
            throw "Gemini CLI not found in repo-local Bun lane."
        }
        $merged = & bun $entry @CliArgs 2>&1
    }

    $exitCode = $LASTEXITCODE
    $rawText = ($merged | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine

    return [pscustomobject]@{
        ExitCode = $exitCode
        RawText = $rawText
    }
}

function Invoke-GeminiSelfUpdate {
    Write-Host "[gemini-wrapper] Updating Gemini CLI in repo-local Bun lane..." -ForegroundColor Cyan
    $geminiChannel = Get-GeminiDeclaredSpecifier
    # Keep node-gyp/native addon lanes deterministic on Windows.
    $prevMakeFlags = $env:MAKEFLAGS
    $prevMflags = $env:MFLAGS
    if ($env:MAKEFLAGS) { Remove-Item Env:MAKEFLAGS -ErrorAction SilentlyContinue }
    if ($env:MFLAGS) { Remove-Item Env:MFLAGS -ErrorAction SilentlyContinue }

    Push-Location (Get-RepoRoot)
    try {
        & bun add -D ("@google/gemini-cli{0}" -f $geminiChannel)
    } finally {
        Pop-Location
    }

    if ($null -ne $prevMakeFlags) { $env:MAKEFLAGS = $prevMakeFlags }
    if ($null -ne $prevMflags) { $env:MFLAGS = $prevMflags }
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Gemini CLI self-update failed (exit $LASTEXITCODE)."
        exit $LASTEXITCODE
    }

    $geminiExe = Resolve-GeminiExecutable
    $updated = $null
    if ($geminiExe) {
        $updated = & $geminiExe --version 2>$null
    } else {
        $entry = Get-GeminiEntrypoint
        if ($entry) {
            $updated = & bun $entry --version 2>$null
        }
    }
    if ($LASTEXITCODE -eq 0 -and $updated) {
        Write-Host "[gemini-wrapper] Updated Gemini CLI version: $updated" -ForegroundColor Green
    } else {
        Write-Host "[gemini-wrapper] Update completed. Run `gemini --version` from the repo to confirm." -ForegroundColor Yellow
    }
}

function Invoke-GeminiRepair {
    Write-Host "[gemini-wrapper] Repairing Gemini CLI repo-local lane..." -ForegroundColor Cyan
    Invoke-GeminiSelfUpdate

    $geminiExe = Get-GeminiExecutablePath
    $validated = $null
    if ($geminiExe -and (Test-Path $geminiExe)) {
        $validated = & $geminiExe --version 2>$null
    }
    if ($LASTEXITCODE -ne 0 -or -not $validated) {
        $entry = Get-GeminiEntrypoint
        if ($entry) {
            $validated = & bun $entry --version 2>$null
        }
    }
    if ($LASTEXITCODE -ne 0 -or -not $validated) {
        Write-Error "Gemini CLI repair failed: repo-local Gemini still is not runnable."
        exit 1
    }

    $validatedVersion = ($validated | Select-Object -First 1).Trim()
    Write-Host "[gemini-wrapper] Repair validated: $validatedVersion" -ForegroundColor Green
}

function Get-GeminiCurrentVersion {
    $geminiExe = Resolve-GeminiExecutable
    if ($geminiExe) {
        $raw = & $geminiExe --version 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $raw) {
            return $null
        }
        return ($raw | Select-Object -First 1).Trim()
    }

    $entry = Get-GeminiEntrypoint
    if (-not $entry) {
        return $null
    }
    $raw = & bun $entry --version 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $raw) {
        return $null
    }
    return ($raw | Select-Object -First 1).Trim()
}

function Get-GeminiLatestVersion {
    $geminiChannel = Get-GeminiDeclaredSpecifier
    $raw = & bun pm view ("@google/gemini-cli{0}" -f $geminiChannel) version 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $raw) {
        return $null
    }
    $line = ($raw | Select-Object -First 1).Trim()
    if ($line -match '^\d+\.\d+\.\d+([\-+].*)?$') {
        return $line
    }
    return $null
}

function Invoke-GeminiUpdateCheck {
    $current = Get-GeminiCurrentVersion
    $latest = Get-GeminiLatestVersion

    if (-not $current) {
        Write-Host "[gemini-wrapper] Gemini CLI not found locally." -ForegroundColor Red
        Write-Host ("[gemini-wrapper] Install: bun add -D @google/gemini-cli{0}" -f (Get-GeminiDeclaredSpecifier)) -ForegroundColor Yellow
        exit 1
    }
    if (-not $latest) {
        Write-Host "[gemini-wrapper] Could not query registry for latest version." -ForegroundColor Yellow
        Write-Host "[gemini-wrapper] Current version: $current" -ForegroundColor Cyan
        exit 0
    }

    $needsUpdate = $false
    try {
        $needsUpdate = ([version]$current -lt [version]$latest)
    } catch {
        # Non-standard SemVer labels: fallback to exact compare.
        $needsUpdate = ($current -ne $latest)
    }

    if ($needsUpdate) {
        Write-Host "[gemini-wrapper] Update available: $current -> $latest" -ForegroundColor Yellow
        Write-Host "[gemini-wrapper] Run: pwsh -NoProfile -File scripts/gemini-cli-wrapper.ps1 -u" -ForegroundColor Yellow
    } else {
        Write-Host "[gemini-wrapper] Up to date: $current" -ForegroundColor Green
    }
}

$cliArgs = @()

if ($PSBoundParameters.ContainsKey("Model")) {
    $cliArgs += @("-m", $Model)
}
if ($PSBoundParameters.ContainsKey("Prompt")) {
    $cliArgs += @("--prompt", $Prompt)
}
if ($PSBoundParameters.ContainsKey("PromptInteractive")) {
    $cliArgs += @("--prompt-interactive", $PromptInteractive)
}
if ($Yolo) {
    $cliArgs += "--yolo"
}
if ($Help) {
    $cliArgs += "--help"
}
if ($Version) {
    $cliArgs += "--version"
}
if ($Arguments) {
    $cliArgs += $Arguments
}

$positionalUpdate =
    ($Model -eq "update" -or $Model -eq "--update") -and
    -not $PSBoundParameters.ContainsKey("Prompt") -and
    -not $PSBoundParameters.ContainsKey("PromptInteractive") -and
    (-not $Arguments -or $Arguments.Count -eq 0)

$positionalCheck =
    ($Model -eq "check" -or $Model -eq "check-update" -or $Model -eq "--check-update") -and
    -not $PSBoundParameters.ContainsKey("Prompt") -and
    -not $PSBoundParameters.ContainsKey("PromptInteractive") -and
    (-not $Arguments -or $Arguments.Count -eq 0)

$positionalRepair =
    ($Model -eq "repair" -or $Model -eq "--repair") -and
    -not $PSBoundParameters.ContainsKey("Prompt") -and
    -not $PSBoundParameters.ContainsKey("PromptInteractive") -and
    (-not $Arguments -or $Arguments.Count -eq 0)

if ($CheckUpdate -or $positionalCheck -or ($Arguments -and $Arguments.Count -gt 0 -and ($Arguments[0] -in @("check", "check-update", "--check-update")))) {
    Test-LegacyGeminiDependency
    Invoke-GeminiUpdateCheck
    exit 0
}

if ($Repair -or $positionalRepair -or ($Arguments -and $Arguments.Count -gt 0 -and $Arguments[0] -eq "repair")) {
    Test-LegacyGeminiDependency
    Invoke-GeminiRepair
    exit 0
}

if ($SelfUpdate -or $positionalUpdate -or ($Arguments -and $Arguments.Count -gt 0 -and $Arguments[0] -eq "update")) {
    Test-LegacyGeminiDependency
    Invoke-GeminiSelfUpdate
    exit 0
}

Test-LegacyGeminiDependency

$env:CHTHONIC_GEMINI_MODEL_REGISTRY = Get-GeminiRegistryPath
Invoke-GeminiRouterSync

$isHeadlessInvocation = Get-IsHeadlessInvocation -CliArgs $cliArgs
$isInformationalInvocation = Get-IsInformationalInvocation -CliArgs $cliArgs
$routerDecision = $null
if (-not $isInformationalInvocation) {
    $routerDecision = Get-GeminiRouterDecision -CliArgs $cliArgs -Headless:$isHeadlessInvocation
}

if ($routerDecision -and $routerDecision.forceModelFlag -and $routerDecision.effectiveRequestModel) {
    $cliArgs = Set-GeminiModelArg -ExistingArgs $cliArgs -ModelName $routerDecision.effectiveRequestModel
}

if (-not $isHeadlessInvocation -and
    $routerDecision -and
    $routerDecision.requestedModel -and
    $routerDecision.effectiveRequestModel -and
    $routerDecision.requestedModel -ne $routerDecision.effectiveRequestModel) {
    Write-GeminiCompatNotice ("[gemini-wrapper] Flash-Lite preview compatibility active. Using {0} for this interactive session." -f $routerDecision.effectiveRequestModel)
}

if ($isHeadlessInvocation) {
    $captured = Invoke-GeminiCommandCapture -CliArgs $cliArgs

    if ($captured.ExitCode -ne 0 -and
        $routerDecision -and
        $routerDecision.headlessRetryAllowed -and
        $routerDecision.fallbackRequestModel -and
        (Test-GeminiCompatRetryableError -Text $captured.RawText -Decision $routerDecision)) {
        Write-GeminiCompatNotice ("[gemini-wrapper] Flash-Lite preview unavailable. Retrying with {0}." -f $routerDecision.fallbackRequestModel)
        $fallbackArgs = Set-GeminiModelArg -ExistingArgs $cliArgs -ModelName $routerDecision.fallbackRequestModel
        $captured = Invoke-GeminiCommandCapture -CliArgs $fallbackArgs
    }

    if (-not [string]::IsNullOrEmpty($captured.RawText)) {
        [Console]::Out.Write($captured.RawText)
        if (-not $captured.RawText.EndsWith([Environment]::NewLine)) {
            [Console]::Out.Write([Environment]::NewLine)
        }
    }

    exit $captured.ExitCode
}

$geminiExe = Resolve-GeminiExecutable
if ($geminiExe) {
    & $geminiExe @cliArgs
    exit $LASTEXITCODE
}

# Fallback execution via repo-local package entrypoint.
$geminiCliPath = Get-GeminiEntrypoint
if (-not $geminiCliPath) {
    Write-Error "Gemini CLI not found in repo-local Bun lane."
    Write-Host "Repair with: pwsh -NoProfile -File scripts/gemini-cli-wrapper.ps1 -r" -ForegroundColor Yellow
    exit 1
}

& bun $geminiCliPath @cliArgs
exit $LASTEXITCODE
