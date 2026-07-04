// Native NVML access — replaces `nvidia-smi` subprocess calls entirely.
// NVML exposes both driver/CUDA version (static-ish, read once per hw_inspect
// probe) and live telemetry (dynamic, read fresh on every gpu_telemetry call)
// through the same handle, at sub-millisecond latency.

use nvml_wrapper::enum_wrappers::device::{Clock, TemperatureSensor};
use nvml_wrapper::Nvml;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GpuTelemetry {
    pub name: String,
    pub gpu_utilization_percent: u32,
    pub memory_utilization_percent: u32,
    pub vram_used_bytes: u64,
    pub vram_total_bytes: u64,
    pub graphics_clock_mhz: u32,
    pub memory_clock_mhz: u32,
    pub temperature_celsius: u32,
    pub power_usage_milliwatts: u32,
    pub fan_speed_percent: Option<u32>,
}

/// Driver version + CUDA UMD max, read natively via NVML — no nvidia-smi subprocess.
pub fn driver_and_cuda_umd() -> (Option<String>, Option<String>) {
    let nvml = match Nvml::init() {
        Ok(n) => n,
        Err(e) => {
            tracing::warn!("NVML init failed: {e}");
            return (None, None);
        }
    };
    let driver = nvml.sys_driver_version().ok();
    let cuda_umd = nvml.sys_cuda_driver_version().ok().map(|v| {
        format!(
            "{}.{}",
            nvml_wrapper::cuda_driver_version_major(v),
            nvml_wrapper::cuda_driver_version_minor(v)
        )
    });
    (driver, cuda_umd)
}

pub fn query_telemetry() -> anyhow::Result<GpuTelemetry> {
    let nvml = Nvml::init()?;
    let device = nvml.device_by_index(0)?;

    let name = device.name()?;
    let util = device.utilization_rates()?;
    let mem = device.memory_info()?;
    let graphics_clock = device.clock_info(Clock::Graphics)?;
    let memory_clock = device.clock_info(Clock::Memory)?;
    let temp = device.temperature(TemperatureSensor::Gpu)?;
    let power = device.power_usage()?;
    let fan = device.fan_speed(0).ok();

    Ok(GpuTelemetry {
        name,
        gpu_utilization_percent: util.gpu,
        memory_utilization_percent: util.memory,
        vram_used_bytes: mem.used,
        vram_total_bytes: mem.total,
        graphics_clock_mhz: graphics_clock,
        memory_clock_mhz: memory_clock,
        temperature_celsius: temp,
        power_usage_milliwatts: power,
        fan_speed_percent: fan,
    })
}
