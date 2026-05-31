#!/usr/bin/env pwsh
#
# @SID: SCRIPT_INSIDERS_SYNC_V1
# @Type: UTILITY
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Deterministic VS Code Insiders convergence lane for Chthonic extensions.
#
<#
SYNOPSIS
  Deterministic VS Code Insiders convergence lane for Chthonic extensions.

GOAL
  Run one command after VS Code Insiders + extension updates/restarts so the
  workspace converges to a known-good state.

USAGE
  pwsh -NoProfile -File scripts/insiders-sync.ps1
  pwsh -NoProfile -File scripts/insiders-sync.ps1 -Quick
  pwsh -NoProfile -File scripts/insiders-sync.ps1 -Package
  pwsh -NoProfile -File scripts/insiders-sync.ps1 -WithDts -Package
  pwsh -NoProfile -File scripts/insiders-sync.ps1 -Install        # package + force-install into Insiders
  pwsh -NoProfile -File scripts/insiders-sync.ps1 -Quick -Install # fast train-stop: compile + e2e + package + install

NOTE
  -Package builds and validates the VSIX but does NOT install it. -Install
  implies -Package and then force-installs every *-insiders.vsix into VS Code
  Insiders (version is unchanged, so --force is required), closing the gap where
  a "sync" never reached the running extension. Reload the window afterward.
#>

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
    # Install requires a freshly-built, validated VSIX — packaging is its prerequisite.
    if ($Install) { $Package = $true }
    function Invoke-Bun {
        param(
            [Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)][string[]]$Args
        )

        & bun @Args
        if ($LASTEXITCODE -ne 0) {
            throw "bun $($Args -join ' ') failed with exit code $LASTEXITCODE"
        }
    }

    function Invoke-Step {
        param(
            [Parameter(Mandatory = $true)][string]$Label,
            [Parameter(Mandatory = $true)][scriptblock]$Body
        )

        Write-Host "==> $Label" -ForegroundColor Cyan
        if ($DryRun) {
            Write-Host "[dry-run] Would run: $Label" -ForegroundColor Yellow
        } else {
            & $Body
            Write-Host "ok: $Label" -ForegroundColor Green
        }
    }

    # Discover every local extension following the insiders packaging convention
    # (exposes an `insiders:package` script). Convention-based, NOT a hardcoded
    # list — a new extension joins this lane the moment it adopts the script, so
    # the lane can never silently leave one stale (the bug that left vampire-corpus
    # and Chtonic-rendered behind the old hardcoded trio).
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
    Write-Host ("discovered " + $exts.Count + " insiders-convention extension(s): " + (($exts | ForEach-Object { $_.Dir }) -join ', ')) -ForegroundColor DarkGray

    Invoke-Step -Label "Insiders dev kits check" -Body {
        Invoke-Bun run ext:kits:check
    }

    if ($WithDts) {
        Invoke-Step -Label "Sync vscode-dts (archive/statusbar/mandala)" -Body {
            Invoke-Bun run --cwd extensions/chthonic-archive insiders:dts:sync
            Invoke-Bun run --cwd extensions/chthonic-statusbar insiders:dts:sync
            Invoke-Bun run --cwd extensions/chthonic-mandala insiders:dts:sync
        }
    }

    Invoke-Step -Label "Compile discovered extensions" -Body {
        foreach ($e in $exts) {
            if ($e.HasCompile) { Invoke-Bun run --cwd "extensions/$($e.Dir)" compile }
            else { Write-Host "  (skip compile: $($e.Dir) has no compile script; its insiders:package self-builds)" -ForegroundColor DarkGray }
        }
    }

    Invoke-Step -Label "Insiders E2E smoke" -Body {
        Invoke-Bun run ext:e2e
    }

    if (-not $Quick) {
        Invoke-Step -Label "Archaeology diagnostics" -Body {
            Invoke-Bun run verify
        }

        Invoke-Step -Label "Bun strict audit" -Body {
            Invoke-Bun run bun:audit:strict
        }
    }

    if ($Package) {
        Invoke-Step -Label "Package Insiders VSIX" -Body {
            foreach ($e in $exts) {
                Invoke-Bun run --cwd "extensions/$($e.Dir)" insiders:package
            }
        }
        if (-not $DryRun) {
            $vsixFiles = @(Get-ChildItem -Path $RepoRoot -Filter "*.vsix" -Recurse -ErrorAction SilentlyContinue)
            if ($vsixFiles.Count -eq 0) {
                throw "Package step produced no .vsix files under $RepoRoot"
            }
            $zeroSize = @($vsixFiles | Where-Object { $_.Length -eq 0 })
            if ($zeroSize.Count -gt 0) {
                throw "Package step produced 0-byte .vsix file(s): $($zeroSize.FullName -join ', ')"
            }
            Write-Host "vsix validation OK: $($vsixFiles.Count) file(s), all > 0 bytes" -ForegroundColor Green
        }
    }

    if ($Install) {
        Invoke-Step -Label "Install Insiders VSIX (--force)" -Body {
            if (-not (Get-Command code-insiders -ErrorAction SilentlyContinue)) {
                throw "code-insiders not on PATH; packaged VSIX(s) remain under $RepoRoot for manual install."
            }
            # Install only the *-insiders.vsix this lane produces (skip stray vsix).
            $insidersVsix = @(Get-ChildItem -Path $RepoRoot -Filter "*-insiders.vsix" -Recurse -ErrorAction SilentlyContinue)
            if ($insidersVsix.Count -eq 0) { throw "no *-insiders.vsix found to install" }
            foreach ($v in $insidersVsix) {
                Write-Host "  installing $($v.Name)" -ForegroundColor DarkCyan
                & code-insiders --install-extension $v.FullName --force
                if ($LASTEXITCODE -ne 0) { throw "install failed for $($v.Name) (exit $LASTEXITCODE)" }
            }
            Write-Host "  installed $($insidersVsix.Count) extension(s); RELOAD the window (Developer: Reload Window) to activate." -ForegroundColor Yellow
        }
    }

    Write-Host "sync complete: VS Code Insiders extension lanes converged." -ForegroundColor Green
}
finally {
    Pop-Location
}
