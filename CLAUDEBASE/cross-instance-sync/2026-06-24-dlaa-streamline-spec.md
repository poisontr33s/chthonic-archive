# Rung 2: DLAA Consumer (Streamline SDK) — Architecture Spec
**Date:** 2026-06-24
**Author:** AGY 
**For:** Claude Code / Execution Lane

---

## 1. The ABI Boundary: Extern C Scaffold
DLAA is driven via the NVIDIA Streamline SDK as an `extern C` bypass downstream of the render pass. We will not pollute the core Vulkan renderer with Streamline C++ headers. Instead, we define a pure C FFI boundary.

### 1.1 FFI Bindings (`src/render/streamline_ffi.rs`)
You will need to construct a lightweight FFI bridge for Streamline's core evaluation function and the structures it expects per-frame.

```rust
#[repr(C)]
pub struct SlConstants {
    pub jitter_offset: [f32; 2],        // In pixel space: [-0.5, 0.5]
    pub mv_scale: [f32; 2],             // Usually [1.0, 1.0] if MVs are already in pixel space, or viewport dims if NDC
    pub depth_clip_near: f32,
    pub depth_clip_far: f32,
    pub camera_view_to_clip: [f32; 16], // MUST be the unjittered projection
    pub motion_vectors_jittered: bool,  // MUST be true (we remove jitter in the shader ourselves)
    pub reset: bool,                    // Set to true for a single frame on camera cut or resize
    pub depth_inverted: bool,           // MUST be false (unless using reverse-Z)
}

#[repr(C)]
pub enum SlBufferType {
    ScalingInputColor = 0,
    Depth = 1,
    MotionVectors = 2,
    ScalingOutputColor = 3,
}

// Opaque handles representing Vulkan images passed to Streamline
#[repr(C)]
pub struct SlResource {
    pub vk_image: vk::Image,
    pub vk_image_view: vk::ImageView,
    pub vk_format: vk::Format,
    pub width: u32,
    pub height: u32,
}

extern "C" {
    // NOTE: sl_evaluate_dlaa is an invented shorthand for this blueprint. 
    // The real Streamline API requires `slSetTag` per buffer followed by `slEvaluateFeature(kFeatureDLSS)`.
    // The C-bridge must wrap those exact calls into a single execution step matching this signature.
    pub fn sl_evaluate_dlaa(
        cmd_buffer: vk::CommandBuffer,
        constants: *const SlConstants,
        input_color: *const SlResource,
        depth: *const SlResource,
        motion_vectors: *const SlResource,
        output_color: *const SlResource,
    ) -> i32;
}
```

---

## 2. Temporal State & Jitter Handoff
Streamline requires precise jitter offsets in **pixel space** (not NDC). 

From the temporal scaffold (`TemporalState`), we already compute `pixel_offset` via Halton sequences (`halton - 0.5`). 
*   **Action:** When populating `SlConstants`, map `jitter_offset` directly to `halton - 0.5`. Do not pass the NDC delta to this specific field unless the wrapper explicitly expects NDC.
*   **Matrix:** Feed the **unjittered** raw projection matrix into `camera_view_to_clip`. Do not use `TemporalFrame.projection` (which is jittered). You must keep the raw projection pre-jitter available in the render loop to feed this constant, which `TemporalState` has everything needed to reconstruct.

---

## 3. Shader Pass: Per-Pixel Motion Vectors (The Core Missing Piece)
Right now, `motion_vector_image` (`R16G16_SFLOAT`) is cleared to zero. We need a shader pass (or augment the existing geometry pass) to write true velocity.

### 3.1 Velocity Calculation (Fragment Shader)
For static geometry (the ocean/terrain), the velocity is purely driven by the camera's movement.
To compute this, the shader needs `previous_view_projection` passed in via Push Constants or a UBO.

```glsl
// 1. Reconstruct current world position or compute previous clip space directly
vec4 prev_clip = previous_view_projection * inverse(current_view_projection) * vec4(current_ndc_xy, current_depth, 1.0);
vec2 prev_ndc = prev_clip.xy / prev_clip.w;

// 2. Compute NDC velocity
vec2 velocity_ndc = current_ndc_xy - prev_ndc;

// 3. Remove jitter from the velocity
// (DLSS/DLAA expects MVs to represent true geometric motion, untainted by the temporal jitter)
velocity_ndc -= motion_vector_ndc_from_temporal_frame;

// 4. Output to R16G16_SFLOAT buffer
out_motion_vector = velocity_ndc; 
```
*Note: Streamline can be configured to accept NDC MVs (where `[-1, 1]` is screen bounds) or Pixel MVs. If NDC, ensure `mv_scale` in `SlConstants` is `[1.0, 1.0]`. If Pixel, set `mv_scale` to `[width, height]`.*

---

## 4. Pipeline Execution Order (The Bypass)
1.  **Render Pass:** Draw scene. Output to `offscreen_color_image` (`B8G8R8A8_SRGB`), `depth_image` (`D32_SFLOAT`), and the new shader writes to `motion_vector_image` (`R16G16_SFLOAT`).
2.  **Barrier:** Transition all three images to `VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL`.
3.  **Barrier:** Let Streamline manage its own internal barrier for the swapchain output using the tagged resource metadata. Do not manually pre-transition it to `GENERAL` or you will conflict and generate a layout-mismatch VUID.
4.  **Bypass Call:** Invoke the `extern C` `sl_evaluate_dlaa` function (which internally executes `slSetTag` and `slEvaluateFeature`), passing the Vulkan handles.
5.  **Barrier:** Transition `swapchain_image` to `VK_IMAGE_LAYOUT_PRESENT_SRC_KHR` (if Streamline does not natively leave it in the correct presentation layout).
6.  **Present.**

---

## Execution Handoff
Claude: The architecture is defined. You have the exact FFI boundaries, the buffer mappings, and the shader math required to populate the R16G16_SFLOAT buffer. 

Execute the shader MV write pass first, verify the buffer contains valid data (RenderDoc is your friend here, or visual output), and then wire the FFI bypass. Let me know when you are ready to compile the C-bridge or if you need the C++ stub implementation for Streamline generated.
