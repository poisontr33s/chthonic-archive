use std::io::{self, BufRead, Write};

use anyhow::{Context, Result};
use clap::Parser;
use serde::Serialize;

mod anno;
mod env;
mod reactor;
mod types;

use types::{
    JsonRpcError, JsonRpcNotification, JsonRpcRequest, JsonRpcSuccess,
    SedimentRequest,
};

#[derive(Parser, Debug)]
#[command(name = "chthonic-daemon")]
struct Opts {
    /// Workspace root directory to scan for project markers.
    #[arg(long)]
    workspace: String,

    /// Enable headless Vulkan compute for sediment layer calculation.
    /// Falls back to CPU if no Vulkan device is available.
    #[arg(long, default_value_t = false)]
    headless_vulkan: bool,
}

fn main() -> Result<()> {
    let opts = Opts::parse();

    // -------------------------------------------------------------------
    // Phase 1: ANNO project detection
    // -------------------------------------------------------------------

    let manifest = anno::detect_project(&opts.workspace)
        .context("ANNO project detection failed")?;

    write_json(&JsonRpcNotification {
        jsonrpc: "2.0",
        method: "anno/manifest",
        params: &manifest,
    })?;

    // -------------------------------------------------------------------
    // Phase 2: Environment provisioning
    // -------------------------------------------------------------------

    let env_report = env::provision(&manifest, &opts.workspace)
        .context("environment provisioning failed")?;

    write_json(&JsonRpcNotification {
        jsonrpc: "2.0",
        method: "anno/env",
        params: &env_report,
    })?;

    // -------------------------------------------------------------------
    // Phase 3: Vulkan reactor initialization (optional)
    // -------------------------------------------------------------------

    let vulkan_reactor = if opts.headless_vulkan {
        match reactor::initialize() {
            Ok(Some(r)) => {
                write_json(&JsonRpcNotification {
                    jsonrpc: "2.0",
                    method: "reactor/status",
                    params: &serde_json::json!({ "status": "vulkan-ready" }),
                })?;
                Some(r)
            }
            Ok(None) => {
                write_json(&JsonRpcNotification {
                    jsonrpc: "2.0",
                    method: "reactor/status",
                    params: &serde_json::json!({
                        "status": "cpu-only",
                        "reason": "no Vulkan device found"
                    }),
                })?;
                None
            }
            Err(err) => {
                eprintln!("[daemon] Vulkan init error: {err:#}");
                write_json(&JsonRpcNotification {
                    jsonrpc: "2.0",
                    method: "reactor/status",
                    params: &serde_json::json!({
                        "status": "cpu-only",
                        "reason": format!("{err:#}")
                    }),
                })?;
                None
            }
        }
    } else {
        write_json(&JsonRpcNotification {
            jsonrpc: "2.0",
            method: "reactor/status",
            params: &serde_json::json!({ "status": "disabled" }),
        })?;
        None
    };

    // -------------------------------------------------------------------
    // Phase 4: stdin JSON-RPC event loop
    // -------------------------------------------------------------------

    let stdin = io::stdin();
    for line in stdin.lock().lines() {
        let raw = line?;
        let trimmed = raw.trim();
        if trimmed.is_empty() {
            continue;
        }

        let request = match serde_json::from_str::<JsonRpcRequest>(trimmed) {
            Ok(r) => r,
            Err(err) => {
                write_json(&JsonRpcError::parse_error(err))?;
                continue;
            }
        };

        match request.method.as_str() {
            "anno/detect" => {
                match anno::detect_project(&opts.workspace) {
                    Ok(m) => write_json(&JsonRpcSuccess {
                        jsonrpc: "2.0",
                        id: request.id,
                        result: &m,
                    })?,
                    Err(err) => write_json(&JsonRpcError::internal(
                        request.id,
                        err,
                    ))?,
                }
            }

            "anno/provision" => {
                let current = anno::detect_project(&opts.workspace)
                    .unwrap_or_else(|_| manifest.clone());
                match env::provision(&current, &opts.workspace) {
                    Ok(report) => write_json(&JsonRpcSuccess {
                        jsonrpc: "2.0",
                        id: request.id,
                        result: &report,
                    })?,
                    Err(err) => write_json(&JsonRpcError::internal(
                        request.id,
                        err,
                    ))?,
                }
            }

            "reactor/sediment" => {
                let params: SedimentRequest =
                    serde_json::from_value(request.params.clone())
                        .unwrap_or_default();

                let result = match &vulkan_reactor {
                    Some(r) => r.compute_sediment(&opts.workspace, &params),
                    None => compute_sediment_cpu(&opts.workspace, &params),
                };

                match result {
                    Ok(r) => write_json(&JsonRpcSuccess {
                        jsonrpc: "2.0",
                        id: request.id,
                        result: &r,
                    })?,
                    Err(err) => write_json(&JsonRpcError::internal(
                        request.id,
                        err,
                    ))?,
                }
            }

            "reactor/status" => {
                let status = if vulkan_reactor.is_some() {
                    "vulkan-ready"
                } else {
                    "cpu-only"
                };
                write_json(&JsonRpcSuccess {
                    jsonrpc: "2.0",
                    id: request.id,
                    result: &serde_json::json!({ "status": status }),
                })?;
            }

            other => {
                write_json(&JsonRpcError::method_not_found(request.id, other))?;
            }
        }
    }

    Ok(())
}

/// CPU-only sediment computation path. Uses reactor's public API.
fn compute_sediment_cpu(
    workspace: &str,
    params: &SedimentRequest,
) -> Result<types::SedimentResult> {
    let start = std::time::Instant::now();

    // Use reactor's git metrics gathering
    let inputs = reactor::gather_git_metrics(workspace, params)?;
    let vertices = reactor::cpu_fallback(&inputs, params);

    let layer_count = inputs.iter().map(|i| i.layer_depth).max().unwrap_or(0) + 1;

    Ok(types::SedimentResult {
        file_count: inputs.len() as u32,
        layer_count,
        vertices,
        compute_time_ms: start.elapsed().as_millis() as u64,
        backend: "cpu-only",
    })
}

fn write_json<T: Serialize>(value: &T) -> Result<()> {
    let encoded = serde_json::to_string(value)?;
    let mut stdout = io::stdout().lock();
    stdout.write_all(encoded.as_bytes())?;
    stdout.write_all(b"\n")?;
    stdout.flush()?;
    Ok(())
}
