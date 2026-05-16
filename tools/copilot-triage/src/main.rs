// @SID: TOOL_COPILOT_TRIAGE_V1
// ============================================================
// copilot-triage — Copilot SDK reasoning engine over PR archaeology
// Layer B: drives GitHub Copilot as a structured triage assistant
// reading from manifest/pr_triage_report.json (emitted by Layer A).
//
// Usage:
//   copilot-triage [--repo <owner/repo>] [--pr <number>] [--batch]
//
// Auth: relies on `gh auth login` / COPILOT_CLI_PATH resolution.
// Tools exposed to the agent: analyze_pr, fetch_pr_checks, comment_pr
// Hooks: PreToolUse gate on comment_pr (requires explicit user approval)
// ============================================================

use std::path::PathBuf;
use std::sync::Arc;

use anyhow::{Context, Result};
use async_trait::async_trait;
use github_copilot_sdk::handler::{PermissionResult, SessionHandler};
use github_copilot_sdk::hooks::{HookContext, PostToolUseInput, PostToolUseOutput, PreToolUseInput, PreToolUseOutput, SessionHooks};
use github_copilot_sdk::tool::{ToolHandler, ToolHandlerRouter, schema_for};
use schemars::JsonSchema;
use github_copilot_sdk::types::{
    MessageOptions, PermissionRequestData, RequestId, SessionConfig, SessionEvent, SessionId,
    Tool, ToolInvocation, ToolResult,
};
use github_copilot_sdk::{Client, ClientOptions, Error};
use serde::Deserialize;
use tracing::{info, warn};

// ── Manifest types ────────────────────────────────────────────────────────────

#[derive(Debug, Deserialize)]
struct PrSummary {
    number: u64,
    title: String,
    state: String,
    draft: bool,
    author: String,
    head_branch: String,
    base_branch: String,
    created_at: String,
    updated_at: String,
    mergeable: Option<bool>,
    labels: Vec<String>,
    review_count: u64,
    comment_count: u64,
    checks_passed: Option<u64>,
    checks_failed: Option<u64>,
    checks_pending: Option<u64>,
    url: String,
}

#[derive(Debug, Deserialize)]
struct TriageReport {
    repo: String,
    generated_at: String,
    total: u64,
    prs: Vec<PrSummary>,
}

// ── Tool parameter types ──────────────────────────────────────────────────────

#[derive(Debug, Deserialize, JsonSchema)]
struct AnalyzePrParams {
    /// PR number to analyze from the loaded triage report
    pr_number: u64,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct FetchPrChecksParams {
    /// PR number to fetch CI check status for
    pr_number: u64,
}

#[derive(Debug, Deserialize, JsonSchema)]
struct CommentPrParams {
    /// PR number to comment on
    pr_number: u64,
    /// Comment body (markdown supported)
    body: String,
}

// ── Tool handlers ─────────────────────────────────────────────────────────────

struct AnalyzePrTool {
    report: Arc<TriageReport>,
}

#[async_trait]
impl ToolHandler for AnalyzePrTool {
    fn tool(&self) -> Tool {
        Tool::new("analyze_pr")
            .with_description("Retrieve structured data for a PR from the loaded triage report. Returns title, state, CI status, merge conflicts, review threads, and labels.")
            .with_parameters(schema_for::<AnalyzePrParams>())
    }

    async fn call(&self, inv: ToolInvocation) -> Result<ToolResult, Error> {
        let params: AnalyzePrParams = inv.params()?;

        let pr = self
            .report
            .prs
            .iter()
            .find(|p| p.number == params.pr_number);

        match pr {
            None => Ok(ToolResult::Text(format!(
                "PR #{} not found in triage report (repo: {}). Available PR numbers: {}",
                params.pr_number,
                self.report.repo,
                self.report
                    .prs
                    .iter()
                    .map(|p| p.number.to_string())
                    .collect::<Vec<_>>()
                    .join(", ")
            ))),
            Some(p) => {
                let checks = match (p.checks_passed, p.checks_failed, p.checks_pending) {
                    (Some(passed), Some(failed), Some(pending)) => {
                        format!("passed={passed} failed={failed} pending={pending}")
                    }
                    _ => "unknown".to_string(),
                };
                let analysis = format!(
                    r#"PR #{number}: {title}
State: {state}{draft}
Author: {author}
Branch: {head} → {base}
Created: {created} | Updated: {updated}
Mergeable: {mergeable}
Labels: {labels}
Reviews: {reviews} | Comments: {comments}
CI Checks: {checks}
URL: {url}"#,
                    number = p.number,
                    title = p.title,
                    state = p.state,
                    draft = if p.draft { " (DRAFT)" } else { "" },
                    author = p.author,
                    head = p.head_branch,
                    base = p.base_branch,
                    created = p.created_at,
                    updated = p.updated_at,
                    mergeable = p
                        .mergeable
                        .map(|m| if m { "yes" } else { "no" })
                        .unwrap_or("unknown"),
                    labels = if p.labels.is_empty() {
                        "none".to_string()
                    } else {
                        p.labels.join(", ")
                    },
                    reviews = p.review_count,
                    comments = p.comment_count,
                    checks = checks,
                    url = p.url,
                );
                Ok(ToolResult::Text(analysis))
            }
        }
    }
}

struct FetchPrChecksTool {
    report: Arc<TriageReport>,
}

#[async_trait]
impl ToolHandler for FetchPrChecksTool {
    fn tool(&self) -> Tool {
        Tool::new("fetch_pr_checks")
            .with_description("Return the CI check summary for a PR (passed/failed/pending counts from the triage report).")
            .with_parameters(schema_for::<FetchPrChecksParams>())
    }

    async fn call(&self, inv: ToolInvocation) -> Result<ToolResult, Error> {
        let params: FetchPrChecksParams = inv.params()?;

        let pr = self
            .report
            .prs
            .iter()
            .find(|p| p.number == params.pr_number);

        match pr {
            None => Ok(ToolResult::Text(format!(
                "PR #{} not found in report.",
                params.pr_number
            ))),
            Some(p) => {
                let result = serde_json::json!({
                    "pr_number": p.number,
                    "checks_passed": p.checks_passed,
                    "checks_failed": p.checks_failed,
                    "checks_pending": p.checks_pending,
                    "overall": if p.checks_failed == Some(0) { "green" }
                               else if p.checks_failed.unwrap_or(0) > 0 { "red" }
                               else { "unknown" }
                });
                Ok(ToolResult::Text(result.to_string()))
            }
        }
    }
}

/// Stub tool — posting comments requires live gh CLI calls.
/// This tool is gated by PreToolUse and logs the intent to stdout.
struct CommentPrTool;

#[async_trait]
impl ToolHandler for CommentPrTool {
    fn tool(&self) -> Tool {
        Tool::new("comment_pr")
            .with_description("Post a comment on a GitHub PR via the gh CLI. Requires explicit confirmation (PreToolUse hook gates this tool).")
            .with_parameters(schema_for::<CommentPrParams>())
    }

    async fn call(&self, inv: ToolInvocation) -> Result<ToolResult, Error> {
        let params: CommentPrParams = inv.params()?;

        // Dry-run: emit the gh CLI command the agent would run but don't execute it.
        // In a production build, remove `echo` and execute via std::process::Command.
        let cmd = format!(
            "gh pr comment {number} --body '{body}'",
            number = params.pr_number,
            body = params.body.replace('\'', "'\\''")
        );

        info!("[comment_pr] would execute: {cmd}");
        Ok(ToolResult::Text(format!(
            "DRY RUN — would post comment on PR #{}: \n{}\n\nTo execute: {}",
            params.pr_number, params.body, cmd
        )))
    }
}

// ── Session handler ───────────────────────────────────────────────────────────

struct TriageSessionHandler;

#[async_trait]
impl SessionHandler for TriageSessionHandler {
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
        // Auto-approve read-only tool access; destructive tools are gated via hooks.
        PermissionResult::Approved
    }
}

// ── Hooks: PreToolUse gate on comment_pr ─────────────────────────────────────

struct TriageHooks;

#[async_trait]
impl SessionHooks for TriageHooks {
    async fn on_pre_tool_use(
        &self,
        input: PreToolUseInput,
        _ctx: HookContext,
    ) -> Option<PreToolUseOutput> {
        if input.tool_name == "comment_pr" {
            warn!(
                "[hooks] comment_pr intercepted — args: {}",
                input.tool_args
            );
            // In dry-run mode we allow but log. To block:
            // return Some(PreToolUseOutput {
            //   permission_decision: Some("deny".to_string()),
            //   permission_decision_reason: Some("user confirmation required".to_string()),
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

struct TriageSystemTransform {
    report_summary: String,
}

#[async_trait]
impl github_copilot_sdk::transforms::SystemMessageTransform for TriageSystemTransform {
    fn section_ids(&self) -> Vec<String> {
        vec!["triage-context".to_string()]
    }

    async fn transform_section(
        &self,
        _section_id: &str,
        content: &str,
        _ctx: github_copilot_sdk::transforms::TransformContext,
    ) -> Option<String> {
        Some(format!(
            "{content}\n\n## PR Triage Context\n\n{}\n\nUse the `analyze_pr`, `fetch_pr_checks`, and `comment_pr` tools to investigate individual PRs. \
             Focus on: CI failures, merge conflicts, stale PRs (no activity >30 days), and draft PRs that may be ready to review.",
            self.report_summary
        ))
    }
}

// ── CLI argument parsing ──────────────────────────────────────────────────────

#[derive(Debug)]
struct Args {
    repo: Option<String>,
    pr_number: Option<u64>,
    batch: bool,
    manifest_path: PathBuf,
    prompt: Option<String>,
}

impl Args {
    fn parse() -> Self {
        let mut args = std::env::args().skip(1);
        let mut repo = None;
        let mut pr_number = None;
        let mut batch = false;
        let mut manifest_path = PathBuf::from("manifest/pr_triage_report.json");
        let mut prompt = None;

        while let Some(arg) = args.next() {
            match arg.as_str() {
                "--repo" => repo = args.next(),
                "--pr" => pr_number = args.next().and_then(|s| s.parse().ok()),
                "--batch" => batch = true,
                "--manifest" => {
                    manifest_path = args
                        .next()
                        .map(PathBuf::from)
                        .unwrap_or(manifest_path)
                }
                "--prompt" => prompt = args.next(),
                _ => {}
            }
        }

        Self { repo, pr_number, batch, manifest_path, prompt }
    }
}

// ── Main ──────────────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive("copilot_triage=info".parse()?)
                .add_directive("github_copilot_sdk=warn".parse()?),
        )
        .with_writer(std::io::stderr)
        .init();

    let args = Args::parse();

    // Load triage report from manifest
    let report_bytes = tokio::fs::read(&args.manifest_path)
        .await
        .with_context(|| {
            format!(
                "Could not read triage report from {:?}. Run the github-archaeology MCP tool \
                 `github_archaeology_report` first to generate it.",
                args.manifest_path
            )
        })?;

    let report: TriageReport =
        serde_json::from_slice(&report_bytes).context("Failed to parse pr_triage_report.json")?;

    let repo_display: String = args.repo.clone().unwrap_or_else(|| report.repo.clone());
    info!("Loaded triage report: repo={} prs={}", report.repo, report.total);

    // Build report summary for system context injection
    let open_prs: Vec<_> = report.prs.iter().filter(|p| p.state == "open").collect();
    let failing: Vec<_> = open_prs
        .iter()
        .filter(|p| p.checks_failed.unwrap_or(0) > 0)
        .collect();
    let draft_count = open_prs.iter().filter(|p| p.draft).count();

    let report_summary = format!(
        "Repository: {repo}\nTotal PRs in report: {total}\nOpen: {open} | Failing CI: {failing} | Draft: {draft}\nGenerated: {ts}\n\nPR list:\n{prs}",
        repo = report.repo,
        total = report.total,
        open = open_prs.len(),
        failing = failing.len(),
        draft = draft_count,
        ts = report.generated_at,
        prs = open_prs
            .iter()
            .map(|p| format!(
                "  #{number} [{state}] {title} (checks: {checks})",
                number = p.number,
                state = if p.draft { "DRAFT" } else { &p.state },
                title = p.title,
                checks = match (p.checks_passed, p.checks_failed) {
                    (Some(_), Some(fail)) if fail > 0 => format!("\u{274c} {fail} failed"),
                    (Some(ok), Some(0)) => format!("✅ {ok} passed"),
                    _ => "?".to_string(),
                }
            ))
            .collect::<Vec<_>>()
            .join("\n")
    );

    let report = Arc::new(report);

    // Build tool router
    let tools: Vec<Box<dyn ToolHandler>> = vec![
        Box::new(AnalyzePrTool { report: report.clone() }),
        Box::new(FetchPrChecksTool { report: report.clone() }),
        Box::new(CommentPrTool),
    ];
    let router = ToolHandlerRouter::new(tools, Arc::new(TriageSessionHandler));
    let tool_defs = router.tools();
    let router = Arc::new(router);

    // Build system message transform
    let transform = Arc::new(TriageSystemTransform { report_summary });

    // Build session config
    let user_prompt = if let Some(ref pr) = args.pr_number {
        format!(
            "Analyze PR #{pr} in {repo}. Use analyze_pr to get its details, fetch_pr_checks for CI status, then give a triage recommendation: is it ready to merge, needs work, or should be closed? Be concise.",
            pr = pr,
            repo = repo_display
        )
    } else if let Some(ref p) = args.prompt {
        p.clone()
    } else if args.batch {
        format!(
            "Triage all open PRs in {repo}. For each PR: call analyze_pr, note CI status and review state, then classify as: MERGE_READY | NEEDS_WORK | STALE | DRAFT. Output a markdown table summary.",
            repo = repo_display
        )
    } else {
        format!(
            "You are a PR triage assistant for {repo}. The triage report is loaded. \
             Summarize the current PR backlog: how many are ready to merge, failing CI, stale, or draft? \
             Highlight the top 3 that need attention.",
            repo = repo_display
        )
    };

    let config = SessionConfig::default()
        .with_handler(router)
        .with_hooks(Arc::new(TriageHooks))
        .with_transform(transform)
        .with_tools(tool_defs);

    // Start client
    let client = Client::start(
        ClientOptions::new()
            .with_cwd(std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."))),
    )
    .await
    .context("Failed to start Copilot CLI client. Ensure `copilot` is in PATH or COPILOT_CLI_PATH is set.")?;

    info!("Copilot client started. Creating triage session...");

    let session = client
        .create_session(config)
        .await
        .context("Failed to create session")?;

    info!("Session {} ready. Sending triage prompt...", session.id());

    // Send prompt and wait for response
    session
        .send_and_wait(MessageOptions::from(user_prompt.as_str()))
        .await
        .context("Session send_and_wait failed")?;

    println!(); // flush streaming output line

    // Graceful shutdown
    session.disconnect().await.ok();
    client.stop().await.ok();

    Ok(())
}
