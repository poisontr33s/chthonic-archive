//! Render module - Vulkan 1.3 Dynamic Rendering Pipeline
//!
//! "We do not accept legacy Render Passes. We demand Dynamic Rendering."
//! — Gemini 3 Pro Thinking (Architect)
//!
//! This module implements the Vulkan 1.3 graphics backend with:
//! - Dynamic Rendering (no legacy VkRenderPass)
//! - RTX 4090 optimization path
//! - Isometric Camera System
//! - Ray Tracing Pipeline preparation (Phase 13)

pub mod vulkan;
pub mod swapchain;
pub mod pipeline;
pub mod renderer;
pub mod camera;

pub use vulkan::VulkanContext;
pub use swapchain::VulkanSwapchain;
pub use pipeline::{VulkanPipeline, PushConstants, Vertex, triangle_vertices};
pub use renderer::Renderer;
pub use camera::IsometricCamera;
