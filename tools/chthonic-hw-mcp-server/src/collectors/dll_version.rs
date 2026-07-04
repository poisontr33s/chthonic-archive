// Win32 VersionInfo reader — GetFileVersionInfoSizeW/GetFileVersionInfoW/
// VerQueryValueW straight to VS_FIXEDFILEINFO, no PowerShell `.VersionInfo`
// indirection. Formats the version as a proper dotted string from the two
// packed dwFileVersionMS/LS DWORDs, sidestepping the comma-formatted
// FileVersion string PowerShell emits (worked around by hand earlier this
// session — see docs/reference/NVIDIA_DLL_INVENTORY.md history).

use std::collections::HashMap;
use std::ffi::c_void;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use windows::core::{w, HSTRING};
use windows::Win32::Storage::FileSystem::{
    GetFileVersionInfoSizeW, GetFileVersionInfoW, VerQueryValueW, VS_FIXEDFILEINFO,
};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct DllInfo {
    pub version: String,
    pub path: String,
}

pub fn read_dll_version(path: &Path) -> Option<String> {
    let path_str = path.to_str()?;
    let wide = HSTRING::from(path_str);

    unsafe {
        let size = GetFileVersionInfoSizeW(&wide, None);
        if size == 0 {
            return None;
        }

        let mut buffer = vec![0u8; size as usize];
        GetFileVersionInfoW(&wide, None, size, buffer.as_mut_ptr() as *mut c_void).ok()?;

        let mut fixed_info_ptr: *mut c_void = std::ptr::null_mut();
        let mut fixed_info_len: u32 = 0;
        let ok = VerQueryValueW(
            buffer.as_ptr() as *const c_void,
            w!("\\"),
            &mut fixed_info_ptr,
            &mut fixed_info_len,
        );
        if !ok.as_bool() || fixed_info_ptr.is_null() {
            return None;
        }

        let info = &*(fixed_info_ptr as *const VS_FIXEDFILEINFO);
        let ms = info.dwFileVersionMS;
        let ls = info.dwFileVersionLS;
        Some(format!(
            "{}.{}.{}.{}",
            (ms >> 16) & 0xffff,
            ms & 0xffff,
            (ls >> 16) & 0xffff,
            ls & 0xffff,
        ))
    }
}

const SYSTEM32_DRIVER_DLLS: &[&str] = &[
    "nvapi64.dll",
    "nvcuda.dll",
    "nvcuvid.dll",
    "nvEncodeAPI64.dll",
    "nvml.dll",
    "nvofapi64.dll",
    "NvFBC64.dll",
    "NvIFR64.dll",
];

pub fn system32_driver_dlls() -> HashMap<String, String> {
    let sys32 = Path::new(r"C:\Windows\System32");
    let mut out = HashMap::new();
    for name in SYSTEM32_DRIVER_DLLS {
        if let Some(ver) = read_dll_version(&sys32.join(name)) {
            out.insert((*name).to_string(), ver);
        }
    }
    out
}

fn version_sort_key(v: &str) -> (u32, u32, u32, u32) {
    let parts: Vec<u32> = v.split('.').filter_map(|p| p.parse().ok()).collect();
    (
        parts.first().copied().unwrap_or(0),
        parts.get(1).copied().unwrap_or(0),
        parts.get(2).copied().unwrap_or(0),
        parts.get(3).copied().unwrap_or(0),
    )
}

pub fn newest_dlss(repo_root: &Path) -> Option<DllInfo> {
    let candidates: Vec<PathBuf> = vec![
        repo_root
            .join("CLAUDEBASE")
            .join("The-Savant-High-Bounties")
            .join("streamline-sdk-v2.12.0")
            .join("bin")
            .join("x64")
            .join("nvngx_dlss.dll"),
        PathBuf::from(r"C:\Program Files (x86)\World of Warcraft\_retail_\nvngx_dlss.dll"),
        PathBuf::from(
            r"C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2\Bin\Win64Shared\nvngx_dlss.dll",
        ),
        PathBuf::from(
            r"C:\Program Files (x86)\Steam\steamapps\common\Path of Exile 2\Streamline\nvngx_dlss.dll",
        ),
    ];

    let found: Vec<DllInfo> = candidates
        .iter()
        .filter_map(|p| read_dll_version(p).map(|version| DllInfo {
            version,
            path: p.to_string_lossy().into_owned(),
        }))
        .collect();

    found.into_iter().max_by_key(|d| version_sort_key(&d.version))
}

fn find_first_matching(dir: &Path, filename: &str) -> Option<PathBuf> {
    let entries = std::fs::read_dir(dir).ok()?;
    for entry in entries.filter_map(|e| e.ok()) {
        let path = entry.path();
        if path.is_dir() {
            if let Some(found) = find_first_matching(&path, filename) {
                return Some(found);
            }
        } else if path.file_name().and_then(|n| n.to_str()) == Some(filename) {
            return Some(path);
        }
    }
    None
}

pub fn cudnn_state() -> (Option<String>, Option<String>) {
    let base = Path::new(r"C:\Program Files\NVIDIA\CUDNN");
    let Ok(entries) = std::fs::read_dir(base) else {
        return (None, None);
    };
    let latest_dir = entries
        .filter_map(|e| e.ok())
        .filter(|e| e.path().is_dir())
        .max_by_key(|e| e.file_name());

    let Some(dir) = latest_dir else {
        return (None, None);
    };

    let version =
        find_first_matching(&dir.path(), "cudnn_adv64_9.dll").and_then(|p| read_dll_version(&p));

    (version, Some(dir.path().to_string_lossy().into_owned()))
}
