// @SID: TOOL_CHTHONIC_COPILOT_BRIDGE_V1
// ============================================================
// chthonic-copilot-bridge — spawned by the chthonic-archive VS Code
// extension. Holds the Rust-side GitHub Copilot SDK client and a
// session loop; streams assistant output to stdout for the TS shell
// to consume.
//
// This first iteration is the Phase-3 smoke surface (per
// ~/.claude/plans/2-copilot-sdk-vogue-anchor.md): one-shot prompt
// execution, end-to-end through the official Copilot CLI. The richer
// JSON-RPC dispatch toward the TS shell lands in a follow-up
// iteration once this proves the bridge is wired.
//
// Modes:
//   --smoke              run a built-in canned prompt and exit (CI gate)
//   --prompt "<text>"    run the given prompt and exit
//   (no flags)           read a single prompt from stdin (line) and exit
//
// Auth: relies on `gh auth login` / COPILOT_CLI_PATH resolution
// performed by the SDK at Client::start time.
// ============================================================

use std::io::{self, BufRead, Write};
use std::sync::Arc;
use std::time::Duration;

use anyhow::{Context, Result};
use clap::Parser;
use github_copilot_sdk::handler::ApproveAllHandler;
use github_copilot_sdk::types::{MessageOptions, SessionConfig, SessionEvent};
use github_copilot_sdk::{Client, ClientOptions};
use tracing::info;

#[derive(Debug, Parser)]
#[command(
    name = "chthonic-copilot-bridge",
    about = "Chthonic bridge to the GitHub Copilot SDK",
)]
struct Args {
    /// Run a built-in canned prompt and exit. Used by the TS shell as a liveness check.
    #[arg(long)]
    smoke: bool,

    /// One-shot prompt to send. Mutually exclusive with --smoke.
    #[arg(long)]
    prompt: Option<String>,

    /// Override the request timeout (seconds) for the assistant reply.
    #[arg(long, default_value_t = 120)]
    timeout_secs: u64,
}

const SMOKE_PROMPT: &str = "Reply with exactly the string 'chthonic-copilot-bridge: ok' and nothing else.";

fn print_session_event(event: &SessionEvent) {
    match event.event_type.as_str() {
        "assistant.message_delta" => {
            let text = event
                .data
                .get("deltaContent")
                .and_then(|c| c.as_str())
                .unwrap_or("");
            print!("{text}");
            let _ = io::stdout().flush();
        }
        "assistant.message" => {
            println!();
        }
        "session.error" => {
            let msg = event
                .data
                .get("message")
                .and_then(|m| m.as_str())
                .unwrap_or("unknown error");
            eprintln!("[bridge.error] {msg}");
        }
        _ => {}
    }
}

fn read_stdin_prompt() -> Option<String> {
    let stdin = io::stdin();
    let mut line = String::new();
    stdin.lock().read_line(&mut line).ok()?;
    let trimmed = line.trim_end_matches(['\n', '\r']);
    if trimmed.is_empty() {
        None
    } else {
        Some(trimmed.to_string())
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new(
                    "chthonic_copilot_bridge=info,github_copilot_sdk=warn",
                )),
        )
        .with_writer(io::stderr)
        .init();

    let args = Args::parse();

    let prompt = match (args.smoke, args.prompt.as_deref()) {
        (true, Some(_)) => anyhow::bail!("--smoke and --prompt are mutually exclusive"),
        (true, None) => SMOKE_PROMPT.to_string(),
        (false, Some(p)) => p.to_string(),
        (false, None) => read_stdin_prompt()
            .context("No prompt supplied: pass --prompt or write one line to stdin")?,
    };

    info!("Starting Copilot client...");
    let client = Client::start(ClientOptions::default())
        .await
        .context(
            "Failed to start Copilot CLI client. \
             Ensure `copilot` is in PATH or COPILOT_CLI_PATH is set, \
             and `gh auth login` has been completed.",
        )?;

    let mut config = SessionConfig::default()
        .with_permission_handler(Arc::new(ApproveAllHandler));
    config.streaming = Some(true);

    let session = client
        .create_session(config)
        .await
        .context("Failed to create session")?;
    info!("Session {} ready.", session.id());

    let mut events = session.subscribe();
    let event_pump = tokio::spawn(async move {
        while let Ok(event) = events.recv().await {
            print_session_event(&event);
        }
    });

    session
        .send_and_wait(
            MessageOptions::from(prompt.as_str())
                .with_wait_timeout(Duration::from_secs(args.timeout_secs)),
        )
        .await
        .context("send_and_wait failed")?;

    // Best-effort flush: give the streamed deltas a moment to drain.
    let _ = tokio::time::timeout(Duration::from_millis(100), event_pump).await;
    let _ = io::stdout().flush();

    session.disconnect().await.ok();
    client.stop().await.ok();
    Ok(())
}
