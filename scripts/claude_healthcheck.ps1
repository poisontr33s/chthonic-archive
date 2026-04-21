#!/usr/bin/env pwsh
# @SID: SCRIPT_CLAUDE_HEALTHCHECK_V1
# @Type: SHIM
# @Purpose: Thin delegate — forwards to claude_ide.ps1 health subcommand.
# Legacy callers preserved. Real logic lives in .deprecated/claude_healthcheck.ps1.
& "$PSScriptRoot/claude_ide.ps1" health @args
