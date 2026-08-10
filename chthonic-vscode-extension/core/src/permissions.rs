use anyhow::{bail, Result};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub enum Permission {
    ReadFile,
    WriteFile,
    RunShell,
    NetworkRequest,
    McpTool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PermissionPolicy {
    pub allow_file_reads: bool,
    pub allow_file_writes: bool,
    pub allow_shell: bool,
    pub allow_network: bool,
    pub allow_mcp: bool,
}

impl PermissionPolicy {
    pub fn from_env() -> Self {
        let mut policy = Self::default();
        if let Some(allow_file_writes) = env_bool("CHTHONIC_ALLOW_FILE_WRITES")
            .or_else(|| env_bool("DEEPSEEK_CORE_ALLOW_FILE_WRITES"))
        {
            policy.allow_file_writes = allow_file_writes;
        }
        policy
    }

    pub fn check(&self, permissions: &[Permission]) -> Result<()> {
        for permission in permissions {
            match permission {
                Permission::ReadFile if !self.allow_file_reads => {
                    bail!("file read permission is not granted")
                }
                Permission::WriteFile if !self.allow_file_writes => {
                    bail!("file write permission is not granted")
                }
                Permission::RunShell if !self.allow_shell => {
                    bail!("shell execution permission is not granted")
                }
                Permission::NetworkRequest if !self.allow_network => {
                    bail!("network permission is not granted")
                }
                Permission::McpTool if !self.allow_mcp => {
                    bail!("MCP tool permission is not granted")
                }
                _ => {}
            }
        }
        Ok(())
    }
}

impl Default for PermissionPolicy {
    fn default() -> Self {
        Self {
            allow_file_reads: true,
            allow_file_writes: true,
            allow_shell: false,
            allow_network: true,
            allow_mcp: false,
        }
    }
}

fn env_bool(name: &str) -> Option<bool> {
    std::env::var(name).ok().and_then(|value| {
        let normalized = value.trim().to_lowercase();
        match normalized.as_str() {
            "1" | "true" | "yes" | "on" => Some(true),
            "0" | "false" | "no" | "off" => Some(false),
            _ => None,
        }
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn policy_denies_ungranted_write() {
        let policy = PermissionPolicy {
            allow_file_writes: false,
            ..PermissionPolicy::default()
        };
        let error = policy
            .check(&[Permission::WriteFile])
            .unwrap_err()
            .to_string();
        assert!(error.contains("file write permission"));
    }
}
