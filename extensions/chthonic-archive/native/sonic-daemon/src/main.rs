// @SID: SONIC_DAEMON_MAIN_V1
//! sonic-daemon — WASAPI loopback capture for the Chthonic Archive sonic loop.
//!
//! Captures the *actual* system audio the user hears (cpal loopback on the default
//! output device), reduces it to a rolling window of derived scalars, and writes an
//! atomic snapshot to `<workspace>/manifest/sonic_window.json`. The MCP `sonic_read`
//! tool reads that file at turn start — capture (continuous) and reads (discrete, at
//! turn boundaries) are fully decoupled by the file.
//!
//! Privacy: only derived scalars (energy, …) are ever written — never raw audio.
//!   SONIC_CAPTURE=off  → write a `disabled` window and exit (kill-switch).
//!   SONIC_WINDOW_SECS  → rolling window length (default 5).
//!   SONIC_SNAPSHOT_MS  → snapshot cadence (default 1000).
//!
//! Reaping: reads stdin to EOF on a side thread. When the spawning MCP supervisor
//! dies and closes our stdin, EOF flips the stop flag and the daemon exits cleanly
//! (mirrors how `chthonic-daemon` is owned by its parent).
//!
//! Usage: `sonic-daemon [workspace_root]`  (workspace_root defaults to cwd)

mod capture;

use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

use anyhow::Result;

use crate::capture::{run_capture, CaptureConfig};

fn main() -> Result<()> {
    let workspace = std::env::args()
        .nth(1)
        .map(PathBuf::from)
        .unwrap_or_else(|| std::env::current_dir().unwrap_or_else(|_| PathBuf::from(".")));

    // One-shot diagnostic: enumerate render endpoints + their audio sessions, then exit.
    if env_truthy("SONIC_DIAG") {
        return crate::capture::run_diagnostics();
    }

    let cfg = CaptureConfig::from_env(workspace);

    // Kill-switch: don't even open the audio device.
    if !cfg.enabled {
        let _ = cfg.write_disabled();
        eprintln!("[sonic] capture disabled via SONIC_CAPTURE=off — wrote disabled window, exiting");
        return Ok(());
    }

    let stop = Arc::new(AtomicBool::new(false));

    // Reap-on-stdin is for the supervised case only: the MCP server spawns us with a
    // stdin pipe and sets SONIC_REAP_ON_STDIN=1, so closing that pipe ends us. Standalone
    // runs (no flag) ignore stdin and stop on Ctrl+C / process kill instead — otherwise a
    // closed/null stdin under a non-interactive shell would exit us immediately.
    if env_truthy("SONIC_REAP_ON_STDIN") {
        spawn_stdin_eof_watcher(Arc::clone(&stop));
    }

    run_capture(cfg, stop)
}

fn env_truthy(key: &str) -> bool {
    std::env::var(key)
        .map(|v| matches!(v.trim().to_ascii_lowercase().as_str(), "1" | "true" | "yes" | "on"))
        .unwrap_or(false)
}

/// Read stdin to EOF on a background thread; signal stop when the pipe closes.
/// This is the reap path — the MCP supervisor ends us by closing our stdin.
fn spawn_stdin_eof_watcher(stop: Arc<AtomicBool>) {
    std::thread::spawn(move || {
        use std::io::Read;
        let mut buf = [0u8; 256];
        let mut stdin = std::io::stdin();
        loop {
            match stdin.read(&mut buf) {
                Ok(0) | Err(_) => break, // EOF or error → parent gone
                Ok(_) => {}              // ignore any input bytes
            }
        }
        stop.store(true, Ordering::Release);
    });
}
