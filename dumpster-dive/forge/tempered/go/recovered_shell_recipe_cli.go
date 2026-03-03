package main

// @SID: FORGE_SHELL_RECIPE_CLI_V1
// Purpose: Cross-language Go CLI distilled from shell recipe fragments.
import (
    "flag"
    "fmt"
    "strings"
)

type recipe struct {
    Name string
    Source string
    Commands []string
}

var recipes = []recipe{
    {Name: "profile", Source: ".vscode/profile.ps1", Commands: []string{"# GPU status check", "Write-Host \"   Run 'claudine-versions' to verify toolchain\" -ForegroundColor DarkGray"}},
    {Name: "shell_capabilities", Source: "scripts/shell_capabilities.ps1", Commands: []string{"# \u2551 Purpose: Minimal, deterministic shell/environment probe (ABI-stable)      \u2551", "# \u2551 Flags/Modes: None (pure read-only probe)                                  \u2551"}},
    {Name: "validate_shell_probe", Source: "scripts/validate_shell_probe.ps1", Commands: []string{"# \u2551 Purpose: Enforce ABI-stable probe invariants for shell_capabilities.ps1    \u2551"}},
    {Name: "ssot_crc_selector", Source: "scripts/ssot_crc_selector.ps1", Commands: []string{"# \u2551 Spectral Frequency: WHITE                                                 \u2551", "# \u2551 Architectural Role: SSOT                                                  \u2551", "# \u2551 Semantic ID: SCRIPT_SSOT_CRC_SELECTOR_V1                                   \u2551", "# \u2551 Purpose: Suggest Conceptual Resonance Core for task                        \u2551", "# \u2551 Exports: (none)                                                           \u2551"}},
    {Name: "validate_probe", Source: "scripts/validate_probe.ps1", Commands: []string{"# \u2551 Purpose: Run ABI validation plus advisory probe checks                     \u2551"}},
    {Name: "ssot_registry_query_v2", Source: "scripts/ssot_registry_query_v2.ps1", Commands: []string{"# \u2551 Spectral Frequency: WHITE                                                 \u2551", "# \u2551 Architectural Role: SSOT                                                  \u2551", "# \u2551 Semantic ID: SCRIPT_SSOT_REGISTRY_QUERY_V2_V1                              \u2551", "# \u2551 Purpose: Dynamically parse SSOT registries from copilot-instructions.md    \u2551", "# \u2551 Exports: (none)                                                           \u2551"}},
    {Name: "ssot_tier_query", Source: "scripts/ssot_tier_query.ps1", Commands: []string{"# \u2551 Spectral Frequency: WHITE                                                 \u2551", "# \u2551 Architectural Role: SSOT                                                  \u2551", "# \u2551 Semantic ID: SCRIPT_SSOT_TIER_QUERY_V1                                     \u2551", "# \u2551 Purpose: Query GHAR-MHS tier hierarchy and entities                        \u2551", "# \u2551 Exports: (none)                                                           \u2551"}},
    {Name: "harvest_claudines", Source: "scripts/harvest_claudines.ps1", Commands: []string{"# \u2551 Spectral Frequency: WHITE                                                 \u2551", "# \u2551 Architectural Role: HARVEST                                               \u2551", "# \u2551 Semantic ID: SCRIPT_HARVEST_CLAUDINES_V1                                   \u2551", "# \u2551 Purpose: Harvest external Claudine scripts into intake folder             \u2551", "# \u2551 Exports: (none)                                                           \u2551"}},
    {Name: "ssot_registry_query", Source: "scripts/ssot_registry_query.ps1", Commands: []string{"# \u2551 Spectral Frequency: WHITE                                                 \u2551", "# \u2551 Architectural Role: SSOT                                                  \u2551", "# \u2551 Semantic ID: SCRIPT_SSOT_REGISTRY_QUERY_V1                                 \u2551", "# \u2551 Purpose: Query AR/CR/SAI registries from SSOT                              \u2551", "# \u2551 Exports: (none)                                                           \u2551"}},
    {Name: "ssot_outline_extractor", Source: "scripts/ssot_outline_extractor.ps1", Commands: []string{"# \u2551 Spectral Frequency: WHITE                                                 \u2551", "# \u2551 Architectural Role: SSOT                                                  \u2551", "# \u2551 Semantic ID: SCRIPT_SSOT_OUTLINE_EXTRACTOR_V1                              \u2551", "# \u2551 Purpose: Extract SSOT outline and update structural index                 \u2551", "# \u2551 Exports: (none)                                                           \u2551"}},
    {Name: "ssot_acronym_audit", Source: "scripts/ssot_acronym_audit.ps1", Commands: []string{"# \u2551 Spectral Frequency: WHITE                                                 \u2551", "# \u2551 Architectural Role: SSOT                                                  \u2551", "# \u2551 Semantic ID: SCRIPT_SSOT_ACRONYM_AUDIT_V1                                  \u2551", "# \u2551 Purpose: Audit SSOT acronym consistency and line locations                \u2551", "# \u2551 Exports: (none)                                                           \u2551"}},
    {Name: "patch-claude-insiders", Source: "dumpster-dive/intake/claude-ide-harden-2026-02-10/raw/patch-claude-insiders.ps1", Commands: []string{"# \u2551 Spectral Frequency: WHITE                                                 \u2551", "# \u2551 Architectural Role: UTILITY                                               \u2551", "# \u2551 Semantic ID: SCRIPT_PATCH_CLAUDE_INSIDERS_V1                               \u2551", "# \u2551 Purpose: Patch Claude Code CLI to use code-insiders on Windows             \u2551", "# \u2551 Exports: (none)                                                           \u2551"}},
    {Name: "launch_claude_code", Source: "dumpster-dive/intake/claude-ide-harden-2026-02-10/raw/launch_claude_code.ps1", Commands: []string{"# \u2551 Architectural Role: Claude Code/Desktop installation and launch manager   \u2551", "# \u2551 Purpose: Install/start Claude Code / Claude Desktop on Windows 11         \u2551", "# \u2551 Flags/Modes: -Force (skip running check), -WaitSeconds <int>              \u2551"}},
    {Name: "check-solana-version", Source: "scripts/check-solana-version.ps1", Commands: []string{"# \u2551 Spectral Frequency: WHITE                                                 \u2551", "# \u2551 Architectural Role: GOVERNANCE                                            \u2551", "# \u2551 Semantic ID: SCRIPT_CHECK_SOLANA_VERSION_V1                               \u2551", "# \u2551 Purpose: Enforce max-version-drift policy for local Solana CLI            \u2551", "# \u2551 Exports: (none)                                                           \u2551"}},
    {Name: "start_mcp_session", Source: "dumpster-dive/intake/claude-ide-harden-2026-02-10/raw/start_mcp_session.ps1", Commands: []string{"# \u2551 Spectral Frequency: orchestration/bootstrap                               \u2551", "# \u2551 Architectural Role: MCP server launcher with optional Claude integration  \u2551", "# \u2551 Semantic ID: SCRIPT_START_MCP_SESSION_V1                                  \u2551", "# \u2551 Purpose: Bootstrap MCP server session, optionally ensuring Claude is up   \u2551", "# \u2551 Exports: None (launcher script)                                           \u2551"}},
    {Name: "start_github_mcp", Source: "dumpster-dive/intake/claude-ide-harden-2026-02-10/raw/start_github_mcp.ps1", Commands: []string{"# \u2551 Spectral Frequency: integration/mcp                                       \u2551", "# \u2551 Architectural Role: GitHub credential bridge for MCP server               \u2551", "# \u2551 Semantic ID: SCRIPT_START_GITHUB_MCP_V1                                   \u2551", "# \u2551 Purpose: Bridge gh CLI credentials to official GitHub MCP Server          \u2551", "# \u2551 Exports: None (launcher script, sets GITHUB_PERSONAL_ACCESS_TOKEN env)    \u2551"}},
    {Name: "run_overnight_daemon", Source: "scripts/run_overnight_daemon.ps1", Commands: []string{"# \u2551 Purpose: Launch overnight_daemon.ts via Bun with configurable parameters  \u2551"}},
    {Name: "chthonic", Source: "scripts/chthonic.ps1", Commands: []string{"\"azurecli\"   {", "$v = az version --query '\"azure-cli\"' -o tsv 2>$null", "if ($v) { return $v.Trim() }", "return $null", "}"}},
}

func main() {
    filter := flag.String("filter", "", "recipe name filter")
    flag.Parse()
    for _, recipe := range recipes {
        if *filter != "" && !strings.Contains(strings.ToLower(recipe.Name), strings.ToLower(*filter)) { continue }
        fmt.Printf("[%s] %s\n", recipe.Name, recipe.Source)
        for _, command := range recipe.Commands { fmt.Printf("  - %s\n", command) }
    }
}
