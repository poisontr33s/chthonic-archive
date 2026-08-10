use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ChatMessage {
    pub role: String,
    pub content: String,
    pub timestamp_ms: u128,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct SessionState {
    pub conversation: Vec<ChatMessage>,
    pub active_plan_ids: Vec<String>,
    pub workspace_snapshot: Vec<String>,
    pub provider: String,
    pub last_modified_ms: u128,
}

impl SessionState {
    pub fn load() -> Result<Self> {
        Self::load_from(&session_path()?)
    }

    pub fn save(&self) -> Result<()> {
        Self::save_to(&session_path()?, self)
    }

    pub fn load_from(path: &Path) -> Result<Self> {
        if !path.exists() {
            return Ok(Self::default());
        }

        let content = fs::read_to_string(path)
            .with_context(|| format!("failed to read session file: {}", path.display()))?;
        serde_json::from_str(&content)
            .with_context(|| format!("failed to parse session file: {}", path.display()))
    }

    pub fn save_to(path: &Path, state: &Self) -> Result<()> {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).with_context(|| {
                format!("failed to create session directory: {}", parent.display())
            })?;
        }

        let mut state = state.clone();
        state.last_modified_ms = now_ms();
        let content =
            serde_json::to_string_pretty(&state).context("failed to serialize session")?;
        fs::write(path, content)
            .with_context(|| format!("failed to write session file: {}", path.display()))
    }
}

pub fn session_path() -> Result<PathBuf> {
    if let Some(path) = std::env::var_os("DEEPSEEK_CODE_SESSION_PATH") {
        return Ok(PathBuf::from(path));
    }

    Ok(session_base_path()?.join("session.json"))
}

pub fn session_base_path() -> Result<PathBuf> {
    if let Some(path) = std::env::var_os("DEEPSEEK_CODE_SESSION_PATH") {
        return PathBuf::from(path)
            .parent()
            .map(Path::to_path_buf)
            .context("DEEPSEEK_CODE_SESSION_PATH must include a file name");
    }

    let base = dirs_next::data_dir()
        .or_else(|| std::env::var_os("APPDATA").map(PathBuf::from))
        .context("failed to resolve APPDATA/session data directory")?;
    Ok(base.join("Chthonic").join("DeepSeekCode"))
}

pub fn rollback_base_path() -> Result<PathBuf> {
    Ok(session_base_path()?.join("rollback"))
}

pub fn workspace_graph_path() -> Result<PathBuf> {
    Ok(session_base_path()?.join("workspace_graph.json"))
}

pub fn snippet_base_path() -> Result<PathBuf> {
    Ok(session_base_path()?.join("snippets"))
}

pub fn now_ms() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("system clock is before UNIX_EPOCH")
        .as_millis()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn session_roundtrip() {
        let path = std::env::temp_dir().join(format!("chthonic-test-session-{}.json", now_ms()));
        let mut state = SessionState::default();
        state.provider = "deepseek".to_owned();
        state.conversation.push(ChatMessage {
            role: "user".to_owned(),
            content: "hello".to_owned(),
            timestamp_ms: now_ms(),
        });

        SessionState::save_to(&path, &state).unwrap();
        let loaded = SessionState::load_from(&path).unwrap();
        assert_eq!(loaded.provider, "deepseek");
        assert_eq!(loaded.conversation.len(), 1);
        fs::remove_file(path).ok();
    }
}
