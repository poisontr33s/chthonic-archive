<!--
@SID:           REF_FAF_CLAUDE_DESIGN_TOKEN_BOUNDARY_PROTOTYPE_V1
@Type:          FAF Application - Claude Design / Claude Code token boundary prototype
@Context:       Frontend-first design artifact bridge for low-backend / scarce-token operation
@References:    FAF_FRAMING_AS_FUNCTION_METHODOLOGY.md, FAF_CHTHONIC_WEBVIEW_HMR.md, ../ops/CLAUDE_DESIGN_FAF_BRIDGE.md
@Filed:         2026-05-07
-->

# FAF Application: Claude Design Token Boundary Prototype

**Version:** v0.1  
**Status:** Research-backed prototype frame  
**Primary challenge:** Turn Claude Design output into a local, frontend-first implementation surface without spending Claude Code tokens until the implementation handoff is compact and explicit.

---

## 0. Decision

The prototype should not clone or embed the live `claude.ai/design` product.

The prototype should be a **Design Frame**:

```text
Claude Design export
  -> local export folder
  -> local frame manifest
  -> VS Code / browser frontend preview
  -> compact implementation contract
  -> optional Claude Code handoff
```

This uses the now-confirmed separation between Claude Design usage and Claude Code/chat usage as the load-bearing boundary.

---

## 1. Current Factual Ground

Verified 2026-05-07 from Anthropic / Claude official sources:

| Topic | Ground |
|-------|--------|
| Claude Design metering | Claude Design is priced and metered independently from the rest of Claude. It has separate usage tracking, allowances, and weekly subscription limits alongside chat or Claude Code limits. |
| Claude Design allowance cadence | Individual and Team/Enterprise seat allowances reset weekly. Extra usage is available for purchase. |
| Claude Design tracking caveat | Because Claude Design is an Anthropic Labs release, it does not yet support audit logs or usage tracking, while Design activity itself is still metered separately from chat and Claude Code. |
| Claude Design exports | Claude Design can export/share as internal URL, folder, Canva, PDF, PPTX, or standalone HTML. |
| Claude Design handoff | When ready to build, Claude Design packages a handoff bundle for Claude Code. |
| Claude Code cost model | Claude Code charges by token consumption for API usage; Pro/Max subscribers have usage included in subscription, and API/session cost figures are mainly relevant for API users. |
| Claude Code usage mitigation | Claude Code docs recommend small context, `/clear`, `/compact`, model selection, reduced MCP overhead, and hooks/skills to preprocess data before Claude sees it. |
| Claude Code login model | How usage is metered depends on sign-in: Enterprise seat usage pool vs API key pay-as-you-go. |
| Agent SDK boundary | Claude Agent SDK is for custom applications/automation and uses API-key/provider authentication; it should not be treated as a way to spend `claude.ai` subscription allowances unless Anthropic has explicitly approved that product path. |
| Live embed viability | `claude.ai/design` is not a valid VS Code iframe target under the observed Cloudflare challenge, `X-Frame-Options: SAMEORIGIN`, and restrictive CSP recorded in `docs/ops/CLAUDE_DESIGN_FAF_BRIDGE.md`. |

Primary sources:

- `https://support.claude.com/en/articles/14667344-claude-design-subscription-usage-and-pricing`
- `https://www.anthropic.com/news/claude-design-anthropic-labs`
- `https://code.claude.com/docs/en/costs`
- `https://support.claude.com/en/articles/14552983-models-usage-and-limits-in-claude-code`
- `https://code.claude.com/docs/en/agent-sdk/overview`

---

## 2. Retargeting Declaration

The base FAF challenge:

> Every surfaced impossibility must become a gate.

This application retargets it to:

> **Can a Claude Design export become a local, previewable, contract-producing frontend artifact that preserves design intent and delays Claude Code token usage until the build request is small?**

The host is the local repo + VS Code webview/frontend.  
The foreign capability is Claude Design output.  
The membrane is the export intake contract.  
The ledger is the manifest + design contract.  
The impossible-currently boundary is live embedding or unauthenticated product integration.

---

## 3. False Success Ban

The prototype is **not** admitted because:

- Claude Design exists.
- A design export folder exists.
- `index.html` opens in a browser.
- A screenshot was saved.
- Claude Design can generate a Claude Code handoff.
- A VS Code webview can render local HTML.
- A prompt says "implement this design."

Those facts create candidate gates. They do not admit the bridge.

A valid prototype is admitted only when:

```text
1. A local export folder is detected.
2. The export is classified without using Claude Code.
3. A manifest records provenance and export structure.
4. A frontend preview renders or degrades honestly.
5. A compact design_contract.md is generated locally.
6. A handoff prompt references only compact artifacts and exact paths.
7. The user can hand the artifact to Codex/frontend work without needing backend or extra Claude Code context.
```

---

## 4. Capability Ladder

| Level | Name | Meaning |
|-------|------|---------|
| L0 | Export discoverable | A Claude Design export or handoff folder exists locally. |
| L1 | Export classifiable | Intake identifies HTML/folder/PDF/PPTX/assets/handoff files and records them. |
| L2 | Previewable | A local frontend/webview can display the export, screenshot sheet, or honest degraded view. |
| L3 | Contracted | Local tooling emits `design_contract.md`, `tokens.json`, and `manifest.json`. |
| L4 | Token-bound | Handoff prompt references compact artifacts only; no raw export dump or conversation history. |
| L5 | Implementation-ready | Codex/Claude Code can implement from the contract with exact target files, breakpoints, assets, and acceptance checks. |

No gate may skip levels silently.

---

## 5. Prototype Shape: Design Frame Zero

**Name:** `Design Frame Zero`  
**Type:** frontend-first local artifact browser  
**Backend requirement:** none for the first prototype  
**Preferred surface:** VS Code webview inside `extensions/chthonic-archive`  
**Fallback surface:** static browser HTML under `artifacts/claude-design/_prototype/`

Implementation note: the first VS Code surface is implemented as `chthonic.designFrameView`, opened by `Chthonic: Open Claude Design Frame`.

### 5.1 Folder Contract

```text
artifacts/claude-design/<project-slug>/<export-timestamp>/
  source/
    index.html              # if exported standalone HTML/folder
    assets/                 # optional
    handoff.md              # optional Claude Code handoff
    *.pdf | *.pptx          # optional
  frame/
    manifest.json
    tokens.json
    design_contract.md
    handoff_prompt.md
    screenshots/
      desktop.png
      mobile.png
      contact-sheet.png
```

### 5.2 Frontend Panels

The frontend should have four dense, utilitarian panels:

| Panel | Purpose |
|-------|---------|
| Preview | Render local export if safe; otherwise show screenshot/contact sheet. |
| Tokens | Colors, typography, spacing, radius, shadows, assets, component hints. |
| Gates | L0-L5 status with evidence paths and blocked boundaries. |
| Handoff | Copyable compact prompt for Codex/Claude Code implementation. |

No chat surface is needed in the first prototype.

### 5.3 Visual Behavior

The prototype should feel like a working inspector, not a landing page:

- left rail: export selector and gate status;
- center: preview iframe/screenshot;
- right rail: tokens, contract summary, handoff prompt;
- bottom strip: manifest evidence and blocked boundaries;
- clear badges for `admitted`, `blocked_not_closed`, and `degraded`.

### 5.4 Tool Status

`scripts/claude-design-intake.ts` is implemented as the first local probe and compiler. It owns the first-slice contract extraction path:

```text
input export folder
  -> frame/manifest.json
  -> frame/tokens.json
  -> frame/design_contract.md
  -> frame/handoff_prompt.md
  -> frame/gate_ledger.jsonl
```

`scripts/claude-design-contract.ts` is not a current tool. It is a reserved future split only if contract extraction grows beyond the intake script's scope. Until then, the intake script remains the single source for C2, C4, and C5.

---

## 6. Data Contracts

### 6.1 `manifest.json`

```json
{
  "artifact_type": "claude_design_frame_manifest",
  "schema_version": 1,
  "export_id": "project-slug/2026-05-07T000000Z",
  "source_root": "artifacts/claude-design/project-slug/2026-05-07T000000Z/source",
  "frame_root": "artifacts/claude-design/project-slug/2026-05-07T000000Z/frame",
  "detected": {
    "html": true,
    "assets": true,
    "pdf": false,
    "pptx": false,
    "handoff": true
  },
  "levels": {
    "L0": "admitted",
    "L1": "admitted",
    "L2": "blocked_not_closed",
    "L3": "open",
    "L4": "open",
    "L5": "open"
  },
  "blocked_boundaries": [
    {
      "artifact_type": "impossible_currently_boundary",
      "gate": "preview/live_claude_design_embed",
      "claim": "Render live claude.ai/design in VS Code",
      "observed_failure": "X-Frame-Options/CSP/auth boundary",
      "minimum_condition_to_reopen": "Official Anthropic embeddable Design API or approved integration surface",
      "status": "blocked_not_closed"
    }
  ],
  "sources": [
    "https://support.claude.com/en/articles/14667344-claude-design-subscription-usage-and-pricing",
    "https://www.anthropic.com/news/claude-design-anthropic-labs"
  ]
}
```

### 6.2 `tokens.json`

```json
{
  "artifact_type": "claude_design_tokens",
  "schema_version": 1,
  "colors": [
    { "name": "background", "value": "#0f172a", "source": "css" }
  ],
  "typography": [
    { "role": "heading", "family": "Inter", "weight": 700, "source": "css" }
  ],
  "spacing": [
    { "name": "card-gap", "value": "16px", "source": "css" }
  ],
  "assets": [
    { "path": "source/assets/hero.png", "role": "hero" }
  ],
  "unknowns": [
    "Component intent not inferable from static export alone"
  ]
}
```

### 6.3 `design_contract.md`

Minimum sections:

```markdown
# Design Contract

## Source
- Export root:
- Handoff source:
- Screenshots:

## Implementation Target
- App:
- Route/component:
- Files expected to change:

## Visual Requirements
- Layout:
- Breakpoints:
- Colors:
- Typography:
- Assets:

## Interaction Requirements
- States:
- Inputs:
- Empty/loading/error:

## Acceptance Checks
- Desktop screenshot:
- Mobile screenshot:
- No overlapping text:
- Contract tokens matched:

## Token Boundary
- Do not paste raw export into Claude Code.
- Use this contract plus selected screenshots only.
```

### 6.4 `handoff_prompt.md`

```markdown
Implement the design contract at:
artifacts/claude-design/<project>/<timestamp>/frame/design_contract.md

Use these supporting files only:
- artifacts/claude-design/<project>/<timestamp>/frame/tokens.json
- artifacts/claude-design/<project>/<timestamp>/frame/screenshots/desktop.png
- artifacts/claude-design/<project>/<timestamp>/frame/screenshots/mobile.png

Target files:
- <exact repo path>

Do not read the raw export unless the contract explicitly lacks required visual facts.
Before editing, report the files you will touch.
After editing, run the relevant frontend checks and capture desktop/mobile screenshots.
```

---

## 7. Gate Ledger

### Gate C0 - Source fact gate

**Question:** Are the token and surface claims based on current official documentation?

**Probe:** Read and cite the official Claude Design subscription usage article, Anthropic launch article, Claude Code costs article, Claude Code limits article, and Agent SDK overview.

**Artifact:** This document §1.

**Status:** `admitted`.

---

### Gate C1 - Live embed boundary

**Question:** Can the live `claude.ai/design` surface be embedded in VS Code?

**Probe:** HEAD/open request plus header inspection, recorded in `docs/ops/CLAUDE_DESIGN_FAF_BRIDGE.md`.

**Artifact:** `impossible_currently_boundary`.

**Status:** `blocked_not_closed`.

**Minimum condition to reopen:** Anthropic ships an official embeddable Design integration, API, MCP, or approved webview surface.

---

### Gate C2 - Local export intake

**Question:** Can a Claude Design export be classified locally without model/API calls?

**Prototype target:** `scripts/claude-design-intake.ts`

**Required behavior:**

```text
Input folder -> detect HTML/assets/PDF/PPTX/handoff -> write manifest.json
```

**Status:** `admitted`.

**Evidence:** first slice implemented in `scripts/claude-design-intake.ts`.

---

### Gate C3 - Frontend preview

**Question:** Can the export be shown in a frontend surface without backend?

**Prototype target:** `extensions/chthonic-archive` webview or static HTML fallback.

**Required behavior:**

```text
manifest.json + source/index.html/screenshots -> preview panel
```

**Failure membrane:** If HTML cannot be safely rendered, show screenshot/contact sheet and mark `L2=degraded`, not failed.

**Status:** `admitted`.

**Evidence:** lightweight pane implemented in `extensions/chthonic-archive/src/design/designFrameView.ts` with webview assets in `extensions/chthonic-archive/media/views/design-frame/`.

---

### Gate C4 - Contract extraction

**Question:** Can the local lane emit a compact implementation contract?

**Prototype target:** `scripts/claude-design-intake.ts`.

`scripts/claude-design-contract.ts` is intentionally not created for the first slice. Split only if the extraction logic becomes too large for intake.

**Required behavior:**

```text
Extract CSS tokens where possible.
Capture unknowns explicitly.
Write design_contract.md and tokens.json.
```

**Status:** `admitted`.

**Evidence:** first slice implemented in `scripts/claude-design-intake.ts`.

---

### Gate C5 - Token-bound handoff

**Question:** Can implementation be requested without spending tokens on raw exports or backend exploration?

**Required artifact:** `handoff_prompt.md`

**Admission rule:** The prompt references only:

- `design_contract.md`
- `tokens.json`
- selected screenshots
- exact target files
- acceptance checks

**Status:** `admitted`.

**Evidence:** first slice implemented in `scripts/claude-design-intake.ts`.

---

## 8. Backend-Scarce Operating Mode

When backend/API/token limits are scarce:

1. Use Claude Design for visual exploration only.
2. Export a folder or standalone HTML.
3. Run local intake.
4. Use the frontend preview to inspect and refine the contract.
5. Hand only the compact contract to Codex/frontend implementation.
6. Defer all backend integration behind mocked data contracts.

The first frontend prototype should therefore use static fixtures:

```text
fixtures/design-frame/
  manifest.json
  tokens.json
  design_contract.md
  screenshots/desktop.png
```

No API key.  
No Agent SDK.  
No Claude Code session until the compact handoff is ready.

Current command:

```text
bun run design:intake artifacts/claude-design/<project>/<timestamp> --target <repo-path>
```

---

## 9. Frontend Prototype Prompt

Use this when asking Codex to build the first UI:

```markdown
Build the Design Frame Zero frontend from
docs/reference/FAF_CLAUDE_DESIGN_TOKEN_BOUNDARY_PROTOTYPE.md.

Scope:
- frontend only;
- no Claude API;
- no Claude Agent SDK;
- no backend service;
- read mock JSON from local fixtures;
- render Preview / Tokens / Gates / Handoff panels;
- make the handoff prompt copyable;
- show gate states from manifest.json;
- support degraded preview state.

Design posture:
- dense inspector, not landing page;
- VS Code-compatible layout;
- no nested cards;
- stable dimensions;
- desktop and mobile responsive;
- no decorative gradients/orbs;
- all text must fit.

Acceptance:
- `bun run compile` for the extension surface or static build command passes;
- desktop and mobile screenshots verify no overlapping UI;
- handoff prompt includes only compact artifact paths.
```

---

## 10. Verdict

The usable prototype is not a backend integration. It is a **boundary compiler**:

```text
Claude Design visual work
  -> exported artifact
  -> FAF gates
  -> compact implementation contract
  -> frontend build request
```

The separate Claude Design meter raises the ceiling because visual exploration no longer has to consume Claude Code/chat limits. FAF keeps that advantage from dissolving by forcing the export, preview, contract, and handoff into explicit gates.

No false success. No live-product scraping. No token mythology.
