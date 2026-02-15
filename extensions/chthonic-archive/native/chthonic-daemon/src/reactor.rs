use std::time::Instant;

use anyhow::{Context, Result};

use crate::types::{SedimentRequest, SedimentResult, SedimentVertex};

// ---------------------------------------------------------------------------
// GPU-mirrored data structures (must match sediment.comp layout exactly)
// ---------------------------------------------------------------------------

/// A single node in the force-directed sediment graph.
/// Layout matches the GLSL `Node` struct: 3 × vec4 = 48 bytes.
///
/// - `position`: xyz = spatial position, w = mass (1.0 = old/heavy, 0.1 = new/light)
/// - `velocity`: xyz = velocity vector,  w = entropy (0.0 to 1.0)
/// - `color`:    rgba output for the renderer
#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct Node {
    // vec4 position
    pub pos_x: f32,
    pub pos_y: f32,
    pub pos_z: f32,
    pub mass: f32,
    // vec4 velocity
    pub vel_x: f32,
    pub vel_y: f32,
    pub vel_z: f32,
    pub entropy: f32,
    // vec4 color
    pub r: f32,
    pub g: f32,
    pub b: f32,
    pub a: f32,
}

/// Push constants for the compute shader.
#[repr(C)]
#[derive(Debug, Clone, Copy)]
struct PushConstants {
    delta_time: f32,
    total_time: f32,
    node_count: u32,
    gravity_str: f32,
    repel_str: f32,
}

// ---------------------------------------------------------------------------
// Simulation constants
// ---------------------------------------------------------------------------

const SIM_STEPS: u32 = 200;
const DELTA_TIME: f32 = 0.016; // ~60 fps equivalent
const GOLDEN_ANGLE: f32 = 2.399_963_2;
const DECAY: f32 = 0.98;
const GRAVITY: f32 = -4.9;
const SPRING_K: f32 = 2.0;
const REPEL_STR: f32 = 1.0;

// ---------------------------------------------------------------------------
// VulkanReactor
// ---------------------------------------------------------------------------

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
    /// Compute sediment layers from git history via force-directed simulation.
    ///
    /// Walks the repository's commit graph via `gix`, extracts per-file
    /// metrics, initializes node state, runs the force-directed simulation
    /// (GPU or CPU fallback), and returns settled vertex data.
    pub fn compute_sediment(
        &self,
        workspace: &str,
        request: &SedimentRequest,
    ) -> Result<SedimentResult> {
        let start = Instant::now();
        let metrics = gather_git_metrics(workspace, request)?;

        if metrics.nodes.is_empty() {
            return Ok(SedimentResult {
                vertices: Vec::new(),
                layer_count: 0,
                file_count: 0,
                compute_time_ms: start.elapsed().as_millis() as u64,
                backend: "empty",
            });
        }

        // Try GPU dispatch; fall back to CPU on any error
        match self.gpu_dispatch(&metrics.nodes) {
            Ok(settled) => Ok(SedimentResult {
                layer_count: metrics.layer_count,
                file_count: settled.len() as u32,
                vertices: nodes_to_vertices(&settled),
                compute_time_ms: start.elapsed().as_millis() as u64,
                backend: "vulkan",
            }),
            Err(err) => {
                eprintln!("[reactor] GPU dispatch failed, falling back to CPU: {err}");
                let settled = cpu_simulate(metrics.nodes);
                Ok(SedimentResult {
                    layer_count: metrics.layer_count,
                    file_count: settled.len() as u32,
                    vertices: nodes_to_vertices(&settled),
                    compute_time_ms: start.elapsed().as_millis() as u64,
                    backend: "cpu-fallback",
                })
            }
        }
    }

    /// Dispatch the compute shader on the GPU.
    fn gpu_dispatch(
        &self,
        _nodes: &[Node],
    ) -> Result<Vec<Node>> {
        // Full Vulkan dispatch for the force-directed simulation:
        //
        // 1. Allocate a single read/write storage buffer (Node[])
        // 2. Upload initial node state
        // 3. For each simulation step:
        //    a. Update push constants (delta_time, total_time, node_count, ...)
        //    b. Record command buffer: bind pipeline, bind descriptors,
        //       push constants, dispatch(ceil(N/256), 1, 1)
        //    c. Pipeline barrier (compute -> compute)
        //    d. Submit to compute queue with fence, wait
        // 4. Map buffer, read back settled Node[]
        //
        // For now, delegate to CPU until buffer management is wired.
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

// ---------------------------------------------------------------------------
// Vulkan initialization
// ---------------------------------------------------------------------------

/// Initialize the Vulkan reactor: load entry, create instance, select
/// compute device, compile shader, build pipeline.
///
/// Returns `None` if no Vulkan device is available (graceful degradation).
pub fn initialize() -> Result<Option<VulkanReactor>> {
    // 1. Load Vulkan runtime (hardened: System32-only on Windows)
    let entry = match unsafe { load_vulkan_secure() } {
        Ok(e) => e,
        Err(err) => {
            eprintln!("[reactor] Vulkan not available: {err}");
            return Ok(None);
        }
    };

    // 2. Create instance (headless -- no surface extensions)
    let app_info = ash::vk::ApplicationInfo::default()
        .application_name(c"chthonic-daemon")
        .application_version(ash::vk::make_api_version(0, 0, 1, 0))
        .api_version(ash::vk::API_VERSION_1_2);

    let create_info = ash::vk::InstanceCreateInfo::default().application_info(&app_info);
    let instance = unsafe { entry.create_instance(&create_info, None) }
        .context("failed to create Vulkan instance")?;

    // 3. Select physical device with compute queue
    let (physical_device, compute_family_index) =
        select_compute_device(&instance)?;

    // 4. Create logical device
    let queue_priorities = [1.0_f32];
    let queue_info = ash::vk::DeviceQueueCreateInfo::default()
        .queue_family_index(compute_family_index)
        .queue_priorities(&queue_priorities);

    let device_info =
        ash::vk::DeviceCreateInfo::default().queue_create_infos(std::slice::from_ref(&queue_info));

    let device = unsafe { instance.create_device(physical_device, &device_info, None) }
        .context("failed to create Vulkan device")?;

    let compute_queue = unsafe { device.get_device_queue(compute_family_index, 0) };

    // 5. Compile GLSL compute shader via shaderc
    let spirv = compile_sediment_shader()?;

    // 6. Create descriptor set layout (single read/write storage buffer)
    let bindings = [
        ash::vk::DescriptorSetLayoutBinding::default()
            .binding(0)
            .descriptor_type(ash::vk::DescriptorType::STORAGE_BUFFER)
            .descriptor_count(1)
            .stage_flags(ash::vk::ShaderStageFlags::COMPUTE),
    ];
    let layout_info =
        ash::vk::DescriptorSetLayoutCreateInfo::default().bindings(&bindings);
    let descriptor_set_layout =
        unsafe { device.create_descriptor_set_layout(&layout_info, None) }
            .context("failed to create descriptor set layout")?;

    // 7. Create pipeline layout (with push constants)
    let push_range = ash::vk::PushConstantRange::default()
        .stage_flags(ash::vk::ShaderStageFlags::COMPUTE)
        .offset(0)
        .size(std::mem::size_of::<PushConstants>() as u32);

    let pipeline_layout_info = ash::vk::PipelineLayoutCreateInfo::default()
        .set_layouts(std::slice::from_ref(&descriptor_set_layout))
        .push_constant_ranges(std::slice::from_ref(&push_range));

    let pipeline_layout = unsafe { device.create_pipeline_layout(&pipeline_layout_info, None) }
        .context("failed to create pipeline layout")?;

    // 8. Create shader module
    let shader_info = ash::vk::ShaderModuleCreateInfo::default().code(&spirv);
    let shader_module = unsafe { device.create_shader_module(&shader_info, None) }
        .context("failed to create shader module")?;

    // 9. Create compute pipeline
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

    // 10. Create command pool
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

// ---------------------------------------------------------------------------
// Secure Vulkan loader
// ---------------------------------------------------------------------------

/// Load vulkan-1.dll exclusively from System32 via `LoadLibraryExA` with
/// `LOAD_LIBRARY_SEARCH_SYSTEM32`. This prevents a rogue vulkan-1.dll on
/// PATH from being loaded by the standard DLL search order.
///
/// The DLL handle is intentionally leaked: vulkan-1.dll must remain loaded
/// for the entire process lifetime, and `ash::Entry::from_static_fn` does
/// not own the library.
#[cfg(windows)]
unsafe fn load_vulkan_secure() -> Result<ash::Entry> {
    use windows_sys::Win32::System::LibraryLoader::{
        GetProcAddress, LoadLibraryExA, LOAD_LIBRARY_SEARCH_SYSTEM32,
    };

    let handle = LoadLibraryExA(
        b"vulkan-1.dll\0".as_ptr(),
        std::ptr::null_mut(), // hFile: must be NULL
        LOAD_LIBRARY_SEARCH_SYSTEM32,
    );

    if handle.is_null() {
        anyhow::bail!(
            "Failed to load vulkan-1.dll from System32. \
             Ensure the Vulkan runtime is installed."
        );
    }

    let proc = GetProcAddress(handle, b"vkGetInstanceProcAddr\0".as_ptr());
    let Some(proc) = proc else {
        anyhow::bail!("vkGetInstanceProcAddr not exported by vulkan-1.dll");
    };

    // SAFETY: vkGetInstanceProcAddr has a well-known C ABI. We transmute the
    // FARPROC (extern "system" fn() -> isize) to the Vulkan function pointer type.
    let get_instance_proc_addr: ash::vk::PFN_vkGetInstanceProcAddr =
        std::mem::transmute(proc);

    let static_fn = ash::StaticFn {
        get_instance_proc_addr,
    };

    Ok(ash::Entry::from_static_fn(static_fn))
}

/// On non-Windows platforms, use the standard `ash::Entry::load()`.
/// libvulkan.so/.dylib is loaded from standard system paths by the linker.
#[cfg(not(windows))]
unsafe fn load_vulkan_secure() -> Result<ash::Entry> {
    ash::Entry::load().map_err(|e| anyhow::anyhow!("Vulkan not available: {e}"))
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

/// Result of git history analysis: nodes with initial state + metadata.
pub struct GitMetricsResult {
    pub nodes: Vec<Node>,
    pub layer_count: u32,
}

/// Walk git history and produce initial Node state for force-directed simulation.
///
/// Each file in the repository becomes a Node. Properties:
/// - `mass`: derived from age (old files are heavy, sink)
/// - `entropy`: path-based heuristic + change frequency
/// - `position`: starts at origin (simulation moves via spring forces)
/// - `velocity`: starts at zero
pub fn gather_git_metrics(
    workspace: &str,
    request: &SedimentRequest,
) -> Result<GitMetricsResult> {
    let repo = gix::open(workspace).context("failed to open git repository")?;
    let head = repo
        .head_commit()
        .context("failed to resolve HEAD commit")?;

    let mut file_metrics: std::collections::HashMap<String, FileMetrics> =
        std::collections::HashMap::new();

    let mut total_commits: u32 = 0;
    let max_walk = request.max_layers * 100;

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

        let layer = (total_commits / (max_walk / request.max_layers.max(1)))
            .min(request.max_layers - 1);

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
        return Ok(GitMetricsResult {
            nodes: Vec::new(),
            layer_count: 0,
        });
    }

    let total_f = total_commits as f32;
    let max_authors = file_metrics
        .values()
        .map(|m| m.authors.len())
        .max()
        .unwrap_or(1) as f32;

    let max_layer_seen = file_metrics
        .values()
        .map(|m| m.latest_layer)
        .filter(|&l| l != u32::MAX)
        .max()
        .unwrap_or(0);

    // Convert to Node initial state
    let nodes: Vec<Node> = file_metrics
        .into_iter()
        .enumerate()
        .take(request.max_files as usize)
        .map(|(_idx, (path, m))| {
            let change_freq = (m.commit_count as f32) / total_f;
            let recency = 1.0 - (m.latest_layer as f32 / request.max_layers as f32);
            let _diversity = (m.authors.len() as f32) / max_authors;
            let entropy = compute_path_entropy(&path);

            // Mass: old files are heavy (sink). New files are light (float).
            let mass = (1.0 - recency).max(0.1);

            // Entropy blended with change frequency for richer signal
            let blended_entropy = (entropy * 0.6 + change_freq * 0.4).min(1.0);

            Node {
                // Initial position at origin; simulation moves via spring forces
                pos_x: 0.0,
                pos_y: 0.0,
                pos_z: 0.0,
                mass,
                // Velocity starts at zero
                vel_x: 0.0,
                vel_y: 0.0,
                vel_z: 0.0,
                entropy: blended_entropy,
                // Color starts black; simulation paints via entropy mapping
                r: 0.0,
                g: 0.0,
                b: 0.0,
                a: 1.0,
            }
        })
        .collect();

    Ok(GitMetricsResult {
        nodes,
        layer_count: max_layer_seen + 1,
    })
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
    let hash = path.bytes().fold(0u32, |acc, b| acc.wrapping_mul(31).wrapping_add(b as u32));
    let noise = ((hash % 100) as f32) / 500.0;
    (base + noise).min(1.0)
}

// ---------------------------------------------------------------------------
// CPU fallback: force-directed simulation matching sediment.comp
// ---------------------------------------------------------------------------

/// Run the force-directed simulation on the CPU.
/// Same algorithm as `sediment.comp`: spring force to golden spiral target,
/// Brownian motion for high-entropy nodes, Euler integration with damping.
///
/// Returns the settled node state after `SIM_STEPS` iterations.
pub fn cpu_simulate(mut nodes: Vec<Node>) -> Vec<Node> {
    let node_count = nodes.len() as u32;
    let mut total_time: f32 = 0.0;

    for _step in 0..SIM_STEPS {
        for idx in 0..node_count {
            let i = idx as usize;
            let entropy = nodes[i].entropy;
            let mass = nodes[i].mass;

            // Target position: golden spiral
            let r = (idx as f32).sqrt() * 0.5;
            let theta = (idx as f32) * GOLDEN_ANGLE + (total_time * 0.05 * entropy);
            let target_x = r * theta.cos();
            let target_z = r * theta.sin();
            let target_y = (-mass * 50.0) + (entropy * 20.0 * (total_time + idx as f32).sin());

            // Spring force to target
            let mut fx = (target_x - nodes[i].pos_x) * SPRING_K;
            let mut fy = (target_y - nodes[i].pos_y) * SPRING_K;
            let mut fz = (target_z - nodes[i].pos_z) * SPRING_K;

            // Brownian motion for high-entropy nodes
            if entropy > 0.8 {
                let jx = gpu_hash(idx.wrapping_add(total_time as u32)) - 0.5;
                let jy = gpu_hash(idx.wrapping_add(1).wrapping_add(total_time as u32)) - 0.5;
                let jz = gpu_hash(idx.wrapping_add(2).wrapping_add(total_time as u32)) - 0.5;
                fx += jx * REPEL_STR * 5.0;
                fy += jy * REPEL_STR * 5.0;
                fz += jz * REPEL_STR * 5.0;
            }

            // Gravity
            fy += GRAVITY * mass;

            // Euler integration
            nodes[i].vel_x = (nodes[i].vel_x + fx * DELTA_TIME) * DECAY;
            nodes[i].vel_y = (nodes[i].vel_y + fy * DELTA_TIME) * DECAY;
            nodes[i].vel_z = (nodes[i].vel_z + fz * DELTA_TIME) * DECAY;

            nodes[i].pos_x += nodes[i].vel_x * DELTA_TIME;
            nodes[i].pos_y += nodes[i].vel_y * DELTA_TIME;
            nodes[i].pos_z += nodes[i].vel_z * DELTA_TIME;

            // Color: entropy -> void/gold bioluminescence
            let pulse = 0.8 + 0.2 * (total_time * 3.0 + idx as f32).sin();
            nodes[i].r = lerp(0.05, 0.96, entropy) * pulse;
            nodes[i].g = lerp(0.05, 0.77, entropy) * pulse;
            nodes[i].b = lerp(0.05, 0.19, entropy) * pulse;
            nodes[i].a = 1.0;
        }
        total_time += DELTA_TIME;
    }

    nodes
}

/// Convert settled Node state to the SedimentVertex wire format.
fn nodes_to_vertices(nodes: &[Node]) -> Vec<SedimentVertex> {
    nodes
        .iter()
        .map(|n| SedimentVertex {
            x: n.pos_x,
            y: n.pos_y,
            z: n.pos_z,
            radius: 2.0 + n.entropy * 5.0 + n.mass * 1.5,
            r: n.r,
            g: n.g,
            b: n.b,
            alpha: n.a,
        })
        .collect()
}

/// Matches the GLSL `hash()` function for deterministic Brownian motion.
fn gpu_hash(n: u32) -> f32 {
    let mut n = n;
    n = (n << 13) ^ n;
    n = n
        .wrapping_mul(n.wrapping_mul(n).wrapping_mul(15731).wrapping_add(789221))
        .wrapping_add(1376312589);
    (n & 0x7fffffff) as f32 / 0x7fffffff_u32 as f32
}

fn lerp(a: f32, b: f32, t: f32) -> f32 {
    a + (b - a) * t
}
