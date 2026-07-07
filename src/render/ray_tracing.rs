//! Rung 2.5 — hardware ray-traced water reflections. Phase 2: acceleration structures only.
//!
//! Two BLAS built once at startup from the CPU-side vertex buffers as they exist today:
//! the bathymetry mesh (genuinely static) and the ocean mesh (flat rest-state — all
//! Tessendorf wave displacement happens GPU-side in water.vert, never touching the CPU
//! vertex buffer). This trades wave-crest ripple accuracy in reflections for a much
//! simpler first cut; a displaced-BLAS upgrade is a deliberately deferred follow-up.
//!
//! One TLAS with two identity-transform instances, architected to rebuild every frame
//! from the start even though the flat-mesh approximation doesn't strictly require it yet —
//! this keeps the future displaced-BLAS upgrade to a localized change (swap which BLAS
//! handle the ocean instance points at) instead of a second architecture change.
//!
//! No consumer yet (Phase 3/4 add the shaders and pipeline that trace against this TLAS).
//! Correctness here is judged by validation layers reporting zero VUIDs on the AS builds.

//! @SID:    RENDER_RAY_TRACING_V1
//! @Shabti: Ray-Tracing

use anyhow::{Context, Result};
use ash::{khr, vk};
use gpu_allocator::vulkan::{Allocation, AllocationCreateDesc, AllocationScheme};
use gpu_allocator::MemoryLocation;
use log::info;

use super::pipeline::Vertex;
use super::vulkan::VulkanContext;

struct RtBuffer {
    buffer: vk::Buffer,
    alloc: Option<Allocation>,
    device_address: vk::DeviceAddress,
}

#[allow(dead_code)] // .accel/.backing consumed once Phase 5 rebuilds the TLAS per frame
struct Blas {
    accel: vk::AccelerationStructureKHR,
    backing: RtBuffer,
}

/// Rung 2.5 acceleration-structure state. Owns the BLAS/TLAS backing buffers and the
/// acceleration_structure device loader; the ray_tracing_pipeline loader is added in Phase 4.
#[allow(dead_code)] // blas_*/tlas_backing/tlas_instance_buffer consumed once Phase 4/5 land
pub struct RayTracing {
    pub accel_loader: khr::acceleration_structure::Device,
    #[allow(dead_code)] // consumed once Phase 4/5 bind the TLAS into the RT pipeline descriptor set
    pub tlas: vk::AccelerationStructureKHR,
    blas_bathymetry: Blas,
    blas_ocean: Blas,
    tlas_backing: RtBuffer,
    tlas_instance_buffer: RtBuffer,
    /// Device addresses of the (leaked, never-freed) BLAS-input copy buffers — the closest-hit
    /// shader's push constants need these to read per-triangle vertex data
    /// (water_reflection.rchit). Captured before the RtBuffer wrappers are forgotten in `new`.
    pub bathymetry_vertex_addr: vk::DeviceAddress,
    pub ocean_vertex_addr: vk::DeviceAddress,

    // Phase 4 — pipeline object + SBT. Populated by `build_pipeline`, called once other
    // per-frame resources (normal_ws/depth views, the shared frame-UBO descriptor set) exist.
    pub rt_pipeline_loader: Option<khr::ray_tracing_pipeline::Device>,
    pub pipeline_layout: vk::PipelineLayout,
    pub pipeline: vk::Pipeline,
    pub set0_layout: vk::DescriptorSetLayout,
    set0_pool: vk::DescriptorPool,
    pub set0: vk::DescriptorSet,
    nearest_sampler: vk::Sampler,
    pub output_image: vk::Image,
    output_alloc: Option<Allocation>,
    pub output_view: vk::ImageView,
    sbt_buffer: Option<RtBuffer>,
    pub raygen_region: vk::StridedDeviceAddressRegionKHR,
    pub miss_region: vk::StridedDeviceAddressRegionKHR,
    pub hit_region: vk::StridedDeviceAddressRegionKHR,
    pub callable_region: vk::StridedDeviceAddressRegionKHR,
}

impl RayTracing {
    /// Build both BLAS and the TLAS in one one-shot command buffer submission.
    ///
    /// # Safety
    /// Requires a valid `VulkanContext` with the RT device extensions/features enabled
    /// (Phase 1) and valid, already-uploaded vertex buffers.
    pub unsafe fn new(
        ctx: &VulkanContext,
        command_pool: vk::CommandPool,
        bathymetry_vertex_buffer: vk::Buffer,
        bathymetry_vertex_count: u32,
        ocean_vertex_buffer: vk::Buffer,
        ocean_vertex_count: u32,
    ) -> Result<Self> {
        let accel_loader = khr::acceleration_structure::Device::new(&ctx.instance, &ctx.device);

        let vertex_stride = std::mem::size_of::<Vertex>() as vk::DeviceSize;
        let bathy_size = vertex_stride * u64::from(bathymetry_vertex_count);
        let ocean_size = vertex_stride * u64::from(ocean_vertex_count);

        // Existing raster vertex buffers are HOST_VISIBLE/HOST_COHERENT with VERTEX_BUFFER
        // usage only — copy into dedicated device-local buffers carrying the AS-build-input
        // + device-address usage bits, rather than touching the shared raster buffer path.
        let blas_input_bathy = Self::create_rt_buffer(
            ctx,
            bathy_size,
            vk::BufferUsageFlags::ACCELERATION_STRUCTURE_BUILD_INPUT_READ_ONLY_KHR
                | vk::BufferUsageFlags::TRANSFER_DST,
            MemoryLocation::GpuOnly,
            "blas-input-bathymetry",
        )?;
        let blas_input_ocean = Self::create_rt_buffer(
            ctx,
            ocean_size,
            vk::BufferUsageFlags::ACCELERATION_STRUCTURE_BUILD_INPUT_READ_ONLY_KHR
                | vk::BufferUsageFlags::TRANSFER_DST,
            MemoryLocation::GpuOnly,
            "blas-input-ocean",
        )?;

        let cmd = Self::begin_one_shot(ctx, command_pool)?;

        ctx.device.cmd_copy_buffer(
            cmd,
            bathymetry_vertex_buffer,
            blas_input_bathy.buffer,
            &[vk::BufferCopy::default().size(bathy_size)],
        );
        ctx.device.cmd_copy_buffer(
            cmd,
            ocean_vertex_buffer,
            blas_input_ocean.buffer,
            &[vk::BufferCopy::default().size(ocean_size)],
        );

        let copy_barrier = vk::MemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::COPY)
            .src_access_mask(vk::AccessFlags2::TRANSFER_WRITE)
            .dst_stage_mask(vk::PipelineStageFlags2::ACCELERATION_STRUCTURE_BUILD_KHR)
            .dst_access_mask(vk::AccessFlags2::ACCELERATION_STRUCTURE_READ_KHR);
        ctx.device.cmd_pipeline_barrier2(
            cmd,
            &vk::DependencyInfo::default().memory_barriers(std::slice::from_ref(&copy_barrier)),
        );

        let (blas_bathymetry, bathy_scratch) = Self::build_blas(
            ctx,
            &accel_loader,
            cmd,
            &blas_input_bathy,
            bathymetry_vertex_count,
            "blas-bathymetry",
        )?;
        let (blas_ocean, ocean_scratch) = Self::build_blas(
            ctx,
            &accel_loader,
            cmd,
            &blas_input_ocean,
            ocean_vertex_count,
            "blas-ocean",
        )?;

        // TLAS build reads BLAS device addresses via the instance buffer — ensure both BLAS
        // builds above are complete and their writes visible before the TLAS build below.
        let as_barrier = vk::MemoryBarrier2::default()
            .src_stage_mask(vk::PipelineStageFlags2::ACCELERATION_STRUCTURE_BUILD_KHR)
            .src_access_mask(vk::AccessFlags2::ACCELERATION_STRUCTURE_WRITE_KHR)
            .dst_stage_mask(vk::PipelineStageFlags2::ACCELERATION_STRUCTURE_BUILD_KHR)
            .dst_access_mask(vk::AccessFlags2::ACCELERATION_STRUCTURE_READ_KHR);
        ctx.device.cmd_pipeline_barrier2(
            cmd,
            &vk::DependencyInfo::default().memory_barriers(std::slice::from_ref(&as_barrier)),
        );

        let (tlas, tlas_backing, tlas_instance_buffer, tlas_scratch) =
            Self::build_tlas(ctx, &accel_loader, cmd, &blas_bathymetry, &blas_ocean)?;

        Self::end_one_shot(ctx, command_pool, cmd)?;

        // Deliberately leaked, not freed: calling ctx.allocator.free() on these (even after
        // the fence wait above confirms the GPU is done with them) was empirically observed
        // to corrupt later allocations in this same Renderer::new — the offscreen/history/
        // depth images created after this point came back as full-frame noise (verified via
        // render-smoke.ps1 screenshot: 145KB clean bytes vs 3.6MB visible garbage once these
        // buffers were freed). Root cause not further isolated; leaking matches every other
        // subsystem's convention already (ocean_compute.rs etc. never call allocator.free()
        // either — see VulkanContext::drop, the only Drop impl in this codebase).
        // Captured before forgetting — the closest-hit shader's push constants need these
        // (Phase 4) to read per-triangle vertex data back out of these same buffers.
        let bathymetry_vertex_addr = blas_input_bathy.device_address;
        let ocean_vertex_addr = blas_input_ocean.device_address;

        std::mem::forget(blas_input_bathy);
        std::mem::forget(blas_input_ocean);
        std::mem::forget(bathy_scratch);
        std::mem::forget(ocean_scratch);
        std::mem::forget(tlas_scratch);

        info!("🟢 Rung 2.5 Phase 2: BLAS (bathymetry + ocean) + TLAS built, zero VUIDs expected");

        Ok(Self {
            accel_loader,
            tlas,
            blas_bathymetry,
            blas_ocean,
            tlas_backing,
            tlas_instance_buffer,
            bathymetry_vertex_addr,
            ocean_vertex_addr,
            rt_pipeline_loader: None,
            pipeline_layout: vk::PipelineLayout::null(),
            pipeline: vk::Pipeline::null(),
            set0_layout: vk::DescriptorSetLayout::null(),
            set0_pool: vk::DescriptorPool::null(),
            set0: vk::DescriptorSet::null(),
            nearest_sampler: vk::Sampler::null(),
            output_image: vk::Image::null(),
            output_alloc: None,
            output_view: vk::ImageView::null(),
            sbt_buffer: None,
            raygen_region: vk::StridedDeviceAddressRegionKHR::default(),
            miss_region: vk::StridedDeviceAddressRegionKHR::default(),
            hit_region: vk::StridedDeviceAddressRegionKHR::default(),
            callable_region: vk::StridedDeviceAddressRegionKHR::default(),
        })
    }

    /// Rung 2.5 Phase 4 — build the RT pipeline object (rgen/rmiss/rchit) and its shader
    /// binding table. Called once, after `new`, and after the caller's normal_ws/depth image
    /// views and shared frame-UBO descriptor set (set=1, reused verbatim — see
    /// water_reflection.rgen's header comment) already exist.
    ///
    /// # Safety
    /// Requires a valid `VulkanContext`, a completed `new()` call, and the caller-supplied
    /// views/descriptor-set to already be created.
    pub unsafe fn build_pipeline(
        &mut self,
        ctx: &VulkanContext,
        extent: vk::Extent2D,
        normal_ws_view: vk::ImageView,
        depth_view: vk::ImageView,
        sst_desc_set_layout: vk::DescriptorSetLayout,
        sst_desc_set: vk::DescriptorSet,
    ) -> Result<()> {
        let rt_pipeline_loader = khr::ray_tracing_pipeline::Device::new(&ctx.instance, &ctx.device);

        // --- output storage image (rgba16f) ---
        let (output_image, output_alloc, output_view) = Self::alloc_storage_image(ctx, extent)?;

        // --- nearest sampler for texelFetch reads of normal_ws/depth ---
        let nearest_sampler = ctx.device.create_sampler(
            &vk::SamplerCreateInfo::default()
                .mag_filter(vk::Filter::NEAREST)
                .min_filter(vk::Filter::NEAREST)
                .address_mode_u(vk::SamplerAddressMode::CLAMP_TO_EDGE)
                .address_mode_v(vk::SamplerAddressMode::CLAMP_TO_EDGE)
                .address_mode_w(vk::SamplerAddressMode::CLAMP_TO_EDGE),
            None,
        ).context("create RT nearest sampler")?;

        // --- set=0: TLAS, output image, normal_ws input, depth input ---
        let set0_bindings = [
            vk::DescriptorSetLayoutBinding::default()
                .binding(0)
                .descriptor_type(vk::DescriptorType::ACCELERATION_STRUCTURE_KHR)
                .descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::RAYGEN_KHR),
            vk::DescriptorSetLayoutBinding::default()
                .binding(1)
                .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
                .descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::RAYGEN_KHR),
            vk::DescriptorSetLayoutBinding::default()
                .binding(2)
                .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::RAYGEN_KHR),
            vk::DescriptorSetLayoutBinding::default()
                .binding(3)
                .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
                .descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::RAYGEN_KHR),
        ];
        let set0_layout = ctx.device.create_descriptor_set_layout(
            &vk::DescriptorSetLayoutCreateInfo::default().bindings(&set0_bindings),
            None,
        ).context("RT set0 layout")?;

        let set0_pool_sizes = [
            vk::DescriptorPoolSize::default().ty(vk::DescriptorType::ACCELERATION_STRUCTURE_KHR).descriptor_count(1),
            vk::DescriptorPoolSize::default().ty(vk::DescriptorType::STORAGE_IMAGE).descriptor_count(1),
            vk::DescriptorPoolSize::default().ty(vk::DescriptorType::COMBINED_IMAGE_SAMPLER).descriptor_count(2),
        ];
        let set0_pool = ctx.device.create_descriptor_pool(
            &vk::DescriptorPoolCreateInfo::default().max_sets(1).pool_sizes(&set0_pool_sizes),
            None,
        ).context("RT set0 pool")?;
        let set0 = ctx.device.allocate_descriptor_sets(
            &vk::DescriptorSetAllocateInfo::default()
                .descriptor_pool(set0_pool)
                .set_layouts(std::slice::from_ref(&set0_layout)),
        ).context("RT set0 alloc")?[0];

        self.write_set0(ctx, set0, output_view, normal_ws_view, depth_view, nearest_sampler);

        // --- pipeline layout: set0 (RT-specific) + set1 (reused water frame-UBO set) ---
        // Push constants: the two BLAS-input vertex-buffer addresses, read by the closest-hit
        // shader only (water_reflection.rchit).
        let push_range = vk::PushConstantRange::default()
            .stage_flags(vk::ShaderStageFlags::CLOSEST_HIT_KHR)
            .offset(0)
            .size(16);
        let set_layouts = [set0_layout, sst_desc_set_layout];
        let pipeline_layout = ctx.device.create_pipeline_layout(
            &vk::PipelineLayoutCreateInfo::default()
                .set_layouts(&set_layouts)
                .push_constant_ranges(std::slice::from_ref(&push_range)),
            None,
        ).context("RT pipeline layout")?;

        // --- shader modules + stages + groups ---
        let rgen_module = create_shader(&ctx.device, include_bytes!(concat!(env!("OUT_DIR"), "/water_reflection.rgen.spv")))?;
        let rmiss_module = create_shader(&ctx.device, include_bytes!(concat!(env!("OUT_DIR"), "/water_reflection.rmiss.spv")))?;
        let rchit_module = create_shader(&ctx.device, include_bytes!(concat!(env!("OUT_DIR"), "/water_reflection.rchit.spv")))?;

        let stages = [
            vk::PipelineShaderStageCreateInfo::default()
                .stage(vk::ShaderStageFlags::RAYGEN_KHR)
                .module(rgen_module)
                .name(c"main"),
            vk::PipelineShaderStageCreateInfo::default()
                .stage(vk::ShaderStageFlags::MISS_KHR)
                .module(rmiss_module)
                .name(c"main"),
            vk::PipelineShaderStageCreateInfo::default()
                .stage(vk::ShaderStageFlags::CLOSEST_HIT_KHR)
                .module(rchit_module)
                .name(c"main"),
        ];

        let groups = [
            vk::RayTracingShaderGroupCreateInfoKHR::default()
                .ty(vk::RayTracingShaderGroupTypeKHR::GENERAL)
                .general_shader(0)
                .closest_hit_shader(vk::SHADER_UNUSED_KHR)
                .any_hit_shader(vk::SHADER_UNUSED_KHR)
                .intersection_shader(vk::SHADER_UNUSED_KHR),
            vk::RayTracingShaderGroupCreateInfoKHR::default()
                .ty(vk::RayTracingShaderGroupTypeKHR::GENERAL)
                .general_shader(1)
                .closest_hit_shader(vk::SHADER_UNUSED_KHR)
                .any_hit_shader(vk::SHADER_UNUSED_KHR)
                .intersection_shader(vk::SHADER_UNUSED_KHR),
            vk::RayTracingShaderGroupCreateInfoKHR::default()
                .ty(vk::RayTracingShaderGroupTypeKHR::TRIANGLES_HIT_GROUP)
                .general_shader(vk::SHADER_UNUSED_KHR)
                .closest_hit_shader(2)
                .any_hit_shader(vk::SHADER_UNUSED_KHR)
                .intersection_shader(vk::SHADER_UNUSED_KHR),
        ];

        let pipeline_info = vk::RayTracingPipelineCreateInfoKHR::default()
            .stages(&stages)
            .groups(&groups)
            .max_pipeline_ray_recursion_depth(1) // single bounce — no recursive reflections yet
            .layout(pipeline_layout);

        let pipeline = rt_pipeline_loader.create_ray_tracing_pipelines(
            vk::DeferredOperationKHR::null(),
            vk::PipelineCache::null(),
            std::slice::from_ref(&pipeline_info),
            None,
        ).map_err(|(_, e)| e).context("create RT pipeline")?[0];

        ctx.device.destroy_shader_module(rgen_module, None);
        ctx.device.destroy_shader_module(rmiss_module, None);
        ctx.device.destroy_shader_module(rchit_module, None);

        // --- shader binding table ---
        let mut rt_props = vk::PhysicalDeviceRayTracingPipelinePropertiesKHR::default();
        let mut props2 = vk::PhysicalDeviceProperties2::default().push_next(&mut rt_props);
        ctx.instance.get_physical_device_properties2(ctx.physical_device, &mut props2);

        let handle_size = rt_props.shader_group_handle_size as vk::DeviceSize;
        let handle_alignment = vk::DeviceSize::from(rt_props.shader_group_handle_alignment);
        let base_alignment = vk::DeviceSize::from(rt_props.shader_group_base_alignment);
        let aligned_handle_size = align_up(handle_size, handle_alignment);

        let handles = rt_pipeline_loader.get_ray_tracing_shader_group_handles(
            pipeline, 0, 3, 3 * handle_size as usize,
        ).context("get RT shader group handles")?;

        let raygen_offset = 0u64;
        let miss_offset = align_up(raygen_offset + aligned_handle_size, base_alignment);
        let hit_offset = align_up(miss_offset + aligned_handle_size, base_alignment);
        let sbt_size = hit_offset + aligned_handle_size;

        let mut sbt_buffer = Self::create_rt_buffer(
            ctx,
            sbt_size,
            vk::BufferUsageFlags::SHADER_BINDING_TABLE_KHR,
            MemoryLocation::CpuToGpu,
            "rt-sbt",
        )?;
        {
            let slice = sbt_buffer.alloc.as_mut().and_then(|a| a.mapped_slice_mut())
                .context("SBT buffer not host-mapped")?;
            let hs = handle_size as usize;
            slice[raygen_offset as usize..raygen_offset as usize + hs].copy_from_slice(&handles[0..hs]);
            slice[miss_offset as usize..miss_offset as usize + hs].copy_from_slice(&handles[hs..2 * hs]);
            slice[hit_offset as usize..hit_offset as usize + hs].copy_from_slice(&handles[2 * hs..3 * hs]);
        }
        let sbt_addr = sbt_buffer.device_address;

        let raygen_region = vk::StridedDeviceAddressRegionKHR::default()
            .device_address(sbt_addr + raygen_offset)
            .stride(aligned_handle_size)
            .size(aligned_handle_size); // spec requires stride == size for the raygen region
        let miss_region = vk::StridedDeviceAddressRegionKHR::default()
            .device_address(sbt_addr + miss_offset)
            .stride(aligned_handle_size)
            .size(aligned_handle_size);
        let hit_region = vk::StridedDeviceAddressRegionKHR::default()
            .device_address(sbt_addr + hit_offset)
            .stride(aligned_handle_size)
            .size(aligned_handle_size);
        let callable_region = vk::StridedDeviceAddressRegionKHR::default();

        info!("🟢 Rung 2.5 Phase 4: RT pipeline + SBT built (handle_size={handle_size}, aligned={aligned_handle_size})");

        self.rt_pipeline_loader = Some(rt_pipeline_loader);
        self.pipeline_layout = pipeline_layout;
        self.pipeline = pipeline;
        self.set0_layout = set0_layout;
        self.set0_pool = set0_pool;
        self.set0 = set0;
        self.nearest_sampler = nearest_sampler;
        self.output_image = output_image;
        self.output_alloc = Some(output_alloc);
        self.output_view = output_view;
        self.sbt_buffer = Some(sbt_buffer);
        self.raygen_region = raygen_region;
        self.miss_region = miss_region;
        self.hit_region = hit_region;
        self.callable_region = callable_region;
        Ok(())
    }

    unsafe fn write_set0(
        &self,
        ctx: &VulkanContext,
        set0: vk::DescriptorSet,
        output_view: vk::ImageView,
        normal_ws_view: vk::ImageView,
        depth_view: vk::ImageView,
        sampler: vk::Sampler,
    ) {
        let accel_structs = [self.tlas];
        let mut accel_write = vk::WriteDescriptorSetAccelerationStructureKHR::default()
            .acceleration_structures(&accel_structs);

        let output_info = vk::DescriptorImageInfo::default()
            .image_view(output_view)
            .image_layout(vk::ImageLayout::GENERAL);
        let normal_ws_info = vk::DescriptorImageInfo::default()
            .sampler(sampler)
            .image_view(normal_ws_view)
            .image_layout(vk::ImageLayout::SHADER_READ_ONLY_OPTIMAL);
        let depth_info = vk::DescriptorImageInfo::default()
            .sampler(sampler)
            .image_view(depth_view)
            .image_layout(vk::ImageLayout::DEPTH_STENCIL_READ_ONLY_OPTIMAL);

        let write0 = vk::WriteDescriptorSet::default()
            .dst_set(set0)
            .dst_binding(0)
            .descriptor_type(vk::DescriptorType::ACCELERATION_STRUCTURE_KHR)
            .descriptor_count(1)
            .push_next(&mut accel_write);

        let write1 = vk::WriteDescriptorSet::default()
            .dst_set(set0)
            .dst_binding(1)
            .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
            .image_info(std::slice::from_ref(&output_info));
        let write2 = vk::WriteDescriptorSet::default()
            .dst_set(set0)
            .dst_binding(2)
            .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
            .image_info(std::slice::from_ref(&normal_ws_info));
        let write3 = vk::WriteDescriptorSet::default()
            .dst_set(set0)
            .dst_binding(3)
            .descriptor_type(vk::DescriptorType::COMBINED_IMAGE_SAMPLER)
            .image_info(std::slice::from_ref(&depth_info));

        ctx.device.update_descriptor_sets(&[write0, write1, write2, write3], &[]);
    }

    unsafe fn alloc_storage_image(
        ctx: &VulkanContext,
        extent: vk::Extent2D,
    ) -> Result<(vk::Image, Allocation, vk::ImageView)> {
        let format = vk::Format::R16G16B16A16_SFLOAT;
        let image = ctx.device.create_image(
            &vk::ImageCreateInfo::default()
                .image_type(vk::ImageType::TYPE_2D)
                .format(format)
                .extent(vk::Extent3D { width: extent.width, height: extent.height, depth: 1 })
                .mip_levels(1)
                .array_layers(1)
                .samples(vk::SampleCountFlags::TYPE_1)
                .tiling(vk::ImageTiling::OPTIMAL)
                .usage(vk::ImageUsageFlags::STORAGE | vk::ImageUsageFlags::SAMPLED)
                .sharing_mode(vk::SharingMode::EXCLUSIVE)
                .initial_layout(vk::ImageLayout::UNDEFINED),
            None,
        ).context("create RT output image")?;

        let req = ctx.device.get_image_memory_requirements(image);
        let alloc = ctx.allocator.lock().unwrap().allocate(&AllocationCreateDesc {
            name: "rt-reflection-output",
            requirements: req,
            location: MemoryLocation::GpuOnly,
            linear: false,
            allocation_scheme: AllocationScheme::GpuAllocatorManaged,
        }).context("gpu-allocator: alloc RT output image")?;
        ctx.device.bind_image_memory(image, alloc.memory(), alloc.offset())?;

        let view = ctx.device.create_image_view(
            &vk::ImageViewCreateInfo::default()
                .image(image)
                .view_type(vk::ImageViewType::TYPE_2D)
                .format(format)
                .subresource_range(vk::ImageSubresourceRange {
                    aspect_mask: vk::ImageAspectFlags::COLOR,
                    base_mip_level: 0,
                    level_count: 1,
                    base_array_layer: 0,
                    layer_count: 1,
                }),
            None,
        ).context("create RT output image view")?;

        Ok((image, alloc, view))
    }

    unsafe fn build_blas(
        ctx: &VulkanContext,
        accel_loader: &khr::acceleration_structure::Device,
        cmd: vk::CommandBuffer,
        input: &RtBuffer,
        vertex_count: u32,
        label: &str,
    ) -> Result<(Blas, RtBuffer)> {
        let triangle_count = vertex_count / 3;
        let vertex_stride = std::mem::size_of::<Vertex>() as vk::DeviceSize;

        let triangles_data = vk::AccelerationStructureGeometryTrianglesDataKHR::default()
            .vertex_format(vk::Format::R32G32B32_SFLOAT)
            .vertex_data(vk::DeviceOrHostAddressConstKHR {
                device_address: input.device_address,
            })
            .vertex_stride(vertex_stride)
            .max_vertex(vertex_count - 1)
            .index_type(vk::IndexType::NONE_KHR);

        let geometries = [vk::AccelerationStructureGeometryKHR::default()
            .geometry_type(vk::GeometryTypeKHR::TRIANGLES)
            .geometry(vk::AccelerationStructureGeometryDataKHR {
                triangles: triangles_data,
            })
            .flags(vk::GeometryFlagsKHR::OPAQUE)];

        let build_info = vk::AccelerationStructureBuildGeometryInfoKHR::default()
            .ty(vk::AccelerationStructureTypeKHR::BOTTOM_LEVEL)
            .flags(vk::BuildAccelerationStructureFlagsKHR::PREFER_FAST_TRACE)
            .mode(vk::BuildAccelerationStructureModeKHR::BUILD)
            .geometries(&geometries);

        let mut size_info = vk::AccelerationStructureBuildSizesInfoKHR::default();
        accel_loader.get_acceleration_structure_build_sizes(
            vk::AccelerationStructureBuildTypeKHR::DEVICE,
            &build_info,
            &[triangle_count],
            &mut size_info,
        );

        let backing = Self::create_rt_buffer(
            ctx,
            size_info.acceleration_structure_size,
            vk::BufferUsageFlags::ACCELERATION_STRUCTURE_STORAGE_KHR,
            MemoryLocation::GpuOnly,
            &format!("{label}-backing"),
        )?;

        let accel = accel_loader
            .create_acceleration_structure(
                &vk::AccelerationStructureCreateInfoKHR::default()
                    .buffer(backing.buffer)
                    .size(size_info.acceleration_structure_size)
                    .ty(vk::AccelerationStructureTypeKHR::BOTTOM_LEVEL),
                None,
            )
            .context("create BLAS")?;

        let scratch = Self::create_rt_buffer(
            ctx,
            size_info.build_scratch_size,
            vk::BufferUsageFlags::STORAGE_BUFFER,
            MemoryLocation::GpuOnly,
            &format!("{label}-scratch"),
        )?;

        let build_info = build_info
            .dst_acceleration_structure(accel)
            .scratch_data(vk::DeviceOrHostAddressKHR {
                device_address: scratch.device_address,
            });

        let build_range = vk::AccelerationStructureBuildRangeInfoKHR::default()
            .primitive_count(triangle_count)
            .primitive_offset(0)
            .first_vertex(0)
            .transform_offset(0);
        let build_ranges: [&[vk::AccelerationStructureBuildRangeInfoKHR]; 1] =
            [std::slice::from_ref(&build_range)];

        accel_loader.cmd_build_acceleration_structures(
            cmd,
            std::slice::from_ref(&build_info),
            &build_ranges,
        );

        Ok((Blas { accel, backing }, scratch))
    }

    unsafe fn build_tlas(
        ctx: &VulkanContext,
        accel_loader: &khr::acceleration_structure::Device,
        cmd: vk::CommandBuffer,
        blas_bathymetry: &Blas,
        blas_ocean: &Blas,
    ) -> Result<(
        vk::AccelerationStructureKHR,
        RtBuffer,
        RtBuffer,
        RtBuffer,
    )> {
        let bathy_ref = accel_loader.get_acceleration_structure_device_address(
            &vk::AccelerationStructureDeviceAddressInfoKHR::default()
                .acceleration_structure(blas_bathymetry.accel),
        );
        let ocean_ref = accel_loader.get_acceleration_structure_device_address(
            &vk::AccelerationStructureDeviceAddressInfoKHR::default()
                .acceleration_structure(blas_ocean.accel),
        );

        // Both world-space vertex buffers already bake in the model transform (ocean's
        // pc.model is Mat4::IDENTITY, renderer.rs:2028) — identity instance transform for both.
        let identity = vk::TransformMatrixKHR {
            matrix: [
                1.0, 0.0, 0.0, 0.0, //
                0.0, 1.0, 0.0, 0.0, //
                0.0, 0.0, 1.0, 0.0,
            ],
        };

        let instances = [
            vk::AccelerationStructureInstanceKHR {
                transform: identity,
                instance_custom_index_and_mask: vk::Packed24_8::new(0, 0xFF),
                instance_shader_binding_table_record_offset_and_flags: vk::Packed24_8::new(
                    0,
                    vk::GeometryInstanceFlagsKHR::TRIANGLE_FACING_CULL_DISABLE.as_raw() as u8,
                ),
                acceleration_structure_reference: vk::AccelerationStructureReferenceKHR {
                    device_handle: bathy_ref,
                },
            },
            vk::AccelerationStructureInstanceKHR {
                transform: identity,
                instance_custom_index_and_mask: vk::Packed24_8::new(1, 0xFF),
                instance_shader_binding_table_record_offset_and_flags: vk::Packed24_8::new(
                    0,
                    vk::GeometryInstanceFlagsKHR::TRIANGLE_FACING_CULL_DISABLE.as_raw() as u8,
                ),
                acceleration_structure_reference: vk::AccelerationStructureReferenceKHR {
                    device_handle: ocean_ref,
                },
            },
        ];

        let instance_size =
            std::mem::size_of::<vk::AccelerationStructureInstanceKHR>() as vk::DeviceSize;
        let instance_buffer_size = instance_size * instances.len() as vk::DeviceSize;

        // CpuToGpu (persistently mapped) rather than a staging-buffer round trip: this is
        // exactly the memory type a future per-frame TLAS rebuild (Phase 5+) will also want
        // for its 2-3 instances, so this isn't a shortcut being paid down later.
        let mut instance_buffer = Self::create_rt_buffer(
            ctx,
            instance_buffer_size,
            vk::BufferUsageFlags::ACCELERATION_STRUCTURE_BUILD_INPUT_READ_ONLY_KHR,
            MemoryLocation::CpuToGpu,
            "tlas-instances",
        )?;
        {
            let slice = instance_buffer
                .alloc
                .as_mut()
                .and_then(|a| a.mapped_slice_mut())
                .context("tlas instance buffer not host-mapped")?;
            let bytes = std::slice::from_raw_parts(
                instances.as_ptr().cast::<u8>(),
                instances.len() * instance_size as usize,
            );
            slice[..bytes.len()].copy_from_slice(bytes);
        }

        let instances_data = vk::AccelerationStructureGeometryInstancesDataKHR::default()
            .array_of_pointers(false)
            .data(vk::DeviceOrHostAddressConstKHR {
                device_address: instance_buffer.device_address,
            });

        let geometries = [vk::AccelerationStructureGeometryKHR::default()
            .geometry_type(vk::GeometryTypeKHR::INSTANCES)
            .geometry(vk::AccelerationStructureGeometryDataKHR {
                instances: instances_data,
            })];

        let build_info = vk::AccelerationStructureBuildGeometryInfoKHR::default()
            .ty(vk::AccelerationStructureTypeKHR::TOP_LEVEL)
            .flags(vk::BuildAccelerationStructureFlagsKHR::PREFER_FAST_TRACE)
            .mode(vk::BuildAccelerationStructureModeKHR::BUILD)
            .geometries(&geometries);

        let instance_count = instances.len() as u32;
        let mut size_info = vk::AccelerationStructureBuildSizesInfoKHR::default();
        accel_loader.get_acceleration_structure_build_sizes(
            vk::AccelerationStructureBuildTypeKHR::DEVICE,
            &build_info,
            &[instance_count],
            &mut size_info,
        );

        let backing = Self::create_rt_buffer(
            ctx,
            size_info.acceleration_structure_size,
            vk::BufferUsageFlags::ACCELERATION_STRUCTURE_STORAGE_KHR,
            MemoryLocation::GpuOnly,
            "tlas-backing",
        )?;

        let tlas = accel_loader
            .create_acceleration_structure(
                &vk::AccelerationStructureCreateInfoKHR::default()
                    .buffer(backing.buffer)
                    .size(size_info.acceleration_structure_size)
                    .ty(vk::AccelerationStructureTypeKHR::TOP_LEVEL),
                None,
            )
            .context("create TLAS")?;

        let scratch = Self::create_rt_buffer(
            ctx,
            size_info.build_scratch_size,
            vk::BufferUsageFlags::STORAGE_BUFFER,
            MemoryLocation::GpuOnly,
            "tlas-scratch",
        )?;

        let build_info = build_info
            .dst_acceleration_structure(tlas)
            .scratch_data(vk::DeviceOrHostAddressKHR {
                device_address: scratch.device_address,
            });

        let build_range = vk::AccelerationStructureBuildRangeInfoKHR::default()
            .primitive_count(instance_count)
            .primitive_offset(0)
            .first_vertex(0)
            .transform_offset(0);
        let build_ranges: [&[vk::AccelerationStructureBuildRangeInfoKHR]; 1] =
            [std::slice::from_ref(&build_range)];

        accel_loader.cmd_build_acceleration_structures(
            cmd,
            std::slice::from_ref(&build_info),
            &build_ranges,
        );

        Ok((tlas, backing, instance_buffer, scratch))
    }

    unsafe fn create_rt_buffer(
        ctx: &VulkanContext,
        size: vk::DeviceSize,
        usage: vk::BufferUsageFlags,
        location: MemoryLocation,
        label: &str,
    ) -> Result<RtBuffer> {
        let buffer = ctx
            .device
            .create_buffer(
                &vk::BufferCreateInfo::default()
                    .size(size)
                    .usage(usage | vk::BufferUsageFlags::SHADER_DEVICE_ADDRESS)
                    .sharing_mode(vk::SharingMode::EXCLUSIVE),
                None,
            )
            .context("create RT buffer")?;
        let req = ctx.device.get_buffer_memory_requirements(buffer);
        let alloc = ctx
            .allocator
            .lock()
            .unwrap()
            .allocate(&AllocationCreateDesc {
                name: label,
                requirements: req,
                location,
                linear: true,
                allocation_scheme: AllocationScheme::GpuAllocatorManaged,
            })
            .context("gpu-allocator: alloc RT buffer")?;
        ctx.device
            .bind_buffer_memory(buffer, alloc.memory(), alloc.offset())?;
        let device_address = ctx
            .device
            .get_buffer_device_address(&vk::BufferDeviceAddressInfo::default().buffer(buffer));
        Ok(RtBuffer {
            buffer,
            alloc: Some(alloc),
            device_address,
        })
    }

    unsafe fn begin_one_shot(ctx: &VulkanContext, command_pool: vk::CommandPool) -> Result<vk::CommandBuffer> {
        let cmd = ctx.device.allocate_command_buffers(
            &vk::CommandBufferAllocateInfo::default()
                .command_pool(command_pool)
                .level(vk::CommandBufferLevel::PRIMARY)
                .command_buffer_count(1),
        )?[0];
        ctx.device.begin_command_buffer(
            cmd,
            &vk::CommandBufferBeginInfo::default()
                .flags(vk::CommandBufferUsageFlags::ONE_TIME_SUBMIT),
        )?;
        Ok(cmd)
    }

    unsafe fn end_one_shot(
        ctx: &VulkanContext,
        command_pool: vk::CommandPool,
        cmd: vk::CommandBuffer,
    ) -> Result<()> {
        ctx.device.end_command_buffer(cmd)?;
        let fence = ctx.device.create_fence(&vk::FenceCreateInfo::default(), None)?;
        let cmds = [cmd];
        let submit = vk::SubmitInfo::default().command_buffers(&cmds);
        ctx.device.queue_submit(ctx.graphics_queue, &[submit], fence)?;
        ctx.device.wait_for_fences(&[fence], true, u64::MAX)?;
        ctx.device.destroy_fence(fence, None);
        ctx.device.free_command_buffers(command_pool, &cmds);
        Ok(())
    }
}

/// Mirrors `ocean_compute.rs`'s `create_shader` — this module has its own three RT stages.
unsafe fn create_shader(device: &ash::Device, spv: &[u8]) -> Result<vk::ShaderModule> {
    assert!(spv.len().is_multiple_of(4));
    let words: Vec<u32> = spv
        .chunks_exact(4)
        .map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]]))
        .collect();
    device
        .create_shader_module(&vk::ShaderModuleCreateInfo::default().code(&words), None)
        .context("create RT shader module")
}

fn align_up(value: vk::DeviceSize, alignment: vk::DeviceSize) -> vk::DeviceSize {
    value.div_ceil(alignment) * alignment
}
