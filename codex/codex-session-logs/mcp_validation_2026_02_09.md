---
type: mcp-validation-report
created: 2026-02-09
scope: mcp smoke test (connectivity + basic read)
---

# MCP Validation Report (2026-02-09)

## Configuration Observed

- MCP config file: `.mcp.json`
- Configured servers:
  - `github` (HTTP) pointing at Copilot MCP endpoint

## Smoke Tests Performed

### github MCP

- `resources/list`: returned an empty list (OK; server can be reachable even without listing resources).
- `resourceTemplates/list`: returned 5 templates (OK):
  - `repo://{owner}/{repo}/contents{/path*}`
  - `repo://{owner}/{repo}/refs/heads/{branch}/contents{/path*}`
  - `repo://{owner}/{repo}/refs/pull/{prNumber}/head/contents{/path*}`
  - `repo://{owner}/{repo}/refs/tags/{tag}/contents{/path*}`
  - `repo://{owner}/{repo}/sha/{sha}/contents{/path*}`

- `resources/read` success:
  - Read `repo://poisontr33s/chthonic-archive/contents/AGENTS.md` (OK)
  - Read `repo://poisontr33s/chthonic-archive/refs/heads/main/contents/AGENTS.md` (OK)

- `resources/read` expected limitation:
  - Reading `repo://poisontr33s/chthonic-archive/contents/` failed with: `directories are not supported` (not a connectivity failure; this MCP only supports file reads for the `contents` template).

## Notes / Risks

- `.mcp.json` contains an Authorization bearer token in plaintext. Per workspace rules, auth settings are workspace-locked, so this report does not change it. If you want drift-resistance across VS Code Insiders updates, the stable fix is to move secrets into a dedicated API pool and keep `.mcp.json` referencing that indirection (when/if your MCP host supports it).

