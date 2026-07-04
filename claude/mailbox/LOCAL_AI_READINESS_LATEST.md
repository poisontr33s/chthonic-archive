# Local AI Readiness (Latest)

- Generated: `2026-07-03T21:39:04Z`
- Runtime ready: `True`
- C++/Vulkan toolchain ready: `True`
- Local refiner ready: `True`
- HF stack ready: `True`
- Overnight data ready: `True`
- Scheduler log clean: `True`
- Ready for skill integration: `True`

## Toolchain
- `uv`: `uv 0.11.25 (1fc7de7c4 2026-06-26 x86_64-pc-windows-msvc)`
- `python`: `3.14.6 (main, Jun 11 2026, 04:05:02) [MSC v.1944 64 bit (AMD64)]`
- `rv`: `rv 0.6.0`
- `ruby`: `ruby 4.0.5 (2026-05-20 revision 64336ffd0e) +PRISM [x64-mingw-ucrt]`
- `az`: `2.86.0`
- `bun`: `1.3.14`
- `pwsh`: `7.6.1`
- `rustc`: `rustc 1.96.0 (ac68faa20 2026-05-25)`
- `cargo`: `cargo 1.96.0 (30a34c682 2026-05-25)`
- `msvc_cl`: `C:\Program Files\Microsoft Visual Studio\18\Insiders\VC\Tools\MSVC\14.51.36231\bin\Hostx64\x64\cl.exe`
- `cmake`: `cmake version 4.3.4`
- `ninja`: `1.13.0.git.kitware.jobserver-pipe-1`
- `msbuild`: `C:\Program Files\Microsoft Visual Studio\18\Insiders\MSBuild\Current\Bin\MSBuild.exe`
- `glslc`: `shaderc v2026.2 v2026.2`
- `vulkan_sdk`: `C:\VulkanSDK\1.4.350.0`
- `vs_build_tools`: `display=17.14.35 (June 2026) install=17.14.37411.7`
- `vs_any_instance`: `SQL Server Management Studio 22 (22.7.11919.86)`
- `ssms`: `22.7.11919.86`

## Paths
- Latest daemon run: `C:/Users/eldno/chthonic-archive/dumpster-dive/intake/overnight-daemon/20260430_023324`
- Latest scheduler log: `C:/Users/eldno/chthonic-archive/dumpster-dive/intake/overnight-daemon/nightly-scheduled-2026-03-13_030005.log`
- Latest archaeology run: `C:/Users/eldno/chthonic-archive/dumpster-dive/intake/overnight-intelligence/arch-2026-02-20T02-00-06`
- Latest digest: `None`

## Model Residences
- `qwen_14b`: exists=`True` format=`gguf` files=`7` size_gb=`8.371` path=`C:/Users/eldno/chthonic-archive/models/Qwen2.5-14B-Instruct-GGUF`
- `gpt_oss_20b`: exists=`True` format=`gguf` files=`3` size_gb=`11.004` path=`C:/Users/eldno/chthonic-archive/models/GPT-OSS-20B-NEOPlus-Uncensored`
- `llama_8b_exl2`: exists=`True` format=`safetensors/exl2` files=`19` size_gb=`6.247` path=`C:/Users/eldno/chthonic-archive/models/Llama-3.1-8B-Instruct-exl2-6.0bpw`

## Lane Baseline
- `local_refiner_v2` [python] ready=`True` entry=`scripts/local_refiner_v2.py`
  - model: `C:/Users/eldno/chthonic-archive/models/Qwen2.5-14B-Instruct-GGUF`
  - required: `llama_cpp, pydantic, numpy, tool:uv, tool:pwsh`
  - missing_required: `(none)`
  - optional_missing: `(none)`
  - Primary local LLM lane (structured JSON).
- `local_refiner_v1` [python] ready=`False` entry=`scripts/local_refiner.py`
  - model: `C:/Users/eldno/chthonic-archive/models/Llama-3.1-8B-Instruct-exl2-6.0bpw`
  - required: `exllamav2, torch, tool:uv, tool:pwsh`
  - missing_required: `exllamav2`
  - optional_missing: `(none)`
  - Legacy fallback lane (ExLlamaV2).
- `hf_refiner` [python] ready=`True` entry=`scripts/hf_refiner.py`
  - required: `huggingface_hub, requests, mcp, pydantic_settings, tool:uv, tool:pwsh`
  - missing_required: `(none)`
  - optional_missing: `(none)`
  - Uses HF token auth; can run without local GPU model files.
- `overnight_daemon` [typescript+powershell] ready=`True` entry=`scripts/run_archaeology.ps1 + scripts/overnight_daemon.ts`
  - required: `tool:bun, tool:pwsh, tool:uv`
  - missing_required: `(none)`
  - optional_missing: `(none)`
  - Scavenge/classification lane that feeds L1 ore and daemon reports.
- `cpp_vulkan_toolchain` [msvc+cmake+ninja+vulkan] ready=`True` entry=`native toolchain baseline for local-ai extensions + shaders`
  - required: `tool:cl, tool:cmake, tool:ninja, tool:glslc, tool:vulkan_sdk`
  - missing_required: `(none)`
  - optional_missing: `(none)`
  - Tracks native/C++ readiness for local model backends and Vulkan shader pipelines.
  - msbuild and vs_build_tools are reported as additional environment indicators.

## Checks
- `OK` `runtime:uv`: uv 0.11.25 (1fc7de7c4 2026-06-26 x86_64-pc-windows-msvc)
- `OK` `runtime:python`: 3.14.6 (main, Jun 11 2026, 04:05:02) [MSC v.1944 64 bit (AMD64)]
- `OK` `runtime:bun`: 1.3.14
- `OK` `runtime:pwsh`: 7.6.1
- `OK` `runtime:rustc`: rustc 1.96.0 (ac68faa20 2026-05-25)
  - Rust toolchain is optional for current local-AI paths but available for extension lanes.
- `OK` `runtime:rv`: rv 0.6.0
  - Ruby manager lane in your polyglot toolchain.
- `OK` `runtime:ruby`: ruby 4.0.5 (2026-05-20 revision 64336ffd0e) +PRISM [x64-mingw-ucrt]
  - Optional for local-AI flows; useful for broader polyglot automation.
- `OK` `runtime:az`: 2.86.0
  - Azure CLI is optional but useful for model artifact storage and cloud deployment lanes.
- `OK` `runtime:msvc_cl`: found on disk (not on PATH): C:/Program Files/Microsoft Visual Studio/18/Insiders/VC/Tools/MSVC/14.51.36231/bin/Hostx64/x64/cl.exe
  - Core C++ compiler for native extension and tooling builds.
  - If only found on disk, launch Developer PowerShell or run vcvarsall to activate PATH.
- `OK` `runtime:cmake`: cmake version 4.3.4
  - Required by many C++/CUDA projects and local model runtimes.
- `OK` `runtime:ninja`: 1.13.0.git.kitware.jobserver-pipe-1
  - Recommended high-speed build backend for CMake projects.
- `OK` `runtime:msbuild`: found on disk (not on PATH): C:/Program Files/Microsoft Visual Studio/18/Insiders/MSBuild/Current/Bin/MSBuild.exe
  - Needed for some Visual Studio and native extension workflows.
  - If only found on disk, launch Developer PowerShell to expose msbuild on PATH.
- `OK` `runtime:glslc`: shaderc v2026.2 v2026.2
  - Shader compiler from Vulkan SDK.
- `OK` `runtime:vulkan_sdk`: C:\VulkanSDK\1.4.350.0
  - Expected when targeting Vulkan-native shader/tooling lanes.
- `OK` `runtime:vs_build_tools`: display=17.14.35 (June 2026) install=17.14.37411.7
  - Uses vswhere for discovery.
  - Detected Visual Studio-family instance: SQL Server Management Studio 22 (22.7.11919.86)
- `OK` `runtime:ssms`: 22.7.11919.86
  - SQL Server Management Studio detection via vswhere product Microsoft.VisualStudio.Product.Ssms.
- `OK` `module:llama_cpp`: import ok
- `OK` `module:pydantic`: import ok
- `OK` `module:numpy`: import ok
- `OK` `module:huggingface_hub`: import ok
- `OK` `module:requests`: import ok
- `OK` `module:mcp`: import ok
- `OK` `module:pydantic_settings`: import ok
- `OK` `module:transformers`: import ok
- `OK` `module:tokenizers`: import ok
- `OK` `module:safetensors`: import ok
- `OK` `module:datasets`: import ok
- `OK` `module:accelerate`: import ok
- `OK` `module:torch`: import ok
- `FAIL` `module:exllamav2`: missing module exllamav2
  - Optional legacy lane for local_refiner.py (v1).
- `OK` `model:qwen_14b`: 3 gguf file(s) in C:/Users/eldno/chthonic-archive/models/Qwen2.5-14B-Instruct-GGUF
- `OK` `model:gpt_oss_20b`: 1 gguf file(s) in C:/Users/eldno/chthonic-archive/models/GPT-OSS-20B-NEOPlus-Uncensored
- `OK` `model:llama_8b_exl2`: 1 safetensors file(s) in C:/Users/eldno/chthonic-archive/models/Llama-3.1-8B-Instruct-exl2-6.0bpw
- `OK` `artifact:daemon_report_json`: C:/Users/eldno/chthonic-archive/dumpster-dive/intake/overnight-daemon/20260430_023324/report.json
- `OK` `artifact:daemon_report_md`: C:/Users/eldno/chthonic-archive/dumpster-dive/intake/overnight-daemon/20260430_023324/report.md
- `OK` `artifact:l1_ore`: C:/Users/eldno/chthonic-archive/dumpster-dive/intake/overnight-intelligence/arch-2026-02-20T02-00-06/L1-ore.json
- `OK` `artifact:l1_summary`: C:/Users/eldno/chthonic-archive/dumpster-dive/intake/overnight-intelligence/arch-2026-02-20T02-00-06/L1-summary.md
- `FAIL` `artifact:latest_digest`: no ARCHAEOLOGY_DIGEST_*.md found
  - Digest absence is acceptable for L1-only runs.
- `OK` `log:scheduler`: C:/Users/eldno/chthonic-archive/dumpster-dive/intake/overnight-daemon/nightly-scheduled-2026-03-13_030005.log
  - No fatal markers in latest scheduler log.

## Recommendations
- Legacy ExLlamaV2 lane is not fully ready; keep v2 (llama-cpp) as primary.
- Safe to route nightly outputs into skill workflows (ingest/mailbox/orchestrator lanes).
