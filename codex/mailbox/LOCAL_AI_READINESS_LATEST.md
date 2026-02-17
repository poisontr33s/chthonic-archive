# Local AI Readiness (Latest)

- Generated: `2026-02-17T02:26:34Z`
- Runtime ready: `True`
- Local refiner ready: `False`
- Overnight data ready: `True`
- Scheduler log clean: `False`
- Ready for skill integration: `False`

## Paths
- Latest daemon run: `C:/Users/erdno/chthonic-archive/dumpster-dive/intake/overnight-daemon/20260217_030002`
- Latest scheduler log: `C:/Users/erdno/chthonic-archive/dumpster-dive/intake/overnight-daemon/nightly-scheduled-2026-02-17_030002.log`
- Latest archaeology run: `C:/Users/erdno/chthonic-archive/dumpster-dive/intake/overnight-intelligence/arch-2026-02-17T02-00-04`
- Latest digest: `C:/Users/erdno/chthonic-archive/claude/mailbox/ARCHAEOLOGY_DIGEST_2026_02_13.md`

## Checks
- `OK` `runtime:uv`: C:\Users\erdno\.local\bin\uv.EXE
- `OK` `runtime:python`: 3.13.11 (main, Dec  9 2025, 19:02:08) [MSC v.1944 64 bit (AMD64)]
- `FAIL` `module:llama_cpp`: missing module llama_cpp
  - Install hint: uv add --dev llama-cpp-python
- `OK` `module:pydantic`: import ok
- `OK` `model:qwen_14b`: 3 gguf file(s) in C:/Users/erdno/chthonic-archive/models/Qwen2.5-14B-Instruct-GGUF
- `OK` `model:gpt_oss_20b`: 1 gguf file(s) in C:/Users/erdno/chthonic-archive/models/GPT-OSS-20B-NEOPlus-Uncensored
- `OK` `artifact:daemon_report_json`: C:/Users/erdno/chthonic-archive/dumpster-dive/intake/overnight-daemon/20260217_030002/report.json
- `OK` `artifact:daemon_report_md`: C:/Users/erdno/chthonic-archive/dumpster-dive/intake/overnight-daemon/20260217_030002/report.md
- `OK` `artifact:l1_ore`: C:/Users/erdno/chthonic-archive/dumpster-dive/intake/overnight-intelligence/arch-2026-02-17T02-00-04/L1-ore.json
- `OK` `artifact:l1_summary`: C:/Users/erdno/chthonic-archive/dumpster-dive/intake/overnight-intelligence/arch-2026-02-17T02-00-04/L1-summary.md
- `OK` `artifact:latest_digest`: C:/Users/erdno/chthonic-archive/claude/mailbox/ARCHAEOLOGY_DIGEST_2026_02_13.md
  - Digest absence is acceptable for L1-only runs.
- `FAIL` `log:scheduler`: C:/Users/erdno/chthonic-archive/dumpster-dive/intake/overnight-daemon/nightly-scheduled-2026-02-17_030002.log
  - Python traceback detected in scheduler log.
  - ModuleNotFoundError detected in scheduler log.

## Recommendations
- Install local refiner deps and verify Qwen GGUF model directory before skill-side automation.
- Fix scheduler/runtime errors first; treat latest run as informational only.
