# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: probe_toolchain_path.ps1
# ║ Module: Toolchain PATH probe
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: PROBE
# ║ Semantic ID: SCRIPT_PROBE_TOOLCHAIN_PATH_V1
# ║ Purpose: Probe toolchain paths and emit curated PATH outputs
# ║ Exports: (none)
# ║ Flags/Modes: -ExtraRoots, -OutRoot, -ApplyToSession, -WriteVscodeSnippet
# ║ Cross-References: dumpster-dive/intake/toolchain-probe/
# ╚════════════════════════════════════════════════════════════════════════════

[CmdletBinding()]
param(
  # Additional roots to probe (non-recursive heuristics; no full C:\ recurse).
  [string[]]$ExtraRoots = @(),

  # Write outputs under dumpster-dive intake.
  [string]$OutRoot = (Join-Path $PSScriptRoot '..\dumpster-dive\intake\toolchain-probe'),

  # Apply the computed PATH to the current PowerShell session.
  [switch]$ApplyToSession,

  # Emit a VS Code settings snippet (does not modify repo settings by default).
  [switch]$WriteVscodeSnippet
)

$ErrorActionPreference = 'Stop'

$STATE_DIR = Join-Path $env:USERPROFILE ".chthonic"
$CONFIG_FILE = Join-Path $STATE_DIR "config.json"

# Default fallback paths (Sync with chthonic.ps1)
$defaultPolyglotPaths = @(
    "$env:USERPROFILE\.bun\bin",
    "$env:USERPROFILE\.cargo\bin",
    "C:\Go\bin",
    "$env:USERPROFILE\go\bin",
    "$env:USERPROFILE\.local\bin",
    "C:\Ruby34-x64\bin",
    "C:\Ruby34-x64\msys64\ucrt64\bin",
    "C:\Ruby34-x64\msys64\usr\bin",
    "C:\Program Files\Git\cmd"
)

function Get-PolyglotConfig {
  if (Test-Path $CONFIG_FILE) {
    try {
      $cfg = Get-Content $CONFIG_FILE -Raw | ConvertFrom-Json
      if ($cfg.PolyglotPaths -and $cfg.PolyglotPaths.Count -gt 0) {
        return $cfg.PolyglotPaths
      }
    } catch {
      Write-Warning "Failed to parse config.json, using defaults."
    }
  }
  return $defaultPolyglotPaths
}

function New-Stamp {
  $d = Get-Date
  '{0:0000}{1:00}{2:00}_{3:00}{4:00}{5:00}' -f $d.Year, $d.Month, $d.Day, $d.Hour, $d.Minute, $d.Second
}

function Normalize-Dir([string]$p) {
  if ([string]::IsNullOrWhiteSpace($p)) { return $null }
  try {
    $rp = (Resolve-Path -LiteralPath $p -ErrorAction Stop).Path
    return $rp.TrimEnd('\\')
  } catch {
    return $null
  }
}

function Add-UniqueDir([System.Collections.Generic.List[string]]$list, [string]$dir) {
  $nd = Normalize-Dir $dir
  if (-not $nd) { return }
  if ($list.Contains($nd)) { return }
  $list.Add($nd) | Out-Null
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$stamp = New-Stamp
$outRootResolved = $null
try {
  $outRootResolved = (Resolve-Path -LiteralPath $OutRoot -ErrorAction Stop).Path
} catch {
  $outRootResolved = $OutRoot
}

if (-not (Test-Path -LiteralPath $outRootResolved)) {
  New-Item -ItemType Directory -Force -Path $outRootResolved | Out-Null
}

$logFile = Join-Path $outRootResolved "probe_path_$stamp.log"
$pathFile = Join-Path $outRootResolved "probed_path_$stamp.txt"
$vscodeFile = Join-Path $outRootResolved "vscode_settings_$stamp.json"

function Log([string]$msg) {
  $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
  "$ts $msg" | Out-File -Append -Encoding utf8 -FilePath $logFile
  Write-Host "$ts $msg" -ForegroundColor Gray
}

Log "Starting Toolchain PATH Probe..."
Log "Repo Root: $repoRoot"

# 1. Start with current PATH
$pathDirs = [System.Collections.Generic.List[string]]::new()
($env:Path -split ';') | ForEach-Object { Add-UniqueDir $pathDirs $_ }

# 2. Add Polyglot Paths (Config or Default)
Log "Loading polyglot paths..."
$polyglotPaths = Get-PolyglotConfig
foreach ($p in $polyglotPaths) {
    if (Test-Path $p) {
        Add-UniqueDir $pathDirs $p
        Log "  + Added: $p"
    } else {
        Log "  - Skipped (missing): $p"
    }
}

# 3. Add ExtraRoots if provided
foreach ($r in $ExtraRoots) {
  Add-UniqueDir $pathDirs $r
}

# 4. Standard Windows System Paths (Always ensure these exist)
$sysPaths = @(
    'C:\Windows\System32',
    'C:\Windows',
    'C:\Windows\System32\Wbem',
    'C:\Windows\System32\WindowsPowerShell\v1.0',
    'C:\Program Files\PowerShell\7'
)
foreach ($sp in $sysPaths) {
    Add-UniqueDir $pathDirs $sp
}

Log "Constructed PATH with $($pathDirs.Count) entries."

# Construct new PATH string
$newPath = $pathDirs -join ';'

# Output to file
$newPath | Out-File -Encoding utf8 -FilePath $pathFile
Log "Wrote probed PATH to: $pathFile"

# VS Code Snippet
if ($WriteVscodeSnippet) {
  $jsonObj = @{
    "terminal.integrated.env.windows" = @{
      "PATH" = $newPath
    }
  }
  $jsonObj | ConvertTo-Json -Depth 5 | Out-File -Encoding utf8 -FilePath $vscodeFile
  Log "Wrote VS Code snippet to: $vscodeFile"
}

# Apply to session
if ($ApplyToSession) {
  $env:Path = $newPath
  Log "Applied new PATH to current session."
  
  # Quick verification
  $tools = @('go', 'ruby', 'bun', 'uv', 'cargo')
  foreach ($t in $tools) {
    if (Get-Command $t -ErrorAction SilentlyContinue) {
        Log "  [OK] Found $t"
    } else {
        Log "  [WARN] Could not find $t"
    }
  }
}

Log "Probe complete."