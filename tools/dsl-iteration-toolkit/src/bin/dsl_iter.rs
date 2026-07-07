// dsl-iter CLI — invoke the toolkit's methodology against a project.

use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use dsl_iteration_toolkit::{Checkpoint, Config, IterationChecker, Ledger};
use std::path::PathBuf;
use std::process::ExitCode;

#[derive(Parser)]
#[command(name = "dsl-iter", about = "Generalized PEG-DSL iteration toolkit", version)]
struct Cli {
    /// Path to dsl-iter.toml config (default: ./dsl-iter.toml).
    #[arg(short, long, global = true, default_value = "dsl-iter.toml")]
    config: PathBuf,

    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    /// Run pattern catalog test + coverage + ledger append.
    Check {
        /// Don't actually write to the ledger (dry-run).
        #[arg(long)]
        dry_run: bool,
    },
    /// Show the last N ledger rows.
    History {
        #[arg(long, default_value_t = 5)]
        last: usize,
    },
    /// Initialize a new dsl-iter.toml in the current directory.
    Init {
        project_name: String,
    },
    /// Show the toolkit's known surfaces (paren, bold, backtick, ...).
    Surfaces,
    /// List checkpoints (snapshots taken before stateful ops).
    CheckpointList,
    /// Show a checkpoint's manifest in detail.
    CheckpointShow { id: String },
    /// Revert state to a checkpoint (default: most recent).
    Revert {
        /// Specific checkpoint id (from `dsl-iter checkpoint-list`).
        #[arg(long)]
        to: Option<String>,
        /// Confirm the revert without prompting.
        #[arg(short, long)]
        yes: bool,
    },
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let result = match cli.cmd {
        Cmd::Check { dry_run } => cmd_check(&cli.config, dry_run),
        Cmd::History { last } => cmd_history(&cli.config, last),
        Cmd::Init { project_name } => cmd_init(&cli.config, &project_name),
        Cmd::Surfaces => cmd_surfaces(),
        Cmd::CheckpointList => cmd_checkpoint_list(&cli.config),
        Cmd::CheckpointShow { id } => cmd_checkpoint_show(&cli.config, &id),
        Cmd::Revert { to, yes } => cmd_revert(&cli.config, to.as_deref(), yes),
    };
    match result {
        Ok(code) => code,
        Err(e) => {
            eprintln!("[dsl-iter] FATAL: {e:?}");
            ExitCode::from(2)
        }
    }
}

fn cmd_check(config_path: &PathBuf, dry_run: bool) -> Result<ExitCode> {
    let checker = IterationChecker::from_config_path(config_path)?;
    let report = checker.check()?;
    println!("[dsl-iter] grammar_hash={} patterns={}/{} surfaces={}",
        report.grammar_hash,
        report.pattern_results.iter().filter(|(_, r)| matches!(r, dsl_iteration_toolkit::PatternResult::Pass)).count(),
        report.pattern_results.len(),
        report.coverage_reports.len(),
    );
    for cov in &report.coverage_reports {
        println!("  [{}] coverage {}/{} = {:.2}%",
            cov.surface, cov.matched_correctly_count, cov.total_occurrences, cov.coverage_pct);
    }
    println!("[dsl-iter] checkpoint: {}", report.checkpoint_id);
    if !report.regressions.is_empty() {
        for r in &report.regressions {
            println!("  ! REGRESSION: {}", r.describe());
        }
        println!("[dsl-iter] To roll back this run: dsl-iter revert --to {}", report.checkpoint_id);
        return Ok(ExitCode::from(1));
    } else if report.is_duplicate_of_last {
        println!("[dsl-iter] no change vs prior ledger row — not appended");
    } else if dry_run {
        println!("[dsl-iter] dry-run — ledger NOT updated");
    } else {
        println!("[dsl-iter] ledger row appended");
    }
    Ok(ExitCode::from(0))
}

fn manifest_dir_from_config(config_path: &PathBuf) -> Result<(Config, PathBuf, PathBuf)> {
    let config = Config::load(config_path)?;
    let config_dir = config_path.parent().unwrap_or_else(|| std::path::Path::new(".")).to_path_buf();
    let manifest_dir = if config.manifest_dir.is_absolute() {
        config.manifest_dir.clone()
    } else {
        config_dir.join(&config.manifest_dir)
    };
    Ok((config, config_dir, manifest_dir))
}

fn cmd_checkpoint_list(config_path: &PathBuf) -> Result<ExitCode> {
    let (_, _, manifest_dir) = manifest_dir_from_config(config_path)?;
    let checkpoint = Checkpoint::new(&manifest_dir);
    let all = checkpoint.list()?;
    if all.is_empty() {
        println!("[dsl-iter] no checkpoints found in {}", manifest_dir.join(".checkpoints").display());
        return Ok(ExitCode::from(0));
    }
    println!("[dsl-iter] {} checkpoint(s), newest first:", all.len());
    for m in &all {
        println!("  {}  reason={}  files={}  grammar={}",
            m.id, m.reason, m.files.len(),
            m.grammar_hash.as_deref().unwrap_or("(none)"));
    }
    Ok(ExitCode::from(0))
}

fn cmd_checkpoint_show(config_path: &PathBuf, id: &str) -> Result<ExitCode> {
    let (_, _, manifest_dir) = manifest_dir_from_config(config_path)?;
    let checkpoint = Checkpoint::new(&manifest_dir);
    let m = checkpoint.load(id)?;
    println!("{}", serde_json::to_string_pretty(&m)?);
    Ok(ExitCode::from(0))
}

fn cmd_revert(config_path: &PathBuf, to: Option<&str>, yes: bool) -> Result<ExitCode> {
    let (_, _, manifest_dir) = manifest_dir_from_config(config_path)?;
    let checkpoint = Checkpoint::new(&manifest_dir);
    let all = checkpoint.list()?;
    if all.is_empty() {
        eprintln!("[dsl-iter] no checkpoints to revert to.");
        return Ok(ExitCode::from(1));
    }
    let target = match to {
        Some(id) => checkpoint.load(id)?,
        None => all[0].clone(),  // most recent
    };
    println!("[dsl-iter] will restore checkpoint: {}  (reason={}, created={})",
        target.id, target.reason, target.created_at);
    println!("           files to restore: {}", target.files.len());
    for f in &target.files {
        let action = if f.was_missing { "DELETE (was missing at checkpoint)" } else { "RESTORE" };
        println!("             {} {}", action, f.original_path.display());
    }
    if !yes {
        use std::io::Write;
        print!("[dsl-iter] confirm (y/N): ");
        std::io::stdout().flush()?;
        let mut s = String::new();
        std::io::stdin().read_line(&mut s)?;
        if !s.trim().eq_ignore_ascii_case("y") {
            println!("[dsl-iter] cancelled.");
            return Ok(ExitCode::from(0));
        }
    }
    checkpoint.restore(&target.id)?;
    println!("[dsl-iter] restored.");
    Ok(ExitCode::from(0))
}

fn cmd_history(config_path: &PathBuf, last: usize) -> Result<ExitCode> {
    let config = Config::load(config_path)?;
    let config_dir = config_path.parent().unwrap_or_else(|| std::path::Path::new(".")).to_path_buf();
    let manifest_dir = if config.manifest_dir.is_absolute() {
        config.manifest_dir.clone()
    } else {
        config_dir.join(&config.manifest_dir)
    };
    let ledger_path = manifest_dir.join(format!("{}_iteration_history.ndjson", config.project_name));
    let ledger = Ledger::load(&ledger_path)?;
    let rows = ledger.rows();
    let start = rows.len().saturating_sub(last);
    for row in &rows[start..] {
        println!("{}", serde_json::to_string_pretty(row)?);
        println!("---");
    }
    Ok(ExitCode::from(0))
}

fn cmd_init(config_path: &PathBuf, project_name: &str) -> Result<ExitCode> {
    let cfg = Config::template(project_name);
    cfg.save(config_path).with_context(|| format!("write {}", config_path.display()))?;
    println!("[dsl-iter] wrote template config at {}", config_path.display());
    println!("Next: edit grammar_path / corpus_path / catalog_path to match your project.");
    Ok(ExitCode::from(0))
}

fn cmd_surfaces() -> Result<ExitCode> {
    println!("Known coverage surfaces:");
    println!("  paren     — (non-nested ...) constructs");
    println!("  bold      — **X** constructs (bold_parened_id vs bold_prose)");
    println!("  backtick  — `X` constructs (ticked_id / ticked_phrase / ticked_any)");
    println!("  fenced    — ```...``` code blocks (fenced_code_block)");
    println!("  (more surfaces: header — pending implementation)");
    Ok(ExitCode::from(0))
}
