use pest::Parser;
use pest_derive::Parser;
use std::fs;

#[derive(Parser)]
#[grammar = "chthonic.pest"]
struct ChthonicParser;

fn try_parse(label: &str, input: &str) {
    println!("\n=== PROBE: {} ===", label);
    println!("input (len {}): {:?}", input.len(), &input[..input.len().min(120)]);
    match ChthonicParser::parse(Rule::program, input) {
        Ok(_) => println!("  PARSE: OK"),
        Err(e) => println!("  PARSE: FAIL\n  {}", e),
    }
}

fn main() {
    let ssot_path = std::env::args().nth(1).expect("usage: probe <ssot.md>");
    let text = fs::read_to_string(&ssot_path).expect("readable");
    let lines: Vec<&str> = text.lines().collect();

    // Slice 4's problem line (SSOT L2050, slice line 51)
    let problem_line = lines[2049];   // 0-indexed
    
    // Try the line alone
    try_parse("L2050 alone", problem_line);
    
    // Try L2050 with trailing newline
    try_parse("L2050 + \n", &format!("{}\n", problem_line));
    
    // Try just the final fragment: `**PS**.`
    try_parse("just **PS**.", "**PS**.");
    
    // Try just **PS**
    try_parse("just **PS**", "**PS**");
    
    // Try just `**'X'**` to see if curly quotes break things
    try_parse("**'X'**", "**\u{2018}X\u{2019}**");
    
    // Try `**X**.` with trailing period (the suspicious case)
    try_parse("**X**.", "**X**.");
    
    // Try `**(X)**` substrate-shape
    try_parse("**(X)**", "**(X)**");
    
    // The simplest possible bold_prose + dot
    try_parse("**AA**.", "**AA**.");
}
