// @SID: ARCHIPELAGO_SIM_V0
// L−1 · LADDER-AS-PHASES — the four rungs become one gated state machine.
//
// L−5 interpolated · L−4 diffused · L−3 fed live temperature · L−2 advected by live wind.
// L−1 COMPOSES them: instantiate → (diffuse ⋈ advect)* → converge → render. The field is
// driven by operator-split advection-diffusion — each OUTER iteration relaxes toward the
// island temperatures (Dirichlet sources, the L−4 shader) THEN transports the result downwind
// (the L−2 shader), and the CONVERGE gate reads the field back and measures max|Δ| between
// outers, halting when the system reaches a steady state. Each phase is a verified gate: the
// next opens only when the last reports OK. No new shader — the two existing rungs ARE the
// operators; this rung is the machine that runs them to a fixpoint.
//
//   cargo run --bin archipelago_sim -- [<boundary.json>] [--diffuse D] [--advect V] [--max-outer M] [--eps E] [--scale S]
//   feed it a live boundary:  ../../live_boundary.json  (barometer --boundary writes temp + wind)

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
    elevation_m: f32,
    #[serde(default)]
    seed: Option<f32>, // live apparent-temp °C (L−3); falls back to elevation if absent
    #[serde(default)]
    wind_dir: Option<f32>, // meteorological: degrees the wind comes FROM
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

unsafe fn readback(device: &Device, memory: vk::DeviceMemory, count: usize, bytes: u64) -> Vec<f32> {
    let ptr = device.map_memory(memory, 0, bytes, vk::MemoryMapFlags::empty()).expect("map readback") as *const f32;
    let v = std::slice::from_raw_parts(ptr, count).to_vec();
    device.unmap_memory(memory);
    v
}

fn main() {
    let mut path = PathBuf::from("../../CLAUDEBASE/charts/archipelago.json");
    let mut d_steps: u32 = 30; // diffusion relaxation steps per outer
    let mut v_steps: u32 = 8; // advection transport steps per outer
    let mut max_outer: u32 = 40;
    let mut eps: f32 = 0.02; // converge when max|Δ| per outer drops below this (°C scale)
    let mut scale: f32 = 0.04; // wind m/s → cells/step (gentle: diffusion re-anchors each outer)
    let args: Vec<String> = std::env::args().collect();
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--diffuse" if i + 1 < args.len() => { d_steps = args[i + 1].parse().unwrap_or(30); i += 2; }
            "--advect" if i + 1 < args.len() => { v_steps = args[i + 1].parse().unwrap_or(8); i += 2; }
            "--max-outer" if i + 1 < args.len() => { max_outer = args[i + 1].parse().unwrap_or(40); i += 2; }
            "--eps" if i + 1 < args.len() => { eps = args[i + 1].parse().unwrap_or(0.02); i += 2; }
            "--scale" if i + 1 < args.len() => { scale = args[i + 1].parse().unwrap_or(0.04); i += 2; }
            s if !s.starts_with("--") => { path = PathBuf::from(s); i += 1; }
            _ => { i += 1; }
        }
    }

    let raw = std::fs::read_to_string(&path).unwrap_or_else(|e| panic!("read {}: {e}", path.display()));
    let twin: Twin = serde_json::from_str(&raw).expect("parse boundary json");
    assert!(!twin.islands.is_empty(), "no islands");

    // Bounding box (padded) — same framing as the other rungs.
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

    // ── INSTANTIATE — seed the temperature field (L−3) and the velocity field (L−2) ──
    let seed_of = |isl: &IslandJson| isl.seed.unwrap_or(isl.elevation_m);
    let mean_seed = twin.islands.iter().map(seed_of).sum::<f32>() / twin.islands.len() as f32;
    let rad = std::f32::consts::PI / 180.0;

    // Temperature sources (mask: [isSource, value]) + warm-started field.
    let mut mask = vec![[0.0f32, 0.0f32]; cells];
    let mut field0 = vec![mean_seed; cells];
    for isl in &twin.islands {
        let (cx, cy) = cell_of(isl.lat, isl.lon);
        let c = (cy * W + cx) as usize;
        let s = seed_of(isl);
        mask[c] = [1.0, s];
        field0[c] = s;
    }

    // Velocity field by inverse-distance weighting of island winds (cells/step, +x east +y south).
    struct Src { cx: f32, cy: f32, vx: f32, vy: f32 }
    let srcs: Vec<Src> = twin.islands.iter().map(|isl| {
        let (cx, cy) = cell_of(isl.lat, isl.lon);
        let dir = isl.wind_dir.unwrap_or(0.0);
        let spd = isl.wind_speed.unwrap_or(0.0);
        Src { cx: cx as f32, cy: cy as f32, vx: -(dir * rad).sin() * spd * scale, vy: (dir * rad).cos() * spd * scale }
    }).collect();
    let mut vel = vec![[0.0f32, 0.0f32]; cells];
    for cy in 0..H {
        for cx in 0..W {
            let (mut wsum, mut ax, mut ay) = (0.0f32, 0.0f32, 0.0f32);
            for s in &srcs {
                let w = 1.0 / ((cx as f32 - s.cx).powi(2) + (cy as f32 - s.cy).powi(2) + 0.5);
                wsum += w; ax += w * s.vx; ay += w * s.vy;
            }
            vel[(cy * W + cx) as usize] = [ax / wsum, ay / wsum];
        }
    }

    // ── Vulkan device ───────────────────────────────────────────────────────
    let entry = unsafe { Entry::load().expect("Vulkan loader not found") };
    let app = vk::ApplicationInfo::default().application_name(c"archipelago_sim").api_version(vk::API_VERSION_1_3);
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

    println!("archipelago_sim  L−1 phases  GPU: {gpu}  grid: {W}×{H}  per outer: {d_steps} diffuse ⋈ {v_steps} advect  (max {max_outer} outers, ε={eps})");
    println!("  ▸ instantiate ✓ — {} islands → temperature sources + wind velocity field; open sea warm-started at mean {mean_seed:.1} °C", twin.islands.len());

    // ── Buffers: ping-pong field A/B + diffusion mask + advection velocity ──
    let field_bytes = (cells * mem::size_of::<f32>()) as u64;
    let vec2_bytes = (cells * mem::size_of::<[f32; 2]>()) as u64;
    let ssbo = vk::BufferUsageFlags::STORAGE_BUFFER;
    let (buf_a, mem_a) = unsafe { alloc_mapped_buffer(&device, &instance, pd, field_bytes, ssbo) };
    let (buf_b, mem_b) = unsafe { alloc_mapped_buffer(&device, &instance, pd, field_bytes, ssbo) };
    let (buf_m, mem_m) = unsafe { alloc_mapped_buffer(&device, &instance, pd, vec2_bytes, ssbo) };
    let (buf_v, mem_v) = unsafe { alloc_mapped_buffer(&device, &instance, pd, vec2_bytes, ssbo) };
    unsafe {
        upload(&device, mem_a, &field0);
        upload(&device, mem_b, &field0);
        upload(&device, mem_m, &mask);
        upload(&device, mem_v, &vel);
    }

    // ── Two shader modules (the two existing rungs) on ONE shared layout ─────
    let make_module = |bytes: &[u8]| -> vk::ShaderModule {
        let words: Vec<u32> = bytes.chunks_exact(4).map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]])).collect();
        unsafe { device.create_shader_module(&vk::ShaderModuleCreateInfo::default().code(&words), None).expect("shader") }
    };
    let mod_diffuse = make_module(include_bytes!("../../shaders/archipelago_diffuse.comp.spv"));
    let mod_advect = make_module(include_bytes!("../../shaders/archipelago_advect.comp.spv"));

    let bindings = [0u32, 1, 2].map(|b| {
        vk::DescriptorSetLayoutBinding::default().binding(b).descriptor_type(vk::DescriptorType::STORAGE_BUFFER).descriptor_count(1).stage_flags(vk::ShaderStageFlags::COMPUTE)
    });
    let dsl = unsafe { device.create_descriptor_set_layout(&vk::DescriptorSetLayoutCreateInfo::default().bindings(&bindings), None).expect("dsl") };
    let pc_range = [vk::PushConstantRange { stage_flags: vk::ShaderStageFlags::COMPUTE, offset: 0, size: mem::size_of::<Push>() as u32 }];
    let layout = unsafe { device.create_pipeline_layout(&vk::PipelineLayoutCreateInfo::default().set_layouts(&[dsl]).push_constant_ranges(&pc_range), None).expect("layout") };
    let make_pipe = |module: vk::ShaderModule| -> vk::Pipeline {
        let stage = vk::PipelineShaderStageCreateInfo::default().stage(vk::ShaderStageFlags::COMPUTE).module(module).name(c"main");
        unsafe { device.create_compute_pipelines(vk::PipelineCache::null(), &[vk::ComputePipelineCreateInfo::default().stage(stage).layout(layout)], None).expect("pipeline")[0] }
    };
    let pipe_diffuse = make_pipe(mod_diffuse);
    let pipe_advect = make_pipe(mod_advect);

    // ── Four descriptor sets: {diffuse,advect} × {A→B, B→A}; binding 2 is mask for diffuse, vel for advect ──
    let pool_sizes = [vk::DescriptorPoolSize { ty: vk::DescriptorType::STORAGE_BUFFER, descriptor_count: 12 }];
    let pool = unsafe { device.create_descriptor_pool(&vk::DescriptorPoolCreateInfo::default().max_sets(4).pool_sizes(&pool_sizes), None).expect("pool") };
    let sets = unsafe { device.allocate_descriptor_sets(&vk::DescriptorSetAllocateInfo::default().descriptor_pool(pool).set_layouts(&[dsl, dsl, dsl, dsl])).expect("sets") };
    let (diff_ab, diff_ba, adv_ab, adv_ba) = (sets[0], sets[1], sets[2], sets[3]);

    let write_set = |set: vk::DescriptorSet, read: vk::Buffer, wbuf: vk::Buffer, aux: vk::Buffer, aux_bytes: u64| {
        let infos = [
            vk::DescriptorBufferInfo { buffer: read, offset: 0, range: field_bytes },
            vk::DescriptorBufferInfo { buffer: wbuf, offset: 0, range: field_bytes },
            vk::DescriptorBufferInfo { buffer: aux, offset: 0, range: aux_bytes },
        ];
        let writes: Vec<vk::WriteDescriptorSet> = infos.iter().enumerate().map(|(i, bi)| {
            vk::WriteDescriptorSet::default().dst_set(set).dst_binding(i as u32).descriptor_type(vk::DescriptorType::STORAGE_BUFFER).buffer_info(std::slice::from_ref(bi))
        }).collect();
        unsafe { device.update_descriptor_sets(&writes, &[]) };
    };
    write_set(diff_ab, buf_a, buf_b, buf_m, vec2_bytes);
    write_set(diff_ba, buf_b, buf_a, buf_m, vec2_bytes);
    write_set(adv_ab, buf_a, buf_b, buf_v, vec2_bytes);
    write_set(adv_ba, buf_b, buf_a, buf_v, vec2_bytes);

    // ── Command machinery (re-recorded each outer) ──────────────────────────
    let cmd_pool = unsafe { device.create_command_pool(&vk::CommandPoolCreateInfo::default().flags(vk::CommandPoolCreateFlags::RESET_COMMAND_BUFFER).queue_family_index(qf), None).expect("cmd_pool") };
    let cmd = unsafe { device.allocate_command_buffers(&vk::CommandBufferAllocateInfo::default().command_pool(cmd_pool).level(vk::CommandBufferLevel::PRIMARY).command_buffer_count(1)).expect("cmds")[0] };
    let fence = unsafe { device.create_fence(&vk::FenceCreateInfo::default(), None).expect("fence") };
    let push = Push { w: W, h: H };
    let push_bytes: [u8; 8] = unsafe { mem::transmute(push) };
    let (gx, gy) = ((W + 7) / 8, (H + 7) / 8);
    let barrier = vk::MemoryBarrier::default().src_access_mask(vk::AccessFlags::SHADER_WRITE).dst_access_mask(vk::AccessFlags::SHADER_READ);
    let cmd_bufs = [cmd];

    // ── The state machine: (diffuse ⋈ advect)* until the CONVERGE gate fires ──
    let mut prev = field0.clone();
    let mut read_is_a = true; // current data starts in A (both A and B hold field0)
    let mut converged_at: Option<u32> = None;
    let mut last_delta = f32::INFINITY;

    for outer in 0..max_outer {
        unsafe {
            device.reset_command_buffer(cmd, vk::CommandBufferResetFlags::empty()).expect("reset cmd");
            device.begin_command_buffer(cmd, &vk::CommandBufferBeginInfo::default().flags(vk::CommandBufferUsageFlags::ONE_TIME_SUBMIT)).expect("begin");
            // diffuse phase
            device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::COMPUTE, pipe_diffuse);
            device.cmd_push_constants(cmd, layout, vk::ShaderStageFlags::COMPUTE, 0, &push_bytes);
            for _ in 0..d_steps {
                let set = if read_is_a { diff_ab } else { diff_ba };
                device.cmd_bind_descriptor_sets(cmd, vk::PipelineBindPoint::COMPUTE, layout, 0, &[set], &[]);
                device.cmd_dispatch(cmd, gx, gy, 1);
                device.cmd_pipeline_barrier(cmd, vk::PipelineStageFlags::COMPUTE_SHADER, vk::PipelineStageFlags::COMPUTE_SHADER, vk::DependencyFlags::empty(), &[barrier], &[], &[]);
                read_is_a = !read_is_a;
            }
            // advect phase
            device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::COMPUTE, pipe_advect);
            device.cmd_push_constants(cmd, layout, vk::ShaderStageFlags::COMPUTE, 0, &push_bytes);
            for _ in 0..v_steps {
                let set = if read_is_a { adv_ab } else { adv_ba };
                device.cmd_bind_descriptor_sets(cmd, vk::PipelineBindPoint::COMPUTE, layout, 0, &[set], &[]);
                device.cmd_dispatch(cmd, gx, gy, 1);
                device.cmd_pipeline_barrier(cmd, vk::PipelineStageFlags::COMPUTE_SHADER, vk::PipelineStageFlags::COMPUTE_SHADER, vk::DependencyFlags::empty(), &[barrier], &[], &[]);
                read_is_a = !read_is_a;
            }
            device.end_command_buffer(cmd).expect("end");
            device.queue_submit(queue, &[vk::SubmitInfo::default().command_buffers(&cmd_bufs)], fence).expect("submit");
            device.wait_for_fences(&[fence], true, u64::MAX).expect("wait");
            device.reset_fences(&[fence]).expect("reset fence");
        }

        // CONVERGE gate — read the live field, measure the step's max change.
        let cur_mem = if read_is_a { mem_a } else { mem_b };
        let field = unsafe { readback(&device, cur_mem, cells, field_bytes) };
        last_delta = field.iter().zip(&prev).map(|(a, b)| (a - b).abs()).fold(0.0f32, f32::max);
        if outer < 3 || outer % 5 == 4 {
            println!("    diffuse ⋈ advect · outer {outer:>2}: max|Δ| = {last_delta:.4} °C");
        }
        prev = field;
        if last_delta < eps {
            converged_at = Some(outer);
            break;
        }
    }

    match converged_at {
        Some(k) => println!("  ▸ converge ✓ — steady state at outer {k} (max|Δ| {last_delta:.4} < ε {eps}); the advection-diffusion balance settled"),
        None => println!("  ▸ converge — halted at max-outer {max_outer}; max|Δ| {last_delta:.4} still ≥ ε {eps} (stirring exceeds relaxation at this scale)"),
    }

    render(&prev, &twin.islands, min_lat, max_lat, min_lon, max_lon, converged_at, max_outer);
    unsafe { device.device_wait_idle().ok() };
}

#[allow(clippy::too_many_arguments)]
fn render(field: &[f32], islands: &[IslandJson], min_lat: f32, max_lat: f32, min_lon: f32, max_lon: f32, converged_at: Option<u32>, max_outer: u32) {
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
    let state = match converged_at {
        Some(k) => format!("converged at outer {k}"),
        None => format!("{max_outer} outers, not yet steady"),
    };
    println!("\n  steady-state field · advection-diffusion · {state} · {fmin:.1}–{fmax:.1} °C · low→high = blue→red");
    let mut legend: Vec<(char, &str)> = overlay.values().map(|(c, n)| (*c, n.as_str())).collect();
    legend.sort_by_key(|(c, _)| *c);
    println!("  {}\n", legend.iter().map(|(c, n)| format!("{c} {n}")).collect::<Vec<_>>().join("   "));
}
