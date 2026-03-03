# @SID: FORGE_SHELL_RECIPE_BOOK_V1
# Purpose: Recovered PowerShell recipe book from corpse-vault shell fragments.
# Source-Files: .vscode/profile.ps1, scripts/shell_capabilities.ps1, scripts/validate_shell_probe.ps1, scripts/ssot_crc_selector.ps1, scripts/validate_probe.ps1, scripts/ssot_registry_query_v2.ps1, scripts/ssot_tier_query.ps1, scripts/harvest_claudines.ps1, scripts/ssot_registry_query.ps1, scripts/ssot_outline_extractor.ps1, scripts/ssot_acronym_audit.ps1, dumpster-dive/intake/claude-ide-harden-2026-02-10/raw/patch-claude-insiders.ps1, dumpster-dive/intake/claude-ide-harden-2026-02-10/raw/launch_claude_code.ps1, scripts/check-solana-version.ps1, dumpster-dive/intake/claude-ide-harden-2026-02-10/raw/start_mcp_session.ps1, dumpster-dive/intake/claude-ide-harden-2026-02-10/raw/start_github_mcp.ps1, scripts/run_overnight_daemon.ps1, scripts/chthonic.ps1
# Pathway: shell fragments -> command extraction -> PowerShell recipe book
# Kept: Recipe names, provenance, and representative commands.
# Discarded: Deleted process glue and unsafe inline environment mutations.
$script:RecoveredShellRecipes = @(
    [pscustomobject]@{
        Name = 'profile'
        SourceFile = '.vscode/profile.ps1'
        Hash = '74d70e47c4256808'
        Commands = @('# GPU status check', 'Write-Host "   Run ''claudine-versions'' to verify toolchain" -ForegroundColor DarkGray')
    }
    [pscustomobject]@{
        Name = 'shell_capabilities'
        SourceFile = 'scripts/shell_capabilities.ps1'
        Hash = '034ae3ef00cff7fd'
        Commands = @('# ║ Purpose: Minimal, deterministic shell/environment probe (ABI-stable)      ║', '# ║ Flags/Modes: None (pure read-only probe)                                  ║')
    }
    [pscustomobject]@{
        Name = 'validate_shell_probe'
        SourceFile = 'scripts/validate_shell_probe.ps1'
        Hash = 'dd293475d65736ea'
        Commands = @('# ║ Purpose: Enforce ABI-stable probe invariants for shell_capabilities.ps1    ║')
    }
    [pscustomobject]@{
        Name = 'ssot_crc_selector'
        SourceFile = 'scripts/ssot_crc_selector.ps1'
        Hash = '9947cfda043497cb'
        Commands = @('# ║ Spectral Frequency: WHITE                                                 ║', '# ║ Architectural Role: SSOT                                                  ║', '# ║ Semantic ID: SCRIPT_SSOT_CRC_SELECTOR_V1                                   ║', '# ║ Purpose: Suggest Conceptual Resonance Core for task                        ║', '# ║ Exports: (none)                                                           ║')
    }
    [pscustomobject]@{
        Name = 'validate_probe'
        SourceFile = 'scripts/validate_probe.ps1'
        Hash = 'd4b51048595c0fb4'
        Commands = @('# ║ Purpose: Run ABI validation plus advisory probe checks                     ║')
    }
    [pscustomobject]@{
        Name = 'ssot_registry_query_v2'
        SourceFile = 'scripts/ssot_registry_query_v2.ps1'
        Hash = '0f146eaa424c3ac9'
        Commands = @('# ║ Spectral Frequency: WHITE                                                 ║', '# ║ Architectural Role: SSOT                                                  ║', '# ║ Semantic ID: SCRIPT_SSOT_REGISTRY_QUERY_V2_V1                              ║', '# ║ Purpose: Dynamically parse SSOT registries from copilot-instructions.md    ║', '# ║ Exports: (none)                                                           ║')
    }
    [pscustomobject]@{
        Name = 'ssot_tier_query'
        SourceFile = 'scripts/ssot_tier_query.ps1'
        Hash = '2a3d236302c010ee'
        Commands = @('# ║ Spectral Frequency: WHITE                                                 ║', '# ║ Architectural Role: SSOT                                                  ║', '# ║ Semantic ID: SCRIPT_SSOT_TIER_QUERY_V1                                     ║', '# ║ Purpose: Query GHAR-MHS tier hierarchy and entities                        ║', '# ║ Exports: (none)                                                           ║')
    }
    [pscustomobject]@{
        Name = 'harvest_claudines'
        SourceFile = 'scripts/harvest_claudines.ps1'
        Hash = '5c959b051cfc11e5'
        Commands = @('# ║ Spectral Frequency: WHITE                                                 ║', '# ║ Architectural Role: HARVEST                                               ║', '# ║ Semantic ID: SCRIPT_HARVEST_CLAUDINES_V1                                   ║', '# ║ Purpose: Harvest external Claudine scripts into intake folder             ║', '# ║ Exports: (none)                                                           ║')
    }
    [pscustomobject]@{
        Name = 'ssot_registry_query'
        SourceFile = 'scripts/ssot_registry_query.ps1'
        Hash = '9dbfb4621749c903'
        Commands = @('# ║ Spectral Frequency: WHITE                                                 ║', '# ║ Architectural Role: SSOT                                                  ║', '# ║ Semantic ID: SCRIPT_SSOT_REGISTRY_QUERY_V1                                 ║', '# ║ Purpose: Query AR/CR/SAI registries from SSOT                              ║', '# ║ Exports: (none)                                                           ║')
    }
    [pscustomobject]@{
        Name = 'ssot_outline_extractor'
        SourceFile = 'scripts/ssot_outline_extractor.ps1'
        Hash = 'a676305a77b31ae6'
        Commands = @('# ║ Spectral Frequency: WHITE                                                 ║', '# ║ Architectural Role: SSOT                                                  ║', '# ║ Semantic ID: SCRIPT_SSOT_OUTLINE_EXTRACTOR_V1                              ║', '# ║ Purpose: Extract SSOT outline and update structural index                 ║', '# ║ Exports: (none)                                                           ║')
    }
    [pscustomobject]@{
        Name = 'ssot_acronym_audit'
        SourceFile = 'scripts/ssot_acronym_audit.ps1'
        Hash = 'd17f1f080e1d8eac'
        Commands = @('# ║ Spectral Frequency: WHITE                                                 ║', '# ║ Architectural Role: SSOT                                                  ║', '# ║ Semantic ID: SCRIPT_SSOT_ACRONYM_AUDIT_V1                                  ║', '# ║ Purpose: Audit SSOT acronym consistency and line locations                ║', '# ║ Exports: (none)                                                           ║')
    }
    [pscustomobject]@{
        Name = 'patch-claude-insiders'
        SourceFile = 'dumpster-dive/intake/claude-ide-harden-2026-02-10/raw/patch-claude-insiders.ps1'
        Hash = 'c20bdc3ed68a4012'
        Commands = @('# ║ Spectral Frequency: WHITE                                                 ║', '# ║ Architectural Role: UTILITY                                               ║', '# ║ Semantic ID: SCRIPT_PATCH_CLAUDE_INSIDERS_V1                               ║', '# ║ Purpose: Patch Claude Code CLI to use code-insiders on Windows             ║', '# ║ Exports: (none)                                                           ║')
    }
    [pscustomobject]@{
        Name = 'launch_claude_code'
        SourceFile = 'dumpster-dive/intake/claude-ide-harden-2026-02-10/raw/launch_claude_code.ps1'
        Hash = '0b083603baba3733'
        Commands = @('# ║ Architectural Role: Claude Code/Desktop installation and launch manager   ║', '# ║ Purpose: Install/start Claude Code / Claude Desktop on Windows 11         ║', '# ║ Flags/Modes: -Force (skip running check), -WaitSeconds <int>              ║')
    }
    [pscustomobject]@{
        Name = 'check-solana-version'
        SourceFile = 'scripts/check-solana-version.ps1'
        Hash = '0bf0b913fc2e91b3'
        Commands = @('# ║ Spectral Frequency: WHITE                                                 ║', '# ║ Architectural Role: GOVERNANCE                                            ║', '# ║ Semantic ID: SCRIPT_CHECK_SOLANA_VERSION_V1                               ║', '# ║ Purpose: Enforce max-version-drift policy for local Solana CLI            ║', '# ║ Exports: (none)                                                           ║')
    }
    [pscustomobject]@{
        Name = 'start_mcp_session'
        SourceFile = 'dumpster-dive/intake/claude-ide-harden-2026-02-10/raw/start_mcp_session.ps1'
        Hash = '9da35b76f3134571'
        Commands = @('# ║ Spectral Frequency: orchestration/bootstrap                               ║', '# ║ Architectural Role: MCP server launcher with optional Claude integration  ║', '# ║ Semantic ID: SCRIPT_START_MCP_SESSION_V1                                  ║', '# ║ Purpose: Bootstrap MCP server session, optionally ensuring Claude is up   ║', '# ║ Exports: None (launcher script)                                           ║')
    }
    [pscustomobject]@{
        Name = 'start_github_mcp'
        SourceFile = 'dumpster-dive/intake/claude-ide-harden-2026-02-10/raw/start_github_mcp.ps1'
        Hash = 'b1dd530ebaf58cbb'
        Commands = @('# ║ Spectral Frequency: integration/mcp                                       ║', '# ║ Architectural Role: GitHub credential bridge for MCP server               ║', '# ║ Semantic ID: SCRIPT_START_GITHUB_MCP_V1                                   ║', '# ║ Purpose: Bridge gh CLI credentials to official GitHub MCP Server          ║', '# ║ Exports: None (launcher script, sets GITHUB_PERSONAL_ACCESS_TOKEN env)    ║')
    }
    [pscustomobject]@{
        Name = 'run_overnight_daemon'
        SourceFile = 'scripts/run_overnight_daemon.ps1'
        Hash = 'ecbf198838934d8d'
        Commands = @('# ║ Purpose: Launch overnight_daemon.ts via Bun with configurable parameters  ║')
    }
    [pscustomobject]@{
        Name = 'chthonic'
        SourceFile = 'scripts/chthonic.ps1'
        Hash = 'fa4a6e69f9a230ff'
        Commands = @('"azurecli"   {', '$v = az version --query ''"azure-cli"'' -o tsv 2>$null', 'if ($v) { return $v.Trim() }', 'return $null', '}')
    }
)

function Get-RecoveredShellRecipe {
    [CmdletBinding()]
    param([string]$Name)
    if ($Name) { return $script:RecoveredShellRecipes | Where-Object { $_.Name -like "*$Name*" } }
    return $script:RecoveredShellRecipes
}

function Show-RecoveredShellRecipe {
    [CmdletBinding()]
    param([string]$Name)
    Get-RecoveredShellRecipe -Name $Name | ForEach-Object {
        Write-Host "[$($_.Name)] $($_.SourceFile)"
        $_.Commands | ForEach-Object { Write-Host "  $_" }
    }
}
