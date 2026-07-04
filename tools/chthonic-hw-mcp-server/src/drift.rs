// Compares live hw_inspect state against the two frontier docs. Table cells
// are extracted via pulldown-cmark's event stream (tracking TableCell start/
// end boundaries so multi-run cells — plain text mixed with **bold** — join
// into one string per cell, not one entry per text run).
//
// Matching is intentionally small and explicit: a fixed rule list mapping a
// doc-table component label to a live HwInventory accessor, rather than a
// generic schema-inference layer. The frontier docs are hand-maintained
// prose tables, not a stable machine schema — over-generalizing the matcher
// would be solving a problem that doesn't exist yet.

use std::path::Path;

use pulldown_cmark::{Event, Options, Parser, Tag, TagEnd};
use serde::{Deserialize, Serialize};

use crate::HwInventory;

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq)]
pub enum Severity {
    Info,
    Warning,
    Critical,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct DriftEntry {
    pub component: String,
    pub expected_version: Option<String>,
    pub actual_version: Option<String>,
    pub severity: Severity,
    pub is_legitimate_variation: bool,
    pub rationale: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct DriftReport {
    pub is_synchronized: bool,
    pub checked_at_unix: u64,
    pub entries: Vec<DriftEntry>,
}

fn extract_table_rows(markdown: &str) -> Vec<Vec<String>> {
    let mut options = Options::empty();
    options.insert(Options::ENABLE_TABLES);
    let parser = Parser::new_ext(markdown, options);

    let mut rows = Vec::new();
    let mut current_row: Vec<String> = Vec::new();
    let mut current_cell = String::new();
    let mut in_cell = false;

    for event in parser {
        match event {
            Event::Start(Tag::TableCell) => {
                in_cell = true;
                current_cell.clear();
            }
            Event::End(TagEnd::TableCell) => {
                in_cell = false;
                current_row.push(current_cell.trim().to_string());
            }
            Event::Start(Tag::TableRow) => {
                current_row = Vec::new();
            }
            Event::End(TagEnd::TableRow) => {
                if !current_row.is_empty() {
                    rows.push(std::mem::take(&mut current_row));
                }
            }
            Event::Text(text) if in_cell => current_cell.push_str(&text),
            Event::Code(text) if in_cell => current_cell.push_str(&text),
            _ => {}
        }
    }
    rows
}

/// Pulls the first version-like token (digits/dots) out of a doc cell, e.g.
/// "**610.62**" -> "610.62", "SDK: `C:\VulkanSDK\1.4.350.0` · Instance 1.4.350"
/// -> "1.4.350.0" (first match).
fn first_version_token(cell: &str) -> Option<String> {
    let mut token = String::new();
    let mut in_token = false;
    for ch in cell.chars() {
        if ch.is_ascii_digit() || (in_token && ch == '.') {
            token.push(ch);
            in_token = true;
        } else if in_token {
            if token.contains('.') || token.len() > 1 {
                return Some(token.trim_end_matches('.').to_string());
            }
            token.clear();
            in_token = false;
        }
    }
    if in_token && (token.contains('.') || token.len() > 1) {
        return Some(token.trim_end_matches('.').to_string());
    }
    None
}

fn find_row<'a>(rows: &'a [Vec<String>], label_contains: &str) -> Option<&'a Vec<String>> {
    rows.iter().find(|row| {
        row.first()
            .map(|c| c.to_lowercase().contains(&label_contains.to_lowercase()))
            .unwrap_or(false)
    })
}

fn compare(
    component: &str,
    expected_cell: Option<&str>,
    actual: Option<&String>,
    is_legitimate_variation: bool,
    variation_rationale: &str,
) -> DriftEntry {
    let expected_version = expected_cell.and_then(first_version_token);
    let actual_version = actual.cloned();

    let matches = match (&expected_version, &actual_version) {
        (Some(e), Some(a)) => a.starts_with(e.as_str()) || e.starts_with(a.as_str()),
        _ => false,
    };

    let (severity, rationale) = if matches {
        (Severity::Info, "matches documented baseline".to_string())
    } else if is_legitimate_variation {
        (Severity::Info, variation_rationale.to_string())
    } else if expected_version.is_none() || actual_version.is_none() {
        (
            Severity::Warning,
            "could not resolve one side of the comparison (doc row or live probe missing)"
                .to_string(),
        )
    } else {
        (
            Severity::Critical,
            format!(
                "documented {:?} but live probe reports {:?} — investigate",
                expected_version, actual_version
            ),
        )
    };

    DriftEntry {
        component: component.to_string(),
        expected_version,
        actual_version,
        severity,
        is_legitimate_variation: matches || is_legitimate_variation,
        rationale,
    }
}

pub fn check(repo_root: &Path, inv: &HwInventory) -> DriftReport {
    let checked_at_unix = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);

    let frontier_path = repo_root
        .join("docs")
        .join("reference")
        .join("COMPUTE_FRONTIER_LANDSCAPE.md");
    let dll_inventory_path = repo_root
        .join("docs")
        .join("reference")
        .join("NVIDIA_DLL_INVENTORY.md");

    let frontier_rows = std::fs::read_to_string(&frontier_path)
        .map(|text| extract_table_rows(&text))
        .unwrap_or_default();
    let dll_rows = std::fs::read_to_string(&dll_inventory_path)
        .map(|text| extract_table_rows(&text))
        .unwrap_or_default();

    let mut entries = Vec::new();

    entries.push(compare(
        "GPU driver",
        find_row(&frontier_rows, "GPU driver").and_then(|r| r.get(2)).map(String::as_str),
        inv.driver_version.as_ref(),
        false,
        "",
    ));

    entries.push(compare(
        "CUDA runtime max (UMD)",
        find_row(&frontier_rows, "CUDA runtime max").and_then(|r| r.get(2)).map(String::as_str),
        inv.cuda_umd_max.as_ref(),
        false,
        "",
    ));

    entries.push(compare(
        "Vulkan SDK",
        find_row(&frontier_rows, "Vulkan").and_then(|r| r.get(2)).map(String::as_str),
        inv.vulkan_sdk_path.as_ref().and_then(|_| {
            // Compare against the SDK version embedded in the path, e.g. .../1.4.350.0
            inv.vulkan_sdk_path
                .as_ref()
                .and_then(|p| p.split(['\\', '/']).last().map(str::to_string))
        }).as_ref(),
        false,
        "",
    ));

    entries.push(compare(
        "cuDNN",
        find_row(&frontier_rows, "cuDNN").and_then(|r| r.get(2)).map(String::as_str),
        inv.cudnn_version.as_ref(),
        false,
        "",
    ));

    // DLSS is a documented, expected-to-vary case: the doc records the newest
    // app-bundled copy found on disk, not a system-wide baseline. Any drift
    // here is informational (a newer SDK drop landed) rather than a fault.
    entries.push(compare(
        "DLSS (newest on disk)",
        find_row(&dll_rows, "nvngx_dlss.dll")
            .or_else(|| find_row(&frontier_rows, "DLSS"))
            .and_then(|r| r.get(1).or_else(|| r.get(2)))
            .map(String::as_str),
        inv.dlss_newest.as_ref().map(|d| &d.version),
        true,
        "DLSS is app-bundled and expected to vary by directory — informational only",
    ));

    for (dll_name, live_version) in &inv.dll_versions {
        let expected = find_row(&dll_rows, dll_name).and_then(|r| r.get(1)).map(String::as_str);
        if expected.is_some() {
            entries.push(compare(
                dll_name,
                expected,
                Some(live_version),
                false,
                "",
            ));
        }
    }

    let is_synchronized = entries
        .iter()
        .all(|e| e.severity != Severity::Critical);

    DriftReport {
        is_synchronized,
        checked_at_unix,
        entries,
    }
}
