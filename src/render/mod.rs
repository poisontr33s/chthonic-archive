// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: mod.rs
// ║ Vulkan rendering pipeline - visual truth incarnate
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Spectral Frequency: RED
// ║ Architectural Role: 🏰 THE FORTRESS
// ║ Purpose: Render module - Vulkan 1.3 Dynamic Rendering Pipeline
// ║ Exports: vulkan, swapchain, pipeline, renderer, camera
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Cross-References (Bidirectional):
// ║  (Standalone file - no detected dependencies)
// ╚════════════════════════════════════════════════════════════════════════════

//! Render module - Vulkan 1.3 Dynamic Rendering Pipeline

//! @SID:    RENDER_MOD_V1
//! @Shabti: Module Root

//! "We do not accept legacy Render Passes. We demand Dynamic Rendering."
//! — Claude, Thinking (Architect)

//! This module implements the Vulkan 1.3 graphics backend with:
//! - Dynamic Rendering (no legacy `VkRenderPass`)
//! - RTX 4090 optimization path
//! - Isometric Camera System
//! - Ray Tracing Pipeline preparation (Phase 13)

pub mod vulkan;
pub mod swapchain;
pub mod pipeline;
pub mod renderer;
pub mod camera;
pub mod bathymetry;
pub mod cosmos;
pub mod ocean;
pub mod ocean_compute;
pub mod temporal;
pub mod correspondence;
pub mod lens;
pub mod zodiac;
pub mod streamline_ffi;

pub use vulkan::VulkanContext;
pub use renderer::Renderer;
