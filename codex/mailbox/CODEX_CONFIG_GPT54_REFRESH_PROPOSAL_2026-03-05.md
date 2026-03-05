# Codex Config GPT-5.4 Refresh Proposal

Date: 2026-03-05

This repo forbids agent edits to `.codex/*.toml` and `~/.codex/*.toml`, so this is a proposal artifact, not an in-place mutation.

## Verdict

Refresh both Codex config files to the current documented key surface.

Preserve:

- autonomous operation
- visible reasoning
- VS Code Insiders file opening
- workspace-write sandboxing
- GitHub MCP

Replace or remove:

- `model_reasoning_effort = "extra high"` -> use `xhigh`
- `features.web_search_request = true` -> use top-level `web_search = "live"`
- top-level `network_access = true` -> move to `[sandbox_workspace_write].network_access = true`
- non-canonical `[behavior] execution_mode` and `suppress_option_menus` -> do not carry forward
- undocumented `write_permissions = true` -> do not carry forward

Add:

- explicit GPT-5.4 context declaration
- explicit auto-compaction threshold
- official OpenAI developer docs MCP server
- a small set of current canonical feature flags that improve usability in a PowerShell-heavy repo

## Proposed Workspace Config

Target: `C:/Users/erdno/chthonic-archive/.codex/config.toml`

```toml
# Workspace Codex Configuration (canonical GPT-5.4 refresh)

model = "gpt-5.4"
model_provider = "openai"
file_opener = "vscode-insiders"

approval_policy = "never"
sandbox_mode = "workspace-write"
web_search = "live"

# GPT-5.4 documented context window.
model_context_window = 1050000

# Inference: compact before the last ~150k tokens of headroom disappear.
model_auto_compact_token_limit = 900000

model_reasoning_effort = "xhigh"
model_reasoning_summary = "auto"
hide_agent_reasoning = false
show_raw_agent_reasoning = true
personality = "pragmatic"

[sandbox_workspace_write]
writable_roots = [
  "C:/Users/erdno/chthonic-archive",
]
deny_paths = [
  ".codex/config.toml",
  ".codex/instructions.md",
  ".git/hooks",
]
network_access = true
exclude_tmpdir_env_var = false
exclude_slash_tmp = false

[features]
apply_patch_freeform = true
unified_exec = true
child_agents_md = true
powershell_utf8 = true
remote_models = true
runtime_metrics = true
shell_snapshot = true
search_tool = true

[mcp_servers.github]
url = "https://api.githubcopilot.com/mcp/"
bearer_token_env_var = "GITHUB_MCP_PAT"
enabled_tools = ["issues", "pull_requests", "repos", "user"]
required = false
startup_timeout_sec = 20
tool_timeout_sec = 90
http_headers = { "User-Agent" = "Codex-CLI/1.0" }

[mcp_servers.openaiDeveloperDocs]
url = "https://developers.openai.com/mcp"
required = false
startup_timeout_sec = 20
tool_timeout_sec = 90
```

## Proposed Global Config

Target: `C:/Users/erdno/.codex/config.toml`

```toml
# Global Codex Configuration (canonical fallback)

cli_auth_credentials_store = "file"
forced_login_method = "chatgpt"

model = "gpt-5.4"
approval_policy = "never"
web_search = "live"
model_reasoning_effort = "xhigh"
model_reasoning_summary = "auto"
hide_agent_reasoning = false
show_raw_agent_reasoning = true
personality = "pragmatic"

[features]
apply_patch_freeform = true
unified_exec = true
child_agents_md = true
powershell_utf8 = true
remote_models = true
runtime_metrics = true
shell_snapshot = true

[mcp_servers.github]
url = "https://api.githubcopilot.com/mcp/"
bearer_token_env_var = "GITHUB_MCP_PAT"
enabled_tools = ["issues", "pull_requests", "repos", "user"]
required = false
startup_timeout_sec = 20
tool_timeout_sec = 90

[mcp_servers.github.http_headers]
User-Agent = "Codex-CLI/1.0"

[mcp_servers.hf-mcp-server]
url = "https://huggingface.co/mcp?login"
required = false

[mcp_servers.openaiDeveloperDocs]
url = "https://developers.openai.com/mcp"
required = false
startup_timeout_sec = 20
tool_timeout_sec = 90

[windows]
sandbox = "elevated"
```

## Why This Is The Better 2026 Baseline

- `gpt-5.4` is the current frontier model for professional work and is available in Codex, the API, and ChatGPT.
- GPT-5.4 supports a `1,050,000` token context window and `128,000` max output tokens.
- `model_context_window` and `model_auto_compact_token_limit` are current documented Codex config keys.
- `web_search = "live"` is the canonical replacement for deprecated `features.web_search_request = true`.
- `approval_policy = "never"` is the current documented control that matches autonomous/non-interactive behavior.
- `powershell_utf8`, `shell_snapshot`, `remote_models`, `runtime_metrics`, and `search_tool` are current documented feature flags.
- adding `openaiDeveloperDocs` closes the current documentation MCP gap in this environment.

## Notes

- `model_auto_compact_token_limit = 900000` is an inference, not a documented mandatory value.
- I chose `model = "gpt-5.4"` because that is the current public documented model id. If your installed Codex build only accepts the Codex-surface alias, keep `gpt-5.4-codex` and apply the rest of the refresh unchanged.
- `service_tier = "priority"` is an API request setting, not a Codex TOML key. If you want GPT-5.4 at the fastest API path, set it in clients that call the OpenAI API.
- `tool search` is primarily a model/API capability. `features.search_tool = true` only affects Codex Apps tool discovery.
- I am intentionally not carrying forward undocumented keys that did not appear in the current config reference.

## Source References

- OpenAI release: https://openai.com/index/introducing-gpt-5-4/
- Codex config reference: https://developers.openai.com/codex/config-reference
- GPT-5.4 model page: https://developers.openai.com/api/docs/models/gpt-5.4
- Priority processing: https://developers.openai.com/api/docs/guides/priority-processing
- Tool search: https://developers.openai.com/api/docs/guides/tools-tool-search

## Post-Application Audit

Observed on 2026-03-05 after the user applied the refresh manually.

### Current Status

- both `C:/Users/erdno/chthonic-archive/.codex/config.toml` and `C:/Users/erdno/.codex/config.toml` parse as valid TOML
- workspace config now carries the GPT-5.4 long-context keys and current canonical search setting
- global config now carries the current canonical search setting and OpenAI docs MCP declaration
- workspace kept `model = "gpt-5.4-codex"` while global uses `model = "gpt-5.4"`; this is acceptable if the local Codex build prefers the Codex alias

### Remaining Discrepancies

- the live Codex session has not reloaded the new MCP server declarations yet
- `openaiDeveloperDocs` is present in config but is not active in the current process until Codex is restarted
- workspace has `model_context_window` and `model_auto_compact_token_limit`, while global does not; this is fallback drift for non-workspace sessions
- `features.search_tool = true` exists in workspace but not in global; this is parity drift, not a hard blocker
- `file_opener = "vscode-insiders"` exists in workspace but not in global; this is fallback drift, not a hard blocker

### Image Tool Note

- there is no current documented direct replacement for legacy `view_image_tool`
- leaving that key out is correct
- image viewing is typically provided by the runtime/tool harness, not by a current Codex TOML feature flag
- image generation remains an API or skill-level concern rather than a config-toggle concern

### MCP Review

Required for this repo's current practical command surface:

- `github`
- `openaiDeveloperDocs`

Optional:

- `hf-mcp-server` if you actively use the global Hugging Face lane

Not currently necessary:

- a filesystem MCP, because shell access plus patch tooling already covers local file operations
- additional repo MCP servers, because current repo workflows are already covered by shell, GitHub MCP, and OpenAI docs MCP

### Stale Global Layer Findings

The main stale global artifact is not the global config file anymore. It is `C:/Users/erdno/.codex/instructions.md`.

It still contains older lane rules such as:

- forbidding `git add` and `git commit`
- mailbox response routing rules that do not match the current repo-local execution model
- older skill references that are narrower than the workspace skill surface

`C:/Users/erdno/.codex/skills` is not obviously broken, but it is a much smaller baseline than the workspace `.codex/skills` tree and should be treated as a generic fallback, not as a parity mirror.

### Next Practical Action

- restart Codex so the newly added MCP server declarations are loaded into the live session
- after restart, verify that `openaiDeveloperDocs` appears alongside `github`
- if you want strict fallback parity, copy the workspace `search_tool` and `file_opener` choices into global config as well
- if you want to eliminate the remaining stale guidance layer, refresh `C:/Users/erdno/.codex/instructions.md` and possibly `C:/Users/erdno/.codex/AGENTS.md` to match the current governance baseline
