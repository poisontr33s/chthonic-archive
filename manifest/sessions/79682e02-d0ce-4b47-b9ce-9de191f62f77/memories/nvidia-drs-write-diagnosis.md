# NVIDIA DRS Write Path Diagnosis

## Root Cause Found — THREE bugs

### Bug 1: FIELD ORDER SWAPPED
NPI struct NVDRS_SETTING (actual correct order):
- offset 4120 = **predefinedValue** (union, 4100 bytes)
- offset 8220 = **currentValue** (union, 4100 bytes)
We had them reversed! We were writing to predefinedValue (4120) thinking it was currentValue.

### Bug 2: SetSetting delegate has 5 params
NPI signature: `DRS_SetSetting(session, profile, ref setting, uint x=0, uint y=0)`
We only had 3 params. Missing two trailing uint args (both always 0).

### Bug 3: Different primary function IDs
- SetSetting: PRIMARY=0x8A2CF5F5, FALLBACK=0x577DD202 (we used fallback)
- GetSetting: PRIMARY=0xEA99498D, FALLBACK=0x73BF8338 (we used fallback)
- EnumSettings: PRIMARY=0xCFD6983E, FALLBACK=0xAE3039DA

## NPI Source (confirmed from GitHub master)
- `DrsSettingsServiceBase.cs` → `StoreDwordValue()` constructs NVDRS_SETTING struct with:
  - version, settingId, settingType=DWORD, settingLocation=CURRENT_PROFILE_LOCATION
  - currentValue = NVDRS_SETTING_UNION { dwordValue = value }
- `DRS_SetSetting(hSession, hProfile, ref newSetting)` — passes by ref
- `DRS_SaveSettings(hSession)` — saves

## Our Issue
We use raw IntPtr + Marshal.WriteInt32 which:
1. May have wrong offsets due to struct alignment/padding differences
2. Sets settingLocation=0 instead of NVDRS_CURRENT_PROFILE_LOCATION  
3. The raw buffer approach might not match what NVAPI expects

## Controlled Test Results
- SetSetting returns 0 (OK), SaveSettings returns 0 (OK)
- DRS files ARE modified (timestamps change, size grew)
- But readback shows currentValue=0 always
- Writing DID change predefinedValue (from 1→0 when zeroed buffer used)
- This proves the struct offsets for predefinedValue (8220) work but currentValue (4120) doesn't

## FIX IMPLEMENTATION PLAN (from NPI NvapiDrsWrapper.cs)

### Fix 1: FIELD ORDER — predefinedValue at 4120, currentValue at 8220
In ReadSettingFromPtr:
- u32Pre = ReadInt32(ptr, 4120)  // predefinedValue FIRST
- u32Val = ReadInt32(ptr, 8220)  // currentValue SECOND
- strVal reads from 8220 not 4120

In SetDwordSetting:
- Write value at offset 8220 (not 4120)

### Fix 2: Delegate signatures
D_GetSetting: add `ref uint x` as 5th param
D_SetSetting: add `uint x, uint y` as 4th and 5th params

### Fix 3: Function IDs with fallback
SetSetting: PRIMARY=0x8A2CF5F5, FALLBACK=0x577DD202
GetSetting: PRIMARY=0xEA99498D, FALLBACK=0x73BF8338
EnumSettings: PRIMARY=0xCFD6983E, FALLBACK=0xAE3039DA

### Fix 4: Call sites
GetSettingById: `uint x = 0; _getSetting(session, profile, id, buf, ref x)`
SetDwordSetting: `_setSetting(session, profile, buf, 0, 0)`

### NPI struct definition (confirmed)
```csharp
[StructLayout(LayoutKind.Sequential, Pack = 8, CharSet = CharSet.Unicode)]
public struct NVDRS_SETTING {
    public uint version;
    [MarshalAs(ByValTStr, SizeConst=2048)] public string settingName;
    public uint settingId;
    public NVDRS_SETTING_TYPE settingType;
    public NVDRS_SETTING_LOCATION settingLocation;
    public uint isCurrentPredefined;
    public uint isPredefinedValid;
    public NVDRS_SETTING_UNION predefinedValue;  // offset 4120
    public NVDRS_SETTING_UNION currentValue;     // offset 8220
}
```
NVDRS_SETTING_LOCATION enum: 0=CURRENT_PROFILE, 1=GLOBAL, 2=BASE, 3=DEFAULT
NVDRS_SETTING_UNION: Sequential, Pack=8, Size=4100, contains byte[4100] rawData
  dwordValue = first 4 bytes of rawData

## IMPLEMENTATION STATUS: ALL FIXES APPLIED AND VERIFIED
All 7 replacements in scripts/nvidia_drs_tool.ps1 applied and tested:
1. ✅ Field offset comments corrected (predefined@4120, current@8220)
2. ✅ Function IDs: primary 0x8A2CF5F5/0xEA99498D/0xCFD6983E with fallbacks
3. ✅ Delegate signatures: D_GetSetting has ref uint x, D_SetSetting has uint x, uint y
4. ✅ Initialize() uses TryGetDelegate for primary ?? GetDelegate for fallback
5. ✅ ReadSettingFromPtr: u32Pre=ReadInt32(4120), u32Val=ReadInt32(8220), strVal from 8220
6. ✅ GetSettingById: passes ref uint x to _getSetting
7. ✅ SetDwordSetting: writes value at offset 8220, passes (buf, 0, 0) to _setSetting, also sets settingLocation=0 at offset 4108

## WRITE VERIFIED WORKING
- DLAA (0x10E41DF4) set to 1, verified persisted through game session
- Elevated process output now captured via temp wrapper script
- Temp files cleaned up after use

## WoW DLSS/DLAA ANALYSIS
- WoW does NOT have native DLSS SDK integration (confirmed PCGamingWiki: only FXAA/CMAA/MSAA/SSAA)
- WoW uses DX12 (`GxApi = d3d12`), has ray-traced shadows (`shadowRt = 3`)
- Driver override "Override DLSS mode to be DLAA" only works when game initializes DLSS SDK
- Since WoW never initializes DLSS, the override has no effect on rendering
- User's visual quality comes from SSGSAA x8 (driver) + MSAA x8 (in-game MSAAQuality=3)
- WoW has `LowLatencyMode = 2`, `RenderScale = 1`, `ResampleSharpness = 0`
- No hidden DLSS/upscaling CVars found in Config.wtf

## NPI LATEST
- v3.0.1.12 released 6 HOURS AGO (2026-04-18)
- Major UI/UX overhaul from v2.x to v3.x series
- User has v2.3.0.13 — very outdated
- New features: dark/light themes, Mica effects, collapsible groups, AI-generated descriptions
- v3.0.1.10 added Dynamic FG and Shader Pre-compile CSN entries
- v3.0.1.11 added midnight theme, AI-reworked reference data
- v3.0.1.12 added in-place updater, profile value overrides, visual input validation
- All v3.x releases are Pre-release on GitHub
- Download: https://github.com/Orbmu2k/nvidiaProfileInspector/releases

## KEY WoW CVars
- GxApi: d3d12
- MSAAQuality: 3 (8x)
- MSAAAlphaTest: 0
- RenderScale: 1 (native)
- ResampleSharpness: 0
- graphicsQuality: 9 (max)
- shadowRt: 3 (ray traced shadows ON)
- LowLatencyMode: 2
- vsync: 0
- farclip/horizonClip: 10000
- GxWindowedResolution: 1920x1080
