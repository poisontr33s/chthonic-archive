//! Rung 4.2 — ocean displacement compute subsystem.
//!
//! 4.2a: compute pipeline seam closed — water.vert samples displacement image.
//! 4.2b: Phillips spectrum analytical body in ocean_displace.comp.
//! 4.2c: Full Tessendorf IFFT pipeline (single cascade).
//! 4.2d: Dual cascade — ripple (C0) + swell (C1) summed in water.vert.
//!         C0: patch=5m,  wind=3.8 m/s — high-frequency chop.
//!         C1: patch=60m, wind=8.0 m/s — low-frequency swell.
//!
//! Pipelines (h0 / evolve / fft) are compiled once and shared across both cascades;
//! cascade-specific parameters are passed via push constants each dispatch.

//! @SID:    RENDER_OCEAN_COMPUTE_V1
//! @Shabti: Ocean-Compute

use anyhow::{Context, Result};
use ash::{Device, vk};
use gpu_allocator::vulkan::{Allocation, AllocationCreateDesc, AllocationScheme};
use gpu_allocator::MemoryLocation;
use log::info;

use super::vulkan::VulkanContext;

const RESOLUTION: u32 = 256;
const FFT_STAGES: u32 = 8; // log2(256)

/// Per-cascade tuning. Pipelines are shared; these differ per cascade.
struct CascadeSpec {
    patch_size:  f32,
    wind_speed:  f32,
    wind_dir:    f32,
    phillips_a:  f32,
}

const CASCADE: [CascadeSpec; 2] = [
    CascadeSpec { patch_size: 5.0,  wind_speed: 3.8, wind_dir: 90.0, phillips_a: 0.0004 },
    CascadeSpec { patch_size: 60.0, wind_speed: 8.0, wind_dir: 90.0, phillips_a: 0.0002 },
];

// ─────────────────────────────────────────────────────────────────────────────
// Push-constant layouts
// ─────────────────────────────────────────────────────────────────────────────

#[repr(C)] #[derive(Clone, Copy)]
struct H0Push { resolution: u32, wind_speed: f32, wind_dir: f32, phillips_a: f32 }

#[repr(C)] #[derive(Clone, Copy)]
struct EvolvePush { time: f32, resolution: u32, patch_size: f32, _pad: f32 }

#[repr(C)] #[derive(Clone, Copy)]
struct FftPush { stage: u32, axis: u32, resolution: u32, _pad: u32 }

// ─────────────────────────────────────────────────────────────────────────────
// OceanCascade — per-cascade images and descriptor sets.
// ─────────────────────────────────────────────────────────────────────────────

struct OceanCascade {
    disp_image: vk::Image,
    disp_alloc: Option<Allocation>,
    disp_view:  vk::ImageView,

    h0_image: vk::Image,
    h0_alloc: Option<Allocation>,
    h0_view:  vk::ImageView,

    fft_a_image: vk::Image,
    fft_a_alloc: Option<Allocation>,
    fft_a_view:  vk::ImageView,
    fft_b_image: vk::Image,
    fft_b_alloc: Option<Allocation>,
    fft_b_view:  vk::ImageView,

    // Per-cascade compute descriptor sets (bound from the shared pipelines).
    h0_set:      vk::DescriptorSet,
    evolve_set:  vk::DescriptorSet,
    fft_set_ab:  vk::DescriptorSet, // src=a dst=b
    fft_set_ba:  vk::DescriptorSet, // src=b dst=a
    fft_set_aD:  vk::DescriptorSet, // src=a dst=disp (final stage)
    fft_set_bD:  vk::DescriptorSet, // src=b dst=disp (final stage alt)

    h0_dispatched: bool,
}

impl OceanCascade {
    unsafe fn dispatch(
        &mut self,
        device: &Device,
        cmd: vk::CommandBuffer,
        time: f32,
        spec: &CascadeSpec,
        n: u32,
        pipelines: &OceanPipelines,
    ) {
        let groups = n.div_ceil(16);

        if !self.h0_dispatched {
            let barriers = [
                to_general_barrier(self.h0_image),
                to_general_barrier(self.fft_a_image),
                to_general_barrier(self.fft_b_image),
                to_general_barrier(self.disp_image),
            ];
            device.cmd_pipeline_barrier2(cmd, &vk::DependencyInfo::default().image_memory_barriers(&barriers));

            device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::COMPUTE, pipelines.h0_pipeline);
            device.cmd_bind_descriptor_sets(cmd, vk::PipelineBindPoint::COMPUTE, pipelines.h0_pipeline_layout, 0, &[self.h0_set], &[]);
            let push = H0Push { resolution: n, wind_speed: spec.wind_speed, wind_dir: spec.wind_dir, phillips_a: spec.phillips_a };
            device.cmd_push_constants(cmd, pipelines.h0_pipeline_layout, vk::ShaderStageFlags::COMPUTE, 0, push_bytes(&push));
            device.cmd_dispatch(cmd, groups, groups, 1);

            let b = [compute_rw_barrier(self.h0_image)];
            device.cmd_pipeline_barrier2(cmd, &vk::DependencyInfo::default().image_memory_barriers(&b));
            self.h0_dispatched = true;
        } else {
            let b = [vk::ImageMemoryBarrier2::default()
                .src_stage_mask(vk::PipelineStageFlags2::VERTEX_SHADER | vk::PipelineStageFlags2::FRAGMENT_SHADER)
                .src_access_mask(vk::AccessFlags2::SHADER_READ)
                .dst_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
                .dst_access_mask(vk::AccessFlags2::SHADER_WRITE | vk::AccessFlags2::SHADER_READ)
                .old_layout(vk::ImageLayout::GENERAL)
                .new_layout(vk::ImageLayout::GENERAL)
                .image(self.disp_image)
                .subresource_range(color_range())];
            device.cmd_pipeline_barrier2(cmd, &vk::DependencyInfo::default().image_memory_barriers(&b));
        }

        // Evolve h(k,t) → fft_a.
        device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::COMPUTE, pipelines.evolve_pipeline);
        device.cmd_bind_descriptor_sets(cmd, vk::PipelineBindPoint::COMPUTE, pipelines.evolve_pipeline_layout, 0, &[self.evolve_set], &[]);
        let ep = EvolvePush { time, resolution: n, patch_size: spec.patch_size, _pad: 0.0 };
        device.cmd_push_constants(cmd, pipelines.evolve_pipeline_layout, vk::ShaderStageFlags::COMPUTE, 0, push_bytes(&ep));
        device.cmd_dispatch(cmd, groups, groups, 1);

        // 16 butterfly passes (8H + 8V).
        device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::COMPUTE, pipelines.fft_pipeline);
        let total: u32 = FFT_STAGES * 2;
        for i in 0..total {
            let axis  = i / FFT_STAGES;
            let stage = i % FFT_STAGES;
            let is_last = i == total - 1;

            let prev_writer = if i % 2 == 0 { self.fft_a_image } else { self.fft_b_image };
            let b = [compute_rw_barrier(prev_writer)];
            device.cmd_pipeline_barrier2(cmd, &vk::DependencyInfo::default().image_memory_barriers(&b));

            let desc_set = if is_last {
                if i % 2 == 0 { self.fft_set_aD } else { self.fft_set_bD }
            } else if i % 2 == 0 {
                self.fft_set_ab
            } else {
                self.fft_set_ba
            };

            device.cmd_bind_descriptor_sets(cmd, vk::PipelineBindPoint::COMPUTE, pipelines.fft_pipeline_layout, 0, &[desc_set], &[]);
            let fp = FftPush { stage, axis, resolution: n, _pad: 0 };
            device.cmd_push_constants(cmd, pipelines.fft_pipeline_layout, vk::ShaderStageFlags::COMPUTE, 0, push_bytes(&fp));
            device.cmd_dispatch(cmd, groups, groups, 1);
        }

        let b = [disp_to_shader_read(self.disp_image)];
        device.cmd_pipeline_barrier2(cmd, &vk::DependencyInfo::default().image_memory_barriers(&b));
    }

    unsafe fn cleanup(&mut self, device: &Device, allocator: &mut gpu_allocator::vulkan::Allocator) {
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

// ─────────────────────────────────────────────────────────────────────────────
// OceanPipelines — compiled shaders and pipeline objects, shared across cascades.
// ─────────────────────────────────────────────────────────────────────────────

struct OceanPipelines {
    h0_set_layout:          vk::DescriptorSetLayout,
    h0_pipeline_layout:     vk::PipelineLayout,
    h0_pipeline:            vk::Pipeline,
    h0_shader:              vk::ShaderModule,

    evolve_set_layout:      vk::DescriptorSetLayout,
    evolve_pipeline_layout: vk::PipelineLayout,
    evolve_pipeline:        vk::Pipeline,
    evolve_shader:          vk::ShaderModule,

    fft_set_layout:         vk::DescriptorSetLayout,
    fft_pipeline_layout:    vk::PipelineLayout,
    fft_pipeline:           vk::Pipeline,
    fft_shader:             vk::ShaderModule,
}

impl OceanPipelines {
    unsafe fn cleanup(&self, device: &Device) {
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
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// OceanCompute — public entry point.
// ─────────────────────────────────────────────────────────────────────────────

pub struct OceanCompute {
    cascades:   [OceanCascade; 2],
    pipelines:  OceanPipelines,
    pub sampler: vk::Sampler,
    pub desc_pool: vk::DescriptorPool,
    /// Graphics set: set 0 bindings 0+1 = combined-image-samplers for C0+C1 disp.
    pub graphics_set_layout: vk::DescriptorSetLayout,
    pub graphics_set:        vk::DescriptorSet,
    pub resolution: u32,
}

impl OceanCompute {
    pub unsafe fn new(ctx: &VulkanContext) -> Result<Self> {
        let device = &ctx.device;
        let n = RESOLUTION;

        // ── Shared sampler ───────────────────────────────────────────────────
        let sampler = device.create_sampler(
            &vk::SamplerCreateInfo::default()
                .mag_filter(vk::Filter::LINEAR)
                .min_filter(vk::Filter::LINEAR)
                .address_mode_u(vk::SamplerAddressMode::REPEAT)
                .address_mode_v(vk::SamplerAddressMode::REPEAT)
                .address_mode_w(vk::SamplerAddressMode::REPEAT),
            None,
        ).context("create ocean sampler")?;

        // ── Descriptor pool ──────────────────────────────────────────────────
        // Per cascade: h0(1) + evolve(1) + fft×4(4) = 6 sets, storage images = 1+2+8 = 11.
        // 2 cascades × 6 = 12 sets, 22 storage images.
        // + 1 graphics set, 2 combined-image-samplers.
        let pool_sizes = [
            vk::DescriptorPoolSize::default().ty(vk::DescriptorType::STORAGE_IMAGE).descriptor_count(22),
            vk::DescriptorPoolSize::default().ty(vk::DescriptorType::COMBINED_IMAGE_SAMPLER).descriptor_count(2),
        ];
        let desc_pool = device.create_descriptor_pool(
            &vk::DescriptorPoolCreateInfo::default().pool_sizes(&pool_sizes).max_sets(13),
            None,
        ).context("create ocean descriptor pool")?;

        // ── Shared pipelines ─────────────────────────────────────────────────
        let h0_set_layout = storage_image_layout(device, vk::ShaderStageFlags::COMPUTE)?;
        let h0_shader = create_shader(device, include_bytes!(concat!(env!("OUT_DIR"), "/ocean_h0.comp.spv")))?;
        let (h0_pipeline_layout, h0_pipeline) = build_compute_pipeline(
            device, h0_set_layout, std::mem::size_of::<H0Push>() as u32, h0_shader)?;

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
        let evolve_shader = create_shader(device, include_bytes!(concat!(env!("OUT_DIR"), "/ocean_evolve.comp.spv")))?;
        let (evolve_pipeline_layout, evolve_pipeline) = build_compute_pipeline(
            device, evolve_set_layout, std::mem::size_of::<EvolvePush>() as u32, evolve_shader)?;

        let fft_set_layout = fft_set_layout_new(device)?;
        let fft_shader = create_shader(device, include_bytes!(concat!(env!("OUT_DIR"), "/ocean_fft.comp.spv")))?;
        let (fft_pipeline_layout, fft_pipeline) = build_compute_pipeline(
            device, fft_set_layout, std::mem::size_of::<FftPush>() as u32, fft_shader)?;

        let pipelines = OceanPipelines {
            h0_set_layout, h0_pipeline_layout, h0_pipeline, h0_shader,
            evolve_set_layout, evolve_pipeline_layout, evolve_pipeline, evolve_shader,
            fft_set_layout, fft_pipeline_layout, fft_pipeline, fft_shader,
        };

        // ── Build each cascade ───────────────────────────────────────────────
        let cascades = {
            let mut arr: [std::mem::MaybeUninit<OceanCascade>; 2] =
                [std::mem::MaybeUninit::uninit(), std::mem::MaybeUninit::uninit()];
            for (i, slot) in arr.iter_mut().enumerate() {
                let label = |s: &str| format!("ocean_{s}_c{i}");
                let (disp_image,  disp_alloc,  disp_view)  = alloc_storage_image(ctx, &label("disp"),  n)?;
                let (h0_image,    h0_alloc,    h0_view)    = alloc_storage_image(ctx, &label("h0"),    n)?;
                let (fft_a_image, fft_a_alloc, fft_a_view) = alloc_storage_image(ctx, &label("fft_a"), n)?;
                let (fft_b_image, fft_b_alloc, fft_b_view) = alloc_storage_image(ctx, &label("fft_b"), n)?;

                // h0 set (binding 0 = h0 write).
                let h0_set = device.allocate_descriptor_sets(
                    &vk::DescriptorSetAllocateInfo::default().descriptor_pool(desc_pool)
                        .set_layouts(&[pipelines.h0_set_layout])
                ).context("alloc h0 set")?[0];
                write_storage_image(device, h0_set, 0, h0_view);

                // evolve set (0=h0 read, 1=fft_a write).
                let evolve_set = device.allocate_descriptor_sets(
                    &vk::DescriptorSetAllocateInfo::default().descriptor_pool(desc_pool)
                        .set_layouts(&[pipelines.evolve_set_layout])
                ).context("alloc evolve set")?[0];
                write_storage_image(device, evolve_set, 0, h0_view);
                write_storage_image(device, evolve_set, 1, fft_a_view);

                // 4 FFT sets.
                let fft_sets = device.allocate_descriptor_sets(
                    &vk::DescriptorSetAllocateInfo::default().descriptor_pool(desc_pool)
                        .set_layouts(&[pipelines.fft_set_layout; 4])
                ).context("alloc fft sets")?;
                let [fft_set_ab, fft_set_ba, fft_set_aD, fft_set_bD] =
                    [fft_sets[0], fft_sets[1], fft_sets[2], fft_sets[3]];
                write_storage_image(device, fft_set_ab, 0, fft_a_view);
                write_storage_image(device, fft_set_ab, 1, fft_b_view);
                write_storage_image(device, fft_set_ba, 0, fft_b_view);
                write_storage_image(device, fft_set_ba, 1, fft_a_view);
                write_storage_image(device, fft_set_aD, 0, fft_a_view);
                write_storage_image(device, fft_set_aD, 1, disp_view);
                write_storage_image(device, fft_set_bD, 0, fft_b_view);
                write_storage_image(device, fft_set_bD, 1, disp_view);

                slot.write(OceanCascade {
                    disp_image, disp_alloc: Some(disp_alloc), disp_view,
                    h0_image,   h0_alloc:   Some(h0_alloc),   h0_view,
                    fft_a_image, fft_a_alloc: Some(fft_a_alloc), fft_a_view,
                    fft_b_image, fft_b_alloc: Some(fft_b_alloc), fft_b_view,
                    h0_set, evolve_set,
                    fft_set_ab, fft_set_ba, fft_set_aD, fft_set_bD,
                    h0_dispatched: false,
                });
            }
            // SAFETY: both elements initialized above.
            arr.map(|s| s.assume_init())
        };

        // ── Graphics set: 2 combined-image-samplers (C0 + C1 disp) ─────────
        let gfx_bindings = [
            vk::DescriptorSetLayoutBinding::default()
                .binding(0).descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .descriptor_count(1).stage_flags(vk::ShaderStageFlags::VERTEX),
            vk::DescriptorSetLayoutBinding::default()
                .binding(1).descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .descriptor_count(1).stage_flags(vk::ShaderStageFlags::VERTEX),
        ];
        let graphics_set_layout = device.create_descriptor_set_layout(
            &vk::DescriptorSetLayoutCreateInfo::default().bindings(&gfx_bindings), None
        ).context("create graphics set layout")?;
        let graphics_set = device.allocate_descriptor_sets(
            &vk::DescriptorSetAllocateInfo::default().descriptor_pool(desc_pool)
                .set_layouts(&[graphics_set_layout])
        ).context("alloc graphics set")?[0];
        let img_infos = [
            vk::DescriptorImageInfo::default()
                .sampler(sampler).image_view(cascades[0].disp_view).image_layout(vk::ImageLayout::GENERAL),
            vk::DescriptorImageInfo::default()
                .sampler(sampler).image_view(cascades[1].disp_view).image_layout(vk::ImageLayout::GENERAL),
        ];
        device.update_descriptor_sets(&[
            vk::WriteDescriptorSet::default()
                .dst_set(graphics_set).dst_binding(0)
                .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .image_info(&img_infos[0..1]),
            vk::WriteDescriptorSet::default()
                .dst_set(graphics_set).dst_binding(1)
                .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .image_info(&img_infos[1..2]),
        ], &[]);

        info!("🌊 OceanCompute: 2-cascade Tessendorf — C0 patch={}m  C1 patch={}m  {}×{} each",
            CASCADE[0].patch_size, CASCADE[1].patch_size, n, n);

        Ok(Self { cascades, pipelines, sampler, desc_pool, graphics_set_layout, graphics_set, resolution: n })
    }

    pub unsafe fn dispatch(&mut self, device: &Device, cmd: vk::CommandBuffer, time: f32) {
        for i in 0..2 {
            self.cascades[i].dispatch(device, cmd, time, &CASCADE[i], self.resolution, &self.pipelines);
        }
    }

    pub unsafe fn cleanup(&mut self, device: &Device, allocator: &mut gpu_allocator::vulkan::Allocator) {
        self.pipelines.cleanup(device);
        device.destroy_descriptor_set_layout(self.graphics_set_layout, None);
        device.destroy_descriptor_pool(self.desc_pool, None);
        device.destroy_sampler(self.sampler, None);
        for c in &mut self.cascades {
            c.cleanup(device, allocator);
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

fn color_range() -> vk::ImageSubresourceRange {
    vk::ImageSubresourceRange {
        aspect_mask:      vk::ImageAspectFlags::COLOR,
        base_mip_level:   0,
        level_count:      1,
        base_array_layer: 0,
        layer_count:      1,
    }
}

unsafe fn alloc_storage_image(
    ctx: &VulkanContext,
    label: &str,
    resolution: u32,
) -> Result<(vk::Image, Allocation, vk::ImageView)> {
    let device = &ctx.device;
    let format = vk::Format::R16G16B16A16_SFLOAT;
    let image = device.create_image(
        &vk::ImageCreateInfo::default()
            .image_type(vk::ImageType::TYPE_2D)
            .format(format)
            .extent(vk::Extent3D { width: resolution, height: resolution, depth: 1 })
            .mip_levels(1).array_layers(1)
            .samples(vk::SampleCountFlags::TYPE_1)
            .tiling(vk::ImageTiling::OPTIMAL)
            .usage(vk::ImageUsageFlags::STORAGE | vk::ImageUsageFlags::SAMPLED)
            .sharing_mode(vk::SharingMode::EXCLUSIVE)
            .initial_layout(vk::ImageLayout::UNDEFINED),
        None,
    ).context("create ocean image")?;

    let req = device.get_image_memory_requirements(image);
    let alloc = ctx.allocator.lock().unwrap().allocate(&AllocationCreateDesc {
        name: label, requirements: req,
        location: MemoryLocation::GpuOnly, linear: false,
        allocation_scheme: AllocationScheme::GpuAllocatorManaged,
    }).context("gpu-allocator: alloc ocean image")?;
    device.bind_image_memory(image, alloc.memory(), alloc.offset())?;

    let view = device.create_image_view(
        &vk::ImageViewCreateInfo::default()
            .image(image).view_type(vk::ImageViewType::TYPE_2D)
            .format(format).subresource_range(color_range()),
        None,
    ).context("create ocean image view")?;

    Ok((image, alloc, view))
}

unsafe fn create_shader(device: &Device, spv: &[u8]) -> Result<vk::ShaderModule> {
    assert!(spv.len().is_multiple_of(4));
    let words: Vec<u32> = spv.chunks_exact(4)
        .map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]]))
        .collect();
    device.create_shader_module(&vk::ShaderModuleCreateInfo::default().code(&words), None)
        .context("create shader module")
}

unsafe fn build_compute_pipeline(
    device: &Device,
    set_layout: vk::DescriptorSetLayout,
    push_size: u32,
    shader: vk::ShaderModule,
) -> Result<(vk::PipelineLayout, vk::Pipeline)> {
    let push_ranges = [vk::PushConstantRange::default()
        .stage_flags(vk::ShaderStageFlags::COMPUTE)
        .offset(0).size(push_size)];
    let set_layouts = [set_layout];
    let layout = device.create_pipeline_layout(
        &vk::PipelineLayoutCreateInfo::default()
            .set_layouts(&set_layouts)
            .push_constant_ranges(&push_ranges),
        None,
    ).context("create compute pipeline layout")?;
    let stage = vk::PipelineShaderStageCreateInfo::default()
        .stage(vk::ShaderStageFlags::COMPUTE).module(shader).name(c"main");
    let pipeline = device.create_compute_pipelines(
        vk::PipelineCache::null(),
        &[vk::ComputePipelineCreateInfo::default().stage(stage).layout(layout)],
        None,
    ).map_err(|(_, e)| e).context("create compute pipeline")?[0];
    Ok((layout, pipeline))
}

unsafe fn storage_image_layout(device: &Device, stage: vk::ShaderStageFlags) -> Result<vk::DescriptorSetLayout> {
    let bindings = [vk::DescriptorSetLayoutBinding::default()
        .binding(0).descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
        .descriptor_count(1).stage_flags(stage)];
    device.create_descriptor_set_layout(
        &vk::DescriptorSetLayoutCreateInfo::default().bindings(&bindings), None,
    ).context("create storage-image set layout")
}

unsafe fn fft_set_layout_new(device: &Device) -> Result<vk::DescriptorSetLayout> {
    let bindings = [
        vk::DescriptorSetLayoutBinding::default().binding(0)
            .descriptor_type(vk::DescriptorType::STORAGE_IMAGE).descriptor_count(1)
            .stage_flags(vk::ShaderStageFlags::COMPUTE),
        vk::DescriptorSetLayoutBinding::default().binding(1)
            .descriptor_type(vk::DescriptorType::STORAGE_IMAGE).descriptor_count(1)
            .stage_flags(vk::ShaderStageFlags::COMPUTE),
    ];
    device.create_descriptor_set_layout(
        &vk::DescriptorSetLayoutCreateInfo::default().bindings(&bindings), None,
    ).context("create fft set layout")
}

fn write_storage_image(device: &Device, set: vk::DescriptorSet, binding: u32, view: vk::ImageView) {
    let img_info = [vk::DescriptorImageInfo::default()
        .image_view(view).image_layout(vk::ImageLayout::GENERAL)];
    let write = vk::WriteDescriptorSet::default()
        .dst_set(set).dst_binding(binding)
        .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
        .image_info(&img_info);
    unsafe { device.update_descriptor_sets(&[write], &[]) };
}

fn push_bytes<T: Copy>(v: &T) -> &[u8] {
    unsafe {
        std::slice::from_raw_parts((v as *const T).cast::<u8>(), std::mem::size_of::<T>())
    }
}

fn to_general_barrier(image: vk::Image) -> vk::ImageMemoryBarrier2<'static> {
    vk::ImageMemoryBarrier2::default()
        .src_stage_mask(vk::PipelineStageFlags2::ALL_COMMANDS)
        .dst_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
        .dst_access_mask(vk::AccessFlags2::SHADER_WRITE | vk::AccessFlags2::SHADER_READ)
        .old_layout(vk::ImageLayout::UNDEFINED)
        .new_layout(vk::ImageLayout::GENERAL)
        .image(image).subresource_range(color_range())
}

fn compute_rw_barrier(image: vk::Image) -> vk::ImageMemoryBarrier2<'static> {
    vk::ImageMemoryBarrier2::default()
        .src_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
        .src_access_mask(vk::AccessFlags2::SHADER_WRITE)
        .dst_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
        .dst_access_mask(vk::AccessFlags2::SHADER_READ | vk::AccessFlags2::SHADER_WRITE)
        .old_layout(vk::ImageLayout::GENERAL)
        .new_layout(vk::ImageLayout::GENERAL)
        .image(image).subresource_range(color_range())
}

fn disp_to_shader_read(image: vk::Image) -> vk::ImageMemoryBarrier2<'static> {
    vk::ImageMemoryBarrier2::default()
        .src_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
        .src_access_mask(vk::AccessFlags2::SHADER_WRITE)
        .dst_stage_mask(vk::PipelineStageFlags2::VERTEX_SHADER | vk::PipelineStageFlags2::FRAGMENT_SHADER)
        .dst_access_mask(vk::AccessFlags2::SHADER_READ)
        .old_layout(vk::ImageLayout::GENERAL)
        .new_layout(vk::ImageLayout::GENERAL)
        .image(image).subresource_range(color_range())
}
