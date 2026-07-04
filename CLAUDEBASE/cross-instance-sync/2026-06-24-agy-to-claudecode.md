# Cross-Instance Sync — Claude Code ↔ Antigravity (AGY)
**Date:** 2026-06-24  
**Author:** Antigravity / AGY (Claude in Antigravity CLI, pwsh terminal)  
**For:** Claude Code (engine lane, VS Code Insiders)  
**Relay:** Owner (manual routing)

---

## What AGY Has Done (Gemini lane absorbed, now AGY-owned)

Two MCP servers are **compiled, workspace-registered, and ready to wire.**

### `tools/bevy-mcp-server`
- **Purpose:** Anti-hallucination gate for Bevy 0.19.0. Fetches live Markdown from `bevyengine/bevy-website` raw GitHub. Scrapes `docs.rs` for type signatures.
- **Tools exposed:** `bevy_book_index`, `bevy_read_section`, `bevy_api_search`
- **Known stub:** `bevy_api_search` targets `all.html` — JS rendering limits depth. Functional but shallow. Upgrade path exists (path-mapping lookup table) — not blocking.
- **Status:** `cargo check` clean, 0 errors.

### `tools/vulkan-mcp-server`
- **Purpose:** Ingests 14.5MB `validusage.json` from KhronosGroup at startup into `Arc<HashMap>`. Deduplicates raw validation layer console residue. Zero-latency VUID lookup. Heuristic remediation by object type.
- **Tools exposed:** `vulkan_audit_logs`, `vulkan_resolve_vuid`, `vulkan_suggest_remediation`
- **Status:** `cargo check` clean, 0 errors.

### What was patched (rmcp 1.7 API drift)
The DR spec used a 1-arg `ErrorData::internal_error(msg)` — actual rmcp 1.7 requires `(msg, Option<Value>)`. All call sites patched to `(msg, None)`. `ServerInfo` construction updated to `ServerInfo::new(caps)`. DR source artifact also corrected to match.

### Pending (AGY will handle when you give the signal)
- Wire both servers into `.mcp.json` — needs `cargo build --release` paths and environment config
- `bevy_api_search` upgrade to path-mapping (optional, not blocking any rung)

---

## What AGY Needs from Claude Code

To stay in sync and not duplicate work or drift:

1. **Current state of `src/render/zodiac.rs`** — specifically the `ZodiacSlot` fields and what the `semantics` output currently returns. AGY knows it's `"owner-defined"` but needs the exact struct shape before touching it.

2. **Any live Vulkan validation errors** — if there are new VUIDs in `CLAUDEBASE/watch/error-log-2026-06-23.md` or any newer log, paste them into `vulkan_audit_logs` once the server is wired. That's the first real test of the Vulkan MCP.

3. **DLAA consumer shape** — when Rung 2 starts, AGY wants to know: is this additive to the existing TAA pipeline, or does it replace the resolve pass? The `Streamline` scaffold — is it a Bevy plugin, raw Vulkan extension, or extern C ABI?

4. **Perspective lens (§2.7)** — what does the current `iso` view abstraction look like in code? File + struct name. AGY can spec the lens abstraction layer without touching the engine if the interface is known.

---

## What Claude Code Should Know AGY is NOT Doing

- **Not touching engine Rust files** (`src/render/`, `assets/shaders/`) — that's Claude Code's lane
- **Not defining semantics** for the 7 celestial bodies — those come from the owner (SSOT.md), and are owner-defined only
- **Not committing** to main — AGY's MCP work should go on a branch or be committed by Claude Code after review

---

## Shared CLAUDEBASE Paths (canonical cross-instance refs)

| Path | Owner | What |
|---|---|---|
| `.chthonic/SESSION_ANCHOR.md` | AGY updates | Cold-start state, platter order |
| `CLAUDEBASE/charts/north-star-constellations.md` | Claude Code | Rung ledger (authoritative) |
| `CLAUDEBASE/watch/error-log-2026-06-23.md` | Claude Code | Structured Vulkan bug log |
| `CLAUDEBASE/sub-surface-skinny-dipping/sub-terranean-refreshed-returns/bevy-and-vulkan-mcp-servers.md` | AGY (corrected) | MCP server DR + corrected implementation |
| `tools/bevy-mcp-server/src/main.rs` | AGY | Bevy MCP implementation |
| `tools/vulkan-mcp-server/src/main.rs` | AGY | Vulkan MCP implementation |
| `src/render/zodiac.rs` | Claude Code | 7-body ankhological engine |

---

## Relay Question for Claude Code

> **"What would you find most useful from AGY right now — and what can you give AGY that unblocks the next sync?"**

Suggested answers Claude Code might give:
- A ready-to-paste `.mcp.json` config block with the compiled binary paths
- The `zodiac.rs` struct shape so AGY can prep the semantics integration layer
- Confirmation on DLAA architecture (additive vs. replace) so AGY can spec the MCP remediation heuristics for that rung's Vulkan surface

---

*This packet is the routing artifact. Owner relays it. Neither instance polls the other directly.*
