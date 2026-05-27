use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;
use std::env;
use std::fmt::Write as _;
use std::fs;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

const LOCAL_LLM_URL: &str = "http://127.0.0.1:5000/v1/chat/completions";
const MODEL_NAME: &str = "Llama-3.1-8B-Instruct-exl2-8.0bpw";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum OutputFormat {
    Markdown,
    Json,
}

#[derive(Debug)]
struct Cli {
    input: PathBuf,
    output: Option<PathBuf>,
    format: OutputFormat,
}

#[derive(Debug, Deserialize, Default)]
struct ContextPacket {
    packet_id: Option<String>,
    intent: Option<String>,
    summary: Option<String>,
    files: Option<Vec<FileHint>>,
    interfaces: Option<Vec<InterfaceHint>>,
    constraints: Option<Vec<String>>,
    tasks: Option<Vec<String>>,
    tags: Option<Vec<String>>,
}

#[derive(Debug, Deserialize, Clone)]
struct FileHint {
    path: String,
    purpose: Option<String>,
}

#[derive(Debug, Deserialize, Clone)]
struct InterfaceHint {
    name: String,
    path: Option<String>,
    contract: Option<String>,
}

#[derive(Debug, Serialize)]
struct CompressedContext {
    packet_id: String,
    objective: String,
    priority_files: Vec<String>,
    interfaces: Vec<String>,
    constraints: Vec<String>,
    tasks: Vec<String>,
    tags: Vec<String>,
}

// LLM structs
#[derive(Serialize)]
struct ChatCompletionRequest {
    model: String,
    messages: Vec<ChatMessage>,
    temperature: f32,
    max_tokens: u32,
}

#[derive(Serialize, Deserialize)]
struct ChatMessage {
    role: String,
    content: String,
}

#[derive(Deserialize)]
struct ChatCompletionResponse {
    choices: Vec<ChatChoice>,
}

#[derive(Deserialize)]
struct ChatChoice {
    message: ChatMessage,
}

#[derive(Debug, Deserialize, Default)]
struct FileAnalysis {
    #[serde(default)]
    purpose: String,
    #[serde(default)]
    interfaces: Vec<String>,
}

#[tokio::main]
async fn main() {
    match run().await {
        Ok(()) => {}
        Err(err) => {
            eprintln!("context-compressor: {err}");
            std::process::exit(1);
        }
    }
}

async fn run() -> Result<(), String> {
    let cli = parse_args()?;

    // If input is a directory, we generate a packet from it
    let packet = if cli.input.is_dir() {
        generate_packet_from_dir(&cli.input).await?
    } else {
        let raw = fs::read_to_string(&cli.input)
            .map_err(|e| format!("failed to read input '{}': {e}", cli.input.display()))?;
        parse_packet(&cli.input, &raw)?
    };

    let compact = compress(packet);

    let rendered = match cli.format {
        OutputFormat::Json => serde_json::to_string_pretty(&compact)
            .map_err(|e| format!("failed to serialize JSON output: {e}"))?,
        OutputFormat::Markdown => render_markdown(&compact),
    };

    if let Some(output) = cli.output {
        fs::write(&output, rendered)
            .map_err(|e| format!("failed to write output '{}': {e}", output.display()))?;
        println!("wrote {}", output.display());
    } else {
        println!("{rendered}");
    }

    Ok(())
}

async fn generate_packet_from_dir(dir: &Path) -> Result<ContextPacket, String> {
    println!("Scanning directory: {}", dir.display());
    let mut file_hints = Vec::new();
    let mut interface_hints = Vec::new();
    let constraints = Vec::new();

    let client = reqwest::Client::new();

    for entry in WalkDir::new(dir).into_iter().filter_map(|e| e.ok()) {
        let path = entry.path();
        if path.is_file() {
            if let Some(ext) = path.extension().and_then(|s| s.to_str()) {
                if matches!(ext, "rs" | "ts" | "js" | "py" | "toml" | "json" | "md") {
                    // Quick filter for lockfiles and very large sources.
                    if path.to_string_lossy().contains("lock")
                        || path.metadata().map(|m| m.len() > 200_000).unwrap_or(false)
                    {
                        continue;
                    }
                    
                    match process_file(&client, dir, path).await {
                        Ok((hint, intfs)) => {
                            file_hints.push(hint);
                            interface_hints.extend(intfs);
                        },
                        Err(e) => eprintln!("Failed to process {}: {}", path.display(), e),
                    }
                }
            }
        }
    }

    Ok(ContextPacket {
        packet_id: Some(format!("auto-scan-{}", chrono::Local::now().format("%Y%m%d-%H%M%S"))),
        intent: Some(format!("Context scan of {}", dir.display())),
        summary: Some("Auto-generated context packet from directory scan via Reflex Cortex.".to_string()),
        files: Some(file_hints),
        interfaces: Some(interface_hints),
        constraints: Some(constraints),
        tasks: None,
        tags: Some(vec!["auto-generated".to_string(), "reflex-cortex".to_string()]),
    })
}

async fn process_file(
    client: &reqwest::Client,
    root_dir: &Path,
    path: &Path,
) -> Result<(FileHint, Vec<InterfaceHint>), String> {
    let content = fs::read_to_string(path).map_err(|e| e.to_string())?;
    let rel_path = path
        .strip_prefix(root_dir)
        .unwrap_or(path)
        .to_string_lossy()
        .to_string();

    let prompt = format!(
        "Analyze this source file and output ONLY valid JSON.\n\
         Schema:\n\
         {{\"purpose\": string, \"interfaces\": string[]}}\n\
         Rules:\n\
         - no markdown\n\
         - no preamble\n\
         - no explanation\n\
         - do not output placeholders like `fn a(...)` or `struct X`\n\
         - interfaces must be actual symbols from this file\n\
         - if none, use []\n\n\
         File: {rel_path}\n\
         Code:\n```\n{content}\n```"
    );

    let request = ChatCompletionRequest {
        model: MODEL_NAME.to_string(),
        messages: vec![
            ChatMessage {
                role: "system".to_string(),
                content: "You extract structured code summaries. Reply with ONLY one JSON object and nothing else."
                    .to_string(),
            },
            ChatMessage { role: "user".to_string(), content: prompt },
        ],
        temperature: 0.0,
        max_tokens: 320,
    };

    let resp = client
        .post(LOCAL_LLM_URL)
        .json(&request)
        .send()
        .await
        .map_err(|e| format!("LLM request failed: {e}"))?;

    if !resp.status().is_success() {
        return Err(format!("LLM request failed with HTTP {}", resp.status()));
    }

    let chat_resp: ChatCompletionResponse = resp
        .json()
        .await
        .map_err(|e| format!("Failed to parse LLM response: {e}"))?;
    let raw_content = chat_resp
        .choices
        .first()
        .ok_or("No choices in LLM response")?
        .message
        .content
        .clone();

    let parsed = parse_file_analysis(&raw_content).unwrap_or_else(|| FileAnalysis {
        purpose: sanitize_single_line(&raw_content, 180),
        interfaces: Vec::new(),
    });

    let local_interfaces = extract_local_interfaces(&content);
    let mut parsed_interfaces = parsed
        .interfaces
        .into_iter()
        .filter(|i| !i.trim().is_empty())
        .filter(|i| !is_placeholder_interface(i))
        .map(|name| sanitize_single_line(&name, 180))
        .collect::<Vec<_>>();

    if parsed_interfaces.is_empty() {
        parsed_interfaces = local_interfaces;
    }

    let interfaces = parsed_interfaces
        .into_iter()
        .map(|name| InterfaceHint {
            name,
            path: Some(rel_path.clone()),
            contract: None,
        })
        .collect::<Vec<_>>();

    let mut purpose = sanitize_single_line(&parsed.purpose, 180);
    if looks_chatty_purpose(&purpose) || purpose == "n/a" {
        purpose = synthesize_purpose(&rel_path, &interfaces);
    }

    Ok((
        FileHint {
            path: rel_path,
            purpose: Some(purpose),
        },
        interfaces,
    ))
}

fn parse_file_analysis(raw: &str) -> Option<FileAnalysis> {
    if let Ok(parsed) = serde_json::from_str::<FileAnalysis>(raw.trim()) {
        return Some(parsed);
    }

    if let Some(json_block) = extract_json_fence(raw) {
        if let Ok(parsed) = serde_json::from_str::<FileAnalysis>(json_block.trim()) {
            return Some(parsed);
        }
    }

    if let Some(object) = extract_first_json_object(raw) {
        if let Ok(parsed) = serde_json::from_str::<FileAnalysis>(object.trim()) {
            return Some(parsed);
        }
    }

    None
}

fn extract_first_json_object(raw: &str) -> Option<String> {
    let mut start = None;
    let mut depth = 0usize;
    let mut in_string = false;
    let mut escaped = false;

    for (idx, ch) in raw.char_indices() {
        if start.is_none() {
            if ch == '{' {
                start = Some(idx);
                depth = 1;
            }
            continue;
        }

        if in_string {
            if escaped {
                escaped = false;
            } else if ch == '\\' {
                escaped = true;
            } else if ch == '"' {
                in_string = false;
            }
            continue;
        }

        match ch {
            '"' => in_string = true,
            '{' => depth += 1,
            '}' => {
                if depth == 0 {
                    return None;
                }
                depth -= 1;
                if depth == 0 {
                    let s = start?;
                    return Some(raw[s..=idx].to_string());
                }
            }
            _ => {}
        }
    }

    None
}

fn sanitize_single_line(input: &str, max_chars: usize) -> String {
    let compact = input.split_whitespace().collect::<Vec<_>>().join(" ");
    let trimmed = compact.trim();
    if trimmed.is_empty() {
        return "n/a".to_string();
    }
    trimmed.chars().take(max_chars).collect()
}

fn is_placeholder_interface(value: &str) -> bool {
    let lower = value.to_ascii_lowercase();
    lower.contains("fn a(")
        || lower.contains("struct x")
        || lower.contains("{...}")
        || lower.contains("example")
}

fn looks_chatty_purpose(value: &str) -> bool {
    let lower = value.to_ascii_lowercase();
    lower.starts_with("here is")
        || lower.contains("json object")
        || lower.contains("purpose")
        || lower.contains("schema")
}

fn synthesize_purpose(path: &str, interfaces: &[InterfaceHint]) -> String {
    if interfaces.is_empty() {
        format!("{path} source file (no explicit public interfaces detected)")
    } else {
        format!(
            "{path} source file with {} detected interface(s)",
            interfaces.len()
        )
    }
}

fn extract_local_interfaces(content: &str) -> Vec<String> {
    let mut out = Vec::new();
    for raw_line in content.lines() {
        let line = raw_line.trim();
        if line.is_empty() || line.starts_with("//") || line.starts_with('#') {
            continue;
        }
        let starts_candidate = line.starts_with("fn ")
            || line.starts_with("pub fn ")
            || line.starts_with("async fn ")
            || line.starts_with("pub async fn ")
            || line.starts_with("struct ")
            || line.starts_with("pub struct ")
            || line.starts_with("enum ")
            || line.starts_with("pub enum ")
            || line.starts_with("trait ")
            || line.starts_with("pub trait ")
            || line.starts_with("impl ");

        if starts_candidate {
            out.push(sanitize_single_line(line, 180));
        }
        if out.len() >= 24 {
            break;
        }
    }
    out
}


fn parse_args() -> Result<Cli, String> {
    let mut input: Option<PathBuf> = None;
    let mut output: Option<PathBuf> = None;
    let mut format = OutputFormat::Markdown;

    let mut args = env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "-i" | "--in" => {
                let value = args
                    .next()
                    .ok_or_else(|| "missing value for --in".to_string())?;
                input = Some(PathBuf::from(value));
            }
            "-o" | "--out" => {
                let value = args
                    .next()
                    .ok_or_else(|| "missing value for --out".to_string())?;
                output = Some(PathBuf::from(value));
            }
            "-f" | "--format" => {
                let value = args
                    .next()
                    .ok_or_else(|| "missing value for --format".to_string())?;
                format = match value.as_str() {
                    "md" | "markdown" => OutputFormat::Markdown,
                    "json" => OutputFormat::Json,
                    _ => {
                        return Err(format!(
                            "invalid format '{value}'; use 'md' or 'json'"
                        ))
                    }
                };
            }
            "-h" | "--help" => {
                print_help();
                std::process::exit(0);
            }
            _ => {
                return Err(format!(
                    "unknown argument '{arg}'. Use --help for usage."
                ))
            }
        }
    }

    let input = input.ok_or_else(|| "missing --in <path> argument".to_string())?;
    Ok(Cli {
        input,
        output,
        format,
    })
}

fn parse_packet(input: &Path, raw: &str) -> Result<ContextPacket, String> {
    if input
        .extension()
        .and_then(|s| s.to_str())
        .is_some_and(|ext| ext.eq_ignore_ascii_case("json"))
    {
        return serde_json::from_str(raw)
            .map_err(|e| format!("invalid JSON context packet: {e}"));
    }

    if let Some(json_block) = extract_json_fence(raw) {
        return serde_json::from_str(&json_block)
            .map_err(|e| format!("invalid JSON block in markdown packet: {e}"));
    }

    parse_markdown_fallback(raw)
}

fn extract_json_fence(raw: &str) -> Option<String> {
    let fence = "```json";
    let start = raw.find(fence)?;
    let body = &raw[(start + fence.len())..];
    let end = body.find("```")?;
    Some(body[..end].trim().to_string())
}

fn parse_markdown_fallback(raw: &str) -> Result<ContextPacket, String> {
    let intent = section_text(raw, "Intent")
        .or_else(|| section_text(raw, "Objective"))
        .or_else(|| first_non_empty_paragraph(raw));
    let summary = section_text(raw, "Summary").or_else(|| section_text(raw, "System State"));
    let constraints = section_bullets(raw, "Constraints");
    let tasks = section_bullets(raw, "Tasks");

    if intent.is_none() && summary.is_none() && constraints.is_empty() && tasks.is_empty() {
        return Err(
            "could not parse markdown packet. Provide JSON, a ```json code block, or headers like ## Intent/## Tasks."
                .to_string(),
        );
    }

    Ok(ContextPacket {
        packet_id: None,
        intent,
        summary,
        files: None,
        interfaces: None,
        constraints: if constraints.is_empty() {
            None
        } else {
            Some(constraints)
        },
        tasks: if tasks.is_empty() { None } else { Some(tasks) },
        tags: None,
    })
}

fn section_text(raw: &str, title: &str) -> Option<String> {
    let normalized = raw.replace("\r\n", "\n");
    let lines: Vec<&str> = normalized.lines().collect();
    let marker = format!("## {title}");
    let mut idx = None;
    for (i, line) in lines.iter().enumerate() {
        if line.trim() == marker {
            idx = Some(i + 1);
            break;
        }
    }
    let start = idx?;
    let mut buf = String::new();
    for line in &lines[start..] {
        let trimmed = line.trim();
        if trimmed.starts_with("## ") {
            break;
        }
        if !trimmed.is_empty() {
            if !buf.is_empty() {
                buf.push(' ');
            }
            buf.push_str(trimmed);
        }
    }
    if buf.is_empty() {
        None
    } else {
        Some(buf)
    }
}

fn section_bullets(raw: &str, title: &str) -> Vec<String> {
    let normalized = raw.replace("\r\n", "\n");
    let lines: Vec<&str> = normalized.lines().collect();
    let marker = format!("## {title}");
    let mut idx = None;
    for (i, line) in lines.iter().enumerate() {
        if line.trim() == marker {
            idx = Some(i + 1);
            break;
        }
    }
    let Some(start) = idx else {
        return Vec::new();
    };

    let mut out = Vec::new();
    for line in &lines[start..] {
        let trimmed = line.trim();
        if trimmed.starts_with("## ") {
            break;
        }
        if let Some(item) = trimmed.strip_prefix("- ") {
            out.push(item.trim().to_string());
        } else if let Some(item) = trimmed.strip_prefix("* ") {
            out.push(item.trim().to_string());
        }
    }
    out
}

fn first_non_empty_paragraph(raw: &str) -> Option<String> {
    for line in raw.replace("\r\n", "\n").lines() {
        let t = line.trim();
        if t.is_empty() || t.starts_with('#') || t.starts_with("```") {
            continue;
        }
        return Some(t.to_string());
    }
    None
}

fn compress(packet: ContextPacket) -> CompressedContext {
    let packet_id = packet
        .packet_id
        .unwrap_or_else(|| "context-packet-unlabeled".to_string());
    let objective = packet
        .intent
        .or(packet.summary)
        .unwrap_or_else(|| "No objective provided".to_string());

    let mut priority_files = Vec::new();
    if let Some(files) = packet.files {
        for f in files {
            let mut line = f.path;
            if let Some(purpose) = f.purpose {
                line.push_str(" :: ");
                line.push_str(purpose.trim());
            }
            priority_files.push(line);
        }
    }

    let mut interfaces = Vec::new();
    if let Some(intfs) = packet.interfaces {
        for i in intfs {
            let mut line = i.name;
            if let Some(path) = i.path {
                if !path.trim().is_empty() {
                    line.push_str(" @ ");
                    line.push_str(path.trim());
                }
            }
            if let Some(contract) = i.contract {
                if !contract.trim().is_empty() {
                    line.push_str(" -> ");
                    line.push_str(contract.trim());
                }
            }
            interfaces.push(line);
        }
    }

    let constraints = packet.constraints.unwrap_or_default();
    let tasks = packet.tasks.unwrap_or_default();
    let mut tags_set: BTreeSet<String> = BTreeSet::new();
    for tag in packet.tags.unwrap_or_default() {
        if !tag.trim().is_empty() {
            tags_set.insert(tag.trim().to_ascii_lowercase());
        }
    }

    CompressedContext {
        packet_id,
        objective,
        priority_files,
        interfaces,
        constraints,
        tasks,
        tags: tags_set.into_iter().collect(),
    }
}

fn render_markdown(ctx: &CompressedContext) -> String {
    let mut out = String::new();
    let _ = writeln!(out, "# Compressed Context");
    let _ = writeln!(out);
    let _ = writeln!(out, "- Packet: `{}`", ctx.packet_id);
    let _ = writeln!(out, "- Objective: {}", ctx.objective);
    if !ctx.tags.is_empty() {
        let _ = writeln!(out, "- Tags: {}", ctx.tags.join(", "));
    }
    let _ = writeln!(out);

    render_section(&mut out, "Priority Files", &ctx.priority_files);
    render_section(&mut out, "Interfaces", &ctx.interfaces);
    render_section(&mut out, "Constraints", &ctx.constraints);
    render_section(&mut out, "Tasks", &ctx.tasks);

    out
}

fn render_section(out: &mut String, title: &str, items: &[String]) {
    let _ = writeln!(out, "## {title}");
    if items.is_empty() {
        let _ = writeln!(out, "- (none)");
    } else {
        for item in items {
            let _ = writeln!(out, "- {}", item.trim());
        }
    }
    let _ = writeln!(out);
}

fn print_help() {
    println!(
        "context-compressor\n\
         Compresses Context Packets (JSON/Markdown) or scans a directory using the local Reflex endpoint.\n\n\
         Usage:\n\
           cargo run -- --in <packet-or-dir> [--out <output-path>] [--format md|json]\n\n\
         Options:\n\
           -i, --in       Input packet path (.json/.md) or directory to scan\n\
           -o, --out      Optional output path (prints to stdout if omitted)\n\
           -f, --format   Output format: md (default) or json\n\
           -h, --help     Show this help\n"
    );
}
