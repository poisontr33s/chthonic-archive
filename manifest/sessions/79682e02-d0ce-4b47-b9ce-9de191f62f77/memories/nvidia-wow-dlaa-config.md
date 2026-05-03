# NVIDIA WoW DLAA Configuration Session

## What Was Done
1. Read `C:\Users\eldno\AppData\Local\NVIDIA Corporation\NVIDIA app\NvBackend\ApplicationStorage.json`
2. Found WoW entry: "World of Warcraft: Dragonflight", LocalId 348736599
3. Install: `C:\Program Files (x86)\World of Warcraft\`, Exe: `_retail_\Wow.exe`
4. Flipped all 5 override flags from true → false:
   - Disable_FG_Override, Disable_RR_Override, Disable_SR_Override
   - Disable_RR_Model_Override, Disable_SR_Model_Override
5. Set file to read-only
6. Backup at: `ApplicationStorage.json.bak.2026-04-17_200344`

## NVIDIA App Global Settings (confirmed from screenshots)
- DLSS-overstyring - Super Resolution-modus: **DLAA (100%)**
- DLSS-overstyring - Forhåndsinnstillinger for modeller: Tilpasset
  - Bildegenerering: Bruk innstillingen for 3D-programvare
  - Super Resolution: Anbefalt*
  - Strålerekonstruksjon: Anbefalt*
- Jevn og myk bevegelse: På
- CUDA GPU: NVIDIA GeForce RTX 4090
- Maks bildefrekvens: 120 FPS

## Per-Game WoW Profile
- Per-game overrides showed "Støttes ikke" (Not supported) for all 3 DLSS override lines
- Global override was used instead

## In-Game Observations
- FPS 121, GPU 21-25%, CPU 5-6%, LAT 24.5-29.4ms
- No SR OVR: DLAA indicator visible in overlay
- User already has SSGSAA x8 / TRSSGSAA x8 in NVIDIA Profile Inspector
- Those may conflict with or override DLAA

## Current Task
- User wants to read WoW's NVIDIA Profile Inspector settings to validate what's actually active
- NPI is at: `C:\Users\eldno\Downloads\nvidiaProfileInspector\nvidiaProfileInspector.exe`
- NPI GUI-only (single exe, 592KB), no CLI export confirmed
- Tried registry paths (NVTweak, NGXCore) and nvidia-smi — output truncated/empty
- NPI `-export` flag attempted — no output file created, CLI export not supported in this version
- Registry/AppData DRS file search — PS output truncated multiple times
- nvidia-smi confirmed: RTX 4090, driver 596.21
- CONCLUSION: NPI is GUI-only for this version. Cannot programmatically read WoW's per-app NPI profile.
- RECOMMENDED: Ask user to open NPI, select WoW profile, screenshot the AA section (specifically: AA Mode, AA Setting, AA Transparency, FXAA, DLSS settings).
- Key NPI IDs for WoW AA:
  - 0x10F9DC83 = Antialiasing - Mode
  - 0x107D639D = Antialiasing - Setting
  - 0x00A06946 = Antialiasing - Transparency Supersampling (this is SSGSAA/TRSSGSAA)
  - 0x10D773D2 = Antialiasing - Behavior Flags
  - DLSS-related: 0x10F9DC81, 0x10F9DC85 (if present)
- WoW profile name in NPI is likely "World of Warcraft" or keyed by executable path
- User has SSGSAA x8 and TRSSGSAA x8 already set — these are the key settings to validate
- Key NPI settings to look for: 0x00A06946 (AA Transparency Supersampling), 0x10F9DC83 (AA Mode), 0x1056F985 (DLSS flags)
- WoW install: C:\Program Files (x86)\World of Warcraft\_retail_\Wow.exe
- Driver: 596.21 (DLSS 4.5), installed 2026-04-17

## Revert Command
```powershell
Set-ItemProperty "C:\Users\eldno\AppData\Local\NVIDIA Corporation\NVIDIA app\NvBackend\ApplicationStorage.json" -Name IsReadOnly -Value $false
Copy-Item "C:\Users\eldno\AppData\Local\NVIDIA Corporation\NVIDIA app\NvBackend\ApplicationStorage.json.bak.2026-04-17_200344" "C:\Users\eldno\AppData\Local\NVIDIA Corporation\NVIDIA app\NvBackend\ApplicationStorage.json" -Force
```
