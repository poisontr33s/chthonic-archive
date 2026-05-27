// Checkpoint — step-level rewindability for the toolkit's stateful operations.
// Complements git's commit-level rewindability and the ledger's run-level
// regression detection. The three resolutions stack:
//
//   commit-level   git revert HEAD        coarse, durable across sessions
//   run-level      ledger comparison      detects regressions across runs
//   step-level     checkpoint snapshot    backtracks individual mutations
//
// Each `dsl-iter check` (and similar stateful op) snapshots the state files it's
// about to modify BEFORE the mutation. If something goes wrong (catalog
// corruption, ledger out of sync, unexpected coverage results), `dsl-iter revert`
// restores the snapshot.

use anyhow::{anyhow, Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};

/// Where checkpoints live (relative to manifest_dir): `<manifest_dir>/.checkpoints/`
pub const CHECKPOINT_DIR_NAME: &str = ".checkpoints";

/// Default retention — keep this many checkpoints before pruning oldest.
pub const DEFAULT_RETENTION: usize = 20;

/// Manifest of one checkpoint — describes what was snapshotted.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CheckpointManifest {
    pub id: String,                    // ISO-timestamp-based id
    pub created_at: DateTime<Utc>,
    pub reason: String,                // e.g. "pre-check" / "pre-pattern-add"
    pub files: Vec<CheckpointedFile>,
    pub git_head: Option<String>,
    pub grammar_hash: Option<String>,
    pub project_name: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CheckpointedFile {
    /// Original path (relative to project root)
    pub original_path: PathBuf,
    /// Where the snapshot lives inside the checkpoint dir
    pub snapshot_path: PathBuf,
    /// Was the original missing at snapshot time? (so revert means deletion)
    pub was_missing: bool,
    pub size_bytes: u64,
}

pub struct Checkpoint {
    /// Root dir for all checkpoints (typically manifest_dir/.checkpoints/)
    root: PathBuf,
}

impl Checkpoint {
    pub fn new(manifest_dir: impl AsRef<Path>) -> Self {
        Self { root: manifest_dir.as_ref().join(CHECKPOINT_DIR_NAME) }
    }

    /// Create a new checkpoint snapshotting the given state files.
    /// Files that don't currently exist are recorded with was_missing=true
    /// (so a revert deletes anything created since).
    pub fn create(
        &self,
        files: &[PathBuf],
        reason: &str,
        git_head: Option<String>,
        grammar_hash: Option<String>,
        project_name: Option<&str>,
    ) -> Result<CheckpointManifest> {
        let now = Utc::now();
        let id = now.format("%Y%m%dT%H%M%S%.3fZ").to_string();
        let ckpt_dir = self.root.join(&id);
        fs::create_dir_all(&ckpt_dir)
            .with_context(|| format!("create checkpoint dir {}", ckpt_dir.display()))?;

        let mut entries = Vec::new();
        for original in files {
            let snapshot_path = ckpt_dir.join(safe_name(original));
            let entry = if original.exists() {
                let bytes = fs::read(original)
                    .with_context(|| format!("read {}", original.display()))?;
                let size = bytes.len() as u64;
                fs::write(&snapshot_path, bytes)
                    .with_context(|| format!("write snapshot {}", snapshot_path.display()))?;
                CheckpointedFile {
                    original_path: original.clone(),
                    snapshot_path: snapshot_path.strip_prefix(&self.root).unwrap_or(&snapshot_path).to_path_buf(),
                    was_missing: false,
                    size_bytes: size,
                }
            } else {
                CheckpointedFile {
                    original_path: original.clone(),
                    snapshot_path: PathBuf::from(""),
                    was_missing: true,
                    size_bytes: 0,
                }
            };
            entries.push(entry);
        }

        let manifest = CheckpointManifest {
            id: id.clone(),
            created_at: now,
            reason: reason.into(),
            files: entries,
            git_head,
            grammar_hash,
            project_name: project_name.map(Into::into),
        };
        let manifest_path = ckpt_dir.join("manifest.json");
        fs::write(&manifest_path, serde_json::to_string_pretty(&manifest)? + "\n")?;

        Ok(manifest)
    }

    /// List checkpoints by id (newest first).
    pub fn list(&self) -> Result<Vec<CheckpointManifest>> {
        if !self.root.exists() {
            return Ok(vec![]);
        }
        let mut out = Vec::new();
        for entry in fs::read_dir(&self.root)? {
            let entry = entry?;
            let manifest_path = entry.path().join("manifest.json");
            if manifest_path.exists() {
                let content = fs::read_to_string(&manifest_path)?;
                let m: CheckpointManifest = serde_json::from_str(&content)?;
                out.push(m);
            }
        }
        out.sort_by(|a, b| b.id.cmp(&a.id));  // newest first
        Ok(out)
    }

    /// Load a specific checkpoint by id.
    pub fn load(&self, id: &str) -> Result<CheckpointManifest> {
        let manifest_path = self.root.join(id).join("manifest.json");
        if !manifest_path.exists() {
            return Err(anyhow!("checkpoint {} not found at {}", id, manifest_path.display()));
        }
        let content = fs::read_to_string(&manifest_path)?;
        Ok(serde_json::from_str(&content)?)
    }

    /// Restore a checkpoint — overwrites originals + deletes anything created since.
    pub fn restore(&self, id: &str) -> Result<()> {
        let manifest = self.load(id)?;
        for f in &manifest.files {
            if f.was_missing {
                // Original didn't exist at checkpoint time; if it exists now, delete it.
                if f.original_path.exists() {
                    fs::remove_file(&f.original_path)
                        .with_context(|| format!("remove {}", f.original_path.display()))?;
                }
            } else {
                let snapshot = self.root.join(&f.snapshot_path);
                if let Some(parent) = f.original_path.parent() {
                    fs::create_dir_all(parent)?;
                }
                fs::copy(&snapshot, &f.original_path)
                    .with_context(|| format!("restore {} from {}", f.original_path.display(), snapshot.display()))?;
            }
        }
        Ok(())
    }

    /// Prune oldest checkpoints, keeping only `retention` newest.
    pub fn prune(&self, retention: usize) -> Result<usize> {
        let mut all = self.list()?;
        if all.len() <= retention {
            return Ok(0);
        }
        // all is newest-first; drain from index `retention` onward
        let to_remove: Vec<_> = all.drain(retention..).collect();
        let mut count = 0;
        for m in &to_remove {
            let dir = self.root.join(&m.id);
            if dir.exists() {
                fs::remove_dir_all(&dir)
                    .with_context(|| format!("remove checkpoint dir {}", dir.display()))?;
                count += 1;
            }
        }
        Ok(count)
    }
}

/// Convert a path to a safe filename for storing inside the checkpoint dir.
fn safe_name(p: &Path) -> String {
    p.to_string_lossy()
        .replace(['/', '\\', ':'], "_")
}
