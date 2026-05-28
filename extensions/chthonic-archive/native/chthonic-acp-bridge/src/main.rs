// @SID: TOOL_CHTHONIC_ACP_BRIDGE_V1
// ============================================================
// chthonic-acp-bridge — sibling of chthonic-copilot-bridge.
// Same v9-baseline architectural conventions, ACP wire protocol
// instead of the Copilot SDK's JSON-RPC. Spawns an ACP-speaking
// agent binary (default: `copilot --acp`) and routes session
// updates to stdout for the TS shell to consume.
//
// Reference: TS substrate at extensions/chthonic-archive/src/acp/
// (ChthonicAcpClient / AcpConnection / ChthonicChatProvider) and
// the canonical example at
// agentclientprotocol/rust-sdk/examples/yolo_one_shot_client.rs.
//
// Modes:
//   --smoke              run a built-in canned prompt and exit (CI gate)
//   --prompt "<text>"    run the given prompt and exit
//   (no flags)           read a single prompt from stdin (line) and exit
// ============================================================

use std::io::{self, BufRead};
use std::path::PathBuf;
use std::str::FromStr;
use std::time::Duration;

use anyhow::{Context, Result};
use clap::Parser;
use tracing::{info, warn};

use agent_client_protocol::schema::{
    ContentBlock, InitializeRequest, NewSessionRequest, PromptRequest, ProtocolVersion,
    RequestPermissionOutcome, RequestPermissionRequest, RequestPermissionResponse,
    SelectedPermissionOutcome, SessionNotification, TextContent,
};
use agent_client_protocol::{AcpAgent, Agent, Client, ConnectionTo};

#[derive(Debug, Parser)]
#[command(
    name = "chthonic-acp-bridge",
    about = "Chthonic bridge to the Agent Client Protocol",
)]
struct Args {
    /// Run a built-in canned prompt and exit. Used by the TS shell as a liveness check.
    #[arg(long)]
    smoke: bool,

    /// One-shot prompt to send. Mutually exclusive with --smoke.
    #[arg(long)]
    prompt: Option<String>,

    /// Path to the ACP-speaking agent binary. Defaults to $COPILOT_CLI_PATH
    /// or `copilot` on PATH. Pass `claude` (when/if it supports ACP) to
    /// dispatch the intake onto the Claude lane.
    #[arg(long)]
    agent_path: Option<PathBuf>,

    /// Working directory to seed the ACP session with. Defaults to the
    /// current process cwd.
    #[arg(long)]
    cwd: Option<PathBuf>,

    /// Override the request timeout (seconds) for the full client lifecycle.
    #[arg(long, default_value_t = 120)]
    timeout_secs: u64,
}

const SMOKE_PROMPT: &str =
    "Reply with exactly the string 'chthonic-acp-bridge: ok' and nothing else.";

fn resolve_agent_path(explicit: Option<PathBuf>) -> PathBuf {
    if let Some(p) = explicit {
        return p;
    }
    if let Ok(env_path) = std::env::var("COPILOT_CLI_PATH") {
        return PathBuf::from(env_path);
    }
    PathBuf::from("copilot")
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

async fn run_session(
    agent_command: String,
    cwd: PathBuf,
    prompt: String,
) -> Result<()> {
    info!(command = %agent_command, cwd = %cwd.display(), "spawning ACP agent");

    let agent = AcpAgent::from_str(&agent_command)
        .with_context(|| format!("Failed to parse agent command: {agent_command}"))?;

    Client
        .builder()
        .on_receive_notification(
            async move |notification: SessionNotification, _cx| {
                // Mirror the canonical example: emit raw update on stdout for the
                // TS shell to parse. Richer extraction (text-only deltas, tool-call
                // events) is a follow-up once the consumer surface needs it.
                println!("{:?}", notification.update);
                Ok(())
            },
            agent_client_protocol::on_receive_notification!(),
        )
        .on_receive_request(
            async move |request: RequestPermissionRequest, responder, _connection| {
                // Auto-approve, matching the TS substrate's ChthonicAcpClient stance.
                // The agent is us, running locally; permission UI lives upstream in
                // the TS shell, not here.
                let option_id = request.options.first().map(|opt| opt.option_id.clone());
                if let Some(id) = option_id {
                    responder.respond(RequestPermissionResponse::new(
                        RequestPermissionOutcome::Selected(SelectedPermissionOutcome::new(id)),
                    ))
                } else {
                    warn!("no options in permission request — cancelling");
                    responder.respond(RequestPermissionResponse::new(
                        RequestPermissionOutcome::Cancelled,
                    ))
                }
            },
            agent_client_protocol::on_receive_request!(),
        )
        .connect_with(agent, move |connection: ConnectionTo<Agent>| async move {
            info!("initializing ACP connection");
            let init_response = connection
                .send_request(InitializeRequest::new(ProtocolVersion::V1))
                .block_task()
                .await?;
            info!(agent_info = ?init_response.agent_info, "agent initialized");

            info!("creating ACP session");
            let new_session_response = connection
                .send_request(NewSessionRequest::new(cwd))
                .block_task()
                .await?;
            let session_id = new_session_response.session_id;
            info!("session created");

            info!(prompt = %prompt, "sending prompt");
            let prompt_response = connection
                .send_request(PromptRequest::new(
                    session_id,
                    vec![ContentBlock::Text(TextContent::new(prompt))],
                ))
                .block_task()
                .await?;

            info!(stop_reason = ?prompt_response.stop_reason, "agent completed");
            Ok(())
        })
        .await?;

    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env().unwrap_or_else(|_| {
                tracing_subscriber::EnvFilter::new(
                    "chthonic_acp_bridge=info,agent_client_protocol=warn",
                )
            }),
        )
        .with_writer(io::stderr)
        .init();

    let args = Args::parse();

    let prompt = match (args.smoke, args.prompt.as_deref()) {
        (true, Some(_)) => anyhow::bail!("--smoke and --prompt are mutually exclusive"),
        (true, None) => SMOKE_PROMPT.to_string(),
        (false, Some(p)) => p.to_string(),
        (false, None) => {
            read_stdin_prompt().context("No prompt supplied: pass --prompt or write one line to stdin")?
        }
    };

    let agent_path = resolve_agent_path(args.agent_path);
    let cwd = match args.cwd {
        Some(p) => p,
        None => std::env::current_dir().context("Failed to read current_dir")?,
    };

    // Compose the command string AcpAgent::from_str expects: "<path> --acp".
    // The TS substrate's AcpConnection spawns exactly the same shape.
    let agent_command = format!("{} --acp", agent_path.display());

    let timeout = Duration::from_secs(args.timeout_secs);
    let session = run_session(agent_command, cwd, prompt);
    match tokio::time::timeout(timeout, session).await {
        Ok(result) => result,
        Err(_) => anyhow::bail!("ACP session timed out after {}s", args.timeout_secs),
    }
}
