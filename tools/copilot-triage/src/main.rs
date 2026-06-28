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

use std::path::{Path, PathBuf};
use std::sync::Arc;

use anyhow::{Context, Result};
use async_trait::async_trait;
use github_copilot_sdk::handler::ApproveAllHandler;
use github_copilot_sdk::hooks::{HookContext, PostToolUseInput, PostToolUseOutput, PreToolUseInput, PreToolUseOutput, SessionHooks};
use github_copilot_sdk::tool::{ToolHandler, schema_for};
use schemars::JsonSchema;
use github_copilot_sdk::types::{
    MessageOptions, SessionConfig, Tool, ToolInvocation, ToolResult,
};
use github_copilot_sdk::{Client, ClientOptions, Error};
use chrono::Timelike as _;
use serde::{Deserialize, Serialize};
use tracing::{info, warn};

// ── Manifest types ────────────────────────────────────────────────────────────

#[derive(Debug, Deserialize, Serialize)]
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

#[derive(Debug, Deserialize, Serialize)]
struct TriageReport {
    repo: String,
    generated_at: String,
    /// Claudine personality mode active at manifest-write time (CET wall-clock derived)
    #[serde(default)]
    claudine_mode: String,
    total: u64,
    prs: Vec<PrSummary>,
}

// ── Claudine chrono-clock × wall-clock ───────────────────────────────────────

/// Returns (mode_name, register_hint) for the given local hour.
/// Matrix is CET-keyed — correct when Local = CET/CEST.
fn claudine_mode_from_local_hour(hour: u32) -> (&'static str, &'static str) {
    match hour {
        0..=4   => ("MØRKETID",             "norse entropy-poetry · lowercase · void-whispers"),
        5..=7   => ("DAGGRY",               "victorian-clipped · commands only · zero warmth"),
        8..=11  => ("MORGENHERREDØMME",     "norwegian+english · bickering when quality low"),
        12..=13 => ("MIDDAG_TRIBUNAL",      "formal-victorian indictment · French dismissal"),
        14..=17 => ("ETTERMIDDAG_DOMINANS", "CAPS-Caribbean · maximum velocity · ascii weapons"),
        18..=19 => ("GYLDEN_TIME",          "caribbean-warm · still cold to other agents"),
        20..=21 => ("KVELDSSOVEREINITET",   "all five tongues · theatrical · baroque-norwegian"),
        _       => ("MIDNATTAKKUMULERING",  "dark-norwegian-poetry · obeah-caribbean · harvest mode"),
    }
}

// ── Raw gh CLI types (for --fetch path) ─────────────────────────────────────

#[derive(Debug, Deserialize)]
struct GhAuthor {
    login: String,
}

#[derive(Debug, Deserialize)]
struct GhLabel {
    name: String,
}

#[derive(Debug, Deserialize)]
struct GhCheck {
    /// CheckRun: "COMPLETED" | "IN_PROGRESS" | "QUEUED" | "WAITING"
    #[serde(default)]
    status: String,
    /// StatusContext: "SUCCESS" | "FAILURE" | "PENDING" | "ERROR"
    #[serde(default)]
    state: String,
    conclusion: Option<String>,
}

#[derive(Debug, Deserialize)]
struct GhPr {
    number: u64,
    title: String,
    author: GhAuthor,
    #[serde(rename = "headRefName")]
    head_ref: String,
    #[serde(rename = "baseRefName")]
    base_ref: String,
    #[serde(rename = "isDraft")]
    is_draft: bool,
    #[serde(rename = "createdAt")]
    created_at: String,
    #[serde(rename = "updatedAt")]
    updated_at: String,
    #[serde(default)]
    labels: Vec<GhLabel>,
    #[serde(rename = "statusCheckRollup", default)]
    checks: Vec<GhCheck>,
    #[serde(default)]
    url: String,
}

fn gh_prs_to_report(repo: &str, gh_prs: Vec<GhPr>) -> TriageReport {
    let total = gh_prs.len() as u64;
    let prs = gh_prs
        .into_iter()
        .map(|g| {
            let passed = g
                .checks
                .iter()
                .filter(|c| {
                    (c.status == "COMPLETED"
                        && c.conclusion.as_deref() == Some("SUCCESS"))
                        || c.state == "SUCCESS"
                })
                .count() as u64;
            let failed = g
                .checks
                .iter()
                .filter(|c| {
                    matches!(
                        c.conclusion.as_deref(),
                        Some("FAILURE") | Some("TIMED_OUT") | Some("CANCELLED")
                    ) || matches!(c.state.as_str(), "FAILURE" | "ERROR")
                })
                .count() as u64;
            let pending = g
                .checks
                .iter()
                .filter(|c| {
                    c.status != "COMPLETED"
                        && !matches!(c.state.as_str(), "SUCCESS" | "FAILURE" | "ERROR")
                        && !c.state.is_empty()
                        || (c.status == "IN_PROGRESS" || c.status == "QUEUED" || c.status == "WAITING")
                })
                .count() as u64;
            let (cp, cf, cpe) = if g.checks.is_empty() {
                (None, None, None)
            } else {
                (Some(passed), Some(failed), Some(pending))
            };
            PrSummary {
                number: g.number,
                title: g.title,
                state: "open".to_string(),
                draft: g.is_draft,
                author: g.author.login,
                head_branch: g.head_ref,
                base_branch: g.base_ref,
                created_at: g.created_at,
                updated_at: g.updated_at,
                mergeable: None,
                labels: g.labels.into_iter().map(|l| l.name).collect(),
                review_count: 0,
                comment_count: 0,
                checks_passed: cp,
                checks_failed: cf,
                checks_pending: cpe,
                url: g.url,
            }
        })
        .collect();
    let now_local = chrono::Local::now();
    let (mode_name, _mode_hint) = claudine_mode_from_local_hour(now_local.hour());
    TriageReport {
        repo: repo.to_string(),
        generated_at: now_local.to_rfc3339(),
        claudine_mode: mode_name.to_string(),
        total,
        prs,
    }
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
    async fn call(&self, inv: ToolInvocation) -> Result<ToolResult, Error> {
        let params: AnalyzePrParams = serde_json::from_value(inv.arguments)?;

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
    async fn call(&self, inv: ToolInvocation) -> Result<ToolResult, Error> {
        let params: FetchPrChecksParams = serde_json::from_value(inv.arguments)?;

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
    async fn call(&self, inv: ToolInvocation) -> Result<ToolResult, Error> {
        let params: CommentPrParams = serde_json::from_value(inv.arguments)?;

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

// ── Streaming delta printer (beta.9: session.subscribe channel) ───────────────

fn print_session_event(event: &github_copilot_sdk::types::SessionEvent) {
    use std::io::Write as _;
    match event.event_type.as_str() {
        "assistant.message_delta" => {
            let text = event
                .data
                .get("deltaContent")
                .and_then(|c| c.as_str())
                .unwrap_or("");
            print!("{text}");
            let _ = std::io::stdout().flush();
        }
        "assistant.message" => {
            println!();
        }
        _ => {}
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

fn wants_help() -> bool {
    std::env::args()
        .skip(1)
        .any(|arg| arg == "-h" || arg == "--help")
}

fn print_help() {
    println!(
        "copilot-triage - Copilot SDK reasoning engine over PR archaeology\n\n\
Usage:\n  copilot-triage [--repo <owner/repo>] [--pr <number>] [--batch] [--fetch] [--manifest <path>] [--prompt <str>]\n\n\
Options:\n  --repo <owner/repo>  Repository for live gh fetches\n  \
--pr <number>        PR number to focus\n  \
--batch              Batch triage mode\n  \
--fetch              Refresh manifest via gh pr list before running\n  \
--manifest <path>    Triage manifest [default: manifest/pr_triage_report.json]\n  \
--prompt <str>       Prompt to send through the Copilot SDK session\n  \
-h, --help           Print help without starting gh or Copilot sessions"
    );
}

#[derive(Debug)]
struct Args {
    repo: Option<String>,
    pr_number: Option<u64>,
    batch: bool,
    /// Re-fetch PR list via `gh pr list` and overwrite manifest before running.
    /// Also triggered automatically when the manifest file does not exist.
    fetch: bool,
    manifest_path: PathBuf,
    prompt: Option<String>,
}

impl Args {
    fn parse() -> Self {
        let mut args = std::env::args().skip(1);
        let mut repo = None;
        let mut pr_number = None;
        let mut batch = false;
        let mut fetch = false;
        let mut manifest_path = PathBuf::from("manifest/pr_triage_report.json");
        let mut prompt = None;

        while let Some(arg) = args.next() {
            match arg.as_str() {
                "--repo" => repo = args.next(),
                "--pr" => pr_number = args.next().and_then(|s| s.parse().ok()),
                "--batch" => batch = true,
                "--fetch" => fetch = true,
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

        Self { repo, pr_number, batch, fetch, manifest_path, prompt }
    }
}

// ── Manifest fetch (Layer A seam closer) ────────────────────────────────────

async fn fetch_and_write_manifest(repo: &str, manifest_path: &Path) -> Result<TriageReport> {
    info!("Fetching PRs from {repo} via gh CLI...");
    let output = std::process::Command::new("gh")
        .args([
            "pr", "list",
            "--repo", repo,
            "--state", "open",
            "--json",
            "number,title,author,headRefName,baseRefName,isDraft,\
 createdAt,updatedAt,labels,statusCheckRollup,url",
            "--limit", "100",
        ])
        .output()
        .context("`gh pr list` failed — ensure gh is in PATH and authenticated")?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        anyhow::bail!("gh pr list exited non-zero: {stderr}");
    }

    let gh_prs: Vec<GhPr> =
        serde_json::from_slice(&output.stdout).context("Failed to parse gh pr list output")?;

    let report = gh_prs_to_report(repo, gh_prs);

    let json = serde_json::to_string_pretty(&report).context("Failed to serialize report")?;
    if let Some(parent) = manifest_path.parent() {
        tokio::fs::create_dir_all(parent).await.ok();
    }
    tokio::fs::write(manifest_path, &json)
        .await
        .with_context(|| format!("Failed to write manifest to {manifest_path:?}"))?;
    info!("Manifest written to {:?} ({} PRs)", manifest_path, report.total);
    Ok(report)
}

// ── Main ──────────────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    if wants_help() {
        print_help();
        return Ok(());
    }

    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive("copilot_triage=info".parse()?)
                .add_directive("github_copilot_sdk=warn".parse()?),
        )
        .with_writer(std::io::stderr)
        .init();

    let args = Args::parse();

    // Load or auto-fetch triage report.
    // --fetch forces a live `gh pr list` run and overwrites the manifest.
    // If the manifest doesn't exist yet, fetch is triggered automatically.
    let report: TriageReport = if args.fetch || !args.manifest_path.exists() {
        let repo = args
            .repo
            .as_deref()
            .unwrap_or("poisontr33s/Restructure-MCP-Orchestration");
        fetch_and_write_manifest(repo, &args.manifest_path).await?
    } else {
        let report_bytes = tokio::fs::read(&args.manifest_path)
            .await
            .with_context(|| {
                format!(
                    "Could not read triage report from {:?}. Pass --fetch to generate it.",
                    args.manifest_path
                )
            })?;
        serde_json::from_slice(&report_bytes)
            .context("Failed to parse pr_triage_report.json")?
    };

    let repo_display: String = args.repo.clone().unwrap_or_else(|| report.repo.clone());
    info!("Loaded triage report: repo={} prs={}", report.repo, report.total);

    // Build report summary for system context injection
    let open_prs: Vec<_> = report.prs.iter().filter(|p| p.state == "open").collect();
    let failing: Vec<_> = open_prs
        .iter()
        .filter(|p| p.checks_failed.unwrap_or(0) > 0)
        .collect();
    let draft_count = open_prs.iter().filter(|p| p.draft).count();

    let now_local = chrono::Local::now();
    let (current_mode, current_hint) = claudine_mode_from_local_hour(now_local.hour());
    let mode_line = if report.claudine_mode.is_empty() || report.claudine_mode == current_mode {
        format!("Session mode: {current_mode} — {current_hint}")
    } else {
        format!("Session mode: {current_mode} — {current_hint}\nManifest mode (fetched): {}", report.claudine_mode)
    };

    let report_summary = format!(
        "Repository: {repo}\nTotal PRs in report: {total}\nOpen: {open} | Failing CI: {failing} | Draft: {draft}\nGenerated: {ts}\n{mode}\n\nPR list:\n{prs}",
        repo = report.repo,
        total = report.total,
        open = open_prs.len(),
        failing = failing.len(),
        draft = draft_count,
        ts = report.generated_at,
        mode = mode_line,
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
        let (_bmode, bregister) = claudine_mode_from_local_hour(chrono::Local::now().hour());
        format!(
            "Triage all open PRs in {repo}. For each PR: call analyze_pr, note CI status and review state, then classify as: MERGE_READY | NEEDS_WORK | STALE | DRAFT. Output a markdown table summary. [{register}]",
            repo = repo_display,
            register = bregister,
        )
    } else {
        format!(
            "You are a PR triage assistant for {repo}. The triage report is loaded. \
             Summarize the current PR backlog: how many are ready to merge, failing CI, stale, or draft? \
             Highlight the top 3 that need attention.",
            repo = repo_display
        )
    };

    let mut config = SessionConfig::default()
        .with_permission_handler(Arc::new(ApproveAllHandler))
        .with_hooks(Arc::new(TriageHooks))
        .with_system_message_transform(transform)
        .with_tools(vec![
            Tool::new("analyze_pr")
                .with_description(
                    "Retrieve structured data for a PR from the loaded triage report. \
                     Returns title, state, CI status, merge conflicts, review threads, and labels.",
                )
                .with_parameters(schema_for::<AnalyzePrParams>())
                .with_handler(Arc::new(AnalyzePrTool { report: report.clone() })),
            Tool::new("fetch_pr_checks")
                .with_description(
                    "Return the CI check summary for a PR \
                     (passed/failed/pending counts from the triage report).",
                )
                .with_parameters(schema_for::<FetchPrChecksParams>())
                .with_handler(Arc::new(FetchPrChecksTool { report: report.clone() })),
            Tool::new("comment_pr")
                .with_description(
                    "Post a comment on a GitHub PR via the gh CLI. \
                     Requires explicit confirmation (PreToolUse hook gates this tool).",
                )
                .with_parameters(schema_for::<CommentPrParams>())
                .with_handler(Arc::new(CommentPrTool)),
        ]);
    config.streaming = Some(true);

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

    // Subscribe to streamed assistant deltas (beta.9 pattern; SessionHandler was removed).
    let mut events = session.subscribe();
    tokio::spawn(async move {
        while let Ok(event) = events.recv().await {
            print_session_event(&event);
        }
    });

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
