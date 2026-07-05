# VS Code Terminal Crash Doctor Report

- Generated (UTC): 2026-02-26T03:25:47.3675691Z
- Crash signature: `-1073741819` (`0xC0000005`, access violation)
- pwsh: `C:\Program Files\PowerShell\7\pwsh.exe` version `7.5.4`

## Probe Matrix

| Probe | Exit | Hex | Elapsed ms |
|---|---:|---|---:|
| no_profile | 0 | 0x00000000 | 1022 |
| with_profile_repo | 0 | 0x00000000 | 1030 |
| with_profile_temp | 0 | 0x00000000 | 1010 |

## Findings
- Smoke tests passed. If VS Code still crashes, focus on VS Code terminal host/extension/GPU path with trace logs.

## Logs
- Source log dir: `C:\Users\eldno\AppData\Roaming\Code - Insiders\logs\20260226T042503`
- Copied log files: `0`
- Crash-pattern hits: `0`

## Code Status
- code-insiders --status exit: `0`
- Renderer crash lines: `0`
- GPU error lines: `15`

## Next Steps
1. Inside VS Code Insiders, run: Developer: Set Log Level... -> Trace.
1. Inside VS Code Insiders, run: Terminal: Set Log Level... -> Trace.
1. Set terminal profile to no-profile during stabilization: args ["-NoProfile", "-NoLogo"].
1. Start Insiders once with --disable-gpu and compare crash frequency.
1. Start Insiders once with --disable-extensions and compare crash frequency.
1. If no-profile is stable, re-enable profile incrementally and isolate crashing hook.

## Artifacts
- JSON: `C:\Users\eldno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032547Z\triage_report.json`
- API doctor log: `C:\Users\eldno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032547Z\api_doctor.log`
- Bundle dir: `C:\Users\eldno\chthonic-archive\codex\mailbox\VSCODE_TERMINAL_TRIAGE_20260226T032547Z`

