use std::collections::HashMap;
use std::path::Path;

use anyhow::Result;

use crate::types::{
    AnnoManifest, DetectedMarker, LanguagePolicy, MarkerKind, ToolOwner,
};

/// Scan `workspace` for project marker files and build the ANNO manifest.
///
/// The manifest declares tool ownership per language. Python stays on `uv`
/// to avoid shim races, while Ruby/Go use dedicated rustified lanes
/// (`rv`, `goup`) and the JS/TS lane defaults to `bun`.
pub fn detect_project(workspace: &str) -> Result<AnnoManifest> {
    let root = Path::new(workspace);
    let mut markers = Vec::new();
    let mut languages = Vec::new();
    let mut warnings = Vec::new();

    // -----------------------------------------------------------------------
    // Phase 1: Scan for marker files
    // -----------------------------------------------------------------------

    let marker_checks: &[(&str, MarkerKind, &str)] = &[
        ("pyproject.toml", MarkerKind::PythonPyproject, "python"),
        ("requirements.txt", MarkerKind::PythonRequirements, "python"),
        (".ruby-version", MarkerKind::RubyVersion, "ruby"),
        ("Gemfile", MarkerKind::RubyGemfile, "ruby"),
        ("Cargo.toml", MarkerKind::CargoToml, "rust"),
        ("package.json", MarkerKind::PackageJson, "javascript"),
        ("go.mod", MarkerKind::GoMod, "go"),
        ("Anchor.toml", MarkerKind::SolanaAnchorToml, "solana"),
        (".mise.toml", MarkerKind::MiseToml, ""),
        ("mise.toml", MarkerKind::MiseToml, ""),
        ("anno-manifest.toml", MarkerKind::AnnoManifest, ""),
    ];

    let mut seen_languages = std::collections::HashSet::new();

    for &(filename, kind, lang) in marker_checks {
        let candidate = root.join(filename);
        if candidate.exists() {
            markers.push(DetectedMarker {
                path: filename.to_string(),
                kind,
            });
            if !lang.is_empty() {
                seen_languages.insert(lang.to_string());
            }
        }
    }

    // Also check .chthonic/ subdirectories for sidecar markers
    if root.join(".chthonic").join("python").exists() {
        seen_languages.insert("python".to_string());
    }
    if root.join(".chthonic").join("ruby").exists() {
        seen_languages.insert("ruby".to_string());
    }

    // -----------------------------------------------------------------------
    // Phase 2: Assign tool ownership per language
    // -----------------------------------------------------------------------

    for lang in &seen_languages {
        let (tool, priority) = default_tool_for_language(lang);
        languages.push(LanguagePolicy {
            language: lang.clone(),
            tool,
            shim_priority: priority,
        });
    }

    // -----------------------------------------------------------------------
    // Phase 3: Read anno-manifest.toml overrides (if present)
    // -----------------------------------------------------------------------

    let anno_path = root.join("anno-manifest.toml");
    if anno_path.exists() {
        if let Err(err) = apply_manifest_overrides(&anno_path, &mut languages, &mut warnings) {
            warnings.push(format!("anno-manifest.toml parse error: {err}"));
        }
    }

    // -----------------------------------------------------------------------
    // Phase 4: Validate mise.toml for shim-race violations
    // -----------------------------------------------------------------------

    for mise_name in &[".mise.toml", "mise.toml"] {
        let mise_path = root.join(mise_name);
        if mise_path.exists() {
            check_mise_shim_race(&mise_path, &mut warnings);
        }
    }

    // -----------------------------------------------------------------------
    // Phase 5: Shim-race guard (INVARIANT)
    // -----------------------------------------------------------------------

    resolve_shim_conflicts(&mut languages, &mut warnings);

    // Build tool_owners map (binary name -> owner)
    let mut tool_owners = HashMap::new();
    for policy in &languages {
        let binaries = binaries_for_policy(policy);
        for bin in binaries {
            tool_owners.insert(bin.to_string(), policy.tool);
        }
    }

    // Force Python binary ownership to uv regardless (shim-race guard).
    for bin in &["python", "python3", "pip", "pip3", "uvx"] {
        tool_owners.insert((*bin).to_string(), ToolOwner::Uv);
    }

    Ok(AnnoManifest {
        languages,
        tool_owners,
        detected_markers: markers,
        warnings,
    })
}

/// Default tool assignment per language.
fn default_tool_for_language(lang: &str) -> (ToolOwner, u8) {
    match lang {
        "python" => (ToolOwner::Uv, 0),
        "ruby" => (ToolOwner::Rv, 1),
        "go" => (ToolOwner::Goup, 3),
        "javascript" | "typescript" => (ToolOwner::Bun, 4),
        "rust" => (ToolOwner::Rustup, 20),
        "solana" | "java" => (ToolOwner::Mise, 10),
        _ => (ToolOwner::System, 99),
    }
}

/// Which binary names does a language claim for a given owner?
fn binaries_for_policy(policy: &LanguagePolicy) -> &[&str] {
    match policy.language.as_str() {
        "python" => &["python", "python3", "pip", "pip3"],
        "ruby" => &["ruby", "gem", "bundle", "bundler", "rake"],
        "javascript" | "typescript" => match policy.tool {
            ToolOwner::Bun => &["bun", "bunx", "node", "npm", "npx", "corepack"],
            ToolOwner::Mise => &["node", "npm", "npx", "corepack"],
            _ => &["node", "npm", "npx", "corepack"],
        },
        "rust" => &["cargo", "rustc", "rustup"],
        "go" => &["go", "gofmt"],
        "solana" => &["solana", "anchor", "solana-test-validator"],
        _ => &[],
    }
}

/// Enforce shim-race invariants: uv owns Python, rv owns Ruby.
fn resolve_shim_conflicts(languages: &mut Vec<LanguagePolicy>, warnings: &mut Vec<String>) {
    for policy in languages.iter_mut() {
        if policy.language == "python" && policy.tool != ToolOwner::Uv {
            warnings.push(format!(
                "shim-race guard: overriding python tool from {:?} to uv (exclusive ownership)",
                policy.tool,
            ));
            policy.tool = ToolOwner::Uv;
            policy.shim_priority = 0;
        }
        if policy.language == "ruby" && policy.tool != ToolOwner::Rv {
            warnings.push(format!(
                "shim-race guard: overriding ruby tool from {:?} to rv (exclusive ownership)",
                policy.tool,
            ));
            policy.tool = ToolOwner::Rv;
            policy.shim_priority = 1;
        }
    }
}

/// Check mise.toml for Python tool entries that would cause a shim race.
fn check_mise_shim_race(mise_path: &Path, warnings: &mut Vec<String>) {
    let content = match std::fs::read_to_string(mise_path) {
        Ok(c) => c,
        Err(_) => return,
    };
    let table: toml::Table = match content.parse() {
        Ok(t) => t,
        Err(_) => return,
    };

    if let Some(tools) = table.get("tools").and_then(|v| v.as_table()) {
        if tools.contains_key("python") {
            warnings.push(format!(
                "SHIM RACE: {path} declares [tools.python]. \
                 This conflicts with uv's exclusive Python ownership. \
                 Remove python from mise.toml [tools] or set [settings] disable_tools = [\"python\"].",
                path = mise_path.display(),
            ));
        }
    }
}

/// Apply overrides from an existing `anno-manifest.toml`.
fn apply_manifest_overrides(
    path: &Path,
    languages: &mut Vec<LanguagePolicy>,
    warnings: &mut Vec<String>,
) -> Result<()> {
    let content = std::fs::read_to_string(path)?;
    let table: toml::Table = content.parse()?;

    let ownership = match table.get("ownership").and_then(|v| v.as_table()) {
        Some(t) => t,
        None => return Ok(()),
    };

    for (lang, tool_val) in ownership {
        let tool_str = tool_val.as_str().unwrap_or("system");
        let tool = match tool_str {
            "uv" => ToolOwner::Uv,
            "rv" => ToolOwner::Rv,
            "goup" => ToolOwner::Goup,
            "mise" => ToolOwner::Mise,
            "bun" => ToolOwner::Bun,
            "rustup" => ToolOwner::Rustup,
            _ => {
                warnings.push(format!("anno-manifest.toml: unknown tool '{tool_str}' for {lang}"));
                ToolOwner::System
            }
        };

        // Override or add
        if let Some(existing) = languages.iter_mut().find(|p| p.language == *lang) {
            existing.tool = tool;
        } else {
            let (_, default_priority) = default_tool_for_language(lang);
            languages.push(LanguagePolicy {
                language: lang.clone(),
                tool,
                shim_priority: default_priority,
            });
        }
    }

    Ok(())
}
