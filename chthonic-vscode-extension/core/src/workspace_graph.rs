use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::UNIX_EPOCH;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct FileEntry {
    pub uri: String,
    pub relative_path: String,
    pub language_id: String,
    pub last_modified: u128,
    pub size: u64,
    #[serde(default)]
    pub dependencies: Vec<String>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct WorkspaceGraph {
    pub files: HashMap<String, FileEntry>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct WorkspaceChange {
    pub uri: String,
    #[serde(rename = "type")]
    pub change_type: FileChangeType,
    #[serde(default)]
    pub relative_path: Option<String>,
    #[serde(default)]
    pub language_id: Option<String>,
}

#[derive(Debug, Clone, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub enum FileChangeType {
    Created,
    Changed,
    Deleted,
}

impl WorkspaceGraph {
    pub fn load_from_disk(path: &Path) -> Result<Self> {
        if !path.exists() {
            return Ok(Self::default());
        }

        let content = fs::read_to_string(path)
            .with_context(|| format!("failed to read workspace graph: {}", path.display()))?;
        serde_json::from_str(&content)
            .with_context(|| format!("failed to parse workspace graph: {}", path.display()))
    }

    pub fn save_to_disk(&self, path: &Path) -> Result<()> {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).with_context(|| {
                format!(
                    "failed to create workspace graph directory: {}",
                    parent.display()
                )
            })?;
        }

        let content =
            serde_json::to_string_pretty(self).context("failed to serialize workspace graph")?;
        fs::write(path, content)
            .with_context(|| format!("failed to write workspace graph: {}", path.display()))
    }

    pub fn ingest_full_file_list(&mut self, files: Vec<FileEntry>) {
        self.files = files
            .into_iter()
            .map(|entry| (entry.uri.clone(), entry))
            .collect();
    }

    pub fn apply_change(&mut self, change: WorkspaceChange) -> Result<()> {
        if change.change_type == FileChangeType::Deleted {
            self.files.remove(&change.uri);
            return Ok(());
        }

        let path = uri_to_path(&change.uri)?;
        let entry =
            file_entry_from_path(change.uri, path, change.relative_path, change.language_id)?;
        self.files.insert(entry.uri.clone(), entry);
        Ok(())
    }

    pub fn len(&self) -> usize {
        self.files.len()
    }
}

pub fn file_entry_from_path(
    uri: String,
    path: PathBuf,
    relative_path: Option<String>,
    language_id: Option<String>,
) -> Result<FileEntry> {
    let metadata =
        fs::metadata(&path).with_context(|| format!("failed to stat file: {}", path.display()))?;
    let last_modified = metadata
        .modified()
        .ok()
        .and_then(|time| time.duration_since(UNIX_EPOCH).ok())
        .map(|duration| duration.as_millis())
        .unwrap_or_default();

    Ok(FileEntry {
        uri,
        relative_path: relative_path.unwrap_or_else(|| path.display().to_string()),
        language_id: language_id.unwrap_or_else(|| infer_language_id(&path)),
        last_modified,
        size: metadata.len(),
        dependencies: Vec::new(),
    })
}

pub fn uri_to_path(uri: &str) -> Result<PathBuf> {
    let path = uri
        .strip_prefix("file:///")
        .with_context(|| format!("only file:/// URIs are supported: {uri}"))?;
    Ok(PathBuf::from(path.replace('/', "\\")))
}

fn infer_language_id(path: &Path) -> String {
    match path.extension().and_then(|extension| extension.to_str()) {
        Some("js") => "javascript",
        Some("jsx") => "javascriptreact",
        Some("ts") => "typescript",
        Some("tsx") => "typescriptreact",
        Some("rs") => "rust",
        Some("py") => "python",
        Some("json") => "json",
        Some("md") => "markdown",
        Some("ps1") => "powershell",
        Some("toml") => "toml",
        Some("yaml") | Some("yml") => "yaml",
        _ => "",
    }
    .to_owned()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn graph_roundtrip_preserves_file_entries() {
        let path = std::env::temp_dir().join(format!(
            "chthonic-test-workspace-graph-{}.json",
            crate::session::now_ms()
        ));
        let mut graph = WorkspaceGraph::default();
        graph.ingest_full_file_list(vec![FileEntry {
            uri: "file:///C:/workspace/src/main.rs".to_owned(),
            relative_path: "src/main.rs".to_owned(),
            language_id: "rust".to_owned(),
            last_modified: 42,
            size: 128,
            dependencies: Vec::new(),
        }]);

        graph.save_to_disk(&path).unwrap();
        let loaded = WorkspaceGraph::load_from_disk(&path).unwrap();
        assert_eq!(loaded, graph);
        fs::remove_file(path).ok();
    }

    #[test]
    fn delete_change_removes_file() {
        let mut graph = WorkspaceGraph::default();
        graph.ingest_full_file_list(vec![FileEntry {
            uri: "file:///C:/workspace/src/main.rs".to_owned(),
            relative_path: "src/main.rs".to_owned(),
            language_id: "rust".to_owned(),
            last_modified: 42,
            size: 128,
            dependencies: Vec::new(),
        }]);

        graph
            .apply_change(WorkspaceChange {
                uri: "file:///C:/workspace/src/main.rs".to_owned(),
                change_type: FileChangeType::Deleted,
                relative_path: None,
                language_id: None,
            })
            .unwrap();
        assert_eq!(graph.len(), 0);
    }
}
