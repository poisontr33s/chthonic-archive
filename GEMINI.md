# GEMINI.md

This file provides guidance to Google Gemini CLI when working with code in this repository.

> **Shared Config:** See [AGENT_COMMON.md](AGENT_COMMON.md) for execution invariants, commands, architecture, and triad references.

---

## Gemini-Specific Notes

- **Workspace config:** `.gemini/settings.json`
- **Global config:** `~/.gemini/settings.json`
- **Model:** Use `auto-gemini-3` or `gemini-3-pro-preview` (requires `general.previewFeatures: true`)
- **Auth:** OAuth for Gemini API; GitHub MCP requires PAT via user env var (not JSON, not `.env`)
- MCP servers should NOT use Docker on this system (Docker not installed)
- `_sources/` directories are optional repo clones; only `gemini-extension.json` files are required

## MCP Validation

To verify GitHub MCP is working:
```
gemini
/mcp list
```
Should show GitHub MCP connected with PAT auth.

## Gemini File Filtering

If Gemini can't read files due to `.gitignore` patterns:
1. Check `.gemini/settings.json` has `"respectGitIgnore": false`
2. Check `.geminiignore` is a blacklist (not broken whitelist)
3. Restart Gemini CLI to clear cache
