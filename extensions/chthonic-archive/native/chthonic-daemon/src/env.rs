use std::path::PathBuf;

use anyhow::Result;

use crate::types::{AnnoManifest, EnvReport, PathSegment, ToolOwner};

#[cfg(windows)]
use crate::types::DevKitReport;

/// Build the environment provisioning report based on the ANNO manifest.
///
/// This constructs PATH mutation order for rustified owners (`uv`, `rv`,
/// `goup`, `fnm`/`volta`, `mise`) and detects MSYS2/UCRT64 DevKit on Windows
/// for Ruby native gems.
pub fn provision(manifest: &AnnoManifest, _workspace: &str) -> Result<EnvReport> {
    let mut report = EnvReport::default();

    // -------------------------------------------------------------------
    // PATH construction: ordered by shim priority (lower = earlier on PATH)
    // -------------------------------------------------------------------

    let mut segments: Vec<PathSegment> = Vec::new();

    if manifest.has_language("python") {
        if let Some(uv_dir) = locate_uv_shim_dir() {
            segments.push(PathSegment {
                path: uv_dir,
                owner: "uv".to_string(),
                priority: 0,
            });
        } else {
            report
                .warnings
                .push("uv shim directory not found; Python resolution may fail".to_string());
        }
    }

    if manifest.has_language("ruby") {
        if let Some(rv_dir) = locate_rv_shim_dir() {
            segments.push(PathSegment {
                path: rv_dir,
                owner: "rv".to_string(),
                priority: 1,
            });
        } else {
            report
                .warnings
                .push("rv shim directory not found; Ruby resolution may fail".to_string());
        }
    }

    if manifest.has_language("go") {
        match preferred_owner_for_language(manifest, "go") {
            Some(ToolOwner::Goup) => {
                if let Some(goup_dir) = locate_goup_bin_dir() {
                    segments.push(PathSegment {
                        path: goup_dir,
                        owner: "goup".to_string(),
                        priority: 3,
                    });
                } else {
                    report.warnings.push(
                        "goup ownership selected but ~/.goup/current/bin was not found".to_string(),
                    );
                }
            }
            _ => {}
        }
    }

    if manifest.has_language("javascript") || manifest.has_language("typescript") {
        match preferred_js_owner(manifest) {
            Some(ToolOwner::Fnm) => {
                if let Some(fnm_dir) = locate_fnm_bin_dir() {
                    segments.push(PathSegment {
                        path: fnm_dir,
                        owner: "fnm".to_string(),
                        priority: 4,
                    });
                } else {
                    report.warnings.push(
                        "fnm ownership selected but fnm directory was not found".to_string(),
                    );
                }
            }
            Some(ToolOwner::Volta) => {
                if let Some(volta_dir) = locate_volta_bin_dir() {
                    segments.push(PathSegment {
                        path: volta_dir,
                        owner: "volta".to_string(),
                        priority: 6,
                    });
                } else {
                    report.warnings.push(
                        "volta ownership selected but ~/.volta/bin was not found".to_string(),
                    );
                }
            }
            Some(ToolOwner::Bun) => {
                if let Some(bun_dir) = locate_bun_dir() {
                    segments.push(PathSegment {
                        path: bun_dir,
                        owner: "bun".to_string(),
                        priority: 5,
                    });
                } else {
                    report.warnings.push(
                        "bun ownership selected but bun bin directory was not found".to_string(),
                    );
                }
            }
            _ => {
                if let Some(fnm_dir) = locate_fnm_bin_dir() {
                    segments.push(PathSegment {
                        path: fnm_dir,
                        owner: "fnm".to_string(),
                        priority: 4,
                    });
                } else if let Some(volta_dir) = locate_volta_bin_dir() {
                    segments.push(PathSegment {
                        path: volta_dir,
                        owner: "volta".to_string(),
                        priority: 6,
                    });
                } else if let Some(bun_dir) = locate_bun_dir() {
                    segments.push(PathSegment {
                        path: bun_dir,
                        owner: "bun".to_string(),
                        priority: 5,
                    });
                }
            }
        }
    }

    if manifest.needs_mise() {
        if let Some(mise_dir) = locate_mise_shim_dir() {
            segments.push(PathSegment {
                path: mise_dir,
                owner: "mise".to_string(),
                priority: 10,
            });
        }
    }

    // Sort by priority (lowest first = highest on PATH)
    segments.sort_by_key(|s| s.priority);
    report.path_mutations = segments;

    // -------------------------------------------------------------------
    // MSYS2/UCRT64 DevKit for Ruby on Windows
    // -------------------------------------------------------------------

    #[cfg(windows)]
    if manifest.has_language("ruby") {
        match detect_msys2_devkit() {
            Ok(Some(dk)) => report.dev_kit = Some(dk),
            Ok(None) => report.warnings.push(
                "Ruby detected but MSYS2/UCRT64 DevKit not found. \
                 Native gems will fail to compile. \
                 Install RubyInstaller DevKit or place MSYS2 at C:\\DevKit\\msys64."
                    .to_string(),
            ),
            Err(err) => report
                .warnings
                .push(format!("DevKit detection error: {err}")),
        }
    }

    Ok(report)
}

// ---------------------------------------------------------------------------
// Tool directory locators
// ---------------------------------------------------------------------------

fn locate_uv_shim_dir() -> Option<String> {
    // uv installs to ~/.local/bin on Unix, %LOCALAPPDATA%\uv on Windows
    if cfg!(windows) {
        let local_app = std::env::var("LOCALAPPDATA").ok()?;
        let dir = PathBuf::from(&local_app).join("uv");
        if dir.exists() {
            return Some(dir.to_string_lossy().into_owned());
        }
        // Also check %USERPROFILE%\.local\bin (uv's alternate location)
        let home = std::env::var("USERPROFILE").ok()?;
        let alt = PathBuf::from(&home).join(".local").join("bin");
        if alt.exists() {
            return Some(alt.to_string_lossy().into_owned());
        }
    } else {
        let home = std::env::var("HOME").ok()?;
        let dir = PathBuf::from(&home).join(".local").join("bin");
        if dir.exists() {
            return Some(dir.to_string_lossy().into_owned());
        }
    }
    None
}

fn locate_rv_shim_dir() -> Option<String> {
    // rv installs to ~/.cargo/bin (rv.exe, rvw.exe) but the managed Ruby
    // lives at %APPDATA%/rv/rubies/<version>/bin on Windows,
    // or ~/.local/share/rv/rubies/<version>/bin on Unix.
    //
    // We find the active Ruby's bin/ directory by looking for rv's rubies.
    if cfg!(windows) {
        let appdata = std::env::var("APPDATA").ok()?;
        let rubies_dir = PathBuf::from(&appdata).join("rv").join("rubies");
        if rubies_dir.exists() {
            // Find the first (or latest) installed Ruby
            let mut entries: Vec<_> = std::fs::read_dir(&rubies_dir)
                .ok()?
                .filter_map(|e| e.ok())
                .filter(|e| e.file_type().ok().is_some_and(|ft| ft.is_dir()))
                .collect();
            entries.sort_by(|a, b| b.file_name().cmp(&a.file_name())); // newest first
            if let Some(latest) = entries.first() {
                let bin = latest.path().join("bin");
                if bin.exists() {
                    return Some(bin.to_string_lossy().into_owned());
                }
            }
        }
    } else {
        let home = std::env::var("HOME").ok()?;
        let rubies_dir = PathBuf::from(&home)
            .join(".local")
            .join("share")
            .join("rv")
            .join("rubies");
        if rubies_dir.exists() {
            let mut entries: Vec<_> = std::fs::read_dir(&rubies_dir)
                .ok()?
                .filter_map(|e| e.ok())
                .filter(|e| e.file_type().ok().is_some_and(|ft| ft.is_dir()))
                .collect();
            entries.sort_by(|a, b| b.file_name().cmp(&a.file_name()));
            if let Some(latest) = entries.first() {
                let bin = latest.path().join("bin");
                if bin.exists() {
                    return Some(bin.to_string_lossy().into_owned());
                }
            }
        }
    }
    None
}

fn locate_goup_bin_dir() -> Option<String> {
    if cfg!(windows) {
        let home = std::env::var("USERPROFILE").ok()?;
        let dir = PathBuf::from(&home).join(".goup").join("current").join("bin");
        if dir.exists() {
            return Some(dir.to_string_lossy().into_owned());
        }
    } else {
        let home = std::env::var("HOME").ok()?;
        let dir = PathBuf::from(&home).join(".goup").join("current").join("bin");
        if dir.exists() {
            return Some(dir.to_string_lossy().into_owned());
        }
    }
    None
}

fn locate_mise_shim_dir() -> Option<String> {
    // mise shims live at ~/.local/share/mise/shims
    let data_dir = if cfg!(windows) {
        std::env::var("LOCALAPPDATA")
            .ok()
            .map(|d| PathBuf::from(d).join("mise").join("shims"))
    } else {
        std::env::var("HOME")
            .ok()
            .map(|h| PathBuf::from(h).join(".local").join("share").join("mise").join("shims"))
    };

    data_dir.and_then(|d| {
        if d.exists() {
            Some(d.to_string_lossy().into_owned())
        } else {
            None
        }
    })
}

fn locate_bun_dir() -> Option<String> {
    if cfg!(windows) {
        let home = std::env::var("USERPROFILE").ok()?;
        let dir = PathBuf::from(&home).join(".bun").join("bin");
        if dir.exists() {
            return Some(dir.to_string_lossy().into_owned());
        }
    } else {
        let home = std::env::var("HOME").ok()?;
        let dir = PathBuf::from(&home).join(".bun").join("bin");
        if dir.exists() {
            return Some(dir.to_string_lossy().into_owned());
        }
    }
    None
}

fn locate_volta_bin_dir() -> Option<String> {
    if cfg!(windows) {
        let home = std::env::var("USERPROFILE").ok()?;
        let dir = PathBuf::from(&home).join(".volta").join("bin");
        if dir.exists() {
            return Some(dir.to_string_lossy().into_owned());
        }
    } else {
        let home = std::env::var("HOME").ok()?;
        let dir = PathBuf::from(&home).join(".volta").join("bin");
        if dir.exists() {
            return Some(dir.to_string_lossy().into_owned());
        }
    }
    None
}

fn locate_fnm_bin_dir() -> Option<String> {
    if cfg!(windows) {
        let mut candidates: Vec<PathBuf> = Vec::new();
        if let Ok(appdata) = std::env::var("APPDATA") {
            candidates.push(PathBuf::from(&appdata).join("fnm"));
        }
        if let Ok(local_app) = std::env::var("LOCALAPPDATA") {
            candidates.push(PathBuf::from(&local_app).join("fnm"));
        }
        if let Ok(home) = std::env::var("USERPROFILE") {
            candidates.push(PathBuf::from(&home).join(".fnm"));
        }
        for candidate in candidates {
            if candidate.exists() {
                return Some(candidate.to_string_lossy().into_owned());
            }
        }
    } else {
        let home = std::env::var("HOME").ok()?;
        let dir = PathBuf::from(&home).join(".fnm");
        if dir.exists() {
            return Some(dir.to_string_lossy().into_owned());
        }
    }
    None
}

fn preferred_owner_for_language(manifest: &AnnoManifest, language: &str) -> Option<ToolOwner> {
    manifest
        .languages
        .iter()
        .find(|policy| policy.language == language)
        .map(|policy| policy.tool)
}

fn preferred_js_owner(manifest: &AnnoManifest) -> Option<ToolOwner> {
    manifest
        .languages
        .iter()
        .find(|policy| policy.language == "javascript" || policy.language == "typescript")
        .map(|policy| policy.tool)
}

// ---------------------------------------------------------------------------
// MSYS2/UCRT64 DevKit detection (Windows only)
// ---------------------------------------------------------------------------

#[cfg(windows)]
fn detect_msys2_devkit() -> Result<Option<DevKitReport>> {
    let search_roots: Vec<PathBuf> = [
        ruby_install_root(),
        // RubyInstaller DevKit locations (primary source for UCRT64 toolchain)
        Some(PathBuf::from(r"C:\Ruby40-x64")),
        Some(PathBuf::from(r"C:\Ruby35-x64")),
        Some(PathBuf::from(r"C:\Ruby34-x64")),
        Some(PathBuf::from(r"C:\Ruby33-x64")),
        Some(PathBuf::from(r"C:\Ruby32-x64")),
        // Standalone MSYS2 (if DevKit extracted separately)
        // C:\DevKit\msys64 or C:\msys64 (root = C:\)
        Some(PathBuf::from(r"C:\DevKit")),
        Some(PathBuf::from(r"C:\")),
    ]
    .into_iter()
    .flatten()
    .collect();

    for root in &search_roots {
        let msys2_dir = root.join("msys64");
        let ucrt64_bin = msys2_dir.join("ucrt64").join("bin");
        let perl = msys2_dir.join("usr").join("bin").join("perl.exe");

        if ucrt64_bin.exists() && perl.exists() {
            let gcc = ucrt64_bin.join("gcc.exe");
            let gxx = ucrt64_bin.join("g++.exe");

            return Ok(Some(DevKitReport {
                msys2_home: msys2_dir.to_string_lossy().into_owned(),
                ucrt64_bin: ucrt64_bin.to_string_lossy().into_owned(),
                perl_path: perl.to_string_lossy().into_owned(),
                cc: gcc.to_string_lossy().into_owned(),
                cxx: gxx.to_string_lossy().into_owned(),
                env_vars: vec![
                    ("MSYS2_HOME".to_string(), msys2_dir.to_string_lossy().into_owned()),
                    ("CC".to_string(), "gcc".to_string()),
                    ("CXX".to_string(), "g++".to_string()),
                    ("RI_DEVKIT".to_string(), msys2_dir.to_string_lossy().into_owned()),
                ],
                path_prepend: vec![
                    ucrt64_bin.to_string_lossy().into_owned(),
                    msys2_dir.join("usr").join("bin").to_string_lossy().into_owned(),
                ],
            }));
        }
    }

    Ok(None)
}

/// Try to determine the Ruby install root from the `ruby` binary on PATH.
#[cfg(windows)]
fn ruby_install_root() -> Option<PathBuf> {
    let output = std::process::Command::new("ruby")
        .args(["-e", "print RbConfig.ruby"])
        .output()
        .ok()?;

    if !output.status.success() {
        return None;
    }

    let ruby_exe = String::from_utf8_lossy(&output.stdout);
    let ruby_exe = ruby_exe.trim();
    if ruby_exe.is_empty() {
        return None;
    }

    std::path::Path::new(ruby_exe).parent()?.parent().map(std::path::Path::to_path_buf)
}
