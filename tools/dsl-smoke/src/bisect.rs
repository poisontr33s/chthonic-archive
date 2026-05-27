use pest::Parser;
use pest_derive::Parser;
use std::fs;

#[derive(Parser)]
#[grammar = "chthonic.pest"]
struct ChthonicParser;

fn main() {
    let path = std::env::args().nth(1).expect("usage: bisect <ssot>");
    let text = fs::read_to_string(&path).expect("readable");
    let lines: Vec<&str> = text.lines().collect();

    // Slice 4 range: SSOT L2000..=2050 (0-indexed 1999..=2049)
    let slice_start = 1999;
    let slice_end = 2049;
    let total = slice_end - slice_start + 1;

    // Try each prefix of the slice — first that fails tells us the boundary line.
    for n in 1..=total {
        let prefix = lines[slice_start..slice_start + n].join("\n");
        let result = match ChthonicParser::parse(Rule::program, &prefix) {
            Ok(_) => "OK",
            Err(_) => "FAIL",
        };
        if result == "FAIL" || n == total {
            println!("prefix lines 1..{} ({} lines, {} bytes): {}", n, n, prefix.len(), result);
            if result == "FAIL" {
                if let Err(e) = ChthonicParser::parse(Rule::program, &prefix) {
                    println!("  {}", e);
                }
                // Try with one less line to confirm the boundary
                if n > 1 {
                    let smaller = lines[slice_start..slice_start + n - 1].join("\n");
                    let r2 = match ChthonicParser::parse(Rule::program, &smaller) {
                        Ok(_) => "OK",
                        Err(_) => "FAIL",
                    };
                    println!("prefix lines 1..{}: {}", n - 1, r2);
                }
                break;
            }
        }
    }
}
