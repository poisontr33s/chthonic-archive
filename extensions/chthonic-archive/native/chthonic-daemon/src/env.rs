use std::path::PathBuf;

use anyhow::Result;

use crate::types::{AnnoManifest, EnvReport, PathSegment, ToolOwner};

/// Build the environment provisioning report based on the ANNO manifest.
///
/// This constructs PATH mutation order for rustified owners (`uv`, `rv`,
/// `goup`, `bun`, `mise`) for deterministic workspace activation.
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
                if let Some(bun_dir) = locate_bun_dir() {
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
