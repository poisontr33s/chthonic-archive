//! Rung 6.2 — Atmosphere scattering compute subsystem.
//! 
//! Implements Hillaire's physically-based scalable atmosphere model.
//! Precomputes Transmittance, Multi-Scattering, and Sky View lookup tables (LUTs).
//!
//! @SID:    RENDER_ATMOSPHERE_COMPUTE_V1
//! @Shabti: Atmosphere-Compute

use anyhow::{Context, Result};
use ash::{Device, vk};
use gpu_allocator::vulkan::{Allocation, AllocationCreateDesc, AllocationScheme};
use gpu_allocator::MemoryLocation;
use log::info;

use super::vulkan::VulkanContext;

pub const TRANSMITTANCE_LUT_WIDTH: u32 = 256;
pub const TRANSMITTANCE_LUT_HEIGHT: u32 = 64;

pub const MULTI_SCATTERING_LUT_WIDTH: u32 = 32;
pub const MULTI_SCATTERING_LUT_HEIGHT: u32 = 32;

pub const SKY_VIEW_LUT_WIDTH: u32 = 200;
pub const SKY_VIEW_LUT_HEIGHT: u32 = 200;

/// Manages the texture allocations and compute pipelines for the atmosphere LUTs.
pub struct AtmosphereCompute {
    pub transmittance_image: vk::Image,
    pub transmittance_alloc: Option<Allocation>,
    pub transmittance_view: vk::ImageView,

    pub multi_scattering_image: vk::Image,
    pub multi_scattering_alloc: Option<Allocation>,
    pub multi_scattering_view: vk::ImageView,

    pub sky_view_image: vk::Image,
    pub sky_view_alloc: Option<Allocation>,
    pub sky_view_view: vk::ImageView,

    pub sampler: vk::Sampler,
    
    pub desc_pool: vk::DescriptorPool,
    pub transmittance_set_layout: vk::DescriptorSetLayout,
    pub transmittance_desc_set: vk::DescriptorSet,
    pub transmittance_pipeline_layout: vk::PipelineLayout,
    pub transmittance_pipeline: vk::Pipeline,

    pub multiscatter_set_layout: vk::DescriptorSetLayout,
    pub multiscatter_desc_set: vk::DescriptorSet,
    pub multiscatter_pipeline_layout: vk::PipelineLayout,
    pub multiscatter_pipeline: vk::Pipeline,

    pub skyview_set_layout: vk::DescriptorSetLayout,
    pub skyview_desc_set: vk::DescriptorSet,
    pub skyview_pipeline_layout: vk::PipelineLayout,
    pub skyview_pipeline: vk::Pipeline,
}

impl AtmosphereCompute {
    pub unsafe fn new(ctx: &VulkanContext, sst_desc_set_layout: vk::DescriptorSetLayout) -> Result<Self> {
        info!("🌤️ Initializing Atmosphere Compute (Hillaire LUTs)");

        let sampler = ctx.device.create_sampler(
            &vk::SamplerCreateInfo::default()
                .mag_filter(vk::Filter::LINEAR)
                .min_filter(vk::Filter::LINEAR)
                .mipmap_mode(vk::SamplerMipmapMode::LINEAR)
                .address_mode_u(vk::SamplerAddressMode::CLAMP_TO_EDGE)
                .address_mode_v(vk::SamplerAddressMode::CLAMP_TO_EDGE)
                .address_mode_w(vk::SamplerAddressMode::CLAMP_TO_EDGE)
                .max_anisotropy(1.0),
            None,
        ).context("create atmosphere sampler")?;

        let (transmittance_image, transmittance_alloc, transmittance_view) = Self::alloc_storage_image(
            ctx,
            "Atmosphere Transmittance LUT",
            vk::Extent3D { width: TRANSMITTANCE_LUT_WIDTH, height: TRANSMITTANCE_LUT_HEIGHT, depth: 1 },
        )?;

        let (multi_scattering_image, multi_scattering_alloc, multi_scattering_view) = Self::alloc_storage_image(
            ctx,
            "Atmosphere Multi-Scattering LUT",
            vk::Extent3D { width: MULTI_SCATTERING_LUT_WIDTH, height: MULTI_SCATTERING_LUT_HEIGHT, depth: 1 },
        )?;

        let (sky_view_image, sky_view_alloc, sky_view_view) = Self::alloc_storage_image(
            ctx,
            "Atmosphere Sky View LUT",
            vk::Extent3D { width: SKY_VIEW_LUT_WIDTH, height: SKY_VIEW_LUT_HEIGHT, depth: 1 },
        )?;

        let pool_sizes = [
            vk::DescriptorPoolSize::default().ty(vk::DescriptorType::STORAGE_IMAGE).descriptor_count(3),
            vk::DescriptorPoolSize::default().ty(vk::DescriptorType::COMBINED_IMAGE_SAMPLER).descriptor_count(3),
        ];
        let desc_pool = ctx.device.create_descriptor_pool(
            &vk::DescriptorPoolCreateInfo::default()
                .max_sets(3)
                .pool_sizes(&pool_sizes),
            None,
        ).context("atmosphere desc pool")?;

        // Transmittance
        let transmittance_bindings = [vk::DescriptorSetLayoutBinding::default()
            .binding(0)
            .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
            .descriptor_count(1)
            .stage_flags(vk::ShaderStageFlags::COMPUTE)];
        let transmittance_set_layout = ctx.device.create_descriptor_set_layout(
            &vk::DescriptorSetLayoutCreateInfo::default().bindings(&transmittance_bindings),
            None,
        ).context("transmittance desc set layout")?;

        let transmittance_desc_set = ctx.device.allocate_descriptor_sets(
            &vk::DescriptorSetAllocateInfo::default()
                .descriptor_pool(desc_pool)
                .set_layouts(std::slice::from_ref(&transmittance_set_layout)),
        ).context("transmittance desc set")?[0];

        let trans_image_info = vk::DescriptorImageInfo::default()
            .image_layout(vk::ImageLayout::GENERAL)
            .image_view(transmittance_view);
        let write_trans = vk::WriteDescriptorSet::default()
            .dst_set(transmittance_desc_set)
            .dst_binding(0)
            .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
            .image_info(std::slice::from_ref(&trans_image_info));
        ctx.device.update_descriptor_sets(std::slice::from_ref(&write_trans), &[]);

        let transmittance_pipeline_layout = ctx.device.create_pipeline_layout(
            &vk::PipelineLayoutCreateInfo::default()
                .set_layouts(&[transmittance_set_layout, sst_desc_set_layout]),
            None,
        ).context("transmittance pipeline layout")?;

        let trans_shader_bytes = std::fs::read("target/debug/transmittance.comp.spv")
            .context("failed to read transmittance.comp.spv")?;
        let trans_shader_info = vk::ShaderModuleCreateInfo::default().code(bytemuck::cast_slice(&trans_shader_bytes));
        let trans_shader_module = ctx.device.create_shader_module(&trans_shader_info, None)?;

        let trans_pipeline_info = vk::ComputePipelineCreateInfo::default()
            .stage(vk::PipelineShaderStageCreateInfo::default()
                .stage(vk::ShaderStageFlags::COMPUTE)
                .module(trans_shader_module)
                .name(std::ffi::CStr::from_bytes_with_nul(b"main\0").unwrap()))
            .layout(transmittance_pipeline_layout);
        let transmittance_pipeline = ctx.device.create_compute_pipelines(vk::PipelineCache::null(), std::slice::from_ref(&trans_pipeline_info), None)
            .map_err(|e| anyhow::anyhow!("transmittance pipeline creation failed: {:?}", e))?[0];
        ctx.device.destroy_shader_module(trans_shader_module, None);

        // Multiscatter
        let multiscatter_bindings = [
            vk::DescriptorSetLayoutBinding::default()
                .binding(0)
                .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
                .descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::COMPUTE),
            vk::DescriptorSetLayoutBinding::default()
                .binding(1)
                .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::COMPUTE),
        ];
        let multiscatter_set_layout = ctx.device.create_descriptor_set_layout(
            &vk::DescriptorSetLayoutCreateInfo::default().bindings(&multiscatter_bindings),
            None,
        ).context("multiscatter desc set layout")?;

        let multiscatter_desc_set = ctx.device.allocate_descriptor_sets(
            &vk::DescriptorSetAllocateInfo::default()
                .descriptor_pool(desc_pool)
                .set_layouts(std::slice::from_ref(&multiscatter_set_layout)),
        ).context("multiscatter desc set")?[0];

        let ms_image_info = vk::DescriptorImageInfo::default()
            .image_layout(vk::ImageLayout::GENERAL)
            .image_view(multi_scattering_view);
        let trans_sampler_info = vk::DescriptorImageInfo::default()
            .image_layout(vk::ImageLayout::SHADER_READ_ONLY_OPTIMAL)
            .image_view(transmittance_view)
            .sampler(sampler);
        let writes_ms = [
            vk::WriteDescriptorSet::default()
                .dst_set(multiscatter_desc_set)
                .dst_binding(0)
                .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
                .image_info(std::slice::from_ref(&ms_image_info)),
            vk::WriteDescriptorSet::default()
                .dst_set(multiscatter_desc_set)
                .dst_binding(1)
                .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .image_info(std::slice::from_ref(&trans_sampler_info)),
        ];
        ctx.device.update_descriptor_sets(&writes_ms, &[]);

        let multiscatter_pipeline_layout = ctx.device.create_pipeline_layout(
            &vk::PipelineLayoutCreateInfo::default()
                .set_layouts(&[multiscatter_set_layout, sst_desc_set_layout]),
            None,
        ).context("multiscatter pipeline layout")?;

        let ms_shader_bytes = std::fs::read("target/debug/multiscatter.comp.spv")
            .context("failed to read multiscatter.comp.spv")?;
        let ms_shader_info = vk::ShaderModuleCreateInfo::default().code(bytemuck::cast_slice(&ms_shader_bytes));
        let ms_shader_module = ctx.device.create_shader_module(&ms_shader_info, None)?;

        let ms_pipeline_info = vk::ComputePipelineCreateInfo::default()
            .stage(vk::PipelineShaderStageCreateInfo::default()
                .stage(vk::ShaderStageFlags::COMPUTE)
                .module(ms_shader_module)
                .name(std::ffi::CStr::from_bytes_with_nul(b"main\0").unwrap()))
            .layout(multiscatter_pipeline_layout);
        let multiscatter_pipeline = ctx.device.create_compute_pipelines(vk::PipelineCache::null(), std::slice::from_ref(&ms_pipeline_info), None)
            .map_err(|e| anyhow::anyhow!("multiscatter pipeline creation failed: {:?}", e))?[0];
        ctx.device.destroy_shader_module(ms_shader_module, None);

        // Skyview
        let skyview_bindings = [
            vk::DescriptorSetLayoutBinding::default()
                .binding(0)
                .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
                .descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::COMPUTE),
            vk::DescriptorSetLayoutBinding::default()
                .binding(1)
                .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::COMPUTE),
            vk::DescriptorSetLayoutBinding::default()
                .binding(2)
                .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::COMPUTE),
        ];
        let skyview_set_layout = ctx.device.create_descriptor_set_layout(
            &vk::DescriptorSetLayoutCreateInfo::default().bindings(&skyview_bindings),
            None,
        ).context("skyview desc set layout")?;

        let skyview_desc_set = ctx.device.allocate_descriptor_sets(
            &vk::DescriptorSetAllocateInfo::default()
                .descriptor_pool(desc_pool)
                .set_layouts(std::slice::from_ref(&skyview_set_layout)),
        ).context("skyview desc set")?[0];

        let sv_image_info = vk::DescriptorImageInfo::default()
            .image_layout(vk::ImageLayout::GENERAL)
            .image_view(sky_view_view);
        let sv_trans_info = vk::DescriptorImageInfo::default()
            .image_layout(vk::ImageLayout::SHADER_READ_ONLY_OPTIMAL)
            .image_view(transmittance_view)
            .sampler(sampler);
        let sv_ms_info = vk::DescriptorImageInfo::default()
            .image_layout(vk::ImageLayout::SHADER_READ_ONLY_OPTIMAL)
            .image_view(multi_scattering_view)
            .sampler(sampler);
        let writes_sv = [
            vk::WriteDescriptorSet::default()
                .dst_set(skyview_desc_set)
                .dst_binding(0)
                .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
                .image_info(std::slice::from_ref(&sv_image_info)),
            vk::WriteDescriptorSet::default()
                .dst_set(skyview_desc_set)
                .dst_binding(1)
                .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .image_info(std::slice::from_ref(&sv_trans_info)),
            vk::WriteDescriptorSet::default()
                .dst_set(skyview_desc_set)
                .dst_binding(2)
                .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .image_info(std::slice::from_ref(&sv_ms_info)),
        ];
        ctx.device.update_descriptor_sets(&writes_sv, &[]);

        let skyview_pipeline_layout = ctx.device.create_pipeline_layout(
            &vk::PipelineLayoutCreateInfo::default()
                .set_layouts(&[skyview_set_layout, sst_desc_set_layout]),
            None,
        ).context("skyview pipeline layout")?;

        let sv_shader_bytes = std::fs::read("target/debug/skyview.comp.spv")
            .context("failed to read skyview.comp.spv")?;
        let sv_shader_info = vk::ShaderModuleCreateInfo::default().code(bytemuck::cast_slice(&sv_shader_bytes));
        let sv_shader_module = ctx.device.create_shader_module(&sv_shader_info, None)?;

        let sv_pipeline_info = vk::ComputePipelineCreateInfo::default()
            .stage(vk::PipelineShaderStageCreateInfo::default()
                .stage(vk::ShaderStageFlags::COMPUTE)
                .module(sv_shader_module)
                .name(std::ffi::CStr::from_bytes_with_nul(b"main\0").unwrap()))
            .layout(skyview_pipeline_layout);
        let skyview_pipeline = ctx.device.create_compute_pipelines(vk::PipelineCache::null(), std::slice::from_ref(&sv_pipeline_info), None)
            .map_err(|e| anyhow::anyhow!("skyview pipeline creation failed: {:?}", e))?[0];
        ctx.device.destroy_shader_module(sv_shader_module, None);

        info!("🌤️ Atmosphere Compute: Transmittance + Multi-Scattering + Sky View LUTs ready");

        Ok(Self {
            transmittance_image,
            transmittance_alloc: Some(transmittance_alloc),
            transmittance_view,

            multi_scattering_image,
            multi_scattering_alloc: Some(multi_scattering_alloc),
            multi_scattering_view,

            sky_view_image,
            sky_view_alloc: Some(sky_view_alloc),
            sky_view_view,

            sampler,

            desc_pool,
            transmittance_set_layout,
            transmittance_desc_set,
            transmittance_pipeline_layout,
            transmittance_pipeline,

            multiscatter_set_layout,
            multiscatter_desc_set,
            multiscatter_pipeline_layout,
            multiscatter_pipeline,

            skyview_set_layout,
            skyview_desc_set,
            skyview_pipeline_layout,
            skyview_pipeline,
        })
    }

    pub unsafe fn dispatch_transmittance(
        &self,
        device: &Device,
        cmd: vk::CommandBuffer,
        sst_desc_set: vk::DescriptorSet,
    ) {
        // Initial barrier: UNDEFINED -> GENERAL
        let init_barrier = vk::ImageMemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::TOP_OF_PIPE)
            .src_access_mask(vk::AccessFlags2::empty())
            .dst_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
            .dst_access_mask(vk::AccessFlags2::SHADER_WRITE)
            .old_layout(vk::ImageLayout::UNDEFINED)
            .new_layout(vk::ImageLayout::GENERAL)
            .image(self.transmittance_image)
            .subresource_range(vk::ImageSubresourceRange {
                aspect_mask: vk::ImageAspectFlags::COLOR,
                base_mip_level: 0,
                level_count: 1,
                base_array_layer: 0,
                layer_count: 1,
            });

        device.cmd_pipeline_barrier2(
            cmd,
            &vk::DependencyInfo::default()
                .image_memory_barriers(std::slice::from_ref(&init_barrier)),
        );

        // Bind pipeline and descriptors
        device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::COMPUTE, self.transmittance_pipeline);
        device.cmd_bind_descriptor_sets(
            cmd,
            vk::PipelineBindPoint::COMPUTE,
            self.transmittance_pipeline_layout,
            0,
            &[self.transmittance_desc_set, sst_desc_set],
            &[],
        );

        // Dispatch (LUT size is 256x64, local size is 8x8 -> groups: 32x8x1)
        let group_x = (TRANSMITTANCE_LUT_WIDTH + 7) / 8;
        let group_y = (TRANSMITTANCE_LUT_HEIGHT + 7) / 8;
        device.cmd_dispatch(cmd, group_x, group_y, 1);

        // Barrier: Compute Write (GENERAL) -> Shader Read (SHADER_READ_ONLY_OPTIMAL)
        let barrier = vk::ImageMemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
            .src_access_mask(vk::AccessFlags2::SHADER_WRITE)
            .dst_stage_mask(vk::PipelineStageFlags2::FRAGMENT_SHADER | vk::PipelineStageFlags2::COMPUTE_SHADER)
            .dst_access_mask(vk::AccessFlags2::SHADER_READ)
            .old_layout(vk::ImageLayout::GENERAL)
            .new_layout(vk::ImageLayout::SHADER_READ_ONLY_OPTIMAL)
            .image(self.transmittance_image)
            .subresource_range(vk::ImageSubresourceRange {
                aspect_mask: vk::ImageAspectFlags::COLOR,
                base_mip_level: 0,
                level_count: 1,
                base_array_layer: 0,
                layer_count: 1,
            });

        device.cmd_pipeline_barrier2(
            cmd,
            &vk::DependencyInfo::default()
                .image_memory_barriers(std::slice::from_ref(&barrier)),
        );
    }
    pub unsafe fn dispatch_multiscatter(
        &self,
        device: &Device,
        cmd: vk::CommandBuffer,
        sst_desc_set: vk::DescriptorSet,
    ) {
        // Barrier: UNDEFINED -> GENERAL for multi-scatter LUT
        let init_barrier = vk::ImageMemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::TOP_OF_PIPE)
            .src_access_mask(vk::AccessFlags2::empty())
            .dst_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
            .dst_access_mask(vk::AccessFlags2::SHADER_WRITE)
            .old_layout(vk::ImageLayout::UNDEFINED)
            .new_layout(vk::ImageLayout::GENERAL)
            .image(self.multi_scattering_image)
            .subresource_range(vk::ImageSubresourceRange {
                aspect_mask: vk::ImageAspectFlags::COLOR,
                base_mip_level: 0,
                level_count: 1,
                base_array_layer: 0,
                layer_count: 1,
            });

        device.cmd_pipeline_barrier2(
            cmd,
            &vk::DependencyInfo::default()
                .image_memory_barriers(std::slice::from_ref(&init_barrier)),
        );

        // Bind pipeline and descriptors
        device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::COMPUTE, self.multiscatter_pipeline);
        device.cmd_bind_descriptor_sets(
            cmd,
            vk::PipelineBindPoint::COMPUTE,
            self.multiscatter_pipeline_layout,
            0,
            &[self.multiscatter_desc_set, sst_desc_set],
            &[],
        );

        // Dispatch (LUT size is 32x32, local size is 8x8 -> groups: 4x4x1)
        let group_x = (MULTI_SCATTERING_LUT_WIDTH + 7) / 8;
        let group_y = (MULTI_SCATTERING_LUT_HEIGHT + 7) / 8;
        device.cmd_dispatch(cmd, group_x, group_y, 1);

        // Barrier: Compute Write (GENERAL) -> Shader Read (SHADER_READ_ONLY_OPTIMAL)
        let barrier = vk::ImageMemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
            .src_access_mask(vk::AccessFlags2::SHADER_WRITE)
            .dst_stage_mask(vk::PipelineStageFlags2::FRAGMENT_SHADER | vk::PipelineStageFlags2::COMPUTE_SHADER)
            .dst_access_mask(vk::AccessFlags2::SHADER_READ)
            .old_layout(vk::ImageLayout::GENERAL)
            .new_layout(vk::ImageLayout::SHADER_READ_ONLY_OPTIMAL)
            .image(self.multi_scattering_image)
            .subresource_range(vk::ImageSubresourceRange {
                aspect_mask: vk::ImageAspectFlags::COLOR,
                base_mip_level: 0,
                level_count: 1,
                base_array_layer: 0,
                layer_count: 1,
            });

        device.cmd_pipeline_barrier2(
            cmd,
            &vk::DependencyInfo::default()
                .image_memory_barriers(std::slice::from_ref(&barrier)),
        );
    }

    pub unsafe fn dispatch_skyview(
        &self,
        device: &Device,
        cmd: vk::CommandBuffer,
        sst_desc_set: vk::DescriptorSet,
    ) {
        // UNDEFINED -> GENERAL for sky view LUT
        let init_barrier = vk::ImageMemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::TOP_OF_PIPE)
            .src_access_mask(vk::AccessFlags2::empty())
            .dst_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
            .dst_access_mask(vk::AccessFlags2::SHADER_WRITE)
            .old_layout(vk::ImageLayout::UNDEFINED)
            .new_layout(vk::ImageLayout::GENERAL)
            .image(self.sky_view_image)
            .subresource_range(vk::ImageSubresourceRange {
                aspect_mask: vk::ImageAspectFlags::COLOR,
                base_mip_level: 0,
                level_count: 1,
                base_array_layer: 0,
                layer_count: 1,
            });

        device.cmd_pipeline_barrier2(
            cmd,
            &vk::DependencyInfo::default()
                .image_memory_barriers(std::slice::from_ref(&init_barrier)),
        );

        device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::COMPUTE, self.skyview_pipeline);
        device.cmd_bind_descriptor_sets(
            cmd,
            vk::PipelineBindPoint::COMPUTE,
            self.skyview_pipeline_layout,
            0,
            &[self.skyview_desc_set, sst_desc_set],
            &[],
        );

        // 200x200 LUT, local_size 8x8 -> 25x25 groups
        let group_x = (SKY_VIEW_LUT_WIDTH + 7) / 8;
        let group_y = (SKY_VIEW_LUT_HEIGHT + 7) / 8;
        device.cmd_dispatch(cmd, group_x, group_y, 1);

        // GENERAL -> SHADER_READ_ONLY_OPTIMAL
        // RAY_TRACING_SHADER_KHR added (Rung 2.5, independent review 2026-07-07):
        // water_reflection.rmiss samples this same LUT and was missing from this dst mask —
        // an unsynchronized read on paper even though the layout happened to already match.
        let barrier = vk::ImageMemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::COMPUTE_SHADER)
            .src_access_mask(vk::AccessFlags2::SHADER_WRITE)
            .dst_stage_mask(
                vk::PipelineStageFlags2::FRAGMENT_SHADER
                    | vk::PipelineStageFlags2::COMPUTE_SHADER
                    | vk::PipelineStageFlags2::RAY_TRACING_SHADER_KHR,
            )
            .dst_access_mask(vk::AccessFlags2::SHADER_READ)
            .old_layout(vk::ImageLayout::GENERAL)
            .new_layout(vk::ImageLayout::SHADER_READ_ONLY_OPTIMAL)
            .image(self.sky_view_image)
            .subresource_range(vk::ImageSubresourceRange {
                aspect_mask: vk::ImageAspectFlags::COLOR,
                base_mip_level: 0,
                level_count: 1,
                base_array_layer: 0,
                layer_count: 1,
            });

        device.cmd_pipeline_barrier2(
            cmd,
            &vk::DependencyInfo::default()
                .image_memory_barriers(std::slice::from_ref(&barrier)),
        );
    }

    pub unsafe fn cleanup(&mut self, device: &Device, allocator: &mut gpu_allocator::vulkan::Allocator) {
        device.destroy_pipeline(self.transmittance_pipeline, None);
        device.destroy_pipeline_layout(self.transmittance_pipeline_layout, None);
        device.destroy_descriptor_set_layout(self.transmittance_set_layout, None);

        device.destroy_pipeline(self.multiscatter_pipeline, None);
        device.destroy_pipeline_layout(self.multiscatter_pipeline_layout, None);
        device.destroy_descriptor_set_layout(self.multiscatter_set_layout, None);

        device.destroy_pipeline(self.skyview_pipeline, None);
        device.destroy_pipeline_layout(self.skyview_pipeline_layout, None);
        device.destroy_descriptor_set_layout(self.skyview_set_layout, None);

        device.destroy_descriptor_pool(self.desc_pool, None);

        device.destroy_sampler(self.sampler, None);

        device.destroy_image_view(self.transmittance_view, None);
        device.destroy_image(self.transmittance_image, None);
        if let Some(alloc) = self.transmittance_alloc.take() {
            allocator.free(alloc).unwrap_or_else(|e| log::warn!("Failed to free transmittance alloc: {}", e));
        }

        device.destroy_image_view(self.multi_scattering_view, None);
        device.destroy_image(self.multi_scattering_image, None);
        if let Some(alloc) = self.multi_scattering_alloc.take() {
            allocator.free(alloc).unwrap_or_else(|e| log::warn!("Failed to free multi-scattering alloc: {}", e));
        }

        device.destroy_image_view(self.sky_view_view, None);
        device.destroy_image(self.sky_view_image, None);
        if let Some(alloc) = self.sky_view_alloc.take() {
            allocator.free(alloc).unwrap_or_else(|e| log::warn!("Failed to free sky view alloc: {}", e));
        }
    }

    unsafe fn alloc_storage_image(
        ctx: &VulkanContext,
        label: &str,
        extent: vk::Extent3D,
    ) -> Result<(vk::Image, Allocation, vk::ImageView)> {
        let device = &ctx.device;
        let format = vk::Format::R16G16B16A16_SFLOAT;
        let image = device.create_image(
            &vk::ImageCreateInfo::default()
                .image_type(vk::ImageType::TYPE_2D)
                .format(format)
                .extent(extent)
                .mip_levels(1).array_layers(1)
                .samples(vk::SampleCountFlags::TYPE_1)
                .tiling(vk::ImageTiling::OPTIMAL)
                .usage(vk::ImageUsageFlags::STORAGE | vk::ImageUsageFlags::SAMPLED)
                .sharing_mode(vk::SharingMode::EXCLUSIVE)
                .initial_layout(vk::ImageLayout::UNDEFINED),
            None,
        ).with_context(|| format!("create {}", label))?;

        let req = device.get_image_memory_requirements(image);
        let alloc = ctx.allocator.lock().unwrap().allocate(&AllocationCreateDesc {
            name: label, requirements: req,
            location: MemoryLocation::GpuOnly, linear: false,
            allocation_scheme: AllocationScheme::GpuAllocatorManaged,
        }).with_context(|| format!("gpu-allocator: alloc {}", label))?;
        device.bind_image_memory(image, alloc.memory(), alloc.offset())?;

        let view = device.create_image_view(
            &vk::ImageViewCreateInfo::default()
                .image(image).view_type(vk::ImageViewType::TYPE_2D)
                .format(format)
                .subresource_range(vk::ImageSubresourceRange {
                    aspect_mask: vk::ImageAspectFlags::COLOR,
                    base_mip_level: 0,
                    level_count: 1,
                    base_array_layer: 0,
                    layer_count: 1,
                }),
            None,
        ).with_context(|| format!("create {} view", label))?;

        Ok((image, alloc, view))
    }
}
