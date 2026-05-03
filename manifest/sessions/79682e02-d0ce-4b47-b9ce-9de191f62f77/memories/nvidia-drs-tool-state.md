# NVIDIA DRS Tool - Full Technical State

## Script Location
scripts/nvidia_drs_tool.ps1

## Architecture
- Inline C# class `NvAPI` compiled via Add-Type
- Uses nvapi_QueryInterface to resolve function pointers by ID
- Manual IntPtr marshaling for NVDRS_SETTING (12320 byte struct)
- Read path works. Write path DOES NOT — returns success but values don't persist.

## NVAPI Function IDs (all confirmed working)
- Initialize: 0x0150E828, Unload: 0xD22BDD7E
- CreateSession: 0x0694D52E, DestroySession: 0xDAD9CFF8
- LoadSettings: 0x375DBD6B, SaveSettings: 0xFCBC7E14
- FindProfileByName: 0x7E4A9A0B, GetProfileInfo: 0x61CD6FD6
- EnumSettings: 0xAE3039DA, GetSetting: 0x73BF8338
- SetSetting: 0x577DD202
- GetBaseProfile: 0xDA8466A0, GetNumProfiles: 0x1DAE4FBC, EnumProfiles: 0x7AE3EC10

## NVDRS_SETTING_V1 Struct Layout (12320 bytes)
- version: offset 0 (4 bytes), value = (12320 | (1 << 16)) = 0x00013020
- settingName: offset 4 (NvAPI_UnicodeString = wchar[2048] = 4096 bytes)
- settingId: offset 4100 (4 bytes)
- settingType: offset 4104 (4 bytes), 0=DWORD
- settingLocation: offset 4108 (4 bytes)
- isCurrentPredefined: offset 4112 (4 bytes)
- isPredefinedValid: offset 4116 (4 bytes)
- currentValue union: offset 4120 (4100 bytes) — u32CurrentValue at 4120
- predefinedValue union: offset 8220 (4100 bytes) — u32PredefinedValue at 8220

## Write Path Problem
- SetSetting + SaveSettings both return 0 (NVAPI_OK) 
- DRS files ARE modified (timestamps change, size grew)
- But currentValue always reads back as 0
- predefinedValue at offset 8220 IS writable (tested: changed from 1→0)
- currentValue at offset 4120 NOT writable via our IntPtr approach
- NPI source (GitHub) uses proper C# struct with StructLayout + ref parameter
- NPI sets settingLocation = NVDRS_CURRENT_PROFILE_LOCATION (we set 0)

## FIX NEEDED
Must get NPI's NvapiDrsWrapper.cs to see:
1. Exact NVDRS_SETTING C# struct definition with [StructLayout] attributes
2. NVDRS_SETTING_LOCATION enum values
3. NVDRS_SETTING_UNION struct definition
4. How DRS_SetSetting delegate signature uses ref
URL: https://raw.githubusercontent.com/Orbmu2k/nvidiaProfileInspector/master/nvidiaProfileInspector/Native/NVAPI/NvapiDrsWrapper.cs

## Known Setting IDs
| Setting | ID | Value |
|---------|-----|-------|
| DLAA | 0x10E41DF4 | 0x00000001 |
| Enable DLSS-SR | 0x10E41E01 | 0x00000001 |
| Enable DLSS-RR | 0x10E41E02 | 0x00000001 |
| Enable DLSS-FG | 0x10E41E03 | 0x00000001 |
| AA Mode | 0x107EFC5B | 0x00000001 |
| AA Setting | 0x10D773D2 | 0x00000017 |
| Transparency SS | 0x10D48A85 | 0x00000038 |
| AA Behavior Flags | 0x10ECDB82 | 0x00000001 |
| Ambient Occlusion | 0x00667329 | 0x00000003 |
| AO Usage | 0x00664339 | 0x00000001 |

## WoW Profile
- Name: "World Of Warcraft"
- 13 application executables, ~40 settings, predefined=1
- WoW.exe at: C:\Program Files (x86)\World of Warcraft\_retail_\Wow.exe

## GPU
- NVIDIA GeForce RTX 4090, Driver 596.21 (DLSS 4.5)
- nvapi64.dll at C:\Windows\System32\nvapi64.dll (5.5MB)
- NPI v2.3.0.13 at C:\Users\eldno\Downloads\nvidiaProfileInspector\nvidiaProfileInspector.exe

## DRS Files
- C:\ProgramData\NVIDIA Corporation\Drs\
- nvdrsdb0.bin (~2.58MB), nvdrsdb1.bin (~2.58MB), nvdrssel.bin (1 byte)

## Script Parameters
-List, -Global, -Profile "name", -Filter "regex", -SetId 0x..., -SetValue N, 
-Export file.json, -Watch, -Interval N, -Snapshot, -Effective
