// Coverage — exhaustive per-occurrence grammar match logging across a corpus.
// Defines OccurrenceSurface (paren, bold, backtick, etc.) — each surface has
// its own enumeration pattern + classification rules.

use anyhow::Result;
use regex::Regex;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

use crate::grammar::Grammar;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Occurrence {
    pub line: usize,
    pub col: usize,
    pub content: String,
    pub inferred_category: String,
    pub grammar_top_rule: Option<String>,
    pub grammar_inner_rules: Vec<String>,
    pub classification: String,
}

#[derive(Debug, Clone, Copy)]
pub enum OccurrenceClassification {
    MatchedCorrectly,
    MatchedAsDifferent,
    NoMatch,
}

impl OccurrenceClassification {
    pub fn label(&self) -> &'static str {
        match self {
            OccurrenceClassification::MatchedCorrectly => "matched_correctly",
            OccurrenceClassification::MatchedAsDifferent => "matched_as_different",
            OccurrenceClassification::NoMatch => "no_match",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CoverageReport {
    pub tool: String,
    pub surface: String,
    pub corpus_path: String,
    pub grammar_hash: String,
    pub total_occurrences: usize,
    pub matched_correctly_count: usize,
    pub coverage_pct: f64,
    pub by_category: BTreeMap<String, usize>,
    pub by_classification: BTreeMap<String, usize>,
    pub by_grammar_top_rule: BTreeMap<String, usize>,
    pub occurrences: Vec<Occurrence>,
}

/// Defines a surface (paren, bold, backtick, ...) for coverage analysis.
/// Each surface knows how to enumerate occurrences from corpus text + how to
/// classify each occurrence into categories.
pub trait Surface {
    fn name(&self) -> &str;
    fn enumerate(&self, corpus: &str) -> Vec<(usize, usize, String, String)>;  // (line, col, full_match, content)
    fn classify_content(&self, content: &str) -> String;
    fn expected_rule_for(&self, category: &str) -> Option<&'static str>;
    fn parse_entry_rule(&self) -> &str;  // pest rule to try matching against
    fn wrap_for_parsing(&self, content: &str) -> String;  // wrap the content for grammar input
}

/// Run a coverage pass for a single surface.
pub fn run_coverage(
    surface: &dyn Surface,
    corpus: &str,
    corpus_path: &str,
    grammar: &Grammar,
) -> Result<CoverageReport> {
    let mut occurrences = Vec::new();
    for (line, col, _full, content) in surface.enumerate(corpus) {
        let category = surface.classify_content(&content);
        let wrapped = surface.wrap_for_parsing(&content);
        let parse_summary = grammar.parse_at(surface.parse_entry_rule(), &wrapped)?;

        let top_rule = if parse_summary.ok {
            // Take the first inner rule that ISN'T the entry rule itself —
            // for a CHOICE entry rule like `id_ref`, the entry rule appears
            // first in inner_rules, and its child (the actual matched
            // alternative) is what we care about.
            let entry = surface.parse_entry_rule();
            parse_summary
                .inner_rules
                .iter()
                .find(|r| !is_trivial_rule(r) && r.as_str() != entry)
                .cloned()
        } else {
            None
        };

        let classification = classify_outcome(surface, &category, &top_rule);
        occurrences.push(Occurrence {
            line,
            col,
            content,
            inferred_category: category,
            grammar_top_rule: top_rule,
            grammar_inner_rules: parse_summary.inner_rules,
            classification: classification.into(),
        });
    }

    let total = occurrences.len();
    let mut by_category = BTreeMap::new();
    let mut by_classification = BTreeMap::new();
    let mut by_grammar_top_rule = BTreeMap::new();
    let mut correctly = 0usize;
    for o in &occurrences {
        *by_category.entry(o.inferred_category.clone()).or_insert(0) += 1;
        *by_classification.entry(o.classification.clone()).or_insert(0) += 1;
        let k = o.grammar_top_rule.clone().unwrap_or_else(|| "NO_MATCH".into());
        *by_grammar_top_rule.entry(k).or_insert(0) += 1;
        if o.classification == "matched_correctly" {
            correctly += 1;
        }
    }
    let coverage_pct = if total > 0 { 100.0 * correctly as f64 / total as f64 } else { 0.0 };

    Ok(CoverageReport {
        tool: "DSL_ITERATION_TOOLKIT_COVERAGE_V1".into(),
        surface: surface.name().into(),
        corpus_path: corpus_path.into(),
        grammar_hash: grammar.hash(),
        total_occurrences: total,
        matched_correctly_count: correctly,
        coverage_pct,
        by_category,
        by_classification,
        by_grammar_top_rule,
        occurrences,
    })
}

fn is_trivial_rule(name: &str) -> bool {
    matches!(name, "EOI" | "WHITESPACE" | "NEWLINE" | "COMMENT")
}

fn classify_outcome(surface: &dyn Surface, category: &str, top_rule: &Option<String>) -> String {
    match top_rule {
        None => "no_match".into(),
        Some(actual) => match surface.expected_rule_for(category) {
            Some(expected) if actual == expected => "matched_correctly".into(),
            Some(expected) => format!("matched_as_{}_expected_{}", actual, expected),
            None => format!("matched_as_{}", actual),
        },
    }
}

// ─── Paren surface ──────────────────────────────────────────────────────────

pub struct ParenSurface {
    re: Regex,
}

impl Default for ParenSurface {
    fn default() -> Self {
        Self { re: Regex::new(r"\(([^()]+)\)").unwrap() }
    }
}

impl Surface for ParenSurface {
    fn name(&self) -> &str { "paren" }

    fn enumerate(&self, corpus: &str) -> Vec<(usize, usize, String, String)> {
        let mut out = Vec::new();
        for (line_idx, line) in corpus.lines().enumerate() {
            for m in self.re.captures_iter(line) {
                let full = m.get(0).unwrap();
                let content = m.get(1).unwrap().as_str().to_string();
                out.push((line_idx + 1, full.start() + 1, full.as_str().to_string(), content));
            }
        }
        out
    }

    fn classify_content(&self, content: &str) -> String {
        let c = content.trim();
        let multi_alias_back = Regex::new(r"^`[^`]+`(/`[^`]+`)+$").unwrap();
        let multi_alias_bare = Regex::new(r"^[A-Z][A-Z0-9_\-]*(/[A-Z][A-Z0-9_\-]*)+$").unwrap();
        let ticked_single = Regex::new(r"^`[^`]+`$").unwrap();
        let bare_id = Regex::new(r"^[A-Z][A-Z0-9_\-¹²³⁴⁵⁶⁷⁸⁹⁰]+$").unwrap();
        let line_ref = Regex::new(r"^(line|Line)\s+\d").unwrap();
        let section_ref = Regex::new(r"^§").unwrap();
        if multi_alias_back.is_match(c) { return "multi_alias_backtick".into(); }
        if multi_alias_bare.is_match(c) { return "multi_alias_bare".into(); }
        if ticked_single.is_match(c) { return "ticked_single".into(); }
        if bare_id.is_match(c) { return "bare_id".into(); }
        if line_ref.is_match(c) || section_ref.is_match(c) { return "reference_form".into(); }
        if let Some(first) = c.chars().next() {
            if first.is_lowercase() { return "prose_lowercase".into(); }
            if first.is_ascii_digit() { return "digit_led".into(); }
            if first.is_uppercase() && c.contains(' ') {
                let all_caps_special = c.split_whitespace().all(|t| {
                    let c0 = t.chars().next().unwrap_or(' ');
                    c0.is_uppercase() || c0.is_ascii_digit() || c0 == '`' || c0 == '<'
                        || "αβγδεζηθικλμνξοπρστυφχψω".contains(c0)
                        || t == "," || t == "/" || t == "-" || t == "&" || t == "+"
                });
                return if all_caps_special { "phrase_titlecase".into() } else { "prose_mixed".into() };
            }
        }
        "other".into()
    }

    fn expected_rule_for(&self, category: &str) -> Option<&'static str> {
        match category {
            "multi_alias_backtick" | "multi_alias_bare" => Some("multi_alias"),
            "ticked_single" => Some("parened_id"),
            "bare_id" => Some("parened_id"),
            "phrase_titlecase" => Some("parened_phrase"),
            "prose_lowercase" | "prose_mixed" | "digit_led" | "other" | "reference_form" => Some("prose_parens"),
            _ => None,
        }
    }

    fn parse_entry_rule(&self) -> &str { "id_ref" }

    fn wrap_for_parsing(&self, content: &str) -> String { format!("({})", content) }
}
