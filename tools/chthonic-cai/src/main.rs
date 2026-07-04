// @SID: TOOL_CHTHONIC_CAI_V1
// @Type: Gamification / TUI
// Chthonic AI — gamified Copilot CLI companion.
// Wraps `gh copilot suggest/explain` with a live XP prompt rendered via crossterm.

mod trail;
mod xp;

use anyhow::Result;
use clap::Parser;
use crossterm::{
    execute,
    style::{Color, Print, ResetColor, SetForegroundColor},
    terminal::SetTitle,
};
use std::io::{self, Write};
use std::process::Command;

#[derive(Parser, Debug)]
#[command(
    name = "cai",
    about = "Chthonic AI — gamified Copilot CLI companion\n\nWraps `gh copilot suggest/explain` with live XP tracking.",
    long_about = None
)]
struct Args {
    /// Explain mode — uses `gh copilot explain` instead of suggest
    #[arg(short = 'e', long)]
    explain: bool,

    /// Suggest target: shell | gh | git  (default: shell)
    #[arg(short = 't', long, default_value = "shell")]
    target: String,

    /// Override trail directory path
    #[arg(long)]
    trail: Option<String>,
}

fn main() -> Result<()> {
    // ── Windows: enable UTF-8 on stdout and stdin ──────────────────────────────
    // crossterm handles ANSI/VT on Win10+, but code-page must be set explicitly
    // for emoji/box-drawing to reach the console buffer correctly.
    #[cfg(windows)]
    unsafe {
        unsafe extern "system" {
            fn SetConsoleOutputCP(cp: u32) -> i32;
            fn SetConsoleCP(cp: u32) -> i32;
        }
        SetConsoleOutputCP(65001);
        SetConsoleCP(65001);
    }

    let args = Args::parse();

    // Resolve trail dir from arg or default (~/chthonic-archive/.chthonic/trail)
    let trail_dir = if let Some(p) = args.trail {
        std::path::PathBuf::from(p)
    } else {
        let home = std::env::var("USERPROFILE")
            .or_else(|_| std::env::var("HOME"))
            .unwrap_or_default();
        std::path::PathBuf::from(home)
            .join("chthonic-archive")
            .join(".chthonic")
            .join("trail")
    };
    let state_file = trail_dir
        .parent()
        .map(|p| p.join("xp-state.json"))
        .unwrap_or_else(|| trail_dir.join("..").join("xp-state.json"));

    // Initial XP snapshot
    let events = xp::read_trail(&trail_dir).unwrap_or_default();
    let start_xp = xp::compute_xp(&events);
    let start_lv = xp::level(start_xp);

    let mut stdout = io::stdout();

    // Set title bar + print header
    let _ = execute!(
        stdout,
        SetTitle(format!(
            "[Lv.{} {} | {} XP] Chthonic ◈",
            start_lv,
            xp::level_title(start_lv),
            start_xp
        ))
    );

    writeln!(stdout)?;
    let _ = execute!(
        stdout,
        SetForegroundColor(Color::DarkCyan),
        Print(format!(
            "  [cai] mode:{}  target:{}  |  type 'exit' to return\n\n",
            if args.explain { "explain" } else { "suggest" },
            args.target
        )),
        ResetColor
    );
    stdout.flush()?;

    let mut turn: u32 = 0;

    loop {
        // Recompute XP for live prompt (cheap — just reads NDJSON files)
        let ev = xp::read_trail(&trail_dir).unwrap_or_default();
        let xp_now = xp::compute_xp(&ev);
        let lv_now = xp::level(xp_now);
        let title_now = xp::level_title(lv_now);
        let bar_now = xp::xp_bar(xp_now, lv_now);

        // Update window title live
        let _ = execute!(
            stdout,
            SetTitle(format!(
                "[Lv.{} {} | {} XP] Chthonic ◈",
                lv_now, title_now, xp_now
            ))
        );

        // Render prompt line
        let _ = execute!(stdout, SetForegroundColor(Color::Green));
        write!(stdout, "  [Lv.{} {}|{}XP] ", lv_now, title_now, xp_now)?;
        let _ = execute!(stdout, SetForegroundColor(Color::DarkGreen));
        write!(stdout, "{} ", bar_now)?;
        let _ = execute!(stdout, SetForegroundColor(Color::White));
        write!(stdout, "◈ ")?;
        let _ = execute!(stdout, ResetColor);
        stdout.flush()?;

        // Read input
        let mut line = String::new();
        io::stdin().read_line(&mut line)?;
        let query = line.trim().to_string();

        if query.is_empty() || matches!(query.as_str(), "exit" | "quit" | "q") {
            break;
        }

        // Write query trail event (earns XP on next recompute)
        let _ = trail::write_event(
            &trail_dir,
            "diagnostic",
            "cai-query",
            3,
            &format!("cai: {}", &query[..query.len().min(80)]),
        );

        writeln!(stdout)?;

        // Dispatch to gh copilot
        let result = if args.explain {
            Command::new("gh.exe")
                .args(["copilot", "explain", &query])
                .status()
        } else {
            Command::new("gh.exe")
                .args(["copilot", "suggest", "-t", &args.target, &query])
                .status()
        };

        if let Err(e) = result {
            let _ = execute!(
                stdout,
                SetForegroundColor(Color::Red),
                Print(format!("  [cai] error: {e}\n")),
                ResetColor
            );
        }

        // Write response artifact event + persist state
        let _ = trail::write_event(
            &trail_dir,
            "artifact",
            "cai-response",
            3,
            &format!("cai turn {} response", turn + 1),
        );
        let _ = xp::persist_state(&state_file, &trail_dir);

        turn += 1;
        writeln!(stdout)?;
    }

    // ── Session summary ────────────────────────────────────────────────────────
    let final_ev = xp::read_trail(&trail_dir).unwrap_or_default();
    let final_xp = xp::compute_xp(&final_ev);
    let final_lv = xp::level(final_xp);
    let delta = final_xp as i64 - start_xp as i64;

    let _ = xp::persist_state(&state_file, &trail_dir);
    let _ = execute!(
        stdout,
        SetTitle(format!(
            "[Lv.{} {} | {} XP] Chthonic ◈",
            final_lv,
            xp::level_title(final_lv),
            final_xp
        ))
    );

    writeln!(stdout)?;
    let _ = execute!(
        stdout,
        SetForegroundColor(Color::DarkCyan),
        Print(format!(
            "  [cai] {} turn{} | +{} XP this session\n",
            turn,
            if turn == 1 { "" } else { "s" },
            delta
        )),
        ResetColor
    );
    xp::print_status(&mut stdout, final_xp)?;
    writeln!(stdout)?;

    Ok(())
}
