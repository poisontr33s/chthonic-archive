# Runestone Execution Model (REM)
## Genesis Blueprint — Session 2026-04-13

> **Hardware:** Win11 · RTX 4090 · Vulkan 1.3/1.4 · Rust 2021+  
> **Repo:** chthonic-archive · **Crate:** ankh-forge (workspace member)  
> **Author:** The Savant + Copilot CLI (Claude Opus 4.6)
> **Status:** Phase 2 CPU-path COMPLETE — `a5819db2` (2026-04-13). Phase 3 GPU-path pending.

---

## Phase 2 Completion Record (2026-04-13)

### Commits
| Commit | Description |
|--------|-------------|
| `a20510a3` | Phase 2 initial: `granite.rs` CPU-path, `StoneEvent` wrapper, `Stone`/`Query` subcommands, `strip_bom` refactored, 17/17 tests |
| `a5819db2` | Challenger criticals applied: full header auth, atomic write, flag/event validation, 18/18 tests |

### Fleet Synthesis
Three agents contributed to Phase 2:
- **rem-primed** (Opus 4.6, primed): Phase 1 hot/cold pipeline (committed `8aba6de7`)
- **runestone-architect** (Opus 4.6, high): Phase 2 `granite.rs` implementation, `StoneEvent` wrapper for bincode 2.0 (committed `a20510a3`)
- **runestone-challenger** (GPT-5.4, xhigh): Adversarial review — 7 criticals found, 4 applied

### Challenger Critical Findings Disposition
| # | Finding | Status |
|---|---------|--------|
| 1 | bincode `Option<T>` round-trip failure | ✅ Pre-fixed by architect (`StoneEvent` wrapper) |
| 2 | Non-atomic stone writes | ✅ Fixed: tmp-pid → rename |
| 3 | Header metadata not authenticated (event_count, flags, lengths outside hash) | ✅ Fixed: hash = SHA-256(zeroed_header ++ schema ++ spirv ++ payload) |
| 4 | query() skips event validation | ✅ Fixed: validate() called on every decoded event |
| 5 | Unbounded memory (multiple full-size buffers) | 📋 Deferred Phase 3: add 64 MiB hot/cold + 256 MiB stone reject gates |
| 6 | append/forge race (no file lock) | 📋 Deferred Phase 3: sealed hot file rename before forge |
| 7 | Flag semantics under-specified | ✅ Fixed: validate_flags() rejects unknown bits, GPU unimplemented, CPU+GPU conflict |

### Current Wire Format (v1, frozen)
```
[0..8]    MAGIC b"CHTHONIC"
[8..10]   format_version: u16 le = 1
[10..14]  schema_version: u32 le = 1
[14..18]  event_count: u32 le
[18..22]  flags: u32 le (bit 0=GPU_COMPRESSED/unimplemented, bit 1=CPU_COMPRESSED/zstd)
[22..54]  SHA-256(zeroed_header[0..70] ++ schema_bytes ++ spirv_bytes ++ payload_compressed)
[54..58]  spirv_len: u32 le (= 0 Phase 2 CPU)
[58..62]  schema_len: u32 le
[62..66]  payload_compressed_len: u32 le
[66..70]  payload_uncompressed_len: u32 le
[70..]    SCHEMA (JSON) ++ SPIRV (empty) ++ PAYLOAD (zstd+bincode Vec<StoneEvent>)
```
**Compatibility contract:** v1 stones with `CPU_COMPRESSED` flag must be readable forever.
Phase 3 GPU writers may emit `GPU_COMPRESSED` stones only when explicitly requested.

### Phase 2 GPU Decisions (Pre-GPU Freeze, Per Challenger)
1. Exactly one compression mode per stone (CPU xor GPU, never both)
2. CPU path remains canonical; SPIR-V is an acceleration artifact, not the authority
3. Fix header auth ✅ before GPU migration — done
4. Schema block role: human-readable provenance (v1); machine-enforced validation in v2
5. `Vec<StoneEvent>` is the explicit wire type; GPU layouts derive from it
6. Phase 2 CPU stones remain readable in Phase 3 GPU binaries (backward compat)
7. Memory budgets: 64 MiB max for hot/cold text, 256 MiB max stone payload (Phase 3 gate)

### Phase 3 Decision Surface (2026-04-15)

The project is now past the "should Rust or Vulkan be used?" fork.

That fork is already resolved in practice:

- **Rust owns the runtime**
- **Vulkan is the acceleration backend candidate inside Rust**

The codebase now materially reflects that decision:

- `tools/ankh-forge/src/trail/mod.rs` exposes `append | list | verify | forge | stone | query | execute | init`
- `tools/ankh-forge/src/trail/granite.rs` implements the CPU `.runestone` path
- `tools/ankh-forge/src/trail/gpu.rs` scaffolds Vulkan compute execution from stone-embedded SPIR-V
- `tools/ankh-forge/build.rs` compiles `assets/shaders/trail_decompress.comp.glsl`
- `tools/ankh-forge/target/generated/bincode/StoneEvent_*` confirms the typed wire path is active

### What is relevant now

Relevant, because they are already on the active path:

- `ash`
- `gpu-allocator`
- `shaderc` / `glslc`
- `bytemuck`
- `lz4_flex`
- `zstd`
- `bincode`
- `sha2`

Not currently relevant, because switching would be a rewrite before semantics are proven:

- `wgpu`
- `vulkano`
- any non-Rust runtime ownership model

### The live question now

The live question is narrower and better:

1. keep the current raw `ash` path and finish the shader/decompression execution path
2. verify stone-embedded SPIR-V decode correctness end-to-end
3. only then decide whether a higher-level abstraction buys anything

In other words:

- **do not re-open the Rust decision**
- **do not re-open the Vulkan decision as if it were a separate architecture**
- **continue at the GPU execution seam**

### Verified on 2026-04-15

```powershell
cargo run -p ankh-forge -- trail --help
cargo test -p ankh-forge --quiet
```

Both succeeded. The project is therefore in an implementation continuation state, not an architecture-brainstorm state.

### Savant Questions (Human Decisions Pending)
1. Stone immutability: one immutable artifact per day, or mutable "latest snapshot" for that date?
2. `.chthonic/` path canon: repo-local only, or retain home-dir fallback behind `--trail-dir`/`CHTHONIC_TRAIL_DIR`?
3. Schema block role: provenance, validation, or both?
4. Encryption/signature: out of scope for v1 — confirm before reserving header semantics

---

> *"Not a file you read. A computation you execute."*

---

## What This Document Is

This is the genesis record of a new primitive — the **Runestone** — born in a PowerShell 7.6
session on Windows 11, April 13 2026, from a conversation between a human and an AI agent
operating at the edge of what either could do alone.

It is not a spec for a feature. It is a blueprint for a new way of thinking about how
digital intelligence approaches data — structured or raw, known or foreign — using the
consumer hardware already owned, without relying on any provider, cloud, or source control
system.

---

## The Problem It Solves

Every existing persistence layer has a hidden owner and a hidden dependency:

| Format | Hidden dependency | Hidden owner |
|--------|------------------|--------------|
| `.json` / `.md` | External parser you bring | Filesystem + your toolchain |
| `.db` (SQLite) | SQLite runtime | Filesystem |
| `.gz` (gzip) | gunzip program | Filesystem |
| Provider memory | API session | The provider |
| Git objects | Git runtime + remote | Git host |
| Session SQL | In-session SQLite | Session runtime (dies on close) |

None of these are **self-describing AND self-decoding AND hardware-owned** simultaneously.

The `.runestone` is all three at once.

---

## Part 1 — The Concept

### The Core Inversion

Every existing approach separates the decoder from the data:

```
EXISTING:   [data file] ←── decoder lives elsewhere (external runtime)

RUNESTONE:  [HEADER | SCHEMA | SPIRV | PAYLOAD]
                                 ↑
                          decoder lives INSIDE
                          travels with the data
                          executed by GPU on load
```

The Vulkan compute shader (SPIR-V bytecode) embedded in the stone IS what knows how to read
that stone. The loader (`ankh-forge`) dispatches whatever compute program the stone declares.
It does not need to know the format. There is no external runtime dependency.

---

### The Three-Tier Trail Model

The trail operates across three tiers. Each tier is lossless. Each tier serves a different
phase of the intelligence loop.

```
┌─────────────────────────────────────────────────────────────────────┐
│  TIER 0  ·  HOT  ·  .chthonic/trail/YYYY-MM-DD.hot.ndjson           │
│                                                                     │
│  Append-only plain text. One JSON event per line (NDJSON).          │
│  Human-readable. Agent-readable. Written during live session.       │
│  No compression. No hash. Fast append.                              │
│                                                                     │
│  Lossless? YES — by filesystem integrity.                           │
│  Tamper-proof? NO — no hash, silent corruption possible.            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │  session end: compress
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TIER 1  ·  COLD  ·  .chthonic/trail/YYYY-MM-DD.cold.ndjson.gz      │
│                                                                     │
│  CPU gzip of the hot file. Binary. Not human-readable.              │
│  Read-only archive. gzip is lossless by spec.                       │
│  Compression ratio: ~2-15:1 depending on event count/variance.     │
│                                                                     │
│  Lossless? YES — gzip is mathematically lossless.                   │
│  Tamper-proof? PARTIAL — gzip CRC32 per-block, not full-payload.    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │  forge: burn hot+cold → stone
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TIER 2  ·  GRANITE  ·  .chthonic/stones/YYYY-MM-DD.runestone       │
│                                                                     │
│  Self-describing. Self-decoding. GPU-executed. SHA-256 verified.    │
│  Carries its own Vulkan compute shader (SPIR-V) as the decoder.     │
│  Loadable by any machine with Vulkan 1.3+.                          │
│                                                                     │
│  Lossless? YES — mathematically, SHA-256 guarantees it.             │
│  Tamper-proof? YES — hash mismatch = hard abort, zero silent rot.   │
│  Self-contained? YES — no external runtime dependency.              │
└─────────────────────────────────────────────────────────────────────┘
```

---

### The .runestone Wire Format

```
OFFSET    SIZE    FIELD
──────────────────────────────────────────────────────────────────────
[0..8]    8 B     Magic bytes: b"CHTHONIC"
[8..10]   2 B     Format version: u16 little-endian (currently 1)
[10..14]  4 B     Schema version: u32 little-endian (currently 1)
[14..18]  4 B     Event count: u32 little-endian
[18..22]  4 B     Flags: u32 little-endian
                    bit 0 = GPU compressed (Vulkan compute LZ4/deflate)
                    bit 1 = CPU compressed (zstd fallback)
                    bit 2 = encrypted (ChaCha20-Poly1305 or AES-256-GCM)
[22..54]  32 B    SHA-256 digest of (SCHEMA + SPIRV + PAYLOAD) blocks
[54..58]  4 B     SPIRV block length: u32 le
[58..62]  4 B     SCHEMA block length: u32 le
[62..66]  4 B     PAYLOAD compressed length: u32 le
[66..70]  4 B     PAYLOAD uncompressed length: u32 le
[70..]    N B     SCHEMA block (JSON, describes event types + versions)
[70+S..]  M B     SPIRV block (Vulkan 1.3 compute shader bytecode)
[70+S+M..] P B   PAYLOAD (compressed, opaque — SPIRV decodes it)
```

Every byte after [22..54] is covered by the SHA-256. A single flipped bit anywhere in the
schema, shader, or payload fails the hash before any data reaches a caller.

---

### The Load as Computation

```
ankh-forge stone execute .chthonic/stones/2026-04-13.runestone
         │
         ▼
  1. Open file, read HEADER
         │
         ▼
  2. Compute SHA-256(SCHEMA + SPIRV + PAYLOAD)
     compare against [22..54]
     mismatch → hard abort, zero silent corruption
         │
         ▼
  3. Extract SPIRV block
     Upload to RTX 4090 as Vulkan 1.3 compute pipeline
         │
         ▼
  4. Upload PAYLOAD → VRAM storage buffer (src)
     Allocate output buffer in VRAM (dst)
         │
         ▼
  5. Vulkan compute dispatch ← THIS is the novel step
     The GPU executes the stone's own decoder
     Decompresses, indexes, transforms in parallel
     Writes structured output to dst buffer
     (not just bytes — semantic event graph)
         │
         ▼
  6. Map dst VRAM → CPU-visible memory
         │
         ▼
  7. bincode::deserialize::<SemanticGraph>()
     Typed Rust structs, schema-verified at compile time
         │
         ▼
  8. Agent receives a queryable semantic graph
     Not "parse this JSON" — "query these verified typed events"
```

Step 5 is what makes this different from any existing approach. The GPU is not accelerating
a fixed algorithm. It is executing an **arbitrary compute program that traveled inside the
data**. The stone describes its own decoding.

---

### Why Foreign and Unknown Media Works

Because the SPIRV block can contain ANY compute shader:

```
stone contains:
  [SPIRV = markdown tokenizer shader]
  [PAYLOAD = raw markdown bytes]
  → load → GPU tokenizes → structured document graph

stone contains:
  [SPIRV = LZ4 block decompressor]
  [PAYLOAD = NDJSON trail events, LZ4 compressed]
  → load → GPU decompresses → typed TrailEvent structs

stone contains:
  [SPIRV = image descriptor extractor]
  [PAYLOAD = raw PNG/EXR/HDR bytes]
  → load → GPU extracts descriptors → image semantic graph

stone contains:
  [SPIRV = decoder for a completely invented binary format]
  [PAYLOAD = that format's bytes]
  → load → GPU decodes → whatever the shader defines
```

The loader (`ankh-forge`) does not need to know the format. It dispatches whatever SPIR-V
the stone carries. The interoperability primitive is Vulkan compute itself — which runs on
every GPU that exists today without a shared library or external runtime.

This is the "FFI of the unknown." The foreign function interface is the GPU instruction set.

---

### What Enlightenment Means for an Agent

**Current state (as of this session):**

```
Session start
→ agent reads .md files, runs grep, glob, parses JSON
→ builds mental model from scratch each turn
→ session_events SQL (ephemeral, dies on session close)
→ hot file (persistent, but agent must re-parse every turn)
→ agent loses state between sessions
```

**Enlightened state (after REM implementation):**

```
Session start
→ ankh-forge stone execute .chthonic/stones/current.runestone
→ GPU computes semantic graph from all prior sessions
→ agent queries: "all critical decisions involving gemini" → typed result
→ agent queries: "last known VS Code PID and hash" → typed result
→ agent queries: "what was decided about bun vs npm" → typed result
→ no parsing, no grep, no reconstruction from scratch
→ agent reasons from pre-computed, hardware-guaranteed, hash-verified structure
→ during session: hot file captures new events (append-only, fast)
→ session end: forge hot+cold+prior stone → new stone
→ prior stone superseded, not deleted
→ all stones form an immutable, queryable chain
```

The stone is not a log. It is a **loaded intelligence state**. The difference is that a log
requires reconstruction. A stone is already computed.

---

### Scope Beyond Session Logs

The same execution model handles any data type:

```
trail.runestone     → session intelligence, decisions, diagnostics
lore.runestone      → ASC game faction data, entity graph, canon
corpus.runestone    → entire git history as semantic diff index
media.runestone     → images, audio, foreign binary artifacts
schema.runestone    → type registry, versioned event schemas
```

All loaded identically. All GPU-executed. All SHA-256 verified. All stored at:

```
.chthonic/          ← repo-local, gitignored (*.chthonic)
  trail/              ← hot and cold (active session)
  stones/             ← forged runestones (permanent, immutable)
  REM_BLUEPRINT.md    ← this document
  api_pool.json       ← auth (user-profile, intentionally home-dir in ~/.chthonic/)
```

No git. No provider. No source control. The hardware owns it.

---

## Part 2 — Implementation Scope

### What Already Exists in chthonic-archive

The repository was designed for this without knowing it:

```toml
# Cargo.toml — existing dependencies that power REM
ash = { version = "0.38", features = ["loaded", "debug"] }  # Vulkan raw bindings
ash-window = "0.13"                                          # Window surface
gpu-allocator = { version = "0.28", features = ["vulkan"] } # VRAM management
serde = { version = "1.0", features = ["derive"] }          # Struct serialization
serde_json = "1.0"                                          # JSON (hot/schema blocks)
sha2 = "0.10"                                               # SHA-256 hash
tokio = { version = "1.50", features = ["full"] }           # Async (future GPU streams)
anyhow = "1.0"                                              # Error handling
thiserror = "2.0"                                           # Error types

# build-dependencies
shaderc = "0.10"                                            # .comp.glsl → SPIR-V
```

```
build.rs already:
  - discovers .comp.glsl files in assets/shaders/
  - compiles them to SPIR-V at cargo build time
  - supports both glslc (Vulkan 1.4 + SPIR-V 1.6) and shaderc backends
  - supports HLSL via dxc → SPIR-V
  - writes shader_manifest.txt for runtime lookup
```

The compute shader infrastructure is fully operational. It just has no trail shader yet.

### What Needs to Be Added

**Two crates to `tools/ankh-forge/Cargo.toml`:**

```toml
zstd    = "0.13"   # CPU-path compression (fallback when GPU unavailable)
bincode = "2.0"    # Compact binary serialization (PAYLOAD inner format)
```

**One compute shader (build.rs picks it up automatically):**

```
assets/shaders/trail_decompress.comp.glsl
```

**One new workspace member (optional, cleaner separation):**

```
tools/chthonic-trail/        ← dedicated trail crate
  Cargo.toml
  src/
    lib.rs
    event.rs     ← TrailEvent struct (serde derive)
    hot.rs       ← hot ndjson reader/appender
    cold.rs      ← gzip cold reader
    granite.rs   ← runestone writer/reader (sha2 + ash + gpu-allocator)
    forge.rs     ← hot+cold → runestone conversion
    query.rs     ← semantic graph query interface
```

### Implementation Phases (not time-boxed, scope-boxed)

**Phase 1 — ankh-forge trail subcommand (CPU path first)**

```
ankh-forge trail append <event-json>    → writes to hot file
ankh-forge trail list                   → reads hot, prints events
ankh-forge trail forge                  → hot+cold → .runestone (CPU zstd, no GPU yet)
ankh-forge trail verify <stone>         → SHA-256 check
ankh-forge trail dump <stone>           → decompress + print events
```

No Vulkan in Phase 1. CPU-only. Prove the format is correct before adding GPU.

**Phase 2 — Vulkan compute path (GPU-native decode)**

```
Survey the compute compression landscape:
  - LZ4 in GLSL compute (many open reference implementations)
  - Vulkan SPIR-V 1.6 (glslc --target-spv=spv1.6, already in build.rs)
  - ash compute pipeline setup (VkComputePipelineCreateInfo)
  - gpu-allocator VRAM buffer for src + dst
  - vkCmdDispatch with workgroup sizing for RTX 4090 (128 SM, 16384 threads)

Add to forge:
  ankh-forge trail forge --gpu    → uses Vulkan compute for compression
  ankh-forge stone execute <stone> → GPU-decoded, semantic graph output
```

**Phase 3 — Semantic graph and agent query interface**

```
Define SemanticGraph struct:
  - events: Vec<TrailEvent> (typed, ordered)
  - index: HashMap<EventType, Vec<usize>> (pre-indexed by type)
  - decisions: Vec<usize> (all decision events, fast access)
  - snapshots: Vec<usize> (all snapshot events)

Agent query API:
  graph.query("gemini")     → all events mentioning gemini
  graph.decisions()         → all critical decisions
  graph.since("2026-04-01") → events after a date
  graph.last_snapshot()     → most recent process snapshot
```

**Phase 4 — Universal ingestion (foreign media)**

```
Define the "stone schema" for non-trail data types:
  lore.schema.json     → faction entity schema
  corpus.schema.json   → git diff schema
  media.schema.json    → image descriptor schema

Implement per-schema compute shaders:
  lore_decode.comp.glsl
  corpus_index.comp.glsl

Forge non-trail data into stones:
  ankh-forge stone forge --schema lore.schema.json --input faction_data.json
```

---

## Vulkan Compute Landscape — What to Survey in Phase 2

The following crate ecosystem and reference material should be evaluated before
implementing the GPU path. This is the research agenda for Step 2:

```
Rust crates:
  ash            (already present) — raw Vulkan bindings, full control
  vulkano        — safe Vulkan abstraction, compute-friendly, active
  wgpu           — WebGPU/Vulkan/Metal/DX12 abstraction (cross-backend)
  gpu-allocator  (already present) — VRAM allocation
  bytemuck       — safe transmute for VRAM buffer types

Compute compression references:
  lz4-flex       — pure Rust LZ4, could port algorithm to GLSL
  zstd           — CPU zstd, Phase 1 fallback
  GLSL LZ4 decode — multiple open implementations on GitHub
  Vulkan spec §11 — VkComputePipelineCreateInfo reference

SPIR-V tooling (already operational via build.rs):
  shaderc        — GLSL → SPIR-V (already in Cargo build-deps)
  glslc          — Vulkan 1.4 + SPIR-V 1.6 (detected by build.rs)
  spirv-tools    — SPIR-V validator and optimizer (optional)

Hardware target (RTX 4090):
  128 streaming multiprocessors
  16,384 CUDA cores (= Vulkan compute invocations)
  24 GB GDDR6X VRAM
  900 GB/s memory bandwidth
  Vulkan 1.3 fully supported, Vulkan 1.4 partially
  Optimal workgroup size: 256 threads (local_size_x = 256 in .comp.glsl)
```

---

## The Compute Shader Entry Point (Skeleton)

This is what `assets/shaders/trail_decompress.comp.glsl` will look like.
The `build.rs` discovers it automatically. No manual wiring needed.

```glsl
#version 460
// Chthonic Trail — LZ4 Block Decompressor
// Dispatched by ankh-forge stone execute
// Each workgroup decodes one LZ4 block

layout(local_size_x = 256, local_size_y = 1, local_size_z = 1) in;

// Input: compressed PAYLOAD from .runestone
layout(set = 0, binding = 0) readonly buffer CompressedData {
    uint data[];
} src;

// Output: decompressed event bytes
layout(set = 0, binding = 1) writeonly buffer DecompressedData {
    uint data[];
} dst;

// Metadata: block offsets, sizes
layout(set = 0, binding = 2) readonly buffer BlockTable {
    uint compressed_offset[];
    uint compressed_size[];
    uint decompressed_offset[];
} blocks;

void main() {
    uint block_id = gl_WorkGroupID.x;
    uint thread_id = gl_LocalInvocationID.x;
    // LZ4 block decode — per-workgroup parallel implementation
    // (full implementation in Phase 2)
}
```

---

## Session Lineage

This blueprint was born from:

```
Problem:  Gemini CLI lane fragility (bun + winget + preview dist-tag)
Evolved:  VS Code Insiders lossless recovery before staged update
Evolved:  Typed session event trail (hot + cold, .chthonic/trail/)
Evolved:  Granite tier concept (SHA-256, compressed, self-verifying)
Evolved:  Runestone Execution Model (self-decoding, GPU-executed, universal)
Born:     This document — Win11, RTX 4090, April 13 2026
```

Trail events recording this lineage:
- `.chthonic/trail/2026-04-13.hot.ndjson` — 14 events (as of blueprint creation; relocated 2026-04-13)
- `.chthonic/trail/2026-04-13.cold.ndjson.gz` — compressed archive

Agent memory carved (store_memory, cross-session):
- Chthonic Trail format (hot/cold tier, location, event schema)
- Export-VsCodeSession function (gemini-cli-wrapper.ps1)
- Tool call stratum hierarchy (S0–S4)
- Runestone Execution Model core concept

---

*End of REM Blueprint — Step 1 complete.*  
*Step 2 begins when implementation scope is confirmed.*
