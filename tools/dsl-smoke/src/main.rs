use pest::Parser;
use pest_derive::Parser;
use std::collections::BTreeMap;
use std::fs;

#[derive(Parser)]
#[grammar = "chthonic.pest"]
struct ChthonicParser;

// Each test slice: (label, start_byte, end_byte). Bytes chosen to land on
// line boundaries; they probe a distinct stress region of the catalyst.
struct Slice<'a> {
    label: &'a str,
    text: &'a str,
}

fn classify(rules: &mut BTreeMap<String, usize>, pair: &pest::iterators::Pair<Rule>) {
    let key = format!("{:?}", pair.as_rule());
    *rules.entry(key).or_insert(0) += 1;
    for inner in pair.clone().into_inner() {
        classify(rules, &inner);
    }
}

fn smoke(slice: &Slice) {
    println!("\n────────────────────────────────────────────────────────────");
    println!("SLICE: {}", slice.label);
    println!("  bytes: {}, lines: {}", slice.text.len(), slice.text.lines().count());
    let preview: String = slice.text.chars().take(80).collect();  // char-safe (bytes can split '→')
    println!("  first 80: {:?}", preview);

    match ChthonicParser::parse(Rule::program, slice.text) {
        Ok(mut pairs) => {
            let prog = pairs.next().unwrap();
            let mut counts = BTreeMap::new();
            classify(&mut counts, &prog);
            println!("  PARSE: OK");
            println!("  rule counts (top 12):");
            let mut sorted: Vec<_> = counts.into_iter().collect();
            sorted.sort_by(|a, b| b.1.cmp(&a.1));
            for (rule, n) in sorted.iter().take(12) {
                println!("    {:>6}  {}", n, rule);
            }
            // What fell into prose_fragment vs substrate?
            let prose = sorted.iter().find(|(r, _)| r == "prose_fragment").map(|(_, n)| *n).unwrap_or(0);
            let total: usize = sorted.iter().map(|(_, n)| *n).sum();
            let prose_pct = if total > 0 { 100.0 * prose as f64 / total as f64 } else { 0.0 };
            println!("  prose fraction: {}/{} = {:.1}%", prose, total, prose_pct);
        }
        Err(e) => {
            println!("  PARSE: FAIL");
            println!("  {}", e);
        }
    }
}

fn main() {
    let ssot_path = std::env::args().nth(1).expect("usage: dsl-smoke <ssot.md>");
    let text = fs::read_to_string(&ssot_path).expect("SSOT.md not readable");
    let lines: Vec<&str> = text.lines().collect();

    // Content-anchored slices. Each stress region is located by a stable,
    // distinctive substring in the catalyst, NOT by a hardcoded line number — so
    // the test tracks the living SSOT through refactors instead of drifting every
    // time content above it moves. The predecessor pinned line ranges and had to
    // hand-recalibrate -3 on 2026-05-31; the 2026-06-05 refactor (449 deletions)
    // then moved everything far enough to break all six at once. Anchoring on
    // content ends that whole failure mode. Labels carry no line numbers on
    // purpose: the label is the slice's stable identity for the iteration
    // ledger's regression tracking, so it must not move when the catalyst does.
    let slice_from = |anchor: &str, count: usize| -> String {
        match lines.iter().position(|l| l.contains(anchor)) {
            Some(i) => lines[i..(i + count).min(lines.len())].join("\n"),
            None => String::new(), // anchor gone -> empty -> PARSE FAIL, surfaced honestly
        }
    };

    // (anchor, window_lines, stress label)
    let specs: [(&str, usize, &str); 6] = [
        ("Trinity-Formula", 40, "Trinity Formula + K-CUP (substrate-heavy)"),
        ("Emoji-Semantic-Layer", 25, "ESL emoji declaration (emoji stress)"),
        ("0.75. Decorator Invocation Protocol", 85, "Invocation Protocol 0.75 (invocation stress)"),
        ("CRC Registry (`CR`)", 13, "CRC registry (table stress)"),
        ("| **Tier** | **Organ** | **Body System**", 30, "Organ canon table (table stress)"),
        ("```ankh", 12, "Ankh code block (code-block stress)"),
    ];

    let texts: Vec<String> = specs.iter().map(|&(a, c, _)| slice_from(a, c)).collect();
    let mut slices: Vec<Slice> = Vec::new();
    for (i, &(_, _, label)) in specs.iter().enumerate() {
        slices.push(Slice { label, text: texts[i].as_str() });
    }

    println!("=== CHTHONIC DSL Phase 0 Smoke Test ===");
    println!("Grammar:  .chthonic/grammar/chthonic.peg");
    println!("Catalyst: .chthonic/SSOT.md ({} bytes, {} lines)", text.len(), lines.len());

    for s in &slices {
        smoke(s);
    }

    println!("\n=== END SMOKE ===");
}
