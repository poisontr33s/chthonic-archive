# Gemini 3 Pro Deep Research Request — Anno Live Time (V2)
## Date: 2026-02-19
## Context: Chthonic Archive, native Windows 11, no WSL/WSL2, no Docker

Use this prompt with Gemini 3 Pro Deep Research:

```text
You are doing a high-rigor engineering deep-research pass for a local-first AI stack.

Environment constraints:
- OS: Windows 11 24H2 (native only)
- GPU: RTX 4090 Laptop 16GB VRAM
- Runtime policy: no WSL, no WSL2, no Docker
- Stack: uv + bun + rustup + rv + goup + llama-cpp-python + LocalAI candidate
- Research date target: current as of 2026-02-19

Mission:
Resolve the remaining unanswered technical decisions blocking production hardening.

1) GPT-OSS 20B structured output failure (highest priority)
- Current observed failure: model emits channel tokens like <|channel|>analysis<|message|> and ignores strict JSON constraints.
- We need: deterministic JSON output in llama-cpp-python with schema/grammar constraints.
- Determine:
  - Required chat template and prompt framing for GPT-OSS 20B abliterated variants.
  - Whether GGUF metadata/template mismatch is root cause.
  - Exact llama-cpp-python settings that can suppress chain-of-thought/channel emission.
  - Whether specific model variants/quants (same family) are known to be JSON-compliant.
  - Whether LocalAI improves compliance vs direct llama-cpp-python.
- Deliverable:
  - A tested configuration matrix: {model variant, chat template, decoding params, grammar method, pass/fail for strict JSON}.

2) Uncensored model lane decision for production
- Current local benchmark:
  - Qwen3 Coder A3B abliterated: 100/100 composite
  - Qwen3 Instruct A3B abliterated: 100/100 composite
  - Qwen2.5 14B baseline: 100/100 composite, slower
  - GPT-OSS 20B NEOPlus uncensored: 0/100 composite, fastest tokens/s
- Determine:
  - Best model routing policy for three lanes: strict-JSON classification, code generation, unrestricted content triage.
  - Whether GPT-OSS should remain in lane after template fixes or be demoted.
  - Better uncensored open-source alternatives available now for 16GB VRAM (quality + structure compliance).
- Deliverable:
  - Ranked recommendation with measurable thresholds and a lane routing table.

3) LocalAI on native Win11 (no container path)
- Determine:
  - Current maturity of LocalAI native Windows binary for long-running overnight jobs.
  - Stability and observability compared to direct llama-cpp-python process model.
  - Structured output/grammar capabilities and known limitations on Windows.
  - Best deployment topology for unattended runs (service/scheduler/supervisor pattern).
- Deliverable:
  - Recommended deployment blueprint and failure-recovery playbook.

4) Anno self-healing governance
- We already use endoflife.date for python/rust/go/node/bun lane checks.
- Determine:
  - What to do for products without canonical endoflife.date coverage (e.g., Solana/Agave/Anchor) while preserving deterministic policy.
  - Best policy thresholds for auto-update vs manual gate in production.
  - Version drift strategy for polyglot managers (uv, rv, goup, bun, rustup, mise).
- Deliverable:
  - A policy spec with machine-actionable rules and risk grading.

5) VS Code Insiders extension alignment (1.110.0-insider lane)
- Determine:
  - What is actually supported today for extension-side layout/activity customization in Insiders.
  - Which APIs are stable vs proposed-only and what can be shipped safely.
  - Recommended architecture for a robust fallback path when proposed APIs are unavailable.
- Deliverable:
  - API capability table with implementation guidance and fallback strategy.

6) Native POSIX-equivalent lane without WSL
- We need shell semantics close to POSIX on Windows without WSL.
- Determine:
  - Practical options (MSYS2/Git Bash/Cygwin/Nu/BusyBox/etc.) for scripting interoperability with our polyglot stack.
  - Compatibility/perf tradeoffs for Rust + Bun + uv + Solana toolchain usage.
  - Recommended standard shell contract for this repository.
- Deliverable:
  - A single recommended shell strategy with integration checklist.

Research method requirements:
- Use primary sources first (official docs/repos/release notes).
- Include concrete dates and version numbers.
- Separate confirmed facts vs inferred conclusions.
- Provide links per claim.
- Avoid generic advice; produce decision-grade implementation guidance.

Output format required:
1. Executive verdicts (one page)
2. Evidence table (claim -> source -> date)
3. Decision matrix (options, pros/cons, risk)
4. Exact implementation playbook (commands/config snippets)
5. 30/60/90 day maintenance cadence
```

## Suggested invocation

```powershell
$prompt = Get-Content -Raw "claude-codex-gemini/engineering_agentic_deep_research_candidates/gemini-deep-research-2026-02/10-anno-live-unanswered-questions-v2.md"
# Preferred lane when available in your account:
pwsh -NoProfile -File "scripts/gemini-cli-wrapper.ps1" -m "gemini-3-pro-preview" -p $prompt

# Fallback if preview alias is unavailable:
pwsh -NoProfile -File "scripts/gemini-cli-wrapper.ps1" -m "gemini-2.5-pro" -p $prompt
```
