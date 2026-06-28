# VS Code Couture Gate N Survey, 2026-06-29

Scope: one lane only. This gate evaluates whether to continue implementation now, or first complete a survey of official SDKs, untrusted package scripts, and unofficial VS Code UI/substrate source patterns.

Decision: yes, keep this gate before the next build step.

Reason: the next architecture decision is not about taste yet. It is about boundary control. A marketplace-safe extension and a local VS Code Insiders substrate patcher are different artifacts with different risk profiles. Mixing them too early would make the project brittle and unfocused.

## Current Repo Arsenal

Official SDK catalog:

- `sdk-catalog.toml`
- `scripts/sdk-catalog.ts`
- `scripts/sdk-probe.ts`
- `manifest/sdk-probes/latest.json`

Current commands:

```bash
bun run sdk:list
bun run sdk:check
bun run sdk:latest:dry
bun run sdk:latest
bun run sdk:probe:write
```

Current substrate:

- `scripts/mica-substrate.ps1`
- `designs/chthonic-mica.cjs`
- `designs/vibrancy-obsidian.css`

Current substrate shape:

- patches VS Code Insiders `out/main.js`
- injects one dynamic import block marked `CHTHONIC-MICA`
- injects one workbench CSS link
- uses Electron `BrowserWindow.setBackgroundMaterial(...)`
- avoids taking color authority away from the theme

## Official SDK Status

Cataloged and probed:

- `@vscode/dts`: CLI-only, proposed API helper
- `@vscode/test-electron`: compatible
- `@vscode/test-web`: compatible
- `@vscode/test-cli`: CLI-oriented, importable
- `@vscode/vsce`: CLI-oriented, importable
- `@modelcontextprotocol/sdk`: native import surface
- `openai`: compatible
- `@openai/agents`: compatible
- `@openai/codex-sdk`: compatible
- `@anthropic-ai/sdk`: compatible
- `@anthropic-ai/claude-agent-sdk`: compatible
- `zod`: support dependency for agent schemas

`bun outdated` showed no cataloged SDK updates at gate time. It only reported unrelated packages outside this lane:

- `@sentry/bun`
- `ajv`
- `hono`
- `minimatch`
- `@google/gemini-cli`
- `@playwright/mcp`

## Untrusted Package Scripts

Current Bun blocked lifecycle scripts:

```text
@github/keytar @7.10.6
@playwright/browser-chromium @1.61.1
@vscode/vsce-sign @2.0.9
```

Dependency chains:

```text
@github/keytar
  optional dependency of @google/gemini-cli
  outside this lane

@playwright/browser-chromium
  dependency of @vscode/test-web
  relevant only when web-extension/browser smoke tests are enabled

@vscode/vsce-sign
  dependency of @vscode/vsce
  relevant only when VSIX signing or publish-path packaging requires it
```

Trust policy:

- do not run `bun pm trust` globally
- do not trust `@github/keytar` for this lane
- consider trusting `@playwright/browser-chromium` only when a concrete `@vscode/test-web` smoke test requires a managed browser
- consider trusting `@vscode/vsce-sign` only when packaging or signing fails without its postinstall output

## Official Versus Unofficial Boundary

Official, marketplace-safe surfaces:

- color themes
- file icon themes
- product icon themes
- commands
- views and tree views
- webviews
- configuration schemas
- extension tests through VS Code test tooling
- VSIX packaging through VSCE
- proposed API only when explicitly gated through `@vscode/dts` and Insiders-compatible extension config

Unofficial, local-substrate surfaces:

- editing VS Code `main.js`
- editing `workbench.html`
- editing workbench CSS/JS bundles
- patching CSP or trusted-types
- injecting CSS/JS into the workbench DOM
- overriding Electron `BrowserWindow` construction
- writing native `.node` vibrancy bindings
- patching extension files from another extension
- removing or weakening webview CSP

Boundary decision:

The publishable marketplace extension should stay inside official surfaces. The local couture substrate can use unofficial patching, but it must be explicit, reversible, version-aware, and treated as local infrastructure rather than marketplace-safe behavior.

## Source Survey

Temporary survey root:

```text
C:\Users\eldno\AppData\Local\Temp\chthonic-vscode-couture-survey
```

Surveyed repos:

```text
illixion/vscode-vibrancy-continued      f05f30e
iotacb/vesper-vibrant                  26f8116
drcika/apc-extension                   4d7d3b1
subframe7536/vscode-custom-ui-style    1b1725d
be5invis/vscode-custom-css             fca4a2f
raunofreiberg/vesper                   9043f38
```

### Vibrancy Continued

Repo: `https://github.com/illixion/vscode-vibrancy-continued`

Observed surfaces:

- VS Code extension commands for install, uninstall, update
- settings-driven vibrancy modes
- marker-based `main.js` injection
- CSP/trusted-types patching in `workbench.html`
- runtime import through a global config object
- Electron `browser-window-created` handling
- `setBackgroundMaterial(...)` on Windows 11
- legacy native Windows accent fallback through `.node`
- theme CSS catalog and color-customization backup/restore
- elevation and restart choreography

Useful to us:

- marker discipline
- update/uninstall flow
- version-aware handling
- local config metadata
- distinction between material runtime and theme CSS

Do not copy as core:

- broad theme CSS ownership
- native Windows accent fallback unless we deliberately need Windows 10 support
- marketplace extension owning privileged local install mutation without a hard boundary

### Vesper and Vesper Vibrant

Repos:

- `https://github.com/raunofreiberg/vesper`
- `https://github.com/iotacb/vesper-vibrant`

Observed surfaces:

- conventional VS Code theme packages
- one contributed theme JSON
- no workbench patching
- no extension runtime

Useful to us:

- clean marketplace-safe baseline
- proof that visual identity can ship as pure theme contribution

Limit:

- cannot own shell glass, workbench chrome, Mica, or non-client material

### Apc Customize UI++

Repo: `https://github.com/drcika/apc-extension`

Observed surfaces:

- patches `bootstrap-amd.js`
- patches `main.js`
- writes `vs/modules` and `vs/patch`
- creates a replacement `workbench-apc-extension.html`
- hooks AMD module loading
- overrides internal Electron window options
- exposes broad UI configuration such as fonts, bars, electron options, and buttons

Useful to us:

- shows the maximum reach of a VS Code UI patch extension
- settings schema breadth is a useful reference
- command names and enable/disable rhythm are useful

Do not copy as core:

- bootstrap/AMD module interception as primary strategy
- Object-prototype or internal class override style patching
- broad internal module coupling

### Custom UI Style

Repo: `https://github.com/subframe7536/vscode-custom-ui-style`

Observed surfaces:

- Bun-based build/package workflow
- backup/reload/rollback file manager abstraction
- separate managers for main, renderer, CSS, webview, external imports
- workbench path discovery for current VS Code layouts
- optional webview CSP mutation
- external CSS/JS cache and merge strategy

Useful to us:

- backup/reload/rollback abstraction
- target-specific patch managers
- current workbench path discovery
- atomic write pattern

Do not copy as core:

- remote JS import surface
- default webview CSP removal
- patching unrelated extension files

### Custom CSS and JS Loader

Repo: `https://github.com/be5invis/vscode-custom-css`

Observed surfaces:

- finds workbench HTML candidates
- creates UUID-marked HTML backups
- injects CSS/JS into `<head>`
- removes CSP meta
- supports file and remote imports
- reloads window after patch

Useful to us:

- simple backup marker pattern
- workbench HTML candidate list

Do not copy as core:

- CSP removal as normal behavior
- arbitrary JS injection as user-facing default
- remote script loading

## What We Actually Need

Need now:

1. Official marketplace extension package
   - theme contribution
   - product icon/file icon contribution if chosen
   - commands
   - settings schema
   - VSIX package path
   - tests through cataloged VS Code tooling

2. Local substrate patcher
   - status
   - apply
   - verify
   - restore
   - reapply after Insiders update
   - backup metadata
   - source hash or marker validation

3. Visual verification
   - screenshot current Insiders workbench
   - detect whether Mica/CSS layer exists
   - detect if theme surfaces are transparent enough but still readable

4. SDK smoke probes
   - do not just import SDKs
   - prove a local MCP loopback
   - prove VS Code extension test boot
   - prove VSIX package command
   - keep provider SDK tests dry unless env tokens are explicitly loaded

Need later:

- `@types/vscode`, pinned to the extension engine target
- `@vscode/l10n`, only if localization becomes part of the marketplace polish
- a bundler, only after the extension skeleton proves it needs one
- Playwright/browser trust, only if web extension visual tests become a committed requirement
- VSCE signing trust, only if package/sign/publish requires it

Do not need now:

- native Windows 10 vibrancy addon
- remote JS imports
- patching webview CSP
- bootstrap/AMD module interception
- full Apc-style internal module override
- generic custom CSS loader surface

## Recommended Next Move

Next move: harden `scripts/mica-substrate.ps1` before building the marketplace extension.

Why:

- it is already the local unofficial boundary
- it is narrow and reversible enough to make deterministic
- it prevents Insiders update churn from derailing later design work
- it gives visual verification a stable target

Implement this command surface:

```powershell
pwsh -NoProfile -File scripts/mica-substrate.ps1 -Status
pwsh -NoProfile -File scripts/mica-substrate.ps1 -Apply
pwsh -NoProfile -File scripts/mica-substrate.ps1 -Verify
pwsh -NoProfile -File scripts/mica-substrate.ps1 -Restore
pwsh -NoProfile -File scripts/mica-substrate.ps1 -ReapplyLatest
```

Acceptance:

- `-Status` reports version, commit, Electron, app root, main path, workbench path, patch markers, CSS marker, running process count, latest backup
- `-Verify` exits nonzero if expected markers or files are missing
- `-Restore` restores an explicit backup or latest backup
- `-ReapplyLatest` restores clean source if needed, then applies current runtime and CSS
- no unrelated patch extension behavior enters the marketplace extension package

After that:

1. create/identify the extension skeleton
2. add `@types/vscode` pinned to its `engines.vscode`
3. package through Bun plus VSCE
4. add visual verification
5. expand SDK probes into smoke tests

## Gate Verdict

Continue through Gate N first. Do not build deeper until this survey is accepted as the boundary contract.

The arsenal is enough. The missing piece is not more SDKs; it is keeping official marketplace polish and unofficial local substrate engineering separated, automated, and testable.
