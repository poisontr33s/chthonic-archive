---
- Her-Macp-Architecture-Reference: #!/usr/bin/env markdown
- SID: CLAUDEBASE_MACP_ARCH_REF_V1
- Open-Seas: chthonic-archive/CLAUDEBASE/charts/macp-architecture-reference.md
- Parent-Chart: macp-migration-plan.md
- Register-Blend: Nautical · Industrial · Protocol
---

# (`☥`/`CLAUDEBASE`/`MACP-ARCHITECTURE-REFERENCE`)

> *The borrowed keel has been measured. The new hull is not yet laid.*

This leaf is the Lane-2 intake surface for MACP: **MCP + ACP + the Copilot SDK ergonomic pattern**, without a GitHub runtime dependency.

It is deliberately factual. It records what exists locally after Phase 0 and where the architecture extraction continues.

---

## (`Current Baseline`)

- **Copilot SDK stable baseline:** `github-copilot-sdk = "1.0.4"`.
- **Root consumers verified:** `chthonic-archive`, `chthonic-mcp`, `copilot-triage`.
- **Native consumer verified:** `extensions/chthonic-archive/native/chthonic-copilot-bridge`.
- **ACP sibling verified:** `extensions/chthonic-archive/native/chthonic-acp-bridge` compiles and prints local help.
- **Quota wall observed:** live Copilot sessions exceed monthly quota for this account path.
- **Help-safety repair:** `chthonic-mcp` and `copilot-triage` now print `-h`/`--help` locally before provider startup.

The quota wall is the strategic reason for Lane 2: keep the ergonomic gains, remove entitlement dependency from the in-house lane.

---

## (`Observed Local Lanes`)

### (`GitHub Lane`)

Path:

```text
extensions/chthonic-archive/native/chthonic-copilot-bridge/
```

Role:

- uses `github-copilot-sdk`;
- speaks the Copilot SDK path;
- exposes `--smoke`, `--prompt`, and `--help`;
- remains useful as the GitHub/Copilot bridge, but should not be the only agent substrate.

### (`ACP Lane`)

Path:

```text
extensions/chthonic-archive/native/chthonic-acp-bridge/
```

Role:

- uses `agent-client-protocol = "0.13.1"` with `unstable`;
- spawns an ACP-speaking agent command, currently shaped as `<agent> --acp`;
- creates ACP sessions, sends prompt blocks, streams notifications to stdout;
- auto-approves permission requests locally, with upstream UI expected in the TypeScript shell.

This lane is the closest existing shape to MACP's open standard side.

### (`Local Backend Mirror`)

Paths:

```text
meta-ide/LocalAI-3.11.0/
meta-ide/copilot-sdk/
meta-ide/copilot-sdk-rust-v1.0.0-beta.9/
```

Role:

- `LocalAI-3.11.0` is the candidate OpenAI-compatible backend for self-hosted inference.
- `copilot-sdk` and the archived beta Rust mirror are study material, not the desired runtime dependency.

---

## (`MACP Target Shape`)

MACP should become a local Rust SDK crate, not a Copilot fork:

```text
tools/chthonic-macp-sdk/
```

First crate surface:

- `Transport` — async send/receive boundary.
- `Session` — open, prompt, stream, close.
- `Tool` — typed tool handler with schema.
- `ToolRegistry` — MCP-backed registration layer.
- `MacpClient` — user-facing client.
- `MacpSession` — active session handle.

Backend adapters should be separable:

- `AcpTransport` for ACP-speaking agents.
- `LocalAiTransport` for OpenAI-compatible HTTP/SSE.
- future adapters only if they preserve the same session/tool contract.

---

## (`Architecture Extraction Queue`)

Next agent should read in this order:

1. `extensions/chthonic-archive/native/chthonic-copilot-bridge/src/main.rs`
2. `extensions/chthonic-archive/native/chthonic-acp-bridge/src/main.rs`
3. `tools/chthonic-mcp/src/main.rs`
4. `tools/copilot-triage/src/main.rs`
5. `meta-ide/copilot-sdk-rust-v1.0.0-beta.9/rust/src/` for historical pattern extraction only.
6. `meta-ide/LocalAI-3.11.0/` only when implementing the LocalAI backend.

Do not begin with the archived beta mirror. Begin with the live local bridges, then use the mirror to explain patterns already seen.

---

## (`Non-Negotiables`)

- MACP is not a clone of `github-copilot-sdk`.
- MACP must not require Copilot entitlement for the in-house lane.
- ACP remains the open session-wire reference.
- MCP remains the tool/context/resource injection reference.
- Local files and local binaries are the durable transition surface.
- Provider calls must be explicit; `--help` and local inspection must never spend quota.

---

## (`Next Concrete Step`)

Create `tools/chthonic-macp-sdk/` as a workspace member with traits only:

- no provider calls;
- no LocalAI HTTP yet;
- no derive macro yet;
- compile-only proof that downstream tools can depend on the crate and define a session/tool shape.

After that, fork one small proof binary from `copilot-triage` into `tools/macp-triage` and run it against a fake transport before any live backend is allowed.

*SID: CLAUDEBASE_MACP_ARCH_REF_V1 · Phase-1 seed · created after Phase-0 verification*
