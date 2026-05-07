# Dependency Policy — chthonic-archive

> **Rule set:** "latest stable where compatible, never force a transitive past its parent's declared bound"

---

## Core Rules

### 1. Floor = current stable, ceiling = next major

```toml
"numpy>=2.4.3,<3"   # floor: what's verified working today
                     # ceiling: exclude the next breaking major
```

Never use `>=x.0` bare minimums — they allow the resolver to pick anything from years ago. Set the floor to a version you have actually tested.

### 2. Never pin a transitive past its parent's bound

If `pydantic 2.12.5` declares `pydantic-core==2.41.5`, do not force `pydantic-core>=2.44.0`. The transitive constraint is the parent's responsibility. If you need a newer transitive, upgrade the parent first and let it pull the transitive with it.

**Anti-pattern:**
```toml
"pydantic-core>=2.44.0"   # WRONG — forces past pydantic's own constraint
```

### 3. Optional ML/GPU lanes go in dependency-groups, not base deps

Heavy stacks (torch, transformers, sentence-transformers) are dependency-groups:
```toml
[dependency-groups]
embeddings = [
    "sentence-transformers>=5.3.0,<6",
    "transformers>=5.4.0,<6",
    "torch>=2.11.0,<3",
    "onnx>=1.21.0,<2",
    "onnxscript>=0.6.0,<1",
    "onnxruntime-gpu>=1.25.0,<2",
    # Do not add optimum[onnxruntime-gpu] here while Optimum caps transformers/HF Hub below this lane.
]

[tool.uv]
default-groups = ["dev", "analysis", "embeddings", "hf", "openai", "poe"]
```

All groups are in `default-groups` — plain `uv sync` installs the full environment. Never move heavy deps into `dependencies = [...]`.

`optimum[onnxruntime-gpu]` is also not safe as a sibling dependency group in this project.
Current Optimum 1.x resolves against the Transformers 4.x lane and also expects older
`huggingface-hub` / `numpy` ranges than the repo base dependencies. The equivalent
project-lock solution is `torch.onnx` export plus `onnxruntime-gpu` runtime, which
preserves the ONNX/TRT invariant without importing Optimum's resolver cascade.

### 4. Packages with version-sensitive transitive chains get exact major ceilings

```toml
"huggingface-hub>=1.8.0,<2"     # hf-hub has broken compat at majors before
"sentence-transformers>=5.3.0,<6"
"transformers>=5.4.0,<6"
```

Omitting the ceiling (`<6`) on packages with historically brittle cross-version behavior invites silent breakage at the next major.

### 5. Dev group tracks latest stable independently

Dev tools (`ruff`, `mypy`, `pytest`) do not need to be compatible with production deps — they run in the same venv but only at dev time. Keep them at current stable floors, no artificial ceilings unless there is a known breakage.

---

## Structure (as of 2026-04-15)

All lanes are `dependency-groups` (not `optional-dependencies`), all included in `tool.uv.default-groups`. A plain `uv sync` restores the full environment — no flags needed.

```
dependencies         → base toolchain (networkx, polars, rich, scikit-learn, hf-hub, numpy)
dependency-groups:
  dev                → pytest, ruff, mypy, llama-cpp-python, pip
  embeddings         → sentence-transformers, transformers, torch, onnx, onnxscript, onnxruntime-gpu
  hf                 → mcp, pydantic-settings, requests
  openai             → openai
  poe                → fastapi-poe
  analysis           → radon
```

---

## Refresh Process

When deps drift:

1. Check PyPI for new stable releases of direct deps
2. Raise the floor in `pyproject.toml` to current stable
3. `uv lock` — if it resolves cleanly, done
4. If a transitive conflict appears, diagnose which parent owns it before raising floors
5. Never use `uv pip install` to work around a lock conflict — fix the spec instead

---

## Known Constraints (current as of 2026-04-15)

| Package | Constraint | Reason |
|---------|-----------|--------|
| `huggingface-hub` | `>=1.8.0,<2` | Base dep; all HF tools align to this |
| `pydantic-core` | transitive of `pydantic 2.12.5` → `==2.41.5` | Do not force higher |
| `torch` | `>=2.11.0,<3` (embeddings extra only) | Floor = verified working install |
| `onnx` / `onnxscript` | `onnx>=1.21,<2`; `onnxscript>=0.6,<1` | Required by the torch.export-based ONNX exporter |
| `onnxruntime-gpu` | `>=1.25.0,<2` | Runtime for ONNX CUDA/TensorRT execution; does not cause the Optimum resolver conflict |
| `optimum[onnxruntime-gpu]` | **quarantined outside the project lock** | Current Optimum/optimum-onnx releases cap `transformers` below 5.x and collide with repo base `huggingface-hub` / `numpy`; use `uv --no-project` for isolated export probes |
| `fastembed` | **retired** — was a workaround for the old hf-hub conflict | Remove if still installed |

---

## Out-of-Band Installs

There are no project-venv out-of-band installs. If a package cannot be locked, fix the spec — do not `uv pip install` around it. The lockfile is the source of truth.

Compatibility probes may use `uv run --no-project --with ...` when the point is to prove
that an isolated legacy stack still resolves without mutating the repo lock or venv. This
is the current preservation lane for Optimum ONNX export experiments.

## ONNX Export Migration Watch

The replacement target is not the legacy `optimum[onnxruntime-gpu]` extra. The active
solution is direct `torch.onnx.export(..., dynamo=True)` over `AutoModel`, producing the
same `last_hidden_state` tensor consumed by the existing ONNX Runtime pooling path.
This satisfies the explorer invariant without waiting for `optimum-onnx` or
`sentence-transformers[onnx-gpu]` to catch up to Transformers 5.x / HF Hub 1.x.
Runtime calls must filter tokenizer outputs to the ONNX session input names; BERT-family
tokenizers may emit `token_type_ids` while the direct exporter currently owns only
`input_ids` and `attention_mask`.

Daily research should still watch upstream for a future higher-level exporter, but the
project-lock proof is now the direct exporter probe:

```powershell
uv run --no-project `
  --with "torch>=2.11,<3" `
  --with "transformers>=5.4,<6" `
  --with "huggingface-hub>=1.8,<2" `
  --with "numpy>=2.4,<3" `
  --with "onnx>=1.21,<2" `
  --with "onnxscript>=0.6,<1" `
  --with "onnxruntime-gpu>=1.25,<2" `
  python -c "import torch, transformers, onnxruntime; print('torch-onnx-compatible')"
```

Keep watching `sentence-transformers[onnx-gpu]` and `optimum-onnx` separately. When they
resolve against Transformers 5.x and HF Hub 1.x, they may become a cleaner high-level
export option, but they are no longer blockers for the current ONNX/TRT pipeline.
