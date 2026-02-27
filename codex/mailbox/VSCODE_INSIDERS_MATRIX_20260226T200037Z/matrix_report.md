# VS Code Insiders Stability Matrix

- Generated (UTC): 2026-02-26T20:00:48.7241554Z
- Code path: `C:\Users\erdno\AppData\Local\Programs\Microsoft VS Code Insiders\bin\code-insiders.cmd`
- Temp user-data dir: `C:\Users\erdno\AppData\Local\Temp\vscode-insiders-clean-20260226T200037Z`

## Results

| Case | Exit | Renderer Crashes | GPU Errors | PTY Lines | Score/100 |
|---|---:|---:|---:|---:|---:|
| baseline | 0 | 0 | 11 | 4 | 78 |
| disable_gpu | 0 | 0 | 11 | 4 | 78 |
| disable_extensions | 0 | 0 | 11 | 4 | 78 |
| clean_safe_mode | 0 | 0 | 0 | 0 | 100 |

## Recommended Mode

- Case: `clean_safe_mode`
- Args: `--user-data-dir C:\Users\erdno\AppData\Local\Temp\vscode-insiders-clean-20260226T200037Z --disable-extensions --disable-gpu --status`
- Stability score: `100`

## Artifacts
- JSON: `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T200037Z\matrix_report.json`
- Bundle dir: `C:\Users\erdno\chthonic-archive\codex\mailbox\VSCODE_INSIDERS_MATRIX_20260226T200037Z`
