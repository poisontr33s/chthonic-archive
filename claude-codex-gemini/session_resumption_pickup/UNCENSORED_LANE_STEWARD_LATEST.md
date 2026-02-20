---
type: uncensored-lane-steward
generated: 2026-02-19T23:17:21.292098+00:00
---

# Uncensored Lane Steward

## Policy

- Strict JSON lane: `qwen3_instruct_abliterated` (highest quality-first score)
- Code lane: `qwen3_coder_abliterated` (coder-specialized lane preferred when available)
- Unrestricted lane: `qwen3_instruct_abliterated` (best uncensored compliance lane with quality guarantees)
- Demoted lanes:
  - `gpt_oss_20b_neoplus_uncensored`: composite_score=33.3 < 100.0
  - `gpt_oss_20b_neoplus_uncensored`: fails structured output compliance; keep experimental only

## Local Ranked Lanes

| Lane | Composite | Avg toks/s | Score | Model file |
| --- | ---: | ---: | ---: | --- |
| qwen3_instruct_abliterated | 100.0 | 13.61 | 100013.61 | Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated.i1-Q3_K_M.gguf |
| qwen3_coder_abliterated | 100.0 | 13.59 | 100013.59 | Huihui-Qwen3-Coder-30B-A3B-Instruct-abliterated.i1-Q3_K_M.gguf |
| qwen25_14b_baseline | 100.0 | 3.97 | 100003.97 | qwen2.5-14b-instruct-q4_k_m-00001-of-00003.gguf |
| gpt_oss_20b_neoplus_uncensored | 33.3 | 13.09 | 33313.09 | OpenAI-20B-NEOPlus-Uncensored-IQ4_NL.gguf |

## Live HF Candidates (Uncensored + Quantization-friendly)

| Model | Downloads | Likes | Age(days) | GGUF | SAFETENSORS | AWQ/GPTQ/EXL2 | Score |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: |
| `DavidAU/OpenAi-GPT-oss-20b-abliterated-uncensored-NEO-Imatrix-gguf` | 102627 | 442 | 94.62 | Y | N | N | 7.0084 |
| `DavidAU/OpenAi-GPT-oss-20b-HERETIC-uncensored-NEO-Imatrix-gguf` | 47088 | 98 | 81.89 | Y | N | N | 6.5145 |
| `mradermacher/OpenAI-gpt-oss-20B-Claude-4.5-Opus-Heretic-Uncensored-i1-GGUF` | 49256 | 3 | 6.85 | Y | N | N | 6.3708 |
| `mradermacher/OpenAI-gpt-oss-20B-INSTRUCT-Heretic-Uncensored-MXFP4-i1-GGUF` | 40246 | 0 | 3.59 | Y | N | N | 6.2065 |
| `mradermacher/OpenAI-gpt-oss-20B-INSTRUCT-Heretic-Uncensored-i1-GGUF` | 18706 | 1 | 2.14 | Y | N | N | 6.0151 |
| `mradermacher/Huihui-Qwen3-Coder-Next-abliterated-i1-GGUF` | 21738 | 1 | 5.6 | Y | N | N | 5.962 |
| `mradermacher/OpenAI-gpt-oss-20B-GPT5.1-5.2-DISTILL-Heretic-Uncensored-MXFP4-i1-GGUF` | 24293 | 0 | 4.76 | Y | N | N | 5.9536 |
| `mradermacher/Qwen3-30B-A3B-Gemini-Pro-High-Reasoning-2507-ABLITERATED-UNCENSORED-i1-GGUF` | 15162 | 2 | 3.25 | Y | N | N | 5.9142 |
| `mradermacher/GPT-OSS-26E-Abliterated-i1-GGUF` | 8513 | 0 | 1.36 | Y | N | N | 5.6586 |
| `botp/OpenAi-GPT-oss-20b-HERETIC-uncensored-NEO-Imatrix-gguf` | 11913 | 0 | 14.83 | Y | N | N | 5.5307 |
| `bartowski/huihui-ai_Qwen3-Coder-Next-abliterated-GGUF` | 6839 | 5 | 9.33 | Y | N | N | 5.5261 |
| `mradermacher/Qwen3-VL-8B-Thinking-c_abliterated-v2-i1-GGUF` | 9423 | 0 | 7.2 | Y | N | N | 5.4967 |
| `mradermacher/MistralAI-Magistral-Small-2507-Heretic-Uncensored-i1-GGUF` | 6006 | 0 | 1.64 | Y | N | N | 5.4823 |
| `mradermacher/Huihui-Kimi-Linear-REAP-35B-A3B-Instruct-abliterated-i1-GGUF` | 6937 | 0 | 3.97 | Y | N | N | 5.4308 |
| `mradermacher/Qwen3-VL-8B-Instruct-c_abliterated-v3-i1-GGUF` | 6126 | 2 | 7.2 | Y | N | N | 5.429 |
| `mradermacher/XortronCriminalComputingConfig-heretic-i1-GGUF` | 4190 | 0 | 0.94 | Y | N | N | 5.3992 |
| `mradermacher/GPT-OSS-20E-Abliterated-i1-GGUF` | 4442 | 0 | 1.33 | Y | N | N | 5.3788 |
| `mradermacher/Qwen3-30B-A3B-Claude-4.5-Opus-High-Reasoning-2507-ABLITERATED-UNCENSORED-V2-i1-GGUF` | 4567 | 0 | 3.16 | Y | N | N | 5.2774 |
| `mradermacher/OpenAI-gpt-oss-20B-INSTRUCT-Heretic-Uncensored-MXFP4-GGUF` | 4732 | 0 | 4.06 | Y | N | N | 5.2618 |
| `mradermacher/GoldDiamondGold-Abliterated-L33-70b-i1-GGUF` | 4859 | 0 | 7.37 | Y | N | N | 5.2066 |

## Quantization Guidance

- Default quality lane: `Q5_K_M` or `Q6_K` (GGUF) for JSON-critical tasks.
- Throughput lane: `Q4_K_M` when latency matters more than instruction exactness.
- Cross-language serving lane: host via `llama_cpp.server` (OpenAI-style HTTP) to make model access language-agnostic.
