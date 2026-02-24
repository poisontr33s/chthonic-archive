---
type: standard
category: local-ai
status: canonical
created: 2026-02-24
author: Claude Code Opus 4.6
synthesized-from:
  - claude/mailbox/Local_AI_Teaching_Framework_Research_Variant1of2.md
  - claude/mailbox/Local_AI_Teaching_Framework_Research_Variant2of2.md
research-agent: Gemini-3 Pro Deep Research
---

# Local AI Teaching (LAT) — Canonical Specification

**@SID:** STD_LAT_SPEC_V1
**@Context:** Local AI Infrastructure / Knowledge Distillation
**@Purpose:** Canonical specification for the teacher-student distillation pipeline
              that continuously refines the local Qwen3-30B-A3B MoE model via
              cloud-generated training signals, GBNF grammar synergy, and nightly
              micro-LoRA updates.

> **Research Provenance:** Consolidated from two independent Gemini-3 Pro Deep
> Research variants (2026-02-24). Both variants converge on identical architectural
> decisions; divergences are noted where they occur.

---

## 1. Problem Statement

The local inference stack (Qwen3-30B-A3B via llama-cpp-python with GBNF constrained
decoding) exhibits a **15% execution failure rate** on structured JSON extraction
from creative cRPG content. Failures manifest as:

- Hallucinated file references
- Inconsistent thematic/NSFW-tier classifications
- Abrupt generation collapses ("Summary unavailable")
- GBNF logit coercion distorting semantic coherence

**Target:** Reduce failure rate to **< 2%** via continuous distillation.

---

## 2. Hardware Constraints

| Resource         | Value                                |
|------------------|--------------------------------------|
| GPU              | NVIDIA RTX 4090                      |
| VRAM             | 24 GB                                |
| Compute Cap.     | sm_89                                |
| OS               | Windows 11 (MSVC 18, CMake 4.2.1)   |
| Python           | 3.13                                 |
| CUDA             | 13.x                                 |
| Inference Engine | llama-cpp-python (GGUF Q4_K_M)       |

**VRAM Budget during training:**

| Component                    | VRAM     |
|------------------------------|----------|
| 4-bit base model (Unsloth)   | ~17.5 GB |
| LoRA adapters + optimizer    | ~4.0 GB  |
| Activations + gradients      | ~2.5 GB  |
| **Total**                    | **~24 GB** |

---

## 3. Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    NIGHTLY DAEMON CYCLE                       │
│                                                              │
│  ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐  │
│  │ Inference│───►│ Failure  │───►│ Teacher  │───►│ Replay │  │
│  │ + Flag   │    │ Triage   │    │ Eval     │    │ Buffer │  │
│  │ (local)  │    │ (local)  │    │ (Claude) │    │ Assem. │  │
│  └─────────┘    └──────────┘    └──────────┘    └───┬────┘  │
│                                                      │       │
│  ┌─────────┐    ┌──────────┐    ┌──────────┐        │       │
│  │ Redeploy│◄───│ GGUF     │◄───│ Micro    │◄───────┘       │
│  │ Daemon  │    │ Export   │    │ LoRA SFT │                 │
│  │ (local) │    │ (local)  │    │ (local)  │                 │
│  └─────────┘    └──────────┘    └──────────┘                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 3.1 Phase Sequence

| Phase | Name                  | Engine        | VRAM State          |
|-------|-----------------------|---------------|---------------------|
| 1     | Inference + Flagging  | llama-cpp     | ~8 GB (inference)   |
| 2     | Failure Triage        | Python script | CPU only            |
| 3     | Teacher Evaluation    | Claude API    | CPU only (network)  |
| 4     | Replay Buffer Assem.  | Python script | CPU only            |
| 5     | Micro-LoRA SFT        | Unsloth       | ~24 GB (training)   |
| 6     | GGUF Export           | Unsloth       | ~17.5 GB            |
| 7     | Redeploy              | llama-cpp     | ~8 GB (inference)   |

**Critical:** Phases 1 and 5 are mutually exclusive — the inference daemon
**must** be terminated before training begins to free VRAM.

---

## 4. QLoRA Fine-Tuning Configuration

### 4.1 Framework Selection

| Framework      | MoE Support        | Win11  | VRAM (30B MoE) | Verdict      |
|----------------|--------------------|--------|-----------------|--------------|
| **Unsloth**    | Native (Triton)    | Yes    | ~17.5 GB        | **Mandatory** |
| LLaMA-Factory  | Via HF abstraction | Yes    | ~22-24.5 GB     | Marginal     |
| Axolotl        | Partial            | WSL2   | > 24 GB         | Inviable     |
| MS-Swift       | Yes                | Yes    | OOM-prone       | Inviable     |
| vLLM/PEFT      | Experimental       | WSL2   | Variable        | Inviable     |

**Decision:** Unsloth is the only framework that guarantees execution below the
24 GB hardware ceiling.

### 4.2 Model Loading

```python
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen3-30B-A3B",
    load_in_4bit=True,          # Dynamic NF4 quantization
    max_seq_length=4096,        # Conservative for training
    dtype=None,                 # Auto-detect BF16/FP16
)
```

**CRITICAL — Format Conversion Rule:**
- **NEVER** reverse-convert GGUF → Safetensors (lossy, destroys latent geometry)
- **ALWAYS** train on pristine Safetensors from HuggingFace
- **ALWAYS** export via `save_pretrained_gguf()` (single forward conversion)

### 4.3 LoRA Target Configuration

```python
model = FastLanguageModel.get_peft_model(
    model,
    r=16,                       # Low rank (constrained for abliteration safety)
    lora_alpha=32,
    lora_dropout=0,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    # CRITICAL: Router/gating layers are EXCLUDED by default in Unsloth.
    # Do NOT add router layers to target_modules.
    use_gradient_checkpointing="unsloth",
)
```

### 4.4 Invariants

| Rule | Rationale |
|------|-----------|
| **Freeze MoE router** | Prevents mode collapse. Router adapts organically via shifted expert activations. |
| **LoRA rank r ≤ 16** | Preserves abliteration vectors. Higher ranks risk overwriting the orthogonal refusal-direction projections. |
| **Learning rate ≤ 5e-5** | Abliterated models are fragile. V2 recommends 2e-5 to 5e-6 for maximum stability. |
| **max_seq_length ≤ 4096** | Higher context during training causes OOM spikes from MoE routing memory allocation. |
| **No DeepSpeed** | ZeRO-3 partitioning breaks gradient flow with LoRA on single-GPU MoE architectures. |
| **Paged AdamW 8-bit** | Dynamically offloads optimizer states to system RAM during computation spikes. |

---

## 5. Knowledge Distillation Pipeline

### 5.1 Training Paradigm Selection

| Paradigm | VRAM     | Schema Adherence | Verdict       |
|----------|----------|------------------|---------------|
| **SFT**  | Baseline | Highest for rigid JSON | **Primary** |
| DPO      | 2× (needs reference model) | High for stylistic | **Inviable** (OOM) |
| ORPO     | Baseline | High for preference | Fallback only |
| GRPO     | High     | Reasoning tasks  | Out of scope  |

**Decision:** SFT is the mandatory paradigm for structured JSON extraction.
ORPO is reserved as a fallback if persistent stylistic drift appears after SFT
convergence.

### 5.2 Teacher Evaluation Protocol

```
┌──────────────────────────────────────────────────────────┐
│ CLAUDE TEACHER EVALUATION PROMPT (simplified)            │
│                                                          │
│ System: You are a JSON extraction evaluator. Evaluate    │
│ the local model's output against the FileGenreProfile    │
│ schema. Apply FA¹-FA⁴ axioms. Enforce the 50/50         │
│ Egypto-Andean balance mandate.                           │
│                                                          │
│ Input:                                                   │
│   - Source text (cRPG content)                           │
│   - Local model's failed extraction                      │
│   - FileGenreProfile JSON Schema                         │
│                                                          │
│ Output:                                                  │
│   1. Evaluation rubric score (0-100)                     │
│   2. Failure classification (hallucination / truncation  │
│      / balance violation / schema error)                 │
│   3. Corrected <think> reasoning trace                   │
│   4. Corrected <answer> JSON                             │
│                                                          │
│ Gate: Only corrections scoring 100% on schema            │
│ compliance enter the training queue.                     │
└──────────────────────────────────────────────────────────┘
```

### 5.3 Synthetic Data Format — Two-Stage Reasoning

The training data uses a `<think>` + `<answer>` formulation that lets the MoE
reason in natural language before committing to structured output:

```jsonl
{
  "messages": [
    {
      "role": "system",
      "content": "Extract the SFS aesthetic profile. Maintain the 50/50 Egypto-Andean balance mandate. Apply FA¹-FA⁴ axioms. Provide reasoning inside <think></think> tags, then the final JSON inside <answer></answer> tags. JSON must conform to the FileGenreProfile schema."
    },
    {
      "role": "user",
      "content": "<source_text>...</source_text>"
    },
    {
      "role": "assistant",
      "content": "<think>\n1. FA¹ Alchemical Actualization: Ankh (Egyptian) + Quipu (Andean) → 50/50.\n2. Character Archetype: Umeko identified.\n3. NsfwTier: EXPLICIT (body-as-architecture present).\n4. GenreConfidence: HIGH.\n</think>\n<answer>\n{\"nsfw_tier\": \"EXPLICIT\", \"aesthetic_balance\": {\"egyptian_ratio\": 0.5, \"andean_ratio\": 0.5}, \"motifs\": [\"Ankh\", \"Quipu\"], \"character\": \"Umeko\"}\n</answer>"
    }
  ]
}
```

**Rationale:** Permits the MoE experts to perform semantic analysis (FA¹-FA⁴
evaluation, motif matching) in an unconstrained natural-language latent space
*before* transitioning into strict JSON syntax. This directly eliminates the
root cause of GBNF logit coercion failures.

### 5.4 Dataset Sizing

| Phase        | Examples   | Purpose                                    |
|--------------|------------|--------------------------------------------|
| Bootstrap    | 150–200    | Baseline Egypto-Andean balance, NONE/SUGGESTIVE tiers |
| Intermediate | 300–500    | EXPLICIT tier, cross-referential motif matching |
| Advanced     | 500–1000   | EXTREME tier, dense FA¹-FA⁴ interpolations |
| Convergence  | Throttle   | Auto-stop when schema compliance > 98%     |

**Key insight:** Diversity vastly outweighs volume. 500-1000 curated examples
are sufficient for >98% compliance on a static schema. Beyond 5000, returns
diminish rapidly.

---

## 6. Catastrophic Forgetting Mitigation

### 6.1 Replay Buffer (Mandatory)

Every nightly training batch **must** be constructed from stratified sampling:

| Segment                   | Ratio | Source                              |
|---------------------------|-------|-------------------------------------|
| New teacher corrections   | 25-50% | Claude-generated from today's failures |
| Historical SFS successes  | 25-40% | Golden Dataset (SQLite, tagged by axis/archetype/tier) |
| General reasoning data    | 15-25% | Chain-of-thought / FineTome / Open-Math |

**V1 recommends:** 50% new / 25% historical / 25% general.
**V2 recommends:** 25% new / 75% golden replay (more conservative).
**Decision:** Start with V2's conservative 25/75 ratio during bootstrap phase,
shift toward V1's 50/25/25 once baseline schema compliance exceeds 90%.

### 6.2 Advanced Regularization (Future)

| Technique | Mechanism | When to Apply |
|-----------|-----------|---------------|
| **OPLoRA** | SVD decomposition constrains LoRA updates to orthogonal complement of pre-trained directions | If forgetting persists despite replay buffer |
| **LaLoRA** | Laplace approximation estimates parameter confidence; constrains high-curvature updates | If domain-specific vocabulary degrades |
| **SafeMoE** | Penalty loss preserving routing weight gap between fine-tuned and original aligned model | If expert specialization regresses |

### 6.3 Early Stopping Gate

```
IF validation_loss INCREASES while training_loss DECREASES:
    → ABORT update
    → DISCARD adapter
    → WAIT for larger data accumulation

Holdout validation set: 200 diverse examples covering all domain axes.
```

---

## 7. SFT + GBNF Grammar Synergy

### 7.1 The Latent Distortion Problem

| Configuration       | Schema Adherence | Logical Accuracy | Latency  |
|---------------------|------------------|------------------|----------|
| Pure Prompt Eng.    | ~85%             | High             | Fast     |
| Pure GBNF           | 100% syntax      | Medium (halluc.) | Slower   |
| Pure SFT            | ~95%             | High             | Fast     |
| **SFT + GBNF**      | **100%**         | **Highest**      | **Fastest** |

**Without SFT:** GBNF masks the model's natural-language tokens, forcing
sampling from suppressed low-probability tail → semantic coherence collapses →
syntactically valid but logically hallucinated JSON.

**With SFT:** The model's highest-probability tokens naturally align with JSON
structure → GBNF acts as a passive safety net, rarely triggered → maximum
inference speed and accuracy.

### 7.2 Pydantic Schema Bridge

```python
from pydantic import BaseModel

class FileGenreProfile(BaseModel):
    nsfw_tier: str
    genre_category: str
    genre_tags: list[dict]
    motifs: dict
    aesthetic_balance: dict
    character: str | None
    genre_confidence: str

# Training: embed schema in system prompt
schema_str = FileGenreProfile.model_json_schema()

# Inference: pass to llama-cpp constrained decoding
response = llm.create_chat_completion(
    messages=messages,
    response_format={
        "type": "json_object",
        "schema": FileGenreProfile.model_json_schema()
    }
)
```

### 7.3 GBNF Optimization

- Pre-compile grammar string offline via `json-schema-to-grammar.py`
- Cache compiled grammar — do not recompile per request
- Permit flexible whitespace: `ws ::= [ \t\n]+` before opening `{`
- Set `max_tokens ≥ 2048` to prevent truncation before closing `}`

---

## 8. Environment Setup

### 8.1 Decision: Native Windows vs WSL2

| Approach        | Triton Stability | Build Complexity | Verdict        |
|-----------------|------------------|------------------|----------------|
| Native Win11    | Fragile          | High (MSVC quirks) | Viable with pre-compiled wheels |
| **WSL2 Ubuntu** | Stable           | Standard         | **Recommended for automation** |

**Decision:** Use WSL2 for unattended nightly training automation. Keep
llama-cpp-python inference daemon native on Windows.

### 8.2 Environment Initialization

```bash
# WSL2 Ubuntu 22.04+
sudo apt update && sudo apt install build-essential cmake ccache ninja-build -y

# Isolated environment
conda create --name lat_env python=3.13 -y
conda activate lat_env

# PyTorch targeting CUDA 13.x
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130

# Unsloth
pip install --upgrade --force-reinstall --no-cache-dir unsloth unsloth_zoo
pip install --no-deps trl peft accelerate bitsandbytes
```

---

## 9. Nightly Daemon Lifecycle

```
╔══════════════════════════════════════════════════════════════╗
║                 NIGHTLY DAEMON SEQUENCE                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  22:00  ┌─ Phase 1: Inference + Flagging ──────────────────┐ ║
║         │ • llama-cpp processes day's cRPG files           │ ║
║         │ • Daemon logs: grammar conflicts, hallucinations,│ ║
║         │   "Summary unavailable" errors                   │ ║
║         └──────────────────────────────────────────────────┘ ║
║                              │                               ║
║  23:00  ┌─ Phase 2: Failure Triage ────────────────────────┐ ║
║         │ • Python script parses llama-cpp logs            │ ║
║         │ • Extracts: source text + failed output pairs    │ ║
║         │ • Classifies: hallucination | truncation |       │ ║
║         │   balance violation | schema error               │ ║
║         └──────────────────────────────────────────────────┘ ║
║                              │                               ║
║  23:30  ┌─ Phase 3: Teacher Evaluation ────────────────────┐ ║
║         │ • Package failures → Claude API                  │ ║
║         │ • Claude evaluates against FA¹-FA⁴ axioms        │ ║
║         │ • Generates <think> trace + <answer> JSON        │ ║
║         │ • Gate: only 100% schema-compliant corrections   │ ║
║         │   enter the training queue                       │ ║
║         └──────────────────────────────────────────────────┘ ║
║                              │                               ║
║  00:30  ┌─ Phase 4: Replay Buffer Assembly ────────────────┐ ║
║         │ • Apply SemDeDup (semantic deduplication)        │ ║
║         │ • Stratified sampling from Golden Dataset        │ ║
║         │   (SQLite, tagged by axis/archetype/tier)        │ ║
║         │ • Ratio: 25% new + 75% replay (bootstrap)       │ ║
║         │          50% new + 25% hist + 25% general (post) │ ║
║         │ • Output: training_batch.jsonl                   │ ║
║         └──────────────────────────────────────────────────┘ ║
║                              │                               ║
║  01:00  ┌─ Phase 5: Micro-LoRA SFT ───────────────────────┐ ║
║         │ • TERMINATE llama-cpp daemon (free VRAM)         │ ║
║         │ • Load Safetensors via Unsloth (17.5 GB)         │ ║
║         │ • SFT: 1-2 epochs, lr ≤ 5e-5, batch_size=1     │ ║
║         │ • Gradient accumulation: 4-8 steps               │ ║
║         │ • Early stopping gate: holdout validation set    │ ║
║         └──────────────────────────────────────────────────┘ ║
║                              │                               ║
║  02:30  ┌─ Phase 6: Export + Validation ───────────────────┐ ║
║         │ • Merge LoRA into base weights                   │ ║
║         │ • model.save_pretrained_gguf(                    │ ║
║         │     "sfs_model", tokenizer,                      │ ║
║         │     quantization_method="q4_k_m"                 │ ║
║         │   )                                              │ ║
║         │ • Validate: run holdout test suite against new   │ ║
║         │   GGUF — if accuracy < baseline, DISCARD         │ ║
║         └──────────────────────────────────────────────────┘ ║
║                              │                               ║
║  03:00  ┌─ Phase 7: Redeploy ─────────────────────────────┐ ║
║         │ • Swap GGUF binary on disk                       │ ║
║         │ • Restart llama-cpp inference daemon             │ ║
║         │ • Log cycle metrics to daemon_metrics.jsonl      │ ║
║         └──────────────────────────────────────────────────┘ ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 10. Known Blockers and Mitigations

| # | Blocker | Manifestation | Mitigation |
|---|---------|---------------|------------|
| B1 | **MSVC Compilation** | bitsandbytes/xformers fail to compile | Use pre-compiled .whl for Windows CUDA 13. If irreconcilable, isolate training in WSL2. |
| B2 | **MoE Mode Collapse** | Loss plateaus, generic/repetitive output | Verify router/gate layers are excluded from `target_modules`. |
| B3 | **Quantization Degradation** | Hallucination spikes after re-quantization | Never use intermediate FP16 dumps. Use Unsloth's native `save_pretrained_gguf()`. |
| B4 | **Teacher Style Overfitting** | Local model mimics Claude verbosity inside JSON | Apply SemDeDup. Filter Claude outputs for stylistic artifacts before assembly. |
| B5 | **Catastrophic Forgetting** | 100% JSON compliance but loses motif recognition | Increase replay buffer ratio. Lower LoRA LR. Ensure general reasoning data in every batch. |
| B6 | **DPO VRAM OOM** | Crash on reference model allocation | Abandon DPO. Use SFT. ORPO as last resort. |
| B7 | **GBNF Deadlocks** | Parser freezes on `<think>` → JSON transition | Permit flexible whitespace in grammar: `ws ::= [ \t\n]+` |
| B8 | **Token Truncation** | JSON cut off before closing `}` | Set `max_tokens ≥ 2048`. Grammar relies on model generating `}` + EOS. |
| B9 | **Schema Compilation** | Nested Pydantic schema → massive FSM | Pre-compile GBNF offline. Cache via `LlamaGrammar.from_string()`. |
| B10 | **Abliteration Healing** | Safety-aligned data in training set restores refusal | Exclude any safety-aligned datasets. Keep LR ≤ 5e-5, rank r ≤ 16. |

---

## 11. Distillation Tooling

| Component | Tool | Role |
|-----------|------|------|
| Data Generation | **Distilabel** (Argilla) | Claude-driven eval loops, LLM-as-a-Judge, SemDeDup |
| Training Execution | **Unsloth** (SFTTrainer) | QLoRA fine-tuning, GGUF export |
| Replay Storage | **SQLite** | Tagged by: domain axis, character archetype, NsfwTier |
| Schema Bridge | **Pydantic** | `model_json_schema()` for training + inference alignment |
| Inference | **llama-cpp-python** | GBNF constrained decoding |
| Prototyping | **distil-cli** (Distil Labs) | Quick iterations, Claude integration |

---

## 12. Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Schema compliance rate | 85% | > 98% | % of outputs passing Pydantic validation |
| Hallucination rate | ~10% | < 1% | % of outputs with fabricated references |
| "Summary unavailable" rate | ~5% | 0% | % of generation collapses |
| Egypto-Andean balance deviation | ±15% | ±5% | Mean absolute deviation from 50/50 |
| FA¹-FA⁴ axiom coverage | ~70% | > 95% | % of axioms correctly applied |
| Inference latency (post-SFT) | Baseline | ≤ Baseline | No regression from GBNF synergy |

---

## 13. Curriculum Design

```
Phase 1 — Foundational (Weeks 1-2)
├── NONE-tier texts with overt aesthetic markers
├── Clear Egyptian / Andean vocabulary
├── Simple schema: few motifs, single archetype
└── Goal: Baseline 50/50 balance + JSON structure

Phase 2 — Intermediate (Weeks 3-4)
├── SUGGESTIVE-tier texts
├── Cross-referential motif matching
├── Multiple archetypes per document
└── Goal: Reliable motif extraction + confidence scoring

Phase 3 — Advanced (Weeks 5-8)
├── EXPLICIT / EXTREME texts
├── Dense FA¹-FA⁴ MILFological interpolations
├── Body-as-architecture metaphor resolution
├── Ambiguous texts requiring LOW confidence flags
└── Goal: >98% schema compliance across all tiers

Phase 4 — Convergence (Ongoing)
├── Auto-throttle when compliance plateaus >98%
├── Shift to maintenance mode: weekly batches
└── Goal: Sustained accuracy with minimal compute
```

---

## 14. Cross-References

| Document | Relationship |
|----------|-------------|
| [KCP_PROTOCOL_ONTOLOGY.md](docs/standards/KCP_PROTOCOL_ONTOLOGY.md) | Metadata standard for all source files |
| [KCP_ARCHITECTURE_RATIFICATION.md](docs/standards/KCP_ARCHITECTURE_RATIFICATION.md) | Approach C irrevocability decision |
| Variant 1 | [claude/mailbox/Local_AI_Teaching_Framework_Research_Variant1of2.md](claude/mailbox/Local_AI_Teaching_Framework_Research_Variant1of2.md) |
| Variant 2 | [claude/mailbox/Local_AI_Teaching_Framework_Research_Variant2of2.md](claude/mailbox/Local_AI_Teaching_Framework_Research_Variant2of2.md) |

---

## 15. Variant Divergence Log

Where the two Gemini research variants disagree, this section records both
positions and the consolidation decision.

| Topic | Variant 1 | Variant 2 | Decision |
|-------|-----------|-----------|----------|
| **Replay buffer ratio** | 50% new / 25% hist / 25% general | 25% new / 75% golden replay | Start V2 conservative, shift to V1 post-90% compliance |
| **Windows vs WSL2** | Native Win11 viable with pre-compiled wheels | WSL2 recommended for Triton stability | WSL2 for training; native Windows for inference |
| **Dataset sizing** | 100-200 bootstrap → convergence at 500-1000 | 1000-3000 for >98% compliance | Use V1's aggressive bootstrap, V2's higher target for full convergence |
| **SID naming** | Not specified | Not specified | `TOOL_LAT_DAEMON_V1`, `TOOL_LAT_TRAINER_V1` (when scripts are created) |
| **OPLoRA / LaLoRA** | Not mentioned | Detailed coverage | Adopt as future regularization lane if replay buffer proves insufficient |

---

## Appendix A: Key References (Deduplicated)

| # | Source | Topic |
|---|--------|-------|
| 1 | [Unsloth — Qwen Docs](https://qwen.readthedocs.io/en/latest/training/unsloth.html) | QLoRA + MoE fine-tuning |
| 2 | [Unsloth Blog — Qwen3](https://unsloth.ai/blog/qwen3) | 17.5 GB VRAM, frozen router |
| 3 | [Unsloth — Faster MoE](https://unsloth.ai/docs/new/faster-moe) | 12× faster MoE training |
| 4 | [Qwen/Qwen3-30B-A3B — HF](https://huggingface.co/Qwen/Qwen3-30B-A3B) | Model card: 30.5B total, 3.3B active |
| 5 | [Unsloth — Saving to GGUF](https://unsloth.ai/docs/basics/inference-and-deployment/saving-to-gguf) | Forward conversion pipeline |
| 6 | [arXiv: Think Inside the JSON](https://arxiv.org/pdf/2502.14905) | SFT + constrained decoding synergy |
| 7 | [arXiv: OPLoRA](https://arxiv.org/html/2510.13003v2) | Orthogonal projection for forgetting |
| 8 | [arXiv: SafeMoE](https://arxiv.org/html/2509.22745v1) | Safety routing alignment for MoE |
| 9 | [arXiv: Scaling Laws for Forgetting](https://arxiv.org/html/2401.05605v1) | Power-law decay in fine-tuning |
| 10 | [Distilabel — Argilla](https://github.com/argilla-io/distilabel) | Synthetic data + AI feedback |
| 11 | [arXiv: Agentic Knowledge Distillation](https://arxiv.org/html/2602.10869v1) | Teacher-student SMS detection |
| 12 | [arXiv: ScrapeGraphAI-100k](https://arxiv.org/html/2602.15189v1) | Schema complexity + dataset sizing |
| 13 | [arXiv: Embarrassingly Simple Defense Against Abliteration](https://arxiv.org/html/2505.19056v2) | Abliteration stability risks |
| 14 | [Pydantic — LLM Intro](https://pydantic.dev/articles/llm-intro) | Schema bridge for structured output |
| 15 | [Unsloth — Windows Install](https://unsloth.ai/docs/get-started/install/windows-installation) | Native Windows + WSL2 paths |
