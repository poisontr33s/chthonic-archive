---
type: uncensored-lane-runtime
generated: 2026-02-19T23:17:21.292098+00:00
---

# Uncensored Lane Runtime Manifest

- Default lane: `strict_json`
- Default model: `Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated.i1-Q3_K_M.gguf`
- Base URL: `http://127.0.0.1:8000/v1`

## Lane Routing

| Role | Lane | Model | Exists | Quant | Composite | toks/s |
| --- | --- | --- | --- | --- | ---: | ---: |
| strict_json | qwen3_instruct_abliterated | Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated.i1-Q3_K_M.gguf | Y | Q3_K_M | 100.0 | 13.61 |
| code | qwen3_coder_abliterated | Huihui-Qwen3-Coder-30B-A3B-Instruct-abliterated.i1-Q3_K_M.gguf | Y | Q3_K_M | 100.0 | 13.59 |
| unrestricted | qwen3_instruct_abliterated | Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated.i1-Q3_K_M.gguf | Y | Q3_K_M | 100.0 | 13.61 |

## Launch Commands

- strict JSON: `pwsh -NoProfile -File scripts/serve_uncensored_lane.ps1 -Lane strict_json`
- code: `pwsh -NoProfile -File scripts/serve_uncensored_lane.ps1 -Lane code`
- unrestricted: `pwsh -NoProfile -File scripts/serve_uncensored_lane.ps1 -Lane unrestricted`
