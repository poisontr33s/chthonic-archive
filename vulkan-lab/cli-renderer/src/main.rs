// @SID: VULKAN_CLI_RENDERER_G2
// Gates 1–2: headless Vulkan instance + Euler scoring GPU compute dispatch.
//
// G1: create Entry → headless Instance → pick physical device (RTX 4090)
// G2: select compute queue family (prefer Q2 COMPUTE-only, fallback Q0 GRAPHICS|COMPUTE)
//     → VkDevice → read manifest/todo_roulette.json
//     → EulerTask[n] SSBO upload (host-coherent; staging unnecessary at manifest scale)
//     → euler_score.comp.spv dispatch
//     → read back f32 scores → sorted output
//
// G3 (TODO): fn transition_image_layout() FIRST — load-bearing for G3/G4/G5/G6.
//            VkImage 480×80 RGBA8 → ascii_downsample.comp.spv → ANSI stdout.
// G4 (TODO): 33ms render loop, prev_frame VkImage, GPU diff → dirty-cell cursor.
// G5 (TODO): SpinState { Idle, Spinning, Decelerating, Landed } == RoomState graph.
// G6 (TODO): --mode=polar vs --mode=dungeon via push constant.

use std::ffi::CStr;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

use ash::{vk, Device, Entry, Instance};
use serde::Deserialize;

// ── TAG_PHASE map (mirrors todo_roulette.ts § TAG_PHASE) ─────────────────────
const TAG_PHASE: &[(&str, f32)] = &[
    ("ssot",       0.0),
    ("entity",    30.0),
    ("lore",      60.0),
    ("infra",     90.0),
    ("build",    120.0),
    ("ci",       150.0),
    ("game",     180.0),
    ("narrative",210.0),
    ("vulkan",   240.0),
    ("session",  270.0),
    ("handoff",  300.0),
    ("debt",     330.0),
];

// ── GPU task struct — must match GLSL std430 Task in euler_score.comp.glsl ───
#[repr(C)]
#[derive(Clone, Copy)]
struct EulerTask {
    weight:         f32,
    staleness_days: f32,
    phase_angle:    f32, // radians
    _pad:           f32,
}

// ── manifest schema ───────────────────────────────────────────────────────────
#[derive(Deserialize)]
struct Manifest {
    entries: Vec<ManifestEntry>,
}

#[derive(Deserialize, Clone)]
struct ManifestEntry {
    #[allow(dead_code)]
    id:      String,
    title:   String,
    tags:    Vec<String>,
    weight:  f32,
    created: String,
    #[serde(default)]
    status:  Option<String>,
}

// ── helpers ───────────────────────────────────────────────────────────────────

/// Circular mean of per-tag phase angles (radians), matching TypeScript phaseAngle().
fn phase_radians(tags: &[String]) -> f32 {
    use std::f32::consts::PI;
    if tags.is_empty() {
        return 45.0_f32 * PI / 180.0;
    }
    let (mut sin_sum, mut cos_sum) = (0.0_f32, 0.0_f32);
    for tag in tags {
        let deg = TAG_PHASE.iter()
            .find(|(t, _)| *t == tag.as_str())
            .map(|(_, d)| *d)
            .unwrap_or(45.0);
        let rad = deg * PI / 180.0;
        sin_sum += rad.sin();
        cos_sum += rad.cos();
    }
    sin_sum.atan2(cos_sum)
}

/// Days from Unix epoch (1970-01-01) for a Gregorian date.
fn days_from_epoch(y: i64, m: i64, d: i64) -> i64 {
    let (y, m) = if m <= 2 { (y - 1, m + 12) } else { (y, m) };
    let a = y / 100;
    let b = 2 - a + a / 4;
    ((365.25 * (y + 4716) as f64).floor() as i64)
        + ((30.6001 * (m + 1) as f64).floor() as i64)
        + d + b - 1524 - 2_440_588
}

/// Elapsed days since an ISO-8601 "YYYY-MM-DD..." string.
fn staleness_days(created_iso: &str) -> f32 {
    let now_days = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs() as f64
        / 86400.0;
    created_iso.get(0..10)
        .and_then(|date| {
            let p: Vec<&str> = date.splitn(3, '-').collect();
            if p.len() == 3 {
                let (y, m, d) = (p[0].parse().ok()?, p[1].parse().ok()?, p[2].parse().ok()?);
                Some((now_days - days_from_epoch(y, m, d) as f64).max(0.0) as f32)
            } else {
                None
            }
        })
        .unwrap_or(2.0)
}

/// Index of first memory type matching `filter` bits and required `flags`.
unsafe fn find_memory_type(
    instance: &Instance,
    pd: vk::PhysicalDevice,
    filter: u32,
    flags: vk::MemoryPropertyFlags,
) -> u32 {
    let props = instance.get_physical_device_memory_properties(pd);
    (0..props.memory_type_count)
        .find(|&i| {
            (filter & (1 << i)) != 0
                && props.memory_types[i as usize].property_flags.contains(flags)
        })
        .expect("no suitable Vulkan memory type found")
}

/// Allocate a host-coherent VkBuffer+DeviceMemory pair.
unsafe fn alloc_mapped_buffer(
    device: &Device,
    instance: &Instance,
    pd: vk::PhysicalDevice,
    size: u64,
    usage: vk::BufferUsageFlags,
) -> (vk::Buffer, vk::DeviceMemory) {
    let buf = device
        .create_buffer(
            &vk::BufferCreateInfo::default()
                .size(size)
                .usage(usage)
                .sharing_mode(vk::SharingMode::EXCLUSIVE),
            None,
        )
        .expect("create_buffer");
    let reqs = device.get_buffer_memory_requirements(buf);
    let host_coherent =
        vk::MemoryPropertyFlags::HOST_VISIBLE | vk::MemoryPropertyFlags::HOST_COHERENT;
    let mem = device
        .allocate_memory(
            &vk::MemoryAllocateInfo::default()
                .allocation_size(reqs.size)
                .memory_type_index(find_memory_type(instance, pd, reqs.memory_type_bits, host_coherent)),
            None,
        )
        .expect("allocate_memory");
    device.bind_buffer_memory(buf, mem, 0).expect("bind_buffer_memory");
    (buf, mem)
}

/// Walk cwd upward to find manifest/todo_roulette.json.
fn find_manifest() -> PathBuf {
    let mut dir = std::env::current_dir().unwrap();
    loop {
        let c = dir.join("manifest").join("todo_roulette.json");
        if c.exists() {
            return c;
        }
        if !dir.pop() {
            break;
        }
    }
    panic!(
        "manifest/todo_roulette.json not found.\n  \
         Run from chthonic-archive root or pass --manifest <path>"
    )
}

fn main() {
    // ── CLI: --manifest override ───────────────────────────────────────────
    let args: Vec<String> = std::env::args().collect();
    let manifest_path = args
        .windows(2)
        .find(|w| w[0] == "--manifest")
        .map(|w| PathBuf::from(&w[1]))
        .unwrap_or_else(find_manifest);

    // ── G1: headless Vulkan instance ──────────────────────────────────────
    let entry = unsafe { Entry::load().expect("Vulkan loader not found — install NVIDIA drivers") };

    let app_info = vk::ApplicationInfo::default()
        .application_name(c"cli-renderer")
        .api_version(vk::API_VERSION_1_3);

    let instance: Instance = unsafe {
        entry
            .create_instance(
                &vk::InstanceCreateInfo::default().application_info(&app_info),
                None,
            )
            .expect("create_instance")
    };

    let physical_devices =
        unsafe { instance.enumerate_physical_devices().expect("enumerate_physical_devices") };
    assert!(!physical_devices.is_empty(), "No Vulkan-capable GPU found");
    let pd = physical_devices[0];

    let props = unsafe { instance.get_physical_device_properties(pd) };
    let gpu_name =
        unsafe { CStr::from_ptr(props.device_name.as_ptr()) }.to_string_lossy().into_owned();
    let api = props.api_version;

    println!(
        "cli-renderer  G1 ✓  GPU: {gpu_name}  Vulkan: {}.{}.{}",
        vk::api_version_major(api),
        vk::api_version_minor(api),
        vk::api_version_patch(api)
    );

    // ── G2: select compute queue family ───────────────────────────────────
    // Prefer Q2 (COMPUTE-only on RTX 4090) → fallback Q0 (GRAPHICS|COMPUTE).
    let qf_props = unsafe { instance.get_physical_device_queue_family_properties(pd) };
    let qf_idx = qf_props
        .iter()
        .enumerate()
        .filter(|(_, q)| q.queue_flags.contains(vk::QueueFlags::COMPUTE))
        .min_by_key(|(_, q)| {
            if q.queue_flags.contains(vk::QueueFlags::GRAPHICS) { 1u8 } else { 0u8 }
        })
        .map(|(i, _)| i as u32)
        .expect("No compute-capable queue family");

    // ── G2: create logical device ─────────────────────────────────────────
    let queue_priority = [1.0_f32];
    let queue_ci = [vk::DeviceQueueCreateInfo::default()
        .queue_family_index(qf_idx)
        .queue_priorities(&queue_priority)];

    let device: Device = unsafe {
        instance
            .create_device(
                pd,
                &vk::DeviceCreateInfo::default().queue_create_infos(&queue_ci),
                None,
            )
            .expect("create_device")
    };
    let queue = unsafe { device.get_device_queue(qf_idx, 0) };

    println!("cli-renderer  G2     device created  queue_family={qf_idx}");

    // ── G2: read + parse manifest ─────────────────────────────────────────
    let manifest_str = std::fs::read_to_string(&manifest_path)
        .unwrap_or_else(|e| panic!("read {}: {e}", manifest_path.display()));
    let manifest: Manifest =
        serde_json::from_str(&manifest_str).expect("parse manifest JSON");

    let active: Vec<&ManifestEntry> = manifest
        .entries
        .iter()
        .filter(|e| !matches!(e.status.as_deref(), Some("completed") | Some("ghost")))
        .collect();

    let n = active.len();
    assert!(n > 0, "manifest has 0 active tasks");

    // ── G2: build EulerTask array (host-side tag→phase mapping) ──────────
    let gpu_tasks: Vec<EulerTask> = active
        .iter()
        .map(|e| EulerTask {
            weight:         e.weight,
            staleness_days: staleness_days(&e.created),
            phase_angle:    phase_radians(&e.tags),
            _pad:           0.0,
        })
        .collect();

    println!("cli-renderer  G2     {n} active tasks → uploading SSBO");

    // ── G2: allocate buffers (host-coherent) ──────────────────────────────
    let task_bytes  = (n * std::mem::size_of::<EulerTask>()) as u64;
    let score_bytes = (n * std::mem::size_of::<f32>()) as u64;
    let count_bytes = std::mem::size_of::<u32>() as u64;
    let ssbo = vk::BufferUsageFlags::STORAGE_BUFFER;

    let (task_buf,  task_mem)  =
        unsafe { alloc_mapped_buffer(&device, &instance, pd, task_bytes,  ssbo) };
    let (score_buf, score_mem) =
        unsafe { alloc_mapped_buffer(&device, &instance, pd, score_bytes, ssbo) };
    let (count_buf, count_mem) =
        unsafe { alloc_mapped_buffer(&device, &instance, pd, count_bytes, ssbo) };

    unsafe {
        let ptr = device
            .map_memory(task_mem, 0, task_bytes, vk::MemoryMapFlags::empty())
            .expect("map task_mem") as *mut EulerTask;
        std::ptr::copy_nonoverlapping(gpu_tasks.as_ptr(), ptr, n);
        device.unmap_memory(task_mem);

        let ptr = device
            .map_memory(count_mem, 0, count_bytes, vk::MemoryMapFlags::empty())
            .expect("map count_mem") as *mut u32;
        ptr.write(n as u32);
        device.unmap_memory(count_mem);
    }

    // ── G2: shader module from pre-compiled SPIR-V ────────────────────────
    // build.rs compiles euler_score.comp.glsl → euler_score.comp.spv at build time.
    let spv_bytes = include_bytes!("../shaders/euler_score.comp.spv");
    let spv_words: Vec<u32> = spv_bytes
        .chunks_exact(4)
        .map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]]))
        .collect();

    let shader_module = unsafe {
        device
            .create_shader_module(
                &vk::ShaderModuleCreateInfo::default().code(&spv_words),
                None,
            )
            .expect("create_shader_module")
    };

    // ── G2: descriptor set layout (binding 0/1/2 = task/score/count SSBO) ─
    let bindings = [0u32, 1, 2].map(|i| {
        vk::DescriptorSetLayoutBinding::default()
            .binding(i)
            .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
            .descriptor_count(1)
            .stage_flags(vk::ShaderStageFlags::COMPUTE)
    });
    let dsl = unsafe {
        device
            .create_descriptor_set_layout(
                &vk::DescriptorSetLayoutCreateInfo::default().bindings(&bindings),
                None,
            )
            .expect("create_descriptor_set_layout")
    };
    let pipeline_layout = unsafe {
        device
            .create_pipeline_layout(
                &vk::PipelineLayoutCreateInfo::default().set_layouts(&[dsl]),
                None,
            )
            .expect("create_pipeline_layout")
    };

    // ── G2: compute pipeline ──────────────────────────────────────────────
    let stage = vk::PipelineShaderStageCreateInfo::default()
        .stage(vk::ShaderStageFlags::COMPUTE)
        .module(shader_module)
        .name(c"main");
    let pipelines = unsafe {
        device
            .create_compute_pipelines(
                vk::PipelineCache::null(),
                &[vk::ComputePipelineCreateInfo::default()
                    .stage(stage)
                    .layout(pipeline_layout)],
                None,
            )
            .expect("create_compute_pipelines")
    };
    let pipeline = pipelines[0];

    // ── G2: descriptor pool → set → write ────────────────────────────────
    let pool_sizes = [vk::DescriptorPoolSize {
        ty:               vk::DescriptorType::STORAGE_BUFFER,
        descriptor_count: 3,
    }];
    let desc_pool = unsafe {
        device
            .create_descriptor_pool(
                &vk::DescriptorPoolCreateInfo::default()
                    .max_sets(1)
                    .pool_sizes(&pool_sizes),
                None,
            )
            .expect("create_descriptor_pool")
    };
    let desc_sets = unsafe {
        device
            .allocate_descriptor_sets(
                &vk::DescriptorSetAllocateInfo::default()
                    .descriptor_pool(desc_pool)
                    .set_layouts(&[dsl]),
            )
            .expect("allocate_descriptor_sets")
    };
    let desc_set = desc_sets[0];

    let buf_infos = [
        vk::DescriptorBufferInfo { buffer: task_buf,  offset: 0, range: task_bytes  },
        vk::DescriptorBufferInfo { buffer: score_buf, offset: 0, range: score_bytes },
        vk::DescriptorBufferInfo { buffer: count_buf, offset: 0, range: count_bytes },
    ];
    let writes: Vec<vk::WriteDescriptorSet> = buf_infos
        .iter()
        .enumerate()
        .map(|(i, bi)| {
            vk::WriteDescriptorSet::default()
                .dst_set(desc_set)
                .dst_binding(i as u32)
                .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
                .buffer_info(std::slice::from_ref(bi))
        })
        .collect();
    unsafe { device.update_descriptor_sets(&writes, &[]) };

    // ── G2: command pool → buffer → record dispatch ───────────────────────
    let cmd_pool = unsafe {
        device
            .create_command_pool(
                &vk::CommandPoolCreateInfo::default().queue_family_index(qf_idx),
                None,
            )
            .expect("create_command_pool")
    };
    let cmd_bufs = unsafe {
        device
            .allocate_command_buffers(
                &vk::CommandBufferAllocateInfo::default()
                    .command_pool(cmd_pool)
                    .level(vk::CommandBufferLevel::PRIMARY)
                    .command_buffer_count(1),
            )
            .expect("allocate_command_buffers")
    };
    let cmd = cmd_bufs[0];

    unsafe {
        device
            .begin_command_buffer(
                cmd,
                &vk::CommandBufferBeginInfo::default()
                    .flags(vk::CommandBufferUsageFlags::ONE_TIME_SUBMIT),
            )
            .expect("begin_command_buffer");
        device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::COMPUTE, pipeline);
        device.cmd_bind_descriptor_sets(
            cmd, vk::PipelineBindPoint::COMPUTE, pipeline_layout, 0, &[desc_set], &[],
        );
        let groups = ((n as u32) + 63) / 64; // ceil(n/64) — local_size_x = 64
        device.cmd_dispatch(cmd, groups, 1, 1);
        device.end_command_buffer(cmd).expect("end_command_buffer");
    }

    // ── G2: submit + fence wait ───────────────────────────────────────────
    let fence = unsafe {
        device.create_fence(&vk::FenceCreateInfo::default(), None).expect("create_fence")
    };
    let submit_info = vk::SubmitInfo::default().command_buffers(&cmd_bufs);
    unsafe {
        device.queue_submit(queue, &[submit_info], fence).expect("queue_submit");
        device.wait_for_fences(&[fence], true, u64::MAX).expect("wait_for_fences");
    }

    // ── G2: read back scores (HOST_COHERENT — no flush needed) ────────────
    let scores: Vec<f32> = unsafe {
        let ptr = device
            .map_memory(score_mem, 0, score_bytes, vk::MemoryMapFlags::empty())
            .expect("map score_mem") as *const f32;
        let s = std::slice::from_raw_parts(ptr, n).to_vec();
        device.unmap_memory(score_mem);
        s
    };

    // ── G2: sort and print ────────────────────────────────────────────────
    let mut ranked: Vec<(f32, &ManifestEntry)> = scores
        .iter()
        .zip(active.iter().copied())
        .map(|(s, e)| (*s, e))
        .collect();
    ranked.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));

    println!(
        "\n  {:>8}  {:>9}  {:48}  {}",
        "Score", "Phase(°)", "Title", "Tags"
    );
    println!(
        "  {}  {}  {}  {}",
        "─".repeat(8), "─".repeat(9), "─".repeat(48), "─".repeat(20)
    );
    for (score, entry) in &ranked {
        let phase_deg = phase_radians(&entry.tags).to_degrees().rem_euclid(360.0);
        let tag_str   = entry.tags.iter().map(|t| format!("#{t}")).collect::<Vec<_>>().join(" ");
        let title_tr  = if entry.title.chars().count() > 48 {
            entry.title.chars().take(47).collect::<String>() + "…"
        } else {
            entry.title.clone()
        };
        println!(
            "  {:>8.2}  {:>8.0}°  {:<48}  \x1b[2m{tag_str}\x1b[0m",
            score, phase_deg, title_tr
        );
    }

    println!("\ncli-renderer  G2 ✓  {n} tasks scored via GPU (euler_score.comp.spv  QF={qf_idx})");
    println!("cli-renderer  →     G3: fn transition_image_layout() → VkImage 480×80 → ANSI stdout");

    // ── cleanup ───────────────────────────────────────────────────────────
    unsafe {
        device.destroy_fence(fence, None);
        device.destroy_command_pool(cmd_pool, None);
        device.destroy_descriptor_pool(desc_pool, None);
        device.destroy_pipeline(pipeline, None);
        device.destroy_pipeline_layout(pipeline_layout, None);
        device.destroy_descriptor_set_layout(dsl, None);
        device.destroy_shader_module(shader_module, None);
        device.free_memory(score_mem, None);
        device.destroy_buffer(score_buf, None);
        device.free_memory(count_mem, None);
        device.destroy_buffer(count_buf, None);
        device.free_memory(task_mem, None);
        device.destroy_buffer(task_buf, None);
        device.destroy_device(None);
        instance.destroy_instance(None);
    }
}
