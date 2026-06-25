//! Rust FFI declarations for the Streamline C++ bridge (streamline_bridge.cpp).
//!
//! All Vulkan handles are passed as `*mut c_void`.  Ash handle types expose
//! `as_raw() -> u64`; cast to `*mut c_void` via `handle.as_raw() as usize as *mut _`.
//!
//! `FrameToken` is an opaque SL-owned object; store the returned pointer and
//! hand it back each frame — do not free it, SL owns the lifetime.

//! @SID:    RENDER_STREAMLINE_FFI_V1
//! @Shabti: Streamline FFI

use std::ffi::c_int;
use std::os::raw::c_void;

unsafe extern "C" {
    /// Initialize Streamline.  Call once at renderer startup before any feature use.
    /// `plugin_path`: UTF-16 (Windows wide-char) path to the sl.*.dll directory, or null.
    /// Returns 0 on success (sl::Result::eOk).
    pub fn chthonic_sl_init(plugin_path: *const u16, app_id: u32) -> c_int;

    /// Provide the already-created Vulkan handles to Streamline.
    /// Must be called immediately after vkCreateDevice.
    pub fn chthonic_sl_set_vulkan_info(
        vk_instance: *mut c_void,
        vk_physical_device: *mut c_void,
        vk_device: *mut c_void,
        graphics_queue_index: u32,
        graphics_queue_family: u32,
        compute_queue_index: u32,
        compute_queue_family: u32,
    ) -> c_int;

    /// Seed per-viewport DLSS options before the first DLSS evaluation.
    /// Uses the bridge's fixed viewport id 0, matching constants and evaluate inputs.
    pub fn chthonic_sl_set_dlaa_options(width: u32, height: u32) -> c_int;

    /// Present through Streamline's proxied vkQueuePresentKHR. The proxy runs
    /// common present hooks and then forwards to the real driver present.
    pub fn chthonic_sl_vk_queue_present(queue: *mut c_void, present_info: *const c_void) -> c_int;

    /// Submit through Streamline's proxied vkQueueSubmit when available.
    pub fn chthonic_sl_vk_queue_submit(
        queue: *mut c_void,
        submit_count: u32,
        submits: *const c_void,
        fence: *mut c_void,
    ) -> c_int;

    /// Obtain a per-frame token for the given frame index.
    /// Returns an opaque pointer owned by SL; null on failure.
    /// Store it and pass it back to set_constants / evaluate_dlaa each frame.
    pub fn chthonic_sl_new_frame_token(frame_index: u32) -> *mut c_void;

    /// Set per-frame temporal constants.
    /// `proj_col_major` / `inv_proj_col_major`: unjittered projection and its inverse,
    ///   16-float column-major arrays (glam `Mat4::to_cols_array()`).
    /// `clip_to_prev_clip` / `prev_clip_to_clip`: temporal reprojection matrices.
    /// `mvec_scale_*`: converts motion vector texture units to pixels. The water shader writes
    ///   UV-space `previous - current`, so pass render width/height.
    /// `motion_vectors_jittered`: 0 — our shader already removes jitter from MVs.
    /// `reset`: 1 on camera cut or swapchain resize.
    pub fn chthonic_sl_set_constants(
        frame_token: *mut c_void,
        jitter_x: f32,
        jitter_y: f32,
        proj_col_major: *const f32,
        inv_proj_col_major: *const f32,
        clip_to_prev_clip_col_major: *const f32,
        prev_clip_to_clip_col_major: *const f32,
        near_z: f32,
        far_z: f32,
        fov_y: f32,
        aspect: f32,
        mvec_scale_x: f32,
        mvec_scale_y: f32,
        motion_vectors_jittered: c_int,
        reset: c_int,
    ) -> c_int;

    /// Tag the four render targets and evaluate DLAA in a single call.
    /// `native_*`: VkImage as u64 cast to `*mut c_void` (handle.as_raw() as usize as *mut _).
    /// `view_*`:   VkImageView, same scheme.
    /// `state_*`:  VkImageLayout value at the time of tagging.
    ///   COLOR_ATTACHMENT_OPTIMAL=2, GENERAL=1, DEPTH_ATTACHMENT_OPTIMAL=0x3B9ACB68u32.
    /// Returns 0 on success.
    #[allow(clippy::too_many_arguments)]
    pub fn chthonic_sl_evaluate_dlaa(
        frame_token: *mut c_void,
        cmd_buffer: *mut c_void,
        native_color: *mut c_void,
        view_color: *mut c_void,
        state_color: u32,
        native_depth: *mut c_void,
        view_depth: *mut c_void,
        state_depth: u32,
        native_mvec: *mut c_void,
        view_mvec: *mut c_void,
        state_mvec: u32,
        native_output: *mut c_void,
        view_output: *mut c_void,
        state_output: u32,
        width: u32,
        height: u32,
        color_format: u32,
        depth_format: u32,
        mvec_format: u32,
        output_format: u32,
        color_usage: u32,
        depth_usage: u32,
        mvec_usage: u32,
        output_usage: u32,
    ) -> c_int;

    /// Shut down Streamline.  Call on renderer teardown.
    pub fn chthonic_sl_shutdown();
}
