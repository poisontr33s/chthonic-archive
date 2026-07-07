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
        })
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
