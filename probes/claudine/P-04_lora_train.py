#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @SID: claudine-lora/P-04
# @PROBE: lora_train
# @GATE: C-G4
# @DESC: LoRA adapter training on Mistral-7B-v0.3 using PsychoNoir-Kontrapunkt dataset
#        4-bit quantized base (bitsandbytes NF4) — runs on RTX 4090 (24GB VRAM)
#        Output adapter: adapters/claudine-v1/
# @RUN:  uv run probes/claudine/P-04_lora_train.py [--steps 2000] [--dry-run]
# @DEPS: C-G3 (manifest/claudine_train.jsonl must exist)
# @MANIFEST: manifest/claudine_train_run.json, adapters/claudine-v1/

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

MANIFEST_DIR = Path(r"C:\Users\eldno\chthonic-archive\manifest")
ADAPTER_DIR  = Path(r"C:\Users\eldno\chthonic-archive\adapters\claudine-v1")
TRAIN_JSONL  = MANIFEST_DIR / "claudine_train.jsonl"
RUN_META     = MANIFEST_DIR / "claudine_train_run.json"

BASE_MODEL   = "mistralai/Mistral-7B-v0.3"
MAX_SEQ_LEN  = 1024

# LoRA config — conservative for stability, adjust rank for more capacity
LORA_R       = 16
LORA_ALPHA   = 32
LORA_DROPOUT = 0.05
LORA_TARGETS = ["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]


def load_dataset(jsonl_path: Path, max_examples: int | None = None) -> list[str]:
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


def build_model_and_tokenizer(dry_run: bool):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    print(f"[P-04] Loading base model: {BASE_MODEL}")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=False,
    )
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=False)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    return model, tokenizer


def apply_lora(model):
    from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training

    model = prepare_model_for_kbit_training(model)
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        target_modules=LORA_TARGETS,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    return model


def make_hf_dataset(texts: list[str], tokenizer, max_seq_len: int):
    from datasets import Dataset  # type: ignore

    def tokenize(examples):
        out = tokenizer(
            examples["text"],
            truncation=True,
            max_length=max_seq_len,
            padding="max_length",
            return_tensors=None,
        )
        out["labels"] = out["input_ids"].copy()
        return out

    ds = Dataset.from_dict({"text": texts})
    return ds.map(tokenize, batched=True, remove_columns=["text"])


def train(model, tokenizer, dataset, steps: int, output_dir: Path) -> dict:
    import torch
    from transformers import DataCollatorForLanguageModeling, Trainer, TrainingArguments

    args = TrainingArguments(
        output_dir=str(output_dir / "checkpoints"),
        max_steps=steps,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,          # effective batch = 8
        warmup_steps=min(50, steps // 10),
        learning_rate=2e-4,
        fp16=False,
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        save_steps=min(500, steps),
        save_total_limit=2,
        optim="paged_adamw_8bit",
        lr_scheduler_type="cosine",
        report_to="none",
        remove_unused_columns=False,
        dataloader_num_workers=0,               # Windows: keep 0
    )

    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    trainer  = Trainer(
        model=model,
        args=args,
        train_dataset=dataset,
        data_collator=collator,
    )

    t0 = time.time()
    train_result = trainer.train()
    elapsed = time.time() - t0

    model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    print(f"[P-04] Adapter saved to {output_dir}")

    return {
        "steps": train_result.global_step,
        "train_loss": round(train_result.training_loss, 4),
        "elapsed_s": round(elapsed, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Claudine LoRA training probe P-04")
    parser.add_argument("--steps", type=int, default=2000, help="Max training steps (default 2000)")
    parser.add_argument("--dry-run", action="store_true", help="Run 5 steps on 200 examples only")
    args = parser.parse_args()

    if args.dry_run:
        args.steps = 5

    t_start = time.time()

    max_ex = 200 if args.dry_run else None
    texts  = load_dataset(TRAIN_JSONL, max_examples=max_ex)
    print(f"[P-04] Loaded {len(texts):,} training examples")

    model, tokenizer = build_model_and_tokenizer(args.dry_run)
    model            = apply_lora(model)
    dataset          = make_hf_dataset(texts, tokenizer, MAX_SEQ_LEN)
    print(f"[P-04] Dataset tokenized: {len(dataset):,} examples")

    ADAPTER_DIR.mkdir(parents=True, exist_ok=True)
    stats = train(model, tokenizer, dataset, args.steps, ADAPTER_DIR)

    meta = {
        "gate": "C-G4",
        "status": "admitted",
        "probe": "P-04_lora_train",
        "dry_run": args.dry_run,
        "base_model": BASE_MODEL,
        "adapter_dir": str(ADAPTER_DIR),
        "lora_r": LORA_R,
        "lora_alpha": LORA_ALPHA,
        "lora_targets": LORA_TARGETS,
        "max_seq_len": MAX_SEQ_LEN,
        "num_examples": len(texts),
        "elapsed_total_s": round(time.time() - t_start, 2),
        **stats,
    }
    RUN_META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[P-04] GATE C-G4 → admitted")
    print(f"       steps={stats['steps']}  loss={stats['train_loss']}  elapsed={stats['elapsed_s']}s")
    print(f"       adapter → {ADAPTER_DIR}")


if __name__ == "__main__":
    main()
