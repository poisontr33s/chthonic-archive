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
#>

param(
    [switch]$Quick,
    [switch]$WithDts,
    [switch]$Package,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $RepoRoot = Split-Path -Parent $PSScriptRoot
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

    Invoke-Step -Label "Compile extension trio" -Body {
        Invoke-Bun run --cwd extensions/chthonic-archive compile
        Invoke-Bun run --cwd extensions/chthonic-statusbar compile
        Invoke-Bun run --cwd extensions/chthonic-mandala compile
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
            Invoke-Bun run ext:package:insiders
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

    Write-Host "sync complete: VS Code Insiders extension lanes converged." -ForegroundColor Green
}
finally {
    Pop-Location
}
