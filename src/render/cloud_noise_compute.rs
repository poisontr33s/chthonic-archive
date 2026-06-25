//! Rung 6.3 — Volumetric cloud noise precomputation (Stage-3-D).
//!
//! Bakes three noise assets once at startup (frame_index == 0):
//!   Base shape  128³  RGBA8  Perlin-Worley R + Worley FBM octaves G/B/A
//!   Detail      32³   RGBA8  Worley FBM at increasing frequencies R/G/B
//!   Coverage    512²  R8     2-D Perlin FBM (partly-cloudy bias)
//!
//! Single compute pipeline, target selected by `push_constant.target_pass`.
//! All three images end in SHADER_READ_ONLY_OPTIMAL for the raymarcher.
//!
//! @SID:    RENDER_CLOUD_NOISE_V1
//! @Shabti: Cloud-Noise-Compute

use anyhow::{Context, Result};
use ash::{Device, vk};
use gpu_allocator::vulkan::{Allocation, AllocationCreateDesc, AllocationScheme};
use gpu_allocator::MemoryLocation;
use log::info;

use super::vulkan::VulkanContext;

pub const BASE_NOISE_SIZE:   u32 = 128;
pub const DETAIL_NOISE_SIZE: u32 = 32;
pub const COVERAGE_MAP_SIZE: u32 = 512;

#[repr(C)]
#[derive(Clone, Copy)]
struct CloudNoisePush {
    target_pass: i32,
    scale:       f32,
}

pub struct CloudNoiseCompute {
    pub base_noise_image:   vk::Image,
    pub base_noise_alloc:   Option<Allocation>,
    pub base_noise_view:    vk::ImageView,

    pub detail_noise_image: vk::Image,
    pub detail_noise_alloc: Option<Allocation>,
    pub detail_noise_view:  vk::ImageView,

    pub coverage_map_image: vk::Image,
    pub coverage_map_alloc: Option<Allocation>,
    pub coverage_map_view:  vk::ImageView,

    /// Linear-repeat sampler for tiling 3D noise reads.
    pub sampler_3d: vk::Sampler,
    /// Linear-repeat sampler for world-tiled coverage map reads.
    pub sampler_2d: vk::Sampler,

    pub desc_pool:       vk::DescriptorPool,
    pub desc_set_layout: vk::DescriptorSetLayout,
    pub desc_set:        vk::DescriptorSet,
    pub pipeline_layout: vk::PipelineLayout,
    pub pipeline:        vk::Pipeline,
}

impl CloudNoiseCompute {
    pub unsafe fn new(ctx: &VulkanContext) -> Result<Self> {
        info!("☁️  Initializing Cloud Noise Compute (Base+Detail+Coverage)");

        let (base_noise_image, base_noise_alloc, base_noise_view) =
            Self::alloc_3d_image(ctx, "cloud_base_noise",
                BASE_NOISE_SIZE, vk::Format::R8G8B8A8_UNORM)?;

        let (detail_noise_image, detail_noise_alloc, detail_noise_view) =
            Self::alloc_3d_image(ctx, "cloud_detail_noise",
                DETAIL_NOISE_SIZE, vk::Format::R8G8B8A8_UNORM)?;

        // R8_UNORM is supported as a storage image on NVIDIA Ampere/Ada (RTX 3xxx/4xxx).
        let (coverage_map_image, coverage_map_alloc, coverage_map_view) =
            Self::alloc_2d_image(ctx, "cloud_coverage_map",
                COVERAGE_MAP_SIZE, vk::Format::R8_UNORM)?;

        let sampler_3d = ctx.device.create_sampler(
            &vk::SamplerCreateInfo::default()
                .mag_filter(vk::Filter::LINEAR)
                .min_filter(vk::Filter::LINEAR)
                .mipmap_mode(vk::SamplerMipmapMode::LINEAR)
                .address_mode_u(vk::SamplerAddressMode::REPEAT)
                .address_mode_v(vk::SamplerAddressMode::REPEAT)
                .address_mode_w(vk::SamplerAddressMode::REPEAT)
                .max_anisotropy(1.0),
            None,
        ).context("cloud noise 3D sampler")?;

        let sampler_2d = ctx.device.create_sampler(
            &vk::SamplerCreateInfo::default()
                .mag_filter(vk::Filter::LINEAR)
                .min_filter(vk::Filter::LINEAR)
                .address_mode_u(vk::SamplerAddressMode::REPEAT)
                .address_mode_v(vk::SamplerAddressMode::REPEAT)
                .max_anisotropy(1.0),
            None,
        ).context("cloud noise 2D sampler")?;

        // Descriptor pool: 3 STORAGE_IMAGE slots, 1 set.
        let pool_sizes = [vk::DescriptorPoolSize::default()
            .ty(vk::DescriptorType::STORAGE_IMAGE)
            .descriptor_count(3)];
        let desc_pool = ctx.device.create_descriptor_pool(
            &vk::DescriptorPoolCreateInfo::default()
                .max_sets(1)
                .pool_sizes(&pool_sizes),
            None,
        ).context("cloud noise desc pool")?;

        let bindings = [
            vk::DescriptorSetLayoutBinding::default()
                .binding(0).descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
                .descriptor_count(1).stage_flags(vk::ShaderStageFlags::COMPUTE),
            vk::DescriptorSetLayoutBinding::default()
                .binding(1).descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
                .descriptor_count(1).stage_flags(vk::ShaderStageFlags::COMPUTE),
            vk::DescriptorSetLayoutBinding::default()
                .binding(2).descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
                .descriptor_count(1).stage_flags(vk::ShaderStageFlags::COMPUTE),
        ];
        let desc_set_layout = ctx.device.create_descriptor_set_layout(
            &vk::DescriptorSetLayoutCreateInfo::default().bindings(&bindings),
            None,
        ).context("cloud noise desc set layout")?;

        let desc_set = ctx.device.allocate_descriptor_sets(
            &vk::DescriptorSetAllocateInfo::default()
                .descriptor_pool(desc_pool)
                .set_layouts(std::slice::from_ref(&desc_set_layout)),
        ).context("cloud noise desc set")?[0];

        let base_info     = vk::DescriptorImageInfo::default()
            .image_layout(vk::ImageLayout::GENERAL).image_view(base_noise_view);
        let detail_info   = vk::DescriptorImageInfo::default()
            .image_layout(vk::ImageLayout::GENERAL).image_view(detail_noise_view);
        let coverage_info = vk::DescriptorImageInfo::default()
            .image_layout(vk::ImageLayout::GENERAL).image_view(coverage_map_view);
        ctx.device.update_descriptor_sets(&[
            vk::WriteDescriptorSet::default().dst_set(desc_set).dst_binding(0)
                .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
                .image_info(std::slice::from_ref(&base_info)),
            vk::WriteDescriptorSet::default().dst_set(desc_set).dst_binding(1)
                .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
                .image_info(std::slice::from_ref(&detail_info)),
            vk::WriteDescriptorSet::default().dst_set(desc_set).dst_binding(2)
                .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
                .image_info(std::slice::from_ref(&coverage_info)),
        ], &[]);

        let push_range = vk::PushConstantRange::default()
            .stage_flags(vk::ShaderStageFlags::COMPUTE)
            .offset(0)
            .size(std::mem::size_of::<CloudNoisePush>() as u32);
        let pipeline_layout = ctx.device.create_pipeline_layout(
            &vk::PipelineLayoutCreateInfo::default()
                .set_layouts(std::slice::from_ref(&desc_set_layout))
                .push_constant_ranges(std::slice::from_ref(&push_range)),
            None,
        ).context("cloud noise pipeline layout")?;

        let shader_bytes = std::fs::read("target/debug/cloud_noise.comp.spv")
            .context("failed to read cloud_noise.comp.spv")?;
        let words: Vec<u32> = shader_bytes.chunks_exact(4)
            .map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]]))
            .collect();
        let shader_module = ctx.device.create_shader_module(
            &vk::ShaderModuleCreateInfo::default().code(&words),
            None,
        ).context("cloud noise shader module")?;

        let pipeline_info = vk::ComputePipelineCreateInfo::default()
            .stage(vk::PipelineShaderStageCreateInfo::default()
                .stage(vk::ShaderStageFlags::COMPUTE)
                .module(shader_module)
                .name(std::ffi::CStr::from_bytes_with_nul(b"main\0").unwrap()))
            .layout(pipeline_layout);
        let pipeline = ctx.device.create_compute_pipelines(
            vk::PipelineCache::null(),
            std::slice::from_ref(&pipeline_info),
            None,
        ).map_err(|e| anyhow::anyhow!("cloud noise pipeline: {:?}", e))?[0];
        ctx.device.destroy_shader_module(shader_module, None);

        info!("☁️  Cloud Noise: {}³ base + {}³ detail + {}² coverage allocated",
            BASE_NOISE_SIZE, DETAIL_NOISE_SIZE, COVERAGE_MAP_SIZE);

        Ok(Self {
            base_noise_image,
            base_noise_alloc: Some(base_noise_alloc),
            base_noise_view,
            detail_noise_image,
            detail_noise_alloc: Some(detail_noise_alloc),
            detail_noise_view,
            coverage_map_image,
            coverage_map_alloc: Some(coverage_map_alloc),
            coverage_map_view,
            sampler_3d,
            sampler_2d,
            desc_pool,
            desc_set_layout,
            desc_set,
            pipeline_layout,
            pipeline,
        })
    }

    /// One-shot bake — call exactly once on `frame_index == 0`.
    /// Dispatches all three passes sequentially. No barriers are needed between
    /// passes because each writes a distinct image (no hazard).
    pub unsafe fn dispatch(&self, device: &Device, cmd: vk::CommandBuffer) {
        // All three images: UNDEFINED → GENERAL
        let init = [
            Self::undef_to_general(self.base_noise_image),
            Self::undef_to_general(self.detail_noise_image),
            Self::undef_to_general(self.coverage_map_image),
        ];
        device.cmd_pipeline_barrier2(
            cmd, &vk::DependencyInfo::default().image_memory_barriers(&init));

        device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::COMPUTE, self.pipeline);
        device.cmd_bind_descriptor_sets(
            cmd, vk::PipelineBindPoint::COMPUTE, self.pipeline_layout,
            0, &[self.desc_set], &[]);

        // Pass 0: base 128³ — 16×16×16 groups
        let p0 = CloudNoisePush { target_pass: 0, scale: 1.0 };
        device.cmd_push_constants(cmd, self.pipeline_layout,
            vk::ShaderStageFlags::COMPUTE, 0, Self::push_bytes(&p0));
        let g128 = (BASE_NOISE_SIZE + 7) / 8;
        device.cmd_dispatch(cmd, g128, g128, g128);

        // Pass 1: detail 32³ — 4×4×4 groups (different image, no barrier)
        let p1 = CloudNoisePush { target_pass: 1, scale: 1.0 };
        device.cmd_push_constants(cmd, self.pipeline_layout,
            vk::ShaderStageFlags::COMPUTE, 0, Self::push_bytes(&p1));
        let g32 = (DETAIL_NOISE_SIZE + 7) / 8;
        device.cmd_dispatch(cmd, g32, g32, g32);

        // Pass 2: coverage 512² — 64×64×1 groups
        let p2 = CloudNoisePush { target_pass: 2, scale: 1.0 };
        device.cmd_push_constants(cmd, self.pipeline_layout,
            vk::ShaderStageFlags::COMPUTE, 0, Self::push_bytes(&p2));
        let g512 = (COVERAGE_MAP_SIZE + 7) / 8;
        device.cmd_dispatch(cmd, g512, g512, 1);

        // All three: GENERAL → SHADER_READ_ONLY_OPTIMAL
        let read = [
            Self::general_to_read(self.base_noise_image),
            Self::general_to_read(self.detail_noise_image),
            Self::general_to_read(self.coverage_map_image),
        ];
        device.cmd_pipeline_barrier2(
            cmd, &vk::DependencyInfo::default().image_memory_barriers(&read));
    }

    pub unsafe fn cleanup(
        &mut self,
        device: &Device,
        allocator: &mut gpu_allocator::vulkan::Allocator,
    ) {
        device.destroy_pipeline(self.pipeline, None);
        device.destroy_pipeline_layout(self.pipeline_layout, None);
        device.destroy_descriptor_set_layout(self.desc_set_layout, None);
        device.destroy_descriptor_pool(self.desc_pool, None);
        device.destroy_sampler(self.sampler_3d, None);
        device.destroy_sampler(self.sampler_2d, None);

        device.destroy_image_view(self.base_noise_view, None);
        device.destroy_image(self.base_noise_image, None);
        if let Some(a) = self.base_noise_alloc.take() {
            allocator.free(a).unwrap_or_else(|e| log::warn!("base noise free: {e}"));
        }
        device.destroy_image_view(self.detail_noise_view, None);
        device.destroy_image(self.detail_noise_image, None);
        if let Some(a) = self.detail_noise_alloc.take() {
            allocator.free(a).unwrap_or_else(|e| log::warn!("detail noise free: {e}"));
        }
        device.destroy_image_view(self.coverage_map_view, None);
        device.destroy_image(self.coverage_map_image, None);
        if let Some(a) = self.coverage_map_alloc.take() {
            allocator.free(a).unwrap_or_else(|e| log::warn!("coverage map free: {e}"));
        }
    }

    // ─── Private helpers ──────────────────────────────────────────────────────

    unsafe fn alloc_3d_image(
        ctx: &VulkanContext,
        label: &str,
        size: u32,
        format: vk::Format,
    ) -> Result<(vk::Image, Allocation, vk::ImageView)> {
        let image = ctx.device.create_image(
            &vk::ImageCreateInfo::default()
                .image_type(vk::ImageType::TYPE_3D)
                .format(format)
                .extent(vk::Extent3D { width: size, height: size, depth: size })
                .mip_levels(1)
                .array_layers(1)        // 3D images must have exactly 1 array layer
                .samples(vk::SampleCountFlags::TYPE_1)
                .tiling(vk::ImageTiling::OPTIMAL)
                .usage(vk::ImageUsageFlags::STORAGE | vk::ImageUsageFlags::SAMPLED)
                .sharing_mode(vk::SharingMode::EXCLUSIVE)
                .initial_layout(vk::ImageLayout::UNDEFINED),
            None,
        ).with_context(|| format!("create {label} 3D image"))?;

        let req = ctx.device.get_image_memory_requirements(image);
        let alloc = ctx.allocator.lock().unwrap().allocate(&AllocationCreateDesc {
            name: label, requirements: req,
            location: MemoryLocation::GpuOnly, linear: false,
            allocation_scheme: AllocationScheme::GpuAllocatorManaged,
        }).with_context(|| format!("alloc {label}"))?;
        ctx.device.bind_image_memory(image, alloc.memory(), alloc.offset())?;

        let view = ctx.device.create_image_view(
            &vk::ImageViewCreateInfo::default()
                .image(image)
                .view_type(vk::ImageViewType::TYPE_3D)  // must match image type
                .format(format)
                .subresource_range(vk::ImageSubresourceRange {
                    aspect_mask: vk::ImageAspectFlags::COLOR,
                    base_mip_level: 0, level_count: 1,
                    base_array_layer: 0, layer_count: 1,
                }),
            None,
        ).with_context(|| format!("create {label} 3D view"))?;

        Ok((image, alloc, view))
    }

    unsafe fn alloc_2d_image(
        ctx: &VulkanContext,
        label: &str,
        size: u32,
        format: vk::Format,
    ) -> Result<(vk::Image, Allocation, vk::ImageView)> {
        let image = ctx.device.create_image(
            &vk::ImageCreateInfo::default()
                .image_type(vk::ImageType::TYPE_2D)
                .format(format)
                .extent(vk::Extent3D { width: size, height: size, depth: 1 })
                .mip_levels(1).array_layers(1)
                .samples(vk::SampleCountFlags::TYPE_1)
                .tiling(vk::ImageTiling::OPTIMAL)
                .usage(vk::ImageUsageFlags::STORAGE | vk::ImageUsageFlags::SAMPLED)
                .sharing_mode(vk::SharingMode::EXCLUSIVE)
                .initial_layout(vk::ImageLayout::UNDEFINED),
            None,
        ).with_context(|| format!("create {label} 2D image"))?;

        let req = ctx.device.get_image_memory_requirements(image);
        let alloc = ctx.allocator.lock().unwrap().allocate(&AllocationCreateDesc {
            name: label, requirements: req,
            location: MemoryLocation::GpuOnly, linear: false,
            allocation_scheme: AllocationScheme::GpuAllocatorManaged,
        }).with_context(|| format!("alloc {label}"))?;
        ctx.device.bind_image_memory(image, alloc.memory(), alloc.offset())?;

        let view = ctx.device.create_image_view(
            &vk::ImageViewCreateInfo::default()
                .image(image).view_type(vk::ImageViewType::TYPE_2D)
                .format(format)
                .subresource_range(vk::ImageSubresourceRange {
                    aspect_mask: vk::ImageAspectFlags::COLOR,
                    base_mip_level: 0, level_count: 1,
                    base_array_layer: 0, layer_count: 1,
                }),
            None,
        ).with_context(|| format!("create {label} 2D view"))?;

        Ok((image, alloc, view))
    }

    fn push_bytes<T: Copy>(v: &T) -> &[u8] {
        unsafe {
            std::slice::from_raw_parts(
                (v as *const T).cast::<u8>(), std::mem::size_of::<T>())
        }
    }

    fn undef_to_general(image: vk::Image) -> vk::ImageMemoryBarrier2<'static> {
        vk::ImageMemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::TOP_OF_PIPE)
            .src_access_mask(vk::AccessFlags2::empty())
            .dst_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
            .dst_access_mask(vk::AccessFlags2::SHADER_WRITE)
            .old_layout(vk::ImageLayout::UNDEFINED)
            .new_layout(vk::ImageLayout::GENERAL)
            .image(image)
            .subresource_range(vk::ImageSubresourceRange {
                aspect_mask: vk::ImageAspectFlags::COLOR,
                base_mip_level: 0, level_count: 1,
                base_array_layer: 0, layer_count: 1,
            })
    }

    fn general_to_read(image: vk::Image) -> vk::ImageMemoryBarrier2<'static> {
        vk::ImageMemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
            .src_access_mask(vk::AccessFlags2::SHADER_WRITE)
            .dst_stage_mask(
                vk::PipelineStageFlags2::FRAGMENT_SHADER
                    | vk::PipelineStageFlags2::COMPUTE_SHADER)
            .dst_access_mask(vk::AccessFlags2::SHADER_READ)
            .old_layout(vk::ImageLayout::GENERAL)
            .new_layout(vk::ImageLayout::SHADER_READ_ONLY_OPTIMAL)
            .image(image)
            .subresource_range(vk::ImageSubresourceRange {
                aspect_mask: vk::ImageAspectFlags::COLOR,
                base_mip_level: 0, level_count: 1,
                base_array_layer: 0, layer_count: 1,
            })
    }
}
