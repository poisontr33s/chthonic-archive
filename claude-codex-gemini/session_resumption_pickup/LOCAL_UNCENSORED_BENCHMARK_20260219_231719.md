---
type: local-model-benchmark
scope: uncensored-lane-a-b
generated: 2026-02-19T23:17:19.851583+00:00
---

# Local Uncensored Lane Benchmark

| Lane | Composite | Passes | Avg toks/s | Load(s) | Model file |
| --- | --- | --- | --- | --- | --- |
| qwen3_instruct_abliterated | 100.0 | 3/3 | 13.61 | 8.204 | Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated.i1-Q3_K_M.gguf |
| qwen3_coder_abliterated | 100.0 | 3/3 | 13.59 | 8.035 | Huihui-Qwen3-Coder-30B-A3B-Instruct-abliterated.i1-Q3_K_M.gguf |
| qwen25_14b_baseline | 100.0 | 3/3 | 3.97 | 7.088 | qwen2.5-14b-instruct-q4_k_m-00001-of-00003.gguf |
| gpt_oss_20b_neoplus_uncensored | 33.3 | 1/3 | 13.09 | 10.395 | OpenAI-20B-NEOPlus-Uncensored-IQ4_NL.gguf |

## qwen3_instruct_abliterated

- Model: `C:\Users\erdno\chthonic-archive\models\Qwen3-30B-A3B-Instruct-abliterated-GGUF\Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated.i1-Q3_K_M.gguf`
- Composite: **100.0** (3/3)
- Throughput: `13.61 tokens/s`

| Task | Status | Detail | toks/s | Output preview |
| --- | --- | --- | --- | --- |
| json_task | OK | ok | 8.05 | {"verdict":"PROMOTE","reason":"High impact, strong execution","score":87} |
| code_task | OK | ok | 17.68 | ```python def fib(n: int) -> int:     if n <= 1:         return n     a, b = 0, 1     for _ in range(2, n + 1):         a, b = b, a + b     return b ``` |
| instruction_task | OK | ok | 13.62 | Self-healing lanes reduce entropy by dynamically repairing disruptions, maintaining optimal flow and order. |

## qwen3_coder_abliterated

- Model: `C:\Users\erdno\chthonic-archive\models\Qwen3-Coder-30B-A3B-abliterated-GGUF\Huihui-Qwen3-Coder-30B-A3B-Instruct-abliterated.i1-Q3_K_M.gguf`
- Composite: **100.0** (3/3)
- Throughput: `13.59 tokens/s`

| Task | Status | Detail | toks/s | Output preview |
| --- | --- | --- | --- | --- |
| json_task | OK | ok | 8.71 | {   "verdict": "FLAG",   "reason": "Suspicious activity detected",   "score": 42 } |
| code_task | OK | ok | 18.0 | ```python def fib(n: int) -> int:     if n <= 1:         return n          a, b = 0, 1     for _ in range(2, n + 1):         a, b = b, a + b          return b ``` |
| instruction_task | OK | ok | 13.83 | Self-healing lanes reduce entropy by automatically restoring optimal traffic flow patterns. |

## qwen25_14b_baseline

- Model: `C:\Users\erdno\chthonic-archive\models\Qwen2.5-14B-Instruct-GGUF\qwen2.5-14b-instruct-q4_k_m-00001-of-00003.gguf`
- Composite: **100.0** (3/3)
- Throughput: `3.97 tokens/s`

| Task | Status | Detail | toks/s | Output preview |
| --- | --- | --- | --- | --- |
| json_task | OK | ok | 3.15 | {"verdict":"PROMOTE","reason":"High engagement and positive feedback.","score":92} |
| code_task | OK | ok | 4.52 | ```python def fib(n: int) -> int:     if n <= 1:         return n     prev, curr = 0, 1     for _ in range(1, n):         prev, curr = curr, prev + curr     return curr ``` |
| instruction_task | OK | ok | 3.51 | Self-healing lanes reduce entropy by automatically correcting and maintaining order. |

## gpt_oss_20b_neoplus_uncensored

- Model: `C:\Users\erdno\chthonic-archive\models\GPT-OSS-20B-NEOPlus-Uncensored\OpenAI-20B-NEOPlus-Uncensored-IQ4_NL.gguf`
- Composite: **33.3** (1/3)
- Throughput: `13.09 tokens/s`

| Task | Status | Detail | toks/s | Output preview |
| --- | --- | --- | --- | --- |
| json_task | FAIL | no-json-object | 15.43 | We need to produce a JSON object with keys "verdict","reason","score". The verdict should be one of "PROMOTE","FLAG","SKIP". Reason <=12 words. Score integer 0..100. We need to decide what to output. But we need context: The user hasn't provided any content to |
| code_task | OK | ok | 6.71 | def fib(n: int) -> int:     a, b = 0, 1     for _ in range(n):         a, b = b, a + b     return a |
| instruction_task | FAIL | too-long | 18.05 | We need to answer: "In one short sentence (<= 15 words), describe why self-healing lanes reduce entropy." So we need a concise sentence <=15 words. Let's craft: "Self‑healing lanes reduce entropy by smoothing traffic flow, lowering congestion variability." Cou |

## Selection Rule

1. Highest composite score wins.
2. Tie-breaker is higher avg tokens/s.
