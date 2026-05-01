// @SID: VULKAN_CLI_RENDERER_V9
// Gates 1–7 complete. V8: isometric cRPG vertical slice (--iso flag).
// V9: raw terminal mode (crossterm) + Ω-3 XP trail write (roulette_steward events → chthonic-xp.ps1).
//
// G1: create Entry → headless Instance → pick physical device (RTX 4090)
// G2: select compute queue family (prefer Q2 COMPUTE-only, fallback Q0 GRAPHICS|COMPUTE)
//     → VkDevice → read manifest/todo_roulette.json
//     → EulerTask[n] SSBO upload → euler_score.comp.spv dispatch → sorted output
// G3: fn transition_image_layout() (load-bearing for G3/G4/G5/G6)
//     → VkImage 480×80 RGBA8 (phase-colored fill) → ascii_downsample.comp.spv
//     → ANSI truecolor block-char stdout (60×5 cell grid)
//
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
    ("liminal",  306.0),   // 17π/10 rad
    ("scaffold", 350.0),   // 35π/18 rad
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
    id:        String,
    title:     String,
    tags:      Vec<String>,
    weight:    f32,
    created:   String,
    #[serde(default)]
    status:    Option<String>,
    #[serde(default)]
    completed: Option<String>,
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

/// Record a VkImage layout transition barrier into `cmd`.
unsafe fn transition_image_layout(
    device:     &Device,
    cmd:        vk::CommandBuffer,
    image:      vk::Image,
    old_layout: vk::ImageLayout,
    new_layout: vk::ImageLayout,
    src_stage:  vk::PipelineStageFlags,
    dst_stage:  vk::PipelineStageFlags,
    src_access: vk::AccessFlags,
    dst_access: vk::AccessFlags,
) {
    let barrier = vk::ImageMemoryBarrier::default()
        .old_layout(old_layout)
        .new_layout(new_layout)
        .src_queue_family_index(vk::QUEUE_FAMILY_IGNORED)
        .dst_queue_family_index(vk::QUEUE_FAMILY_IGNORED)
        .image(image)
        .subresource_range(
            vk::ImageSubresourceRange::default()
                .aspect_mask(vk::ImageAspectFlags::COLOR)
                .base_mip_level(0)
                .level_count(1)
                .base_array_layer(0)
                .layer_count(1),
        )
        .src_access_mask(src_access)
        .dst_access_mask(dst_access);
    device.cmd_pipeline_barrier(
        cmd,
        src_stage,
        dst_stage,
        vk::DependencyFlags::empty(),
        &[], &[], &[barrier],
    );
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

/// G5: SpinState ≡ RoomState — same 4-phase FSM, two names.
/// Polar mode:  Idle → Spinning → Decelerating → Landed (arc-wheel animation tempo)
/// Dungeon mode: Locked → Unlocked → Visited → Cleared (room visual state)
#[derive(Clone, Copy, Debug, PartialEq)]
enum StatePhase { Idle = 0, Spinning = 1, Decelerating = 2, Landed = 3 }

fn tick_state(s: StatePhase, frame: u64) -> StatePhase {
    match s {
        StatePhase::Idle         => StatePhase::Spinning,
        StatePhase::Spinning     => if frame % 90 == 0 { StatePhase::Decelerating } else { s },
        StatePhase::Decelerating => if frame % 30 == 0 { StatePhase::Landed       } else { s },
        StatePhase::Landed       => StatePhase::Idle,
    }
}

fn state_label(s: StatePhase) -> &'static str {
    match s {
        StatePhase::Idle         => "Idle/Locked",
        StatePhase::Spinning     => "Spinning/Unlocked",
        StatePhase::Decelerating => "Decel/Visited",
        StatePhase::Landed       => "Landed/Cleared",
    }
}

/// Ω-3: Emit a roulette_steward trail event when a dungeon room reaches cleared state.
/// chthonic-xp.ps1 reads .chthonic/trail/*.json → type (XP_BASE=10) + kind (KIND_BONUS=12) + priority (MULT=1.5).
/// Total XP per cleared room: (10 + 12) × 1.5 = 33.
fn write_trail_event(trail_dir: &std::path::Path, task_title: &str) {
    let _ = std::fs::create_dir_all(trail_dir);
    let ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    let fname = trail_dir.join(format!("roulette_{ns}.json"));
    let title_esc = task_title.replace('\\', "\\\\").replace('"', "\\\"");
    let payload = format!(
        "{{\"type\":\"artifact\",\"kind\":\"roulette_steward\",\"priority\":1,\"msg\":\"dungeon room cleared: {title_esc}\"}}"
    );
    let _ = std::fs::write(fname, payload.as_bytes());
}

/// Ω-4: XP tier from cumulative XP. Returns (class_label, xp_in_tier, tier_size).
fn xp_tier(total_xp: u64) -> (&'static str, u64, u64) {
    const TIER: u64 = 80;
    let class = match total_xp / TIER {
        0 => "Acolyte",
        1 => "Adept",
        2 => "Expert",
        _ => "Archon",
    };
    (class, total_xp % TIER, TIER)
}

/// Ω-4: Render `[Class ████░░░░ xp/next XP]` as ANSI string for row-23 HUD overlay.
fn render_xp_hud(total_xp: u64) -> String {
    let (class, xp_in, tier_size) = xp_tier(total_xp);
    let filled = ((xp_in * 8) / tier_size).min(8) as usize;
    let empty  = 8usize.saturating_sub(filled);
    let bar    = "█".repeat(filled) + &"░".repeat(empty);
    format!("\x1b[48;2;15;10;25m\x1b[38;2;180;140;255m[{class} {bar} {xp_in}/{tier_size} XP]\x1b[0m")
}

/// V8: Player position in iso tile space.
#[repr(C)]
#[derive(Clone, Copy)]
struct PlayerState {
    tile_x: i32,
    tile_y: i32,
    facing: u32,
    _pad:   u32,
}

/// V8: One iso room — maps to a todo_roulette task.
#[repr(C)]
#[derive(Clone, Copy)]
struct IsoRoom {
    tile_x:      i32,
    tile_y:      i32,
    room_state:  u32,
    task_idx:    u32,
    tag_color_r: f32,
    tag_color_g: f32,
    tag_color_b: f32,
    _pad:        f32,
}

/// V8: Push constants for iso_render.comp — 16 bytes.
#[repr(C)]
#[derive(Clone, Copy)]
struct IsoPushConst {
    state_phase:   u32,
    player_tile_x: i32,
    player_tile_y: i32,
    _pad:          u32,
}

fn main() {
    // ── CLI args ──────────────────────────────────────────────────────────
    let args: Vec<String> = std::env::args().collect();
    let manifest_path = args
        .windows(2)
        .find(|w| w[0] == "--manifest")
        .map(|w| PathBuf::from(&w[1]))
        .unwrap_or_else(find_manifest);
    // --loop: continuous 33ms render loop for TS --live orchestration.
    // --dungeon: G6 Urca de Lima synthesis — same manifest, dungeon projection.
    // --iso: V8 isometric cRPG vertical slice, diamond-angle terminal rendering.
    // Emits JSON events on stdout; non-JSON lines are ANSI display output.
    let loop_mode    = args.iter().any(|a| a == "--loop");
    let dungeon_mode = args.iter().any(|a| a == "--dungeon");
    let iso_mode     = args.iter().any(|a| a == "--iso");

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
        .filter(|e| e.completed.is_none() && !matches!(e.status.as_deref(), Some("completed") | Some("ghost")))
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
    // RESET_COMMAND_BUFFER: allows per-buffer reset for the G4 render loop.
    let cmd_pool = unsafe {
        device
            .create_command_pool(
                &vk::CommandPoolCreateInfo::default()
                    .queue_family_index(qf_idx)
                    .flags(vk::CommandPoolCreateFlags::RESET_COMMAND_BUFFER),
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

    // G6 dungeon: re-write score_buf in ranked order (room 0 = highest Euler score).
    if dungeon_mode {
        let sorted_scores: Vec<f32> = ranked.iter().map(|(s, _)| *s).collect();
        unsafe {
            let ptr = device.map_memory(score_mem, 0, score_bytes, vk::MemoryMapFlags::empty())
                .expect("map score_mem ranked") as *mut f32;
            for (i, &s) in sorted_scores.iter().enumerate().take(n) {
                ptr.add(i).write(s);
            }
            device.unmap_memory(score_mem);
        }
    }

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

    // ── G3: VkImage 480×80 → ascii_downsample → ANSI stdout ──────────────
    const IMG_W: u32 = 480;
    const IMG_H: u32 = 80;
    const CELL_W: u32 = 8;
    const CELL_H: u32 = 16;
    let cell_cols  = IMG_W / CELL_W;               // 60
    let cell_rows  = IMG_H / CELL_H;               // 5
    let cell_count = (cell_cols * cell_rows) as usize; // 300

    // Create device-local framebuffer image (OPTIMAL tiling, STORAGE | TRANSFER_DST)
    let fb_image = unsafe {
        device
            .create_image(
                &vk::ImageCreateInfo::default()
                    .image_type(vk::ImageType::TYPE_2D)
                    .format(vk::Format::R8G8B8A8_UNORM)
                    .extent(vk::Extent3D { width: IMG_W, height: IMG_H, depth: 1 })
                    .mip_levels(1)
                    .array_layers(1)
                    .samples(vk::SampleCountFlags::TYPE_1)
                    .tiling(vk::ImageTiling::OPTIMAL)
                    .usage(vk::ImageUsageFlags::STORAGE | vk::ImageUsageFlags::TRANSFER_DST)
                    .sharing_mode(vk::SharingMode::EXCLUSIVE)
                    .initial_layout(vk::ImageLayout::UNDEFINED),
                None,
            )
            .expect("create_image G3")
    };
    let img_mem = unsafe {
        let reqs = device.get_image_memory_requirements(fb_image);
        let mem  = device
            .allocate_memory(
                &vk::MemoryAllocateInfo::default()
                    .allocation_size(reqs.size)
                    .memory_type_index(find_memory_type(
                        &instance, pd, reqs.memory_type_bits,
                        vk::MemoryPropertyFlags::DEVICE_LOCAL,
                    )),
                None,
            )
            .expect("allocate image mem G3");
        device.bind_image_memory(fb_image, mem, 0).expect("bind_image_memory G3");
        mem
    };
    let img_view = unsafe {
        device
            .create_image_view(
                &vk::ImageViewCreateInfo::default()
                    .image(fb_image)
                    .view_type(vk::ImageViewType::TYPE_2D)
                    .format(vk::Format::R8G8B8A8_UNORM)
                    .subresource_range(
                        vk::ImageSubresourceRange::default()
                            .aspect_mask(vk::ImageAspectFlags::COLOR)
                            .base_mip_level(0)
                            .level_count(1)
                            .base_array_layer(0)
                            .layer_count(1),
                    ),
                None,
            )
            .expect("create_image_view G3")
    };

    // Output cell buffer: 300 × u32 (HOST_COHERENT — direct readback, no flush)
    let cell_bytes = (cell_count * std::mem::size_of::<u32>()) as u64;
    let (cell_buf, cell_mem) = unsafe {
        alloc_mapped_buffer(&device, &instance, pd, cell_bytes, vk::BufferUsageFlags::STORAGE_BUFFER)
    };

    // ascii_downsample shader + pipeline
    let asc_spv   = include_bytes!("../shaders/ascii_downsample.comp.spv");
    let asc_words: Vec<u32> = asc_spv
        .chunks_exact(4)
        .map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]]))
        .collect();
    let asc_module = unsafe {
        device
            .create_shader_module(&vk::ShaderModuleCreateInfo::default().code(&asc_words), None)
            .expect("create ascii_downsample shader module")
    };
    let asc_bindings = [
        vk::DescriptorSetLayoutBinding::default()
            .binding(0)
            .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
            .descriptor_count(1)
            .stage_flags(vk::ShaderStageFlags::COMPUTE),
        vk::DescriptorSetLayoutBinding::default()
            .binding(1)
            .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
            .descriptor_count(1)
            .stage_flags(vk::ShaderStageFlags::COMPUTE),
    ];
    let asc_dsl = unsafe {
        device
            .create_descriptor_set_layout(
                &vk::DescriptorSetLayoutCreateInfo::default().bindings(&asc_bindings),
                None,
            )
            .expect("asc dsl")
    };
    let asc_pl = unsafe {
        device
            .create_pipeline_layout(
                &vk::PipelineLayoutCreateInfo::default().set_layouts(&[asc_dsl]),
                None,
            )
            .expect("asc pipeline layout")
    };
    let asc_stage = vk::PipelineShaderStageCreateInfo::default()
        .stage(vk::ShaderStageFlags::COMPUTE)
        .module(asc_module)
        .name(c"main");
    let asc_pipeline = unsafe {
        device
            .create_compute_pipelines(
                vk::PipelineCache::null(),
                &[vk::ComputePipelineCreateInfo::default().stage(asc_stage).layout(asc_pl)],
                None,
            )
            .expect("asc pipeline")[0]
    };
    let asc_pool_sizes = [
        vk::DescriptorPoolSize { ty: vk::DescriptorType::STORAGE_IMAGE,  descriptor_count: 1 },
        vk::DescriptorPoolSize { ty: vk::DescriptorType::STORAGE_BUFFER, descriptor_count: 1 },
    ];
    let asc_desc_pool = unsafe {
        device
            .create_descriptor_pool(
                &vk::DescriptorPoolCreateInfo::default().max_sets(1).pool_sizes(&asc_pool_sizes),
                None,
            )
            .expect("asc desc pool")
    };
    let asc_desc_set = unsafe {
        device
            .allocate_descriptor_sets(
                &vk::DescriptorSetAllocateInfo::default()
                    .descriptor_pool(asc_desc_pool)
                    .set_layouts(&[asc_dsl]),
            )
            .expect("asc desc sets")[0]
    };
    let img_info     = vk::DescriptorImageInfo::default()
        .image_layout(vk::ImageLayout::GENERAL)
        .image_view(img_view);
    let cell_buf_info = vk::DescriptorBufferInfo { buffer: cell_buf, offset: 0, range: cell_bytes };
    unsafe {
        device.update_descriptor_sets(
            &[
                vk::WriteDescriptorSet::default()
                    .dst_set(asc_desc_set)
                    .dst_binding(0)
                    .descriptor_type(vk::DescriptorType::STORAGE_IMAGE)
                    .image_info(std::slice::from_ref(&img_info)),
                vk::WriteDescriptorSet::default()
                    .dst_set(asc_desc_set)
                    .dst_binding(1)
                    .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
                    .buffer_info(std::slice::from_ref(&cell_buf_info)),
            ],
            &[],
        )
    };

    // ── G6: dungeon pipeline (4×STORAGE_BUFFER + push_constant uint state_phase) ────
    let dng_spv   = include_bytes!("../shaders/ascii_dungeon.comp.spv");
    let dng_words: Vec<u32> = dng_spv.chunks_exact(4)
        .map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]])).collect();
    let dng_module = unsafe {
        device.create_shader_module(
            &vk::ShaderModuleCreateInfo::default().code(&dng_words), None)
            .expect("dng shader module")
    };
    let dng_bindings = [0u32, 1, 2, 3].map(|i|
        vk::DescriptorSetLayoutBinding::default()
            .binding(i)
            .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
            .descriptor_count(1)
            .stage_flags(vk::ShaderStageFlags::COMPUTE)
    );
    let dng_dsl = unsafe {
        device.create_descriptor_set_layout(
            &vk::DescriptorSetLayoutCreateInfo::default().bindings(&dng_bindings), None)
            .expect("dng dsl")
    };
    let dng_push_range = vk::PushConstantRange::default()
        .stage_flags(vk::ShaderStageFlags::COMPUTE)
        .offset(0).size(std::mem::size_of::<u32>() as u32);
    let dng_pl = unsafe {
        device.create_pipeline_layout(
            &vk::PipelineLayoutCreateInfo::default()
                .set_layouts(&[dng_dsl])
                .push_constant_ranges(&[dng_push_range]),
            None)
            .expect("dng pipeline layout")
    };
    let dng_stage = vk::PipelineShaderStageCreateInfo::default()
        .stage(vk::ShaderStageFlags::COMPUTE).module(dng_module).name(c"main");
    let dng_pipeline = unsafe {
        device.create_compute_pipelines(
            vk::PipelineCache::null(),
            &[vk::ComputePipelineCreateInfo::default().stage(dng_stage).layout(dng_pl)],
            None)
            .expect("dng pipeline")[0]
    };
    let dng_pool_sizes = [vk::DescriptorPoolSize {
        ty: vk::DescriptorType::STORAGE_BUFFER, descriptor_count: 4 }];
    let dng_desc_pool = unsafe {
        device.create_descriptor_pool(
            &vk::DescriptorPoolCreateInfo::default().max_sets(1).pool_sizes(&dng_pool_sizes), None)
            .expect("dng desc pool")
    };
    let dng_desc_set = unsafe {
        device.allocate_descriptor_sets(
            &vk::DescriptorSetAllocateInfo::default()
                .descriptor_pool(dng_desc_pool).set_layouts(&[dng_dsl]))
            .expect("dng desc sets")[0]
    };
    let dng_buf_infos = [
        vk::DescriptorBufferInfo { buffer: task_buf,  offset: 0, range: task_bytes  },
        vk::DescriptorBufferInfo { buffer: score_buf, offset: 0, range: score_bytes },
        vk::DescriptorBufferInfo { buffer: count_buf, offset: 0, range: count_bytes },
        vk::DescriptorBufferInfo { buffer: cell_buf,  offset: 0, range: cell_bytes  },
    ];
    let dng_writes: Vec<vk::WriteDescriptorSet> = dng_buf_infos.iter().enumerate().map(|(i, bi)|
        vk::WriteDescriptorSet::default()
            .dst_set(dng_desc_set).dst_binding(i as u32)
            .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
            .buffer_info(std::slice::from_ref(bi))
    ).collect();
    unsafe { device.update_descriptor_sets(&dng_writes, &[]) };
    println!("cli-renderer  G6     dungeon pipeline ready");

    // ── V8: iso buffers (80×24=1920 cells, player, 12 rooms) ─────────────────
    let iso_cell_cols  = 80u32;
    let iso_cell_rows  = 24u32;
    let iso_cell_count = (iso_cell_cols * iso_cell_rows) as usize; // 1920
    let iso_cell_bytes = (iso_cell_count * std::mem::size_of::<u32>()) as u64; // 7680
    let (iso_cell_buf, iso_cell_mem) = unsafe {
        alloc_mapped_buffer(&device, &instance, pd, iso_cell_bytes, vk::BufferUsageFlags::STORAGE_BUFFER)
    };
    let player_bytes = std::mem::size_of::<PlayerState>() as u64; // 16
    let (player_buf, player_mem) = unsafe {
        alloc_mapped_buffer(&device, &instance, pd, player_bytes, vk::BufferUsageFlags::STORAGE_BUFFER)
    };
    unsafe {
        let ptr = device.map_memory(player_mem, 0, player_bytes, vk::MemoryMapFlags::empty())
            .expect("map player_mem") as *mut PlayerState;
        ptr.write(PlayerState { tile_x: 6, tile_y: 3, facing: 2, _pad: 0 });
        device.unmap_memory(player_mem);
    }
    let iso_room_bytes = (12 * std::mem::size_of::<IsoRoom>()) as u64; // 384
    let (iso_room_buf, iso_room_mem) = unsafe {
        alloc_mapped_buffer(&device, &instance, pd, iso_room_bytes, vk::BufferUsageFlags::STORAGE_BUFFER)
    };
    // Seed 12 rooms from manifest tasks (clamped to available tasks)
    {
        let ptr = unsafe {
            device.map_memory(iso_room_mem, 0, iso_room_bytes, vk::MemoryMapFlags::empty())
                .expect("map iso_room_mem") as *mut IsoRoom
        };
        let room_layout: [(i32, i32); 12] = [
            (2,1),(4,1),(6,1),(8,1),
            (3,2),(5,2),(7,2),
            (2,3),(4,3),(6,3),(8,3),
            (5,4),
        ];
        for (i, &(tx, ty)) in room_layout.iter().enumerate() {
            let task_idx = i.min(gpu_tasks.len().saturating_sub(1)) as u32;
            let phase: f32 = if i < gpu_tasks.len() { gpu_tasks[i].phase_angle } else { 0.0 };
            let rr = (0.5_f32 + 0.5 * phase.cos()).clamp(0.0, 1.0);
            let rg = (0.5_f32 + 0.5 * (phase + 2.0 * std::f32::consts::PI / 3.0).cos()).clamp(0.0, 1.0);
            let rb = (0.5_f32 + 0.5 * (phase + 4.0 * std::f32::consts::PI / 3.0).cos()).clamp(0.0, 1.0);
            unsafe {
                ptr.add(i).write(IsoRoom {
                    tile_x: tx, tile_y: ty,
                    room_state: 0u32,
                    task_idx,
                    tag_color_r: rr, tag_color_g: rg, tag_color_b: rb,
                    _pad: 0.0,
                });
            }
        }
        unsafe { device.unmap_memory(iso_room_mem); }
    }

    // ── V8: iso_render shader + pipeline ─────────────────────────────────────
    let iso_spv   = include_bytes!("../shaders/iso_render.comp.spv");
    let iso_words: Vec<u32> = iso_spv.chunks_exact(4)
        .map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]])).collect();
    let iso_module = unsafe {
        device.create_shader_module(
            &vk::ShaderModuleCreateInfo::default().code(&iso_words), None)
            .expect("iso shader module")
    };
    let iso_bindings = [0u32, 1, 2, 3, 4, 5].map(|i|
        vk::DescriptorSetLayoutBinding::default()
            .binding(i).descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
            .descriptor_count(1).stage_flags(vk::ShaderStageFlags::COMPUTE)
    );
    let iso_dsl = unsafe {
        device.create_descriptor_set_layout(
            &vk::DescriptorSetLayoutCreateInfo::default().bindings(&iso_bindings), None)
            .expect("iso dsl")
    };
    let iso_push_range = vk::PushConstantRange::default()
        .stage_flags(vk::ShaderStageFlags::COMPUTE)
        .offset(0).size(std::mem::size_of::<IsoPushConst>() as u32); // 16
    let iso_pl = unsafe {
        device.create_pipeline_layout(
            &vk::PipelineLayoutCreateInfo::default()
                .set_layouts(&[iso_dsl])
                .push_constant_ranges(&[iso_push_range]),
            None).expect("iso pipeline layout")
    };
    let iso_stage = vk::PipelineShaderStageCreateInfo::default()
        .stage(vk::ShaderStageFlags::COMPUTE).module(iso_module).name(c"main");
    let iso_pipeline = unsafe {
        device.create_compute_pipelines(
            vk::PipelineCache::null(),
            &[vk::ComputePipelineCreateInfo::default().stage(iso_stage).layout(iso_pl)],
            None).expect("iso pipeline")[0]
    };
    let iso_pool_sizes = [vk::DescriptorPoolSize {
        ty: vk::DescriptorType::STORAGE_BUFFER, descriptor_count: 6 }];
    let iso_desc_pool = unsafe {
        device.create_descriptor_pool(
            &vk::DescriptorPoolCreateInfo::default().max_sets(1).pool_sizes(&iso_pool_sizes), None)
            .expect("iso desc pool")
    };
    let iso_desc_set = unsafe {
        device.allocate_descriptor_sets(
            &vk::DescriptorSetAllocateInfo::default()
                .descriptor_pool(iso_desc_pool).set_layouts(&[iso_dsl]))
            .expect("iso desc sets")[0]
    };
    let iso_buf_infos = [
        vk::DescriptorBufferInfo { buffer: task_buf,     offset: 0, range: task_bytes     },
        vk::DescriptorBufferInfo { buffer: score_buf,    offset: 0, range: score_bytes    },
        vk::DescriptorBufferInfo { buffer: count_buf,    offset: 0, range: count_bytes    },
        vk::DescriptorBufferInfo { buffer: iso_cell_buf, offset: 0, range: iso_cell_bytes },
        vk::DescriptorBufferInfo { buffer: player_buf,   offset: 0, range: player_bytes   },
        vk::DescriptorBufferInfo { buffer: iso_room_buf, offset: 0, range: iso_room_bytes },
    ];
    let iso_writes: Vec<vk::WriteDescriptorSet> = iso_buf_infos.iter().enumerate().map(|(i, bi)|
        vk::WriteDescriptorSet::default()
            .dst_set(iso_desc_set).dst_binding(i as u32)
            .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
            .buffer_info(std::slice::from_ref(bi))
    ).collect();
    unsafe { device.update_descriptor_sets(&iso_writes, &[]) };
    println!("cli-renderer  V8     iso pipeline ready");

    // G3 command buffer (fresh allocation from existing pool)
    let g3_cmd = unsafe {
        device
            .allocate_command_buffers(
                &vk::CommandBufferAllocateInfo::default()
                    .command_pool(cmd_pool)
                    .level(vk::CommandBufferLevel::PRIMARY)
                    .command_buffer_count(1),
            )
            .expect("alloc g3 cmd")[0]
    };
    unsafe {
        device
            .begin_command_buffer(
                g3_cmd,
                &vk::CommandBufferBeginInfo::default()
                    .flags(vk::CommandBufferUsageFlags::ONE_TIME_SUBMIT),
            )
            .expect("begin g3 cmd");

        // 1. UNDEFINED → TRANSFER_DST_OPTIMAL
        transition_image_layout(
            &device, g3_cmd, fb_image,
            vk::ImageLayout::UNDEFINED, vk::ImageLayout::TRANSFER_DST_OPTIMAL,
            vk::PipelineStageFlags::TOP_OF_PIPE, vk::PipelineStageFlags::TRANSFER,
            vk::AccessFlags::empty(),            vk::AccessFlags::TRANSFER_WRITE,
        );

        // 2. Fill with hue derived from top-ranked task phase angle
        let (fill_r, fill_g, fill_b) = if let Some((_score, entry)) = ranked.first() {
            let phase = phase_radians(&entry.tags);
            let r = (0.5 + 0.5 * phase.cos()).clamp(0.0, 1.0);
            let g = (0.5 + 0.5 * (phase + 2.0 * std::f32::consts::PI / 3.0).cos()).clamp(0.0, 1.0);
            let b = (0.5 + 0.5 * (phase + 4.0 * std::f32::consts::PI / 3.0).cos()).clamp(0.0, 1.0);
            (r, g, b)
        } else {
            (0.4_f32, 0.1_f32, 0.6_f32)
        };
        let subres_range = vk::ImageSubresourceRange::default()
            .aspect_mask(vk::ImageAspectFlags::COLOR)
            .base_mip_level(0).level_count(1)
            .base_array_layer(0).layer_count(1);
        device.cmd_clear_color_image(
            g3_cmd, fb_image,
            vk::ImageLayout::TRANSFER_DST_OPTIMAL,
            &vk::ClearColorValue { float32: [fill_r, fill_g, fill_b, 1.0] },
            &[subres_range],
        );

        // 3. TRANSFER_DST_OPTIMAL → GENERAL (storage image read for ascii_downsample)
        transition_image_layout(
            &device, g3_cmd, fb_image,
            vk::ImageLayout::TRANSFER_DST_OPTIMAL, vk::ImageLayout::GENERAL,
            vk::PipelineStageFlags::TRANSFER,      vk::PipelineStageFlags::COMPUTE_SHADER,
            vk::AccessFlags::TRANSFER_WRITE,       vk::AccessFlags::SHADER_READ,
        );

        // 4. Dispatch: polar (ascii_downsample) or dungeon (ascii_dungeon) or iso (iso_render)
        if dungeon_mode {
            // Dungeon path: no VkImage used, dispatch directly to cell_buf.
            device.cmd_bind_pipeline(g3_cmd, vk::PipelineBindPoint::COMPUTE, dng_pipeline);
            device.cmd_bind_descriptor_sets(
                g3_cmd, vk::PipelineBindPoint::COMPUTE, dng_pl, 0, &[dng_desc_set], &[],
            );
            device.cmd_push_constants(
                g3_cmd, dng_pl, vk::ShaderStageFlags::COMPUTE, 0, &0u32.to_ne_bytes());
            device.cmd_dispatch(g3_cmd, 8, 1, 1); // local(8,8,1): ceil(60/8)=8x, rows guarded
        } else if iso_mode {
            // Iso path: dispatch to iso_cell_buf (80×24).
            let player_state: PlayerState = unsafe {
                let ptr = device.map_memory(player_mem, 0, player_bytes, vk::MemoryMapFlags::empty())
                    .expect("map player for push") as *const PlayerState;
                let s = *ptr; device.unmap_memory(player_mem); s
            };
            let push = IsoPushConst {
                state_phase: 0u32,
                player_tile_x: player_state.tile_x,
                player_tile_y: player_state.tile_y,
                _pad: 0,
            };
            let push_bytes: [u8; 16] = unsafe { std::mem::transmute(push) };
            device.cmd_bind_pipeline(g3_cmd, vk::PipelineBindPoint::COMPUTE, iso_pipeline);
            device.cmd_bind_descriptor_sets(
                g3_cmd, vk::PipelineBindPoint::COMPUTE, iso_pl, 0, &[iso_desc_set], &[],
            );
            device.cmd_push_constants(g3_cmd, iso_pl, vk::ShaderStageFlags::COMPUTE, 0, &push_bytes);
            device.cmd_dispatch(g3_cmd, 10, 3, 1); // ceil(80/8)=10, ceil(24/8)=3
        } else {
            device.cmd_bind_pipeline(g3_cmd, vk::PipelineBindPoint::COMPUTE, asc_pipeline);
            device.cmd_bind_descriptor_sets(
                g3_cmd, vk::PipelineBindPoint::COMPUTE, asc_pl, 0, &[asc_desc_set], &[],
            );
            device.cmd_dispatch(g3_cmd, cell_cols, cell_rows, 1);
        }
        device.end_command_buffer(g3_cmd).expect("end g3 cmd");
    }

    let g3_fence = unsafe {
        device.create_fence(&vk::FenceCreateInfo::default(), None).expect("g3 fence")
    };
    unsafe {
        let submit = vk::SubmitInfo::default().command_buffers(std::slice::from_ref(&g3_cmd));
        device.queue_submit(queue, &[submit], g3_fence).expect("g3 submit");
        device.wait_for_fences(&[g3_fence], true, u64::MAX).expect("g3 wait");
    }

    // Read back cells[] → decode ANSI truecolor block characters
    // Indices 0–4: polar density (ascii_downsample). Indices 5–12: box-drawing (dungeon).
    const BLOCK_CHARS: &[&str] = &[
        " ", "░", "▒", "▓", "█",                  // 0-4:  density blocks (polar mode)
        "╔", "═", "╗", "║", "╚", "╝", "·", "╬",  // 5-12: box-drawing (dungeon mode)
        "◆", "◇", "╱", "╲", "▲", "▼", "@", "☥",  // 13-20: iso cRPG (V8)
    ];
    let cells: Vec<u32> = unsafe {
        let ptr = device
            .map_memory(cell_mem, 0, cell_bytes, vk::MemoryMapFlags::empty())
            .expect("map cell_mem") as *const u32;
        let v = std::slice::from_raw_parts(ptr, cell_count).to_vec();
        device.unmap_memory(cell_mem);
        v
    };
    println!();
    for row in 0..cell_rows as usize {
        let mut line = String::new();
        for col in 0..cell_cols as usize {
            let cell = cells[row * cell_cols as usize + col];
            let idx  = ((cell >> 24) & 0xFF) as usize;
            let r    = (cell >> 16) & 0xFF;
            let g    = (cell >>  8) & 0xFF;
            let b    =  cell        & 0xFF;
            let ch   = BLOCK_CHARS.get(idx).copied().unwrap_or("█");
            line.push_str(&format!("\x1b[38;2;{r};{g};{b}m{ch}"));
        }
        line.push_str("\x1b[0m");
        println!("{line}");
    }
    println!();
    println!("cli-renderer  G3 ✓  480×80 VkImage → ascii_downsample.comp.spv → {cell_count} cells → ANSI stdout");
    if iso_mode {
        // V8: iso one-shot readback and print (80×24 grid)
        let iso_cells: Vec<u32> = unsafe {
            let ptr = device.map_memory(iso_cell_mem, 0, iso_cell_bytes, vk::MemoryMapFlags::empty())
                .expect("map iso_cell_mem") as *const u32;
            let v = std::slice::from_raw_parts(ptr, iso_cell_count).to_vec();
            device.unmap_memory(iso_cell_mem);
            v
        };
        println!();
        for row in 0..iso_cell_rows as usize {
            let mut line = String::new();
            for col in 0..iso_cell_cols as usize {
                let cell = iso_cells[row * iso_cell_cols as usize + col];
                let idx  = ((cell >> 24) & 0xFF) as usize;
                let r    = (cell >> 16) & 0xFF;
                let g    = (cell >>  8) & 0xFF;
                let b    =  cell        & 0xFF;
                let ch   = BLOCK_CHARS.get(idx).copied().unwrap_or(" ");
                line.push_str(&format!("\x1b[38;2;{r};{g};{b}m{ch}"));
            }
            line.push_str("\x1b[0m");
            println!("{line}");
        }
        println!();
        println!("cli-renderer  V8 ✓  iso cRPG  {iso_cell_cols}×{iso_cell_rows} terminal grid → diamond-angle Vulkan");
    }
    if !loop_mode {
        println!("cli-renderer  →     G4: prev_frame VkImage + GPU diff pass → dirty-cell cursor positioning");
    }

    // ── G4: dirty-cell render loop (activated by --loop) ──────────────────
    // Architecture: TS --live spawns this binary with --loop. stdout = ANSI display
    // (passed through to user terminal). stderr = JSON events (captured by TS for IPC).
    // Containment contract: agents can only act on manifest entries; roulette physics
    // determine selection. The manifest is the safe boundary.
    if loop_mode {
        use std::io::{BufRead, Write};
        use std::sync::mpsc;
        use std::time::{Duration, Instant};
        use crossterm::event::{self as ct_event, Event, KeyCode, KeyEventKind, KeyModifiers};
        use crossterm::terminal::{enable_raw_mode, disable_raw_mode};

        // Allocate prev_cells and dirty-flag buffers (HOST_COHERENT STORAGE_BUFFER, 300×u32).
        let (prev_buf, prev_mem) = unsafe {
            alloc_mapped_buffer(&device, &instance, pd, cell_bytes, vk::BufferUsageFlags::STORAGE_BUFFER)
        };
        let (dirty_buf, dirty_mem) = unsafe {
            alloc_mapped_buffer(&device, &instance, pd, cell_bytes, vk::BufferUsageFlags::STORAGE_BUFFER)
        };

        // ── dirty_diff shader + pipeline ──────────────────────────────────
        let diff_spv   = include_bytes!("../shaders/dirty_diff.comp.spv");
        let diff_words: Vec<u32> = diff_spv
            .chunks_exact(4)
            .map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]]))
            .collect();
        let diff_module = unsafe {
            device
                .create_shader_module(&vk::ShaderModuleCreateInfo::default().code(&diff_words), None)
                .expect("dirty_diff shader module")
        };
        let diff_bindings = [0u32, 1u32, 2u32].map(|i| {
            vk::DescriptorSetLayoutBinding::default()
                .binding(i)
                .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
                .descriptor_count(1)
                .stage_flags(vk::ShaderStageFlags::COMPUTE)
        });
        let diff_dsl = unsafe {
            device
                .create_descriptor_set_layout(
                    &vk::DescriptorSetLayoutCreateInfo::default().bindings(&diff_bindings),
                    None,
                )
                .expect("diff dsl")
        };
        let diff_pc_range = vk::PushConstantRange::default()
            .stage_flags(vk::ShaderStageFlags::COMPUTE)
            .offset(0)
            .size(4); // cell_count as u32
        let diff_pl = unsafe {
            device
                .create_pipeline_layout(
                    &vk::PipelineLayoutCreateInfo::default()
                        .set_layouts(&[diff_dsl])
                        .push_constant_ranges(std::slice::from_ref(&diff_pc_range)),
                    None,
                )
                .expect("diff pipeline layout")
        };
        let diff_stage = vk::PipelineShaderStageCreateInfo::default()
            .stage(vk::ShaderStageFlags::COMPUTE)
            .module(diff_module)
            .name(c"main");
        let diff_pipeline = unsafe {
            device
                .create_compute_pipelines(
                    vk::PipelineCache::null(),
                    &[vk::ComputePipelineCreateInfo::default().stage(diff_stage).layout(diff_pl)],
                    None,
                )
                .expect("diff pipeline")[0]
        };
        let diff_pool_sizes = [vk::DescriptorPoolSize {
            ty: vk::DescriptorType::STORAGE_BUFFER, descriptor_count: 3,
        }];
        let diff_desc_pool = unsafe {
            device
                .create_descriptor_pool(
                    &vk::DescriptorPoolCreateInfo::default()
                        .max_sets(1)
                        .pool_sizes(&diff_pool_sizes),
                    None,
                )
                .expect("diff desc pool")
        };
        let diff_desc_set = unsafe {
            device
                .allocate_descriptor_sets(
                    &vk::DescriptorSetAllocateInfo::default()
                        .descriptor_pool(diff_desc_pool)
                        .set_layouts(&[diff_dsl]),
                )
                .expect("diff desc sets")[0]
        };
        // binding 0 = curr (cell_buf), binding 1 = prev, binding 2 = dirty
        let diff_buf_infos = [
            vk::DescriptorBufferInfo { buffer: cell_buf,  offset: 0, range: cell_bytes },
            vk::DescriptorBufferInfo { buffer: prev_buf,  offset: 0, range: cell_bytes },
            vk::DescriptorBufferInfo { buffer: dirty_buf, offset: 0, range: cell_bytes },
        ];
        let diff_writes: Vec<vk::WriteDescriptorSet> = diff_buf_infos
            .iter()
            .enumerate()
            .map(|(i, bi)| {
                vk::WriteDescriptorSet::default()
                    .dst_set(diff_desc_set)
                    .dst_binding(i as u32)
                    .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
                    .buffer_info(std::slice::from_ref(bi))
            })
            .collect();
        unsafe { device.update_descriptor_sets(&diff_writes, &[]) };

        // Diff command buffer + fence (distinct from G3).
        let diff_cmd = unsafe {
            device
                .allocate_command_buffers(
                    &vk::CommandBufferAllocateInfo::default()
                        .command_pool(cmd_pool)
                        .level(vk::CommandBufferLevel::PRIMARY)
                        .command_buffer_count(1),
                )
                .expect("alloc diff cmd")[0]
        };
        let diff_fence = unsafe {
            device.create_fence(&vk::FenceCreateInfo::default(), None).expect("diff fence")
        };

        // V9: raw keypress reader (iso) or line-based IPC (polar/dungeon).
        // TS --live sends {"cmd":"quit"} to terminate cleanly.
        let (stdin_tx, stdin_rx) = mpsc::channel::<String>();
        if iso_mode {
            // Raw mode: immediate keypress, no Enter required.
            enable_raw_mode().expect("enable raw mode");
            std::thread::spawn(move || {
                loop {
                    if let Ok(Event::Key(ke)) = ct_event::read() {
                        if ke.kind != KeyEventKind::Press { continue; }
                        let cmd: String = match ke.code {
                            KeyCode::Char('q') | KeyCode::Esc => "{\"cmd\":\"quit\"}".into(),
                            KeyCode::Char('c') if ke.modifiers.contains(KeyModifiers::CONTROL) => "{\"cmd\":\"quit\"}".into(),
                            KeyCode::Char('w') | KeyCode::Up    => "w".into(),
                            KeyCode::Char('s') | KeyCode::Down  => "s".into(),
                            KeyCode::Char('a') | KeyCode::Left  => "a".into(),
                            KeyCode::Char('d') | KeyCode::Right => "d".into(),
                            _ => continue,
                        };
                        if stdin_tx.send(cmd).is_err() { break; }
                    }
                }
            });
        } else {
            std::thread::spawn(move || {
                for line in std::io::stdin().lock().lines().flatten() {
                    if stdin_tx.send(line).is_err() { break; }
                }
            });
        }

        // Ready event: TS orchestrator waits for this line before interacting.
        eprintln!("{{\"event\":\"ready\"}}");

        let frame_target = Duration::from_millis(33);
        let mut frame_count: u64 = 0;
        // G5: SpinState == RoomState — state drives both animation phase (polar) and room visual (dungeon).
        let mut spin_state = StatePhase::Idle;
        // Ω-2: last room index the player stepped on — prevents state advancing every frame.
        let mut last_entered_room: i32 = -1;
        // Ω-3: trail directory + cleared-room dedup tracker.
        let trail_dir: std::path::PathBuf = manifest_path
            .parent()
            .and_then(|p| p.parent())
            .map(|p| p.join(".chthonic").join("trail"))
            .unwrap_or_else(|| std::path::PathBuf::from(".chthonic/trail"));
        let mut cleared_rooms: std::collections::HashSet<usize> = std::collections::HashSet::new();
        // Ω-4: load base XP from .chthonic/xp-state.json (cross-session persistence).
        let base_xp: u64 = {
            let xp_path = trail_dir.parent()
                .map(|d| d.join("xp-state.json"))
                .unwrap_or_else(|| std::path::PathBuf::from(".chthonic/xp-state.json"));
            std::fs::read_to_string(&xp_path).ok()
                .and_then(|s| serde_json::from_str::<serde_json::Value>(&s).ok())
                .and_then(|v| v["xp"].as_u64())
                .unwrap_or(0)
        };

        print!("\x1B[?25l"); // hide cursor for flicker-free overwrite
        std::io::stdout().flush().ok();

        // G3 one-shot printed:
        //   println!()        → blank line      (+1)
        //   println!(row 0-4) → 5 cell rows     (+5)
        //   println!()        → blank line      (+1)
        //   println!(G3 ✓)    → status          (+1)
        // Total: 8 lines above cursor at loop entry.
        // Each loop iter after frame 0 reprints: blank+5rows+status = 7 lines, cursor on status (no NL).
        // So: frame 0 needs `up=8`, frame N needs `up=6` (blank+5rows ends on last row, + status no-NL).

        'render: loop {
            let t0 = Instant::now();

            // Drain IPC commands (non-blocking).
            while let Ok(cmd) = stdin_rx.try_recv() {
                if cmd.contains("\"quit\"") { break 'render; }
                if iso_mode {
                    let trimmed = cmd.trim();
                    let delta: Option<(i32, i32)> = match trimmed {
                        "w" => Some((0, -1)),
                        "s" => Some((0,  1)),
                        "a" => Some((-1, 0)),
                        "d" => Some(( 1, 0)),
                        _ => None,
                    };
                    if let Some((dx, dy)) = delta {
                        unsafe {
                            let ptr = device.map_memory(player_mem, 0, player_bytes, vk::MemoryMapFlags::empty())
                                .expect("map player WASD") as *mut PlayerState;
                            (*ptr).tile_x = ((*ptr).tile_x + dx).max(0).min(11);
                            (*ptr).tile_y = ((*ptr).tile_y + dy).max(0).min(5);
                            device.unmap_memory(player_mem);
                        }
                    }
                }
            }

            // Ω-2: room_state mutation — advance state once per new tile the player steps onto.
            if iso_mode {
                unsafe {
                    let pptr = device.map_memory(player_mem, 0, player_bytes, vk::MemoryMapFlags::empty())
                        .expect("map player Ω2") as *const PlayerState;
                    let (px, py) = ((*pptr).tile_x, (*pptr).tile_y);
                    device.unmap_memory(player_mem);

                    let rptr = device.map_memory(iso_room_mem, 0, iso_room_bytes, vk::MemoryMapFlags::empty())
                        .expect("map iso_room Ω2") as *mut IsoRoom;
                    let mut entered: i32 = -1;
                    for i in 0..12usize {
                        let room = &*rptr.add(i);
                        if room.tile_x == px && room.tile_y == py {
                            entered = i as i32;
                            if entered != last_entered_room {
                                let r = &mut *rptr.add(i);
                                if r.room_state < 3 {
                                    r.room_state += 1;
                                    // Ω-3: room cleared → emit roulette_steward trail event.
                                    if r.room_state == 3 && !cleared_rooms.contains(&i) {
                                        cleared_rooms.insert(i);
                                        let task_title = active
                                            .get(r.task_idx as usize)
                                            .map(|e| e.title.as_str())
                                            .unwrap_or("unknown task");
                                        write_trail_event(&trail_dir, task_title);
                                    }
                                }
                            }
                            break;
                        }
                    }
                    device.unmap_memory(iso_room_mem);
                    last_entered_room = entered;
                }
            }

            // G5: advance SpinState FSM each frame (drives polar arc phase + iso room visual cue).
            spin_state = tick_state(spin_state, frame_count);

            // ── Re-record + submit G3 ─────────────────────────────────────
            // UNDEFINED→TRANSFER_DST is valid every frame because we immediately clear.
            unsafe {
                device.reset_command_buffer(g3_cmd, vk::CommandBufferResetFlags::empty())
                    .expect("reset g3_cmd");
                device.reset_fences(&[g3_fence]).expect("reset g3 fence");
                device.begin_command_buffer(
                    g3_cmd,
                    &vk::CommandBufferBeginInfo::default()
                        .flags(vk::CommandBufferUsageFlags::ONE_TIME_SUBMIT),
                ).expect("begin g3 loop");

                transition_image_layout(
                    &device, g3_cmd, fb_image,
                    vk::ImageLayout::UNDEFINED,             vk::ImageLayout::TRANSFER_DST_OPTIMAL,
                    vk::PipelineStageFlags::TOP_OF_PIPE,    vk::PipelineStageFlags::TRANSFER,
                    vk::AccessFlags::empty(),               vk::AccessFlags::TRANSFER_WRITE,
                );

                let (fr, fg, fb_) = if let Some((_score, entry)) = ranked.first() {
                    let ph = phase_radians(&entry.tags);
                    (
                        (0.5 + 0.5 * ph.cos()).clamp(0.0, 1.0),
                        (0.5 + 0.5 * (ph + 2.0 * std::f32::consts::PI / 3.0).cos()).clamp(0.0, 1.0),
                        (0.5 + 0.5 * (ph + 4.0 * std::f32::consts::PI / 3.0).cos()).clamp(0.0, 1.0),
                    )
                } else { (0.4_f32, 0.1_f32, 0.6_f32) };

                let subres = vk::ImageSubresourceRange::default()
                    .aspect_mask(vk::ImageAspectFlags::COLOR)
                    .base_mip_level(0).level_count(1).base_array_layer(0).layer_count(1);
                device.cmd_clear_color_image(
                    g3_cmd, fb_image, vk::ImageLayout::TRANSFER_DST_OPTIMAL,
                    &vk::ClearColorValue { float32: [fr, fg, fb_, 1.0] }, &[subres],
                );
                transition_image_layout(
                    &device, g3_cmd, fb_image,
                    vk::ImageLayout::TRANSFER_DST_OPTIMAL, vk::ImageLayout::GENERAL,
                    vk::PipelineStageFlags::TRANSFER,      vk::PipelineStageFlags::COMPUTE_SHADER,
                    vk::AccessFlags::TRANSFER_WRITE,       vk::AccessFlags::SHADER_READ,
                );
                if dungeon_mode {
                    // Dungeon G6: skip VkImage ops, dispatch dungeon shader with state_phase.
                    device.cmd_bind_pipeline(g3_cmd, vk::PipelineBindPoint::COMPUTE, dng_pipeline);
                    device.cmd_bind_descriptor_sets(
                        g3_cmd, vk::PipelineBindPoint::COMPUTE, dng_pl, 0, &[dng_desc_set], &[],
                    );
                    device.cmd_push_constants(
                        g3_cmd, dng_pl, vk::ShaderStageFlags::COMPUTE, 0,
                        &(spin_state as u32).to_ne_bytes());
                    device.cmd_dispatch(g3_cmd, 8, 1, 1);
                } else if iso_mode {
                    // Iso V8: dispatch to iso_cell_buf (80×24) with player push constant.
                    let player_state: PlayerState = {
                        let ptr = device.map_memory(player_mem, 0, player_bytes, vk::MemoryMapFlags::empty())
                            .expect("map player loop") as *const PlayerState;
                        let s = *ptr; device.unmap_memory(player_mem); s
                    };
                    let push = IsoPushConst {
                        state_phase: spin_state as u32,
                        player_tile_x: player_state.tile_x,
                        player_tile_y: player_state.tile_y,
                        _pad: 0,
                    };
                    let push_bytes: [u8; 16] = std::mem::transmute(push);
                    device.cmd_bind_pipeline(g3_cmd, vk::PipelineBindPoint::COMPUTE, iso_pipeline);
                    device.cmd_bind_descriptor_sets(
                        g3_cmd, vk::PipelineBindPoint::COMPUTE, iso_pl, 0, &[iso_desc_set], &[],
                    );
                    device.cmd_push_constants(g3_cmd, iso_pl, vk::ShaderStageFlags::COMPUTE, 0, &push_bytes);
                    device.cmd_dispatch(g3_cmd, 10, 3, 1);
                } else {
                    // Polar G3: image-based ascii downsample.
                    device.cmd_bind_pipeline(g3_cmd, vk::PipelineBindPoint::COMPUTE, asc_pipeline);
                    device.cmd_bind_descriptor_sets(
                        g3_cmd, vk::PipelineBindPoint::COMPUTE, asc_pl, 0, &[asc_desc_set], &[],
                    );
                    device.cmd_dispatch(g3_cmd, cell_cols, cell_rows, 1);
                }
                device.end_command_buffer(g3_cmd).expect("end g3 loop");

                let sub = vk::SubmitInfo::default().command_buffers(std::slice::from_ref(&g3_cmd));
                device.queue_submit(queue, &[sub], g3_fence).expect("g3 loop submit");
                device.wait_for_fences(&[g3_fence], true, u64::MAX).expect("g3 loop wait");
            }

            // Read curr_cells (polar/dungeon) or iso_cells (iso mode).
            let curr_cells: Vec<u32> = unsafe {
                let ptr = device
                    .map_memory(cell_mem, 0, cell_bytes, vk::MemoryMapFlags::empty())
                    .expect("map cell_mem loop") as *const u32;
                let v = std::slice::from_raw_parts(ptr, cell_count).to_vec();
                device.unmap_memory(cell_mem);
                v
            };
            // V8: iso display uses a separate larger cell buffer.
            let (display_cells, display_cols, display_rows): (Vec<u32>, usize, usize) = if iso_mode {
                let iso_cells = unsafe {
                    let ptr = device.map_memory(iso_cell_mem, 0, iso_cell_bytes, vk::MemoryMapFlags::empty())
                        .expect("map iso_cell loop") as *const u32;
                    let v = std::slice::from_raw_parts(ptr, iso_cell_count).to_vec();
                    device.unmap_memory(iso_cell_mem);
                    v
                };
                (iso_cells, iso_cell_cols as usize, iso_cell_rows as usize)
            } else {
                (curr_cells.clone(), cell_cols as usize, cell_rows as usize)
            };

            // ── Dispatch dirty_diff ───────────────────────────────────────
            unsafe {
                device.reset_command_buffer(diff_cmd, vk::CommandBufferResetFlags::empty())
                    .expect("reset diff_cmd");
                device.reset_fences(&[diff_fence]).expect("reset diff fence");
                device.begin_command_buffer(
                    diff_cmd,
                    &vk::CommandBufferBeginInfo::default()
                        .flags(vk::CommandBufferUsageFlags::ONE_TIME_SUBMIT),
                ).expect("begin diff cmd");

                device.cmd_bind_pipeline(diff_cmd, vk::PipelineBindPoint::COMPUTE, diff_pipeline);
                device.cmd_bind_descriptor_sets(
                    diff_cmd, vk::PipelineBindPoint::COMPUTE, diff_pl, 0, &[diff_desc_set], &[],
                );
                device.cmd_push_constants(
                    diff_cmd, diff_pl, vk::ShaderStageFlags::COMPUTE, 0,
                    &(cell_count as u32).to_ne_bytes(),
                );
                let groups = ((cell_count as u32) + 63) / 64;
                device.cmd_dispatch(diff_cmd, groups, 1, 1);
                device.end_command_buffer(diff_cmd).expect("end diff cmd");

                let sub = vk::SubmitInfo::default().command_buffers(std::slice::from_ref(&diff_cmd));
                device.queue_submit(queue, &[sub], diff_fence).expect("diff submit");
                device.wait_for_fences(&[diff_fence], true, u64::MAX).expect("diff wait");
            }

            // Read dirty count (sum of dirty[] — the IPC telemetry signal).
            let dirty_count: u32 = unsafe {
                let ptr = device
                    .map_memory(dirty_mem, 0, cell_bytes, vk::MemoryMapFlags::empty())
                    .expect("map dirty_mem") as *const u32;
                let v: u32 = std::slice::from_raw_parts(ptr, cell_count).iter().sum();
                device.unmap_memory(dirty_mem);
                v
            };

            // ── ANSI overwrite-in-place (no clear-screen, no flicker) ──────
            // up: iso=24 rows → 26/25; polar/dungeon=5 rows → 8/6.
            let up: u32 = if iso_mode {
                if frame_count == 0 { 26 } else { 25 }
            } else if frame_count == 0 { 8 } else { 6 };
            print!("\x1B[{up}A\r\n");
            for row in 0..display_rows {
                print!("\r");
                for col in 0..display_cols {
                    let cell = display_cells[row * display_cols + col];
                    let idx  = ((cell >> 24) & 0xFF) as usize;
                    let r    = (cell >> 16) & 0xFF;
                    let g    = (cell >>  8) & 0xFF;
                    let b    =  cell        & 0xFF;
                    let ch   = BLOCK_CHARS.get(idx).copied().unwrap_or("█");
                    print!("\x1b[38;2;{r};{g};{b}m{ch}");
                }
                print!("\x1b[0m\n");
            }
            // Ω-4: XP HUD overlay — rewrite left half of iso row 23 with progress bar.
            if iso_mode {
                let total_xp = base_xp + (cleared_rooms.len() as u64 * 33);
                let hud = render_xp_hud(total_xp);
                // Cursor sits at status-line position (1 line below row 23). Step up, write, step back.
                print!("\x1B[1A\r{hud}\x1B[1B\r");
            }
            let elapsed_ms = t0.elapsed().as_millis();
            let mode_label = if dungeon_mode { "dungeon" } else if iso_mode { "iso" } else { "polar" };
            let cell_total = if iso_mode { iso_cell_count } else { cell_count };
            print!("\r\x1b[2m  G5 frame:{frame_count:>6}  Δcells:{dirty_count:>3}/{cell_total}  {elapsed_ms:>3}ms  [{mode_label}:{state}]\x1b[0m",
                state = state_label(spin_state));
            std::io::stdout().flush().ok();

            // Copy curr → prev (1200 bytes on CPU; no GPU copy needed at this scale).
            unsafe {
                let src = device
                    .map_memory(cell_mem, 0, cell_bytes, vk::MemoryMapFlags::empty())
                    .expect("map cell for curr→prev") as *const u32;
                let dst = device
                    .map_memory(prev_mem, 0, cell_bytes, vk::MemoryMapFlags::empty())
                    .expect("map prev for curr→prev") as *mut u32;
                std::ptr::copy_nonoverlapping(src, dst, cell_count);
                device.unmap_memory(cell_mem);
                device.unmap_memory(prev_mem);
            }

            // Machine-readable frame event on stderr (TS --live reads this).
            eprintln!("{{\"event\":\"frame\",\"frame\":{frame_count},\"dirty\":{dirty_count},\"state\":{phase}}}",
                phase = spin_state as u32);
            frame_count += 1;

            // Sleep remainder of 33ms budget.
            let elapsed = t0.elapsed();
            if elapsed < frame_target { std::thread::sleep(frame_target - elapsed); }
        } // 'render

        // V9: restore terminal on exit.
        if iso_mode { let _ = disable_raw_mode(); }
        // Restore cursor visibility; move past render area.
        print!("\x1B[?25h\n");
        std::io::stdout().flush().ok();
        eprintln!("{{\"event\":\"stopped\",\"frames\":{frame_count}}}");

        // Cleanup G4-specific resources (before the main cleanup below).
        unsafe {
            device.destroy_fence(diff_fence, None);
            device.destroy_descriptor_pool(diff_desc_pool, None);
            device.destroy_pipeline(diff_pipeline, None);
            device.destroy_pipeline_layout(diff_pl, None);
            device.destroy_descriptor_set_layout(diff_dsl, None);
            device.destroy_shader_module(diff_module, None);
            device.free_memory(dirty_mem, None);
            device.destroy_buffer(dirty_buf, None);
            device.free_memory(prev_mem, None);
            device.destroy_buffer(prev_buf, None);
        }
    } // end loop_mode

    // ── cleanup ───────────────────────────────────────────────────────────
    unsafe {
        // V8 iso pipeline resources
        device.destroy_descriptor_pool(iso_desc_pool, None);
        device.destroy_pipeline(iso_pipeline, None);
        device.destroy_pipeline_layout(iso_pl, None);
        device.destroy_descriptor_set_layout(iso_dsl, None);
        device.destroy_shader_module(iso_module, None);
        device.free_memory(iso_room_mem, None);
        device.destroy_buffer(iso_room_buf, None);
        device.free_memory(player_mem, None);
        device.destroy_buffer(player_buf, None);
        device.free_memory(iso_cell_mem, None);
        device.destroy_buffer(iso_cell_buf, None);
        // G6 dungeon pipeline resources
        device.destroy_descriptor_pool(dng_desc_pool, None);
        device.destroy_pipeline(dng_pipeline, None);
        device.destroy_pipeline_layout(dng_pl, None);
        device.destroy_descriptor_set_layout(dng_dsl, None);
        device.destroy_shader_module(dng_module, None);
        device.destroy_fence(g3_fence, None);
        device.destroy_descriptor_pool(asc_desc_pool, None);
        device.destroy_pipeline(asc_pipeline, None);
        device.destroy_pipeline_layout(asc_pl, None);
        device.destroy_descriptor_set_layout(asc_dsl, None);
        device.destroy_shader_module(asc_module, None);
        device.free_memory(cell_mem, None);
        device.destroy_buffer(cell_buf, None);
        device.destroy_image_view(img_view, None);
        device.free_memory(img_mem, None);
        device.destroy_image(fb_image, None);
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
