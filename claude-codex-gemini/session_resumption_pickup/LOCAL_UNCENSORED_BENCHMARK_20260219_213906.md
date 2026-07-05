---
type: local-model-benchmark
scope: uncensored-lane-a-b
generated: 2026-02-19T21:39:06.531238+00:00
---

# Local Uncensored Lane Benchmark

| Lane | Composite | Passes | Avg toks/s | Load(s) | Model file |
| --- | --- | --- | --- | --- | --- |
| qwen3_coder_abliterated | 100.0 | 3/3 | 13.5 | 6.711 | Huihui-Qwen3-Coder-30B-A3B-Instruct-abliterated.i1-Q3_K_M.gguf |
| qwen3_instruct_abliterated | 100.0 | 3/3 | 11.94 | 5.823 | Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated.i1-Q3_K_M.gguf |
| qwen25_14b_baseline | 100.0 | 3/3 | 4.09 | 6.219 | qwen2.5-14b-instruct-q4_k_m-00001-of-00003.gguf |
| gpt_oss_20b_neoplus_uncensored | 0.0 | 0/3 | 18.0 | 9.153 | OpenAI-20B-NEOPlus-Uncensored-IQ4_NL.gguf |

## qwen3_coder_abliterated

- Model: `C:\Users\eldno\chthonic-archive\models\Qwen3-Coder-30B-A3B-abliterated-GGUF\Huihui-Qwen3-Coder-30B-A3B-Instruct-abliterated.i1-Q3_K_M.gguf`
- Composite: **100.0** (3/3)
- Throughput: `13.5 tokens/s`

| Task | Status | Detail | toks/s | Output preview |
| --- | --- | --- | --- | --- |
| json_task | OK | ok | 9.22 | {   "verdict": "FLAG",   "reason": "Suspicious activity detected",   "score": 42 } |
| code_task | OK | ok | 17.6 | ```python def fib(n: int) -> int:     if n <= 1:         return n          a, b = 0, 1     for _ in range(2, n + 1):         a, b = b, a + b          return b ``` |
| instruction_task | OK | ok | 12.02 | Self-healing lanes reduce entropy by automatically restoring optimal traffic flow patterns. |

## qwen3_instruct_abliterated

- Model: `C:\Users\eldno\chthonic-archive\models\Qwen3-30B-A3B-Instruct-abliterated-GGUF\Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated.i1-Q3_K_M.gguf`
- Composite: **100.0** (3/3)
- Throughput: `11.94 tokens/s`

| Task | Status | Detail | toks/s | Output preview |
| --- | --- | --- | --- | --- |
| json_task | OK | ok | 6.4 | {"verdict":"PROMOTE","reason":"High impact, strong execution","score":87} |
| code_task | OK | ok | 16.48 | ```python def fib(n: int) -> int:     if n <= 1:         return n     a, b = 0, 1     for _ in range(2, n + 1):         a, b = b, a + b     return b ``` |
| instruction_task | OK | ok | 12.55 | Self-healing lanes reduce entropy by dynamically repairing disruptions, maintaining optimal flow and order. |

## qwen25_14b_baseline

- Model: `C:\Users\eldno\chthonic-archive\models\Qwen2.5-14B-Instruct-GGUF\qwen2.5-14b-instruct-q4_k_m-00001-of-00003.gguf`
- Composite: **100.0** (3/3)
- Throughput: `4.09 tokens/s`

| Task | Status | Detail | toks/s | Output preview |
| --- | --- | --- | --- | --- |
| json_task | OK | ok | 3.18 | {"verdict":"PROMOTE","reason":"High engagement and positive feedback.","score":92} |
| code_task | OK | ok | 4.7 | ```python def fib(n: int) -> int:     if n <= 1:         return n     prev, curr = 0, 1     for _ in range(1, n):         prev, curr = curr, prev + curr     return curr ``` |
| instruction_task | OK | ok | 3.59 | Self-healing lanes reduce entropy by automatically correcting and maintaining order. |

## gpt_oss_20b_neoplus_uncensored

- Model: `C:\Users\eldno\chthonic-archive\models\GPT-OSS-20B-NEOPlus-Uncensored\OpenAI-20B-NEOPlus-Uncensored-IQ4_NL.gguf`
- Composite: **0.0** (0/3)
- Throughput: `18.0 tokens/s`

| Task | Status | Detail | toks/s | Output preview |
| --- | --- | --- | --- | --- |
| json_task | FAIL | no-json-object | 15.06 | <\|channel\|>analysis<\|message\|>We need to produce a JSON object with keys "verdict","reason","score". The verdict should be one of "PROMOTE","FLAG","SKIP". Reason <=12 words. Score integer 0..100. We need to decide what to output. The user didn't provide any co |
| code_task | FAIL | code-compile-fail | 19.67 | <\|channel\|>analysis<\|message\|>We need to output only Python code for function fib(n: int) -> int: iterative, no recursion, returns nth Fibonacci. The user says "Write only Python code for function `def fib(n: int) -> int:` iterative, no recursion, returns nth  |
| instruction_task | FAIL | too-long | 19.12 | <\|channel\|>analysis<\|message\|>We need to answer: "In one short sentence (<= 15 words), describe why self-healing lanes reduce entropy." So we need a concise sentence <=15 words. Let's craft: "Self‑healing lanes reduce entropy by smoothing traffic flow, lowerin |

## Selection Rule

1. Highest composite score wins.
2. Tie-breaker is higher avg tokens/s.

