#!/usr/bin/env pwsh
# SID: CHTHONIC_INTEGRITY_RECONCILE_PS1_V1
# scripts/insiders-integrity-reconcile.ps1
#
# Owned integrity reconciler for the Chthonic VS Code Insiders substrate.
# Recomputes product.json checksums for Chthonic-owned patched files only.
#
# Does not touch any checksum entry outside the allowlist.
# Does not run unless mica-substrate.ps1 -Verify passes.
# Does not endorse foreign drift — Vibrancy or Claude Design markers abort.
#
# Algorithm: SHA-256(file_bytes) → base64 → strip trailing =
# Replicates VS Code ChecksumService exactly (src/vs/platform/checksum/node/checksumService.ts).
#
# Modes: -Status | -Apply | -Verify | -Restore
# Made by Claude.

[CmdletBinding()]
param(
    [switch]$Status,
    [switch]$Apply,
    [switch]$Verify,
    [switch]$Restore
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── Allowlist ─────────────────────────────────────────────────────
# Only these paths may be reconciled. All resolve to {app_root}/out/{path}.
# main.js is intentionally absent — not tracked in the checksum table.

$ALLOWLIST = @(
    'vs/code/electron-browser/workbench/workbench.html',
    'vs/code/electron-sandbox/workbench/workbench.html',
    'vs/code/electron-sandbox/workbench/workbench.esm.html'
)

# ── Marker constants ──────────────────────────────────────────────
# Must match mica-substrate.ps1 exactly.

$CHTHONIC_CSS_MARKER = 'data-claude-design-substrate="vibrancy-obsidian"'
$VIBRANCY_MARKER     = '!! VSCODE-VIBRANCY-START !!'

# ── Paths ─────────────────────────────────────────────────────────

$PROGRAMS_ROOT = Join-Path $env:LOCALAPPDATA 'Programs\Microsoft VS Code Insiders'
$REPO_ROOT     = Split-Path -Parent $PSScriptRoot
$BACKUP_DIR    = Join-Path $REPO_ROOT 'CLAUDEBASE\hold\vscode-insiders-substrate\backups'

# ── Discovery ─────────────────────────────────────────────────────

function Find-AppRoot {
    $dirs = Get-ChildItem -Path $PROGRAMS_ROOT -Directory -ErrorAction Stop |
        Where-Object { $_.Name -match '^[0-9a-f]{10,}$' } |
        Sort-Object LastWriteTime -Descending
    if (-not $dirs) {
        throw "No VS Code Insiders commit directory under $PROGRAMS_ROOT"
    }
    $appRoot = Join-Path $dirs[0].FullName 'resources\app'
    if (-not (Test-Path $appRoot)) {
        throw "resources\app not found under $($dirs[0].FullName)"
    }
    return $appRoot
}

function Read-AppMeta {
    param([string]$AppRoot)
    $productPath = Join-Path $AppRoot 'product.json'
    if (-not (Test-Path $productPath)) {
        throw "product.json not found at $productPath"
    }
    $raw = [System.IO.File]::ReadAllText($productPath, [System.Text.Encoding]::UTF8)
    $obj = $raw | ConvertFrom-Json
    return @{
        AppRoot     = $AppRoot
        ProductPath = $productPath
        ProductRaw  = $raw
        Commit      = $obj.commit
        Version     = $obj.version
        Checksums   = $obj.checksums
    }
}

# ── Checksum ──────────────────────────────────────────────────────

function Get-VscChecksum {
    param([string]$FilePath)
    # Exact replication of VS Code ChecksumService.
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.IO.File]::ReadAllBytes($FilePath)
        $hash  = $sha256.ComputeHash($bytes)
        return [System.Convert]::ToBase64String($hash).TrimEnd('=')
    } finally {
        $sha256.Dispose()
    }
}

# ── Marker guard ──────────────────────────────────────────────────

function Assert-ChthonicOwnership {
    param([string]$FilePath)
    $text = [System.IO.File]::ReadAllText($FilePath, [System.Text.Encoding]::UTF8)
    if ($text -notmatch [regex]::Escape($CHTHONIC_CSS_MARKER)) {
        throw "Chthonic CSS marker absent in $(Split-Path $FilePath -Leaf) — substrate not applied"
    }
    if ($text -match [regex]::Escape($VIBRANCY_MARKER)) {
        throw "Vibrancy Continued marker found in $(Split-Path $FilePath -Leaf) — foreign drift; abort"
    }
}

# ── Substrate gate ────────────────────────────────────────────────

function Assert-SubstrateVerified {
    $script = Join-Path $REPO_ROOT 'scripts\mica-substrate.ps1'
    if (-not (Test-Path $script)) {
        throw "mica-substrate.ps1 not found — cannot verify substrate state before reconcile"
    }
    & pwsh -NoProfile -File $script -Verify | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "mica-substrate.ps1 -Verify failed — run scripts\mica-substrate.ps1 -Apply first"
    }
}

# ── Backup ────────────────────────────────────────────────────────

function Write-ProductBackup {
    param([string]$ProductPath, [string]$Commit, [string]$ProductRaw)
    New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null
    $dest = Join-Path $BACKUP_DIR "product.json.$Commit.bak"
    if (Test-Path $dest) { return $dest }  # idempotent per commit
    [System.IO.File]::WriteAllText($dest, $ProductRaw, [System.Text.Encoding]::UTF8)
    return $dest
}

function Find-BackupForCommit {
    param([string]$Commit)
    $path = Join-Path $BACKUP_DIR "product.json.$Commit.bak"
    if (Test-Path $path) { return $path }
    return $null
}

function Find-LatestBackup {
    if (-not (Test-Path $BACKUP_DIR)) { return $null }
    return Get-ChildItem -Path $BACKUP_DIR -Filter 'product.json.*.bak' |
        Where-Object { $_.Name -notmatch '\.pre-restore\.bak$' } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1 -ExpandProperty FullName
}

# ── Targeted JSON update ──────────────────────────────────────────
# Regex replace rather than parse/reserialize — preserves all product.json
# formatting, property order, and values we never need to touch.

function Update-ProductJsonChecksum {
    param([string]$Json, [string]$Entry, [string]$NewChecksum)
    $keyEsc     = [regex]::Escape('"' + $Entry + '"')
    $pattern    = "($keyEsc\s*:\s*"")([A-Za-z0-9+/=]+)("")"
    $replacement = '${1}' + $NewChecksum + '${3}'
    $updated    = [regex]::Replace($Json, $pattern, $replacement)
    if ($updated -eq $Json) {
        throw "Regex found no match for '$Entry' in product.json — entry format unexpected"
    }
    return $updated
}

# ── Modes ─────────────────────────────────────────────────────────

function Invoke-Status {
    $appRoot = Find-AppRoot
    $meta    = Read-AppMeta -AppRoot $appRoot

    Write-Host "Version:  $($meta.Version)"
    Write-Host "Commit:   $($meta.Commit)"
    Write-Host "App root: $appRoot"

    $backup = Find-BackupForCommit -Commit $meta.Commit
    Write-Host "Backup:   $(if ($backup) { $backup } else { 'none' })"

    if (-not $meta.Checksums) {
        Write-Host "Checksums: no checksums block in product.json"
        return
    }

    foreach ($entry in $ALLOWLIST) {
        $prop = $meta.Checksums.PSObject.Properties[$entry]
        if (-not $prop) {
            Write-Host "${entry}: not tracked in this build"
            continue
        }
        $filePath = Join-Path $appRoot ('out\' + ($entry -replace '/', '\'))
        if (-not (Test-Path $filePath)) {
            Write-Host "${entry}: file absent"
            continue
        }
        $actual   = Get-VscChecksum -FilePath $filePath
        $expected = $prop.Value
        if ($actual -eq $expected) {
            Write-Host "${entry}: checksum current"
        } else {
            Write-Host "${entry}: checksum drift"
            Write-Host "  product.json: $expected"
            Write-Host "  actual file:  $actual"
        }
    }
}

function Invoke-Apply {
    Write-Host "Verifying substrate state..."
    Assert-SubstrateVerified

    $appRoot = Find-AppRoot
    $meta    = Read-AppMeta -AppRoot $appRoot

    if (-not $meta.Checksums) {
        Write-Host "No checksums block in product.json — nothing to reconcile."
        return
    }

    $backup = Write-ProductBackup -ProductPath $meta.ProductPath `
                                  -Commit $meta.Commit `
                                  -ProductRaw $meta.ProductRaw
    Write-Host "Backup: $backup"

    $json    = $meta.ProductRaw
    $updated = $false

    foreach ($entry in $ALLOWLIST) {
        $prop = $meta.Checksums.PSObject.Properties[$entry]
        if (-not $prop) {
            Write-Host "${entry}: not tracked — skip"
            continue
        }
        $filePath = Join-Path $appRoot ('out\' + ($entry -replace '/', '\'))
        if (-not (Test-Path $filePath)) {
            Write-Host "${entry}: file absent — skip"
            continue
        }

        Write-Host "Verifying Chthonic ownership of $(Split-Path $filePath -Leaf)..."
        Assert-ChthonicOwnership -FilePath $filePath

        $newChecksum = Get-VscChecksum -FilePath $filePath
        $oldChecksum = $prop.Value

        if ($newChecksum -eq $oldChecksum) {
            Write-Host "${entry}: already current"
            continue
        }

        $json    = Update-ProductJsonChecksum -Json $json -Entry $entry -NewChecksum $newChecksum
        $updated = $true
        Write-Host "${entry}: $oldChecksum → $newChecksum"
    }

    if ($updated) {
        [System.IO.File]::WriteAllText($meta.ProductPath, $json, [System.Text.Encoding]::UTF8)
        Write-Host "product.json written."
        Write-Host "Restart VS Code Insiders to clear the integrity warning."
    } else {
        Write-Host "No entries required update."
    }
}

function Invoke-Verify {
    $appRoot = Find-AppRoot
    $meta    = Read-AppMeta -AppRoot $appRoot
    $ok      = $true

    if (-not $meta.Checksums) {
        Write-Host "integrity-checksum-owned: no checksums block"
        $ok = $false
    } else {
        $anyTracked = $false
        foreach ($entry in $ALLOWLIST) {
            $prop = $meta.Checksums.PSObject.Properties[$entry]
            if (-not $prop) { continue }
            $filePath = Join-Path $appRoot ('out\' + ($entry -replace '/', '\'))
            if (-not (Test-Path $filePath)) { continue }
            $anyTracked = $true
            $actual     = Get-VscChecksum -FilePath $filePath
            $expected   = $prop.Value
            if ($actual -eq $expected) {
                Write-Host "integrity-checksum-owned: $entry ok"
            } else {
                Write-Host "integrity-checksum-owned: $entry drift"
                $ok = $false
            }
        }
        if (-not $anyTracked) {
            Write-Host "integrity-checksum-owned: no allowlisted entries tracked in this build"
        }
    }

    $backup = Find-BackupForCommit -Commit $meta.Commit
    if ($backup) {
        Write-Host "integrity-product-json-backup-present: ok"
    } else {
        Write-Host "integrity-product-json-backup-present: absent"
        $ok = $false
    }

    if ($ok) { Write-Host "Ok: true"; exit 0 }
    else     { Write-Host "Ok: false"; exit 1 }
}

function Invoke-Restore {
    $appRoot = Find-AppRoot
    $meta    = Read-AppMeta -AppRoot $appRoot

    $backup = Find-BackupForCommit -Commit $meta.Commit
    if (-not $backup) {
        $backup = Find-LatestBackup
        if (-not $backup) { throw "No backup found to restore from" }
        Write-Host "No per-commit backup found — using latest: $backup"
    }

    New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null
    $preRestore = Join-Path $BACKUP_DIR "product.json.$($meta.Commit).pre-restore.bak"
    [System.IO.File]::WriteAllText($preRestore, $meta.ProductRaw, [System.Text.Encoding]::UTF8)
    Write-Host "Pre-restore snapshot: $preRestore"

    Copy-Item -LiteralPath $backup -Destination $meta.ProductPath -Force
    Write-Host "Restored from $backup"
    Write-Host "Restart VS Code Insiders to activate."
}

# ── Dispatch ──────────────────────────────────────────────────────

if     ($Status)  { Invoke-Status }
elseif ($Apply)   { Invoke-Apply }
elseif ($Verify)  { Invoke-Verify }
elseif ($Restore) { Invoke-Restore }
else {
    Write-Host "Usage: insiders-integrity-reconcile.ps1 [-Status] [-Apply] [-Verify] [-Restore]"
    Write-Host ""
    Write-Host "  -Status    Show current checksum state for allowlisted files"
    Write-Host "  -Apply     Reconcile product.json after verified Chthonic substrate patch"
    Write-Host "  -Verify    Check checksums current and backup present (for couture:gate)"
    Write-Host "  -Restore   Restore product.json from per-commit or latest backup"
    exit 1
}
