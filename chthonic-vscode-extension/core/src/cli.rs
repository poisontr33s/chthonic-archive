use crate::agent::Agent;
use crate::protocol::ChatRequest;
use anyhow::{Context, Result};
use std::io::{self, Read, Write};

pub fn chat(prompt: Vec<String>, workspace: String) -> Result<()> {
    let text = if prompt.is_empty() {
        let mut input = String::new();
        io::stdin()
            .read_to_string(&mut input)
            .context("failed to read chat prompt from stdin")?;
        input
    } else {
        prompt.join(" ")
    };

    let agent = Agent::from_env()?;
    let request = ChatRequest { text, workspace };
    let mut stdout = io::stdout().lock();

    let plans = agent.stream_chat(&request, |delta| {
        stdout
            .write_all(delta.as_bytes())
            .context("failed to write chat delta")?;
        stdout.flush().context("failed to flush chat delta")
    })?;

    for plan in plans {
        writeln!(
            stdout,
            "\n[edit-plan] {} ({} edit{})",
            plan.summary,
            plan.edits.len(),
            if plan.edits.len() == 1 { "" } else { "s" }
        )
        .context("failed to write edit plan summary")?;
    }

    stdout
        .write_all(b"\n")
        .context("failed to finish chat output")
}
