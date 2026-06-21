//! Rung 4.2 — the ocean displacement compute subsystem. The renderer's first compute
//! pipeline + descriptor sets. A compute shader (`ocean_displace.comp`) writes a
//! displacement field into a storage image each frame; the surface vertex shader samples
//! it (wired in 4.2a-ii). 4.2a: procedural Gerstner body; 4.2b/c: Tessendorf spectrum + IFFT.

//! @SID:    RENDER_OCEAN_COMPUTE_V1
//! @Shabti: Ocean-Compute

use anyhow::{Context, Result};
use ash::{Device, vk};
use log::info;

use super::vulkan::VulkanContext;

/// Push constants for the displacement compute (16 bytes; matches `ocean_displace.comp`).
#[repr(C)]
#[derive(Clone, Copy)]
struct ComputePush {
    time: f32,
    x_half: f32,
    z_half: f32,
    resolution: u32,
}

/// World half-extents of the surface grid (must match `ocean::surface_grid`).
const X_HALF: f32 = 2.45;
const Z_HALF: f32 = 0.92;

/// The ocean displacement compute subsystem.
pub struct OceanCompute {
    pub image: vk::Image,
    pub memory: vk::DeviceMemory,
    pub view: vk::ImageView,
    pub sampler: vk::Sampler,
    pub desc_pool: vk::DescriptorPool,
    pub compute_set_layout: vk::DescriptorSetLayout,
    pub compute_set: vk::DescriptorSet,
    /// Set layout for the graphics pass (binding 0 = combined-image-sampler). Wire into the
    /// graphics pipeline layout so water.vert can sample the displacement image.
    pub graphics_set_layout: vk::DescriptorSetLayout,
    /// Descriptor set the graphics pass binds — water.vert samples this at set 0, binding 0.
    pub graphics_set: vk::DescriptorSet,
    pub pipeline_layout: vk::PipelineLayout,
    pub pipeline: vk::Pipeline,
    pub shader: vk::ShaderModule,
    pub resolution: u32,
}

fn color_range() -> vk::ImageSubresourceRange {
    vk::ImageSubresourceRange {
        aspect_mask: vk::ImageAspectFlags::COLOR,
        base_mip_level: 0,
        level_count: 1,
        base_array_layer: 0,
        layer_count: 1,
    }
}

impl OceanCompute {
    /// # Safety
    /// Requires a valid Vulkan context; cleanup() must be called before device destruction.
    pub unsafe fn new(ctx: &VulkanContext) -> Result<Self> {
        let device = &ctx.device;
        let resolution: u32 = 256;
        let format = vk::Format::R16G16B16A16_SFLOAT;

        // --- storage image (compute writes, graphics samples) ---
        let image_info = vk::ImageCreateInfo::default()
            .image_type(vk::ImageType::TYPE_2D)
            .format(format)
            .extent(vk::Extent3D {
                width: resolution,
                height: resolution,
                depth: 1,
            })
            .mip_levels(1)
            .array_layers(1)
            .samples(vk::SampleCountFlags::TYPE_1)
            .tiling(vk::ImageTiling::OPTIMAL)
            .usage(vk::ImageUsageFlags::STORAGE | vk::ImageUsageFlags::SAMPLED)
            .sharing_mode(vk::SharingMode::EXCLUSIVE)
            .initial_layout(vk::ImageLayout::UNDEFINED);
        let image = device
            .create_image(&image_info, None)
            .context("create displacement image")?;

        let req = device.get_image_memory_requirements(image);
        let mem_type = Self::find_memory_type(
            ctx,
            req.memory_type_bits,
            vk::MemoryPropertyFlags::DEVICE_LOCAL,
        )?;
        let memory = device
            .allocate_memory(
                &vk::MemoryAllocateInfo::default()
                    .allocation_size(req.size)
                    .memory_type_index(mem_type),
                None,
            )
            .context("alloc displacement memory")?;
        device.bind_image_memory(image, memory, 0)?;

        let view = device
            .create_image_view(
                &vk::ImageViewCreateInfo::default()
                    .image(image)
                    .view_type(vk::ImageViewType::TYPE_2D)
                    .format(format)
                    .subresource_range(color_range()),
                None,
            )
            .context("create displacement view")?;

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
            .context("create displacement sampler")?;

        // --- descriptor pool (sized for the compute storage-image set + the later graphics sampler set) ---
        let pool_sizes = [
            vk::DescriptorPoolSize::default()
                .ty(vk::DescriptorType::STORAGE_IMAGE)
                .descriptor_count(1),
            vk::DescriptorPoolSize::default()
                .ty(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .descriptor_count(1),
        ];
        let desc_pool = device
            .create_descriptor_pool(
                &vk::DescriptorPoolCreateInfo::default()
                    .pool_sizes(&pool_sizes)
                    .max_sets(2),
                None,
            )
            .context("create descriptor pool")?;

        // --- compute descriptor set (binding 0 = storage image) ---
        let bindings = [vk::DescriptorSetLayoutBinding::default()
            .binding(0)
            .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
            .descriptor_count(1)
            .stage_flags(vk::ShaderStageFlags::COMPUTE)];
        let compute_set_layout = device
            .create_descriptor_set_layout(
                &vk::DescriptorSetLayoutCreateInfo::default().bindings(&bindings),
                None,
            )
            .context("create compute set layout")?;

        let set_layouts = [compute_set_layout];
        let compute_set = device
            .allocate_descriptor_sets(
                &vk::DescriptorSetAllocateInfo::default()
                    .descriptor_pool(desc_pool)
                    .set_layouts(&set_layouts),
            )
            .context("alloc compute set")?[0];

        let img_info = [vk::DescriptorImageInfo::default()
            .image_view(view)
            .image_layout(vk::ImageLayout::GENERAL)];
        let write = vk::WriteDescriptorSet::default()
            .dst_set(compute_set)
            .dst_binding(0)
            .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
            .image_info(&img_info);
        device.update_descriptor_sets(&[write], &[]);

        // --- graphics descriptor set (binding 0 = combined-image-sampler for water.vert) ---
        let gfx_bindings = [vk::DescriptorSetLayoutBinding::default()
            .binding(0)
            .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
            .descriptor_count(1)
            .stage_flags(vk::ShaderStageFlags::VERTEX)];
        let graphics_set_layout = device
            .create_descriptor_set_layout(
                &vk::DescriptorSetLayoutCreateInfo::default().bindings(&gfx_bindings),
                None,
            )
            .context("create graphics sampler set layout")?;

        let gfx_layouts = [graphics_set_layout];
        let graphics_set = device
            .allocate_descriptor_sets(
                &vk::DescriptorSetAllocateInfo::default()
                    .descriptor_pool(desc_pool)
                    .set_layouts(&gfx_layouts),
            )
            .context("alloc graphics sampler set")?[0];

        let gfx_img_info = [vk::DescriptorImageInfo::default()
            .sampler(sampler)
            .image_view(view)
            .image_layout(vk::ImageLayout::GENERAL)];
        let gfx_write = vk::WriteDescriptorSet::default()
            .dst_set(graphics_set)
            .dst_binding(0)
            .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
            .image_info(&gfx_img_info);
        device.update_descriptor_sets(&[gfx_write], &[]);

        // --- compute pipeline ---
        let spv = include_bytes!(concat!(env!("OUT_DIR"), "/ocean_displace.comp.spv"));
        let shader = Self::create_shader_module(device, spv)?;
        let push_ranges = [vk::PushConstantRange::default()
            .stage_flags(vk::ShaderStageFlags::COMPUTE)
            .offset(0)
            .size(u32::try_from(std::mem::size_of::<ComputePush>()).unwrap())];
        let pipeline_layout = device
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
                &[vk::ComputePipelineCreateInfo::default()
                    .stage(stage)
                    .layout(pipeline_layout)],
                None,
            )
            .map_err(|(_, e)| e)
            .context("create compute pipeline")?[0];

        info!(
            "🌊 Ocean compute: {resolution}x{resolution} displacement field (compute pipeline + descriptors)"
        );

        Ok(Self {
            image,
            memory,
            view,
            sampler,
            desc_pool,
            compute_set_layout,
            compute_set,
            graphics_set_layout,
            graphics_set,
            pipeline_layout,
            pipeline,
            shader,
            resolution,
        })
    }

    /// Dispatch the displacement compute for this frame. Discards + rewrites the whole image,
    /// then barriers the write for the vertex/fragment readers (4.2a-ii).
    ///
    /// # Safety
    /// `cmd` must be recording, outside any dynamic-rendering scope.
    pub unsafe fn dispatch(&self, device: &Device, cmd: vk::CommandBuffer, time: f32) {
        // Ready the image for compute write (discard previous contents — we rewrite every texel).
        let to_general = vk::ImageMemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::ALL_COMMANDS)
            .dst_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
            .dst_access_mask(vk::AccessFlags2::SHADER_WRITE)
            .old_layout(vk::ImageLayout::UNDEFINED)
            .new_layout(vk::ImageLayout::GENERAL)
            .image(self.image)
            .subresource_range(color_range());
        device.cmd_pipeline_barrier2(
            cmd,
            &vk::DependencyInfo::default().image_memory_barriers(&[to_general]),
        );

        device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::COMPUTE, self.pipeline);
        device.cmd_bind_descriptor_sets(
            cmd,
            vk::PipelineBindPoint::COMPUTE,
            self.pipeline_layout,
            0,
            &[self.compute_set],
            &[],
        );
        let push = ComputePush {
            time,
            x_half: X_HALF,
            z_half: Z_HALF,
            resolution: self.resolution,
        };
        device.cmd_push_constants(
            cmd,
            self.pipeline_layout,
            vk::ShaderStageFlags::COMPUTE,
            0,
            std::slice::from_raw_parts(
                (&raw const push).cast::<u8>(),
                std::mem::size_of::<ComputePush>(),
            ),
        );
        let groups = self.resolution.div_ceil(16);
        device.cmd_dispatch(cmd, groups, groups, 1);

        // Make the write visible to the surface vertex/fragment shaders.
        let to_read = vk::ImageMemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
            .src_access_mask(vk::AccessFlags2::SHADER_WRITE)
            .dst_stage_mask(
                vk::PipelineStageFlags2::VERTEX_SHADER | vk::PipelineStageFlags2::FRAGMENT_SHADER,
            )
            .dst_access_mask(vk::AccessFlags2::SHADER_READ)
            .old_layout(vk::ImageLayout::GENERAL)
            .new_layout(vk::ImageLayout::GENERAL)
            .image(self.image)
            .subresource_range(color_range());
        device.cmd_pipeline_barrier2(
            cmd,
            &vk::DependencyInfo::default().image_memory_barriers(&[to_read]),
        );
    }

    unsafe fn find_memory_type(
        ctx: &VulkanContext,
        type_filter: u32,
        properties: vk::MemoryPropertyFlags,
    ) -> Result<u32> {
        let mem = ctx
            .instance
            .get_physical_device_memory_properties(ctx.physical_device);
        for i in 0..mem.memory_type_count {
            if (type_filter & (1 << i)) != 0
                && mem.memory_types[i as usize]
                    .property_flags
                    .contains(properties)
            {
                return Ok(i);
            }
        }
        Err(anyhow::anyhow!(
            "no suitable memory type for ocean compute image"
        ))
    }

    unsafe fn create_shader_module(device: &Device, code: &[u8]) -> Result<vk::ShaderModule> {
        assert!(
            code.len().is_multiple_of(4),
            "SPIR-V must be 4-byte aligned"
        );
        let words: Vec<u32> = code
            .chunks_exact(4)
            .map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]]))
            .collect();
        device
            .create_shader_module(&vk::ShaderModuleCreateInfo::default().code(&words), None)
            .context("create compute shader module")
    }

    /// # Safety
    /// Device must be idle; call once before context destruction.
    pub unsafe fn cleanup(&self, device: &Device) {
        device.destroy_pipeline(self.pipeline, None);
        device.destroy_pipeline_layout(self.pipeline_layout, None);
        device.destroy_shader_module(self.shader, None);
        device.destroy_descriptor_set_layout(self.graphics_set_layout, None);
        device.destroy_descriptor_set_layout(self.compute_set_layout, None);
        device.destroy_descriptor_pool(self.desc_pool, None);
        device.destroy_sampler(self.sampler, None);
        device.destroy_image_view(self.view, None);
        device.destroy_image(self.image, None);
        device.free_memory(self.memory, None);
    }
}
