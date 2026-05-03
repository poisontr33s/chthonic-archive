# WoW Graphics Enhancement Session — 2026-04-18

## Baseline Snapshot
- Exported to: `$env:TEMP\wow_profile_baseline_2026-04-18.json`
- 50 DRS settings captured for WoW profile "World Of Warcraft"
- Key current values:
  - NIS 2.0 Enable [0x00ABAC21] = 0 (DISABLED)
  - DLAA Override [0x10E41DF4] = 1 (enabled, but WoW never calls NGX)
  - DLSSG Override [0x10308298] = 1 (enabled, same dead end)
  - TrueHDR [0x00DD48FB] = 1 (enabled)
  - DeepDVC Enable [0x00980880] = 0 (disabled)
  - DeepDVC Intensity [0x00ABAB22] = 50
  - DeepDVC Saturation [0x00ABAB13] = 50
  - AA Mode [0x107EFC5B] = 1 (Override)
  - AA Setting [0x10D773D2] = 0x17
  - AO [0x00667329] = 3
  - FRL: Whisper Mode App FPS [0x10115C8B] = 60 (0x3C)
  - TrueHDR Contrast [0x00DD48FE] = 100
  - TrueHDR Saturation [0x00DD48FF] = 100
  - TrueHDR MiddleGrey [0x00DD48FD] = 50
  - TrueHDR PeakBrightness [0x00DD48FC] = 417 (0x1A1)

## NPI Versions
- OLD: C:\Users\eldno\Downloads\nvidiaProfileInspector\ — single exe (592KB), v2.3.0.13, portable, ZERO user state → SAFE TO DELETE
- NEW: C:\Users\eldno\Downloads\nvidiaProfileInspector-v3.0.1.12\ — exe (975KB) + Reference.xml (898KB) + .config + .pdb, v3.0.1.12

## CLI Tool
- scripts/nvidia_drs_tool.ps1 — 649 lines, 33783 bytes
- All 3 bugs fixed (field order, delegate sigs, function IDs)
- Read/Write/Watch/Export/Snapshot/Effective all verified working
- PENDING UPDATE: Integrate NPI v3.0.1.12 Reference.xml for setting name lookups
  - Path: C:\Users\eldno\Downloads\nvidiaProfileInspector-v3.0.1.12\Reference.xml
  - Schema: CustomSettingNames > Settings > CustomSetting
  - Fields per entry: HexSettingID, UserfriendlyName, Description, GroupName, DataType, SettingValues
  - 812 total settings defined
  - Add -NpiRef param pointing to Reference.xml, load as name+value lookup dictionary
  - Enriches all output with human-readable names for the 50+ unnamed hex IDs
  - Also add -ResetProfile to wipe all overrides from a profile (needed after NPI/NVCP global reset)
  - Also add -Apply / -Preset to batch-apply a saved JSON snapshot

## User Reset Event (2026-04-18)
- User reset NVIDIA settings in NPI and NVCP (both global and WoW profile)
- ALL DRS overrides were wiped: NIS 2.0, DLAA, DLSS-FG, TrueHDR, DeepDVC, etc.
- Need to re-apply from baseline JSON: $env:TEMP\wow_profile_baseline_2026-04-18.json

## NIS 2.0 vs FSR 1.0 CAS — Technical Comparison

### NIS (NVIDIA Image Scaling) — What's in Your Driver
- SDK version on GitHub: v1.0.3 (Aug 2022, latest release)
- Algorithm: 6-tap scaling filter + 4 directional scaling + adaptive sharpening filters
- Two modes: NVScaler (upscale+sharpen) and NVSharpen (sharpen only, NO upscaling)
- Pipeline placement: MUST be applied post-tonemapping (after gamma correction)
- Color space: LDR [0,1], HDR PQ [0,1], HDR Linear [0,12.5]
- Cross-platform: works on ANY GPU (NVIDIA, AMD, Intel)
- "NIS 2.0" in DRS = driver-level NVSharpen applied after game renders
- DRS settings: Enable [0x00ABAC21], SharpValue (currently 0x0B = 11)
- When enabled at native res: acts as sharpening-only pass (no upscaling)
- OPERATES AT: Driver compositor level, AFTER game output

### FSR 1.0 CAS (WoW's Built-in) — What's in the Engine
- Algorithm: Contrast Adaptive Sharpening — adjusts sharpening per-pixel
- Sharpens less where already sharp, more where detail is lacking
- Designed to counteract TAA blur specifically
- Two passes in FSR 1: EASU (Edge-Adaptive Spatial Upsampling) + RCAS (Robust CAS)
- At native res with ResampleAlwaysSharpen=1: ONLY the RCAS pass runs (sharpening, no upscaling)
- OPERATES AT: Inside the engine pipeline, before final UI compositing
- CVar controls: ResampleAlwaysSharpen "1", ResampleSharpness "0" (=max), RenderScale "1"

### Stacking Analysis — DO THEY CONFLICT?
**NO.** They operate at completely different pipeline stages:
1. WoW renders frame → FSR 1.0 RCAS sharpens inside engine (if CVar enabled)
2. Frame leaves game → Driver compositor → NIS 2.0 NVSharpen applies (if DRS enabled)

**Risk of over-sharpening:** Yes, if both are cranked. Mitigation:
- FSR 1.0 CAS is adaptive — won't over-sharpen already-sharp areas
- NIS 2.0 SharpValue at 11 (out of 100?) is conservative
- Start with one, add the other, compare visually

### Verdict
They are COMPLEMENTARY, not competitive. FSR 1.0 CAS fixes TAA blur in-engine.
NIS 2.0 adds a second pass at the driver level. Both are spatial/single-frame.
Neither is temporal. Neither creates new detail — they enhance what exists.

## Action Plan — Execution Log
1. ✅ Remove old NPI v2.3.0.13 — DELETED (single exe, no state)
2. ✅ Added `SET ResampleAlwaysSharpen "1"` to Config.wtf (line 129, after ResampleSharpness)
   - ResampleSharpness was already "0" (max CAS strength)
   - RenderScale already "1" (native res — RCAS-only pass, no EASU upscaling)
3. ✅ Flipped NIS 2.0 Enable [0x00ABAC21] = 0→1 via nvidia_drs_tool.ps1
   - Verified: cur=0x00000001, pre=0x00000000
   - NIS SharpValue remains at 11 (conservative)
4. ⬜ TEST: Launch WoW, evaluate dual-stack sharpening visually
5. ⬜ If over-sharpened: reduce NIS SharpValue or set ResampleSharpness to "0.3"-"0.5"
6. ⬜ If under-sharpened: increase NIS SharpValue
7. Future: Lossless Scaling for ML frame generation (Steam purchase)

## DLSS/DLAA Strategy — Persistent Overrides
- DLAA [0x10E41DF4] = 1 — STAYS ON. If Blizzard ever adds NGX SDK, this fires immediately.
- DLSS-SR [0x10E41DF4] = 1, DLSS-FG [0x10308298] = 1 — same logic.
- These are zero-cost dormant hooks. No reason to disable.

## Current Enhancement Stack (Active)
```
WoW Engine Render (DX12, 1080p native, 8x MSAA, RT Shadows)
  → FSR 1.0 RCAS pass (ResampleAlwaysSharpen=1, ResampleSharpness=0 [max])
  → Frame exits engine
  → NIS 2.0 NVSharpen (Enable=1, SharpValue=11 [conservative])
  → NVIDIA Reflex (LowLatencyMode=2)
  → Display
```
