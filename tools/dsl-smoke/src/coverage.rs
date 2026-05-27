// dsl-coverage — exhaustive per-occurrence grammar match logging for
// the catalyst. For now: every `(...)` paren construct gets:
//   1. its actual content
//   2. its inferred category (from regex-based classification)
//   3. the top-level grammar rule that matched it (when parsed in isolation)
//   4. classification: matched_correctly | matched_as_different | no_match
//
// Output: manifest/dsl_coverage_paren_audit.json — full record per occurrence.
// Aggregates printed to stdout for the iteration ledger to capture.
//
// Future: extend to **...** bold spans, `...` backtick spans, fenced blocks,
// headers, blockquotes. Each is a separate surface; same per-occurrence shape.

use pest::Parser;
use pest_derive::Parser;
use regex::Regex;
use serde::Serialize;
use std::collections::BTreeMap;
use std::fs;

#[derive(Parser)]
#[grammar = "chthonic.pest"]
struct ChthonicParser;

#[derive(Serialize)]
struct Occurrence {
    line: usize,
    col: usize,
    content: String,
    inferred_category: String,
    grammar_top_rule: Option<String>,
    grammar_inner_rules: Vec<String>,
    classification: String,
}

#[derive(Serialize)]
struct CoverageReport {
    tool: &'static str,
    ssot_path: String,
    total_occurrences: usize,
    by_category: BTreeMap<String, usize>,
    by_classification: BTreeMap<String, usize>,
    by_grammar_top_rule: BTreeMap<String, usize>,
    occurrences: Vec<Occurrence>,
}

fn classify_paren_content(c: &str) -> String {
    let trimmed = c.trim();
    let multi_alias_back = Regex::new(r"^`[^`]+`(/`[^`]+`)+$").unwrap();
    let multi_alias_bare = Regex::new(r"^[A-Z][A-Z0-9_\-]*(/[A-Z][A-Z0-9_\-]*)+$").unwrap();
    let ticked_single = Regex::new(r"^`[^`]+`$").unwrap();
    let bare_id = Regex::new(r"^[A-Z][A-Z0-9_\-¹²³⁴⁵⁶⁷⁸⁹⁰]+$").unwrap();
    let line_ref = Regex::new(r"^(line|Line)\s+\d").unwrap();
    let section_ref = Regex::new(r"^§").unwrap();
    if multi_alias_back.is_match(trimmed) { return "multi_alias_backtick".into(); }
    if multi_alias_bare.is_match(trimmed) { return "multi_alias_bare".into(); }
    if ticked_single.is_match(trimmed) { return "ticked_single".into(); }
    if bare_id.is_match(trimmed) { return "bare_id".into(); }
    if line_ref.is_match(trimmed) || section_ref.is_match(trimmed) { return "reference_form".into(); }
    if let Some(first) = trimmed.chars().next() {
        if first.is_lowercase() { return "prose_lowercase".into(); }
        if first.is_ascii_digit() { return "digit_led".into(); }
        if first.is_uppercase() && trimmed.contains(' ') {
            let all_capital_or_special = trimmed.split_whitespace().all(|t| {
                let c0 = t.chars().next().unwrap_or(' ');
                c0.is_uppercase() || c0.is_ascii_digit() || c0 == '`' || c0 == '<'
                    || "αβγδεζηθικλμνξοπρστυφχψω".contains(c0)
                    || t == "," || t == "/" || t == "-" || t == "&" || t == "+"
            });
            return if all_capital_or_special { "phrase_titlecase".into() } else { "prose_mixed".into() };
        }
    }
    "other".into()
}

fn try_match(input: &str) -> (Option<String>, Vec<String>) {
    // Parse with id_ref as entry — gives us the SUBSTANTIVE rule that matched,
    // not the wrapping statement node. id_ref's alternatives cover all paren
    // forms (bold_parened_id, multi_alias, parened_phrase, parened_id,
    // prose_parens, ticked_id, identifier, bold_prose).
    match ChthonicParser::parse(Rule::id_ref, input) {
        Ok(mut pairs) => {
            let first = pairs.next();
            let mut inner: Vec<String> = Vec::new();
            // id_ref is a CHOICE rule — top child is the actual matched alternative.
            if let Some(p) = first {
                // id_ref itself is the outer; its inner is the chosen alternative.
                let mut iter = p.into_inner();
                let chosen = iter.next();
                if let Some(c) = chosen {
                    let top = format!("{:?}", c.as_rule());
                    // Collect descendants
                    fn collect(p: &pest::iterators::Pair<Rule>, into: &mut Vec<String>) {
                        for inner in p.clone().into_inner() {
                            into.push(format!("{:?}", inner.as_rule()));
                            collect(&inner, into);
                        }
                    }
                    collect(&c, &mut inner);
                    return (Some(top), inner);
                }
            }
            (None, inner)
        }
        Err(_) => (None, vec![])
    }
}

/// Expected top-rule given the inferred category. Drives classification.
fn expected_rule_for(category: &str) -> Option<&'static str> {
    match category {
        "multi_alias_backtick" | "multi_alias_bare" => Some("multi_alias"),
        "ticked_single" => Some("parened_id"),
        "bare_id" => Some("parened_id"),
        "phrase_titlecase" => Some("parened_phrase"),
        "prose_lowercase" | "prose_mixed" | "digit_led" | "other" | "reference_form" => Some("prose_parens"),
        _ => None,
    }
}

fn classify_result(category: &str, top_rule: &Option<String>) -> String {
    match top_rule {
        None => "no_match".into(),
        Some(actual) => {
            match expected_rule_for(category) {
                Some(expected) if actual == expected => "matched_correctly".into(),
                Some(expected) => format!("matched_as_{}_expected_{}", actual, expected),
                None => format!("matched_as_{}", actual),
            }
        }
    }
}

fn main() {
    let ssot_path = std::env::args().nth(1).expect("usage: dsl-coverage <ssot.md>");
    let text = fs::read_to_string(&ssot_path).expect("readable");
    // Non-nested paren regex (same as the earlier Python classifier).
    let paren_re = Regex::new(r"\(([^()]+)\)").unwrap();

    let mut occurrences: Vec<Occurrence> = Vec::new();
    for (line_idx, line) in text.lines().enumerate() {
        for m in paren_re.captures_iter(line) {
            let full = m.get(0).unwrap();
            let content = m.get(1).unwrap().as_str().to_string();
            let category = classify_paren_content(&content);
            let parened = format!("({})", content);
            let (top_rule, inner_rules) = try_match(&parened);
            let classification = classify_result(&category, &top_rule);
            occurrences.push(Occurrence {
                line: line_idx + 1,
                col: full.start() + 1,
                content,
                inferred_category: category,
                grammar_top_rule: top_rule,
                grammar_inner_rules: inner_rules,
                classification,
            });
        }
    }

    // Aggregate
    let mut by_category = BTreeMap::new();
    let mut by_classification = BTreeMap::new();
    let mut by_grammar_top_rule = BTreeMap::new();
    for o in &occurrences {
        *by_category.entry(o.inferred_category.clone()).or_insert(0) += 1;
        *by_classification.entry(o.classification.clone()).or_insert(0) += 1;
        let key = o.grammar_top_rule.clone().unwrap_or_else(|| "NO_MATCH".into());
        *by_grammar_top_rule.entry(key).or_insert(0) += 1;
    }

    let total = occurrences.len();
    let correctly = by_classification.get("matched_correctly").copied().unwrap_or(0);
    let coverage_pct = if total > 0 { 100.0 * correctly as f64 / total as f64 } else { 0.0 };

    println!("=== DSL Coverage Report (paren occurrences) ===");
    println!("SSOT:  {}", ssot_path);
    println!("Total: {} non-nested paren occurrences", total);
    println!();
    println!("Coverage: {}/{} matched_correctly = {:.2}%", correctly, total, coverage_pct);
    println!();
    println!("By inferred category:");
    let mut sorted_cat: Vec<_> = by_category.iter().collect();
    sorted_cat.sort_by(|a, b| b.1.cmp(a.1));
    for (k, v) in &sorted_cat {
        let pct = 100.0 * **v as f64 / total as f64;
        println!("  {:>22}  {:>6}  ({:.1}%)", k, v, pct);
    }
    println!();
    println!("By classification result:");
    let mut sorted_class: Vec<_> = by_classification.iter().collect();
    sorted_class.sort_by(|a, b| b.1.cmp(a.1));
    for (k, v) in &sorted_class {
        let pct = 100.0 * **v as f64 / total as f64;
        println!("  {:>50}  {:>6}  ({:.1}%)", k, v, pct);
    }
    println!();
    println!("By grammar top rule actually matched:");
    let mut sorted_rule: Vec<_> = by_grammar_top_rule.iter().collect();
    sorted_rule.sort_by(|a, b| b.1.cmp(a.1));
    for (k, v) in &sorted_rule {
        let pct = 100.0 * **v as f64 / total as f64;
        println!("  {:>30}  {:>6}  ({:.1}%)", k, v, pct);
    }

    // Write full report
    let report = CoverageReport {
        tool: "TOOL_DSL_COVERAGE_V1",
        ssot_path: ssot_path.clone(),
        total_occurrences: total,
        by_category,
        by_classification,
        by_grammar_top_rule,
        occurrences,
    };
    let out_path = "manifest/dsl_coverage_paren_audit.json";
    let json = serde_json::to_string_pretty(&report).unwrap();
    fs::write(out_path, json).expect("write manifest");
    println!();
    println!("Full per-occurrence record: {}", out_path);
}
