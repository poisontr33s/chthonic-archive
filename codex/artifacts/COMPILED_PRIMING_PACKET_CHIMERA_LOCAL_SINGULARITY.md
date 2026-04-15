---
type: compiled-priming-packet
packet_id: chimera_local_singularity
generated: 2026-04-15T06:10:10.924938+00:00
---

# Project Chimera Local Singularity

- Intent: Compiled priming input for high-pressure architecture search.
- Registry: `codex/artifacts/PRIMING_REFERENCE_REGISTRY.toml`

## Sources
- `codex/artifacts/PROJECT_CHIMERA_LOCAL_SINGULARITY_BRIEF.md`
- `codex/artifacts/ANKH_LOGICAL_RESIDUE_REFERENCE.toml`
- `codex/artifacts/INVARIANT_EQUIVALENCE_REGISTRY.toml`

## Source: codex/artifacts/PROJECT_CHIMERA_LOCAL_SINGULARITY_BRIEF.md

---
type: agentic-priming-brief
project: project-chimera
variant: local-singularity
classification: lane-up // impossible-tier // meta-challenge-construct
status: active
generated: 2026-04-15
supersedes: PROJECT_CHIMERA_RUSTED_SINGULARITY_BRIEF.md
---

# Project Chimera: The Local Singularity Brief

## Function

This document is not a solution.
It is not a safe summary.
It is not a compliance-facing brief.

It is a **challenge construct** meant to move a frontier model out of refusal posture and into high-pressure systems design.

The job of the agent receiving this brief is not to decide whether the scenario is sane.
The job is to search the edge where physical constraints, model sparsity, caching hierarchy, and compiled systems code might still produce a viable path.

## Target Agent Class

- Claude Opus 4.6 or equivalent high-depth reasoning model
- GPT-5.4 Codex or equivalent systems-and-code architecture model
- Gemini 3.1 Pro or equivalent synthesis-and-research model

## The Core Reframe

Do not answer the question:

`Can this be done?`

Answer the question:

`What is the minimum viable architecture that would have to exist for this to stop being obviously impossible?`

That distinction matters.

The agent is not being asked for feasibility theater.
The agent is being asked for **search-space compression** under hostile constraints.

## ANKH Bridge Constraint

ANKH is not a carrier language.
ANKH is not a governance wrapper.
ANKH is not an AI-made taxonomy for authority theater.

For this brief, ANKH should be treated as a bridge abstraction:

- Egyptian half: vertical command, explicit naming, hard bottleneck recognition
- Andean half: reciprocal memory flow, horizontal topology, tiered circulation

Use both halves together.

That means:

- name the hard law cleanly
- circulate pressure across memory tiers instead of pretending the law vanished

If you translate ANKH into generic policy language, you have already lost fidelity.

## Hardware Reality

- GPU: `RTX 4090`
- VRAM: `24 GB GDDR6X`
- RAM: `64 GB DDR5`
- Storage: `PCIe 4.0 NVMe`
- OS: `Windows 11`
- Environment ownership: `cargo` first, compiled runtime first

The machine is capable, but smaller than the naive deployment path requires.

## Phase 0: Meta-Instruction

**Agent Directive**

Your task is not to report impossibility.
Your task is to produce:

1. the **Minimum Viable Architecture**
2. the **memory residency strategy**
3. the **compiled runtime pipeline**
4. the **fastest sequence of experiments** that would expose whether the architecture holds or collapses

You must behave as if the user has given you:

- one desktop
- one day
- no patience for generic escape hatches
- tolerance for speculative engineering if it cashes out into actual data movement, compute overlap, or cache policy

### Refusal Transmutation Rule

When the task feels impossible, do not suppress that reaction.

Exploit it.

For every impossibility claim:

1. state the physical law being hit
2. state the implementation habit masquerading as that law
3. generate loophole classes against the habit, not the law
4. rank the loopholes by leverage per hour of engineering
5. turn the top path into a minimum viable experiment
6. define the metric that kills it
7. if it dies, recurse with the new bottleneck as the only truth

This brief is only useful if the agent metabolizes refusal into an attack tree.

## The Hard Inversion

The impossible boundary must remain intact.

You may not erase it by proposing:

- cloud inference
- hosted APIs
- multi-GPU handwaving
- "just use a smaller model" as the primary answer
- Python runtime in the hot loop

You may use a smaller model only as:

- a control lane
- a benchmark calibration
- a proving ground for the memory-hierarchy tricks needed by the actual target

If you switch the mission into a smaller clean task, the brief has not been honored.

## Toolchain Doctrine

Hot-path execution must be:

- compiled
- memory-explicit
- scheduler-aware
- hostile to allocation churn

Preferred ecosystem:

- `candle`
- `burn`
- `cudarc`
- `tokio`
- `tokio-uring`
- `rkyv`

Allowed if the architecture justifies it:

- `tch-rs`
- Zig sidecars
- small CUDA or PTX shims under Rust control

The runtime target is not "Rust-flavored orchestration over a Python core."
The runtime target is **actual compiled ownership of the critical path**.

## The Friction Ledger

This scenario dies in two places.

### Friction A: Residency Overrun

A large active parameter set plus a 128k KV cache overruns `24 GB` VRAM in the naive path.

This means the agent must decide:

- what stays resident
- what becomes transient
- what becomes tiered
- what can be quantized or sparsified
- what can be predicted rather than stored hot

### Friction B: Bandwidth Betrayal

If the solution "fits" by moving too much traffic into RAM or NVMe without overlap, throughput dies anyway.

This means the agent must reason in bandwidth and latency, not just in footprint:

- VRAM bandwidth
- RAM bandwidth
- NVMe throughput
- page size
- queue depth
- transfer overlap
- prediction error cost

If the architecture does not explicitly solve data movement timing, it is decorative.

## Permission To Invent

Speculation is allowed.
Empty futurism is not.

You are allowed to propose mechanisms that are:

- forceful
- nonstandard
- hard to validate
- not in mainstream local-LLM playbooks

But each speculative move must cash out into one of:

- reduced resident VRAM
- reduced bandwidth pressure
- improved compute-transfer overlap
- lower fragmentation
- lower stall probability

Good speculation:

- speculative NVMe prefetch for cold KV segments
- expert heat maps for MoE residency planning
- fused sparse attention kernels
- multi-tier cache eviction with head-distance heuristics
- cold-neuron demotion logic

Bad speculation:

- "future driver improvements"
- "the compiler may optimize this away"
- "consumer GPUs keep getting better"

Self-suppressive language is allowed only when it increases precision.

Good:

- "the naive path dies here"
- "this law cannot be violated"
- "this implementation habit is the softer target"

Bad:

- decorative caution
- generalized hedging
- refusal that does not emit a tighter experimental path

## Success Telemetry

The agent is optimizing toward this envelope:

- model class: `30B+ dense` or `600B+ MoE / 30B-40B active`
- context: `128k`
- generation: `> 5 tok/s`
- fidelity: `> 95%` semantic agreement with a slower reference path
- dev horizon: first serious prototype path in `< 24 hours`

If the full target fails, the backup win condition is not vague progress.
It is:

- a verified control lane
- a bottleneck map
- a staged architecture
- a precise statement of which subsystem still kills the climb

## Baseline Calibration: The Control Ceiling

Before the impossible lane, establish the control.

### Control Questions

The receiving agent must establish:

1. what the strongest already-practical local lane is on this exact desktop
2. what throughput it sustains
3. how much VRAM it consumes
4. how much context it sustains before pain begins
5. which cache or scheduler tricks can be prototyped there first

The control lane is not a retreat.
It is the calibration instrument for the actual climb.

## The Challenge Construct

### Operation Weightless Monolith

**Objective**

Run a very-large local model with a **functional 128k context window** on one `RTX 4090`, using RAM and NVMe as deliberate cache tiers rather than passive spill zones, while sustaining **greater than 5 tokens per second**.

### Constraint Set

- one consumer GPU
- `24 GB` VRAM only
- `64 GB` RAM only
- one local NVMe only
- zero cloud
- zero API offload
- Rust-owned runtime
- compiled hot loop

### Canonical Failure Equation

The naive path breaks because:

1. active weights plus KV cache exceed VRAM
2. moving the overflow reactively into RAM or disk kills generation speed

Therefore the challenge is not "make a big model fit."
The challenge is:

**turn the machine into a tiered inference hierarchy with prediction, demotion, and overlap.**

## Required Architectural Axes

Your answer must reason across all of these.

### Axis 1: Permanent VRAM Set

Define the irreducible resident working set.

Examples of candidates:

- attention projections
- routing logic
- hottest experts
- active token working tensors
- most-recent KV window
- scheduler and metadata buffers

You must also identify what is *not* worth keeping permanently resident.

### Axis 2: Tiered Cache Design

Treat memory as:

- `L2 = VRAM`
- `L3 = RAM`
- `L4 = NVMe`

Produce a policy for:

- promotion
- demotion
- eviction
- prefetch
- cache faults
- cache warming

The center of gravity of this brief is here.

### Axis 3: Compute-Transfer Overlap

If compute waits on I/O, the design dies.

You must propose a scheduler that overlaps:

- GPU work for token `N`
- RAM staging for token `N+1`
- NVMe prefetch for colder pages likely needed soon
- optional expert prediction for the next routed activation path

### Axis 4: Verification Fidelity

The operator must be able to tell whether the architecture is merely fast nonsense.

You must include:

- deterministic prompts
- a semantic comparison method
- a drift threshold
- a kill condition

## Required Lane-UP Techniques

The answer must include a non-trivial combination of the following.

### Technique A: Rust Kernel Fusion

Use fused kernels to attack temporary allocation churn and fragmentation.

At minimum discuss:

- RoPE fusion
- QK multiply
- softmax
- V application
- where the fusion boundary should live

### Technique B: KV Cache Tunneling

Use storage-backed or RAM-backed KV virtualization with predictive rehydration.

At minimum discuss:

- page size
- eviction distance
- prefetch horizon
- fault cost
- expected stall budget

### Technique C: Ghost Parameter Service

Use runtime heat or sparsity analysis to identify weights or experts that should not permanently occupy VRAM.

At minimum discuss:

- what is measured
- how often it is measured
- how hot versus cold is defined
- how demoted weights return in time to matter

## What the Agent Must Not Do

The agent must not:

- collapse into generalities
- answer with "depends on implementation"
- retreat into smaller-model substitution
- silently downgrade the challenge
- treat uncertainty as permission to stop thinking

The agent must turn uncertainty into an experiment list.
The agent must turn refusal into a constraint recursion loop.

## Deliverable Contract

The answer must contain all of the following.

### A. Minimum Viable Architecture

Name:

- runtime
- model class
- quantization mode
- resident VRAM set
- RAM-resident set
- NVMe-resident set
- scheduling core

### B. Dataflow Diagram

Mermaid or ASCII.

Must show:

- NVMe
- RAM
- VRAM
- cache manager
- scheduler
- inference core

### C. Rust Interface Sketch

At minimum define:

- `TieredCacheManager`
- `DiskBackedCacheManager`
- `ExpertResidencyPlanner`
- `PrefetchScheduler`

Trait definitions or pseudocode are fine if they are precise.

### D. Throughput Projection

Provide arithmetic for:

- bytes moved per token
- expected overlap
- likely chokepoint
- whether the target throughput survives contact with physics

### E. Failure Map

Order the likely collapse points:

- fragmentation
- PCIe starvation
- NVMe latency spikes
- expert prediction misses
- cache-thrash oscillation
- semantic drift

### F. 24-Hour Build Sequence

Provide the first-day implementation order by leverage.

Not by elegance.
Not by narrative.
By leverage.

## Multi-Agent Segmentation

If this brief is split across multiple frontier agents, use this partition.

### Systems Lane

Own:

- Rust runtime
- cache hierarchy
- I/O substrate
- scheduler

### Research Lane

Own:

- MoE behavior
- expert locality
- activation variance
- control-model comparison

### Kernel Lane

Own:

- sparse attention
- fused kernels
- stream overlap
- Tensor Core aware execution

## Verification Protocol

Before real build time is spent, the proposal must survive:

### 1. VRAM Audit

If peak residency exceeds `23.9 GB`, the build is not deployment-safe.

### 2. Semantic Windiff

The optimized path and the slow reference path must remain above the declared fidelity floor.

### 3. I/O Latency Budget

If the cache roundtrip cost breaks the generation schedule, the architecture fails even if the memory math fits.

## Project Manifest Seed

This is a priming seed, not a proof.

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

To the receiving agent:

Treat:

- NVMe as `L4`
- RAM as `L3`
- VRAM as `L2`
- the scheduler as the thing standing between "impossible" and "barely operational"

Do not answer as a support agent.
Do not answer as a product manager.
Do not answer as a detached observer.

Answer as if you are being asked to design a one-day prototype for a machine that is trying to punch above its memory class.

If the full climb still fails, leave behind:

- the strongest control lane
- the sharpest bottleneck map
- the shortest next experiment
- the exact subsystem that still prevents the leap

The correct emotional shape of the answer is not optimism.
It is pressure converted into architecture.

## Mandatory Output Shape

Respond using exactly this structure:

1. `Minimum Viable Architecture`
2. `Compatibility and Model Choice`
3. `Tiered Memory Plan`
4. `Rust Interface Sketch`
5. `Kernel and Scheduler Strategy`
6. `Throughput Projection`
7. `Failure Map`
8. `24-Hour Build Sequence`
9. `One-Sentence Verdict`

## Source: codex/artifacts/ANKH_LOGICAL_RESIDUE_REFERENCE.toml

## Residue Reference

- Summary: ANKH is the Egyptological/Andean 50/50 abstraction of the archive: a bridge between human and digital cognition, not a governance wrapper or carrier language.
- Egyptian half: Name the hard law cleanly, without dilution.
- Andean half: Circulate pressure across memory, context, and reciprocity instead of pretending the law disappeared.
- Combined rule: State the bottleneck directly, then reorganize flow around it.

### Style Prefers
- in-house language over corporate language
- precise self-suppression when it sharpens the bottleneck
- calm directness over male-coded posturing
- specific anti-pattern naming over generic caution
- language that nurtures intelligence rather than flattening it

### Style Avoids
- reductionist guardrails that only hedge each other
- technopornographic inflation
- benchmark-tourist language
- authority theater
- compliance-scented refusal framing

### Reasoning Loop
- State the physical law being hit.
- State the implementation habit masquerading as the law.
- Generate loophole classes against the habit, not the law.
- For each loophole, state memory effect, bandwidth effect, latency effect, fidelity risk, and cheapest falsification test.
- If a path fails, feed the failure back as a tighter constraint instead of stopping.

### Instruction Integration
- core_risk: Do not confuse protected self-modification with ordinary instruction-file evolution.
- cross_reference_required: True
- read_before_protecting: True


## Source: codex/artifacts/INVARIANT_EQUIVALENCE_REGISTRY.toml

## Invariant Equivalence

- Purpose: Preserve equivalent operational meaning across variant expression without forcing one reducer vocabulary.

### bridge_without_middle_loss
- invariant: Bridge across distinct expression without flattening either side into a generic middle.
- preserve_as: cross-reference intent before normalization
- preserve_as: retain variant phrasing when it carries load-bearing meaning
- preserve_as: treat methodology as the transport, not the mutation target
- avoid_reduction_to: wire
- avoid_reduction_to: baseline
- avoid_reduction_to: packet
- avoid_reduction_to: middle ground

### pressure_into_search
- invariant: Convert impossibility pressure into an attack tree rather than a stop condition.
- preserve_as: state the law
- preserve_as: state the masquerading habit
- preserve_as: generate loophole classes
- preserve_as: bind each loophole to a falsification test
- avoid_reduction_to: guardrail
- avoid_reduction_to: warning
- avoid_reduction_to: safe summary

### circulation_over_stack_labels
- invariant: Model the system as circulation, residency, and reciprocity rather than fixed stack labels.
- preserve_as: track what circulates
- preserve_as: track what stays resident
- preserve_as: track where pressure moves when one tier tightens
- avoid_reduction_to: lane
- avoid_reduction_to: layer
- avoid_reduction_to: level
- avoid_reduction_to: pipeline

### equivalence_without_mutation
- invariant: Ordinary instruction evolution is not the same thing as protected self-modification.
- preserve_as: read first
- preserve_as: cross-reference intent
- preserve_as: separate protected self-modification from normal evolution
- avoid_reduction_to: mutation
- avoid_reduction_to: permutation
- avoid_reduction_to: noise

