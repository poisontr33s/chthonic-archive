#!/usr/bin/env pwsh
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
    [switch]$Package
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location (Split-Path -Parent $PSScriptRoot)
try {
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
        & $Body
        Write-Host "ok: $Label" -ForegroundColor Green
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
    }

    Write-Host "sync complete: VS Code Insiders extension lanes converged." -ForegroundColor Green
}
finally {
    Pop-Location
}
