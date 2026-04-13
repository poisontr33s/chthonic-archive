mod trail;

use std::path::PathBuf;

use anyhow::Result;
use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(
    name = "ankh-forge",
    version,
    about = "Rust-native WPTG acceleration CLI",
    arg_required_else_help = true
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Produce a Phase 0 extension universe scan.
    Scan {
        #[arg(long, default_value = ".")]
        root: PathBuf,
        #[arg(long)]
        output: Option<PathBuf>,
    },
    /// Produce a Part 1-style filetype census.
    Census {
        #[arg(long, default_value = ".")]
        root: PathBuf,
        #[arg(long)]
        output: Option<PathBuf>,
    },
    /// Classify one file's extension intelligence and pathway.
    Audit {
        path: PathBuf,
        #[arg(long, default_value = ".")]
        root: PathBuf,
        #[arg(long)]
        output: Option<PathBuf>,
    },
    /// Suggest a transmutation pathway for an extension.
    Pathway { extension: String },
    /// Syntax-validate a file where the target runtime is available.
    Validate { path: PathBuf },
    /// Emit the oxidized tooling landscape as JSON.
    Landscape {
        #[arg(long, default_value = ".")]
        root: PathBuf,
        #[arg(long)]
        output: Option<PathBuf>,
    },
    /// Check installed runtime versions against endoflife.date.
    Eol {
        #[arg(long)]
        output: Option<PathBuf>,
    },
    /// Inspect a binary header and suggest extractable intelligence.
    Forensics { path: PathBuf },
    /// Runestone Execution Model — typed event trail (hot/cold/granite).
    Trail(trail::TrailArgs),
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Scan { root, output } => {
            ankh_forge::emit_json(ankh_forge::scan_command(&root)?, output)?;
        }
        Commands::Census { root, output } => {
            ankh_forge::emit_json(ankh_forge::census_command(&root)?, output)?;
        }
        Commands::Audit { path, root, output } => {
            ankh_forge::emit_json(ankh_forge::audit_command(&root, &path)?, output)?;
        }
        Commands::Pathway { extension } => {
            ankh_forge::emit_json(ankh_forge::pathway_command(&extension), None)?;
        }
        Commands::Validate { path } => {
            ankh_forge::emit_json(ankh_forge::validate_command(&path), None)?;
        }
        Commands::Landscape { root, output } => {
            ankh_forge::emit_json(ankh_forge::landscape_command(&root)?, output)?;
        }
        Commands::Eol { output } => {
            ankh_forge::emit_json(ankh_forge::eol_command()?, output)?;
        }
        Commands::Forensics { path } => {
            ankh_forge::emit_json(ankh_forge::forensics_command(&path)?, None)?;
        }
        Commands::Trail(args) => {
            trail::run(args)?;
        }
    }

    Ok(())
}
