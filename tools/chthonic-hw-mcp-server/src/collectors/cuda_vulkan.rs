// CUDA/Vulkan environment probing — pure env var + filesystem reads, plus two
// narrowly-scoped subprocess calls (nvcc --version, glslc/vulkaninfoSDK
// --version) that have no native-Rust equivalent. Both run only on a 24h
// cache miss via hw_inspect, never on a hot path — the same reasoning that
// keeps a subprocess call acceptable for a rarely-invoked, cached probe.

use std::collections::HashMap;
use std::path::Path;
use std::process::Command;

use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct CudaPathSlot {
    pub value: Option<String>,
    pub exists: bool,
    pub has_nvcc: bool,
    pub has_cudart_lib: bool,
    pub cudart_dll: Option<String>,
}

const CUDA_PATH_VARS: &[&str] = &[
    "CUDA_PATH",
    "CUDA_PATH_V12_8",
    "CUDA_PATH_V12_9",
    "CUDA_PATH_V13_2",
    "CUDA_PATH_V13_3",
];

pub fn cuda_path_env_slots() -> HashMap<String, CudaPathSlot> {
    let mut out = HashMap::new();
    for var in CUDA_PATH_VARS {
        let value = std::env::var(var).ok();
        let slot = match &value {
            Some(v) => {
                let base = Path::new(v);
                let has_nvcc = base.join("bin").join("nvcc.exe").exists();
                let has_cudart_lib = base.join("lib").join("x64").join("cudart.lib").exists();
                let cudart_dll = std::fs::read_dir(base.join("bin")).ok().and_then(|entries| {
                    entries
                        .filter_map(|e| e.ok())
                        .map(|e| e.file_name().to_string_lossy().into_owned())
                        .find(|name| name.starts_with("cudart64_") && name.ends_with(".dll"))
                });
                CudaPathSlot {
                    value: value.clone(),
                    exists: base.exists(),
                    has_nvcc,
                    has_cudart_lib,
                    cudart_dll,
                }
            }
            None => CudaPathSlot {
                value: None,
                exists: false,
                has_nvcc: false,
                has_cudart_lib: false,
                cudart_dll: None,
            },
        };
        out.insert((*var).to_string(), slot);
    }
    out
}

fn which_nvcc() -> Option<String> {
    if let Ok(cuda_path) = std::env::var("CUDA_PATH") {
        let candidate = Path::new(&cuda_path).join("bin").join("nvcc.exe");
        if candidate.exists() {
            return Some(candidate.to_string_lossy().into_owned());
        }
    }
    let path_var = std::env::var("PATH").ok()?;
    for dir in path_var.split(';') {
        let candidate = Path::new(dir).join("nvcc.exe");
        if candidate.exists() {
            return Some(candidate.to_string_lossy().into_owned());
        }
    }
    None
}

pub fn nvcc_version_and_path() -> (Option<String>, Option<String>) {
    let path = which_nvcc();
    let version = path.as_ref().and_then(|p| {
        Command::new(p).arg("--version").output().ok().and_then(|o| {
            let text = String::from_utf8_lossy(&o.stdout);
            text.lines().find_map(|l| {
                l.split("release ")
                    .nth(1)
                    .map(|rest| rest.split(',').next().unwrap_or(rest).trim().to_string())
            })
        })
    });
    (version, path)
}

pub fn vulkan_sdk_state() -> (Option<String>, Option<String>) {
    let sdk_path = std::env::var("VULKAN_SDK").ok();
    let instance_version = sdk_path.as_ref().and_then(|sdk| {
        let vkinfo = Path::new(sdk).join("Bin").join("vulkaninfoSDK.exe");
        if !vkinfo.exists() {
            return None;
        }
        Command::new(&vkinfo).arg("--version").output().ok().and_then(|o| {
            let text = String::from_utf8_lossy(&o.stdout);
            text.lines()
                .find_map(|l| l.split("Vulkan Instance Version:").nth(1))
                .map(|v| v.trim().to_string())
        })
    });
    (sdk_path, instance_version)
}
