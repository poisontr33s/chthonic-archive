---
type: session_landing
status: ready_for_restart
created: 2026-05-29
session_window: 2026-05-28 → 2026-05-29 (multi-day continuous arc)
arc_origin: FLUX complaint + chthonic-archive stale-extension framing (spartanic-madman shape)
arc_destination: parallel-arsenal Rust bridges + polyglot spread scanner with workspace-file mode
audience: conductor after VS Code Insiders update + extension restart
preconditions: read this before reactivating chthonic-archive extension or its native crates
---

# SESSION 2026-05-28/29 LANDING

Pre-restart landing memo. Comprehensive map of where we are so the VS Code Insiders update + extension restart doesn't lose the thread.

The user's framing for this memo: "structurize everything from the beginning of session FLUX complaint + Chthonic Archive spartanic madman, stale extension... summarize when you got it, without needing me to tell you... glue the long spleens between them and compound as method that works then structurize and re-align between the lines." This is the spleen-as-substrate work — making the wide-field session coherent so the post-restart pickup is clean.

---

## I. Arc origin (where this started)

The session opened with the chthonic-archive VS Code extension in "stacked spartan chaos" state: stale extension shape with FLUX gate panel, Loom panel (stacked markers), Lens (`StatusTreeProvider`), 5-button action bar (Refresh Toolchain / Rescan Health / Self-Heal / Deep Focus / Restore Order), most subsystems gated behind opt-in flags. The local-agent dynamic had pushed prior framings toward joke-shape, which the user named explicitly as fine but worth acknowledging.

The user's pivot, mid-session, set the canon: the GitHub Copilot SDK Rust v1.0.0-beta.9 (released to align with VS Code Insiders) was the anchor; everything else became reference. Plan committed at `~/.claude/plans/2-copilot-sdk-vogue-anchor.md` with 6 phases. Subsequent iterations expanded the scope: ACP became a second canonical anchor sibling, then a third lane (the polyglot spread scanner) compounded into the work, then the polyrepo was named as 8 origin-main satellites that bind the scanner's first-class object.

---

## II. What landed (substrate delta)

### A. Copilot SDK alignment (Phase 1 + 1.5)

- Bumped `github-copilot-sdk = "1.0.0-beta.4"` → `"1.0.0-beta.9"` and `edition = "2021"` → `"2024"` in 3 Cargo.toml files: root `Cargo.toml`, `tools/chthonic-mcp/Cargo.toml`, `tools/copilot-triage/Cargo.toml`
- Refactored 9 `ToolHandler` impls across `tools/chthonic-mcp/src/main.rs` and `tools/copilot-triage/src/main.rs` to beta.9 API: removed `SessionHandler` (replaced by `ApproveAllHandler`), removed `ToolHandlerRouter` (Tool builders inlined with `.with_handler()`), removed `fn tool(&self) -> Tool` method (Tool definitions moved to config-build site), swapped `inv.params()` → `serde_json::from_value(inv.arguments)`, renamed `with_transform()` → `with_system_message_transform()`, streaming via `session.subscribe()` channel + `tokio::spawn` reader
- WPTG'd prior consumer code as `tools/{chthonic-mcp,copilot-triage}/src/main.rs.beta4.off`
- `cargo check --workspace` returns 0 hard errors. The 114 `unsafe_op_in_unsafe_fn` warnings in `src/render/*.rs` are edition-2024 deferred follow-up, not introduced by this work
- Reference memory at `~/.claude/projects/c--Users-eldno-chthonic-archive/memory/reference_copilot_sdk_rust_beta9.md` updated with the actual consumer-side API breakage (which was larger than PR #1400's error refactor alone)

### B. Dead-lane WPTG cleanup (Phase 2 — partially reversed)

- `extensions/chthonic-archive/src/sdk/` → `src/sdk.unused.off/` (parked)
- `extensions/chthonic-archive/media/abyssalPane.js` → `media/abyssalPane.js.unused.off` (parked)
- `extensions/chthonic-archive/src/acp/` → `src/acp.unused.off/` then RESTORED later when the user named ACP as canonical anchor sibling to the Copilot SDK
- `tsconfig.json` exclude pattern `"src/**/*.unused.off/**"` added
- Conductor-side: `ci/checks/ignored-source.ts` updated (by user) to treat `*.unused.off` as intentional disabled-source quarantine — closes the commit-guard loop with the WPTG convention

### C. Parallel-arsenal Rust bridge crates (Phase 3)

Both new crates sit in `extensions/chthonic-archive/native/` as siblings to the pre-existing `chthonic-{daemon, synapse-schema, etc.}` workspace members. Both follow the v9-baseline skeleton: `edition = "2024"` per-crate override (workspace pins 2021), `version.workspace = true`, `license.workspace = true`, local `tokio = { version = "1.52", features = ["full"] }`, tracing-subscriber to stderr, clap-driven CLI with shared `--smoke` / `--prompt` / `--cwd` / `--timeout-secs` flags.

- **`extensions/chthonic-archive/native/chthonic-copilot-bridge/`** — anchors on `github-copilot-sdk = "1.0.0-beta.9"`. JSON-RPC wire toward the official `copilot` CLI binary. Three modes: `--smoke` (canned liveness prompt), `--prompt "<text>"` (one-shot), no-flag (single stdin line). Uses `ApproveAllHandler` for permission auto-approve, `session.subscribe()` + spawned reader for streaming deltas
- **`extensions/chthonic-archive/native/chthonic-acp-bridge/`** — anchors on `agent-client-protocol = "0.12"` with `unstable` feature flag (mirrors Zed's pin pattern). ACP wire toward the agent binary (default: `copilot --acp`, configurable via `--agent-path`). Auto-approves permission requests matching the TS substrate's `ChthonicAcpClient` stance. Three modes mirror the Copilot bridge
- Both registered in `extensions/.../native/Cargo.toml` `members` + `default-members`. Both compile clean; `--help` shows the shared shape
- Canonical reference at `meta-ide/copilot-sdk-rust-v1.0.0-beta.9/` (shallow git clone of the SDK) for Copilot side; ACP reference at `agentclientprotocol/rust-sdk/examples/yolo_one_shot_client.rs`
- Memory: `reference_agent_client_protocol_rust.md`, `reference_parallel_arsenal_bridges.md` (architectural commitment), `reference_copilot_sdk_rust_beta9.md` (updated)

### D. Dispatcher seam (Phase 4 stub, additive non-invasive)

`extensions/chthonic-archive/src/acp/dispatch.ts` — new file, doesn't touch existing `AcpConnection`. Exports:

- `chooseAgent(kind, options) → AgentSpec | null` where kind ∈ `{'acp-direct', 'copilot-sdk', 'acp-bridge', 'auto'}`
- `resolveCopilotPath()` — `$COPILOT_CLI_PATH` env → WinGet known-path → bare `copilot` on PATH fallback chain
- `locateBridgeBinary(repoRoot, crateName)` — release-first, debug-fallback, returns null if unbuilt
- `describeAgent(spec)` — one-line log description

Bundle stayed 93 modules (extension still builds clean); nothing imports `dispatch.ts` yet — wiring is conductor's call. Notable: the existing `AcpConnection` at `src/acp/connection.ts:11` pins a hardcoded `COPILOT_PATH` containing the username `erdno` (robocopy migration residue from old laptop, not a typo — user named the provenance 2026-05-29). The dispatch seam is the durable fix when AcpConnection eventually consumes `resolveCopilotPath()`.

### E. Polyglot spread scanner (a major parallel arc)

This grew from one Bun script into a Rust-ported workspace-file-aware content-value engine. The iteration ladder:

| Iteration | Artifact | What it added |
|-----------|----------|---------------|
| V1.0 | `scripts/spread-sweep.ts` | Wide-angle project discovery (127 projects across 8 sibling workspaces), framework heuristics, repurposability scoring, mode_hint (snipe/sweep/noise) |
| V1.5 | same | Per-extension line counts, native/GPU stack detection, expanded buckets |
| V1.6 | same | Vendored-path filter (vcpkg buildtrees, .cargo/registry, rv/library) — 127→110 projects |
| V1.7a | `ci/checks/spread-freshness.ts` | CI freshness gate (read-only health, surfaces shape + age) |
| V1.7b | `scripts/spread-drill.ts` | Per-snipe drill-down (`Bun.Transpiler.scan` for TS imports/exports, regex for Rust `pub` items, symbol-hint for native) |
| V1.8 | spread-sweep extension | `salvage_verdict` classifier: chthonic-member / absorb-candidate / mirror-of / independent / unclassified — surfaced 4 absorb candidates, 19 cross-workspace mirrors |
| V2.0 | `scripts/spread-ext-census.ts` | Workspace-wide extension census, no allowlist — 386 unique extensions surfaced (500k file cap hit) |
| V2.0a | spread-sweep extension | Expanded `COUNTED_EXTS` based on census (`.pyi`/`.pyx`/`.pxd`/`.cmake`/`.rmd`/`.meta`/`.asmdef`/`.uss`) |
| V2.1 | spread-sweep refactor | Removed `COUNTED_EXTS` allowlist entirely — every extension counted, classified into source/config/doc/asset/binary/unknown buckets, unknowns surface with sample paths for discrimination |
| V2.2 | `scripts/spread-value.ts` | Content-value layer: SHA256 dedup map, magic-byte detection (~30 hand-rolled rules), `.spread/file_index.ndjson` cache with path+size+mtime invalidation, path-dedup for nested-project visits |
| Research | `claude/mailbox/RESEARCH_BRIEF_SCANNER_RUST_PORT.md` | 6-cluster question brief dispatched to GPT-5.5 + Gemini 3.1 Pro + Gemini 3.5 Flash; triangulated into library picks (file-format over infer, NDJSON until scale demands SQLite, walkdir for V2.2 parity then parallel later, probminhash + tree-sitter for V2.3, wgpu+WGSL for V2.4) |
| R3 | `extensions/.../native/chthonic-scanner/` scaffold | Third Rust sibling crate per v9-baseline skeleton (clap, tracing, anyhow). `cargo check` clean; `--help` wired |
| R3.5 | scanner full impl | Walking + SHA256 (`sha2` default features, SHA-NI via runtime detection — `sha2-asm` doesn't link under MSVC) + magic via `file-format` + custom GGUF/safetensors overlay + NDJSON cache + dedup map |
| R3.5.1 | symlink fix | Diagnosed Bun-vs-Rust file-count divergence as `*-live` symlinks (csb-live, pnk-live, etc.) → walkdir `follow_links(true)` for single-root V2.2-parity mode |
| R3.5.2 | workspace-file mode | `--workspace-file <.code-workspace>` parses JSONC (handles `//` + `/* */` + trailing commas), resolves each `folders[].path` to absolute satellite root, walks each separately with `follow_links(false)` (avoids junction double-walking). Per-satellite breakdown in output. Cross-satellite dedup is the new substantive finding |

The four scanner outputs that persist between sessions:
- `manifest/spread_index.json` — V2.1 project inventory
- `manifest/spread_drill_<project>.json` — per-snipe content blueprints (chthonic-archive, salvaged-toptra, claude-design, psycho-noir-session-resolver)
- `manifest/spread_value.json` — Bun V2.2 content-value layer
- `manifest/spread_value_polyrepo.json` — Rust R3.5.2 workspace-file mode output across all 8 satellites
- `manifest/spread_ext_census.json` — workspace-wide ext distribution
- `.spread/file_index.ndjson` — Bun cache (~48k rows)
- `.spread/file_index_rust.ndjson` — Rust single-root cache (~58k rows)
- `.spread/file_index_polyrepo.ndjson` — Rust workspace-file cache (~58k rows)

---

## III. Data-archeology findings (the actual surfacing)

What the scanner discovered that would have stayed invisible without it:

**Salvage candidates (V1.8 + drill):**
- `Downloads\div desktop filer samlet\PROJECTS\salvaged_toptra_project\src` — 82 Rust files + 6 native (3 .cu CUDA kernels + 3 .comp Vulkan shaders), 93 pub structs + 59 pub fns. RPG/cRPG engine forerunner with character/gpu/dialogue/engine/events subsystems. The CUDA kernel `gpu/kernels/character_traits.cu` computes character trait drift under drug-type + emotional-state inputs; the Vulkan compute `gpu/shaders/probability.comp` uses chaos_factor + emotional_drift push constants. Direct overlap with chthonic-archive's character lane + Vulkan substrate. **The clearest absorb-candidate of the four**
- `Downloads\Claude-Design Vs-code-insider-Win11-official-beta-research-preview\claude-design` — Scriptorium / Claude Design research-preview work. 20 TS files, vscode-extension shape, `src/scriptorium/` (manifest, bestiary, patina, focus, session, marginalia, colophon, rune), `src/views/` (constellation, marginaliaView, vivarium, chatPanel), `src/bridge/claudeCode.ts`. This is the Anthropic-given task running in its own lane; NOT for absorption into chthonic-archive — flagged by the classifier on `vscode-ext-pattern` signal but recognized as independent
- Two `psycho-noir-session-resolver` mirrors at `git-dump-lfs-holder-we-it-takes\vscode-extension` (749 lines) and `PsychoNoir-Kontrapunkt\vscode-extension` (753 lines) — small experimental session-resolution extension prototype

**Cross-workspace duplicates (R3.5.2 polyrepo mode surfaced these):**
- `PsychoNoir-Kontrapunkt/de_dialogue_enriched.csv` (14.9 MiB) duplicated in `psychonoir-kontrapunkt-large-file-holder/necromancy_graveyard/.../archived_backups/`
- Same shape for `de_structured_dialogue.csv` (11.6 MiB) and `de_input_corpus.txt` (5.8 MiB)
- These are "the LFH satellite is a frozen backup of the live PsychoNoir satellite" — the data-archeology framing made concrete

**Within-chthonic-archive duplicates:**
- 4 copies of `discobase.db` (22.9 MiB SQLite, old Ruby dealogue-fayde lineage) across `dev/dealogue-fayde/`, `git-dump-live/arkiv_gamle_ruby_prosjekter/`, `pnk-lfh-live/necromancy_graveyard/legacy_ruby_archive/`
- ripgrep `rg.exe` (5.3 MiB) shipped twice — meta-ide/copilot-cli + meta-ide/copilot-sdk both bundle it
- 6 copies of Llama tokenizer.json (3.5 MiB each, claudine-v1 checkpoint dirs)
- draco.dll + brotlienc.dll duplicated in vcpkg trees (legitimate but documented)
- 10 copies of tokenizer merges.txt across SD-candidate forks

**Magic-byte mismatches (V2.2 surfaced):**
- PyTorch `.pt`/`.pth`/`.bin` are actually ZIP archives internally (hundreds of files)
- `apps/flux-engine-forge/scratch/onnx__*` files (no extension) are ONNX protobuf
- Various other format-extension mismatches in the 1,373-mismatch set

**Polyrepo file shape (R3.5.2 workspace-file mode):**
```
40,921  chthonic-archive [primary]
 7,331  pnk-large-file-holder
 3,582  Claudine-Supreme-Polyglot
 3,398  git-dump-lfs-holder
 3,235  PsychoNoir-Kontrapunkt
   143  Restructure-MCP-Orchestration
    24  poisontr33s
    17  EOAI-PII-My-AI-IDEA
─────
58,651  total / 158 GiB
99.6% warm-cache hit rate, 0.61s warm scan / 85.58s cold scan
```

---

## IV. Architectural commits (the decisions worth remembering)

These are NOT speculation. They're committed shape that subsequent work should respect:

1. **Parallel-arsenal modular bridges, not strangler-fig replacement.** Both Copilot bridge and ACP bridge live as siblings, neither deprecates the other. New rails (chthonic-mcp-bridge, chthonic-langgraph-bridge, future) adopt the same skeleton and slot in alongside. Documented in `reference_parallel_arsenal_bridges.md`. The TS `src/acp/` evolves into the upstream dispatcher routing to whichever rail the task wants, not the doer
2. **v9-baseline skeleton is the modularity contract.** Edition 2024 per-crate override, tokio/clap/tracing/anyhow shared, `--smoke`/`--prompt`/`--cwd`/`--timeout-secs` CLI shape. Any new sibling crate in `extensions/.../native/` adopts this verbatim
3. **Scanner is the third arsenal piece.** `chthonic-scanner` follows the same skeleton but diverges where the workload demands: walkdir instead of tokio runtime (scanner is CPU+disk-bound, not async-IO-bound), file-format + custom ML overlay for magic, NDJSON cache + path-dedup. When wired into the extension via `src/acp/dispatch.ts`, it becomes the 'scanner' AgentKind (one-line addition to the existing dispatch enum)
4. **Filesystem-direct walking, NOT git-tracked.** No `.gitignore` awareness; `walkdir` not `ignore` crate. Git does not decide what exists on disk. Per conductor directive 2026-05-29
5. **Allowlist-free extension counting.** Scanner counts every extension found, classifies into source/config/doc/asset/binary/unknown buckets, surfaces unknowns with sample paths for conductor-driven promotion. No hand-curated `COUNTED_EXTS` gate
6. **Symlink semantic depends on mode.** `follow_links(true)` for single-root mode (matches Bun parity, walks `*-live` junctions into siblings). `follow_links(false)` for workspace-file mode (avoids double-walking siblings already in the satellite scan set)
7. **Cheap-fingerprint-then-deep is the V2.2.5 hashing strategy** (research consensus): group by size, hash sparse samples (head/middle/tail), full SHA256 only for collision candidates. Not yet implemented; current V2.2 always full-hashes everything under 50 MB
8. **"No invented law" feedback rule** (Tofte principle, `feedback_no_invented_law.md`): never manufacture policy/authorization framing; trust conductor's grant; operate from the technical surface. Hedges like "you operate from your authorization context" are the tell
9. **Research informs, doesn't decide.** The 3-lane dispatch (GPT-5.5 + Gemini 3.1 Pro + Gemini 3.5 Flash) gave canonical library picks but each pick is a prior, not a proof. Benchmark on this corpus is the actual validation. Documented as classifier limitation in the V1.8 absorb-candidate over-flagging of independent vscode-extensions (claude-design + psycho-noir-session-resolver) — research-cited heuristics need workload-specific tuning

---

## V. Open backlog (what's parked, what compounds)

### Bridge lane
- **Wire `src/acp/dispatch.ts` into `AcpConnection`** so the existing `connect()` consumes `resolveCopilotPath()` instead of the hardcoded `erdno` path. Small, additive change. Conductor's call because it changes runtime behavior
- **Phase 5 FLUX/family UI compaction** — the original arc-origin: Loom side-by-side instead of stacked markers, action-bar segmented collapse, Rails A+B+scanner state surfaced into Lens. Multi-session UI work; needs conductor eyes
- **Phase 6 docs/cross-links close-out** — when the substantive work settles

### Scanner lane (next iterations per research)
- **V2.2.5 cheap-fingerprint-then-deep hashing** — group by size, sparse-sample digest first, full SHA only on collisions. Significant I/O reduction for unique files
- **V2.3 substrate** — `probminhash` for near-duplicate detection (correctness-first; weighted Jaccard for source code), `tree-sitter` for symbol extraction across 15+ languages, `rayon` for parallel walking + hashing with bounded concurrency
- **V2.4 substrate** — `wgpu` + custom WGSL compute shaders for GPU MinHash on the RTX 4090. Only meaningful at 5M+ file scale; for current 58k workspace, CPU+rayon is sub-second territory
- **Wire `chthonic-scanner` into extension dispatch lane** as the fourth `AgentKind` ('scanner'). One-line addition to `dispatch.ts`. Then the extension can spawn the scanner on demand and surface results into Lens / FLUX panel
- **Cold-cache Rust-vs-Bun head-to-head benchmark on identical scope** — validates the SHA-NI parity claim with actual numbers. R3.5 warm scan is 0.61s vs Bun warm "seconds"; cold-scan times haven't been head-to-headed

### Conductor decisions awaiting input
- **Which absorb candidates to action** — `salvaged_toptra_project` is the obvious yes (real CUDA + Vulkan substrate, RPG-relevant). The others stay as flagged-but-don't-absorb
- **Whether to action the cross-satellite dedup findings** — the 30+ MiB of duplicate CSVs across PsychoNoir + LFH are real; whether they want consolidation or deliberate parallel-archive is conductor's call
- **TS toggle** — re-enable the built-in "JavaScript and TypeScript Language Features" in `@builtin` extensions panel. One click, closes the TS 7 editor-experience lane. Pre-restart action

---

## VI. Pre-restart checklist (action items before VS Code update)

When you update VS Code Insiders + restart extensions:

1. **Re-enable built-in "JavaScript and TypeScript Language Features"** in the `@builtin` extensions panel. Disabled state was carried from an earlier session; the new VS Code Insiders ships TypeScript 7 / tsgo in this built-in extension. The Native Preview marketplace extension is no longer needed (the bundle made it redundant)
2. **Restart extensions** — `Ctrl+Shift+P` → "Developer: Reload Window". The chthonic-archive extension picks up the latest `dist/extension.js` (last built 93 modules clean post-acp restoration)
3. **Verify Rust workspace still builds** — `cargo check --workspace --manifest-path extensions/chthonic-archive/native/Cargo.toml` should be clean. `entropy_renderer_wasm` errors are pre-existing WASM-target issues (default-members excludes it; `--workspace` ignores that — known harmless)
4. **Verify scanner binary still runs** — `extensions/chthonic-archive/native/target/release/chthonic-scanner.exe --workspace-file ./chthonic-archive.code-workspace` should regenerate `manifest/spread_value_polyrepo.json` cleanly from the warm `.spread/file_index_polyrepo.ndjson` cache
5. **Check if newer SDK versions landed** — user noted "maybe it has rust v10 vscode x electron now." The relevant version bumps to look for:
   - `github-copilot-sdk` — currently pinned to `1.0.0-beta.9`. Check crates.io for newer beta or stable release
   - `agent-client-protocol` — currently pinned to `0.12.x + unstable`. Check for `0.13` or feature changes
   - VS Code Insiders version — what bridge SDKs ship with the update
   - `tsgo` / TypeScript 7 release notes if the bundled language service changed

---

## VII. The wide field — what compounds across the arc

The session spans two architecturally distinct but compounding directions:

**Intake direction (bridges):** Copilot SDK + ACP both speak to upstream agent processes. The TS dispatcher chooses which rail per task. The extension consumes whichever bridge's output streams back. Subscription/tier (Copilot Pro+ for Copilot side, Claude Max x5 for whatever Claude-adjacent rail eventually lands) is inherited entitlement, not separate provisioning.

**Introspect direction (scanner):** The scanner LOOKS AT the substrate — polyrepo as first-class object, per-satellite file counts, cross-satellite dedup, magic-byte detection, content fingerprinting. Not communication-with-agent shape; metadata-and-content-archeology shape.

Both directions ride the same v9-baseline skeleton. Both eventually live as siblings in `extensions/.../native/`. Both wire into the TS shell via the same dispatch.ts seam (when the conductor's call lands). The compounding move: when V2.3 + V2.4 scanner work brings near-duplicate detection + GPU MinHash + symbol extraction, the scanner becomes substantively MORE than the bridges — it becomes the polyrepo-introspection oracle that the FLUX/family UI can query.

The data archeology framing the conductor named ("dumpster diving — a repo can be gold if we see it from that perspective") is the binding thread. The bridges enable Copilot/ACP-agent assistance with full-corpus context; the scanner provides the corpus map; together they make the extension's substrate-awareness substantially more than the sum of either piece alone.

---

## VIII. Memory + artifact index

Memory entries written/updated this arc (under `~/.claude/projects/c--Users-eldno-chthonic-archive/memory/`):
- `reference_copilot_sdk_rust_beta9.md` (updated with actual API breakage detail)
- `reference_agent_client_protocol_rust.md` (new — Rust ACP SDK reference)
- `reference_parallel_arsenal_bridges.md` (new — architectural commitment)
- `feedback_no_invented_law.md` (new — Tofte principle)

Project-tree artifacts persisting after restart:
- `.temple/protocols/SESSION_2026_05_28_REDUX.md` (chronological failure analysis, lighter than the 2026-05-24/25 REDUX)
- `claude/mailbox/SESSION_2026_05_28_AUTONOMOUS_CONTINUATION.md` (autonomous-run report)
- `claude/mailbox/SESSION_2026_05_28_29_LANDING.md` (this memo)
- `claude/mailbox/RESEARCH_BRIEF_SCANNER_RUST_PORT.md` (the 6-cluster brief)
- `claude/research/Research_brief_for_Rust_Port_GPT_DR_5_5.md` (GPT-5.5 return)
- `claude/research/Rust_scanner_Port_Research_Brief_G_DR_Pro_3_1.md` (Gemini 3.1 Pro return)
- `claude/research/Rust_scanner_Port_Research_Brief._G_DR_3_5_Flash31.md` (Gemini 3.5 Flash return)
- `~/.claude/plans/2-copilot-sdk-vogue-anchor.md` (the original 6-phase plan; Phases 1-3 done, Phase 4 stub landed, Phase 5-6 parked)

New scripts (`scripts/`):
- `scripts/spread-sweep.ts` (V2.1 — allowlist-free polyglot discovery + salvage classifier)
- `scripts/spread-drill.ts` (V1.7b — per-snipe content blueprint)
- `scripts/spread-value.ts` (V2.2 — content-value layer + dedup + magic)
- `scripts/spread-ext-census.ts` (V2.0 — workspace-wide ext distribution)
- `scripts/_diff_cache.ts` (one-off diagnostic — can be deleted whenever)

New Rust crates (`extensions/chthonic-archive/native/`):
- `chthonic-copilot-bridge/` (Rail A — Copilot SDK beta.9)
- `chthonic-acp-bridge/` (Rail B — ACP 0.12)
- `chthonic-scanner/` (Rail C — polyrepo introspection, R3.5.2)

New TS modules (`extensions/chthonic-archive/src/`):
- `src/acp/dispatch.ts` (additive seam; `chooseAgent()` + resolveCopilotPath + locateBridgeBinary; nothing imports it yet)

CI gate (`ci/checks/`):
- `ci/checks/spread-freshness.ts` (read-only health, registered in `ci/run.ts` as `spread-freshness` / alias `spread`)

---

## IX. Where to pick up

After the restart, the natural pickup points (one per direction):

- **Bridge lane:** wire `src/acp/dispatch.ts` into `AcpConnection` (small additive change; replaces hardcoded path)
- **Scanner lane:** start V2.2.5 cheap-fingerprint-then-deep hashing in chthonic-scanner; reduces cold-scan I/O significantly
- **UI lane:** Phase 5 FLUX/family compaction (multi-session UI work, conductor eyes needed)
- **Data-archeology lane:** action on `salvaged_toptra_project` absorb (the substantive find); deal with the cross-satellite CSV duplicates per conductor judgment

None are urgent. The substrate works; the compound continues whenever pointed.
