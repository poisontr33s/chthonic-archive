# MCP Server Specifications for Gemini Deep Research

**Target Audience:** Gemini Deep Research Agent
**Objective:** Research, design, and scaffold two specialized MCP servers to accelerate engine development by preventing framework hallucinations and structurizing dense error logs.

---

## 1. Bevy Knowledge MCP Server (`bevy-mcp-server`)

### Problem Statement
Bevy APIs change rapidly between versions. Agents frequently hallucinate outdated APIs (e.g., from 0.12 or 0.14) when attempting to write logic for the current stable `0.19.0`. A specialized MCP server pointing to the official, up-to-date documentation is required.

### Target Domain
- **Source:** `https://bevy.org/learn/` (The Bevy Book) and `https://docs.rs/bevy/latest/bevy/` (Rustdocs).
- **Target Version:** `0.19.0` (Latest Stable).

### Required Tools to Implement
1. **`bevy_book_index`**
   - **Description:** Retrieves the table of contents and sections from the Bevy Book to allow agents to understand the documentation structure.
2. **`bevy_read_section`**
   - **Description:** Fetches the full markdown/text content of a specific Bevy Book section (e.g., "ECS", "Systems", "Assets").
3. **`bevy_api_search`**
   - **Description:** Queries the Bevy rustdocs for specific types, functions, or traits (e.g., `Commands`, `Query`, `ResMut`) to retrieve their precise `0.19.0` signatures and docstrings.

### Deep Research Tasks
- Identify the most efficient way to scrape or ingest the Bevy Book into the MCP server (e.g., using `reqwest` + `scraper`, or downloading the raw markdown from the Bevy GitHub repo).
- Design the stdio transport wrapper using `rmcp`.

---

## 2. Vulkan Diagnostics MCP Server (`vulkan-mcp-server`)

### Problem Statement
Vulkan Validation Layers produce highly verbose, disparate console residue. While we have a primitive log parser (`chthonic_vulkan_doctor`), we need a dedicated MCP server that not only clusters errors but actively resolves VUIDs against the Vulkan Specification to provide actionable fixes.

### Target Domain
- **Source 1:** Local `target/render-smoke.log` (or dynamic standard output streams).
- **Source 2:** The Official Vulkan Specification registry (`https://registry.khronos.org/vulkan/`).

### Required Tools to Implement
1. **`vulkan_audit_logs`**
   - **Description:** Parses raw Vulkan validation logs, deduplicates repeating VUIDs, and returns a structured JSON or Markdown summary of active issues (e.g., Count, VUID, Object, Message).
2. **`vulkan_resolve_vuid`**
   - **Description:** Takes a specific VUID (e.g., `VUID-vkCmdDraw-None-08114`) and fetches the exact specification text from the Khronos registry or a local offline spec JSON.
3. **`vulkan_suggest_remediation`**
   - **Description:** (Optional/Stretch) Cross-references the VUID with common Rust/Ash/Vulkano implementation pitfalls to suggest the exact pipeline, layout transition, or alignment fix required.

### Deep Research Tasks
- Determine if Khronos provides a machine-readable format (JSON/XML) for VUIDs that the MCP server can bundle for offline, zero-latency spec resolution.
- Design the regex patterns required to flawlessly extract Object Handles, Memory Pointers, and VUIDs from the raw validation layer text.
- Scaffold the server in Rust using `tokio` and `rmcp`.

---

## Next Steps for Gemini
1. **Ingest this Spec:** Review the requirements above.
2. **Execute Research:** Identify data sources (GitHub repos for Bevy docs, Khronos XML for Vulkan).
3. **Output:** Generate the `src/main.rs` and `Cargo.toml` implementations for both servers.
