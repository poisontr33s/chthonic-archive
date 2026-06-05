#!/usr/bin/env pwsh
# @SID: SCRIPT_INSIDERS_SYNC_V1
# @Purpose: Package and force-install Chthonic VS Code Insiders extensions.
#
# Discovers every extension exposing an `insiders:package` script, compiles +
# packages each, validates the VSIX is non-zero, and (with -Install) force-installs
# only the *-insiders.vsix from those discovered folders. The version is unchanged
# on reinstall, so --force is required. Reload the window afterward to activate.
#
#   pwsh -NoProfile -File scripts/insiders-sync.ps1 -Install
#   pwsh -NoProfile -File scripts/insiders-sync.ps1 -DryRun

param(
    [switch]$Quick,
    [switch]$WithDts,
    [switch]$Package,
    [switch]$Install,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $RepoRoot = Split-Path -Parent $PSScriptRoot
    if ($Install) { $Package = $true }   # install needs a fresh, validated VSIX

    function Invoke-Bun {
        param([Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)][string[]]$Args)
        & bun @Args
        if ($LASTEXITCODE -ne 0) { throw "bun $($Args -join ' ') failed with exit code $LASTEXITCODE" }
    }

    function Invoke-Step {
        param([Parameter(Mandatory = $true)][string]$Label, [Parameter(Mandatory = $true)][scriptblock]$Body)
        Write-Host "==> $Label" -ForegroundColor Cyan
        if ($DryRun) { Write-Host "[dry-run] Would run: $Label" -ForegroundColor Yellow }
        else { & $Body; Write-Host "ok: $Label" -ForegroundColor Green }
    }

    # Discover by convention: any extension folder whose package.json exposes an
    # `insiders:package` script. A new extension joins the lane the moment it adopts
    # the script -- no hardcoded list to leave one stale.
    $extRoot = Join-Path $RepoRoot 'extensions'
    $exts = @(Get-ChildItem $extRoot -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $pj = Join-Path $_.FullName 'package.json'
        if (Test-Path $pj) {
            try { $j = Get-Content $pj -Raw | ConvertFrom-Json } catch { return }
            $names = if ($j.PSObject.Properties.Name -contains 'scripts' -and $j.scripts) { $j.scripts.PSObject.Properties.Name } else { @() }
            if ($names -contains 'insiders:package') {
                [pscustomobject]@{ Dir = $_.Name; HasCompile = ($names -contains 'compile') }
            }
        }
    })
    if ($exts.Count -eq 0) { throw "no extensions expose an 'insiders:package' script under $extRoot" }
    Write-Host ("discovered " + $exts.Count + " extension(s): " + (($exts | ForEach-Object { $_.Dir }) -join ', ')) -ForegroundColor DarkGray

    # Only ever the *-insiders.vsix produced inside the discovered extension folders --
    # never a recursive repo-wide search (that reinstalled stale VSIX from archives).
    function Get-DiscoveredInsidersVsix {
        @($exts | ForEach-Object { Get-ChildItem -Path (Join-Path $extRoot $_.Dir) -Filter "*-insiders.vsix" -File -ErrorAction SilentlyContinue })
    }

    if ($WithDts) {
        Invoke-Step -Label "Sync vscode-dts" -Body {
            Invoke-Bun run --cwd extensions/chthonic-archive insiders:dts:sync
            Invoke-Bun run --cwd extensions/chthonic-statusbar insiders:dts:sync
            Invoke-Bun run --cwd extensions/chthonic-mandala insiders:dts:sync
        }
    }

    Invoke-Step -Label "Compile discovered extensions" -Body {
        foreach ($e in $exts) {
            if ($e.HasCompile) { Invoke-Bun run --cwd "extensions/$($e.Dir)" compile }
            else { Write-Host "  (skip compile: $($e.Dir) self-builds via insiders:package)" -ForegroundColor DarkGray }
        }
    }

    if ($Package) {
        Invoke-Step -Label "Package Insiders VSIX" -Body {
            foreach ($e in $exts) { Invoke-Bun run --cwd "extensions/$($e.Dir)" insiders:package }
        }
        if (-not $DryRun) {
            $vsixFiles = Get-DiscoveredInsidersVsix
            if ($vsixFiles.Count -eq 0) { throw "Package step produced no *-insiders.vsix under discovered extension directories" }
            $zeroSize = @($vsixFiles | Where-Object { $_.Length -eq 0 })
            if ($zeroSize.Count -gt 0) { throw "Package step produced 0-byte .vsix file(s): $($zeroSize.FullName -join ', ')" }
            Write-Host "vsix validation OK: $($vsixFiles.Count) file(s), all > 0 bytes" -ForegroundColor Green
        }
    }

    if ($Install) {
        Invoke-Step -Label "Install Insiders VSIX (--force)" -Body {
            if (-not (Get-Command code-insiders -ErrorAction SilentlyContinue)) {
                throw "code-insiders not on PATH; packaged VSIX(s) remain in their extension folders for manual install."
            }
            $insidersVsix = Get-DiscoveredInsidersVsix
            if ($insidersVsix.Count -eq 0) { throw "no *-insiders.vsix found to install" }
            foreach ($v in $insidersVsix) {
                Write-Host "  installing $($v.Name)" -ForegroundColor DarkCyan
                & code-insiders --install-extension $v.FullName --force
                if ($LASTEXITCODE -ne 0) { throw "install failed for $($v.Name) (exit $LASTEXITCODE)" }
            }
            Write-Host "  installed $($insidersVsix.Count) extension(s); RELOAD the window (Developer: Reload Window) to activate." -ForegroundColor Yellow
        }
    }

    Write-Host "sync complete." -ForegroundColor Green
}
finally {
    Pop-Location
}
