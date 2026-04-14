// tools/ankh-forge/src/trail/gpu.rs
//
// Vulkan compute context for GPU-path runestone decompression.
// Initialised once per `trail execute` invocation; single compute dispatch.
//
// Decompressor shader: trail_decompress.comp.glsl (compiled to SPIR-V at build time).
// GPU stones are self-decoding: the SPIR-V is extracted from the stone itself,
// not from a hardcoded binary. This module accepts any compatible SPIR-V bytes.

use anyhow::{bail, Context, Result};
use ash::vk;
use gpu_allocator::{MemoryLocation, vulkan as vk_alloc};

pub struct GpuContext {
    _entry: ash::Entry,
    _instance: ash::Instance,
    device: ash::Device,
    queue: vk::Queue,
    allocator: vk_alloc::Allocator,
    descriptor_set_layout: vk::DescriptorSetLayout,
    pipeline_layout: vk::PipelineLayout,
    pipeline: vk::Pipeline,
    descriptor_pool: vk::DescriptorPool,
    command_pool: vk::CommandPool,
}

impl GpuContext {
    /// Load Vulkan, select a compute-capable device, and build the compute pipeline
    /// from the provided `spirv` bytes (extracted from the stone's SPIRV block).
    pub fn init(spirv: &[u8]) -> Result<Self> {
        if spirv.len() % 4 != 0 {
            bail!("SPIRV length {} is not 4-byte aligned", spirv.len());
        }

        // 1. Load Vulkan loader at runtime (no compile-time SDK link).
        let entry = unsafe { ash::Entry::load() }
            .context("failed to load Vulkan loader — is a Vulkan driver installed?")?;

        // 2. Instance (no extensions needed for headless compute).
        let app_info = vk::ApplicationInfo::default()
            .application_name(c"ankh-forge")
            .api_version(vk::API_VERSION_1_3);
        let instance_info = vk::InstanceCreateInfo::default()
            .application_info(&app_info);
        let instance = unsafe { entry.create_instance(&instance_info, None) }
            .context("failed to create Vulkan instance")?;

        // 3. Physical device: prefer discrete GPU with a compute queue.
        let physical_devices = unsafe { instance.enumerate_physical_devices() }
            .context("failed to enumerate physical devices")?;
        if physical_devices.is_empty() {
            bail!("no Vulkan-capable devices found");
        }
        let (physical_device, queue_family_index) =
            select_compute_device(&instance, &physical_devices)?;

        // 4. Logical device + compute queue.
        let queue_priority = 1.0f32;
        let queue_info = vk::DeviceQueueCreateInfo::default()
            .queue_family_index(queue_family_index)
            .queue_priorities(std::slice::from_ref(&queue_priority));
        let device_info = vk::DeviceCreateInfo::default()
            .queue_create_infos(std::slice::from_ref(&queue_info));
        let device = unsafe { instance.create_device(physical_device, &device_info, None) }
            .context("failed to create logical device")?;
        let queue = unsafe { device.get_device_queue(queue_family_index, 0) };

        // 5. GPU memory allocator.
        let allocator = vk_alloc::Allocator::new(&vk_alloc::AllocatorCreateDesc {
            instance: instance.clone(),
            device: device.clone(),
            physical_device,
            debug_settings: Default::default(),
            buffer_device_address: false,
            allocation_sizes: Default::default(),
        })
        .context("failed to create GPU allocator")?;

        // 6. Descriptor set layout: 3 STORAGE_BUFFER bindings.
        //    binding 0 = CompressedData (src, readonly in shader)
        //    binding 1 = DecompressedData (dst, readwrite)
        //    binding 2 = Metadata (sizes)
        let bindings = [
            vk::DescriptorSetLayoutBinding::default()
                .binding(0)
                .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
                .descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::COMPUTE),
            vk::DescriptorSetLayoutBinding::default()
                .binding(1)
                .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
                .descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::COMPUTE),
            vk::DescriptorSetLayoutBinding::default()
                .binding(2)
                .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
                .descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::COMPUTE),
        ];
        let layout_info =
            vk::DescriptorSetLayoutCreateInfo::default().bindings(&bindings);
        let descriptor_set_layout =
            unsafe { device.create_descriptor_set_layout(&layout_info, None) }
                .context("failed to create descriptor set layout")?;

        // 7. Pipeline layout.
        let pipeline_layout_info = vk::PipelineLayoutCreateInfo::default()
            .set_layouts(std::slice::from_ref(&descriptor_set_layout));
        let pipeline_layout =
            unsafe { device.create_pipeline_layout(&pipeline_layout_info, None) }
                .context("failed to create pipeline layout")?;

        // 8. Shader module from stone-embedded SPIR-V.
        let spirv_words: Vec<u32> = spirv
            .chunks_exact(4)
            .map(|b| u32::from_le_bytes(b.try_into().unwrap()))
            .collect();
        let shader_info = vk::ShaderModuleCreateInfo::default().code(&spirv_words);
        let shader_module = unsafe { device.create_shader_module(&shader_info, None) }
            .context("failed to create shader module")?;

        // 9. Compute pipeline.
        let stage = vk::PipelineShaderStageCreateInfo::default()
            .stage(vk::ShaderStageFlags::COMPUTE)
            .module(shader_module)
            .name(c"main");
        let pipeline_info = vk::ComputePipelineCreateInfo::default()
            .stage(stage)
            .layout(pipeline_layout);
        let pipeline = unsafe {
            device
                .create_compute_pipelines(vk::PipelineCache::null(), &[pipeline_info], None)
                .map_err(|(_, e)| anyhow::anyhow!("create_compute_pipelines: {e}"))?
        }[0];

        // Shader module no longer needed once the pipeline is compiled.
        unsafe { device.destroy_shader_module(shader_module, None) };

        // 10. Descriptor pool (1 set, 3 STORAGE_BUFFER descriptors).
        let pool_size = vk::DescriptorPoolSize::default()
            .ty(vk::DescriptorType::STORAGE_BUFFER)
            .descriptor_count(3);
        let pool_info = vk::DescriptorPoolCreateInfo::default()
            .max_sets(1)
            .pool_sizes(std::slice::from_ref(&pool_size));
        let descriptor_pool = unsafe { device.create_descriptor_pool(&pool_info, None) }
            .context("failed to create descriptor pool")?;

        // 11. Command pool (transient: single-use command buffers).
        let cmd_pool_info = vk::CommandPoolCreateInfo::default()
            .queue_family_index(queue_family_index)
            .flags(vk::CommandPoolCreateFlags::TRANSIENT);
        let command_pool = unsafe { device.create_command_pool(&cmd_pool_info, None) }
            .context("failed to create command pool")?;

        Ok(GpuContext {
            _entry: entry,
            _instance: instance,
            device,
            queue,
            allocator,
            descriptor_set_layout,
            pipeline_layout,
            pipeline,
            descriptor_pool,
            command_pool,
        })
    }

    /// GPU-decompress `compressed` (LZ4 block) into `uncompressed_size` bytes.
    ///
    /// Allocates HOST_VISIBLE src/dst/meta buffers, dispatches vkCmdDispatch(1,1,1),
    /// waits on a fence, then maps and returns the decompressed bytes.
    pub fn execute(&mut self, compressed: &[u8], uncompressed_size: u32) -> Result<Vec<u8>> {
        // Clone the device handle (ash Device is a shallow clone of the Vulkan handle).
        // This lets us call &mut self methods (create_buffer) while still holding
        // an owned ash::Device for descriptor/command operations below.
        let device = self.device.clone();

        // Buffer sizes padded to uint[] alignment (4 bytes).
        let src_size  = pad4(compressed.len()).max(4) as u64;
        let dst_size  = pad4(uncompressed_size as usize).max(4) as u64;
        let meta_size = 8u64; // two u32: compressed_size + uncompressed_size

        // ── Allocate buffers ──────────────────────────────────────────────────

        let (src_buf, src_alloc) = self.create_buffer(
            src_size,
            vk::BufferUsageFlags::STORAGE_BUFFER,
            MemoryLocation::CpuToGpu,
            "trail_src",
        )?;
        let (dst_buf, dst_alloc) = self.create_buffer(
            dst_size,
            vk::BufferUsageFlags::STORAGE_BUFFER,
            MemoryLocation::GpuToCpu,
            "trail_dst",
        )?;
        let (meta_buf, meta_alloc) = self.create_buffer(
            meta_size,
            vk::BufferUsageFlags::STORAGE_BUFFER,
            MemoryLocation::CpuToGpu,
            "trail_meta",
        )?;

        // ── Write input data ──────────────────────────────────────────────────

        {
            let ptr = src_alloc
                .mapped_ptr()
                .context("src buffer is not HOST_VISIBLE — cannot map")?;
            unsafe {
                std::ptr::copy_nonoverlapping(
                    compressed.as_ptr(),
                    ptr.as_ptr() as *mut u8,
                    compressed.len(),
                );
            }
        }
        {
            let ptr = meta_alloc
                .mapped_ptr()
                .context("meta buffer is not HOST_VISIBLE")?;
            let meta_bytes = {
                let mut b = [0u8; 8];
                b[0..4].copy_from_slice(&(compressed.len() as u32).to_le_bytes());
                b[4..8].copy_from_slice(&uncompressed_size.to_le_bytes());
                b
            };
            unsafe {
                std::ptr::copy_nonoverlapping(
                    meta_bytes.as_ptr(),
                    ptr.as_ptr() as *mut u8,
                    8,
                );
            }
        }

        // ── Descriptor set ────────────────────────────────────────────────────

        let alloc_info = vk::DescriptorSetAllocateInfo::default()
            .descriptor_pool(self.descriptor_pool)
            .set_layouts(std::slice::from_ref(&self.descriptor_set_layout));
        let descriptor_set = unsafe { device.allocate_descriptor_sets(&alloc_info) }
            .context("failed to allocate descriptor set")?[0];

        let src_bi  = vk::DescriptorBufferInfo::default().buffer(src_buf) .offset(0).range(vk::WHOLE_SIZE);
        let dst_bi  = vk::DescriptorBufferInfo::default().buffer(dst_buf) .offset(0).range(vk::WHOLE_SIZE);
        let meta_bi = vk::DescriptorBufferInfo::default().buffer(meta_buf).offset(0).range(vk::WHOLE_SIZE);

        let writes = [
            vk::WriteDescriptorSet::default()
                .dst_set(descriptor_set).dst_binding(0)
                .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
                .buffer_info(std::slice::from_ref(&src_bi)),
            vk::WriteDescriptorSet::default()
                .dst_set(descriptor_set).dst_binding(1)
                .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
                .buffer_info(std::slice::from_ref(&dst_bi)),
            vk::WriteDescriptorSet::default()
                .dst_set(descriptor_set).dst_binding(2)
                .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
                .buffer_info(std::slice::from_ref(&meta_bi)),
        ];
        unsafe { device.update_descriptor_sets(&writes, &[]) };

        // ── Record command buffer ─────────────────────────────────────────────

        let cmd_alloc_info = vk::CommandBufferAllocateInfo::default()
            .command_pool(self.command_pool)
            .level(vk::CommandBufferLevel::PRIMARY)
            .command_buffer_count(1);
        let cmd = unsafe { device.allocate_command_buffers(&cmd_alloc_info) }
            .context("failed to allocate command buffer")?[0];

        let begin_info = vk::CommandBufferBeginInfo::default()
            .flags(vk::CommandBufferUsageFlags::ONE_TIME_SUBMIT);
        unsafe { device.begin_command_buffer(cmd, &begin_info) }
            .context("begin_command_buffer")?;

        unsafe {
            device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::COMPUTE, self.pipeline);
            device.cmd_bind_descriptor_sets(
                cmd,
                vk::PipelineBindPoint::COMPUTE,
                self.pipeline_layout,
                0,
                &[descriptor_set],
                &[],
            );
            device.cmd_dispatch(cmd, 1, 1, 1);

            // Memory barrier: COMPUTE_SHADER writes → HOST reads.
            // Ensures decompressed bytes are visible after the fence signals.
            let barrier = vk::MemoryBarrier::default()
                .src_access_mask(vk::AccessFlags::SHADER_WRITE)
                .dst_access_mask(vk::AccessFlags::HOST_READ);
            device.cmd_pipeline_barrier(
                cmd,
                vk::PipelineStageFlags::COMPUTE_SHADER,
                vk::PipelineStageFlags::HOST,
                vk::DependencyFlags::empty(),
                &[barrier],
                &[],
                &[],
            );
        }

        unsafe { device.end_command_buffer(cmd) }.context("end_command_buffer")?;

        // ── Submit and wait ───────────────────────────────────────────────────

        let submit_info = vk::SubmitInfo::default()
            .command_buffers(std::slice::from_ref(&cmd));
        let fence = unsafe { device.create_fence(&vk::FenceCreateInfo::default(), None) }
            .context("create_fence")?;

        unsafe { device.queue_submit(self.queue, &[submit_info], fence) }
            .context("queue_submit")?;

        // 10-second timeout — more than enough for a single-block decompress.
        unsafe { device.wait_for_fences(&[fence], true, 10_000_000_000) }
            .context("GPU decompression timed out (>10s)")?;

        // ── Read back result ──────────────────────────────────────────────────

        let result = {
            let ptr = dst_alloc
                .mapped_ptr()
                .context("dst buffer is not HOST_VISIBLE — cannot read back")?;
            let slice = unsafe {
                std::slice::from_raw_parts(
                    ptr.as_ptr() as *const u8,
                    uncompressed_size as usize,
                )
            };
            slice.to_vec()
        };

        // ── Cleanup (per-execute resources) ───────────────────────────────────

        unsafe {
            device.destroy_fence(fence, None);
            device.free_command_buffers(self.command_pool, &[cmd]);
            // Buffers destroyed before freeing allocations (Vulkan requirement).
            device.destroy_buffer(src_buf, None);
            device.destroy_buffer(dst_buf, None);
            device.destroy_buffer(meta_buf, None);
        }

        self.allocator.free(src_alloc).context("free src_alloc")?;
        self.allocator.free(dst_alloc).context("free dst_alloc")?;
        self.allocator.free(meta_alloc).context("free meta_alloc")?;

        // Reset the descriptor pool so it can be reused on the next call.
        unsafe {
            device.reset_descriptor_pool(
                self.descriptor_pool,
                vk::DescriptorPoolResetFlags::empty(),
            )
        }
        .context("reset_descriptor_pool")?;

        Ok(result)
    }

    /// Allocate a Vulkan buffer + bind GPU memory from gpu-allocator.
    fn create_buffer(
        &mut self,
        size: u64,
        usage: vk::BufferUsageFlags,
        location: MemoryLocation,
        name: &str,
    ) -> Result<(vk::Buffer, vk_alloc::Allocation)> {
        let buffer_info = vk::BufferCreateInfo::default()
            .size(size)
            .usage(usage)
            .sharing_mode(vk::SharingMode::EXCLUSIVE);
        let buffer = unsafe { self.device.create_buffer(&buffer_info, None) }
            .with_context(|| format!("create_buffer({name})"))?;

        let requirements =
            unsafe { self.device.get_buffer_memory_requirements(buffer) };

        let alloc = self
            .allocator
            .allocate(&vk_alloc::AllocationCreateDesc {
                name,
                requirements,
                location,
                linear: true,
                allocation_scheme: vk_alloc::AllocationScheme::GpuAllocatorManaged,
            })
            .with_context(|| format!("allocate({name})"))?;

        unsafe {
            self.device
                .bind_buffer_memory(buffer, alloc.memory(), alloc.offset())
        }
        .with_context(|| format!("bind_buffer_memory({name})"))?;

        Ok((buffer, alloc))
    }
}

// GpuContext intentionally has no Drop impl: ankh-forge is a short-lived CLI
// process. Vulkan handles are released by the driver on process exit.
// A future server/daemon mode would need explicit destroy ordering here.

/// Select the best Vulkan physical device for headless compute.
/// Prefers a discrete GPU; falls back to any device with a compute queue.
fn select_compute_device(
    instance: &ash::Instance,
    physical_devices: &[vk::PhysicalDevice],
) -> Result<(vk::PhysicalDevice, u32)> {
    let mut best: Option<(vk::PhysicalDevice, u32, bool)> = None; // (device, qfi, is_discrete)

    for &pd in physical_devices {
        let props = unsafe { instance.get_physical_device_properties(pd) };
        let queue_props =
            unsafe { instance.get_physical_device_queue_family_properties(pd) };

        let Some(qfi) = queue_props
            .iter()
            .position(|qp| qp.queue_flags.contains(vk::QueueFlags::COMPUTE))
        else {
            continue;
        };

        let is_discrete = props.device_type == vk::PhysicalDeviceType::DISCRETE_GPU;

        match &best {
            None => best = Some((pd, qfi as u32, is_discrete)),
            Some((_, _, was_discrete)) if is_discrete && !was_discrete => {
                best = Some((pd, qfi as u32, is_discrete));
            }
            _ => {}
        }
    }

    let (pd, qfi, _) = best.context("no Vulkan device with a compute queue found")?;
    Ok((pd, qfi))
}

/// Round `n` up to the next multiple of 4 (for `uint[]` buffer alignment).
fn pad4(n: usize) -> usize {
    (n + 3) & !3
}
