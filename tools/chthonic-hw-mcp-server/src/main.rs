// @SID: TOOL_CHTHONIC_HW_MCP_SERVER_V1
// ============================================================
// chthonic-hw-mcp-server — native hardware/driver environment MCP server (rmcp 1.x)
//
// Separate process from chthonic-mcp-server / vulkan-mcp-server: WMI/COM and
// NVML are FFI surfaces that can hard-crash a process (COM apartment
// violations, driver-level access violations) in ways Rust's Result<T,E>
// cannot catch. Isolating that failure domain from the stable, pure-logic
// Vulkan spec tools follows the repo's modular-siblings-never-strangler-fig
// convention (see tools/MCP_SERVERS.md).
//
// Three tools:
//   hw_inspect       static + semi-static inventory (CPU/RAM/board/storage via
//                    WMI, driver/CUDA/Vulkan/DLSS/cuDNN versions via Win32 +
//                    env vars). Cached to .chthonic/cache/hw_inspect.json with
//                    a 24h TTL; `live: true` forces a fresh probe.
//   gpu_telemetry    dynamic GPU state via NVML (utilization, VRAM, clocks,
//                    temp, power). Always live — caching telemetry defeats
//                    its purpose.
//   hw_drift_check   compares the hw_inspect snapshot against the versions
//                    documented in docs/reference/COMPUTE_FRONTIER_LANDSCAPE.md
//                    and NVIDIA_DLL_INVENTORY.md, flagging real drift while
//                    tolerating legitimate per-directory variation (e.g.
//                    app-bundled DLSS).
//
// Transport: stdio (rmcp). Tracing -> stderr (stdout is the JSON-RPC channel).
// Repo root: CHTHONIC_ROOT env (set by .mcp.json) -> cwd fallback.
// ============================================================

#![allow(non_camel_case_types)]

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::{CallToolResult, ContentBlock, ServerCapabilities, ServerInfo};
use rmcp::{tool, tool_handler, tool_router, ErrorData, ServerHandler, ServiceExt};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use tracing::{info, warn};

mod collectors;
mod drift;

use collectors::{cuda_vulkan, dll_version, nvml, wmi_inventory};

const CACHE_TTL_SECS: u64 = 24 * 60 * 60; // 24h — static/semi-static inventory only

// ── Aggregate state types ────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct HwInventory {
    pub probed_at_unix: u64,
    pub cpu: Option<wmi_inventory::CpuInfo>,
    pub memory: Vec<wmi_inventory::MemoryModule>,
    pub storage: Vec<wmi_inventory::DiskInfo>,
    pub board: Option<wmi_inventory::BoardInfo>,
    pub driver_version: Option<String>,
    pub cuda_umd_max: Option<String>,
    pub nvcc_version: Option<String>,
    pub nvcc_path: Option<String>,
    pub cuda_path_env: HashMap<String, cuda_vulkan::CudaPathSlot>,
    pub vulkan_sdk_path: Option<String>,
    pub vulkan_instance_version: Option<String>,
    pub dll_versions: HashMap<String, String>,
    pub dlss_newest: Option<dll_version::DllInfo>,
    pub cudnn_version: Option<String>,
    pub cudnn_path: Option<String>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct HwInspectParams {
    /// Restrict output to one segment: cpu | memory | storage | board | software | all (default all).
    scope: Option<String>,
    /// Force a fresh probe, bypassing the 24h JSON cache.
    live: Option<bool>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct DriftCheckParams {
    /// Force a fresh hw_inspect probe before comparing (default: use cache/24h TTL like hw_inspect).
    live: Option<bool>,
}

// ── Server ────────────────────────────────────────────────────────────────────

#[derive(Clone)]
struct HwServer {
    repo_root: PathBuf,
    cache_path: PathBuf,
    // Routed through by the #[tool_router] macro-generated code; the dead-code
    // lint can't see that use, so silence it (same pattern as chthonic-mcp-server).
    #[allow(dead_code)]
    tool_router: rmcp::handler::server::router::tool::ToolRouter<HwServer>,
}

impl HwServer {
    fn new() -> Self {
        let repo_root = std::env::var("CHTHONIC_ROOT")
            .map(PathBuf::from)
            .unwrap_or_else(|_| std::env::current_dir().unwrap_or_else(|_| PathBuf::from(".")));
        let cache_path = repo_root.join(".chthonic").join("cache").join("hw_inspect.json");
        Self {
            repo_root,
            cache_path,
            tool_router: Self::tool_router(),
        }
    }

    fn cache_is_fresh(&self) -> bool {
        let Ok(meta) = std::fs::metadata(&self.cache_path) else {
            return false;
        };
        let Ok(modified) = meta.modified() else {
            return false;
        };
        let Ok(age) = SystemTime::now().duration_since(modified) else {
            return false;
        };
        age < Duration::from_secs(CACHE_TTL_SECS)
    }

    fn load_cache(&self) -> Option<HwInventory> {
        let text = std::fs::read_to_string(&self.cache_path).ok()?;
        serde_json::from_str(&text).ok()
    }

    fn write_cache(&self, inv: &HwInventory) {
        if let Some(parent) = self.cache_path.parent() {
            let _ = std::fs::create_dir_all(parent);
        }
        if let Ok(text) = serde_json::to_string_pretty(inv) {
            if let Err(e) = std::fs::write(&self.cache_path, text) {
                warn!("failed to write hw_inspect cache: {e}");
            }
        }
    }

    /// Full static + semi-static probe. WMI runs on its own async path (the
    /// `wmi` crate initializes COM internally per-call); DLL/env reads are
    /// synchronous but sub-millisecond, so no spawn_blocking is needed.
    async fn probe(&self) -> HwInventory {
        let probed_at_unix = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        let (cpu, memory, storage, board) = wmi_inventory::collect_all().await;

        let (driver_version, cuda_umd_max) = nvml::driver_and_cuda_umd();
        let (nvcc_version, nvcc_path) = cuda_vulkan::nvcc_version_and_path();
        let cuda_path_env = cuda_vulkan::cuda_path_env_slots();
        let (vulkan_sdk_path, vulkan_instance_version) = cuda_vulkan::vulkan_sdk_state();

        let dll_versions = dll_version::system32_driver_dlls();
        let dlss_newest = dll_version::newest_dlss(&self.repo_root);
        let (cudnn_version, cudnn_path) = dll_version::cudnn_state();

        HwInventory {
            probed_at_unix,
            cpu,
            memory,
            storage,
            board,
            driver_version,
            cuda_umd_max,
            nvcc_version,
            nvcc_path,
            cuda_path_env,
            vulkan_sdk_path,
            vulkan_instance_version,
            dll_versions,
            dlss_newest,
            cudnn_version,
            cudnn_path,
        }
    }

    async fn inventory(&self, force_live: bool) -> HwInventory {
        if !force_live && self.cache_is_fresh() {
            if let Some(cached) = self.load_cache() {
                return cached;
            }
        }
        let fresh = self.probe().await;
        self.write_cache(&fresh);
        fresh
    }
}

fn scope_filter(inv: &HwInventory, scope: &str) -> serde_json::Value {
    match scope {
        "cpu" => serde_json::json!({ "cpu": inv.cpu }),
        "memory" => serde_json::json!({ "memory": inv.memory }),
        "storage" => serde_json::json!({ "storage": inv.storage }),
        "board" => serde_json::json!({ "board": inv.board }),
        "software" => serde_json::json!({
            "driver_version": inv.driver_version,
            "cuda_umd_max": inv.cuda_umd_max,
            "nvcc_version": inv.nvcc_version,
            "nvcc_path": inv.nvcc_path,
            "cuda_path_env": inv.cuda_path_env,
            "vulkan_sdk_path": inv.vulkan_sdk_path,
            "vulkan_instance_version": inv.vulkan_instance_version,
            "dll_versions": inv.dll_versions,
            "dlss_newest": inv.dlss_newest,
            "cudnn_version": inv.cudnn_version,
            "cudnn_path": inv.cudnn_path,
        }),
        _ => serde_json::to_value(inv).unwrap_or(serde_json::Value::Null),
    }
}

#[tool_router]
impl HwServer {
    #[tool(
        description = "Static + semi-static hardware/driver inventory: CPU, RAM, motherboard, storage (WMI), plus NVIDIA driver/CUDA/Vulkan/DLSS/cuDNN versions (Win32 VersionInfo + env vars). Cached 24h; pass live=true to force a fresh probe. scope narrows output to cpu|memory|storage|board|software|all."
    )]
    async fn hw_inspect(
        &self,
        Parameters(p): Parameters<HwInspectParams>,
    ) -> Result<CallToolResult, ErrorData> {
        let inv = self.inventory(p.live.unwrap_or(false)).await;
        let scope = p.scope.as_deref().unwrap_or("all");
        let value = scope_filter(&inv, scope);
        let text = serde_json::to_string_pretty(&value)
            .unwrap_or_else(|e| format!("serialization error: {e}"));
        Ok(CallToolResult::success(vec![ContentBlock::text(text)]))
    }

    #[tool(
        description = "Live GPU telemetry via NVML — utilization, VRAM used/total, graphics/memory clocks, core temp, power draw, fan speed. Always queries fresh (no caching — dynamic state decays immediately)."
    )]
    async fn gpu_telemetry(&self) -> Result<CallToolResult, ErrorData> {
        match nvml::query_telemetry() {
            Ok(t) => {
                let text = serde_json::to_string_pretty(&t)
                    .unwrap_or_else(|e| format!("serialization error: {e}"));
                Ok(CallToolResult::success(vec![ContentBlock::text(text)]))
            }
            Err(e) => Ok(CallToolResult::error(vec![ContentBlock::text(format!(
                "NVML query failed: {e}"
            ))])),
        }
    }

    #[tool(
        description = "Compare live hardware/driver state against docs/reference/COMPUTE_FRONTIER_LANDSCAPE.md and NVIDIA_DLL_INVENTORY.md. Reports per-component drift with severity (info|warning|critical) and flags legitimate variations (e.g. app-bundled DLSS) rather than false-positiving on them."
    )]
    async fn hw_drift_check(
        &self,
        Parameters(p): Parameters<DriftCheckParams>,
    ) -> Result<CallToolResult, ErrorData> {
        let inv = self.inventory(p.live.unwrap_or(false)).await;
        let report = drift::check(&self.repo_root, &inv);
        let text = serde_json::to_string_pretty(&report)
            .unwrap_or_else(|e| format!("serialization error: {e}"));
        Ok(CallToolResult::success(vec![ContentBlock::text(text)]))
    }
}

#[tool_handler]
impl ServerHandler for HwServer {
    fn get_info(&self) -> ServerInfo {
        let mut info = ServerInfo::default();
        info.server_info.name = "chthonic-hw-mcp-server".to_string();
        info.server_info.version = env!("CARGO_PKG_VERSION").to_string();
        info.capabilities = ServerCapabilities::builder().enable_tools().build();
        info.instructions = Some(
            "Native hardware/driver environment probe (WMI + Win32 VersionInfo + NVML — no \
             PowerShell subprocess on the hot path). `hw_inspect` for static/semi-static \
             CPU/RAM/board/storage/driver/SDK state (cached 24h, live=true to force fresh). \
             `gpu_telemetry` for live NVML metrics (always fresh). `hw_drift_check` to compare \
             live state against docs/reference/COMPUTE_FRONTIER_LANDSCAPE.md and \
             NVIDIA_DLL_INVENTORY.md."
                .to_string(),
        );
        info
    }
}

#[allow(dead_code)]
fn repo_relative(root: &Path, rel: &str) -> PathBuf {
    root.join(rel)
}

// ── main ──────────────────────────────────────────────────────────────────────

/// One-shot warm-start summary for the SessionStart hook: respects the 24h
/// cache (cheap on every session after the first each day), prints one
/// compact line to stdout, never touches the MCP stdio transport. Avoids
/// making the hook drive a full JSON-RPC handshake just for one probe.
async fn warm_start_summary() -> anyhow::Result<()> {
    let server = HwServer::new();
    let inv = server.inventory(false).await;

    let vram_gb = inv
        .memory
        .iter()
        .map(|m| m.capacity_bytes)
        .sum::<u64>() as f64
        / (1024.0 * 1024.0 * 1024.0);

    println!(
        "GPU driver {} | CUDA UMD {} | Vulkan SDK {} | cuDNN {} | DLSS {} | RAM {:.0} GB",
        inv.driver_version.as_deref().unwrap_or("?"),
        inv.cuda_umd_max.as_deref().unwrap_or("?"),
        inv.vulkan_sdk_path
            .as_deref()
            .and_then(|p| p.split(['\\', '/']).last())
            .unwrap_or("?"),
        inv.cudnn_version.as_deref().unwrap_or("?"),
        inv.dlss_newest.as_ref().map(|d| d.version.as_str()).unwrap_or("?"),
        vram_gb,
    );
    Ok(())
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    if std::env::args().any(|a| a == "--warm-start-summary") {
        return warm_start_summary().await;
    }

    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "chthonic_hw_mcp_server=info".into()),
        )
        .with_writer(std::io::stderr)
        .init();

    let server = HwServer::new();
    info!(
        "chthonic-hw-mcp-server starting (repo_root={}, cache={})",
        server.repo_root.display(),
        server.cache_path.display()
    );

    let service = server.serve(rmcp::transport::stdio()).await?;
    service.waiting().await?;
    Ok(())
}
