# context-compressor

Rust CLI for Chthonic Neural Bus packet compression.

This tool ingests a Context Packet and emits a compact handoff for Codex fabrication:
- JSON packet input (`.json`)
- Markdown-hybrid packet input (`.md`) with embedded ` ```json ` block
- Fallback markdown parsing for `## Intent`, `## Constraints`, `## Tasks`

## Build

```powershell
cargo build --manifest-path extensions/context-compressor/Cargo.toml
```

## Usage

```powershell
cargo run --manifest-path extensions/context-compressor/Cargo.toml -- --in <packet-path>
```

Options:
- `--out <path>` write output to file (stdout if omitted)
- `--format md|json` output format (default: `md`)

Examples:

```powershell
cargo run --manifest-path extensions/context-compressor/Cargo.toml -- --in packet.json --format md
cargo run --manifest-path extensions/context-compressor/Cargo.toml -- --in packet.md --format json --out compact.json
```

## Packet Contract

Canonical schema:
- `extensions/context-compressor/packet.schema.json`

Minimum required field:
- `intent: string`

