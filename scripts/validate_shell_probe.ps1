# scripts/validate_shell_probe.ps1
# Enforces ABI-stable probe invariants for scripts\shell_capabilities.ps1
# Zero dependencies. Read-only.

param(
  [string]$ProbePath = "scripts\shell_capabilities.ps1",
  [string]$ExpectedSha256 = "6D6782ED8FFC4BF434D2A7108A0F3BACF13C3B40CC5C8F00F53CB789A96D9DF8"
)

$ErrorActionPreference = "Stop"

# 1) File exists
if (-not (Test-Path $ProbePath)) {
  Write-Error "Probe missing: $ProbePath"
  exit 2
}

# 2) Hash matches
$hash = (Get-FileHash $ProbePath -Algorithm SHA256).Hash
if ($hash -ne $ExpectedSha256) {
  Write-Error "Hash mismatch. Found: $hash Expected: $ExpectedSha256"
  exit 3
}

# 3) No logic keywords in non-comment lines
$keywords = '\b(if|else|elseif|switch|try|catch|throw|while|for|return|break|continue)\b'
$nonComment = Get-Content $ProbePath | Where-Object { $_ -notmatch '^\s*#' }

if ($nonComment -match $keywords) {
  Write-Error "Logic keyword detected in non-comment code. ABI invariant violated."
  exit 4
}

Write-Host "OK: Probe exists, hash matches, no-logic invariant satisfied."
exit 0
