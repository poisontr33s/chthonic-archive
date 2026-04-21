#!/usr/bin/env pwsh
#
# @SID: SCRIPT_MAILBOX_HANDOFF_V1
# @Type: UTILITY
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: [Parameter(Mandatory=$true)][ValidateSet("claude","codex","gemini")][string]$Tar
#

param(
  [Parameter(Mandatory=$true)][ValidateSet("claude","codex","gemini")][string]$Target,
  [string]$Source,
  [string]$Inbox,
  [switch]$SendLatest,
  [switch]$SendAll,
  [double]$RequireScoreMin = 0.0,
  [string]$AuditJson = "codex/mailbox/HANDOFF_AUDIT_LATEST.json",
  [switch]$RunAudit
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Resolve-TargetDir {
  param([string]$Lane, [string]$Root)
  if ($Lane -eq "claude") { return (Join-Path $Root "claude/mailbox") }
  if ($Lane -eq "codex")  { return (Join-Path $Root "codex/mailbox") }
  if ($Lane -eq "gemini") { return (Join-Path $Root "gemini/mailbox") }
  throw "Unknown target lane: $Lane"
}

function To-RepoRelative {
  param([string]$PathValue, [string]$Root)
  $resolvedPath = (Resolve-Path -Path $PathValue).Path
  $resolvedRoot = (Resolve-Path -Path $Root).Path
  if ($resolvedPath.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    $trimmed = $resolvedPath.Substring($resolvedRoot.Length).TrimStart('\', '/')
    return ($trimmed -replace "\\", "/")
  }
  return ($resolvedPath -replace "\\", "/")
}

function Validate-HandoffSchema {
  param([string]$FilePath)
  if (-not (Test-Path $FilePath)) { throw "File not found for schema validation: $FilePath" }
  $text = Get-Content $FilePath -Raw
  $errors = @()
  # YAML frontmatter presence
  if ($text -notmatch '(?s)^---\s*\r?\n.*?\r?\n---') {
    $errors += "Missing YAML frontmatter block (--- delimiters)"
  }
  # Required frontmatter keys
  foreach ($key in @('type', 'from', 'to', 'created', 'priority', 'scope')) {
    if ($text -notmatch "(?m)^${key}\s*:") {
      $errors += "Missing required frontmatter field: $key"
    }
  }
  # Required sections (loose match)
  foreach ($section in @('Actions Taken', 'Files Changed', 'How to[Vv]erify', 'Next Actions')) {
    if ($text -notmatch "(?m)^#{1,6}\s+$section") {
      $errors += "Missing required section: $section"
    }
  }
  return $errors
}


  param([string]$AuditPath)
  if (-not (Test-Path $AuditPath)) {
    throw "Audit JSON not found: $AuditPath"
  }
  $payload = Get-Content -Path $AuditPath -Raw | ConvertFrom-Json
  $map = @{}
  foreach ($handoff in @($payload.handoffs)) {
    $path = [string]$handoff.path
    if (-not $path) { continue }
    $map[$path] = [double]$handoff.score_10
  }
  return $map
}

function Filter-HandoffsByScore {
  param(
    [array]$Items,
    [hashtable]$ScoreMap,
    [double]$MinScore,
    [string]$RepoRootPath
  )
  $eligible = @()
  foreach ($item in $Items) {
    $relative = To-RepoRelative -PathValue $item.FullName -Root $RepoRootPath
    if (-not $ScoreMap.ContainsKey($relative)) { continue }
    $score = [double]$ScoreMap[$relative]
    if ($score -ge $MinScore) {
      $eligible += $item
    }
  }
  return $eligible
}

$targetDir = Resolve-TargetDir -Lane $Target -Root $repoRoot

New-Item -ItemType Directory -Path $targetDir -Force | Out-Null

if ($SendLatest -or $SendAll) {
  if (-not $Inbox) { throw "Inbox path required for SendLatest/SendAll." }
  if (-not (Test-Path $Inbox)) { throw "Inbox not found: $Inbox" }

  # Handoff-first semantics: prefer SESSION_HANDOFF files over generic markdown.
  $items = Get-ChildItem $Inbox -File -Filter SESSION_HANDOFF_*.md | Sort-Object LastWriteTime -Descending
  if (-not $items) {
    Write-Host "No SESSION_HANDOFF_*.md found in $Inbox; falling back to *.md." -ForegroundColor Yellow
    $items = Get-ChildItem $Inbox -File -Filter *.md | Sort-Object LastWriteTime -Descending
  }
  if (-not $items) { throw "No .md files in inbox: $Inbox" }

  if ($RequireScoreMin -gt 0.0) {
    if ($RunAudit) {
      & uv run scripts/handoff_audit.py --emit-mailbox | Out-Host
      if (-not $?) { throw "Failed to run handoff audit." }
    }
    $scoreMap = Get-HandoffScoreMap -AuditPath $AuditJson
    $eligible = Filter-HandoffsByScore -Items $items -ScoreMap $scoreMap -MinScore $RequireScoreMin -RepoRootPath $repoRoot
    if (-not $eligible) {
      throw "No handoffs in $Inbox met RequireScoreMin=$RequireScoreMin based on $AuditJson"
    }
    $items = $eligible
  }

  if ($SendLatest) {
    $items = @($items | Select-Object -First 1)
  }

  foreach ($item in $items) {
    # JSON schema validation before copy
    $schemaErrors = Validate-HandoffSchema -FilePath $item.FullName
    if ($schemaErrors.Count -gt 0) {
      Write-Warning "[schema] Skipping $($item.Name) — validation errors:"
      foreach ($err in $schemaErrors) { Write-Warning "  $err" }
      continue
    }
    $dest = Join-Path $targetDir $item.Name
    Copy-Item -Path $item.FullName -Destination $dest -Force
    Write-Host "Mailbox sent -> $dest"
  }
  exit 0
}

if (-not $Source) {
  throw "Source file required unless using SendLatest/SendAll."
}

if (-not (Test-Path $Source)) {
  throw "Source file not found: $Source"
}

$resolvedSource = Resolve-Path -Path $Source

if ($RequireScoreMin -gt 0.0) {
  if ($RunAudit) {
    & uv run scripts/handoff_audit.py --emit-mailbox | Out-Host
    if (-not $?) { throw "Failed to run handoff audit." }
  }
  $scoreMap = Get-HandoffScoreMap -AuditPath $AuditJson
  $relative = To-RepoRelative -PathValue $resolvedSource -Root $repoRoot
  if ($scoreMap.ContainsKey($relative)) {
    $score = [double]$scoreMap[$relative]
    if ($score -lt $RequireScoreMin) {
      throw "Source handoff score $score is below RequireScoreMin=${RequireScoreMin}: $relative"
    }
  } else {
    throw "Source file not present in audit handoff set: $relative"
  }
}

# Single source route — validate schema before copy
$schemaErrors = Validate-HandoffSchema -FilePath $resolvedSource
if ($schemaErrors.Count -gt 0) {
  $schemaErrors | ForEach-Object { Write-Warning "[schema] $_" }
  throw "Source handoff failed schema validation: $Source"
}

$dest = Join-Path $targetDir (Split-Path $Source -Leaf)
Copy-Item -Path $resolvedSource -Destination $dest -Force
Write-Host "Mailbox sent -> $dest"
