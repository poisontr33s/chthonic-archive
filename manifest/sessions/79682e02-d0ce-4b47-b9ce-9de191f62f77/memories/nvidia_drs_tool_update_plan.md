# nvidia_drs_tool.ps1 Update Plan

## Current Tool State
- File: c:\Users\eldno\chthonic-archive\scripts\nvidia_drs_tool.ps1
- 649 lines, all core NVAPI functionality working
- Params: $List, $Global, $Profile, $Filter, $SetId, $SetValue, $Export, $Watch, $Interval, $Snapshot, $Effective
- C# class NvAPI with full DRS read/write via P/Invoke
- Setting names come from the NVAPI settingName field (4096 byte unicode string at offset 4)
- Many settings have empty names → show as "0x{id:X8}"

## NPI v3.0.1.12 Reference.xml
- Path: C:\Users\eldno\Downloads\nvidiaProfileInspector-v3.0.1.12\Reference.xml
- 812 settings with full names, descriptions, group names, and enum values
- XML Schema: CustomSettingNames > Settings > CustomSetting
  - HexSettingID (e.g., "0x00ABAC21")
  - UserfriendlyName (e.g., "NIS V2 Mode Nvapp Or Nvcp Required")
  - Description
  - GroupName (e.g., "05 - Upscaling and Frame Generation")
  - DataType (DWORD, etc.)
  - SettingValues > CustomSettingValue > UserfriendlyName + HexValue

## Features to Add
1. **-NpiRef param** — path to Reference.xml (default: auto-detect alongside NPI exe)
   - Load as dictionary: HexSettingID → { Name, Description, Group, Values }
   - Enrich all output: replace unnamed hex IDs with human-readable names
   - Show enum value names when displaying settings (e.g., "Enabled" instead of "0x00000001")

2. **-Apply param** — batch-apply a saved JSON snapshot
   - Reads the JSON from -Export format
   - For each setting with a non-zero Value: SetDwordSetting(profile, id, value)
   - Useful for restoring after NPI/NVCP reset
   - Auto-elevates like single SetId does

3. **-ResetProfile** — wipe all user overrides from a profile
   - Enumerate all settings, delete non-predefined ones
   - Needs NVAPI_DRS_DELETESETTING (function ID TBD)

## Key Settings to Re-Apply After Reset
From the baseline export ($env:TEMP\wow_profile_baseline_2026-04-18.json):
- Enable NIS 2.0 [0x00ABAC21] = 1
- Override DLSS mode to be DLAA [0x10E41DF4] = 1
- Override DLSSG mode [0x10308298] = 1
- Override DLSSG multi-frame count [0x104D6667] = 1
- Override DLSSG Target Frame Rate [0x10CF4125] = 1
- Override maximum DLSSG dynamic multi frame count [0x10562D0F] = 1
- Enable TrueHDR Feature [0x00DD48FB] = 1
- TrueHDR Contrast [0x00DD48FE] = 100
- TrueHDR Saturation [0x00DD48FF] = 100
- TrueHDR MiddleGrey [0x00DD48FD] = 50
- TrueHDR PeakBrightness [0x00DD48FC] = 417
- AA Mode [0x107EFC5B] = 1 (Override)
- AA Setting [0x10D773D2] = 0x17

## Line Ranges (from last read)
- Lines 1-15: Header/shebang/usage
- Lines 16-28: param() block  
- Lines 30-397: C# NvAPI class (P/Invoke, structs, methods)
- Lines 398-649: PowerShell main logic (List, Write, Enum, Display, Watch)
- Key display section: ~line 540-560 (setting output formatting)
- Watch mode: ~line 565-649

## EXACT param() block (lines 16-28):
```powershell
param(
    [switch]$List,
    [switch]$Global,
    [string]$Profile,
    [string]$Filter,
    [string]$SetId,
    [uint32]$SetValue,
    [string]$Export,
    [switch]$Watch,
    [int]$Interval = 2,
    [switch]$Snapshot,
    [switch]$Effective
)
```

## EXACT setting display block (approx lines 540-560):
The main display loop uses Sort-Object Name, formats with:
- $label = if Name matches ^0x then hex, else "$Name [$id]"
- Two modes: $Effective shows layer detail, else shows [MOD from $pre]
- Format: "  {0,-65} {1}  ({2}){3}" for non-Effective mode

## NPI Reference.xml Quick Example Entry:
```xml
<CustomSetting>
  <UserfriendlyName>NIS V2 Mode Nvapp Or Nvcp Required</UserfriendlyName>
  <HexSettingID>0x00ABAC21</HexSettingID>
  <Description>NIS V2 Mode...</Description>
  <GroupName>05 - Upscaling and Frame Generation</GroupName>
  <OverrideDefault>0x00000000</OverrideDefault>
  <DataType>DWORD</DataType>
  <SettingValues>
    <CustomSettingValue>
      <UserfriendlyName>Disabled</UserfriendlyName>
      <HexValue>0x00000000</HexValue>
    </CustomSettingValue>
    <CustomSettingValue>
      <UserfriendlyName>Enabled</UserfriendlyName>
      <HexValue>0x00000001</HexValue>
    </CustomSettingValue>
  </SettingValues>
</CustomSetting>
```
