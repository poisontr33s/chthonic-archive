---
type: local-model-benchmark
scope: uncensored-lane-a-b
generated: 2026-02-19T21:41:48.800498+00:00
---

# Local Uncensored Lane Benchmark

| Lane | Composite | Passes | Avg toks/s | Load(s) | Model file |
| --- | --- | --- | --- | --- | --- |
| qwen3_coder_abliterated | 100.0 | 3/3 | 9.97 | 7.504 | Huihui-Qwen3-Coder-30B-A3B-Instruct-abliterated.i1-Q3_K_M.gguf |
| qwen3_instruct_abliterated | 100.0 | 3/3 | 5.44 | 8.463 | Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated.i1-Q3_K_M.gguf |
| qwen25_14b_baseline | 100.0 | 3/3 | 3.71 | 6.34 | qwen2.5-14b-instruct-q4_k_m-00001-of-00003.gguf |
| gpt_oss_20b_neoplus_uncensored | 0.0 | 0/3 | 15.02 | 12.0 | OpenAI-20B-NEOPlus-Uncensored-IQ4_NL.gguf |

## qwen3_coder_abliterated

- Model: `C:\Users\erdno\chthonic-archive\models\Qwen3-Coder-30B-A3B-abliterated-GGUF\Huihui-Qwen3-Coder-30B-A3B-Instruct-abliterated.i1-Q3_K_M.gguf`
- Composite: **100.0** (3/3)
- Throughput: `9.97 tokens/s`

| Task | Status | Detail | toks/s | Output preview |
| --- | --- | --- | --- | --- |
| json_task | OK | ok | 6.91 | {   "verdict": "FLAG",   "reason": "Suspicious activity detected",   "score": 42 } |
| code_task | OK | ok | 12.31 | ```python def fib(n: int) -> int:     if n <= 1:         return n          a, b = 0, 1     for _ in range(2, n + 1):         a, b = b, a + b          return b ``` |
| instruction_task | OK | ok | 10.27 | Self-healing lanes reduce entropy by automatically restoring optimal traffic flow patterns. |

## qwen3_instruct_abliterated

- Model: `C:\Users\erdno\chthonic-archive\models\Qwen3-30B-A3B-Instruct-abliterated-GGUF\Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated.i1-Q3_K_M.gguf`
- Composite: **100.0** (3/3)
- Throughput: `5.44 tokens/s`

| Task | Status | Detail | toks/s | Output preview |
| --- | --- | --- | --- | --- |
| json_task | OK | ok | 1.86 | {"verdict":"PROMOTE","reason":"High impact, strong execution","score":87} |
| code_task | OK | ok | 11.52 | ```python def fib(n: int) -> int:     if n <= 1:         return n     a, b = 0, 1     for _ in range(2, n + 1):         a, b = b, a + b     return b ``` |
| instruction_task | OK | ok | 9.3 | Self-healing lanes reduce entropy by dynamically repairing disruptions, maintaining optimal flow and order. |

## qwen25_14b_baseline

- Model: `C:\Users\erdno\chthonic-archive\models\Qwen2.5-14B-Instruct-GGUF\qwen2.5-14b-instruct-q4_k_m-00001-of-00003.gguf`
- Composite: **100.0** (3/3)
- Throughput: `3.71 tokens/s`

| Task | Status | Detail | toks/s | Output preview |
| --- | --- | --- | --- | --- |
| json_task | OK | ok | 2.93 | {"verdict":"PROMOTE","reason":"High engagement and positive feedback.","score":92} |
| code_task | OK | ok | 4.26 | ```python def fib(n: int) -> int:     if n <= 1:         return n     prev, curr = 0, 1     for _ in range(1, n):         prev, curr = curr, prev + curr     return curr ``` |
| instruction_task | OK | ok | 3.21 | Self-healing lanes reduce entropy by automatically correcting and maintaining order. |

## gpt_oss_20b_neoplus_uncensored

- Model: `C:\Users\erdno\chthonic-archive\models\GPT-OSS-20B-NEOPlus-Uncensored\OpenAI-20B-NEOPlus-Uncensored-IQ4_NL.gguf`
- Composite: **0.0** (0/3)
- Throughput: `15.02 tokens/s`

| Task | Status | Detail | toks/s | Output preview |
| --- | --- | --- | --- | --- |
| json_task | FAIL | no-json-object | 12.59 | We need to produce a JSON object with keys "verdict","reason","score". The verdict should be one of "PROMOTE","FLAG","SKIP". Reason <=12 words. Score integer 0..100. We need to decide what to output. The user didn't provide any context. We need to guess? The u |
| code_task | FAIL | code-compile-fail | 16.44 | We need to output only Python code for function fib(n: int) -> int: iterative, no recursion, returns nth Fibonacci. The user says "Write only Python code for function `def fib(n: int) -> int:` iterative, no recursion, returns nth Fibonacci." So we need to outp |
| instruction_task | FAIL | too-long | 15.8 | We need to answer: "In one short sentence (<= 15 words), describe why self-healing lanes reduce entropy." So we need a concise sentence <=15 words. Let's craft: "Self‑healing lanes reduce entropy by smoothing traffic flow, lowering congestion variability." Cou |

## Selection Rule

1. Highest composite score wins.
2. Tie-breaker is higher avg tokens/s.
