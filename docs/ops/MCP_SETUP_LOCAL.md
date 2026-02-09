---
type: ops
status: active
created: 2026-02-09
---

# MCP Local Setup (Tokens, Scopes, and Known Limits)

This repo uses MCP for tool access. MCP auth should be stable across VS Code Insiders updates by keeping secrets out of tracked files.

## Where To Put Tokens (VS Code on Windows)

- VS Code extension logins (GitHub, Copilot, etc.) are typically stored in VS Code **Secret Storage** (backed by Windows Credential Manager).
- MCP server auth in this repo is currently configured via a local `.mcp.json` file at the repo root.

Important: `.mcp.json` is not intended to be committed.

## Local `.mcp.json`

Create a local `.mcp.json` in the repo root (this file is ignored by default due to the repo's whitelist `.gitignore`).

Example:
```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer <YOUR_TOKEN_HERE>"
      }
    }
  }
}
```

Restart VS Code after editing so the host reloads MCP config.

## Scopes / Permissions

Increasing "scope" is done by minting a token with broader permissions (or switching auth method).

Notes:
- This affects *authorization* (what repos/contents you can access).
- It does not change MCP server feature support (for example, whether directory listing is supported).

### GitHub Token Guidance

Prefer least privilege:
- Fine-grained PAT: allow read access to the specific repo(s) you need.
- Classic PAT: broad; avoid unless you need it.

## Known Limits (Not Fixable by Token Scope)

- The GitHub MCP endpoint used here supports reading file contents via `repo://.../contents/<path>`.
- Directory reads such as `repo://.../contents/` can fail with `directories are not supported`.
  This is a server/endpoint limitation, not a token scope issue.

