---
type: hardening-plan
generated_on_utc: 2026-02-26T03:30:00Z
scope: vscode-insiders-win11-stability
objective: Stabilize terminal/renderer crash lanes and establish a reproducible hardening pipeline for Chthonic Golden VS Code
---

# Chthonic Golden VS Code Hardening Plan

## Current Evidence Baseline
1. Terminal crash signature observed: `-1073741819` (`0xC0000005`, access violation).
2. `code-insiders --status` shows GPU software renderer path (`SwiftShader`) and repeated shared-image GPU errors.
3. External `pwsh` smoke tests pass (`-NoProfile` and profile mode), so the current fault is likely in VS Code/Electron renderer/pty host/extension interaction, not base PowerShell.

Reference artifacts:
- `codex/mailbox/VSCODE_TERMINAL_TRIAGE_20260226T033307Z/triage_report.md`
- `codex/mailbox/VSCODE_TERMINAL_TRIAGE_20260226T033307Z/triage_report.json`
- `codex/mailbox/VSCODE_INSIDERS_MATRIX_20260226T033328Z/matrix_report.md`
- `codex/mailbox/API_KEY_GAP_REPORT_20260226T032737Z.md`

Latest matrix outcome:
1. Baseline, `--disable-gpu`, and `--disable-extensions` all still show GPU error lines.
2. `clean_safe_mode` (`--user-data-dir <temp> --disable-extensions --disable-gpu`) scored best (`100/100`), indicating user-data and extension state are major stability factors.

Applied hardening in workspace settings:
1. `terminal.integrated.gpuAcceleration = "off"`
2. `terminal.integrated.logLevel = "trace"`
3. `terminal.integrated.defaultProfile.windows = "Pwsh (No Profile)"`

## Phase 1: Deterministic Repro Matrix (Crash Isolation)
1. Baseline run:
`code-insiders --status`
2. GPU-off run:
`code-insiders --disable-gpu --status`
3. Extensions-off run:
`code-insiders --disable-extensions --status`
4. Clean user-data run:
`code-insiders --user-data-dir "%TEMP%\\vscode-insiders-clean" --disable-extensions --disable-gpu --status`
5. Compare crash frequency and renderer/GPU log errors across all four runs.

Pass criteria:
- One mode runs without renderer crash and without recurring GPU shared-image errors.

## Phase 2: Terminal Stabilization Gate
1. Set terminal log level to trace (Developer + Terminal command palette actions).
2. Temporarily force terminal to `pwsh -NoProfile -NoLogo`.
3. Keep shell integration on, but disable custom startup hooks until stable.
4. Re-enable profile logic incrementally:
   - load minimal profile
   - load chthonic env hook
   - load additional aliases/functions
5. Stop at first regression and capture exact hook causing instability.

Pass criteria:
- 24h run window without terminal process crash dialog.

## Phase 3: Renderer/GPU Hardening
1. If GPU lane is unstable, keep software-safe mode in workspace:
   - `terminal.integrated.gpuAcceleration = "off"` (or keep disabled state validated by matrix).
2. Audit heavy extensions affecting terminal/renderer lifecycle.
3. Run extension bisect on crash window.
4. Pin stable Insiders build once a known-good commit hash is confirmed.

Pass criteria:
- No `CodeWindow: renderer process gone` entries in active log cycle.

## Phase 4: Crash Telemetry Pipeline (Always-On)
1. Run doctor tool after every crash:
`pwsh -NoProfile -File scripts/vscode_terminal_crash_doctor.ps1`
2. Store triage bundle in mailbox for cross-agent review.
3. Track trend fields:
   - renderer crash count
   - gpu error line count
   - pty/terminal crash hits
4. Escalate only if counts regress over 2 consecutive sessions.

Pass criteria:
- Trend is flat/down for 5 consecutive sessions.

## Phase 5: API Capability Expansion (Project Autonomy)
1. Run key gap report:
`pwsh -NoProfile -File scripts/api_key_gap_report.ps1`
2. Acquire missing keys from provider portals.
3. Populate local secret store only (`%USERPROFILE%\\.chthonic\\api_pool.json`), never repo files.
4. Validate with:
`pwsh -NoProfile -File .codex/skills/api-manager/scripts/api_manager.ps1 -Doctor`

Current missing keys:
1. `OPENAI_API_KEY`
2. `GEMINI_API_KEY`

## Tooling Added This Session
1. `scripts/vscode_terminal_crash_doctor.ps1`
   - smoke probes
   - Insiders log capture
   - `code-insiders --status` GPU/renderer extraction
   - JSON + MD triage bundle output
2. `scripts/api_key_gap_report.ps1`
   - no-secret key availability audit
   - acquisition URL mapping
   - JSON + MD outputs

## Operational Loop (KISS)
1. Crash happens -> run crash doctor.
2. Read triage report -> pick failing lane (GPU, extension, profile, pty).
3. Apply one change only.
4. Re-run matrix.
5. Commit only when regression count drops.
