// game-cli — CLI face for the game-core turn-contract kernel.
//
// State is persisted at .chthonic/game/active_run.json (auto-located by walking up from cwd).
// Commands:
//   game-cli new [--seed N]        — start a fresh run (default: time-based seed)
//   game-cli observe               — print current observation as JSON
//   game-cli act --dir N|S|E|W     — take one move action, print new observation
//   game-cli act --dir wait        — wait action
//   game-cli act --json '{"kind":"Move","dir":"East"}'  — raw Action JSON
//
// The observation JSON is the same structure both the agent (game_observe MCP tool)
// and the human face (cli-renderer) will read — one contract, two faces.

use game_core::{Action, Dir, GameState};
use std::fs;
use std::path::PathBuf;

// ── State file resolution ─────────────────────────────────────

fn state_path() -> PathBuf {
    let cwd = std::env::current_dir().expect("cwd");
    let mut dir = cwd.clone();
    loop {
        let candidate = dir.join(".chthonic");
        if candidate.is_dir() {
            return candidate.join("game").join("active_run.json");
        }
        if !dir.pop() {
            break;
        }
    }
    // Fallback: USERPROFILE / HOME
    let home = std::env::var("USERPROFILE")
        .or_else(|_| std::env::var("HOME"))
        .unwrap_or_else(|_| ".".into());
    PathBuf::from(home)
        .join(".chthonic")
        .join("game")
        .join("active_run.json")
}

fn load_state() -> GameState {
    let path = state_path();
    let json = fs::read_to_string(&path).unwrap_or_else(|e| {
        eprintln!("error: no active run at {} — {}", path.display(), e);
        eprintln!("  start one: game-cli new");
        std::process::exit(1);
    });
    serde_json::from_str(&json).unwrap_or_else(|e| {
        eprintln!("error: corrupt run state — {}", e);
        std::process::exit(1);
    })
}

fn save_state(state: &GameState) {
    let path = state_path();
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).unwrap_or_else(|e| {
            eprintln!("error: cannot create {}: {}", parent.display(), e);
            std::process::exit(1);
        });
    }
    let json = serde_json::to_string_pretty(state).expect("serialize");
    fs::write(&path, &json).unwrap_or_else(|e| {
        eprintln!("error: cannot write {}: {}", path.display(), e);
        std::process::exit(1);
    });
}

// ── arg parsing helpers ───────────────────────────────────────

fn flag_val<'a>(args: &'a [String], flag: &str) -> Option<&'a str> {
    args.iter()
        .position(|a| a == flag)
        .and_then(|i| args.get(i + 1))
        .map(String::as_str)
}

fn has_flag(args: &[String], flag: &str) -> bool {
    args.iter().any(|a| a == flag)
}

// ── main ──────────────────────────────────────────────────────

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let cmd = args.get(1).map(String::as_str).unwrap_or("help");

    match cmd {
        // ── new ──────────────────────────────────────────────
        "new" => {
            let seed: u64 = flag_val(&args, "--seed")
                .and_then(|s| s.parse().ok())
                .unwrap_or_else(|| {
                    std::time::SystemTime::now()
                        .duration_since(std::time::UNIX_EPOCH)
                        .unwrap_or_default()
                        .as_millis() as u64
                });
            let state = GameState::new(seed);
            save_state(&state);
            eprintln!("new run — seed={} state={}", seed, state_path().display());
            println!("{}", state.observe_json());
        }

        // ── observe ──────────────────────────────────────────
        "observe" => {
            let state = load_state();
            println!("{}", state.observe_json());
        }

        // ── act ──────────────────────────────────────────────
        "act" => {
            let mut state = load_state();

            let action: Action = if let Some(dir_str) = flag_val(&args, "--dir") {
                match dir_str.to_lowercase().as_str() {
                    "north" | "n" | "up" => Action::Move { dir: Dir::North },
                    "south" | "s" | "down" => Action::Move { dir: Dir::South },
                    "east" | "e" | "right" => Action::Move { dir: Dir::East },
                    "west" | "w" | "left" => Action::Move { dir: Dir::West },
                    "wait" => Action::Wait,
                    other => {
                        eprintln!(
                            "error: unknown dir '{}' (north/south/east/west/wait)",
                            other
                        );
                        std::process::exit(1);
                    }
                }
            } else if let Some(json_str) = flag_val(&args, "--json") {
                serde_json::from_str(json_str).unwrap_or_else(|e| {
                    eprintln!("error: invalid action JSON — {}", e);
                    std::process::exit(1);
                })
            } else if has_flag(&args, "wait") {
                // bare 'game-cli act wait' convenience alias
                Action::Wait
            } else {
                eprintln!("error: act requires --dir <dir> or --json <Action JSON>");
                std::process::exit(1);
            };

            state.step(action);
            save_state(&state);
            println!("{}", state.observe_json());
        }

        // ── help / unknown ────────────────────────────────────
        _ => {
            eprintln!(concat!(
                "game-cli — turn-contract kernel CLI\n",
                "usage:\n",
                "  game-cli new [--seed N]                     start a fresh run\n",
                "  game-cli observe                             print current board\n",
                "  game-cli act --dir north|south|east|west     move\n",
                "  game-cli act --dir wait                      wait one turn\n",
                "  game-cli act --json \x27{{\"kind\":\"Move\",\"dir\":\"East\"}}\x27  raw Action",
            ));
            if cmd != "help" {
                std::process::exit(1);
            }
        }
    }
}

