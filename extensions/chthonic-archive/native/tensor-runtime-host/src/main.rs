use std::fs;
use std::path::{Path, PathBuf};

use anyhow::Result;
use clap::Parser;
use libloading::Library;
use serde::Serialize;

#[derive(Parser, Debug)]
#[command(name = "tensor-runtime-host")]
struct Opts {
    #[arg(long, default_value_t = false)]
    json: bool,
}

#[derive(Debug, Serialize)]
struct TensorRuntimeStatus {
    cuda_path: Option<String>,
    tensorrt_dirs: Vec<String>,
    cudnn_dirs: Vec<String>,
    tensorrt_probe: Option<DllProbe>,
    cudnn_probe: Option<DllProbe>,
}

#[derive(Debug, Serialize)]
struct DllProbe {
    path: String,
    loaded: bool,
    error: Option<String>,
}

fn main() -> Result<()> {
    let opts = Opts::parse();
    let status = TensorRuntimeStatus {
        cuda_path: std::env::var("CUDA_PATH").ok(),
        tensorrt_dirs: discover_dirs(r"C:\Program Files\NVIDIA", "TensorRT"),
        cudnn_dirs: discover_dirs(r"C:\Program Files\NVIDIA\CUDNN", ""),
        tensorrt_probe: probe_first_dll(
            &discover_matching_dlls(r"C:\Program Files\NVIDIA", &["nvinfer", "nvinfer_plugin"]),
        ),
        cudnn_probe: probe_first_dll(
            &discover_matching_dlls(r"C:\Program Files\NVIDIA\CUDNN", &["cudnn"]),
        ),
    };

    if opts.json {
        println!("{}", serde_json::to_string_pretty(&status)?);
    } else {
        println!("Tensor Runtime Host");
        println!("  CUDA_PATH: {}", status.cuda_path.as_deref().unwrap_or("unset"));
        println!("  TensorRT dirs: {}", status.tensorrt_dirs.len());
        for dir in &status.tensorrt_dirs {
            println!("    - {dir}");
        }
        println!("  cuDNN dirs: {}", status.cudnn_dirs.len());
        for dir in &status.cudnn_dirs {
            println!("    - {dir}");
        }
        println!("  TensorRT probe: {}", summarize_probe(status.tensorrt_probe.as_ref()));
        println!("  cuDNN probe: {}", summarize_probe(status.cudnn_probe.as_ref()));
    }

    Ok(())
}

fn summarize_probe(probe: Option<&DllProbe>) -> String {
    match probe {
        Some(probe) if probe.loaded => format!("loaded {}", probe.path),
        Some(probe) => format!(
            "failed {} ({})",
            probe.path,
            probe.error.as_deref().unwrap_or("unknown error")
        ),
        None => "not found".to_string(),
    }
}

fn discover_dirs(base: &str, prefix: &str) -> Vec<String> {
    let path = Path::new(base);
    if !path.exists() {
        return Vec::new();
    }

    let mut dirs = Vec::new();
    let entries = match fs::read_dir(path) {
        Ok(entries) => entries,
        Err(_) => return dirs,
    };

    for entry in entries.flatten() {
        let dir_path = entry.path();
        if !dir_path.is_dir() {
            continue;
        }
        let name = entry.file_name().to_string_lossy().to_string();
        if prefix.is_empty() || name.starts_with(prefix) {
            dirs.push(dir_path.display().to_string());
        }
    }

    dirs.sort();
    dirs
}

fn discover_matching_dlls(base: &str, prefixes: &[&str]) -> Vec<PathBuf> {
    let mut found = Vec::new();
    let root = Path::new(base);
    if !root.exists() {
        return found;
    }

    let mut stack = vec![root.to_path_buf()];
    while let Some(dir) = stack.pop() {
        let entries = match fs::read_dir(&dir) {
            Ok(entries) => entries,
            Err(_) => continue,
        };

        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() {
                stack.push(path);
                continue;
            }
            if path.extension().and_then(|ext| ext.to_str()).map(|ext| ext.eq_ignore_ascii_case("dll")) != Some(true) {
                continue;
            }
            let file_name = path.file_name().and_then(|name| name.to_str()).unwrap_or_default().to_ascii_lowercase();
            if prefixes.iter().any(|prefix| file_name.starts_with(&prefix.to_ascii_lowercase())) {
                found.push(path);
            }
        }
    }

    found.sort();
    found
}

fn probe_first_dll(candidates: &[PathBuf]) -> Option<DllProbe> {
    let path = candidates.first()?;
    let outcome = unsafe { Library::new(path) };
    Some(match outcome {
        Ok(_) => DllProbe {
            path: path.display().to_string(),
            loaded: true,
            error: None,
        },
        Err(error) => DllProbe {
            path: path.display().to_string(),
            loaded: false,
            error: Some(error.to_string()),
        },
    })
}
