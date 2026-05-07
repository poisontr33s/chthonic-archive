<!--
================================================================================
SEMANTIC IDENTITY (Anchor & Signal Protocol)
================================================================================
@SID:           DOC_CLAUDE_DESIGN_FAF_BRIDGE
@Type:          Operational Architecture
@Context:       Claude Design / VS Code / Claude Code token-boundary bridge
@Created:       2026-05-07
@UpdateFrequency: Medium while Claude Design remains in research preview
================================================================================
-->

# Claude Design FAF Bridge

## Decision

Do not embed `claude.ai/design` directly inside a VS Code webview. Treat Claude Design as the upstream design-generation surface, then use exported artifacts as the function input to a local VS Code "framed design" surface.

The bridge is:

```text
Claude Design export/handoff
  -> local artifact intake
  -> framed VS Code preview + contract extraction
  -> compact MCP/tool handoff to Claude Code or another implementation agent
```

This separates design exploration from Claude Code tokenomics. Claude Design still uses the user's Claude subscription limits, but VS Code bridge work is local and Claude Code is only engaged against a compact implementation contract.
Update 2026-05-07: Claude Design is now documented as metered independently from chat and Claude Code, with its own allowances and weekly limits. The bridge therefore treats Design exploration as a separate allowance lane, then keeps implementation traffic compact before it enters Claude Code.

## Current Official Surface Facts

Verified 2026-05-07:

- Anthropic launched Claude Design on 2026-04-17 as an Anthropic Labs product at `claude.ai/design`.
- Claude Design is a research preview for Claude Pro, Max, Team, and Enterprise subscribers.
- Claude Design usage is metered separately from chat and Claude Code, with its own usage tracking, allowances, and weekly limits.
- Claude Design supports exports as an internal URL, folder, Canva, PDF, PPTX, and standalone HTML files.
- Claude Design supports a handoff bundle for Claude Code.
- Claude Code for VS Code is the official VS Code extension surface for coding workflows. It supports editor integration, subagents, custom slash commands, and MCP.
- The Claude Agent SDK is the renamed Claude Code SDK. It uses API-key authentication for custom products; Anthropic documentation says third-party products generally cannot offer `claude.ai` login or rate limits without approval.

Sources:

- `https://www.anthropic.com/news/claude-design-anthropic-labs`
- `https://support.claude.com/en/articles/14667344-claude-design-subscription-usage-and-pricing`
- `https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code`
- `https://code.claude.com/docs/en/agent-sdk/overview`
- `https://platform.claude.com/docs/en/agent-sdk/mcp`
- `https://code.visualstudio.com/api/extension-guides/webview`

FAF prototype frame: [`FAF_CLAUDE_DESIGN_TOKEN_BOUNDARY_PROTOTYPE.md`](../reference/FAF_CLAUDE_DESIGN_TOKEN_BOUNDARY_PROTOTYPE.md)

## Implementation Status

`scripts/claude-design-intake.ts` exists and is the first executable probe for this bridge. It performs the local, no-model first slice:

```text
export folder -> manifest.json + tokens.json + design_contract.md + handoff_prompt.md + gate_ledger.jsonl
```

Contract extraction is intentionally integrated into `scripts/claude-design-intake.ts` for the first implementation. `scripts/claude-design-contract.ts` does not exist today and should only be created later if contract extraction becomes large enough to justify a separate tool.

The lightweight VS Code Insiders surface is implemented inside `extensions/chthonic-archive`:

- View id: `chthonic.designFrameView`
- Command: `chthonic.openClaudeDesignFrame`
- Webview assets: `extensions/chthonic-archive/media/views/design-frame/`
- Provider: `extensions/chthonic-archive/src/design/designFrameView.ts`

It reads generated frame artifacts and renders the Preview / Tokens / Gates / Handoff inspector locally. If a selected export has not been compiled yet, the pane can launch `bun run design:intake` in a VS Code terminal.

## Live Embed Gate

`claude.ai/design` should be considered non-embeddable in VS Code.

Observed HEAD request on 2026-05-07 returned:

```text
HTTP 403 Cloudflare challenge
X-Frame-Options: SAMEORIGIN
Content-Security-Policy: default-src 'none'; ... frame-src 'self' https://challenges.cloudflare.com blob:
Cross-Origin-Embedder-Policy: require-corp
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Resource-Policy: same-origin
```

That makes a direct webview iframe/proxy approach brittle, likely blocked, and not a sound architecture. It also risks drifting into unsupported auth/session behavior.

## FAF: Framing As Function

The frame is the product boundary, not a decoration.

```text
F(export_bundle, repo_context, frame_rules) -> design_contract
```

Inputs:

- `export_bundle`: standalone HTML/folder/PDF/PPTX/assets/handoff from Claude Design.
- `repo_context`: design system files, existing components, screenshots, package metadata.
- `frame_rules`: local constraints such as FA4 structural integrity, FA5 visual integrity, responsive breakpoints, accessibility gates, and token-budget caps.

Output:

- `design_contract.md`: compact implementation instructions.
- `tokens.json`: extracted colors, spacing, typography, assets, component hints.
- `manifest.json`: provenance, source paths, export timestamps, checksums.
- `screenshots/`: local preview captures for visual diff.
- optional `mcp_index.json`: small, queryable design facts for Claude Code.

## Proposed Local Workflow

1. In Claude Design, explore visually until the design is good enough.
2. Export as standalone HTML or folder, plus the Claude Code handoff bundle when available.
3. Place the export under:

```text
artifacts/claude-design/<project-slug>/<export-timestamp>/
```

4. Run the local intake command:

```text
bun run design:intake artifacts/claude-design/<project-slug>/<export-timestamp>
```

5. Intake writes:

```text
artifacts/claude-design/<project-slug>/<export-timestamp>/frame/
  manifest.json
  design_contract.md
  tokens.json
  screenshots/
```

6. Open the framed preview with `Chthonic: Open Claude Design Frame`.
7. When implementation begins, Claude Code receives only `design_contract.md`, selected screenshots, and exact file targets.

## VS Code Surface

Add a new optional pane to `extensions/chthonic-archive`:

- View id: `chthonic.designFrameView`
- Command: `chthonic.openClaudeDesignFrame`
- Input: local export folder path
- Rendering mode:
  - preferred: render exported standalone HTML from local files with strict CSP
  - fallback: render screenshot/contact-sheet preview if the export uses incompatible scripts
- Actions:
  - refresh export
  - capture screenshot
  - extract tokens
  - generate implementation contract
  - copy compact Claude Code handoff prompt

This reuses the existing extension webview pattern instead of creating a new extension.

## MCP Boundary

Expose design facts through a read-only MCP server rather than dumping the full artifact into Claude Code.

Candidate tools:

```text
list_design_exports(project?)
get_design_manifest(export_id)
get_design_contract(export_id)
get_design_tokens(export_id)
get_design_asset(export_id, asset_path)
get_design_screenshot(export_id, viewport)
compare_impl_to_design(export_id, url_or_path)
```

Tool output must be small by default. Large artifacts require explicit path selection.

## Token Boundary

Claude Design lane:

- Used for ideation, visual editing, and design-system-aware exploration.
- Consumes Claude subscription limits and optional extra usage.
- Does not consume Claude Code agent turns until handoff.

Local FAF lane:

- Parses exports.
- Produces screenshots and manifests.
- Extracts tokens and contracts.
- Runs local visual diffs.
- No Anthropic API or Claude Code usage required.

Claude Code lane:

- Used only for implementation.
- Receives compact contracts, not raw exploratory history.
- Reads exact repo files and exact design artifacts through MCP/path references.

Agent SDK lane:

- Optional only if building a custom automation product.
- Uses `ANTHROPIC_API_KEY` / API billing, not `claude.ai` subscription rate limits, unless Anthropic has explicitly approved otherwise.

## First Vertical Slice

Implement the first slice without calling any model:

1. `scripts/claude-design-intake.ts` (implemented first slice)
   - validate export folder
   - detect `index.html`, assets, screenshots, handoff files
   - write `manifest.json`
   - extract obvious CSS tokens into `tokens.json`
   - generate `design_contract.md`
   - generate `handoff_prompt.md`
   - write `gate_ledger.jsonl`

2. `extensions/chthonic-archive` (implemented lightweight first slice)
   - add `chthonic.designFrameView`
   - render selected local export or generated screenshot contact sheet
   - show token summary and contract path

3. Optional MCP (future)
   - add read-only tools over the generated `frame/` folder

Success condition:

```text
Claude Design export can be viewed, indexed, and converted into a compact
implementation contract in VS Code without launching Claude Code or using the
Claude Agent SDK.
```

## Non-Goals

- No live embedding of `claude.ai/design`.
- No scraping authenticated Claude sessions.
- No reuse of Claude Code OAuth tokens.
- No third-party wrapper pretending to be Claude Design.
- No automatic implementation from raw visual export without a compact contract.

## Verdict

The way through is not a cloned Claude Design UI. The reliable architecture is a framed local design artifact lane: Claude Design produces the rich visual output, FAF converts that output into a local function boundary, and Claude Code only sees a compact implementation contract when it is time to build.
