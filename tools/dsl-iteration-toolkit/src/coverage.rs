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

// ─── Bold surface ───────────────────────────────────────────────────────────
// full-SSOT-smoke iteration 10 (2026-07-06), added per LIFECYCLE.md's Phase 1
// maturation step — same shape as ParenSurface: enumerate **X** occurrences,
// classify by whether X is itself paren-wrapped (→ bold_parened_id) or plain
// prose (→ bold_prose). Deliberately excludes "***" (bold-italic) from the
// regex's char class so triple-star spans aren't miscounted as bold.

pub struct BoldSurface {
    re: Regex,
}

impl Default for BoldSurface {
    fn default() -> Self {
        // (?:\*\*\*)? lookaround isn't available in `regex` crate's engine
        // without look-around support, so exclude "*" from content directly —
        // this naturally skips over "***X***" (content would start with "*",
        // failing the [^*]+ class) without needing negative lookahead.
        Self { re: Regex::new(r"\*\*([^*]+)\*\*").unwrap() }
    }
}

impl Surface for BoldSurface {
    fn name(&self) -> &str { "bold" }

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
        let paren_wrapped = Regex::new(r"^\(.+\)$").unwrap();
        if paren_wrapped.is_match(c) { return "paren_wrapped".into(); }
        "prose".into()
    }

    fn expected_rule_for(&self, category: &str) -> Option<&'static str> {
        match category {
            "paren_wrapped" => Some("bold_parened_id"),
            "prose" => Some("bold_prose"),
            _ => None,
        }
    }

    fn parse_entry_rule(&self) -> &str { "id_ref" }

    fn wrap_for_parsing(&self, content: &str) -> String { format!("**{}**", content) }
}

// ─── Backtick surface ───────────────────────────────────────────────────────
// full-SSOT-smoke iteration 10 (2026-07-06). Classifies by which of the three
// backtick rules the content shape targets: ticked_id (strict uppercase),
// ticked_phrase (Title-Case), ticked_any (everything else — the catch-all).

pub struct BacktickSurface {
    re: Regex,
}

impl Default for BacktickSurface {
    fn default() -> Self {
        Self { re: Regex::new(r"`([^`]+)`").unwrap() }
    }
}

impl Surface for BacktickSurface {
    fn name(&self) -> &str { "backtick" }

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
        let uppercase_id = Regex::new(r"^[A-Z0-9_\-¹²³⁴⁵⁶⁷⁸⁹⁰]+$").unwrap();
        let titlecase_phrase = Regex::new(r"^[A-Z][A-Za-z0-9_\-]*$").unwrap();
        if uppercase_id.is_match(c) { return "uppercase_id".into(); }
        if titlecase_phrase.is_match(c) { return "titlecase_phrase".into(); }
        "any_content".into()
    }

    fn expected_rule_for(&self, category: &str) -> Option<&'static str> {
        match category {
            "uppercase_id" => Some("ticked_id"),
            "titlecase_phrase" => Some("ticked_phrase"),
            "any_content" => Some("ticked_any"),
            _ => None,
        }
    }

    fn parse_entry_rule(&self) -> &str { "id_ref" }

    fn wrap_for_parsing(&self, content: &str) -> String { format!("`{}`", content) }
}

// ─── Fenced surface ─────────────────────────────────────────────────────────
// full-SSOT-smoke iteration 10 (2026-07-06). Structurally different from the
// other three surfaces: fenced code blocks are multi-line, so enumeration
// scans the whole line list for matching ``` pairs instead of a per-line
// regex. Every occurrence is expected to land on fenced_code_block — there's
// only one shape here, unlike paren/bold/backtick's multi-category split.

pub struct FencedSurface;

impl Default for FencedSurface {
    fn default() -> Self { Self }
}

impl Surface for FencedSurface {
    fn name(&self) -> &str { "fenced" }

    fn enumerate(&self, corpus: &str) -> Vec<(usize, usize, String, String)> {
        let mut out = Vec::new();
        let lines: Vec<&str> = corpus.lines().collect();
        let mut i = 0;
        while i < lines.len() {
            if lines[i].trim_start().starts_with("```") {
                let start_line = i;
                let mut j = i + 1;
                while j < lines.len() && !lines[j].trim_start().starts_with("```") {
                    j += 1;
                }
                if j < lines.len() {
                    let content = lines[start_line + 1..j].join("\n");
                    let full = lines[start_line..=j].join("\n");
                    out.push((start_line + 1, 1, full, content));
                    i = j + 1;
                    continue;
                }
            }
            i += 1;
        }
        out
    }

    fn classify_content(&self, _content: &str) -> String { "code_block".into() }

    fn expected_rule_for(&self, category: &str) -> Option<&'static str> {
        match category {
            "code_block" => Some("fenced_code_block"),
            _ => None,
        }
    }

    fn parse_entry_rule(&self) -> &str { "statement" }

    fn wrap_for_parsing(&self, content: &str) -> String { format!("```\n{}\n```", content) }
}
