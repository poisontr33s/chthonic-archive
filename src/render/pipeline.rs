//! Vulkan 1.3 Graphics Pipeline with Dynamic Rendering
//!
//! "I will dissect your darkest fantasy and show you the beauty hidden within."
//! — Dr. Lysandra Thorne
//!
//! This pipeline implementation:
//! - Uses VkPipelineRenderingCreateInfo (no VkRenderPass)
//! - Loads SPIR-V shaders compiled at build time
//! - Configures triangle rendering with push constants for MVP
//! - Prepares for isometric grid rendering

use anyhow::{Context, Result};
use ash::{vk, Device};
use log::{debug, info};
use std::ffi::CStr;

/// Graphics pipeline for rendering
pub struct VulkanPipeline {
    pub pipeline: vk::Pipeline,
    pub pipeline_layout: vk::PipelineLayout,
    pub vertex_shader: vk::ShaderModule,
    pub fragment_shader: vk::ShaderModule,
}

/// Push constants for MVP transformation (192 bytes = 3 mat4)
#[repr(C)]
#[derive(Clone, Copy, Debug)]
pub struct PushConstants {
    pub model: [[f32; 4]; 4],
    pub view: [[f32; 4]; 4],
    pub projection: [[f32; 4]; 4],
}

impl Default for PushConstants {
    fn default() -> Self {
        Self {
            model: identity_matrix(),
            view: identity_matrix(),
            projection: identity_matrix(),
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

/// Vertex data for rendering (position + color)
#[repr(C)]
#[derive(Clone, Copy, Debug)]
pub struct Vertex {
    pub position: [f32; 3],
    pub color: [f32; 3],
}

impl Vertex {
    /// Get vertex input binding description
    pub fn binding_description() -> vk::VertexInputBindingDescription {
        vk::VertexInputBindingDescription::default()
            .binding(0)
            .stride(std::mem::size_of::<Self>() as u32)
            .input_rate(vk::VertexInputRate::VERTEX)
    }

    /// Get vertex attribute descriptions (position, color)
    pub fn attribute_descriptions() -> [vk::VertexInputAttributeDescription; 2] {
        [
            // Position at location 0
            vk::VertexInputAttributeDescription::default()
                .binding(0)
                .location(0)
                .format(vk::Format::R32G32B32_SFLOAT)
                .offset(0),
            // Color at location 1
            vk::VertexInputAttributeDescription::default()
                .binding(0)
                .location(1)
                .format(vk::Format::R32G32B32_SFLOAT)
                .offset(12), // 3 * sizeof(f32)
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
        color_format: vk::Format,
    ) -> Result<Self> {
        info!("╔══════════════════════════════════════════════════════════════╗");
        info!("║   GRAPHICS PIPELINE - Dynamic Rendering Mode                 ║");
        info!("╚══════════════════════════════════════════════════════════════╝");

        // Load SPIR-V shaders (compiled at build time)
        let vertex_spv = include_bytes!(concat!(env!("OUT_DIR"), "/iso_grid.vert.spv"));
        let fragment_spv = include_bytes!(concat!(env!("OUT_DIR"), "/iso_grid.frag.spv"));

        info!("   Vertex shader: {} bytes", vertex_spv.len());
        info!("   Fragment shader: {} bytes", fragment_spv.len());

        let vertex_shader = Self::create_shader_module(device, vertex_spv)?;
        let fragment_shader = Self::create_shader_module(device, fragment_spv)?;
        info!("✅ Shader modules created");

        // Shader stages
        let entry_point = CStr::from_bytes_with_nul_unchecked(b"main\0");
        
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

        // Push constant range (MVP matrices = 192 bytes)
        let push_constant_range = vk::PushConstantRange::default()
            .stage_flags(vk::ShaderStageFlags::VERTEX)
            .offset(0)
            .size(std::mem::size_of::<PushConstants>() as u32);

        let push_constant_ranges = [push_constant_range];
        let pipeline_layout_info = vk::PipelineLayoutCreateInfo::default()
            .push_constant_ranges(&push_constant_ranges);

        let pipeline_layout = device
            .create_pipeline_layout(&pipeline_layout_info, None)
            .context("Failed to create pipeline layout")?;

        info!("✅ Pipeline layout created (192 bytes push constants)");

        // === DYNAMIC RENDERING (Vulkan 1.3) ===
        // No VkRenderPass! Use VkPipelineRenderingCreateInfo instead
        let color_formats = [color_format];
        let mut rendering_info = vk::PipelineRenderingCreateInfo::default()
            .color_attachment_formats(&color_formats);

        // Create graphics pipeline
        let pipeline_info = vk::GraphicsPipelineCreateInfo::default()
            .stages(&shader_stages)
            .vertex_input_state(&vertex_input_state)
            .input_assembly_state(&input_assembly_state)
            .viewport_state(&viewport_state)
            .rasterization_state(&rasterization_state)
            .multisample_state(&multisample_state)
            .color_blend_state(&color_blend_state)
            .dynamic_state(&dynamic_state)
            .layout(pipeline_layout)
            .push_next(&mut rendering_info)
            // render_pass is null for Dynamic Rendering
            .render_pass(vk::RenderPass::null())
            .subpass(0);

        let pipelines = device
            .create_graphics_pipelines(vk::PipelineCache::null(), &[pipeline_info], None)
            .map_err(|(_, e)| e)
            .context("Failed to create graphics pipeline")?;

        let pipeline = pipelines[0];

        info!("═══════════════════════════════════════════════════════════════");
        info!("🔥 GRAPHICS PIPELINE CREATED - Dynamic Rendering Active!");
        info!("═══════════════════════════════════════════════════════════════");

        Ok(Self {
            pipeline,
            pipeline_layout,
            vertex_shader,
            fragment_shader,
        })
    }

    /// Create a shader module from SPIR-V bytecode
    unsafe fn create_shader_module(device: &Device, code: &[u8]) -> Result<vk::ShaderModule> {
        // SPIR-V code must be aligned to 4 bytes
        assert!(code.len() % 4 == 0, "SPIR-V code must be 4-byte aligned");

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
        debug!("✅ Graphics pipeline cleaned up");
    }
}

/// Triangle vertices in WORLD SPACE for isometric camera testing
/// The isometric camera looks at origin with ortho_size=5, so vertices
/// should be within ~5 units of origin to be visible
pub fn triangle_vertices() -> Vec<Vertex> {
    vec![
        // Top vertex (red) - The Apex
        // Y is up in world space, visible from isometric camera
        Vertex {
            position: [0.0, 2.0, 0.0],
            color: [1.0, 0.0, 0.0],
        },
        // Bottom-right (green) - The Dexter Foundation
        Vertex {
            position: [2.0, -1.0, 0.0],
            color: [0.0, 1.0, 0.0],
        },
        // Bottom-left (blue) - The Sinister Foundation
        Vertex {
            position: [-2.0, -1.0, 0.0],
            color: [0.0, 0.0, 1.0],
        },
    ]
}
