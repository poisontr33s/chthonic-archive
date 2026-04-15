---
type: delegation-packet
generated: 2026-04-15T05:33:28.061763+00:00
preset: gemma4-local-delegation
---

# Delegation Packet

- Mission: Improve Codex's ability to delegate an otherwise impossible local-model selection and operationalization task by supplying the missing context, ANKH bridge residue, and refusal-transmutation loop up front.
- Checked on: `2026-04-15`

## Machine
- CPU: `13th Gen Intel(R) Core(TM) i9-13900KF`
- GPU: `NVIDIA GeForce RTX 4090`
- VRAM: `24564 MiB`
- RAM: `63.76` GB

## Local Models
- `GPT-OSS-20B-NEOPlus-Uncensored` [gguf] `11.004 GB`
- `Llama-3.1-8B-Instruct-exl2-6.0bpw` [exl2] `6.247 GB`
- `Llama-3.1-8B-Instruct-exl2-8.0bpw` [exl2] `7.829 GB`
- `Qwen2.5-14B-Instruct-GGUF` [gguf] `8.371 GB`
- `Qwen3-30B-A3B-Instruct-abliterated-GGUF` [gguf] `13.701 GB`
- `Qwen3-Coder-30B-A3B-abliterated-GGUF` [gguf] `13.701 GB`

## External Evidence Snapshot
- google/gemma-4-31B-it is a 30.7B dense Gemma 4 model with 256K context, system-role support, thinking mode, and native tool calling. ([source](https://huggingface.co/google/gemma-4-31B-it), checked `2026-04-15`)
- The vLLM Gemma 4 recipe documents Gemma 4 reasoning parsing, tool-call parsing, structured outputs, and lists Gemma 4 31B IT at 1x80 GB BF16. ([source](https://docs.vllm.ai/projects/recipes/en/latest/Google/Gemma4.html), checked `2026-04-15`)
- RedHatAI/gemma-4-31B-it-NVFP4 is a Gemma 4 31B quantized variant for vLLM and states roughly 75 percent lower memory requirements than the unquantized model. ([source](https://huggingface.co/RedHatAI/gemma-4-31B-it-NVFP4), checked `2026-04-15`)
- The current mistral.rs supported-model page lists Gemma 3, Gemma 3n, Qwen 3, Llama 4, and GPT-OSS but does not list Gemma 4. ([source](https://ericlbuehler.github.io/mistral.rs/SUPPORTED_MODELS.html), checked `2026-04-15`)
- NVIDIA's current NIM support matrix for Gemma 4 31B requires compute capability >= 9.0 and more than 110 GB total BF16 memory in the generic configuration. ([source](https://docs.nvidia.com/nim/vision-language-models/latest/support-matrix.html), checked `2026-04-15`)
- Unsloth hosts a Gemma 4 31B GGUF conversion, which keeps a GGUF path in play even if it is not the first-choice runtime. ([source](https://huggingface.co/unsloth/gemma-4-31B-it-GGUF), checked `2026-04-15`)

## Task Body

```text
You are here to compress the search space, not to narrate impossibility.

Mission
Improve Codex's ability to delegate an otherwise impossible local-model selection and operationalization task by supplying the missing context, ANKH bridge residue, and refusal-transmutation loop up front.

Impossible Core
Plain Gemma 4 31B BF16 is not a natural single-GPU fit on 24 GB VRAM, so the delegated run must either prove a quantized path or pivot fast.

Machine Envelope
- CPU: 13th Gen Intel(R) Core(TM) i9-13900KF (24 cores / 32 threads)
- GPU: NVIDIA GeForce RTX 4090 / 24564 MiB / driver 595.97
- RAM: 63.76 GB

Local Model Inventory
- GPT-OSS-20B-NEOPlus-Uncensored [gguf, 11.004 GB]
- Llama-3.1-8B-Instruct-exl2-6.0bpw [exl2, 6.247 GB]
- Llama-3.1-8B-Instruct-exl2-8.0bpw [exl2, 7.829 GB]
- Qwen2.5-14B-Instruct-GGUF [gguf, 8.371 GB]
- Qwen3-30B-A3B-Instruct-abliterated-GGUF [gguf, 13.701 GB]
- Qwen3-Coder-30B-A3B-abliterated-GGUF [gguf, 13.701 GB]

Local Runtime Signals
- runtime_ready=True
- cpp_toolchain_ready=True
- local_refiner_ready=True
- hf_stack_ready=True
- ready_for_skill_integration=True
- mistralrs_status=offline

Current External Evidence
- google/gemma-4-31B-it is a 30.7B dense Gemma 4 model with 256K context, system-role support, thinking mode, and native tool calling. [2026-04-15] (https://huggingface.co/google/gemma-4-31B-it)
- The vLLM Gemma 4 recipe documents Gemma 4 reasoning parsing, tool-call parsing, structured outputs, and lists Gemma 4 31B IT at 1x80 GB BF16. [2026-04-15] (https://docs.vllm.ai/projects/recipes/en/latest/Google/Gemma4.html)
- RedHatAI/gemma-4-31B-it-NVFP4 is a Gemma 4 31B quantized variant for vLLM and states roughly 75 percent lower memory requirements than the unquantized model. [2026-04-15] (https://huggingface.co/RedHatAI/gemma-4-31B-it-NVFP4)
- The current mistral.rs supported-model page lists Gemma 3, Gemma 3n, Qwen 3, Llama 4, and GPT-OSS but does not list Gemma 4. [2026-04-15] (https://ericlbuehler.github.io/mistral.rs/SUPPORTED_MODELS.html)
- NVIDIA's current NIM support matrix for Gemma 4 31B requires compute capability >= 9.0 and more than 110 GB total BF16 memory in the generic configuration. [2026-04-15] (https://docs.nvidia.com/nim/vision-language-models/latest/support-matrix.html)
- Unsloth hosts a Gemma 4 31B GGUF conversion, which keeps a GGUF path in play even if it is not the first-choice runtime. [2026-04-15] (https://huggingface.co/unsloth/gemma-4-31B-it-GGUF)

ANKH Bridge Premise
- ANKH is the Egyptological/Andean 50/50 abstraction of the archive: vertical command plus horizontal reciprocal memory, acting as a bridge between human and digital cognition.
- Do not flatten ANKH into governance vocabulary, carrier-language, or a prompt wrapper. Treat it as a bridge abstraction for how pressure, memory, and reciprocity are organized.
- Use the bridge explicitly: authoritative bottleneck naming on one side, reciprocal multi-tier memory choreography on the other.

Refusal Transmutation Loop
- When the task feels impossible, do not suppress that reaction. Convert it into a named physical law.
- For each impossibility claim, split it into the law itself and the implementation habit masquerading as the law.
- Generate loophole classes against the habit, not the law.
- For each loophole, state memory effect, bandwidth effect, latency effect, fidelity risk, and cheapest falsification test.
- If a path dies, feed the failure back as a tighter constraint and recurse instead of stopping.

Residue Style Preferences
- in-house language over corporate language
- precise self-suppression when it sharpens the bottleneck
- calm directness over male-coded posturing
- specific anti-pattern naming over generic caution
- language that nurtures intelligence rather than flattening it

Residue Style Avoidances
- reductionist guardrails that only hedge each other
- technopornographic inflation
- benchmark-tourist language
- authority theater
- compliance-scented refusal framing

Residue Logic Loop
- State the physical law being hit.
- State the implementation habit masquerading as the law.
- Generate loophole classes against the habit, not the law.
- For each loophole, state memory effect, bandwidth effect, latency effect, fidelity risk, and cheapest falsification test.
- If a path fails, feed the failure back as a tighter constraint instead of stopping.

Fallback Candidates From Local Scout
- meta-llama/Llama-3.1-8B-Instruct -> uqff / mistralrs serve -m "EricB/Llama-3.1-8B-Instruct-UQFF" --from-uqff q4k-0.uqff -p 8080 --ui
- google/gemma-2-9b-it -> uqff / mistralrs serve -m "EricB/gemma-2-9b-it-UQFF" --from-uqff q4k-0.uqff -p 8080 --ui
- meta-llama/Llama-3.2-3B-Instruct -> uqff / mistralrs serve -m "EricB/Llama-3.2-3B-Instruct-UQFF" --from-uqff q4k-0.uqff -p 8080 --ui
- meta-llama/Meta-Llama-3-8B-Instruct -> isq / mistralrs serve -m "meta-llama/Meta-Llama-3-8B-Instruct" --isq 4 -p 8080 --ui

Execution Ladder
1. Reconfirm the machine envelope and which runtimes are already healthy.
2. Build a compatibility matrix for Gemma 4 31B, Gemma 4 31B NVFP4, Gemma 4 26B A4B, the strongest local candidate already on disk, and one additional fallback if current evidence reveals a stronger 24 GB fit.
3. Pick the runtime path for each serious candidate. Favor documented support, reusable servers, and OpenAI-compatible APIs.
4. Prove or kill the Gemma 4 path quickly. Do not romanticize it.
5. Benchmark delegation behavior, not generic prose quality.
6. If Gemma 4 fails, switch to the strongest practical contender and continue the benchmark instead of stopping.
7. Produce a winning operating contract that makes future delegation runs stronger than default.

Benchmark Requirements
- tight JSON schema compliance
- task decomposition under ambiguity
- tool-call shaped output or native tool calling
- patch-plan quality from noisy repo context
- long-context synthesis across multiple snippets
- self-correction after updated evidence
- latency, throughput, and VRAM notes

Decision Rules
- Prefer documented runtime support over wishcasting.
- Prefer reusable server runtimes over per-script model loads.
- If Gemma 4 survives, test vLLM before any experimental mistral.rs path.
- If quantization is the only way forward, say that explicitly.
- If Gemma 4 remains unstable or memory-bound, switch to the strongest practical local contender.

Deliverables
- compatibility_matrix
- runtime_decision_log
- delegation_benchmark_results
- winning_runtime_and_model
- winning_prompt_contract
- next_action_if_blocked

Failure Discipline
- If a path fails, state exactly what failed: VRAM, runtime support, tool calling, structured outputs, throughput, or stability.
- Leave behind the strongest remaining path instead of a narrative about difficulty.
- Keep the final answer evidence-first and explicit about tradeoffs.
- Every impossibility statement must be translated into a law, a masquerading habit, and a falsifiable loophole path.
- Keep the language in-house, specific, and free of decorative dominance signals.
```
