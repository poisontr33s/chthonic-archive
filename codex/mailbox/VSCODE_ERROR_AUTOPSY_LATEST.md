# VS Code Error Autopsy Report

- **Generated (UTC):** 2026-02-26T19:59:41.851955+00:00
- **Stability Score:** 0/100
- **Total Lines Scanned:** 37,614
- **Total Errors (deduped):** 142
- **Duplicates Collapsed:** 1219
- **Log Sources:** 62

## Severity Summary

| Severity | Count |
|---|---:|
| CRITICAL | 8 |
| HIGH | 51 |
| MEDIUM | 28 |
| LOW | 27 |
| INFO | 28 |

## Category Summary

| Category | Count |
|---|---:|
| GPU | 56 |
| EXTHOST | 56 |
| MEMORY | 26 |
| PTY | 2 |
| NETWORK | 1 |
| UI | 1 |

## Top Remediations (Priority Order)

1. [CRITICAL] GPU/renderer_process_gone: Collect crash dump from %TEMP%/Electron Crashes. Disable GPU acceleration as workaround. Report to VS Code issues.
2. [HIGH] GPU/shared_image_manager_produce_memory: For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.
3. [HIGH] MEMORY/listener_leak: Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.
4. [HIGH] UI/type_error_null_ref: Report to VS Code issues with full stack trace. May be triggered by specific chat/editor operations.
5. [MEDIUM] GPU/swiftshader_active: If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.
6. [MEDIUM] PTY/shell_integration_timeout: Use -NoProfile for PowerShell terminals during triage. Increase terminal integration timeout if available.
7. [MEDIUM] EXTHOST/chat_participant_not_declared: Update extension or wait for publisher fix. Disable the extension if it causes instability.
8. [LOW] EXTHOST/deprecated_module: Informational only. Will break in future Node.js versions.
9. [LOW] NETWORK/embeddings_cdn_404: Self-resolving on next Insiders update. Informational only.
10. [INFO] EXTHOST/experimental_feature_warning: Informational. Monitor for breakage on updates.

## Error Details

### [CRITICAL] GPU/renderer_process_gone
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032245Z\insiders_logs\main.log` L5
- **Match:** `renderer process gone`
- **Root Cause:** Electron renderer process crashed. Window becomes unresponsive.
- **Remediation:** Collect crash dump from %TEMP%/Electron Crashes. Disable GPU acceleration as workaround. Report to VS Code issues.

### [CRITICAL] GPU/renderer_process_gone
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032320Z\insiders_logs\main.log` L5
- **Match:** `renderer process gone`
- **Root Cause:** Electron renderer process crashed. Window becomes unresponsive.
- **Remediation:** Collect crash dump from %TEMP%/Electron Crashes. Disable GPU acceleration as workaround. Report to VS Code issues.

### [CRITICAL] GPU/renderer_process_gone
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032622Z\insiders_logs\main.log` L5
- **Match:** `renderer process gone`
- **Root Cause:** Electron renderer process crashed. Window becomes unresponsive.
- **Remediation:** Collect crash dump from %TEMP%/Electron Crashes. Disable GPU acceleration as workaround. Report to VS Code issues.

### [CRITICAL] GPU/renderer_process_gone
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033307Z\insiders_logs\main.log` L5
- **Match:** `renderer process gone`
- **Root Cause:** Electron renderer process crashed. Window becomes unresponsive.
- **Remediation:** Collect crash dump from %TEMP%/Electron Crashes. Disable GPU acceleration as workaround. Report to VS Code issues.

### [CRITICAL] GPU/renderer_process_gone
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033834Z\insiders_logs\main.log` L5
- **Match:** `renderer process gone`
- **Root Cause:** Electron renderer process crashed. Window becomes unresponsive.
- **Remediation:** Collect crash dump from %TEMP%/Electron Crashes. Disable GPU acceleration as workaround. Report to VS Code issues.

### [CRITICAL] GPU/renderer_process_gone
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034024Z\insiders_logs\main.log` L5
- **Match:** `renderer process gone`
- **Root Cause:** Electron renderer process crashed. Window becomes unresponsive.
- **Remediation:** Collect crash dump from %TEMP%/Electron Crashes. Disable GPU acceleration as workaround. Report to VS Code issues.

### [CRITICAL] GPU/renderer_process_gone
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034240Z\insiders_logs\main.log` L5
- **Match:** `renderer process gone`
- **Root Cause:** Electron renderer process crashed. Window becomes unresponsive.
- **Remediation:** Collect crash dump from %TEMP%/Electron Crashes. Disable GPU acceleration as workaround. Report to VS Code issues.

### [CRITICAL] GPU/renderer_process_gone
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\main.log` L4
- **Match:** `renderer process gone`
- **Root Cause:** Electron renderer process crashed. Window becomes unresponsive.
- **Remediation:** Collect crash dump from %TEMP%/Electron Crashes. Disable GPU acceleration as workaround. Report to VS Code issues.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033112Z\matrix_baseline_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033112Z\matrix_disable_extensions_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033112Z\matrix_disable_gpu_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033146Z\matrix_baseline_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033146Z\matrix_disable_extensions_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033146Z\matrix_disable_gpu_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033328Z\matrix_baseline_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033328Z\matrix_disable_extensions_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033328Z\matrix_disable_gpu_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033855Z\matrix_baseline_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033855Z\matrix_disable_extensions_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033855Z\matrix_disable_gpu_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T195738Z\matrix_baseline_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T195738Z\matrix_disable_extensions_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T195738Z\matrix_disable_gpu_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032245Z\insiders_logs\window1\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032245Z\insiders_logs\window2\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032245Z\insiders_logs\window3\renderer.log` L11
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032320Z\insiders_logs\window1\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032320Z\insiders_logs\window2\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032320Z\insiders_logs\window3\renderer.log` L11
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032438Z\code_insiders_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032459Z\code_insiders_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032547Z\code_insiders_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032622Z\code_insiders_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032622Z\insiders_logs\window1\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032622Z\insiders_logs\window2\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032622Z\insiders_logs\window3\renderer.log` L11
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033307Z\code_insiders_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033307Z\insiders_logs\window1\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033307Z\insiders_logs\window2\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033307Z\insiders_logs\window3\renderer.log` L11
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033834Z\code_insiders_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033834Z\insiders_logs\window1\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033834Z\insiders_logs\window2\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033834Z\insiders_logs\window3\renderer.log` L11
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034024Z\code_insiders_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034024Z\insiders_logs\window1\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034024Z\insiders_logs\window2\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034024Z\insiders_logs\window3\renderer.log` L11
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034240Z\code_insiders_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034240Z\insiders_logs\window1\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034240Z\insiders_logs\window2\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034240Z\insiders_logs\window3\renderer.log` L11
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\code_insiders_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window1\renderer.log` L13
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window2\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window3\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window4\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] UI/type_error_null_ref
- **Source:** `C:\Users\erdno\chthonic-archive\debugging_data\Window.log` L23
- **Match:** `TypeError: Cannot read properties of undefined`
- **Root Cause:** Null reference in UI renderer. Component accessed before initialization.
- **Remediation:** Report to VS Code issues with full stack trace. May be triggered by specific chat/editor operations.

### [HIGH] MEMORY/listener_leak
- **Source:** `C:\Users\erdno\chthonic-archive\debugging_data\Window.log` L65
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033112Z\matrix_baseline_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033112Z\matrix_disable_extensions_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033112Z\matrix_disable_gpu_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033146Z\matrix_baseline_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033146Z\matrix_disable_extensions_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033146Z\matrix_disable_gpu_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033328Z\matrix_baseline_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033328Z\matrix_disable_extensions_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033328Z\matrix_disable_gpu_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033855Z\matrix_baseline_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033855Z\matrix_disable_extensions_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033855Z\matrix_disable_gpu_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T195738Z\matrix_baseline_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T195738Z\matrix_disable_extensions_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T195738Z\matrix_disable_gpu_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032438Z\code_insiders_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032459Z\code_insiders_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032547Z\code_insiders_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032622Z\code_insiders_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033307Z\code_insiders_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033834Z\code_insiders_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034024Z\code_insiders_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034240Z\code_insiders_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\code_insiders_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] PTY/shell_integration_timeout
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\terminal.log` L16
- **Match:** `_waitForShellIntegration: Timed out 5000ms`
- **Root Cause:** Shell integration handshake exceeded timeout. First terminal after startup is slow due to profile loading.
- **Remediation:** Use -NoProfile for PowerShell terminals during triage. Increase terminal integration timeout if available.

### [MEDIUM] EXTHOST/chat_participant_not_declared
- **Source:** `C:\Users\erdno\chthonic-archive\debugging_data\Extension_Host_data.log` L17
- **Match:** `chatParticipant must be declared in package.json: claude-code`
- **Root Cause:** Extension tries to register a chat participant not declared in its package.json. Typically claude-code or similar AI extensions with incomplete manifest.
- **Remediation:** Update extension or wait for publisher fix. Disable the extension if it causes instability.

### [MEDIUM] PTY/shell_integration_timeout
- **Source:** `C:\Users\erdno\chthonic-archive\debugging_data\Extension_Host_data.log` L58
- **Match:** `_waitForShellIntegration: Timed out 5000ms`
- **Root Cause:** Shell integration handshake exceeded timeout. First terminal after startup is slow due to profile loading.
- **Remediation:** Use -NoProfile for PowerShell terminals during triage. Increase terminal integration timeout if available.

### [MEDIUM] EXTHOST/chat_participant_not_declared
- **Source:** `C:\Users\erdno\chthonic-archive\debugging_data\Window.log` L11
- **Match:** `chatParticipant must be declared in package.json: claude-code`
- **Root Cause:** Extension tries to register a chat participant not declared in its package.json. Typically claude-code or similar AI extensions with incomplete manifest.
- **Remediation:** Update extension or wait for publisher fix. Disable the extension if it causes instability.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032245Z\insiders_logs\window1\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032245Z\insiders_logs\window2\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032245Z\insiders_logs\window3\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032320Z\insiders_logs\window1\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032320Z\insiders_logs\window2\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032320Z\insiders_logs\window3\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032622Z\insiders_logs\window1\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032622Z\insiders_logs\window2\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032622Z\insiders_logs\window3\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033307Z\insiders_logs\window1\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033307Z\insiders_logs\window2\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033307Z\insiders_logs\window3\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033834Z\insiders_logs\window1\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033834Z\insiders_logs\window2\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033834Z\insiders_logs\window3\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034024Z\insiders_logs\window1\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034024Z\insiders_logs\window2\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034024Z\insiders_logs\window3\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034240Z\insiders_logs\window1\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034240Z\insiders_logs\window2\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034240Z\insiders_logs\window3\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window1\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window2\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window3\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window4\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `C:\Users\erdno\chthonic-archive\debugging_data\Window.log` L4
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] NETWORK/embeddings_cdn_404
- **Source:** `C:\Users\erdno\chthonic-archive\debugging_data\Window.log` L19
- **Match:** `Failed to fetch remote embeddings cache`
- **Root Cause:** Embeddings CDN returned 404. Version mismatch between client and CDN.
- **Remediation:** Self-resolving on next Insiders update. Informational only.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032245Z\insiders_logs\window1\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032245Z\insiders_logs\window2\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032245Z\insiders_logs\window3\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032320Z\insiders_logs\window1\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032320Z\insiders_logs\window2\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032320Z\insiders_logs\window3\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032622Z\insiders_logs\window1\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032622Z\insiders_logs\window2\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032622Z\insiders_logs\window3\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033307Z\insiders_logs\window1\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033307Z\insiders_logs\window2\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033307Z\insiders_logs\window3\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033834Z\insiders_logs\window1\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033834Z\insiders_logs\window2\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033834Z\insiders_logs\window3\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034024Z\insiders_logs\window1\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034024Z\insiders_logs\window2\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034024Z\insiders_logs\window3\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034240Z\insiders_logs\window1\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034240Z\insiders_logs\window2\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034240Z\insiders_logs\window3\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window1\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window2\exthost\exthost.log` L107
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window2\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window3\exthost\exthost.log` L99
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window3\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window4\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `C:\Users\erdno\chthonic-archive\debugging_data\Window.log` L6
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

## Log Sources Scanned

- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033112Z\matrix_baseline_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033112Z\matrix_disable_extensions_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033112Z\matrix_disable_gpu_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033146Z\matrix_baseline_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033146Z\matrix_disable_extensions_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033146Z\matrix_disable_gpu_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033328Z\matrix_baseline_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033328Z\matrix_disable_extensions_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033328Z\matrix_disable_gpu_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033855Z\matrix_baseline_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033855Z\matrix_disable_extensions_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T033855Z\matrix_disable_gpu_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T195738Z\matrix_baseline_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T195738Z\matrix_disable_extensions_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T195738Z\matrix_disable_gpu_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032245Z\insiders_logs\main.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032245Z\insiders_logs\window1\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032245Z\insiders_logs\window2\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032245Z\insiders_logs\window3\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032320Z\insiders_logs\main.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032320Z\insiders_logs\window1\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032320Z\insiders_logs\window2\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032320Z\insiders_logs\window3\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032438Z\code_insiders_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032459Z\code_insiders_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032547Z\code_insiders_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032622Z\code_insiders_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032622Z\insiders_logs\main.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032622Z\insiders_logs\window1\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032622Z\insiders_logs\window2\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032622Z\insiders_logs\window3\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033307Z\code_insiders_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033307Z\insiders_logs\main.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033307Z\insiders_logs\window1\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033307Z\insiders_logs\window2\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033307Z\insiders_logs\window3\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033834Z\code_insiders_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033834Z\insiders_logs\main.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033834Z\insiders_logs\window1\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033834Z\insiders_logs\window2\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T033834Z\insiders_logs\window3\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034024Z\code_insiders_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034024Z\insiders_logs\main.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034024Z\insiders_logs\window1\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034024Z\insiders_logs\window2\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034024Z\insiders_logs\window3\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034240Z\code_insiders_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034240Z\insiders_logs\main.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034240Z\insiders_logs\window1\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034240Z\insiders_logs\window2\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T034240Z\insiders_logs\window3\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\code_insiders_status.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\main.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\terminal.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window1\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window2\exthost\exthost.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window2\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window3\exthost\exthost.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window3\renderer.log`
- `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T195738Z\insiders_logs\window4\renderer.log`
- `C:\Users\erdno\chthonic-archive\debugging_data\Extension_Host_data.log`
- `C:\Users\erdno\chthonic-archive\debugging_data\Window.log`
