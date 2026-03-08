---
type: session-resumption-packet
owner: codex
generated: 2026-03-08T02:47:11.170202+00:00
scope: claude-side continuation + localai stewardship
---

# Session Resumption High Coverage (Codex Stewardship)

- Coverage score: **75.0%**
- Generated (UTC): `2026-03-08 02:47:11`

## Continuation Trail (Claude-side)

- Latest digest: `C:\Users\erdno\chthonic-archive\claude\mailbox\ARCHAEOLOGY_DIGEST_2026_02_20.md`
- Latest local-AI readiness: `C:\Users\erdno\chthonic-archive\claude\mailbox\LOCAL_AI_READINESS_LATEST.json`
- Latest session sync packet: `C:\Users\erdno\chthonic-archive\claude\mailbox\SESSION_SYNC_PACKET_2026_02_09.md`
- Mailbox state anchor: `C:\Users\erdno\chthonic-archive\claude\mailbox\MAILBOX_CURRENT_STATE.md`
- Session log anchor: `C:\Users\erdno\chthonic-archive\claude-codex-gemini\session_resumption_pickup\session_resumption_pickup_codex.md`

## Coverage Checks

| Check | Status | Detail |
| --- | --- | --- |
| Claude digest exists | OK | C:\Users\erdno\chthonic-archive\claude\mailbox\ARCHAEOLOGY_DIGEST_2026_02_20.md |
| Local AI readiness snapshot exists | OK | C:\Users\erdno\chthonic-archive\claude\mailbox\LOCAL_AI_READINESS_LATEST.json |
| Nightly scheduler log exists | OK | C:\Users\erdno\chthonic-archive\dumpster-dive\intake\overnight-daemon\nightly-scheduled-2026-03-08_030002.log |
| Nightly scheduler log clean | OK | clean |
| Nightly completion marker present | OK | complete marker found |
| Daemon report exists | OK | C:\Users\erdno\chthonic-archive\dumpster-dive\intake\overnight-daemon\20260308_030002\report.json |
| L1 ore exists | OK | C:\Users\erdno\chthonic-archive\dumpster-dive\intake\overnight-intelligence\arch-2026-02-20T02-00-06\L1-ore.json |
| Uncensored model lane present | OK | detected |
| Qwen3 abliterated lane present | OK | detected |
| numpy 2.x functional | FAIL | missing |
| polars functional | FAIL | missing |
| llama-cpp lane import | FAIL | missing |

## Nightly Daemon Status

- Latest scheduler log: `C:\Users\erdno\chthonic-archive\dumpster-dive\intake\overnight-daemon\nightly-scheduled-2026-03-08_030002.log`
- Latest daemon run: `C:\Users\erdno\chthonic-archive\dumpster-dive\intake\overnight-daemon\20260308_030002`
- Latest archaeology run: `C:\Users\erdno\chthonic-archive\dumpster-dive\intake\overnight-intelligence\arch-2026-02-20T02-00-06`
- Nightly clean: **yes**

## LocalAI Runtime

| Tool | Status | Detail |
| --- | --- | --- |
| uv | OK | uv 0.10.8 (c021be36a 2026-03-03) |
| bun | OK | 1.3.9 |
| pwsh | OK | PowerShell 7.5.4 |

- numpy: `missing`
- polars: `missing`
- llama_cpp: `missing`

## Model Inventory (Installed)

| Model | Format | Files | Size(GB) | Uncensored | Largest file |
| --- | --- | --- | --- | --- | --- |
| GPT-OSS-20B-NEOPlus-Uncensored | gguf | 3 | 11.004 | yes | OpenAI-20B-NEOPlus-Uncensored-IQ4_NL.gguf |
| Llama-3.1-8B-Instruct-exl2-6.0bpw | safetensors/exl2 | 19 | 6.247 | no | output.safetensors |
| Llama-3.1-8B-Instruct-exl2-8.0bpw | safetensors/exl2 | 28 | 7.829 | no | output.safetensors |
| Qwen2.5-14B-Instruct-GGUF | gguf | 7 | 8.371 | no | qwen2.5-14b-instruct-q4_k_m-00001-of-00003.gguf |
| Qwen3-30B-A3B-Instruct-abliterated-GGUF | gguf | 3 | 13.701 | yes | Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated.i1-Q3_K_M.gguf |
| Qwen3-Coder-30B-A3B-abliterated-GGUF | gguf | 3 | 13.701 | yes | Huihui-Qwen3-Coder-30B-A3B-Instruct-abliterated.i1-Q3_K_M.gguf |

## Live Uncensored Model Signals (Hugging Face API)

### Search: `uncensored` (top by downloads)

| Model ID | Downloads | Likes | Last Modified |
| --- | --- | --- | --- |
| DavidAU/GLM-4.7-Flash-Uncensored-Heretic-NEO-CODE-Imatrix-MAX-GGUF | 125879 | 273 | 2026-01-28T09:07:52.000Z |
| TheBloke/Wizard-Vicuna-30B-Uncensored-GPTQ | 107116 | 605 | 2023-09-27T12:44:25.000Z |
| DavidAU/OpenAi-GPT-oss-20b-abliterated-uncensored-NEO-Imatrix-gguf | 100798 | 455 | 2025-11-17T08:20:27.000Z |
| mradermacher/Llama3.3-8B-Instruct-Thinking-Heretic-Uncensored-Claude-4.5-Opus-High-Reasoning-i1-GGUF | 91888 | 17 | 2026-01-02T19:45:54.000Z |
| mradermacher/OpenAI-gpt-oss-20B-Claude-4.5-Opus-Heretic-Uncensored-i1-GGUF | 68091 | 20 | 2026-02-13T03:00:09.000Z |
| DavidAU/Llama-3.2-8X3B-MOE-Dark-Champion-Instruct-uncensored-abliterated-18.4B-GGUF | 62669 | 506 | 2025-12-01T03:54:02.000Z |
| HauhauCS/Qwen3.5-9B-Uncensored-HauhauCS-Aggressive | 52816 | 184 | 2026-03-04T00:31:47.000Z |
| DavidAU/OpenAi-GPT-oss-20b-HERETIC-uncensored-NEO-Imatrix-gguf | 47477 | 111 | 2025-11-30T01:55:32.000Z |

### Search: `abliterated` (top by downloads)

| Model ID | Downloads | Likes | Last Modified |
| --- | --- | --- | --- |
| DavidAU/OpenAi-GPT-oss-20b-abliterated-uncensored-NEO-Imatrix-gguf | 100798 | 455 | 2025-11-17T08:20:27.000Z |
| huihui-ai/Qwen2.5-72B-Instruct-abliterated | 66436 | 36 | 2025-06-06T09:15:07.000Z |
| mlabonne/gemma-3-12b-it-abliterated | 65697 | 26 | 2025-03-21T16:10:27.000Z |
| DavidAU/Llama-3.2-8X3B-MOE-Dark-Champion-Instruct-uncensored-abliterated-18.4B-GGUF | 62669 | 506 | 2025-12-01T03:54:02.000Z |
| Goekdeniz-Guelmez/Josiefied-Qwen3-14B-abliterated-v3 | 56283 | 25 | 2025-08-11T15:23:13.000Z |
| jnvdx666/Qwen3-32B-abliterated-awq | 50228 | 0 | 2025-05-12T20:47:34.000Z |
| BennyDaBall/Qwen3-4b-Z-Image-Turbo-AbliteratedV1 | 42406 | 37 | 2026-01-31T17:47:55.000Z |
| mradermacher/Huihui-Qwen3.5-27B-abliterated-GGUF | 39784 | 12 | 2026-02-28T07:34:24.000Z |

## Anno Live Time (endoflife.date)

| Product | Cycle | Latest Patch | Patch Date | EOL From | Maintained |
| --- | --- | --- | --- | --- | --- |
| python | 3.14 | 3.14.3 | 2026-02-03 | 2030-10-31 | yes |
| rust | 1.94 | 1.94.0 | 2026-03-05 | unknown | yes |
| go | 1.26 | 1.26.1 | 2026-03-05 | unknown | yes |
| nodejs | 25 | 25.8.0 | 2026-03-03 | 2026-06-01 | yes |
| bun | 1 | 1.3.10 | 2026-02-25 | unknown | yes |

## Continuation Actions (Immediate)

1. Keep `Qwen3-30B-A3B-Instruct-abliterated` as primary local uncensored lane for nightly v2 refiner.
2. Keep `Qwen3-Coder-30B-A3B-abliterated` as code-heavy fallback lane.
3. Keep `GPT-OSS-20B-NEOPlus-Uncensored` as secondary uncensored checkpoint model.
4. Use `uv run scripts/session_resumption_high_coverage.py` after major nightlies to refresh continuity packet.
5. If a lane regresses, compare against this packet first, then reopen from Claude digest + nightly log pair.

## Session Log Tail (Raw Anchor)

```text
OUT
0
Bash Uncommitted diff stats
IN
cd /c/Users/erdno/chthonic-archive && git diff --stat

OUT
0
Bash Today's commit count
IN
cd /c/Users/erdno/chthonic-archive && git log --oneline --since="24 hours ago" | wc -l

OUT
24
```
