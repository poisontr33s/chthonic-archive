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

use std::{ffi::CStr, mem, path::PathBuf, time::Instant};

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
    sst: Option<f32>, // live sea-surface-temperature °C (M-2); sources the sea field, preferred over air
    #[serde(default)]
    seed: Option<f32>, // live apparent-temp °C (L−3); falls back to elevation if absent
    #[serde(default)]
    wind_dir: Option<f32>, // meteorological: degrees the wind comes FROM
    #[serde(default)]
    wind_speed: Option<f32>, // m/s
    #[serde(default)]
    isle: String,
}

#[derive(Deserialize)]
struct Bathy {
    #[serde(rename = "W")]
    w: u32,
    #[serde(rename = "H")]
    h: u32,
    depth: Vec<f32>,
}

#[repr(C)]
#[derive(Clone, Copy)]
struct Push {
    w: u32,
    h: u32,
}

// W/H are runtime now (--grid WxH, default 56×22): the sim is resolution-scalable, not POC-locked.
// Same Vulkan/Rust engine from a 1,232-cell toy to a multi-million-cell field on the 4090 — the
// "can it compound to high-end" proof is just a bigger grid through the same kernels.

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

#[allow(non_snake_case)] // W/H are runtime grid dims; kept uppercase to leave main's body untouched
fn main() {
    let mut path = PathBuf::from("../../CLAUDEBASE/charts/archipelago.json");
    let mut d_steps: u32 = 30; // diffusion relaxation steps per outer
    let mut v_steps: u32 = 8; // advection transport steps per outer
    let mut max_outer: u32 = 40;
    let mut eps: f32 = 0.02; // converge when max|Δ| per outer drops below this (°C scale)
    let mut scale: f32 = 0.04; // wind m/s → cells/step (gentle: diffusion re-anchors each outer)
    let mut html_out: Option<String> = None; // L0 render: emit a self-contained SVG/HTML of the steady field
    let mut bathy_path = PathBuf::from("../../CLAUDEBASE/charts/bathymetry.json"); // the medium (optional)
    let mut grid: (u32, u32) = (56, 22); // --grid WxH; default is the terminal-renderable POC size
    let args: Vec<String> = std::env::args().collect();
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--diffuse" if i + 1 < args.len() => { d_steps = args[i + 1].parse().unwrap_or(30); i += 2; }
            "--advect" if i + 1 < args.len() => { v_steps = args[i + 1].parse().unwrap_or(8); i += 2; }
            "--max-outer" if i + 1 < args.len() => { max_outer = args[i + 1].parse().unwrap_or(40); i += 2; }
            "--eps" if i + 1 < args.len() => { eps = args[i + 1].parse().unwrap_or(0.02); i += 2; }
            "--scale" if i + 1 < args.len() => { scale = args[i + 1].parse().unwrap_or(0.04); i += 2; }
            s if s.starts_with("--html=") => { html_out = Some(s.trim_start_matches("--html=").to_string()); i += 1; }
            s if s.starts_with("--bathymetry=") => { bathy_path = PathBuf::from(s.trim_start_matches("--bathymetry=")); i += 1; }
            s if s.starts_with("--grid=") => { if let Some((a, b)) = s.trim_start_matches("--grid=").split_once('x') { grid = (a.parse().unwrap_or(56).max(4), b.parse().unwrap_or(22).max(4)); } i += 1; }
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

    let (W, H) = grid; // resolution-scalable: the same kernels run at 56×22 or millions of cells
    let cells = (W * H) as usize;

    // THE MEDIUM — real GEBCO depth per cell (charts/bathymetry.json, written by the barometer
    // --bathymetry). Present → land (elev ≥ 0) becomes a no-flux barrier the field flows around;
    // absent or grid-mismatched → all-sea, the old flat behaviour. Stable data: read, not fetched.
    let depth: Vec<f32> = std::fs::read_to_string(&bathy_path).ok()
        .and_then(|s| serde_json::from_str::<Bathy>(&s).ok())
        .filter(|b| b.w == W && b.h == H && b.depth.len() == cells)
        .map(|b| b.depth)
        .unwrap_or_else(|| vec![-1.0; cells]);
    let land_cells = depth.iter().filter(|&&d| d >= 0.0).count();

    let cell_of = |lat: f32, lon: f32| -> (u32, u32) {
        let fx = ((lon - min_lon) / (max_lon - min_lon)).clamp(0.0, 1.0);
        let fy = ((max_lat - lat) / (max_lat - min_lat)).clamp(0.0, 1.0);
        ((fx * (W - 1) as f32).round() as u32, (fy * (H - 1) as f32).round() as u32)
    };

    // ── INSTANTIATE — seed the temperature field (L−3) and the velocity field (L−2) ──
    let seed_of = |isl: &IslandJson| isl.sst.or(isl.seed).unwrap_or(isl.elevation_m); // real SST first (M-2), then air-temp, then elevation
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

    // Real land (elev ≥ 0) that is not an island source becomes a no-flux barrier (mask.x = −1):
    // the field flows around it. Sources win over land, so an island's seed still radiates.
    for c in 0..cells {
        if depth[c] >= 0.0 && mask[c][0] < 0.5 {
            mask[c] = [-1.0, 0.0];
        }
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
    let medium = if land_cells > 0 { format!("GEBCO bathymetry ({land_cells} land cells as no-flux barriers, {} sea)", cells - land_cells) } else { "flat (no bathymetry.json found)".to_string() };
    println!("  ▸ instantiate ✓ — {} islands → real-SST sources + wind-drift velocity; open sea warm-started at mean {mean_seed:.1} °C (SST)", twin.islands.len());
    println!("  ▸ medium: {medium}");

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
    let t_loop = Instant::now(); // L+1 perform — wall-clock the whole run
    let mut gpu_ns: u128 = 0; // and the pure GPU submit→wait time within it

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
            let t_gpu = Instant::now();
            device.queue_submit(queue, &[vk::SubmitInfo::default().command_buffers(&cmd_bufs)], fence).expect("submit");
            device.wait_for_fences(&[fence], true, u64::MAX).expect("wait");
            gpu_ns += t_gpu.elapsed().as_nanos();
            device.reset_fences(&[fence]).expect("reset fence");
        }

        // CONVERGE gate — read the live field, measure the step's max change.
        let cur_mem = if read_is_a { mem_a } else { mem_b };
        let field = unsafe { readback(&device, cur_mem, cells, field_bytes) };
        last_delta = field.iter().zip(&prev).enumerate().filter(|(c, _)| depth[*c] < 0.0).map(|(_, (a, b))| (a - b).abs()).fold(0.0f32, f32::max);
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

    // L+1 PERFORM — heavy is only worth it if it is fast. Measure what it actually cost.
    let outers_done = converged_at.map(|k| k + 1).unwrap_or(max_outer) as u64;
    let total_steps = outers_done * (d_steps + v_steps) as u64;
    let gpu_ms = gpu_ns as f64 / 1.0e6;
    let wall_ms = t_loop.elapsed().as_secs_f64() * 1000.0;
    let us_per_step = if total_steps > 0 { (gpu_ns as f64 / 1.0e3) / total_steps as f64 } else { 0.0 };
    println!("  ▸ perform ✓ — {outers_done} outers × {} steps = {total_steps} GPU dispatches · GPU {gpu_ms:.1} ms ({us_per_step:.1} µs/step incl submit) · wall {wall_ms:.1} ms incl readback — heavy verified fast", d_steps + v_steps);

    render(&prev, &depth, &twin.islands, min_lat, max_lat, min_lon, max_lon, converged_at, max_outer, W, H);
    if let Some(p) = &html_out {
        write_html(p, &prev, &depth, &twin.islands, min_lat, max_lat, min_lon, max_lon, converged_at, max_outer, W, H);
        println!("  ▸ render ✓ — steady field → {p}  ({}×{} px self-contained SVG; live-derived, ephemeral)", W * 15, H * 15);
    }
    unsafe { device.device_wait_idle().ok() };
}

#[allow(clippy::too_many_arguments)]
fn render(field: &[f32], depth: &[f32], islands: &[IslandJson], min_lat: f32, max_lat: f32, min_lon: f32, max_lon: f32, converged_at: Option<u32>, max_outer: u32, w: u32, h: u32) {
    // Scale over SEA cells only — land holds a placeholder, it must not stretch the heat ramp.
    let sea: Vec<f32> = field.iter().enumerate().filter(|(c, _)| depth[*c] < 0.0).map(|(_, v)| *v).collect();
    let fmin = sea.iter().copied().fold(f32::MAX, f32::min);
    let fmax = sea.iter().copied().fold(f32::MIN, f32::max);
    let span = (fmax - fmin).max(1e-6);
    let state = match converged_at {
        Some(k) => format!("converged at outer {k}"),
        None => format!("{max_outer} outers, not yet steady"),
    };
    let land = depth.iter().filter(|&&d| d >= 0.0).count();
    let land_note = if land > 0 { format!(" · \x1b[38;5;22m█\x1b[0m {land} land (GEBCO)") } else { String::new() };
    // Terminal ASCII only renders at POC scale; past it the field IS the data, not the picture.
    if w > 120 || h > 60 {
        println!("\n  [grid {w}×{h} = {} cells — beyond the terminal; field computed on the GPU, perf above]", w * h);
        println!("  steady-state field · advection-diffusion · {state} · {fmin:.1}–{fmax:.1} °C{land_note}\n");
        return;
    }
    const RAMP: [char; 6] = [' ', '·', '░', '▒', '▓', '█'];
    let mut overlay = std::collections::HashMap::new();
    for (k, isl) in islands.iter().enumerate() {
        let fx = ((isl.lon - min_lon) / (max_lon - min_lon)).clamp(0.0, 1.0);
        let fy = ((max_lat - isl.lat) / (max_lat - min_lat)).clamp(0.0, 1.0);
        let cx = (fx * (w - 1) as f32).round() as u32;
        let cy = (fy * (h - 1) as f32).round() as u32;
        overlay.insert((cx, cy), (b"ABCDEFGH"[k.min(7)] as char, isl.isle.clone()));
    }
    println!();
    for cy in 0..h {
        let mut line = String::from("  ");
        for cx in 0..w {
            if let Some((c, _)) = overlay.get(&(cx, cy)) {
                line.push_str(&format!("\x1b[1;97m{c}\x1b[0m"));
            } else if depth[(cy * w + cx) as usize] >= 0.0 {
                line.push_str("\x1b[38;5;22m█\x1b[0m"); // real land — dark green; the field flows around it
            } else {
                let v = (field[(cy * w + cx) as usize] - fmin) / span;
                let code = if v < 0.2 { "38;5;39" } else if v < 0.4 { "38;5;45" } else if v < 0.6 { "38;5;226" } else if v < 0.8 { "38;5;208" } else { "38;5;196" };
                let g = RAMP[((v * (RAMP.len() - 1) as f32).round() as usize).min(RAMP.len() - 1)];
                line.push_str(&format!("\x1b[{code}m{g}\x1b[0m"));
            }
        }
        println!("{line}");
    }
    println!("\n  steady-state field · advection-diffusion · {state} · {fmin:.1}–{fmax:.1} °C · low→high = blue→red{land_note}");
    let mut legend: Vec<(char, &str)> = overlay.values().map(|(c, n)| (*c, n.as_str())).collect();
    legend.sort_by_key(|(c, _)| *c);
    println!("  {}\n", legend.iter().map(|(c, n)| format!("{c} {n}")).collect::<Vec<_>>().join("   "));
}

// L0 RENDER — the same steady field, but as a self-contained browser artifact: an inline SVG
// heat-map with a SMOOTH blue→red gradient (the terminal can only band into 5 ANSI colours).
// Live-derived, so it is a view, never committed — like live_boundary.json. Modular enough to
// drop into The-Savant-Grade-Undercellar_Library_Study as an Index.html/png.
#[allow(clippy::too_many_arguments)]
fn write_html(path: &str, field: &[f32], depth: &[f32], islands: &[IslandJson], min_lat: f32, max_lat: f32, min_lon: f32, max_lon: f32, converged_at: Option<u32>, max_outer: u32, w: u32, h: u32) {
    if w * h > 60_000 { eprintln!("  html skipped — {w}×{h} = {} cells too many for an inline-SVG page (raster export is the high-res path)", w * h); return; }
    let sea: Vec<f32> = field.iter().enumerate().filter(|(c, _)| depth[*c] < 0.0).map(|(_, v)| *v).collect();
    let fmin = sea.iter().copied().fold(f32::MAX, f32::min);
    let fmax = sea.iter().copied().fold(f32::MIN, f32::max);
    let span = (fmax - fmin).max(1e-6);
    const CELL: u32 = 15;
    let (vw, vh) = (w * CELL, h * CELL);
    // Five gradient stops, lerped continuously — matches the terminal's blue→cyan→yellow→orange→red.
    let stops: [(f32, f32, f32); 5] = [(41.0, 120.0, 255.0), (54.0, 207.0, 255.0), (255.0, 230.0, 0.0), (255.0, 140.0, 0.0), (255.0, 43.0, 43.0)];
    let hex = |v: f32| -> String {
        let seg = (v.clamp(0.0, 1.0) * 4.0).min(3.999);
        let i = seg as usize;
        let t = seg - i as f32;
        let (r0, g0, b0) = stops[i];
        let (r1, g1, b1) = stops[i + 1];
        let mix = |a: f32, b: f32| (a + (b - a) * t).round() as u32;
        format!("#{:02x}{:02x}{:02x}", mix(r0, r1), mix(g0, g1), mix(b0, b1))
    };
    let mut svg = String::new();
    for cy in 0..h {
        for cx in 0..w {
            let c = (cy * w + cx) as usize;
            let fill = if depth[c] >= 0.0 { "#1f3d2b".to_string() } else { hex((field[c] - fmin) / span) }; // land = muted green
            svg.push_str(&format!("<rect x='{}' y='{}' width='{CELL}' height='{CELL}' fill='{fill}'/>", cx * CELL, cy * CELL));
        }
    }
    for (k, isl) in islands.iter().enumerate() {
        let fx = ((isl.lon - min_lon) / (max_lon - min_lon)).clamp(0.0, 1.0);
        let fy = ((max_lat - isl.lat) / (max_lat - min_lat)).clamp(0.0, 1.0);
        let cx = (fx * (w - 1) as f32).round() as u32;
        let cy = (fy * (h - 1) as f32).round() as u32;
        let letter = b"ABCDEFGH"[k.min(7)] as char;
        svg.push_str(&format!(
            "<text x='{}' y='{}' fill='#fff' font-size='12' font-weight='bold' text-anchor='middle' dominant-baseline='central' style='paint-order:stroke;stroke:#000;stroke-width:2.5px'>{letter}</text>",
            cx * CELL + CELL / 2,
            cy * CELL + CELL / 2
        ));
    }
    let state = match converged_at { Some(k) => format!("converged at outer {k}"), None => format!("{max_outer} outers — not yet steady") };
    let legend: String = islands.iter().enumerate().map(|(k, i)| format!("<li><b>{}</b> {} — {:.1} °C</li>", b"ABCDEFGH"[k.min(7)] as char, i.isle, i.seed.unwrap_or(i.elevation_m))).collect();
    let html = format!(
        "<!DOCTYPE html>\n<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>\n<title>archipelago · steady-state field</title>\n<style>body{{margin:0;background:#0a0e14;color:#cbd5e1;font:14px/1.55 ui-monospace,Menlo,Consolas,monospace;padding:28px;max-width:980px}}h1{{font-size:16px;font-weight:600;letter-spacing:.04em;color:#e2e8f0}}svg{{width:100%;height:auto;margin:8px 0;border:1px solid #1e293b;border-radius:8px}}.cap{{color:#64748b;margin:6px 0 16px}}ul{{columns:2;gap:32px;max-width:560px;padding-left:18px;list-style:none}}li{{margin:.15em 0}}b{{color:#fff}}</style></head>\n<body><h1>☥ archipelago · advection-diffusion steady state</h1>\n<svg viewBox='0 0 {vw} {vh}' xmlns='http://www.w3.org/2000/svg' shape-rendering='crispEdges'>{svg}</svg>\n<p class='cap'>{state} · {fmin:.1}–{fmax:.1} °C · blue→red = cool→warm · live sky, rendered by archipelago_sim (L0)</p>\n<ul>{legend}</ul>\n</body></html>\n"
    );
    std::fs::write(path, html).unwrap_or_else(|e| eprintln!("  html write failed: {e}"));
}
