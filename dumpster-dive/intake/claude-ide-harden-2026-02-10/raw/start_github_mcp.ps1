#!/usr/bin/env pwsh

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: start_github_mcp.ps1
# ║ Module: GitHub MCP Server Launcher
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: integration/mcp
# ║ Architectural Role: GitHub credential bridge for MCP server
# ║ Semantic ID: SCRIPT_START_GITHUB_MCP_V1
# ║ Purpose: Bridge gh CLI credentials to official GitHub MCP Server
# ║ Exports: None (launcher script, sets GITHUB_PERSONAL_ACCESS_TOKEN env)
# ║ Flags/Modes: None
# ║ Cross-References: @modelcontextprotocol/server-github
# ╚════════════════════════════════════════════════════════════════════════════
# Bridging 'gh' CLI credentials to the GitHub MCP Server

$ghToken = gh auth token
if (-not $ghToken) {
    Write-Error "Could not retrieve GitHub token. Please run 'gh auth login' first."
    exit 1
}

# Set environment variable for the server
$env:GITHUB_PERSONAL_ACCESS_TOKEN = $ghToken

# Run the official GitHub MCP server via bun
# Note: Using 'bun x' ensures we use the latest version without manual installation
bun x @modelcontextprotocol/server-github

