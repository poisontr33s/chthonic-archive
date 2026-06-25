//! Rung 6.3 — Volumetric Cloud Raymarcher (Stage-3-D).
//!
//! Dispatches a full-screen compute shader every frame that integrates
//! Beer–Lambert extinction + Henyey-Greenstein phase function + Nubis-style
//! noise erosion. Output is a pre-multiplied RGBA16F cloud texture ready for
//! alpha-blending over the sky background.
//!
//! Descriptor sets consumed:
//!   Set 0  output rgba16f image (owned here)
//!   Set 1  FrameUniform UBO  (reuses sst_desc_set_layout + sst_desc_set)
//!   Set 2  3× noise CIS  (base 3D, detail 3D, coverage 2D) — views from CloudNoiseCompute
//!   Set 3  2× LUT  CIS   (transmittance, multi-scatter)    — views from AtmosphereCompute
//!
//! @SID:    RENDER_CLOUD_RAYMARCH_V1
//! @Shabti: Cloud-Raymarch

use anyhow::{Context, Result};
use ash::{Device, vk};
use gpu_allocator::vulkan::{Allocation, AllocationCreateDesc, AllocationScheme};
use gpu_allocator::MemoryLocation;
use log::info;

use super::vulkan::VulkanContext;

/// Push constant block matching `cloud_raymarch.comp`.
/// 64 + 16 + 8 + 8 = 96 bytes (within the 128-byte Vulkan minimum guarantee).
#[repr(C)]
#[derive(Clone, Copy)]
struct CloudRaymarchPush {
    inv_view_proj: [[f32; 4]; 4], // 64 bytes
    cam_pos_time:  [f32; 4],      // 16 bytes  (xyz = camera pos, w = time)
    resolution:    [f32; 2],      // 8  bytes
    pad:           [f32; 2],      // 8  bytes (alignment pad)
}

pub struct CloudRaymarchCompute {
    /// Full-resolution RGBA16F cloud render target.
    pub target_image: vk::Image,
    pub target_alloc: Option<Allocation>,
    pub target_view:  vk::ImageView,

    /// Linear clamp-to-edge sampler for the compositor to read the cloud target.
    pub target_sampler: vk::Sampler,

    /// Descriptor pool owning sets 0, 2, 3.
    pub desc_pool: vk::DescriptorPool,

    pub output_set_layout: vk::DescriptorSetLayout, // set 0
    pub output_set:        vk::DescriptorSet,

    pub noise_set_layout: vk::DescriptorSetLayout,  // set 2
    pub noise_set:        vk::DescriptorSet,

    pub lut_set_layout: vk::DescriptorSetLayout,    // set 3
    pub lut_set:        vk::DescriptorSet,

    pub pipeline_layout: vk::PipelineLayout,
    pub pipeline:        vk::Pipeline,
}

impl CloudRaymarchCompute {
    /// Build the cloud raymarcher.
    ///
    /// `sst_desc_set_layout` is the layout for set=1 (FrameUniform + sky view LUT);
    /// it is reused from the main pipeline — not stored here, only used for pipeline
    /// layout creation.
    pub unsafe fn new(
        ctx: &VulkanContext,
        width: u32,
        height: u32,
        sst_desc_set_layout: vk::DescriptorSetLayout,
        atmosphere: &super::atmosphere_compute::AtmosphereCompute,
        noise: &super::cloud_noise_compute::CloudNoiseCompute,
    ) -> Result<Self> {
        info!("☁️  Initializing Cloud Raymarch Compute ({}×{})", width, height);

        // ── Target image: rgba16f full-res ───────────────────────────────────
        let (target_image, target_alloc, target_view) =
            Self::alloc_rgba16f_target(ctx, width, height)?;

        let target_sampler = ctx.device.create_sampler(
            &vk::SamplerCreateInfo::default()
                .mag_filter(vk::Filter::LINEAR)
                .min_filter(vk::Filter::LINEAR)
                .address_mode_u(vk::SamplerAddressMode::CLAMP_TO_EDGE)
                .address_mode_v(vk::SamplerAddressMode::CLAMP_TO_EDGE)
                .max_anisotropy(1.0),
            None,
        ).context("cloud raymarch target sampler")?;

        // ── Descriptor pool: 3 sets, 1 SI + 5 CIS ───────────────────────────
        let pool_sizes = [
            vk::DescriptorPoolSize::default()
                .ty(vk::DescriptorType::STORAGE_IMAGE)
                .descriptor_count(1),
            vk::DescriptorPoolSize::default()
                .ty(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .descriptor_count(5),
        ];
        let desc_pool = ctx.device.create_descriptor_pool(
            &vk::DescriptorPoolCreateInfo::default()
                .max_sets(3)
                .pool_sizes(&pool_sizes),
            None,
        ).context("cloud raymarch desc pool")?;

        // ── Set 0: output STORAGE_IMAGE ──────────────────────────────────────
        let output_binding = [
            vk::DescriptorSetLayoutBinding::default()
                .binding(0)
                .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
                .descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::COMPUTE),
        ];
        let output_set_layout = ctx.device.create_descriptor_set_layout(
            &vk::DescriptorSetLayoutCreateInfo::default().bindings(&output_binding),
            None,
        ).context("cloud raymarch output set layout")?;

        // ── Set 2: 3 COMBINED_IMAGE_SAMPLER (noise textures) ─────────────────
        let noise_bindings = [
            vk::DescriptorSetLayoutBinding::default()
                .binding(0).descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .descriptor_count(1).stage_flags(vk::ShaderStageFlags::COMPUTE),
            vk::DescriptorSetLayoutBinding::default()
                .binding(1).descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .descriptor_count(1).stage_flags(vk::ShaderStageFlags::COMPUTE),
            vk::DescriptorSetLayoutBinding::default()
                .binding(2).descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .descriptor_count(1).stage_flags(vk::ShaderStageFlags::COMPUTE),
        ];
        let noise_set_layout = ctx.device.create_descriptor_set_layout(
            &vk::DescriptorSetLayoutCreateInfo::default().bindings(&noise_bindings),
            None,
        ).context("cloud raymarch noise set layout")?;

        // ── Set 3: 2 COMBINED_IMAGE_SAMPLER (atmosphere LUTs) ────────────────
        let lut_bindings = [
            vk::DescriptorSetLayoutBinding::default()
                .binding(0).descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .descriptor_count(1).stage_flags(vk::ShaderStageFlags::COMPUTE),
            vk::DescriptorSetLayoutBinding::default()
                .binding(1).descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .descriptor_count(1).stage_flags(vk::ShaderStageFlags::COMPUTE),
        ];
        let lut_set_layout = ctx.device.create_descriptor_set_layout(
            &vk::DescriptorSetLayoutCreateInfo::default().bindings(&lut_bindings),
            None,
        ).context("cloud raymarch lut set layout")?;

        // ── Allocate 3 sets ───────────────────────────────────────────────────
        let layouts = [output_set_layout, noise_set_layout, lut_set_layout];
        let mut sets = ctx.device.allocate_descriptor_sets(
            &vk::DescriptorSetAllocateInfo::default()
                .descriptor_pool(desc_pool)
                .set_layouts(&layouts),
        ).context("cloud raymarch desc sets")?;
        let (output_set, noise_set, lut_set) = (sets[0], sets[1], sets[2]);

        // ── Write descriptors ─────────────────────────────────────────────────
        let out_info = vk::DescriptorImageInfo::default()
            .image_layout(vk::ImageLayout::GENERAL)
            .image_view(target_view);

        let base_info = vk::DescriptorImageInfo::default()
            .image_layout(vk::ImageLayout::SHADER_READ_ONLY_OPTIMAL)
            .image_view(noise.base_noise_view)
            .sampler(noise.sampler_3d);
        let detail_info = vk::DescriptorImageInfo::default()
            .image_layout(vk::ImageLayout::SHADER_READ_ONLY_OPTIMAL)
            .image_view(noise.detail_noise_view)
            .sampler(noise.sampler_3d);
        let cov_info = vk::DescriptorImageInfo::default()
            .image_layout(vk::ImageLayout::SHADER_READ_ONLY_OPTIMAL)
            .image_view(noise.coverage_map_view)
            .sampler(noise.sampler_2d);

        let tx_info = vk::DescriptorImageInfo::default()
            .image_layout(vk::ImageLayout::SHADER_READ_ONLY_OPTIMAL)
            .image_view(atmosphere.transmittance_view)
            .sampler(atmosphere.sampler);
        let ms_info = vk::DescriptorImageInfo::default()
            .image_layout(vk::ImageLayout::SHADER_READ_ONLY_OPTIMAL)
            .image_view(atmosphere.multi_scattering_view)
            .sampler(atmosphere.sampler);

        ctx.device.update_descriptor_sets(&[
            vk::WriteDescriptorSet::default()
                .dst_set(output_set).dst_binding(0)
                .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
                .image_info(std::slice::from_ref(&out_info)),
            vk::WriteDescriptorSet::default()
                .dst_set(noise_set).dst_binding(0)
                .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .image_info(std::slice::from_ref(&base_info)),
            vk::WriteDescriptorSet::default()
                .dst_set(noise_set).dst_binding(1)
                .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .image_info(std::slice::from_ref(&detail_info)),
            vk::WriteDescriptorSet::default()
                .dst_set(noise_set).dst_binding(2)
                .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .image_info(std::slice::from_ref(&cov_info)),
            vk::WriteDescriptorSet::default()
                .dst_set(lut_set).dst_binding(0)
                .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .image_info(std::slice::from_ref(&tx_info)),
            vk::WriteDescriptorSet::default()
                .dst_set(lut_set).dst_binding(1)
                .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .image_info(std::slice::from_ref(&ms_info)),
        ], &[]);

        // ── Pipeline layout: sets 0-3 + push constant ────────────────────────
        let set_layouts = [
            output_set_layout,
            sst_desc_set_layout, // set 1: reuse existing FrameUniform layout
            noise_set_layout,
            lut_set_layout,
        ];
        let push_range = vk::PushConstantRange::default()
            .stage_flags(vk::ShaderStageFlags::COMPUTE)
            .offset(0)
            .size(std::mem::size_of::<CloudRaymarchPush>() as u32);
        let pipeline_layout = ctx.device.create_pipeline_layout(
            &vk::PipelineLayoutCreateInfo::default()
                .set_layouts(&set_layouts)
                .push_constant_ranges(std::slice::from_ref(&push_range)),
            None,
        ).context("cloud raymarch pipeline layout")?;

        // ── Shader + pipeline ─────────────────────────────────────────────────
        let spv_bytes = std::fs::read("target/debug/cloud_raymarch.comp.spv")
            .context("failed to read cloud_raymarch.comp.spv")?;
        let words: Vec<u32> = spv_bytes.chunks_exact(4)
            .map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]]))
            .collect();
        let shader_module = ctx.device.create_shader_module(
            &vk::ShaderModuleCreateInfo::default().code(&words),
            None,
        ).context("cloud raymarch shader module")?;

        let stage = vk::PipelineShaderStageCreateInfo::default()
            .stage(vk::ShaderStageFlags::COMPUTE)
            .module(shader_module)
            .name(std::ffi::CStr::from_bytes_with_nul(b"main\0").unwrap());
        let pipeline = ctx.device.create_compute_pipelines(
            vk::PipelineCache::null(),
            std::slice::from_ref(&vk::ComputePipelineCreateInfo::default()
                .stage(stage)
                .layout(pipeline_layout)),
            None,
        ).map_err(|e| anyhow::anyhow!("cloud raymarch pipeline: {:?}", e))?[0];
        ctx.device.destroy_shader_module(shader_module, None);

        info!("☁️  Cloud Raymarch: {}×{} rgba16f target ready", width, height);

        Ok(Self {
            target_image,
            target_alloc: Some(target_alloc),
            target_view,
            target_sampler,
            desc_pool,
            output_set_layout,
            output_set,
            noise_set_layout,
            noise_set,
            lut_set_layout,
            lut_set,
            pipeline_layout,
            pipeline,
        })
    }

    /// Dispatch the cloud raymarcher.
    ///
    /// Must be called AFTER `cmd_end_rendering` and BEFORE the TAA/DLAA resolve.
    /// The cloud target transitions: UNDEFINED → GENERAL (write), then
    /// GENERAL → SHADER_READ_ONLY_OPTIMAL (ready for composite sampling).
    ///
    /// `inv_view_proj` — inverse of the frame's render VP matrix (glam row-major cols array).
    /// `cam_pos`       — camera position in game world space.
    /// `time`          — elapsed frame time for wind advection.
    pub unsafe fn dispatch(
        &self,
        device: &Device,
        cmd: vk::CommandBuffer,
        sst_desc_set: vk::DescriptorSet,
        inv_view_proj: [[f32; 4]; 4],
        cam_pos: [f32; 3],
        time: f32,
        width: u32,
        height: u32,
    ) {
        let subresource = vk::ImageSubresourceRange {
            aspect_mask: vk::ImageAspectFlags::COLOR,
            base_mip_level: 0, level_count: 1,
            base_array_layer: 0, layer_count: 1,
        };

        // UNDEFINED → GENERAL (discard previous frame; we rewrite fully each frame)
        let write_barrier = vk::ImageMemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::FRAGMENT_SHADER
                | vk::PipelineStageFlags2::COMPUTE_SHADER)
            .src_access_mask(vk::AccessFlags2::SHADER_READ)
            .dst_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
            .dst_access_mask(vk::AccessFlags2::SHADER_WRITE)
            .old_layout(vk::ImageLayout::UNDEFINED)
            .new_layout(vk::ImageLayout::GENERAL)
            .image(self.target_image)
            .subresource_range(subresource);
        device.cmd_pipeline_barrier2(
            cmd,
            &vk::DependencyInfo::default()
                .image_memory_barriers(std::slice::from_ref(&write_barrier)),
        );

        device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::COMPUTE, self.pipeline);
        device.cmd_bind_descriptor_sets(
            cmd, vk::PipelineBindPoint::COMPUTE, self.pipeline_layout,
            0,
            &[self.output_set, sst_desc_set, self.noise_set, self.lut_set],
            &[],
        );

        let push = CloudRaymarchPush {
            inv_view_proj,
            cam_pos_time: [cam_pos[0], cam_pos[1], cam_pos[2], time],
            resolution: [width as f32, height as f32],
            pad: [0.0, 0.0],
        };
        device.cmd_push_constants(
            cmd, self.pipeline_layout, vk::ShaderStageFlags::COMPUTE,
            0, Self::push_bytes(&push));

        let gx = (width  + 7) / 8;
        let gy = (height + 7) / 8;
        device.cmd_dispatch(cmd, gx, gy, 1);

        // GENERAL → SHADER_READ_ONLY_OPTIMAL (ready for compositor reads)
        let read_barrier = vk::ImageMemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
            .src_access_mask(vk::AccessFlags2::SHADER_WRITE)
            .dst_stage_mask(vk::PipelineStageFlags2::FRAGMENT_SHADER
                | vk::PipelineStageFlags2::COMPUTE_SHADER)
            .dst_access_mask(vk::AccessFlags2::SHADER_READ)
            .old_layout(vk::ImageLayout::GENERAL)
            .new_layout(vk::ImageLayout::SHADER_READ_ONLY_OPTIMAL)
            .image(self.target_image)
            .subresource_range(subresource);
        device.cmd_pipeline_barrier2(
            cmd,
            &vk::DependencyInfo::default()
                .image_memory_barriers(std::slice::from_ref(&read_barrier)),
        );
    }

    pub unsafe fn cleanup(
        &mut self,
        device: &Device,
        allocator: &mut gpu_allocator::vulkan::Allocator,
    ) {
        device.destroy_pipeline(self.pipeline, None);
        device.destroy_pipeline_layout(self.pipeline_layout, None);
        device.destroy_descriptor_set_layout(self.lut_set_layout, None);
        device.destroy_descriptor_set_layout(self.noise_set_layout, None);
        device.destroy_descriptor_set_layout(self.output_set_layout, None);
        device.destroy_descriptor_pool(self.desc_pool, None);
        device.destroy_sampler(self.target_sampler, None);
        device.destroy_image_view(self.target_view, None);
        device.destroy_image(self.target_image, None);
        if let Some(a) = self.target_alloc.take() {
            allocator.free(a).unwrap_or_else(|e| log::warn!("cloud target free: {e}"));
        }
    }

    // ─── Private helpers ──────────────────────────────────────────────────────

    unsafe fn alloc_rgba16f_target(
        ctx: &VulkanContext,
        width: u32,
        height: u32,
    ) -> Result<(vk::Image, Allocation, vk::ImageView)> {
        let image = ctx.device.create_image(
            &vk::ImageCreateInfo::default()
                .image_type(vk::ImageType::TYPE_2D)
                .format(vk::Format::R16G16B16A16_SFLOAT)
                .extent(vk::Extent3D { width, height, depth: 1 })
                .mip_levels(1).array_layers(1)
                .samples(vk::SampleCountFlags::TYPE_1)
                .tiling(vk::ImageTiling::OPTIMAL)
                .usage(vk::ImageUsageFlags::STORAGE | vk::ImageUsageFlags::SAMPLED)
                .sharing_mode(vk::SharingMode::EXCLUSIVE)
                .initial_layout(vk::ImageLayout::UNDEFINED),
            None,
        ).context("create cloud raymarch target")?;

        let req = ctx.device.get_image_memory_requirements(image);
        let alloc = ctx.allocator.lock().unwrap().allocate(&AllocationCreateDesc {
            name: "cloud_raymarch_target",
            requirements: req,
            location: MemoryLocation::GpuOnly,
            linear: false,
            allocation_scheme: AllocationScheme::GpuAllocatorManaged,
        }).context("alloc cloud raymarch target")?;
        ctx.device.bind_image_memory(image, alloc.memory(), alloc.offset())?;

        let view = ctx.device.create_image_view(
            &vk::ImageViewCreateInfo::default()
                .image(image)
                .view_type(vk::ImageViewType::TYPE_2D)
                .format(vk::Format::R16G16B16A16_SFLOAT)
                .subresource_range(vk::ImageSubresourceRange {
                    aspect_mask: vk::ImageAspectFlags::COLOR,
                    base_mip_level: 0, level_count: 1,
                    base_array_layer: 0, layer_count: 1,
                }),
            None,
        ).context("cloud raymarch target view")?;

        Ok((image, alloc, view))
    }

    fn push_bytes<T: Copy>(v: &T) -> &[u8] {
        unsafe {
            std::slice::from_raw_parts(
                (v as *const T).cast::<u8>(), std::mem::size_of::<T>())
        }
    }
}
