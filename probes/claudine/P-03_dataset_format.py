#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @SID: claudine-lora/P-03
# @PROBE: dataset_format
# @GATE: C-G3
# @DESC: Convert PsychoNoir-Kontrapunkt .md corpus to completion-style JSONL training data
#        Completion-style: raw text continuation (NOT instruction/response pairs)
#        Voice preservation — no template injection, no role formatting
#        Emits: manifest/claudine_train.jsonl + manifest/claudine_dataset_meta.json
# @RUN:  uv run probes/claudine/P-03_dataset_format.py [--min-chars 120] [--dry-run]
# @DEPS: none (reads corpus directly, not P-01/P-02 manifests)
# @MANIFEST: manifest/claudine_train.jsonl, manifest/claudine_dataset_meta.json

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

CORPUS_ROOT  = Path(r"C:\Users\eldno\PsychoNoir-Kontrapunkt")
MANIFEST_DIR = Path(r"C:\Users\eldno\chthonic-archive\manifest")
TRAIN_JSONL  = MANIFEST_DIR / "claudine_train.jsonl"
DS_META_JSON = MANIFEST_DIR / "claudine_dataset_meta.json"

# Sliding window parameters — match P-01 chunking
CHUNK_CHARS   = 1800
OVERLAP_CHARS = 200
MIN_CHARS     = 120   # discard chunks shorter than this (boilerplate headers etc.)

# Files to skip — low-signal noise
SKIP_PATTERNS = [
    "node_modules",
    ".git",
    "__pycache__",
    "package-lock.json",
    "yarn.lock",
]


def should_skip(path: Path) -> bool:
    parts = path.parts
    return any(pat in parts for pat in SKIP_PATTERNS)


def chunk_file(content: str, chunk: int = CHUNK_CHARS, overlap: int = OVERLAP_CHARS) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(content):
        end = min(start + chunk, len(content))
        chunk_text = content[start:end].strip()
        chunks.append(chunk_text)
        if end == len(content):
            break
        start += chunk - overlap
    return chunks


def collect_training_examples(corpus: Path, min_chars: int, dry_run: bool) -> list[dict]:
    md_files = sorted(corpus.rglob("*.md"))
    if dry_run:
        md_files = md_files[:20]

    examples: list[dict] = []
    for md in md_files:
        if should_skip(md):
            continue
        try:
            content = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if not content.strip():
            continue

        rel = str(md.relative_to(corpus))
        for chunk in chunk_file(content):
            if len(chunk) < min_chars:
                continue
            # Completion-style: the model learns to continue text in Claudine's voice
            # No instruction wrapper — raw text is the training signal
            examples.append({
                "text": chunk,
                "source": rel,
            })

    return examples


def write_jsonl(examples: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for ex in examples:
            # Training format for CLM: single "text" field
            # Compatible with HuggingFace datasets + PEFT SFTTrainer
            f.write(json.dumps({"text": ex["text"]}, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Claudine corpus dataset formatter P-03")
    parser.add_argument("--min-chars", type=int, default=MIN_CHARS)
    parser.add_argument("--dry-run", action="store_true", help="Process only first 20 files")
    args = parser.parse_args()

    t0 = time.time()
    print(f"[P-03] Collecting completion examples from {CORPUS_ROOT}")
    examples = collect_training_examples(CORPUS_ROOT, args.min_chars, args.dry_run)

    total_chars = sum(len(e["text"]) for e in examples)
    print(f"[P-03] {len(examples):,} examples  {total_chars/1e6:.1f}M chars")

    write_jsonl(examples, TRAIN_JSONL)
    print(f"[P-03] Wrote {TRAIN_JSONL}")

    meta = {
        "gate": "C-G3",
        "status": "admitted",
        "probe": "P-03_dataset_format",
        "dry_run": args.dry_run,
        "corpus_root": str(CORPUS_ROOT),
        "num_examples": len(examples),
        "total_chars": total_chars,
        "avg_chars": round(total_chars / len(examples)) if examples else 0,
        "min_chars_filter": args.min_chars,
        "format": "completion",
        "jsonl_path": str(TRAIN_JSONL),
        "elapsed_s": round(time.time() - t0, 2),
    }
    DS_META_JSON.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[P-03] GATE C-G3 → admitted")
    print(f"       examples={len(examples):,}  total={total_chars/1e6:.1f}M chars  → {TRAIN_JSONL}")


if __name__ == "__main__":
    main()
