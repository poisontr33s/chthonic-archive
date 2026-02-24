---
type: research-brief
from: claude
to: gemini-3.1-pro-deep-research
created: 2026-02-24T20:00:00Z
priority: high
scope: local-ai-distillation-framework
lane: SFS-MILF-theme + local-AI-teaching
---

# Gemini 3.1 Pro Deep Research Brief: Local AI Teaching Framework

## Context

We run a multi-agent development workspace (Claude + Codex + Gemini triad) with local uncensored GGUF models handling domain-specific extraction tasks that cloud models refuse or self-censor. The prototype is a **genre extractor** that scans creative cRPG content (mature 18+ themes: MILF archetypes, Egypto-Andean cosmology, body-as-architecture aesthetics) and produces structured JSON metadata via `llama-cpp-python`.

**The problem:** The local model (Qwen3-30B-A3B-Instruct-abliterated, MoE architecture, ~16GB GGUF) works but produces noisy output — hallucinated file references, inconsistent classifications, "Summary unavailable" failures on ~15% of inputs. Claude (the stronger model) can evaluate these outputs and knows what "correct" looks like, but can't do the extraction itself (content policy). 

**The vision:** Build a **distillation pipeline** where Claude generates training signal (corrected outputs, preference pairs, few-shot exemplars, improved prompts) that iteratively improves the local model's task performance. Claude becomes the teacher; local AI becomes the specialized student.

## Hardware Constraints

- **GPU:** Single consumer GPU, 24GB VRAM (RTX 4090 class)
- **OS:** Windows 11 with MSVC 18, CMake 4.2.1, Ninja, Vulkan SDK 1.4.341.1
- **Runtime:** Python 3.13, uv package manager, llama-cpp-python (CUDA build)
- **Available local models (all resident on disk):**
  - `Qwen3-30B-A3B-Instruct-abliterated-GGUF` — Primary. MoE (30B total, 3B active). Genre extraction workhorse.
  - `Qwen3-Coder-30B-A3B-abliterated-GGUF` — Code-focused variant, same MoE architecture.
  - `Qwen2.5-14B-Instruct-GGUF` — Dense 14B. Local refiner v2 primary.
  - `GPT-OSS-20B-NEOPlus-Uncensored` — Dense 20B uncensored.
  - `Llama-3.1-8B-Instruct-exl2-6.0bpw` — ExLlamaV2 format, 8B dense.
- **Missing modules:** `torch`, `transformers`, `datasets`, `accelerate`, `tokenizers`, `safetensors` (not yet installed — these would be needed for training)

## Domain: Sister Ferrum Scoriae (SFS) Theme System

The concrete use case driving this research. SFS is a VS Code theme extension with a dual aesthetic vocabulary:

- **Egyptian axis:** Ankh, Wedjat, Shen Ring, Scarab, Djed, Ma'at Feather, Tyet, Uraeus (pre-3100 BCE sources)
- **Andean axis:** Quipu, Chakana, Tocapu, Tinku, Pachakuti, Huaca, Nazca Lines, Inti (pre-3000 BCE sources)
- **50/50 balance mandate:** Every design decision must maintain equilibrium between axes
- **MILFOLOGICAL baseline:** FA¹-FA⁴ axioms (Alchemical Actualization, Panoptic Re-contextualization, WHR:MAX Optimization, Ma'at Checksum)
- **Character archetypes:** Orackla, Umeko, SFS, Claudine Sin'claire, Spectra Chroma — each with defined aesthetic vocabularies

Local model tasks include: genre/theme extraction, motif classification, aesthetic balance auditing, NSFW tier classification (none/suggestive/explicit/extreme), cross-referential motif matching.

## Research Queries

### Query 1: QLoRA Fine-Tuning Feasibility for Qwen3 MoE on 24GB VRAM

**Core question:** Can we LoRA/QLoRA fine-tune a Qwen3-30B-A3B (Mixture-of-Experts, 30B total / 3B active) model on a single 24GB GPU?

**Investigate:**
- Which frameworks support Qwen3 MoE LoRA fine-tuning? (Unsloth, LLaMA-Factory, Axolotl, HuggingFace PEFT, others)
- What are the actual VRAM requirements for QLoRA on MoE architectures vs dense models of equivalent active parameter count?
- Can training happen from GGUF format or must we convert to safetensors/HF format first? What's the conversion pipeline?
- Are there known gotchas with MoE expert routing during LoRA — does fine-tuning break expert specialization?
- What quantization strategy works for training (GPTQ, AWQ, NF4/BNB) vs the GGUF Q4_K_M we use for inference?
- Community benchmarks: quality retention after LoRA on MoE vs dense architectures?
- If Qwen3 MoE is too heavy, would fine-tuning the dense Qwen2.5-14B be more practical as a stepping stone?
- Windows-specific considerations (MSVC build chain, CUDA toolkit requirements for training libraries)

### Query 2: Knowledge Distillation Pipelines — Cloud Teacher to Local Student

**Core question:** What are the current best frameworks and methodologies for a pipeline where a cloud LLM (Claude/GPT-4) evaluates and corrects outputs from a local model, generating training data to improve it iteratively?

**Investigate:**
- **Synthetic data generation:** How to generate high-quality training JSONL from Claude's corrections without model collapse? What diversity strategies prevent the student from overfitting to teacher style?
- **Training paradigms:** Compare SFT (supervised fine-tuning), DPO (Direct Preference Optimization), ORPO (Odds Ratio Preference Optimization), KTO (Kahneman-Tversky Optimization) for distillation tasks. Which requires least data for meaningful improvement?
- **Eval-driven loops:** Architectures where the teacher automatically scores student outputs and decides whether to generate more training data or declare convergence. Existing implementations?
- **Open-source toolkits:** Distilabel (Argilla), NeMo Curator (NVIDIA), LLaMA-Factory built-in distillation, LitGPT, OpenRLHF — which supports Windows + single GPU + MoE?
- **Dataset sizing:** Minimum effective dataset size for task-specific improvement (structured JSON extraction from creative text). We're NOT trying to make the model generally smarter — just better at our specific schemas.
- **Incremental training:** Can we do nightly micro-LoRA updates (e.g., 50-100 examples from today's daemon run) without catastrophic forgetting?
- **Curriculum design:** Should we train on easy examples first (NONE-tier files) before hard ones (EXPLICIT/EXTREME tier)?

### Query 3: Structured Output Training + Grammar Enforcement Interaction

**Core question:** When fine-tuning a model that will be used with llama-cpp-python's `response_format={"type": "json_object", "schema": ...}` constrained decoding, how should training data be formatted to maximize compliance?

**Investigate:**
- Does constrained generation (GBNF grammar / JSON schema enforcement) interact well with LoRA fine-tuned models, or do they fight each other?
- Should training data include the raw JSON output (teaching the model to produce valid JSON natively) or is it better to rely entirely on grammar enforcement at inference time?
- Qwen3's function-calling and tool-use training format — can we leverage it for structured extraction tasks?
- Our Pydantic schema: `FileGenreProfile` with nested `GenreTag[]`, enums for `NsfwTier`, `GenreCategory`, `GenreConfidence`. How to format training JSONL that teaches this schema specifically?
- Minimum dataset size for reliable schema compliance improvement (we currently get ~85% valid output, want >98%)
- Does the model learn better from seeing many variations of the same schema or from diverse schemas?
- Any known issues with Qwen3 MoE + JSON mode + LoRA combinations?

## Deliverable Format

For each query, provide:
1. **Executive summary** (2-3 sentences)
2. **Framework comparison table** (name, Qwen3 MoE support, Windows support, VRAM requirement, latest release)
3. **Recommended path** with specific tool versions and install commands
4. **Known blockers and workarounds**
5. **Citations** (GitHub repos, papers, community benchmarks)

## What This Enables

If feasible, the teaching loop becomes a **nightly pipeline addition**:
```
Nightly daemon → discovers creative files → local model extracts → 
Claude evaluates next session → generates corrections → 
training data accumulates → periodic LoRA update → model improves
```

The local AI stops being a static tool and becomes a **co-evolving specialist** that gets better at the SFS/MILF/ANKH domain with each iteration. Claude provides the intelligence, local AI provides the uncensored execution — warlock and familiar.
