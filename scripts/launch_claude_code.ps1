<#
 scripts/launch_claude_code.ps1
 Purpose: Install/start Claude Code / Claude Desktop on Windows 11.
 Usage: pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\launch_claude_code.ps1 [-Force] [-WaitSeconds 30]
#>

param(
  [switch]$Force,
  [int]$WaitSeconds = 30
)

function Log($m){ Write-Host "[launch_claude_code] $m" }

# Check for winget
$winget = (Get-Command winget -ErrorAction SilentlyContinue) -ne $null

# Helper: detect running process variants
function ClaudeRunning {
  $names = @("claude","Claude","claude-code","claudeCode")
  foreach ($n in $names) {
    if (Get-Process -Name $n -ErrorAction SilentlyContinue) { return $true }
  }
  return $false
}

if (-not $Force -and (ClaudeRunning)) {
  Log "Claude appears to be running."
  exit 0
}

if ($winget) {
  Log "Attempting winget install of Claude..."
  # Use exact id if package available (community repo). Accepts interactive prompts.
  winget install -e --id Anthropic.Claude -h || Log "winget install returned non-zero."
}

if (-not (ClaudeRunning)) {
  Log "Winget did not detect a running Claude. Attempting manual download fallback..."
  # Use official landing page or direct link if you have it. We use landing page to let user pick installer.
  $landing = "https://code.claude.com/docs/en/overview"
  $tmp = Join-Path $env:TEMP "claude_installer_hint.url"
  Set-Content -Path $tmp -Value $landing -Encoding UTF8
  Log "Opening Claude Code docs/landing page in browser. Please download & install if needed: $landing"
  Start-Process $landing
  Log "Waiting $WaitSeconds seconds for manual install & sign-in..."
  for ($i=0; $i -lt $WaitSeconds; $i++) {
    Start-Sleep -Seconds 1
    if (ClaudeRunning) { Log "Claude running."; exit 0 }
  }
  if (-not (ClaudeRunning)) {
    Log "Claude not detected after wait. Please install and sign in manually, then re-run the script."
    exit 2
  }
}

# If we get here, Claude is running
Log "Claude detected and running."
exit 0
