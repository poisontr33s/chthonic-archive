use std::fs::{self, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};

/// 64 MiB ceiling on hot trail size — refuse appends that would exceed it.
const MAX_HOT_SIZE: u64 = 64 * 1024 * 1024;

use anyhow::{Context, Result, bail};
use chrono::Utc;
use serde_json::Value;

use super::event::{TrailEvent, strip_bom};

/// Build the filename for a hot trail file.
pub fn hot_path(trail_dir: &Path, date: &str) -> PathBuf {
    trail_dir.join(format!("{date}.hot.ndjson"))
}

/// Build the filename for a sealed (archived) hot trail file.
pub(crate) fn sealed_path(trail_dir: &Path, date: &str) -> PathBuf {
    trail_dir.join(format!("{date}.hot.ndjson.sealed"))
}

/// Resolve the hot trail path for a date — open first, sealed fallback.
pub(crate) fn hot_or_sealed_path(trail_dir: &Path, date: &str) -> Result<PathBuf> {
    let h = hot_path(trail_dir, date);
    if h.exists() { return Ok(h); }
    let s = sealed_path(trail_dir, date);
    if s.exists() { return Ok(s); }
    bail!("no hot or sealed trail for {date}")
}

/// Append a single event to today's hot trail file.
pub fn append(
    trail_dir: &Path,
    event_type: &str,
    kind: &str,
    msg: &str,
    priority: u8,
    file: Option<&str>,
    data: Option<&str>,
) -> Result<()> {
    let parsed_data: Option<Value> = match data {
        Some(raw) => {
            let v: Value =
                serde_json::from_str(raw).context("--data must be valid JSON")?;
            if !v.is_object() {
                bail!("--data must be a JSON object, got: {}", v);
            }
            Some(v)
        }
        None => None,
    };

    let event = TrailEvent {
        event_type: event_type.to_owned(),
        kind: kind.to_owned(),
        at: Utc::now(),
        p: priority,
        msg: msg.to_owned(),
        file: file.map(String::from),
        data: parsed_data,
    };

    event.validate()?;

    let today = event.at.format("%Y-%m-%d").to_string();
    let path = hot_path(trail_dir, &today);

    // Refuse appends to sealed (archived) dates.
    if sealed_path(trail_dir, &today).exists() {
        bail!(
            "hot trail for {today} is sealed (archived to cold). Appends are for open dates only."
        );
    }

    // Serialize first — need byte count for size preflight.
    let line = serde_json::to_string(&event).context("serializing event")?;
    let line_bytes = line.len() as u64 + 1; // +1 for newline

    // Pre-flight: reject if appending would breach 64 MiB ceiling.
    let current_size = if path.exists() {
        fs::metadata(&path)
            .with_context(|| format!("checking size of {}", path.display()))?
            .len()
    } else {
        0
    };
    if current_size + line_bytes > MAX_HOT_SIZE {
        bail!(
            "hot trail at {} would exceed 64 MiB ({} + {} bytes). Forge and stone it first.",
            path.display(), current_size, line_bytes
        );
    }

    fs::create_dir_all(trail_dir)
        .with_context(|| format!("creating trail dir {}", trail_dir.display()))?;

    let mut f = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path)
        .with_context(|| format!("opening {}", path.display()))?;

    writeln!(f, "{line}").with_context(|| format!("writing to {}", path.display()))?;

    eprintln!("appended to {}", path.display());
    Ok(())
}

/// List events from a hot trail file, with optional filters.
pub fn list(
    trail_dir: &Path,
    date: &str,
    type_filter: Option<&str>,
    priority_filter: Option<u8>,
) -> Result<()> {
    let path = hot_or_sealed_path(trail_dir, date)?;
    let file = fs::File::open(&path)
        .with_context(|| format!("opening {}", path.display()))?;
    let reader = BufReader::new(file);

    let mut count = 0u64;
    let mut bom_checked = false;
    for (i, line) in reader.lines().enumerate() {
        let raw = line.with_context(|| format!("reading line {}", i + 1))?;
        let line = if !bom_checked { bom_checked = true; strip_bom(&raw) } else { raw.as_str() };
        if line.trim().is_empty() {
            continue;
        }

        let event: TrailEvent = serde_json::from_str(line)
            .with_context(|| format!("parsing line {}", i + 1))?;

        if let Some(tf) = type_filter {
            if event.event_type != tf {
                continue;
            }
        }

        if let Some(pf) = priority_filter {
            if event.p != pf {
                continue;
            }
        }

        println!("{event}");
        count += 1;
    }

    eprintln!("{count} event(s) displayed");
    Ok(())
}

/// Verify that every line in a hot trail file is valid NDJSON conforming to the
/// `TrailEvent` schema.
pub fn verify(trail_dir: &Path, date: &str) -> Result<()> {
    let path = hot_or_sealed_path(trail_dir, date)?;
    let file = fs::File::open(&path)
        .with_context(|| format!("opening {}", path.display()))?;
    let reader = BufReader::new(file);

    let mut errors = 0u64;
    let mut total = 0u64;
    let mut bom_checked = false;

    for (i, line) in reader.lines().enumerate() {
        let lineno = i + 1;
        let raw = line.with_context(|| format!("reading line {lineno}"))?;
        let line = if !bom_checked { bom_checked = true; strip_bom(&raw) } else { raw.as_str() };
        if line.trim().is_empty() {
            continue;
        }
        total += 1;

        let event: TrailEvent = match serde_json::from_str(line) {
            Ok(e) => e,
            Err(err) => {
                eprintln!("line {lineno}: parse error: {err}");
                errors += 1;
                continue;
            }
        };

        if let Err(err) = event.validate() {
            eprintln!("line {lineno}: schema error: {err}");
            errors += 1;
        }
    }

    if errors > 0 {
        bail!("{errors} error(s) in {total} event(s) from {}", path.display());
    }

    eprintln!("{total} event(s) verified OK in {}", path.display());
    Ok(())
}
