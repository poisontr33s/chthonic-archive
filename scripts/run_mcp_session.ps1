<#
 scripts/run_mcp_session.ps1
 Usage:
 pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_mcp_session.ps1 [-EnsureClaude] [-McpCmd "bun run mcp/server.ts"]
#>

param(
  [switch]$EnsureClaude,
  [string]$McpCmd = "bun run mcp/server.ts"
)

function Log($s){ Write-Host "[run_mcp_session] $s" }

if ($EnsureClaude) {
  Log "Ensuring Claude Code / Desktop is installed & running..."
  pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\launch_claude_code.ps1
  if ($LASTEXITCODE -ne 0) { throw "Claude ensure failed (exit $LASTEXITCODE)" }
  Log "Claude up."
}

# Start MCP server in background
Log "Starting MCP server: $McpCmd"
$startInfo = @{
  FilePath = "powershell"
  ArgumentList = "-NoProfile","-Command",$McpCmd
  WindowStyle = "Hidden"
}

# spawn as a job (so it continues after this script exits)
Start-Job -ScriptBlock { param($cmd) powershell -NoProfile -Command $cmd } -ArgumentList $McpCmd | Out-Null
Start-Sleep -Seconds 2

# Optional: list processes and show status
Log "Listing processes of interest..."
Get-Process -Name "Claude" -ErrorAction SilentlyContinue | Select-Object Name,Id,CPU | Format-Table -AutoSize
Write-Output "MCP server should be running as a process started by Start-Job. Use bun ps / check logs if needed."

Log "Session bootstrap complete. Add local server manifest in Claude Code (see claude_code_mcp_hint.json)."
