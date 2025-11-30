//! Renderer - Main rendering orchestration using Dynamic Rendering
//!
//! "The worlds first isometric RPG based on your new designated classification...
//!  Rust/Vulkan/Native with Solana Blockchain"
//! — The Savant
//!
//! This module:
//! - Orchestrates swapchain, pipeline, and command buffer management
//! - Implements render_frame using cmd_begin_rendering/cmd_end_rendering (Vulkan 1.3)
//! - Manages vertex buffers and memory
//! - Integrates isometric camera system

use anyhow::{Context, Result};
use ash::{vk, Device};
use glam::{Mat4, Vec3};
use log::{debug, info};

use super::camera::IsometricCamera;
use super::swapchain::VulkanSwapchain;
use super::pipeline::{PushConstants, Vertex, VulkanPipeline, triangle_vertices};
use super::vulkan::VulkanContext;

/// Main renderer state
pub struct Renderer {
    pub swapchain: VulkanSwapchain,
    pub pipeline: VulkanPipeline,
    pub command_pool: vk::CommandPool,
    pub command_buffers: Vec<vk::CommandBuffer>,
    pub vertex_buffer: vk::Buffer,
    pub vertex_buffer_memory: vk::DeviceMemory,
    pub vertex_count: u32,
    pub needs_resize: bool,
    pub camera: IsometricCamera,
}

impl Renderer {
    /// Create a new renderer with all subsystems initialized
    ///
    /// # Safety
    /// Requires valid Vulkan context
    pub unsafe fn new(ctx: &VulkanContext, window_size: (u32, u32)) -> Result<Self> {
        info!("╔══════════════════════════════════════════════════════════════╗");
        info!("║   RENDERER INITIALIZATION - Phase 11                         ║");
        info!("╚══════════════════════════════════════════════════════════════╝");

        // Create swapchain
        let swapchain = VulkanSwapchain::new(
            &ctx.instance,
            &ctx.device,
            ctx.physical_device,
            &ctx.surface_loader,
            ctx.surface,
            ctx.queue_family_index,
            window_size,
        )?;

        // Create pipeline
        let pipeline = VulkanPipeline::new(&ctx.device, swapchain.format)?;

        // Create command pool
        let pool_info = vk::CommandPoolCreateInfo::default()
            .queue_family_index(ctx.queue_family_index)
            .flags(vk::CommandPoolCreateFlags::RESET_COMMAND_BUFFER);

        let command_pool = ctx.device
            .create_command_pool(&pool_info, None)
            .context("Failed to create command pool")?;

        // Allocate command buffers (one per frame in flight)
        let alloc_info = vk::CommandBufferAllocateInfo::default()
            .command_pool(command_pool)
            .level(vk::CommandBufferLevel::PRIMARY)
            .command_buffer_count(swapchain.frames_in_flight as u32);

        let command_buffers = ctx.device
            .allocate_command_buffers(&alloc_info)
            .context("Failed to allocate command buffers")?;

        info!("✅ Allocated {} command buffers", command_buffers.len());

        // Create vertex buffer with triangle data
        let vertices = triangle_vertices();
        let (vertex_buffer, vertex_buffer_memory) = 
            Self::create_vertex_buffer(ctx, &vertices)?;

        // Initialize isometric camera
        // Looking at origin from isometric angle, 10 units away, ortho size 5
        let aspect_ratio = window_size.0 as f32 / window_size.1 as f32;
        let mut camera = IsometricCamera::new(Vec3::ZERO, 10.0, 5.0);
        camera.update_matrices(aspect_ratio);

        info!("═══════════════════════════════════════════════════════════════");
        info!("🔥 RENDERER READY - Dynamic Rendering Pipeline Active!");
        info!("🎥 Isometric Camera: Engaged (Y:45° X:35.264°)");
        info!("═══════════════════════════════════════════════════════════════");

        Ok(Self {
            swapchain,
            pipeline,
            command_pool,
            command_buffers,
            vertex_buffer,
            vertex_buffer_memory,
            vertex_count: vertices.len() as u32,
            needs_resize: false,
            camera,
        })
    }

    /// Create a vertex buffer and upload vertex data
    unsafe fn create_vertex_buffer(
        ctx: &VulkanContext,
        vertices: &[Vertex],
    ) -> Result<(vk::Buffer, vk::DeviceMemory)> {
        let buffer_size = (std::mem::size_of::<Vertex>() * vertices.len()) as vk::DeviceSize;

        // Create buffer
        let buffer_info = vk::BufferCreateInfo::default()
            .size(buffer_size)
            .usage(vk::BufferUsageFlags::VERTEX_BUFFER)
            .sharing_mode(vk::SharingMode::EXCLUSIVE);

        let buffer = ctx.device
            .create_buffer(&buffer_info, None)
            .context("Failed to create vertex buffer")?;

        // Get memory requirements
        let mem_requirements = ctx.device.get_buffer_memory_requirements(buffer);

        // Find suitable memory type (host visible for simplicity)
        let memory_type_index = Self::find_memory_type(
            ctx,
            mem_requirements.memory_type_bits,
            vk::MemoryPropertyFlags::HOST_VISIBLE | vk::MemoryPropertyFlags::HOST_COHERENT,
        )?;

        // Allocate memory
        let alloc_info = vk::MemoryAllocateInfo::default()
            .allocation_size(mem_requirements.size)
            .memory_type_index(memory_type_index);

        let memory = ctx.device
            .allocate_memory(&alloc_info, None)
            .context("Failed to allocate vertex buffer memory")?;

        // Bind buffer to memory
        ctx.device.bind_buffer_memory(buffer, memory, 0)?;

        // Map memory and copy vertex data
        let data_ptr = ctx.device
            .map_memory(memory, 0, buffer_size, vk::MemoryMapFlags::empty())?;
        
        std::ptr::copy_nonoverlapping(
            vertices.as_ptr() as *const u8,
            data_ptr as *mut u8,
            buffer_size as usize,
        );
        
        ctx.device.unmap_memory(memory);

        info!("✅ Vertex buffer created: {} bytes, {} vertices", 
              buffer_size, vertices.len());

        Ok((buffer, memory))
    }

    /// Find a suitable memory type
    unsafe fn find_memory_type(
        ctx: &VulkanContext,
        type_filter: u32,
        properties: vk::MemoryPropertyFlags,
    ) -> Result<u32> {
        let mem_properties = ctx.instance
            .get_physical_device_memory_properties(ctx.physical_device);

        for i in 0..mem_properties.memory_type_count {
            if (type_filter & (1 << i)) != 0
                && mem_properties.memory_types[i as usize]
                    .property_flags
                    .contains(properties)
            {
                return Ok(i);
            }
        }

        Err(anyhow::anyhow!("Failed to find suitable memory type"))
    }

    /// Render a frame using Dynamic Rendering (Vulkan 1.3)
    ///
    /// # Safety
    /// Requires valid Vulkan handles and properly synchronized operations
    pub unsafe fn render_frame(&mut self, ctx: &VulkanContext) -> Result<bool> {
        // Acquire next swapchain image
        let (image_index, needs_resize) = self.swapchain.acquire_next_image(&ctx.device)?;
        
        if needs_resize {
            self.needs_resize = true;
            return Ok(true);
        }

        let (image_available, render_finished, in_flight) = self.swapchain.current_sync();
        
        // Reset fence for this frame
        ctx.device.reset_fences(&[in_flight])?;

        // Get current command buffer
        let cmd = self.command_buffers[self.swapchain.current_frame];
        
        // Reset and begin command buffer
        ctx.device.reset_command_buffer(cmd, vk::CommandBufferResetFlags::empty())?;
        
        let begin_info = vk::CommandBufferBeginInfo::default()
            .flags(vk::CommandBufferUsageFlags::ONE_TIME_SUBMIT);
        ctx.device.begin_command_buffer(cmd, &begin_info)?;

        // === TRANSITION IMAGE TO COLOR ATTACHMENT ===
        let image_barrier_to_render = vk::ImageMemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::TOP_OF_PIPE)
            .src_access_mask(vk::AccessFlags2::empty())
            .dst_stage_mask(vk::PipelineStageFlags2::COLOR_ATTACHMENT_OUTPUT)
            .dst_access_mask(vk::AccessFlags2::COLOR_ATTACHMENT_WRITE)
            .old_layout(vk::ImageLayout::UNDEFINED)
            .new_layout(vk::ImageLayout::COLOR_ATTACHMENT_OPTIMAL)
            .image(self.swapchain.images[image_index as usize])
            .subresource_range(vk::ImageSubresourceRange {
                aspect_mask: vk::ImageAspectFlags::COLOR,
                base_mip_level: 0,
                level_count: 1,
                base_array_layer: 0,
                layer_count: 1,
            });

        let barriers_to_render = [image_barrier_to_render];
        let dependency_info_to_render = vk::DependencyInfo::default()
            .image_memory_barriers(&barriers_to_render);

        ctx.device.cmd_pipeline_barrier2(cmd, &dependency_info_to_render);

        // === BEGIN DYNAMIC RENDERING ===
        let clear_value = vk::ClearValue {
            color: vk::ClearColorValue {
                float32: [0.05, 0.02, 0.08, 1.0], // Abyssal purple-black
            },
        };

        let color_attachment = vk::RenderingAttachmentInfo::default()
            .image_view(self.swapchain.image_views[image_index as usize])
            .image_layout(vk::ImageLayout::COLOR_ATTACHMENT_OPTIMAL)
            .load_op(vk::AttachmentLoadOp::CLEAR)
            .store_op(vk::AttachmentStoreOp::STORE)
            .clear_value(clear_value);

        let color_attachments = [color_attachment];
        let rendering_info = vk::RenderingInfo::default()
            .render_area(vk::Rect2D {
                offset: vk::Offset2D { x: 0, y: 0 },
                extent: self.swapchain.extent,
            })
            .layer_count(1)
            .color_attachments(&color_attachments);

        ctx.device.cmd_begin_rendering(cmd, &rendering_info);

        // Set viewport and scissor
        let viewport = vk::Viewport {
            x: 0.0,
            y: 0.0,
            width: self.swapchain.extent.width as f32,
            height: self.swapchain.extent.height as f32,
            min_depth: 0.0,
            max_depth: 1.0,
        };
        ctx.device.cmd_set_viewport(cmd, 0, &[viewport]);

        let scissor = vk::Rect2D {
            offset: vk::Offset2D { x: 0, y: 0 },
            extent: self.swapchain.extent,
        };
        ctx.device.cmd_set_scissor(cmd, 0, &[scissor]);

        // Bind pipeline
        ctx.device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::GRAPHICS, self.pipeline.pipeline);

        // Push constants with isometric camera matrices
        let push_constants = PushConstants {
            model: Mat4::IDENTITY.to_cols_array_2d(),
            view: self.camera.view_as_array(),
            projection: self.camera.projection_as_array(),
        };
        let push_data = std::slice::from_raw_parts(
            &push_constants as *const PushConstants as *const u8,
            std::mem::size_of::<PushConstants>(),
        );
        ctx.device.cmd_push_constants(
            cmd,
            self.pipeline.pipeline_layout,
            vk::ShaderStageFlags::VERTEX,
            0,
            push_data,
        );

        // Bind vertex buffer
        ctx.device.cmd_bind_vertex_buffers(cmd, 0, &[self.vertex_buffer], &[0]);

        // DRAW THE TRIANGLE! 🔺
        ctx.device.cmd_draw(cmd, self.vertex_count, 1, 0, 0);

        // === END DYNAMIC RENDERING ===
        ctx.device.cmd_end_rendering(cmd);

        // === TRANSITION IMAGE TO PRESENT ===
        let image_barrier_to_present = vk::ImageMemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::COLOR_ATTACHMENT_OUTPUT)
            .src_access_mask(vk::AccessFlags2::COLOR_ATTACHMENT_WRITE)
            .dst_stage_mask(vk::PipelineStageFlags2::BOTTOM_OF_PIPE)
            .dst_access_mask(vk::AccessFlags2::empty())
            .old_layout(vk::ImageLayout::COLOR_ATTACHMENT_OPTIMAL)
            .new_layout(vk::ImageLayout::PRESENT_SRC_KHR)
            .image(self.swapchain.images[image_index as usize])
            .subresource_range(vk::ImageSubresourceRange {
                aspect_mask: vk::ImageAspectFlags::COLOR,
                base_mip_level: 0,
                level_count: 1,
                base_array_layer: 0,
                layer_count: 1,
            });

        let barriers_to_present = [image_barrier_to_present];
        let dependency_info_to_present = vk::DependencyInfo::default()
            .image_memory_barriers(&barriers_to_present);

        ctx.device.cmd_pipeline_barrier2(cmd, &dependency_info_to_present);

        // End command buffer
        ctx.device.end_command_buffer(cmd)?;

        // === SUBMIT ===
        let wait_semaphores = [image_available];
        let wait_stages = [vk::PipelineStageFlags::COLOR_ATTACHMENT_OUTPUT];
        let command_buffers_submit = [cmd];
        let signal_semaphores = [render_finished];

        let submit_info = vk::SubmitInfo::default()
            .wait_semaphores(&wait_semaphores)
            .wait_dst_stage_mask(&wait_stages)
            .command_buffers(&command_buffers_submit)
            .signal_semaphores(&signal_semaphores);

        ctx.device.queue_submit(ctx.graphics_queue, &[submit_info], in_flight)?;

        // === PRESENT ===
        let needs_resize = self.swapchain.present(ctx.graphics_queue, image_index)?;
        if needs_resize {
            self.needs_resize = true;
        }

        Ok(needs_resize)
    }

    /// Handle window resize
    pub unsafe fn handle_resize(&mut self, ctx: &VulkanContext, new_size: (u32, u32)) -> Result<()> {
        info!("🔄 Handling resize to {}x{}", new_size.0, new_size.1);
        
        ctx.device.device_wait_idle()?;

        self.swapchain.recreate(
            &ctx.instance,
            &ctx.device,
            ctx.physical_device,
            &ctx.surface_loader,
            ctx.surface,
            ctx.queue_family_index,
            new_size,
        )?;

        // Update camera aspect ratio for new window dimensions
        let aspect_ratio = new_size.0 as f32 / new_size.1.max(1) as f32;
        self.camera.update_matrices(aspect_ratio);
        debug!("📐 Camera aspect ratio updated: {:.3}", aspect_ratio);

        self.needs_resize = false;
        Ok(())
    }

    /// Clean up all renderer resources
    pub unsafe fn cleanup(&mut self, device: &Device) {
        debug!("🧹 Cleaning up renderer...");

        device.device_wait_idle().ok();

        // Free vertex buffer
        device.destroy_buffer(self.vertex_buffer, None);
        device.free_memory(self.vertex_buffer_memory, None);

        // Command pool (implicitly frees command buffers)
        device.destroy_command_pool(self.command_pool, None);

        // Pipeline
        self.pipeline.cleanup(device);

        // Swapchain
        self.swapchain.cleanup(device);

        debug!("✅ Renderer cleaned up");
    }
}
