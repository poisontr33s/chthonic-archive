pub mod cold;
pub mod event;
pub mod granite;
pub mod hot;

use std::fs;
use std::path::{Path, PathBuf};

use anyhow::{Context, Result, bail};
use chrono::Utc;
use clap::{Args, Subcommand};

/// Detect the trail directory by walking up from `start` until `.chthonic`
/// is found, then returning `.chthonic/trail`. Falls back to `$HOME/.chthonic/trail`.
fn find_trail_dir(start: &Path) -> Result<PathBuf> {
    let mut dir = start.to_path_buf();
    loop {
        let candidate = dir.join(".chthonic");
        if candidate.is_dir() {
            return Ok(candidate.join("trail"));
        }
        if !dir.pop() {
            break;
        }
    }

    // Fallback: $HOME/.chthonic/trail
    let home = std::env::var("USERPROFILE")
        .or_else(|_| std::env::var("HOME"))
        .context("could not determine home directory (USERPROFILE / HOME)")?;

    let fallback = PathBuf::from(home).join(".chthonic").join("trail");
    if fallback.parent().map_or(false, |p| p.exists()) {
        Ok(fallback)
    } else {
        bail!(
            "no .chthonic directory found above {} and home fallback {} does not exist",
            start.display(),
            fallback.display()
        );
    }
}

/// Resolve the trail directory: use an explicit override or auto-detect.
fn resolve_trail_dir() -> Result<PathBuf> {
    let cwd = std::env::current_dir().context("getting current directory")?;
    find_trail_dir(&cwd)
}

fn today() -> String {
    Utc::now().format("%Y-%m-%d").to_string()
}

// ── Clap structures ──────────────────────────────────────────────────

#[derive(Debug, Args)]
pub struct TrailArgs {
    #[command(subcommand)]
    pub command: TrailCommand,
}

#[derive(Debug, Subcommand)]
pub enum TrailCommand {
    /// Append a new event to today's hot trail.
    Append {
        /// Event type (diagnostic, decision, artifact, snapshot, meta, memory, recovery).
        #[arg(long, rename_all = "verbatim")]
        r#type: String,

        /// Event sub-kind.
        #[arg(long)]
        kind: String,

        /// Human-readable message.
        #[arg(long)]
        msg: String,

        /// Priority: 1=critical, 2=important, 3=informational.
        #[arg(long, default_value_t = 2)]
        p: u8,

        /// Source file this event relates to.
        #[arg(long)]
        file: Option<String>,

        /// Arbitrary JSON object to attach.
        #[arg(long)]
        data: Option<String>,
    },

    /// List events from a hot trail file.
    List {
        /// Date to list (YYYY-MM-DD). Defaults to today.
        #[arg(long)]
        date: Option<String>,

        /// Filter by event type.
        #[arg(long, rename_all = "verbatim")]
        r#type: Option<String>,

        /// Filter by priority.
        #[arg(long)]
        p: Option<u8>,
    },

    /// Verify all lines in a hot trail file are valid NDJSON + schema.
    Verify {
        /// Date to verify (YYYY-MM-DD). Defaults to today.
        #[arg(long)]
        date: Option<String>,
    },

    /// Compress hot → cold (gzip), with round-trip verification.
    Forge {
        /// Date to forge (YYYY-MM-DD). Defaults to today.
        #[arg(long)]
        date: Option<String>,
    },

    /// Compile a cold archive into a .runestone binary stone.
    Stone {
        /// Date to stone (YYYY-MM-DD). Defaults to today.
        #[arg(long)]
        date: Option<String>,

        /// Overwrite an existing stone. Stones are immutable by default.
        #[arg(long, default_value_t = false)]
        force: bool,
    },

    /// Query/inspect a .runestone binary stone.
    Query {
        /// Path to the .runestone file.
        stone: std::path::PathBuf,
    },

    /// Initialize the .chthonic/ directory structure in the current repo root.
    Init,
}

/// Dispatch a trail subcommand.
pub fn run(args: TrailArgs) -> Result<()> {
    let trail_dir = resolve_trail_dir()?;

    match args.command {
        TrailCommand::Append {
            r#type,
            kind,
            msg,
            p,
            file,
            data,
        } => hot::append(
            &trail_dir,
            &r#type,
            &kind,
            &msg,
            p,
            file.as_deref(),
            data.as_deref(),
        ),

        TrailCommand::List { date, r#type, p } => {
            let d = date.unwrap_or_else(today);
            hot::list(&trail_dir, &d, r#type.as_deref(), p)
        }

        TrailCommand::Verify { date } => {
            let d = date.unwrap_or_else(today);
            // Verify hot file; if a cold file also exists, verify that too.
            hot::verify(&trail_dir, &d)?;
            let cold = cold::cold_path(&trail_dir, &d);
            if cold.exists() {
                cold::verify_cold(&trail_dir, &d)?;
            }
            Ok(())
        }

        TrailCommand::Forge { date } => {
            let d = date.unwrap_or_else(today);
            cold::forge(&trail_dir, &d)
        }

        TrailCommand::Stone { date, force } => {
            let d = date.unwrap_or_else(today);
            granite::compile(&trail_dir, &d, force)
        }

        TrailCommand::Query { stone } => {
            granite::query(&stone)
        }

        TrailCommand::Init => {
            let cwd = std::env::current_dir().context("getting current directory")?;
            // Walk up to find an existing .chthonic; otherwise create in cwd.
            let chthonic = {
                let mut dir = cwd.clone();
                loop {
                    let c = dir.join(".chthonic");
                    if c.is_dir() { break c; }
                    if !dir.pop() { break cwd.join(".chthonic"); }
                }
            };
            let trail_d = chthonic.join("trail");
            let stones_d = chthonic.join("stones");
            fs::create_dir_all(&trail_d)
                .with_context(|| format!("creating {}", trail_d.display()))?;
            fs::create_dir_all(&stones_d)
                .with_context(|| format!("creating {}", stones_d.display()))?;
            eprintln!("initialized .chthonic/ → {}", chthonic.display());
            eprintln!("  trail:  {}", trail_d.display());
            eprintln!("  stones: {}", stones_d.display());
            Ok(())
        }
    }
}
