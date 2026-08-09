// XP engine — mirrors chthonic-xp.ps1 formula exactly.
// Formula: base[type] + kind_bonus[kind], multiplied by priority, rounded per event.
// Level = floor(sqrt(xp / 10))

use anyhow::Result;
use chrono::Utc;
use crossterm::{
    execute,
    style::{Color, Print, ResetColor, SetForegroundColor},
    terminal::SetTitle,
};
use serde::{Deserialize, Serialize};
use std::{
    fs,
    io::Write,
    path::{Path, PathBuf},
};

/// Raw trail event from NDJSON
#[derive(Debug, Deserialize, Clone)]
pub struct TrailEvent {
    #[serde(rename = "type")]
    pub event_type: String,
    pub kind: Option<String>,
    pub p: Option<serde_json::Value>,
    #[allow(dead_code)]
    pub msg: Option<String>,
    /// An explicit scored judgement, e.g. from `scripts/pwsh-experience.ps1`.
    /// Kept as a raw Value, not `Option<i64>`, so "field present but null" is
    /// distinguishable from "field absent" — chthonic-xp.ps1 branches on property
    /// *presence* (`$e.PSObject.Properties['xp_delta']`), and a null there scores 0
    /// rather than falling through to the type table.
    pub xp_delta: Option<serde_json::Value>,
}

/// Persisted XP state file
#[derive(Debug, Serialize)]
pub struct XpState {
    pub xp: u32,
    pub level: u32,
    pub unlocked: Vec<String>,
    pub updated: String,
}

// ── Trail ingestion ────────────────────────────────────────────────────────────

pub fn read_trail(dir: &Path) -> Result<Vec<TrailEvent>> {
    let mut events: Vec<TrailEvent> = Vec::new();
    if !dir.exists() {
        return Ok(events);
    }

    let mut paths: Vec<PathBuf> = fs::read_dir(dir)?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| {
            p.file_name()
                .and_then(|n| n.to_str())
                .map(|n| n.ends_with(".hot.ndjson"))
                .unwrap_or(false)
        })
        .collect();
    paths.sort();

    for path in paths {
        if let Ok(content) = fs::read_to_string(&path) {
            for line in content.lines() {
                // Rust's `trim` removes White_Space, and U+FEFF is not White_Space —
                // so a BOM'd first line survives trimming, fails to deserialize, and
                // is swallowed by the `if let Ok` below. Measured 2026-08-09:
                // `.chthonic/trail/2026-04-13.hot.ndjson` is BOM'd, and its first line
                // is worth exactly the 8 XP by which cai trailed chthonic-xp.ps1
                // (828 vs 836). ankh-forge already carries the same guard as
                // `strip_bom` in tools/ankh-forge/src/trail/event.rs:23.
                let line = line.strip_prefix('\u{FEFF}').unwrap_or(line).trim();
                if line.is_empty() {
                    continue;
                }
                if let Ok(ev) = serde_json::from_str::<TrailEvent>(line) {
                    events.push(ev);
                }
            }
        }
    }
    Ok(events)
}

// ── XP computation (must stay in sync with chthonic-xp.ps1) ──────────────────

/// Session bookkeeping. Work earns XP; presence does not.
///
/// Omitting this was the single largest divergence from `chthonic-xp.ps1`:
/// measured 2026-08-09 over the live trail, 22,751 of 22,804 events are these
/// kinds, so scoring them put cai at 91,741 XP / Lv.95 against the engine's
/// 836 / Lv.9 — a 113x gap, 99.8% of it noise.
const META_KINDS: &[&str] = &["session_start", "session_end", "zjit-session", "msys2-session"];

/// .NET's `[Math]::Round` is banker's rounding (half-to-even); Rust's `f64::round`
/// is half-away-from-zero. They disagree on exact .5 values, which are reachable
/// here — `snapshot`(3) + `wiring`(3) at p3 is 4.5, where PowerShell yields 4 and
/// `.round()` yields 5. Matching the engine means matching its rounding.
fn round_half_to_even(x: f64) -> f64 {
    let r = x.round();
    if (x - x.trunc()).abs() == 0.5 && r % 2.0 != 0.0 {
        r - x.signum()
    } else {
        r
    }
}

/// Mirrors `Measure-XP` in `scripts/chthonic-xp.ps1`, including its branch order:
/// meta-kind skip, then explicit `xp_delta`, then the type table.
///
/// Accumulates in i64 so a negative `xp_delta` (e.g. from `pwsh-experience.ps1`,
/// which can subtract) is arithmetically real rather than saturating mid-sum.
/// The total is clamped to 0 on return because `level()`/`xp_bar()` are u32-shaped;
/// a negative career total would be meaningless to display and `sqrt` of it is NaN.
/// That clamp is a deliberate, stated divergence: the PowerShell engine has no
/// clamp and would produce NaN there instead.
pub fn compute_xp(events: &[TrailEvent]) -> u32 {
    // Base XP per event type
    let base_xp = |t: &str| match t {
        "artifact" => 10,
        "decision" => 8,
        "diagnostic" => 5,
        "memory" => 4,
        "recovery" => 15,
        "snapshot" => 3,
        "meta" => 5,
        _ => 1,
    };

    // Kind bonus stacked on top of base. Full table — four entries were missing
    // here (redux, roulette_steward, bounty_hunt, pwsh_fullstack) against the
    // engine's seven.
    let kind_bonus = |k: &str| match k {
        "epoch-close" => 45,
        "git_commit" => 5,
        "wiring" => 3,
        "redux" => 8,
        "roulette_steward" => 12,
        "bounty_hunt" => 20,
        "pwsh_fullstack" => 15,
        _ => 0,
    };

    // Priority multiplier: p1=1.5, p2=1.0, p3=0.75, missing/unknown=1.0.
    // The engine's `else { 1.0 }` covers absent p; this defaulted to 0.75.
    let prio_mult = |p: Option<&serde_json::Value>| -> f64 {
        match p.and_then(|v| v.as_u64()) {
            Some(1) => 1.5,
            Some(2) => 1.0,
            Some(3) => 0.75,
            _ => 1.0,
        }
    };

    let mut total: i64 = 0;
    for ev in events {
        if let Some(k) = ev.kind.as_deref() {
            if META_KINDS.contains(&k) {
                continue;
            }
        }
        // An explicit judgement outranks the type table, which can only ever add.
        if let Some(d) = ev.xp_delta.as_ref() {
            total += d.as_i64().unwrap_or(0);
            continue;
        }
        let base = base_xp(ev.event_type.as_str()) as f64;
        let bonus = ev.kind.as_deref().map(kind_bonus).unwrap_or(0) as f64;
        let prio = prio_mult(ev.p.as_ref());
        total += round_half_to_even((base + bonus) * prio) as i64;
    }
    total.max(0) as u32
}

// ── Level math ────────────────────────────────────────────────────────────────

pub fn level(xp: u32) -> u32 {
    ((xp as f64 / 10.0).sqrt().floor()) as u32
}

pub fn level_threshold(lv: u32) -> u32 {
    lv * lv * 10
}

pub fn level_title(lv: u32) -> &'static str {
    const TITLES: &[&str] = &[
        "Initiate",
        "Apprentice",
        "Adept",
        "Journeyman",
        "Craftsman",
        "Expert",
        "Master",
        "Archivist",
        "Sage",
        "Oracle",
        "Sovereign",
    ];
    TITLES.get(lv as usize).copied().unwrap_or("Sovereign")
}

/// 10-char XP bar using block elements. Matches PS1 Get-XpBar.
pub fn xp_bar(xp: u32, lv: u32) -> String {
    let lo = level_threshold(lv);
    let hi = level_threshold(lv + 1);
    let pct = if hi > lo {
        (xp.saturating_sub(lo)) as f64 / (hi - lo) as f64
    } else {
        1.0
    };
    let filled = ((pct * 10.0).round() as usize).min(10);
    format!("[{}{}]", "█".repeat(filled), "░".repeat(10 - filled))
}

// ── State persistence ─────────────────────────────────────────────────────────

pub fn persist_state(state_file: &Path, trail_dir: &Path) -> Result<()> {
    let events = read_trail(trail_dir)?;
    let xp = compute_xp(&events);
    let lv = level(xp);
    let state = XpState {
        xp,
        level: lv,
        unlocked: vec![], // full achievement check is in chthonic-xp.ps1
        updated: Utc::now().to_rfc3339(),
    };
    fs::write(state_file, serde_json::to_string_pretty(&state)?)?;
    Ok(())
}

// ── Status line (matches chthonic-xp.ps1 output format) ──────────────────────

pub fn print_status(out: &mut impl Write, xp: u32) -> std::io::Result<()> {
    let lv = level(xp);
    let t = level_title(lv);
    let bar = xp_bar(xp, lv);
    let xp_next = level_threshold(lv + 1).saturating_sub(xp);

    let _ = execute!(
        out,
        SetForegroundColor(Color::Yellow),
        Print(format!(
            "  [XP] Lv.{lv} {t} {bar} {xp} XP (+{xp_next} -> Lv.{})\n",
            lv + 1
        )),
        ResetColor,
        SetTitle(format!("[Lv.{lv} {t} | {xp} XP] Chthonic ◈"))
    );
    Ok(())
}
