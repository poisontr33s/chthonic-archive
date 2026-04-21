#!/usr/bin/env pwsh
# @SID: SCRIPT_CLAUDE_INSIDERS_SELFHEAL_V1
# @Type: SHIM
# @Purpose: Thin delegate — forwards to claude_ide.ps1 heal subcommand.
# Legacy callers preserved. Real logic lives in .deprecated/claude_insiders_selfheal.ps1.
& "$PSScriptRoot/claude_ide.ps1" heal @args
