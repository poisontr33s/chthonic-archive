# VS Code Electron Hardener Report

- **Generated (UTC):** 2026-02-26T03:50:56.624571+00:00
- **Mode:** full
- **Dry Run:** False
- **Health Score:** 10/100
- **argv.json:** `C:\Users\erdno\AppData\Roaming\Code - Insiders\argv.json`

## Findings

| Component | Status | Message |
|---|---|---|
| GPU | CRITICAL | argv.json not found or unreadable |
| MEMORY | WARN | Cannot check memory flags: argv.json missing |
| USERDATA | CRITICAL | User data dir is 3270MB (20,765 files) |
| USERDATA | WARN | Found 31 log sessions in logs dir |
| SETTINGS | WARN | Failed to parse .vscode/settings.json |
| GPU | FIXED | Hardware acceleration not explicitly disabled |

### CRITICAL GPU: argv.json not found or unreadable
- **Detail:** VS Code cannot configure GPU without runtime flags file.
- **Action:** Create argv.json with GPU acceleration flags.

### CRITICAL USERDATA: User data dir is 3270MB (20,765 files)
- **Detail:** Excessive size indicates cache bloat or state corruption.
- **Action:** Clear CachedData and CachedExtensions directories.

### WARN USERDATA: Found 31 log sessions in logs dir
- **Detail:** Excessive log sessions can slow startup.
- **Action:** Clean old log sessions (keep last 5).

## Actions Taken

- Creating new argv.json at C:\Users\erdno\AppData\Roaming\Code - Insiders\argv.json
- argv.json: disable-hardware-acceleration: <unset> -> False
- argv.json: enable-gpu-rasterization: <unset> -> True
- argv.json: ignore-gpu-blocklist: <unset> -> True
- argv.json: js-flags: '' -> '--max-old-space-size=8192'
- Wrote patched argv.json to C:\Users\erdno\AppData\Roaming\Code - Insiders\argv.json

## Recommended Launch Command

```powershell
code-insiders --enable-gpu-rasterization --ignore-gpu-blocklist --force-gpu-mem-available-mb=4096 --js-flags="--max-old-space-size=8192"
```
