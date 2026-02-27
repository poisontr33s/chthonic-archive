# VS Code Error Autopsy Report

- **Generated (UTC):** 2026-02-26T20:04:33.262749+00:00
- **Stability Score:** 0/100
- **Total Lines Scanned:** 3,576
- **Total Errors (deduped):** 22
- **Duplicates Collapsed:** 124
- **Log Sources:** 11

## Severity Summary

| Severity | Count |
|---|---:|
| CRITICAL | 1 |
| HIGH | 7 |
| MEDIUM | 4 |
| LOW | 4 |
| INFO | 6 |

## Category Summary

| Category | Count |
|---|---:|
| EXTHOST | 10 |
| GPU | 7 |
| MEMORY | 4 |
| PTY | 1 |

## Top Remediations (Priority Order)

1. [CRITICAL] GPU/renderer_process_gone: Collect crash dump from %TEMP%/Electron Crashes. Disable GPU acceleration as workaround. Report to VS Code issues.
2. [HIGH] GPU/shared_image_manager_produce_memory: For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.
3. [HIGH] MEMORY/listener_leak: Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.
4. [MEDIUM] GPU/swiftshader_active: If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.
5. [MEDIUM] PTY/shell_integration_timeout: Use -NoProfile for PowerShell terminals during triage. Increase terminal integration timeout if available.
6. [LOW] EXTHOST/deprecated_module: Informational only. Will break in future Node.js versions.
7. [INFO] EXTHOST/experimental_feature_warning: Informational. Monitor for breakage on updates.

## Error Details

### [CRITICAL] GPU/renderer_process_gone
- **Source:** `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\main.log` L4
- **Match:** `renderer process gone`
- **Root Cause:** Electron renderer process crashed. Window becomes unresponsive.
- **Remediation:** Collect crash dump from %TEMP%/Electron Crashes. Disable GPU acceleration as workaround. Report to VS Code issues.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T200037Z\matrix_baseline_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T200037Z\matrix_disable_extensions_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] GPU/shared_image_manager_produce_memory
- **Source:** `codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T200037Z\matrix_disable_gpu_status.log` L28
- **Match:** `SharedImageManager::ProduceMemory: Trying to Produce a Memory representation from a non-existent mailbox`
- **Root Cause:** Chromium GPU command buffer referencing destroyed shared image mailbox. Indicates GPU process instability or software rendering fallback.
- **Remediation:** For crash containment, first run with --disable-gpu and terminal GPU off. After stability returns, test hardware acceleration with updated GPU drivers.

### [HIGH] MEMORY/listener_leak
- **Source:** `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window1\renderer.log` L13
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window2\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window3\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [HIGH] MEMORY/listener_leak
- **Source:** `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window4\renderer.log` L8
- **Match:** `potential listener LEAK detected, having 175 listeners`
- **Root Cause:** Event emitter accumulating listeners without cleanup. Causes memory growth and eventual slowdown.
- **Remediation:** Identify the emitter source from stack trace. If VS Code internal, report upstream. If extension, file bug.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T200037Z\matrix_baseline_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T200037Z\matrix_disable_extensions_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] GPU/swiftshader_active
- **Source:** `codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T200037Z\matrix_disable_gpu_status.log` L10
- **Match:** `SwiftShader`
- **Root Cause:** Software Vulkan renderer active instead of hardware GPU. Performance degradation and increased crash risk.
- **Remediation:** If crashes persist, keep software-safe mode (--disable-gpu) until stable. Then validate hardware path via driver updates and controlled re-enable.

### [MEDIUM] PTY/shell_integration_timeout
- **Source:** `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\terminal.log` L16
- **Match:** `_waitForShellIntegration: Timed out 5000ms`
- **Root Cause:** Shell integration handshake exceeded timeout. First terminal after startup is slow due to profile loading.
- **Remediation:** Use -NoProfile for PowerShell terminals during triage. Increase terminal integration timeout if available.

### [LOW] EXTHOST/deprecated_module
- **Source:** `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window1\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window2\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window3\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [LOW] EXTHOST/deprecated_module
- **Source:** `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window4\renderer.log` L3
- **Match:** `DeprecationWarning: The `punycode`
- **Root Cause:** Node.js deprecated module used by extension or VS Code itself.
- **Remediation:** Informational only. Will break in future Node.js versions.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window1\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window2\exthost\exthost.log` L107
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window2\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window3\exthost\exthost.log` L99
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window3\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

### [INFO] EXTHOST/experimental_feature_warning
- **Source:** `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window4\renderer.log` L5
- **Match:** `experimental feature`
- **Root Cause:** Extension using experimental API/feature.
- **Remediation:** Informational. Monitor for breakage on updates.

## Log Sources Scanned

- `codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T200037Z\matrix_baseline_status.log`
- `codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T200037Z\matrix_disable_extensions_status.log`
- `codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T200037Z\matrix_disable_gpu_status.log`
- `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\main.log`
- `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\terminal.log`
- `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window1\renderer.log`
- `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window2\exthost\exthost.log`
- `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window2\renderer.log`
- `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window3\exthost\exthost.log`
- `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window3\renderer.log`
- `codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T200225Z\insiders_logs\window4\renderer.log`
