use std::io::{self, BufRead, Write};

use anyhow::{Context, Result};
use clap::{Parser, ValueEnum};
use serde::Serialize;

mod anno;
mod entropy_monitor;
mod env;
mod reactor;
mod synapse;
mod types;

use types::{
    JsonRpcError, JsonRpcNotification, JsonRpcRequest, JsonRpcSuccess,
    SedimentRequest,
};

#[derive(Clone, Copy, Debug, PartialEq, Eq, ValueEnum)]
enum ReactorTransportMode {
    #[value(name = "auto")]
    Auto,
    #[value(name = "shared_memory", alias = "shm", alias = "synapse")]
    SharedMemory,
    #[value(name = "jsonl", alias = "safe")]
    Jsonl,
}

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

    /// Sediment transport mode. Defaults to CHTHONIC_REACTOR_TRANSPORT, then auto.
    #[arg(long, value_enum)]
    transport: Option<ReactorTransportMode>,
}

fn main() -> Result<()> {
    let opts = Opts::parse();
    let transport_mode = reactor_transport_mode(opts.transport);

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
    // Phase 3.5: Shared memory synapse initialization
    // -------------------------------------------------------------------

    let mut synapse_writer = if transport_mode == ReactorTransportMode::Jsonl {
        write_json(&JsonRpcNotification {
            jsonrpc: "2.0",
            method: "reactor/synapse",
            params: &serde_json::json!({
                "status": "disabled",
                "mode": "jsonl",
            }),
        })?;
        None
    } else {
        match synapse::SynapseWriter::create() {
            Ok(writer) => {
                write_json(&JsonRpcNotification {
                    jsonrpc: "2.0",
                    method: "reactor/synapse",
                    params: writer.descriptor(),
                })?;
                Some(writer)
            }
            Err(err) => {
                write_json(&JsonRpcNotification {
                    jsonrpc: "2.0",
                    method: "reactor/synapse",
                    params: &serde_json::json!({
                        "status": "unavailable",
                        "mode": "jsonl",
                        "reason": format!("{err:#}")
                    }),
                })?;
                eprintln!("[daemon] shared memory synapse unavailable; falling back to JSONL: {err:#}");
                None
            }
        }
    };

    // -------------------------------------------------------------------
    // Phase 3.75: Entropy monitor initialization
    // -------------------------------------------------------------------

    let entropy_monitor = entropy_monitor::EntropyMonitor::start(
        entropy_monitor::EntropyMonitorOptions::from_env(opts.workspace.clone()),
        |state| {
            if let Err(error) = write_json(&JsonRpcNotification {
                jsonrpc: "2.0",
                method: "reactor/entropyState",
                params: &state,
            }) {
                eprintln!("[daemon] failed to emit entropy state: {error:#}");
            }
        },
    );

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

            "reactor/sediment_stream" => {
                let params: SedimentRequest =
                    serde_json::from_value(request.params.clone())
                        .unwrap_or_default();

                let result = match &vulkan_reactor {
                    Some(r) => r.compute_sediment(&opts.workspace, &params),
                    None => compute_sediment_cpu(&opts.workspace, &params),
                };

                match result {
                    Ok(r) => {
                        stream_sediment_chunks(&r, params.chunk_size.max(1))?;
                        write_json(&JsonRpcSuccess {
                            jsonrpc: "2.0",
                            id: request.id,
                            result: &r,
                        })?;
                    }
                    Err(err) => write_json(&JsonRpcError::internal(
                        request.id,
                        err,
                    ))?,
                }
            }

            "reactor/sediment_synapse" => {
                let params: SedimentRequest =
                    serde_json::from_value(request.params.clone())
                        .unwrap_or_default();

                let result = reactor::simulate_firedancer_telemetry(&opts.workspace, &params);

                match result {
                    Ok(r) => {
                        let publish = if let Some(writer) = synapse_writer.as_mut() {
                            writer.publish_result(&r, params.chunk_size.max(1))?
                        } else {
                            synapse::SynapsePublishSummary {
                                total_chunks: 0,
                                chunks_written: 0,
                                dropped_chunks: 0,
                                queue_depth: 0,
                            }
                        };

                        write_json(&JsonRpcSuccess {
                            jsonrpc: "2.0",
                            id: request.id,
                            result: &serde_json::json!({
                                "backend": r.backend,
                                "layer_count": r.layer_count,
                                "file_count": r.file_count,
                                "compute_time_ms": r.compute_time_ms,
                                "total_chunks": publish.total_chunks,
                                "chunks_written": publish.chunks_written,
                                "dropped_chunks": publish.dropped_chunks,
                                "queue_depth": publish.queue_depth,
                                "transport": if synapse_writer.is_some() { "shared_memory" } else { "jsonl" },
                            }),
                        })?;

                        if let Some(telemetry) = &r.telemetry {
                            write_json(&JsonRpcNotification {
                                jsonrpc: "2.0",
                                method: "reactor/firedancerSurge",
                                params: &serde_json::json!({
                                    "slot": telemetry.slot,
                                    "shred_count": telemetry.shred_count,
                                    "packet_count": telemetry.packet_count,
                                    "simulated_tps": telemetry.simulated_tps,
                                    "surge": telemetry.surge,
                                }),
                            })?;
                        }
                    }
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

            "reactor/entropy_state" => {
                let snapshot = entropy_monitor.snapshot();
                write_json(&JsonRpcSuccess {
                    jsonrpc: "2.0",
                    id: request.id,
                    result: &snapshot,
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

    let metrics = reactor::gather_git_metrics(workspace, params)?;
    let settled = reactor::cpu_simulate(metrics.nodes);

    Ok(types::SedimentResult {
        file_count: settled.len() as u32,
        layer_count: metrics.layer_count,
        vertices: settled
            .iter()
            .map(|n| types::SedimentVertex {
                x: n.pos_x,
                y: n.pos_y,
                z: n.pos_z,
                radius: 2.0 + n.entropy * 5.0 + n.mass * 1.5,
                r: n.r,
                g: n.g,
                b: n.b,
                alpha: n.a,
            })
            .collect(),
        compute_time_ms: start.elapsed().as_millis() as u64,
        backend: "cpu-only",
        telemetry: None,
    })
}

fn stream_sediment_chunks(result: &types::SedimentResult, chunk_size: u32) -> Result<()> {
    let chunk_size = chunk_size.max(1) as usize;
    let total_chunks = ((result.vertices.len() + chunk_size - 1) / chunk_size) as u32;

    for (chunk_index, vertices) in result.vertices.chunks(chunk_size).enumerate() {
        write_json(&JsonRpcNotification {
            jsonrpc: "2.0",
            method: "reactor/sedimentChunk",
            params: &serde_json::json!({
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
                "layer_count": result.layer_count,
                "file_count": result.file_count,
                "backend": result.backend,
                "vertices": vertices,
            }),
        })?;
    }

    Ok(())
}

fn write_json<T: Serialize>(value: &T) -> Result<()> {
    let encoded = serde_json::to_string(value)?;
    let mut stdout = io::stdout().lock();
    stdout.write_all(encoded.as_bytes())?;
    stdout.write_all(b"\n")?;
    stdout.flush()?;
    Ok(())
}

fn reactor_transport_mode(cli_mode: Option<ReactorTransportMode>) -> ReactorTransportMode {
    if let Some(mode) = cli_mode {
        return mode;
    }

    match std::env::var("CHTHONIC_REACTOR_TRANSPORT") {
        Ok(raw) => match raw.trim().to_ascii_lowercase().as_str() {
            "shared_memory" | "shm" | "synapse" => ReactorTransportMode::SharedMemory,
            "jsonl" | "safe" => ReactorTransportMode::Jsonl,
            _ => ReactorTransportMode::Auto,
        },
        Err(_) => ReactorTransportMode::Auto,
    }
}
