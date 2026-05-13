#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: claudine_retrieval.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🏰 THE FORTRESS
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
mas_mcp/claudine_retrieval.py — Claudine LoRA Completion MCP Tool.

Standalone FastMCP server exposing the Claudine LoRA adapter
(Mistral-7B-v0.3 + adapters/claudine-v1/) as a completion tool.

Gate dependency: C-G4 must be admitted before this tool returns
model completions. Returns adapter_status metadata until then.

Usage:
    uv run mas_mcp/claudine_retrieval.py          # stdio MCP server
    uv run mas_mcp/claudine_retrieval.py --probe  # status check only

@SID:           CLAUDINE_RETRIEVAL_MCP_V1
@Shabti:        CLI Script
@Purpose:       mas_mcp/claudine_retrieval.py — Claudine LoRA Completion MCP Tool.
"""

# @SID: CLAUDINE_RETRIEVAL_MCP_V1
# Run from repo root: uv run mas_mcp/claudine_retrieval.py
# Requires: peft, transformers, torch, bitsandbytes (root .venv)

import json
import sys
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("claudine-retrieval")

REPO_ROOT = Path(__file__).parent.parent
ADAPTER_PATH = REPO_ROOT / "adapters" / "claudine-v1"
MANIFEST_PATH = REPO_ROOT / "manifest" / "claudine_train_run.json"
BASE_MODEL_ID = "mistralai/Mistral-7B-v0.3"

# ── Lazy state (module-level singleton after first load) ──────────────────────
_model = None
_tokenizer = None
_model_loaded = False
_load_error: Optional[str] = None


def _adapter_available() -> bool:
    """Check if the trained adapter exists and is not a dry-run artifact."""
    if not ADAPTER_PATH.exists():
        return False
    if MANIFEST_PATH.exists():
        try:
            run = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            if run.get("dry_run", False):
                return False
            if run.get("status") not in ("completed", "admitted"):
                return False
        except Exception:
            pass
    # Check for adapter_config.json (minimal adapter completeness check)
    return (ADAPTER_PATH / "adapter_config.json").exists()


def _load_model():
    """Lazy-load the LoRA-adapted model into VRAM (NF4, 4-bit)."""
    global _model, _tokenizer, _model_loaded, _load_error
    if _model_loaded:
        return
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        from peft import PeftModel

        logger.info("Loading base model %s in 4-bit NF4...", BASE_MODEL_ID)
        bnb_cfg = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        _tokenizer = AutoTokenizer.from_pretrained(
            str(ADAPTER_PATH),
            trust_remote_code=True,
        )
        if _tokenizer.pad_token is None:
            _tokenizer.pad_token = _tokenizer.eos_token

        base = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_ID,
            quantization_config=bnb_cfg,
            device_map="auto",
            trust_remote_code=True,
        )
        _model = PeftModel.from_pretrained(base, str(ADAPTER_PATH))
        _model.eval()
        _model_loaded = True
        logger.info("Claudine adapter loaded — ready for completions.")
    except Exception as exc:
        _load_error = str(exc)
        logger.error("Failed to load Claudine adapter: %s", _load_error)


def claudine_complete(prompt: str, max_new_tokens: int = 256, temperature: float = 0.7) -> dict:
    """
    Generate a completion using the Claudine LoRA adapter.

    Returns dict with keys:
        status: "completed" | "adapter_not_ready" | "error"
        text:   generated continuation (if status=="completed")
        prompt: echo of input prompt
        adapter_path: str path
        message: human-readable status (if not completed)
    """
    if not _adapter_available():
        train_run = {}
        if MANIFEST_PATH.exists():
            try:
                train_run = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "status": "adapter_not_ready",
            "message": (
                "C-G4 not yet admitted. Training in progress or not yet started. "
                f"Check manifest/claudine_train_run.json for current state."
            ),
            "adapter_path": str(ADAPTER_PATH),
            "train_run_status": train_run.get("status", "unknown"),
            "train_run_steps": train_run.get("steps"),
            "train_run_dry_run": train_run.get("dry_run"),
        }

    _load_model()

    if _load_error:
        return {
            "status": "error",
            "message": f"Model load failed: {_load_error}",
            "adapter_path": str(ADAPTER_PATH),
        }

    try:
        import torch

        inputs = _tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1024,
        ).to(_model.device)

        with torch.no_grad():
            out = _model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=_tokenizer.eos_token_id,
                eos_token_id=_tokenizer.eos_token_id,
            )

        new_tokens = out[0][inputs["input_ids"].shape[1]:]
        continuation = _tokenizer.decode(new_tokens, skip_special_tokens=True)

        return {
            "status": "completed",
            "prompt": prompt,
            "text": continuation,
            "adapter_path": str(ADAPTER_PATH),
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "adapter_path": str(ADAPTER_PATH),
        }


def claudine_status() -> dict:
    """Return current adapter and gate status without loading the model."""
    adapter_ready = _adapter_available()
    train_run = {}
    if MANIFEST_PATH.exists():
        try:
            train_run = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    return {
        "adapter_path": str(ADAPTER_PATH),
        "adapter_ready": adapter_ready,
        "model_loaded_in_session": _model_loaded,
        "train_run": {
            "status": train_run.get("status"),
            "steps": train_run.get("steps"),
            "final_loss": train_run.get("final_loss"),
            "elapsed_s": train_run.get("elapsed_s"),
            "dry_run": train_run.get("dry_run"),
        } if train_run else None,
        "gate": "C-G4",
        "gate_status": "admitted" if (
            adapter_ready
            and train_run.get("status") in ("completed", "admitted")
            and not train_run.get("dry_run")
        ) else "not_admitted",
    }


# ── FastMCP server entrypoint ─────────────────────────────────────────────────

def _make_mcp_server():
    from fastmcp import FastMCP  # type: ignore

    mcp = FastMCP(
        "claudine-retrieval",
        instructions=(
            "Claudine LoRA adapter — completion tool over Mistral-7B-v0.3 "
            "fine-tuned on the PsychoNoir-Kontrapunkt corpus. "
            "Use claudine_status() to check adapter readiness before calling claudine_complete()."
        ),
    )

    @mcp.tool()
    def claudine_complete_tool(
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
    ) -> dict:
        """
        Generate a continuation from the Claudine LoRA-adapted Mistral-7B-v0.3.
        Returns status='adapter_not_ready' if C-G4 training is not yet complete.
        """
        return claudine_complete(prompt, max_new_tokens, temperature)

    @mcp.tool()
    def claudine_adapter_status() -> dict:
        """
        Check Claudine adapter and gate C-G4 status without loading the model.
        Returns adapter_ready, gate_status, and training run metadata.
        """
        return claudine_status()

    return mcp


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if "--probe" in sys.argv:
        # Status-only probe — no model load, no MCP server
        status = claudine_status()
        print(json.dumps(status, indent=2))
        sys.exit(0 if status["gate_status"] == "admitted" else 1)

    mcp = _make_mcp_server()
    mcp.run()
