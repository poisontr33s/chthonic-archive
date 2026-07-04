# vulkan-lab/CLAUDE.md

## Purpose

High-performance Vulkan 1.4 experimentation lab on NVIDIA RTX 4090 (Ada Lovelace, SM 8.9).
Five frontier vectors. C++ explores, Rust hardens, mise orchestrates.

## Hardware Baseline

- **GPU:** RTX 4090 — 128 SMs, 16384 CUDA cores, 24 GB VRAM, 384-bit bus
- **Driver:** 610.62, CUDA 13.3, Vulkan API 1.4.350
- **Monitor:** AOC AGON PRO AG276QZD — QD-OLED, 2560x1440, 240 Hz, HDR True Black 400

## Toolchain (Frozen)

| Tool | Path / Version | Notes |
|---|---|---|
| Vulkan SDK | `C:\VulkanSDK\1.4.350.0` | Headers, validation layers, glslc, dxc |
| CMake | VS Insiders cmake 4.3.1-msvc1 (see mise.toml `CMAKE_COMMAND`) | **PATH cmake is a broken uv shim — never use it** |
| GCC | 16.1.0 (rv MSYS2 DevKit ucrt64) | `%APPDATA%\rv\rubies\ruby-4.0.5\msys64\ucrt64\bin\gcc.exe`; CC/CXX in mise.toml require rv MSYS2 in PATH |
| Ninja | 1.13.2 | Generator for CMake |
| glslc | v2026.2 (shaderc) | GLSL → SPIR-V, `--target-env=vulkan1.3` |
| mise | 2026.6.14 | Task runner — `mise run <task>` |
| Rust | 1.96.0 stable (pinned in `rust-toolchain.toml`) | ash 0.38. `cargo check` verified clean on 1.96.0 |
| VS Installer | **18.8.11925.187** | VS Community + Build Tools 2026 Insiders. SSMS 22.7.11919.86. User-updated 2026-07-03; exported `.vsconfig` evidence at `.vs/visualStudioInstaller/<lane>/.vsconfig` (deterministic install path unchanged, exports just feed granular component state) |

## Build Commands

```
cd vulkan-lab
mise trust            # first time only
mise run probe        # configure → build → run device probe
mise run gemm         # configure → build → run cooperative matrix GEMM
mise run v3-video     # configure → build → run AV1 decode session probe
mise run rebuild      # clean → configure → build
```

## Architecture

### Two Lanes, One Orchestrator

- **C++ / CMake / Ninja** — exploration lane. Proof-of-concept, spec-fighting, rapid iteration.
- **Rust / Cargo / ash 0.38** — hardening lane. Proven patterns graduate here.
- **mise.toml** — stateless orchestrator. Freezes toolchain paths, provides task aliases, owns dependency chains. No Ruby. No external SDKs.

Build systems are **intentionally separate**. Do not merge them.

### Queue Families (RTX 4090)

| QF | Queues | Flags | Vectors |
|----|--------|-------|---------|
| Q0 | 16 | GRAPHICS COMPUTE TRANSFER SPARSE | V1(RT), V4(DGC), V5 |
| Q1 | 2 | TRANSFER SPARSE | DMA |
| Q2 | 8 | COMPUTE TRANSFER SPARSE | V2(coop_matrix), V5 |
| Q3 | 1 | VIDEO_DECODE TRANSFER SPARSE | V3(decode) |
| Q4 | 2 | VIDEO_ENCODE TRANSFER SPARSE | V3(encode) |
| Q5 | 1 | OPTICAL_FLOW TRANSFER SPARSE | — |

### Cooperative Matrix Types (15 total)

```
FP16→FP16: 16x16x16, 16x8x16, 16x8x8
FP16→FP32: 16x16x16, 16x8x16, 16x8x8    ← GEMM uses this
UINT8→UINT32: 16x16x32, 16x8x32
INT8→INT32: 16x16x32, 16x8x32
BF16→FP32: 16x16x16
FP8e5m2→FP16/FP32: 16x16x32 each
FP8e4m3→FP16/FP32: 16x16x32 each
```

## Vectors

| # | Name | Status | Queue | Key Files |
|---|------|--------|-------|-----------|
| V1 | RT Spatial Query | Not started | Q0 | — |
| V2 | Cooperative Matrix | **Done** (16x16 GEMM verified) | Q2 | `vectors/coop_matrix/` |
| V3 | Video Decode/Encode | **Session probe done** (AV1) | Q3/Q4 | `vectors/v3_video/` |
| V4 | Device-Generated Commands | Not started | Q0 | — |
| V5 | GPU-as-Primary-Processor | Not started | Q0/Q2 | — |

## V3 AV1 Decode State

- Session probe: PASS — 1920x1080 AV1 Main 8-bit 4:2:0
- Max resolution: 8192x8192 (Level 7.3)
- DPB mode: **COINCIDENT only** (output + reference share same VkImage)
- DPB slots: 8 configured (AV1 spec: 7 refs + 1 current)
- Session memory: 5 bindings, 4.12 MB
- Output format: NV12 (G8_B8R8_2PLANE_420)
- **Pattern:** Video KHR functions require dynamic loading via `vkGetInstanceProcAddr` / `vkGetDeviceProcAddr` — vulkan-1.lib does not export them.

### V3 Next Steps

1. Source AV1 test bitstream (IVF container via one-shot FFmpeg: `ffmpeg -i input.mp4 -c:v copy -an output.ivf`)
2. Implement IVF reader (~50 lines — 32-byte file header + 12-byte frame headers)
3. Single-keyframe decode via `vkCmdDecodeVideoKHR` on Q3
4. Timestamp instrumentation (reuse GEMM pattern)

## Conventions

- **VK_CHECK macro** — all Vulkan calls. Prints error code + call site, returns 1.
- **Host-visible coherent memory** for CPU-accessible buffers.
- **Device-local memory** for session/DPB state.
- **NOMINMAX + WIN32_LEAN_AND_MEAN** on all targets.
- **SPIR-V shaders** compiled by glslc at build time via `compile_shader()` CMake function.
- Executables emit boxed ASCII headers (╔═╗/║/╚═╝) for visual structure.

## Anti-Patterns

- Do not add Ruby, Python, or any scripting layer to vulkan-lab.
- Do not add FFmpeg or external codec SDKs to the build graph. FFmpeg is a one-shot utility for bitstream prep only.
- Do not use PATH cmake — it's a broken uv shim.
- Do not merge C++ and Rust build systems.
- Do not allocate more DPB slots than the codec spec requires (AV1: 8, not hardware max 16).
