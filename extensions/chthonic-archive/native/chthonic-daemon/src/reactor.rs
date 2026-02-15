use std::time::Instant;

use anyhow::{Context, Result};

use crate::types::{SedimentRequest, SedimentResult, SedimentVertex};

#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct SedimentInput {
    pub entropy: f32,
    pub change_frequency: f32,
    pub recency: f32,
    pub author_diversity: f32,
    pub file_index: u32,
    pub layer_depth: u32,
    pub complexity: f32,
    pub _padding: f32,
}

/// Push constants for the compute shader.
#[repr(C)]
#[derive(Debug, Clone, Copy)]
struct PushConstants {
    total_files: u32,
    time_scale: f32,
    entropy_scale: f32,
    layer_gap: f32,
}

/// The Vulkan reactor. Holds all GPU resources for headless compute.
pub struct VulkanReactor {
    _entry: ash::Entry,
    instance: ash::Instance,
    device: ash::Device,
    _compute_queue: ash::vk::Queue,
    _compute_family_index: u32,
    descriptor_set_layout: ash::vk::DescriptorSetLayout,
    pipeline_layout: ash::vk::PipelineLayout,
    pipeline: ash::vk::Pipeline,
    command_pool: ash::vk::CommandPool,
    _spirv: Vec<u32>,
}

impl VulkanReactor {
    /// Compute sediment layers from git history.
    ///
    /// Walks the repository's commit graph via `gix`, extracts per-file
    /// metrics, dispatches the GPU compute shader, reads back vertex data.
    /// Falls back to CPU if any GPU step fails.
    pub fn compute_sediment(
        &self,
        workspace: &str,
        request: &SedimentRequest,
    ) -> Result<SedimentResult> {
        let start = Instant::now();
        let inputs = gather_git_metrics(workspace, request)?;

        if inputs.is_empty() {
            return Ok(SedimentResult {
                vertices: Vec::new(),
                layer_count: 0,
                file_count: 0,
                compute_time_ms: start.elapsed().as_millis() as u64,
                backend: "empty",
            });
        }

        // Try GPU dispatch; fall back to CPU on any error
        match self.gpu_dispatch(&inputs, request) {
            Ok(vertices) => Ok(SedimentResult {
                layer_count: inputs.iter().map(|i| i.layer_depth).max().unwrap_or(0) + 1,
                file_count: inputs.len() as u32,
                vertices,
                compute_time_ms: start.elapsed().as_millis() as u64,
                backend: "vulkan",
            }),
            Err(err) => {
                eprintln!("[reactor] GPU dispatch failed, falling back to CPU: {err}");
                let vertices = cpu_fallback(&inputs, request);
                Ok(SedimentResult {
                    layer_count: inputs.iter().map(|i| i.layer_depth).max().unwrap_or(0) + 1,
                    file_count: inputs.len() as u32,
                    vertices,
                    compute_time_ms: start.elapsed().as_millis() as u64,
                    backend: "cpu-fallback",
                })
            }
        }
    }

    /// Dispatch the compute shader on the GPU.
    fn gpu_dispatch(
        &self,
        _inputs: &[SedimentInput],
        _request: &SedimentRequest,
    ) -> Result<Vec<SedimentVertex>> {
        // Full Vulkan dispatch: create buffers, write descriptors, record
        // command buffer, submit, fence wait, read back.
        //
        // This is a placeholder for the full implementation. The key steps:
        //
        // 1. Allocate input storage buffer (VK_BUFFER_USAGE_STORAGE_BUFFER_BIT)
        // 2. Allocate output storage buffer
        // 3. Map input buffer, memcpy SedimentInput array
        // 4. Update descriptor set (binding 0 = input, binding 1 = output)
        // 5. Record command buffer: bind pipeline, bind descriptors, push
        //    constants, dispatch(ceil(N/256), 1, 1)
        // 6. Submit to compute queue with fence
        // 7. Wait on fence
        // 8. Map output buffer, read SedimentVertex array
        //
        // For now, delegate to CPU fallback until buffer management is wired.
        anyhow::bail!("GPU buffer management not yet wired; using CPU fallback")
    }
}

impl Drop for VulkanReactor {
    fn drop(&mut self) {
        unsafe {
            self.device.destroy_command_pool(self.command_pool, None);
            self.device.destroy_pipeline(self.pipeline, None);
            self.device
                .destroy_pipeline_layout(self.pipeline_layout, None);
            self.device
                .destroy_descriptor_set_layout(self.descriptor_set_layout, None);
            self.device.destroy_device(None);
            self.instance.destroy_instance(None);
        }
    }
}

/// Initialize the Vulkan reactor: load entry, create instance, select
/// compute device, compile shader, build pipeline.
///
/// Returns `None` if no Vulkan device is available (graceful degradation).
pub fn initialize() -> Result<Option<VulkanReactor>> {
    // 1. Load Vulkan runtime
    let entry = match unsafe { ash::Entry::load() } {
        Ok(e) => e,
        Err(err) => {
            eprintln!("[reactor] Vulkan not available: {err}");
            return Ok(None);
        }
    };

    // 2. Verify DLL origin on Windows
    crate::env::verify_vulkan_dll_origin()
        .context("Vulkan DLL verification failed")?;

    // 3. Create instance (headless -- no surface extensions)
    let app_info = ash::vk::ApplicationInfo::default()
        .application_name(c"chthonic-daemon")
        .application_version(ash::vk::make_api_version(0, 0, 1, 0))
        .api_version(ash::vk::API_VERSION_1_2);

    let create_info = ash::vk::InstanceCreateInfo::default().application_info(&app_info);
    let instance = unsafe { entry.create_instance(&create_info, None) }
        .context("failed to create Vulkan instance")?;

    // 4. Select physical device with compute queue
    let (physical_device, compute_family_index) =
        select_compute_device(&instance)?;

    // 5. Create logical device
    let queue_priorities = [1.0_f32];
    let queue_info = ash::vk::DeviceQueueCreateInfo::default()
        .queue_family_index(compute_family_index)
        .queue_priorities(&queue_priorities);

    let device_info =
        ash::vk::DeviceCreateInfo::default().queue_create_infos(std::slice::from_ref(&queue_info));

    let device = unsafe { instance.create_device(physical_device, &device_info, None) }
        .context("failed to create Vulkan device")?;

    let compute_queue = unsafe { device.get_device_queue(compute_family_index, 0) };

    // 6. Compile GLSL compute shader via shaderc
    let spirv = compile_sediment_shader()?;

    // 7. Create descriptor set layout (2 storage buffers)
    let bindings = [
        ash::vk::DescriptorSetLayoutBinding::default()
            .binding(0)
            .descriptor_type(ash::vk::DescriptorType::STORAGE_BUFFER)
            .descriptor_count(1)
            .stage_flags(ash::vk::ShaderStageFlags::COMPUTE),
        ash::vk::DescriptorSetLayoutBinding::default()
            .binding(1)
            .descriptor_type(ash::vk::DescriptorType::STORAGE_BUFFER)
            .descriptor_count(1)
            .stage_flags(ash::vk::ShaderStageFlags::COMPUTE),
    ];
    let layout_info =
        ash::vk::DescriptorSetLayoutCreateInfo::default().bindings(&bindings);
    let descriptor_set_layout =
        unsafe { device.create_descriptor_set_layout(&layout_info, None) }
            .context("failed to create descriptor set layout")?;

    // 8. Create pipeline layout (with push constants)
    let push_range = ash::vk::PushConstantRange::default()
        .stage_flags(ash::vk::ShaderStageFlags::COMPUTE)
        .offset(0)
        .size(std::mem::size_of::<PushConstants>() as u32);

    let pipeline_layout_info = ash::vk::PipelineLayoutCreateInfo::default()
        .set_layouts(std::slice::from_ref(&descriptor_set_layout))
        .push_constant_ranges(std::slice::from_ref(&push_range));

    let pipeline_layout = unsafe { device.create_pipeline_layout(&pipeline_layout_info, None) }
        .context("failed to create pipeline layout")?;

    // 9. Create shader module
    let shader_info = ash::vk::ShaderModuleCreateInfo::default().code(&spirv);
    let shader_module = unsafe { device.create_shader_module(&shader_info, None) }
        .context("failed to create shader module")?;

    // 10. Create compute pipeline
    let stage = ash::vk::PipelineShaderStageCreateInfo::default()
        .stage(ash::vk::ShaderStageFlags::COMPUTE)
        .module(shader_module)
        .name(c"main");

    let pipeline_info = ash::vk::ComputePipelineCreateInfo::default()
        .stage(stage)
        .layout(pipeline_layout);

    let pipelines = unsafe {
        device.create_compute_pipelines(
            ash::vk::PipelineCache::null(),
            std::slice::from_ref(&pipeline_info),
            None,
        )
    }
    .map_err(|(_, err)| err)
    .context("failed to create compute pipeline")?;

    // Shader module can be destroyed after pipeline creation
    unsafe { device.destroy_shader_module(shader_module, None) };

    // 11. Create command pool
    let pool_info = ash::vk::CommandPoolCreateInfo::default()
        .queue_family_index(compute_family_index)
        .flags(ash::vk::CommandPoolCreateFlags::RESET_COMMAND_BUFFER);

    let command_pool = unsafe { device.create_command_pool(&pool_info, None) }
        .context("failed to create command pool")?;

    Ok(Some(VulkanReactor {
        _entry: entry,
        instance,
        device,
        _compute_queue: compute_queue,
        _compute_family_index: compute_family_index,
        descriptor_set_layout,
        pipeline_layout,
        pipeline: pipelines[0],
        command_pool,
        _spirv: spirv,
    }))
}

fn select_compute_device(
    instance: &ash::Instance,
) -> Result<(ash::vk::PhysicalDevice, u32)> {
    let devices = unsafe { instance.enumerate_physical_devices() }
        .context("failed to enumerate physical devices")?;

    for device in devices {
        let families =
            unsafe { instance.get_physical_device_queue_family_properties(device) };
        for (index, family) in families.iter().enumerate() {
            if family.queue_flags.contains(ash::vk::QueueFlags::COMPUTE) {
                let props = unsafe { instance.get_physical_device_properties(device) };
                let name = unsafe {
                    std::ffi::CStr::from_ptr(props.device_name.as_ptr())
                };
                eprintln!(
                    "[reactor] selected device: {} (queue family {index})",
                    name.to_string_lossy()
                );
                return Ok((device, index as u32));
            }
        }
    }

    anyhow::bail!("no Vulkan device with compute queue found")
}

fn compile_sediment_shader() -> Result<Vec<u32>> {
    let compiler = shaderc::Compiler::new()
        .ok_or_else(|| anyhow::anyhow!("failed to create shaderc compiler"))?;

    let mut options = shaderc::CompileOptions::new()
        .ok_or_else(|| anyhow::anyhow!("failed to create shaderc options"))?;
    options.set_target_env(
        shaderc::TargetEnv::Vulkan,
        shaderc::EnvVersion::Vulkan1_2 as u32,
    );

    let source = include_str!("shaders/sediment.comp");
    let result = compiler.compile_into_spirv(
        source,
        shaderc::ShaderKind::Compute,
        "sediment.comp",
        "main",
        Some(&options),
    )?;

    Ok(result.as_binary().to_vec())
}

// ---------------------------------------------------------------------------
// Git metrics extraction via gix
// ---------------------------------------------------------------------------

pub fn gather_git_metrics(
    workspace: &str,
    request: &SedimentRequest,
) -> Result<Vec<SedimentInput>> {
    let repo = gix::open(workspace).context("failed to open git repository")?;
    let head = repo
        .head_commit()
        .context("failed to resolve HEAD commit")?;

    let mut file_metrics: std::collections::HashMap<String, FileMetrics> =
        std::collections::HashMap::new();

    let mut total_commits: u32 = 0;
    let max_walk = request.max_layers * 100; // walk more commits than layers

    // Walk commit history
    let mut ancestors = head.ancestors().all().context("failed to walk ancestors")?;
    while let Some(Ok(info)) = ancestors.next() {
        if total_commits >= max_walk {
            break;
        }
        total_commits += 1;

        let commit = info.object().context("failed to read commit object")?;
        let author = commit
            .author()
            .ok()
            .map(|a| a.name.to_string())
            .unwrap_or_default();

        // Assign this commit to a layer based on depth
        let layer = (total_commits / (max_walk / request.max_layers.max(1)))
            .min(request.max_layers - 1);

        // Get the tree to list files (simplified: just the root tree)
        if let Ok(tree) = commit.tree() {
            let mut recorder = gix::traverse::tree::Recorder::default();
            if tree.traverse().breadthfirst(&mut recorder).is_ok() {
                for entry in &recorder.records {
                    let path = entry.filepath.to_string();
                    let metrics = file_metrics.entry(path).or_insert_with(FileMetrics::default);
                    metrics.commit_count += 1;
                    metrics.authors.insert(author.clone());
                    metrics.latest_layer = metrics.latest_layer.min(layer);
                    if file_metrics.len() >= request.max_files as usize {
                        break;
                    }
                }
            }
        }
    }

    if total_commits == 0 {
        return Ok(Vec::new());
    }

    // Convert to SedimentInput array
    let total_f = total_commits as f32;
    let max_authors = file_metrics
        .values()
        .map(|m| m.authors.len())
        .max()
        .unwrap_or(1) as f32;

    let mut inputs: Vec<SedimentInput> = file_metrics
        .into_iter()
        .enumerate()
        .take(request.max_files as usize)
        .map(|(idx, (path, m))| {
            let change_freq = (m.commit_count as f32) / total_f;
            let recency = 1.0 - (m.latest_layer as f32 / request.max_layers as f32);
            let diversity = (m.authors.len() as f32) / max_authors;
            let entropy = compute_path_entropy(&path);

            SedimentInput {
                entropy,
                change_frequency: change_freq.min(1.0),
                recency,
                author_diversity: diversity,
                file_index: idx as u32,
                layer_depth: m.latest_layer,
                complexity: change_freq * entropy,
                _padding: 0.0,
            }
        })
        .collect();

    inputs.sort_by_key(|i| i.file_index);
    Ok(inputs)
}

struct FileMetrics {
    commit_count: u32,
    authors: std::collections::HashSet<String>,
    latest_layer: u32,
}

impl Default for FileMetrics {
    fn default() -> Self {
        Self {
            commit_count: 0,
            authors: std::collections::HashSet::new(),
            latest_layer: u32::MAX,
        }
    }
}

/// Simple path-based entropy heuristic (matches the TS entropy worker's
/// approach: deeper paths and certain extensions = higher entropy).
pub fn compute_path_entropy(path: &str) -> f32 {
    let depth = path.matches('/').count() as f32;
    let ext_weight = match path.rsplit('.').next() {
        Some("rs" | "ts" | "py" | "rb") => 0.3,
        Some("toml" | "json" | "yaml") => 0.15,
        Some("md" | "txt") => 0.05,
        _ => 0.2,
    };
    let base = (depth * 0.08 + ext_weight).min(1.0);
    // Add some hash-based variation so files at the same depth differ
    let hash = path.bytes().fold(0u32, |acc, b| acc.wrapping_mul(31).wrapping_add(b as u32));
    let noise = ((hash % 100) as f32) / 500.0;
    (base + noise).min(1.0)
}

// ---------------------------------------------------------------------------
// CPU fallback: same math as the GLSL shader, in pure Rust
// ---------------------------------------------------------------------------

/// CPU fallback when Vulkan is not available. Same algorithm as sediment.comp.
pub fn cpu_fallback(inputs: &[SedimentInput], _request: &SedimentRequest) -> Vec<SedimentVertex> {
    let total = inputs.len() as u32;
    inputs
        .iter()
        .map(|inp| {
            let (x, y) = sunflower_position(inp.file_index, total);
            let spread = 0.3 + 0.7 * inp.recency;
            let sx = x * spread * 400.0;
            let sy = y * spread * 400.0;

            let z = -(inp.layer_depth as f32) * 50.0
                + inp.entropy * 30.0
                + inp.change_frequency * 20.0;

            let radius = 2.0 + inp.complexity * 3.0 + inp.change_frequency * 2.0;
            let (r, g, b) = entropy_color(inp.entropy);
            let alpha = 0.4 + 0.6 * inp.author_diversity;

            SedimentVertex {
                x: sx,
                y: sy,
                z,
                radius,
                r,
                g,
                b,
                alpha,
            }
        })
        .collect()
}

fn sunflower_position(index: u32, total: u32) -> (f32, f32) {
    let golden_angle: f32 = 2.399_963_2;
    let r = ((index as f32) / (total.max(1) as f32)).sqrt();
    let theta = (index as f32) * golden_angle;
    (r * theta.cos(), r * theta.sin())
}

fn entropy_color(entropy: f32) -> (f32, f32, f32) {
    if entropy >= 0.78 {
        (0.541, 0.298, 0.165) // brown #8a4c2a
    } else if entropy >= 0.48 {
        (0.788, 0.663, 0.384) // gold #c9a962
    } else {
        (0.486, 0.682, 0.404) // green #7cae67
    }
}
