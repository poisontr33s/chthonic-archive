//! Rung 4.2 — ocean displacement compute subsystem.
//!
//! 4.2a: compute pipeline seam closed — water.vert samples displacement image.
//! 4.2b: Phillips spectrum analytical body in ocean_displace.comp.
//! 4.2c: Full Tessendorf IFFT pipeline:
//!         h0(k) → evolve h(k,t) → N×butterfly H passes → N×butterfly V passes → displacement.
//!
//! The `OceanCompute` struct always dispatches the Tessendorf path; the old single-shader
//! body (ocean_displace.comp) is superseded once 4.2c wiring is complete.

//! @SID:    RENDER_OCEAN_COMPUTE_V1
//! @Shabti: Ocean-Compute

use anyhow::{Context, Result};
use ash::{Device, vk};
use gpu_allocator::vulkan::{Allocation, AllocationCreateDesc, AllocationScheme};
use gpu_allocator::MemoryLocation;
use log::info;

use super::vulkan::VulkanContext;

/// Number of FFT texels per side. Must be a power of two; log2(RESOLUTION) = number of stages.
const RESOLUTION: u32 = 256;
/// FFT stages per axis.
const FFT_STAGES: u32 = 8; // log2(256)

/// World half-extents of the surface grid (must match ocean::surface_grid constants).
const X_HALF: f32 = 2.45;
const Z_HALF: f32 = 0.92;

/// Wind parameters — matched to Bahama trade-wind mean.
const WIND_SPEED: f32 = 3.8;
const WIND_DIR: f32 = 90.0;
const PHILLIPS_A: f32 = 0.0004;
/// FFT patch world size (sets the physical wavenumber scale).
const PATCH_SIZE: f32 = 5.0;

// ─────────────────────────────────────────────────────────────────────────────
// Push-constant layouts (one per shader).
// ─────────────────────────────────────────────────────────────────────────────

/// ocean_displace.comp — legacy fallback path (4.2b analytical sum).
#[repr(C)]
#[derive(Clone, Copy)]
#[allow(dead_code)]
struct DisplacePush {
    time: f32,
    x_half: f32,
    z_half: f32,
    resolution: u32,
}

/// ocean_h0.comp — initial spectrum (dispatched once / wind-change).
#[repr(C)]
#[derive(Clone, Copy)]
struct H0Push {
    resolution: u32,
    wind_speed: f32,
    wind_dir: f32,
    phillips_a: f32,
}

/// ocean_evolve.comp — per-frame time evolution.
#[repr(C)]
#[derive(Clone, Copy)]
struct EvolvePush {
    time: f32,
    resolution: u32,
    patch_size: f32,
    _pad: f32,
}

/// ocean_fft.comp — butterfly stage (axis-split).
#[repr(C)]
#[derive(Clone, Copy)]
struct FftPush {
    stage: u32,
    axis: u32,
    resolution: u32,
    _pad: u32,
}

// ─────────────────────────────────────────────────────────────────────────────
// OceanCompute
// ─────────────────────────────────────────────────────────────────────────────

/// The full Tessendorf ocean compute subsystem.
///
/// Images:
///   disp_image  — final displacement (rgba16f); water.vert samples this (graphics_set).
///   h0_image    — initial Phillips spectrum h0(k) (rgba16f); written once.
///   fft_a/b     — FFT ping-pong pair (rgba16f); evolve writes to a, passes alternate.
///
/// Dispatch sequence per frame:
///   evolve(t)                       → writes fft_a
///   for stage in 0..8               → butterfly H (fft_a↔fft_b)
///   for stage in 0..8               → butterfly V (fft_a↔fft_b)
///   blit/copy from "current" to disp_image if needed (or disp_image IS the final ping target)
///
/// To keep disp_image as the final IFFT output, we arrange the ping-pong so that
/// the last FFT stage writes into disp_image. With 16 total stages (8H + 8V),
/// and evolve writing fft_a as initial source:
///   stage 0  H: src=fft_a → dst=fft_b
///   stage 1  H: src=fft_b → dst=fft_a
///   ...
///   stage 7  H: src=fft_b → dst=fft_a   (8 stages, even-indexed dst=fft_b, odd=fft_a; final=fft_a)
///   stage 0  V: src=fft_a → dst=fft_b
///   ...
///   stage 7  V: src=fft_b → dst=fft_a   (same pattern; final=fft_a)
/// So after 16 stages the IFFT result is in fft_a. We then need one copy pass into disp_image,
/// OR we swap which image the graphics_set points at. The simpler route: use disp_image as the
/// final FFT destination by substituting it for fft_a on the LAST stage.
/// Implemented below: for the final stage (stage 15) dst = disp_image.
pub struct OceanCompute {
    // Displacement image — the output water.vert samples.
    pub disp_image: vk::Image,
    disp_alloc:     Option<Allocation>,
    pub disp_view:  vk::ImageView,
    pub sampler:    vk::Sampler,

    // Initial spectrum h0(k).
    h0_image: vk::Image,
    h0_alloc: Option<Allocation>,
    h0_view:  vk::ImageView,

    // FFT ping-pong pair.
    fft_a_image: vk::Image,
    fft_a_alloc: Option<Allocation>,
    fft_a_view:  vk::ImageView,
    fft_b_image: vk::Image,
    fft_b_alloc: Option<Allocation>,
    fft_b_view:  vk::ImageView,

    // Descriptor pool.
    pub desc_pool: vk::DescriptorPool,

    // h0 pipeline (once at init).
    h0_set_layout: vk::DescriptorSetLayout,
    h0_set:        vk::DescriptorSet,
    h0_pipeline_layout: vk::PipelineLayout,
    h0_pipeline:        vk::Pipeline,
    h0_shader:          vk::ShaderModule,

    // Evolve pipeline (per frame).
    evolve_set_layout: vk::DescriptorSetLayout,
    evolve_set:        vk::DescriptorSet,
    evolve_pipeline_layout: vk::PipelineLayout,
    evolve_pipeline:        vk::Pipeline,
    evolve_shader:          vk::ShaderModule,

    // FFT pipeline (16 passes per frame, src/dst vary per stage).
    // We use 3 pre-allocated descriptor sets:
    //   fft_set_ab: src=fft_a, dst=fft_b
    //   fft_set_ba: src=fft_b, dst=fft_a
    //   fft_set_aD: src=fft_a, dst=disp_image  (final stage)
    //   fft_set_bD: src=fft_b, dst=disp_image  (final stage alt)
    fft_set_layout: vk::DescriptorSetLayout,
    fft_set_ab:     vk::DescriptorSet,
    fft_set_ba:     vk::DescriptorSet,
    fft_set_aD:     vk::DescriptorSet,
    fft_set_bD:     vk::DescriptorSet,
    fft_pipeline_layout: vk::PipelineLayout,
    fft_pipeline:        vk::Pipeline,
    fft_shader:          vk::ShaderModule,

    // Graphics sampler descriptor set — water.vert binds this.
    pub graphics_set_layout: vk::DescriptorSetLayout,
    pub graphics_set:        vk::DescriptorSet,

    pub resolution: u32,
    /// Whether h0 has been dispatched this run.
    h0_dispatched: bool,
}

fn color_range() -> vk::ImageSubresourceRange {
    vk::ImageSubresourceRange {
        aspect_mask:      vk::ImageAspectFlags::COLOR,
        base_mip_level:   0,
        level_count:      1,
        base_array_layer: 0,
        layer_count:      1,
    }
}

/// Allocate and bind a DEVICE_LOCAL rgba16f STORAGE image via gpu-allocator.
unsafe fn alloc_storage_image(
    ctx: &VulkanContext,
    label: &str,
    resolution: u32,
) -> Result<(vk::Image, Allocation, vk::ImageView)> {
    let device = &ctx.device;
    let format = vk::Format::R16G16B16A16_SFLOAT;

    let image = device
        .create_image(
            &vk::ImageCreateInfo::default()
                .image_type(vk::ImageType::TYPE_2D)
                .format(format)
                .extent(vk::Extent3D { width: resolution, height: resolution, depth: 1 })
                .mip_levels(1)
                .array_layers(1)
                .samples(vk::SampleCountFlags::TYPE_1)
                .tiling(vk::ImageTiling::OPTIMAL)
                .usage(vk::ImageUsageFlags::STORAGE | vk::ImageUsageFlags::SAMPLED)
                .sharing_mode(vk::SharingMode::EXCLUSIVE)
                .initial_layout(vk::ImageLayout::UNDEFINED),
            None,
        )
        .context("create ocean image")?;

    let req = device.get_image_memory_requirements(image);
    let alloc = ctx.allocator.lock().unwrap().allocate(&AllocationCreateDesc {
        name:     label,
        requirements: req,
        location: MemoryLocation::GpuOnly,
        linear:   false,
        allocation_scheme: AllocationScheme::GpuAllocatorManaged,
    }).context("gpu-allocator: alloc ocean image")?;
    device.bind_image_memory(image, alloc.memory(), alloc.offset())?;

    let view = device
        .create_image_view(
            &vk::ImageViewCreateInfo::default()
                .image(image)
                .view_type(vk::ImageViewType::TYPE_2D)
                .format(format)
                .subresource_range(color_range()),
            None,
        )
        .context("create ocean image view")?;

    Ok((image, alloc, view))
}

unsafe fn create_shader(device: &Device, spv: &[u8]) -> Result<vk::ShaderModule> {
    assert!(spv.len().is_multiple_of(4));
    let words: Vec<u32> = spv.chunks_exact(4)
        .map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]]))
        .collect();
    device
        .create_shader_module(&vk::ShaderModuleCreateInfo::default().code(&words), None)
        .context("create shader module")
}

/// Build a compute pipeline with one descriptor set layout + push constants.
unsafe fn build_compute_pipeline(
    device: &Device,
    set_layout: vk::DescriptorSetLayout,
    push_size: u32,
    shader: vk::ShaderModule,
) -> Result<(vk::PipelineLayout, vk::Pipeline)> {
    let push_ranges = [vk::PushConstantRange::default()
        .stage_flags(vk::ShaderStageFlags::COMPUTE)
        .offset(0)
        .size(push_size)];
    let set_layouts = [set_layout];
    let layout = device
        .create_pipeline_layout(
            &vk::PipelineLayoutCreateInfo::default()
                .set_layouts(&set_layouts)
                .push_constant_ranges(&push_ranges),
            None,
        )
        .context("create compute pipeline layout")?;
    let stage = vk::PipelineShaderStageCreateInfo::default()
        .stage(vk::ShaderStageFlags::COMPUTE)
        .module(shader)
        .name(c"main");
    let pipeline = device
        .create_compute_pipelines(
            vk::PipelineCache::null(),
            &[vk::ComputePipelineCreateInfo::default().stage(stage).layout(layout)],
            None,
        )
        .map_err(|(_, e)| e)
        .context("create compute pipeline")?[0];
    Ok((layout, pipeline))
}

/// Storage-image descriptor set layout (binding 0 read OR write, determined per-use).
unsafe fn storage_image_layout(device: &Device, stage: vk::ShaderStageFlags) -> Result<vk::DescriptorSetLayout> {
    let bindings = [vk::DescriptorSetLayoutBinding::default()
        .binding(0)
        .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
        .descriptor_count(1)
        .stage_flags(stage)];
    device
        .create_descriptor_set_layout(
            &vk::DescriptorSetLayoutCreateInfo::default().bindings(&bindings),
            None,
        )
        .context("create storage-image set layout")
}

/// Two-binding storage-image layout (binding 0 = src, binding 1 = dst) for the FFT.
unsafe fn fft_set_layout_new(device: &Device) -> Result<vk::DescriptorSetLayout> {
    let bindings = [
        vk::DescriptorSetLayoutBinding::default()
            .binding(0)
            .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
            .descriptor_count(1)
            .stage_flags(vk::ShaderStageFlags::COMPUTE),
        vk::DescriptorSetLayoutBinding::default()
            .binding(1)
            .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
            .descriptor_count(1)
            .stage_flags(vk::ShaderStageFlags::COMPUTE),
    ];
    device
        .create_descriptor_set_layout(
            &vk::DescriptorSetLayoutCreateInfo::default().bindings(&bindings),
            None,
        )
        .context("create fft set layout")
}

fn write_storage_image(
    device: &Device,
    set: vk::DescriptorSet,
    binding: u32,
    view: vk::ImageView,
) {
    let img_info = [vk::DescriptorImageInfo::default()
        .image_view(view)
        .image_layout(vk::ImageLayout::GENERAL)];
    let write = vk::WriteDescriptorSet::default()
        .dst_set(set)
        .dst_binding(binding)
        .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
        .image_info(&img_info);
    unsafe { device.update_descriptor_sets(&[write], &[]) };
}

fn push_bytes<T: Copy>(v: &T) -> &[u8] {
    unsafe {
        std::slice::from_raw_parts(
            (v as *const T).cast::<u8>(),
            std::mem::size_of::<T>(),
        )
    }
}

/// Barrier to transition an image to GENERAL layout for compute write.
fn to_general_barrier(image: vk::Image) -> vk::ImageMemoryBarrier2<'static> {
    vk::ImageMemoryBarrier2::default()
        .src_stage_mask(vk::PipelineStageFlags2::ALL_COMMANDS)
        .dst_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
        .dst_access_mask(vk::AccessFlags2::SHADER_WRITE | vk::AccessFlags2::SHADER_READ)
        .old_layout(vk::ImageLayout::UNDEFINED)
        .new_layout(vk::ImageLayout::GENERAL)
        .image(image)
        .subresource_range(color_range())
}

/// Barrier between compute stages (GENERAL → GENERAL, write→read).
fn compute_rw_barrier(image: vk::Image) -> vk::ImageMemoryBarrier2<'static> {
    vk::ImageMemoryBarrier2::default()
        .src_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
        .src_access_mask(vk::AccessFlags2::SHADER_WRITE)
        .dst_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
        .dst_access_mask(vk::AccessFlags2::SHADER_READ | vk::AccessFlags2::SHADER_WRITE)
        .old_layout(vk::ImageLayout::GENERAL)
        .new_layout(vk::ImageLayout::GENERAL)
        .image(image)
        .subresource_range(color_range())
}

/// Barrier after final FFT stage: make disp_image readable by vertex/fragment stages.
fn disp_to_shader_read(image: vk::Image) -> vk::ImageMemoryBarrier2<'static> {
    vk::ImageMemoryBarrier2::default()
        .src_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
        .src_access_mask(vk::AccessFlags2::SHADER_WRITE)
        .dst_stage_mask(
            vk::PipelineStageFlags2::VERTEX_SHADER | vk::PipelineStageFlags2::FRAGMENT_SHADER,
        )
        .dst_access_mask(vk::AccessFlags2::SHADER_READ)
        .old_layout(vk::ImageLayout::GENERAL)
        .new_layout(vk::ImageLayout::GENERAL)
        .image(image)
        .subresource_range(color_range())
}

impl OceanCompute {
    /// # Safety
    /// Requires a valid Vulkan context; cleanup() must be called before device destruction.
    pub unsafe fn new(ctx: &VulkanContext) -> Result<Self> {
        let device = &ctx.device;
        let n = RESOLUTION;

        // ── Images ───────────────────────────────────────────────────────────
        let (disp_image,  disp_alloc,  disp_view)  = alloc_storage_image(ctx, "ocean_disp",  n)?;
        let (h0_image,    h0_alloc,    h0_view)    = alloc_storage_image(ctx, "ocean_h0",    n)?;
        let (fft_a_image, fft_a_alloc, fft_a_view) = alloc_storage_image(ctx, "ocean_fft_a", n)?;
        let (fft_b_image, fft_b_alloc, fft_b_view) = alloc_storage_image(ctx, "ocean_fft_b", n)?;

        // ── Sampler (disp_image → water.vert) ────────────────────────────────
        let sampler = device
            .create_sampler(
                &vk::SamplerCreateInfo::default()
                    .mag_filter(vk::Filter::LINEAR)
                    .min_filter(vk::Filter::LINEAR)
                    .address_mode_u(vk::SamplerAddressMode::CLAMP_TO_EDGE)
                    .address_mode_v(vk::SamplerAddressMode::CLAMP_TO_EDGE)
                    .address_mode_w(vk::SamplerAddressMode::CLAMP_TO_EDGE),
                None,
            )
            .context("create ocean sampler")?;

        // ── Descriptor pool ──────────────────────────────────────────────────
        // Sets: h0(1) + evolve(1) + fft×4(4) + graphics(1) = 7; storage images: 1+2+8+1=12; samplers: 1
        let pool_sizes = [
            vk::DescriptorPoolSize::default().ty(vk::DescriptorType::STORAGE_IMAGE).descriptor_count(12),
            vk::DescriptorPoolSize::default().ty(vk::DescriptorType::COMBINED_IMAGE_SAMPLER).descriptor_count(1),
        ];
        let desc_pool = device
            .create_descriptor_pool(
                &vk::DescriptorPoolCreateInfo::default().pool_sizes(&pool_sizes).max_sets(7),
                None,
            )
            .context("create ocean descriptor pool")?;

        // ── h0 pipeline ──────────────────────────────────────────────────────
        let h0_set_layout = storage_image_layout(device, vk::ShaderStageFlags::COMPUTE)?;
        let h0_set = device.allocate_descriptor_sets(
            &vk::DescriptorSetAllocateInfo::default().descriptor_pool(desc_pool).set_layouts(&[h0_set_layout])
        ).context("alloc h0 set")?[0];
        write_storage_image(device, h0_set, 0, h0_view);
        let h0_shader = create_shader(device, include_bytes!(concat!(env!("OUT_DIR"), "/ocean_h0.comp.spv")))?;
        let (h0_pipeline_layout, h0_pipeline) = build_compute_pipeline(
            device, h0_set_layout, u32::try_from(std::mem::size_of::<H0Push>()).unwrap(), h0_shader)?;

        // ── evolve pipeline ──────────────────────────────────────────────────
        // Two storage images: binding 0 = h0 (read), binding 1 = fft_a (write).
        let evolve_bindings = [
            vk::DescriptorSetLayoutBinding::default().binding(0)
                .descriptor_type(vk::DescriptorType::STORAGE_IMAGE).descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::COMPUTE),
            vk::DescriptorSetLayoutBinding::default().binding(1)
                .descriptor_type(vk::DescriptorType::STORAGE_IMAGE).descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::COMPUTE),
        ];
        let evolve_set_layout = device.create_descriptor_set_layout(
            &vk::DescriptorSetLayoutCreateInfo::default().bindings(&evolve_bindings), None
        ).context("create evolve set layout")?;
        let evolve_set = device.allocate_descriptor_sets(
            &vk::DescriptorSetAllocateInfo::default().descriptor_pool(desc_pool).set_layouts(&[evolve_set_layout])
        ).context("alloc evolve set")?[0];
        write_storage_image(device, evolve_set, 0, h0_view);
        write_storage_image(device, evolve_set, 1, fft_a_view);
        let evolve_shader = create_shader(device, include_bytes!(concat!(env!("OUT_DIR"), "/ocean_evolve.comp.spv")))?;
        let (evolve_pipeline_layout, evolve_pipeline) = build_compute_pipeline(
            device, evolve_set_layout, u32::try_from(std::mem::size_of::<EvolvePush>()).unwrap(), evolve_shader)?;

        // ── FFT pipeline (4 src→dst combos) ─────────────────────────────────
        let fft_set_layout = fft_set_layout_new(device)?;
        let fft_sets = device.allocate_descriptor_sets(
            &vk::DescriptorSetAllocateInfo::default().descriptor_pool(desc_pool)
                .set_layouts(&[fft_set_layout, fft_set_layout, fft_set_layout, fft_set_layout])
        ).context("alloc fft sets")?;
        let [fft_set_ab, fft_set_ba, fft_set_aD, fft_set_bD] = [fft_sets[0], fft_sets[1], fft_sets[2], fft_sets[3]];
        // ab: src=fft_a, dst=fft_b
        write_storage_image(device, fft_set_ab, 0, fft_a_view);
        write_storage_image(device, fft_set_ab, 1, fft_b_view);
        // ba: src=fft_b, dst=fft_a
        write_storage_image(device, fft_set_ba, 0, fft_b_view);
        write_storage_image(device, fft_set_ba, 1, fft_a_view);
        // aD: src=fft_a, dst=disp
        write_storage_image(device, fft_set_aD, 0, fft_a_view);
        write_storage_image(device, fft_set_aD, 1, disp_view);
        // bD: src=fft_b, dst=disp
        write_storage_image(device, fft_set_bD, 0, fft_b_view);
        write_storage_image(device, fft_set_bD, 1, disp_view);

        let fft_shader = create_shader(device, include_bytes!(concat!(env!("OUT_DIR"), "/ocean_fft.comp.spv")))?;
        let (fft_pipeline_layout, fft_pipeline) = build_compute_pipeline(
            device, fft_set_layout, u32::try_from(std::mem::size_of::<FftPush>()).unwrap(), fft_shader)?;

        // ── Graphics sampler set (water.vert reads disp_image) ───────────────
        let gfx_bindings = [vk::DescriptorSetLayoutBinding::default()
            .binding(0)
            .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
            .descriptor_count(1)
            .stage_flags(vk::ShaderStageFlags::VERTEX)];
        let graphics_set_layout = device.create_descriptor_set_layout(
            &vk::DescriptorSetLayoutCreateInfo::default().bindings(&gfx_bindings), None
        ).context("create graphics set layout")?;
        let graphics_set = device.allocate_descriptor_sets(
            &vk::DescriptorSetAllocateInfo::default().descriptor_pool(desc_pool).set_layouts(&[graphics_set_layout])
        ).context("alloc graphics set")?[0];
        let gfx_img_info = [vk::DescriptorImageInfo::default()
            .sampler(sampler).image_view(disp_view).image_layout(vk::ImageLayout::GENERAL)];
        device.update_descriptor_sets(&[vk::WriteDescriptorSet::default()
            .dst_set(graphics_set).dst_binding(0)
            .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
            .image_info(&gfx_img_info)], &[]);

        info!("🌊 OceanCompute: Tessendorf IFFT pipeline — {}×{} displacement field ({} FFT stages × 2 axes)",
            n, n, FFT_STAGES);

        Ok(Self {
            disp_image, disp_alloc: Some(disp_alloc), disp_view, sampler,
            h0_image, h0_alloc: Some(h0_alloc), h0_view,
            fft_a_image, fft_a_alloc: Some(fft_a_alloc), fft_a_view,
            fft_b_image, fft_b_alloc: Some(fft_b_alloc), fft_b_view,
            desc_pool,
            h0_set_layout, h0_set, h0_pipeline_layout, h0_pipeline, h0_shader,
            evolve_set_layout, evolve_set, evolve_pipeline_layout, evolve_pipeline, evolve_shader,
            fft_set_layout, fft_set_ab, fft_set_ba, fft_set_aD, fft_set_bD,
            fft_pipeline_layout, fft_pipeline, fft_shader,
            graphics_set_layout, graphics_set,
            resolution: n,
            h0_dispatched: false,
        })
    }

    /// Dispatch the full Tessendorf frame: h0 (once) → evolve → 16 FFT passes → disp_image.
    ///
    /// # Safety
    /// `cmd` must be recording, outside any dynamic-rendering scope.
    pub unsafe fn dispatch(&mut self, device: &Device, cmd: vk::CommandBuffer, time: f32) {
        let n = self.resolution;
        let groups = n.div_ceil(16);

        // ── Transition all images to GENERAL on first frame ──────────────────
        if !self.h0_dispatched {
            let barriers = [
                to_general_barrier(self.h0_image),
                to_general_barrier(self.fft_a_image),
                to_general_barrier(self.fft_b_image),
                to_general_barrier(self.disp_image),
            ];
            device.cmd_pipeline_barrier2(cmd, &vk::DependencyInfo::default().image_memory_barriers(&barriers));

            // h0 dispatch — only once.
            device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::COMPUTE, self.h0_pipeline);
            device.cmd_bind_descriptor_sets(cmd, vk::PipelineBindPoint::COMPUTE, self.h0_pipeline_layout, 0, &[self.h0_set], &[]);
            let push = H0Push { resolution: n, wind_speed: WIND_SPEED, wind_dir: WIND_DIR, phillips_a: PHILLIPS_A };
            device.cmd_push_constants(cmd, self.h0_pipeline_layout, vk::ShaderStageFlags::COMPUTE, 0, push_bytes(&push));
            device.cmd_dispatch(cmd, groups, groups, 1);

            // Barrier: h0 write → h0 read in evolve.
            let b = [compute_rw_barrier(self.h0_image)];
            device.cmd_pipeline_barrier2(cmd, &vk::DependencyInfo::default().image_memory_barriers(&b));

            self.h0_dispatched = true;
        } else {
            // Every frame: transition disp back to GENERAL for writing.
            let b = [
                vk::ImageMemoryBarrier2::default()
                    .src_stage_mask(vk::PipelineStageFlags2::VERTEX_SHADER | vk::PipelineStageFlags2::FRAGMENT_SHADER)
                    .src_access_mask(vk::AccessFlags2::SHADER_READ)
                    .dst_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
                    .dst_access_mask(vk::AccessFlags2::SHADER_WRITE | vk::AccessFlags2::SHADER_READ)
                    .old_layout(vk::ImageLayout::GENERAL)
                    .new_layout(vk::ImageLayout::GENERAL)
                    .image(self.disp_image)
                    .subresource_range(color_range()),
            ];
            device.cmd_pipeline_barrier2(cmd, &vk::DependencyInfo::default().image_memory_barriers(&b));
        }

        // ── Evolve h(k,t) → fft_a ───────────────────────────────────────────
        device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::COMPUTE, self.evolve_pipeline);
        device.cmd_bind_descriptor_sets(cmd, vk::PipelineBindPoint::COMPUTE, self.evolve_pipeline_layout, 0, &[self.evolve_set], &[]);
        let ep = EvolvePush { time, resolution: n, patch_size: PATCH_SIZE, _pad: 0.0 };
        device.cmd_push_constants(cmd, self.evolve_pipeline_layout, vk::ShaderStageFlags::COMPUTE, 0, push_bytes(&ep));
        device.cmd_dispatch(cmd, groups, groups, 1);

        // ── Butterfly FFT passes (8H + 8V = 16 total) ───────────────────────
        // After evolve, fft_a has the frequency-domain data.
        // Stages alternate: fft_a→fft_b (ab) or fft_b→fft_a (ba).
        // The LAST stage (stage 15 = V stage 7) writes to disp_image.
        // Last stage: if 16 stages and first src=fft_a, src/dst pattern:
        //   stage 0: ab (src a, dst b)
        //   stage 1: ba (src b, dst a)
        //   ...
        //   stage 15 (0-indexed): src = (15%2==0)? a : b.  15%2=1 → src=b, dst=? normally a.
        //   We substitute dst=disp on the last stage.
        device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::COMPUTE, self.fft_pipeline);

        let total_stages: u32 = FFT_STAGES * 2; // 8H + 8V
        for i in 0..total_stages {
            let axis  = i / FFT_STAGES;  // 0 = horizontal, 1 = vertical
            let stage = i % FFT_STAGES;
            let is_last = i == total_stages - 1;

            // Barrier: previous write visible to current read.
            {
                let prev_writer = if i % 2 == 0 { self.fft_a_image } else { self.fft_b_image };
                let b = [compute_rw_barrier(prev_writer)];
                device.cmd_pipeline_barrier2(cmd, &vk::DependencyInfo::default().image_memory_barriers(&b));
            }

            let desc_set = if is_last {
                // Final stage → write directly into disp_image.
                if i % 2 == 0 { self.fft_set_aD } else { self.fft_set_bD }
            } else if i % 2 == 0 {
                self.fft_set_ab  // src=a, dst=b
            } else {
                self.fft_set_ba  // src=b, dst=a
            };

            device.cmd_bind_descriptor_sets(cmd, vk::PipelineBindPoint::COMPUTE, self.fft_pipeline_layout, 0, &[desc_set], &[]);
            let fp = FftPush { stage, axis, resolution: n, _pad: 0 };
            device.cmd_push_constants(cmd, self.fft_pipeline_layout, vk::ShaderStageFlags::COMPUTE, 0, push_bytes(&fp));
            device.cmd_dispatch(cmd, groups, groups, 1);
        }

        // ── Final barrier: disp readable by vertex/fragment ─────────────────
        let b = [disp_to_shader_read(self.disp_image)];
        device.cmd_pipeline_barrier2(cmd, &vk::DependencyInfo::default().image_memory_barriers(&b));
    }

    /// # Safety
    /// Device must be idle; call once before context destruction.
    pub unsafe fn cleanup(&mut self, device: &Device, allocator: &mut gpu_allocator::vulkan::Allocator) {
        device.destroy_pipeline(self.fft_pipeline, None);
        device.destroy_pipeline_layout(self.fft_pipeline_layout, None);
        device.destroy_shader_module(self.fft_shader, None);
        device.destroy_descriptor_set_layout(self.fft_set_layout, None);

        device.destroy_pipeline(self.evolve_pipeline, None);
        device.destroy_pipeline_layout(self.evolve_pipeline_layout, None);
        device.destroy_shader_module(self.evolve_shader, None);
        device.destroy_descriptor_set_layout(self.evolve_set_layout, None);

        device.destroy_pipeline(self.h0_pipeline, None);
        device.destroy_pipeline_layout(self.h0_pipeline_layout, None);
        device.destroy_shader_module(self.h0_shader, None);
        device.destroy_descriptor_set_layout(self.h0_set_layout, None);

        device.destroy_descriptor_set_layout(self.graphics_set_layout, None);
        device.destroy_descriptor_pool(self.desc_pool, None);
        device.destroy_sampler(self.sampler, None);

        device.destroy_image_view(self.fft_b_view, None);
        device.destroy_image(self.fft_b_image, None);
        if let Some(a) = self.fft_b_alloc.take() { let _ = allocator.free(a); }

        device.destroy_image_view(self.fft_a_view, None);
        device.destroy_image(self.fft_a_image, None);
        if let Some(a) = self.fft_a_alloc.take() { let _ = allocator.free(a); }

        device.destroy_image_view(self.h0_view, None);
        device.destroy_image(self.h0_image, None);
        if let Some(a) = self.h0_alloc.take() { let _ = allocator.free(a); }

        device.destroy_image_view(self.disp_view, None);
        device.destroy_image(self.disp_image, None);
        if let Some(a) = self.disp_alloc.take() { let _ = allocator.free(a); }
    }
}
