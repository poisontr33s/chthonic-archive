---
SID: CODEX_RUST_NATIVE_VSCODE_INSIDERS_PLAN_V1
created: 2026-07-09
status: active-adjustment
scope: chthonic-vscode-extension
evidence_gate: "Plan changed before continuation"
---

# Codex Rust-Native VS Code Insiders Plan

This supersedes the earlier web-app-heavy plan for the Chthonic VS Code Insiders companion.

The corrected target is not a React/Next application embedded in VS Code. The corrected target is a Rust-native local coding agent, shaped like OpenAI Codex CLI and Claude Code terminal flow, with VS Code Insiders acting as a thin editor shell.

## Evidence

- VS Code extension APIs are JavaScript-facing. The extension host runs Node.js for desktop extensions, so a tiny TypeScript adapter is unavoidable for registration, SecretStorage, terminal APIs, webview lifecycle, and WorkspaceEdit application.
- VS Code webviews are HTML surfaces controlled by the extension and communicate with the extension by message passing. They do not require React, Next.js, shadcn, or a browser-app architecture.
- OpenAI Codex CLI is distributed as a local coding agent with terminal use and editor install path. Its current public repository and release flow prove the desired product class is a native local agent first, editor integration second.
- Warp's current public framing also points the same way: terminal-born agentic development environment, with Claude Code, Codex, Gemini CLI, and similar agents brought into the terminal workflow.

## Corrected End-State

The end product is:

- `deepseek-core.exe`: Rust-native CLI/TUI and JSON-RPC sidecar.
- `chthonic-vscode-extension`: thin TypeScript VS Code bridge.
- Static webview: HTML/CSS plus a tiny `postMessage` bridge, not a React application.
- VS Code pseudoterminal: Rust-backed agent loop, Claude Code / Codex CLI style.
- Shared protocol: the same Rust event schema drives standalone CLI, VS Code chat, and VS Code terminal.

## Architecture

Rust owns:

- provider routing for Claude/OpenAI/Codex-compatible backends
- prompt and context management
- workspace graph/indexing
- streaming events
- terminal agent loop
- diff planning and rollback metadata
- session persistence
- logs and diagnostics

TypeScript owns only:

- extension activation
- command registration
- webview lifecycle
- SecretStorage access
- child-process spawn
- VS Code terminal/pseudoterminal registration
- applying Rust-produced `WorkspaceEdit` data

## Immediate Consequence

The Rust sidecar already added under `chthonic-vscode-extension/core/` is the correct first rung.

The next work must continue by expanding that Rust sidecar into a real Rust-native agent core and CLI/TUI, not by adding Next.js, shadcn/ui, or more frontend framework weight.

## Next Build Rungs

1. DONE — Split `core/src/main.rs` into protocol, command, and agent modules.
2. DONE — Add a standalone CLI mode: `deepseek-core chat`.
3. DONE — Keep JSON-RPC stdio mode for VS Code: `deepseek-core rpc`.
4. DONE — Move the deterministic stream stub behind a provider trait.
5. DONE — Add Claude/OpenAI provider modules after the protocol contract is stable.
6. DONE — Replace React webview code with static HTML/CSS and a minimal bridge once the Rust stream contract is complete.
7. IMPLEMENTED (2026-07-09) — Pseudoterminal integration with dedicated sidecar per terminal, streaming token output.

## Execution Checkpoint

Implemented 2026-07-09:

- `chthonic-vscode-extension/core/src/protocol.rs`
- `chthonic-vscode-extension/core/src/provider.rs`
- `chthonic-vscode-extension/core/src/agent.rs`
- `chthonic-vscode-extension/core/src/rpc.rs`
- `chthonic-vscode-extension/core/src/cli.rs`
- `chthonic-vscode-extension/webview/index.js`
- `chthonic-vscode-extension/src/extension.ts`

Verified:

- `cargo fmt --manifest-path core/Cargo.toml`
- `cargo build --manifest-path core/Cargo.toml`
- `bunx tsc --noEmit`
- `bun run build`
- `deepseek-core.exe chat --workspace probe "explain native plan"`
- `deepseek-core.exe rpc` via Bun subprocess JSON-RPC probe

Provider rung implemented 2026-07-09:

- `CHTHONIC_PROVIDER=auto` selects OpenAI when `OPENAI_API_KEY` exists, Anthropic when `ANTHROPIC_API_KEY` exists, otherwise deterministic offline mode.
- `CHTHONIC_PROVIDER=openai` / `codex` forces OpenAI Responses API SSE.
- `CHTHONIC_PROVIDER=anthropic` / `claude` forces Anthropic Messages API SSE.
- `OPENAI_MODEL` or `CHTHONIC_OPENAI_MODEL` override the OpenAI model.
- `ANTHROPIC_MODEL` or `CHTHONIC_ANTHROPIC_MODEL` override the Anthropic model.
- Forced provider mode fails before network when its required key is absent.

Provider verification:

- `cargo fmt --manifest-path core/Cargo.toml`
- `cargo build --manifest-path core/Cargo.toml`
- `bunx tsc --noEmit`
- `bun run build`
- `CHTHONIC_PROVIDER=deterministic deepseek-core.exe chat --workspace probe "provider rung"`
- `CHTHONIC_PROVIDER=deterministic deepseek-core.exe rpc` via Bun subprocess JSON-RPC probe
- `CHTHONIC_PROVIDER=openai` without `OPENAI_API_KEY` returns a provider initialization error before attempting a request

Critical-gap closure implemented 2026-07-09:

- Workspace Trust runtime guard added before sidecar spawn.
- Extension manifest declares workspace extension kind and unsupported untrusted workspaces.
- `initialize` RPC added for SecretStorage key injection from VS Code to Rust.
- `workspace/files` RPC added for a filtered workspace file feed.
- Rust agent now tracks indexed file count and includes it in chat context.
- `agent/status` RPC added for provider and workspace index state.
- `diff/apply` server notification path added; TypeScript bridge translates it to `vscode.WorkspaceEdit`.
- `chthonic.startTerminal` command alias added beside `chthonic.openTerminal`.

Critical-gap verification:

- `cargo fmt --manifest-path core/Cargo.toml`
- `cargo build --manifest-path core/Cargo.toml`
- `bunx tsc --noEmit`
- `bun run build`
- JSON-RPC probe: `initialize` + `workspace/files` + `agent/status` + `chat.stream`
- JSON-RPC probe: `/demo-edit C:/tmp/chthonic-demo.txt` emits `diff/apply`

Edit-plan and rollback rung implemented 2026-07-09:

- `/demo-edit` probe removed from the active path.
- `/plan-edit <file-uri-or-path>` deterministic probe emits `edit/plan`.
- `edit/confirm` applies a pending plan and emits `diff/apply`.
- `edit/reject` discards a pending plan.
- `edit/rollback` emits reverse `diff/apply` operations from an in-memory snapshot store.
- Edit ranges now use the nested contract shape: `range.start.line`, `range.start.character`, `range.end.line`, `range.end.character`.
- VS Code bridge asks the user to Apply or Reject on `edit/plan`.
- `chthonic.rollbackLastEdit` command sends `edit/rollback` for the latest applied plan.
- Minimal Rust and Bun test skeletons added.

Edit-plan verification:

- `cargo fmt --manifest-path core/Cargo.toml`
- `cargo test --manifest-path core/Cargo.toml`
- `bun test`
- `bun run build`
- JSON-RPC lifecycle probe: `/plan-edit <temp-file>` -> `edit/plan` -> `edit/confirm` -> `diff/apply` -> `edit/rollback` -> reverse `diff/apply`

Pseudoterminal rung implemented 2026-07-09:

- `chthonic-vscode-extension/src/terminal.ts` defines `ChthonicTerminal`.
- Each terminal spawns its own `deepseek-core.exe rpc` child process.
- Terminal startup sends `initialize` and `workspace/files` to the dedicated sidecar.
- Input lines are sent as `chat.stream` requests.
- `chat.chunk` notifications render directly into the terminal with CRLF normalization.
- Backspace handling and basic line editing are included.
- `/help` and `/undo` are handled in the terminal lane.
- `edit/plan` prompts Apply/Reject from the terminal lane.
- `diff/apply` notifications from the terminal lane are applied through `vscode.WorkspaceEdit`.
- Closing the terminal kills the dedicated sidecar process.

Pseudoterminal verification:

- `bunx tsc --noEmit`
- `bun run build`
- `bun test`
- `cargo test --manifest-path core/Cargo.toml`

## Non-Goals

- No Next.js.
- No shadcn/ui.
- No app-router web app inside the extension.
- No AI orchestration in TypeScript.
- No separate Node service.

*Adjustment recorded before continuation. This file is the gate artifact proving the end-state changed from web-app-in-extension to Rust-native local coding agent with a VS Code Insiders bridge.*

## Chthonic Deepcode Self-Visibility Surface

This section exists so Chthonic Deepcode can inspect its own work in progress before the next implementation pass.

### Current Product Identity

The product identity is **Chthonic Deepcode (DeepSeek)**, also named **Chthonic Depths** in the deeper project substrate. It is not generic "Chthonic Code."

Chthonic Deepcode is currently a Rust-native local coding agent with three working surfaces:

- standalone CLI: `deepseek-core.exe chat`
- VS Code sidebar: static webview -> TypeScript bridge -> `deepseek-core.exe rpc`
- VS Code terminal: pseudoterminal -> dedicated `deepseek-core.exe rpc`

The TypeScript extension is not the agent. It is the editor shell and safety adapter. The Rust binary is the agent.

### Current Architecture Map

Rust core:

- `chthonic-vscode-extension/core/src/main.rs` — CLI/RPC entrypoint selection.
- `chthonic-vscode-extension/core/src/protocol.rs` — JSON-RPC request/response primitives.
- `chthonic-vscode-extension/core/src/provider.rs` — deterministic, OpenAI Responses SSE, Anthropic Messages SSE providers.
- `chthonic-vscode-extension/core/src/provider.rs` — deterministic, DeepSeek Chat Completions SSE, OpenAI Responses SSE, Anthropic Messages SSE providers.
- `chthonic-vscode-extension/core/src/agent.rs` — provider config, injected keys, workspace file state, edit-plan state, session state.
- `chthonic-vscode-extension/core/src/rpc.rs` — RPC dispatch, chat streaming, initialize, workspace feed, edit plan, rollback.
- `chthonic-vscode-extension/core/src/cli.rs` — terminal-native `deepseek-core chat`.
- `chthonic-vscode-extension/core/src/edit_plan.rs` — plan, snapshot, confirm, reject, rollback store.
- `chthonic-vscode-extension/core/src/session.rs` — `%APPDATA%/Chthonic/DeepSeekCode/session.json` persistence.

VS Code bridge:

- `chthonic-vscode-extension/src/extension.ts` — activation, Trust guard, webview, main sidecar, SecretStorage, workspace feed, WorkspaceEdit application, rollback command.
- `chthonic-vscode-extension/src/terminal.ts` — dedicated pseudoterminal sidecar, terminal input loop, `/help`, `/undo`, terminal edit-plan flow.
- `chthonic-vscode-extension/webview/index.js` — static webview message bridge.
- `chthonic-vscode-extension/package.json` — command/view contributions, Trust metadata, workspace extension kind.

Tests:

- `chthonic-vscode-extension/core/src/edit_plan.rs` — Rust edit-plan unit tests.
- `chthonic-vscode-extension/tests/package-smoke.test.ts` — Bun manifest smoke test.

### Current Capability Ledger

Implemented:

- workspace Trust guard
- Rust CLI mode
- Rust JSON-RPC mode
- VS Code sidebar chat streaming
- VS Code pseudoterminal chat streaming
- SecretStorage-to-Rust key injection
- workspace file feed
- provider routing
- deterministic offline provider
- official DeepSeek API provider through bearer-auth Chat Completions SSE
- DeepSeek API pool integration with `DEEPSEEK_API_KEY` doctor/mock/load/verify support
- OpenAI Responses SSE provider
- Anthropic Messages SSE provider
- edit plan notification
- Apply/Reject confirmation flow
- `diff/apply` WorkspaceEdit application
- persistent rollback snapshots with integrity check
- Rust-owned workspace graph persisted to disk
- live workspace file watching via `workspace/fileChanged`
- snippet-guarded read-before-write edit plans
- write permission gate for edit confirmation
- provider-emitted deterministic edit plans through the normal `chat.stream` path
- live-provider structured JSON edit-plan parsing
- `agent/cancel` cancellation token for in-flight streams
- sidecar restart/backoff for sidebar and terminal sidecars
- `/undo` in terminal lane
- `Chthonic: Rollback Last Edit` command
- Rust-owned session persistence for conversation, active plans, workspace snapshot, provider, timestamp

Not yet implemented:

- provider-driven tool loop
- packaged release binary placement
- VS Code Insiders interactive E2E verification
- DeepSeek-style visual polish
- DeepSeek chat OAuth/session login bridge; distinct from developer API-key bearer auth and not yet wired into Chthonic
- Puter user-pays AI gateway provider lane; viable candidate for no-DeepSeek-key live probes, distinct from official DeepSeek API and chat-session login
- Moonshot/Kimi provider lane; not yet investigated or wired

### Active Protocol Surface

Client -> Rust requests:

- `core.ping`
- `initialize`
- `workspace/files`
- `agent/status`
- `agent/cancel`
- `chat.stream`
- `edit/confirm`
- `edit/reject`
- `edit/rollback`
- `core.shutdown`

Rust -> client notifications:

- `chat.chunk`
- `edit/plan`
- `diff/apply`
- `core.log`

Deterministic probes:

- `/plan-edit <file-uri-or-path>` emits an `edit/plan`.
- `/snippet-plan <file-uri-or-path>` emits a snippet-guarded `edit/plan`.
- `/undo` in the pseudoterminal sends `edit/rollback`.

### Architectural Inputs For Next Pass

Chthonic Deepcode should use these constraints before continuing:

- Keep Rust as the owner of agent behavior. Do not move planning, provider routing, context packing, or edit generation into TypeScript.
- Keep TypeScript as a VS Code bridge only.
- Prefer explicit JSON-RPC contracts over ad hoc string parsing.
- Preserve static webview and no framework dependency.
- Treat terminal, sidebar, and CLI as peers using the same Rust core.
- Treat edits as plan -> confirm -> apply -> rollback; no silent mutation.
- Keep env vars as CLI fallback, but VS Code secrets should flow through `initialize`.
- DeepSeek API support is mandatory. Prefer `CHTHONIC_PROVIDER=deepseek` and `DEEPSEEK_API_KEY` or `chthonic.deepseekKey`.
- Keep DeepSeek chat login/OAuth separate from developer API bearer authentication until a supported bridge is chosen.
- Treat DeepSeek chat login as mandatory to investigate before packaging, but do not invent OAuth endpoints, Google client IDs, token exchanges, or internal chat API routes.
- Any DeepSeek chat-session lane must start with a reproducible reconnaissance artifact: observed login endpoints, redirect/callback shape, token/cookie names without values, request headers, and chat stream endpoint shape.
- Do not bake scraped or unstable consumer-chat internals into the release path without a feature flag and a documented breakage boundary.
- Keep Windows 11 as the target platform unless a later plan explicitly widens scope.

### Next Candidate Rungs

1. DONE — Session persistence:
   - Rust-owned session log under `%APPDATA%/Chthonic/DeepSeekCode/session.json`.
   - Persists chat turns, active plan IDs, provider selection, workspace snapshot, and timestamp.

2. DONE — Persistent rollback store:
   - Move snapshots from memory to disk.
   - Include plan metadata and affected-file hashes.
   - Refuse rollback when current file hash diverges unexpectedly unless user confirms.

3. DONE — Workspace graph:
   - Replace flat file count with a Rust index of paths, extensions, modified times, and lightweight symbols.
   - Add `workspace/fileChanged` notifications from VS Code file watchers.

4. DONE — Real edit planning:
   - Provider prompt asks for structured edit plans.
   - Rust validates JSON plan shape.
   - VS Code applies only after confirmation.

5. DONE — Snippet-guarded edit substrate:
   - `core/src/snippet_store.rs` persists snippets under `%APPDATA%/Chthonic/DeepSeekCode/snippets/`.
   - `FileEdit.snippetId` binds edit confirmation to a prior read.
   - `EditPlan.requiredPermissions` declares required scopes.
   - `edit/confirm` checks permission policy and snippet file hash before rollback snapshot or `diff/apply`.

6. DONE — Cancellation and restart:
   - Add `agent/cancel`.
   - Add sidecar exit detection, status surfacing, and restart command/backoff in TypeScript.

7. Packaging:
   - Build release `deepseek-core.exe`.
   - Bundle Windows binary into the VSIX.
   - Prefer `win32-x64` platform packaging.

8. REQUIRED BEFORE PACKAGING — DeepSeek chat login/OAuth reconnaissance:
   - DeepSeek chat login exists at `https://chat.deepseek.com/` and supports ordinary consumer sign-in flows.
   - This is distinct from developer API usage, which currently works through API-key bearer auth in Chthonic.
   - The next step is not speculative implementation. It is evidence capture: identify whether DeepSeek exposes a stable callback, token exchange, session refresh, and chat streaming contract that Chthonic can legally and technically wrap.
   - Output artifact: `CLAUDEBASE/charts/deepseek-chat-login-recon.md`.
   - If a stable bridge exists, implement it as a separate provider lane: `CHTHONIC_PROVIDER=deepseek-chat`.
   - If only private web internals exist, keep the lane experimental and feature-gated.

9. Puter user-pays gateway provider:
   - Puter documents DeepSeek model access through Puter.js with a user-pays model and no developer DeepSeek API key.
   - This is a third lane: not official DeepSeek API-key auth and not DeepSeek consumer chat-session login.
   - Viable for live structured-plan probes if Chthonic can obtain a Puter auth token and keep Rust as provider owner.
   - Direct TypeScript-side AI calls are disallowed; any implementation must be a Rust provider or a tightly bounded Rust-owned bridge.

10. Moonshot/Kimi provider:
   - Candidate remaining frontier provider lane.
   - Must be investigated against current official Moonshot/Kimi API docs before implementation.
   - Same rule as all providers: Rust owns requests, streaming, structured plan parsing, snippets, permissions, and rollback.

### DeepSeek Chat Login And API Auth Recheck 2026-07-09

- Reviewed `https://deepseekai.guide/guides/deepseek-login/`.
- Rechecked official DeepSeek API docs on 2026-07-09.
- The guide is an independent resource and not affiliated with DeepSeek.
- It describes user login surfaces: web chat, mobile app, and developer platform.
- It confirms Google/Apple sign-in exists for the consumer chat/account surface.
- That consumer chat login surface is not the same contract as developer API bearer authentication.
- Official DeepSeek API docs continue to describe API access as bearer authentication with an API key created in the platform console.
- Chthonic must not conflate chat-session OAuth/login with API-key bearer auth. If both are supported, they should be modeled as separate auth/provider lanes.
- Official DeepSeek API docs do not currently publish a third-party OAuth client registration flow, authorization endpoint, token endpoint, scopes, redirect URI rules, or refresh-token contract for coding-agent integrations.
- Therefore the immediate work is a reconnaissance artifact, not blind OAuth implementation.

### Puter Gateway Recheck 2026-07-09

- Reviewed `https://developer.puter.com/tutorials/free-unlimited-deepseek-api/#getting-started`.
- Puter offers DeepSeek model access through `puter.ai.chat()` and describes a user-pays model where users cover their own AI usage.
- The tutorial targets Puter.js via NPM or browser CDN and lists supported DeepSeek models such as `deepseek/deepseek-v4-flash`, `deepseek/deepseek-v4-pro`, and DeepSeek R1/V3 variants.
- Puter docs state Puter.js supports Node.js and can initialize with a Puter auth token; if browser access exists, a CLI can obtain a token through web-based login.
- Chthonic may use this as an experimental Puter gateway provider only if the Rust core remains the owner of chat streaming, plan parsing, snippet guarding, and edit confirmation.
- Do not move provider calls into the VS Code TypeScript bridge merely because Puter.js is JavaScript-first.

### Snippet Guard And Permission Gate Implemented 2026-07-09

- `core/src/snippet_store.rs` adds persistent snippets with `snippetId`, URI, range, captured content, source file hash, and timestamp.
- `core/src/permissions.rs` adds `Permission` and `PermissionPolicy`.
- `EditPlan` now carries `requiredPermissions`.
- `FileEdit` now carries optional `snippetId`.
- `CHTHONIC_ALLOW_FILE_WRITES=false` denies write plans before confirmation can apply.
- `/snippet-plan <file>` creates a read-before-write guarded edit plan.
- `edit/confirm` returns a JSON-RPC error for permission denial or snippet hash mismatch.

Snippet/permission verification:

- `cargo fmt --manifest-path core/Cargo.toml`
- `cargo fmt --manifest-path core/Cargo.toml -- --check`
- `cargo test --manifest-path core/Cargo.toml`
- `bun run build`
- JSON-RPC probe: `/snippet-plan <temp-file>` -> `edit/plan` with `requiredPermissions:["writeFile"]` -> `edit/confirm` -> `diff/apply`
- JSON-RPC probe: `CHTHONIC_ALLOW_FILE_WRITES=false` rejects `edit/confirm`
- JSON-RPC probe: mutate file between `edit/plan` and `edit/confirm`; confirmation rejects with `snippet hash mismatch`

### Provider-Generated Edit Plans Implemented 2026-07-09

- `provider.rs` now emits typed provider responses: streamed token chunks or structured `EditPlan` proposals.
- Deterministic provider emits an edit plan for `suggest an edit to <file-uri-or-path>`.
- Real network providers now include edit-plan JSON instructions in their system/developer prompts and parse valid `EditPlan` JSON from accumulated streamed text.
- `agent.stream_chat` registers provider plans by checking permissions, creating snippets for each edit, and inserting the pending plan.
- `rpc.rs` emits provider-generated plans as `edit/plan` notifications from the normal `chat.stream` path.
- CLI mode prints provider plan summaries when a provider proposes edits.
- Native tool/function calling remains future work under the provider-driven tool loop rung.

Provider-plan verification:

- `cargo fmt --manifest-path core/Cargo.toml`
- `cargo test --manifest-path core/Cargo.toml`
- `bun run build`
- Rust parser tests cover raw JSON, fenced JSON, missing plans, and invalid plan shape.
- JSON-RPC probe: `chat.stream` with `suggest an edit to <temp-file>` emits `chat.chunk`, then `edit/plan` with `requiredPermissions:["writeFile"]` and a registered `snippetId`, then `edit/confirm` emits `diff/apply`
- JSON-RPC probe: same prompt with `CHTHONIC_ALLOW_FILE_WRITES=false` emits a clear write-permission denial and no `edit/plan`

### DeepSeek API And Session Rung Implemented 2026-07-09

- `CHTHONIC_PROVIDER=deepseek` selects the official DeepSeek API provider.
- `CHTHONIC_PROVIDER=auto` now prefers DeepSeek when `DEEPSEEK_API_KEY` or injected `chthonic.deepseekKey` exists.
- DeepSeek provider uses bearer auth and `https://api.deepseek.com/chat/completions`.
- `scripts/api_pool.ps1` now treats `DEEPSEEK_API_KEY` as a first-class local pool key.
- `api_manager.ps1 -VerifyDeepSeek` validates the key against `https://api.deepseek.com/models` without printing secrets.
- Default DeepSeek model is `deepseek-chat`; override with `DEEPSEEK_MODEL`, `CHTHONIC_DEEPSEEK_MODEL`, or VS Code setting `chthonic.deepseekModel`.
- VS Code injects `chthonic.deepseekKey` through `initialize`.
- Rust session persistence writes JSON to `%APPDATA%/Chthonic/DeepSeekCode/session.json`.
- `DEEPSEEK_CODE_SESSION_PATH` can override the session path for tests/probes.
- `agent/status` reports `conversationLength` and `sessionLoaded`.
- DeepSeek chat login/OAuth and developer API-key auth are separate lanes; Chthonic currently implements only the API-key bearer lane.

DeepSeek/session verification:

- `cargo fmt --manifest-path core/Cargo.toml`
- `cargo test --manifest-path core/Cargo.toml`
- `bun test`
- `bunx tsc --noEmit`
- `bun run build`
- two-process JSON-RPC probe confirms session restore from isolated `DEEPSEEK_CODE_SESSION_PATH`
- `CHTHONIC_PROVIDER=deepseek` without `DEEPSEEK_API_KEY` fails before network with a clear initialization error
- API pool probe: `api_manager.ps1 -VerifyDeepSeek` loads `DEEPSEEK_API_KEY` and confirms DeepSeek models are reachable.
- Live edit-plan probe reaches DeepSeek but currently stops at `402 Payment Required: Insufficient Balance`; this proves auth/routing and identifies billing as the live-stream blocker.

### DeepSeek Provider Status Report 2026-07-09

- Official DeepSeek developer API lane is proven viable for Chthonic.
- Local key convention is settled: `DEEPSEEK_API_KEY` in `~/.chthonic/api_pool.json`, loaded by `scripts/api_pool.ps1`.
- `api_pool.ps1 -Mock` validates local pool shape without network calls.
- `api_manager.ps1 -VerifyDeepSeek` validates bearer auth and model-list reachability without exposing the key.
- `bun run probe:live-deepseek-plan` successfully reaches the DeepSeek provider path but cannot complete a chat stream while the platform account has insufficient balance.
- Development may continue safely against deterministic/mock providers because the remaining blocker is external account balance, not Chthonic provider wiring.
- Once balance is available, rerun `bun run probe:live-deepseek-plan` to verify live structured edit-plan streaming end to end.

### Cancellation And Restart Implemented 2026-07-09

- Rust `Agent` owns a shared cancellation token.
- `agent/cancel` flips the token and returns `{ ok: true, cancelled: true }`.
- `chat.stream` runs on a Rust worker thread so the stdio RPC loop can continue reading `agent/cancel` while providers stream.
- Deterministic and live provider loops check the cancellation token and abort with `chat stream cancelled`.
- `agent/status` reports `cancelled`.
- VS Code sidebar exposes `Chthonic: Cancel Current Request` and `Chthonic: Restart Agent`.
- Sidebar sidecar detects unexpected exits, rejects pending RPCs, restarts with exponential backoff, and surfaces status through a status bar item.
- Sidebar webview includes a Stop button that sends `agent/cancel`.
- Terminal sidecar sends `agent/cancel` on Ctrl+C and restarts its dedicated sidecar with exponential backoff after unexpected exits.

Cancellation/restart verification:

- `cargo fmt --manifest-path core/Cargo.toml`
- `cargo test --manifest-path core/Cargo.toml`
- `bun test`
- `bunx tsc --noEmit`
- `bun run build`
- JSON-RPC probe: deterministic `chat.stream` -> first `chat.chunk` -> `agent/cancel` -> cancel ack -> `chat stream cancelled`

### Current Verification Commands

Run from `chthonic-vscode-extension/`:

```powershell
cargo fmt --manifest-path core/Cargo.toml
cargo test --manifest-path core/Cargo.toml
bun test
bunx tsc --noEmit
bun run build
```

Manual IDE check:

```powershell
code-insiders . --extensionDevelopmentPath=$PWD
```

Then verify:

- `Chthonic: Open Chat`
- `Chthonic: Open Terminal Agent`
- terminal prompt accepts `explain native plan`
- terminal `/plan-edit <file>` prompts Apply/Reject
- terminal `/undo` reverts the last applied terminal plan
- sidebar chat streams via `chat.chunk`
