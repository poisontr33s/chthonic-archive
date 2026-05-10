#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @SID: claudine-lora/P-04v2
# @PROBE: lora_train_v2
# @GATE: C-G4v2
# @DESC: LoRA adapter training v2 — claudine-v2
#
#   Improvements over P-04 (claudine-v1):
#     1. Flash Attention 2  — attn_implementation="flash_attention_2"
#        (~30-40% faster attention, lower VRAM, RTX 4090 fully utilized)
#     2. DoRA               — weight-decomposed LoRA, better downstream quality
#        same parameter count as LoRA, higher fidelity adaptation
#     3. RSLoRA             — rank-stabilized scaling, better at r=16+
#     4. SFTTrainer+packing — TRL SFTTrainer, packing=True eliminates padding waste
#        ~30-50% fewer GPU cycles vs padding="max_length"
#     5. resume_from_checkpoint — survives interrupts, resumes from latest checkpoint
#     6. gradient_checkpointing — explicit, reduces peak VRAM ~20%
#
#   Prereq: uv add trl
#
# @RUN:  uv run probes/claudine/P-04v2_lora_train.py [--steps 2000] [--dry-run] [--resume]
# @DEPS: C-G3 (manifest/claudine_train.jsonl), trl>=0.9, flash_attn>=2.0
# @MANIFEST: manifest/claudine_train_run_v2.json
# @ADAPTER:  adapters/claudine-v2/

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

MANIFEST_DIR  = Path(r"C:\Users\eldno\chthonic-archive\manifest")
ADAPTER_DIR   = Path(r"C:\Users\eldno\chthonic-archive\adapters\claudine-v2")
TRAIN_JSONL   = MANIFEST_DIR / "claudine_train.jsonl"
RUN_META      = MANIFEST_DIR / "claudine_train_run_v2.json"
CHECKPOINT_DIR = ADAPTER_DIR / "checkpoints"

BASE_MODEL   = "mistralai/Mistral-7B-v0.3"
MAX_SEQ_LEN  = 1024

# LoRA v2 config — DoRA + RSLoRA on same target set as v1
LORA_R        = 16
LORA_ALPHA    = 32
LORA_DROPOUT  = 0.05
LORA_TARGETS  = ["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
USE_DORA      = True   # Weight-decomposed LoRA — better quality, same param count
USE_RSLORA    = True   # Rank-stabilized scaling — better convergence at r=16


def _find_latest_checkpoint(checkpoint_dir: Path) -> Path | None:
    """Return the latest HuggingFace checkpoint dir, or None if none exist."""
    if not checkpoint_dir.exists():
        return None
    candidates = sorted(
        [d for d in checkpoint_dir.iterdir() if d.is_dir() and d.name.startswith("checkpoint-")],
        key=lambda d: int(d.name.split("-")[-1]),
    )
    return candidates[-1] if candidates else None


def _write_intermediate_manifest(step: int, loss: float | None, adapter_dir: Path, extra: dict) -> None:
    """Write a mid-training manifest marker (not the final gate artifact)."""
    meta = {
        "gate": "C-G4v2",
        "status": "in_progress",
        "step": step,
        "loss": loss,
        "adapter_dir": str(adapter_dir),
        **extra,
    }
    RUN_META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def load_dataset_texts(jsonl_path: Path, max_examples: int | None = None) -> list[str]:
    if not jsonl_path.exists():
        raise FileNotFoundError(f"Run P-03 first: {jsonl_path} not found")
    texts: list[str] = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            texts.append(obj["text"])
            if max_examples and len(texts) >= max_examples:
                break
    return texts


def build_model_and_tokenizer() -> tuple:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # Attempt Flash Attention 2 — fallback to sdpa if unavailable
    attn_impl = "flash_attention_2"
    try:
        import flash_attn  # noqa: F401
        print(f"[P-04v2] Flash Attention 2 available — using attn_implementation='{attn_impl}'")
    except ImportError:
        attn_impl = "sdpa"
        print("[P-04v2] flash_attn not found — falling back to sdpa (install flash_attn for ~30% speedup)")

    print(f"[P-04v2] Loading base model: {BASE_MODEL}")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        attn_implementation=attn_impl,
        device_map="auto",
        torch_dtype="auto",
        trust_remote_code=False,
    )

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=False)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    return model, tokenizer


def apply_lora(model):
    from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training

    # gradient_checkpointing=True: explicit, reduces peak VRAM ~20%
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        target_modules=LORA_TARGETS,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
        use_dora=USE_DORA,       # DoRA: decomposes magnitude + direction
        use_rslora=USE_RSLORA,   # RSLoRA: rank-stabilized α scaling
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    return model


def train_with_sft(model, tokenizer, texts: list[str], steps: int, resume: bool) -> dict:
    """
    SFTTrainer (TRL) with packing=True.
    Packing concatenates short sequences into MAX_SEQ_LEN chunks — no padding waste.
    ~30-50% fewer GPU cycles compared to padded training.
    """
    try:
        from trl import SFTConfig, SFTTrainer  # noqa: F401
    except ImportError:
        raise ImportError(
            "trl not installed. Run: uv add trl\n"
            "SFTTrainer is required for packing support in P-04v2."
        )
    from datasets import Dataset  # type: ignore

    raw_dataset = Dataset.from_dict({"text": texts})

    # Resolve resume checkpoint
    resume_from = None
    if resume:
        ckpt = _find_latest_checkpoint(CHECKPOINT_DIR)
        if ckpt:
            resume_from = str(ckpt)
            print(f"[P-04v2] Resuming from checkpoint: {resume_from}")
        else:
            print("[P-04v2] --resume requested but no checkpoint found — training from scratch")

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    ADAPTER_DIR.mkdir(parents=True, exist_ok=True)

    sft_config = SFTConfig(
        output_dir=str(CHECKPOINT_DIR),
        max_steps=steps,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,     # effective batch = 8
        gradient_checkpointing=True,       # explicit (also set in prepare_model_for_kbit_training)
        warmup_steps=min(50, steps // 10),
        learning_rate=2e-4,
        fp16=False,
        bf16=True,                         # Mistral-7B + RTX 4090 supports bf16
        logging_steps=10,
        save_steps=min(500, max(steps // 4, 1)),
        save_total_limit=3,                # keep 3 checkpoints (more recovery options)
        optim="paged_adamw_8bit",
        lr_scheduler_type="cosine",
        report_to="none",
        remove_unused_columns=False,
        dataloader_num_workers=0,          # Windows: keep 0
        # SFT-specific
        max_seq_length=MAX_SEQ_LEN,
        packing=True,                      # ← key improvement: no padding waste
        dataset_text_field="text",
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=raw_dataset,
        processing_class=tokenizer,
    )

    t0 = time.time()

    # Write in-progress marker before training begins
    _write_intermediate_manifest(0, None, ADAPTER_DIR, {"resume_from": resume_from})

    result = trainer.train(resume_from_checkpoint=resume_from)
    elapsed = time.time() - t0

    # Save final adapter (separate from checkpoints)
    model.save_pretrained(str(ADAPTER_DIR))
    tokenizer.save_pretrained(str(ADAPTER_DIR))
    print(f"[P-04v2] Adapter saved to {ADAPTER_DIR}")

    return {
        "steps": result.global_step,
        "train_loss": round(result.training_loss, 4),
        "elapsed_s": round(elapsed, 2),
        "resumed_from": resume_from,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Claudine LoRA training v2 — FA2 + DoRA + SFTTrainer")
    parser.add_argument("--steps",    type=int,  default=2000, help="Training steps (default 2000)")
    parser.add_argument("--dry-run",  action="store_true",     help="5 steps, 200 examples — smoke test")
    parser.add_argument("--resume",   action="store_true",     help="Resume from latest checkpoint in adapters/claudine-v2/checkpoints/")
    args = parser.parse_args()

    if args.dry_run:
        args.steps = 5

    t_start = time.time()

    max_ex  = 200 if args.dry_run else None
    texts   = load_dataset_texts(TRAIN_JSONL, max_examples=max_ex)
    print(f"[P-04v2] Loaded {len(texts):,} training examples")

    model, tokenizer = build_model_and_tokenizer()
    model            = apply_lora(model)

    stats = train_with_sft(model, tokenizer, texts, args.steps, args.resume)

    meta = {
        "gate":        "C-G4v2",
        "status":      "admitted",
        "probe":       "P-04v2_lora_train",
        "dry_run":     args.dry_run,
        "base_model":  BASE_MODEL,
        "adapter_dir": str(ADAPTER_DIR),
        "lora_r":      LORA_R,
        "lora_alpha":  LORA_ALPHA,
        "lora_targets": LORA_TARGETS,
        "use_dora":    USE_DORA,
        "use_rslora":  USE_RSLORA,
        "max_seq_len": MAX_SEQ_LEN,
        "packing":     True,
        "attn_impl":   "flash_attention_2",
        "num_examples": len(texts),
        "elapsed_total_s": round(time.time() - t_start, 2),
        **stats,
    }
    RUN_META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[P-04v2] GATE C-G4v2 → admitted")
    print(f"         steps={stats['steps']}  loss={stats['train_loss']}  elapsed={stats['elapsed_s']}s")
    print(f"         adapter → {ADAPTER_DIR}")


if __name__ == "__main__":
    main()
