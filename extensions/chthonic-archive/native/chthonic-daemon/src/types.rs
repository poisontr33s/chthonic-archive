use serde::{Deserialize, Serialize};
use std::collections::HashMap;

// ---------------------------------------------------------------------------
// JSON-RPC wire types (mirrors entropy-ledger-host conventions)
// ---------------------------------------------------------------------------

#[derive(Debug, Deserialize)]
pub struct JsonRpcRequest {
    pub id: u64,
    pub method: String,
    #[serde(default)]
    pub params: serde_json::Value,
}

#[derive(Debug, Serialize)]
pub struct JsonRpcNotification<T: Serialize> {
    pub jsonrpc: &'static str,
    pub method: &'static str,
    pub params: T,
}

#[derive(Debug, Serialize)]
pub struct JsonRpcSuccess<T: Serialize> {
    pub jsonrpc: &'static str,
    pub id: u64,
    pub result: T,
}

#[derive(Debug, Serialize)]
pub struct JsonRpcError {
    pub jsonrpc: &'static str,
    pub id: u64,
    pub error: ErrorPayload,
}

#[derive(Debug, Serialize)]
pub struct ErrorPayload {
    pub code: i32,
    pub message: String,
}

impl JsonRpcError {
    pub fn parse_error(err: impl std::fmt::Display) -> Self {
        Self {
            jsonrpc: "2.0",
            id: 0,
            error: ErrorPayload {
                code: -32700,
                message: format!("invalid JSON: {err}"),
            },
        }
    }

    pub fn method_not_found(id: u64, method: &str) -> Self {
        Self {
            jsonrpc: "2.0",
            id,
            error: ErrorPayload {
                code: -32601,
                message: format!("unknown method: {method}"),
            },
        }
    }

    pub fn internal(id: u64, msg: impl std::fmt::Display) -> Self {
        Self {
            jsonrpc: "2.0",
            id,
            error: ErrorPayload {
                code: -32000,
                message: msg.to_string(),
            },
        }
    }
}

// ---------------------------------------------------------------------------
// ANNO manifest types
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnnoManifest {
    pub languages: Vec<LanguagePolicy>,
    pub tool_owners: HashMap<String, ToolOwner>,
    pub detected_markers: Vec<DetectedMarker>,
    pub warnings: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LanguagePolicy {
    pub language: String,
    pub tool: ToolOwner,
    pub shim_priority: u8,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ToolOwner {
    Uv,
    Rv,
    Goup,
    Mise,
    Bun,
    Rustup,
    System,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DetectedMarker {
    pub path: String,
    pub kind: MarkerKind,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MarkerKind {
    PythonPyproject,
    PythonRequirements,
    RubyVersion,
    RubyGemfile,
    CargoToml,
    PackageJson,
    GoMod,
    MiseToml,
    AnnoManifest,
    SolanaAnchorToml,
}

impl AnnoManifest {
    pub fn has_language(&self, lang: &str) -> bool {
        self.languages.iter().any(|p| p.language == lang)
    }

    pub fn needs_mise(&self) -> bool {
        self.languages
            .iter()
            .any(|p| matches!(p.tool, ToolOwner::Mise))
    }
}

// ---------------------------------------------------------------------------
// Environment provisioning types
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct EnvReport {
    pub path_mutations: Vec<PathSegment>,
    pub vulkan_status: String,
    pub warnings: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PathSegment {
    pub path: String,
    pub owner: String,
    pub priority: u8,
}

// ---------------------------------------------------------------------------
// Reactor types
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SedimentRequest {
    #[serde(default = "default_max_layers")]
    pub max_layers: u32,
    #[serde(default = "default_max_files")]
    pub max_files: u32,
    #[serde(default = "default_chunk_size")]
    pub chunk_size: u32,
}

impl Default for SedimentRequest {
    fn default() -> Self {
        Self {
            max_layers: default_max_layers(),
            max_files: default_max_files(),
            chunk_size: default_chunk_size(),
        }
    }
}

fn default_max_layers() -> u32 {
    10
}
fn default_max_files() -> u32 {
    500
}
fn default_chunk_size() -> u32 {
    220
}

#[derive(Debug, Clone, Serialize)]
pub struct SedimentResult {
    pub vertices: Vec<SedimentVertex>,
    pub layer_count: u32,
    pub file_count: u32,
    pub compute_time_ms: u64,
    pub backend: &'static str,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub telemetry: Option<FiredancerTelemetry>,
}

#[derive(Debug, Clone, Serialize)]
pub struct FiredancerTelemetry {
    pub slot: u64,
    pub shred_count: u32,
    pub packet_count: u32,
    pub shred_version: u16,
    pub leader_distance: u16,
    pub simulated_tps: u32,
    pub surge: bool,
}

#[derive(Debug, Clone, Copy, Serialize)]
pub struct SedimentVertex {
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub radius: f32,
    pub r: f32,
    pub g: f32,
    pub b: f32,
    pub alpha: f32,
}
