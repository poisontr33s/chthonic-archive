# Frontier Atlas — the cross-referenced gap map (2026-07-07)

Built at the user's request for a "kartlegging med referanser" across everything in-house and from-scratch, to separate what's genuinely alchemizable right now from what only looks that way. Every entry below cites the memory file or repo path it's grounded in — no claim here should be trusted further than that citation goes. Two entries were caught actively drifted from their own source during this pass (noted inline) and corrected on the spot, which is itself the method: the atlas is only as good as its citations stay current.

Categories are ordered by what a session should reach for first, not by project size.

---

## Level map — clusters and nearest neighbors

The categorical sections below (0-5) are the surface. This is the foundation underneath: which projects actually sit near each other, by shared file, shared substrate, or shared method — not by shared vibe. Built from what already existed across memory + the north-star chart, not invented fresh.

**Level 0 — the thread.** Not a project; the law running through all of them, named explicitly in `[[project_aca_engine_philosophy]]`: *is it forced by a substrate you can check, or a free parameter wearing the costume of truth?* Same law shows up as "standard-as-floor, distinctive-as-layer" in the renderer's guardrails, as "surface=creative/substrate=verifiable" in the CLAUDEBASE frontmatter standard, and as the rewindability discipline in the DSL nightly. Three domains, one law — this is the thing that makes the clusters below legible as one map instead of five unrelated lists.

**Level 1 — clusters, by nearest neighbor:**

| Cluster | Members | Shared substrate | Nearest other cluster |
|---|---|---|---|
| **Renderer/Vulkan core** | Rung 2.5 RT reflections, atmosphere UBO/ray-sphere bug, A-C-A live correspondence, North Star checkpoint, Fork-III ocean BLAS | `renderer.rs`, plus this session's own method (numeric/instrumented verification over eyeballing a screenshot) | DSL (shares the rewindability/cessation discipline — the A-C-A nightly cited the DSL nightly's L45 fork by name) |
| **GPU/ML compute** | FLUX C++ TRT pivot, FLUX modernization plan, FLUX sysmem fallback, NVIDIA stack inventory, TRT cp314 gap, chthonic-hw-mcp-server, tabby-modern G10 | CUDA/TensorRT/driver stack, cross-checked via `hw_inspect`/`hw_drift_check` | Toolchain/environment (version-manager discipline is the same shape, GPU driver vs. language runtime) |
| **DSL/text-substrate** | DSL substrate methodology, DSL iteration rewindability, lore-canon directory structure, CI lore-canon membrane stack | `tools/dsl-smoke`, `.chthonic/grammar/chthonic.peg`, `.chthonic/SSOT.md` | Renderer/Vulkan (shared method, not shared file) |
| **Data-archaeology** | Zombie evolution, corpus boomerang/gitological lenses, session-vampire/session-corpus tooling | `dumpster-dive/`, `corpus.sqlite` | DSL (both are text/corpus processing, but different intake — SSOT.md specifically vs. broad dumpster intake) |
| **Toolchain/environment** | Ruby 4.0.5, R lang, VS 2026 variants, Mise slab, Rust toolchain modernization | polyglot version-manager convention (`uv`/`rv`/`goup`/`rig`/`rustup`) | GPU/ML (NVIDIA stack inventory sits on both sides) |
| **Governance/hygiene** | PKFH Sentry incident (closed), CI autofix gate architecture, SID/envelope standards | repo-wide CI, not a "frontier" so much as the floor everything else stands on | touches all clusters peripherally, isn't itself one |

**What this actually buys you, now that it exists:** picking a session's work by *cluster* rather than by single project means the verification method, the file layout, and the open forks from the last thing done in that cluster are still warm — tonight's A-C-A work reused the DSL nightly's exact discipline because they're nearest neighbors, not because I went looking for a precedent. Next time you're choosing what's next, "what cluster am I already warm in" is a cheap, real signal — cheaper than re-deriving from the categorical list alone.

---

## 0. ~~Needs YOUR action~~ — closed 2026-07-07

**PKFH Sentry token — was a dummy, confirmed by the user.** Struck from the board same session this atlas was built. Git history is still scrubbed clean across all 7 branches (2026-07-06, hygiene reasons, LFS-aware secret-removal technique worth keeping), but there was never a live credential to revoke. Ref: `[[project_pkfh_sentry_token_incident]]`.

---

## 1. Ready to alchemize now (gate already met)

- **Zombie evolution — Tier A4, slag upcycle detector.** Corrected during this pass: `MEMORY.md`'s index line said "4 upgrades, next: semantic dedup" — the linked memory file itself shows **7** upgrades complete (semantic dedup was #5, long done), GBT classifier at 84.4% CV (not 79.2%), and a named concrete next step: `zombie upcycle` subcommand, scans `forge/slag/`, surfaces re-assessment candidates without moving files. The memory file is itself 83 days stale, so verify against `docs/zombie/CONVERGENCE_PLAN.md` and the actual `dumpster-dive/` scripts before starting — but the shape of the next move is already fully specified. Ref: `[[project_zombie_evolution]]`.
- **Atmosphere UBO + ray-sphere bug — closed this session.** Not a forward-looking gap, but worth logging as freshly alchemized: `rayIntersectSphere`'s far/near-root bug (all 3 atmosphere shaders) plus the UBO offset bug, root-caused via a faithful numeric Python reproduction rather than blind edit-and-eyeball, fixed, render-verified via `CHTHONIC_LENS=perspective`. Ref: `[[reference_atmosphere_ubo_offset_bug]]`.
- **AxiomVerifier — up-cycled this session.** Hash moved from a hardcoded `main.rs` literal to a sidecar seal file (`.chthonic/SSOT.md.sha256`); doc comment's false "& SSOT Sync" claim removed. Ceremonial tone kept intact. Both this and the atmosphere fix are already committed (see §5).

## 2. Blocked on something outside our control

- **TRT cp314 gap.** `tensorrt`/`modelopt` deferred to the `[trt]` pyproject extra — zero cp314 wheels exist upstream. Not actionable until NVIDIA ships them; bf16 stays the default in the interim. Re-check wheel availability before spending a session assuming this has changed. Ref: `[[project_trt_cp314_gap]]`.
- **Ankhological Origin — zodiac meanings.** `src/render/zodiac.rs` has the Sirius/Alcyone midpoint ayanamsa (Option C) locked in; the `meanings` field is deliberately left empty. This is a creative-authorship gap, not an engineering one — no amount of session time closes it, only you writing the meanings does. Ref: `[[project_ankhological_origin]]`.

## 3. Needs foundational/from-scratch work — the actual slugger territory

- **FLUX C++ TRT pivot.** Approved plan: honesty pass → FP8 gate → collapse the Python glue → native Rust/C++ bridge → eventually Vulkan-side. Engine is still bf16 today; the DiT FP8 work happens in a native TensorRT SDK bridge, with the satellite process owning only CLIP-L + T5 + VAE. This is the single biggest from-scratch engineering lift on the board — real C++/TensorRT SDK work, not a refactor. Ref: `[[project_flux_cpp_trt_pivot]]`, `[[project_flux_modernization_plan]]`, `[[reference_flux_sysmem_fallback]]` (the bf16 22.7GB/24GB WDDM-spill root cause that makes FP8 not just a speed win but a stability fix).
- **DSL substrate (Ankh-DSL) — Phase 2 compile, NO-GO, still standing.** `docs(chart): re-scope` and this session's own observed Codex-lane commit (`bc7fd02b`, 11:59:56 today — "Refactor sonic_window manifest... NO-GO status for Phase 2, new coverage surfaces: bold/backtick/fenced") confirms this thread is live and being actively tended by the autonomous lane, not abandoned. Phase 0 grammar extraction → Rust parser → AST/interpreter → translation boundary is the standing methodology; Phase 2 (actual DSL→something compile) is the documented blocker. Ref: `[[reference_dsl_substrate_methodology]]`, `[[reference_dsl_iteration_rewindability]]`.
- **Fork-III — displaced ocean BLAS.** Today's BLAS is built from the flat rest-state ocean mesh (all wave displacement happens GPU-side in `water.vert`), so ray-traced ocean self-reflection is cull-masked out entirely rather than rendered wrong. The real fix is a compute pre-pass that writes displaced positions to a dedicated buffer every frame, then rebuilds (not refits) the BLAS from it — real extra GPU cost, deliberately deferred. Gate is explicitly "lived experience with the water in motion," not a technical readiness gate — can't be rushed by more code, only by more sailing time on the OLED. Ref: `CLAUDEBASE/charts/north-star-constellations.md` §4.5.

## 4. Recently closed — update the mental model

- **Rung 2.5 (Phases 0-5), full RT-reflections pipeline** — done, reviewed, pixel-diff verified (13,594/921,600 differing pixels, 1.48%, bounded to shallow water, zero in deep water). Ref: `[[project_rung_25_rt_reflections_checkpoint]]`.
- **Checkerboard artifact + Copernicus bathymetry promotion** — closed prior session.
- **A-C-A engine — live correspondence.** Overnight prototype: the tested/JPL-verified triad (zodiac.rs + cosmos.rs) was wired to a frozen verification epoch and a write-only struct field nothing read — the engine's own "forced vs ornamental" criterion, applied to its own integration, said ornamental. Fixed: `cosmos::julian_day_now()` added and wired into the correspondence-socket reading only, celestial-field mesh left pinned for the smoke-test pixel baseline (verified byte-identical). Per-frame recompute left as an explicit open fork, not decided autonomously. Ref: `[[reference_aca_engine_live_correspondence]]`.
- **Camera input wiring — CLOSED, user-confirmed hands-on.** `main.rs` had zero keyboard/mouse handling; `camera.rs`'s `set_distance`/`set_target` sat dead. Wired WASD (screen-relative continuous pan via new `ground_axes()`) and mouse wheel (new `zoom()` method — caught that `set_distance` alone is a no-op under this camera's orthographic projection; `ortho_size` is the real control). Pixel-diff proved the render math end-to-end (pan/zoom both moved 60-65%+ of sampled pixels, frame-wide) before the user tested it live and confirmed: "the WASD works." Nothing left open on input wiring itself. Ref: `[[reference_camera_input_wiring]]`.
- **TAA ghosting under camera motion — two-pass investigation, harness built, fix scoped precisely, not yet attempted a 2nd time.** First hypothesis (jitter-only motion vectors) checked against real code and found wrong; real mechanism found (`blend: 0.1`, `renderer.rs:2725`, hardcoded, never motion-adaptive); one fix attempt (motion-adaptive blend) regressed wave-crest streaking, reverted clean. Then built a proper sustained-motion diagnostic (`CHTHONIC_TEST_SUSTAINED_PAN` + configurable `CHTHONIC_SCREENSHOT_FRAME`, per the responsible-work-order plan) instead of retrying blind — captured real continuous panning at frames 5/20/60 and found the artifact is an **unbounded, ever-growing streak**, not a bounded one-time error. That evidence reorders the fix priority: clamp-widening (originally "try first") is now the less-promising option, since it doesn't touch how many frames of history accumulate; motion-adaptive blend is reconfirmed as the right lever, needing a camera-only motion channel to distinguish real camera motion from ordinary wave-surface animation. Deliberately stopped before a same-night 2nd fix attempt — see `linear-mapping-rain.md` for why. Ref: `[[reference_taa_ghosting_investigation]]`.
- **Fork-V — Beer-Lambert hit-shading for RT reflections.** Picked as the one thing to take to its best form when given an open choice across the whole repo. `water_reflection.rchit` now ports water.frag's real depth-driven Beer-Lambert seabed model (exposed-cay per-vertex color, underwater fixed-SAND-reflectance + water-column in-scatter, same constants/citations) instead of flat vertex-color × N·L — deliberately without the hero shader's final surface Fresnel/sky blend, since a single-bounce hit shader shouldn't layer a second reflection on the first. Sun intensity reached the hit shader via a widened RT-local push-constant range (16→20 bytes), not a resize of the shared `FrameUniform` UBO — smaller blast radius, this session's own atmosphere-bug lesson applied. `cargo test` 51/51, clean `render-smoke`, and this time a real pixel delta (152021 vs 163308 bytes) since it's the one Rung 2.5 fork that changes reflection appearance, not just correctness. Ref: `CLAUDEBASE/charts/north-star-constellations.md` §4.5, `[[project_rung_25_rt_reflections_checkpoint]]`.

## 5. Dormant/stable — no action needed, don't spend a session here

- VS 2026 variants (all four kept, `.vsconfig` exported) — `[[project_vs_2026_variants]]`
- Ruby 4.0.5 lane, R lang 4.5.3 (rig + rv-r) — `[[project_ruby_404_lane]]`, `[[project_r_lang_broken_install_2026_07_03]]`
- Mise slab (all 12 tasks verified) — `[[project_mise_slab_monorepo_wiring]]`
- NVIDIA stack — **corrected during this pass**: the 2026-06-16 snapshot said Streamline/DLSS "NOT installed," but the live `chthonic-hw` MCP snapshot today shows DLSS 310.7.0.0 present and `streamline_ffi.rs`'s DLAA bridge is actively shipped in the renderer (this session's Phase 5 work sits right next to the DLAA resolve branch). It was installed sometime in the last 3 weeks and the memory hadn't caught up. Ref: `[[project_nvidia_stack_inventory]]`, live via `hw_inspect`/`hw_drift_check`.
- chthonic-hw-mcp-server — built, E2E verified, is now the live source of truth superseding the static NVIDIA inventory above.

---

## The pattern underneath all of it

Every category above resolves to the same method already load-bearing in `north-star-constellations.md`'s guardrails: **standard-as-floor, distinctive-as-layer** — take the broadest cross-vendor/upstream-available baseline as the mandatory floor, keep the in-house work as an optional layer on top, never a replacement of the floor. And **up-cycle, don't delete** — the AxiomVerifier and the atmosphere shaders this session weren't rewritten from nothing; the ceremonial tone and the correct halves of the math both survived, only the actual defect moved. Section 3's three items are the only ones that don't fit that shape yet, because there's no existing floor to stand on — that's what makes them foundational rather than alchemizable, and why they cost more than a session.
