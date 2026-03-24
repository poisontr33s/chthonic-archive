// @SID: FORGE_SHELL_RECIPE_CLI_PROMOTED_V1
// Purpose: Active-lane Go CLI promoted from tempered shell recipe artifact.
// Source-Files: dumpster-dive/forge/tempered/go/recovered_shell_recipe_cli.go
// Pathway: tempered/go -> scripts promotion lane
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strings"
)

type recipe struct {
	Name     string   `json:"name"`
	Source   string   `json:"source"`
	Commands []string `json:"commands"`
}

var recipes = []recipe{
	{
		Name:   "profile",
		Source: ".vscode/profile.ps1",
		Commands: []string{
			"GPU status check",
			"Run claudine-versions to verify toolchain",
		},
	},
	{
		Name:   "shell_capabilities",
		Source: "scripts/shell_capabilities.ps1",
		Commands: []string{
			"Minimal deterministic shell/environment probe",
			"Flags/Modes: None (read-only)",
		},
	},
	{
		Name:   "validate_shell_probe",
		Source: "scripts/validate_shell_probe.ps1",
		Commands: []string{
			"Enforce ABI-stable probe invariants",
		},
	},
	{
		Name:   "ssot_crc_selector",
		Source: "scripts/ssot_crc_selector.ps1",
		Commands: []string{
			"Suggest conceptual resonance core for task",
		},
	},
	{
		Name:   "ssot_registry_query_v2",
		Source: "scripts/ssot_registry_query_v2.ps1",
		Commands: []string{
			"Dynamically parse SSOT registries",
		},
	},
	{
		Name:   "harvest_claudines",
		Source: "scripts/harvest_claudines.ps1",
		Commands: []string{
			"Harvest external scripts into intake folder",
		},
	},
	{
		Name:   "check-solana-version",
		Source: "scripts/check-solana-version.ps1",
		Commands: []string{
			"Enforce max-version-drift policy",
		},
	},
	{
		Name:   "run_overnight_daemon",
		Source: "scripts/run_overnight_daemon.ps1",
		Commands: []string{
			"Launch overnight_daemon.ts via Bun",
		},
	},
}

func filterRecipes(needle string) []recipe {
	if needle == "" {
		return recipes
	}
	out := make([]recipe, 0, len(recipes))
	lowered := strings.ToLower(needle)
	for _, r := range recipes {
		if strings.Contains(strings.ToLower(r.Name), lowered) || strings.Contains(strings.ToLower(r.Source), lowered) {
			out = append(out, r)
		}
	}
	return out
}

func main() {
	filter := flag.String("filter", "", "filter by recipe name/source")
	asJSON := flag.Bool("json", false, "emit JSON")
	flag.Parse()

	selected := filterRecipes(*filter)
	if *asJSON {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		if err := enc.Encode(selected); err != nil {
			fmt.Fprintf(os.Stderr, "encode error: %v\n", err)
			os.Exit(1)
		}
		return
	}

	for _, r := range selected {
		fmt.Printf("[%s] %s\n", r.Name, r.Source)
		for _, cmd := range r.Commands {
			fmt.Printf("  - %s\n", cmd)
		}
	}
}
