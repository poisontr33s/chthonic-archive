// dsl-full-smoke — parse the entire SSOT.md as a single program, report stats.
//
// Used after the 6-slice corpus is clean to verify the grammar against the
// 10,532-line catalyst in full. Surfaces the unknown unknowns — catalyst regions
// the hand-picked slices didn't cover.
//
// On parse failure: also runs a bisect to find the first failing line.

use pest::Parser;
use pest_derive::Parser;
use std::collections::BTreeMap;
use std::fs;

#[derive(Parser)]
#[grammar = "chthonic.pest"]
struct ChthonicParser;

fn classify(rules: &mut BTreeMap<String, usize>, pair: &pest::iterators::Pair<Rule>) {
    let key = format!("{:?}", pair.as_rule());
    *rules.entry(key).or_insert(0) += 1;
    for inner in pair.clone().into_inner() {
        classify(rules, &inner);
    }
}

fn bisect_first_fail(lines: &[&str]) -> Option<usize> {
    // Binary search: find smallest N where prefix [0..N] fails.
    let mut lo = 1usize;
    let mut hi = lines.len();
    let mut last_failing = None;

    // First quickly confirm the full prefix fails (already known from caller).
    if ChthonicParser::parse(Rule::program, &lines.join("\n")).is_ok() {
        return None;
    }

    while lo < hi {
        let mid = lo + (hi - lo) / 2;
        let prefix = lines[..mid].join("\n");
        if ChthonicParser::parse(Rule::program, &prefix).is_ok() {
            lo = mid + 1;
        } else {
            last_failing = Some(mid);
            hi = mid;
        }
    }
    last_failing
}

fn main() {
    let path = std::env::args().nth(1).expect("usage: dsl-full-smoke <ssot.md>");
    let text = fs::read_to_string(&path).expect("readable");
    let lines: Vec<&str> = text.lines().collect();

    println!("=== CHTHONIC DSL Phase 0 — FULL SSOT smoke ===");
    println!("Catalyst: {}", path);
    println!("Size:     {} bytes, {} lines", text.len(), lines.len());
    println!();

    let result = ChthonicParser::parse(Rule::program, &text);
    match result {
        Ok(mut pairs) => {
            let prog = pairs.next().unwrap();
            let mut counts = BTreeMap::new();
            classify(&mut counts, &prog);
            println!("PARSE: OK — entire catalyst parses against current grammar");
            println!();
            println!("Rule counts (top 20):");
            let mut sorted: Vec<_> = counts.into_iter().collect();
            sorted.sort_by(|a, b| b.1.cmp(&a.1));
            for (rule, n) in sorted.iter().take(20) {
                println!("    {:>8}  {}", n, rule);
            }
            let prose = sorted.iter().find(|(r, _)| r == "prose_fragment").map(|(_, n)| *n).unwrap_or(0);
            let total: usize = sorted.iter().map(|(_, n)| *n).sum();
            let prose_pct = if total > 0 { 100.0 * prose as f64 / total as f64 } else { 0.0 };
            println!();
            println!("Total nodes: {}", total);
            println!("Prose fraction: {}/{} = {:.2}%", prose, total, prose_pct);
            println!();
            println!("Substrate-bearing rule counts:");
            for rule in ["bold_parened_id", "bold_prose", "multi_alias", "parened_phrase",
                         "parened_id", "prose_parens", "ticked_id", "invocation",
                         "fenced_code_block", "header", "composition", "phrase_id"] {
                let n = sorted.iter().find(|(r, _)| r == rule).map(|(_, n)| *n).unwrap_or(0);
                println!("    {:>8}  {}", n, rule);
            }
        }
        Err(e) => {
            println!("PARSE: FAIL — full catalyst does not parse against current grammar");
            println!();
            println!("Error:");
            println!("{}", e);
            println!();
            println!("Bisecting for first failing prefix line...");
            match bisect_first_fail(&lines) {
                Some(n) => {
                    println!("First failing prefix: lines 1..{}  (line {} introduces failure)", n, n);
                    if n > 0 && n <= lines.len() {
                        println!("Line {}: {}", n, lines[n - 1]);
                    }
                }
                None => println!("(bisect inconclusive)"),
            }
        }
    }
}
