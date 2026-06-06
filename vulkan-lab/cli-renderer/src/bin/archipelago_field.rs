// @SID: ARCHIPELAGO_FIELD_V0
// L−5 · THE SEAM — barometer twin → SSBO → Vulkan inverse-distance field → ASCII.
//
// Reads CLAUDEBASE/charts/archipelago.json (the digital twin), uploads the islands as
// an SSBO, dispatches archipelago_field.comp on the 4090 to compute an inverse-distance
// ELEVATION field over a lat/lon grid, reads it back, prints it tinted by field value.
// Proves the whole long tack is real: barometer (geography) → GPU (field) → render,
// in one compute pass. The first verified rung of the ladder (Arc II · L−5).
//
//   cargo run --bin archipelago_field -- [<archipelago.json>]
//   default path: ../../CLAUDEBASE/charts/archipelago.json  (run from cli-renderer/)

use std::{ffi::CStr, mem, path::PathBuf};

use ash::{vk, Device, Entry, Instance};
use serde::Deserialize;

// ── Twin schema (subset of archipelago.json) ────────────────────────────────
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
    isle: String,
}

// ── GPU structs — must match std430 in archipelago_field.comp.glsl ───────────
#[repr(C)]
#[derive(Clone, Copy)]
struct Island {
    lat: f32,
    lon: f32,
    elev: f32,
    seed: f32,
}

#[repr(C)]
#[derive(Clone, Copy)]
struct Push {
    count: u32,
    w: u32,
    h: u32,
    min_lat: f32,
    max_lat: f32,
    min_lon: f32,
    max_lon: f32,
}

const W: u32 = 56;
const H: u32 = 22;

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
        .expect("no suitable Vulkan memory type")
}

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
    let hc = vk::MemoryPropertyFlags::HOST_VISIBLE | vk::MemoryPropertyFlags::HOST_COHERENT;
    let mem = device
        .allocate_memory(
            &vk::MemoryAllocateInfo::default()
                .allocation_size(reqs.size)
                .memory_type_index(find_memory_type(instance, pd, reqs.memory_type_bits, hc)),
            None,
        )
        .expect("allocate_memory");
    device.bind_buffer_memory(buf, mem, 0).expect("bind_buffer_memory");
    (buf, mem)
}

fn main() {
    let path = std::env::args()
        .nth(1)
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("../../CLAUDEBASE/charts/archipelago.json"));
    let raw = std::fs::read_to_string(&path)
        .unwrap_or_else(|e| panic!("read {}: {e}\n  run from vulkan-lab/cli-renderer/ or pass the twin path", path.display()));
    let twin: Twin = serde_json::from_str(&raw).expect("parse archipelago.json");
    let n = twin.islands.len();
    assert!(n > 0, "no islands in the twin");

    // Bounding box with a small pad so islands don't land on the frame edge.
    let (mut min_lat, mut max_lat) = (f32::MAX, f32::MIN);
    let (mut min_lon, mut max_lon) = (f32::MAX, f32::MIN);
    for i in &twin.islands {
        min_lat = min_lat.min(i.lat);
        max_lat = max_lat.max(i.lat);
        min_lon = min_lon.min(i.lon);
        max_lon = max_lon.max(i.lon);
    }
    let pad_lat = (max_lat - min_lat) * 0.08 + 0.1;
    let pad_lon = (max_lon - min_lon) * 0.08 + 0.1;
    min_lat -= pad_lat;
    max_lat += pad_lat;
    min_lon -= pad_lon;
    max_lon += pad_lon;

    // Seed = real elevation → an inverse-distance topography field over the sea.
    let islands: Vec<Island> = twin
        .islands
        .iter()
        .map(|i| Island { lat: i.lat, lon: i.lon, elev: i.elevation_m, seed: i.elevation_m })
        .collect();

    // ── Vulkan: instance → device → queue (mirrors euler_score in main.rs) ───
    let entry = unsafe { Entry::load().expect("Vulkan loader not found — install NVIDIA drivers") };
    let app = vk::ApplicationInfo::default()
        .application_name(c"archipelago_field")
        .api_version(vk::API_VERSION_1_3);
    let instance: Instance = unsafe {
        entry
            .create_instance(&vk::InstanceCreateInfo::default().application_info(&app), None)
            .expect("create_instance")
    };
    let pd = unsafe { instance.enumerate_physical_devices().expect("enumerate_physical_devices") }[0];
    let props = unsafe { instance.get_physical_device_properties(pd) };
    let gpu = unsafe { CStr::from_ptr(props.device_name.as_ptr()) }
        .to_string_lossy()
        .into_owned();

    let qf_props = unsafe { instance.get_physical_device_queue_family_properties(pd) };
    let qf = qf_props
        .iter()
        .enumerate()
        .filter(|(_, q)| q.queue_flags.contains(vk::QueueFlags::COMPUTE))
        .min_by_key(|(_, q)| if q.queue_flags.contains(vk::QueueFlags::GRAPHICS) { 1u8 } else { 0u8 })
        .map(|(i, _)| i as u32)
        .expect("no compute-capable queue family");
    let prio = [1.0f32];
    let qci = [vk::DeviceQueueCreateInfo::default()
        .queue_family_index(qf)
        .queue_priorities(&prio)];
    let device: Device = unsafe {
        instance
            .create_device(pd, &vk::DeviceCreateInfo::default().queue_create_infos(&qci), None)
            .expect("create_device")
    };
    let queue = unsafe { device.get_device_queue(qf, 0) };

    println!("archipelago_field  L−5 seam  GPU: {gpu}  islands: {n}  grid: {W}×{H}");

    // ── Buffers: islands (in) + field (out) ─────────────────────────────────
    let island_bytes = (n * mem::size_of::<Island>()) as u64;
    let field_len = (W * H) as usize;
    let field_bytes = (field_len * mem::size_of::<f32>()) as u64;
    let ssbo = vk::BufferUsageFlags::STORAGE_BUFFER;
    let (island_buf, island_mem) = unsafe { alloc_mapped_buffer(&device, &instance, pd, island_bytes, ssbo) };
    let (field_buf, field_mem) = unsafe { alloc_mapped_buffer(&device, &instance, pd, field_bytes, ssbo) };

    unsafe {
        let ptr = device
            .map_memory(island_mem, 0, island_bytes, vk::MemoryMapFlags::empty())
            .expect("map island_mem") as *mut Island;
        std::ptr::copy_nonoverlapping(islands.as_ptr(), ptr, n);
        device.unmap_memory(island_mem);
    }

    // ── Shader → descriptor layout → pipeline (push constants for grid/bbox) ─
    let spv_bytes = include_bytes!("../../shaders/archipelago_field.comp.spv");
    let spv_words: Vec<u32> = spv_bytes
        .chunks_exact(4)
        .map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]]))
        .collect();
    let shader = unsafe {
        device
            .create_shader_module(&vk::ShaderModuleCreateInfo::default().code(&spv_words), None)
            .expect("create_shader_module")
    };

    let bindings = [0u32, 1].map(|i| {
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
    let pc_range = [vk::PushConstantRange {
        stage_flags: vk::ShaderStageFlags::COMPUTE,
        offset: 0,
        size: mem::size_of::<Push>() as u32,
    }];
    let layout = unsafe {
        device
            .create_pipeline_layout(
                &vk::PipelineLayoutCreateInfo::default()
                    .set_layouts(&[dsl])
                    .push_constant_ranges(&pc_range),
                None,
            )
            .expect("create_pipeline_layout")
    };
    let stage = vk::PipelineShaderStageCreateInfo::default()
        .stage(vk::ShaderStageFlags::COMPUTE)
        .module(shader)
        .name(c"main");
    let pipeline = unsafe {
        device
            .create_compute_pipelines(
                vk::PipelineCache::null(),
                &[vk::ComputePipelineCreateInfo::default().stage(stage).layout(layout)],
                None,
            )
            .expect("create_compute_pipelines")[0]
    };

    // ── Descriptor pool → set → write ───────────────────────────────────────
    let pool_sizes = [vk::DescriptorPoolSize {
        ty: vk::DescriptorType::STORAGE_BUFFER,
        descriptor_count: 2,
    }];
    let pool = unsafe {
        device
            .create_descriptor_pool(
                &vk::DescriptorPoolCreateInfo::default().max_sets(1).pool_sizes(&pool_sizes),
                None,
            )
            .expect("create_descriptor_pool")
    };
    let set = unsafe {
        device
            .allocate_descriptor_sets(
                &vk::DescriptorSetAllocateInfo::default()
                    .descriptor_pool(pool)
                    .set_layouts(&[dsl]),
            )
            .expect("allocate_descriptor_sets")[0]
    };
    let infos = [
        vk::DescriptorBufferInfo { buffer: island_buf, offset: 0, range: island_bytes },
        vk::DescriptorBufferInfo { buffer: field_buf, offset: 0, range: field_bytes },
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

    // ── Command buffer: push constants → dispatch ───────────────────────────
    let cmd_pool = unsafe {
        device
            .create_command_pool(
                &vk::CommandPoolCreateInfo::default().queue_family_index(qf),
                None,
            )
            .expect("create_command_pool")
    };
    let cmd = unsafe {
        device
            .allocate_command_buffers(
                &vk::CommandBufferAllocateInfo::default()
                    .command_pool(cmd_pool)
                    .level(vk::CommandBufferLevel::PRIMARY)
                    .command_buffer_count(1),
            )
            .expect("allocate_command_buffers")[0]
    };

    let push = Push { count: n as u32, w: W, h: H, min_lat, max_lat, min_lon, max_lon };
    let push_bytes: [u8; 28] = unsafe { mem::transmute(push) };
    let groups = (field_len as u32 + 63) / 64;
    let cmd_bufs = [cmd];
    unsafe {
        device
            .begin_command_buffer(
                cmd,
                &vk::CommandBufferBeginInfo::default()
                    .flags(vk::CommandBufferUsageFlags::ONE_TIME_SUBMIT),
            )
            .expect("begin_command_buffer");
        device.cmd_bind_pipeline(cmd, vk::PipelineBindPoint::COMPUTE, pipeline);
        device.cmd_bind_descriptor_sets(cmd, vk::PipelineBindPoint::COMPUTE, layout, 0, &[set], &[]);
        device.cmd_push_constants(cmd, layout, vk::ShaderStageFlags::COMPUTE, 0, &push_bytes);
        device.cmd_dispatch(cmd, groups, 1, 1);
        device.end_command_buffer(cmd).expect("end_command_buffer");
    }
    let fence = unsafe {
        device.create_fence(&vk::FenceCreateInfo::default(), None).expect("create_fence")
    };
    unsafe {
        device
            .queue_submit(queue, &[vk::SubmitInfo::default().command_buffers(&cmd_bufs)], fence)
            .expect("queue_submit");
        device.wait_for_fences(&[fence], true, u64::MAX).expect("wait_for_fences");
    }

    // ── Read back the field (HOST_COHERENT — no flush) ──────────────────────
    let field: Vec<f32> = unsafe {
        let ptr = device
            .map_memory(field_mem, 0, field_bytes, vk::MemoryMapFlags::empty())
            .expect("map field_mem") as *const f32;
        let v = std::slice::from_raw_parts(ptr, field_len).to_vec();
        device.unmap_memory(field_mem);
        v
    };

    render(&field, &twin.islands, min_lat, max_lat, min_lon, max_lon);

    unsafe { device.device_wait_idle().ok() };
}

fn render(field: &[f32], islands: &[IslandJson], min_lat: f32, max_lat: f32, min_lon: f32, max_lon: f32) {
    let fmin = field.iter().copied().fold(f32::MAX, f32::min);
    let fmax = field.iter().copied().fold(f32::MIN, f32::max);
    let span = (fmax - fmin).max(1e-6);
    const RAMP: [char; 6] = [' ', '·', '░', '▒', '▓', '█'];

    // Island overlay: stamp each island's nearest cell with a letter.
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
                let code = if v < 0.2 { "38;5;39" } else if v < 0.4 { "38;5;45" }
                    else if v < 0.6 { "38;5;226" } else if v < 0.8 { "38;5;208" } else { "38;5;196" };
                let g = RAMP[((v * (RAMP.len() - 1) as f32).round() as usize).min(RAMP.len() - 1)];
                line.push_str(&format!("\x1b[{code}m{g}\x1b[0m"));
            }
        }
        println!("{line}");
    }
    println!("\n  inverse-distance ELEVATION field over the archipelago · {fmin:.0}–{fmax:.0} m · low→high = blue→red");
    let mut legend: Vec<(char, &str)> = overlay.values().map(|(c, n)| (*c, n.as_str())).collect();
    legend.sort_by_key(|(c, _)| *c);
    let legend_str = legend.iter().map(|(c, n)| format!("{c} {n}")).collect::<Vec<_>>().join("   ");
    println!("  {legend_str}\n");
}
