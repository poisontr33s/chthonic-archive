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
    println!("  first 80: {:?}", &slice.text[..slice.text.len().min(80)]);

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

    // Build slices by line range. Each slice is rejoined with \n.
    let slice_lines = |start: usize, end: usize| -> String {
        lines[start.saturating_sub(1)..end.min(lines.len())].join("\n")
    };

    let trinity = slice_lines(70, 130);          // Trinity Formula / K-CUP block
    let esl_emoji = slice_lines(95, 115);         // ESL emoji declaration region
    let invocation = slice_lines(1115, 1200);     // §0.75 invocation examples
    let crc_table = slice_lines(2000, 2050);      // §IV CRC registry region
    let organ_canon = slice_lines(285, 340);      // §295-326 Organ table
    let inline_script_region = slice_lines(8485, 8550);  // suspected inline-script region

    let slices = vec![
        Slice { label: "Trinity Formula + K-CUP (L70-130, substrate-heavy)", text: &trinity },
        Slice { label: "ESL emoji declaration (L95-115, emoji stress)", text: &esl_emoji },
        Slice { label: "Invocation examples (L1115-1200, invocation stress)", text: &invocation },
        Slice { label: "CRC registry (L2000-2050, table stress)", text: &crc_table },
        Slice { label: "Organ canon table (L285-340, table stress)", text: &organ_canon },
        Slice { label: "Suspected inline-script region (L8485-8550, code-block stress)", text: &inline_script_region },
    ];

    println!("=== CHTHONIC DSL Phase 0 Smoke Test ===");
    println!("Grammar:  .chthonic/grammar/chthonic.peg");
    println!("Catalyst: .chthonic/SSOT.md ({} bytes, {} lines)", text.len(), lines.len());

    for s in &slices {
        smoke(s);
    }

    println!("\n=== END SMOKE ===");
}
