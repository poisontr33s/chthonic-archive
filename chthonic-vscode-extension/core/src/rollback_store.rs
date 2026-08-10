use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct PlanSnapshot {
    pub plan_id: String,
    pub edits: Vec<FileSnapshot>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct FileSnapshot {
    pub uri: String,
    pub original_content: String,
    pub original_hash: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub applied_hash: Option<String>,
}

pub fn load_all(base_path: &Path) -> Vec<PlanSnapshot> {
    let Ok(entries) = fs::read_dir(base_path) else {
        return Vec::new();
    };

    entries
        .filter_map(Result::ok)
        .map(|entry| entry.path())
        .filter(|path| {
            path.extension()
                .is_some_and(|extension| extension == "json")
        })
        .filter_map(|path| load_one(&path).ok())
        .collect()
}

pub fn save(plan: &PlanSnapshot, base_path: &Path) -> Result<()> {
    fs::create_dir_all(base_path).with_context(|| {
        format!(
            "failed to create rollback snapshot directory: {}",
            base_path.display()
        )
    })?;
    let path = snapshot_path(base_path, &plan.plan_id);
    let content = serde_json::to_string_pretty(plan)
        .with_context(|| format!("failed to serialize rollback snapshot: {}", plan.plan_id))?;
    fs::write(&path, content)
        .with_context(|| format!("failed to write rollback snapshot: {}", path.display()))
}

#[allow(dead_code)]
pub fn delete(plan_id: &str, base_path: &Path) -> Result<()> {
    let path = snapshot_path(base_path, plan_id);
    match fs::remove_file(&path) {
        Ok(()) => Ok(()),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(()),
        Err(error) => Err(error)
            .with_context(|| format!("failed to delete rollback snapshot: {}", path.display())),
    }
}

pub fn sha256_hex(content: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(content.as_bytes());
    format!("{:x}", hasher.finalize())
}

fn load_one(path: &Path) -> Result<PlanSnapshot> {
    let content = fs::read_to_string(path)
        .with_context(|| format!("failed to read rollback snapshot: {}", path.display()))?;
    serde_json::from_str(&content)
        .with_context(|| format!("failed to parse rollback snapshot: {}", path.display()))
}

fn snapshot_path(base_path: &Path, plan_id: &str) -> PathBuf {
    base_path.join(format!("{}.json", safe_plan_id(plan_id)))
}

fn safe_plan_id(plan_id: &str) -> String {
    plan_id
        .chars()
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
    fn snapshot_roundtrip_preserves_content() {
        let base = std::env::temp_dir().join(format!(
            "chthonic-test-rollback-{}",
            crate::session::now_ms()
        ));
        let plan = PlanSnapshot {
            plan_id: "plan-test".to_owned(),
            edits: vec![FileSnapshot {
                uri: "file:///C:/tmp/probe.txt".to_owned(),
                original_content: "alpha".to_owned(),
                original_hash: sha256_hex("alpha"),
                applied_hash: Some(sha256_hex("beta")),
            }],
        };

        save(&plan, &base).unwrap();
        let loaded = load_all(&base);
        assert_eq!(loaded, vec![plan]);

        delete("plan-test", &base).unwrap();
        fs::remove_dir_all(base).ok();
    }
}
