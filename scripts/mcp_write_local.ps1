#!/usr/bin/env pwsh
# @SID: SCRIPT_MCP_WRITE_LOCAL_V1
# @Type: SHIM
# @Purpose: Thin delegate — forwards to claude_ide.ps1 write-mcp subcommand.
# Legacy callers preserved. Real logic lives in .deprecated/mcp_write_local.ps1.
& "$PSScriptRoot/claude_ide.ps1" write-mcp @args
