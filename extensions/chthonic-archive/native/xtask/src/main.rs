use std::env;
use std::path::{Path, PathBuf};
use std::process::{Command, ExitCode};

// ANSI colors
const CYAN: &str = "\x1b[36m";
const GREEN: &str = "\x1b[32m";
const YELLOW: &str = "\x1b[33m";
const RED: &str = "\x1b[31m";
const RESET: &str = "\x1b[0m";

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    let task = args.get(1).map(String::as_str).unwrap_or("help");

    match task {
        "verify" => verify_host(),
        "build" => build_workspace(&args[2..]),
        "build-daemon" => build_crate("chthonic-daemon", &args[2..]),
        "build-ledger" => build_crate("entropy-ledger-host", &args[2..]),
        _ => {
            eprintln!("xtask — Chthonic Archive build orchestrator");
            eprintln!();
            eprintln!("Usage: cargo xtask <task>");
            eprintln!();
            eprintln!("Tasks:");
            eprintln!("  verify        Run preflight host verification");
            eprintln!("  build         Build default workspace members (MAKEFLAGS-clean)");
            eprintln!("  build-daemon  Build chthonic-daemon only");
            eprintln!("  build-ledger  Build entropy-ledger-host only");
            ExitCode::from(1)
        }
    }
}

// ---------------------------------------------------------------------------
// Build tasks — sanitize environment before spawning cargo
// ---------------------------------------------------------------------------

fn build_workspace(extra_args: &[String]) -> ExitCode {
    let mut cmd = cargo_command();
    cmd.arg("build");
    cmd.args(extra_args);
    run_or_fail(cmd)
}

fn build_crate(name: &str, extra_args: &[String]) -> ExitCode {
    let mut cmd = cargo_command();
    cmd.args(["build", "-p", name]);
    cmd.args(extra_args);
    run_or_fail(cmd)
}

/// Create a `cargo` Command with environment sanitized:
/// - MAKEFLAGS/MFLAGS stripped (nmake crashes on GNU Make flags like -j12)
/// - cmake injected into PATH from VS Build Tools if not already available
fn cargo_command() -> Command {
    let mut cmd = Command::new("cargo");
    cmd.env_remove("MAKEFLAGS");
    cmd.env_remove("MFLAGS");

    // Ensure we run from the workspace root (parent of xtask/)
    if let Ok(manifest_dir) = env::var("CARGO_MANIFEST_DIR") {
        if let Some(workspace_root) = Path::new(&manifest_dir).parent() {
            cmd.current_dir(workspace_root);
        }
    }

    // If cmake isn't on PATH, inject the VS installation path
    if run_cmd(&["cmake", "--version"]).ok {
        return cmd;
    }
    if let Some(cmake_dir) = find_vs_cmake_dir() {
        let current_path = env::var("PATH").unwrap_or_default();
        let sep = if cfg!(windows) { ";" } else { ":" };
        let cmake_str = cmake_dir.to_string_lossy();
        if !current_path.to_lowercase().contains(&cmake_str.to_lowercase()) {
            cmd.env("PATH", format!("{cmake_str}{sep}{current_path}"));
            eprintln!("[xtask] injected cmake from VS: {cmake_str}");
        }
    }

    cmd
}

fn run_or_fail(mut cmd: Command) -> ExitCode {
    match cmd.status() {
        Ok(status) if status.success() => ExitCode::SUCCESS,
        Ok(status) => ExitCode::from(status.code().unwrap_or(1) as u8),
        Err(err) => {
            eprintln!("{RED}[xtask] failed to spawn cargo: {err}{RESET}");
            ExitCode::from(1)
        }
    }
}

// ---------------------------------------------------------------------------
// Verify host — replicate verify-host.ts checks in pure Rust
// ---------------------------------------------------------------------------

struct CheckResult {
    ok: bool,
    note: Option<String>,
}

fn verify_host() -> ExitCode {
    println!("{CYAN}[Chthonic] Running Oxidized Preflight Host Verification...{RESET}");

    let mut failed = false;

    // 1. Rust toolchain
    check("Rust Toolchain", || {
        probe_cmd(&["rustc", "--version"], None)
    }, "Install Rust via rustup: https://rustup.rs", false, &mut failed);

    // 2. WASM target
    check("WASM Target", || {
        let r = run_cmd(&["rustup", "target", "list", "--installed"]);
        if r.ok && r.note.as_deref().map_or(false, |s| s.contains("wasm32-unknown-unknown")) {
            CheckResult { ok: true, note: None }
        } else {
            // Attempt auto-fix
            let fix = run_cmd(&["rustup", "target", "add", "wasm32-unknown-unknown"]);
            if fix.ok {
                CheckResult { ok: true, note: Some("auto-installed".into()) }
            } else {
                CheckResult { ok: false, note: None }
            }
        }
    }, "Run: rustup target add wasm32-unknown-unknown", false, &mut failed);

    // 3. wasm-bindgen CLI
    check("wasm-bindgen CLI", || {
        probe_cmd(&["wasm-bindgen", "--version"], None)
    }, "Install: cargo install wasm-bindgen-cli", false, &mut failed);

    // 4. Perl (for OpenSSL build)
    check("Perl (OpenSSL build)", || {
        // First: check PATH perl
        let path_perl = run_cmd(&["perl", "--version"]);
        if path_perl.ok && !is_cygwin_perl(path_perl.note.as_deref().unwrap_or("")) {
            return CheckResult { ok: true, note: Some("using perl from PATH".into()) };
        }

        // Second: hunt for Ruby DevKit perl
        if let Some(devkit_perl) = find_devkit_perl() {
            CheckResult {
                ok: true,
                note: Some(format!("using Ruby DevKit perl: {}", devkit_perl.display())),
            }
        } else if path_perl.ok {
            // Cygwin perl is better than nothing
            CheckResult { ok: true, note: Some("using Cygwin perl (may fail for OpenSSL)".into()) }
        } else {
            CheckResult { ok: false, note: None }
        }
    }, "Install RubyInstaller with DevKit and run `ridk install 3`.", false, &mut failed);

    // 5. MAKEFLAGS hygiene
    check("MAKEFLAGS Hygiene", || {
        let makeflags = env::var("MAKEFLAGS").unwrap_or_default();
        let mflags = env::var("MFLAGS").unwrap_or_default();
        if makeflags.trim().is_empty() && mflags.trim().is_empty() {
            CheckResult { ok: true, note: Some("clean (no MAKEFLAGS/MFLAGS)".into()) }
        } else {
            CheckResult {
                ok: true,
                note: Some(format!(
                    "will sanitize at build time (MAKEFLAGS={makeflags}, MFLAGS={mflags})"
                )),
            }
        }
    }, "No action needed — xtask sanitizes MAKEFLAGS per process.", false, &mut failed);

    // 6. Solana CLI (warn only)
    check("Solana CLI", || {
        probe_cmd(&["solana", "--version"], None)
    }, "Install Solana Tool Suite for local validator mode.", true, &mut failed);

    // 7. Ruby Runtime (warn only)
    check("Ruby Runtime", || {
        let r = run_cmd(&["ruby", "--version"]);
        if r.ok {
            CheckResult { ok: true, note: r.note }
        } else {
            CheckResult { ok: false, note: None }
        }
    }, "Install Ruby dev toolchain (RubyInstaller + ridk).", true, &mut failed);

    // 8. cmake (for shaderc) — check PATH first, then VS Build Tools / VS Community
    check("cmake (shaderc build)", || {
        let path_cmake = run_cmd(&["cmake", "--version"]);
        if path_cmake.ok {
            return CheckResult {
                ok: true,
                note: Some(format!("on PATH: {}", path_cmake.note.unwrap_or_default())),
            };
        }

        // Hunt in VS installations
        if let Some(cmake_dir) = find_vs_cmake_dir() {
            let cmake_exe = cmake_dir.join("cmake.exe");
            let probe = run_cmd_path(&cmake_exe, &["--version"]);
            if probe.ok {
                return CheckResult {
                    ok: true,
                    note: Some(format!(
                        "VS: {} ({})",
                        probe.note.unwrap_or_default(),
                        cmake_dir.display()
                    )),
                };
            }
        }

        // Hunt in MSYS2
        for root in ["C:\\Ruby34-x64", "C:\\Ruby33-x64", "C:\\Ruby35-x64"] {
            let candidate = PathBuf::from(root)
                .join("msys64").join("ucrt64").join("bin").join("cmake.exe");
            if candidate.exists() {
                let probe = run_cmd_path(&candidate, &["--version"]);
                if probe.ok {
                    return CheckResult {
                        ok: true,
                        note: Some(format!(
                            "MSYS2: {} ({})",
                            probe.note.unwrap_or_default(),
                            candidate.display()
                        )),
                    };
                }
            }
        }

        CheckResult { ok: false, note: None }
    }, "Install cmake: VS Build Tools component, `winget install cmake`, or `pacman -S mingw-w64-ucrt-x86_64-cmake`.", false, &mut failed);

    println!();
    if failed {
        println!("{RED}[!] Host verification failed. Resolve the failing checks above.{RESET}");
        ExitCode::from(1)
    } else {
        println!("{GREEN}[+] Host verification passed. Ready for Oxidation.{RESET}");
        ExitCode::SUCCESS
    }
}

fn check(
    name: &str,
    f: impl FnOnce() -> CheckResult,
    fix_msg: &str,
    warn_only: bool,
    failed: &mut bool,
) {
    print!("Checking {name}... ");
    let result = f();
    if result.ok {
        println!("{GREEN}OK{RESET}");
        if let Some(note) = result.note {
            println!("  {note}");
        }
    } else if warn_only {
        println!("{YELLOW}WARN{RESET}");
        if let Some(note) = result.note {
            println!("  {note}");
        }
        println!("  {fix_msg}");
    } else {
        println!("{RED}FAILED{RESET}");
        if let Some(note) = result.note {
            println!("  {note}");
        }
        println!("  {fix_msg}");
        *failed = true;
    }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn probe_cmd(cmd: &[&str], _check: Option<&dyn Fn(&str) -> bool>) -> CheckResult {
    run_cmd(cmd)
}

fn run_cmd(cmd: &[&str]) -> CheckResult {
    match Command::new(cmd[0]).args(&cmd[1..]).output() {
        Ok(output) if output.status.success() => {
            let stdout = String::from_utf8_lossy(&output.stdout).to_string();
            CheckResult {
                ok: true,
                note: Some(stdout.lines().next().unwrap_or("").trim().to_string()),
            }
        }
        _ => CheckResult { ok: false, note: None },
    }
}

fn run_cmd_path(exe: &Path, args: &[&str]) -> CheckResult {
    match Command::new(exe).args(args).output() {
        Ok(output) if output.status.success() => {
            let stdout = String::from_utf8_lossy(&output.stdout).to_string();
            CheckResult {
                ok: true,
                note: Some(stdout.lines().next().unwrap_or("").trim().to_string()),
            }
        }
        _ => CheckResult { ok: false, note: None },
    }
}

/// Search Visual Studio installations for the bundled cmake.
/// Checks Build Tools, Community, Professional, Enterprise across:
///   - VS 2026 Insiders: `\18\Insiders`
///   - VS 2026 Stable:   `\18\Community` (or `\2026\Community`)
///   - VS 2022:          `\2022\Community`
fn find_vs_cmake_dir() -> Option<PathBuf> {
    let bases = [
        r"C:\Program Files\Microsoft Visual Studio",
        r"C:\Program Files (x86)\Microsoft Visual Studio",
    ];
    // VS uses internal version numbers (18) or marketing years (2022/2026)
    let version_dirs = ["18", "2026", "2022"];
    let editions = [
        "Insiders", "Preview", "BuildTools", "Community", "Professional", "Enterprise",
    ];
    let cmake_rel = r"Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin";

    for base in &bases {
        for ver in &version_dirs {
            for edition in &editions {
                let candidate = PathBuf::from(base)
                    .join(ver)
                    .join(edition)
                    .join(cmake_rel);
                if candidate.join("cmake.exe").exists() {
                    return Some(candidate);
                }
            }
        }
    }
    None
}

fn is_cygwin_perl(version_line: &str) -> bool {
    version_line.to_lowercase().contains("cygwin")
}

/// Search Ruby DevKit install locations for a native (non-Cygwin) perl.
fn find_devkit_perl() -> Option<PathBuf> {
    let mut roots: Vec<PathBuf> = Vec::new();

    // Dynamic: ask ruby for its install root
    if let Ok(output) = Command::new("ruby").args(["-e", "print RbConfig.ruby"]).output() {
        if output.status.success() {
            let exe = String::from_utf8_lossy(&output.stdout).trim().to_string();
            if let Some(root) = Path::new(&exe).parent().and_then(|p| p.parent()) {
                roots.push(root.to_path_buf());
            }
        }
    }

    // Static search roots
    for drive in ["C", "D"] {
        for ver in ["40", "35", "34", "33", "32"] {
            roots.push(PathBuf::from(format!("{drive}:\\Ruby{ver}-x64")));
        }
    }

    let perl_rel = ["msys64/ucrt64/bin/perl.exe", "msys64/usr/bin/perl.exe"];

    for root in &roots {
        for rel in &perl_rel {
            let candidate = root.join(rel);
            if candidate.exists() {
                // Verify it's not Cygwin
                if let Ok(out) = Command::new(&candidate).arg("--version").output() {
                    let version = String::from_utf8_lossy(&out.stdout);
                    if !is_cygwin_perl(&version) {
                        return Some(candidate);
                    }
                }
            }
        }
    }

    None
}
