// Ledger — time-series iteration history with regression detection.
// One NDJSON file per project; appended-to per iteration; queried for
// before/after comparisons.

use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LedgerRow {
    pub tool: String,
    pub timestamp: DateTime<Utc>,
    pub git_head: Option<String>,
    pub grammar_hash: String,
    pub slice_count: usize,
    pub slice_pass_count: usize,
    pub slice_fail_count: usize,
    pub audit_shadow_total: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub full_corpus_status: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub full_corpus_first_failing_line: Option<usize>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub paren_coverage_pct: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bold_coverage_pct: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub backtick_coverage_pct: Option<f64>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub regression_warnings: Vec<String>,
    #[serde(flatten)]
    pub extra: std::collections::BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone)]
pub enum Regression {
    /// A slice that previously passed now fails
    ParseRateDrop { slice_label: String, prev: String, current: String },
    /// Audit shadow count rose
    ShadowRise { prev: usize, current: usize },
    /// Coverage percentage dropped on some surface
    CoverageDrop { surface: String, prev: f64, current: f64 },
    /// Same failure position 2+ runs in a row
    Plateau { description: String },
}

impl Regression {
    pub fn describe(&self) -> String {
        match self {
            Regression::ParseRateDrop { slice_label, prev, current } => format!(
                "parse_rate_drop: '{}' was {}, now {}",
                slice_label, prev, current
            ),
            Regression::ShadowRise { prev, current } => format!(
                "shadow_rise: audit shadows {} -> {}",
                prev, current
            ),
            Regression::CoverageDrop { surface, prev, current } => format!(
                "coverage_drop: {} surface {:.2}% -> {:.2}%",
                surface, prev, current
            ),
            Regression::Plateau { description } => format!("plateau: {}", description),
        }
    }
}

pub struct Ledger {
    path: std::path::PathBuf,
    rows: Vec<LedgerRow>,
}

impl Ledger {
    pub fn load(path: impl AsRef<Path>) -> Result<Self> {
        let path = path.as_ref().to_path_buf();
        let mut rows = Vec::new();
        if path.exists() {
            let content = fs::read_to_string(&path)
                .with_context(|| format!("read ledger at {}", path.display()))?;
            for (i, line) in content.lines().enumerate() {
                if line.trim().is_empty() { continue; }
                let row: LedgerRow = serde_json::from_str(line)
                    .with_context(|| format!("parse ledger row {} at {}", i + 1, path.display()))?;
                rows.push(row);
            }
        }
        Ok(Self { path, rows })
    }

    pub fn last(&self) -> Option<&LedgerRow> {
        self.rows.last()
    }

    pub fn rows(&self) -> &[LedgerRow] {
        &self.rows
    }

    pub fn append(&mut self, row: LedgerRow) -> Result<()> {
        if let Some(parent) = self.path.parent() {
            fs::create_dir_all(parent)?;
        }
        let mut file = OpenOptions::new().create(true).append(true).open(&self.path)?;
        writeln!(file, "{}", serde_json::to_string(&row)?)?;
        self.rows.push(row);
        Ok(())
    }

    /// Compare a candidate new row to the most recent existing row.
    /// Returns regressions detected.
    pub fn detect_regressions(&self, candidate: &LedgerRow) -> Vec<Regression> {
        let prev = match self.last() {
            Some(p) => p,
            None => return vec![],
        };
        let mut warnings = Vec::new();
        if candidate.audit_shadow_total > prev.audit_shadow_total {
            warnings.push(Regression::ShadowRise {
                prev: prev.audit_shadow_total,
                current: candidate.audit_shadow_total,
            });
        }
        if candidate.slice_pass_count < prev.slice_pass_count {
            warnings.push(Regression::ParseRateDrop {
                slice_label: "(aggregate)".into(),
                prev: format!("{}/{} pass", prev.slice_pass_count, prev.slice_count),
                current: format!("{}/{} pass", candidate.slice_pass_count, candidate.slice_count),
            });
        }
        for (surface, prev_pct, curr_pct) in [
            ("paren", prev.paren_coverage_pct, candidate.paren_coverage_pct),
            ("bold", prev.bold_coverage_pct, candidate.bold_coverage_pct),
            ("backtick", prev.backtick_coverage_pct, candidate.backtick_coverage_pct),
        ] {
            if let (Some(p), Some(c)) = (prev_pct, curr_pct) {
                if c < p - 0.01 {  // 0.01% tolerance for noise
                    warnings.push(Regression::CoverageDrop {
                        surface: surface.into(),
                        prev: p,
                        current: c,
                    });
                }
            }
        }
        warnings
    }
}
