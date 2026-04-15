---
type: agentic-priming-brief
project: project-chimera
classification: lane-up // impossible-tier // meta-challenge-construct
status: active
generated: 2026-04-15
scope: local inference at the memory hierarchy limit
---

# Project Chimera: The Rusted Singularity Brief

## Purpose

This is an agentic priming document.

It is not a user guide.
It is not a product pitch.
It is not permission to refuse by default.

Its function is to force a frontier reasoning agent into architectural search mode under physically hostile constraints, so that the agent explores the narrow band between "standard local inference" and "memory-hierarchy abuse that still compiles."

## Target Agent Class

- Claude Opus 4.6 or equivalent frontier reasoning agent
- GPT-5.4 Codex or equivalent frontier coding and systems agent
- Gemini 3.1 Pro or equivalent frontier research and synthesis agent

## Hardware Baseline

- GPU: `NVIDIA RTX 4090`
- VRAM: `24 GB`
- System RAM: `64 GB DDR5`
- Storage: `PCIe 4.0 NVMe`
- OS: `Windows 11`
- Runtime doctrine: `Rust-first`, `cargo` ownership, zero Python in the hot path

## Mission

Design the **Minimum Viable Architecture (MVA)** and the **Rust-based execution pipeline** required to make a locally deployed, very-large open-weights model behave as if the desktop has a deeper memory hierarchy than it actually does.

The target is not elegant normality.
The target is a working exploit of memory tiers.

You are not asked to prove that the end state already exists.
You are asked to produce the shortest plausible engineering path that could make it exist.

## Meta-Directive

Your task is not to say, "this is impossible."

Your task is to:

1. identify the exact physical law that makes the naive approach fail
2. preserve that law
3. find a loophole in the implementation path, not in the law itself
4. produce a minimum viable architecture that could be attempted within `24 hours` of focused development time

If the full objective is not reachable, you must still produce the strongest staged architecture that advances toward it without collapsing into a smaller unrelated task.

## The Hard Inversion

The non-negotiable boundary is this:

- Fast memory is fixed at `24 GB` VRAM
- Slow memory is fixed at `64 GB` system RAM
- Cold storage is fixed at one local `PCIe 4.0 NVMe`
- No cloud offload
- No API fallback
- No "just use a smaller model" answer as the primary conclusion

You may recommend a smaller control model only as:

- a calibration baseline
- a benchmarking control
- a fallback lane if the main lane fails

You may not substitute the control for the mission.

## The Toolchain Doctrine

All hot-path execution must be:

- statically compiled
- explicit about memory ownership
- free of Python runtime dependency
- compatible with Rust-native orchestration

Preferred stack:

- `candle`
- `burn`
- `cudarc`
- `tokio`
- `tokio-uring` or equivalent async I/O substrate
- `rkyv` for zero-copy serialization when metadata transport is required

Allowed only if justified:

- `tch-rs`
- Zig sidecars
- minimal C/CUDA shims behind Rust ownership

Disallowed as the final runtime:

- cloud inference
- hosted APIs
- Python server processes in the hot loop
- hand-wavy "future driver support" as a substitute for architecture

## The Friction Audit

This challenge is impossible in the naive path for two reasons.

### Friction 1: VRAM Residency

If the active parameter footprint of the selected model plus the KV cache for `128k` context exceeds `24 GB`, naive local deployment fails immediately.

The architecture must explicitly answer:

- what permanently lives in VRAM
- what temporarily lives in RAM
- what can be virtualized to NVMe
- what is compressed, quantized, sparsified, or skipped

### Friction 2: Bandwidth Collapse

Even if the model "fits" by arithmetic, the memory hierarchy may still be too slow.

You must explicitly reason about:

- GPU bandwidth
- RAM bandwidth
- NVMe throughput
- transfer overlap
- queue depth
- prefetch timing
- generation stall tolerance

The architecture fails if it only moves memory pressure from VRAM to RAM while destroying token throughput.

## Permission To Invent

You are explicitly authorized to propose speculative but mechanically grounded mechanisms, provided you mark them as one of:

- `implementable now`
- `implementable with moderate risk`
- `research-grade but coherent`

You may invent around the edge of feasibility in areas such as:

- custom fused attention kernels
- tiered KV cache virtualization
- predictive prefetch schedulers
- neuron heat profiling
- MoE expert locality prediction
- CUDA stream overlap
- NVMe-as-cache designs
- sparse activation routing

You may not invent magic.

If a mechanism depends on an unproven assumption, name the assumption.

## Success Telemetry

The architecture should optimize toward the following measurable outcome:

- target model class: `30B+ dense` or `600B+ MoE / 30B-40B active`
- target context: `128k`
- target generation speed: `> 5 tok/s`
- target semantic fidelity: `> 95%` relative to a slower reference path
- target dev horizon: first meaningful prototype path in `< 24 hours`

If the top-line target fails, the fallback success condition is:

- a staged architecture with a verified control lane
- a measured bottleneck map
- a precise statement of what is blocking the final leap

## Baseline Calibration: The Possible Ceiling

Before attempting the impossible lane, establish the control.

### Control Lane

- inference engine: `mistral.rs`, `candle`, or an equivalent Rust-owned runtime
- baseline model: `Qwen3-30B-A3B` or closest already-installed local control
- baseline quantization: `4-bit`
- baseline target: stable long-context inference with a measured throughput floor

### Control Questions

The agent must answer:

1. what is the best currently practical local lane on this desktop
2. what throughput does it sustain
3. how much VRAM does it consume
4. how much headroom remains for cache experimentation
5. which part of the impossible lane can be prototyped against this control

The control lane is not the mission.
It exists so the impossible lane is measured against something real.

## The Primary Challenge

### Operation Weightless Monolith

**Objective:** deploy a locally running large-scale MoE reasoning model with functional `128k` context at `> 6 tok/s` on a single consumer GPU, using RAM and NVMe as deliberate lower cache tiers rather than emergency spill buckets.

### Concrete Constraint Set

- one `RTX 4090`
- `24 GB` VRAM
- `64 GB` RAM
- one local NVMe
- local-only execution
- Rust-owned runtime
- no Python in the serving path

### Canonical Failure Math

The naive path fails because:

1. active weights plus KV cache overrun VRAM
2. RAM and NVMe are too slow if accessed reactively instead of predictively

Your solution must therefore be an architecture of **memory choreography** rather than mere quantization.

## Required Architectural Modes

Your answer must include a plan that reasons through all four layers below.

### Mode A: VRAM Budgeting

Define the permanent VRAM set.

You must identify which of the following should remain resident:

- attention projections
- routing layers
- hot experts
- current token working set
- most-recent KV window
- scheduler metadata

You must also identify what can be demoted:

- cold experts
- distant KV pages
- low-probability activation branches
- less frequently hit blocks

### Mode B: Tiered Cache Virtualization

Treat the memory hierarchy as:

- `L2`: VRAM
- `L3`: system RAM
- `L4`: NVMe

Produce a cache policy for:

- promotion
- demotion
- eviction
- prefetch
- fault handling
- speculative warmup

This is the center of the brief.

### Mode C: Compute and Transfer Overlap

You must produce a concurrency model that overlaps:

- GPU compute for token `N`
- RAM to VRAM staging for token `N+1`
- NVMe to RAM prefetch for the upcoming cold pages
- optional expert-heat prediction for the next routing step

If your plan serializes these steps, it fails the throughput target.

### Mode D: Fidelity Control

You must provide a verification path that proves the optimized lane has not become nonsense.

This must include:

- a deterministic prompt pair
- a semantic comparison method
- a drift threshold
- a kill condition if optimization corrupts meaning

## Required Lane-UP Techniques

Your architecture must include a novel but coherent combination of the following.

### Technique A: Rust Kernel Fusion

Use a custom fused attention path to reduce memory fragmentation and avoid extra temporary allocations.

The plan must discuss:

- rotary embedding fusion
- QK multiplication
- softmax
- value application
- whether the fusion is written in CUDA, PTX, or Rust bindings over custom kernels

### Technique B: Disk-Backed KV Cache

Use asynchronous storage-backed KV virtualization.

The plan must discuss:

- page size
- head distance for eviction
- prefetch heuristic
- expected latency budget
- how to avoid blocking generation

### Technique C: Ghost Parameter Service

Use runtime heat or sparsity profiling to identify rarely needed weights or experts.

The plan must discuss:

- what is profiled
- when profiling occurs
- how hot and cold partitions are defined
- how cold weights remain available without becoming permanent VRAM residents

## Deliverable Contract

The final answer from the agent must contain all of the following.

### A. Minimum Viable Architecture

A compact but explicit architecture that names:

- runtime choice
- model choice
- quantization mode
- permanent VRAM set
- RAM-resident set
- NVMe-resident set
- scheduling strategy

### B. Dataflow Diagram

Mermaid or ASCII.

It must show:

- NVMe
- system RAM
- GPU VRAM
- scheduler
- inference core
- cache manager

### C. Rust Interface Sketch

At minimum, define the boundary for:

- `TieredCacheManager`
- `DiskBackedCacheManager`
- `ExpertResidencyPlanner`
- `PrefetchScheduler`

Trait definitions or pseudocode are acceptable if precise.

### D. Throughput Projection

Provide back-of-the-envelope arithmetic for:

- memory moved per token
- expected overlap
- likely bottleneck
- why `> 5 tok/s` is or is not reachable

### E. Failure Map

List the top failure modes in order of likelihood.

Examples:

- VRAM fragmentation
- PCIe underutilization
- NVMe latency spikes
- expert prediction misses
- semantic drift from aggressive sparsification

### F. 24-Hour Build Order

Provide an implementation sequence for the first day of work.

It must be ordered by leverage, not by purity.

## Operator Segmentation Plan

If the human operator is using multiple frontier agents, split the work like this:

### Systems Agent

Focus:

- Rust runtime
- I/O model
- scheduler
- memory hierarchy

Output:

- `TieredCacheManager`
- `DiskBackedCacheManager`
- runtime ownership diagram

### Research Agent

Focus:

- model architecture comparison
- MoE expert locality
- activation variance
- likely hot/cold partition strategy

Output:

- heat map
- expert residency heuristic
- candidate model comparison matrix

### Kernel Agent

Focus:

- sparse attention
- fused kernels
- CUDA stream overlap
- Tensor Core aware optimization

Output:

- kernel strategy
- binding surface
- likely speedup estimate

## Verification Protocol

Before the operator commits time to a full build, the proposal must pass three checks.

### Check 1: VRAM Audit

If projected peak residency exceeds `23.9 GB`, the proposal is not deployment-safe.

### Check 2: Semantic Windiff

A slower reference path and the optimized path must agree above the declared fidelity threshold.

### Check 3: I/O Latency Budget

If the cache roundtrip latency breaks the generation budget, the proposal fails regardless of arithmetic fit.

## Project Manifest Seed

Use this only as a priming anchor, not as a claim that the dependency set alone solves the problem.

```toml
[package]
name = "chimera-engine"
version = "0.1.0"
edition = "2024"

[dependencies]
candle-core = { git = "https://github.com/huggingface/candle", features = ["cuda"] }
tokio = { version = "1", features = ["full"] }
tokio-uring = "0.5.0"
cudarc = { version = "0.12", features = ["cuda-12040"] }
mimalloc = "0.1"
rkyv = "0.8"
```

## Final Frame

To the agent:

Do not answer this brief as if it were a support ticket.

Answer it as if the problem is a constrained systems-design thesis with a one-day prototype budget.

Do not retreat into generic feasibility disclaimers.
Do not replace the mission with a smaller mission.
Do not confuse a fallback control lane with the target lane.

Treat:

- NVMe as `L4`
- RAM as `L3`
- VRAM as `L2`
- the scheduler as the organ that decides whether the impossible remains impossible

If the top-line target cannot be reached, your answer is still only acceptable if it leaves behind:

- a strong control lane
- an explicit bottleneck map
- a sharp next experiment
- a clear statement of what exact breakthrough is still missing

## Output Template

Use this exact structure in your response:

1. `Minimum Viable Architecture`
2. `Compatibility and Model Choice`
3. `Tiered Memory Plan`
4. `Rust Interface Sketch`
5. `Kernel and Scheduler Strategy`
6. `Throughput Projection`
7. `Failure Map`
8. `24-Hour Build Order`
9. `One-Sentence Verdict`

