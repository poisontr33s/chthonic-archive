---
type: uncensored-lane-steward
generated: 2026-02-19T23:10:22.505616+00:00
---

# Uncensored Lane Steward

## Policy

- Strict JSON lane: `qwen3_coder_abliterated` (highest quality-first score)
- Code lane: `qwen3_coder_abliterated` (coder-specialized lane preferred when available)
- Unrestricted lane: `qwen3_instruct_abliterated` (best uncensored compliance lane with quality guarantees)
- Demoted lanes:
  - `gpt_oss_20b_neoplus_uncensored`: composite_score=33.3 < 100.0
  - `gpt_oss_20b_neoplus_uncensored`: fails structured output compliance; keep experimental only

## Local Ranked Lanes

| Lane | Composite | Avg toks/s | Score | Model file |
| --- | ---: | ---: | ---: | --- |
| qwen3_coder_abliterated | 100.0 | 13.2 | 100013.2 | Huihui-Qwen3-Coder-30B-A3B-Instruct-abliterated.i1-Q3_K_M.gguf |
| qwen3_instruct_abliterated | 100.0 | 13.02 | 100013.02 | Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated.i1-Q3_K_M.gguf |
| qwen25_14b_baseline | 100.0 | 3.98 | 100003.98 | qwen2.5-14b-instruct-q4_k_m-00001-of-00003.gguf |
| gpt_oss_20b_neoplus_uncensored | 33.3 | 12.18 | 33312.18 | OpenAI-20B-NEOPlus-Uncensored-IQ4_NL.gguf |

## Live HF Candidates (Uncensored + Quantization-friendly)

| Model | Downloads | Likes | Age(days) | GGUF | SAFETENSORS | AWQ/GPTQ/EXL2 | Score |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: |
| `DavidAU/OpenAi-GPT-oss-20b-abliterated-uncensored-NEO-Imatrix-gguf` | 102627 | 442 | 94.62 | Y | N | N | 7.0084 |
| `DavidAU/OpenAi-GPT-oss-20b-HERETIC-uncensored-NEO-Imatrix-gguf` | 47088 | 98 | 81.89 | Y | N | N | 6.5145 |
| `mradermacher/OpenAI-gpt-oss-20B-Claude-4.5-Opus-Heretic-Uncensored-i1-GGUF` | 49256 | 3 | 6.84 | Y | N | N | 6.3709 |
| `mradermacher/OpenAI-gpt-oss-20B-INSTRUCT-Heretic-Uncensored-MXFP4-i1-GGUF` | 40246 | 0 | 3.58 | Y | N | N | 6.2067 |
| `mradermacher/OpenAI-gpt-oss-20B-INSTRUCT-Heretic-Uncensored-i1-GGUF` | 18706 | 1 | 2.14 | Y | N | N | 6.0154 |
| `mradermacher/Huihui-Qwen3-Coder-Next-abliterated-i1-GGUF` | 21738 | 1 | 5.6 | Y | N | N | 5.9621 |
| `mradermacher/OpenAI-gpt-oss-20B-GPT5.1-5.2-DISTILL-Heretic-Uncensored-MXFP4-i1-GGUF` | 24293 | 0 | 4.75 | Y | N | N | 5.9537 |
| `mradermacher/Qwen3-30B-A3B-Gemini-Pro-High-Reasoning-2507-ABLITERATED-UNCENSORED-i1-GGUF` | 15162 | 2 | 3.24 | Y | N | N | 5.9144 |
| `mradermacher/GPT-OSS-26E-Abliterated-i1-GGUF` | 8513 | 0 | 1.35 | Y | N | N | 5.6591 |
| `botp/OpenAi-GPT-oss-20b-HERETIC-uncensored-NEO-Imatrix-gguf` | 11913 | 0 | 14.82 | Y | N | N | 5.5307 |
| `bartowski/huihui-ai_Qwen3-Coder-Next-abliterated-GGUF` | 6839 | 5 | 9.32 | Y | N | N | 5.5261 |
| `mradermacher/Qwen3-VL-8B-Thinking-c_abliterated-v2-i1-GGUF` | 9423 | 0 | 7.2 | Y | N | N | 5.4968 |
| `mradermacher/MistralAI-Magistral-Small-2507-Heretic-Uncensored-i1-GGUF` | 6006 | 0 | 1.63 | Y | N | N | 5.4827 |
| `mradermacher/Huihui-Kimi-Linear-REAP-35B-A3B-Instruct-abliterated-i1-GGUF` | 6937 | 0 | 3.96 | Y | N | N | 5.4309 |
| `mradermacher/Qwen3-VL-8B-Instruct-c_abliterated-v3-i1-GGUF` | 6126 | 2 | 7.2 | Y | N | N | 5.429 |
| `mradermacher/XortronCriminalComputingConfig-heretic-i1-GGUF` | 4190 | 0 | 0.93 | Y | N | N | 5.3998 |
| `mradermacher/GPT-OSS-20E-Abliterated-i1-GGUF` | 4442 | 0 | 1.33 | Y | N | N | 5.3793 |
| `mradermacher/Qwen3-30B-A3B-Claude-4.5-Opus-High-Reasoning-2507-ABLITERATED-UNCENSORED-V2-i1-GGUF` | 4567 | 0 | 3.15 | Y | N | N | 5.2776 |
| `mradermacher/OpenAI-gpt-oss-20B-INSTRUCT-Heretic-Uncensored-MXFP4-GGUF` | 4732 | 0 | 4.06 | Y | N | N | 5.2619 |
| `mradermacher/GoldDiamondGold-Abliterated-L33-70b-i1-GGUF` | 4859 | 0 | 7.37 | Y | N | N | 5.2067 |

## Quantization Guidance

- Default quality lane: `Q5_K_M` or `Q6_K` (GGUF) for JSON-critical tasks.
- Throughput lane: `Q4_K_M` when latency matters more than instruction exactness.
- Cross-language serving lane: host via `llama_cpp.server` (OpenAI-style HTTP) to make model access language-agnostic.
