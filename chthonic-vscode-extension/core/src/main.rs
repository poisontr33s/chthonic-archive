mod agent;
mod cli;
mod edit_plan;
mod permissions;
mod plan_parser;
mod protocol;
mod provider;
mod rollback_store;
mod rpc;
mod session;
mod snippet_store;
mod workspace_graph;

use anyhow::Result;
use clap::{Parser, Subcommand};

#[derive(Debug, Parser)]
#[command(name = "deepseek-core")]
#[command(version, about = "Rust-native Chthonic coding agent core")]
struct Args {
    #[command(subcommand)]
    command: Option<Command>,
}

#[derive(Debug, Subcommand)]
enum Command {
    /// Run JSON-RPC over stdin/stdout for the VS Code bridge.
    Rpc,
    /// Run a terminal-native chat request.
    Chat {
        /// Prompt text. If omitted, stdin is consumed.
        prompt: Vec<String>,
        /// Workspace label/path included in context.
        #[arg(long, default_value = "terminal")]
        workspace: String,
    },
}

fn main() -> Result<()> {
    let args = Args::parse();

    match args.command.unwrap_or(Command::Rpc) {
        Command::Rpc => rpc::run(),
        Command::Chat { prompt, workspace } => cli::chat(prompt, workspace),
    }
}
