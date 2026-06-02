// @SID: SEED_SLICE_V1
// The anchor slice — four rungs in one shot:
//   GROUND:        .chthonic/ankh_seeds.yaml      → one BCE principle
//   COMPUTE:       manifest/sonic_window.json      → one live sonic value
//   RENDER:        ANSI iso diamond tinted by energy × phase hue
//   LOADED STATE:  .chthonic/trail/YYYY-MM-DD.cold.ndjson → forge → runestone
//
// Usage:
//   cargo run --bin seed_slice -- [<repo_root>] [--seed <label>]
//   (repo_root defaults to "." i.e. run from chthonic-archive root)
//
// After running, forge the runestone:
//   cargo run -p ankh-forge -- trail forge
//
// The trail event appended here will be included in the next forge cycle.

use std::{
    fs,
    io::Write,
    path::{Path, PathBuf},
    time::{SystemTime, UNIX_EPOCH},
};

use serde::Deserialize;

// ── Seed types ───────────────────────────────────────────────────────────────

#[derive(Deserialize)]
struct SeedFile {
    #[serde(default)]
    andean_bce: Vec<Seed>,
    #[serde(default)]
    egyptologic_bce: Vec<Seed>,
}

#[derive(Deserialize)]
struct Seed {
    label: String,
    principle: String,
    #[serde(default)]
    weight: f32,
    #[serde(default)]
    resonance_terms: Vec<String>,
}

// ── Sonic window (schema v1) ──────────────────────────────────────────────────

#[derive(Deserialize, Default)]
struct SonicWindow {
    energy:     Option<f32>,
    silent:     Option<bool>,
    brightness: Option<f32>,
    tonality:   Option<f32>,
    voiceness:  Option<f32>,
}

// ── Colour ────────────────────────────────────────────────────────────────────

/// HSV → RGB. h in [0, 360), s/v in [0, 1].
fn hsv_to_rgb(h: f32, s: f32, v: f32) -> (u8, u8, u8) {
    let h = h.rem_euclid(360.0);
    let c = v * s;
    let x = c * (1.0 - ((h / 60.0) % 2.0 - 1.0).abs());
    let m = v - c;
    let (r1, g1, b1) = match (h / 60.0) as u32 {
        0 => (c, x, 0.0_f32),
        1 => (x, c, 0.0),
        2 => (0.0, c, x),
        3 => (0.0, x, c),
        4 => (x, 0.0, c),
        _ => (c, 0.0, x),
    };
    (
        ((r1 + m) * 255.0).round() as u8,
        ((g1 + m) * 255.0).round() as u8,
        ((b1 + m) * 255.0).round() as u8,
    )
}

// ── Isometric render ──────────────────────────────────────────────────────────

fn render_iso_entity(seed: &Seed, energy: f32, brightness: f32, seed_idx: usize) {
    // Phase hue: 30° per seed slot (same radial distribution as cli-renderer TAG_PHASE)
    let hue        = (seed_idx as f32 * 30.0).rem_euclid(360.0);
    // Luminance driven by sonic energy; floor at 0.25 so it's readable at silence
    let val        = 0.25 + energy.clamp(0.0, 1.0) * 0.75;
    // Saturation driven by brightness; dark rooms are grey, bright rooms are vivid
    let sat        = 0.45 + brightness.clamp(0.0, 1.0) * 0.55;
    let (r, g, b)  = hsv_to_rgb(hue, sat, val);
    let ansi_fg    = format!("\x1b[38;2;{r};{g};{b}m");
    let ansi_reset = "\x1b[0m";
    let ansi_bold  = "\x1b[1m";
    let ansi_dim   = "\x1b[2m";

    // Isometric diamond: 7 rows — 1, 3, 5, 7, 5, 3, 1 cells
    // Each cell is "◆ " (diamond + space) to give the iso perspective feel.
    const WIDTHS: &[usize] = &[1, 3, 5, 7, 5, 3, 1];
    // Left-pad so centre column aligns at column 8
    const PADS:   &[usize] = &[6, 5, 4, 3, 4, 5, 6];

    println!();
    println!("  {ansi_bold}{}{ansi_reset}", seed.label);
    let excerpt = if seed.principle.len() > 72 {
        &seed.principle[..72]
    } else {
        &seed.principle
    };
    println!("  {ansi_dim}{excerpt}…{ansi_reset}");
    println!();

    for (&width, &pad) in WIDTHS.iter().zip(PADS.iter()) {
        let indent: String = " ".repeat(pad);
        let cells: String  = std::iter::repeat_n("◆ ", width).collect();
        println!("  {indent}{ansi_fg}{cells}{ansi_reset}");
    }

    println!();

    // Energy bar (20 cells)
    let bar_filled = (energy.clamp(0.0, 1.0) * 20.0).round() as usize;
    let bar: String = std::iter::repeat_n('█', bar_filled)
        .chain(std::iter::repeat_n('░', 20 - bar_filled))
        .collect();
    println!(
        "  energy   {ansi_fg}{bar}{ansi_reset}  {:.2}",
        energy
    );

    // Resonance terms (first five)
    if !seed.resonance_terms.is_empty() {
        let terms: Vec<&str> = seed.resonance_terms.iter()
            .take(5)
            .map(String::as_str)
            .collect();
        println!("  resonance {ansi_dim}{}{ansi_reset}", terms.join(" · "));
    }

    println!(
        "  hue={hue:.0}°  sat={sat:.2}  val={val:.2}  weight={}",
        if seed.weight > 0.0 { seed.weight } else { 1.0 }
    );
    println!();
}

// ── Time helpers (no external deps) ──────────────────────────────────────────

fn epoch_to_parts(s: u64) -> (u32, u32, u32, u32, u32, u32) {
    let sec = (s % 60) as u32;
    let s   = s / 60;
    let min = (s % 60) as u32;
    let s   = s / 60;
    let hr  = (s % 24) as u32;
    let days = s / 24;
    // Civil Gregorian algorithm
    let z   = days + 719_468;
    let era = z / 146_097;
    let doe = z - era * 146_097;
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146_096) / 365;
    let y   = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp  = (5 * doy + 2) / 153;
    let d   = doy - (153 * mp + 2) / 5 + 1;
    let mo  = if mp < 10 { mp + 3 } else { mp - 9 };
    let y   = if mo <= 2 { y + 1 } else { y };
    (y as u32, mo as u32, d as u32, hr, min, sec)
}

fn now_rfc3339() -> String {
    let s = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    let (y, mo, d, h, mi, sec) = epoch_to_parts(s);
    format!("{y:04}-{mo:02}-{d:02}T{h:02}:{mi:02}:{sec:02}Z")
}

fn today_str() -> String {
    let s = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    let (y, mo, d, _, _, _) = epoch_to_parts(s);
    format!("{y:04}-{mo:02}-{d:02}")
}

// ── Trail append ──────────────────────────────────────────────────────────────

fn append_trail_event(repo_root: &Path, seed: &Seed, energy: f32, brightness: f32, hue: f32) -> PathBuf {
    let trail_dir = repo_root.join(".chthonic").join("trail");
    let _ = fs::create_dir_all(&trail_dir);
    let cold_path = trail_dir.join(format!("{}.hot.ndjson", today_str()));

    let event = serde_json::json!({
        "type": "artifact",
        "kind": "seed_render",
        "at": now_rfc3339(),
        "p": 1,
        "msg": format!(
            "seed_slice/v1: {} — energy={:.3} brightness={:.3} hue={:.0}°",
            seed.label, energy, brightness, hue
        ),
        "data": {
            "seed_label": seed.label,
            "principle_excerpt": &seed.principle[..seed.principle.len().min(140)],
            "resonance_terms": seed.resonance_terms.iter().take(8).collect::<Vec<_>>(),
            "energy": energy,
            "brightness": brightness,
            "hue_deg": hue,
            "source": "seed_slice/v1",
            "slice": "cli-renderer draws one ankh_seed as iso entity tinted by sonic energy"
        }
    });

    let mut line = event.to_string();
    line.push('\n');

    match fs::OpenOptions::new().create(true).append(true).open(&cold_path) {
        Ok(mut f) => {
            let _ = f.write_all(line.as_bytes());
        }
        Err(e) => {
            eprintln!("[seed_slice] warn: could not write trail event: {e}");
        }
    }

    cold_path
}

// ── Main ──────────────────────────────────────────────────────────────────────

fn main() {
    let args: Vec<String> = std::env::args().collect();

    // Parse --seed <label> and optional positional repo_root
    let mut repo_root = PathBuf::from(".");
    let mut seed_label: Option<String> = None;
    let mut i = 1;
    while i < args.len() {
        if args[i] == "--seed" && i + 1 < args.len() {
            seed_label = Some(args[i + 1].clone());
            i += 2;
        } else if !args[i].starts_with("--") {
            repo_root = PathBuf::from(&args[i]);
            i += 1;
        } else {
            i += 1;
        }
    }

    // ── 1. Load ankh_seeds ────────────────────────────────────────────────────
    let seeds_path = repo_root.join(".chthonic").join("ankh_seeds.yaml");
    let seeds_raw = match fs::read_to_string(&seeds_path) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("[seed_slice] cannot read {}: {e}", seeds_path.display());
            eprintln!("[seed_slice] run from the chthonic-archive root or pass repo root as arg");
            std::process::exit(1);
        }
    };
    let seed_file: SeedFile = match serde_yaml::from_str(&seeds_raw) {
        Ok(sf) => sf,
        Err(e) => {
            eprintln!("[seed_slice] yaml parse error: {e}");
            std::process::exit(1);
        }
    };

    // All seeds: andean first (preserves 50/50 cultural balance at selection)
    let all_seeds: Vec<&Seed> = seed_file.andean_bce.iter()
        .chain(seed_file.egyptologic_bce.iter())
        .collect();

    if all_seeds.is_empty() {
        eprintln!("[seed_slice] no seeds found in {}", seeds_path.display());
        std::process::exit(1);
    }

    let (seed_idx, seed) = match seed_label {
        Some(ref label) => {
            match all_seeds.iter().enumerate().find(|(_, s)| &s.label == label) {
                Some((idx, s)) => (idx, *s),
                None => {
                    eprintln!("[seed_slice] seed '{label}' not found");
                    eprintln!("[seed_slice] available: {}",
                        all_seeds.iter().map(|s| s.label.as_str()).collect::<Vec<_>>().join(", "));
                    std::process::exit(1);
                }
            }
        }
        None => (0, all_seeds[0]),
    };

    // ── 2. Read sonic energy ──────────────────────────────────────────────────
    let sonic_path = repo_root.join("manifest").join("sonic_window.json");
    let sonic: SonicWindow = fs::read_to_string(&sonic_path)
        .ok()
        .and_then(|s| serde_json::from_str(&s).ok())
        .unwrap_or_default();

    let energy     = sonic.energy.unwrap_or(0.0).clamp(0.0, 1.0);
    let brightness = sonic.brightness.unwrap_or(0.5).clamp(0.0, 1.0);
    let silent     = sonic.silent.unwrap_or(true);

    let hue = (seed_idx as f32 * 30.0).rem_euclid(360.0);

    // ── 3. Render iso entity ──────────────────────────────────────────────────
    if silent || sonic.energy.is_none() {
        println!("[seed_slice] sonic daemon not writing — using fallback energy=0.0");
        println!("[seed_slice] start the daemon: cargo run -p sonic-daemon");
        println!();
    }

    render_iso_entity(seed, energy, brightness, seed_idx);

    // ── 4. Save trail event → runestone forge cycle ───────────────────────────
    let cold_path = append_trail_event(&repo_root, seed, energy, brightness, hue);

    println!("[seed_slice] trail event saved → {}", cold_path.display());
    println!("[seed_slice] forge runestone: cargo run -p ankh-forge -- trail forge");
    println!("[seed_slice] query: cargo run -p ankh-forge -- trail query --kind seed_render");
}
