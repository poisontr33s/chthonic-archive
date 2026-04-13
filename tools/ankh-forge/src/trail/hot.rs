use std::fs::{self, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::Path;

use anyhow::{Context, Result, bail};
use chrono::Utc;
use serde_json::Value;

use super::event::TrailEvent;

/// Strip UTF-8 BOM if present at the start of a line.
fn strip_bom(line: &str) -> &str {
    line.strip_prefix('\u{FEFF}').unwrap_or(line)
}

/// Build the filename for a hot trail file.
pub fn hot_path(trail_dir: &Path, date: &str) -> std::path::PathBuf {
    trail_dir.join(format!("{date}.hot.ndjson"))
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

    fs::create_dir_all(trail_dir)
        .with_context(|| format!("creating trail dir {}", trail_dir.display()))?;

    let mut f = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path)
        .with_context(|| format!("opening {}", path.display()))?;

    let line = serde_json::to_string(&event).context("serializing event")?;
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
    let path = hot_path(trail_dir, date);
    if !path.exists() {
        bail!("no hot trail for date {date}: {}", path.display());
    }

    let file = fs::File::open(&path)
        .with_context(|| format!("opening {}", path.display()))?;
    let reader = BufReader::new(file);

    let mut count = 0u64;
    for (i, line) in reader.lines().enumerate() {
        let raw = line.with_context(|| format!("reading line {}", i + 1))?;
        let line = strip_bom(&raw);
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
    let path = hot_path(trail_dir, date);
    if !path.exists() {
        bail!("no hot trail for date {date}: {}", path.display());
    }

    let file = fs::File::open(&path)
        .with_context(|| format!("opening {}", path.display()))?;
    let reader = BufReader::new(file);

    let mut errors = 0u64;
    let mut total = 0u64;

    for (i, line) in reader.lines().enumerate() {
        let lineno = i + 1;
        let raw = line.with_context(|| format!("reading line {lineno}"))?;
        let line = strip_bom(&raw);
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
