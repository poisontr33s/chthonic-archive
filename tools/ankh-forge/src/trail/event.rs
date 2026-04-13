use std::fmt;

use anyhow::{Result, bail};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;

/// Valid event types for the Runestone trail.
const VALID_TYPES: &[&str] = &[
    "diagnostic",
    "decision",
    "artifact",
    "snapshot",
    "meta",
    "memory",
    "recovery",
];

/// Priority levels: 1 = critical, 2 = important, 3 = informational.
const VALID_PRIORITIES: std::ops::RangeInclusive<u8> = 1..=3;

/// A single event in the Runestone Execution Model trail.
///
/// Serialized as one JSON line in `.hot.ndjson` files.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrailEvent {
    /// Event classification (e.g. "diagnostic", "decision").
    #[serde(rename = "type")]
    pub event_type: String,

    /// Sub-classification within the type.
    pub kind: String,

    /// RFC 3339 timestamp.
    pub at: DateTime<Utc>,

    /// Priority: 1=critical, 2=important, 3=informational.
    pub p: u8,

    /// Human-readable message.
    pub msg: String,

    /// Optional source file path this event relates to.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub file: Option<String>,

    /// Optional arbitrary structured data.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<Value>,
}

impl TrailEvent {
    /// Validate that all required fields conform to the REM schema.
    pub fn validate(&self) -> Result<()> {
        if !VALID_TYPES.contains(&self.event_type.as_str()) {
            bail!(
                "invalid event type '{}'; expected one of: {}",
                self.event_type,
                VALID_TYPES.join(", ")
            );
        }

        if self.kind.is_empty() {
            bail!("event kind must not be empty");
        }

        if !VALID_PRIORITIES.contains(&self.p) {
            bail!("priority must be 1, 2, or 3; got {}", self.p);
        }

        if self.msg.is_empty() {
            bail!("event msg must not be empty");
        }

        Ok(())
    }
}

impl fmt::Display for TrailEvent {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let priority_label = match self.p {
            1 => "CRIT",
            2 => "IMPT",
            3 => "INFO",
            _ => "????",
        };
        write!(
            f,
            "[{}] {} {}/{}: {}",
            self.at.format("%Y-%m-%dT%H:%M:%SZ"),
            priority_label,
            self.event_type,
            self.kind,
            self.msg,
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip_minimal_event() -> Result<()> {
        let json = r#"{"type":"diagnostic","kind":"test","at":"2026-04-13T05:00:00Z","p":2,"msg":"hello"}"#;
        let evt: TrailEvent = serde_json::from_str(json)?;
        evt.validate()?;
        assert_eq!(evt.event_type, "diagnostic");
        assert!(evt.file.is_none());
        assert!(evt.data.is_none());
        Ok(())
    }

    #[test]
    fn invalid_type_rejected() {
        let json = r#"{"type":"bogus","kind":"x","at":"2026-04-13T05:00:00Z","p":2,"msg":"m"}"#;
        let evt: TrailEvent = serde_json::from_str(json).unwrap();
        assert!(evt.validate().is_err());
    }

    #[test]
    fn invalid_priority_rejected() {
        let json = r#"{"type":"meta","kind":"x","at":"2026-04-13T05:00:00Z","p":5,"msg":"m"}"#;
        let evt: TrailEvent = serde_json::from_str(json).unwrap();
        assert!(evt.validate().is_err());
    }
}
