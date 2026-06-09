// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: renderer.rs
// ║ Vulkan rendering pipeline - visual truth incarnate
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Spectral Frequency: RED
// ║ Architectural Role: 🏰 THE FORTRESS
// ║ Purpose: Renderer - Main rendering orchestration using Dynamic Rendering
// ║ Exports: Renderer
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Cross-References (Bidirectional):
// ║  (Standalone file - no detected dependencies)
// ╚════════════════════════════════════════════════════════════════════════════

//! Renderer - Main rendering orchestration using Dynamic Rendering
//!
//! @SID:    RENDER_RENDERER_V1
//! @Shabti: Renderer
//!
//! "The worlds first isometric RPG based on your new designated classification...
//!  Rust/Vulkan/Native with Solana Blockchain"
//! — The Savant
//!
//! This module:
//! - Orchestrates swapchain, pipeline, and command buffer management
//! - Implements `render_frame` using `cmd_begin_rendering/cmd_end_rendering` (Vulkan 1.3)
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
    pub depth_image: vk::Image,
    pub depth_memory: vk::DeviceMemory,
    pub depth_view: vk::ImageView,
    pub frame_index: u64,
    pub screenshot: Option<String>,
    pub shot_taken: bool,
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
        let pipeline = VulkanPipeline::new(
            &ctx.device,
            &ctx.physical_device_properties,
            swapchain.format,
        )?;

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
            .command_buffer_count(u32::try_from(swapchain.frames_in_flight).unwrap());

        let command_buffers = ctx.device
            .allocate_command_buffers(&alloc_info)
            .context("Failed to allocate command buffers")?;

        info!("✅ Allocated {0} command buffers", command_buffers.len());

        // Create vertex buffer — the real Bahama bathymetry heightfield (rung 3),
        // falling back to the test triangle if the data plane is unreadable.
        let vertices = match super::bathymetry::Bathymetry::load(super::bathymetry::DEFAULT_PATH) {
            Ok(b) => {
                let mesh = b.mesh();
                info!("🌊 Bathymetry loaded: {0}x{1} → {2} vertices", b.w, b.h, mesh.len());
                mesh
            }
            Err(e) => {
                log::warn!("⚠️ bathymetry load failed ({e:#}); falling back to triangle");
                triangle_vertices()
            }
        };
        let (vertex_buffer, vertex_buffer_memory) =
            Self::create_vertex_buffer(ctx, &vertices)?;

        // Initialize isometric camera
        // Looking at origin from isometric angle, 10 units away, ortho size 5
        #[allow(clippy::cast_precision_loss)]
        let aspect_ratio = window_size.0 as f32 / window_size.1 as f32;
        let mut camera = IsometricCamera::new(Vec3::ZERO, 10.0, 5.0);
        camera.update_matrices(aspect_ratio);

        info!("═══════════════════════════════════════════════════════════════");
        info!("🔥 RENDERER READY - Dynamic Rendering Pipeline Active!");
        info!("🎥 Isometric Camera: Engaged (Y:45° X:35.264°)");
        info!("═══════════════════════════════════════════════════════════════");

        let (depth_image, depth_memory, depth_view) =
            Self::create_depth_resources(ctx, swapchain.extent)?;

        Ok(Self {
            swapchain,
            pipeline,
            command_pool,
            command_buffers,
            vertex_buffer,
            vertex_buffer_memory,
            vertex_count: u32::try_from(vertices.len()).unwrap(),
            depth_image,
            depth_memory,
            depth_view,
            frame_index: 0,
            screenshot: std::env::var("CHTHONIC_SCREENSHOT").ok(),
            shot_taken: false,
            needs_resize: false,
            camera,
        })
    }

    /// Create a vertex buffer and upload vertex data
    unsafe fn create_vertex_buffer(
        ctx: &VulkanContext,
        vertices: &[Vertex],
    ) -> Result<(vk::Buffer, vk::DeviceMemory)> {
        let buffer_size = u64::try_from(std::mem::size_of_val(vertices)).unwrap();

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
            vertices.as_ptr().cast::<u8>(),
            data_ptr.cast::<u8>(),
            usize::try_from(buffer_size).unwrap(),
        );

        ctx.device.unmap_memory(memory);

        info!("✅ Vertex buffer created: {0} bytes, {1} vertices",
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

    /// Create the depth image / memory / view (D32) sized to the swapchain extent.
    unsafe fn create_depth_resources(
        ctx: &VulkanContext,
        extent: vk::Extent2D,
    ) -> Result<(vk::Image, vk::DeviceMemory, vk::ImageView)> {
        let format = vk::Format::D32_SFLOAT;
        let image_info = vk::ImageCreateInfo::default()
            .image_type(vk::ImageType::TYPE_2D)
            .format(format)
            .extent(vk::Extent3D { width: extent.width, height: extent.height, depth: 1 })
            .mip_levels(1)
            .array_layers(1)
            .samples(vk::SampleCountFlags::TYPE_1)
            .tiling(vk::ImageTiling::OPTIMAL)
            .usage(vk::ImageUsageFlags::DEPTH_STENCIL_ATTACHMENT)
            .sharing_mode(vk::SharingMode::EXCLUSIVE)
            .initial_layout(vk::ImageLayout::UNDEFINED);
        let image = ctx.device.create_image(&image_info, None).context("create depth image")?;

        let mem_req = ctx.device.get_image_memory_requirements(image);
        let mem_type = Self::find_memory_type(
            ctx,
            mem_req.memory_type_bits,
            vk::MemoryPropertyFlags::DEVICE_LOCAL,
        )?;
        let alloc_info = vk::MemoryAllocateInfo::default()
            .allocation_size(mem_req.size)
            .memory_type_index(mem_type);
        let memory = ctx.device.allocate_memory(&alloc_info, None).context("alloc depth memory")?;
        ctx.device.bind_image_memory(image, memory, 0)?;

        let view_info = vk::ImageViewCreateInfo::default()
            .image(image)
            .view_type(vk::ImageViewType::TYPE_2D)
            .format(format)
            .subresource_range(vk::ImageSubresourceRange {
                aspect_mask: vk::ImageAspectFlags::DEPTH,
                base_mip_level: 0,
                level_count: 1,
                base_array_layer: 0,
                layer_count: 1,
            });
        let view = ctx.device.create_image_view(&view_info, None).context("create depth view")?;
        Ok((image, memory, view))
    }

    /// Capture the just-presented swapchain image to a PNG so the build loop can
    /// self-verify a render without a human screenshot. One-shot, synchronous
    /// (its own command buffer + fence). Triggered via `CHTHONIC_SCREENSHOT`.
    unsafe fn capture_screenshot(
        &self,
        ctx: &VulkanContext,
        image_index: u32,
        path: &str,
    ) -> Result<()> {
        let device = &ctx.device;
        device.device_wait_idle()?;

        let extent = self.swapchain.extent;
        let (w, h) = (extent.width, extent.height);
        let size = u64::from(w) * u64::from(h) * 4;

        // Host-visible readback buffer.
        let buffer_info = vk::BufferCreateInfo::default()
            .size(size)
            .usage(vk::BufferUsageFlags::TRANSFER_DST)
            .sharing_mode(vk::SharingMode::EXCLUSIVE);
        let buffer = device.create_buffer(&buffer_info, None)?;
        let req = device.get_buffer_memory_requirements(buffer);
        let mem_type = Self::find_memory_type(
            ctx,
            req.memory_type_bits,
            vk::MemoryPropertyFlags::HOST_VISIBLE | vk::MemoryPropertyFlags::HOST_COHERENT,
        )?;
        let memory = device.allocate_memory(
            &vk::MemoryAllocateInfo::default()
                .allocation_size(req.size)
                .memory_type_index(mem_type),
            None,
        )?;
        device.bind_buffer_memory(buffer, memory, 0)?;

        let color_range = vk::ImageSubresourceRange {
            aspect_mask: vk::ImageAspectFlags::COLOR,
            base_mip_level: 0,
            level_count: 1,
            base_array_layer: 0,
            layer_count: 1,
        };
        let src_image = self.swapchain.images[image_index as usize];

        // One-time command buffer: image → TRANSFER_SRC, copy to buffer, → PRESENT_SRC.
        let cmd = device.allocate_command_buffers(
            &vk::CommandBufferAllocateInfo::default()
                .command_pool(self.command_pool)
                .level(vk::CommandBufferLevel::PRIMARY)
                .command_buffer_count(1),
        )?[0];
        device.begin_command_buffer(
            cmd,
            &vk::CommandBufferBeginInfo::default()
                .flags(vk::CommandBufferUsageFlags::ONE_TIME_SUBMIT),
        )?;

        let to_src = vk::ImageMemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::ALL_COMMANDS)
            .dst_stage_mask(vk::PipelineStageFlags2::ALL_TRANSFER)
            .dst_access_mask(vk::AccessFlags2::TRANSFER_READ)
            .old_layout(vk::ImageLayout::PRESENT_SRC_KHR)
            .new_layout(vk::ImageLayout::TRANSFER_SRC_OPTIMAL)
            .image(src_image)
            .subresource_range(color_range);
        device.cmd_pipeline_barrier2(
            cmd,
            &vk::DependencyInfo::default().image_memory_barriers(&[to_src]),
        );

        let region = vk::BufferImageCopy::default()
            .image_subresource(
                vk::ImageSubresourceLayers::default()
                    .aspect_mask(vk::ImageAspectFlags::COLOR)
                    .layer_count(1),
            )
            .image_extent(vk::Extent3D { width: w, height: h, depth: 1 });
        device.cmd_copy_image_to_buffer(
            cmd,
            src_image,
            vk::ImageLayout::TRANSFER_SRC_OPTIMAL,
            buffer,
            &[region],
        );

        let to_present = vk::ImageMemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::ALL_TRANSFER)
            .src_access_mask(vk::AccessFlags2::TRANSFER_READ)
            .dst_stage_mask(vk::PipelineStageFlags2::ALL_COMMANDS)
            .old_layout(vk::ImageLayout::TRANSFER_SRC_OPTIMAL)
            .new_layout(vk::ImageLayout::PRESENT_SRC_KHR)
            .image(src_image)
            .subresource_range(color_range);
        device.cmd_pipeline_barrier2(
            cmd,
            &vk::DependencyInfo::default().image_memory_barriers(&[to_present]),
        );

        device.end_command_buffer(cmd)?;

        let fence = device.create_fence(&vk::FenceCreateInfo::default(), None)?;
        let submit_cmds = [cmd];
        let submit = vk::SubmitInfo::default().command_buffers(&submit_cmds);
        device.queue_submit(ctx.graphics_queue, &[submit], fence)?;
        device.wait_for_fences(&[fence], true, u64::MAX)?;

        // Read back. Swap channel order for BGRA swapchains; write PNG.
        let ptr = device.map_memory(memory, 0, size, vk::MemoryMapFlags::empty())?.cast::<u8>();
        let mut pixels = std::slice::from_raw_parts(ptr, usize::try_from(size).unwrap()).to_vec();
        device.unmap_memory(memory);

        let is_bgra = matches!(
            self.swapchain.format,
            vk::Format::B8G8R8A8_UNORM | vk::Format::B8G8R8A8_SRGB
        );
        if is_bgra {
            for px in pixels.chunks_exact_mut(4) {
                px.swap(0, 2);
            }
        }

        device.destroy_fence(fence, None);
        device.free_command_buffers(self.command_pool, &[cmd]);
        device.destroy_buffer(buffer, None);
        device.free_memory(memory, None);

        let img = image::RgbaImage::from_raw(w, h, pixels)
            .ok_or_else(|| anyhow::anyhow!("buffer size mismatch for {w}x{h}"))?;
        img.save(path).map_err(|e| anyhow::anyhow!("png save {path}: {e}"))?;
        info!("📸 screenshot → {path} ({w}x{h}, bgra={is_bgra})");
        Ok(())
    }

    /// Render a frame using Dynamic Rendering (Vulkan 1.3)
    ///
    /// # Safety
    /// Requires valid Vulkan handles and properly synchronized operations
    #[allow(clippy::too_many_lines)]
    pub unsafe fn render_frame(&mut self, ctx: &VulkanContext, layer_color: [f32; 4]) -> Result<bool> {
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

        let depth_barrier_to_render = vk::ImageMemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::TOP_OF_PIPE)
            .src_access_mask(vk::AccessFlags2::empty())
            .dst_stage_mask(
                vk::PipelineStageFlags2::EARLY_FRAGMENT_TESTS
                    | vk::PipelineStageFlags2::LATE_FRAGMENT_TESTS,
            )
            .dst_access_mask(vk::AccessFlags2::DEPTH_STENCIL_ATTACHMENT_WRITE)
            .old_layout(vk::ImageLayout::UNDEFINED)
            .new_layout(vk::ImageLayout::DEPTH_ATTACHMENT_OPTIMAL)
            .image(self.depth_image)
            .subresource_range(vk::ImageSubresourceRange {
                aspect_mask: vk::ImageAspectFlags::DEPTH,
                base_mip_level: 0,
                level_count: 1,
                base_array_layer: 0,
                layer_count: 1,
            });

        let barriers_to_render = [image_barrier_to_render, depth_barrier_to_render];
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

        let depth_clear = vk::ClearValue {
            depth_stencil: vk::ClearDepthStencilValue { depth: 1.0, stencil: 0 },
        };
        let depth_attachment = vk::RenderingAttachmentInfo::default()
            .image_view(self.depth_view)
            .image_layout(vk::ImageLayout::DEPTH_ATTACHMENT_OPTIMAL)
            .load_op(vk::AttachmentLoadOp::CLEAR)
            .store_op(vk::AttachmentStoreOp::DONT_CARE)
            .clear_value(depth_clear);

        let rendering_info = vk::RenderingInfo::default()
            .render_area(vk::Rect2D {
                offset: vk::Offset2D { x: 0, y: 0 },
                extent: self.swapchain.extent,
            })
            .layer_count(1)
            .color_attachments(&color_attachments)
            .depth_attachment(&depth_attachment);

        ctx.device.cmd_begin_rendering(cmd, &rendering_info);

        // Set viewport and scissor
        #[allow(clippy::cast_precision_loss)]
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

        // Push constants with isometric camera matrices and layer color
        let push_constants = PushConstants {
            model: Mat4::IDENTITY.to_cols_array_2d(),
            view: self.camera.view_as_array(),
            projection: self.camera.projection_as_array(),
            layer_color,
        };
        let push_data = std::slice::from_raw_parts(
            (&raw const push_constants).cast::<u8>(),
            std::mem::size_of_val(&push_constants),
        );
        ctx.device.cmd_push_constants(
            cmd,
            self.pipeline.pipeline_layout,
            vk::ShaderStageFlags::VERTEX | vk::ShaderStageFlags::FRAGMENT,
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

        // One-shot framebuffer capture (agent self-verify). Frame ≥5 lets the
        // scene settle before we read the pixels back to PNG.
        self.frame_index += 1;
        if !self.shot_taken && self.frame_index >= 5 {
            if let Some(path) = self.screenshot.clone() {
                if let Err(e) = self.capture_screenshot(ctx, image_index, &path) {
                    log::warn!("📸 screenshot failed: {e:#}");
                }
                self.shot_taken = true;
            }
        }

        Ok(needs_resize)
    }

    /// Handle window resize
    pub unsafe fn handle_resize(&mut self, ctx: &VulkanContext, new_size: (u32, u32)) -> Result<()> {
        info!("🔄 Handling resize to {0}x{1}", new_size.0, new_size.1);

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

        // Recreate the depth buffer at the new extent
        ctx.device.destroy_image_view(self.depth_view, None);
        ctx.device.destroy_image(self.depth_image, None);
        ctx.device.free_memory(self.depth_memory, None);
        let (depth_image, depth_memory, depth_view) =
            Self::create_depth_resources(ctx, self.swapchain.extent)?;
        self.depth_image = depth_image;
        self.depth_memory = depth_memory;
        self.depth_view = depth_view;

        // Update camera aspect ratio for new window dimensions
        #[allow(clippy::cast_precision_loss)]
        let aspect_ratio = new_size.0 as f32 / new_size.1.max(1) as f32;
        self.camera.update_matrices(aspect_ratio);
        debug!("📐 Camera aspect ratio updated: {aspect_ratio:.3}");

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

        // Free depth buffer
        device.destroy_image_view(self.depth_view, None);
        device.destroy_image(self.depth_image, None);
        device.free_memory(self.depth_memory, None);

        // Command pool (implicitly frees command buffers)
        device.destroy_command_pool(self.command_pool, None);

        // Pipeline
        self.pipeline.cleanup(device);

        // Swapchain
        self.swapchain.cleanup(device);

        debug!("✅ Renderer cleaned up");
    }
}
