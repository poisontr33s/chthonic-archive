# Cartography: Chthonic Archive VS Code Extension
# Generated: 2026-05-28
# Surface: extensions/chthonic-archive/
# Scope: full extension — subsystems, views, commands, wiring, status annotations

---

## Architecture Map

```
extension.ts  (activate)
│
├── LaneRegistry                         [WORKING] runtime/laneState.ts
│   └── binds to globalStorageUri snapshot
│
├── runActivationLane[dev-reload]        [OPT-IN-DEFAULT-OFF]
│   └── runtime/devAutoReload.ts        watches dist/extension.js, reloads window
│
├── runActivationLane[webview-hmr]       [WORKING]
│   └── runtime/webviewHmrWatcher.ts    watches media/views/**/*.{html,js}, pushes reload msg
│
├── runActivationLane[markdown-paste]    [WORKING]
│   └── markdownPaste/register.ts       turndown + markdown-it; context menu in markdown files
│
├── ActivityBarMorph                     [WORKING]
│   └── monolith/activityBarMorph.ts    changes sidebar icon/badge on toolchain score + entropy state
│
├── registerToolchainCompleteness()      [WORKING]
│   └── monolith/rustificationScore.ts
│       Scans 14 file markers at workspace root, weights → 0-100 score, tier gate/lens/loom
│       FileSystemWatcher on {uv.lock,Cargo.toml,mise.toml,...} triggers refresh
│       Feeds → loomProvider.update(report) + activityBarMorph.update(report)
│
├── runActivationLane[sidecars]          [WORKING as gate; most lanes OPT-IN-DEFAULT-OFF]
│   └── activation/activateSidecars.ts
│       ├── EntropyWorkerClient          [OPT-IN-DEFAULT-OFF] entropy.enabled=false
│       │   └── entropy/entropyWorkerClient.ts  Worker thread → dist/entropy-worker.js
│       ├── EntropyDecorationProvider    [OPT-IN-DEFAULT-OFF]
│       │   └── entropy/entropyDecorations.ts
│       ├── AbyssalPaneProvider          [WORKING-UI / DATA-OPT-IN]
│       │   └── entropy/archiveAbyssalView.ts   renders even when entropy off; data stream is off
│       ├── PolyglotEntropyOrchestrator  [OPT-IN-DEFAULT-OFF] entropy.polyglotEnabled=false AND allowNativeSidecars=false
│       │   └── polyglot/polyglotEntropyOrchestrator.ts
│       │       ├── polyglot/ledgerBroker.ts
│       │       ├── polyglot/merkleAccumulator.ts
│       │       ├── polyglot/solanaLedger.ts     Solana validator/bankrun lane
│       │       └── polyglot/polyglotBroker.ts
│       ├── SelfHealingLoop              [OPT-IN-DEFAULT-OFF] slab.selfHealingEnabled=false AND allowNativeSidecars=false
│       │   └── monolith/selfHealingLoop.ts
│       ├── AnnoClient                   [OPT-IN-DEFAULT-OFF] reactor.enabled=false AND allowNativeSidecars=false
│       │   └── reactor/annoClient.ts   spawns chthonic-daemon (Rust binary via child_process JSONL)
│       ├── CockpitLayout                [OPT-IN-DEFAULT-OFF]
│       │   └── reactor/cockpitLayout.ts
│       └── SynapseBridge                [OPT-IN-DEFAULT-OFF]
│           └── reactor/synapseBridge.ts  shared-memory or JSONL transport to daemon
│
├── runActivationLane[views]             [WORKING]
│   └── activation/activateViews.ts
│       ├── AnkhReferenceProvider        → chthonic.chatView        [WORKING]
│       ├── LoomViewProvider             → chthonic.loomView        [WORKING]
│       ├── DesignFrameProvider          → chthonic.designFrameView [WORKING-UI / UNCERTAIN-data]
│       ├── StylusInputProvider          → chthonic.stylusView      [WORKING-UI / UNCERTAIN-functional]
│       ├── EntropyDecorationProvider    → FileDecorationProvider   [OPT-IN-DEFAULT-OFF]
│       ├── AbyssalPaneProvider          → chthonic.abyssalView     [WORKING-UI / DATA-OPT-IN]
│       ├── ThemeTreeProvider            → chthonic.themeView       [WORKING]
│       └── StatusTreeProvider           → chthonic.statusView      [WORKING]
│
├── runActivationLane[commands]          [WORKING]
│   └── activation/activateCommands.ts  (see command table below)
│
├── runActivationLane[flux]              [WORKING — self-contained lane]
│   └── flux/fluxService.ts
│       ├── FluxLauncherViewProvider     → chthonic.fluxLauncherView [WORKING]
│       ├── FluxPanel                    editor panel, on-demand   [WORKING-UI / BLOCKED-no-bridge]
│       └── StatusBarItem                $(zap) FLUX: idle/running  [WORKING]
│
├── runActivationLane[status]            [WORKING]
│   └── activation/activateStatus.ts    SSOT hash + lineage in statusbar (OPT-IN flags)
│
└── ensureDefaultChthonicPlacement()     [WORKING]
    └── monolith/restoreOrderLayout.ts  runs once per version bump on workspace state
```

---

## 8 Views — Provider Class Index

| View name (package.json) | View ID | Provider class | File | Status |
|---|---|---|---|---|
| FLUX Gate | chthonic.fluxLauncherView | FluxLauncherViewProvider | flux/fluxLauncherView.ts | WORKING |
| ANKH Reference | chthonic.chatView | AnkhReferenceProvider | monolith/ankhReferenceView.ts | WORKING |
| Abyssal Pane | chthonic.abyssalView | AbyssalPaneProvider | entropy/archiveAbyssalView.ts | WORKING-UI / DATA-OPT-IN |
| Themes | chthonic.themeView | ThemeTreeProvider | activation/activateViews.ts | WORKING |
| Lens | chthonic.statusView | StatusTreeProvider | activation/activateViews.ts | WORKING |
| The Loom | chthonic.loomView | LoomViewProvider | monolith/loomView.ts | WORKING |
| Design Frame | chthonic.designFrameView | DesignFrameProvider | design/designFrameView.ts | WORKING-UI / UNCERTAIN |
| Stylus Pad | chthonic.stylusView | StylusInputProvider | monolith/stylusInputView.ts | WORKING-UI / UNCERTAIN |

---

## Command Table — Wiring Status

| Command ID | Registered in activateCommands.ts | Subsystem owner | Status |
|---|---|---|---|
| chthonic.switchTheme | YES (line 312) | views/themeProvider | WORKING |
| chthonic.refreshStatus | YES (line 345) | status + entropy + toolchain | WORKING |
| chthonic.verifySSOT | YES (line 334) | activateStatus (fingerprint) | WORKING |
| chthonic.entropyRefresh | YES (line 82) | entropy worker + polyglot | OPT-IN-DEFAULT-OFF |
| chthonic.activateCockpit | YES (line 96) | reactor/cockpitLayout | OPT-IN-DEFAULT-OFF |
| chthonic.annoDetect | YES (line 117) | reactor/annoClient | OPT-IN-DEFAULT-OFF |
| chthonic.reactorSediment | YES (line 137) | reactor/annoClient + synapseBridge | OPT-IN-DEFAULT-OFF |
| chthonic.openStylusInput | YES (line 59) | monolith/stylusInputView | WORKING |
| chthonic.openClaudeDesignFrame | YES (line 64) | design/designFrameView | WORKING |
| chthonic.selectClaudeDesignFrameExport | YES (line 69) | design/designFrameView | WORKING |
| chthonic.openClaudeDesignInBrowser | YES (line 74) | design/designFrameView | WORKING |
| chthonic.importClaudeDesignCapture | YES (line 77) | design/designFrameView | WORKING |
| chthonic.deepFocus | YES (line 99) | monolith/deepFocusLayout | WORKING |
| chthonic.restoreOrder | YES (line 102) | monolith/restoreOrderLayout | WORKING |
| chthonic.slabHeal | YES (line 105) | monolith/selfHealingLoop | OPT-IN-DEFAULT-OFF |
| chthonic.refreshRustification | YES (line 114) | monolith/rustificationScore | WORKING |
| chthonic.openWebCockpit | YES (line 166) | activation/activateCockpit | WORKING (reachability-gated) |
| chthonic.startWebCockpit | YES (line 188) | activation/activateCockpit | WORKING |
| chthonic.openBunTrainingDocs | YES (line 205) | inline quickpick | WORKING |
| chthonic.postRestartVerify | YES (line 236) | terminal → insiders script | WORKING |
| chthonic.restartGate | YES (line 249) | terminal → insiders script | WORKING |
| chthonic.runtimeStatus | YES (line 262) | runtime/statusReport | WORKING |
| chthonic.flux.openPanel | YES (fluxService.ts line 71) | flux/fluxPanel | WORKING |
| chthonic.flux.focusLauncher | YES (fluxService.ts line 72) | flux/fluxLauncherView | WORKING |
| chthonic.flux.verifyPresence | YES (fluxService.ts line 73) | flux/fluxService | WORKING |
| chthonic.flux.showOutput | YES (fluxService.ts line 74) | outputChannel | WORKING |
| chthonic.flux.startBackend | YES (fluxService.ts line 75) | flux/fluxService → bridge | BLOCKED-no-bridge |
| chthonic.flux.stopBackend | YES (fluxService.ts line 76) | flux/fluxService → bridge | BLOCKED-no-bridge |
| chthonic.flux.rotateSecret | YES (fluxService.ts line 77) | SecretStorage | WORKING |
| chthonic.flux.setMasterSecret | YES (fluxService.ts line 78) | SecretStorage | WORKING |
| chthonic.flux.revealMasterSecret | YES (fluxService.ts line 79) | SecretStorage | WORKING |
| chthonic.pasteRenderedAiMarkdown | YES (markdownPaste/register.ts) | markdownPaste | WORKING |

No commands declared in package.json are orphans. Every command ID has a registration site.

---

## Section 2: The Loom — Data Source Wiring

The Loom renders via `media/views/loom/index.html` + `media/views/loom/view.js`.
The provider is `LoomViewProvider` (`monolith/loomView.ts`).

It receives state via two independent push paths:

**Path A — Toolchain score (the "54%" section)**
- `extension.ts: registerToolchainCompleteness()` calls `computeRustificationReport(workspaceRoot)`
- `rustificationScore.ts` walks 14 hardcoded file markers at workspace root, weights them, produces score 0-100
- Score is pushed to `loomProvider.update(report)` → `postState()` → webview `message.report`
- `view.js` reads `report.score`, `report.tier`, `report.present[]`, `report.missing[]`
- Refresh triggers: startup, FileSystemWatcher events on the 14 marker filenames, manual `chthonic.refreshRustification`
- The "Markers Present" and "Markers Missing" lists in the UI are exactly `report.present[]` and `report.missing[]`

**Path B — Workspace Health Stream (the four zero-values)**
- `activateSidecars.ts` calls `loomProvider.updateWorkspaceHealth(entropyClient.getSnapshot())`
- Also wired: `entropyClient.onDidUpdateSnapshot → loomProvider.updateWorkspaceHealth(snapshot)`
- `view.js` reads `snapshot.totalFiles`, `snapshot.averageEntropy`, `snapshot.lastScanDurationMs`, `snapshot.lastScanAt`
- **The snapshot is all zeros/empty on every default startup** because `entropyClient.start()` is only called inside `if (entropyEnabled)` in `wireReactorEvents()`, and `entropyEnabled` defaults to `false`
- The loom shows `entropy disabled` in the health-updated field when `snapshot` is null/absent

Summary: The "54%" score is live on every startup. The Workspace Health Stream fields ("files", "avg entropy", "duration", "updated") show zeros or dashes unless `chthonic.entropy.enabled=true`.

---

## Section 3: The Five Action Buttons

**Refresh Toolchain**
- Button → webview `postMessage({type:'refresh'})` → `loomView.ts` dispatch → `vscode.commands.executeCommand('chthonic.refreshRustification')`
- Handler in `activateCommands.ts:114`: `deps.refreshToolchainCompleteness('manual-command')`
- Which calls `computeRustificationReport(workspaceRoot)` → `loomProvider.update(report)`
- Status: WORKING. Runs unconditionally (no flag gate). Result visible immediately in Loom.

**Rescan Health**
- Button → webview `postMessage({type:'rescan'})` → `vscode.commands.executeCommand('chthonic.entropyRefresh')`
- Handler in `activateCommands.ts:82`:
  - If `!entropyEnabled`: shows warning "Workspace health lane is disabled (chthonic.entropy.enabled=false)" and returns
  - If enabled: calls `entropyClient.rescanNow()` + `entropyClient.requestGraph(260)` + `polyglotOrchestrator.requestManualScan()`
- Status: OPT-IN-DEFAULT-OFF. The button is visible and clickable but fires a warning when entropy is off (the default). It does NOT silently do nothing — it explicitly warns.

**Self-Heal**
- Button → webview `postMessage({type:'heal'})` → `vscode.commands.executeCommand('chthonic.slabHeal')`
- Handler in `activateCommands.ts:105`:
  - If `!allowNativeSidecars`: shows warning "Native sidecars are disabled (chthonic.security.allowNativeSidecars=false)" and returns
  - If allowed: `deps.selfHealingLoop.runNow('manual')`
- `selfHealingLoop.runNow()` in `monolith/selfHealingLoop.ts`:
  1. Runs `auditVsToolchain()` → pwsh vs2026_audit.ps1 -Json
  2. `collectRuntimeStates()` — probes python3/py/python, ruby, go, rustc, solana via child_process + vswhere.exe for VS version
  3. Checks each version against endoflife.date API
  4. If stale: runs `mise upgrade` + `mise reshim`, refreshes toolpool snapshot via bun, attempts to symlink/create MSVC include junction at `.chthonic/native/msvc/include`, sets `CHTHONIC_VS_CPP_INCLUDE` + `INCLUDE` in EnvironmentVariableCollection
- Status: OPT-IN-DEFAULT-OFF (double-gated: `slab.selfHealingEnabled=false` AND `security.allowNativeSidecars=false`). The actual repair logic is real and substantive, not a stub.

**Deep Focus**
- Button → webview `postMessage({type:'deepFocus'})` → `vscode.commands.executeCommand('chthonic.deepFocus')`
- Handler in `activateCommands.ts:99`: `deps.deepFocusLayout.activate()`
- `deepFocusLayout.ts`:
  1. `workbench.action.terminal.moveToSidePanel`
  2. `workbench.action.toggleAuxiliaryBar`
  3. `workbench.action.focusActiveEditorGroup`
  4. `workbench.view.extension.chthonic-archive`
  5. `chthonic.loomView.focus`
- Status: WORKING. No flag gate. Moves terminal to side panel, opens Chthonic sidebar, focuses The Loom.

**Restore Order**
- Button → webview `postMessage({type:'restoreOrder'})` → `vscode.commands.executeCommand('chthonic.restoreOrder')`
- Handler in `activateCommands.ts:102`: `deps.restoreOrderLayout.activate()`
- `restoreOrderLayout.ts` fires best-effort sequence:
  1. `workbench.view.extension.chthonic-archive`
  2. `chthonic.statusView.focus`
  3. `workbench.action.moveFocusedViewToSecondarySidebar`
  4. `chthonic.loomView.focus`
  5. `workbench.action.moveFocusedViewToPanel`
  6. `workbench.action.positionPanelBottom`
  7. `workbench.action.focusActiveEditorGroup`
- Status: WORKING. No flag gate. Also called automatically on first launch per version (`ensureDefaultChthonicPlacement`).

---

## Section 4: Stale / Functional / Flag-Gated Inventory

**WORKING — active on default startup**
- Themes (4 color themes, 1 file icon theme, 1 product icon theme): pure JSON, always active
- Language grammars (GLSL, TOML): always active
- AnkhReferenceProvider: reads EPOCH_*.md or legacy .github/copilot-instructions.archive.md, parses ANKH notation sections
- LoomViewProvider + rustificationScore: toolchain marker scan live on startup
- ThemeTreeProvider / StatusTreeProvider (Lens view)
- ActivityBarMorph: icon badge updates with toolchain score
- markdownPaste lane: turndown + markdown-it, context menu in .md files
- All five Loom action buttons (Deep Focus and Restore Order unconditional; others warn when gated)
- FluxService: launcher view, status bar item, secret management commands all live
- devAutoReload lane: OPT-IN-DEFAULT-OFF (`chthonic.dev.autoReload=false`)
- RestoreOrderLayout runs once on first activation per version bump

**OPT-IN-DEFAULT-OFF (visible UI, inactive data/logic)**
- Workspace Health Stream in The Loom: four health fields show zeros until `entropy.enabled=true`
- AbyssalPaneProvider: sidebar pane renders but receives no data stream (entropy worker never started)
- EntropyDecorationProvider: file decoration badges never fire
- Rescan Health button: warns but does nothing
- Self-Heal button: warns but does nothing (double-gated)
- AnnoClient / ReactorSediment / CockpitLayout: require `reactor.enabled=true` AND `security.allowNativeSidecars=true` AND daemon binary present at `native/target/release/chthonic-daemon.exe`
- PolyglotOrchestrator / Solana / Merkle / ledger lanes: require `entropy.polyglotEnabled=true` AND `security.allowNativeSidecars=true`
- FLUX startBackend / stopBackend / generate: require native bridge `.node` addon at `apps/chthonic-tensor-bridge/build/Release/chthonic_tensor_bridge.node` (or configured path) — binary not present → graceful error message

**UNCERTAIN (UI present; backing logic not fully verified from source)**
- DesignFrameProvider: substantial implementation (design/designFrameView.ts), handles export root selection, HTML/image preview, handoff prompt, gate status rendering — wiring is real, but runtime completeness depends on whether an export root has been configured
- StylusInputProvider: webview renders (media/views/stylus/), routes text to editor/terminal/chat — functional on Android tunnel; on desktop no pen input means the route targets may never fire

**STALE / ONE-TRICK**
- `src/acp/` directory (client.ts, connection.ts, index.ts, webview.ts): present in the glob but not imported anywhere in the activation chain. Zero references from extension.ts, activateCommands.ts, activateSidecars.ts, or activateViews.ts. These are a disconnected subsystem.
- `src/sdk/` directory (connection.ts, index.ts, webview.ts): same pattern — not imported from any activation path. Likely a parallel/earlier attempt at a bridge SDK, never wired.
- `media/abyssalPane.js`: flat file at media root, not under `media/views/`. The AbyssalPane view uses `media/views/abyssal/view.js`. This file at the root is unreferenced by the loader.

---

## Section 5: FLUX Subsystem Integration Points

FLUX runs in `runActivationLane[flux]` as its own self-contained lane. `FluxService.register()` is the single entry point.

**Connection to the rest of the extension:**
- Shares the `outputChannel` (same channel as all other lanes)
- Shares `workspaceRoot`
- Shares `context` (subscriptions, secrets, extensionPath)
- Status bar item is created inside FLUX (not shared with activateStatus)
- No dependency on entropy, reactor, sidecars, or loom — it imports none of their types

**Where FLUX stands alone:**
- FluxLauncherViewProvider is registered directly inside FluxService.register(), not via activateViews.ts
- FluxPanel is created on demand inside FluxService, not pre-instantiated
- All 9 FLUX commands are registered inside fluxService.ts, not in activateCommands.ts
- The native bridge is loaded via `require(p)` at runtime from a candidate path list; no build-time import
- FLUX has no subscriber to LoomViewProvider, EntropyWorkerClient, or LaneRegistry — it emits no lane state

The FLUX lane is the only lane that does not participate in LaneRegistry. Its state is reported only via the status bar item and the launcher view's own UI. The StatusTreeProvider "Lens" view has no FLUX entry.

---

## Summary

Five nodes dominate the architecture: `activateSidecars` (orchestrates ~8 optional subsystems behind two kill-switches), `LoomViewProvider` (the concentration point for toolchain score and health data), `AnnoClient` (the Rust daemon IPC hub), `FluxService` (fully self-contained, bridge-gated), and `EntropyWorkerClient` (the worker thread behind all workspace-health surfaces). Isolated nodes: `src/acp/` and `src/sdk/` are disconnected — imported nowhere, dead. `media/abyssalPane.js` at the media root is unreferenced. The most significant structural fact: the majority of visible UI surfaces (Abyssal Pane health data, Rescan Health, Self-Heal, all reactor commands) require `chthonic.security.allowNativeSidecars=true` and `chthonic.entropy.enabled=true`, both off by default — the extension presents a larger surface than it runs at default settings.
