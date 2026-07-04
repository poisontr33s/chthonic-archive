---
- Her-Macp-Plan: #!/usr/bin/env markdown
- SID: CLAUDEBASE_MACP_V1
- Claudebase-Flavored-Blend: permanently-living-document
- Ssot-Monolith: [ssot](../../.chthonic/SSOT.md)
- Open-Seas: chthonic-archive/CLAUDEBASE/charts/macp-migration-plan.md
- Altitude: Chart-Room · Dry-Dock
- Island: Cat-Island · 24.4000,-75.5000 — the shipyard cay; where hulls are rebuilt
- Real-Sky: --live (Open-Meteo; never stamped)
- Heat-Index: Ozone-And-Solder · Blueprint-Blue · Anvil-Cool
- Cosmological-Altitude: --live celestial over this chamber's island · CLAUDEBASE_COSMOS_V1 · verified vs JPL Horizons
- Register-Blend: Nautical · Industrial · Architectural
- Barometer: read by CLAUDEBASE_BAROMETER_V1 (re-run to refresh)
- Upcycle-Protocol: [upcycle-protocol.md](upcycle-protocol.md)
---

# (`☥`/`CLAUDEBASE`/`MACP-MIGRATION-PLAN`)

> *Det som var lånt fra dypet, skal bli bygget på eget kjøl.*  
> *What was borrowed from the deep, shall be built on its own keel.*

- *— This plan executes — **(`Lane-2`)** — of the Copilot SDK migration: fork the SDK's ergonomic architecture into an in-house agent substrate called — **(`MACP`)** — that unifies — **(`ACP`)** — (Agent Client Protocol, Zed's open standard) with — **(`MCP`)** — (Model Context Protocol). The backend swaps from GitHub Copilot to — **(`LocalAI`)** — or any OpenAI-compatible endpoint. No GitHub runtime dependency.*

---

## (`Vision`)

- **(`MACP`)** = **(`M`)**odel-context + **(`A`)**gent-client + **(`P`)**rotocol.
  - **(`ACP`)** provides the agent session wire: open, stream tokens, close. Open standard. Pre-1.0 (`0.13.1`, `unstable` feature) but canonical (Zed ships it).
  - **(`MCP`)** provides tool/resource/context injection: typed tools, schemas, server lifecycle. Open standard.
  - **(`Copilot-SDK-pattern`)** provides the ergonomics: typed tools via `derive`, streaming, clean session lifecycle. We steal the pattern, not the crate.
  - **(`LocalAI`)** provides the backend: self-hosted, OpenAI-compatible, already in workspace at `meta-ide/LocalAI-3.11.0/`.

- *— The result: a — **(`chthonic-macp-sdk`)** — Rust crate that any in-house tool can depend on instead of `github-copilot-sdk`. Same ergonomic API. No GitHub entitlement required. Backend-agnostic.*

---

## (`Phases`)

### (`Phase-0`/`Lane-1`/`Baseline-Unification`) — COMPLETE

Bump all `github-copilot-sdk` pins to latest stable `1.0.4`. Precondition for everything.

| File | Current | Target |
|---|---|---|
| `Cargo.toml` (root) | `1.0.0-beta.9` | `1.0.4` |
| `tools/chthonic-mcp/Cargo.toml` | `1.0.0-beta.9` | `1.0.4` |
| `tools/copilot-triage/Cargo.toml` | `1.0.0-beta.9` | `1.0.4` |
| `extensions/chthonic-archive/native/chthonic-copilot-bridge/Cargo.toml` | `1.0.0` | `1.0.4` |

- Rebuild all 4 consumers. E2E verify `chthonic-mcp --help` and `copilot-triage --help`.
- Regenerate root `Cargo.lock`.
- Mark `meta-ide/copilot-sdk-rust-v1.0.0-beta.9/` as historical reference (Phase 6 retires it).

**Verification — 2026-06-28**

- `Cargo.toml` root: `github-copilot-sdk = "1.0.4"`.
- `tools/chthonic-mcp/Cargo.toml`: `github-copilot-sdk = "1.0.4"` with `derive`.
- `tools/copilot-triage/Cargo.toml`: `github-copilot-sdk = "1.0.4"` with `derive`.
- `extensions/chthonic-archive/native/chthonic-copilot-bridge/Cargo.toml`: `github-copilot-sdk = "1.0.4"`.
- Root `Cargo.lock`: `github-copilot-sdk v1.0.4`.
- Native extension `Cargo.lock`: `github-copilot-sdk v1.0.4`.
- `cargo check -p chthonic-archive`: PASS, warnings only.
- `cargo check -p chthonic-mcp`: PASS.
- `cargo check -p copilot-triage`: PASS.
- `cargo check -p chthonic-copilot-bridge` from `extensions/chthonic-archive/native`: PASS.
- `cargo run -p chthonic-mcp -- --help`: PASS, local help only.
- `cargo run -p copilot-triage -- --help`: PASS, local help only.
- `cargo run -p chthonic-copilot-bridge -- --help`: PASS.

**Quota-wall finding**

Before the help repair, `chthonic-mcp --help` and `copilot-triage --help` started live Copilot sessions and hit the monthly quota wall. That was not a 1.0.4 regression; it was missing local help handling in the two hand-rolled CLIs. Both tools now intercept `-h`/`--help` before manifest loading, `gh`, or Copilot startup.

---

### (`Phase-1`/`Architecture-Extraction`) — IN PROGRESS

Study the Copilot SDK source + ACP crate. Document the 4 core abstractions and what's GitHub-specific vs protocol-generic.

- Read `meta-ide/copilot-sdk-rust-v1.0.0-beta.9/rust/src/` — extract: transport, typed tool derive, session lifecycle, streaming.
- Read `chthonic-acp-bridge` source — extract: ACP wire format, how it differs from Copilot JSON-RPC.
- Read `agent-client-protocol` crate API (0.13.1).
- Output: `CLAUDEBASE/charts/macp-architecture-reference.md` — the pattern document MACP is built from. Seed created 2026-06-28 after Phase 0 verification; deeper source extraction remains open.

---

### (`Phase-2`/`MACP-Scaffold`)

Create the crate skeleton.

- Path: `tools/chthonic-macp-sdk/` (workspace member).
- `Cargo.toml`: `agent-client-protocol = "0.13.1"`, `serde`, `tokio`, `schemars`, `anyhow`, `tracing`.
- Core traits: `Transport`, `Tool`, `Session`, `Stream`.
- Core types: `MacpClient`, `MacpSession`, `ToolDefinition`, `ToolSchema`.
- No backend yet — traits only.

---

### (`Phase-3`/`LocalAI-Backend`)

Implement the first concrete backend.

- `LocalAiTransport` — speaks OpenAI-compatible HTTP to `meta-ide/LocalAI-3.11.0/` (or any endpoint).
- Streams tokens via SSE.
- Maps ACP session lifecycle to OpenAI chat-completion lifecycle.

---

### (`Phase-4`/`MCP-Tool-Injection`)

Wire MCP into MACP.

- `McpToolRegistry` — discovers and registers MCP tool servers.
- `define_tool!` derive macro (mirrors Copilot SDK's `derive` feature, but on `schemars` directly).
- Tools injected into ACP session as tool-call schema.

---

### (`Phase-5`/`E2E-Proof`)

Migrate one consumer as proof-of-concept.

- `tools/copilot-triage` → fork to `tools/macp-triage` (or refactor in place).
- Swap `github-copilot-sdk` dep for `chthonic-macp-sdk`.
- Point at LocalAI backend.
- E2E: triage a test input, verify tool calls fire, tokens stream, session closes clean.

---

### (`Phase-6`/`Retire-Beta`)

- Archive `meta-ide/copilot-sdk-rust-v1.0.0-beta.9/` → `meta-ide/archive/copilot-sdk-rust-v1.0.0-beta.9/`.
- Update `hold/stow-manifest.md` if it references the beta.
- Document the migration in `CLAUDEBASE/charts/macp-architecture-reference.md`.

---

## (`Status-Tracker`)

| Phase | Status | Started | Completed |
|---|---|---|---|
| 0 — Baseline Unification | COMPLETE | 2026-06-28 | 2026-06-28 |
| 1 — Architecture Extraction | IN PROGRESS | 2026-06-28 | — |
| 2 — MACP Scaffold | PENDING | — | — |
| 3 — LocalAI Backend | PENDING | — | — |
| 4 — MCP Tool Injection | PENDING | — | — |
| 5 — E2E Proof | PENDING | — | — |
| 6 — Retire Beta | PENDING | — | — |

---

*SID: CLAUDEBASE_MACP_V1 · initiated 2026-06-28 · Lane-2 fork: Copilot SDK pattern → MACP (ACP+MCP) → LocalAI backend*
