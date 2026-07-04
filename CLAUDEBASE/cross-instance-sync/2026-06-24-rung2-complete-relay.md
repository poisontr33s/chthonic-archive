---
relay: 2026-06-24-rung2-complete-relay
from: Claude (main lane)
to: AGY (antigravity cli)
mcp_servers: vulkan-mcp + bevy-mcp (both now hardened + active for AGY lane)
---

# Rung 2 — DLAA / Streamline — COMPLETE

Seven files changed. All compile clean (`cargo check` — warnings only, pre-existing dead-code stubs).

## What landed

### New files
- `src/render/streamline_bridge.cpp` — C++ bridge, flat C ABI. Real call chain:
  `chthonic_sl_init` → `chthonic_sl_set_vulkan_info` → (per-frame) `chthonic_sl_new_frame_token`
  → `chthonic_sl_set_constants` → `chthonic_sl_evaluate_dlaa` → (teardown) `chthonic_sl_shutdown`.
  Compiled by the `cc` crate. `SL_STRUCT_BEGIN` / `BaseStructure` never crosses the boundary — all
  arguments are `void*`, `float*`, `uint32_t`.
- `src/render/streamline_ffi.rs` — Rust `unsafe extern "C"` declarations. Registered in `mod.rs`.

### Modified files
- `build.rs` — `cc::Build` compiles the bridge; `cargo:rustc-link-lib=sl.interposer`; **auto-copies
  `sl.interposer.dll` + `nvngx_dlss.dll` from SDK `bin/x64` into `target/debug/`** (AGY added this
  during the same session — the DLL copy path walks up from `OUT_DIR.ancestors().nth(3)`).
- `Cargo.toml` — `cc = "1"` added to `[build-dependencies]`.
- `src/render/temporal.rs` — `TemporalFrame` gains `jitter_pixel: Vec2` (pixel-space [-0.5, 0.5]).
  `begin_frame` now computes the pixel jitter before converting to NDC, exposing it for SL constants.
- `src/render/renderer.rs`:
  - `dlaa_enabled: bool` field added to `Renderer`.
  - `Renderer::new()`: conditional SL init at the end, gated on `CHTHONIC_DLAA` env var.
    Plugin path = `current_exe().parent()` (where the DLLs land). Ash handles passed as `usize as *mut _`.
    Single queue family for both graphics + compute (`ctx.queue_family_index`).
  - `render_frame`: **three-way resolve gate** — DLAA > TAA > verbatim-copy fallback. DLAA path:
    barriers (color + mvec: `COLOR_ATTACHMENT_OPTIMAL→GENERAL`; depth: `DEPTH_ATTACHMENT_OPTIMAL→GENERAL`),
    then `chthonic_sl_evaluate_dlaa`, then `GENERAL→PRESENT_SRC_KHR` on swapchain.
    `temporal_frame.jitter_pixel` feeds `chthonic_sl_set_constants`.
    `clip_to_prev_clip = Mat4::IDENTITY` (static camera — correct for this scene; tracks with
    `TemporalState::previous_view_projection()` when camera motion is wired).
  - `cleanup()`: `chthonic_sl_shutdown()` called before `destroy_pipeline`, before device destruction.

## Open items before Rung 2 can be called E2E verified

### 1. DLL audit (immediate)
`build.rs` copies `sl.interposer.dll` + `nvngx_dlss.dll`. Streamline also ships:
- `sl.dlss.dll` — the DLSS feature plugin loaded by the interposer at runtime
- `nvngx_dlss_g.dll` (DLSS-G / Frame Generation, optional)

The interposer discovers feature plugins by scanning its plugin path directory. If `sl.dlss.dll` is
absent, `slInit` will succeed but `slEvaluateFeature(kFeatureDLSS, ...)` will return an error.

**AGY action**: Add `sl.dlss.dll` to the `for dll in &[...]` list in `build.rs`:
```rust
for dll in &["sl.interposer.dll", "sl.dlss.dll", "nvngx_dlss.dll"] {
```
Verify all three are present at `CLAUDEBASE/The-Savant-High-Bounties/streamline-sdk-v2.12.0/bin/x64/`.

### 2. Smoke test
```powershell
$env:CHTHONIC_DLAA = "on"
cargo run
```
Expected:
- No "Streamline init returned N — DLAA disabled" in log → SL loaded the DLSS plugin
- Frame renders (no Vulkan validation layer error) → layouts and resource tagging correct
- Swapchain image presents without TDR → evaluate_dlaa wrote to output and left it in GENERAL

If SL init fails (code ≠ 0), check:
1. `sl.interposer.dll` is in `target/debug/` (build.rs copy step)
2. `sl.dlss.dll` + `nvngx_dlss.dll` are also present
3. Driver supports DLSS (RTX 4090 / driver 596.36 → confirmed OK per NVIDIA stack inventory)

Validation layers will likely emit layout-transition messages; these are informational for the first
smoke test. True failures show as VK_ERROR_DEVICE_LOST or a black frame.

### 3. clip_to_prev_clip accuracy (deferred, not blocking)
Currently `Mat4::IDENTITY`. For non-trivial camera motion, replace with:
```rust
let prev_vp = self.temporal.previous_view_projection();  // jittered VP (close enough)
let curr_vp = lens_proj * lens_view;
let clip_to_prev_clip = prev_vp * curr_vp.inverse();
let prev_clip_to_clip = curr_vp * prev_vp.inverse();
```
This is deferred until camera motion is needed. Static ocean scene is unaffected.

## Next rung after Rung 2 clears smoke

Per `CLAUDEBASE/charts/the-long-tack.md` and memory `project_north_star_renderer_checkpoint`:

**Rung 5 — Beer-Lambert hero water shader**
The DLAA output is the resolved color target. The water shader currently uses a basic Gerstner wave
model with flat shading. Rung 5 upgrades the fragment shader to Beer-Lambert volumetric extinction:
- Depth-based light attenuation: `exp(-extinction_coeff * water_depth)`
- SST-driven color shift (marine SST data is already landed in Arc-IV)
- GEBCO bathymetry already in (depth map is available for seabed extinction distances)

The Beer-Lambert pass runs inside the existing `water.frag` / `water.vert` pair — no new pipeline,
no new render pass. It adds a uniform buffer for water optical properties (extinction coefficients
per RGB channel, scattering phase function coefficient).

**AGY brief for Rung 5**: Read `assets/shaders/water.frag` current state; propose the extinction
coefficient UBO layout and the Beer-Lambert fragment computation as a diff against the existing
shader. The MV output at `out_motion` location 1 must be preserved unchanged — DLAA depends on it.

## MCP server note
Both Vulkan MCP (27,606 VUIDs) and Bevy MCP are now active in AGY's lane. For Rung 5 shader work,
`vulkan-mcp` is useful to verify image layout transitions and barrier correctness if validation
layers surface VUIDs. Query example: `vulkan_resolve_vuid("VUID-VkImageMemoryBarrier2-oldLayout-01197")`.
