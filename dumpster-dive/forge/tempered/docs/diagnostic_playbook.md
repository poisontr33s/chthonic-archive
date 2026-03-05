---
sid: FORGE_DIAGNOSTIC_PLAYBOOK_V1
title: Recovered Diagnostic Playbook
created: 2026-03-05T19:27:19+00:00
source_files: ["codex/mailbox/MISTRALRS_CUDA_BUILD_20260227T194707Z.err.log", "codex/mailbox/MISTRALRS_CUDA_BUILD_20260227T194707Z.out.log", "codex/mailbox/MISTRALRS_CUDA_BUILD_20260227T195207Z.err.log", "codex/mailbox/MISTRALRS_CUDA_BUILD_20260227T195207Z.out.log", "codex/mailbox/VS2026_ELEVATED_VALIDATE_20260217_054144.log", "codex/mailbox/VS2026_ELEVATED_VALIDATE_20260217_054157.log", "codex/mailbox/VS2026_ELEVATED_VALIDATE_20260217_231023.log", "codex/mailbox/VS2026_ELEVATED_VALIDATE_20260217_231058.log", "codex/mailbox/VS2026_ELEVATED_VALIDATE_20260217_231535.log", "codex/mailbox/VS2026_ELEVATED_VALIDATE_20260217_235550.log", "codex/mailbox/VS2026_ELEVATED_VALIDATE_20260217_235653.log", "codex/mailbox/VS2026_ELEVATED_VALIDATE_20260218_000139.log", "codex/mailbox/VS2026_ELEVATED_VALIDATE_20260218_001043.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033112Z/matrix_baseline_status.err.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033112Z/matrix_baseline_status.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033112Z/matrix_clean_safe_mode_status.err.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033112Z/matrix_clean_safe_mode_status.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033112Z/matrix_disable_extensions_status.err.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033112Z/matrix_disable_extensions_status.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033112Z/matrix_disable_gpu_status.err.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033112Z/matrix_disable_gpu_status.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033146Z/matrix_baseline_status.err.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033146Z/matrix_baseline_status.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033146Z/matrix_clean_safe_mode_status.err.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033146Z/matrix_clean_safe_mode_status.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033146Z/matrix_disable_extensions_status.err.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033146Z/matrix_disable_extensions_status.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033146Z/matrix_disable_gpu_status.err.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033146Z/matrix_disable_gpu_status.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033328Z/matrix_baseline_status.err.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033328Z/matrix_baseline_status.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033328Z/matrix_clean_safe_mode_status.err.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033328Z/matrix_clean_safe_mode_status.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033328Z/matrix_disable_extensions_status.err.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033328Z/matrix_disable_extensions_status.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033328Z/matrix_disable_gpu_status.err.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033328Z/matrix_disable_gpu_status.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033855Z/matrix_baseline_status.err.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033855Z/matrix_baseline_status.log", "codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033855Z/matrix_clean_safe_mode_status.err.log", "... and 292 more"]
pathway: log -> diagnostic pattern extraction -> playbook
kept: Repeated failure signatures, environment markers, and toolchain versions.
discarded: Redundant per-run noise once the repeated signature is captured.
---
# Recovered Diagnostic Playbook

## Top Failure Signatures

- `29x` Version:          Code - Insiders 1.110.0-insider (7e5adbd392329afffaa38da9e47df976a05e2f2c, 2026-02-25T17:04:31.230Z)
- `29x` OS Version:       Windows_NT x64 10.0.26200
- `29x` GPU0:                                   VENDOR= 0xffff \[Google Inc. (Google)\], DEVICE=0xffff [ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero) (0x0000C0DE)), SwiftShader d
- `29x` Machine model version:
- `20x` \[20212:0226/041104.328:ERROR:gpu\command_buffer\service\shared_image\shared_image_manager.cc:526\] : SharedImageManager::ProduceMemory: Trying to Produce a Memory representation fro
- `14x` 2026-02-26 02:46:09.839 \[warning\] Shell integration failed to add capabilities within 10 seconds []
- `9x` \[39328:0226/205722.607:ERROR:gpu\command_buffer\service\shared_image\shared_image_manager.cc:526\] : SharedImageManager::ProduceMemory: Trying to Produce a Memory representation fro
- `7x` 2026-02-26 02:31:38.454 \[error\] vscode-file: Refused to load resource c:\Users\erdno\AppData\Local\Programs\Microsoft VS Code Insiders\4741aa0afd\resources\app\extensions\theme-set
- `7x` 2026-02-26 03:02:05.039 \[error\] CodeWindow: renderer process gone (reason: crashed, code: -2147483645)
- `7x` 2026-02-26 03:50:06.777 \[error\] CodeWindow: renderer process gone (reason: crashed, code: -2147483645)
- `7x` 2026-02-26 02:46:09.813 \[warning\] Shell integration failed to add capabilities within 10 seconds []
- `7x` 2026-02-26 02:46:09.821 \[warning\] Shell integration failed to add capabilities within 10 seconds []
- `7x` 2026-02-26 02:46:09.827 \[warning\] Shell integration failed to add capabilities within 10 seconds []
- `7x` 2026-02-26 03:02:05.059 \[error\] An error occurred when disposing the subscriptions for extension 'GitHub.copilot-chat':
- `7x` 2026-02-26 03:02:05.059 \[error\] Error: Channel has been closed
- `7x` 2026-02-26 03:02:05.068 \[error\] Error: Channel has been closed
- `7x` 2026-02-26 02:31:40.191 \[error\] \[Extension Host\] (node:52928) \[DEP0040\] DeprecationWarning: The `punycode` module is deprecated. Please use a userland alternative instead.
- `7x` 2026-02-26 02:31:40.191 \[error\] \[Extension Host\] (node:52928) ExperimentalWarning: SQLite is an experimental feature and might change at any time
- `7x` 2026-02-26 02:46:00.723 \[error\] \[441\] potential listener LEAK detected, having 175 listeners already. MOST frequent listener (1):: Error
- `7x` 2026-02-26 02:46:00.726 \[error\] \[1b9\] potential listener LEAK detected, having 175 listeners already. MOST frequent listener (1):: Error

## Recovery Notes

- Renderer crashes and shared image memory failures cluster around VS Code Insiders GPU and telemetry lanes.
- Shell integration capability timeouts recur across the terminal triage captures.
- CUDA build logs preserve compiler and NVCC versions; the short empty siblings can be archived after extraction by proposal.
