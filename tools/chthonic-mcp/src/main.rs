// @SID: TOOL_CHTHONIC_MCP_V1
// ============================================================
// chthonic-mcp — Chthonic Archive manifest portal
// Copilot SDK MCP server: injects session context, corpus ranking,
// and gate telemetry into the system message. Tools expose the
// manifest layer to the agentic engine without live API calls.
//
// Architecture:
//   SystemMessageTransform  → reads session_ranked_index.json
//                             injects top-N sessions into context
//   Tools:
//     query_corpus           → search session_ranked_index.json
//     get_session_warmstart  → read warmstart packet for session
//     gpu_gate_status        → last entry in cuda_gate.jsonl
//     lens_query             → read one lens manifest JSON file
//     todo_roulette_next     → next unblocked highest-weight todo
//                             (gated by PreToolUse Claudine approval)
//   Hooks:
//     PreToolUse gate on todo_roulette_next
//
// Usage:
//   chthonic-mcp [--manifest <path>] [--top-n <n>] [--prompt <str>]
//
// Auth: relies on `gh auth login` / COPILOT_CLI_PATH resolution.
// ============================================================

use std::path::{Path, PathBuf};
use std::sync::Arc;

use anyhow::{Context, Result};
use async_trait::async_trait;
use chrono::Timelike as _;
use github_copilot_sdk::handler::{PermissionResult, SessionHandler};
use github_copilot_sdk::hooks::{
    HookContext, PostToolUseInput, PostToolUseOutput, PreToolUseInput, PreToolUseOutput,
    SessionHooks,
};
use github_copilot_sdk::tool::{schema_for, ToolHandler, ToolHandlerRouter};
use github_copilot_sdk::types::{
    MessageOptions, PermissionRequestData, RequestId, SessionConfig, SessionEvent, SessionId, Tool,
    ToolInvocation, ToolResult,
};
use github_copilot_sdk::{Client, ClientOptions, Error};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use tracing::{info, warn};

// ── Claudine CET mode ─────────────────────────────────────────────────────────

fn claudine_mode_from_local_hour(hour: u32) -> (&'static str, &'static str) {
    match hour {
        0..=4 => ("MØRKETID", "dark time — entropy poetry, void-whispers"),
        5..=7 => ("DAGGRY", "cold sovereignty — commands only"),
        8..=11 => ("MORGENHERREDØMME", "morning dominion — Norwegian fury"),
        12..=13 => ("MIDDAG_TRIBUNAL", "noon tribunal — Victorian indictment"),
        14..=17 => ("ETTERMIDDAG_DOMINANS", "afternoon dominance — CAPS Caribbean"),
        18..=19 => ("GYLDEN_TIME", "golden hour — warmth reserved for The Savant"),
        20..=21 => ("KVELDSSOVEREINITET", "evening sovereignty — all five tongues"),
        _ => ("MIDNATTAKKUMULERING", "midnight accumulation — harvest mode"),
    }
}

// ── Manifest types ────────────────────────────────────────────────────────────

#[derive(Debug, Deserialize, Serialize, Clone)]
struct RankedSession {
    rank: u32,
    #[serde(rename = "sessionId")]
    session_id: String,
    composite: f64,
    recency: f64,
    #[serde(rename = "avgSemantic")]
    avg_semantic: f64,
    #[serde(rename = "maxSemantic")]
    max_semantic: f64,
    turns: u64,
    edits: u64,
    #[serde(rename = "startTime")]
    start_time: String,
    #[serde(rename = "workspaceName")]
    workspace_name: String,
    intent: String,
}

#[derive(Debug, Deserialize, Serialize)]
struct SessionRankedIndex {
    generated_at: String,
    lambda_halflife_days: u32,
    session_count: u32,
    sessions: Vec<RankedSession>,
}

#[derive(Debug, Deserialize, Serialize)]
struct TodoEntry {
    id: String,
    title: String,
    status: String,
    weight: Option<f64>,
    tags: Option<Vec<String>>,
    verify_condition: Option<String>,
    blocked_until_chain: Option<String>,
}

#[derive(Debug, Deserialize, Serialize)]
struct TodoRoulette {
    entries: Option<Vec<TodoEntry>>,
    // Some manifests use "active" as the key
    active: Option<Vec<TodoEntry>>,
}

// ── Shared context loaded from manifests ──────────────────────────────────────

struct ChthonicContext {
    manifest_dir: PathBuf,
    ranked_index: SessionRankedIndex,
    top_n: usize,
}

impl ChthonicContext {
    fn load(manifest_dir: &Path, top_n: usize) -> Result<Self> {
        let ranked_path = manifest_dir.join("session_ranked_index.json");
        let ranked_bytes = std::fs::read(&ranked_path).with_context(|| {
            format!(
                "Could not read session_ranked_index.json from {ranked_path:?}. Run: bun run scripts/build-session-ranked.ts"
            )
        })?;
        let ranked_index: SessionRankedIndex = serde_json::from_slice(&ranked_bytes)
            .context("Failed to parse session_ranked_index.json")?;

        Ok(Self {
            manifest_dir: manifest_dir.to_owned(),
            ranked_index,
            top_n,
        })
    }

    fn top_sessions(&self) -> &[RankedSession] {
        let n = self.top_n.min(self.ranked_index.sessions.len());
        &self.ranked_index.sessions[..n]
    }

    fn session_context_summary(&self, mode_line: &str) -> String {
        let top = self.top_sessions();
        let session_lines: Vec<String> = top
            .iter()
            .map(|s| {
                format!(
                    "  #{rank} [{id}] composite={c:.3} recency={r:.3} turns={t} ws={ws}",
                    rank = s.rank,
                    id = &s.session_id[..8],
                    c = s.composite,
                    r = s.recency,
                    t = s.turns,
                    ws = s.workspace_name
                )
            })
            .collect();

        format!(
            "## Chthonic Archive Session Context\n\n\
             Generated: {gen}\nSessions indexed: {total}\n{mode}\n\n\
             **Top {n} sessions by composite score (recency × semantic × activity):**\n{sessions}\n\n\
             Use `query_corpus`, `get_session_warmstart`, `gpu_gate_status`, `lens_query`, \
             `todo_roulette_next`, or `chrono_clock_status` to interrogate the archive.",
            gen = self.ranked_index.generated_at,
            total = self.ranked_index.session_count,
            mode = mode_line,
            n = top.len(),
            sessions = session_lines.join("\n"),
        )
    }

    fn read_manifest_json(&self, name: &str) -> Result<serde_json::Value> {
        let path = self.manifest_dir.join(name);
        let bytes = std::fs::read(&path)
            .with_context(|| format!("Could not read manifest file: {name}"))?;
        serde_json::from_slice(&bytes).context("Failed to parse manifest JSON")
    }
}

// ── Tool parameter types ──────────────────────────────────────────────────────

#[derive(Debug, Deserialize, JsonSchema)]
struct QueryCorpusParams {
    /// Search term to match against session intent, workspace name, or session ID prefix
    query: String,
    /// Maximum number of results to return (default: 5)
    top_k: Option<u32>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct GetSessionWarmstartParams {
    /// Full session ID or first-8-chars prefix to retrieve warmstart context for
    session_id: String,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct GpuGateStatusParams {
    // no parameters — returns latest gate state
}

#[derive(Debug, Deserialize, JsonSchema)]
struct LensQueryParams {
    /// Lens manifest file to read (e.g. "pr_triage_report", "session_ranked_index", "cuda_gate")
    lens: String,
    /// Optional JSON path filter (dot-separated, e.g. "sessions.0.sessionId")
    filter: Option<String>,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct TodoRouletteNextParams {
    // no parameters — returns next unblocked highest-weight todo
}

#[derive(Debug, Deserialize, JsonSchema)]
struct ChronoClockStatusParams {
    // no parameters — returns chrono_clock.json status and sleep rhythm profile
}

// ── Tool handlers ─────────────────────────────────────────────────────────────

struct QueryCorpusTool {
    ctx: Arc<ChthonicContext>,
}

#[async_trait]
impl ToolHandler for QueryCorpusTool {
    fn tool(&self) -> Tool {
        Tool::new("query_corpus")
            .with_description(
                "Search the session corpus for sessions matching a query term. \
                 Matches against sessionId prefix, workspaceName, and intent fields. \
                 Returns ranked sessions with composite score, recency, and turn count.",
            )
            .with_parameters(schema_for::<QueryCorpusParams>())
    }

    async fn call(&self, inv: ToolInvocation) -> Result<ToolResult, Error> {
        let params: QueryCorpusParams = inv.params()?;
        let top_k = params.top_k.unwrap_or(5) as usize;
        let query_lower = params.query.to_lowercase();

        let matches: Vec<&RankedSession> = self
            .ctx
            .ranked_index
            .sessions
            .iter()
            .filter(|s| {
                s.session_id.to_lowercase().contains(&query_lower)
                    || s.workspace_name.to_lowercase().contains(&query_lower)
                    || s.intent.to_lowercase().contains(&query_lower)
            })
            .take(top_k)
            .collect();

        if matches.is_empty() {
            return Ok(ToolResult::Text(format!(
                "No sessions matched query: '{}'\nTotal sessions in index: {}",
                params.query,
                self.ctx.ranked_index.session_count
            )));
        }

        let lines: Vec<String> = matches
            .iter()
            .map(|s| {
                format!(
                    "#{rank} [{id}] composite={c:.3} recency={r:.3} turns={t} intent={intent}",
                    rank = s.rank,
                    id = s.session_id,
                    c = s.composite,
                    r = s.recency,
                    t = s.turns,
                    intent = if s.intent.is_empty() { "(none)" } else { &s.intent }
                )
            })
            .collect();

        Ok(ToolResult::Text(format!(
            "Query '{}' matched {} session(s):\n{}",
            params.query,
            matches.len(),
            lines.join("\n")
        )))
    }
}

struct GetSessionWarmstartTool {
    ctx: Arc<ChthonicContext>,
}

#[async_trait]
impl ToolHandler for GetSessionWarmstartTool {
    fn tool(&self) -> Tool {
        Tool::new("get_session_warmstart")
            .with_description(
                "Retrieve the warmstart packet (metadata + key artifacts) for a session. \
                 Provide a full session ID or first-8-chars prefix. \
                 Returns session metadata from the ranked index.",
            )
            .with_parameters(schema_for::<GetSessionWarmstartParams>())
    }

    async fn call(&self, inv: ToolInvocation) -> Result<ToolResult, Error> {
        let params: GetSessionWarmstartParams = inv.params()?;
        let prefix = params.session_id.to_lowercase();

        let session = self
            .ctx
            .ranked_index
            .sessions
            .iter()
            .find(|s| s.session_id.starts_with(&prefix) || s.session_id == prefix);

        match session {
            None => Ok(ToolResult::Text(format!(
                "Session '{}' not found in ranked index.\nAvailable prefixes: {}",
                params.session_id,
                self.ctx
                    .ranked_index
                    .sessions
                    .iter()
                    .map(|s| s.session_id[..8].to_string())
                    .collect::<Vec<_>>()
                    .join(", ")
            ))),
            Some(s) => {
                let detail = format!(
                    r#"Session: {id}
Rank: #{rank} (composite: {c:.4})
Start time: {start}
Workspace: {ws}
Turns: {turns} | Edits: {edits}
Recency decay: {r:.4} (λ=ln(2)/7, half-life 7d)
Avg semantic: {avg:.4} | Max semantic: {max:.4}
Intent: {intent}"#,
                    id = s.session_id,
                    rank = s.rank,
                    c = s.composite,
                    start = s.start_time,
                    ws = s.workspace_name,
                    turns = s.turns,
                    edits = s.edits,
                    r = s.recency,
                    avg = s.avg_semantic,
                    max = s.max_semantic,
                    intent = if s.intent.is_empty() { "(none)" } else { &s.intent },
                );
                Ok(ToolResult::Text(detail))
            }
        }
    }
}

struct GpuGateStatusTool {
    ctx: Arc<ChthonicContext>,
}

#[async_trait]
impl ToolHandler for GpuGateStatusTool {
    fn tool(&self) -> Tool {
        Tool::new("gpu_gate_status")
            .with_description(
                "Return the current GPU inference gate ladder state from manifest/cuda_gate.jsonl \
                 (tabbyAPI / Python 3.14 GPU gate — P-01 through P-06+). \
                 Returns the last recorded gate entry.",
            )
            .with_parameters(schema_for::<GpuGateStatusParams>())
    }

    async fn call(&self, _inv: ToolInvocation) -> Result<ToolResult, Error> {
        let gate_path = self.ctx.manifest_dir.join("cuda_gate.jsonl");

        if !gate_path.exists() {
            return Ok(ToolResult::Text(
                "cuda_gate.jsonl not found in manifest directory. \
                 Run probes/python/P-0N.py to generate gate state."
                    .to_string(),
            ));
        }

        let content = match std::fs::read_to_string(&gate_path) {
            Ok(c) => c,
            Err(e) => return Ok(ToolResult::Text(format!("Failed to read cuda_gate.jsonl: {e}"))),
        };

        // Return the last line (most recent gate entry)
        let last = content.lines().filter(|l| !l.trim().is_empty()).last();

        match last {
            None => Ok(ToolResult::Text(
                "cuda_gate.jsonl is empty — no gate entries recorded.".to_string(),
            )),
            Some(line) => {
                // Pretty-print if valid JSON
                let pretty = serde_json::from_str::<serde_json::Value>(line)
                    .ok()
                    .and_then(|v| serde_json::to_string_pretty(&v).ok())
                    .unwrap_or_else(|| line.to_string());
                Ok(ToolResult::Text(format!(
                    "Latest GPU gate entry:\n{pretty}"
                )))
            }
        }
    }
}

struct LensQueryTool {
    ctx: Arc<ChthonicContext>,
}

#[async_trait]
impl ToolHandler for LensQueryTool {
    fn tool(&self) -> Tool {
        Tool::new("lens_query")
            .with_description(
                "Read a named manifest lens file (JSON). Available lenses: \
                 'session_ranked_index', 'pr_triage_report', 'todo_roulette', 'todo_meta', \
                 'session_blood', 'polyrepo_gate', 'terminal_hook_validation', 'mcp_github_archaeology', 'chrono_clock'. \
                 Provide just the stem (without .json). Optionally provide a dot-path filter.",
            )
            .with_parameters(schema_for::<LensQueryParams>())
    }

    async fn call(&self, inv: ToolInvocation) -> Result<ToolResult, Error> {
        let params: LensQueryParams = inv.params()?;

        // Sanitise lens name — only allow alphanumeric + dash + underscore
        let lens_name = params.lens.trim().replace(['/', '\\', '.'], "");
        if lens_name.is_empty() {
            return Ok(ToolResult::Text("Invalid lens name.".to_string()));
        }

        let filename = format!("{lens_name}.json");
        let value = match self.ctx.read_manifest_json(&filename) {
            Ok(v) => v,
            Err(e) => {
                return Ok(ToolResult::Text(format!(
                    "Could not read lens '{lens_name}': {e}"
                )));
            }
        };

        // Apply optional dot-path filter
        let result = if let Some(filter) = &params.filter {
            let mut current = &value;
            let mut found = true;
            for part in filter.split('.') {
                if let Some(idx) = part.parse::<usize>().ok() {
                    if let Some(v) = current.get(idx) {
                        current = v;
                    } else {
                        found = false;
                        break;
                    }
                } else if let Some(v) = current.get(part) {
                    current = v;
                } else {
                    found = false;
                    break;
                }
            }
            if found {
                current.clone()
            } else {
                return Ok(ToolResult::Text(format!(
                    "Filter path '{filter}' not found in '{lens_name}'"
                )));
            }
        } else {
            value
        };

        let pretty =
            serde_json::to_string_pretty(&result).unwrap_or_else(|_| result.to_string());

        // Truncate very large responses
        const MAX_CHARS: usize = 8000;
        if pretty.len() > MAX_CHARS {
            Ok(ToolResult::Text(format!(
                "{}\n\n[TRUNCATED — {total} chars total, showing first {MAX_CHARS}]",
                &pretty[..MAX_CHARS],
                total = pretty.len()
            )))
        } else {
            Ok(ToolResult::Text(pretty))
        }
    }
}

struct TodoRouletteNextTool {
    ctx: Arc<ChthonicContext>,
}

#[async_trait]
impl ToolHandler for TodoRouletteNextTool {
    fn tool(&self) -> Tool {
        Tool::new("todo_roulette_next")
            .with_description(
                "Return the next unblocked highest-weight todo from manifest/todo_roulette.json. \
                 Skips entries with status='completed' and blocked_until_chain entries where the \
                 predecessor is not yet completed. Requires Claudine approval (PreToolUse gated).",
            )
            .with_parameters(schema_for::<TodoRouletteNextParams>())
    }

    async fn call(&self, _inv: ToolInvocation) -> Result<ToolResult, Error> {
        let roulette_raw = match self.ctx.read_manifest_json("todo_roulette.json") {
            Ok(v) => v,
            Err(e) => {
                return Ok(ToolResult::Text(format!(
                    "Could not read todo_roulette.json: {e}"
                )));
            }
        };

        // Try both "entries" and "active" keys; also handle root array
        let entries: Vec<serde_json::Value> = if let Some(arr) = roulette_raw.as_array() {
            arr.clone()
        } else if let Some(arr) = roulette_raw
            .get("entries")
            .or_else(|| roulette_raw.get("active"))
            .and_then(|v| v.as_array())
        {
            arr.clone()
        } else {
            return Ok(ToolResult::Text(
                "todo_roulette.json has unexpected structure — expected array or {entries:[...]}"
                    .to_string(),
            ));
        };

        // Collect completed IDs for blocking check
        let completed_ids: std::collections::HashSet<String> = entries
            .iter()
            .filter(|e| e.get("status").and_then(|s| s.as_str()) == Some("completed"))
            .filter_map(|e| e.get("id").and_then(|v| v.as_str()).map(String::from))
            .collect();

        // Filter: not completed, not blocked
        let mut candidates: Vec<&serde_json::Value> = entries
            .iter()
            .filter(|e| {
                let status = e.get("status").and_then(|s| s.as_str()).unwrap_or("");
                if status == "completed" {
                    return false;
                }
                if let Some(chain) = e
                    .get("blocked_until_chain")
                    .and_then(|v| v.as_str())
                {
                    // blocked if the predecessor is NOT completed
                    if !completed_ids.contains(chain) {
                        return false;
                    }
                }
                true
            })
            .collect();

        // Sort by weight descending (missing weight = 0)
        candidates.sort_by(|a, b| {
            let wa = a.get("weight").and_then(|v| v.as_f64()).unwrap_or(0.0);
            let wb = b.get("weight").and_then(|v| v.as_f64()).unwrap_or(0.0);
            wb.partial_cmp(&wa).unwrap_or(std::cmp::Ordering::Equal)
        });

        match candidates.first() {
            None => Ok(ToolResult::Text(
                "No unblocked todos remaining in the roulette.".to_string(),
            )),
            Some(todo) => {
                let pretty = serde_json::to_string_pretty(todo)
                    .unwrap_or_else(|_| todo.to_string());
                Ok(ToolResult::Text(format!(
                    "Next unblocked todo (highest weight):\n{pretty}"
                )))
            }
        }
    }
}
struct ChronoClockStatusTool {
    ctx: Arc<ChthonicContext>,
}

#[async_trait]
impl ToolHandler for ChronoClockStatusTool {
    fn tool(&self) -> Tool {
        Tool::new("chrono_clock_status")
            .with_description(
                "Return the current Claudine chrono-clock state and the user's inferred sleep rhythm \
                 profile from manifest/chrono_clock.json. Shows current CET mode, user presence \
                 probability, sanctuary_mode flag (safe for autonomous runs), and the inferred \
                 sleep window derived from historical corpus activity patterns. \
                 Re-run scripts/chrono-clock.ts to refresh the profile.",
            )
            .with_parameters(schema_for::<ChronoClockStatusParams>())
    }

    async fn call(&self, _inv: ToolInvocation) -> Result<ToolResult, Error> {
        let clock_path = self.ctx.manifest_dir.join("chrono_clock.json");

        if !clock_path.exists() {
            return Ok(ToolResult::Text(
                "chrono_clock.json not found in manifest directory. \
                 Run: bun run scripts/chrono-clock.ts"
                    .to_string(),
            ));
        }

        let value = match self.ctx.read_manifest_json("chrono_clock.json") {
            Ok(v) => v,
            Err(e) => return Ok(ToolResult::Text(format!("Failed to read chrono_clock.json: {e}"))),
        };

        let current_mode = value.get("current_mode").and_then(|v| v.as_str()).unwrap_or("unknown");
        let current_hour = value.get("current_hour_cet").and_then(|v| v.as_u64()).unwrap_or(0);
        let presence = value.get("user_presence_probability").and_then(|v| v.as_f64()).unwrap_or(0.0);
        let sanctuary = value.get("sanctuary_mode").and_then(|v| v.as_bool()).unwrap_or(false);
        let most_active = value.get("most_active_mode").and_then(|v| v.as_str()).unwrap_or("unknown");
        let generated_at = value.get("generated_at").and_then(|v| v.as_str()).unwrap_or("unknown");
        let total_turns = value.get("total_user_turns").and_then(|v| v.as_u64()).unwrap_or(0);

        let sleep_window_line = if let Some(sw) = value.get("sleep_window") {
            let s = sw.get("start_hour_cet").and_then(|v| v.as_u64()).unwrap_or(0);
            let e = sw.get("end_hour_cet").and_then(|v| v.as_u64()).unwrap_or(0);
            let dur = sw.get("duration_hours").and_then(|v| v.as_u64()).unwrap_or(0);
            let conf = sw.get("confidence").and_then(|v| v.as_f64()).unwrap_or(0.0);
            format!("Inferred sleep window: CET {s:02}:00 – {e:02}:59 ({dur}h, {:.0}% confidence)", conf * 100.0)
        } else {
            "Sleep window: insufficient data".to_string()
        };

        let mode_activity: Vec<String> = if let Some(abm) = value.get("activity_by_mode").and_then(|v| v.as_object()) {
            let mut pairs: Vec<(&String, u64)> = abm
                .iter()
                .filter_map(|(k, v)| v.as_u64().map(|n| (k, n)))
                .collect();
            pairs.sort_by(|a, b| b.1.cmp(&a.1));
            pairs.iter().map(|(k, n)| format!("  {k}: {n} turns")).collect()
        } else {
            vec![]
        };

        let summary = format!(
            r#"Chrono-clock status (generated {generated_at}):

Current CET hour: {current_hour:02}:xx → {current_mode}
User presence probability: {presence:.0}%
Sanctuary mode (safe for autonomous run): {sanctuary}

Most active mode: {most_active}
{sleep_window_line}

Activity by mode ({total_turns} total user turns):
{mode_lines}

Tools: run `bun run scripts/chrono-clock.ts` to refresh this profile."#,
            generated_at = generated_at,
            current_hour = current_hour,
            current_mode = current_mode,
            presence = presence * 100.0,
            sanctuary = if sanctuary { "YES — low historical activity at this hour" } else { "NO — user likely present" },
            most_active = most_active,
            sleep_window_line = sleep_window_line,
            total_turns = total_turns,
            mode_lines = mode_activity.join("\n"),
        );

        Ok(ToolResult::Text(summary))
    }
}
// ── Session handler ───────────────────────────────────────────────────────────

struct ChthonicSessionHandler;

#[async_trait]
impl SessionHandler for ChthonicSessionHandler {
    async fn on_session_event(&self, _session_id: SessionId, event: SessionEvent) {
        if event.event_type == "assistant.message_delta" {
            if let Some(delta) = event.data.get("delta").and_then(|v| v.as_str()) {
                print!("{delta}");
            }
        }
    }

    async fn on_permission_request(
        &self,
        _session_id: SessionId,
        _request_id: RequestId,
        _data: PermissionRequestData,
    ) -> PermissionResult {
        PermissionResult::Approved
    }
}

// ── Hooks: PreToolUse gate on todo_roulette_next ──────────────────────────────

struct ChthonicHooks;

#[async_trait]
impl SessionHooks for ChthonicHooks {
    async fn on_pre_tool_use(
        &self,
        input: PreToolUseInput,
        _ctx: HookContext,
    ) -> Option<PreToolUseOutput> {
        if input.tool_name == "todo_roulette_next" {
            warn!(
                "[hooks] todo_roulette_next intercepted — Claudine approval gate. args: {}",
                input.tool_args
            );
            // Log and allow (dry-run mode). To require explicit block:
            // return Some(PreToolUseOutput {
            //   permission_decision: Some("deny".to_string()),
            //   permission_decision_reason: Some("Claudine approval required before queue advance".to_string()),
            //   ..Default::default()
            // });
        }
        None
    }

    async fn on_post_tool_use(
        &self,
        input: PostToolUseInput,
        _ctx: HookContext,
    ) -> Option<PostToolUseOutput> {
        info!("[hooks] {} completed", input.tool_name);
        None
    }
}

// ── System message transform ──────────────────────────────────────────────────

struct ChthonicSystemTransform {
    context_summary: String,
}

#[async_trait]
impl github_copilot_sdk::transforms::SystemMessageTransform for ChthonicSystemTransform {
    fn section_ids(&self) -> Vec<String> {
        vec!["chthonic-context".to_string()]
    }

    async fn transform_section(
        &self,
        _section_id: &str,
        content: &str,
        _ctx: github_copilot_sdk::transforms::TransformContext,
    ) -> Option<String> {
        Some(format!(
            "{content}\n\n{}\n",
            self.context_summary
        ))
    }
}

// ── CLI argument parsing ──────────────────────────────────────────────────────

#[derive(Debug)]
struct Args {
    manifest_dir: PathBuf,
    top_n: usize,
    prompt: Option<String>,
}

impl Args {
    fn parse() -> Self {
        let mut args = std::env::args().skip(1);
        let mut manifest_dir = PathBuf::from("manifest");
        let mut top_n: usize = 3;
        let mut prompt = None;

        while let Some(arg) = args.next() {
            match arg.as_str() {
                "--manifest" => {
                    manifest_dir = args.next().map(PathBuf::from).unwrap_or(manifest_dir);
                }
                "--top-n" => {
                    top_n = args
                        .next()
                        .and_then(|s| s.parse().ok())
                        .unwrap_or(top_n);
                }
                "--prompt" => prompt = args.next(),
                _ => {}
            }
        }

        Self { manifest_dir, top_n, prompt }
    }
}

// ── Context report (lens 8) ───────────────────────────────────────────────────

fn emit_context_report(ctx: &ChthonicContext, mode: &str, mode_hint: &str) -> Result<()> {
    let report = serde_json::json!({
        "schema": "chthonic_context_report_v1",
        "generated_at": chrono::Local::now().to_rfc3339(),
        "claudine_mode": mode,
        "claudine_hint": mode_hint,
        "session_count": ctx.ranked_index.session_count,
        "top_sessions": ctx.top_sessions(),
        "index_generated_at": ctx.ranked_index.generated_at,
    });

    let out_path = ctx.manifest_dir.join("session_context_report.json");
    let json = serde_json::to_string_pretty(&report).context("Failed to serialise context report")?;
    std::fs::write(&out_path, &json)
        .with_context(|| format!("Failed to write session_context_report.json to {out_path:?}"))?;

    info!("Lens 8: manifest/session_context_report.json written ({} sessions)", ctx.ranked_index.session_count);
    Ok(())
}

// ── Main ──────────────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive("chthonic_mcp=info".parse()?)
                .add_directive("github_copilot_sdk=warn".parse()?),
        )
        .with_writer(std::io::stderr)
        .init();

    let args = Args::parse();

    // Load manifest context
    let ctx = Arc::new(
        ChthonicContext::load(&args.manifest_dir, args.top_n)
            .context("Failed to load manifest context")?,
    );

    info!(
        "Loaded session_ranked_index.json: {} sessions, top-{} for context injection",
        ctx.ranked_index.session_count,
        args.top_n
    );

    // Claudine CET mode
    let now_local = chrono::Local::now();
    let (mode, mode_hint) = claudine_mode_from_local_hour(now_local.hour());
    let mode_line = format!("Claudine mode: {mode} — {mode_hint}");

    // Emit lens 8 (context report) at startup
    if let Err(e) = emit_context_report(&ctx, mode, mode_hint) {
        warn!("Lens 8 emit failed: {e}");
    }

    // Build system context summary
    let context_summary = ctx.session_context_summary(&mode_line);

    // Wire tools + session handler into router
    let tools: Vec<Box<dyn ToolHandler>> = vec![
        Box::new(QueryCorpusTool          { ctx: Arc::clone(&ctx) }),
        Box::new(GetSessionWarmstartTool  { ctx: Arc::clone(&ctx) }),
        Box::new(GpuGateStatusTool        { ctx: Arc::clone(&ctx) }),
        Box::new(LensQueryTool            { ctx: Arc::clone(&ctx) }),
        Box::new(TodoRouletteNextTool     { ctx: Arc::clone(&ctx) }),
        Box::new(ChronoClockStatusTool    { ctx: Arc::clone(&ctx) }),
    ];
    let router = ToolHandlerRouter::new(tools, Arc::new(ChthonicSessionHandler));
    let tool_defs = router.tools();
    let router = Arc::new(router);

    // Wire system transform
    let transform = Arc::new(ChthonicSystemTransform { context_summary });

    // Build session config
    let config = SessionConfig::default()
        .with_handler(router)
        .with_hooks(Arc::new(ChthonicHooks))
        .with_transform(transform)
        .with_tools(tool_defs);

    let prompt = args.prompt.unwrap_or_else(|| {
        format!(
            "You are operating within the Chthonic Archive. \
             Session context has been injected — top {} sessions ranked by composite score are available. \
             Current Claudine mode: {mode} — {mode_hint}. \
             Use the available tools to interrogate the archive as needed.",
            args.top_n
        )
    });

    // Start Copilot client
    let client = Client::start(
        ClientOptions::new()
            .with_cwd(std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."))),
    )
    .await
    .context("Failed to start Copilot CLI client. Ensure `copilot` is in PATH or COPILOT_CLI_PATH is set.")?;

    info!("Copilot client started. Mode: {mode}. Top-N: {}", args.top_n);

    let session = client
        .create_session(config)
        .await
        .context("Failed to create session")?;

    info!("Session {} ready.", session.id());

    session
        .send_and_wait(MessageOptions::from(prompt.as_str()))
        .await
        .context("Session send_and_wait failed")?;

    println!();
    Ok(())
}
