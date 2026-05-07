# Research Digest: Optimum ONNX Migration

Date: 2026-05-06
Owner lane: Codex / toolchain stewardship
Status: Actionable. Direct `torch.onnx` export satisfies the ONNX/TRT invariant without Optimum.

## Findings

- The current repo lock is correct to keep `optimum[onnxruntime-gpu]>=1.23,<2` out of the default environment. Live `uv` resolution shows it pulls `optimum 1.27.0`, `transformers 4.53.3`, and `onnxruntime-gpu 1.25.1`, which conflicts with the active Transformers 5.x lane.
- The newer Hugging Face direction is `optimum-onnx`, not the old monolithic Optimum extra. The official Transformers production-export docs point ONNX export at Optimum ONNX, and the Optimum ONNX docs install with `optimum-onnx[onnxruntime]` or `optimum-onnx[onnxruntime-gpu]`.
- `optimum-onnx` is not green for this repo yet. Live resolution shows `optimum-onnx 0.1.0` depends on `transformers>=4.36,<4.58` and the resolved Transformers 4.57.x line still depends on `huggingface-hub<1.0`.
- Sentence Transformers now exposes the preferred embedding-level replacement: `SentenceTransformer(..., backend="onnx")` plus `export_optimized_onnx_model(...)`. Its current `onnx-gpu` extra still depends on `optimum-onnx`, so it inherits the same Transformers/HF Hub incompatibility today.
- Plain `onnxruntime-gpu` is not the collision. Export tooling is the collision. Runtime-only ONNX inference can stay conceptually separate from export tooling.
- Direct PyTorch export is green under the active repo lane. A live probe with `torch>=2.11`, `transformers>=5.4`, `huggingface-hub>=1.8`, `numpy>=2.4`, `onnx>=1.21`, `onnxscript>=0.6`, and `onnxruntime-gpu>=1.25` exported a tiny encoder model via `torch.onnx.export(dynamo=True)`.
- The direct exporter output loaded under ONNX Runtime and matched PyTorch output with max absolute drift around `7e-7` on the tested encoder. CUDA provider discovery succeeded, but this local shell fell back to CPU because `cublasLt64_12.dll` was missing from the runtime PATH. That is a CUDA runtime surface, not a resolver conflict.
- The runtime must filter tokenizer outputs to ONNX session input names. Some tokenizer families emit `token_type_ids`; the direct exporter intentionally exports only `input_ids` and `attention_mask`, so unfiltered `dict(enc)` can fail even when the ONNX file is valid.

## Decisions

| Decision | Options | Recommendation |
| --- | --- | --- |
| Keep Optimum in the root project? | Restore old extra, add dependency group, quarantine | Quarantine only. Root deps and sibling dependency groups still collide through base HF Hub / NumPy. |
| Replacement target | Legacy `optimum[onnxruntime-gpu]`, `optimum-onnx`, Sentence Transformers ONNX backend, direct `torch.onnx` | Use direct `torch.onnx.export(dynamo=True)` now; continue watching high-level exporters as optional future simplification. |
| Daily research signal | Watch package names manually, run a resolver probe, make a TODO | Keep the direct-export proof as the acceptance baseline; watch `optimum-onnx` / ST ONNX only for future cleanup, not as blockers. |

## Actionable Checklist

- [chthonic] Keep `pyproject.toml` default `embeddings` on `sentence-transformers>=5.3,<6`, `transformers>=5.4,<6`, and `huggingface-hub>=1.8,<2`.
- [chthonic] Add `onnx`, `onnxscript`, and `onnxruntime-gpu` to the default embeddings lane; these satisfy export/runtime without pulling Optimum.
- [codex] Preserve Optimum export experiments with `uv run --no-project --with "optimum[onnxruntime-gpu]>=1.23,<2" ...` when proving old behavior.
- [codex] Use this direct-export resolver probe as the daily green condition:

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

- [codex] Replace both `optimum.exporters.onnx.main_export` call sites in `probes/python/embedding_explorer.py` with a shared `torch.onnx.export(dynamo=True)` encoder export helper.
- [codex] Route ONNX/TRT inference through an input-filter helper so tokenizer extras do not violate the exported model input contract.
- [manual] Do not downgrade repo-wide HF Hub or Transformers just to satisfy ONNX export. That would trade one contained export problem for a whole-repo dependency rollback.

## Dependencies

| Package | Install vector | Current research state |
| --- | --- | --- |
| `optimum[onnxruntime-gpu]>=1.23,<2` | `uv run --no-project --with ...` | Resolves only as legacy isolate; pulls Transformers 4.53.x. |
| `optimum-onnx[onnxruntime-gpu]` | `uv run --no-project --with ...` | Resolves to `optimum-onnx 0.1.0`, `optimum 2.1.0`, `transformers 4.57.6`, `onnxruntime-gpu 1.25.1`; still incompatible with HF Hub 1.x. |
| `sentence-transformers[onnx-gpu]` | future project dependency candidate | Not compatible with Transformers 5.x yet because it depends on `optimum-onnx`. |
| `torch.onnx` + `onnxscript` + `onnxruntime-gpu` | project `embeddings` group | Compatible with the active repo lane; preserves ONNX Runtime + TRT pipeline without Optimum. |

## Contradictions

CONFLICT: Hugging Face docs describe Sentence Transformers ONNX and Optimum ONNX as the modern route, but the current package metadata still resolves that route through Transformers 4.x and HF Hub `<1.0`.

CONFLICT: Adding a separate uv dependency group sounds isolated, but uv still resolves project base dependencies with that group. Because root `huggingface-hub>=1.8` is part of the collision, this cannot be solved as a sibling group inside the current root project.

RESOLVED: The explorer does not require Optimum specifically. It requires a valid ONNX file whose first output is `last_hidden_state` so the existing tokenizer, pooling, normalization, ONNX Runtime, and TRT cache path remain invariant. Direct `torch.onnx` export satisfies that contract.

## Sources

- Hugging Face Transformers production export docs: https://huggingface.co/docs/transformers/main/serialization
- Hugging Face Optimum ONNX installation/docs: https://huggingface.co/docs/optimum-onnx/en/installation
- Hugging Face Optimum ONNX repository: https://github.com/huggingface/optimum-onnx
- Sentence Transformers efficiency docs: https://sbert.net/docs/sentence_transformer/usage/efficiency.html
- PyTorch torch.export-based ONNX exporter docs: https://docs.pytorch.org/docs/stable/onnx_export.html
