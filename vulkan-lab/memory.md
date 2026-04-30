# vulkan-lab/memory.md — Session Trail (Granite)

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-17 | C++ explores, Rust hardens — separate build systems | CMake integrates deeply with Vulkan SDK/Windows headers; Cargo provides memory safety for production. Merging creates coupling with no benefit. |
| 2026-04-17 | mise.toml as stateless orchestrator | Freezes toolchain paths (bypasses broken uv cmake shim), provides task aliases, zero-entropy rebuild. No Ruby dependency. |
| 2026-04-17 | AV1 over H.264 for V3 first target | AV1 is the frontier codec on Ada Lovelace. H.264 is a fallback, not the exploration target. |
| 2026-04-18 | Coincident DPB (driver-managed) | RTX 4090 reports COINCIDENT-only for AV1. Output and reference share same VkImage — simplifies allocation, reduces memory traffic. |
| 2026-04-18 | 8 DPB slots (not hardware max 16) | AV1 spec requires 7 refs + 1 current = 8. Over-provisioning wastes VRAM and creates false confidence in testing. |
| 2026-04-18 | Dynamic loading for video KHR | vulkan-1.lib does not export video extension functions. `vkGetInstanceProcAddr` / `vkGetDeviceProcAddr` is the canonical pattern. |
| 2026-04-18 | No external codec SDKs | FFmpeg is a one-shot utility for bitstream prep. NVENC SDK, codec2, etc. are out of scope. Vulkan Video is the native path. |
| 2026-04-18 | IVF container for test bitstreams | IVF is trivially parseable (32-byte header + 12-byte frame records). Simpler than Matroska/MP4 demuxing. |
| 2026-04-19 | Full dependency audit (13 Cargo.toml, 80+ crates) | Audit-before-update discipline. 4 cross-Cargo.toml version divergences (tokio, shaderc, reqwest, clap). bincode found unmaintained (v3 is tombstone) — architectural impact on REM wire format. |
| 2026-04-19 | VS Installer trio updated (11612.153 → 11709.129) | SSMS 22.5.0, VS Community + Build Tools 2026 Insiders. .vsconfig exports at `.vs/visualStudioInstaller2026/`. Paths unchanged, version numbers only. |
| 2026-05-01 | HOST_COHERENT buffers for G2 SSBO (no staging) | manifest/todo_roulette.json is ~8–16 KB at most. Staging buffer setup cost vastly exceeds benefit. HOST_VISIBLE|HOST_COHERENT is correct at manifest scale. |
| 2026-05-01 | build.rs for GLSL→SPIR-V compilation | `cargo build` compiles shaders at build time via glslc 1.4.341.1. `-fshader-stage=<stage>` must be explicit — glslc does not infer stage from `.comp.glsl` compound extension. Stage inferred from second-to-last extension in build.rs. |
| 2026-05-01 | include_bytes! for SPIR-V embedding | Avoids runtime path resolution. `../shaders/euler_score.comp.spv` is relative to `src/main.rs`. SPV committed to repo alongside .glsl sources. |
| 2026-05-01 | QF=2 (COMPUTE-only) preferred over QF=0 | G2 queue selection: min-by-key(has GRAPHICS flag). On RTX 4090: Q0=GRAPHICS+COMPUTE (16 queues), Q2=COMPUTE-only (8 queues). Q2 selected. |

## Verified Outputs

| Artifact | Result | Date |
|----------|--------|------|
| `mise run probe` | 41/41 frontier extensions, 274 total, 6 QFs, 15 coop matrix types | 2026-04-17 |
| `mise run gemm` | 16x16 FP16→FP32 GEMM — 0 mismatches, ~2500-3300 ns GPU time | 2026-04-17 |
| `mise run v3-video` | AV1 session alive — 1080p, 8 DPB slots, 4.12 MB, NV12 output | 2026-04-18 |
| Dep audit (13 Cargo.toml) | 80+ entries mapped, 4 version divergences, 2 major-jump crates, 1 unmaintained (bincode) | 2026-04-19 |
| Branch C (workspace) | tokio 1.52, clap 4.6, shaderc 0.10, reqwest 0.13, gix 0.79 — non-Solana crates clean | 2026-04-19 |
| **cli-renderer G1** | headless Vulkan instance, RTX 4090, Vulkan 1.4.329 (commit `1c073231`) | 2026-04-30 |
| **cli-renderer G2** | 11 tasks scored via GPU: `euler_score.comp.spv` dispatched on QF=2. Sorted table to stdout. (commit `d135e3a1`) | 2026-05-01 |

## Corrections Applied

| Source | Claim | Correction |
|--------|-------|------------|
| Assisted feedback | `av1_metadata` BSF for extraction | Wrong — that's metadata manipulation. Correct: `ffmpeg -i in.mp4 -c:v copy -an out.ivf` |
| Assisted feedback | 16 VkImage objects for DPB | Over-provisioned — AV1 spec needs 8 (7 refs + 1 current) |
| Assisted feedback | Multi-session stress test as next step | Premature — single-frame decode must verify first |
| Assisted feedback | `ruby.toml` for vulkan-lab orchestration | Hallucinated — Ruby has no relationship to this project. rv provided GCC; that's the only transitive link. |
| Initial probe | 1000141000 = "FP8 E4M3 NV" | Wrong — it's VK_COMPONENT_TYPE_BFLOAT16_KHR (BF16). Corrected in type_str(). |

## File Map

```
vulkan-lab/
├── CLAUDE.md              ← agent context (this project's rules)
├── memory.md              ← this file (decisions + verified outputs)
├── mise.toml              ← task orchestrator (frozen toolchain paths)
├── CMakeLists.txt         ← C++ build graph (Ninja, C++20, Vulkan)
├── CMakePresets.json       ← configure/build presets (dev, release)
├── probes/
│   └── vk_capability_probe.cpp   ← device enumeration (41 frontier exts)
├── vectors/
│   ├── coop_matrix/
│   │   ├── main.cpp              ← V2: tensor-core GEMM host (465 lines)
│   │   └── coop_matmul.comp      ← V2: GLSL compute shader (36 lines)
│   └── v3_video/
│       └── main.cpp              ← V3: AV1 session probe (dynamic loading)
├── rust-lane/
│   ├── Cargo.toml                ← ash 0.38 (dormant)
│   └── src/main.rs               ← stub
└── cli-renderer/
    ├── Cargo.toml           ← [workspace] isolation; ash 0.38, serde, serde_json
    ├── build.rs             ← glslc GLSL→SPIR-V compiler (stage from compound ext)
    ├── src/main.rs          ← G1+G2 complete; G3–G6 TODO stubs
    └── shaders/
        ├── euler_score.comp.glsl     ← compute shader (local_size_x=64, KAPPA=0.07)
        ├── euler_score.comp.spv      ← compiled SPIR-V (committed)
        ├── ascii_downsample.comp.glsl ← G3 shader (local_size_x=8, local_size_y=16)
        └── ascii_downsample.comp.spv  ← compiled SPIR-V (committed)
```

## Open Work

| Vector | Next Milestone | Blocked On |
|--------|---------------|------------|
| V2.1 | Tiled GEMM (64x64, 256x256) with shared memory staging | Nothing — ready when prioritized |
| V2.1 | FP8/BF16 cooperative matrix experiments | Nothing |
| V3 | Single-keyframe AV1 decode via `vkCmdDecodeVideoKHR` | AV1 test bitstream (IVF) |
| V1 | RT spatial query scaffold | Not started |
| V4 | Device-generated commands scaffold | Not started |
| V5 | GPU scheduler scaffold | Not started |
| ~~Toolchain~~ | ~~mise 2026.4.17, Rust 1.95.0~~ | **DONE** 2026-04-19 — `cargo check` clean |
| ~~Deps (root)~~ | ~~Bump tokio 1.50→1.52~~ | **DONE** 2026-04-19 — Branch B |
| ~~Deps (workspace)~~ | ~~Harmonize tokio/clap/shaderc/reqwest/gix~~ | **DONE** 2026-04-19 — Branch C. gix parked at 0.79 (0.81 blocked by gix-hash Rust 1.95 bug). reqwest feature renamed. shaderc API fix. |
| Deps (workspace) | OpenSSL 4.0.0 vs openssl-sys 0.9.112 | **PRE-EXISTING** — blocks entropy-ledger-host only. Deferred to Branch F. |
| Deps (tools) | crossterm 0.28→0.29, clap normalization | Branch D — minor |
| Deps (Solana) | solana-sdk 2.3.1→4.0.1, anchor-lang 0.32.1→1.0.0 | MAJOR — breaking, needs dedicated branch |
| Deps (bincode) | bincode 2.0 unmaintained — evaluate wincode/postcard/rkyv | CRITICAL — impacts REM .runestone wire format |
| Research | Rust game engine for VS Code Insiders (Bevy ecosystem) | Not started |
