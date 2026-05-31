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

    // Build slices by line range. Each slice is rejoined with \n.
    let slice_lines = |start: usize, end: usize| -> String {
        lines[start.saturating_sub(1)..end.min(lines.len())].join("\n")
    };

    // Line anchors are −3 vs the pre-2026-05-31 calibration: purifying three
    // injected operational-meta lines from the §0 governance preamble (L45/47/50,
    // stale seal + codex-injected Update-Protocol + .github file-path constraint)
    // shifted all content below the preamble up by 3 lines.
    let trinity = slice_lines(67, 127);          // Trinity Formula / K-CUP block
    let esl_emoji = slice_lines(92, 112);         // ESL emoji declaration region
    let invocation = slice_lines(1112, 1197);     // §0.75 invocation examples
    let crc_table = slice_lines(1997, 2047);      // §IV CRC registry region
    let organ_canon = slice_lines(282, 337);      // §295-326 Organ table
    let inline_script_region = slice_lines(8482, 8547);  // suspected inline-script region

    let slices = vec![
        Slice { label: "Trinity Formula + K-CUP (L67-127, substrate-heavy)", text: &trinity },
        Slice { label: "ESL emoji declaration (L92-112, emoji stress)", text: &esl_emoji },
        Slice { label: "Invocation examples (L1112-1197, invocation stress)", text: &invocation },
        Slice { label: "CRC registry (L1997-2047, table stress)", text: &crc_table },
        Slice { label: "Organ canon table (L282-337, table stress)", text: &organ_canon },
        Slice { label: "Suspected inline-script region (L8482-8547, code-block stress)", text: &inline_script_region },
    ];

    println!("=== CHTHONIC DSL Phase 0 Smoke Test ===");
    println!("Grammar:  .chthonic/grammar/chthonic.peg");
    println!("Catalyst: .chthonic/SSOT.md ({} bytes, {} lines)", text.len(), lines.len());

    for s in &slices {
        smoke(s);
    }

    println!("\n=== END SMOKE ===");
}
