#!/usr/bin/env pwsh

# @SID: CLAUDEBASE_BRIDGE_TROLL_V3

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: YouJustGotTrolled.ps1
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: VIOLET
# ║ Temple-Ayllu Zone: 🔱 THE MALLQUI-AKH FORGE
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ scripts/chthonic.ps1  (Target Monolith — canonical Clear-MCPLocks lives here)
# ║   └─◄ CLAUDEBASE/usables/BridgeTroll/Init_bridgetroll.md  (Original commission)
# ║   └─◄ ROAST.md / TODO.md  (repo root — the audit this was born from)
# ╚════════════════════════════════════════════════════════════════════════════

# ==============================================================================
# BridgeTroll - Del 3: repeatable toolchain refresh, lock-safe
#
# V1/V2 were one-shot patch scripts (config-file edits + sqlpackage install);
# those fixes already landed directly during the 2026-07-05 BridgeTroll audit
# pass and are not repeated here — re-running them would just no-op against
# already-corrected files, so keeping them here would be dead weight.
#
# What's left as genuinely repeatable is the lock-then-update sequence: MCP
# stdio servers (uvx mcp-server-*) hold Windows file-image locks on the exact
# binaries `uv self update` / `bun upgrade` need to overwrite. That routine
# now lives ONCE, canonically, in scripts/chthonic.ps1 as `Clear-MCPLocks` +
# `chthonic mcp unlock` (also auto-runs as a pre-step inside `doctor --fix`).
# This file is a thin caller, not a second implementation — see
# AGENT_COMMON.md's "canonical source, pointer only" rule and
# CLAUDEBASE/MANIFEST.md's "same value six times is noise, not safety".
# ==============================================================================

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$chthonic = Join-Path $repoRoot "scripts\chthonic.ps1"

Write-Host "`n[BRIDGE TROLL DEL 3: TOOLCHAIN REFRESH]" -ForegroundColor Cyan

Write-Host "`n[1/2] Clearing MCP-spawned toolchain locks (delegated to chthonic mcp unlock)..." -ForegroundColor Yellow
if (Test-Path $chthonic) {
    & $chthonic mcp unlock
} else {
    Write-Warning "scripts/chthonic.ps1 not found at expected repo root: $repoRoot"
}

Write-Host "`n[2/2] Syncing toolchain to latest patch..." -ForegroundColor Yellow
try { rustup update stable } catch { Write-Warning "rustup update failed: $_" }
try { uv self update } catch { Write-Warning "uv self update failed: $_" }
try { bun upgrade } catch { Write-Warning "bun upgrade failed: $_" }

Write-Host "`n==============================================================================" -ForegroundColor Cyan
Write-Host "BRIDGE TROLL DEL 3 FULLFØRT — locks cleared, toolchain synced, no duplication." -ForegroundColor Green
Write-Host "==============================================================================" -ForegroundColor Cyan
