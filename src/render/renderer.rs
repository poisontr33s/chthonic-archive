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
use gpu_allocator::vulkan::{Allocation, AllocationCreateDesc, Allocator};
use gpu_allocator::MemoryLocation;
use log::{debug, info};
use std::sync::{Arc, Mutex};

use super::camera::IsometricCamera;
use super::pipeline::{PushConstants, Vertex, VulkanPipeline};
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
    pub offscreen_color_image: vk::Image,
    pub offscreen_color_memory: vk::DeviceMemory,
    pub offscreen_color_view: vk::ImageView,
    pub history_color_images: [vk::Image; 2],
    pub history_color_allocs: [Option<Allocation>; 2],
    pub history_color_views: [vk::ImageView; 2],
    pub history_sampler: vk::Sampler,
    // TAA Gate 3 — resolve pipeline
    pub taa_pipeline: vk::Pipeline,
    pub taa_pipeline_layout: vk::PipelineLayout,
    pub taa_desc_pool: vk::DescriptorPool,
    pub taa_desc_set_layout: vk::DescriptorSetLayout,
    pub taa_desc_sets: Vec<vk::DescriptorSet>,  // one per frame-in-flight
    pub taa_enabled: bool,
    pub taa_debug: bool,
    /// Tracks whether each history slot has been written at least once.
    /// Prevents UNDEFINED→GENERAL from discarding valid history on frame N>0.
    pub history_initialized: [bool; 2],
    pub frame_index: u64,
    pub screenshot: Option<String>,
    pub show_motion: bool,
    pub lens: super::lens::Lens,
    pub heading: super::lens::Heading,
    pub shot_taken: bool,
    pub needs_resize: bool,
    pub camera: IsometricCamera,
    pub temporal: TemporalState,
    /// ACA cosmology glue — all seven bodies in their Ankhological signs at the scene epoch.
    /// Tuple: (label, sign_index 0..=11, sign_name, degree_within_sign).
    /// Computed once at init (the scene JD is deterministic); queryable at render time and by
    /// the game layer. Meaning stays owner-defined; this is position only.
    pub zodiac_bodies: Vec<(&'static str, usize, &'static str, f64)>,
}

impl Renderer {
    /// Create a new renderer with all subsystems initialized
    ///
    /// # Safety
    /// Requires valid Vulkan context
    pub unsafe fn new(ctx: &VulkanContext, window_size: (u32, u32), bathymetry_vertices: Vec<super::pipeline::Vertex>) -> Result<Self> {
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

        // Rung 4.2: displacement compute — created first so its graphics_set_layout can be
        // threaded into the graphics pipeline layout (water.vert samples the displacement image).
        let ocean_compute = super::ocean_compute::OceanCompute::new(ctx)?;

        // Create pipeline — set 0 is the ocean displacement sampler (water.vert reads it).
        let pipeline = VulkanPipeline::new(
            &ctx.device,
            &ctx.physical_device_properties,
            swapchain.format,
            &[ocean_compute.graphics_set_layout],
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

        // Rung 3: bathymetry vertices were loaded off the render thread by the caller
        // (std::thread + join before Renderer::new). IO is complete by the time we arrive here.
        let vertices = bathymetry_vertices;
        info!("🌊 Bathymetry mesh: {0} vertices (pre-loaded off render thread)", vertices.len());
        let (vertex_buffer, vertex_buffer_memory) = Self::create_vertex_buffer(ctx, &vertices)?;

        // Rung 4: LOD clipmap ocean mesh (levels=4, ring=32 → ~13 K cells, finest at centre).
        let ocean_vertices = super::ocean::clipmap_grid(4, 32);
        let (ocean_vertex_buffer, ocean_vertex_memory) =
            Self::create_vertex_buffer(ctx, &ocean_vertices)?;
        let ocean_vertex_count = u32::try_from(ocean_vertices.len()).unwrap();
        info!("🌊 Ocean clipmap: {0} vertices ({1} triangles)", ocean_vertices.len(), ocean_vertices.len() / 3);

        // Initialize isometric camera
        // Looking at origin from isometric angle, 10 units away, ortho size 5
        #[allow(clippy::cast_precision_loss)]
        let aspect_ratio = window_size.0 as f32 / window_size.1 as f32;
        let mut camera = IsometricCamera::new(Vec3::ZERO, 10.0, 5.0);
        camera.update_matrices(aspect_ratio);

        // The active lens is selected once, explicitly (§2.7 / 03A — never an auto-cycle), and is
        // the single source of the vantage: the celestial field is built facing the same eye the
        // draw loop renders through, so the as-above sky faces whoever is actually looking.
        let lens = super::lens::Lens::from_env();
        // The orientable heading (the rung's freedom): where the as-above lens looks. The eye is
        // fixed; only the heading turns. `CHTHONIC_LOOK=zodiac` aims at the Ankhological origin on
        // the true ecliptic — turning the head toward the wheel without moving the sky.
        let heading = Self::resolve_heading(
            super::cosmos::NEW_PROVIDENCE_LAT_DEG,
            super::cosmos::NEW_PROVIDENCE_LON_DEG,
            super::cosmos::scene_julian_day(),
        );

        // Rung 6.2: the verified celestial field made visible in the scene sky, facing the lens.
        let (cf_eye, cf_target) = lens.vantage(&camera, heading);
        let celestial_vertices = Self::celestial_field_vertices(
            cf_eye,
            cf_target,
            super::cosmos::scene_julian_day(),
        );
        let (celestial_vertex_buffer, celestial_vertex_memory) =
            Self::create_vertex_buffer(ctx, &celestial_vertices)?;
        let celestial_vertex_count = u32::try_from(celestial_vertices.len()).unwrap();
        info!("🌌 Celestial field mesh: {celestial_vertex_count} vertices");

        // Stage 2a: correspondence socket reads the true sky — ayanamsa + slot binding logged.
        {
            use super::correspondence::{Correspondence, SkyContext};
            let jd = super::cosmos::scene_julian_day();
            let ctx = SkyContext::new_providence(jd);
            let engine = Correspondence::new().with_slot(Box::new(super::zodiac::ZodiacSlot));
            for reading in engine.read(&ctx) {
                let ayan = reading
                    .entries
                    .iter()
                    .find(|(k, _)| k == "ayanamsa_deg")
                    .map_or("?", |(_, v)| v.as_str());
                info!("☥ Correspondence [{}]: ayanamsa {ayan}° (origin sirius-alcyone-midpoint)", reading.slot);
            }
        }
        // Stage 2b/2c: all seven bodies in their Ankhological signs — stored on the renderer so
        // the render loop and the game layer can query sign placements without recomputing.
        // Position only; meaning is the owner's.
        let zodiac_bodies = super::zodiac::bodies_in_signs(super::cosmos::scene_julian_day());
        info!(
            "☥ Zodiac bodies: {}",
            zodiac_bodies
                .iter()
                .map(|(label, _i, sign, deg)| format!("{label} in {sign} {deg:.1}°"))
                .collect::<Vec<_>>()
                .join(" · ")
        );

        info!("═══════════════════════════════════════════════════════════════");
        info!("🔥 RENDERER READY - Dynamic Rendering Pipeline Active!");
        info!("═══════════════════════════════════════════════════════════════");

        let (depth_image, depth_memory, depth_view) =
            Self::create_depth_resources(ctx, swapchain.extent)?;
        let (motion_vector_image, motion_vector_memory, motion_vector_view) =
            Self::create_motion_vector_resources(ctx, swapchain.extent)?;
        let (offscreen_color_image, offscreen_color_memory, offscreen_color_view) =
            Self::create_offscreen_color_resources(ctx, swapchain.extent, swapchain.format)?;
        let (history_color_images, history_color_allocs, history_color_views, history_sampler) =
            Self::create_history_resources(ctx, swapchain.extent)?;
        let taa_enabled = std::env::var("CHTHONIC_TAA").map_or(true, |v| v != "off");
        let taa_debug   = std::env::var("CHTHONIC_TAA_DEBUG").is_ok();
        let (taa_pipeline, taa_pipeline_layout, taa_desc_pool, taa_desc_set_layout, taa_desc_sets) =
            Self::create_taa_pipeline(ctx, vk::Format::R16G16B16A16_SFLOAT, swapchain.frames_in_flight,
                &history_color_views, history_sampler,
                &offscreen_color_view, &motion_vector_view)?;
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
            offscreen_color_image,
            offscreen_color_memory,
            offscreen_color_view,
            history_color_images,
            history_color_allocs,
            history_color_views,
            history_sampler,
            taa_pipeline,
            taa_pipeline_layout,
            taa_desc_pool,
            taa_desc_set_layout,
            taa_desc_sets,
            taa_enabled,
            taa_debug,
            history_initialized: [false, false],
            frame_index: 0,
            screenshot: std::env::var("CHTHONIC_SCREENSHOT").ok(),
            show_motion: std::env::var("CHTHONIC_SHOW_MOTION").is_ok(),
            lens,
            heading,
            shot_taken: false,
            needs_resize: false,
            camera,
            temporal,
            zodiac_bodies,
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

    /// Resolve the orientable heading for the as-above lens. Default: the explicit env heading
    /// ([`super::lens::Heading::from_env`]). `CHTHONIC_LOOK=zodiac` (or `ecliptic`) instead aims at
    /// the Ankhological origin keystone on the *true* ecliptic — turning the head toward the wheel
    /// without moving the sky. If the origin sits below the horizon at this scene date, the honest
    /// result is a heading that looks at empty ground; we do not fake the framing.
    fn resolve_heading(lat: f64, lon: f64, jd: f64) -> super::lens::Heading {
        match std::env::var("CHTHONIC_LOOK").ok().as_deref() {
            Some("zodiac") | Some("ecliptic") => {
                let origin_lon = super::zodiac::sign_boundaries_tropical(jd)[0];
                let (alt, az) = super::cosmos::ecliptic_altaz(origin_lon, lat, lon, jd);
                super::lens::Heading { az_deg: az as f32, alt_deg: alt as f32 }
            }
            _ => super::lens::Heading::from_env(),
        }
    }

    /// Build the celestial-field mesh facing the *active lens's* eye. The discs are CPU-billboarded
    /// to a single shared plane (the dome is small relative to the bodies), so the facing must track
    /// whichever lens is looking — `(eye, target)` come from [`super::lens::Lens::vantage`]. For the
    /// iso lens these reproduce the camera's own vantage exactly, so the iso render is unchanged.
    fn celestial_field_vertices(eye: Vec3, target: Vec3, jd: f64) -> Vec<Vertex> {
        let lat = super::cosmos::NEW_PROVIDENCE_LAT_DEG;
        let lon = super::cosmos::NEW_PROVIDENCE_LON_DEG;

        let forward = (target - eye).normalize();
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
                + 3 * CELESTIAL_CIRCLE_POINTS)
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
        // and planets ride — in gold; the celestial equator in cool blue; the galactic equator
        // (Milky Way midline, the Andean dark-cloud substrate) in milky white. Below-horizon
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
            let (g_alt, g_az) = super::cosmos::galactic_equator_altaz(ang, lat, lon, jd);
            let g_dir = super::cosmos::altaz_to_world_direction(g_alt, g_az);
            Self::push_body_disc(
                &mut vertices,
                Vec3::new(g_dir[0], g_dir[1], g_dir[2]),
                g_alt.to_radians().sin().max(0.0) as f32,
                0.006,
                [0.74, 0.76, 0.82],
                right,
                up,
            );
        }

        // Stage 2b: the Ankhological zodiac wheel — the twelve 30° sign boundaries marked on the
        // true ecliptic. Positions are math-forced (the verified Sirius/Alcyone origin + exact 30°
        // steps); only their rendered form is chosen. Boundary 0 — the origin, the Egyptian/Andean
        // midpoint — is the gold keystone; the other eleven are cool studs that punctuate the
        // ecliptic into its sectors. Below-horizon spokes self-cull like every other body.
        let mut wheel_up = 0_u32;
        for (k, &boundary_lon) in super::zodiac::sign_boundaries_tropical(jd).iter().enumerate() {
            let (alt, az) = super::cosmos::ecliptic_altaz(boundary_lon, lat, lon, jd);
            let dir = super::cosmos::altaz_to_world_direction(alt, az);
            // Form (the chosen layer): a lavender no body or great circle wears, so the boundaries
            // read as one set, not as scattered stars; the origin keystone is a larger warm
            // gold-white — the one mark the eye finds first.
            let (color, radius) = if k == 0 {
                ([1.00, 0.92, 0.58], 0.110) // the Ankhological origin — the keystone
            } else {
                ([0.82, 0.66, 1.00], 0.050) // the eleven lesser spokes
            };
            if Self::push_body_disc(
                &mut vertices,
                Vec3::new(dir[0], dir[1], dir[2]),
                alt.to_radians().sin().max(0.0) as f32,
                radius,
                color,
                right,
                up,
            ) {
                wheel_up += 1;
            }
        }

        info!(
            "🌌 Celestial field: {visible}/7 bodies + {stars_up}/{} bright stars above the airless horizon",
            super::cosmos::STARS.len()
        );
        info!("☥ Ankhological zodiac wheel: {wheel_up}/12 sign boundaries above the horizon (origin = Sirius/Alcyone midpoint)");
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

    /// Create the offscreen scene-colour target (TAA Gate 1). The scene renders here instead of
    /// straight to the swapchain; for now it is copied verbatim to the swapchain before present, so
    /// there is no visual change. Same format as the swapchain so the copy needs no conversion;
    /// `TRANSFER_SRC` for that copy and `SAMPLED` so a later resolve pass can read it.
    unsafe fn create_offscreen_color_resources(
        ctx: &VulkanContext,
        extent: vk::Extent2D,
        format: vk::Format,
    ) -> Result<(vk::Image, vk::DeviceMemory, vk::ImageView)> {
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
            .usage(
                vk::ImageUsageFlags::COLOR_ATTACHMENT
                    | vk::ImageUsageFlags::TRANSFER_SRC
                    | vk::ImageUsageFlags::SAMPLED,
            )
            .sharing_mode(vk::SharingMode::EXCLUSIVE)
            .initial_layout(vk::ImageLayout::UNDEFINED);
        let image = ctx
            .device
            .create_image(&image_info, None)
            .context("create offscreen colour image")?;

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
            .context("alloc offscreen colour memory")?;
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
            .context("create offscreen colour view")?;
        Ok((image, memory, view))
    }

    /// Create the history ping-pong buffers for TAA (Gate 2).
    /// Format is R16G16B16A16_SFLOAT (HDR). Needs COLOR_ATTACHMENT and SAMPLED.
    unsafe fn create_history_resources(
        ctx: &VulkanContext,
        extent: vk::Extent2D,
    ) -> Result<([vk::Image; 2], [Option<Allocation>; 2], [vk::ImageView; 2], vk::Sampler)> {
        let format = vk::Format::R16G16B16A16_SFLOAT;
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
            .usage(
                vk::ImageUsageFlags::COLOR_ATTACHMENT
                    | vk::ImageUsageFlags::SAMPLED
                    | vk::ImageUsageFlags::TRANSFER_DST
                    | vk::ImageUsageFlags::TRANSFER_SRC,
            )
            .sharing_mode(vk::SharingMode::EXCLUSIVE)
            .initial_layout(vk::ImageLayout::UNDEFINED);

        let mut images = [vk::Image::null(); 2];
        let mut allocs: [Option<Allocation>; 2] = [None, None];
        let mut views = [vk::ImageView::null(); 2];

        for i in 0..2 {
            let image = ctx
                .device
                .create_image(&image_info, None)
                .context("create history image")?;
            images[i] = image;

            let req = ctx.device.get_image_memory_requirements(image);
            let alloc = ctx.allocator.lock().unwrap().allocate(&AllocationCreateDesc {
                name: &format!("taa_history_{i}"),
                requirements: req,
                location: MemoryLocation::GpuOnly,
                linear: false,
                allocation_scheme: gpu_allocator::vulkan::AllocationScheme::GpuAllocatorManaged,
            }).context("gpu-allocator: alloc history image")?;
            ctx.device.bind_image_memory(image, alloc.memory(), alloc.offset())?;
            allocs[i] = Some(alloc);

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
            views[i] = ctx
                .device
                .create_image_view(&view_info, None)
                .context("create history view")?;
        }

        let sampler_info = vk::SamplerCreateInfo::default()
            .mag_filter(vk::Filter::LINEAR)
            .min_filter(vk::Filter::LINEAR)
            .address_mode_u(vk::SamplerAddressMode::CLAMP_TO_EDGE)
            .address_mode_v(vk::SamplerAddressMode::CLAMP_TO_EDGE)
            .address_mode_w(vk::SamplerAddressMode::CLAMP_TO_EDGE);
        let sampler = ctx
            .device
            .create_sampler(&sampler_info, None)
            .context("create history sampler")?;

        Ok((images, allocs, views, sampler))
    }

    /// Build the TAA resolve pipeline (Gate 3).
    /// Descriptor set: binding 0 = current (SAMPLED), 1 = history (SAMPLED), 2 = motion (SAMPLED).
    /// Push constant: TaaParams { texel_size: vec2, blend: f32, debug: f32 } = 16 bytes.
    /// Output format matches the swapchain (passed in as `out_format`).
    #[allow(clippy::too_many_arguments)]
    unsafe fn create_taa_pipeline(
        ctx: &VulkanContext,
        out_format: vk::Format,
        frames_in_flight: usize,
        history_views: &[vk::ImageView; 2],
        history_sampler: vk::Sampler,
        current_view: &vk::ImageView,
        motion_view: &vk::ImageView,
    ) -> Result<(vk::Pipeline, vk::PipelineLayout, vk::DescriptorPool, vk::DescriptorSetLayout, Vec<vk::DescriptorSet>)> {
        let device = &ctx.device;

        // --- descriptor set layout: 3 combined image samplers ---
        let bindings = [
            vk::DescriptorSetLayoutBinding::default()
                .binding(0)
                .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::FRAGMENT),
            vk::DescriptorSetLayoutBinding::default()
                .binding(1)
                .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::FRAGMENT),
            vk::DescriptorSetLayoutBinding::default()
                .binding(2)
                .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::FRAGMENT),
        ];
        let set_layout = device
            .create_descriptor_set_layout(
                &vk::DescriptorSetLayoutCreateInfo::default().bindings(&bindings),
                None,
            )
            .context("taa: create desc set layout")?;

        // --- pipeline layout: one push constant range (16 bytes: texel_xy + blend + debug) ---
        let push_range = vk::PushConstantRange::default()
            .stage_flags(vk::ShaderStageFlags::FRAGMENT)
            .offset(0)
            .size(16); // vec2 texel_size + f32 blend + f32 debug
        let pl_info = vk::PipelineLayoutCreateInfo::default()
            .set_layouts(std::slice::from_ref(&set_layout))
            .push_constant_ranges(std::slice::from_ref(&push_range));
        let pipeline_layout = device
            .create_pipeline_layout(&pl_info, None)
            .context("taa: create pipeline layout")?;

        // --- descriptor pool + sets (one per frame-in-flight) ---
        let pool_sizes = [vk::DescriptorPoolSize::default()
            .ty(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
            .descriptor_count(3 * u32::try_from(frames_in_flight).unwrap())];
        let desc_pool = device
            .create_descriptor_pool(
                &vk::DescriptorPoolCreateInfo::default()
                    .pool_sizes(&pool_sizes)
                    .max_sets(u32::try_from(frames_in_flight).unwrap()),
                None,
            )
            .context("taa: create desc pool")?;

        let set_layouts_vec = vec![set_layout; frames_in_flight];
        let desc_sets = device
            .allocate_descriptor_sets(
                &vk::DescriptorSetAllocateInfo::default()
                    .descriptor_pool(desc_pool)
                    .set_layouts(&set_layouts_vec),
            )
            .context("taa: alloc desc sets")?;

        // Write descriptors for every frame — current + history[frame%2] + motion.
        // Binding 1 = previous frame's history = the OTHER buffer (not the one we write to this
        // frame).  When frame_slot=i, cur_hist=i%2, so prev_hist=(i+1)%2.
        for (i, &ds) in desc_sets.iter().enumerate() {
            let hist_view = history_views[(i + 1) % 2];
            let img_current = vk::DescriptorImageInfo::default()
                .sampler(history_sampler)
                .image_view(*current_view)
                .image_layout(vk::ImageLayout::GENERAL);
            let img_history = vk::DescriptorImageInfo::default()
                .sampler(history_sampler)
                .image_view(hist_view)
                .image_layout(vk::ImageLayout::GENERAL);
            let img_motion = vk::DescriptorImageInfo::default()
                .sampler(history_sampler)
                .image_view(*motion_view)
                .image_layout(vk::ImageLayout::GENERAL);
            let writes = [
                vk::WriteDescriptorSet::default()
                    .dst_set(ds).dst_binding(0)
                    .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                    .image_info(std::slice::from_ref(&img_current)),
                vk::WriteDescriptorSet::default()
                    .dst_set(ds).dst_binding(1)
                    .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                    .image_info(std::slice::from_ref(&img_history)),
                vk::WriteDescriptorSet::default()
                    .dst_set(ds).dst_binding(2)
                    .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                    .image_info(std::slice::from_ref(&img_motion)),
            ];
            device.update_descriptor_sets(&writes, &[]);
        }

        // --- shaders ---
        let vert_spv = include_bytes!(concat!(env!("OUT_DIR"), "/taa_resolve.vert.spv"));
        let frag_spv = include_bytes!(concat!(env!("OUT_DIR"), "/taa_resolve.frag.spv"));
        // include_bytes! is only u8-aligned; convert to u32 slice via chunks, matching pipeline.rs.
        let vert_u32: Vec<u32> = vert_spv.chunks_exact(4)
            .map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]])).collect();
        let frag_u32: Vec<u32> = frag_spv.chunks_exact(4)
            .map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]])).collect();
        let vert_mod = device.create_shader_module(
            &vk::ShaderModuleCreateInfo::default().code(&vert_u32), None)?;
        let frag_mod = device.create_shader_module(
            &vk::ShaderModuleCreateInfo::default().code(&frag_u32), None)?;
        let entry = std::ffi::CStr::from_bytes_with_nul(b"main\0").unwrap();
        let stages = [
            vk::PipelineShaderStageCreateInfo::default()
                .stage(vk::ShaderStageFlags::VERTEX)
                .module(vert_mod)
                .name(entry),
            vk::PipelineShaderStageCreateInfo::default()
                .stage(vk::ShaderStageFlags::FRAGMENT)
                .module(frag_mod)
                .name(entry),
        ];

        // --- pipeline ---
        let vertex_input   = vk::PipelineVertexInputStateCreateInfo::default(); // no vertex buffer
        let input_assembly = vk::PipelineInputAssemblyStateCreateInfo::default()
            .topology(vk::PrimitiveTopology::TRIANGLE_LIST);
        let viewport_state = vk::PipelineViewportStateCreateInfo::default()
            .viewport_count(1).scissor_count(1);
        let rasterizer = vk::PipelineRasterizationStateCreateInfo::default()
            .polygon_mode(vk::PolygonMode::FILL)
            .cull_mode(vk::CullModeFlags::NONE)
            .line_width(1.0);
        let multisample = vk::PipelineMultisampleStateCreateInfo::default()
            .rasterization_samples(vk::SampleCountFlags::TYPE_1);
        let blend_attach = vk::PipelineColorBlendAttachmentState::default()
            .color_write_mask(vk::ColorComponentFlags::RGBA)
            .blend_enable(false);
        let color_blend = vk::PipelineColorBlendStateCreateInfo::default()
            .attachments(std::slice::from_ref(&blend_attach));
        let dyn_states = [vk::DynamicState::VIEWPORT, vk::DynamicState::SCISSOR];
        let dynamic_state = vk::PipelineDynamicStateCreateInfo::default()
            .dynamic_states(&dyn_states);

        // Dynamic rendering — output directly to swapchain format, no depth/stencil.
        let mut rendering_info = vk::PipelineRenderingCreateInfo::default()
            .color_attachment_formats(std::slice::from_ref(&out_format));

        let pipeline_info = vk::GraphicsPipelineCreateInfo::default()
            .stages(&stages)
            .vertex_input_state(&vertex_input)
            .input_assembly_state(&input_assembly)
            .viewport_state(&viewport_state)
            .rasterization_state(&rasterizer)
            .multisample_state(&multisample)
            .color_blend_state(&color_blend)
            .dynamic_state(&dynamic_state)
            .layout(pipeline_layout)
            .push_next(&mut rendering_info);

        let pipeline = device
            .create_graphics_pipelines(vk::PipelineCache::null(), &[pipeline_info], None)
            .map_err(|(_, e)| anyhow::anyhow!("taa: create pipeline: {e}"))?[0];

        device.destroy_shader_module(vert_mod, None);
        device.destroy_shader_module(frag_mod, None);

        Ok((pipeline, pipeline_layout, desc_pool, set_layout, desc_sets))
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
            .image(self.offscreen_color_image)
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
            .image_view(self.offscreen_color_view)
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

        // Bind the displacement image sampler (set 0) so water.vert can read it.
        // Must be bound before ANY draw call since the unified pipeline statically uses it.
        ctx.device.cmd_bind_descriptor_sets(
            cmd,
            vk::PipelineBindPoint::GRAPHICS,
            self.pipeline.pipeline_layout,
            0,
            &[self.ocean_compute.graphics_set],
            &[],
        );

        // Push constants: camera + sun, plus params [time, mode, dt, motion-debug]. Three
        // passes share one pipeline: seabed (mode 0), Gerstner ocean (mode 1), celestial
        // field (mode 2). params.z carries the per-frame dt so the vertex stage can reproject
        // each surface vertex's previous-frame wave position into a true motion vector;
        // params.w > 0.5 paints that motion buffer as colour (CHTHONIC_SHOW_MOTION). This is
        // the current compounding boundary: add real layers here; do not replace the camera
        // path with speculative view cycling.
        const FRAME_DT: f32 = 0.02;
        let time = self.frame_index as f32 * FRAME_DT;
        let aspect =
            self.swapchain.extent.width as f32 / self.swapchain.extent.height.max(1) as f32;
        let (lens_view, lens_proj) =
            super::lens::matrices(self.lens, &self.camera, self.heading, aspect);
        if self.frame_index == 0 {
            info!("🔭 Lens: {}", self.lens.label());
        }
        let temporal_frame = self.temporal.begin_frame(self.swapchain.extent, lens_view, lens_proj);
        let mut push_constants = PushConstants {
            model: Mat4::IDENTITY.to_cols_array_2d(),
            view: lens_view.to_cols_array_2d(),
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

        // === RESOLVE (TAA Gate 3) ===
        // TAA path: transitions inputs to SHADER_READ_ONLY, runs the fullscreen resolve pipeline
        // (neighbourhood clamp + blend), writes directly to the swapchain image.
        // Fallback: CHTHONIC_TAA=off preserves the Gate 1 verbatim-copy path for regression diff.
        let cur_hist  = (self.frame_index % 2) as usize;
        let prev_hist = 1 - cur_hist;

        let color_subresource = vk::ImageSubresourceRange {
            aspect_mask: vk::ImageAspectFlags::COLOR,
            base_mip_level: 0,
            level_count: 1,
            base_array_layer: 0,
            layer_count: 1,
        };

        if self.taa_enabled {
            let barriers_pre = [
                vk::ImageMemoryBarrier2::default()
                    .src_stage_mask(vk::PipelineStageFlags2::COLOR_ATTACHMENT_OUTPUT)
                    .src_access_mask(vk::AccessFlags2::COLOR_ATTACHMENT_WRITE)
                    .dst_stage_mask(vk::PipelineStageFlags2::FRAGMENT_SHADER)
                    .dst_access_mask(vk::AccessFlags2::SHADER_READ)
                    .old_layout(vk::ImageLayout::COLOR_ATTACHMENT_OPTIMAL)
                    .new_layout(vk::ImageLayout::GENERAL)
                    .image(self.offscreen_color_image)
                    .subresource_range(color_subresource),
                vk::ImageMemoryBarrier2::default()
                    .src_stage_mask(vk::PipelineStageFlags2::COLOR_ATTACHMENT_OUTPUT)
                    .src_access_mask(vk::AccessFlags2::COLOR_ATTACHMENT_WRITE)
                    .dst_stage_mask(vk::PipelineStageFlags2::FRAGMENT_SHADER)
                    .dst_access_mask(vk::AccessFlags2::SHADER_READ)
                    .old_layout(vk::ImageLayout::COLOR_ATTACHMENT_OPTIMAL)
                    .new_layout(vk::ImageLayout::GENERAL)
                    .image(self.motion_vector_image)
                    .subresource_range(color_subresource),
                vk::ImageMemoryBarrier2::default()
                    .src_stage_mask(vk::PipelineStageFlags2::TOP_OF_PIPE)
                    .src_access_mask(vk::AccessFlags2::empty())
                    .dst_stage_mask(vk::PipelineStageFlags2::FRAGMENT_SHADER)
                    .dst_access_mask(vk::AccessFlags2::SHADER_READ)
                    .old_layout(if self.history_initialized[prev_hist] {
                        vk::ImageLayout::GENERAL
                    } else {
                        vk::ImageLayout::UNDEFINED
                    })
                    .new_layout(vk::ImageLayout::GENERAL)
                    .image(self.history_color_images[prev_hist])
                    .subresource_range(color_subresource),
                // cur_hist: resolve writes here; transition to COLOR_ATTACHMENT_OPTIMAL for rendering.
                vk::ImageMemoryBarrier2::default()
                    .src_stage_mask(vk::PipelineStageFlags2::TOP_OF_PIPE)
                    .src_access_mask(vk::AccessFlags2::empty())
                    .dst_stage_mask(vk::PipelineStageFlags2::COLOR_ATTACHMENT_OUTPUT)
                    .dst_access_mask(vk::AccessFlags2::COLOR_ATTACHMENT_WRITE)
                    .old_layout(vk::ImageLayout::UNDEFINED)
                    .new_layout(vk::ImageLayout::COLOR_ATTACHMENT_OPTIMAL)
                    .image(self.history_color_images[cur_hist])
                    .subresource_range(color_subresource),
                // swapchain: transition to TRANSFER_DST for the post-resolve blit.
                vk::ImageMemoryBarrier2::default()
                    .src_stage_mask(vk::PipelineStageFlags2::TOP_OF_PIPE)
                    .src_access_mask(vk::AccessFlags2::empty())
                    .dst_stage_mask(vk::PipelineStageFlags2::ALL_TRANSFER)
                    .dst_access_mask(vk::AccessFlags2::TRANSFER_WRITE)
                    .old_layout(vk::ImageLayout::UNDEFINED)
                    .new_layout(vk::ImageLayout::TRANSFER_DST_OPTIMAL)
                    .image(self.swapchain.images[image_index as usize])
                    .subresource_range(color_subresource),
            ];
            ctx.device.cmd_pipeline_barrier2(
                cmd, &vk::DependencyInfo::default().image_memory_barriers(&barriers_pre));

            // Resolve into cur_hist (not swapchain) — this is the write-back.
            let hist_attach = vk::RenderingAttachmentInfo::default()
                .image_view(self.history_color_views[cur_hist])
                .image_layout(vk::ImageLayout::COLOR_ATTACHMENT_OPTIMAL)
                .load_op(vk::AttachmentLoadOp::DONT_CARE)
                .store_op(vk::AttachmentStoreOp::STORE);
            let rendering_info = vk::RenderingInfo::default()
                .render_area(vk::Rect2D { offset: vk::Offset2D::default(), extent: self.swapchain.extent })
                .layer_count(1)
                .color_attachments(std::slice::from_ref(&hist_attach));
            ctx.device.cmd_begin_rendering(cmd, &rendering_info);

            let ext = self.swapchain.extent;
            ctx.device.cmd_set_viewport(cmd, 0, &[vk::Viewport {
                x: 0.0, y: 0.0,
                width: ext.width as f32, height: ext.height as f32,
                min_depth: 0.0, max_depth: 1.0,
            }]);
            ctx.device.cmd_set_scissor(cmd, 0, &[vk::Rect2D {
                offset: vk::Offset2D::default(), extent: ext,
            }]);
            ctx.device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::GRAPHICS, self.taa_pipeline);
            let frame_slot = (self.frame_index % self.taa_desc_sets.len() as u64) as usize;
            ctx.device.cmd_bind_descriptor_sets(
                cmd, vk::PipelineBindPoint::GRAPHICS, self.taa_pipeline_layout, 0,
                &[self.taa_desc_sets[frame_slot]], &[]);

            #[repr(C)]
            #[derive(Clone, Copy, bytemuck::Pod, bytemuck::Zeroable)]
            struct TaaParams { texel: [f32; 2], blend: f32, debug: f32 }
            let params = TaaParams {
                texel: [1.0 / ext.width as f32, 1.0 / ext.height as f32],
                blend: 0.1,
                debug: if self.taa_debug { 1.0 } else { 0.0 },
            };
            ctx.device.cmd_push_constants(
                cmd, self.taa_pipeline_layout,
                vk::ShaderStageFlags::FRAGMENT, 0,
                bytemuck::bytes_of(&params));
            ctx.device.cmd_draw(cmd, 3, 1, 0, 0);
            ctx.device.cmd_end_rendering(cmd);

            // Transition cur_hist to TRANSFER_SRC, then blit to swapchain TRANSFER_DST.
            let barriers_post = [
                vk::ImageMemoryBarrier2::default()
                    .src_stage_mask(vk::PipelineStageFlags2::COLOR_ATTACHMENT_OUTPUT)
                    .src_access_mask(vk::AccessFlags2::COLOR_ATTACHMENT_WRITE)
                    .dst_stage_mask(vk::PipelineStageFlags2::ALL_TRANSFER)
                    .dst_access_mask(vk::AccessFlags2::TRANSFER_READ)
                    .old_layout(vk::ImageLayout::COLOR_ATTACHMENT_OPTIMAL)
                    .new_layout(vk::ImageLayout::TRANSFER_SRC_OPTIMAL)
                    .image(self.history_color_images[cur_hist])
                    .subresource_range(color_subresource),
            ];
            ctx.device.cmd_pipeline_barrier2(
                cmd, &vk::DependencyInfo::default().image_memory_barriers(&barriers_post));

            let sub = vk::ImageSubresourceLayers {
                aspect_mask: vk::ImageAspectFlags::COLOR,
                mip_level: 0, base_array_layer: 0, layer_count: 1,
            };
            let blit = vk::ImageBlit::default()
                .src_subresource(sub)
                .src_offsets([
                    vk::Offset3D::default(),
                    vk::Offset3D { x: ext.width as i32, y: ext.height as i32, z: 1 },
                ])
                .dst_subresource(sub)
                .dst_offsets([
                    vk::Offset3D::default(),
                    vk::Offset3D { x: ext.width as i32, y: ext.height as i32, z: 1 },
                ]);
            ctx.device.cmd_blit_image(
                cmd,
                self.history_color_images[cur_hist], vk::ImageLayout::TRANSFER_SRC_OPTIMAL,
                self.swapchain.images[image_index as usize], vk::ImageLayout::TRANSFER_DST_OPTIMAL,
                &[blit], vk::Filter::LINEAR,
            );

            // cur_hist stays in TRANSFER_SRC_OPTIMAL; reclassify as GENERAL for next frame read.
            // swapchain → PRESENT.
            let barriers_final = [
                vk::ImageMemoryBarrier2::default()
                    .src_stage_mask(vk::PipelineStageFlags2::ALL_TRANSFER)
                    .src_access_mask(vk::AccessFlags2::TRANSFER_READ)
                    .dst_stage_mask(vk::PipelineStageFlags2::TOP_OF_PIPE)
                    .dst_access_mask(vk::AccessFlags2::empty())
                    .old_layout(vk::ImageLayout::TRANSFER_SRC_OPTIMAL)
                    .new_layout(vk::ImageLayout::GENERAL)
                    .image(self.history_color_images[cur_hist])
                    .subresource_range(color_subresource),
                vk::ImageMemoryBarrier2::default()
                    .src_stage_mask(vk::PipelineStageFlags2::ALL_TRANSFER)
                    .src_access_mask(vk::AccessFlags2::TRANSFER_WRITE)
                    .dst_stage_mask(vk::PipelineStageFlags2::BOTTOM_OF_PIPE)
                    .dst_access_mask(vk::AccessFlags2::empty())
                    .old_layout(vk::ImageLayout::TRANSFER_DST_OPTIMAL)
                    .new_layout(vk::ImageLayout::PRESENT_SRC_KHR)
                    .image(self.swapchain.images[image_index as usize])
                    .subresource_range(color_subresource),
            ];
            ctx.device.cmd_pipeline_barrier2(
                cmd, &vk::DependencyInfo::default().image_memory_barriers(&barriers_final));

            self.history_initialized[cur_hist] = true;
        } else {
            // CHTHONIC_TAA=off — Gate 1 verbatim-copy fallback.
            let pre = [
                vk::ImageMemoryBarrier2::default()
                    .src_stage_mask(vk::PipelineStageFlags2::COLOR_ATTACHMENT_OUTPUT)
                    .src_access_mask(vk::AccessFlags2::COLOR_ATTACHMENT_WRITE)
                    .dst_stage_mask(vk::PipelineStageFlags2::ALL_TRANSFER)
                    .dst_access_mask(vk::AccessFlags2::TRANSFER_READ)
                    .old_layout(vk::ImageLayout::COLOR_ATTACHMENT_OPTIMAL)
                    .new_layout(vk::ImageLayout::TRANSFER_SRC_OPTIMAL)
                    .image(self.offscreen_color_image)
                    .subresource_range(color_subresource),
                vk::ImageMemoryBarrier2::default()
                    .src_stage_mask(vk::PipelineStageFlags2::TOP_OF_PIPE)
                    .src_access_mask(vk::AccessFlags2::empty())
                    .dst_stage_mask(vk::PipelineStageFlags2::ALL_TRANSFER)
                    .dst_access_mask(vk::AccessFlags2::TRANSFER_WRITE)
                    .old_layout(vk::ImageLayout::UNDEFINED)
                    .new_layout(vk::ImageLayout::TRANSFER_DST_OPTIMAL)
                    .image(self.swapchain.images[image_index as usize])
                    .subresource_range(color_subresource),
            ];
            ctx.device.cmd_pipeline_barrier2(
                cmd, &vk::DependencyInfo::default().image_memory_barriers(&pre));
            let copy = vk::ImageCopy::default()
                .src_subresource(vk::ImageSubresourceLayers { aspect_mask: vk::ImageAspectFlags::COLOR, mip_level: 0, base_array_layer: 0, layer_count: 1 })
                .dst_subresource(vk::ImageSubresourceLayers { aspect_mask: vk::ImageAspectFlags::COLOR, mip_level: 0, base_array_layer: 0, layer_count: 1 })
                .extent(vk::Extent3D { width: self.swapchain.extent.width, height: self.swapchain.extent.height, depth: 1 });
            ctx.device.cmd_copy_image(cmd,
                self.offscreen_color_image, vk::ImageLayout::TRANSFER_SRC_OPTIMAL,
                self.swapchain.images[image_index as usize], vk::ImageLayout::TRANSFER_DST_OPTIMAL, &[copy]);
            let to_present = vk::ImageMemoryBarrier2::default()
                .src_stage_mask(vk::PipelineStageFlags2::ALL_TRANSFER)
                .src_access_mask(vk::AccessFlags2::TRANSFER_WRITE)
                .dst_stage_mask(vk::PipelineStageFlags2::BOTTOM_OF_PIPE)
                .dst_access_mask(vk::AccessFlags2::empty())
                .old_layout(vk::ImageLayout::TRANSFER_DST_OPTIMAL)
                .new_layout(vk::ImageLayout::PRESENT_SRC_KHR)
                .image(self.swapchain.images[image_index as usize])
                .subresource_range(color_subresource);
            ctx.device.cmd_pipeline_barrier2(
                cmd, &vk::DependencyInfo::default().image_memory_barriers(std::slice::from_ref(&to_present)));
        }

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
        ctx.device.destroy_image_view(self.offscreen_color_view, None);
        ctx.device.destroy_image(self.offscreen_color_image, None);
        ctx.device.free_memory(self.offscreen_color_memory, None);

        // Free old history buffers
        ctx.device.destroy_sampler(self.history_sampler, None);
        for i in 0..2 {
            ctx.device.destroy_image_view(self.history_color_views[i], None);
            ctx.device.destroy_image(self.history_color_images[i], None);
            if let Some(alloc) = self.history_color_allocs[i].take() {
                let _ = ctx.allocator.lock().unwrap().free(alloc);
            }
        }

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
        let (offscreen_color_image, offscreen_color_memory, offscreen_color_view) =
            Self::create_offscreen_color_resources(ctx, self.swapchain.extent, self.swapchain.format)?;
        self.offscreen_color_image = offscreen_color_image;
        self.offscreen_color_memory = offscreen_color_memory;
        self.offscreen_color_view = offscreen_color_view;
        
        let (history_color_images, history_color_allocs, history_color_views, history_sampler) =
            Self::create_history_resources(ctx, self.swapchain.extent)?;
        self.history_color_images = history_color_images;
        self.history_color_allocs = history_color_allocs;
        self.history_color_views = history_color_views;
        self.history_sampler = history_sampler;
        self.history_initialized = [false, false];

        // Re-write TAA descriptor sets with the new image views (old views were just destroyed).
        for (i, &ds) in self.taa_desc_sets.iter().enumerate() {
            let hist_view = self.history_color_views[(i + 1) % 2];
            let img_current = vk::DescriptorImageInfo::default()
                .sampler(self.history_sampler)
                .image_view(self.offscreen_color_view)
                .image_layout(vk::ImageLayout::GENERAL);
            let img_history = vk::DescriptorImageInfo::default()
                .sampler(self.history_sampler)
                .image_view(hist_view)
                .image_layout(vk::ImageLayout::GENERAL);
            let img_motion = vk::DescriptorImageInfo::default()
                .sampler(self.history_sampler)
                .image_view(self.motion_vector_view)
                .image_layout(vk::ImageLayout::GENERAL);
            let writes = [
                vk::WriteDescriptorSet::default()
                    .dst_set(ds).dst_binding(0)
                    .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                    .image_info(std::slice::from_ref(&img_current)),
                vk::WriteDescriptorSet::default()
                    .dst_set(ds).dst_binding(1)
                    .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                    .image_info(std::slice::from_ref(&img_history)),
                vk::WriteDescriptorSet::default()
                    .dst_set(ds).dst_binding(2)
                    .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                    .image_info(std::slice::from_ref(&img_motion)),
            ];
            ctx.device.update_descriptor_sets(&writes, &[]);
        }

        // Update camera aspect ratio for new window dimensions
        #[allow(clippy::cast_precision_loss)]
        let aspect_ratio = new_size.0 as f32 / new_size.1.max(1) as f32;
        self.camera.update_matrices(aspect_ratio);
        debug!("📐 Camera aspect ratio updated: {aspect_ratio:.3}");

        self.needs_resize = false;
        Ok(())
    }

    /// Clean up all renderer resources
    pub unsafe fn cleanup(&mut self, device: &Device, allocator: &Arc<Mutex<Allocator>>) {
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
        self.ocean_compute.cleanup(device, &mut allocator.lock().unwrap());

        // Free depth buffer
        device.destroy_image_view(self.depth_view, None);
        device.destroy_image(self.depth_image, None);
        device.free_memory(self.depth_memory, None);
        device.destroy_image_view(self.motion_vector_view, None);
        device.destroy_image(self.motion_vector_image, None);
        device.free_memory(self.motion_vector_memory, None);
        device.destroy_image_view(self.offscreen_color_view, None);
        device.destroy_image(self.offscreen_color_image, None);
        device.free_memory(self.offscreen_color_memory, None);

        // Free TAA Gate 2 history buffers
        device.destroy_sampler(self.history_sampler, None);
        for i in 0..2 {
            device.destroy_image_view(self.history_color_views[i], None);
            device.destroy_image(self.history_color_images[i], None);
            if let Some(alloc) = self.history_color_allocs[i].take() {
                let _ = allocator.lock().unwrap().free(alloc);
            }
        }

        // Free TAA Gate 3 resolve pipeline resources
        device.destroy_pipeline(self.taa_pipeline, None);
        device.destroy_pipeline_layout(self.taa_pipeline_layout, None);
        device.destroy_descriptor_pool(self.taa_desc_pool, None);
        device.destroy_descriptor_set_layout(self.taa_desc_set_layout, None);

        // Command pool (implicitly frees command buffers)
        device.destroy_command_pool(self.command_pool, None);

        // Pipeline
        self.pipeline.cleanup(device);

        // Swapchain
        self.swapchain.cleanup(device);

        debug!("✅ Renderer cleaned up");
    }
}
