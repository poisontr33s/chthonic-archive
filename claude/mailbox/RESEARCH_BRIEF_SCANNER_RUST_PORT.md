---
type: research_brief
status: open
created: 2026-05-29
dispatcher: conductor (the-Savant)
target: external research (Gemini DR / equivalent) — to run in parallel with the Rust port itself
scope: validate bias + name limitations before/during the Bun → Rust port of the chthonic-archive spread scanner
---

# Research brief — Scanner V2.2 → Rust port: bias, limitations, canonical choices

## Context (self-contained)

A polyglot workspace scanner (`scripts/spread-value.ts`, V2.2 in Bun) has shipped and proven its shape on a 158 GiB / 52,212-file snipe set across 21 projects spanning Rust, TypeScript, Python, CUDA/Vulkan, Unity (`.cs`/`.meta`/`.asmdef`), and many other languages. The scanner produces:

- Per-project file inventory with extension histograms, line counts, bucket classification (source/config/doc/asset/binary/unknown)
- SHA256 content fingerprint per file with `.spread/file_index.ndjson` cache (path+size+mtime invalidation)
- Workspace-wide duplicate-cluster map sorted by bytes-wasted
- Magic-byte detection (hand-rolled, ~30 rules) for unknown/binary files, surfacing extension/content mismatches (e.g. `.pt`/`.pth`/`.bin` actually being ZIP archives)
- Salvage classifier with verdicts (chthonic-member / absorb-candidate / mirror-of / independent / unclassified) and snipe/sweep/noise mode hints

On a warm-cache run the Bun scanner hits 99.5% cache hit rate and completes in seconds. First (cold) run takes a few minutes.

The intended Rust port targets the workspace at `extensions/chthonic-archive/native/` as a sibling to two existing Rust bridges (`chthonic-copilot-bridge` using `github-copilot-sdk = 1.0.0-beta.9`, and `chthonic-acp-bridge` using `agent-client-protocol = 0.12`). The crate would be `chthonic-scanner`, following the same v9-baseline skeleton (`edition = "2024"` per-crate, `version.workspace = true`, clap-driven CLI, tracing-subscriber to stderr).

The next-iteration roadmap after the V2.2 port is V2.3 (MinHash near-duplicate detection, symbol extraction across languages) and V2.4 (optional GPU acceleration via wgpu/ash on the user's RTX 4090).

## Questions

Six clusters of questions, ordered by likely impact on the port decision.

### 1. Performance — which parts are actually faster in Rust, and by how much

The assumption is Rust is uniformly faster than Bun for this workload. That's likely wrong in detail.

1.1. **SHA256 throughput.** Bun uses Node's `crypto` (OpenSSL via N-API). Does it use SHA-NI hardware acceleration on Windows 11 x64 hosts? If yes, the Rust gap (via `sha2` crate with `asm` feature) is likely small for the CPU portion. Benchmark needed: hashing 10,000 files of mixed sizes (1 KB to 10 MB) in Bun vs Rust on the same hardware. Expected gap?

1.2. **File walking.** Bun uses libuv via `node:fs.readdirSync`. Rust has `walkdir`, `ignore` (faster, but respects .gitignore which we explicitly *don't* want per conductor directive), and raw `std::fs::read_dir`. For a 50k-file walk on NTFS, what's the realistic ceiling — and how much is disk-I/O-bound (syscall + read amplification) vs language overhead?

1.3. **Cache I/O.** NDJSON write + parse of ~50k rows. Bun is fast at JSON (built-in parser, fast string ops); Rust would use `serde_json` line-by-line. For this row count, is the Rust win measurable? Worth considering `bincode` or `rmp-serde` (MessagePack) for a more compact cache format?

1.4. **Disk I/O ceiling on user's hardware.** What's the practical read-throughput floor on the conductor's NVMe SSD for 50,000 small (<32 KB) files vs 5,000 medium (~1 MB) files vs 50 large (>10 MB) files? This sets a hard floor below which language choice doesn't matter.

### 2. Hashing strategy — full SHA256 vs cheap-fingerprint-then-deep

The current V2.2 always full-hashes everything under 50 MB. This is wasteful when most files are obviously unique.

2.1. Is there a canonical "cheap fingerprint" pattern: e.g. (size + first 1 KB + last 1 KB + middle 1 KB) hashed → if collision, do full SHA256? What's the false-collision rate?

2.2. For files that need full hashing, is `memmap2` (memory-mapped reads) faster than `std::fs::read`/`fs::File::read_to_end` on Windows? Specifically for files in the 1-50 MB range that don't fit in a single read syscall.

2.3. Is parallel hashing via `rayon::par_iter` a clear win, or do parallel reads on a single SSD thrash and underperform sequential? Expected concurrency sweet spot on NVMe vs SATA?

### 3. Magic-byte detection — canonical Rust library

V2.2 hand-rolls ~30 magic rules. Several canonical Rust options exist:

3.1. **`infer`** (pure-Rust, no native deps, ~120 formats, easy embedding)
3.2. **`tree_magic_mini`** (libmagic-derived in pure Rust, broader format coverage, larger embedded DB)
3.3. **`libmagic-sys`** (FFI binding to the system C `libmagic`, broadest coverage but introduces a native dep)
3.4. **`file-format`** (more recent, claims ~200 formats)

Comparison needed: format coverage matrix specifically for ML/GPU artifacts (`safetensors`, `gguf`, `onnx`, `pytorch .pt`, `.spv` SPIR-V, NVIDIA `.nvph` DXCache), Unity (`.meta`, `.asmdef`), and the long tail of `<noext>` files surfaced by V2.2. Which library catches the most without false positives?

### 4. Cache durability — NDJSON vs SQLite vs binary

V2.2 uses append-only NDJSON. At 50,000 rows it's fast enough; at 5M+ rows (full workspace including AppData) it may become slow to parse on every run.

4.1. At what row count does SQLite (via `rusqlite`) become preferable for the cache? The cache only needs key-by-path lookups + bulk insert; nothing query-rich.

4.2. Is a custom binary format (e.g. fixed-width records + path-table) worth the implementation cost vs `bincode`/MessagePack?

4.3. Should the cache be split per-project (one cache file per project root) to enable parallel cache load + write?

4.4. Is there a canonical "content-addressed cache" pattern (Bazel-style remote-cache, ccache, sccache) that maps cleanly to this scanner's needs?

### 5. Walking strategy — beyond walkdir

V2.2 has a hand-rolled walker with skip-set + vendored-path-pattern filter. Rust options:

5.1. **`walkdir`** (simple recursive walker, single-threaded, respects symlinks)
5.2. **`ignore`** (parallel walker built by ripgrep, respects .gitignore by default — would need to disable that per conductor directive)
5.3. **`jwalk`** (parallel walker, faster than walkdir on many-file directories)

For a workspace with 500k+ files across deeply-nested NTFS directories, which walker produces the lowest wall-clock time after the I/O ceiling is reached?

### 6. V2.3 and V2.4 substrate — what to plan for now

The cache + dedup map (V2.2) is just the foundation. V2.3 adds MinHash near-duplicate detection, V2.4 considers GPU.

6.1. **MinHash libraries in Rust.** Survey of canonical crates: `minhash-rs`, `probminhash`, `probabilistic-collections`. Which is correct (not just fast) for k-shingle near-duplicate detection at file scale? Recommended shingle size + hash count + Jaccard threshold for source code?

6.2. **Symbol extraction across languages.** Tree-sitter has Rust bindings (`tree-sitter` + per-language `tree-sitter-rust` / `tree-sitter-typescript` / etc.). For extracting top-level declarations across 15+ languages, is tree-sitter the right substrate, or are simpler ext-aware regex extractors adequate at V2.3 scope?

6.3. **GPU MinHash.** Is there an existing crate that runs MinHash hash families on the GPU via `wgpu` compute shaders, or does this require custom WGSL? The user's RTX 4090 + existing Vulkan-lab scaffolding at `extensions/chthonic-archive/native/cli-renderer` is the target substrate.

6.4. **Continuous indexing.** When the scanner runs as a persistent service (vs one-shot CLI), what's the canonical pattern: filesystem watcher (notify-rs) + incremental updates, or periodic re-scan with cache reuse? The Rust scanner is intended to eventually live inside the chthonic-archive VS Code extension dispatch lane.

## Anything we are biased on, without access to what IS possible from this baseline.
- *We can't know without research beyond the missing data on the modernizations as of ANNO live time and what we might be missing or architecturally redundant. Hence the need for this research brief to validate assumptions and inform the Rust port design. And whether Vulkan, Cuda, CuDDn, DLAA/DLSS, or other GPU compute APIs are worth targeting for acceleration. Or unexplored unknown libraries that could be a better fit for the scanner's specific needs. And what a poly-repo-scanner's performance ceiling looks like on the conductor's hardware, and which parts of the current Bun implementation are already "good enough" that the Rust port can skip re-implementing them in favor of focusing on the bottlenecks or repurpose bun to rust for repurposing.*

## Out of scope (for this brief)

- The Bun V2.2 scanner is not a deprecation target — both languages might coexist (Bun for ad-hoc dev exploration, Rust for the durable integrated lane). The brief assumes parallel-arsenal, not strangler-fig replacement.
- Format-specific extractors for ONNX/safetensors/.gguf header parsing — covered as a follow-up once magic detection canon is chosen.
- Cross-platform support beyond Windows 11 x64 — the conductor's environment is the primary target.

## What "good enough" looks like

A returned brief that gives:

- A concrete library pick per question with rationale (not a survey)
- Expected order-of-magnitude perf gaps where measurable (not micro-benchmarks)
- A clear "Bun is actually fine for X" verdict where applicable, so the Rust port doesn't waste cycles on parts where the gap is small
- Named failure modes for each pick (where it'll bite when scaled up)

The Rust port proceeds in parallel; this brief informs which specific crates to wire in and which V2.3/V2.4 trajectories to pre-plan for.
