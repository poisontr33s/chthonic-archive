use crate::edit_plan::{EditRange, Position};
use anyhow::{bail, Context, Result};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct Snippet {
    pub snippet_id: String,
    pub uri: String,
    pub range: EditRange,
    pub content: String,
    pub file_hash: String,
    pub created_at_ms: u128,
}

#[derive(Debug, Default)]
pub struct SnippetStore {
    snippets: HashMap<String, Snippet>,
    base_path: Option<PathBuf>,
}

impl SnippetStore {
    pub fn with_base_path(base_path: PathBuf) -> Self {
        let mut store = Self {
            base_path: Some(base_path),
            ..Self::default()
        };
        store.hydrate_from_disk();
        store
    }

    pub fn create(&mut self, uri: &str, range: EditRange) -> Result<Snippet> {
        let path = uri_to_path(uri)?;
        let file_content = fs::read_to_string(&path).with_context(|| {
            format!(
                "failed to read file for snippet creation: {}",
                path.display()
            )
        })?;
        let start = position_to_byte_offset(&file_content, &range.start)?;
        let end = position_to_byte_offset(&file_content, &range.end)?;
        if start > end {
            bail!("snippet range start is after end");
        }

        let snippet = Snippet {
            snippet_id: generate_snippet_id(),
            uri: uri.to_owned(),
            range,
            content: file_content[start..end].to_owned(),
            file_hash: sha256_hex(&file_content),
            created_at_ms: crate::session::now_ms(),
        };
        self.snippets
            .insert(snippet.snippet_id.clone(), snippet.clone());
        self.save_to_disk()?;
        Ok(snippet)
    }

    pub fn validate(&self, snippet_id: &str) -> Result<()> {
        let snippet = self
            .snippets
            .get(snippet_id)
            .with_context(|| format!("snippet not found: {snippet_id}"))?;
        let path = uri_to_path(&snippet.uri)?;
        let current = fs::read_to_string(&path).unwrap_or_default();
        let current_hash = sha256_hex(&current);
        if current_hash != snippet.file_hash {
            bail!(
                "snippet hash mismatch for {}: file changed after snippet {} was created",
                snippet.uri,
                snippet.snippet_id
            );
        }
        Ok(())
    }

    #[cfg(test)]
    pub fn len(&self) -> usize {
        self.snippets.len()
    }

    fn hydrate_from_disk(&mut self) {
        let Some(base_path) = &self.base_path else {
            return;
        };
        let Ok(entries) = fs::read_dir(base_path) else {
            return;
        };

        for entry in entries.filter_map(Result::ok) {
            let path = entry.path();
            if path
                .extension()
                .is_some_and(|extension| extension == "json")
            {
                if let Ok(content) = fs::read_to_string(&path) {
                    if let Ok(snippet) = serde_json::from_str::<Snippet>(&content) {
                        self.snippets.insert(snippet.snippet_id.clone(), snippet);
                    }
                }
            }
        }
    }

    fn save_to_disk(&self) -> Result<()> {
        let Some(base_path) = &self.base_path else {
            return Ok(());
        };
        fs::create_dir_all(base_path).with_context(|| {
            format!(
                "failed to create snippet store directory: {}",
                base_path.display()
            )
        })?;

        for snippet in self.snippets.values() {
            let path = base_path.join(format!("{}.json", safe_id(&snippet.snippet_id)));
            let content = serde_json::to_string_pretty(snippet)
                .with_context(|| format!("failed to serialize snippet: {}", snippet.snippet_id))?;
            fs::write(&path, content)
                .with_context(|| format!("failed to write snippet: {}", path.display()))?;
        }
        Ok(())
    }
}

pub fn uri_to_path(uri: &str) -> Result<PathBuf> {
    let path = uri
        .strip_prefix("file:///")
        .with_context(|| format!("only file:/// URIs are supported: {uri}"))?;
    Ok(PathBuf::from(path.replace('/', "\\")))
}

pub fn sha256_hex(content: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(content.as_bytes());
    format!("{:x}", hasher.finalize())
}

fn generate_snippet_id() -> String {
    format!("snip-{}", crate::session::now_ms())
}

fn position_to_byte_offset(text: &str, position: &Position) -> Result<usize> {
    let mut line = 0;
    let mut character = 0;

    for (offset, ch) in text.char_indices() {
        if line == position.line && character == position.character {
            return Ok(offset);
        }

        if ch == '\n' {
            line += 1;
            character = 0;
        } else {
            character += 1;
        }
    }

    if line == position.line && character == position.character {
        return Ok(text.len());
    }

    bail!(
        "position {}:{} is outside document bounds",
        position.line,
        position.character
    )
}

fn safe_id(id: &str) -> String {
    id.chars()
        .map(|ch| {
            if ch.is_ascii_alphanumeric() || ch == '-' || ch == '_' {
                ch
            } else {
                '_'
            }
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn snippet_roundtrip_and_validation() {
        let base = std::env::temp_dir().join(format!(
            "chthonic-test-snippets-{}",
            crate::session::now_ms()
        ));
        let file = base.join("probe.txt");
        fs::create_dir_all(&base).unwrap();
        fs::write(&file, "alpha\nbeta").unwrap();
        let uri = path_to_file_uri(&file);

        let mut store = SnippetStore::with_base_path(base.join("snippets"));
        let snippet = store
            .create(
                &uri,
                EditRange {
                    start: Position {
                        line: 0,
                        character: 0,
                    },
                    end: Position {
                        line: 0,
                        character: 5,
                    },
                },
            )
            .unwrap();
        assert_eq!(snippet.content, "alpha");

        let restored = SnippetStore::with_base_path(base.join("snippets"));
        restored.validate(&snippet.snippet_id).unwrap();
        assert_eq!(restored.len(), 1);

        fs::remove_dir_all(base).ok();
    }

    #[test]
    fn snippet_validation_detects_file_drift() {
        let base = std::env::temp_dir().join(format!(
            "chthonic-test-snippet-drift-{}",
            crate::session::now_ms()
        ));
        let file = base.join("probe.txt");
        fs::create_dir_all(&base).unwrap();
        fs::write(&file, "alpha").unwrap();
        let uri = path_to_file_uri(&file);

        let mut store = SnippetStore::with_base_path(base.join("snippets"));
        let snippet = store
            .create(
                &uri,
                EditRange {
                    start: Position {
                        line: 0,
                        character: 0,
                    },
                    end: Position {
                        line: 0,
                        character: 5,
                    },
                },
            )
            .unwrap();
        fs::write(&file, "gamma").unwrap();

        let error = store.validate(&snippet.snippet_id).unwrap_err().to_string();
        assert!(error.contains("snippet hash mismatch"));

        fs::remove_dir_all(base).ok();
    }

    fn path_to_file_uri(path: &std::path::Path) -> String {
        format!("file:///{}", path.display().to_string().replace('\\', "/"))
    }
}
