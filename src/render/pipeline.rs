// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: pipeline.rs
// ║ Vulkan rendering pipeline - visual truth incarnate
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Spectral Frequency: RED
// ║ Architectural Role: 🏰 THE FORTRESS
// ║ Purpose: Vulkan 1.3 Graphics Pipeline with Dynamic Rendering
// ║ Exports: VulkanPipeline, PushConstants, Vertex, binding_description, attribut
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Cross-References (Bidirectional):
// ║  (Standalone file - no detected dependencies)
// ╚════════════════════════════════════════════════════════════════════════════

//! Vulkan 1.3 Graphics Pipeline with Dynamic Rendering
//!
//! @SID:    RENDER_PIPELINE_V1
//! @Shabti: Pipeline
//!
//! "I will dissect your darkest fantasy and show you the beauty hidden within."
//! — Dr. Lysandra Thorne
//!
//! This pipeline implementation:
//! - Uses `VkPipelineRenderingCreateInfo` (no `VkRenderPass`)
//! - Loads SPIR-V shaders compiled at build time
//! - Configures triangle rendering with push constants for MVP
//! - Prepares for isometric grid rendering

use anyhow::{Context, Result};
use ash::{vk, Device};
use log::{debug, info, warn};
use std::env;
use std::fs;
use std::io::ErrorKind;
use std::path::{Path, PathBuf};
use std::time::Instant;

/// Graphics pipeline for rendering
pub struct VulkanPipeline {
    pub pipeline: vk::Pipeline,
    pub pipeline_layout: vk::PipelineLayout,
    pub vertex_shader: vk::ShaderModule,
    pub fragment_shader: vk::ShaderModule,
    pub pipeline_cache: vk::PipelineCache,
}

#[derive(Clone, Copy, Debug)]
enum PipelineCacheState {
    ColdStart,
    WarmStart,
    RebuiltFromInvalidData,
}

impl PipelineCacheState {
    fn as_str(self) -> &'static str {
        match self {
            Self::ColdStart => "cold",
            Self::WarmStart => "warm",
            Self::RebuiltFromInvalidData => "rebuild",
        }
    }
}

const PIPELINE_CACHE_SCHEMA_VERSION: u32 = 1;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum ShaderLanguage {
    Glsl,
    Hlsl,
}

impl ShaderLanguage {
    fn as_str(self) -> &'static str {
        match self {
            Self::Glsl => "glsl",
            Self::Hlsl => "hlsl",
        }
    }
}

/// Push constants: MVP + sun vector (`layer_color` slot) + params [time, mode] (224 bytes)
#[repr(C)]
#[derive(Clone, Copy, Debug)]
pub struct PushConstants {
    pub model: [[f32; 4]; 4],
    pub view: [[f32; 4]; 4],
    pub projection: [[f32; 4]; 4],
    pub layer_color: [f32; 4],
    pub params: [f32; 4],
}

impl Default for PushConstants {
    fn default() -> Self {
        Self {
            model: identity_matrix(),
            view: identity_matrix(),
            projection: identity_matrix(),
            layer_color: [1.0, 1.0, 1.0, 1.0],
            params: [0.0, 0.0, 0.0, 0.0],
        }
    }
}

/// 4x4 identity matrix
fn identity_matrix() -> [[f32; 4]; 4] {
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
}

/// Vertex data for rendering (position + normal + color)
#[repr(C)]
#[derive(Clone, Copy, Debug)]
pub struct Vertex {
    pub position: [f32; 3],
    pub normal: [f32; 3],
    pub color: [f32; 3],
}

impl Vertex {
    /// Get vertex input binding description
    pub fn binding_description() -> vk::VertexInputBindingDescription {
        vk::VertexInputBindingDescription::default()
            .binding(0)
            .stride(u32::try_from(std::mem::size_of::<Self>()).expect("Vertex size too large"))
            .input_rate(vk::VertexInputRate::VERTEX)
    }

    /// Get vertex attribute descriptions (position, normal, color)
    pub fn attribute_descriptions() -> [vk::VertexInputAttributeDescription; 3] {
        let f3 = u32::try_from(std::mem::size_of::<[f32; 3]>()).unwrap();
        [
            // Position at location 0
            vk::VertexInputAttributeDescription::default()
                .binding(0)
                .location(0)
                .format(vk::Format::R32G32B32_SFLOAT)
                .offset(0),
            // Normal at location 1
            vk::VertexInputAttributeDescription::default()
                .binding(0)
                .location(1)
                .format(vk::Format::R32G32B32_SFLOAT)
                .offset(f3),
            // Color at location 2
            vk::VertexInputAttributeDescription::default()
                .binding(0)
                .location(2)
                .format(vk::Format::R32G32B32_SFLOAT)
                .offset(f3 * 2),
        ]
    }
}

impl VulkanPipeline {
    /// Create a new graphics pipeline for Dynamic Rendering
    ///
    /// # Safety
    /// Requires valid Vulkan device handle
    pub unsafe fn new(
        device: &Device,
        physical_device_properties: &vk::PhysicalDeviceProperties,
        color_format: vk::Format,
    ) -> Result<Self> {
        info!("╔══════════════════════════════════════════════════════════════╗");
        info!("║   GRAPHICS PIPELINE - Dynamic Rendering Mode                 ║");
        info!("╚══════════════════════════════════════════════════════════════╝");
        let pipeline_start = Instant::now();

        let shader_language = Self::selected_shader_language();
        let (vertex_spv, fragment_spv) = Self::load_shader_pair(shader_language)?;

        info!("   Shader language: {}", shader_language.as_str());
        info!("   Vertex shader: {} bytes", vertex_spv.len());
        info!("   Fragment shader: {} bytes", fragment_spv.len());

        let shader_signature = Self::shader_signature(&vertex_spv, &fragment_spv);
        let cache_path = Self::pipeline_cache_path(
            physical_device_properties,
            color_format,
            shader_language.as_str(),
            shader_signature,
        );
        let (pipeline_cache, cache_state) = Self::create_pipeline_cache(device, &cache_path)?;
        info!(
            "   Pipeline cache: {} ({})",
            cache_state.as_str(),
            cache_path.display()
        );

        let vertex_shader = Self::create_shader_module(device, &vertex_spv)?;
        let fragment_shader = Self::create_shader_module(device, &fragment_spv)?;
        info!("✅ Shader modules created");

        // Shader stages
        let entry_point = c"main";

        let vertex_stage = vk::PipelineShaderStageCreateInfo::default()
            .stage(vk::ShaderStageFlags::VERTEX)
            .module(vertex_shader)
            .name(entry_point);

        let fragment_stage = vk::PipelineShaderStageCreateInfo::default()
            .stage(vk::ShaderStageFlags::FRAGMENT)
            .module(fragment_shader)
            .name(entry_point);

        let shader_stages = [vertex_stage, fragment_stage];

        // Vertex input state
        let binding_desc = Vertex::binding_description();
        let binding_descriptions = [binding_desc];
        let attribute_descriptions = Vertex::attribute_descriptions();

        let vertex_input_state = vk::PipelineVertexInputStateCreateInfo::default()
            .vertex_binding_descriptions(&binding_descriptions)
            .vertex_attribute_descriptions(&attribute_descriptions);

        // Input assembly (triangle list)
        let input_assembly_state = vk::PipelineInputAssemblyStateCreateInfo::default()
            .topology(vk::PrimitiveTopology::TRIANGLE_LIST)
            .primitive_restart_enable(false);

        // Dynamic viewport and scissor
        let dynamic_states = [vk::DynamicState::VIEWPORT, vk::DynamicState::SCISSOR];
        let dynamic_state = vk::PipelineDynamicStateCreateInfo::default()
            .dynamic_states(&dynamic_states);

        // Viewport state (dynamic, so count only)
        let viewport_state = vk::PipelineViewportStateCreateInfo::default()
            .viewport_count(1)
            .scissor_count(1);

        // Rasterization state
        // NOTE: Disable culling for debugging - in Vulkan Y is flipped!
        let rasterization_state = vk::PipelineRasterizationStateCreateInfo::default()
            .depth_clamp_enable(false)
            .rasterizer_discard_enable(false)
            .polygon_mode(vk::PolygonMode::FILL)
            .line_width(1.0)
            .cull_mode(vk::CullModeFlags::NONE)  // DISABLED FOR DEBUG
            .front_face(vk::FrontFace::CLOCKWISE)  // Vulkan Y-flip means CW is front
            .depth_bias_enable(false);

        // Multisampling (no MSAA for now)
        let multisample_state = vk::PipelineMultisampleStateCreateInfo::default()
            .sample_shading_enable(false)
            .rasterization_samples(vk::SampleCountFlags::TYPE_1);

        // Color blend attachment (alpha blending)
        let color_blend_attachment = vk::PipelineColorBlendAttachmentState::default()
            .color_write_mask(vk::ColorComponentFlags::RGBA)
            .blend_enable(true)
            .src_color_blend_factor(vk::BlendFactor::SRC_ALPHA)
            .dst_color_blend_factor(vk::BlendFactor::ONE_MINUS_SRC_ALPHA)
            .color_blend_op(vk::BlendOp::ADD)
            .src_alpha_blend_factor(vk::BlendFactor::ONE)
            .dst_alpha_blend_factor(vk::BlendFactor::ZERO)
            .alpha_blend_op(vk::BlendOp::ADD);

        let color_blend_attachments = [color_blend_attachment];
        let color_blend_state = vk::PipelineColorBlendStateCreateInfo::default()
            .logic_op_enable(false)
            .attachments(&color_blend_attachments);

        // Depth-stencil (rung 3: the heightfield needs correct occlusion)
        let depth_stencil_state = vk::PipelineDepthStencilStateCreateInfo::default()
            .depth_test_enable(true)
            .depth_write_enable(true)
            .depth_compare_op(vk::CompareOp::LESS)
            .depth_bounds_test_enable(false)
            .stencil_test_enable(false);

        // Push constant range (matrices + color = 208 bytes)
        let push_constant_range = vk::PushConstantRange::default()
            .stage_flags(vk::ShaderStageFlags::VERTEX | vk::ShaderStageFlags::FRAGMENT)
            .offset(0)
            .size(u32::try_from(std::mem::size_of::<PushConstants>()).expect("Push constants size too large"));

        let push_constant_ranges = [push_constant_range];
        let pipeline_layout_info = vk::PipelineLayoutCreateInfo::default()
            .push_constant_ranges(&push_constant_ranges);

        let pipeline_layout = device
            .create_pipeline_layout(&pipeline_layout_info, None)
            .context("Failed to create pipeline layout")?;

        info!("✅ Pipeline layout created (208 bytes push constants)");

        // === DYNAMIC RENDERING (Vulkan 1.3) ===
        // No VkRenderPass! Use VkPipelineRenderingCreateInfo instead
        let color_formats = [color_format];
        let mut rendering_info = vk::PipelineRenderingCreateInfo::default()
            .color_attachment_formats(&color_formats)
            .depth_attachment_format(vk::Format::D32_SFLOAT);

        // Create graphics pipeline
        let pipeline_info = vk::GraphicsPipelineCreateInfo::default()
            .stages(&shader_stages)
            .vertex_input_state(&vertex_input_state)
            .input_assembly_state(&input_assembly_state)
            .viewport_state(&viewport_state)
            .rasterization_state(&rasterization_state)
            .multisample_state(&multisample_state)
            .color_blend_state(&color_blend_state)
            .depth_stencil_state(&depth_stencil_state)
            .dynamic_state(&dynamic_state)
            .layout(pipeline_layout)
            .push_next(&mut rendering_info)
            // render_pass is null for Dynamic Rendering
            .render_pass(vk::RenderPass::null())
            .subpass(0);

        let pipelines = device
            .create_graphics_pipelines(pipeline_cache, &[pipeline_info], None)
            .map_err(|(_, e)| e)
            .context("Failed to create graphics pipeline")?;

        let pipeline = pipelines[0];
        Self::persist_pipeline_cache(device, pipeline_cache, &cache_path);

        info!("═══════════════════════════════════════════════════════════════");
        info!("🔥 GRAPHICS PIPELINE CREATED - Dynamic Rendering Active!");
        info!(
            "   Pipeline build time: {} ms",
            pipeline_start.elapsed().as_millis()
        );
        info!("═══════════════════════════════════════════════════════════════");

        Ok(Self {
            pipeline,
            pipeline_layout,
            vertex_shader,
            fragment_shader,
            pipeline_cache,
        })
    }

    fn selected_shader_language() -> ShaderLanguage {
        match env::var("CHTHONIC_SHADER_LANGUAGE") {
            Ok(raw) => match raw.trim().to_ascii_lowercase().as_str() {
                "hlsl" => ShaderLanguage::Hlsl,
                "glsl" => ShaderLanguage::Glsl,
                "auto" => {
                    if Self::shader_artifact_path("iso_grid.vert.hlsl.spv").exists()
                        && Self::shader_artifact_path("iso_grid.frag.hlsl.spv").exists()
                    {
                        ShaderLanguage::Hlsl
                    } else {
                        ShaderLanguage::Glsl
                    }
                }
                _ => ShaderLanguage::Glsl,
            },
            Err(_) => ShaderLanguage::Glsl,
        }
    }

    fn shader_artifact_path(file_name: &str) -> PathBuf {
        PathBuf::from(env!("OUT_DIR")).join(file_name)
    }

    fn load_shader_pair(language: ShaderLanguage) -> Result<(Vec<u8>, Vec<u8>)> {
        match language {
            ShaderLanguage::Glsl => Ok((
                include_bytes!(concat!(env!("OUT_DIR"), "/water.vert.spv")).to_vec(),
                include_bytes!(concat!(env!("OUT_DIR"), "/water.frag.spv")).to_vec(),
            )),
            ShaderLanguage::Hlsl => {
                let vert_path = Self::shader_artifact_path("iso_grid.vert.hlsl.spv");
                let frag_path = Self::shader_artifact_path("iso_grid.frag.hlsl.spv");
                let vertex = fs::read(&vert_path)
                    .with_context(|| format!("Failed to read HLSL vertex artifact {}", vert_path.display()))?;
                let fragment = fs::read(&frag_path)
                    .with_context(|| format!("Failed to read HLSL fragment artifact {}", frag_path.display()))?;
                Ok((vertex, fragment))
            }
        }
    }

    fn shader_signature(vertex_spv: &[u8], fragment_spv: &[u8]) -> u64 {
        const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
        const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

        fn hash_bytes(mut hash: u64, bytes: &[u8], prime: u64) -> u64 {
            for &byte in bytes {
                hash ^= u64::from(byte);
                hash = hash.wrapping_mul(prime);
            }
            hash
        }

        let mut hash = FNV_OFFSET;
        hash = hash_bytes(hash, vertex_spv, FNV_PRIME);
        hash = hash_bytes(hash, &[0xff], FNV_PRIME);
        hash = hash_bytes(hash, fragment_spv, FNV_PRIME);
        hash
    }

    fn pipeline_cache_path(
        physical_device_properties: &vk::PhysicalDeviceProperties,
        color_format: vk::Format,
        shader_language: &str,
        shader_signature: u64,
    ) -> PathBuf {
        let filename = format!(
            "iso_grid_{shader_language}_v{PIPELINE_CACHE_SCHEMA_VERSION}_ven{:04x}_dev{:04x}_drv{:08x}_fmt{}_sig{shader_signature:016x}.bin",
            physical_device_properties.vendor_id,
            physical_device_properties.device_id,
            physical_device_properties.driver_version,
            color_format.as_raw(),
        );
        Self::default_cache_directory().join(filename)
    }

    fn default_cache_directory() -> PathBuf {
        if let Some(dir) = std::env::var_os("CHTHONIC_PIPELINE_CACHE_DIR") {
            return PathBuf::from(dir);
        }

        if let Some(dir) = std::env::var_os("LOCALAPPDATA") {
            return PathBuf::from(dir)
                .join("chthonic-archive")
                .join("vulkan-cache");
        }

        if cfg!(target_os = "macos") {
            if let Some(home) = std::env::var_os("HOME") {
                return PathBuf::from(home)
                    .join("Library")
                    .join("Caches")
                    .join("chthonic-archive")
                    .join("vulkan");
            }
        }

        if let Some(dir) = std::env::var_os("XDG_CACHE_HOME") {
            return PathBuf::from(dir).join("chthonic-archive").join("vulkan");
        }

        if let Some(home) = std::env::var_os("HOME") {
            return PathBuf::from(home)
                .join(".cache")
                .join("chthonic-archive")
                .join("vulkan");
        }

        PathBuf::from("target").join("pipeline-cache")
    }

    unsafe fn create_pipeline_cache(
        device: &Device,
        cache_path: &Path,
    ) -> Result<(vk::PipelineCache, PipelineCacheState)> {
        let initial_data = match fs::read(cache_path) {
            Ok(bytes) => bytes,
            Err(err) if err.kind() == ErrorKind::NotFound => Vec::new(),
            Err(err) => {
                warn!(
                    "⚠️ Failed to read pipeline cache {}: {}",
                    cache_path.display(),
                    err
                );
                Vec::new()
            }
        };

        if initial_data.is_empty() {
            let create_info = vk::PipelineCacheCreateInfo::default();
            let cache = device
                .create_pipeline_cache(&create_info, None)
                .context("Failed to create empty pipeline cache")?;
            return Ok((cache, PipelineCacheState::ColdStart));
        }

        let create_info = vk::PipelineCacheCreateInfo::default().initial_data(&initial_data);
        match device.create_pipeline_cache(&create_info, None) {
            Ok(cache) => Ok((cache, PipelineCacheState::WarmStart)),
            Err(err) => {
                warn!(
                    "⚠️ Pipeline cache invalid at {}: {err:?}. Rebuilding cache.",
                    cache_path.display()
                );
                let fallback_create_info = vk::PipelineCacheCreateInfo::default();
                let cache = device
                    .create_pipeline_cache(&fallback_create_info, None)
                    .context("Failed to recreate pipeline cache after invalid data")?;
                Ok((cache, PipelineCacheState::RebuiltFromInvalidData))
            }
        }
    }

    unsafe fn persist_pipeline_cache(
        device: &Device,
        pipeline_cache: vk::PipelineCache,
        cache_path: &Path,
    ) {
        let cache_data = match device.get_pipeline_cache_data(pipeline_cache) {
            Ok(data) => data,
            Err(err) => {
                warn!("⚠️ Failed to extract pipeline cache data: {err:?}");
                return;
            }
        };

        if cache_data.is_empty() {
            return;
        }

        if let Some(parent) = cache_path.parent() {
            if let Err(err) = fs::create_dir_all(parent) {
                warn!(
                    "⚠️ Failed to create pipeline cache directory {}: {}",
                    parent.display(),
                    err
                );
                return;
            }
        }

        let temp_path = cache_path.with_extension("tmp");
        if let Err(err) = fs::write(&temp_path, &cache_data) {
            warn!(
                "⚠️ Failed writing temporary pipeline cache {}: {}",
                temp_path.display(),
                err
            );
            return;
        }

        if cache_path.exists() && fs::remove_file(cache_path).is_err() {
            warn!(
                "⚠️ Failed to replace existing pipeline cache {}",
                cache_path.display()
            );
        }

        if let Err(err) = fs::rename(&temp_path, cache_path) {
            warn!(
                "⚠️ Failed to finalize pipeline cache {}: {}",
                cache_path.display(),
                err
            );
            let _ = fs::remove_file(&temp_path);
            return;
        }

        debug!(
            "💾 Pipeline cache saved: {} bytes -> {}",
            cache_data.len(),
            cache_path.display()
        );
    }

    /// Create a shader module from SPIR-V bytecode
    unsafe fn create_shader_module(device: &Device, code: &[u8]) -> Result<vk::ShaderModule> {
        // SPIR-V code must be aligned to 4 bytes
        assert!(code.len().is_multiple_of(4), "SPIR-V code must be 4-byte aligned");

        let code_u32: Vec<u32> = code
            .chunks_exact(4)
            .map(|chunk| u32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]))
            .collect();

        let create_info = vk::ShaderModuleCreateInfo::default().code(&code_u32);

        device
            .create_shader_module(&create_info, None)
            .context("Failed to create shader module")
    }

    /// Clean up pipeline resources
    pub unsafe fn cleanup(&self, device: &Device) {
        debug!("🧹 Cleaning up graphics pipeline...");
        device.destroy_pipeline(self.pipeline, None);
        device.destroy_pipeline_layout(self.pipeline_layout, None);
        device.destroy_shader_module(self.vertex_shader, None);
        device.destroy_shader_module(self.fragment_shader, None);
        device.destroy_pipeline_cache(self.pipeline_cache, None);
        debug!("✅ Graphics pipeline cleaned up");
    }
}

/// Triangle vertices in WORLD SPACE for isometric camera testing
/// The isometric camera looks at origin with `ortho_size=5`, so vertices
/// should be within ~5 units of origin to be visible
pub fn triangle_vertices() -> Vec<Vertex> {
    vec![
        // Top vertex (red) - The Apex
        // Y is up in world space, visible from isometric camera
        Vertex {
            position: [0.0, 2.0, 0.0],
            normal: [0.0, 0.0, 1.0],
            color: [1.0, 0.0, 0.0],
        },
        // Bottom-right (green) - The Dexter Foundation
        Vertex {
            position: [2.0, -1.0, 0.0],
            normal: [0.0, 0.0, 1.0],
            color: [0.0, 1.0, 0.0],
        },
        // Bottom-left (blue) - The Sinister Foundation
        Vertex {
            position: [-2.0, -1.0, 0.0],
            normal: [0.0, 0.0, 1.0],
            color: [0.0, 0.0, 1.0],
        },
    ]
}
