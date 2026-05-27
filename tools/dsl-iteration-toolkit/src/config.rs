// Config — dsl-iter.toml per-project configuration.
// Each DSL project sets paths + slice definitions; the toolkit uses these
// to drive smoke + coverage + catalog + ledger operations.

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    /// Path to the pest grammar file (relative to project root).
    pub grammar_path: PathBuf,
    /// Path to the corpus file (the document being parsed).
    pub corpus_path: PathBuf,
    /// Path to the pattern catalog (patterns.json).
    pub catalog_path: PathBuf,
    /// Directory for manifest output (ledger, coverage reports, etc.).
    pub manifest_dir: PathBuf,
    /// Project name (used in ledger tool field, etc.)
    pub project_name: String,
    /// Optional slice definitions for spot-check smoke.
    #[serde(default)]
    pub slices: Vec<Slice>,
    /// Optional surfaces to scan for coverage (default: paren).
    #[serde(default = "default_surfaces")]
    pub coverage_surfaces: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Slice {
    pub label: String,
    pub line_start: usize,
    pub line_end: usize,
}

fn default_surfaces() -> Vec<String> {
    vec!["paren".into()]
}

impl Config {
    pub fn load(path: impl AsRef<Path>) -> Result<Self> {
        let path = path.as_ref();
        let content = fs::read_to_string(path)
            .with_context(|| format!("read config at {}", path.display()))?;
        let cfg: Config = toml::from_str(&content)
            .with_context(|| format!("parse config at {}", path.display()))?;
        Ok(cfg)
    }

    pub fn save(&self, path: impl AsRef<Path>) -> Result<()> {
        let s = toml::to_string_pretty(self)?;
        fs::write(path, s)?;
        Ok(())
    }

    /// Default config for a new project at the given root.
    pub fn template(project_name: &str) -> Self {
        Self {
            grammar_path: PathBuf::from("grammar.pest"),
            corpus_path: PathBuf::from("corpus.md"),
            catalog_path: PathBuf::from("patterns.json"),
            manifest_dir: PathBuf::from("manifest"),
            project_name: project_name.into(),
            slices: vec![],
            coverage_surfaces: default_surfaces(),
        }
    }
}
