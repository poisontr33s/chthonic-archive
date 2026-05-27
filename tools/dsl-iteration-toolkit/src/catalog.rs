// Pattern catalog — typed read/write/validate for patterns.json.
//
// The catalog encodes "what should work" as data: each pattern has an example
// + expected grammar rule(s) + declared status. Compared to actual parse
// outcome to detect Regressions, Shadows, and Improvements.

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Catalog {
    #[serde(rename = "$schema", default)]
    pub schema: Option<String>,
    pub version: u32,
    #[serde(default)]
    pub description: String,
    pub patterns: Vec<Pattern>,
    #[serde(default)]
    pub categories: std::collections::BTreeMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Pattern {
    pub name: String,
    pub description: String,
    pub example: String,
    #[serde(default)]
    pub expected_top_rule: Option<String>,
    #[serde(default)]
    pub expected_inner_rules: Option<Vec<String>>,
    pub status: String,
    #[serde(default)]
    pub since_iter: Option<serde_json::Value>,
    #[serde(default)]
    pub source_line_ssot: Option<u64>,
    pub category: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub note: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub first_failing_grammar_hash: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_verified_grammar_hash: Option<String>,
    #[serde(flatten)]
    pub extra: std::collections::BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone)]
pub enum PatternResult {
    /// Declared working + actually working
    Pass,
    /// Declared working + parses but wrong shape (silent regression)
    Shadow(String),
    /// Declared working + doesn't parse at all
    Regression(String),
    /// Declared failing + truly works → catalog should be updated
    Improved,
    /// Declared failing + still fails (confirmed)
    ConfirmedFail,
    /// status == "deferred"
    Skipped,
}

impl PatternResult {
    pub fn label(&self) -> &'static str {
        match self {
            PatternResult::Pass => "PASS",
            PatternResult::Shadow(_) => "SHADOW",
            PatternResult::Regression(_) => "REGRESSION",
            PatternResult::Improved => "IMPROVED",
            PatternResult::ConfirmedFail => "FAIL (expected)",
            PatternResult::Skipped => "DEFERRED",
        }
    }

    pub fn is_regression(&self) -> bool {
        matches!(self, PatternResult::Shadow(_) | PatternResult::Regression(_))
    }
}

impl Catalog {
    pub fn load(path: impl AsRef<Path>) -> Result<Self> {
        let path = path.as_ref();
        let content = fs::read_to_string(path)
            .with_context(|| format!("read catalog at {}", path.display()))?;
        let catalog: Catalog = serde_json::from_str(&content)
            .with_context(|| format!("parse catalog at {}", path.display()))?;
        Ok(catalog)
    }

    pub fn save(&self, path: impl AsRef<Path>) -> Result<()> {
        let json = serde_json::to_string_pretty(self)?;
        fs::write(path, json + "\n")?;
        Ok(())
    }

    /// Test all patterns against the grammar; return per-pattern results.
    /// Caller provides a closure that runs the actual parse — keeps Catalog
    /// independent of any specific grammar runner.
    pub fn test_all<F>(&self, mut parser: F) -> Vec<(String, PatternResult)>
    where
        F: FnMut(&Pattern) -> (bool, Vec<String>),
    {
        self.patterns
            .iter()
            .map(|p| (p.name.clone(), self.test_one(p, &mut parser)))
            .collect()
    }

    fn test_one<F>(&self, p: &Pattern, parser: &mut F) -> PatternResult
    where
        F: FnMut(&Pattern) -> (bool, Vec<String>),
    {
        if p.status == "deferred" {
            return PatternResult::Skipped;
        }
        let (parses, actual_rules) = parser(p);
        let expected_present = check_expected(p, &actual_rules);

        match (p.status.as_str(), parses, expected_present) {
            ("working", true, true) => PatternResult::Pass,
            ("working", true, false) => PatternResult::Shadow(format!(
                "actual rules: {:?}; expected top: {:?}, inner: {:?}",
                actual_rules, p.expected_top_rule, p.expected_inner_rules
            )),
            ("working", false, _) => PatternResult::Regression("parse failed".into()),
            ("failing", true, true) => PatternResult::Improved,
            ("failing", _, _) => PatternResult::ConfirmedFail,
            _ => PatternResult::Shadow(format!("unknown status: {}", p.status)),
        }
    }
}

fn check_expected(p: &Pattern, actual_rules: &[String]) -> bool {
    let rule_set: std::collections::HashSet<&String> = actual_rules.iter().collect();
    let top_str: String;
    let top_str_ref: String;
    if let Some(expected) = &p.expected_top_rule {
        if expected != "DEFERRED" {
            top_str = expected.clone();
            top_str_ref = top_str.clone();
            if !rule_set.contains(&top_str_ref) {
                return false;
            }
        }
    }
    if let Some(expected_inner) = &p.expected_inner_rules {
        for e in expected_inner {
            if !rule_set.contains(e) {
                return false;
            }
        }
    }
    true
}
