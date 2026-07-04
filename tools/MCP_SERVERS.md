# Chthonic MCP Servers

This repository contains specialised Model Context Protocol (MCP) servers tailored for the Chthonic Arc-IV architecture. These servers provide AI agents (AGY, Claude) with deterministic, zero-latency access to authoritative documentation, preventing framework hallucination in Vulkan and Bevy.

## Architecture & Transport

All servers are built on the `rmcp` Rust crate using the **stdio transport layer**.
- **JSON-RPC** messages are strictly communicated over `stdin` and `stdout`.
- **Tracing / Logging** is explicitly routed to `stderr` (`tracing_subscriber::fmt().with_writer(std::io::stderr)`) to prevent stream corruption.

> **CRITICAL TESTING NOTE (two distinct hazards):**
>
> 1. **PowerShell `$args` shadowing.** `$args` is a PowerShell reserved automatic variable. If a test function names its parameter `$Args`, the value is silently discarded. The tool call is written as `"arguments":}` (malformed JSON), the server emits a JSON parse error, and the test harness receives exactly two lines — the `InitializeResult` and the parse error — totalling 208 bytes. Fix: name the parameter `$ToolArgs` or any non-reserved name.
>
> 2. **Stdin EOF race with in-flight network I/O.** `$proc.StandardInput.Close()` signals EOF. The `rmcp` runtime completes the current tool handler before shutting down, so for fast (HashMap) tools this is safe. For tools that make outbound HTTP calls (`bevy_api_search`, `bevy_book_index`), close stdin *before* reading stdout and use `ReadToEndAsync().GetAwaiter().GetResult()` paired with `WaitForExit()` — not a fixed `Sleep`. This ensures the read task blocks until the process exits cleanly with all output flushed, regardless of network latency.

---

## 1. Vulkan Diagnostics Server (`vulkan-mcp-server`)

Provides offline, regex-driven Vulkan validation log parsing and zero-latency Khronos Specification constraint lookups.

### Initialization
At process start, it downloads the 14.5MB Khronos `validusage.json` and flattens all 27,606 Valid Usage IDs (VUIDs) into an `Arc<HashMap>` in memory. This is cached to `~/.chthonic/validusage.json` to survive network partitions and avoid cold-start penalties.

### Tools
- **`vulkan_resolve_vuid`**: 
  - **Exact Match:** Returns the normative Khronos specification text for a given VUID.
  - **Partial Match:** Scans all keys for substrings and degrades gracefully, returning up to 5 nearest-match VUID candidates sorted by specificity.
- **`vulkan_audit_logs`**: Ingests raw stdout telemetry, uses pre-compiled regexes to extract VUIDs, `Vk` object handles, and enumerations, then returns a deduplicated, sorted JSON summary of violations.
- **`vulkan_suggest_remediation`**: An expert-systems heuristic that maps specific `VK_OBJECT_TYPE_*` failures to known Rust/Ash pipeline pitfalls (e.g., memory lifetimes, layout transitions).

---

## 2. Bevy Knowledge Server (`bevy-mcp-server`)

Provides deterministic API signatures and conceptual documentation for Bevy 0.19.0.

### Tools
- **`bevy_api_search`**: Resolves core Bevy types (e.g., `Commands`, `Query`, `ResMut`) via a static routing table to `docs.rs/bevy/0.19.0`. It fetches the HTML, strips tags, and extracts the raw Rust `struct`/`trait` signature and the primary docblock paragraph.
- **`bevy_book_index`**: Queries the GitHub Git Trees API (`bevyengine/bevy-website`) to return a list of all valid Markdown paths for the Bevy 0.19.0 book, bypassing Zola frontmatter artifacts.
- **`bevy_read_section`**: Fetches raw Markdown content for a specific Bevy Book path directly from GitHub user content.
