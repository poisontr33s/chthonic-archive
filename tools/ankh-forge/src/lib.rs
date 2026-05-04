#![allow(
    clippy::missing_errors_doc,
    clippy::must_use_candidate,
    clippy::needless_pass_by_value
)]

pub mod schema;

use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Duration;

use anyhow::{Context, Result, anyhow, bail};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};

const LANE_EXCLUSION_PREFIXES: &[&str] = &[
    "extensions/chthonic-archive/themes/icons/product-outlined/",
    "extensions/chthonic-archive/themes/fonts/",
    "gemini/to_gemini_DR/",
];

const EXACT_EXCLUSIONS: &[&str] = &[
    "scripts/generate-product-icon-font.mjs",
    "scripts/product_icon_census.py",
    "scripts/theme-sync.ps1",
];

const KNOWN_COMPOUND_EXTENSIONS: &[&str] = &[
    ".d.ts",
    ".spec.js",
    ".spec.ts",
    ".test.js",
    ".test.ts",
    ".test.tsx",
];

const SOURCE_CODE_EXTENSIONS: &[&str] = &[
    ".bat", ".cjs", ".css", ".html", ".js", ".mjs", ".ps1", ".py", ".rb", ".rs", ".sh", ".ts",
    ".tsx",
];
const DATA_CONFIG_EXTENSIONS: &[&str] =
    &[".env", ".json", ".jsonl", ".lock", ".toml", ".yaml", ".yml"];
const BUILD_OUTPUT_EXTENSIONS: &[&str] = &[".db", ".png", ".pyc", ".tsbuildinfo", ".woff"];
const DOCUMENTATION_EXTENSIONS: &[&str] = &[".md", ".txt", ".md\""];
const VCS_META_EXTENSIONS: &[&str] = &[
    ".copilotignore",
    ".geminiignore",
    ".gitattributes",
    ".gitignore",
    ".gitkeep",
    ".keep",
    ".vscodeignore",
];
const GRAPHICS_GPU_EXTENSIONS: &[&str] = &[".comp", ".frag", ".svg", ".vert"];
const GOVERNANCE_EXTENSIONS: &[&str] = &[".bak", ".off", ".vsconfig"];
const DOMAIN_SPECIFIC_EXTENSIONS: &[&str] = &[".chthonic", ".python-version"];
const DAMAGED_EXTENSIONS: &[&str] = &[".md\""];

const PATHWAY_OVERRIDES: &[(&str, &str)] = &[
    (
        ".go",
        "Go CLI transmutation from shell/log automation patterns.",
    ),
    (
        ".cs",
        "C# contract reconstruction from TypeScript interfaces and JSON schemas.",
    ),
    (
        ".fsx",
        "F# typed automation pathway for data/config analysis.",
    ),
    (
        ".c",
        "C shim or header synthesis from Rust layout data and FFI seams.",
    ),
    (
        ".cpp",
        "C++ native helper extraction for performance-sensitive utility lanes.",
    ),
    (
        ".h",
        "Header projection for native interfaces and Rust FFI surfaces.",
    ),
    (
        ".pl",
        "Perl text archaeology utility for extraction-heavy mailbox and log flows.",
    ),
    (
        ".log",
        "Diagnostic playbook plus structured environment snapshot extraction.",
    ),
    (
        ".pyc",
        "Python contract stub reconstructed from bytecode metadata.",
    ),
    (
        ".off",
        "Workflow pattern catalogue plus migration manifest.",
    ),
    (".bat", "PowerShell transliteration with behavior notes."),
    (".env", "Environment schema and integration map."),
    (
        ".vsconfig",
        "Toolchain decision record and deterministic provisioning script.",
    ),
    (
        ".md\"",
        "Filename forensics note and clean-named canonical copy.",
    ),
    (
        ".json",
        "Schema archaeology and state-machine reconstruction.",
    ),
    (
        ".db",
        "Forensics pass first; then extract schema and provenance tables.",
    ),
    (
        ".woff",
        "WOFF header and glyph-map forensics for upstream artifact tracing.",
    ),
    (".png", "Binary forensics and asset provenance note."),
];

const MAGIC_PNG: &[u8] = &[0x89, b'P', b'N', b'G', 0x0D, 0x0A, 0x1A, 0x0A];
const MAGIC_WOFF: &[u8] = b"wOFF";
const MAGIC_SQLITE: &[u8] = b"SQLite format 3\0";

#[derive(Clone, Copy)]
enum OxidizedKind {
    Yes,
    No,
    SelfOxidizing,
    Honorary,
}

impl OxidizedKind {
    fn as_json(self) -> Value {
        match self {
            Self::Yes => Value::Bool(true),
            Self::No => Value::Bool(false),
            Self::SelfOxidizing => Value::String(String::from("self_oxidizing")),
            Self::Honorary => Value::String(String::from("honorary")),
        }
    }
}

#[derive(Clone)]
struct ToolchainSpec {
    key: &'static str,
    display_name: &'static str,
    runtime_cmd: &'static [&'static str],
    manager_cmd: Option<&'static [&'static str]>,
    alternate_manager_cmds: &'static [&'static [&'static str]],
    manager: Option<&'static str>,
    oxidized: OxidizedKind,
    eol_slug: Option<&'static str>,
    represented_extensions: &'static [&'static str],
}

#[derive(Clone, Serialize)]
pub struct ToolchainProbe {
    display_name: String,
    installed: bool,
    runtime_version: Option<String>,
    runtime_output: Option<String>,
    manager: Option<String>,
    manager_installed: bool,
    manager_version: Option<String>,
    #[serde(skip_serializing)]
    oxidized_kind: String,
    oxidized: Value,
    eol_slug: Option<String>,
}

#[derive(Clone, Deserialize)]
struct EolCycle {
    cycle: String,
    eol: Option<Value>,
    latest: Option<String>,
    #[serde(rename = "latestReleaseDate")]
    latest_release_date: Option<String>,
    support: Option<String>,
    #[serde(rename = "extendedSupport")]
    extended_support: Option<String>,
    link: Option<String>,
}

#[derive(Default, Clone)]
struct ExtensionStats {
    count: usize,
    directories: BTreeSet<String>,
    lane_excluded_count: usize,
}

pub fn emit_json(payload: Value, output: Option<PathBuf>) -> Result<()> {
    let rendered = serde_json::to_string_pretty(&payload)?;
    if let Some(path) = output {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).with_context(|| format!("creating {}", parent.display()))?;
        }
        fs::write(&path, format!("{rendered}\n"))
            .with_context(|| format!("writing {}", path.display()))?;
    } else {
        println!("{rendered}");
    }
    Ok(())
}

pub fn scan_command(root: &Path) -> Result<Value> {
    let repo_root = resolve_repo_root(root)?;
    let tracked = tracked_files(&repo_root)?;
    let probes = discover_toolchains()?;
    let eol = build_eol_report(&probes, &fetch_eol_cycle_live);

    let mut inventory: BTreeMap<String, Value> = BTreeMap::new();
    let mut categories: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
    let mut top_counts: BTreeMap<String, usize> = BTreeMap::new();
    let mut stats: BTreeMap<String, ExtensionStats> = BTreeMap::new();

    for rel_path in &tracked {
        let extension = extension_or_placeholder(compound_extension(rel_path));
        let entry = stats.entry(extension.clone()).or_default();
        entry.count += 1;
        let directory = rel_path
            .parent()
            .map_or_else(|| String::from("."), normalize_path);
        entry.directories.insert(directory);
        if path_is_excluded(rel_path) {
            entry.lane_excluded_count += 1;
        }

        categories
            .entry(extension_category(&extension).to_owned())
            .or_default()
            .insert(extension.clone());
        *top_counts.entry(extension).or_default() += 1;
    }

    for (extension, entry) in stats {
        let extension_for_support = if extension == "[no_ext]" {
            ""
        } else {
            extension.as_str()
        };
        inventory.insert(
            extension.clone(),
            json!({
                "count": entry.count,
                "directories": entry.directories.into_iter().collect::<Vec<_>>(),
                "lane_excluded": entry.lane_excluded_count > 0,
                "lane_excluded_count": entry.lane_excluded_count,
                "category": extension_category(&extension),
                "gold_grade": baseline_gold_tier(&extension),
                "runtime_support": runtime_support_for_extension(extension_for_support, &probes),
            }),
        );
    }

    let by_category = categories
        .into_iter()
        .map(|(category, values)| {
            (
                category,
                Value::Array(values.into_iter().map(Value::String).collect()),
            )
        })
        .collect::<serde_json::Map<String, Value>>();

    let details = probes
        .iter()
        .map(|(key, probe)| {
            (
                key.clone(),
                json!({
                    "display_name": probe.display_name,
                    "installed": probe.installed,
                    "runtime_version": probe.runtime_version,
                    "runtime_output": probe.runtime_output,
                    "manager": probe.manager,
                    "manager_installed": probe.manager_installed,
                    "manager_version": probe.manager_version,
                    "oxidized": probe.oxidized,
                }),
            )
        })
        .collect::<serde_json::Map<String, Value>>();

    let viable = viable_but_unrepresented_extensions(&tracked, &probes);

    Ok(json!({
        "timestamp": now_iso(),
        "codebase_extensions": {
            "total_unique": inventory.keys().filter(|value| value.as_str() != "[no_ext]").count(),
            "inventory": inventory,
            "by_category": by_category,
        },
        "system_toolchains": {
            "installed": installed_toolchains(&probes),
            "oxidized": oxidized_toolchains(&probes),
            "unoxidized_installed": unoxidized_installed_toolchains(&probes),
            "oxidized_available_not_installed": oxidized_available_not_installed(&probes),
            "no_oxidized_tooling_exists": no_oxidized_tooling_exists(&probes),
            "details": details,
        },
        "extension_gap": {
            "viable_but_unrepresented": viable.clone(),
            "dead_extensions": dead_extensions(&tracked, &probes),
            "alchemy_opportunities": alchemy_opportunities(&viable),
        },
        "eol_risk": eol,
        "summary": {
            "tracked_files": tracked.len(),
            "lane_excluded_files": tracked.iter().filter(|path| path_is_excluded(path)).count(),
            "non_excluded_files": tracked.iter().filter(|path| !path_is_excluded(path)).count(),
            "top_extensions": top_extensions(&top_counts, 10),
        }
    }))
}

pub fn census_command(root: &Path) -> Result<Value> {
    let repo_root = resolve_repo_root(root)?;
    let tracked = tracked_files(&repo_root)?;
    let mut by_extension: BTreeMap<String, BTreeMap<String, usize>> = BTreeMap::new();
    let mut anomalies: Vec<Value> = Vec::new();
    let mut excluded_paths = Vec::new();
    let mut by_gold_tier: BTreeMap<String, usize> = BTreeMap::new();

    for rel_path in &tracked {
        if path_is_excluded(rel_path) {
            excluded_paths.push(rel_path.display().to_string());
            continue;
        }

        let extension = extension_or_placeholder(compound_extension(rel_path));
        *by_gold_tier
            .entry(baseline_gold_tier(&extension).to_owned())
            .or_default() += 1;
        let bucket = by_extension.entry(extension.clone()).or_default();
        *bucket.entry(String::from("count")).or_default() += 1;

        if let Some(anomaly) = detect_census_anomaly(&repo_root, rel_path, &extension) {
            let anomaly_type = anomaly["type"].as_str().unwrap_or("unknown");
            *bucket.entry(anomaly_type.to_owned()).or_default() += 1;
            anomalies.push(anomaly);
        }
    }

    let by_extension_json = by_extension
        .into_iter()
        .map(|(extension, counts)| {
            let count = counts.get("count").copied().unwrap_or_default();
            let anomaly_counts = counts
                .into_iter()
                .filter(|(key, _)| key != "count")
                .map(|(key, value)| (key, json!(value)))
                .collect::<serde_json::Map<String, Value>>();
            (
                extension,
                json!({
                    "count": count,
                    "anomalies": anomaly_counts,
                }),
            )
        })
        .collect::<serde_json::Map<String, Value>>();

    Ok(json!({
        "timestamp": now_iso(),
        "total_tracked": tracked.len(),
        "excluded_lane_files": excluded_paths.len(),
        "audited_files": tracked.len().saturating_sub(excluded_paths.len()),
        "excluded_paths": excluded_paths,
        "by_extension": by_extension_json,
        "anomalies": anomalies,
        "by_gold_tier": by_gold_tier,
        "verdict": if anomalies.is_empty() { "PASS" } else { "FAIL" },
    }))
}

pub fn audit_command(root: &Path, path: &Path) -> Result<Value> {
    let repo_root = resolve_repo_root(root)?;
    let repo_path = absolute_path(&repo_root, path);
    let rel_path = relative_to_root(&repo_root, &repo_path)?;
    let extension = compound_extension(&rel_path);
    let extension_display = extension_or_placeholder(extension.clone());
    let probes = discover_toolchains()?;

    Ok(json!({
        "timestamp": now_iso(),
        "path": normalize_path(&rel_path),
        "extension": if extension.is_empty() { "[no_ext]" } else { extension.as_str() },
        "category": extension_category(&extension_display),
        "gold_grade": baseline_gold_tier(&extension_display),
        "lane_excluded": path_is_excluded(&rel_path),
        "runtime_support": runtime_support_for_extension(&extension, &probes),
        "pathway": pathway_for_extension(&extension_display),
    }))
}

pub fn pathway_command(extension: &str) -> Value {
    let normalized = normalize_extension_arg(extension);
    json!({
        "timestamp": now_iso(),
        "extension": normalized,
        "category": extension_category(&normalized),
        "gold_grade": baseline_gold_tier(&normalized),
        "pathway": pathway_for_extension(&normalized),
    })
}

pub fn validate_command(path: &Path) -> Value {
    match validate_file(path) {
        Ok(payload) => payload,
        Err(error) => json!({
            "timestamp": now_iso(),
            "path": normalize_path(path),
            "valid": false,
            "validator": "internal",
            "message": error.to_string(),
        }),
    }
}

pub fn landscape_command(root: &Path) -> Result<Value> {
    let repo_root = resolve_repo_root(root)?;
    let tracked = tracked_files(&repo_root)?;
    let probes = discover_toolchains()?;

    Ok(json!({
        "timestamp": now_iso(),
        "confirmed_installed": confirmed_installed_table(&probes),
        "known_oxidized_not_installed": oxidized_not_installed_table(&probes),
        "unoxidized_gap": unoxidized_gap_table(&probes),
        "viable_but_unrepresented": viable_but_unrepresented_extensions(&tracked, &probes),
        "dead_extensions": dead_extensions(&tracked, &probes),
        "eol_risk": build_eol_report(&probes, &fetch_eol_cycle_live),
        "recommendations": landscape_recommendations(&tracked, &probes),
    }))
}

pub fn eol_command() -> Result<Value> {
    let probes = discover_toolchains()?;
    Ok(json!({
        "timestamp": now_iso(),
        "runtimes": build_eol_report(&probes, &fetch_eol_cycle_live),
    }))
}

pub fn forensics_command(path: &Path) -> Result<Value> {
    let bytes = fs::read(path).with_context(|| format!("reading {}", path.display()))?;
    let (detected_type, extractable_intelligence) = if bytes.starts_with(MAGIC_PNG) {
        (
            "png",
            "Image provenance, dimensions, and generation chain audit.",
        )
    } else if bytes.starts_with(MAGIC_WOFF) {
        ("woff", "Glyph-map validation and source-SVG traceability.")
    } else if bytes.starts_with(MAGIC_SQLITE) {
        (
            "sqlite",
            "Schema extraction, table provenance, and state archaeology.",
        )
    } else if is_likely_text(&bytes) {
        (
            "text",
            "Text extraction, extension correction, and content classification.",
        )
    } else {
        (
            "unknown_binary",
            "Magic-byte catalogue expansion or manual inspection required.",
        )
    };

    Ok(json!({
        "timestamp": now_iso(),
        "path": normalize_path(path),
        "size_bytes": bytes.len(),
        "detected_type": detected_type,
        "extractable_intelligence": extractable_intelligence,
    }))
}

fn confirmed_installed_table(probes: &BTreeMap<String, ToolchainProbe>) -> Vec<Value> {
    let replacements: BTreeMap<&str, &str> = BTreeMap::from([
        (
            "python",
            "pip, pip-tools, virtualenv, pyenv, pipenv, poetry",
        ),
        ("ruby", "rbenv, rvm, chruby, ruby-install"),
        ("go", "manual Go SDK installs"),
        ("rust", "canonical Rust toolchain lane"),
        ("typescript", "npm, yarn, pnpm, nvm, node"),
    ]);

    probes
        .iter()
        .filter(|(_, probe)| probe.installed)
        .map(|(key, probe)| {
            json!({
                "language": probe.display_name,
                "tool": probe.manager.as_deref().unwrap_or(key),
                "replaces": replacements.get(key.as_str()).copied().unwrap_or("system runtime"),
                "status": probe.runtime_version.as_ref().map_or_else(
                    || String::from("installed"),
                    |version| format!("installed {version}"),
                ),
            })
        })
        .collect()
}

fn oxidized_not_installed_table(probes: &BTreeMap<String, ToolchainProbe>) -> Vec<Value> {
    let actions: BTreeMap<&str, &str> = BTreeMap::from([
        ("nodejs", "Could install for Node version management."),
        ("julia", "Could install for Julia version management."),
        ("zig", "Could install for native Zig bootstrapping."),
    ]);

    probes
        .iter()
        .filter(|(_, probe)| !probe.installed)
        .filter(|(_, probe)| {
            probe.manager_installed || matches!(probe.oxidized_kind.as_str(), "true" | "honorary")
        })
        .map(|(key, probe)| {
            json!({
                "language": probe.display_name,
                "tool": probe.manager.as_deref().unwrap_or(key),
                "status": if probe.manager_installed {
                    "manager_installed_runtime_absent"
                } else {
                    "known_not_installed"
                },
                "action": actions
                    .get(key.as_str())
                    .copied()
                    .unwrap_or("Review installation value against current repo needs."),
            })
        })
        .collect()
}

fn unoxidized_gap_table(probes: &BTreeMap<String, ToolchainProbe>) -> Vec<Value> {
    let best_tooling: BTreeMap<&str, &str> = BTreeMap::from([
        ("php", "phpbrew / phpenv"),
        ("elixir", "asdf"),
        ("lua", "luaver"),
        ("dotnet", "dotnet"),
        ("java", "sdkman / jabba"),
        ("haskell", "ghcup"),
        ("cobol", "GnuCOBOL"),
        ("perl", "system Perl"),
        ("c_cpp", "compiler toolchains"),
    ]);

    probes
        .iter()
        .filter(|(_, probe)| {
            !matches!(
                probe.oxidized_kind.as_str(),
                "true" | "self_oxidizing" | "honorary"
            )
        })
        .map(|(key, probe)| {
            json!({
                "language": probe.display_name,
                "current_best_tooling": best_tooling.get(key.as_str()).copied().unwrap_or("system tooling"),
                "why_not_oxidized": "No mature Rust-native manager confirmed in the current lane audit.",
                "installed": probe.installed,
            })
        })
        .collect()
}

fn landscape_recommendations(
    tracked: &[PathBuf],
    probes: &BTreeMap<String, ToolchainProbe>,
) -> Vec<String> {
    let viable = viable_but_unrepresented_extensions(tracked, probes);
    let mut recommendations = vec![
        String::from("Keep uv, rv, goup, rustup, and bun as the primary native toolchain lane."),
        String::from(
            "Use ankh-forge scan/census as the fast path before deeper Python archaeology.",
        ),
    ];
    if viable.iter().any(|extension| extension == ".go") {
        recommendations.push(String::from(
            "Promote the recovered Go CLI artifact into a maintained utility lane.",
        ));
    }
    if viable.iter().any(|extension| extension == ".cs") {
        recommendations.push(String::from(
            "Add a lightweight .NET contract lane if typed host tooling becomes a priority.",
        ));
    }
    if probes.get("nodejs").is_some_and(|probe| !probe.installed) {
        recommendations.push(String::from(
            "Consider fnm or Volta if Node-specific version pinning becomes necessary beyond bun.",
        ));
    }
    recommendations
}

fn validate_file(path: &Path) -> Result<Value> {
    let extension = compound_extension(path);
    let normalized_path = normalize_path(path);

    let payload = match extension.as_str() {
        ".json" | ".jsonl" => {
            let text =
                fs::read_to_string(path).with_context(|| format!("reading {}", path.display()))?;
            if extension == ".jsonl" {
                for (index, line) in text.lines().enumerate() {
                    if line.trim().is_empty() {
                        continue;
                    }
                    serde_json::from_str::<Value>(line)
                        .with_context(|| format!("invalid JSONL at line {}", index + 1))?;
                }
            } else {
                serde_json::from_str::<Value>(&text).with_context(|| "invalid JSON")?;
            }
            json!({
                "timestamp": now_iso(),
                "path": normalized_path,
                "valid": true,
                "validator": "serde_json",
                "message": "JSON parsed successfully.",
            })
        }
        ".py" => {
            let path_arg = path.display().to_string();
            let success = run_external(
                path.parent(),
                &["uv", "run", "python", "-m", "py_compile", path_arg.as_str()],
            )?;
            json!({
                "timestamp": now_iso(),
                "path": normalized_path,
                "valid": success,
                "validator": "uv py_compile",
                "message": if success {
                    "Python syntax validation passed."
                } else {
                    "Python syntax validation failed."
                },
            })
        }
        ".ps1" => {
            let script = format!(
                "$null = [System.Management.Automation.Language.Parser]::ParseFile('{}', [ref]$null, [ref]$errors); if ($errors.Count -eq 0) {{ exit 0 }} else {{ exit 1 }}",
                escape_ps_literal(&path.display().to_string())
            );
            let success = run_external(
                path.parent(),
                &["pwsh", "-NoProfile", "-Command", script.as_str()],
            )?;
            json!({
                "timestamp": now_iso(),
                "path": normalized_path,
                "valid": success,
                "validator": "powershell parser",
                "message": if success {
                    "PowerShell syntax validation passed."
                } else {
                    "PowerShell syntax validation failed."
                },
            })
        }
        ".ts" | ".tsx" | ".js" | ".cjs" | ".mjs" => {
            let path_arg = path.display().to_string();
            let success = run_external(
                path.parent(),
                &[
                    "bun",
                    "x",
                    "tsc",
                    "--noEmit",
                    "--pretty",
                    "false",
                    path_arg.as_str(),
                ],
            )?;
            json!({
                "timestamp": now_iso(),
                "path": normalized_path,
                "valid": success,
                "validator": "bun x tsc",
                "message": if success {
                    "TypeScript/JavaScript syntax validation passed."
                } else {
                    "TypeScript/JavaScript syntax validation failed."
                },
            })
        }
        _ => json!({
            "timestamp": now_iso(),
            "path": normalized_path,
            "valid": false,
            "validator": "unsupported",
            "message": format!("No validator configured for {extension}."),
        }),
    };

    Ok(payload)
}

fn run_external(cwd: Option<&Path>, argv: &[&str]) -> Result<bool> {
    let (program, arguments) = argv
        .split_first()
        .ok_or_else(|| anyhow!("external command requires a program"))?;
    let mut command = Command::new(program);
    command.args(arguments);
    if let Some(directory) = cwd {
        command.current_dir(directory);
    }
    let status = command
        .status()
        .with_context(|| format!("running external validator `{program}`"))?;
    Ok(status.success())
}

fn detect_census_anomaly(repo_root: &Path, rel_path: &Path, extension: &str) -> Option<Value> {
    let normalized = normalize_path(rel_path);
    let text = if matches!(
        extension,
        ".env" | ".md" | ".log" | ".bat" | ".off" | ".md\""
    ) {
        fs::read_to_string(repo_root.join(rel_path)).ok()
    } else {
        None
    };

    let anomaly = if Path::new(extension)
        .extension()
        .is_some_and(|ext| ext.eq_ignore_ascii_case("pyc"))
    {
        Some((
            "tracked_bytecode",
            "untrack_gitignore",
            "Generator script is the gold, not this compiled artifact.",
        ))
    } else if extension == ".off" {
        Some((
            "disabled_by_rename",
            "governed_toggle",
            "Disabled-by-rename hides workflow provenance behind filename mutation.",
        ))
    } else if extension == ".md\"" {
        Some((
            "filename_encoding_damage",
            "repair_filename",
            "The content survives, but the path encoding is damaged.",
        ))
    } else if extension == ".bat" {
        Some((
            "legacy_batch_in_pwsh_repo",
            "transliterate_to_pwsh",
            "A lone batch file in a PowerShell-first repo is drift, not a durable lane.",
        ))
    } else if extension == ".env"
        && !normalized.contains("example")
        && !normalized.contains("template")
        && text.as_deref().unwrap_or_default().contains('=')
    {
        Some((
            "tracked_env_surface",
            "extract_schema_only",
            "Tracked environment files should be schemas or templates, not live surfaces.",
        ))
    } else if extension == ".log" && normalized.starts_with("codex/mailbox/") {
        Some((
            "filetype_directory_mismatch",
            "triage_log_signal",
            "Mailbox logs belong to extracted signal, not as ambient tracked exhaust.",
        ))
    } else if extension == ".md" && normalized.starts_with("scripts/") {
        Some((
            "filetype_directory_mismatch",
            "relocate_documentation",
            "Documentation in scripts/ should be canonicalized into a docs/governance lane.",
        ))
    } else {
        None
    };

    anomaly.map(|(kind, recommendation, rationale)| {
        json!({
            "path": normalized,
            "type": kind,
            "gold_grade": baseline_gold_tier(extension),
            "recommendation": recommendation,
            "wptg_rationale": rationale,
        })
    })
}

fn alchemy_opportunities(extensions: &[String]) -> Vec<Value> {
    extensions
        .iter()
        .filter_map(|extension| {
            PATHWAY_OVERRIDES
                .iter()
                .find(|(candidate, _)| candidate == &extension.as_str())
                .map(|(_, rationale)| json!({ "target_ext": extension, "rationale": rationale }))
        })
        .collect()
}

fn dead_extensions(tracked: &[PathBuf], probes: &BTreeMap<String, ToolchainProbe>) -> Vec<String> {
    represented_extensions(tracked)
        .into_iter()
        .filter(|extension| !extension.is_empty())
        .filter(|extension| {
            let support = runtime_support_for_extension(extension, probes);
            let required = support["required_toolchains"]
                .as_array()
                .map_or(0, Vec::len);
            required > 0 && !support["supported"].as_bool().unwrap_or(false)
        })
        .collect()
}

fn viable_but_unrepresented_extensions(
    tracked: &[PathBuf],
    probes: &BTreeMap<String, ToolchainProbe>,
) -> Vec<String> {
    let present = represented_extensions(tracked);
    let primary_present = tracked
        .iter()
        .map(|path| primary_extension(path))
        .collect::<BTreeSet<_>>();

    toolchain_specs()
        .into_iter()
        .filter(|spec| probes.get(spec.key).is_some_and(|probe| probe.installed))
        .flat_map(|spec| spec.represented_extensions.iter().copied())
        .filter(|extension| !present.contains(*extension) && !primary_present.contains(*extension))
        .map(str::to_owned)
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect()
}

fn represented_extensions(tracked: &[PathBuf]) -> BTreeSet<String> {
    tracked
        .iter()
        .map(|path| compound_extension(path))
        .collect()
}

fn runtime_support_for_extension(
    extension: &str,
    probes: &BTreeMap<String, ToolchainProbe>,
) -> Value {
    let required = extension_toolchains(extension);
    let supported_by = required
        .iter()
        .filter(|toolchain| probes.get(**toolchain).is_some_and(|probe| probe.installed))
        .map(|value| (*value).to_owned())
        .collect::<Vec<_>>();
    json!({
        "supported": (!required.is_empty() && !supported_by.is_empty()) || required.is_empty(),
        "supported_by": supported_by,
        "required_toolchains": required,
    })
}

fn build_eol_report<F>(probes: &BTreeMap<String, ToolchainProbe>, fetcher: &F) -> Value
where
    F: Fn(&str, &str) -> Option<EolCycle>,
{
    let report = probes
        .iter()
        .filter(|(_, probe)| probe.installed)
        .filter_map(|(key, probe)| {
            let version = probe.runtime_version.clone()?;
            let slug = probe.eol_slug.clone()?;
            let value = if let Some(cycle) = fetcher(&slug, &version) {
                json!({
                    "version": version,
                    "cycle": cycle.cycle,
                    "eol": cycle.eol,
                    "latest": cycle.latest,
                    "latest_release_date": cycle.latest_release_date,
                    "support": cycle.support,
                    "extended_support": cycle.extended_support,
                    "link": cycle.link,
                    "source": "https://endoflife.date",
                })
            } else {
                json!({
                    "version": version,
                    "status": "unknown",
                    "source": "https://endoflife.date",
                })
            };
            Some((key.clone(), value))
        })
        .collect::<serde_json::Map<String, Value>>();
    Value::Object(report)
}

fn fetch_eol_cycle_live(slug: &str, version: &str) -> Option<EolCycle> {
    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(10))
        .build()
        .ok()?;
    let response = client
        .get(format!("https://endoflife.date/api/{slug}.json"))
        .send()
        .ok()?;
    let cycles = response.json::<Vec<EolCycle>>().ok()?;
    select_eol_cycle(&cycles, version)
}

fn select_eol_cycle(cycles: &[EolCycle], version: &str) -> Option<EolCycle> {
    let mut candidates = Vec::new();
    let mut parts = version.split('.');
    let major = parts.next()?;
    let minor = parts.next();
    if let Some(minor_value) = minor {
        candidates.push(format!("{major}.{minor_value}"));
    }
    candidates.push(major.to_owned());

    candidates.into_iter().find_map(|candidate| {
        cycles
            .iter()
            .find(|cycle| cycle.cycle == candidate)
            .cloned()
    })
}

fn installed_toolchains(probes: &BTreeMap<String, ToolchainProbe>) -> Vec<String> {
    probes
        .iter()
        .filter(|(_, probe)| probe.installed)
        .map(|(key, _)| key.clone())
        .collect()
}

fn oxidized_toolchains(probes: &BTreeMap<String, ToolchainProbe>) -> Vec<String> {
    probes
        .iter()
        .filter(|(_, probe)| probe.installed)
        .filter(|(_, probe)| {
            matches!(
                probe.oxidized_kind.as_str(),
                "true" | "self_oxidizing" | "honorary"
            )
        })
        .map(|(key, _)| key.clone())
        .collect()
}

fn unoxidized_installed_toolchains(probes: &BTreeMap<String, ToolchainProbe>) -> Vec<String> {
    probes
        .iter()
        .filter(|(_, probe)| probe.installed && probe.oxidized_kind == "false")
        .map(|(key, _)| key.clone())
        .collect()
}

fn oxidized_available_not_installed(probes: &BTreeMap<String, ToolchainProbe>) -> Vec<String> {
    probes
        .iter()
        .filter(|(_, probe)| !probe.installed)
        .filter(|(_, probe)| {
            probe.manager_installed || matches!(probe.oxidized_kind.as_str(), "true" | "honorary")
        })
        .map(|(key, probe)| {
            probe
                .manager
                .as_ref()
                .map_or_else(|| key.clone(), |manager| format!("{key} ({manager})"))
        })
        .collect()
}

fn no_oxidized_tooling_exists(probes: &BTreeMap<String, ToolchainProbe>) -> Vec<String> {
    probes
        .iter()
        .filter(|(_, probe)| !probe.installed && probe.oxidized_kind == "false")
        .map(|(key, _)| key.clone())
        .collect()
}

fn discover_toolchains() -> Result<BTreeMap<String, ToolchainProbe>> {
    let mut probes = BTreeMap::new();

    for spec in toolchain_specs() {
        let (installed, runtime_output) = run_command(spec.runtime_cmd, None)?;
        let runtime_version = runtime_output.as_deref().and_then(extract_version);

        let mut manager_installed = false;
        let mut manager_version = None;
        if let Some(manager_cmd) = spec.manager_cmd {
            let (ok, output) = run_command(manager_cmd, None)?;
            manager_installed = ok;
            manager_version = output
                .as_deref()
                .and_then(extract_version)
                .map(str::to_owned);
            if !manager_installed {
                for alternate in spec.alternate_manager_cmds {
                    let (alt_ok, alt_output) = run_command(alternate, None)?;
                    if alt_ok {
                        manager_installed = true;
                        manager_version = alt_output
                            .as_deref()
                            .and_then(extract_version)
                            .map(str::to_owned);
                        break;
                    }
                }
            }
        }

        let oxidized_kind = match spec.oxidized {
            OxidizedKind::Yes => "true",
            OxidizedKind::No => "false",
            OxidizedKind::SelfOxidizing => "self_oxidizing",
            OxidizedKind::Honorary => "honorary",
        };

        probes.insert(
            spec.key.to_owned(),
            ToolchainProbe {
                display_name: spec.display_name.to_owned(),
                installed,
                runtime_version: runtime_version.map(str::to_owned),
                runtime_output,
                manager: spec.manager.map(str::to_owned),
                manager_installed,
                manager_version,
                oxidized_kind: oxidized_kind.to_owned(),
                oxidized: spec.oxidized.as_json(),
                eol_slug: spec.eol_slug.map(str::to_owned),
            },
        );
    }

    Ok(probes)
}

#[allow(clippy::too_many_lines)]
fn toolchain_specs() -> Vec<ToolchainSpec> {
    vec![
        ToolchainSpec {
            key: "rust",
            display_name: "Rust",
            runtime_cmd: &["rustc", "--version"],
            manager_cmd: Some(&["rustup", "--version"]),
            alternate_manager_cmds: &[],
            manager: Some("rustup"),
            oxidized: OxidizedKind::SelfOxidizing,
            eol_slug: Some("rust"),
            represented_extensions: &[".rs"],
        },
        ToolchainSpec {
            key: "python",
            display_name: "Python",
            runtime_cmd: &["uv", "run", "python", "--version"],
            manager_cmd: Some(&["uv", "--version"]),
            alternate_manager_cmds: &[],
            manager: Some("uv"),
            oxidized: OxidizedKind::Yes,
            eol_slug: Some("python"),
            represented_extensions: &[".py", ".pyc", ".python-version"],
        },
        ToolchainSpec {
            key: "ruby",
            display_name: "Ruby",
            runtime_cmd: &["ruby", "--version"],
            manager_cmd: Some(&["rv", "--version"]),
            alternate_manager_cmds: &[],
            manager: Some("rv"),
            oxidized: OxidizedKind::Yes,
            eol_slug: Some("ruby"),
            represented_extensions: &[".rb"],
        },
        ToolchainSpec {
            key: "go",
            display_name: "Go",
            runtime_cmd: &["go", "version"],
            manager_cmd: Some(&["goup", "--version"]),
            alternate_manager_cmds: &[],
            manager: Some("goup"),
            oxidized: OxidizedKind::Yes,
            eol_slug: Some("go"),
            represented_extensions: &[".go"],
        },
        ToolchainSpec {
            key: "typescript",
            display_name: "TypeScript/JS",
            runtime_cmd: &["bun", "--version"],
            manager_cmd: Some(&["bun", "--version"]),
            alternate_manager_cmds: &[],
            manager: Some("bun"),
            oxidized: OxidizedKind::Honorary,
            eol_slug: Some("bun"),
            represented_extensions: &[
                ".cjs",
                ".js",
                ".mjs",
                ".ts",
                ".tsx",
                ".tsbuildinfo",
                ".d.ts",
                ".test.ts",
            ],
        },
        ToolchainSpec {
            key: "dotnet",
            display_name: ".NET / C# / F#",
            runtime_cmd: &["dotnet", "--version"],
            manager_cmd: None,
            alternate_manager_cmds: &[],
            manager: None,
            oxidized: OxidizedKind::No,
            eol_slug: Some("dotnet"),
            represented_extensions: &[".cs", ".fsx"],
        },
        ToolchainSpec {
            key: "c_cpp",
            display_name: "C/C++",
            runtime_cmd: &["gcc", "--version"],
            manager_cmd: None,
            alternate_manager_cmds: &[],
            manager: None,
            oxidized: OxidizedKind::No,
            eol_slug: None,
            represented_extensions: &[".c", ".cpp", ".h"],
        },
        ToolchainSpec {
            key: "perl",
            display_name: "Perl",
            runtime_cmd: &["perl", "-v"],
            manager_cmd: None,
            alternate_manager_cmds: &[],
            manager: None,
            oxidized: OxidizedKind::No,
            eol_slug: Some("perl"),
            represented_extensions: &[".pl"],
        },
        ToolchainSpec {
            key: "php",
            display_name: "PHP",
            runtime_cmd: &["php", "--version"],
            manager_cmd: None,
            alternate_manager_cmds: &[],
            manager: None,
            oxidized: OxidizedKind::No,
            eol_slug: Some("php"),
            represented_extensions: &[".php"],
        },
        ToolchainSpec {
            key: "julia",
            display_name: "Julia",
            runtime_cmd: &["julia", "--version"],
            manager_cmd: Some(&["juliaup", "--version"]),
            alternate_manager_cmds: &[],
            manager: Some("juliaup"),
            oxidized: OxidizedKind::Yes,
            eol_slug: Some("julia"),
            represented_extensions: &[".jl"],
        },
        ToolchainSpec {
            key: "elixir",
            display_name: "Elixir",
            runtime_cmd: &["elixir", "--version"],
            manager_cmd: None,
            alternate_manager_cmds: &[],
            manager: None,
            oxidized: OxidizedKind::No,
            eol_slug: Some("elixir"),
            represented_extensions: &[".ex", ".exs"],
        },
        ToolchainSpec {
            key: "lua",
            display_name: "Lua",
            runtime_cmd: &["lua", "-v"],
            manager_cmd: None,
            alternate_manager_cmds: &[],
            manager: None,
            oxidized: OxidizedKind::No,
            eol_slug: Some("lua"),
            represented_extensions: &[".lua"],
        },
        ToolchainSpec {
            key: "java",
            display_name: "Java",
            runtime_cmd: &["java", "--version"],
            manager_cmd: None,
            alternate_manager_cmds: &[],
            manager: None,
            oxidized: OxidizedKind::No,
            eol_slug: Some("java"),
            represented_extensions: &[".java"],
        },
        ToolchainSpec {
            key: "haskell",
            display_name: "Haskell",
            runtime_cmd: &["ghc", "--version"],
            manager_cmd: Some(&["ghcup", "--version"]),
            alternate_manager_cmds: &[],
            manager: Some("ghcup"),
            oxidized: OxidizedKind::No,
            eol_slug: None,
            represented_extensions: &[".hs"],
        },
        ToolchainSpec {
            key: "cobol",
            display_name: "COBOL",
            runtime_cmd: &["cobc", "--version"],
            manager_cmd: None,
            alternate_manager_cmds: &[],
            manager: None,
            oxidized: OxidizedKind::No,
            eol_slug: None,
            represented_extensions: &[".cob", ".cbl"],
        },
        ToolchainSpec {
            key: "zig",
            display_name: "Zig",
            runtime_cmd: &["zig", "version"],
            manager_cmd: Some(&["zigup", "--version"]),
            alternate_manager_cmds: &[],
            manager: Some("zigup"),
            oxidized: OxidizedKind::Honorary,
            eol_slug: Some("zig"),
            represented_extensions: &[".zig"],
        },
        ToolchainSpec {
            key: "nodejs",
            display_name: "Node.js",
            runtime_cmd: &["node", "--version"],
            manager_cmd: Some(&["fnm", "--version"]),
            alternate_manager_cmds: &[&["volta", "--version"]],
            manager: Some("fnm/volta"),
            oxidized: OxidizedKind::Yes,
            eol_slug: Some("nodejs"),
            represented_extensions: &[".node"],
        },
        ToolchainSpec {
            key: "powershell",
            display_name: "PowerShell",
            runtime_cmd: &["pwsh", "--version"],
            manager_cmd: None,
            alternate_manager_cmds: &[],
            manager: None,
            oxidized: OxidizedKind::No,
            eol_slug: None,
            represented_extensions: &[".ps1"],
        },
        ToolchainSpec {
            key: "shell",
            display_name: "POSIX Shell",
            runtime_cmd: &["bash", "--version"],
            manager_cmd: None,
            alternate_manager_cmds: &[],
            manager: None,
            oxidized: OxidizedKind::No,
            eol_slug: None,
            represented_extensions: &[".sh"],
        },
        ToolchainSpec {
            key: "batch",
            display_name: "Windows Batch",
            runtime_cmd: &["where", "cmd"],
            manager_cmd: None,
            alternate_manager_cmds: &[],
            manager: None,
            oxidized: OxidizedKind::No,
            eol_slug: None,
            represented_extensions: &[".bat"],
        },
        ToolchainSpec {
            key: "glsl",
            display_name: "GLSL / Shader Tooling",
            runtime_cmd: &["glslangValidator", "--version"],
            manager_cmd: None,
            alternate_manager_cmds: &[],
            manager: None,
            oxidized: OxidizedKind::No,
            eol_slug: None,
            represented_extensions: &[".comp", ".frag", ".vert"],
        },
    ]
}

fn extension_toolchains(extension: &str) -> Vec<&'static str> {
    match extension {
        ".bat" => vec!["batch"],
        ".cjs" | ".js" | ".mjs" | ".ts" | ".tsx" | ".tsbuildinfo" | ".d.ts" | ".test.ts" => {
            vec!["typescript"]
        }
        ".comp" | ".frag" | ".vert" => vec!["glsl"],
        ".env" | ".json" | ".jsonl" | ".yaml" | ".yml" | ".log" => {
            vec!["python", "typescript"]
        }
        ".ps1" => vec!["powershell"],
        ".py" | ".pyc" | ".python-version" => vec!["python"],
        ".rb" => vec!["ruby"],
        ".rs" => vec!["rust"],
        ".sh" => vec!["shell"],
        ".toml" => vec!["python", "rust"],
        ".vsconfig" => vec!["dotnet"],
        _ => Vec::new(),
    }
}

fn path_is_excluded(path: &Path) -> bool {
    let normalized = normalize_path(path);
    if EXACT_EXCLUSIONS.contains(&normalized.as_str()) {
        return true;
    }
    if normalized.starts_with("scripts/theme_") && path_has_extension(path, "py") {
        return true;
    }
    if normalized.starts_with("scripts/icon_") && path_has_extension(path, "py") {
        return true;
    }
    if normalized.starts_with("extensions/chthonic-archive/themes/icons/product/")
        && path_has_extension(path, "svg")
    {
        return true;
    }
    if normalized.starts_with("extensions/chthonic-archive/themes/")
        && path_has_extension(path, "json")
    {
        let trimmed = normalized.trim_start_matches("extensions/chthonic-archive/themes/");
        if !trimmed.contains('/') {
            return true;
        }
    }
    LANE_EXCLUSION_PREFIXES
        .iter()
        .any(|prefix| normalized.starts_with(prefix))
}

fn baseline_gold_tier(extension: &str) -> &'static str {
    match extension_category(extension) {
        "source_code" => "tier_1_direct",
        "data_config" | "vcs_meta" | "domain_specific" => "tier_2_structural",
        "documentation" => "tier_3_conceptual",
        _ => "raw_unrefined",
    }
}

fn extension_category(extension: &str) -> &'static str {
    if SOURCE_CODE_EXTENSIONS.contains(&extension) {
        "source_code"
    } else if DATA_CONFIG_EXTENSIONS.contains(&extension) {
        "data_config"
    } else if BUILD_OUTPUT_EXTENSIONS.contains(&extension) {
        "build_output"
    } else if DOCUMENTATION_EXTENSIONS.contains(&extension) {
        "documentation"
    } else if VCS_META_EXTENSIONS.contains(&extension) {
        "vcs_meta"
    } else if GRAPHICS_GPU_EXTENSIONS.contains(&extension) {
        "graphics_gpu"
    } else if GOVERNANCE_EXTENSIONS.contains(&extension) {
        "governance"
    } else if DOMAIN_SPECIFIC_EXTENSIONS.contains(&extension) {
        "domain_specific"
    } else if DAMAGED_EXTENSIONS.contains(&extension) {
        "damaged"
    } else {
        "unclassified"
    }
}

fn pathway_for_extension(extension: &str) -> String {
    if let Some((_, pathway)) = PATHWAY_OVERRIDES
        .iter()
        .find(|(candidate, _)| *candidate == extension)
    {
        return (*pathway).to_owned();
    }

    match extension_category(extension) {
        "source_code" => String::from(
            "Refine into a maintained module with tests and a documented runtime contract.",
        ),
        "data_config" => {
            String::from("Lift into a schema, provenance map, or typed configuration contract.")
        }
        "documentation" => {
            String::from("Canonicalize into governance or operational reference material.")
        }
        "graphics_gpu" => {
            String::from("Preserve as render-source truth and add validation/forensics metadata.")
        }
        "vcs_meta" => String::from(
            "Keep as repository governance and normalize lineage around the controlling process.",
        ),
        "governance" => String::from(
            "Extract intent into a governed record, then replace filename mutation with explicit state.",
        ),
        "domain_specific" => {
            String::from("Preserve domain canon and wire it into the owning toolchain lane.")
        }
        _ => String::from(
            "Run forensics first, then derive a stable target format from the file's signal.",
        ),
    }
}

fn normalize_extension_arg(extension: &str) -> String {
    if extension.starts_with('.') {
        extension.to_owned()
    } else {
        format!(".{extension}")
    }
}

fn extension_or_placeholder(extension: String) -> String {
    if extension.is_empty() {
        String::from("[no_ext]")
    } else {
        extension
    }
}

fn primary_extension(path: &Path) -> String {
    path.extension()
        .and_then(|value| value.to_str())
        .map_or_else(String::new, |value| format!(".{value}"))
}

fn compound_extension(path: &Path) -> String {
    let Some(name) = path.file_name().and_then(|value| value.to_str()) else {
        return String::new();
    };

    if name.starts_with('.') && name.matches('.').count() == 1 {
        return name.to_owned();
    }

    let parts = name.split('.').collect::<Vec<_>>();
    if parts.len() <= 1 {
        return String::new();
    }

    let suffixes = parts
        .iter()
        .skip(1)
        .map(|part| format!(".{part}"))
        .collect::<Vec<_>>();

    if suffixes.len() >= 2 {
        let candidate = format!(
            "{}{}",
            suffixes[suffixes.len() - 2],
            suffixes[suffixes.len() - 1]
        );
        if KNOWN_COMPOUND_EXTENSIONS.contains(&candidate.as_str()) {
            return candidate;
        }
        if suffixes[suffixes.len() - 1] == ".pyc"
            && suffixes[suffixes.len() - 2].starts_with(".cpython-")
        {
            return format!(
                "{}{}",
                suffixes[suffixes.len() - 2],
                suffixes[suffixes.len() - 1]
            );
        }
    }

    suffixes.last().cloned().unwrap_or_default()
}

fn normalize_path(path: &Path) -> String {
    path.to_string_lossy().replace('\\', "/")
}

fn path_has_extension(path: &Path, expected: &str) -> bool {
    path.extension()
        .and_then(|value| value.to_str())
        .is_some_and(|value| value.eq_ignore_ascii_case(expected))
}

fn absolute_path(root: &Path, path: &Path) -> PathBuf {
    if path.is_absolute() {
        path.to_path_buf()
    } else {
        root.join(path)
    }
}

fn relative_to_root(root: &Path, path: &Path) -> Result<PathBuf> {
    path.strip_prefix(root)
        .map(Path::to_path_buf)
        .with_context(|| format!("{} is outside {}", path.display(), root.display()))
}

fn resolve_repo_root(root: &Path) -> Result<PathBuf> {
    let absolute = if root.is_absolute() {
        root.to_path_buf()
    } else {
        std::env::current_dir()?.join(root)
    };
    let mut command = Command::new("git");
    command
        .arg("rev-parse")
        .arg("--show-toplevel")
        .current_dir(&absolute);
    let output = command
        .output()
        .context("running git rev-parse --show-toplevel")?;
    if !output.status.success() {
        bail!("failed to resolve repo root from {}", absolute.display());
    }
    let root_path = String::from_utf8_lossy(&output.stdout).trim().to_owned();
    Ok(PathBuf::from(root_path))
}

fn tracked_files(root: &Path) -> Result<Vec<PathBuf>> {
    let (ok, output) = run_command(&["git", "ls-files"], Some(root))?;
    if !ok {
        bail!("git ls-files failed under {}", root.display());
    }
    Ok(output
        .unwrap_or_default()
        .lines()
        .filter(|line| !line.trim().is_empty())
        .map(PathBuf::from)
        .collect())
}

fn run_command(command: &[&str], cwd: Option<&Path>) -> Result<(bool, Option<String>)> {
    let (program, args) = command
        .split_first()
        .ok_or_else(|| anyhow!("command slice cannot be empty"))?;
    let mut process = Command::new(program);
    process.args(args);
    if let Some(directory) = cwd {
        process.current_dir(directory);
    }
    let output = match process.output() {
        Ok(output) => output,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok((false, None)),
        Err(error) => return Err(error).with_context(|| format!("running `{program}`")),
    };
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    let text = if stdout.trim().is_empty() {
        stderr.trim()
    } else {
        stdout.trim()
    };
    Ok((
        output.status.success(),
        (!text.is_empty()).then(|| text.to_owned()),
    ))
}

fn extract_version(output: &str) -> Option<&str> {
    let mut candidates: Vec<&str> = Vec::new();
    let mut start: Option<usize> = None;

    for (index, ch) in output.char_indices() {
        if ch.is_ascii_digit() || ch == '.' {
            if start.is_none() {
                start = Some(index);
            }
        } else if let Some(candidate_start) = start.take() {
            let candidate = &output[candidate_start..index];
            if candidate.contains('.') && candidate.chars().any(|value| value.is_ascii_digit()) {
                candidates.push(candidate.trim_matches('.'));
            }
        }
    }

    if let Some(candidate_start) = start {
        let candidate = &output[candidate_start..];
        if candidate.contains('.') && candidate.chars().any(|value| value.is_ascii_digit()) {
            candidates.push(candidate.trim_matches('.'));
        }
    }

    let mut best: Option<&str> = None;
    let mut best_dots = 0usize;
    for candidate in candidates {
        let dots = candidate.matches('.').count();
        if best.is_none() || dots > best_dots {
            best = Some(candidate);
            best_dots = dots;
        }
    }

    best
}

fn top_extensions(counts: &BTreeMap<String, usize>, limit: usize) -> Vec<Value> {
    let mut pairs = counts
        .iter()
        .map(|(key, value)| (key.clone(), *value))
        .collect::<Vec<_>>();
    pairs.sort_by(|left, right| right.1.cmp(&left.1).then_with(|| left.0.cmp(&right.0)));
    pairs
        .into_iter()
        .take(limit)
        .map(|(extension, count)| json!([extension, count]))
        .collect()
}

fn now_iso() -> String {
    Command::new("pwsh")
        .args(["-NoProfile", "-Command", "(Get-Date).ToUniversalTime().ToString('o')"])
        .output()
        .ok()
        .and_then(|value| {
            if value.status.success() {
                Some(String::from_utf8_lossy(&value.stdout).trim().to_owned())
            } else {
                None
            }
        })
        .unwrap_or_else(|| String::from("1970-01-01T00:00:00.0000000+00:00"))
}

fn escape_ps_literal(value: &str) -> String {
    value.replace('\'', "''")
}

fn is_likely_text(bytes: &[u8]) -> bool {
    bytes
        .iter()
        .take(256)
        .all(|byte| byte.is_ascii_graphic() || byte.is_ascii_whitespace())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn scan_subcommand_reports_compound_extensions() {
        let repo = temp_repo(&[
            ("src/lib.rs", "pub fn hello() {}\n"),
            ("types/example.d.ts", "export interface Example {}\n"),
            ("tests/sample.test.ts", "export const sample = 1;\n"),
            (
                "extensions/chthonic-archive/themes/chthonic-file-icon-theme.json",
                "{}\n",
            ),
        ]);

        let payload = scan_command(repo.path()).expect("scan should succeed");
        assert_eq!(
            payload["codebase_extensions"]["inventory"][".d.ts"]["count"],
            json!(1)
        );
        assert_eq!(
            payload["codebase_extensions"]["inventory"][".test.ts"]["count"],
            json!(1)
        );
        assert_eq!(
            payload["codebase_extensions"]["inventory"][".json"]["lane_excluded"],
            json!(true)
        );
    }

    #[test]
    fn census_subcommand_detects_anomalies() {
        let repo = temp_repo(&[
            ("codex/mailbox/example.log", "build failed\n"),
            ("scripts/notes.md", "# notes\n"),
            (".env", "SECRET=value\n"),
        ]);

        let payload = census_command(repo.path()).expect("census should succeed");
        assert_eq!(payload["verdict"], json!("FAIL"));
        assert!(
            payload["anomalies"]
                .as_array()
                .expect("anomalies array")
                .iter()
                .any(|entry| entry["type"] == json!("tracked_env_surface"))
        );
    }

    #[test]
    fn audit_subcommand_classifies_one_file() {
        let repo = temp_repo(&[("dumpster-dive/input.log", "warning: drift\n")]);
        let payload = audit_command(repo.path(), Path::new("dumpster-dive/input.log"))
            .expect("audit should succeed");
        assert_eq!(payload["extension"], json!(".log"));
        assert_eq!(payload["category"], json!("unclassified"));
    }

    #[test]
    fn pathway_subcommand_knows_env_pathway() {
        let payload = pathway_command(".env");
        let pathway = payload["pathway"].as_str().expect("pathway string");
        assert!(pathway.contains("Environment schema"));
    }

    #[test]
    fn validate_subcommand_rejects_bad_json() {
        let temp = TempDir::new().expect("tempdir");
        let path = temp.path().join("broken.json");
        fs::write(&path, "{oops").expect("write broken json");
        let payload = validate_command(&path);
        assert_eq!(payload["valid"], json!(false));
    }

    #[test]
    fn landscape_subcommand_reports_recommendations() {
        let repo = temp_repo(&[("scripts/example.py", "print('hi')\n")]);
        let payload = landscape_command(repo.path()).expect("landscape should succeed");
        assert!(payload["recommendations"].as_array().is_some());
    }

    #[test]
    fn eol_subcommand_produces_runtime_object() {
        let payload = eol_command().expect("eol should succeed");
        assert!(payload["runtimes"].is_object());
    }

    #[test]
    fn forensics_subcommand_detects_png_magic() {
        let temp = TempDir::new().expect("tempdir");
        let path = temp.path().join("sample.png");
        fs::write(&path, MAGIC_PNG).expect("write png");
        let payload = forensics_command(&path).expect("forensics should succeed");
        assert_eq!(payload["detected_type"], json!("png"));
    }

    #[test]
    fn forensics_subcommand_detects_woff_magic() {
        let temp = TempDir::new().expect("tempdir");
        let path = temp.path().join("sample.woff");
        fs::write(&path, MAGIC_WOFF).expect("write woff");
        let payload = forensics_command(&path).expect("forensics should succeed");
        assert_eq!(payload["detected_type"], json!("woff"));
    }

    #[test]
    fn forensics_subcommand_detects_sqlite_magic() {
        let temp = TempDir::new().expect("tempdir");
        let path = temp.path().join("sample.db");
        fs::write(&path, MAGIC_SQLITE).expect("write sqlite");
        let payload = forensics_command(&path).expect("forensics should succeed");
        assert_eq!(payload["detected_type"], json!("sqlite"));
    }

    #[test]
    fn select_eol_cycle_prefers_major_minor_then_major() {
        let cycles = vec![
            EolCycle {
                cycle: String::from("3.13"),
                eol: None,
                latest: None,
                latest_release_date: None,
                support: None,
                extended_support: None,
                link: None,
            },
            EolCycle {
                cycle: String::from("3"),
                eol: None,
                latest: None,
                latest_release_date: None,
                support: None,
                extended_support: None,
                link: None,
            },
        ];

        let cycle = select_eol_cycle(&cycles, "3.13.2").expect("cycle should match");
        assert_eq!(cycle.cycle, "3.13");
    }

    fn temp_repo(files: &[(&str, &str)]) -> TempDir {
        let temp = TempDir::new().expect("tempdir");
        for (path, content) in files {
            let file_path = temp.path().join(path);
            if let Some(parent) = file_path.parent() {
                fs::create_dir_all(parent).expect("create parent");
            }
            fs::write(file_path, content).expect("write fixture");
        }

        let init = Command::new("git")
            .args(["init", "-q"])
            .current_dir(temp.path())
            .status()
            .expect("git init");
        assert!(init.success());

        let add = Command::new("git")
            .args(["add", "."])
            .current_dir(temp.path())
            .status()
            .expect("git add");
        assert!(add.success());

        temp
    }
}
