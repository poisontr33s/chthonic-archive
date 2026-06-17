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

//! @SID:    RENDER_RENDERER_V1
//! @Shabti: Renderer

//! "The worlds first isometric RPG based on your new designated classification...
//!  Rust/Vulkan/Native with Solana Blockchain"
//! — The Savant

//! This module:

//! - Orchestrates swapchain, pipeline, and command buffer management
//! - Implements `render_frame` using `cmd_begin_rendering/cmd_end_rendering` (Vulkan 1.4+)
//! - Manages vertex buffers and memory
//! - Integrates isometric camera system
//! - Compounds the verified celestial field onto the current scene; the §2.7
//!   perspective/celestial lens set remains a parked trajectory until it becomes a
//!   real view abstraction, not a scheduler or mode loop.

use anyhow::{Context, Result};
use ash::{Device, vk};
use glam::{Mat4, Vec3};
use log::{debug, info};

use super::camera::IsometricCamera;
use super::pipeline::{PushConstants, Vertex, VulkanPipeline, triangle_vertices};
use super::swapchain::VulkanSwapchain;
use super::temporal::TemporalState;
use super::vulkan::VulkanContext;

const CELESTIAL_DISC_SEGMENTS: usize = 18;
const CELESTIAL_CIRCLE_POINTS: usize = 120;
const SKY_RADIUS: f32 = 4.15;
const SKY_HORIZON_LIFT: f32 = 0.35;

/// Main renderer state
pub struct Renderer {
    pub swapchain: VulkanSwapchain,
    pub pipeline: VulkanPipeline,
    pub command_pool: vk::CommandPool,
    pub command_buffers: Vec<vk::CommandBuffer>,
    pub vertex_buffer: vk::Buffer,
    pub vertex_buffer_memory: vk::DeviceMemory,
    pub vertex_count: u32,
    pub ocean_vertex_buffer: vk::Buffer,
    pub ocean_vertex_memory: vk::DeviceMemory,
    pub ocean_vertex_count: u32,
    pub celestial_vertex_buffer: vk::Buffer,
    pub celestial_vertex_memory: vk::DeviceMemory,
    pub celestial_vertex_count: u32,
    pub ocean_compute: super::ocean_compute::OceanCompute,
    pub depth_image: vk::Image,
    pub depth_memory: vk::DeviceMemory,
    pub depth_view: vk::ImageView,
    pub motion_vector_image: vk::Image,
    pub motion_vector_memory: vk::DeviceMemory,
    pub motion_vector_view: vk::ImageView,
    pub frame_index: u64,
    pub screenshot: Option<String>,
    pub show_motion: bool,
    pub shot_taken: bool,
    pub needs_resize: bool,
    pub camera: IsometricCamera,
    pub temporal: TemporalState,
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

        let command_pool = ctx
            .device
            .create_command_pool(&pool_info, None)
            .context("Failed to create command pool")?;

        // Allocate command buffers (one per frame in flight)
        let alloc_info = vk::CommandBufferAllocateInfo::default()
            .command_pool(command_pool)
            .level(vk::CommandBufferLevel::PRIMARY)
            .command_buffer_count(u32::try_from(swapchain.frames_in_flight).unwrap());

        let command_buffers = ctx
            .device
            .allocate_command_buffers(&alloc_info)
            .context("Failed to allocate command buffers")?;

        info!("✅ Allocated {0} command buffers", command_buffers.len());

        // Create vertex buffer — the real Bahama bathymetry heightfield (rung 3),
        // falling back to the test triangle if the data plane is unreadable.
        let vertices = match super::bathymetry::Bathymetry::load(super::bathymetry::DEFAULT_PATH) {
            Ok(b) => {
                let mesh = b.mesh();
                info!(
                    "🌊 Bathymetry loaded: {0}x{1} → {2} vertices",
                    b.w,
                    b.h,
                    mesh.len()
                );
                mesh
            }
            Err(e) => {
                log::warn!("⚠️ bathymetry load failed ({e:#}); falling back to triangle");
                triangle_vertices()
            }
        };
        let (vertex_buffer, vertex_buffer_memory) = Self::create_vertex_buffer(ctx, &vertices)?;

        // Rung 4: the ocean surface grid (Gerstner-displaced in water.vert, surface mode).
        let ocean_vertices = super::ocean::surface_grid(128);
        let (ocean_vertex_buffer, ocean_vertex_memory) =
            Self::create_vertex_buffer(ctx, &ocean_vertices)?;
        let ocean_vertex_count = u32::try_from(ocean_vertices.len()).unwrap();
        info!("🌊 Ocean surface grid: {0} vertices", ocean_vertices.len());

        // Rung 4.2: the displacement compute subsystem (first compute pipeline + descriptors).
        let ocean_compute = super::ocean_compute::OceanCompute::new(ctx)?;

        // Initialize isometric camera
        // Looking at origin from isometric angle, 10 units away, ortho size 5
        #[allow(clippy::cast_precision_loss)]
        let aspect_ratio = window_size.0 as f32 / window_size.1 as f32;
        let mut camera = IsometricCamera::new(Vec3::ZERO, 10.0, 5.0);
        camera.update_matrices(aspect_ratio);

        // Rung 6.2: the verified celestial field made visible in the scene sky.
        // §2.7 preservation marker: future perspective/upward sky views compound
        // here as another view abstraction. They are intentionally not compiled as
        // inactive camera modes or a deterministic loop.
        let celestial_vertices =
            Self::celestial_field_vertices(&camera, super::cosmos::scene_julian_day());
        let (celestial_vertex_buffer, celestial_vertex_memory) =
            Self::create_vertex_buffer(ctx, &celestial_vertices)?;
        let celestial_vertex_count = u32::try_from(celestial_vertices.len()).unwrap();
        info!("🌌 Celestial field mesh: {celestial_vertex_count} vertices");

        info!("═══════════════════════════════════════════════════════════════");
        info!("🔥 RENDERER READY - Dynamic Rendering Pipeline Active!");
        info!("═══════════════════════════════════════════════════════════════");

        let (depth_image, depth_memory, depth_view) =
            Self::create_depth_resources(ctx, swapchain.extent)?;
        let (motion_vector_image, motion_vector_memory, motion_vector_view) =
            Self::create_motion_vector_resources(ctx, swapchain.extent)?;
        let temporal = TemporalState::new(camera.view_projection());

        Ok(Self {
            swapchain,
            pipeline,
            command_pool,
            command_buffers,
            vertex_buffer,
            vertex_buffer_memory,
            vertex_count: u32::try_from(vertices.len()).unwrap(),
            ocean_vertex_buffer,
            ocean_vertex_memory,
            ocean_vertex_count,
            celestial_vertex_buffer,
            celestial_vertex_memory,
            celestial_vertex_count,
            ocean_compute,
            depth_image,
            depth_memory,
            depth_view,
            motion_vector_image,
            motion_vector_memory,
            motion_vector_view,
            frame_index: 0,
            screenshot: std::env::var("CHTHONIC_SCREENSHOT").ok(),
            show_motion: std::env::var("CHTHONIC_SHOW_MOTION").is_ok(),
            shot_taken: false,
            needs_resize: false,
            camera,
            temporal,
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

        let buffer = ctx
            .device
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

        let memory = ctx
            .device
            .allocate_memory(&alloc_info, None)
            .context("Failed to allocate vertex buffer memory")?;

        // Bind buffer to memory
        ctx.device.bind_buffer_memory(buffer, memory, 0)?;

        // Map memory and copy vertex data
        let data_ptr =
            ctx.device
                .map_memory(memory, 0, buffer_size, vk::MemoryMapFlags::empty())?;

        std::ptr::copy_nonoverlapping(
            vertices.as_ptr().cast::<u8>(),
            data_ptr.cast::<u8>(),
            usize::try_from(buffer_size).unwrap(),
        );

        ctx.device.unmap_memory(memory);

        info!(
            "✅ Vertex buffer created: {0} bytes, {1} vertices",
            buffer_size,
            vertices.len()
        );

        Ok((buffer, memory))
    }

    fn celestial_field_vertices(camera: &IsometricCamera, jd: f64) -> Vec<Vertex> {
        let lat = super::cosmos::NEW_PROVIDENCE_LAT_DEG;
        let lon = super::cosmos::NEW_PROVIDENCE_LON_DEG;

        let forward = (camera.target - camera.position).normalize();
        let axis_up = if forward.dot(Vec3::Y).abs() > 0.95 {
            Vec3::Z
        } else {
            Vec3::Y
        };
        let right = forward.cross(axis_up).normalize();
        let up = right.cross(forward).normalize();

        let mut vertices = Vec::with_capacity(
            (2 + super::cosmos::Planet::ALL.len()
                + super::cosmos::STARS.len()
                + 2 * CELESTIAL_CIRCLE_POINTS)
                * CELESTIAL_DISC_SEGMENTS
                * 3,
        );
        let mut visible = 0_u32;

        let sun = super::cosmos::sun_push_constant(lat, lon, jd);
        if Self::push_body_disc(
            &mut vertices,
            Vec3::new(sun[0], sun[1], sun[2]),
            sun[3],
            0.20,
            [1.00, 0.78, 0.36],
            right,
            up,
        ) {
            visible += 1;
        }

        let moon = super::cosmos::moon_push_constant(lat, lon, jd);
        let phase = super::cosmos::moon_phase(jd) as f32;
        let moon_color = [
            0.42 + phase * 0.38,
            0.46 + phase * 0.34,
            0.52 + phase * 0.36,
        ];
        if Self::push_body_disc(
            &mut vertices,
            Vec3::new(moon[0], moon[1], moon[2]),
            moon[3],
            0.16,
            moon_color,
            right,
            up,
        ) {
            visible += 1;
        }

        for planet in super::cosmos::Planet::ALL {
            let (alt, az) = super::cosmos::planet_position(planet, lat, lon, jd);
            let dir = super::cosmos::altaz_to_world_direction(alt, az);
            let (color, radius) = Self::planet_style(planet);
            if Self::push_body_disc(
                &mut vertices,
                Vec3::new(dir[0], dir[1], dir[2]),
                alt.to_radians().sin().max(0.0) as f32,
                radius,
                color,
                right,
                up,
            ) {
                visible += 1;
            }
        }

        let mut stars_up = 0_u32;
        for star in &super::cosmos::STARS {
            let (alt, az) = super::cosmos::star_position(star.ra_deg, star.dec_deg, lat, lon, jd);
            let dir = super::cosmos::altaz_to_world_direction(alt, az);
            let (color, radius) = Self::star_style(star.mag);
            if Self::push_body_disc(
                &mut vertices,
                Vec3::new(dir[0], dir[1], dir[2]),
                alt.to_radians().sin().max(0.0) as f32,
                radius,
                color,
                right,
                up,
            ) {
                stars_up += 1;
            }
        }

        // Structural great circles (dotted): the ecliptic — the zodiac's backbone, which the Sun
        // and planets ride — in gold, and the celestial equator in cool blue. Below-horizon
        // samples self-cull, so only the arcs above the horizon draw.
        for i in 0..CELESTIAL_CIRCLE_POINTS {
            let ang = i as f64 / CELESTIAL_CIRCLE_POINTS as f64 * 360.0;
            let (e_alt, e_az) = super::cosmos::ecliptic_altaz(ang, lat, lon, jd);
            let e_dir = super::cosmos::altaz_to_world_direction(e_alt, e_az);
            Self::push_body_disc(
                &mut vertices,
                Vec3::new(e_dir[0], e_dir[1], e_dir[2]),
                e_alt.to_radians().sin().max(0.0) as f32,
                0.007,
                [1.00, 0.85, 0.42],
                right,
                up,
            );
            let (q_alt, q_az) = super::cosmos::equator_altaz(ang, lat, lon, jd);
            let q_dir = super::cosmos::altaz_to_world_direction(q_alt, q_az);
            Self::push_body_disc(
                &mut vertices,
                Vec3::new(q_dir[0], q_dir[1], q_dir[2]),
                q_alt.to_radians().sin().max(0.0) as f32,
                0.0045,
                [0.40, 0.58, 0.85],
                right,
                up,
            );
        }

        info!(
            "🌌 Celestial field: {visible}/7 bodies + {stars_up}/{} bright stars above the airless horizon",
            super::cosmos::STARS.len()
        );
        vertices
    }

    fn planet_style(planet: super::cosmos::Planet) -> ([f32; 3], f32) {
        match planet {
            super::cosmos::Planet::Mercury => ([0.70, 0.72, 0.68], 0.045),
            super::cosmos::Planet::Venus => ([1.00, 0.92, 0.70], 0.070),
            super::cosmos::Planet::Mars => ([0.95, 0.42, 0.28], 0.055),
            super::cosmos::Planet::Jupiter => ([0.95, 0.78, 0.54], 0.075),
            super::cosmos::Planet::Saturn => ([0.84, 0.75, 0.50], 0.065),
        }
    }

    /// Star disc colour + radius by visual magnitude: brighter stars render larger and whiter.
    fn star_style(mag: f32) -> ([f32; 3], f32) {
        let b = ((2.2 - mag) / 3.7).clamp(0.0, 1.0); // 0 (faint, ~mag 2) .. 1 (Sirius, ~ -1.5)
        let radius = 0.006 + 0.012 * b;
        let tint = 0.78 + 0.22 * b;
        ([tint, tint, (tint * 1.04).min(1.0)], radius)
    }

    fn push_body_disc(
        vertices: &mut Vec<Vertex>,
        dir: Vec3,
        horizon_intensity: f32,
        radius: f32,
        color: [f32; 3],
        right: Vec3,
        up: Vec3,
    ) -> bool {
        if horizon_intensity <= 0.0 {
            return false;
        }

        let fade = (horizon_intensity / 0.17).clamp(0.0, 1.0).sqrt();
        let color = [
            color[0] * (0.35 + 0.65 * fade),
            color[1] * (0.35 + 0.65 * fade),
            color[2] * (0.35 + 0.65 * fade),
        ];
        let center = dir.normalize_or_zero() * SKY_RADIUS + Vec3::Y * SKY_HORIZON_LIFT;
        let normal = [0.0, 1.0, 0.0];

        for i in 0..CELESTIAL_DISC_SEGMENTS {
            let a0 = i as f32 / CELESTIAL_DISC_SEGMENTS as f32 * std::f32::consts::TAU;
            let a1 = (i + 1) as f32 / CELESTIAL_DISC_SEGMENTS as f32 * std::f32::consts::TAU;
            let p0 = center + (right * a0.cos() + up * a0.sin()) * radius;
            let p1 = center + (right * a1.cos() + up * a1.sin()) * radius;
            vertices.push(Vertex {
                position: center.to_array(),
                normal,
                color,
            });
            vertices.push(Vertex {
                position: p0.to_array(),
                normal,
                color,
            });
            vertices.push(Vertex {
                position: p1.to_array(),
                normal,
                color,
            });
        }

        true
    }

    fn draw_mode(
        device: &Device,
        cmd: vk::CommandBuffer,
        layout: vk::PipelineLayout,
        push_constants: &mut PushConstants,
        mode: f32,
        vertex_buffer: vk::Buffer,
        vertex_count: u32,
    ) {
        push_constants.params[1] = mode;
        unsafe {
            device.cmd_push_constants(
                cmd,
                layout,
                vk::ShaderStageFlags::VERTEX | vk::ShaderStageFlags::FRAGMENT,
                0,
                std::slice::from_raw_parts(
                    (&raw const *push_constants).cast::<u8>(),
                    std::mem::size_of::<PushConstants>(),
                ),
            );
            device.cmd_bind_vertex_buffers(cmd, 0, &[vertex_buffer], &[0]);
            device.cmd_draw(cmd, vertex_count, 1, 0, 0);
        }
    }

    /// Find a suitable memory type
    unsafe fn find_memory_type(
        ctx: &VulkanContext,
        type_filter: u32,
        properties: vk::MemoryPropertyFlags,
    ) -> Result<u32> {
        let mem_properties = ctx
            .instance
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
            .extent(vk::Extent3D {
                width: extent.width,
                height: extent.height,
                depth: 1,
            })
            .mip_levels(1)
            .array_layers(1)
            .samples(vk::SampleCountFlags::TYPE_1)
            .tiling(vk::ImageTiling::OPTIMAL)
            .usage(vk::ImageUsageFlags::DEPTH_STENCIL_ATTACHMENT)
            .sharing_mode(vk::SharingMode::EXCLUSIVE)
            .initial_layout(vk::ImageLayout::UNDEFINED);
        let image = ctx
            .device
            .create_image(&image_info, None)
            .context("create depth image")?;

        let mem_req = ctx.device.get_image_memory_requirements(image);
        let mem_type = Self::find_memory_type(
            ctx,
            mem_req.memory_type_bits,
            vk::MemoryPropertyFlags::DEVICE_LOCAL,
        )?;
        let alloc_info = vk::MemoryAllocateInfo::default()
            .allocation_size(mem_req.size)
            .memory_type_index(mem_type);
        let memory = ctx
            .device
            .allocate_memory(&alloc_info, None)
            .context("alloc depth memory")?;
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
        let view = ctx
            .device
            .create_image_view(&view_info, None)
            .context("create depth view")?;
        Ok((image, memory, view))
    }

    /// Create the RG16F motion-vector target. Rung 2.4 starts with the shared
    /// jitter-induced vector; object and water vectors can compound into this target.
    unsafe fn create_motion_vector_resources(
        ctx: &VulkanContext,
        extent: vk::Extent2D,
    ) -> Result<(vk::Image, vk::DeviceMemory, vk::ImageView)> {
        let format = vk::Format::R16G16_SFLOAT;
        let image_info = vk::ImageCreateInfo::default()
            .image_type(vk::ImageType::TYPE_2D)
            .format(format)
            .extent(vk::Extent3D {
                width: extent.width,
                height: extent.height,
                depth: 1,
            })
            .mip_levels(1)
            .array_layers(1)
            .samples(vk::SampleCountFlags::TYPE_1)
            .tiling(vk::ImageTiling::OPTIMAL)
            .usage(vk::ImageUsageFlags::COLOR_ATTACHMENT | vk::ImageUsageFlags::SAMPLED)
            .sharing_mode(vk::SharingMode::EXCLUSIVE)
            .initial_layout(vk::ImageLayout::UNDEFINED);
        let image = ctx
            .device
            .create_image(&image_info, None)
            .context("create motion-vector image")?;

        let mem_req = ctx.device.get_image_memory_requirements(image);
        let mem_type = Self::find_memory_type(
            ctx,
            mem_req.memory_type_bits,
            vk::MemoryPropertyFlags::DEVICE_LOCAL,
        )?;
        let alloc_info = vk::MemoryAllocateInfo::default()
            .allocation_size(mem_req.size)
            .memory_type_index(mem_type);
        let memory = ctx
            .device
            .allocate_memory(&alloc_info, None)
            .context("alloc motion-vector memory")?;
        ctx.device.bind_image_memory(image, memory, 0)?;

        let view_info = vk::ImageViewCreateInfo::default()
            .image(image)
            .view_type(vk::ImageViewType::TYPE_2D)
            .format(format)
            .subresource_range(vk::ImageSubresourceRange {
                aspect_mask: vk::ImageAspectFlags::COLOR,
                base_mip_level: 0,
                level_count: 1,
                base_array_layer: 0,
                layer_count: 1,
            });
        let view = ctx
            .device
            .create_image_view(&view_info, None)
            .context("create motion-vector view")?;
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
            .image_extent(vk::Extent3D {
                width: w,
                height: h,
                depth: 1,
            });
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
        let ptr = device
            .map_memory(memory, 0, size, vk::MemoryMapFlags::empty())?
            .cast::<u8>();
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
        img.save(path)
            .map_err(|e| anyhow::anyhow!("png save {path}: {e}"))?;
        info!("📸 screenshot → {path} ({w}x{h}, bgra={is_bgra})");
        Ok(())
    }

    /// Render a frame using Dynamic Rendering (Vulkan 1.3)
    ///
    /// # Safety
    /// Requires valid Vulkan handles and properly synchronized operations
    #[allow(clippy::too_many_lines)]
    pub unsafe fn render_frame(
        &mut self,
        ctx: &VulkanContext,
        layer_color: [f32; 4],
    ) -> Result<bool> {
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
        ctx.device
            .reset_command_buffer(cmd, vk::CommandBufferResetFlags::empty())?;

        let begin_info = vk::CommandBufferBeginInfo::default()
            .flags(vk::CommandBufferUsageFlags::ONE_TIME_SUBMIT);
        ctx.device.begin_command_buffer(cmd, &begin_info)?;

        // === RUNG 4.2: ocean displacement compute (writes the displacement field) ===
        let ocean_time = self.frame_index as f32 * 0.02;
        self.ocean_compute.dispatch(&ctx.device, cmd, ocean_time);

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

        let motion_barrier_to_render = vk::ImageMemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::TOP_OF_PIPE)
            .src_access_mask(vk::AccessFlags2::empty())
            .dst_stage_mask(vk::PipelineStageFlags2::COLOR_ATTACHMENT_OUTPUT)
            .dst_access_mask(vk::AccessFlags2::COLOR_ATTACHMENT_WRITE)
            .old_layout(vk::ImageLayout::UNDEFINED)
            .new_layout(vk::ImageLayout::COLOR_ATTACHMENT_OPTIMAL)
            .image(self.motion_vector_image)
            .subresource_range(vk::ImageSubresourceRange {
                aspect_mask: vk::ImageAspectFlags::COLOR,
                base_mip_level: 0,
                level_count: 1,
                base_array_layer: 0,
                layer_count: 1,
            });

        let barriers_to_render = [
            image_barrier_to_render,
            depth_barrier_to_render,
            motion_barrier_to_render,
        ];
        let dependency_info_to_render =
            vk::DependencyInfo::default().image_memory_barriers(&barriers_to_render);

        ctx.device
            .cmd_pipeline_barrier2(cmd, &dependency_info_to_render);

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

        let motion_clear = vk::ClearValue {
            color: vk::ClearColorValue {
                float32: [0.0, 0.0, 0.0, 0.0],
            },
        };
        let motion_attachment = vk::RenderingAttachmentInfo::default()
            .image_view(self.motion_vector_view)
            .image_layout(vk::ImageLayout::COLOR_ATTACHMENT_OPTIMAL)
            .load_op(vk::AttachmentLoadOp::CLEAR)
            .store_op(vk::AttachmentStoreOp::STORE)
            .clear_value(motion_clear);

        let color_attachments = [color_attachment, motion_attachment];

        let depth_clear = vk::ClearValue {
            depth_stencil: vk::ClearDepthStencilValue {
                depth: 1.0,
                stencil: 0,
            },
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
        ctx.device
            .cmd_bind_pipeline(cmd, vk::PipelineBindPoint::GRAPHICS, self.pipeline.pipeline);

        // Push constants: camera + sun, plus params [time, mode, dt, motion-debug]. Three
        // passes share one pipeline: seabed (mode 0), Gerstner ocean (mode 1), celestial
        // field (mode 2). params.z carries the per-frame dt so the vertex stage can reproject
        // each surface vertex's previous-frame wave position into a true motion vector;
        // params.w > 0.5 paints that motion buffer as colour (CHTHONIC_SHOW_MOTION). This is
        // the current compounding boundary: add real layers here; do not replace the camera
        // path with speculative view cycling.
        const FRAME_DT: f32 = 0.02;
        let time = self.frame_index as f32 * FRAME_DT;
        let temporal_frame = self.temporal.begin_frame(
            self.swapchain.extent,
            self.camera.view_matrix(),
            self.camera.projection_matrix(),
        );
        let mut push_constants = PushConstants {
            model: Mat4::IDENTITY.to_cols_array_2d(),
            view: self.camera.view_as_array(),
            projection: temporal_frame.projection.to_cols_array_2d(),
            layer_color,
            params: [time, 0.0, FRAME_DT, if self.show_motion { 1.0 } else { 0.0 }],
        };
        Self::draw_mode(
            &ctx.device,
            cmd,
            self.pipeline.pipeline_layout,
            &mut push_constants,
            0.0,
            self.vertex_buffer,
            self.vertex_count,
        );
        Self::draw_mode(
            &ctx.device,
            cmd,
            self.pipeline.pipeline_layout,
            &mut push_constants,
            1.0,
            self.ocean_vertex_buffer,
            self.ocean_vertex_count,
        );

        // --- celestial field pass (mode 2, topocentric Sun/Moon/planets) ---
        if self.celestial_vertex_count > 0 {
            Self::draw_mode(
                &ctx.device,
                cmd,
                self.pipeline.pipeline_layout,
                &mut push_constants,
                2.0,
                self.celestial_vertex_buffer,
                self.celestial_vertex_count,
            );
        }

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
        let dependency_info_to_present =
            vk::DependencyInfo::default().image_memory_barriers(&barriers_to_present);

        ctx.device
            .cmd_pipeline_barrier2(cmd, &dependency_info_to_present);

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

        ctx.device
            .queue_submit(ctx.graphics_queue, &[submit_info], in_flight)?;

        // One-shot framebuffer capture (agent self-verify). Capture before present while the
        // swapchain image is still acquired; after present it belongs back to the swapchain.
        let next_frame_index = self.frame_index + 1;
        if !self.shot_taken && next_frame_index >= 5 {
            if let Some(path) = self.screenshot.clone() {
                if let Err(e) = self.capture_screenshot(ctx, image_index, &path) {
                    log::warn!("📸 screenshot failed: {e:#}");
                }
                self.shot_taken = true;
            }
        }

        // === PRESENT ===
        let needs_resize = self.swapchain.present(ctx.graphics_queue, image_index)?;
        if needs_resize {
            self.needs_resize = true;
        }

        // Frame count advances after all work for this acquired image has been queued.
        self.frame_index += 1;

        Ok(needs_resize)
    }

    /// Handle window resize
    pub unsafe fn handle_resize(
        &mut self,
        ctx: &VulkanContext,
        new_size: (u32, u32),
    ) -> Result<()> {
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
        ctx.device.destroy_image_view(self.motion_vector_view, None);
        ctx.device.destroy_image(self.motion_vector_image, None);
        ctx.device.free_memory(self.motion_vector_memory, None);
        let (depth_image, depth_memory, depth_view) =
            Self::create_depth_resources(ctx, self.swapchain.extent)?;
        self.depth_image = depth_image;
        self.depth_memory = depth_memory;
        self.depth_view = depth_view;
        let (motion_vector_image, motion_vector_memory, motion_vector_view) =
            Self::create_motion_vector_resources(ctx, self.swapchain.extent)?;
        self.motion_vector_image = motion_vector_image;
        self.motion_vector_memory = motion_vector_memory;
        self.motion_vector_view = motion_vector_view;

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

        // Free vertex buffers (seabed + ocean surface)
        device.destroy_buffer(self.vertex_buffer, None);
        device.free_memory(self.vertex_buffer_memory, None);
        device.destroy_buffer(self.ocean_vertex_buffer, None);
        device.free_memory(self.ocean_vertex_memory, None);
        device.destroy_buffer(self.celestial_vertex_buffer, None);
        device.free_memory(self.celestial_vertex_memory, None);

        // Ocean compute subsystem (pipeline, descriptors, storage image)
        self.ocean_compute.cleanup(device);

        // Free depth buffer
        device.destroy_image_view(self.depth_view, None);
        device.destroy_image(self.depth_image, None);
        device.free_memory(self.depth_memory, None);
        device.destroy_image_view(self.motion_vector_view, None);
        device.destroy_image(self.motion_vector_image, None);
        device.free_memory(self.motion_vector_memory, None);

        // Command pool (implicitly frees command buffers)
        device.destroy_command_pool(self.command_pool, None);

        // Pipeline
        self.pipeline.cleanup(device);

        // Swapchain
        self.swapchain.cleanup(device);

        debug!("✅ Renderer cleaned up");
    }
}
