---
description: Re-apply the VS Code Insiders + MCP self-heal (patch CLI, refresh .mcp.json, ensure plugins).
argument-hint: [--full]
allowed-tools: [Bash]
---

# Self-Heal (Insiders)

Run the repo's idempotent self-heal. This is designed to survive daily VS Code Insiders updates.

## Behavior

- If `$ARGUMENTS` contains `--full`, run the full self-heal (includes marketplace update).
- Otherwise run the fast self-heal.

## Command

Use PowerShell (repo policy):

```text
pwsh -NoProfile -File scripts/claude_insiders_selfheal.ps1
```

Full:

```text
pwsh -NoProfile -File scripts/claude_insiders_selfheal.ps1 -Full
```

