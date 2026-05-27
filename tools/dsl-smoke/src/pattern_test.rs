// dsl-pattern-test — runs each pattern in .chthonic/grammar/patterns.json
// through the current grammar; reports per-pattern result.
//
// For each pattern with status != "deferred":
//   1. Try to parse `example` as a `program`.
//   2. If parsed: traverse parse tree, check that expected_top_rule appears
//      among the children of program (or at deeper depth for inner rules).
//   3. Compare actual result to declared status:
//      - status=working + parse OK + expected rules present → PASS
//      - status=working + parse FAIL → REGRESSION (loud)
//      - status=working + parse OK but expected rules absent → SHADOW (silent failure)
//      - status=failing + parse FAIL → confirmed-fail (expected)
//      - status=failing + parse OK → IMPROVED (the pattern now works; update catalog)
//
// Exit code: 0 if no regressions, 1 if regressions found.

use pest::Parser;
use pest_derive::Parser;
use std::collections::HashSet;
use std::fs;

#[derive(Parser)]
#[grammar = "chthonic.pest"]
struct ChthonicParser;

#[derive(serde::Deserialize)]
struct Catalog {
    patterns: Vec<Pattern>,
}

#[derive(serde::Deserialize)]
#[allow(dead_code)]
struct Pattern {
    name: String,
    description: String,
    example: String,
    #[serde(default)]
    expected_top_rule: Option<String>,
    #[serde(default)]
    expected_inner_rules: Option<Vec<String>>,
    status: String,
    #[serde(default)]
    category: String,
}

fn collect_rule_names(pair: &pest::iterators::Pair<Rule>, into: &mut HashSet<String>) {
    into.insert(format!("{:?}", pair.as_rule()));
    for inner in pair.clone().into_inner() {
        collect_rule_names(&inner, into);
    }
}

#[derive(Debug)]
enum PatternResult {
    Pass,
    Regression(String),
    Shadow(String),
    ConfirmedFail,
    Improved,
    DeferredSkip,
}

/// Derive ACTUAL parse outcome from the grammar, independent of declared status.
/// Returns (parses_ok, expected_rules_present).
fn actual_outcome(p: &Pattern) -> (bool, bool, Option<String>) {
    let parse = ChthonicParser::parse(Rule::program, &p.example);
    match parse {
        Ok(mut pairs) => {
            let prog = pairs.next().unwrap();
            let mut rules = HashSet::new();
            collect_rule_names(&prog, &mut rules);

            // Verify expected rules are present
            let mut top_ok = true;
            if let Some(expected) = &p.expected_top_rule {
                if expected != "DEFERRED" && !rules.contains(expected) {
                    top_ok = false;
                }
            }
            let mut inner_ok = true;
            let mut missing_inner: Vec<String> = Vec::new();
            if let Some(expected) = &p.expected_inner_rules {
                for e in expected {
                    if !rules.contains(e) {
                        missing_inner.push(e.clone());
                        inner_ok = false;
                    }
                }
            }
            let detail = if !top_ok || !inner_ok {
                Some(format!(
                    "actual rules: {:?}{}{}",
                    rules,
                    if !top_ok && p.expected_top_rule.is_some() {
                        format!("  missing top: {:?}", p.expected_top_rule)
                    } else { String::new() },
                    if !missing_inner.is_empty() {
                        format!("  missing inner: {:?}", missing_inner)
                    } else { String::new() }
                ))
            } else {
                None
            };
            (true, top_ok && inner_ok, detail)
        }
        Err(e) => (false, false, Some(format!("parse error: {}", e))),
    }
}

fn test_pattern(p: &Pattern) -> PatternResult {
    if p.status == "deferred" {
        return PatternResult::DeferredSkip;
    }
    let (parses, expected_present, detail) = actual_outcome(p);

    match (p.status.as_str(), parses, expected_present) {
        // Declared working + actually working: PASS
        ("working", true, true) => PatternResult::Pass,
        // Declared working + parses but wrong shape: SHADOW (silent regression)
        ("working", true, false) => PatternResult::Shadow(detail.unwrap_or_default()),
        // Declared working + doesn't parse: REGRESSION (loud)
        ("working", false, _) => PatternResult::Regression(detail.unwrap_or_default()),
        // Declared failing + truly works: IMPROVED — catalog should be updated
        ("failing", true, true) => PatternResult::Improved,
        // Declared failing + parses with wrong shape: STILL FAILING (shadow persists)
        ("failing", true, false) => PatternResult::ConfirmedFail,
        // Declared failing + doesn't parse: CONFIRMED FAIL
        ("failing", false, _) => PatternResult::ConfirmedFail,
        // Unknown status
        _ => PatternResult::Shadow(format!("unknown status: {}", p.status)),
    }
}

fn main() {
    let catalog_path = std::env::args().nth(1).unwrap_or_else(|| ".chthonic/grammar/patterns.json".into());
    let content = fs::read_to_string(&catalog_path)
        .unwrap_or_else(|e| panic!("read {}: {}", catalog_path, e));
    let catalog: Catalog = serde_json::from_str(&content)
        .unwrap_or_else(|e| panic!("parse {}: {}", catalog_path, e));

    let mut counts = std::collections::BTreeMap::new();
    let mut regressions = 0;
    let mut improvements = 0;

    println!("=== DSL Pattern Test ===");
    println!("Catalog: {}  ({} patterns)", catalog_path, catalog.patterns.len());
    println!();

    for p in &catalog.patterns {
        let result = test_pattern(p);
        let result_key = match &result {
            PatternResult::Pass => "PASS",
            PatternResult::Regression(_) => "REGRESSION",
            PatternResult::Shadow(_) => "SHADOW",
            PatternResult::ConfirmedFail => "FAIL (expected)",
            PatternResult::Improved => "IMPROVED",
            PatternResult::DeferredSkip => "DEFERRED",
        };
        *counts.entry(result_key).or_insert(0) += 1;
        let detail = match &result {
            PatternResult::Regression(d) | PatternResult::Shadow(d) => format!(" — {}", d),
            _ => String::new(),
        };
        println!("  [{:>14}]  {:<40} ({}){}", result_key, p.name, p.category, detail);
        match result {
            PatternResult::Regression(_) | PatternResult::Shadow(_) => regressions += 1,
            PatternResult::Improved => improvements += 1,
            _ => {}
        }
    }

    println!();
    println!("=== Summary ===");
    for (k, v) in &counts {
        println!("  {:>14}: {}", k, v);
    }
    println!();
    if improvements > 0 {
        println!("  {} pattern(s) IMPROVED — consider updating catalog status from 'failing' to 'working'", improvements);
    }
    if regressions > 0 {
        println!("  {} pattern(s) REGRESSED or SHADOW-failed — consider git revert", regressions);
        std::process::exit(1);
    } else {
        println!("  no regressions");
    }
}
