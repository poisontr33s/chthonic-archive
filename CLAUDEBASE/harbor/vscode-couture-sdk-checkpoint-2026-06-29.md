# The Extreme Haute Couture — Movement 1

Checkpoint date: 2026-06-29

Spelling canon: `Haute Couture`, not `Haute Coutore`.

This checkpoint covers one lane only: VS Code Insiders substrate design, marketplace-grade extension infrastructure, and the Bun-managed official SDK baseline for that work. Do not merge unrelated archaeology, mailbox, model, game, or polyrepo lanes into this continuation.

## Current Anchor

Branch: `main`

Remote: `origin/main`

Clean tracked state at checkpoint time.

Recent commits:

```text
69cd5b29 Add Bun SDK catalog refresh
9fb318fb Add Bun SDK probe harness
cde594ac chore: checkpoint workspace maintenance
6270587f Add Chthonic Mica substrate
195a9f99 docs(CLAUDEBASE): expand manifest to 11 chambers; add mdseal project assessment
```

## Completed In This Lane

The VS Code Insiders Mica substrate exists and has a reversible patch script:

- `designs/chthonic-mica.cjs`
- `designs/vibrancy-obsidian.css`
- `scripts/mica-substrate.ps1`

The SDK baseline exists and is Bun-first:

- `sdk-catalog.toml`
- `scripts/sdk-catalog.ts`
- `scripts/sdk-probe.ts`
- `manifest/sdk-probes/latest.json`

The one-shot SDK command now exists:

```bash
bun run sdk:latest
```

It refreshes the cataloged SDKs to `latest`, then regenerates the probe report.

Dry run:

```bash
bun run sdk:latest:dry
```

Inspection:

```bash
bun run sdk:list
bun run sdk:check
bun run sdk:probe:write
```

## Cataloged SDK Surface

Runtime dependencies:

- `@modelcontextprotocol/sdk`
- `openai`
- `@openai/agents`
- `@openai/codex-sdk`
- `@anthropic-ai/sdk`
- `@anthropic-ai/claude-agent-sdk`
- `zod`

Development dependencies:

- `@vscode/dts`
- `@vscode/test-electron`
- `@vscode/test-web`
- `@vscode/test-cli`
- `@vscode/vsce`

Current probe verdicts:

- MCP TypeScript SDK: native
- OpenAI, OpenAI Agents, Codex SDK, Anthropic SDK, Claude Agent SDK: Bun-compatible imports
- VS Code test tooling: Bun-compatible or CLI-only as expected
- VSCE and DTS: CLI-oriented, usable from Bun scripts

## Holdups

1. SDK installation is not extension architecture yet.
   The SDKs are installed, cataloged, and import-probed. The next step is real smoke tests tied to our use cases: VS Code extension host, MCP server/client, Codex/Claude/OpenAI agent calls, and VSIX packaging.

2. VS Code workbench couture cannot be solved by ordinary extension APIs alone.
   Normal marketplace extensions can theme, contribute UI, ship webviews, use icons, and package assets. They cannot fully own Electron window vibrancy, renderer shell glass, or workbench chrome without substrate patching or a separate shell strategy.

3. Insiders updates will overwrite workbench substrate patches.
   `scripts/mica-substrate.ps1` must become a repeatable lifecycle command: detect current Insiders build, patch, verify, rollback, and reapply after update.

4. Bun-native is viable, but not every upstream tool is Bun-native in spirit.
   Some tools are CLI wrappers or Node-shaped packages. Our rule is Bun orchestration first, with Node-shaped internals tolerated only when they are inside official package surfaces.

5. Bun blocked lifecycle scripts remain quarantined.
   Current blocked packages:
   - `@github/keytar`
   - `@playwright/browser-chromium`
   - `@vscode/vsce-sign`

   Do not run `bun pm trust` globally. Trust only a named package when a concrete test requires it and the effect is understood.

6. Missing likely next VS Code package candidates need deliberate admission.
   Candidates not yet in `sdk-catalog.toml`:
   - `@types/vscode`, pinned to the extension engine target rather than blindly floated
   - `@vscode/l10n`, if marketplace polish needs localization scaffolding
   - a bundling strategy if the extension package needs compiled output beyond Bun-run scripts

## Continuation Structure

Work in this order. Do not branch into adjacent lanes until the current item has a committed artifact.

1. Substrate lifecycle
   Turn `scripts/mica-substrate.ps1` into a full command surface:
   - `-Status`
   - `-Apply`
   - `-Verify`
   - `-Restore`
   - `-ReapplyLatest`

   Success condition: one command can prove whether current VS Code Insiders is patched, clean, or restorable.

2. Extension host skeleton
   Build or identify the marketplace extension package that will own:
   - theme contributions
   - icon/product icon contributions
   - settings schema
   - commands
   - preview assets
   - test entrypoints

   Success condition: Bun can package a VSIX through the cataloged VS Code tooling.

3. Visual verification harness
   Automate screenshot capture and comparison for:
   - patched Insiders workbench
   - extension theme/icon state
   - high contrast and transparency failure modes

   Success condition: visual regressions become a deterministic local command, not manual squinting.

4. SDK smoke tests
   Add focused tests for each SDK lane:
   - VS Code test Electron launches extension tests
   - VS Code test web launches a web-extension smoke if relevant
   - MCP server/client loopback works locally
   - OpenAI/Codex/Claude SDK imports and non-secret dry construction work

   Success condition: `bun run sdk:probe:write` evolves from import probe to capability probe without leaking secrets.

5. Couture system contract
   Formalize the design system as tokens plus generated artifacts:
   - material tokens
   - glyph/icon atlas
   - workbench substrate CSS
   - VS Code theme JSON
   - preview renders

   Success condition: hand editing becomes an input stage, not the whole production method.

6. Marketplace overkill package
   Build the publishable surface:
   - VSIX
   - README
   - gallery images
   - settings docs
   - changelog
   - license and third-party notices

   Success condition: `bun run` can rebuild and package the release candidate from source.

## Working Rule

If a step repeats twice by hand, convert it into a Bun or PowerShell command before moving on. If a result can be checked deterministically, add a probe or CI gate. If a task requires taste judgment, preserve it as a designed artifact and automate only the validation around it.

The point is not to make more scaffolding. The point is to make the couture workbench system hard to lose, hard to misapply, and easy to push further.

## Movement 2 Seed

Movement 2 is the Rust port investigation.

Terminology boundary:

- Electron is conventionally JavaScript/TypeScript in the main process, with Chromium renderers and Node integration.
- Rust can be attached to Electron through a native Node-API addon, a sidecar process, or a WebAssembly/native service boundary.
- A Rust-first desktop shell is usually Tauri/Wry rather than Electron.

Preferred direction:

1. Keep Movement 1 focused on VS Code Insiders substrate and the marketplace-safe extension package.
2. After Movement 1 can apply, verify, restore, and package deterministically, start Movement 2 as a separate Rust port.
3. For an Electron-compatible Rust port, prototype a thin Electron shell with a Rust core through Node-API or a sidecar process.
4. If the goal becomes Rust-native desktop instead of Electron compatibility, evaluate Tauri/Wry separately and do not call that Electron.

Working sentence:

The Extreme Haute Couture — Movement 1 owns the VS Code workbench/substrate couture system. Movement 2 explores the Rust-backed desktop port without collapsing the official marketplace extension and the local patcher into one unstable artifact.
