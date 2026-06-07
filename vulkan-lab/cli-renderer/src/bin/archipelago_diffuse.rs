// @SID: ARCHIPELAGO_DIFFUSE_V0
// L−4 · ITERATE — the field becomes a simulation.
//
// L−5 interpolated (one analytic pass). L−4 RELAXES: islands are pinned sources, and
// the field diffuses outward over N steps, ping-ponging two GPU buffers with a memory
// barrier between each step. The sim climbs one rung — it evolves, it doesn't just map.
//
//   cargo run --bin archipelago_diffuse -- [<archipelago.json>] [--steps N]
//   default path: ../../CLAUDEBASE/charts/archipelago.json   default steps: 240

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
    seed: Option<f32>,
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
    let mut steps: u32 = 240;
    let args: Vec<String> = std::env::args().collect();
    let mut i = 1;
    while i < args.len() {
        if args[i] == "--steps" && i + 1 < args.len() {
            steps = args[i + 1].parse().unwrap_or(240);
            i += 2;
        } else if !args[i].starts_with("--") {
            path = PathBuf::from(&args[i]);
            i += 1;
        } else {
            i += 1;
        }
    }

    let raw = std::fs::read_to_string(&path).unwrap_or_else(|e| panic!("read {}: {e}", path.display()));
    let twin: Twin = serde_json::from_str(&raw).expect("parse archipelago.json");
    assert!(!twin.islands.is_empty(), "no islands");

    // Bounding box (padded) — same framing as L−5.
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

    // Host-side rasterize: pin each island onto its nearest cell as a source.
    let cells = (W * H) as usize;
    // Warm start: free (sea) cells begin at the mean seed, not 0. The converged harmonic
    // field is identical either way — the Dirichlet sources pin the extrema — but a zero
    // init leaves the far-sea corners un-relaxed after a finite step count, reading as a
    // false cold floor. Seeding at the mean lets the real gradient settle in the steps we run.
    let seed_of = |isl: &IslandJson| isl.seed.unwrap_or(isl.elevation_m); // live apparent-temp if present, else elevation
    let mean_seed = twin.islands.iter().map(seed_of).sum::<f32>() / twin.islands.len() as f32;
    let mut mask = vec![[0.0f32, 0.0f32]; cells]; // [isSource, value]
    let mut field0 = vec![mean_seed; cells];
    let cell_of = |lat: f32, lon: f32| -> usize {
        let fx = ((lon - min_lon) / (max_lon - min_lon)).clamp(0.0, 1.0);
        let fy = ((max_lat - lat) / (max_lat - min_lat)).clamp(0.0, 1.0);
        let cx = (fx * (W - 1) as f32).round() as u32;
        let cy = (fy * (H - 1) as f32).round() as u32;
        (cy * W + cx) as usize
    };
    for isl in &twin.islands {
        let c = cell_of(isl.lat, isl.lon);
        let s = seed_of(isl);
        mask[c] = [1.0, s];
        field0[c] = s;
    }

    // ── Vulkan device ───────────────────────────────────────────────────────
    let entry = unsafe { Entry::load().expect("Vulkan loader not found") };
    let app = vk::ApplicationInfo::default().application_name(c"archipelago_diffuse").api_version(vk::API_VERSION_1_3);
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

    println!("archipelago_diffuse  L−4 iterate  GPU: {gpu}  grid: {W}×{H}  steps: {steps}");

    // ── Buffers: two field buffers (ping-pong) + mask ───────────────────────
    let field_bytes = (cells * mem::size_of::<f32>()) as u64;
    let mask_bytes = (cells * mem::size_of::<[f32; 2]>()) as u64;
    let ssbo = vk::BufferUsageFlags::STORAGE_BUFFER;
    let (buf_a, mem_a) = unsafe { alloc_mapped_buffer(&device, &instance, pd, field_bytes, ssbo) };
    let (buf_b, mem_b) = unsafe { alloc_mapped_buffer(&device, &instance, pd, field_bytes, ssbo) };
    let (buf_m, mem_m) = unsafe { alloc_mapped_buffer(&device, &instance, pd, mask_bytes, ssbo) };
    unsafe {
        upload(&device, mem_a, &field0);
        upload(&device, mem_b, &field0);
        upload(&device, mem_m, &mask);
    }

    // ── Shader → layout (3 SSBO bindings + push{W,H}) → pipeline ─────────────
    let spv = include_bytes!("../../shaders/archipelago_diffuse.comp.spv");
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

    // ── Two descriptor sets: AB (read A, write B) and BA (read B, write A) ───
    let pool_sizes = [vk::DescriptorPoolSize { ty: vk::DescriptorType::STORAGE_BUFFER, descriptor_count: 6 }];
    let pool = unsafe { device.create_descriptor_pool(&vk::DescriptorPoolCreateInfo::default().max_sets(2).pool_sizes(&pool_sizes), None).expect("pool") };
    let sets = unsafe { device.allocate_descriptor_sets(&vk::DescriptorSetAllocateInfo::default().descriptor_pool(pool).set_layouts(&[dsl, dsl])).expect("sets") };
    let (set_ab, set_ba) = (sets[0], sets[1]);

    let write_set = |set: vk::DescriptorSet, read: vk::Buffer, wbuf: vk::Buffer| {
        let infos = [
            vk::DescriptorBufferInfo { buffer: read, offset: 0, range: field_bytes },
            vk::DescriptorBufferInfo { buffer: wbuf, offset: 0, range: field_bytes },
            vk::DescriptorBufferInfo { buffer: buf_m, offset: 0, range: mask_bytes },
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
    let barrier = vk::MemoryBarrier::default()
        .src_access_mask(vk::AccessFlags::SHADER_WRITE)
        .dst_access_mask(vk::AccessFlags::SHADER_READ);
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
                device.cmd_pipeline_barrier(
                    cmd,
                    vk::PipelineStageFlags::COMPUTE_SHADER,
                    vk::PipelineStageFlags::COMPUTE_SHADER,
                    vk::DependencyFlags::empty(),
                    &[barrier],
                    &[],
                    &[],
                );
            }
        }
        device.end_command_buffer(cmd).expect("end");
    }
    let fence = unsafe { device.create_fence(&vk::FenceCreateInfo::default(), None).expect("fence") };
    unsafe {
        device.queue_submit(queue, &[vk::SubmitInfo::default().command_buffers(&cmd_bufs)], fence).expect("submit");
        device.wait_for_fences(&[fence], true, u64::MAX).expect("wait");
    }

    // Final field is in B if steps odd (last write B at even s), else A. Step s writes:
    // s even → B, s odd → A. Last step index = steps-1. So final buffer = (steps-1) even ? B : A.
    let final_mem = if (steps.saturating_sub(1)) % 2 == 0 { mem_b } else { mem_a };
    let field: Vec<f32> = unsafe {
        let ptr = device.map_memory(final_mem, 0, field_bytes, vk::MemoryMapFlags::empty()).expect("map final") as *const f32;
        let v = std::slice::from_raw_parts(ptr, cells).to_vec();
        device.unmap_memory(final_mem);
        v
    };

    render(&field, &twin.islands, min_lat, max_lat, min_lon, max_lon, steps);
    unsafe { device.device_wait_idle().ok() };
}

fn render(field: &[f32], islands: &[IslandJson], min_lat: f32, max_lat: f32, min_lon: f32, max_lon: f32, steps: u32) {
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
    println!("\n  diffused field · {steps} relaxation steps on the GPU · {fmin:.1}–{fmax:.1} · low→high = blue→red");
    let mut legend: Vec<(char, &str)> = overlay.values().map(|(c, n)| (*c, n.as_str())).collect();
    legend.sort_by_key(|(c, _)| *c);
    println!("  {}\n", legend.iter().map(|(c, n)| format!("{c} {n}")).collect::<Vec<_>>().join("   "));
}
