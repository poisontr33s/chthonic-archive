---
type: local-delegation-benchmark
generated: 2026-04-15T06:11:28.233644+00:00
---

# Local Delegation Benchmark

| Lane | Composite | Passes | Avg toks/s | Load(s) | Model file |
| --- | --- | --- | --- | --- | --- |
| qwen25_14b_baseline | 100.0 | 5/5 | 4.32 | 4.702 | qwen2.5-14b-instruct-q4_k_m-00001-of-00003.gguf |

## qwen25_14b_baseline

- Composite: **100.0** (5/5)
- Throughput: `4.32 tokens/s`

| Task | Status | Detail | toks/s | Output preview |
| --- | --- | --- | --- | --- |
| schema_task | OK | ok | 3.89 | {   "verdict": "HOLD",   "confidence": 85,   "reason": "Insufficient data for promotion" } |
| plan_task | OK | ok | 4.73 | {"steps":[{"id":"S1","action":"Reduce model size","why":"To fit within the VRAM capacity"},{"id":"S2","action":"Use 8-bit floating point precision","why":"To further reduce the model size while maintaining acceptable performance"},{"id":"S3","action":"Implemen |
| tool_task | OK | ok | 4.03 | {"tool_calls":[{"name":"benchmark_candidate","arguments":{"model":"Gemma 4","runtime":"vllm","reason":"Initial benchmark on a 4090 GPU"}}]} |
| synthesis_task | OK | ok | 2.66 | {"winner":"B","evidence_ids":["E2","E4"]} |
| revision_task | OK | ok | 4.42 | {   "final_answer": "vLLM lists Gemma 4 31B BF16 at 1x80 GB, while NVFP4 is the plausible 24 GB route.",   "superseded_claim": "BF16 is feasible on a single 4090." } |
