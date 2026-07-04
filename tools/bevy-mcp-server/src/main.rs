use anyhow::{Context, Result};
use reqwest::Client;
use rmcp::{
    handler::server::wrapper::Parameters,
    model::{ServerCapabilities, ServerInfo},
    schemars, tool, tool_handler, tool_router, ServerHandler, ServiceExt,
    transport::stdio,
};
use serde::{Deserialize, Serialize};
use tracing::{error, info, warn};
use tracing_subscriber::EnvFilter;

/// The base URL for the Bevy website's raw Markdown repository.
const GITHUB_RAW_BASE: &str = "https://raw.githubusercontent.com/bevyengine/bevy-website/main";
/// docs.rs base URL for Bevy 0.19.0 rustdoc pages.
const DOCS_RS_BASE: &str = "https://docs.rs/bevy/0.19.0/bevy";

/// Maps a normalised query string to a docs.rs module path fragment (no .html suffix).
fn resolve_type_path(query: &str) -> Option<&'static str> {
    let key: String = query.chars()
        .filter(|c| c.is_alphanumeric())
        .flat_map(|c| c.to_lowercase())
        .collect();
    match key.as_str() {
        "commands"        => Some("ecs/system/struct.Commands"),
        "query"           => Some("ecs/system/struct.Query"),
        "resmut"          => Some("ecs/system/struct.ResMut"),
        "res"             => Some("ecs/system/struct.Res"),
        "world"           => Some("ecs/world/struct.World"),
        "entity"          => Some("ecs/entity/struct.Entity"),
        "component"       => Some("ecs/component/trait.Component"),
        "bundle"          => Some("ecs/bundle/trait.Bundle"),
        "plugin"          => Some("app/trait.Plugin"),
        "app"             => Some("app/struct.App"),
        "schedule"        => Some("ecs/schedule/struct.Schedule"),
        "systemset"       => Some("ecs/schedule/trait.SystemSet"),
        "update"          => Some("app/struct.Update"),
        "startup"         => Some("app/struct.Startup"),
        "fixedupdate"     => Some("app/struct.FixedUpdate"),
        "assets"          => Some("asset/struct.Assets"),
        "assetserver"     => Some("asset/struct.AssetServer"),
        "asset"           => Some("asset/trait.Asset"),
        "handle"          => Some("asset/struct.Handle"),
        "transform"       => Some("transform/components/struct.Transform"),
        "globaltransform" => Some("transform/components/struct.GlobalTransform"),
        "time"            => Some("time/struct.Time"),
        "timer"           => Some("time/struct.Timer"),
        "eventwriter"     => Some("ecs/event/struct.EventWriter"),
        "eventreader"     => Some("ecs/event/struct.EventReader"),
        "event"           => Some("ecs/event/trait.Event"),
        "with"            => Some("ecs/query/struct.With"),
        "without"         => Some("ecs/query/struct.Without"),
        "changed"         => Some("ecs/query/struct.Changed"),
        "added"           => Some("ecs/query/struct.Added"),
        "local"           => Some("ecs/system/struct.Local"),
        "systemstate"     => Some("ecs/system/struct.SystemState"),
        "parent"          => Some("hierarchy/components/struct.Parent"),
        "children"        => Some("hierarchy/components/struct.Children"),
        "visibility"      => Some("render/view/visibility/struct.Visibility"),
        "camera"          => Some("render/camera/struct.Camera"),
        _                 => None,
    }
}

/// Strips HTML tags and decodes common entities from a raw HTML fragment.
fn strip_html_tags(html: &str) -> String {
    let mut result = String::with_capacity(html.len());
    let mut in_tag = false;
    for c in html.chars() {
        match c {
            '<' => in_tag = true,
            '>' => in_tag = false,
            _ if !in_tag => result.push(c),
            _ => {}
        }
    }
    result
        .replace("&lt;", "<").replace("&gt;", ">")
        .replace("&amp;", "&").replace("&quot;", "\"")
        .replace("&#39;", "'").replace("&apos;", "'")
        .replace("&nbsp;", " ").replace("&#x27;", "'")
}

/// Extracts the item declaration and first docblock paragraph from a docs.rs HTML page.
fn extract_rustdoc_summary(html: &str) -> String {
    let mut parts: Vec<String> = Vec::new();

    // Item declaration: <pre class="rust item-decl"><code ...>SIGNATURE</code></pre>
    if let Some(start) = html.find("item-decl\">") {
        let after = &html[start + "item-decl\">".len()..];
        if let Some(end) = after.find("</pre>") {
            let cleaned = strip_html_tags(&after[..end]);
            let trimmed = cleaned.trim();
            if !trimmed.is_empty() {
                parts.push(format!("```rust\n{trimmed}\n```"));
            }
        }
    }

    // First docblock paragraph
    if let Some(db_start) = html.find("class=\"docblock\"") {
        let after = &html[db_start..];
        if let Some(p_start) = after.find("<p>") {
            let content = &after[p_start + 3..];
            if let Some(p_end) = content.find("</p>") {
                let cleaned = strip_html_tags(&content[..p_end]);
                let trimmed = cleaned.trim();
                if !trimmed.is_empty() {
                    parts.push(trimmed.to_string());
                }
            }
        }
    }

    if parts.is_empty() {
        "No declaration extracted — use bevy_read_section for conceptual docs.".to_string()
    } else {
        parts.join("\n\n")
    }
}

#[derive(Clone)]
pub struct BevyKnowledgeServer {
    http_client: Client,
}

#[derive(Debug, Deserialize, Serialize, schemars::JsonSchema)]
pub struct ReadSectionParams {
    #[schemars(description = "The specific section path to read from the Bevy Book, e.g., 'getting-started/ecs.md'")]
    pub section_path: String,
}

#[derive(Debug, Deserialize, Serialize, schemars::JsonSchema)]
pub struct ApiSearchParams {
    #[schemars(description = "The Bevy type, trait, or function to search for, e.g., 'Commands', 'Query', 'ResMut'")]
    pub query: String,
}

#[tool_router]
impl BevyKnowledgeServer {
    pub fn new() -> Self {
        Self {
            http_client: Client::builder()
                .user_agent("chthonic-agy/bevy-mcp-server/0.19.0")
                .timeout(std::time::Duration::from_secs(10))
                .build()
                .expect("Failed to construct resilient HTTP client"),
        }
    }

    /// Exposes the Bevy Book table of contents to the AI agent.
    #[tool(description = "Retrieves the table of contents (valid markdown paths) from the Bevy Book (0.19.0)")]
    async fn bevy_book_index(&self) -> Result<String, rmcp::ErrorData> {
        info!("Executing bevy_book_index tool request");
        // We use the GitHub Git Trees API to fetch the actual directory structure since Zola _index.md files
        // only contain frontmatter and no book TOC.
        let url = "https://api.github.com/repos/bevyengine/bevy-website/git/trees/main?recursive=1";
        match self.http_client.get(url).send().await {
            Ok(response) if response.status().is_success() => {
                let json_data: serde_json::Value = response.json().await.map_err(|e| rmcp::ErrorData::internal_error(e.to_string(), None))?;
                let mut paths = Vec::new();
                if let Some(tree) = json_data.get("tree").and_then(|t| t.as_array()) {
                    for item in tree {
                        if let (Some(path), Some(type_str)) = (item.get("path").and_then(|p| p.as_str()), item.get("type").and_then(|t| t.as_str())) {
                            if type_str == "blob" && path.starts_with("content/learn/") && path.ends_with(".md") && !path.ends_with("_index.md") {
                                paths.push(path.to_string());
                            }
                        }
                    }
                }
                if paths.is_empty() {
                    Ok("Bevy Book Index: No valid markdown paths found. (Rate limit or structure change)".to_string())
                } else {
                    Ok(format!("Bevy Book Index (Available Paths):\n{}", paths.join("\n")))
                }
            }
            Ok(response) => {
                let status = response.status();
                warn!("GitHub API returned non-success status: {}", status);
                Err(rmcp::ErrorData::internal_error(format!("Failed to fetch Bevy Book index. Status: {}", status), None))
            }
            Err(e) => {
                error!("Network failure during Bevy Book index retrieval: {}", e);
                Err(rmcp::ErrorData::internal_error(format!("Network failure: {}", e), None))
            }
        }
    }

    /// Allows the AI agent to dive deeply into a specific Bevy architectural concept.
    #[tool(description = "Fetches the full markdown/text content of a specific Bevy Book section. Use paths returned by bevy_book_index (e.g. 'content/learn/quick-start/getting-started/ecs.md').")]
    async fn bevy_read_section(
        &self,
        Parameters(params): Parameters<ReadSectionParams>,
    ) -> Result<String, rmcp::ErrorData> {
        info!("Executing bevy_read_section for target path: {}", params.section_path);

        // Sanitize the input path to prevent URL malformation
        let mut clean_path = params.section_path.trim_start_matches('/').to_string();
        if !clean_path.ends_with(".md") {
            clean_path.push_str(".md");
        }
        
        let url = format!("{}/{}", GITHUB_RAW_BASE, clean_path);

        let response = self.http_client.get(&url).send().await
            .map_err(|e| rmcp::ErrorData::internal_error(e.to_string(), None))?;

        if response.status().is_success() {
            let content = response.text().await
                .map_err(|e| rmcp::ErrorData::internal_error(e.to_string(), None))?;
            Ok(content)
        } else {
            warn!("Agent requested non-existent Bevy Book section: {}", clean_path);
            Err(rmcp::ErrorData::invalid_params(format!("Section not found at path: {}", clean_path), None))
        }
    }

    /// Fetches Bevy 0.19.0 type signatures and doc summaries from docs.rs.
    #[tool(description = "Queries the Bevy 0.19.0 rustdocs for specific types, functions, or traits to retrieve precise signatures and docstrings")]
    async fn bevy_api_search(
        &self,
        Parameters(params): Parameters<ApiSearchParams>,
    ) -> Result<String, rmcp::ErrorData> {
        info!("bevy_api_search: resolving '{}'", params.query);

        let query = params.query.trim();

        // Resolve to a docs.rs module path: accept an explicit path (contains '/') or look up
        // by type name in the static table.
        let module_path = if query.contains('/') {
            query.trim_end_matches(".html").to_string()
        } else {
            match resolve_type_path(query) {
                Some(p) => p.to_string(),
                None => {
                    return Err(rmcp::ErrorData::invalid_params(
                        format!(
                            "Type '{}' not in lookup table. Known types: Commands, Query, ResMut, Res, \
                             World, Entity, Component, Bundle, Plugin, App, Schedule, Time, Transform, \
                             EventWriter, EventReader, Assets, AssetServer, Local, With, Without, Changed, \
                             Added, Parent, Children, Camera, Visibility. \
                             Or supply an explicit module path like 'ecs/system/struct.Commands'.",
                            query
                        ),
                        None,
                    ));
                }
            }
        };

        let url = format!("{}/{}.html", DOCS_RS_BASE, module_path);
        info!("Fetching docs.rs page: {}", url);

        match self.http_client.get(&url).send().await {
            Ok(resp) if resp.status().is_success() => {
                let html = resp.text().await
                    .map_err(|e| rmcp::ErrorData::internal_error(e.to_string(), None))?;
                let summary = extract_rustdoc_summary(&html);
                Ok(format!("Bevy 0.19.0 — {}\nURL: {}\n\n{}", module_path, url, summary))
            }
            Ok(resp) => {
                warn!("docs.rs returned {} for '{}'", resp.status(), module_path);
                Err(rmcp::ErrorData::invalid_params(
                    format!("docs.rs returned {} for '{}'. The module path may be wrong.", resp.status(), module_path),
                    None,
                ))
            }
            Err(e) => {
                error!("Network failure fetching {}: {}", url, e);
                Err(rmcp::ErrorData::internal_error(format!("Network failure: {}", e), None))
            }
        }
    }
}

// Wire the tool router into the MCP ServerHandler trait
#[tool_handler(name = "bevy-knowledge", version = "0.19.0", instructions = "Query Bevy 0.19.0 documentation and Rust API signatures to prevent framework hallucination.")]
impl ServerHandler for BevyKnowledgeServer {
    fn get_info(&self) -> ServerInfo {
        ServerInfo::new(ServerCapabilities::builder().enable_tools().build())
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Critical Standard I/O Requirement:
    // The MCP stdio transport requires standard output to be strictly reserved for JSON-RPC messages.
    // Any logging to stdout will corrupt the stream and cause the client to disconnect.
    // Therefore, all tracing MUST be routed to stderr.
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env().add_directive(tracing::Level::INFO.into()))
        .with_writer(std::io::stderr)
        .init();

    info!("Starting Bevy Knowledge MCP Server over stdio transport layer.");

    let server = BevyKnowledgeServer::new();

    // Bind the server to the stdio transport mechanism provided by rmcp
    let service = server.serve(stdio()).await.context("Failed to initialize standard I/O transport")?;

    // Maintain process execution until client disconnection or SIGTERM
    service.waiting().await?;
    info!("Client disconnected. Gracefully shutting down Bevy Knowledge MCP Server.");

    Ok(())
}
