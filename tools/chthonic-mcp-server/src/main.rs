// @SID: TOOL_CHTHONIC_MCP_SERVER_V1
// ============================================================
// chthonic-mcp-server — stdio MCP server (rmcp 1.x)
//

// Modern Rust port of the bun `chthonic-v3` server
// (scripts/mcp-chthonic-server.ts). The old server hand-rolled the
// JSON-RPC envelope on the 2024-11-05 protocol and exposed ~30 tools,
// of which ~half were polyglot runners (cargo/uv/gcc/git/bash/...)
// already covered by Claude Code's native Bash tool and the `git` MCP
// server. This port keeps only the unique value — the chthonic.ps1
// domain/action router — and exposes it intuitively:
//

//   chthonic            generic runner: <domain> [action] [args] [-Json]
//   chthonic_commands   discover the live domain/action surface
//   chthonic_status     tool + manager version snapshot
//   chthonic_doctor     versions + origins + EOL health
//   chthonic_ssot       SSOT loremaster control plane
//   chthonic_toolchain  verified toolchain control plane
//

// Everything chthonic.ps1 can do remains reachable through `chthonic`;
// the named tools are convenience shortcuts for the high-value lanes.
//
// Transport: stdio (rmcp). Tool calls shell into chthonic.ps1 via a
// captured subprocess (no stdout pollution; tracing -> stderr).
// Repo root: CHTHONIC_ROOT env (set by .mcp.json) -> cwd fallback.
// ============================================================

use std::path::PathBuf;
use std::process::Stdio;

use rmcp::handler::server::router::tool::ToolRouter;
use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::{CallToolResult, ContentBlock, ServerCapabilities, ServerInfo};
use rmcp::{tool, tool_handler, tool_router, ErrorData, ServerHandler, ServiceExt};
use schemars::JsonSchema;
use serde::Deserialize;
use tokio::process::Command;
use tracing::{info, warn};

// ── Tool parameter types ────────────────────────────────────────────────────────

#[derive(Debug, Deserialize, JsonSchema)]
struct ChthonicParams {
    /// chthonic domain, e.g. doctor | status | ssot | toolchain | book | new |
    /// graphics | memory | ide | mcp | trend | workflow | rust | python | ruby.
    /// Run chthonic_commands to list the full live surface.
    domain: String,
    /// Optional action within the domain (e.g. for ssot: drift|lineage; for new: cargo-rust-bin).
    action: Option<String>,
    /// Additional positional arguments passed after the domain/action.
    args: Option<Vec<String>>,
    /// Request JSON output where the domain supports it (passes -Json).
    json: Option<bool>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct SsotParams {
    /// SSOT action: queue | entity | section | drift | lineage
    action: String,
    /// Additional positional arguments for the action.
    args: Option<Vec<String>>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct ToolchainParams {
    /// toolchain action: hierarchy | verify | scan | paths
    action: String,
    /// Additional positional arguments for the action.
    args: Option<Vec<String>>,
}

// ── Server ──────────────────────────────────────────────────────────────────────

#[derive(Clone)]
struct ChthonicServer {
    repo_root: PathBuf,
    script: PathBuf,
    pwsh: String,
    // Routed through by the #[tool_handler] macro-generated code; the dead-code
    // lint can't see that use, so silence it (known rmcp pattern).
    #[allow(dead_code)]
    tool_router: ToolRouter<ChthonicServer>,
}

impl ChthonicServer {
    fn new() -> Self {
        let repo_root = std::env::var("CHTHONIC_ROOT")
            .map(PathBuf::from)
            .ok()
            .filter(|p| p.join("scripts").join("chthonic.ps1").exists())
            .or_else(|| std::env::current_dir().ok())
            .unwrap_or_else(|| PathBuf::from("."));
        let script = repo_root.join("scripts").join("chthonic.ps1");
        Self {
            repo_root,
            script,
            pwsh: resolve_pwsh(),
            tool_router: Self::tool_router(),
        }
    }

    /// Run chthonic.ps1 with the given positional args, capturing output.
    /// Args are passed as discrete process arguments via -File (no shell
    /// interpolation / no manual escaping — a modernization over the old
    /// -Command string the bun server built).
    async fn run(&self, args: &[String]) -> Result<CallToolResult, ErrorData> {
        if !self.script.exists() {
            return Err(ErrorData::internal_error(
                format!(
                    "chthonic.ps1 not found at {}. Set CHTHONIC_ROOT or run from the repo root.",
                    self.script.display()
                ),
                None,
            ));
        }

        let mut cmd = Command::new(&self.pwsh);
        cmd.arg("-NoProfile")
            .arg("-NoLogo")
            .arg("-File")
            .arg(&self.script);
        for a in args {
            cmd.arg(a);
        }
        cmd.current_dir(&self.repo_root)
            .env("NO_COLOR", "1")
            .env("FORCE_COLOR", "0")
            .stdin(Stdio::null());

        let output = cmd.output().await.map_err(|e| {
            ErrorData::internal_error(format!("failed to spawn {}: {e}", self.pwsh), None)
        })?;

        let stdout = String::from_utf8_lossy(&output.stdout);
        let stderr = String::from_utf8_lossy(&output.stderr);
        let code = output.status.code().unwrap_or(-1);

        let mut text = stdout.trim_end().to_string();
        if !stderr.trim().is_empty() {
            if !text.is_empty() {
                text.push('\n');
            }
            text.push_str(&format!("[stderr]\n{}", stderr.trim()));
        }
        if text.is_empty() {
            text.push_str("(no output)");
        }
        text.push_str(&format!("\n[exit {code}]"));

        if output.status.success() {
            Ok(CallToolResult::success(vec![ContentBlock::text(text)]))
        } else {
            Ok(CallToolResult::error(vec![ContentBlock::text(text)]))
        }
    }
}

#[tool_router]
impl ChthonicServer {
    #[tool(
        description = "Run any chthonic.ps1 domain/action. domain examples: doctor|status|ssot|toolchain|book|new|graphics|memory|ide|mcp|trend|workflow|rust|python|ruby|go|zig|r. Use chthonic_commands to discover the full surface. Returns captured stdout/stderr + exit code."
    )]
    async fn chthonic(
        &self,
        Parameters(p): Parameters<ChthonicParams>,
    ) -> Result<CallToolResult, ErrorData> {
        let mut a = vec![p.domain];
        if let Some(action) = p.action {
            if !action.is_empty() {
                a.push(action);
            }
        }
        if let Some(extra) = p.args {
            a.extend(extra.into_iter().filter(|s| !s.is_empty()));
        }
        if p.json.unwrap_or(false) {
            a.push("-Json".to_string());
        }
        self.run(&a).await
    }

    #[tool(description = "List the live chthonic command surface (all domains + their actions).")]
    async fn chthonic_commands(&self) -> Result<CallToolResult, ErrorData> {
        self.run(&["commands".to_string(), "guide".to_string()]).await
    }

    #[tool(description = "Tool + manager version snapshot (chthonic status).")]
    async fn chthonic_status(&self) -> Result<CallToolResult, ErrorData> {
        self.run(&["status".to_string()]).await
    }

    #[tool(description = "Versions + origins + EOL-state health check (chthonic doctor).")]
    async fn chthonic_doctor(&self) -> Result<CallToolResult, ErrorData> {
        self.run(&["doctor".to_string()]).await
    }

    #[tool(
        description = "SSOT loremaster control plane. action: queue | entity | section | drift | lineage."
    )]
    async fn chthonic_ssot(
        &self,
        Parameters(p): Parameters<SsotParams>,
    ) -> Result<CallToolResult, ErrorData> {
        let mut a = vec!["ssot".to_string(), p.action];
        if let Some(extra) = p.args {
            a.extend(extra.into_iter().filter(|s| !s.is_empty()));
        }
        self.run(&a).await
    }

    #[tool(
        description = "Verified toolchain control plane. action: hierarchy | verify | scan | paths."
    )]
    async fn chthonic_toolchain(
        &self,
        Parameters(p): Parameters<ToolchainParams>,
    ) -> Result<CallToolResult, ErrorData> {
        let mut a = vec!["toolchain".to_string(), p.action];
        if let Some(extra) = p.args {
            a.extend(extra.into_iter().filter(|s| !s.is_empty()));
        }
        self.run(&a).await
    }

    #[tool(description = "Vulkan Validation log structured parser. Analyzes target/render-smoke.log to cluster and structure Vulkan VUID errors, preventing context bloat from verbose console residue.")]
    async fn chthonic_vulkan_doctor(&self) -> Result<CallToolResult, ErrorData> {
        let log_path = self.repo_root.join("target").join("render-smoke.log");
        if !log_path.exists() {
            return Ok(CallToolResult::success(vec![ContentBlock::text("No render-smoke.log found. Run scripts/render-smoke.ps1 first.".to_string())]));
        }
        let content = tokio::fs::read_to_string(&log_path).await.map_err(|e| {
            ErrorData::internal_error(format!("Failed to read smoke log: {}", e), None)
        })?;

        let mut errors: std::collections::HashMap<String, usize> = std::collections::HashMap::new();
        let mut capturing_vuid = false;
        let mut current_err = String::new();

        for line in content.lines() {
            if line.contains("[VK:VALIDATION]") {
                if !current_err.is_empty() {
                    *errors.entry(current_err.clone()).or_insert(0) += 1;
                    current_err.clear();
                }
                current_err = line.split("[VK:VALIDATION]").nth(1).unwrap_or("").trim().to_string();
                capturing_vuid = true;
            } else if capturing_vuid && line.trim_start().starts_with("The Vulkan spec states:") {
                // capture the spec rule
                let rule = line.trim();
                current_err.push_str("\n  ");
                current_err.push_str(rule);
                *errors.entry(current_err.clone()).or_insert(0) += 1;
                current_err.clear();
                capturing_vuid = false;
            } else if capturing_vuid && (line.starts_with("[") || line.trim().is_empty()) {
                *errors.entry(current_err.clone()).or_insert(0) += 1;
                current_err.clear();
                capturing_vuid = false;
            }
        }
        if !current_err.is_empty() {
            *errors.entry(current_err).or_insert(0) += 1;
        }

        if errors.is_empty() {
            return Ok(CallToolResult::success(vec![ContentBlock::text("No Vulkan validation errors found in render-smoke.log. Clean!".to_string())]));
        }

        let mut output = format!("Found {} unique Vulkan validation error signatures:\n\n", errors.len());
        let mut sorted_errors: Vec<_> = errors.into_iter().collect();
        sorted_errors.sort_by(|a, b| b.1.cmp(&a.1));

        for (err, count) in sorted_errors {
            output.push_str(&format!("Count: {}\nError: {}\n----------------------------------------\n", count, err));
        }

        Ok(CallToolResult::success(vec![ContentBlock::text(output)]))
    }
}

#[tool_handler]
impl ServerHandler for ChthonicServer {
    fn get_info(&self) -> ServerInfo {
        // ServerInfo is #[non_exhaustive] — build from Default, then set fields.
        let mut info = ServerInfo::default();
        info.server_info.name = "chthonic-mcp-server".to_string();
        info.server_info.version = env!("CARGO_PKG_VERSION").to_string();
        info.capabilities = ServerCapabilities::builder().enable_tools().build();
        info.instructions = Some(
            "Chthonic polyglot CLI router (Rust/rmcp port of chthonic-v3). \
             Wraps scripts/chthonic.ps1. Use `chthonic` for any domain/action, \
             `chthonic_commands` to discover the surface, `chthonic_status`/`chthonic_doctor` \
             for health, and `chthonic_ssot`/`chthonic_toolchain` for those control planes. \
             Plain toolchain runs (cargo/uv/gcc/git/...) are intentionally omitted — use the \
             native Bash tool or the `git` MCP server."
                .to_string(),
        );
        info
    }
}

// ── pwsh resolution ───────────────────────────────────────────────────────────

fn resolve_pwsh() -> String {
    const CANDIDATES: [&str; 2] = [
        r"C:\Program Files\PowerShell\7\pwsh.exe",
        r"C:\Program Files\PowerShell\7-preview\pwsh.exe",
    ];
    for c in CANDIDATES {
        if std::path::Path::new(c).exists() {
            return c.to_string();
        }
    }
    "pwsh".to_string()
}

// ── main ────────────────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "chthonic_mcp_server=info".into()),
        )
        .with_writer(std::io::stderr)
        .init();

    let server = ChthonicServer::new();
    if !server.script.exists() {
        warn!(
            "chthonic.ps1 not found at {} — tools will error until CHTHONIC_ROOT is set correctly",
            server.script.display()
        );
    }
    info!(
        "chthonic-mcp-server starting (repo_root={}, pwsh={})",
        server.repo_root.display(),
        server.pwsh
    );

    let service = server.serve(rmcp::transport::stdio()).await?;
    service.waiting().await?;
    Ok(())
}
