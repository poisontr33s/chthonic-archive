# WoW DLSS Investigation — Key Findings

## WoW's Built-in Upscaling: AMD FSR 1.0 (Spatial) — CONFIRMED
- Added in **Patch 9.1.5** (Shadowlands, Sep 2021)
- Blizzard forum thread literally titled "Can we please get DLSS 4? FSR 1.0 is not that good"
- `ResampleQuality`: 0=Point, 1=Bilinear, 2=Bicubic, **3=FidelityFX Super Resolution**
- Only applies when `RenderScale` != 1.0 (i.e., must render below native)
- `ResampleSharpness`: FSR sharpness [0.0-2.0], 0=full strength, -1=disable
- `ResampleAlwaysSharpen`: Run sharpness even without FSR upscale active
- `DynamicRenderScale`: Auto-lower RenderScale when GPU bound (beta)
- `DynamicRenderScaleMin`: Lowest RS that DRS can use (default 0.333)
- `RenderScale`: 0.009 to 2.00 (200% = SSAA 4x)
- Forum tip: "Force Resharpen without Render Scale" = ResampleAlwaysSharpen=1 at RenderScale=1.0

## DLSS DLL Status
- nvngx_dlss.dll v310.6.0 DOWNLOADED + VERIFIED
- Path: C:\Users\eldno\Downloads\nvngx_dlss_310.6.0\nvngx_dlss.dll
- Size: 70.6 MB, NVIDIA signed (Valid authenticode)
- DriverStore still missing nvngx_dlss.dll (has nvngx.dll, _nvngx.dll, nvngx_dlssg.dll, nvngx_update.exe)

## OptiScaler: CONFIRMED WON'T WORK for WoW
- OptiScaler intercepts FSR2+/DLSS2+/XeSS temporal API calls
- WoW uses FSR 1.0 (spatial only) — no temporal data, no motion vectors
- OptiScaler has nothing to intercept

## Warden Anti-Cheat Reality
- ReShade (DLL injection, post-processing) widely used in WoW for YEARS — not banned
- Driver-level overrides (NIS, sharpening, SSGSAA via NPI) = invisible to Warden
- Warden detects: memory reading/writing, bot frameworks, game function hooks
- Graphics post-processing ≠ cheating = not targeted

## NPI Migration
- Old: Downloads\nvidiaProfileInspector\ (single exe, 578KB, v2.3.0.13)
- New: Downloads\nvidiaProfileInspector-v3.0.1.12\ (exe+config+pdb+Reference.xml, 952KB)
- Portable app, zero user state — all profiles in driver DRS database
- Migration = just use the new folder

## Anti-Aliasing Modes
- `ffxAntiAliasingMode`: 0=Disabled, 1=FXAA Low, 2=FXAA High, 3=CMAA, 4=CMAA2
- `MSAAQuality`: Multisampling quality (user has 3 = 8x)
- `MSAAAlphaTest`: MSAA for alpha-tested geometry

## NVIDIA Integration Already Present
- `LowLatencyMode`: 0=None, 1=BuiltIn, **2=Reflex**, 3=Reflex+Boost, 4=XeLL
- `shadowRt`: 0-3 raytraced shadows (user has 3)
- `vrsValar`: VRS via velocity+luminance masks. Requires VRS Tier 2 (RTX 4090 has it)
- `ClientSettings_AFTERMATH`: NVIDIA Aftermath crash reporting (WoW ships GFSDK_Aftermath_Lib)

## Why FSR→DLSS Swap Won't Work
- WoW uses FSR **1.0** (spatial upscaler) — a simple resampling filter
- OptiScaler intercepts FSR **2/3** (temporal) API calls w/ motion vectors + depth
- WoW doesn't expose motion vectors or depth to upscaling pipeline
- DLSS requires temporal data that WoW's renderer doesn't provide
- PureDark-style mods ALSO need motion vectors → same blocker

## Viable Alternatives
1. **VRS (vrsValar=1)**: Enable on RTX 4090 for perf headroom → raise RenderScale
2. **NVIDIA Image Scaling (NIS)**: Driver-level, no game integration needed. Force via NPI/NVAPI
3. **SSAA via RenderScale**: Already possible (1.33=2x, 1.67=3x, 2.0=4x SSAA)
4. **FSR sharpening**: ResampleAlwaysSharpen=1, ResampleSharpness=0 (full)
5. **Future**: Blizzard needs to add FSR2/3 or DLSS SDK to engine
6. **ReShade**: DLL injection post-processing — NOT banned by Warden (widely used for years)
   - Can add upscaling shaders (FXAA, SMAA, CAS, sharpening)
   - Driver-level = invisible to Warden entirely
7. **NIS 2.0**: Already in user's profile (Enable=0, SharpValue=11). Flip Enable NIS 2.0 [0x00ABAC21]=1

## Current User Profile State (from watcher at 16:30:26)
- DLSS overrides ALL enabled: DLSS-SR=1, DLSS-RR=1, DLSS-FG=1
- DLAA override: 0x10E41DF4=1
- AA: 0x10D773D2=0x25 (changed from 0x17 — was 8x SSGSAA, now different mode)
- NIS 2.0: Enable=0, SharpValue=0x0B (11)
- DeepDVC: Sat=50, Intensity=50
- TrueHDR: Enabled=1, Contrast=100, Sat=100, MiddleGrey=50
- FRL: 144fps (0x90)
- Sharpening: Value=50, Denoising=17

## Key File Paths
- NPI old: C:\Users\eldno\Downloads\nvidiaProfileInspector\ (v2.3.0.13)
- NPI new: C:\Users\eldno\Downloads\nvidiaProfileInspector-v3.0.1.12\ (v3.0.1.12)
- DLSS DLL: C:\Users\eldno\Downloads\nvngx_dlss_310.6.0\nvngx_dlss.dll (70.6MB, v310.6.0)
- DriverStore: C:\Windows\System32\DriverStore\FileRepository\nv_dispi.inf_amd64_12ab2876952d3f1f\
- OTA: C:\ProgramData\NVIDIA Corporation\NVIDIA App\UpdateFramework\ota-artifacts\
- WoW: C:\Program Files (x86)\World of Warcraft\_retail_\Wow.exe
- WoW Config: <WoW>\_retail_\WTF\Config.wtf
- nvidia_drs_tool.ps1: c:\Users\eldno\chthonic-archive\scripts\nvidia_drs_tool.ps1
