// Trail event writer — NDJSON append, same schema as Add-TrailEvent in profile.
// Format: {"type":"…","kind":"…","at":"…","p":N,"msg":"…"}

use anyhow::Result;
use chrono::Utc;
use std::{fs::OpenOptions, io::Write, path::Path};

pub fn write_event(
    trail_dir: &Path,
    event_type: &str,
    kind: &str,
    priority: u8,
    msg: &str,
) -> Result<()> {
    if !trail_dir.exists() {
        return Ok(());
    }
    let date = Utc::now().format("%Y-%m-%d").to_string();
    let file = trail_dir.join(format!("{date}.hot.ndjson"));
    let event = serde_json::json!({
        "type": event_type,
        "kind": kind,
        "at": Utc::now().to_rfc3339(),
        "p": priority,
        "msg": msg
    });
    let mut f = OpenOptions::new().create(true).append(true).open(&file)?;
    writeln!(f, "{}", event)?;
    Ok(())
}
