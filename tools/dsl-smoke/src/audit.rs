use pest::Parser;
use pest_derive::Parser;
use std::fs;

#[derive(Parser)]
#[grammar = "chthonic.pest"]
struct ChthonicParser;

const SUBSTRATE_MARKERS: &[&str] = &["**", "$", "→", "×", "<->", "↔", "§"];

fn audit_pair(pair: &pest::iterators::Pair<Rule>, slice_label: &str) -> usize {
    let mut shadows = 0;
    let rule_name = format!("{:?}", pair.as_rule());
    if rule_name == "prose_parens" {
        let text = pair.as_str();
        let mut inner_rule_names: Vec<String> = Vec::new();
        for inner in pair.clone().into_inner() {
            inner_rule_names.push(format!("{:?}", inner.as_rule()));
        }
        for marker in SUBSTRATE_MARKERS {
            if text.contains(marker) {
                // Check if there's a corresponding inner rule that recognized the marker
                let has_substrate_inner = inner_rule_names.iter().any(|r| {
                    r == "substrate_marker" || r == "bold_parened_id" || r == "bold_prose"
                    || r == "multi_alias" || r == "parened_phrase" || r == "parened_id"
                    || r == "ticked_id" || r == "invocation"
                });
                if !has_substrate_inner {
                    shadows += 1;
                    let preview = if text.len() > 100 { format!("{}...", &text[..97]) } else { text.to_string() };
                    println!("  [SHADOW-CONFIRMED] {}: prose_parens contains '{}' but has no substrate-aware inner rules", slice_label, marker);
                    println!("                     span: {:?}", preview);
                    println!("                     inner rules: {:?}", inner_rule_names);
                    break;
                }
            }
        }
    }
    for inner in pair.clone().into_inner() {
        shadows += audit_pair(&inner, slice_label);
    }
    shadows
}

fn main() {
    let ssot_path = std::env::args().nth(1).expect("usage: audit <ssot.md>");
    let text = fs::read_to_string(&ssot_path).expect("readable");
    let lines: Vec<&str> = text.lines().collect();

    let slice_lines = |start: usize, end: usize| -> String {
        lines[start.saturating_sub(1)..end.min(lines.len())].join("\n")
    };

    let slices = vec![
        ("S1 Trinity (L70-130)", slice_lines(70, 130)),
        ("S2 ESL emoji (L95-115)", slice_lines(95, 115)),
        ("S3 Invocations (L1115-1200)", slice_lines(1115, 1200)),
        ("S4 CRC registry (L2000-2050)", slice_lines(2000, 2050)),
        ("S5 Organ canon (L285-340)", slice_lines(285, 340)),
        ("S6 Inline-script (L8485-8550)", slice_lines(8485, 8550)),
    ];

    let mut total = 0;
    for (label, content) in &slices {
        println!("\n=== AUDIT: {} ===", label);
        match ChthonicParser::parse(Rule::program, content) {
            Ok(mut pairs) => {
                let prog = pairs.next().unwrap();
                let s = audit_pair(&prog, label);
                if s == 0 { println!("  no shadow failures"); }
                total += s;
            }
            Err(e) => println!("  PARSE FAIL: {}", e),
        }
    }
    println!("\n=== TOTAL CONFIRMED SHADOW FAILURES: {} ===", total);
}
