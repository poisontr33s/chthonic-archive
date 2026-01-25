# Sentry MCP in VS Code (Local stdio)

This repo wires Sentry into VS Code via a **local MCP server** (stdio) for explicit context control.

## Wiring (SSOT)

| Item | Location | Purpose |
|---|---|---|
| VS Code MCP config | [.vscode/mcp.json](../../.vscode/mcp.json) | Registers the `sentry` MCP server (stdio via `bun x`). |
| Local runner | [scripts/run_sentry_mcp.ps1](../../scripts/run_sentry_mcp.ps1) | Runs the Sentry MCP server from a terminal to validate auth/network before involving Copilot. |

## Required environment

| Variable | Required | Notes |
|---|---:|---|
| `SENTRY_ACCESS_TOKEN` | yes | Create in Sentry → Settings → Developer Settings → Auth Tokens. Suggested scopes: `org:read`, `project:read`, `event:read`, `issue:read`. |
| `SENTRY_ORG` | no | Org slug (helps scope queries depending on server behavior). |
| `SENTRY_PROJECTS` | no | Comma-separated project slugs (optional narrowing). |

## Verify MCP server works (terminal first)

Run (PowerShell):
- `pwsh -NoProfile -File ./scripts/run_sentry_mcp.ps1`

Expected:
- Server starts without auth errors.

If it fails here, it is **not** a Copilot problem (token scopes, org slug, network/proxy are the usual causes).

## Verify whether Copilot Chat consumes MCP (VS Code)

1) Restart VS Code.
2) Open Copilot Chat.
3) Ask: “List available MCP tools.”

Interpretation:

| Result | Meaning |
|---|---|
| Sentry tools appear | Copilot Chat in this VS Code build/channel is consuming MCP successfully. |
| No MCP tools appear | VS Code may be hosting MCP but Copilot Chat in this build/channel isn’t wired to consume MCP yet (feature-flag / rollout / policy). |

## Notes
- Sentry MCP auth is based on **Sentry** credentials (`SENTRY_ACCESS_TOKEN`), not GitHub Copilot subscription state.
- This setup keeps Sentry MCP reusable even if Copilot Chat MCP consumption is unavailable in the current channel.
