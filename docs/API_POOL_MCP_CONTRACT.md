# API Pool + MCP Contract

This repo uses one local token source:

```text
~/.chthonic/api_pool.json
```

Do not ask the user to regenerate, refresh, flip, rotate, or paste tokens just because an IDE, shell, MCP JSON file, or current process environment is missing them. First check the pool and load from it.

## Required Order

1. Diagnose without secrets:

   ```powershell
   .\scripts\api_pool.ps1 -Doctor
   ```

2. Run the local mock before any live/provider use:

   ```powershell
   .\scripts\api_pool.ps1 -Mock
   pwsh -NoProfile -File scripts/mcp_write_local.ps1 -Mock
   ```

   Mock mode validates local pool shape, expected MCP token lanes, and generated MCP server wiring. It does not call providers and does not write `.mcp.json`.

3. Load the pool into the current process when a command needs env vars:

   ```powershell
   .\scripts\api_pool.ps1 -Load
   ```

4. Verify known providers only when live auth must be proven:

   ```powershell
   .\scripts\api_pool.ps1 -VerifyProviders
   ```

5. Regenerate MCP JSON from the pool after any IDE or JSON update:

   ```powershell
   pwsh -NoProfile -File scripts/mcp_write_local.ps1 -GitHubMode copilot
   ```

6. List MCP servers without printing secrets:

   ```powershell
   pwsh -NoProfile -File scripts/mcp_write_local.ps1 -List
   ```

## Token Policy

- The API pool is the durable source of truth.
- Token renewal is manual only when a token is actually expired, revoked, or intentionally replaced.
- Scripts must not mint, refresh, rotate, or regenerate API tokens.
- New provider keys belong in `~/.chthonic/api_pool.json` under `env`.
- New MCP/API consumers must read from the pool or from env loaded by `api_pool.ps1`.
- Never commit token values.
- Prefer mock/local validation before live provider verification.

## MCP Servers

The expected workspace MCP server names are:

- `game`
- `sourcer`
- `ssot`
- `sonic`
- `corpus`
- `cocoindex-code`
- `github`
- `huggingface`
- `ncbi`

`github` is currently the Copilot-hosted GitHub MCP endpoint when generated with `-GitHubMode copilot`. `huggingface` is the Hugging Face HTTP MCP endpoint. `ncbi` is the generalized local stdio NCBI E-utilities server for all Entrez content families. `github` and `huggingface` receive generated bearer headers from the API pool in local `.mcp.json`.

`.mcp.json` is local/ignored and may contain generated literal bearer headers because current MCP clients commonly require literal headers. If an IDE update rewrites `.mcp.json`, regenerate it from the pool; do not refresh tokens.
