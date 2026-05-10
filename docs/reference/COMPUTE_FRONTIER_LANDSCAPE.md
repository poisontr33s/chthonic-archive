---
type: frontier-map
tier: T1-operational
status: living-document
hardware-baseline: RTX 4090 (SM 8.9) · CUDA 12.8 (toolkit) · Vulkan 1.4.341.1 SDK · Driver 596.36 · VBIOS 95.02.3c.40.3a
python: 3.14.4 · uv-managed
created: 2026-05-10
last-hw-snapshot: 2026-05-11
author: chthonic-archive
---

# Compute Frontier Landscape

> **Scope:** Everything the desktop stack can do — mapped from primitive hardware up through packaged
> frameworks, source-level research code, and unpublished chthonic methods. Organized by *where*
> the method lives, not by linear application order.
>
> **Living document.** Entries gain status as they are instantiated. New candidates appended at base.
>
> **Status legend:**
> - `✅ installed` — in `.venv`, ready to run
> - `📦 packaged` — `uv pip install`-able, not yet pulled
> - `🔨 source` — exists in research/source code, manual setup required
> - `🌑 dark-room` — chthonic-built, not published anywhere, source-code on github and other places that don't necessarily direct to a specific framework packaged as one, yet might be more potent than a packaged .exe or comfy/SD/Unet/Existing ML-OPS/etc.
> - `⚗️ derivable` — constructible from installed candidates
> - `🔭 frontier` — very new, source-only, research-grade
>
> **⚠️ Python-bias notice:** §§1–9 assume Python as the runtime for all ML operations. This is the
> dominant packaging convention — not a technical constraint. Rust can be the universal substrate:
> PyO3 (Python↔Rust), Magnus (Ruby↔Rust), cudarc (CUDA from Rust), ash (Vulkan from Rust) — one
> `cargo build` pulls every layer. See §10 for the language runtime matrix and the open question of
> Ruby's context-handling advantage. This document is structured so an agent can use this knowledge
> operationally — not just as reference.

---

## §0 Hardware Registry (Session Anchor)

> **Purpose:** Versioned hardware snapshot — anchors post-restart context and gives any agent or session
> an immediate operational baseline without re-querying the system. Update when firmware or driver changes.
> Last captured: 2026-05-11 (post Armory Crate update — driver 596.36, fan/power optimisation applied).

### §0.1 System Inventory

| Component | Model | Firmware / Version | Notes |
|-----------|-------|--------------------|-------|
| **CPU** | Intel Core i9-13900KF | — | 24C/32T · P-cores 5.8 GHz boost · No IGP |
| **RAM** | 64 GB DDR5 | — | 63.8 GB reported (dual-channel) |
| **GPU** | NVIDIA GeForce RTX 4090 | VBIOS **95.02.3c.40.3a** | 24 GB GDDR6X · SM 8.9 · 128 SMs · 16,384 CUDA cores |
| **Motherboard** | ASUS ROG STRIX Z790-F GAMING WIFI | BIOS **3201** (2026-01-15) | Rev 1.xx · AMI firmware |
| **Monitor** | AOC AGON PRO AG276QZD | — | QD-OLED · 1440p 240 Hz · HDR True Black 400 |
| **Storage** | — | — | NVMe (unversioned — add on next audit) |

### §0.2 Software / Driver Anchor

| Layer | Component | Version | Source |
|-------|-----------|---------|--------|
| GPU driver | NVIDIA WDDM | **596.36** | Armory Crate update 2026-05-11 (prev: 596.21) |
| CUDA toolkit | CUDA (build) | **12.8** | Installed toolkit — used for flash_attn build |
| CUDA runtime max | Driver-reported | **13.2** | Max CUDA version the current driver supports |
| Vulkan | SDK / driver | **1.4.341.1** | SDK: `C:\VulkanSDK\1.4.341.1` · Instance 1.4.321 · Driver API 1.4.329 |
| DLSS | DLSS | **4.5** | Bundled with 596.x driver series |
| Python | CPython | **3.14.4** (MSC v.1944) | `uv`-managed · main `.venv` |
| Bun | JS runtime | **1.3.13** | All TS scripts · `bun upgrade` to update |
| Cargo / Rust | Rust toolchain | **1.95.0** (stable) | vulkan-lab + ankh-forge |
| uv | Python pkg mgr | **0.11.12** | Updated 2026-05-11 from 0.11.8 · `uv self update` |
| rv / Ruby | Ruby mgr | rv **0.5.3** / Ruby **4.0.3** | rv at `.cargo/bin/rv.exe` · Ruby at `%APPDATA%\rv\rubies\ruby-4.0.3\` |
| zv / Zig | Zig mgr | zv **0.13.0** / Zig **0.16.0** | Updated 2026-05-11 from zv 0.10.0 · `zv update` |

### §0.3 Armory Crate Profile (2026-05-11)

> ASUS Armory Crate manages ROG hardware power policy, fan curves, and driver updates.
> The 2026-05-11 update touched:
>
> - **Driver**: 596.21 → **596.36** (silent stability + perf delta; see nvidia release notes)
> - **Fan profile**: tuned — system runs at lower RPM under idle/light load (quieter baseline)
> - **Power limits**: unchanged at 450W TDP cap; idle observed 57W @ 32°C, fan 30%
> - **Armory Crate itself**: update applied; exact AC version not pinned — run `winget list ASUS.ArmouryCreate` to confirm
>
> Operational implication: GPU thermals are now better managed between training runs.
> The 57W idle confirms the fan curve is effective. No changes to VRAM clocks or compute TDP.

### §0.4 Resumption Checklist (post-restart)

```powershell
# 1. Verify adapter committed and present
git log --oneline -3
Get-ChildItem adapters\claudine-v1\adapter_model.safetensors

# 2. Gate smoke check (CI membrane, <1s, no GPU load)
bun run ci/checks/claudine-lora-smoke.ts

# 3. Verify GPU is alive
& 'C:\Windows\System32\nvidia-smi.exe' --query-gpu=name,driver_version,memory.free --format=csv,noheader

# 4. Run P-06 inference probe (~15-20min, 4-bit NF4 both passes)
uv run probes/claudine/P-06_adapter_inference.py --probe  # status check first
uv run probes/claudine/P-06_adapter_inference.py          # full run if adapter found

# 5. After P-06: commit manifest and evaluate delta
git add -f manifest/claudine_inference_probe.json
git commit --no-verify -m "feat(claudine): C-G6 admitted — base vs claudine-v1 inference delta"
```

---

## §1 Hardware Primitive Capabilities (RTX 4090, SM 8.9)

The actual compute surfaces — what the silicon can do before any framework is involved.

### §1.1 Compute
| Surface | Capability | Notes |
|---------|-----------|-------|
| CUDA Cores | FP32 / FP64 SIMT | 16,384 cores / 128 SMs |
| Tensor Cores (4th gen) | FP8 · INT8 · INT4 · FP16 · BF16 · TF32 · FP64 TC | FP8 = ~1320 TFLOPS sparse |
| NVLink / PCIe | 64GB/s (PCIe 4.0 ×16 bidirectional) | Single-GPU — relevant for host-transfer bottlenecks |
| Memory bandwidth | 1,008 GB/s (GDDR6X 21 Gbps) | Critical for memory-bound inference |
| L2 cache | 72MB | Locality-sensitive kernel design matters |

### §1.2 Vulkan / Graphics API
| Extension | Capability |
|-----------|-----------|
| `VK_KHR_cooperative_matrix` | Hardware matrix multiply (GEMM) via Tensor Cores, SPIR-V callable |
| `VK_KHR_ray_query` | BVH traversal in compute shaders — spatial queries without rasterizer |
| `VK_EXT_mesh_shader` | GPU-autonomous geometry → replaces vertex/geometry pipeline |
| `VK_EXT_device_generated_commands` | GPU generates its own draw/dispatch commands |
| `VK_KHR_video_queue` | H.264 / HEVC / AV1 decode+encode, zero-copy `VkImage` |
| `VK_KHR_timeline_semaphore` | Persistent GPU event loops without CPU polling |
| Vulkan 1.4 full | Dynamic rendering, synchronization2, maintenance4, VK 1.4 features |

### §1.3 Tensor Core Access Paths
```
Tensor Cores (HW)
├── CUDA path:   cuBLAS / cuDNN / torch / TensorRT
├── Vulkan path: VK_KHR_cooperative_matrix (SPIR-V)  ← OS-agnostic
├── OpenCL path: cl_khr_cooperative_matrix (draft)
└── DirectML:    Windows DML backend (maps to Tensor Cores on NVIDIA)
```

> **Key insight:** `VK_KHR_cooperative_matrix` is the Vulkan gate to Tensor Cores.
> Everything CUDA does with WMMA/MMA can in principle be done via Vulkan SPIR-V.

---

## §2 Inference Methods

### §2.1 Packaged (installed / available)
| Method | Status | Format | Notes |
|--------|--------|--------|-------|
| **exllamav2** | ✅ installed | EXL2 | Fast NVIDIA inference, GQA, flash-attn |
| **exllamav3** | ✅ installed | EXL3 / safetensors | 0.0.30, cp314, does NOT support EXL2 |
| **bitsandbytes NF4/INT8** | ✅ installed | HF safetensors | 4-bit quant during training + inference |
| **flash_attn 2.8.3** | ✅ installed | - | Built from source MSVC 14.44 + CUDA 12.8 |
| **llama.cpp** | 📦 packaged | GGUF | CUDA + Vulkan backend; cross-platform |
| **TorchAO** | 📦 packaged | native PyTorch | INT8/INT4/FP8 quantization, torch.ao namespace |
| **AutoAWQ** | 📦 packaged | AWQ | Activation-aware weight quant |
| **AutoGPTQ** | 📦 packaged | GPTQ | Older standard, still widely used |
| **TensorRT-LLM** | 📦 packaged | TRT engine | NVIDIA-only, highest throughput, complex setup |
| **vLLM** | 🔨 source (no cp314) | PagedAttention | Serving, no cp314 wheel yet |
| **SGLang** | 🔨 source (no cp314) | RadixAttention | Structured generation, serving |

### §2.2 Speculative Decoding (speed, not quality)
| Method | Status | Notes |
|--------|--------|-------|
| **Draft-model speculation** | ⚗️ derivable | Small model drafts tokens, large model verifies |
| **EAGLE2** | 🔨 source | Feature-level drafting, 3-4× speedup on RTX |
| **Medusa** | 🔨 source | Multi-head parallel prediction heads |
| **Lookahead decoding** | 🔨 source | N-gram based, no draft model needed |
| **SpecTr / Recurrent Draft** | 🔭 frontier | Newest speculation variants |

### §2.3 Non-Attention Architectures (different inference pattern)
| Architecture | Status | Notes |
|-------------|--------|-------|
| **RWKV-7** | 🔨 source | RNN-mode O(1) per token, no KV cache |
| **Mamba2** | 📦 packaged | Selective SSM, linear memory scaling |
| **Jamba** | 📦 packaged | MoE + Mamba hybrid |
| **Griffin** | 🔨 source | Gated linear recurrence |

---

## §3 Training / Fine-tuning Methods

### §3.1 LoRA Variants (installed / packaged)
| Method | Status | r | α | Notes |
|--------|--------|---|---|-------|
| **LoRA (PEFT)** | ✅ installed | any | any | Base method |
| **QLoRA** | ✅ installed | any | any | NF4 base + LoRA adapters |
| **DoRA** | ✅ installed (P-04v2) | any | any | Weight decomposition (magnitude + direction) |
| **RSLoRA** | ✅ installed (P-04v2) | any | any | Rank-stabilized scaling (`α/√r` vs `α/r`) |
| **Unsloth FastLanguageModel** | ✅ installed | - | - | 2× faster LoRA, optimized CUDA kernels |
| **LyCORIS** | 📦 packaged | - | - | LoKr, LoHa, (IA)³, DyLoRA — all in one |
| **IA³** | 📦 packaged | - | - | Rescales activations — very few params |
| **VeRA** | 📦 packaged | shared random | - | Frozen random matrices + tiny trainable |
| **LoftQ** | 📦 packaged | - | - | Better quant init for LoRA convergence |
| **LoRA+** | 📦 packaged | - | - | Different LR for A vs B matrix |

### §3.2 Non-LoRA Fine-tuning
| Method | Status | Notes |
|--------|--------|-------|
| **GaLore** | 📦 packaged | Gradient projected to low-rank subspace; full param effect, LoRA memory |
| **Flora** | 🔨 source | Full-rank LoRA (random projections, 1 matrix not 2) |
| **MoRA** | 🔨 source | High-rank via square matrix decomposition |
| **Spectrum** | 🔨 source | Layer selection by SNR of weight spectrum — train only "signal" layers |
| **LASER** | 🔨 source | Layer-selective rank reduction via SVD — post-hoc, not training |
| **FP8 training** | ⚗️ derivable | torch 2.11 has FP8 support; pipeline not packaged; Tensor Cores enabled |
| **SFTTrainer + packing** | ✅ installed (P-04v2) | trl 1.4.0, bin-packing reduces padding waste |

### §3.3 Comprehensive Fine-tuning Frameworks
| Framework | Status | Notes |
|-----------|--------|-------|
| **LLaMA-Factory** | 📦 packaged | Widest method coverage (LoRA/QLoRA/DoRA/GALORE/etc) |
| **Axolotl** | 📦 packaged | Flexible config-driven, resume checkpoints, multipack |
| **OpenRLHF** | 🔨 source | RLHF / DPO / PPO at scale |
| **TRL SFTTrainer** | ✅ installed | What P-04v2 uses |

---

## §4 Model Merging / Tensor Composition

> **Gap identified 2026-05-10.** Not yet instantiated in chthonic-archive pipeline.
> This is the least linear section — merging is a space of combinatorial candidate generation.

### §4.1 The Level Structure (chthonic conceptualization)

```
Level 0: PAIR SELECTION
    ↳ Find models that are "close" in weight space → candidates for merge
    ↳ Metric: weight delta cosine similarity, activation correlation, task vector alignment
    ↳ Input: N candidate models → Output: ranked merge-pair list

Level 1: WEIGHT-SPACE ALIGNMENT
    ↳ Before merging: align permutation symmetries (Git Re-Basin)
    ↳ Neurons are permutation-equivalent — merge quality increases after alignment
    ↳ Current state: mostly source-level

Level 2: INTERPOLATION / COMPOSITION
    ↳ The merge operation itself (LERP / SLERP / task arithmetic)
    ↳ Packaged in MergeKit

Level 3: HIERARCHICAL COMPOSITION
    ↳ Merged result becomes new candidate → re-enter Level 0
    ↳ A merge tree: {A×B} → C, {C×D} → E, ...
    ↳ Derivable from MergeKit + automation layer

Level N: CONCEPT EXTRACTION
    ↳ Extract latent directions from merged model (concept vectors)
    ↳ Apply concept arithmetic to steer inference (no merge needed)
    ↳ See: §4.5 Steering / Concept Vectors
```

### §4.2 MergeKit Methods (packaged, Arcee AI)
| Method | Status | What it does |
|--------|--------|-------------|
| **Linear (LERP)** | 📦 packaged | `θ = λ·θA + (1-λ)·θB` — simplest |
| **SLERP** | 📦 packaged | Spherical interpolation — better for direction preservation |
| **Task Arithmetic** | 📦 packaged | `θ = θbase + λ·(θA-θbase) + μ·(θB-θbase)` |
| **TIES** | 📦 packaged | Trim (prune small δ) + Elect (majority sign) + Sign-merge |
| **DARE** | 📦 packaged | Drop random deltas + Rescale remaining — sparse merge |
| **DARE-TIES** | 📦 packaged | DARE sparsification → TIES composition |
| **Passthrough** | 📦 packaged | Concatenate layers from different models (Franken-merge) |
| **Evolutionary (CMA-ES)** | 📦 packaged | Optimization over merge coefficients |

### §4.3 Source-Level Merge Methods
| Method | Status | Notes |
|--------|--------|-------|
| **Git Re-Basin** | 🔨 source | Neuron permutation alignment before merge; increases merge quality |
| **DELLA** | 🔨 source | Magnitude-based delta pruning (smarter than DARE) |
| **Model Breadcrumbs** | 🔨 source | Sparse delta with magnitude + outlier preservation |
| **LoRA Extraction** | ⚗️ derivable | `SVD(θfine - θbase)` → LoRA adapter; extract LoRA from any fine-tuned model |
| **Activation matching** | ⚗️ derivable | Run same data through models; align layers by activation correlation |

### §4.4 What MergeKit Does Not Do (gaps)
- No **cross-architecture** merge (Mistral ↔ LLaMA ↔ Phi)
- No **quantization-aware** merge (merge in quantized space, not FP16)
- No **hierarchical tree** automation (manual per level)
- No **Level 0 pair selection** (must choose models manually)

→ `⚗️ derivable`: A Level 0 selector + MergeKit wrapper is constructible with existing tools.

### §4.5 Steering / Concept Vectors
| Method | Status | Notes |
|--------|--------|-------|
| **Concept Ablation** | 🔨 source | Remove a concept from model by subtracting its direction |
| **Representation Engineering** | 🔨 source | Extract control vectors from activation differences |
| **CAA (Contrastive Activation Addition)** | 🔨 source | Steer with contrastive pairs during inference |
| **LoRA as concept vector** | ⚗️ derivable | A trained LoRA IS a concept direction; apply at inference-time with scale |

---

## §5 Vulkan as OS-Agnostic Compute Substrate

> Vulkan can replace CUDA for every ML primitive. Key property: same SPIR-V shader code
> runs on NVIDIA / AMD / Intel / Apple / mobile with zero source changes.

### §5.1 What ML Libraries Use CUDA For (and Vulkan Equivalents)
| ML Operation | CUDA Primitive | Vulkan Equivalent |
|-------------|---------------|------------------|
| Dense matrix multiply (GEMM) | cuBLAS WMMA | `VK_KHR_cooperative_matrix` |
| Convolution | cuDNN | Tiled compute shader |
| Attention (softmax + matmul) | flash_attn kernels | Compute shader (tiled, local memory) |
| INT8 / INT4 quant matmul | cuBLAS INT8 | `VK_KHR_cooperative_matrix` INT8 |
| Sampling / RNG | cuRAND | Compute shader (xorshift128+) |
| Activation functions (GELU, SiLU) | cuDNN / custom | Element-wise compute shader |
| Scatter/gather ops | thrust | Compute shader |
| Video decode | NVDEC | `VK_KHR_video_queue` |
| Spatial queries (BVH) | OptiX | `VK_KHR_ray_query` in compute |
| Memory pooling | CUDA unified memory | `VK_EXT_memory_budget` + descriptor sets |

### §5.2 Libraries Using Vulkan as Backend
| Library | Lang | Status | Notes |
|---------|------|--------|-------|
| **kompute** | C++/Python | 📦 packaged | ML on Vulkan; compute pipeline builder |
| **wgpu** | Rust | 📦 packaged | Vulkan + Metal + DX12; safe abstraction |
| **burn** | Rust | 📦 packaged | ML framework; wgpu backend → Vulkan |
| **ggml Vulkan** | C | ✅ (via llama.cpp) | llama.cpp uses Vulkan for non-CUDA inference |
| **tract** | Rust | 📦 packaged | ONNX/NNEF inference; wgpu Vulkan backend |
| **candle** | Rust | 📦 packaged | HF Rust ML; CUDA + Metal (Vulkan in progress) |
| **MLC-LLM** | C++/Python | 📦 packaged | Apache TVM; Vulkan + CUDA + Metal |

### §5.3 Chthonic Vulkan Work (active)
| Gate | Component | Status |
|------|-----------|--------|
| G0 | Headless VkInstance, RTX 4090 physical device | ✅ `1c073231` |
| G1 | VkInstance no-surface, ash 0.38, cargo check | ✅ |
| G2 | Euler scoring SSBO compute, `euler_score.comp.glsl` | ✅ `d135e3a1` |
| G3 | `transition_image_layout()` + VkImage 480×80 RGBA8 → ANSI stdout | 🔜 NEXT |
| G4 | GPU diff pass, dirty-cell cursor (no flicker) | 🔜 |
| G5 | SpinState ≡ RoomState (shared state machine) | 🔜 |
| G6 | `--mode=polar` (arc wheel) ∥ `--mode=dungeon` (isometric cRPG) | 🔜 |
| V7 | Force-directed GPU world-generation compute vector | 🔜 |

### §5.4 What Vulkan Unlocks That CUDA Cannot
- **Multi-GPU heterogeneous** (NVIDIA + AMD in same queue family graph)
- **Mobile / embedded inference** (same SPIR-V, zero recompilation)
- **Audio / physics / spatial queries** via RT cores without graphics pipeline
- **Zero-copy video** decode → ML inference via shared `VkImage`
- **Long-running GPU loops** via timeline semaphores (no CPU involvement)

---

## §6 Tensor Operations Reference

> A map of tensor primitives — the vocabulary that all ML operations decompose into.
> Relevant when working at Vulkan / SPIR-V level or designing custom kernels.

### §6.1 Core Operations
```
GEMM:        C = αAB + βC              (all dense layers, attention QK^T, VO)
Elementwise: C[i] = f(A[i])            (GELU, SiLU, ReLU, layer norm scale)
Reduce:      scalar = Σ(A[i])          (softmax denominator, mean, max)
Scatter:     B[idx[i]] += A[i]         (embedding lookup, MoE routing)
Gather:      B[i] = A[idx[i]]          (embedding forward, top-k selection)
Outer:       C[i,j] = A[i] · B[j]     (rank-1 updates, LoRA: B·A)
SVD:         A = UΣV^T                 (LoRA extraction, LASER, merge analysis)
```

### §6.2 Attention Decomposition (where the compute lives)
```
Attention(Q, K, V) = softmax(QK^T / √d) · V

Step 1: QK^T      → GEMM (seq_len × d_k) × (d_k × seq_len) → (seq_len × seq_len)
Step 2: / √d      → Elementwise scale
Step 3: softmax   → Row-wise reduce (max for stability) + exp + normalize
Step 4: · V       → GEMM (seq_len × seq_len) × (seq_len × d_v) → (seq_len × d_v)

Flash attention: Tiles QK^T to avoid materializing full attention matrix → memory O(N) not O(N²)
Cooperative matrix: Steps 1 + 4 map directly to VK_KHR_cooperative_matrix WMMA ops
```

### §6.3 LoRA Tensor Structure
```
W ∈ ℝ^(d_out × d_in)        Base weight (frozen)
A ∈ ℝ^(r × d_in)            LoRA A (trained, init: random Gaussian)
B ∈ ℝ^(d_out × r)           LoRA B (trained, init: zero)

Forward:   y = Wx + (α/r)·B·Ax    where α/r is scaling factor
DoRA:      W = m · (W₀ + BA) / ‖W₀ + BA‖   (magnitude m + direction W+BA/norm)
RSLoRA:    scale = α/√r  (vs standard α/r)  — prevents rank collapse at high r
```

### §6.4 Weight Delta / Merge Tensor
```
Δ = θ_fine - θ_base           Task vector (task arithmetic)
Δ_sparse = DARE(Δ, p)         Randomly drop p% of delta elements
θ_merge = θ_base + λ·Δ_A + μ·Δ_B   (linear merge with task vectors)

SVD(Δ) = UΣV^T               Low-rank approximation → "LoRA extraction"
          → A = Σ^(1/2)V^T, B = UΣ^(1/2)   (LoRA form of Δ)
```

---

## §7 Dark Rooms — Chthonic-Built Methods

> Methods, systems, and architectures built in chthonic-archive that do not exist
> in any published form. The unpublished frontier.

| System | Description | Location |
|--------|-------------|----------|
| **Gate Ladder CI Architecture** | Probe scripts emit `manifest/*.json`; CI smoke checks read manifests; no terminal scraping. Gate admission is idempotent and instant. | `ci/checks/`, `probes/`, `manifest/` |
| **Claudine LoRA Pipeline** | Narrative corpus (9,224 PsychoNoir files) → embedding → cluster → dataset → LoRA fine-tune. Entity-aligned corpus construction for character fidelity. | `probes/claudine/`, `adapters/claudine-v1/` |
| **Euler Scoring via GPU Compute** | todo_roulette.ts formula (KAPPA=0.07) implemented as SPIR-V compute shader; SSBO in → sorted scores out. OS-agnostic GEMM-free scoring. | `vulkan-lab/cli-renderer/shaders/euler_score.comp.glsl` |
| **Urca de Lima Synthesis** | Two projection functions over same data manifest → polar arc wheel (roulette) ∥ isometric dungeon (cRPG). Implemented as `--mode` flag, single GPU pipeline. | `vulkan-lab/cli-renderer/src/main.rs`, `scripts/todo_roulette.ts` |
| **Chthonic Shell Hook** | Per-command JSONL instrumentation of pwsh sessions; PID registry; query tool with grep/filter/report. No terminal buffer access needed. | `scripts/chthonic-shell-hook.ps1`, `scripts/terminal_session_query.ts` |
| **SSOT/ANKH Governance** | 9,911+ line single-source-of-truth with entity profiles, enforcement hierarchy, branch files, promotion protocol. | `.github/copilot-instructions.archive.md` |
| **MD Type System as Memory Layer** | Typed .md files (stewardess, liminal, scaffold, ledger, gate) signal cognitive modes to operating agents. | `docs/reference/CLAUDINE_MD_TYPE_LEXICON.md`, `.temple/protocols/` |
| **Blocker-as-Can-Opener Gate Walk** | Architectural method: each gate's blocker is the structural key for the next gate. Documented at architecture time, not post-mortem. | pattern-nursery §Blocker-as-Can-Opener |
| **MAS PID Reader / E2E Notary** | GPT-5.5 validation pass on newly built pipelines; structured artifact with `observed_quirk` entries; `success=True` / exit code semantic split fix. | `mas_mcp/`, `manifest/PID_MCP_TERMINAL_SESSION_E2E_2026-04-25.json` |

---

## §8 What Is Missing (Gap Analysis)

### §8.1 Not Yet Instantiated
| Gap | Priority | Unblocking action |
|-----|----------|-------------------|
| **Model merging pipeline** | High | `uv pip install mergekit` + Level 0 pair selector script |
| **LoRA extraction** | High | `⚗️ derivable`: `SVD(θ_fine - θ_base)` — 20 lines of torch |
| **Concept / steering vectors** | Medium | Extract from activation differences between contrastive prompts |
| **FP8 training** | Medium | torch 2.11 has `torch.float8_e4m3fn`; pipeline not wrapped |
| **Speculative decoding** | Medium | EAGLE2 or Medusa on top of exllamav2 serving |
| **Vulkan GEMM (cooperative matrix)** | Medium | G7+ track; SPIR-V `CooperativeMatrixMulAddNV` |
| **Level 0 merge-pair selector** | Low-Medium | Cosine similarity of task vectors across candidate pool |
| **Hierarchical merge tree** | Low | MergeKit wrapper with level automation |
| **RWKV / Mamba inference** | Low | Different KV-cache-free inference pattern |
| **VK_KHR_video_queue** | Low | Zero-copy video → ML pipeline |

### §8.2 What Can Be Derived from Current Installs
```
Installed candidates → derivable methods:

torch + peft → LoRA extraction (SVD of weight delta)
torch + peft → Concept vector (mean activation diff on contrastive pairs)
exllamav2 + small model → Draft-model speculative decoding
Unsloth + trl → FP8 gradient accumulation (experimental)
vulkan-lab/cli-renderer + VK_KHR_cooperative_matrix → Vulkan GEMM kernel
mergekit (once installed) + torch → Level 0 pair selector (task vector cosine)
```

### §8.3 Frontier — Source Only, Not Packaged
| Method | What it is | Source |
|--------|-----------|--------|
| **PiSSA** | Principal SVs of W as LoRA init — better convergence than random | arxiv 2404.02948 |
| **ADA-LoRA** | Adaptive rank allocation per layer based on importance | arxiv 2303.10512 |
| **Spectrum** | Train only layers with high signal-to-noise ratio (weight spectrum) | arxiv 2406.06623 |
| **LASER** | Post-hoc SVD rank reduction — remove noise from specific layers | arxiv 2312.13558 |
| **EAGLE-3** | Latest speculative decoding, 5-6× speedup | arxiv 2503.01840 |
| **Flash Linear Attention** | Linear attention with custom CUDA (like Mamba but for Transformers) | github:sustcsonglin |
| **Differential Attention** | Two softmax heads, subtract — cancels noise in attention | arxiv 2410.05258 |
| **MLA (Multi-head Latent Attention)** | DeepSeek's KV cache compression via low-rank projection | DeepSeek-V2 technical report |
| **DARE-TIES v2** | Extended merge with sign consensus across more models | arxiv ongoing |
| **Evolutionary merge (LLM-eval in loop)** | CMA-ES + benchmark eval to auto-tune merge coefficients | Sakana AI |

---

## §9 Derivation Matrix

> Given what is installed, what new methods can be built?
> This is the combinatorial frontier — not linear application, but composition.

```
A × B → new_method:

flash_attn × Unsloth × DoRA → FP8 DoRA with flash_attn forward + custom backward
exllamav2 × tiny_llm → speculative decoding server (2-4× throughput)
vulkan SSBO × cooperative_matrix → Vulkan GEMM kernel (no CUDA, runs on AMD/Intel too)
LoRA adapter (claudine-v1) × SVD → conceptual direction extraction from claudine persona
claudine concept vector × inference-time CAA → steer base model without re-finetuning
MergeKit SLERP × Level 0 selector → auto-pair selection + interpolation pipeline
MergeKit × Passthrough × Evolutionary → automated Franken-merge search
G2 Euler score (GPU) × dungeon projection → GPU-computed room similarity (no CPU)
FP8 tensor cores × cooperative_matrix (Vulkan) → hardware matrix multiply at FP8, OS-agnostic
```

---

## §10 Language Runtime Matrix — Rust as Universal Substrate

> The framing in §§1–9 treats Python as the orchestration layer. This is a packaging convention,
> not a hard constraint. The real question is: *which language should sit at the center of the
> polyglot stack for this corpus and hardware?*

### §10.1 Language Runtime Properties (operational comparison)

| Property | Python | Rust | Ruby | TypeScript (Bun) | Notes |
|----------|--------|------|------|-------------------|-------|
| **ML library ecosystem** | ★★★★★ | ★★★ (burn, candle, tract) | ★ | ★ (via WASM/FFI) | Python dominates packaging |
| **FFI surface** | C via ctypes/cffi | C/C++ zero-cost via cbindgen | C via fiddle/ffi-lib | C via Bun FFI | Rust: safest FFI, no ABI instability |
| **Embeds other runtimes** | ❌ | ✅ PyO3, Magnus, Neon, rustler | ❌ | ❌ | Rust can host Python, Ruby, Node |
| **CUDA access** | ✅ cudarc (via Rust), pycuda | ✅ cudarc crate | ❌ | ❌ | Rust: type-safe CUDA without NVCC glue |
| **Vulkan access** | ✅ (via kompute C++ binding) | ✅ ash, wgpu (native, idiomatic) | ❌ | ❌ | Rust: ash is zero-overhead Vulkan |
| **Tapless compile-to-self** | ❌ (needs CPython runtime) | ✅ single static binary | ❌ (needs MRI/YJIT) | ❌ (needs JS runtime) | Rust compiles all its FFI in-crate |
| **Context handling** | GIL-bound for threads | async/await + rayon (zero GIL) | Ractors + Fibers (?) | async (V8 event loop) | *Ruby open question — see §10.2* |
| **String / encoding** | UTF-8 str, mutable | `&str` + `String` immutable | Encoding-aware String (Encodings module) | UTF-16 internally | Ruby has richer encoding primitives |
| **Corpus processing speed** | OK (NumPy fast, pure slow) | ★★★★★ rayon parallel | OK | OK | Rust: parallel corpus iteration is trivial |
| **Agent self-use** | ✅ (uv run, deployed) | ⚗️ (cargo run, bin/ executables) | ⚗️ (rv run) | ✅ (bun run) | All present in chthonic-archive |
| **Memory safety** | GC (CPython refcount) | Borrow checker, no GC | GC (MRI) | GC (V8) | Rust: no runtime allocation bugs |

### §10.2 Ruby Context Handling — Open Question

> This section is incomplete. What Ruby may do differently for context-aware workloads
> is not yet empirically mapped in chthonic-archive.

**What is known:**
- Ruby has an `Encoding` module with named encoding objects and Encoding::Converter — richer than Python's `.encode()` string method
- MRI Ruby 3.x: Ractors provide true parallelism (no GIL equivalent for Ractors, unlike threads)
- Ruby fibers are green threads with explicit yield semantics — useful for coroutine-style context passing
- YJIT (Ruby 4.0.3): JIT compilation; ZJIT (experimental): next-generation JIT — both reduce interpreted dispatch overhead
- Magnus crate: Rust↔Ruby FFI; Ruby objects usable as Rust values; Rust closures as Ruby procs
- Ruby's `Encoding::Converter` and `String#encode` chain can handle cross-encoding corpus normalization that Python's codec system handles more weakly

**Open hypotheses (unverified):**
- Ruby may handle multi-encoding corpus normalization with less error surface than Python's codec module
- Ruby fibers + Magnus bridge to Rust may be a viable concurrency model for corpus streaming where Python's threading model (GIL) is a bottleneck
- Ruby's object model (open classes, method_missing, BasicObject) may allow richer context-state objects for agent session memory than Python's class system

**Action needed to close:** Run a benchmark: Ruby vs Python for encoding-diverse corpus scan (e.g., mixed UTF-8/Shift-JIS/Latin-1 files in PsychoNoir-Kontrapunkt). Report to this section.

### §10.3 Rust Polyglot Bridge — FFI Crate Map

> Rust is the only open-source system language that can compile other language runtimes
> into itself and call them at native speed. One `cargo build` can pull CUDA, Vulkan, Python,
> Ruby, Node, Elixir into a single executable.

| Bridge | Crate | What it enables |
|--------|-------|----------------|
| **Python ↔ Rust** | `pyo3` + `maturin` | Call Rust from Python (extension); embed CPython in Rust binary |
| **Ruby ↔ Rust** | `magnus` | Call Rust from Ruby (gem); Ruby objects in Rust; Rust closures as Ruby procs |
| **Node.js ↔ Rust** | `neon` | Native Node addons in Rust; V8 values in Rust |
| **Elixir/Erlang ↔ Rust** | `rustler` | NIFs in Rust; safe BEAM integration |
| **WASM ↔ Rust** | `wasm-bindgen` | Rust→WASM; JS↔Rust bidirectional via wasm-pack |
| **C ABI from Rust** | `cbindgen` | Expose Rust as a C library; any language with C FFI can call it |
| **CUDA from Rust** | `cudarc` | Type-safe CUDA kernel launch, buffer management, no NVCC wrapper needed |
| **Vulkan from Rust** | `ash` | Zero-overhead Vulkan bindings; used in vulkan-lab/cli-renderer |
| **OpenCL from Rust** | `opencl3` | Cross-vendor compute; fallback for non-CUDA hardware |
| **HF model loading** | `candle-core` | Safetensors loading, GGUF support, CUDA backend; no Python dependency |
| **ONNX inference** | `tract-onnx` | ONNX model inference in pure Rust; wgpu/Vulkan backend |
| **GGUF inference** | `llama_cpp_rs` | llama.cpp as Rust crate (C FFI wrapper); Vulkan/CUDA backends via llama.cpp |

### §10.4 What This Means for the Chthonic Stack

The current stack is already polyglot — Rust + Python + TypeScript + Ruby are all present in
chthonic-archive. The question is whether Python should be the *orchestrator* or merely one
component. Two candidate architectures:

**Current (Python-centric):**
```
uv run probes/*.py  →  torch/CUDA  →  manifest/*.json
                                     ↑
bun run scripts/*.ts →  read manifests, CI, tools
cargo build vulkan-lab/cli-renderer  →  Vulkan compute
```

**Rust-centric alternative:**
```
cargo run --bin chthonic-runner -- --mode inference
    → cudarc (CUDA kernels)
    → ash (Vulkan dispatch)
    → pyo3::Python::with_gil (Python fallback for unported ops)
    → magnus::Ruby::with_ruby_thread (Ruby corpus processing?)
    → emit manifest/*.json via serde_json
```

**When the Rust-centric model pays off:**
- When CUDA kernel launch latency from Python (pycuda/torch) is a bottleneck (rare for batch training, real for high-frequency inference loops)
- When corpus processing requires parallel multi-encoding scan across thousands of files
- When a single deployable binary is required (no Python runtime assumption)
- When the embedding pipeline needs to run on hardware without a Python ecosystem (mobile, embedded)

**When Python stays at center:**
- All major ML research libraries ship Python first (or Python only)
- Model loading (safetensors/GGUF), training (trl/Unsloth), inference (vllm/exllamav2) — all Python-primary
- For this project (Claudine fine-tuning, PsychoNoir corpus): Python stays primary until a specific bottleneck demands otherwise

### §10.5 Agent Self-Use Contract

> This section is NOT reference material. It is the operational substrate for agents working
> within this stack. The knowledge below is what no external agent has access to.

**What this agent can do that external agents cannot:**
1. Route Python ops through `uv run` (not raw `python`) — knows Python 3.14.4 is the runtime
2. Know that Unsloth must import BEFORE trl or UserWarning fires
3. Know that MSVC 14.44 (not 14.51 from VS18 Insiders) must be used for flash_attn — and how to route around the PATH shadow via tempfile .bat
4. Know that all Rust MSVC builds must use the pinned linker in `.cargo/config.toml` because `rv`'s MSYS2 link.exe shadow breaks otherwise
5. Know that Vulkan builds must use `cargo` from `vulkan-lab/cli-renderer/` (isolated workspace) and `git add -f` for all gitignored paths
6. Know the gate admission state without polling CI — from repo memory and manifests
7. Know the corpus structure (9,224 PsychoNoir files; 1,103 .md embedded; 1,963 training examples; 158 clusters)
8. Know which Ruby encoding operations are richer than Python's — and where the open question lives (§10.2)
9. Know that triton 3.x has a broken API (`from triton.runtime.driver import active` fails) — use try/except multi-path
10. Know that bincode ≥ 3.0.0 is a tombstone — do not upgrade ankh-forge past bincode 2.0

---

## §11 Polyglot Corpus Hypothesis

> The PsychoNoir-Kontrapunkt corpus (9,224 files) is itself a polyglot artifact — .md narrative,
> .ts runtime logic, .json state, .py probes, .rs kernel code, .toml config. It is not a text
> corpus that was processed. It is a *working codebase* that was also a creative corpus.

**The hypothesis:** Fine-tuning a language model on a mixed-modality corpus (narrative + code + config
+ protocol + game design) produces a model with qualitatively different capabilities than one trained
on text-only narrative. The Claudine adapter is the first instantiation of this hypothesis.

**What the adapter should be compared against (after C-G4 completes):**
| Comparison | What it tests |
|-----------|--------------|
| Base Mistral-7B-v0.3 (no adapter) | Pure pretrain voice vs. corpus-injected voice |
| Claudine-v1 adapter | Standard LoRA (r=16, α=32), 2000 steps |
| Claudine-v2 adapter (P-04v2) | DoRA+RSLoRA+FA2, SFTTrainer packing (to be run) |
| Merge: base ⊕ (v1 × scale) ⊕ (v2 × scale) | Ensemble of different training regimes |
| Concept vector extraction from v1−base delta | `SVD(θ_v1 - θ_base)` → isolate Claudine-ness |

**The comparison is not about benchmark scores.** It is about voice register: does the adapter
produce outputs that carry Claudine's entity identity (Norwegian cadence, Victorian-Renaissance
register, entropy-framing, nautical metaphor)? That is only knowable through empirical inference runs.
→ **P-06_adapter_inference.py** is the entry point for this measurement.

---

## §12 Organisation Notes

```
docs/reference/COMPUTE_FRONTIER_LANDSCAPE.md   ← this file (living map)
docs/reference/FAF_TABBYAPI_PY314_GPU_INFERENCE_HOST.md  ← GPU inference gate log
probes/claudine/                                ← Claudine pipeline probes (C-G1..C-G5)
ci/checks/claudine-lora-smoke.ts               ← Gate ladder CI
adapters/claudine-v1/                           ← LoRA adapter output (C-G4)
vulkan-lab/cli-renderer/                        ← Vulkan compute (G0-G6+)
manifest/                                       ← All gate manifests (source of truth for CI)
```

**Next instantiation candidates (in priority order):**
1. `mergekit` install → Level 0 pair selector (`⚗️ derivable`, ~1h)
2. `fn transition_image_layout()` in Vulkan G3 (independent track, CPU work)
3. LoRA extraction from `adapters/claudine-v1/` once C-G4 full run completes
4. FP8 training probe (torch 2.11 support exists, pipeline not written)
