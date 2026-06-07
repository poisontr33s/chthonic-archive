// @SID: ARCHIPELAGO_ADVECT_V0
// L−2 · ADVECT — the field stops spreading and starts MOVING.
//
// L−4 diffused (isotropic relaxation). L−2 ADVECTS: a velocity field, interpolated from
// each island's live wind, carries the field downwind by semi-Lagrangian backtrace. We seed
// one warm blob at the flagship island and run N steps — and the heat drifts off its origin,
// downwind, smearing as it goes. The origin cools; the trail warms. That is transport, not
// diffusion: the same blob under L−4 would spread symmetrically; here it goes WHERE THE WIND
// GOES. The wind is real (Open-Meteo wind_direction_10m / wind_speed_10m, via the barometer).
//
//   cargo run --bin archipelago_advect -- [<boundary.json>] [--steps N] [--scale S]
//   default path: ../../CLAUDEBASE/charts/archipelago.json (no wind → still wind=0, blob sits)
//   feed it a live boundary:  ../../live_boundary.json     (barometer --boundary writes wind)

use std::{ffi::CStr, mem, path::PathBuf};

use ash::{vk, Device, Entry, Instance};
use serde::Deserialize;

#[derive(Deserialize)]
struct Twin {
    islands: Vec<IslandJson>,
}
#[derive(Deserialize)]
struct IslandJson {
    lat: f32,
    lon: f32,
    #[serde(default)]
    wind_dir: Option<f32>, // meteorological: degrees the wind comes FROM, clockwise from north
    #[serde(default)]
    wind_speed: Option<f32>, // m/s
    #[serde(default)]
    isle: String,
}

#[repr(C)]
#[derive(Clone, Copy)]
struct Push {
    w: u32,
    h: u32,
}

const W: u32 = 56;
const H: u32 = 22;

unsafe fn find_memory_type(instance: &Instance, pd: vk::PhysicalDevice, filter: u32, flags: vk::MemoryPropertyFlags) -> u32 {
    let props = instance.get_physical_device_memory_properties(pd);
    (0..props.memory_type_count)
        .find(|&i| (filter & (1 << i)) != 0 && props.memory_types[i as usize].property_flags.contains(flags))
        .expect("no suitable Vulkan memory type")
}

unsafe fn alloc_mapped_buffer(device: &Device, instance: &Instance, pd: vk::PhysicalDevice, size: u64, usage: vk::BufferUsageFlags) -> (vk::Buffer, vk::DeviceMemory) {
    let buf = device
        .create_buffer(&vk::BufferCreateInfo::default().size(size).usage(usage).sharing_mode(vk::SharingMode::EXCLUSIVE), None)
        .expect("create_buffer");
    let reqs = device.get_buffer_memory_requirements(buf);
    let hc = vk::MemoryPropertyFlags::HOST_VISIBLE | vk::MemoryPropertyFlags::HOST_COHERENT;
    let mem = device
        .allocate_memory(&vk::MemoryAllocateInfo::default().allocation_size(reqs.size).memory_type_index(find_memory_type(instance, pd, reqs.memory_type_bits, hc)), None)
        .expect("allocate_memory");
    device.bind_buffer_memory(buf, mem, 0).expect("bind_buffer_memory");
    (buf, mem)
}

unsafe fn upload<T: Copy>(device: &Device, memory: vk::DeviceMemory, data: &[T]) {
    let bytes = std::mem::size_of_val(data) as u64;
    let ptr = device.map_memory(memory, 0, bytes, vk::MemoryMapFlags::empty()).expect("map") as *mut T;
    std::ptr::copy_nonoverlapping(data.as_ptr(), ptr, data.len());
    device.unmap_memory(memory);
}

fn main() {
    let mut path = PathBuf::from("../../CLAUDEBASE/charts/archipelago.json");
    let mut steps: u32 = 50;
    let mut scale: f32 = 0.06; // m/s → cells/step. ~3.5 m/s mean wind × 50 steps ≈ 9 cells — blob sits mid-grid.
    let args: Vec<String> = std::env::args().collect();
    let mut i = 1;
    while i < args.len() {
        if args[i] == "--steps" && i + 1 < args.len() {
            steps = args[i + 1].parse().unwrap_or(50);
            i += 2;
        } else if args[i] == "--scale" && i + 1 < args.len() {
            scale = args[i + 1].parse().unwrap_or(0.06);
            i += 2;
        } else if !args[i].starts_with("--") {
            path = PathBuf::from(&args[i]);
            i += 1;
        } else {
            i += 1;
        }
    }

    let raw = std::fs::read_to_string(&path).unwrap_or_else(|e| panic!("read {}: {e}", path.display()));
    let twin: Twin = serde_json::from_str(&raw).expect("parse boundary json");
    assert!(!twin.islands.is_empty(), "no islands");

    // Bounding box (padded) — same framing as L−5/L−4.
    let (mut min_lat, mut max_lat) = (f32::MAX, f32::MIN);
    let (mut min_lon, mut max_lon) = (f32::MAX, f32::MIN);
    for isl in &twin.islands {
        min_lat = min_lat.min(isl.lat);
        max_lat = max_lat.max(isl.lat);
        min_lon = min_lon.min(isl.lon);
        max_lon = max_lon.max(isl.lon);
    }
    let pad_lat = (max_lat - min_lat) * 0.08 + 0.1;
    let pad_lon = (max_lon - min_lon) * 0.08 + 0.1;
    min_lat -= pad_lat;
    max_lat += pad_lat;
    min_lon -= pad_lon;
    max_lon += pad_lon;

    let cells = (W * H) as usize;
    let cell_of = |lat: f32, lon: f32| -> (u32, u32) {
        let fx = ((lon - min_lon) / (max_lon - min_lon)).clamp(0.0, 1.0);
        let fy = ((max_lat - lat) / (max_lat - min_lat)).clamp(0.0, 1.0);
        ((fx * (W - 1) as f32).round() as u32, (fy * (H - 1) as f32).round() as u32)
    };

    // Each island's grid velocity (cells/step). Meteorological wind_dir is the bearing the wind
    // comes FROM; it blows TO dir+180. Compass bearing β → (east,north)=(sinβ,cosβ). Grid axes
    // are +x=east, +y=south, so: vx = -sin(dir)·speed, vy = +cos(dir)·speed (then ×scale).
    let rad = std::f32::consts::PI / 180.0;
    struct Src {
        cx: f32,
        cy: f32,
        vx: f32,
        vy: f32,
    }
    let srcs: Vec<Src> = twin
        .islands
        .iter()
        .map(|isl| {
            let (cx, cy) = cell_of(isl.lat, isl.lon);
            let dir = isl.wind_dir.unwrap_or(0.0);
            let spd = isl.wind_speed.unwrap_or(0.0);
            Src {
                cx: cx as f32,
                cy: cy as f32,
                vx: -(dir * rad).sin() * spd * scale,
                vy: (dir * rad).cos() * spd * scale,
            }
        })
        .collect();

    // Velocity field by inverse-distance weighting of the island winds (cell-space, like L−5).
    let mut vel = vec![[0.0f32, 0.0f32]; cells];
    for cy in 0..H {
        for cx in 0..W {
            let (mut wsum, mut ax, mut ay) = (0.0f32, 0.0f32, 0.0f32);
            for s in &srcs {
                let d2 = (cx as f32 - s.cx).powi(2) + (cy as f32 - s.cy).powi(2) + 0.5;
                let w = 1.0 / d2;
                wsum += w;
                ax += w * s.vx;
                ay += w * s.vy;
            }
            vel[(cy * W + cx) as usize] = [ax / wsum, ay / wsum];
        }
    }

    // Seed one warm blob (Gaussian, σ≈2 cells) at the flagship island — New-Providence if named,
    // else the island nearest the grid centre. Everything else starts cold. After N steps the
    // blob has left this cell, so the origin reads cold and the downwind trail reads warm.
    let blob_isle = twin
        .islands
        .iter()
        .find(|i| i.isle == "New-Providence")
        .or_else(|| {
            twin.islands.iter().min_by(|a, b| {
                let da = (cell_of(a.lat, a.lon).0 as i32 - (W / 2) as i32).pow(2) + (cell_of(a.lat, a.lon).1 as i32 - (H / 2) as i32).pow(2);
                let db = (cell_of(b.lat, b.lon).0 as i32 - (W / 2) as i32).pow(2) + (cell_of(b.lat, b.lon).1 as i32 - (H / 2) as i32).pow(2);
                da.cmp(&db)
            })
        })
        .expect("an island to seed");
    let (bx, by) = cell_of(blob_isle.lat, blob_isle.lon);
    let sigma2 = 2.0f32 * 2.0;
    let mut field0 = vec![0.0f32; cells];
    for cy in 0..H {
        for cx in 0..W {
            let d2 = (cx as f32 - bx as f32).powi(2) + (cy as f32 - by as f32).powi(2);
            field0[(cy * W + cx) as usize] = (-d2 / (2.0 * sigma2)).exp();
        }
    }

    // Header wind summary: vector mean of the island winds, reported in m/s (pre-scale).
    let (mut mvx, mut mvy) = (0.0f32, 0.0f32);
    for isl in &twin.islands {
        let dir = isl.wind_dir.unwrap_or(0.0);
        let spd = isl.wind_speed.unwrap_or(0.0);
        mvx += -(dir * rad).sin() * spd;
        mvy += (dir * rad).cos() * spd;
    }
    mvx /= twin.islands.len() as f32;
    mvy /= twin.islands.len() as f32;
    let mean_spd = (mvx * mvx + mvy * mvy).sqrt();
    // bearing the mean wind comes FROM (invert the to-vector): atan2 over (-east,-north)
    let mean_from = ((-mvx).atan2(-mvy) / rad + 360.0) % 360.0;

    // ── Vulkan device ───────────────────────────────────────────────────────
    let entry = unsafe { Entry::load().expect("Vulkan loader not found") };
    let app = vk::ApplicationInfo::default().application_name(c"archipelago_advect").api_version(vk::API_VERSION_1_3);
    let instance: Instance = unsafe { entry.create_instance(&vk::InstanceCreateInfo::default().application_info(&app), None).expect("create_instance") };
    let pd = unsafe { instance.enumerate_physical_devices().expect("enumerate") }[0];
    let props = unsafe { instance.get_physical_device_properties(pd) };
    let gpu = unsafe { CStr::from_ptr(props.device_name.as_ptr()) }.to_string_lossy().into_owned();
    let qf = unsafe { instance.get_physical_device_queue_family_properties(pd) }
        .iter()
        .enumerate()
        .filter(|(_, q)| q.queue_flags.contains(vk::QueueFlags::COMPUTE))
        .min_by_key(|(_, q)| if q.queue_flags.contains(vk::QueueFlags::GRAPHICS) { 1u8 } else { 0u8 })
        .map(|(i, _)| i as u32)
        .expect("no compute queue");
    let prio = [1.0f32];
    let qci = [vk::DeviceQueueCreateInfo::default().queue_family_index(qf).queue_priorities(&prio)];
    let device: Device = unsafe { instance.create_device(pd, &vk::DeviceCreateInfo::default().queue_create_infos(&qci), None).expect("create_device") };
    let queue = unsafe { device.get_device_queue(qf, 0) };

    println!(
        "archipelago_advect  L−2 advect  GPU: {gpu}  grid: {W}×{H}  steps: {steps}  wind: from {mean_from:.0}° @ {mean_spd:.1} m/s"
    );

    // ── Buffers: two field buffers (ping-pong) + one velocity field ─────────
    let field_bytes = (cells * mem::size_of::<f32>()) as u64;
    let vel_bytes = (cells * mem::size_of::<[f32; 2]>()) as u64;
    let ssbo = vk::BufferUsageFlags::STORAGE_BUFFER;
    let (buf_a, mem_a) = unsafe { alloc_mapped_buffer(&device, &instance, pd, field_bytes, ssbo) };
    let (buf_b, mem_b) = unsafe { alloc_mapped_buffer(&device, &instance, pd, field_bytes, ssbo) };
    let (buf_v, mem_v) = unsafe { alloc_mapped_buffer(&device, &instance, pd, vel_bytes, ssbo) };
    unsafe {
        upload(&device, mem_a, &field0);
        upload(&device, mem_b, &field0);
        upload(&device, mem_v, &vel);
    }

    // ── Shader → layout (3 SSBO bindings + push{W,H}) → pipeline ─────────────
    let spv = include_bytes!("../../shaders/archipelago_advect.comp.spv");
    let words: Vec<u32> = spv.chunks_exact(4).map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]])).collect();
    let shader = unsafe { device.create_shader_module(&vk::ShaderModuleCreateInfo::default().code(&words), None).expect("shader") };
    let bindings = [0u32, 1, 2].map(|b| {
        vk::DescriptorSetLayoutBinding::default()
            .binding(b)
            .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
            .descriptor_count(1)
            .stage_flags(vk::ShaderStageFlags::COMPUTE)
    });
    let dsl = unsafe { device.create_descriptor_set_layout(&vk::DescriptorSetLayoutCreateInfo::default().bindings(&bindings), None).expect("dsl") };
    let pc_range = [vk::PushConstantRange { stage_flags: vk::ShaderStageFlags::COMPUTE, offset: 0, size: mem::size_of::<Push>() as u32 }];
    let layout = unsafe { device.create_pipeline_layout(&vk::PipelineLayoutCreateInfo::default().set_layouts(&[dsl]).push_constant_ranges(&pc_range), None).expect("layout") };
    let stage = vk::PipelineShaderStageCreateInfo::default().stage(vk::ShaderStageFlags::COMPUTE).module(shader).name(c"main");
    let pipeline = unsafe {
        device.create_compute_pipelines(vk::PipelineCache::null(), &[vk::ComputePipelineCreateInfo::default().stage(stage).layout(layout)], None).expect("pipeline")[0]
    };

    // ── Two descriptor sets: AB (read A, write B) and BA (read B, write A); V shared ─
    let pool_sizes = [vk::DescriptorPoolSize { ty: vk::DescriptorType::STORAGE_BUFFER, descriptor_count: 6 }];
    let pool = unsafe { device.create_descriptor_pool(&vk::DescriptorPoolCreateInfo::default().max_sets(2).pool_sizes(&pool_sizes), None).expect("pool") };
    let sets = unsafe { device.allocate_descriptor_sets(&vk::DescriptorSetAllocateInfo::default().descriptor_pool(pool).set_layouts(&[dsl, dsl])).expect("sets") };
    let (set_ab, set_ba) = (sets[0], sets[1]);

    let write_set = |set: vk::DescriptorSet, read: vk::Buffer, wbuf: vk::Buffer| {
        let infos = [
            vk::DescriptorBufferInfo { buffer: read, offset: 0, range: field_bytes },
            vk::DescriptorBufferInfo { buffer: wbuf, offset: 0, range: field_bytes },
            vk::DescriptorBufferInfo { buffer: buf_v, offset: 0, range: vel_bytes },
        ];
        let writes: Vec<vk::WriteDescriptorSet> = infos
            .iter()
            .enumerate()
            .map(|(i, bi)| {
                vk::WriteDescriptorSet::default()
                    .dst_set(set)
                    .dst_binding(i as u32)
                    .descriptor_type(vk::DescriptorType::STORAGE_BUFFER)
                    .buffer_info(std::slice::from_ref(bi))
            })
            .collect();
        unsafe { device.update_descriptor_sets(&writes, &[]) };
    };
    write_set(set_ab, buf_a, buf_b);
    write_set(set_ba, buf_b, buf_a);

    // ── Record N steps into one command buffer, barrier between each ─────────
    let cmd_pool = unsafe { device.create_command_pool(&vk::CommandPoolCreateInfo::default().queue_family_index(qf), None).expect("cmd_pool") };
    let cmd = unsafe {
        device.allocate_command_buffers(&vk::CommandBufferAllocateInfo::default().command_pool(cmd_pool).level(vk::CommandBufferLevel::PRIMARY).command_buffer_count(1)).expect("cmds")[0]
    };
    let push = Push { w: W, h: H };
    let push_bytes: [u8; 8] = unsafe { mem::transmute(push) };
    let gx = (W + 7) / 8;
    let gy = (H + 7) / 8;
    let barrier = vk::MemoryBarrier::default().src_access_mask(vk::AccessFlags::SHADER_WRITE).dst_access_mask(vk::AccessFlags::SHADER_READ);
    let cmd_bufs = [cmd];
    unsafe {
        device.begin_command_buffer(cmd, &vk::CommandBufferBeginInfo::default().flags(vk::CommandBufferUsageFlags::ONE_TIME_SUBMIT)).expect("begin");
        device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::COMPUTE, pipeline);
        device.cmd_push_constants(cmd, layout, vk::ShaderStageFlags::COMPUTE, 0, &push_bytes);
        for s in 0..steps {
            let set = if s % 2 == 0 { set_ab } else { set_ba }; // even: A→B, odd: B→A
            device.cmd_bind_descriptor_sets(cmd, vk::PipelineBindPoint::COMPUTE, layout, 0, &[set], &[]);
            device.cmd_dispatch(cmd, gx, gy, 1);
            if s + 1 < steps {
                device.cmd_pipeline_barrier(cmd, vk::PipelineStageFlags::COMPUTE_SHADER, vk::PipelineStageFlags::COMPUTE_SHADER, vk::DependencyFlags::empty(), &[barrier], &[], &[]);
            }
        }
        device.end_command_buffer(cmd).expect("end");
    }
    let fence = unsafe { device.create_fence(&vk::FenceCreateInfo::default(), None).expect("fence") };
    unsafe {
        device.queue_submit(queue, &[vk::SubmitInfo::default().command_buffers(&cmd_bufs)], fence).expect("submit");
        device.wait_for_fences(&[fence], true, u64::MAX).expect("wait");
    }

    // Step s writes: s even → B, s odd → A. Final buffer = (steps-1) even ? B : A.
    let final_mem = if (steps.saturating_sub(1)) % 2 == 0 { mem_b } else { mem_a };
    let field: Vec<f32> = unsafe {
        let ptr = device.map_memory(final_mem, 0, field_bytes, vk::MemoryMapFlags::empty()).expect("map final") as *const f32;
        let v = std::slice::from_raw_parts(ptr, cells).to_vec();
        device.unmap_memory(final_mem);
        v
    };

    render(&field, &twin.islands, min_lat, max_lat, min_lon, max_lon, steps, &blob_isle.isle);
    unsafe { device.device_wait_idle().ok() };
}

#[allow(clippy::too_many_arguments)]
fn render(field: &[f32], islands: &[IslandJson], min_lat: f32, max_lat: f32, min_lon: f32, max_lon: f32, steps: u32, origin: &str) {
    let fmin = field.iter().copied().fold(f32::MAX, f32::min);
    let fmax = field.iter().copied().fold(f32::MIN, f32::max);
    let span = (fmax - fmin).max(1e-6);
    const RAMP: [char; 6] = [' ', '·', '░', '▒', '▓', '█'];
    let mut overlay = std::collections::HashMap::new();
    for (k, isl) in islands.iter().enumerate() {
        let fx = ((isl.lon - min_lon) / (max_lon - min_lon)).clamp(0.0, 1.0);
        let fy = ((max_lat - isl.lat) / (max_lat - min_lat)).clamp(0.0, 1.0);
        let cx = (fx * (W - 1) as f32).round() as u32;
        let cy = (fy * (H - 1) as f32).round() as u32;
        overlay.insert((cx, cy), (b"ABCDEFGH"[k.min(7)] as char, isl.isle.clone()));
    }
    println!();
    for cy in 0..H {
        let mut line = String::from("  ");
        for cx in 0..W {
            if let Some((c, _)) = overlay.get(&(cx, cy)) {
                line.push_str(&format!("\x1b[1;97m{c}\x1b[0m"));
            } else {
                let v = (field[(cy * W + cx) as usize] - fmin) / span;
                let code = if v < 0.2 { "38;5;39" } else if v < 0.4 { "38;5;45" } else if v < 0.6 { "38;5;226" } else if v < 0.8 { "38;5;208" } else { "38;5;196" };
                let g = RAMP[((v * (RAMP.len() - 1) as f32).round() as usize).min(RAMP.len() - 1)];
                line.push_str(&format!("\x1b[{code}m{g}\x1b[0m"));
            }
        }
        println!("{line}");
    }
    println!("\n  advected field · {steps} semi-Lagrangian steps on the GPU · blob seeded at {origin}, now drifted downwind · low→high = blue→red");
    let mut legend: Vec<(char, &str)> = overlay.values().map(|(c, n)| (*c, n.as_str())).collect();
    legend.sort_by_key(|(c, _)| *c);
    println!("  {}\n", legend.iter().map(|(c, n)| format!("{c} {n}")).collect::<Vec<_>>().join("   "));
}
