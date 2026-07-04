use anyhow::{Context, Result};
use rmcp::{
    handler::server::wrapper::Parameters,
    model::{ServerCapabilities, ServerInfo},
    schemars, tool, tool_handler, tool_router, ServerHandler, ServiceExt,
    transport::stdio,
};
use serde::{Deserialize, Serialize};
use std::{collections::HashMap, sync::{Arc, LazyLock}};
use tracing::{info, warn};
use tracing_subscriber::EnvFilter;

/// The official repository location of the massive Vulkan Valid Usage JSON database.
const VALID_USAGE_URL: &str = "https://raw.githubusercontent.com/KhronosGroup/Vulkan-Headers/main/registry/validusage.json";

// ---------------------------------------------------------------------------
// Static regex compilation — compiled once at process start, not per invocation
// ---------------------------------------------------------------------------

/// Matches bare VUID at line-start or after a pipe, and bracketed [ VUID-... ] format.
static VUID_RE: LazyLock<regex::Regex> = LazyLock::new(|| {
    regex::Regex::new(r"(?:^|\|\s*|\[\s*)(VUID-[a-zA-Z0-9-]+)").unwrap()
});

/// Matches `Object N: VkFoo` (Vk-class style) and `type = VK_OBJECT_TYPE_FOO` (enum style).
static OBJ_TYPE_RE: LazyLock<regex::Regex> = LazyLock::new(|| {
    regex::Regex::new(r"(?:Object\s+\d+:\s*(Vk[A-Za-z]+)|type\s*=\s*(VK_OBJECT_TYPE_[A-Z_]+))").unwrap()
});

/// Matches `handle 0x...` (space) and `handle = 0x...` (equals) variants.
static HANDLE_RE: LazyLock<regex::Regex> = LazyLock::new(|| {
    regex::Regex::new(r"handle[\s=]+(0x[0-9a-fA-F]+)").unwrap()
});

// ---------------------------------------------------------------------------
// Object-type normalisation
// ---------------------------------------------------------------------------

/// Converts a Vk-class-style object name to the VK_OBJECT_TYPE_* enum format so
/// that `vulkan_audit_logs` output always matches `vulkan_suggest_remediation` match arms.
///
/// Examples:
///   `VkDescriptorSet`  → `VK_OBJECT_TYPE_DESCRIPTOR_SET`
///   `VkSwapchainKHR`   → `VK_OBJECT_TYPE_SWAPCHAIN_KHR`
///   `VkCommandBuffer`  → `VK_OBJECT_TYPE_COMMAND_BUFFER`
///   `VK_OBJECT_TYPE_*` → returned unchanged (already normalised)
fn vk_class_to_enum(name: &str) -> String {
    if name.starts_with("VK_OBJECT_TYPE_") {
        return name.to_string();
    }
    let stripped = name.strip_prefix("Vk").unwrap_or(name);
    let chars: Vec<char> = stripped.chars().collect();
    let mut result = String::with_capacity(stripped.len() + 20);
    result.push_str("VK_OBJECT_TYPE_");
    for (i, &c) in chars.iter().enumerate() {
        if i > 0 && c.is_uppercase() {
            let prev_lower = chars[i - 1].is_lowercase();
            let next_lower = chars.get(i + 1).map_or(false, |nc| nc.is_lowercase());
            // Insert underscore before an uppercase letter when:
            //   a) it follows a lowercase letter (e.g. t|B in CommandBuffer), OR
            //   b) it follows another uppercase and is itself followed by lowercase
            //      (e.g. K|H|R in KHR should NOT split, but C|Md would split)
            if prev_lower || (chars[i - 1].is_uppercase() && next_lower) {
                result.push('_');
            }
        }
        result.push(c.to_ascii_uppercase());
    }
    result
}

#[derive(Clone)]
pub struct VulkanDiagnosticsServer {
    /// Thread-safe, in-memory cache mapping isolated VUID strings to their normative specification text.
    /// Encapsulated in an Arc to allow concurrent reads across multiple JSON-RPC worker tasks.
    vuid_database: Arc<HashMap<String, String>>,
}

#[derive(Debug, Deserialize, Serialize, schemars::JsonSchema)]
pub struct AuditLogParams {
    #[schemars(description = "Raw, verbose validation layer log text captured from standard output or a log file.")]
    pub log_content: String,
}

#[derive(Debug, Deserialize, Serialize, schemars::JsonSchema)]
pub struct ResolveVuidParams {
    #[schemars(description = "The specific Valid Usage ID to look up in the Khronos registry, e.g., 'VUID-vkCmdDraw-None-08114'.")]
    pub vuid: String,
}

#[derive(Debug, Deserialize, Serialize, schemars::JsonSchema)]
pub struct RemediationParams {
    #[schemars(description = "The target Valid Usage ID.")]
    pub vuid: String,
    #[schemars(description = "The primary Vulkan object type involved in the crash, e.g., 'VK_OBJECT_TYPE_PIPELINE'.")]
    pub obj_type: String,
}

#[derive(Debug, Serialize)]
pub struct ParsedViolation {
    pub vuid: String,
    pub object_types: Vec<String>,
    pub handles: Vec<String>,
    pub occurrence_count: usize,
}

impl VulkanDiagnosticsServer {
    /// Asynchronously downloads and parses the 14.5MB validusage.json file into a flattened HashMap.
    /// Incorporates a local disk cache to prevent cold-start hard crashes on network failure.
    /// This must be executed prior to binding the stdio transport.
    pub async fn initialize() -> Result<Self> {
        let cache_dir = std::path::PathBuf::from(std::env::var("USERPROFILE").unwrap_or_else(|_| ".".into())).join(".chthonic");
        let _ = std::fs::create_dir_all(&cache_dir);
        let cache_file = cache_dir.join("validusage.json");

        info!("Initiating download of validusage.json from Khronos registry...");
        let client = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(15))
            .build()
            .context("Failed to build HTTP client")?;

        let json_text = match client.get(VALID_USAGE_URL).send().await {
            Ok(response) if response.status().is_success() => {
                let text = response.text().await.context("Failure: Could not decode response body to text")?;
                if let Err(e) = std::fs::write(&cache_file, &text) {
                    warn!("Failed to write validusage.json to local cache: {}", e);
                } else {
                    info!("Successfully cached validusage.json to disk.");
                }
                text
            }
            Ok(response) => {
                warn!("Khronos registry returned HTTP {}. Falling back to local cache.", response.status());
                std::fs::read_to_string(&cache_file).context("Network fetch failed (bad status) and local cache is unavailable")?
            }
            Err(e) => {
                warn!("Network failure ({}). Falling back to local cache.", e);
                std::fs::read_to_string(&cache_file).context("Network fetch failed and local cache is unavailable")?
            }
        };

        info!("Parsing validusage.json (Payload size: {} bytes)...", json_text.len());

        // The Khronos JSON schema is structured hierarchically. We must flatten it into a simple K/V store.
        // Structure: { "version info": ..., "validation": { "API_NAME": [ { "vuid": "...", "text": "..." } ] } }
        let root: serde_json::Value = serde_json::from_str(&json_text)
            .context("JSON Deserialization failure: Malformed validusage.json")?;

        let mut database = HashMap::new();

        if let Some(validation_block) = root.get("validation").and_then(|v| v.as_object()) {
            for (_api_construct, statements) in validation_block {
                // direct-array format
                if let Some(array) = statements.as_array() {
                    for entry in array {
                        if let (Some(vuid), Some(text)) = (entry.get("vuid"), entry.get("text")) {
                            if let (Some(vuid_str), Some(text_str)) = (vuid.as_str(), text.as_str()) {
                                database.insert(vuid_str.to_string(), text_str.to_string());
                            }
                        }
                    }
                // nested-object format (actual Khronos schema)
                } else if let Some(inner) = statements.as_object() {
                    for (_, sub) in inner {
                        if let Some(array) = sub.as_array() {
                            for entry in array {
                                if let (Some(vuid), Some(text)) = (entry.get("vuid"), entry.get("text")) {
                                    if let (Some(vuid_str), Some(text_str)) = (vuid.as_str(), text.as_str()) {
                                        database.insert(vuid_str.to_string(), text_str.to_string());
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        info!("Initialization Complete: Successfully flattened {} VUID entries into memory cache.", database.len());

        Ok(Self {
            vuid_database: Arc::new(database),
        })
    }
}

#[tool_router]
impl VulkanDiagnosticsServer {
    /// Ingests raw console residue, applies extraction regexes, and returns a deduplicated violation map.
    #[tool(description = "Parses raw, highly verbose Vulkan validation logs, deduplicates repeating VUIDs, and extracts involved objects and memory handles into a structured summary.")]
    async fn vulkan_audit_logs(
        &self,
        Parameters(params): Parameters<AuditLogParams>,
    ) -> Result<String, rmcp::ErrorData> {
        info!("Executing vulkan_audit_logs analysis over provided telemetry.");

        // Use pre-compiled statics — no recompilation overhead per invocation.
        let mut violations_map: HashMap<String, ParsedViolation> = HashMap::new();

        // Process the telemetry stream line by line
        for line in params.log_content.lines() {
            if let Some(vuid_match) = VUID_RE.captures(line) {
                let vuid = vuid_match[1].to_string();

                // Normalise all object type names to VK_OBJECT_TYPE_* enum format so the
                // output is directly usable by vulkan_suggest_remediation's match arms.
                let obj_types: Vec<String> = OBJ_TYPE_RE.captures_iter(line)
                    .filter_map(|caps| caps.get(1).or_else(|| caps.get(2)))
                    .map(|m| vk_class_to_enum(m.as_str()))
                    .collect();

                let handles: Vec<String> = HANDLE_RE.captures_iter(line)
                    .map(|caps| caps[1].to_string())
                    .collect();

                // Deduplication and aggregation logic
                let entry = violations_map.entry(vuid.clone()).or_insert(ParsedViolation {
                    vuid,
                    object_types: Vec::new(),
                    handles: Vec::new(),
                    occurrence_count: 0,
                });

                entry.occurrence_count += 1;

                for t in obj_types {
                    if !entry.object_types.contains(&t) { entry.object_types.push(t); }
                }
                for h in handles {
                    if !entry.handles.contains(&h) { entry.handles.push(h); }
                }
            }
        }

        // Sort violations by severity (frequency of occurrence)
        let mut results: Vec<&ParsedViolation> = violations_map.values().collect();
        results.sort_by(|a, b| b.occurrence_count.cmp(&a.occurrence_count));

        serde_json::to_string_pretty(&results)
            .map_err(|e| rmcp::ErrorData::internal_error(format!("Serialization failure: {}", e), None))
    }

    /// Provides zero-latency lookup of normative specification constraints.
    #[tool(description = "Takes a specific VUID and fetches the exact, normative specification text from the offline Khronos registry cache.")]
    async fn vulkan_resolve_vuid(
        &self,
        Parameters(params): Parameters<ResolveVuidParams>,
    ) -> Result<String, rmcp::ErrorData> {
        info!("Resolving VUID constraint: {}", params.vuid);

        // Exact match — the fast path for well-formed VUID strings from validation layer output.
        if let Some(text) = self.vuid_database.get(&params.vuid) {
            return Ok(format!("Vulkan Specification for {}:\n\n{}", params.vuid, text));
        }

        // Partial match fallback: the query may be a fragment (function name, suffix number,
        // or misremembered VUID). Search all keys for substring matches and surface suggestions.
        warn!("Exact VUID '{}' not found — attempting partial match.", params.vuid);
        let needle = params.vuid.to_lowercase();
        let mut matches: Vec<(&String, &String)> = self.vuid_database
            .iter()
            .filter(|(k, _)| k.to_lowercase().contains(&needle))
            .collect();

        if matches.is_empty() {
            return Err(rmcp::ErrorData::invalid_params(
                format!(
                    "VUID '{}' not found (exact or partial). Paste the VUID verbatim from \
                     validation layer stderr — it appears as 'MessageID = 0x...' followed by \
                     '[ VUID-... ]' in the log line.",
                    params.vuid
                ),
                None,
            ));
        }

        // Prefer shortest key (closest match), surface at most 5 candidates.
        matches.sort_by_key(|(k, _)| k.len());
        matches.truncate(5);

        // Single unambiguous partial match: resolve it directly.
        if matches.len() == 1 {
            let (vuid, text) = matches[0];
            return Ok(format!(
                "Vulkan Specification for {} (partial match for '{}'):\n\n{}",
                vuid, params.vuid, text
            ));
        }

        // Multiple candidates: return the list so the agent can pick the right one.
        let suggestions = matches
            .iter()
            .map(|(k, _)| format!("  {k}"))
            .collect::<Vec<_>>()
            .join("\n");
        Err(rmcp::ErrorData::invalid_params(
            format!(
                "VUID '{}' not found. Partial matches:\n{}\nCall vulkan_resolve_vuid again with the exact VUID.",
                params.vuid, suggestions
            ),
            None,
        ))
    }

    /// A heuristic engine simulating high-level architectural advice based on object types.
    #[tool(description = "Cross-references a VUID and Object Type with common Rust/Ash/Vulkano implementation pitfalls to suggest the exact architectural fix required.")]
    async fn vulkan_suggest_remediation(
        &self,
        Parameters(params): Parameters<RemediationParams>,
    ) -> Result<String, rmcp::ErrorData> {
        info!("Generating heuristic remediation for {} targeting {}", params.vuid, params.obj_type);

        // This match statement serves as the foundation for an expert-systems diagnostic heuristic.
        let suggestion = match params.obj_type.as_str() {
            "VK_OBJECT_TYPE_PIPELINE" => "Ensure layout transitions match pipeline barrier execution dependencies. In Ash, verify `vk::PipelineLayoutCreateInfo` memory lifetimes, as dropping the layout before the pipeline compiles results in undefined memory access.",
            "VK_OBJECT_TYPE_SWAPCHAIN_KHR" => "Verify that `vkAcquireNextImageKHR` synchronization primitives (Semaphores/Fences) are not currently signaled or in use by another queue operation. Ensure the image index matches the frame-in-flight index.",
            "VK_OBJECT_TYPE_COMMAND_BUFFER" => "Command buffer recording state violated. Ensure `begin_command_buffer` is called before recording, check command pool reset flags, and ensure the buffer is not simultaneously executing on a queue.",
            "VK_OBJECT_TYPE_DESCRIPTOR_SET" => "Descriptor layout mismatch or missing binding. Verify that the shader expects the exact uniform/storage buffer alignment provided in the Rust struct (`#[repr(C)]` or `#[repr(transparent)]` required).",
            _ => "Review the normative specification text returned by `vulkan_resolve_vuid`. Verify memory alignments, explicit layout transitions, and ensure standard Rust lifetime drops are not destroying Vulkan handles prematurely.",
        };

        Ok(format!("Diagnostic Remediation Suggestion:\n{}", suggestion))
    }
}

// Wire the tool router into the core MCP ServerHandler implementation
#[tool_handler(name = "vulkan-diagnostics", version = "1.4.0", instructions = "Resolve Vulkan VUIDs against the Khronos specification and parse verbose validation layers into structured data.")]
impl ServerHandler for VulkanDiagnosticsServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo::new(ServerCapabilities::builder().enable_tools().build())
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Critical Standard I/O Requirement:
    // Stdout is exclusively reserved for the MCP JSON-RPC protocol.
    // We strictly configure tracing to output to stderr to ensure protocol stability.
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env().add_directive(tracing::Level::INFO.into()))
        .with_writer(std::io::stderr)
        .init();

    info!("Initializing Vulkan Diagnostics Server state. Preparing to ingest 14.5MB specification registry...");

    // Block standard operation until the heavy data payload is fully cached into memory
    let server = VulkanDiagnosticsServer::initialize().await
        .context("Critical Initialization Failure: Could not build VUID database")?;

    info!("Database initialized. Starting Vulkan Diagnostics MCP Server over stdio transport layer.");

    // Bind to the underlying OS standard input/output streams
    let service = server.serve(stdio()).await.context("Failed to initialize standard I/O transport")?;

    // Await protocol termination or OS SIGTERM
    service.waiting().await?;
    info!("Client session terminated. Gracefully shutting down Vulkan Diagnostics MCP Server.");

    Ok(())
}
