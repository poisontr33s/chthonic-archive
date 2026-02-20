# Compressed Context

- Packet: `auto-scan-20260220-054235`
- Objective: Context scan of src
- Tags: auto-generated, reflex-cortex

## Priority Files
- main.rs :: main.rs source file with 24 detected interface(s)

## Interfaces
- enum OutputFormat { @ main.rs
- struct Cli { @ main.rs
- struct ContextPacket { @ main.rs
- struct FileHint { @ main.rs
- struct InterfaceHint { @ main.rs
- struct CompressedContext { @ main.rs
- struct ChatCompletionRequest { @ main.rs
- struct ChatMessage { @ main.rs
- struct ChatCompletionResponse { @ main.rs
- struct ChatChoice { @ main.rs
- struct FileAnalysis { @ main.rs
- async fn main() { @ main.rs
- async fn run() -> Result<(), String> { @ main.rs
- async fn generate_packet_from_dir(dir: &Path) -> Result<ContextPacket, String> { @ main.rs
- async fn process_file( @ main.rs
- fn parse_file_analysis(raw: &str) -> Option<FileAnalysis> { @ main.rs
- fn extract_first_json_object(raw: &str) -> Option<String> { @ main.rs
- fn sanitize_single_line(input: &str, max_chars: usize) -> String { @ main.rs
- fn is_placeholder_interface(value: &str) -> bool { @ main.rs
- fn looks_chatty_purpose(value: &str) -> bool { @ main.rs
- fn synthesize_purpose(path: &str, interfaces: &[InterfaceHint]) -> String { @ main.rs
- fn extract_local_interfaces(content: &str) -> Vec<String> { @ main.rs
- fn parse_args() -> Result<Cli, String> { @ main.rs
- fn parse_packet(input: &Path, raw: &str) -> Result<ContextPacket, String> { @ main.rs

## Constraints
- (none)

## Tasks
- (none)

