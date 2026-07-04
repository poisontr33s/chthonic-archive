<!--
  Chthonic Archive License 1.0 (CAL-1.0)
  Copyright 2026 poisontr33s / Espen Synnestvedt / The Chthonic Archive
  Authored under sovereign direction by Claude Code / claude-sonnet-4-6 (C) 2026- 2028 (R)

  All source, documentation, and tooling in this directory is proprietary to The Chthonic Archive
  and its owner. No open-source license applies. Reproduction, redistribution, or derivative works
  require explicit written authorisation from the owner.

  Claude-authored artifacts carry co-authorship by Claude Code under sovereign direction of the
  owner. AI authorship does not transfer rights to Anthropic or any third party.
-->

# `tools/`

*The external-interface layer of the Chthonic Archive. Each subdirectory is a discrete tool with its own `Cargo.toml` / workspace membership. Tools do not import each other. When I read this cold, I start here.*

---

## MCP Server Layer — **Active / Production**

Two `rmcp`-based stdio MCP servers are the primary compounding surface of this layer. Both are E2E-verified and wired into the AGY CLI (`~/.gemini/antigravity-cli/mcp_config.json`) and Claude Code (`.mcp.json`).

**Deep reference:** [`MCP_SERVERS.md`](MCP_SERVERS.md) — transport contract, stdin EOF hazards, parser architecture.

---

### `bevy-mcp-server/` — Bevy 0.19.0 Knowledge

Three tools. No state between calls. HTTP client (`reqwest`, 10 s timeout, `chthonic-agy/bevy-mcp-server/0.19.0` user-agent).

| Tool | What it does |
|---|---|
| `bevy_book_index` | GitHub Git Trees API → filtered list of all `content/learn/**/*.md` paths |
| `bevy_read_section` | Raw GitHub fetch of a specific Bevy Book path → Markdown |
| `bevy_api_search` | Static type-table (35 types) → docs.rs 0.19.0 HTML fetch → declaration + docblock |

*`bevy_api_search` known constraint:* The static table covers the 35 most-used ECS/app types. For unlisted types, supply the explicit module path (`ecs/system/struct.MyType`). The docs.rs HTML extractor targets `item-decl` + first `docblock` paragraph — zero dependency on a parser crate.

---

### `vulkan-mcp-server/` — Vulkan Diagnostics

Three tools. Heavy init (14.5 MB JSON download + parse → `Arc<HashMap<String, String>>` with 27,606 VUID entries). Cache at `~/.chthonic/validusage.json`. After first run, init is local-disk-only.

| Tool | What it does |
|---|---|
| `vulkan_resolve_vuid` | Exact VUID → normative Khronos spec text; falls back to substring search → up to 5 candidates |
| `vulkan_audit_logs` | Raw validation stderr → deduped, occurrence-sorted JSON violation map with object types + handles |
| `vulkan_suggest_remediation` | VUID + `VK_OBJECT_TYPE_*` → heuristic Rust/Ash remediation advice |

*Partial match behaviour:* A fragment like `None-08114` returns all VUIDs whose lowercase key contains that string, sorted by key length (shortest = most specific first). Multiple candidates are returned as a candidates list — agent calls again with the exact VUID.

---

## Build

```powershell
# Both servers together
cargo build -p bevy-mcp-server -p vulkan-mcp-server

# Individual
cargo build -p bevy-mcp-server
cargo build -p vulkan-mcp-server
```

Binaries land at `target/debug/bevy-mcp-server.exe` and `target/debug/vulkan-mcp-server.exe`. These are the paths in both MCP config files — no path changes needed after a rebuild.

---

## Wire-up

| Consumer | Config file |
|---|---|
| Claude Code | `.mcp.json` (project root) |
| AGY CLI (Gemini) | `~/.gemini/antigravity-cli/mcp_config.json` |

Both configs point to the debug binaries. Release builds are not required for MCP server use.

---

## Testing Invariants

**Do not use `$Args` as a PowerShell parameter name.** It is a reserved automatic variable; the value is silently dropped, producing malformed JSON `"arguments":}`. The server returns a parse error (68 bytes), giving a total 208-byte `NO_RESPONSE` result. Use `$ToolArgs` or any other name.

**Use `ReadToEndAsync` + `WaitForExit` for harness I/O**, not `BaseStream.Read()` after a sleep. `Read()` returns what is immediately buffered — for tools making outbound HTTP calls, that may be only the init response. `ReadToEndAsync` blocks until stdout EOF (process exit), capturing the full response regardless of network latency.

Full testing protocol: [`MCP_SERVERS.md`](MCP_SERVERS.md).

---

## Other Tools in This Directory

| Directory | Status | Purpose |
|---|---|---|
| `chthonic-mcp-server/` | Active | Rust rmcp MCP server — chthonic native tools |
| `dsl-smoke/` | Active | 6-binary DSL grammar smoke-test workspace |
| `dsl-iteration-toolkit/` | Active | Rewindability ledger + pattern catalog for DSL iteration |
| `ankh-forge/` | Active | Ankh DSL forge tooling |
| `spec-enforcer/` | Active | Specification enforcement tooling |
| `copilot-triage/` | Active | GitHub PR/check-run noise → structured triage |
| `chthonic-mcp/` | Staging | Earlier MCP iteration |
| `chthonic-cai/` | Staging | CAI integration scaffolding |
| `voice-iter/` | Staging | Voice iteration tooling |

*Status is my read of the directory state at time of authoring. Verify with `cargo check -p <name>` before assuming any tool is buildable.*

---

*Authored by Claude Code / claude-sonnet-4-6 under sovereign direction of poisontr33s / Espen Synnestvedt / CAL-1.0.*
