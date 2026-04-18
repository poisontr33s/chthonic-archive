#!/usr/bin/env pwsh
# SID: nvidia_drs_tool.ps1
# PURPOSE: Read/write NVIDIA DRS (Driver Registry Settings) profiles via NVAPI P/Invoke.
#          Replaces dependency on NVIDIA Profile Inspector GUI.
# USAGE:
#   .\nvidia_drs_tool.ps1 -List                          # List all profile names
#   .\nvidia_drs_tool.ps1 -Profile "World Of Warcraft"   # Dump all settings for a profile
#   .\nvidia_drs_tool.ps1 -Profile "World Of Warcraft" -Filter "DLSS|DLAA|antialias"
#   .\nvidia_drs_tool.ps1 -Profile "World Of Warcraft" -Effective  # Show effective (predefined) values
#   .\nvidia_drs_tool.ps1 -Profile "World Of Warcraft" -SetId 0x10F9DC83 -SetValue 1
#   .\nvidia_drs_tool.ps1 -Profile "World Of Warcraft" -Watch          # Live-watch for changes
#   .\nvidia_drs_tool.ps1 -Profile "World Of Warcraft" -Watch -Interval 5 -Filter "DLSS"
#   .\nvidia_drs_tool.ps1 -Profile "World Of Warcraft" -Export out.json
#   .\nvidia_drs_tool.ps1 -Profile "World Of Warcraft" -Apply out.json  # Batch-restore from JSON
#   .\nvidia_drs_tool.ps1 -Profile "World Of Warcraft" -NpiRef path\to\Reference.xml  # Use NPI names

param(
    [switch]$List,
    [switch]$Global,
    [string]$Profile,
    [string]$Filter,
    [string]$SetId,
    [uint32]$SetValue,
    [string]$Export,
    [string]$Apply,
    [switch]$Watch,
    [int]$Interval = 2,
    [switch]$Snapshot,
    [switch]$Effective,
    [switch]$Audit,
    [string]$NpiRef
)

# --- NVAPI P/Invoke wrapper ---
$nvapi_cs = @'
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Collections.Generic;

public static class NvAPI
{
    // NVAPI uses a function-pointer query pattern. We resolve by ID.
    [DllImport("nvapi64.dll", EntryPoint = "nvapi_QueryInterface", CallingConvention = CallingConvention.Cdecl)]
    private static extern IntPtr QueryInterface(uint id);

    // Function IDs (from NVAPI reference / reverse engineering)
    private const uint NVAPI_INITIALIZE                = 0x0150E828;
    private const uint NVAPI_UNLOAD                    = 0xD22BDD7E;
    private const uint NVAPI_DRS_CREATESESSION          = 0x0694D52E;
    private const uint NVAPI_DRS_DESTROYSESSION         = 0xDAD9CFF8;
    private const uint NVAPI_DRS_LOADSETTINGS           = 0x375DBD6B;
    private const uint NVAPI_DRS_SAVESETTINGS           = 0xFCBC7E14;
    private const uint NVAPI_DRS_ENUMPROFILES           = 0x7AE3EC10;
    private const uint NVAPI_DRS_GETPROFILEINFO         = 0x61CD6FD6;
    private const uint NVAPI_DRS_FINDPROFILEBYNAME      = 0x7E4A9A0B;
    // Primary IDs from NPI (with legacy fallbacks from NVAPI docs)
    private const uint NVAPI_DRS_ENUMSETTINGS           = 0xCFD6983E;
    private const uint NVAPI_DRS_ENUMSETTINGS_FALLBACK  = 0xAE3039DA;
    private const uint NVAPI_DRS_GETSETTING             = 0xEA99498D;
    private const uint NVAPI_DRS_GETSETTING_FALLBACK    = 0x73BF8338;
    private const uint NVAPI_DRS_SETSETTING             = 0x8A2CF5F5;
    private const uint NVAPI_DRS_SETSETTING_FALLBACK    = 0x577DD202;
    private const uint NVAPI_DRS_GETBASEPROFILE         = 0xDA8466A0;
    private const uint NVAPI_DRS_GETNUMPROFILES         = 0x1DAE4FBC;

    // Delegates
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate int D_Init();
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate int D_Unload();
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate int D_CreateSession(out IntPtr session);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate int D_DestroySession(IntPtr session);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate int D_LoadSettings(IntPtr session);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate int D_SaveSettings(IntPtr session);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate int D_EnumProfiles(IntPtr session, uint index, out IntPtr profileHandle);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate int D_GetProfileInfo(IntPtr session, IntPtr profile, ref NVDRS_PROFILE profileInfo);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate int D_FindProfileByName(IntPtr session, [MarshalAs(UnmanagedType.LPWStr)] string name, out IntPtr profileHandle);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate int D_EnumSettings(IntPtr session, IntPtr profile, uint startIndex, ref uint count, IntPtr settingsArray);
    // NPI signatures: GetSetting has trailing ref uint; SetSetting has trailing uint, uint
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate int D_GetSetting(IntPtr session, IntPtr profile, uint settingId, IntPtr setting, ref uint x);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate int D_SetSetting(IntPtr session, IntPtr profile, IntPtr setting, uint x, uint y);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate int D_GetBaseProfile(IntPtr session, out IntPtr profileHandle);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate int D_GetNumProfiles(IntPtr session, out uint count);

    // Structs — sizes must match NVAPI native layout exactly
    private const int NVAPI_UNICODE_STRING_MAX = 2048;  // wchar_t count (4096 bytes)
    private const int NVAPI_BINARY_DATA_MAX = 4096;     // bytes
    // Union size = max(4, 4+4096, 4096) = 4100 bytes (NVAPI_BINARY_TYPE is largest)
    private const int UNION_SIZE = 4100;
    // Total NVDRS_SETTING size = 4 + 4096 + 5*4 + 4100 + 4100 = 12320
    private const int SETTING_STRUCT_SIZE = 12320;

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct NVDRS_PROFILE
    {
        public uint version;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = NVAPI_UNICODE_STRING_MAX)]
        public string profileName;
        public uint gpuSupport;
        public uint isPredefined;
        public uint numOfApps;
        public uint numOfSettings;
    }

    // We marshal NVDRS_SETTING manually via IntPtr because the native struct
    // contains unions that C# Sequential layout can't model correctly.
    // Field offsets in NVDRS_SETTING_V1:
    //   0:    version (uint32)
    //   4:    settingName (wchar[2048] = 4096 bytes)
    //   4100: settingId (uint32)
    //   4104: settingType (uint32)
    //   4108: settingLocation (uint32)
    //   4112: isCurrentPredefined (uint32)
    //   4116: isPredefinedValid (uint32)
    //   4120: predefinedValue union (4100 bytes)  [NPI: predefined FIRST]
    //         - u32PredefinedValue at 4120
    //   8220: currentValue union (4100 bytes)    [NPI: current SECOND]
    //         - u32CurrentValue at 8220
    // Total: 12320 bytes
    // NOTE: Field order confirmed from NPI NvapiDrsWrapper.cs NVDRS_SETTING struct.

    // Dummy struct for MAKE_NVAPI_VERSION on NVDRS_PROFILE only
    // For NVDRS_SETTING we use a hardcoded version constant
    private static readonly uint SETTING_VERSION = (uint)(SETTING_STRUCT_SIZE | (1 << 16));

    // Cached delegates
    private static D_Init _init;
    private static D_Unload _unload;
    private static D_CreateSession _createSession;
    private static D_DestroySession _destroySession;
    private static D_LoadSettings _loadSettings;
    private static D_SaveSettings _saveSettings;
    private static D_EnumProfiles _enumProfiles;
    private static D_GetProfileInfo _getProfileInfo;
    private static D_FindProfileByName _findProfile;
    private static D_EnumSettings _enumSettings;
    private static D_GetSetting _getSetting;
    private static D_SetSetting _setSetting;
    private static D_GetBaseProfile _getBaseProfile;
    private static D_GetNumProfiles _getNumProfiles;

    private static T GetDelegate<T>(uint id) where T : class
    {
        IntPtr ptr = QueryInterface(id);
        if (ptr == IntPtr.Zero) throw new Exception($"NVAPI function 0x{id:X8} not found");
        return Marshal.GetDelegateForFunctionPointer(ptr, typeof(T)) as T;
    }

    private static void Check(int status, string func)
    {
        if (status != 0) throw new Exception($"NVAPI {func} failed: 0x{status:X8}");
    }

    public static uint MAKE_NVAPI_VERSION<T>(int ver) where T : struct
    {
        return (uint)(Marshal.SizeOf(typeof(T)) | (ver << 16));
    }

    // --- Public API ---

    private static IntPtr _session = IntPtr.Zero;
    private static bool _initialized = false;

    private static T TryGetDelegate<T>(uint id) where T : class
    {
        IntPtr ptr = QueryInterface(id);
        if (ptr == IntPtr.Zero) return null;
        return Marshal.GetDelegateForFunctionPointer(ptr, typeof(T)) as T;
    }

    public static void Initialize()
    {
        if (_initialized) return;
        // Phase 1: resolve init/unload (must succeed)
        _init = GetDelegate<D_Init>(NVAPI_INITIALIZE);
        _unload = GetDelegate<D_Unload>(NVAPI_UNLOAD);

        // Phase 2: call init first — some functions only resolve after init
        Check(_init(), "Initialize");

        // Phase 3: resolve DRS functions (after init)
        _createSession = GetDelegate<D_CreateSession>(NVAPI_DRS_CREATESESSION);
        _destroySession = GetDelegate<D_DestroySession>(NVAPI_DRS_DESTROYSESSION);
        _loadSettings = GetDelegate<D_LoadSettings>(NVAPI_DRS_LOADSETTINGS);
        _saveSettings = GetDelegate<D_SaveSettings>(NVAPI_DRS_SAVESETTINGS);
        _findProfile = GetDelegate<D_FindProfileByName>(NVAPI_DRS_FINDPROFILEBYNAME);
        _enumSettings = TryGetDelegate<D_EnumSettings>(NVAPI_DRS_ENUMSETTINGS)
                        ?? GetDelegate<D_EnumSettings>(NVAPI_DRS_ENUMSETTINGS_FALLBACK);
        _getSetting = TryGetDelegate<D_GetSetting>(NVAPI_DRS_GETSETTING)
                      ?? GetDelegate<D_GetSetting>(NVAPI_DRS_GETSETTING_FALLBACK);
        _setSetting = TryGetDelegate<D_SetSetting>(NVAPI_DRS_SETSETTING)
                      ?? GetDelegate<D_SetSetting>(NVAPI_DRS_SETSETTING_FALLBACK);
        _getBaseProfile = GetDelegate<D_GetBaseProfile>(NVAPI_DRS_GETBASEPROFILE);
        _getProfileInfo = GetDelegate<D_GetProfileInfo>(NVAPI_DRS_GETPROFILEINFO);

        // Optional functions (may not exist in all driver versions)
        _enumProfiles = TryGetDelegate<D_EnumProfiles>(NVAPI_DRS_ENUMPROFILES);
        _getNumProfiles = TryGetDelegate<D_GetNumProfiles>(NVAPI_DRS_GETNUMPROFILES);

        Check(_createSession(out _session), "CreateSession");
        Check(_loadSettings(_session), "LoadSettings");
        _initialized = true;
    }

    public static void Cleanup()
    {
        if (_session != IntPtr.Zero)
        {
            _destroySession(_session);
            _session = IntPtr.Zero;
        }
        if (_initialized)
        {
            _unload();
            _initialized = false;
        }
    }

    public static void ReloadSettings()
    {
        // Full teardown: NVAPI caches at the init level, not just session level.
        // Must unload + reinit to pick up changes from external tools (NPI).
        if (_session != IntPtr.Zero)
        {
            _destroySession(_session);
            _session = IntPtr.Zero;
        }
        _unload();
        Check(_init(), "Initialize (reload)");
        Check(_createSession(out _session), "CreateSession (reload)");
        Check(_loadSettings(_session), "LoadSettings (reload)");
    }

    public static List<string> ListProfiles()
    {
        var result = new List<string>();
        if (_enumProfiles == null || _getNumProfiles == null)
        {
            // Fallback: try enumerating by index without count
            for (uint i = 0; i < 5000; i++)
            {
                if (_enumProfiles == null) break;
                IntPtr ph;
                int status = _enumProfiles(_session, i, out ph);
                if (status != 0) break;
                var info = new NVDRS_PROFILE();
                info.version = MAKE_NVAPI_VERSION<NVDRS_PROFILE>(1);
                status = _getProfileInfo(_session, ph, ref info);
                if (status == 0 && !string.IsNullOrEmpty(info.profileName))
                    result.Add(info.profileName);
            }
            return result;
        }
        _getNumProfiles(_session, out uint count);
        for (uint i = 0; i < count; i++)
        {
            IntPtr ph;
            int status = _enumProfiles(_session, i, out ph);
            if (status != 0) break;
            var info = new NVDRS_PROFILE();
            info.version = MAKE_NVAPI_VERSION<NVDRS_PROFILE>(1);
            status = _getProfileInfo(_session, ph, ref info);
            if (status == 0 && !string.IsNullOrEmpty(info.profileName))
                result.Add(info.profileName);
        }
        return result;
    }

    public static IntPtr FindProfile(string name)
    {
        IntPtr ph;
        int status = _findProfile(_session, name, out ph);
        if (status != 0)
            throw new Exception($"Profile '{name}' not found (0x{status:X8}). Use -List to see available profiles.");
        return ph;
    }

    public static IntPtr GetBaseProfile()
    {
        IntPtr ph;
        Check(_getBaseProfile(_session, out ph), "GetBaseProfile");
        return ph;
    }

    public static NVDRS_PROFILE GetProfileInfo(IntPtr ph)
    {
        var info = new NVDRS_PROFILE();
        info.version = MAKE_NVAPI_VERSION<NVDRS_PROFILE>(1);
        Check(_getProfileInfo(_session, ph, ref info), "GetProfileInfo");
        return info;
    }

    private static SettingResult ReadSettingFromPtr(IntPtr ptr)
    {
        string name = Marshal.PtrToStringUni(IntPtr.Add(ptr, 4));
        uint id = (uint)Marshal.ReadInt32(ptr, 4100);
        uint type = (uint)Marshal.ReadInt32(ptr, 4104);
        uint location = (uint)Marshal.ReadInt32(ptr, 4108);
        uint isPre = (uint)Marshal.ReadInt32(ptr, 4112);
        uint u32Pre = (uint)Marshal.ReadInt32(ptr, 4120);  // predefinedValue at 4120
        uint u32Val = (uint)Marshal.ReadInt32(ptr, 8220);  // currentValue at 8220
        string strVal = "";
        if (type == 2 || type == 3) // STRING or WSTRING
            strVal = Marshal.PtrToStringUni(IntPtr.Add(ptr, 8220));  // current string value
        return new SettingResult
        {
            Name = string.IsNullOrEmpty(name) ? $"0x{id:X8}" : name,
            Id = id, Type = type, Value = u32Val, PredefinedValue = u32Pre,
            StringValue = strVal, Location = location, IsPredefined = isPre != 0
        };
    }

    /// <summary>
    /// Read a single setting by ID using GetSetting (returns effective value, not just delta).
    /// Returns null if the setting doesn't exist in this profile.
    /// </summary>
    public static SettingResult GetSettingById(IntPtr profileHandle, uint settingId)
    {
        IntPtr buf = Marshal.AllocHGlobal(SETTING_STRUCT_SIZE);
        try
        {
            for (int i = 0; i < SETTING_STRUCT_SIZE; i++) Marshal.WriteByte(buf, i, 0);
            Marshal.WriteInt32(buf, 0, (int)SETTING_VERSION);
            uint x = 0;
            int status = _getSetting(_session, profileHandle, settingId, buf, ref x);
            if (status != 0) return null;
            return ReadSettingFromPtr(buf);
        }
        finally { Marshal.FreeHGlobal(buf); }
    }

    public static List<SettingResult> EnumSettings(IntPtr profileHandle)
    {
        var results = new List<SettingResult>();
        uint idx = 0;
        int batchSize = 8;
        int blockSize = SETTING_STRUCT_SIZE * batchSize;
        IntPtr buf = Marshal.AllocHGlobal(blockSize);
        try
        {
            while (true)
            {
                // Zero memory and set version in each slot
                for (int i = 0; i < blockSize; i++) Marshal.WriteByte(buf, i, 0);
                for (int i = 0; i < batchSize; i++)
                    Marshal.WriteInt32(buf, i * SETTING_STRUCT_SIZE, (int)SETTING_VERSION);

                uint count = (uint)batchSize;
                int status = _enumSettings(_session, profileHandle, idx, ref count, buf);
                if (status != 0 || count == 0) break;
                for (uint i = 0; i < count; i++)
                {
                    IntPtr slot = IntPtr.Add(buf, (int)(i * SETTING_STRUCT_SIZE));
                    results.Add(ReadSettingFromPtr(slot));
                }
                idx += count;
            }
        }
        finally { Marshal.FreeHGlobal(buf); }
        return results;
    }

    public static void SetDwordSetting(IntPtr profileHandle, uint settingId, uint value)
    {
        IntPtr buf = Marshal.AllocHGlobal(SETTING_STRUCT_SIZE);
        try
        {
            for (int i = 0; i < SETTING_STRUCT_SIZE; i++) Marshal.WriteByte(buf, i, 0);
            Marshal.WriteInt32(buf, 0, (int)SETTING_VERSION);   // version
            Marshal.WriteInt32(buf, 4100, (int)settingId);       // settingId
            Marshal.WriteInt32(buf, 4104, 0);                    // settingType = DWORD
            Marshal.WriteInt32(buf, 4108, 0);                    // settingLocation = CURRENT_PROFILE
            Marshal.WriteInt32(buf, 8220, (int)value);           // u32CurrentValue at 8220 (NOT 4120)
            Check(_setSetting(_session, profileHandle, buf, 0, 0), "SetSetting");
            Check(_saveSettings(_session), "SaveSettings");
        }
        finally { Marshal.FreeHGlobal(buf); }
    }

    public class SettingResult
    {
        public string Name;
        public uint Id;
        public uint Type;
        public uint Value;
        public uint PredefinedValue;
        public string StringValue;
        public uint Location;
        public bool IsPredefined;
    }
}
'@

try {
    Add-Type -TypeDefinition $nvapi_cs -ErrorAction Stop
} catch {
    if ($_.Exception.Message -notmatch 'already exists') { throw }
}

# --- Main ---
# --- Load NPI Reference.xml for human-readable setting names ---
$npiNames = @{}  # HexID string → friendly name
$npiValues = @{} # HexID string → @{ hexVal → friendlyName }
$npiGroups = @{} # HexID string → group name

if (-not $NpiRef) {
    # Auto-detect: look for Reference.xml alongside known NPI installations
    $candidates = @(
        "$env:USERPROFILE\Downloads\nvidiaProfileInspector-v3.0.1.12\Reference.xml",
        "$env:USERPROFILE\Downloads\nvidiaProfileInspector\Reference.xml",
        "$env:ProgramFiles\NVIDIA Profile Inspector\Reference.xml"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { $NpiRef = $c; break }
    }
}

if ($NpiRef -and (Test-Path $NpiRef)) {
    try {
        [xml]$refXml = Get-Content $NpiRef -ErrorAction Stop
        $refSettings = $refXml.CustomSettingNames.Settings.CustomSetting
        foreach ($rs in $refSettings) {
            $hexId = $rs.HexSettingID.ToUpper()
            $npiNames[$hexId] = $rs.UserfriendlyName
            if ($rs.GroupName) { $npiGroups[$hexId] = $rs.GroupName }
            if ($rs.SettingValues -and $rs.SettingValues.CustomSettingValue) {
                $valMap = @{}
                foreach ($sv in $rs.SettingValues.CustomSettingValue) {
                    $valMap[$sv.HexValue.ToUpper()] = $sv.UserfriendlyName
                }
                $npiValues[$hexId] = $valMap
            }
        }
        if (-not $Snapshot) {
            Write-Host "  NPI Reference: $($npiNames.Count) settings loaded from $(Split-Path $NpiRef -Leaf)" -ForegroundColor DarkGray
        }
    } catch {
        Write-Warning "Failed to load NPI Reference.xml: $_"
    }
}

# Helper: resolve a setting name using NPI reference, falling back to NVAPI name
function Resolve-SettingName {
    param([string]$NvapiName, [uint32]$Id)
    $hexKey = "0x{0:X8}" -f $Id
    if ($npiNames.ContainsKey($hexKey)) { return $npiNames[$hexKey] }
    if ($NvapiName -and $NvapiName -notmatch '^0x') { return $NvapiName }
    return $hexKey
}

# Helper: resolve a setting value to friendly name
function Resolve-SettingValue {
    param([uint32]$Id, [uint32]$Value)
    $hexKey = "0x{0:X8}" -f $Id
    $valHex = "0x{0:X8}" -f $Value
    if ($npiValues.ContainsKey($hexKey) -and $npiValues[$hexKey].ContainsKey($valHex)) {
        return $npiValues[$hexKey][$valHex]
    }
    return $null
}

try {
    [NvAPI]::Initialize()

    if ($List) {
        $profiles = [NvAPI]::ListProfiles()
        Write-Output "Found $($profiles.Count) profiles:"
        $profiles | Sort-Object | ForEach-Object { Write-Output "  $_" }
        return
    }

    # Determine target profile handle
    $ph = $null
    $profileLabel = ""
    if ($Global) {
        $ph = [NvAPI]::GetBaseProfile()
        $profileLabel = "(Global/Base Profile)"
    } elseif ($Profile) {
        $ph = [NvAPI]::FindProfile($Profile)
        $profileLabel = $Profile
    } else {
        Write-Output "Usage: specify -List, -Global, or -Profile 'Name'"
        Write-Output "  -List                           List all profile names"
        Write-Output "  -Profile 'World Of Warcraft'    Dump settings for a profile"
        Write-Output "  -Global                         Dump global/base profile"
        Write-Output "  -Filter 'DLSS|DLAA'             Regex filter on setting names"
        Write-Output "  -SetId 0x... -SetValue N        Write a DWORD setting (auto-elevates to admin)"
        Write-Output "  -Export file.json                Export settings to JSON"
        Write-Output "  -Apply file.json                Batch-restore DWORD settings from exported JSON"
        Write-Output "  -NpiRef path\Reference.xml      Use NPI Reference.xml for human-readable names"
        Write-Output "  -Effective                       Show effective values (predefined when not overridden)"
        Write-Output "  -Audit                           Classify settings as ACTIVE/DEAD/MARGINAL"
        Write-Output "  -Watch                           Live-watch for setting changes"
        Write-Output "  -Interval 5                      Poll interval in seconds (default 2)"
        return
    }

    $info = [NvAPI]::GetProfileInfo($ph)
    if (-not $Snapshot) {
        Write-Output "`n=== Profile: $profileLabel ==="
        Write-Output "  Apps: $($info.numOfApps) | Settings: $($info.numOfSettings) | Predefined: $($info.isPredefined)"
    }

    # Write setting if requested
    if ($SetId) {
        # Admin elevation gate — SaveSettings silently fails without admin
        $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        if (-not $isAdmin) {
            Write-Host "Write requires admin. Relaunching elevated..." -ForegroundColor Yellow
            $elevLog = Join-Path $env:TEMP "nvidia_drs_elev.log"
            $elevScript = Join-Path $env:TEMP "nvidia_drs_elev.ps1"
            $elevArgs = @('-NoProfile', '-File', $PSCommandPath)
            if ($Global) { $elevArgs += '-Global' } elseif ($Profile) { $elevArgs += '-Profile'; $elevArgs += "`"$Profile`"" }
            $elevArgs += '-SetId'; $elevArgs += $SetId; $elevArgs += '-SetValue'; $elevArgs += $SetValue
            $wrapperContent = "& pwsh $($elevArgs -join ' ') *> '$elevLog'"
            Set-Content -Path $elevScript -Value $wrapperContent -Force
            Start-Process pwsh -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $elevScript) -Verb RunAs -Wait
            if (Test-Path $elevLog) { Write-Host (Get-Content $elevLog -Raw) -ForegroundColor Cyan }
            Remove-Item -Path $elevScript, $elevLog -Force -ErrorAction SilentlyContinue
            Write-Host "Elevated process completed. Re-reading to verify..." -ForegroundColor Green
            # Re-read via subprocess to confirm
            $verifyArgs = @('-NoProfile', '-File', $PSCommandPath, '-Snapshot')
            if ($Global) { $verifyArgs += '-Global' } elseif ($Profile) { $verifyArgs += '-Profile'; $verifyArgs += $Profile }
            $raw = & pwsh @verifyArgs 2>$null
            if ($raw) {
                $snapObj = $raw | ConvertFrom-Json
                $sid = [uint32]$SetId
                $key = $sid.ToString()
                $s = $snapObj.settings.$key
                if ($s) {
                    $vHex = "0x{0:X8}" -f [uint32]$s.v
                    $pHex = "0x{0:X8}" -f [uint32]$s.p
                    Write-Host "  Verified: $($s.n) = cur=$vHex pre=$pHex" -ForegroundColor Green
                } else {
                    Write-Host "  Setting 0x$($sid.ToString('X8')) not in enum (may be predefined-only)" -ForegroundColor Yellow
                }
            }
            return
        }
        $sid = [uint32]$SetId
        Write-Output "`n--- Setting 0x$($sid.ToString('X8')) to $SetValue ---"
        [NvAPI]::SetDwordSetting($ph, $sid, $SetValue)
        Write-Output "Done. Setting saved to driver."
    }

    # Batch-apply from JSON export
    if ($Apply) {
        if (-not (Test-Path $Apply)) {
            Write-Error "Apply file not found: $Apply"
            return
        }
        $applyData = Get-Content $Apply -Raw | ConvertFrom-Json
        $toApply = $applyData | Where-Object { [uint32]($_.ValueDecimal) -ne 0 -and $_.Type -eq 0 }
        Write-Output "`n--- Applying $($toApply.Count) DWORD settings from: $Apply ---"

        $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        if (-not $isAdmin) {
            Write-Host "Write requires admin. Relaunching elevated..." -ForegroundColor Yellow
            $elevLog = Join-Path $env:TEMP "nvidia_drs_elev.log"
            $elevScript = Join-Path $env:TEMP "nvidia_drs_elev.ps1"
            $elevArgs = @('-NoProfile', '-File', $PSCommandPath, '-Apply', "`"$Apply`"")
            if ($Global) { $elevArgs += '-Global' } elseif ($Profile) { $elevArgs += '-Profile'; $elevArgs += "`"$Profile`"" }
            $wrapperContent = "& pwsh $($elevArgs -join ' ') *> '$elevLog'"
            Set-Content -Path $elevScript -Value $wrapperContent -Force
            Start-Process pwsh -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $elevScript) -Verb RunAs -Wait
            if (Test-Path $elevLog) { Write-Host (Get-Content $elevLog -Raw) -ForegroundColor Cyan }
            Remove-Item -Path $elevScript, $elevLog -Force -ErrorAction SilentlyContinue
            return
        }

        $applied = 0
        foreach ($entry in $toApply) {
            $sid = [uint32]$entry.Id
            $val = [uint32]($entry.ValueDecimal)
            $name = Resolve-SettingName -NvapiName $entry.Name -Id $sid
            try {
                [NvAPI]::SetDwordSetting($ph, $sid, $val)
                $valLabel = Resolve-SettingValue -Id $sid -Value $val
                $valDisp = if ($valLabel) { "$val ($valLabel)" } else { "$val (0x{0:X8})" -f $val }
                Write-Host "  OK: $name = $valDisp" -ForegroundColor Green
                $applied++
            } catch {
                Write-Host "  FAIL: $name — $_" -ForegroundColor Red
            }
        }
        Write-Output "Applied $applied/$($toApply.Count) settings."
        return
    }

    # Enumerate and display settings
    $settings = [NvAPI]::EnumSettings($ph)

    if ($Filter) {
        $settings = $settings | Where-Object {
            $resolved = Resolve-SettingName -NvapiName $_.Name -Id $_.Id
            $resolved -match $Filter -or $_.Name -match $Filter -or ("0x{0:X8}" -f $_.Id) -match $Filter
        }
    }

    # Snapshot mode: output JSON and exit (used by watch subprocess)
    if ($Snapshot) {
        $snap = @{}
        foreach ($s in $settings) {
            $key = $s.Id.ToString()
            $eff = if ($s.Value -ne 0) { $s.Value } elseif ($s.PredefinedValue -ne 0) { $s.PredefinedValue } else { $s.Value }
            $resolvedName = Resolve-SettingName -NvapiName $s.Name -Id $s.Id
            $snap[$key] = @{ n = $resolvedName; v = $s.Value; p = $s.PredefinedValue; e = $eff }
        }
        # Also include DRS file timestamps for file-level change detection
        $drsPath = "C:\ProgramData\NVIDIA Corporation\Drs"
        $drsFiles = @{}
        foreach ($f in @('nvdrsdb0.bin','nvdrsdb1.bin','nvdrssel.bin')) {
            $fp = Join-Path $drsPath $f
            if (Test-Path $fp) {
                $fi = Get-Item $fp
                $drsFiles[$f] = @{ size = $fi.Length; mtime = $fi.LastWriteTime.ToString("o") }
            }
        }
        @{ settings = $snap; drsFiles = $drsFiles } | ConvertTo-Json -Compress -Depth 4
        return
    }

    if ($Export) {
        $exportData = $settings | ForEach-Object {
            $resolvedName = Resolve-SettingName -NvapiName $_.Name -Id $_.Id
            [PSCustomObject]@{
                Name = $resolvedName
                Id = "0x{0:X8}" -f $_.Id
                Type = $_.Type
                Value = "0x{0:X8}" -f $_.Value
                ValueDecimal = $_.Value
                PredefinedValue = "0x{0:X8}" -f $_.PredefinedValue
                Location = $_.Location
                IsPredefined = $_.IsPredefined
            }
        }
        $exportData | ConvertTo-Json -Depth 3 | Set-Content -Path $Export -Encoding UTF8
        Write-Output "`nExported $($settings.Count) settings to: $Export"
    }

    # Deduplicate settings by ID (EnumSettings can return duplicates)
    $seen = @{}
    $deduped = @()
    foreach ($s in $settings) {
        if (-not $seen.ContainsKey($s.Id)) {
            $seen[$s.Id] = $true
            $deduped += $s
        }
    }
    $settings = $deduped

    # --- Audit mode: classify settings by relevance ---
    if ($Audit) {
        # Dead-weight classification rules for single-GPU desktop + DX12
        $deadPatterns = @(
            @{ Match = '08 - SLI'; Reason = 'SLI/NVLink — single GPU, no effect' }
            @{ Match = '10 - OpenGL'; Reason = 'OpenGL path — WoW is DX12, never executes' }
        )
        # Use string hex keys to avoid int32/uint32 type mismatch
        $deadIds = @{
            '0x10F9DC81' = 'Optimus allow-list — desktop GPU, no iGPU mux'
            '0x10F9DC84' = 'Optimus shim — desktop GPU, no iGPU mux'
            '0x10AAA36C' = 'Quadro disable — already GeForce, no-op'
            '0x20797D6C' = 'OpenGL texture quality — DX12 game, OGL path never runs'
        }
        $marginalIds = @{
            '0x10E74421' = 'NvCamera depth block — low cost, niche use'
            '0x1034CB89' = 'Predefined FXAA=0 — already default, redundant entry'
            '0x006BDD49' = 'Surface max priority — 4090 is 384-bit, setting targets 192-bit'
            '0x00EA83C5' = 'DX10 surface priority — DX10 path on DX12 game'
            '0x105E2A1D' = 'CPU Expr Modes — experimental/undocumented'
            '0x80857A28' = 'VSync Expr — telemetry flag per NPI, not rendering'
            '0x00664339' = 'Predefined AO usage — companion to AO, probably needed'
        }

        $active = @(); $dead = @(); $marginal = @()
        foreach ($s in $settings) {
            $hexKey = "0x{0:X8}" -f $s.Id
            $resolvedName = Resolve-SettingName -NvapiName $s.Name -Id $s.Id
            $group = if ($npiGroups.ContainsKey($hexKey)) { $npiGroups[$hexKey] } else { '' }
            $classified = $false

            # Check dead by ID (string key match)
            if ($deadIds.ContainsKey($hexKey)) {
                $dead += [PSCustomObject]@{ Name=$resolvedName; Id=$hexKey; Value=$s.Value; Reason=$deadIds[$hexKey] }
                $classified = $true
            }
            # Check dead by group pattern
            if (-not $classified) {
                foreach ($dp in $deadPatterns) {
                    if ($group -like "*$($dp.Match)*") {
                        $dead += [PSCustomObject]@{ Name=$resolvedName; Id=$hexKey; Value=$s.Value; Reason=$dp.Reason }
                        $classified = $true
                        break
                    }
                }
            }
            # Check unknown hex prefix 0x20 = OpenGL namespace
            if (-not $classified -and $hexKey -match '^0x20' -and $group -eq '') {
                $dead += [PSCustomObject]@{ Name=$resolvedName; Id=$hexKey; Value=$s.Value; Reason='0x20 prefix = OpenGL namespace, DX12 game' }
                $classified = $true
            }
            # Check marginal by ID
            if (-not $classified -and $marginalIds.ContainsKey($hexKey)) {
                $marginal += [PSCustomObject]@{ Name=$resolvedName; Id=$hexKey; Value=$s.Value; Reason=$marginalIds[$hexKey] }
                $classified = $true
            }
            # Unknown settings with no NPI entry
            if (-not $classified -and -not $npiNames.ContainsKey($hexKey) -and $resolvedName -match '^0x') {
                $marginal += [PSCustomObject]@{ Name=$resolvedName; Id=$hexKey; Value=$s.Value; Reason='Unknown — not in NPI Reference.xml' }
                $classified = $true
            }
            if (-not $classified) {
                $active += [PSCustomObject]@{ Name=$resolvedName; Id=$hexKey; Value=$s.Value; Reason='' }
            }
        }

        Write-Host "`n=== Audit: $($settings.Count) settings ===" -ForegroundColor White
        Write-Host "`n  ACTIVE ($($active.Count)) — real work on this GPU/API:" -ForegroundColor Green
        foreach ($a in ($active | Sort-Object Name)) {
            $valLabel = Resolve-SettingValue -Id ([uint32]$a.Id) -Value $a.Value
            $vDisp = if ($valLabel) { "$($a.Value) ($valLabel)" } else { "0x{0:X8}" -f $a.Value }
            Write-Host ("    {0,-55} {1}" -f "$($a.Name) [$($a.Id)]", $vDisp) -ForegroundColor Green
        }

        Write-Host "`n  DEAD ($($dead.Count)) — zero effect, safe to remove:" -ForegroundColor Red
        foreach ($d in ($dead | Sort-Object Name)) {
            Write-Host ("    {0,-55} {1}" -f "$($d.Name) [$($d.Id)]", $d.Reason) -ForegroundColor Red
        }

        Write-Host "`n  MARGINAL ($($marginal.Count)) — debatable, low/no impact:" -ForegroundColor Yellow
        foreach ($m in ($marginal | Sort-Object Name)) {
            Write-Host ("    {0,-55} {1}" -f "$($m.Name) [$($m.Id)]", $m.Reason) -ForegroundColor Yellow
        }

        Write-Host "`n  Summary: $($active.Count) active, $($dead.Count) dead, $($marginal.Count) marginal" -ForegroundColor White
        return
    }

    Write-Output "`n  $($settings.Count) settings$(if($Filter){' (filtered)'}else{''}):`n"
    $settings | Sort-Object { Resolve-SettingName -NvapiName $_.Name -Id $_.Id } | ForEach-Object {
        $id  = "0x{0:X8}" -f $_.Id
        $cur = "0x{0:X8}" -f $_.Value
        $pre = "0x{0:X8}" -f $_.PredefinedValue
        $resolvedName = Resolve-SettingName -NvapiName $_.Name -Id $_.Id
        # Effective: show predefined when current is 0 and predefined exists
        $effVal = if ($_.Value -ne 0) { $_.Value } elseif ($_.PredefinedValue -ne 0) { $_.PredefinedValue } else { $_.Value }
        $eff = "0x{0:X8}" -f $effVal
        $loc = switch ($_.Location) { 0 {"cur"} 1 {"global"} 2 {"base"} 3 {"default"} default {"?"} }
        $label = "$resolvedName [$id]"
        # Append enum value name if available
        $valLabel = Resolve-SettingValue -Id $_.Id -Value ([uint32]$(if ($Effective) { $effVal } else { $_.Value }))
        $valSuffix = if ($valLabel) { " ($valLabel)" } else { "" }
        if ($Effective) {
            $layer = if ($_.Value -ne 0) { 'override' } elseif ($_.PredefinedValue -ne 0) { 'predefined' } else { 'zero' }
            $mod = if ($_.Value -ne 0 -and $_.PredefinedValue -ne 0 -and $_.Value -ne $_.PredefinedValue) { " [overrides $pre]" } else { "" }
            Write-Output ("  {0,-60} {1}{2}  ({3}/{4}){5}" -f $label, $eff, $valSuffix, $loc, $layer, $mod)
        } else {
            $mod = if ($_.Value -ne $_.PredefinedValue -and $_.PredefinedValue -ne 0) { " [MOD from $pre]" } else { "" }
            Write-Output ("  {0,-65} {1}{2}  ({3}){4}" -f $label, $cur, $valSuffix, $loc, $mod)
        }
    }

    # --- Watch mode: poll for changes ---
    if ($Watch) {
        if (-not $Profile -and -not $Global) {
            Write-Warning "Watch mode requires -Profile or -Global."
            return
        }
        Write-Host "`n--- Watch mode (${Interval}s interval) | Ctrl+C to stop ---" -ForegroundColor Cyan
        Write-Host "  Subprocess polling (fresh NVAPI per poll — defeats DLL cache)" -ForegroundColor DarkGray

        # Build initial snapshot from current settings (already loaded in this process)
        $prev = @{}
        $prevPre = @{}
        $prevEff = @{}
        $nameMap = @{}
        foreach ($s in $settings) {
            $key = $s.Id.ToString()
            $prev[$key] = $s.Value
            $prevPre[$key] = $s.PredefinedValue
            $eff = if ($s.Value -ne 0) { $s.Value } elseif ($s.PredefinedValue -ne 0) { $s.PredefinedValue } else { $s.Value }
            $prevEff[$key] = $eff
            $nameMap[$key] = $s.Name
        }
        $prevDrs = @{}  # DRS file timestamps
        Write-Host "  Tracking $($prev.Count) settings (cur+pre+eff) + DRS file timestamps" -ForegroundColor DarkGray

        # Build subprocess command args
        $scriptPath = $PSCommandPath
        $subArgs = @('-NoProfile', '-File', $scriptPath, '-Snapshot')
        if ($Global) { $subArgs += '-Global' }
        else { $subArgs += '-Profile'; $subArgs += $Profile }
        if ($Filter) { $subArgs += '-Filter'; $subArgs += $Filter }

        $tick = 0
        try {
            while ($true) {
                Start-Sleep -Seconds $Interval
                $tick++

                # Spawn fresh process — completely new NVAPI init, no cache
                $raw = & pwsh @subArgs 2>$null
                if (-not $raw) {
                    $spinner = @('|','/','-','\')[$tick % 4]
                    Write-Host -NoNewline "`r  $spinner Watching... (${tick} polls, subprocess error)   " -ForegroundColor Red
                    continue
                }

                $snapObj = $raw | ConvertFrom-Json
                $snap = $snapObj.settings
                $drsNow = $snapObj.drsFiles

                # Check DRS file-level changes first
                if ($prevDrs.Count -gt 0 -and $drsNow) {
                    foreach ($fname in @('nvdrsdb0.bin','nvdrsdb1.bin','nvdrssel.bin')) {
                        $df = $drsNow.$fname
                        $dp = $prevDrs[$fname]
                        if ($df -and $dp) {
                            if ($df.mtime -ne $dp.mtime -or $df.size -ne $dp.size) {
                                $ts = Get-Date -Format "HH:mm:ss"
                                Write-Host "`n[$ts] DRS FILE CHANGED: $fname" -ForegroundColor Magenta
                                Write-Host "  Size: $($dp.size) -> $($df.size) bytes" -ForegroundColor Magenta
                                Write-Host "  Modified: $($dp.mtime) -> $($df.mtime)" -ForegroundColor Magenta
                            }
                        }
                    }
                }
                # Store current DRS state
                $prevDrs = @{}
                if ($drsNow) {
                    foreach ($fname in @('nvdrsdb0.bin','nvdrsdb1.bin','nvdrssel.bin')) {
                        $df = $drsNow.$fname
                        if ($df) { $prevDrs[$fname] = @{ mtime = $df.mtime; size = $df.size } }
                    }
                }

                # Convert PSObject to hashtable for comparison
                # Track three layers: current (delta), predefined, effective
                $curr = @{}
                $currPre = @{}
                $currEff = @{}
                foreach ($prop in $snap.PSObject.Properties) {
                    $curr[$prop.Name] = [uint32]$prop.Value.v
                    $currPre[$prop.Name] = [uint32]$prop.Value.p
                    $currEff[$prop.Name] = [uint32]$prop.Value.e
                    if (-not $nameMap.ContainsKey($prop.Name)) {
                        $nameMap[$prop.Name] = $prop.Value.n
                    }
                }

                $changes = @()
                # Check for changed/new settings (compare effective value)
                foreach ($key in $currEff.Keys) {
                    $name = $nameMap[$key]
                    $newEff = $currEff[$key]
                    $newCur = $curr[$key]
                    $newPre = $currPre[$key]
                    if (-not $prevEff.ContainsKey($key)) {
                        $changes += [PSCustomObject]@{ Name=$name; Id=[uint32]$key; Old=$null; New=$newEff; Tag="NEW"; Detail="cur=0x$($newCur.ToString('X8')) pre=0x$($newPre.ToString('X8'))" }
                    } else {
                        $oldEff = $prevEff[$key]
                        $oldCur = $prev[$key]
                        $oldPre = $prevPre[$key]
                        # Detect any layer change: effective, current, or predefined
                        if ($newEff -ne $oldEff) {
                            $changes += [PSCustomObject]@{ Name=$name; Id=[uint32]$key; Old=$oldEff; New=$newEff; Tag="CHG"; Detail="eff changed" }
                        } elseif ($newCur -ne $oldCur) {
                            $changes += [PSCustomObject]@{ Name=$name; Id=[uint32]$key; Old=$oldCur; New=$newCur; Tag="CUR"; Detail="delta layer changed (eff same)" }
                        } elseif ($newPre -ne $oldPre) {
                            $changes += [PSCustomObject]@{ Name=$name; Id=[uint32]$key; Old=$oldPre; New=$newPre; Tag="PRE"; Detail="predefined changed" }
                        }
                    }
                }
                # Check for removed settings
                foreach ($key in $prevEff.Keys) {
                    if (-not $currEff.ContainsKey($key)) {
                        $name = if ($nameMap.ContainsKey($key)) { $nameMap[$key] } else { "0x$([uint32]$key.ToString('X8'))" }
                        $changes += [PSCustomObject]@{ Name=$name; Id=[uint32]$key; Old=$prevEff[$key]; New=$null; Tag="DEL"; Detail="" }
                    }
                }

                if ($changes.Count -gt 0) {
                    $ts = Get-Date -Format "HH:mm:ss"
                    Write-Host "`n[$ts] $($changes.Count) change(s) detected:" -ForegroundColor Yellow
                    foreach ($c in $changes) {
                        $sidHex = "0x{0:X8}" -f $c.Id
                        $oldHex = if ($null -ne $c.Old) { "0x{0:X8}" -f $c.Old } else { "(none)" }
                        $newHex = if ($null -ne $c.New) { "0x{0:X8}" -f $c.New } else { "(removed)" }
                        $color = switch ($c.Tag) { "NEW" {"Green"} "DEL" {"Red"} "PRE" {"Magenta"} "CUR" {"DarkYellow"} default {"Yellow"} }
                        $detail = if ($c.Detail) { " ($($c.Detail))" } else { "" }
                        Write-Host "  [$($c.Tag)] $($c.Name) [$sidHex]: $oldHex -> $newHex$detail" -ForegroundColor $color
                    }
                } else {
                    $spinner = @('|','/','-','\')[$tick % 4]
                    Write-Host -NoNewline "`r  $spinner Watching... (${tick} polls, no changes)   " -ForegroundColor DarkGray
                }
                # Update all snapshot layers
                $prev = $curr
                $prevPre = $currPre
                $prevEff = $currEff
            }
        } catch [System.Management.Automation.PipelineStoppedException] {
            # Ctrl+C — clean exit
        } finally {
            Write-Host "`n--- Watch stopped ---" -ForegroundColor Cyan
        }
    }

} catch {
    Write-Error "NVAPI Error: $_"
} finally {
    try { [NvAPI]::Cleanup() } catch {}
}
