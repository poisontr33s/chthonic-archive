use crate::permissions::Permission;
use crate::rollback_store::{self, FileSnapshot, PlanSnapshot};
use anyhow::{bail, Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct Position {
    pub line: usize,
    pub character: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct EditRange {
    pub start: Position,
    pub end: Position,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct FileEdit {
    pub uri: String,
    pub range: EditRange,
    pub new_text: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub snippet_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct EditPlan {
    pub plan_id: String,
    pub summary: String,
    pub edits: Vec<FileEdit>,
    pub required_permissions: Vec<Permission>,
    pub created_at_ms: u128,
}

#[derive(Debug, Default)]
pub struct EditPlanStore {
    pending: HashMap<String, EditPlan>,
    snapshots: HashMap<String, PlanSnapshot>,
    last_applied: Option<String>,
    rollback_base_path: Option<PathBuf>,
}

impl EditPlanStore {
    pub fn with_rollback_base_path(base_path: PathBuf) -> Self {
        let mut store = Self {
            rollback_base_path: Some(base_path.clone()),
            ..Self::default()
        };
        store.hydrate_snapshots(&base_path);
        store
    }

    pub fn create_probe_plan(&mut self, uri: String) -> EditPlan {
        let plan = EditPlan {
            plan_id: new_plan_id(),
            summary: "Insert a deepseek-core probe comment".to_owned(),
            edits: vec![FileEdit {
                uri,
                range: EditRange {
                    start: Position {
                        line: 0,
                        character: 0,
                    },
                    end: Position {
                        line: 0,
                        character: 0,
                    },
                },
                new_text: "// deepseek-core planned edit\n".to_owned(),
                snippet_id: None,
            }],
            required_permissions: vec![Permission::WriteFile],
            created_at_ms: now_ms(),
        };

        self.pending.insert(plan.plan_id.clone(), plan.clone());
        plan
    }

    pub fn reject(&mut self, plan_id: &str) -> bool {
        self.pending.remove(plan_id).is_some()
    }

    pub fn pending_plan(&self, plan_id: &str) -> Option<EditPlan> {
        self.pending.get(plan_id).cloned()
    }

    pub fn insert_pending(&mut self, plan: EditPlan) {
        self.pending.insert(plan.plan_id.clone(), plan);
    }

    pub fn confirm(&mut self, plan_id: &str) -> Result<EditPlan> {
        let plan = self
            .pending
            .remove(plan_id)
            .with_context(|| format!("unknown pending edit plan: {plan_id}"))?;

        let mut snapshots = Vec::new();
        for edit in &plan.edits {
            let path = uri_to_path(&edit.uri)?;
            let original = fs::read_to_string(&path).unwrap_or_default();
            let applied = apply_edit(&original, edit)
                .with_context(|| format!("failed to compute rollback guard for {}", edit.uri))?;
            snapshots.push(FileSnapshot {
                uri: edit.uri.clone(),
                original_hash: rollback_store::sha256_hex(&original),
                original_content: original,
                applied_hash: Some(rollback_store::sha256_hex(&applied)),
            });
        }

        let snapshot = PlanSnapshot {
            plan_id: plan.plan_id.clone(),
            edits: snapshots,
        };
        if let Some(base_path) = &self.rollback_base_path {
            rollback_store::save(&snapshot, base_path)?;
        }
        self.snapshots.insert(plan.plan_id.clone(), snapshot);
        self.last_applied = Some(plan.plan_id.clone());
        Ok(plan)
    }

    pub fn rollback(&mut self, plan_id: Option<&str>) -> Result<(String, Vec<FileEdit>)> {
        let selected = match plan_id {
            Some(plan_id) if !plan_id.trim().is_empty() => plan_id.to_owned(),
            _ => self
                .last_applied
                .clone()
                .context("no applied edit plan is available for rollback")?,
        };

        let snapshot = self
            .snapshots
            .get(&selected)
            .with_context(|| format!("no rollback snapshot found for plan: {selected}"))?;

        let mut edits = Vec::new();
        for file_snapshot in &snapshot.edits {
            let path = uri_to_path(&file_snapshot.uri)?;
            let current = fs::read_to_string(&path).unwrap_or_default();
            let current_hash = rollback_store::sha256_hex(&current);
            let expected_hash = file_snapshot
                .applied_hash
                .as_ref()
                .unwrap_or(&file_snapshot.original_hash);
            if &current_hash != expected_hash {
                bail!(
                    "rollback conflict for {}: current file hash does not match the confirmed edit snapshot",
                    file_snapshot.uri
                );
            }
            let end = document_end(&current);
            edits.push(FileEdit {
                uri: file_snapshot.uri.clone(),
                range: EditRange {
                    start: Position {
                        line: 0,
                        character: 0,
                    },
                    end,
                },
                new_text: file_snapshot.original_content.clone(),
                snippet_id: None,
            });
        }

        if edits.is_empty() {
            bail!("rollback snapshot for plan {selected} has no files");
        }

        Ok((selected, edits))
    }

    fn hydrate_snapshots(&mut self, base_path: &Path) {
        for snapshot in rollback_store::load_all(base_path) {
            self.last_applied = Some(snapshot.plan_id.clone());
            self.snapshots.insert(snapshot.plan_id.clone(), snapshot);
        }
    }
}

fn new_plan_id() -> String {
    format!("plan-{}", now_ms())
}

fn now_ms() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("system clock is before UNIX_EPOCH")
        .as_millis()
}

fn document_end(text: &str) -> Position {
    let mut line = 0;
    let mut character = 0;

    for ch in text.chars() {
        if ch == '\n' {
            line += 1;
            character = 0;
        } else {
            character += 1;
        }
    }

    Position { line, character }
}

fn apply_edit(original: &str, edit: &FileEdit) -> Result<String> {
    let start = position_to_byte_offset(original, &edit.range.start)?;
    let end = position_to_byte_offset(original, &edit.range.end)?;
    if start > end {
        bail!("edit range start is after end");
    }

    let mut content = String::with_capacity(original.len() + edit.new_text.len());
    content.push_str(&original[..start]);
    content.push_str(&edit.new_text);
    content.push_str(&original[end..]);
    Ok(content)
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

fn uri_to_path(uri: &str) -> Result<String> {
    let path = uri
        .strip_prefix("file:///")
        .with_context(|| format!("only file:/// URIs are supported: {uri}"))?;
    Ok(path.replace('/', "\\"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn document_end_counts_lines_and_characters() {
        assert_eq!(document_end("alpha\nbeta").line, 1);
        assert_eq!(document_end("alpha\nbeta").character, 4);
    }

    #[test]
    fn probe_plan_uses_nested_range_contract() {
        let mut store = EditPlanStore::default();
        let plan = store.create_probe_plan("file:///C:/probe.txt".to_owned());
        assert_eq!(plan.edits[0].range.start.line, 0);
        assert_eq!(plan.edits[0].range.end.character, 0);
        assert!(store.reject(&plan.plan_id));
    }

    #[test]
    fn apply_edit_replaces_nested_range() {
        let edit = FileEdit {
            uri: "file:///C:/probe.txt".to_owned(),
            range: EditRange {
                start: Position {
                    line: 1,
                    character: 1,
                },
                end: Position {
                    line: 1,
                    character: 3,
                },
            },
            new_text: "OO".to_owned(),
            snippet_id: None,
        };

        assert_eq!(apply_edit("abc\ndef", &edit).unwrap(), "abc\ndOO");
    }

    #[test]
    fn rollback_snapshot_survives_store_restart() {
        let base = std::env::temp_dir().join(format!(
            "chthonic-test-rollback-hydrate-{}",
            crate::session::now_ms()
        ));
        let file = base.join("probe.txt");
        fs::create_dir_all(&base).unwrap();
        fs::write(&file, "alpha").unwrap();

        let plan_id = "plan-hydrate".to_owned();
        let uri = path_to_file_uri(&file);
        let mut store = EditPlanStore::with_rollback_base_path(base.join("rollback"));
        store.pending.insert(
            plan_id.clone(),
            EditPlan {
                plan_id: plan_id.clone(),
                summary: "replace probe".to_owned(),
                edits: vec![FileEdit {
                    uri: uri.clone(),
                    range: EditRange {
                        start: Position {
                            line: 0,
                            character: 0,
                        },
                        end: Position {
                            line: 0,
                            character: 5,
                        },
                    },
                    new_text: "beta".to_owned(),
                    snippet_id: None,
                }],
                required_permissions: vec![Permission::WriteFile],
                created_at_ms: now_ms(),
            },
        );

        store.confirm(&plan_id).unwrap();
        fs::write(&file, "beta").unwrap();

        let mut restored = EditPlanStore::with_rollback_base_path(base.join("rollback"));
        let (_, edits) = restored.rollback(Some(&plan_id)).unwrap();
        assert_eq!(edits[0].new_text, "alpha");

        fs::remove_dir_all(base).ok();
    }

    #[test]
    fn rollback_refuses_when_current_hash_drifted() {
        let base = std::env::temp_dir().join(format!(
            "chthonic-test-rollback-conflict-{}",
            crate::session::now_ms()
        ));
        let file = base.join("probe.txt");
        fs::create_dir_all(&base).unwrap();
        fs::write(&file, "alpha").unwrap();

        let plan_id = "plan-conflict".to_owned();
        let uri = path_to_file_uri(&file);
        let mut store = EditPlanStore::with_rollback_base_path(base.join("rollback"));
        store.pending.insert(
            plan_id.clone(),
            EditPlan {
                plan_id: plan_id.clone(),
                summary: "replace probe".to_owned(),
                edits: vec![FileEdit {
                    uri,
                    range: EditRange {
                        start: Position {
                            line: 0,
                            character: 0,
                        },
                        end: Position {
                            line: 0,
                            character: 5,
                        },
                    },
                    new_text: "beta".to_owned(),
                    snippet_id: None,
                }],
                required_permissions: vec![Permission::WriteFile],
                created_at_ms: now_ms(),
            },
        );

        store.confirm(&plan_id).unwrap();
        fs::write(&file, "gamma").unwrap();

        let error = store.rollback(Some(&plan_id)).unwrap_err().to_string();
        assert!(error.contains("rollback conflict"));

        fs::remove_dir_all(base).ok();
    }

    fn path_to_file_uri(path: &std::path::Path) -> String {
        format!("file:///{}", path.display().to_string().replace('\\', "/"))
    }
}
