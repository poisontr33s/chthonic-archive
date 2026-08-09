// @SID: TOOL_CHTHONIC_MCP_SERVER_V1
// ============================================================
// chthonic-mcp-server — stdio MCP server (rmcp 2.x)
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
// ── Absorbed canon family (2026-08-09) ──────────────────────
// Three standalone bun servers — `ssot`, `sourcer`, `asc-injector` —
// served ten tools that all answer one question: what does the catalyst
// (.chthonic/SSOT.md) say? Measured single-instance they cost
// 110 + 110 + 113 MB, essentially all of it three copies of the bun
// runtime, to run wrappers that shell out and pass JSON through. They
// live here now (see canon.rs); tool names are unchanged except the
// asc-injector `ping`, renamed `asc_ping` for an unambiguous namespace.
//
//   ssot_lint            unbalanced-bold audit of the catalyst
//   ssot_parse_frontier  where the DSL grammar first breaks
//   ssot_outline         header map
//   sourcer_check        is this name rooted in the heritage-root?
//   sourcer_section      where does this topic live?
//   sourcer_roster       canon organs + character rooting status
//   sourcer_orphans      characters the SSOT does not carry
//   sourcer_sdk          repo pins vs upstream latest
//   inject_asc_context   inject the catalyst (or one section)
//   asc_ping             catalyst liveness/size
//
// The engines stay where they were: ssot_loremaster.py, catalyst_lint.py,
// dsl-full-smoke and sourcer-sdk.ts remain the source of truth; this crate
// only spawns and shapes. The bun scripts remain on disk as reference.
//
// Transport: stdio (rmcp). Tool calls shell into chthonic.ps1 via a
// captured subprocess (no stdout pollution; tracing -> stderr).
// Repo root: CHTHONIC_ROOT env (set by .mcp.json) -> cwd fallback.
// ============================================================

mod canon;

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

// ── Absorbed-family parameter types (ssot / sourcer / asc) ──────────────────────

#[derive(Debug, Deserialize, JsonSchema)]
struct CatalystPathParams {
    /// File to operate on. Defaults to the catalyst (.chthonic/SSOT.md).
    path: Option<String>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct OutlineParams {
    /// File to outline. Defaults to the catalyst (.chthonic/SSOT.md).
    path: Option<String>,
    /// Maximum header depth to include (1-6). Default 6.
    max_level: Option<u32>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct NameParams {
    /// The name/term to source-check against the SSOT (case-insensitive substring).
    name: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct QueryParams {
    /// Heading or acronym query (case-insensitive).
    query: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct InjectParams {
    /// Specific section to inject (e.g. 'IV', 'VIII', 'X'). Omit for the full catalyst.
    section: Option<String>,
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

    // ── shared canon helpers (absorbed ssot / sourcer / asc-injector) ────────

    /// Caller-supplied catalyst path, else the resolved default.
    fn catalyst_or(&self, given: Option<String>) -> PathBuf {
        match given.map(|s| s.trim().to_string()).filter(|s| !s.is_empty()) {
            Some(s) => {
                let p = PathBuf::from(&s);
                if p.is_absolute() { p } else { self.repo_root.join(p) }
            }
            None => canon::ssot_path(&self.repo_root),
        }
    }

    /// `uv run scripts/ssot_loremaster.py <subcmd> [value] --json`
    ///
    /// Valid subcommands are fixed by the script: queue | entity | section |
    /// drift | lineage. There is no `check` — sourcer_check is the *tool* name,
    /// and it runs `entity` then shapes the rooted/orphan verdict from the hits.
    async fn loremaster_raw(&self, subcmd: &str, value: Option<&str>) -> Result<String, String> {
        let mut args: Vec<&str> = vec!["run", "scripts/ssot_loremaster.py", subcmd];
        if let Some(v) = value {
            args.push(v);
        }
        args.push("--json");
        canon::run_capture(&self.repo_root, "uv", &args).await
    }

    /// The organ-canon-citation audit manifest — the rooted/deferred roster.
    async fn citation_manifest_json(&self) -> Result<serde_json::Value, ErrorData> {
        let path = self
            .repo_root
            .join("manifest")
            .join("organ_canon_citation_audit.json");
        let text = tokio::fs::read_to_string(&path).await.map_err(|e| {
            ErrorData::internal_error(
                format!(
                    "organ-canon-citation audit not found at {} ({e}).\n\
                     Generate it first: bun run ci/checks/organ-canon-citation.ts",
                    path.display()
                ),
                None,
            )
        })?;
        serde_json::from_str(&text).map_err(|e| {
            ErrorData::internal_error(
                format!("citation manifest at {} is not valid JSON: {e}", path.display()),
                None,
            )
        })
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

    // ── absorbed: ssot lane ─────────────────────────────────────────────────

    #[tool(
        description = "Structural variance audit of the catalyst (.chthonic/SSOT.md). Returns every line with unbalanced markdown bold — the orphan-** defect that runs a bold across newlines and derails the DSL parse far downstream — each tagged with line number, kind (header/list-item/prose/table-row/blockquote), and bold-marker count. Fenced code blocks and inline-code spans are excluded so a literal ** (e.g. an applyTo: \"**\" glob) is not falsely flagged. Detection only."
    )]
    async fn ssot_lint(
        &self,
        Parameters(p): Parameters<CatalystPathParams>,
    ) -> Result<CallToolResult, ErrorData> {
        let path = self.catalyst_or(p.path);
        let path = path.to_string_lossy().to_string();
        match canon::run_capture(
            &self.repo_root,
            "uv",
            &["run", "scripts/catalyst_lint.py", "--json", "--path", &path],
        )
        .await
        {
            Ok(text) => Ok(CallToolResult::success(vec![ContentBlock::text(text)])),
            Err(e) => Ok(CallToolResult::error(vec![ContentBlock::text(e)])),
        }
    }

    #[tool(
        description = "Run the Chthonic DSL grammar against the FULL catalyst and report where the parse first breaks — the next structural corruption to fix. Returns status (OK if the whole catalyst parses, else FAIL), failing line/column, expected token, the first-failing-prefix line, that line's text, plus a diagnosis and next action. The corruption-walker: fix the reported line, re-run, it advances. A cold run compiles the Rust grammar tool and can take 1-2 minutes; warm runs are seconds."
    )]
    async fn ssot_parse_frontier(
        &self,
        Parameters(p): Parameters<CatalystPathParams>,
    ) -> Result<CallToolResult, ErrorData> {
        let path_buf = self.catalyst_or(p.path);
        let path = path_buf.to_string_lossy().to_string();
        let out = canon::run_capture(
            &self.repo_root,
            "cargo",
            &[
                "run", "-p", "dsl-smoke", "--release", "--bin", "dsl-full-smoke", "--quiet", "--",
                &path,
            ],
        )
        .await
        .unwrap_or_else(|e| e); // the tool reports failures on stderr; shape them anyway
        let file_text = tokio::fs::read_to_string(&path_buf).await.ok();
        let verdict = canon::parse_frontier(&out, file_text.as_deref());
        Ok(CallToolResult::success(vec![ContentBlock::text(
            serde_json::to_string_pretty(&verdict).unwrap_or_else(|e| e.to_string()),
        )]))
    }

    #[tool(
        description = "The catalyst's header/section outline — every markdown header as {line, level 1-6, title}, code fences excluded. Use to review structure and ordering: duplicated section numbers, out-of-sequence headers, dual-track (Arabic §0/§1 vs Roman §I/§II) inconsistencies, depth jumps. max_level caps depth (e.g. 3 for the top-level skeleton)."
    )]
    async fn ssot_outline(
        &self,
        Parameters(p): Parameters<OutlineParams>,
    ) -> Result<CallToolResult, ErrorData> {
        let path = self.catalyst_or(p.path);
        let text = tokio::fs::read_to_string(&path).await.map_err(|e| {
            ErrorData::internal_error(format!("failed to read {}: {e}", path.display()), None)
        })?;
        let max_level = p.max_level.unwrap_or(6).clamp(1, 6) as usize;
        let headings = canon::outline(&text, max_level);
        let payload = serde_json::json!({
            "path": path.to_string_lossy(),
            "headers": headings.len(),
            "outline": headings,
        });
        Ok(CallToolResult::success(vec![ContentBlock::text(
            serde_json::to_string_pretty(&payload).unwrap_or_else(|e| e.to_string()),
        )]))
    }

    // ── absorbed: sourcer lane ──────────────────────────────────────────────

    #[tool(
        description = "Ask the SSOT whether a name or term is rooted in the heritage-root canon. Pass an entity name (e.g. 'Orackla Nocticula'), an organ, a protocol, or any phrase; returns ROOTED (with the SSOT line(s) and section(s) where it lives) or ORPHAN (absent from the heritage-root) — so a claim can be sourced before it is trusted, rather than accepted from a derived JSON. Use before treating any character/entity/organ as canon."
    )]
    async fn sourcer_check(
        &self,
        Parameters(p): Parameters<NameParams>,
    ) -> Result<CallToolResult, ErrorData> {
        let query = p.name.trim();
        if query.is_empty() {
            return Ok(CallToolResult::error(vec![ContentBlock::text(
                "sourcer_check requires a non-empty 'name'.",
            )]));
        }
        let raw = match self.loremaster_raw("entity", Some(query)).await {
            Ok(t) => t,
            Err(e) => return Ok(CallToolResult::error(vec![ContentBlock::text(e)])),
        };
        let parsed: serde_json::Value = serde_json::from_str(&raw).map_err(|e| {
            ErrorData::internal_error(format!("ssot_loremaster entity returned non-JSON: {e}"), None)
        })?;
        let empty = Vec::new();
        let hits = parsed
            .get("archive_hits")
            .and_then(|h| h.as_array())
            .unwrap_or(&empty);
        let rooted = !hits.is_empty();
        let sources: Vec<serde_json::Value> = hits
            .iter()
            .take(12)
            .map(|h| {
                serde_json::json!({
                    "line": h.get("line"),
                    "section": h.get("section_title"),
                    "range": h.get("section_range"),
                    "text": h.get("text"),
                })
            })
            .collect();
        let verdict = serde_json::json!({
            "query": query,
            "rooted": rooted,
            "verdict": if rooted {
                "ROOTED — present in the heritage-root SSOT"
            } else {
                "ORPHAN — absent from the heritage-root SSOT (derived-only; source it before trusting)"
            },
            "hit_count": hits.len(),
            "sources": sources,
        });
        Ok(CallToolResult::success(vec![ContentBlock::text(
            serde_json::to_string_pretty(&verdict).unwrap_or_else(|e| e.to_string()),
        )]))
    }

    #[tool(
        description = "Search the SSOT's section headings and acronyms for a query (e.g. 'Triumvirate', 'Organ', 'ANKH'). Returns matching sections with heading line, level, title, acronyms and line range — the map of where a topic lives in the archive, so a reader can go to the source rather than a summary of it."
    )]
    async fn sourcer_section(
        &self,
        Parameters(p): Parameters<QueryParams>,
    ) -> Result<CallToolResult, ErrorData> {
        let query = p.query.trim();
        if query.is_empty() {
            return Ok(CallToolResult::error(vec![ContentBlock::text(
                "sourcer_section requires a non-empty 'query'.",
            )]));
        }
        match self.loremaster_raw("section", Some(query)).await {
            Ok(text) => Ok(CallToolResult::success(vec![ContentBlock::text(text)])),
            Err(e) => Ok(CallToolResult::error(vec![ContentBlock::text(e)])),
        }
    }

    #[tool(
        description = "The canonical roster as the heritage-root defines it: SSOT-canon organs, and every game/lore character with its rooting status (PASS = organ is in the SSOT organ canon; DEFERRED = organ pending SSOT promotion; FAIL = claims an organ the SSOT does not carry). Sourced from the organ-canon-citation audit manifest."
    )]
    async fn sourcer_roster(&self) -> Result<CallToolResult, ErrorData> {
        let m = self.citation_manifest_json().await?;
        let characters: Vec<serde_json::Value> = m
            .get("results")
            .and_then(|r| r.as_array())
            .map(|a| {
                a.iter()
                    .map(|r| {
                        let mut o = serde_json::json!({
                            "path": r.get("path"),
                            "organ": r.get("organ"),
                            "status": r.get("status"),
                        });
                        if let Some(reason) = r.get("reason") {
                            o["reason"] = reason.clone();
                        }
                        o
                    })
                    .collect()
            })
            .unwrap_or_default();
        let roster = serde_json::json!({
            "generated_at": m.get("generated_at"),
            "canonical_organs": m.get("ssot_canonical_organs"),
            "characters": characters,
            "summary": {
                "rooted": m.get("pass_count"),
                "deferred": m.get("deferred_count"),
                "failed": m.get("fail_count"),
            },
        });
        Ok(CallToolResult::success(vec![ContentBlock::text(
            serde_json::to_string_pretty(&roster).unwrap_or_else(|e| e.to_string()),
        )]))
    }

    #[tool(
        description = "List the characters NOT rooted in the heritage-root SSOT — those whose organ is deferred or fails the canon. These are derived artifacts the SSOT does not (yet) carry. Use to catch drift: a new character added without registering it in the SSOT first."
    )]
    async fn sourcer_orphans(&self) -> Result<CallToolResult, ErrorData> {
        let m = self.citation_manifest_json().await?;
        let orphans: Vec<serde_json::Value> = m
            .get("results")
            .and_then(|r| r.as_array())
            .map(|a| {
                a.iter()
                    .filter(|r| r.get("status").and_then(|s| s.as_str()).unwrap_or("") != "PASS")
                    .map(|r| {
                        let status = r.get("status").and_then(|s| s.as_str()).unwrap_or("");
                        let note = if status == "DEFERRED" {
                            serde_json::Value::from(
                                "organ pending SSOT promotion — present only as a derived JSON",
                            )
                        } else {
                            r.get("reason")
                                .cloned()
                                .unwrap_or_else(|| serde_json::Value::from("not rooted in the SSOT"))
                        };
                        serde_json::json!({
                            "path": r.get("path"),
                            "organ": r.get("organ"),
                            "status": r.get("status"),
                            "note": note,
                        })
                    })
                    .collect()
            })
            .unwrap_or_default();
        let payload = serde_json::json!({
            "orphan_count": orphans.len(),
            "orphans": orphans,
            "note": "Orphans are characters the heritage-root SSOT does not carry. To root one: register it in the SSOT first (a semantic act), then promote its organ — never the reverse.",
        });
        Ok(CallToolResult::success(vec![ContentBlock::text(
            serde_json::to_string_pretty(&payload).unwrap_or_else(|e| e.to_string()),
        )]))
    }

    #[tool(
        description = "Source the repo's pinned SDK versions against upstream latest — dependency currency, the same verification pointed at packages instead of canon. Returns each tracked SDK with its repo pin, latest upstream version (crates.io / GitHub releases), and status current/behind/ahead. Read-only: it reports the delta so a bump stays a decision."
    )]
    async fn sourcer_sdk(&self) -> Result<CallToolResult, ErrorData> {
        match canon::run_capture(
            &self.repo_root,
            "bun",
            &["run", "scripts/sourcer-sdk.ts", "compare", "--json"],
        )
        .await
        {
            Ok(text) => Ok(CallToolResult::success(vec![ContentBlock::text(text)])),
            Err(e) => Ok(CallToolResult::error(vec![ContentBlock::text(e)])),
        }
    }

    // ── absorbed: asc lane ──────────────────────────────────────────────────

    #[tool(
        description = "Inject the ASC Framework (Codex Brahmanica Perfectus, .chthonic/SSOT.md) into context. Omit `section` for the full catalyst, or pass a section marker (e.g. 'IV', 'VIII', 'X') to inject just that section. NOTE: the catalyst is ~1.27MB — a full injection is very large; prefer ssot_outline or sourcer_section to locate first."
    )]
    async fn inject_asc_context(
        &self,
        Parameters(p): Parameters<InjectParams>,
    ) -> Result<CallToolResult, ErrorData> {
        let path = canon::ssot_path(&self.repo_root);
        let text = tokio::fs::read_to_string(&path).await.map_err(|e| {
            ErrorData::internal_error(format!("failed to read SSOT at {}: {e}", path.display()), None)
        })?;
        let section = p.section.unwrap_or_else(|| "all".to_string());
        if section == "all" {
            return Ok(CallToolResult::success(vec![ContentBlock::text(format!(
                "ASC Framework Context Injected (Section: all)\n\n{text}"
            ))]));
        }
        match canon::extract_section(&text, &section) {
            Some(body) => Ok(CallToolResult::success(vec![ContentBlock::text(format!(
                "ASC Framework Context Injected (Section: {section})\n\n{body}"
            ))])),
            // The bun original returned "Section X not found. Injecting full SSOT."
            // and then injected nothing — a message describing an action it never
            // took. Report the miss and the real options instead.
            None => {
                let avail = canon::available_sections(&text);
                Ok(CallToolResult::error(vec![ContentBlock::text(format!(
                    "Section '{section}' not found in {}. Nothing was injected.\nAvailable section markers: {}",
                    path.display(),
                    if avail.is_empty() { "(none detected)".to_string() } else { avail.join(", ") }
                ))]))
            }
        }
    }

    #[tool(
        description = "Liveness probe for the canon lane: reports server version, resolved catalyst path and its size in bytes. Formerly the `ping` tool of the standalone asc-injector server; renamed for an unambiguous namespace in the merged surface."
    )]
    async fn asc_ping(&self) -> Result<CallToolResult, ErrorData> {
        let path = canon::ssot_path(&self.repo_root);
        let bytes = tokio::fs::metadata(&path).await.map(|m| m.len()).ok();
        let payload = serde_json::json!({
            "version": env!("CARGO_PKG_VERSION"),
            "ssot_path": path.to_string_lossy(),
            "ssot_bytes": bytes,
            "ssot_present": bytes.is_some(),
        });
        Ok(CallToolResult::success(vec![ContentBlock::text(
            serde_json::to_string_pretty(&payload).unwrap_or_else(|e| e.to_string()),
        )]))
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
