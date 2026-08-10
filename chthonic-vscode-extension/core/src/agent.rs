use crate::edit_plan::{EditPlan, EditPlanStore, EditRange, FileEdit, Position};
use crate::permissions::{Permission, PermissionPolicy};
use crate::protocol::ChatRequest;
use crate::provider::{provider_from_config, ProviderConfig, ProviderResponse};
use crate::session::{
    now_ms, rollback_base_path, snippet_base_path, workspace_graph_path, ChatMessage, SessionState,
};
use crate::snippet_store::SnippetStore;
use crate::workspace_graph::{FileEntry, WorkspaceChange, WorkspaceGraph};
use anyhow::{Context, Result};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::sync::RwLock;

pub struct Agent {
    config: RwLock<ProviderConfig>,
    workspace_graph: RwLock<WorkspaceGraph>,
    edit_plans: RwLock<EditPlanStore>,
    snippets: RwLock<SnippetStore>,
    permissions: RwLock<PermissionPolicy>,
    session: RwLock<SessionState>,
    cancel_token: Arc<AtomicBool>,
}

impl Agent {
    pub fn from_env() -> Result<Self> {
        let config = ProviderConfig::from_env();
        let mut session = SessionState::load().context("failed to load DeepSeek Code session")?;
        if session.provider.is_empty() {
            session.provider = config.requested.clone();
        }
        let mut workspace_graph = WorkspaceGraph::load_from_disk(&workspace_graph_path()?)
            .context("failed to load workspace graph")?;
        if workspace_graph.len() == 0 && !session.workspace_snapshot.is_empty() {
            workspace_graph.ingest_full_file_list(
                session
                    .workspace_snapshot
                    .iter()
                    .map(|file| FileEntry {
                        uri: path_or_uri_to_uri(file),
                        relative_path: file.clone(),
                        language_id: String::new(),
                        last_modified: 0,
                        size: 0,
                        dependencies: Vec::new(),
                    })
                    .collect(),
            );
        }

        Ok(Self {
            workspace_graph: RwLock::new(workspace_graph),
            config: RwLock::new(config),
            edit_plans: RwLock::new(EditPlanStore::with_rollback_base_path(rollback_base_path()?)),
            snippets: RwLock::new(SnippetStore::with_base_path(snippet_base_path()?)),
            permissions: RwLock::new(PermissionPolicy::from_env()),
            session: RwLock::new(session),
            cancel_token: Arc::new(AtomicBool::new(false)),
        })
    }

    pub fn cancel(&self) {
        self.cancel_token.store(true, Ordering::SeqCst);
    }

    pub fn reset_cancel(&self) {
        self.cancel_token.store(false, Ordering::SeqCst);
    }

    pub fn is_cancelled(&self) -> bool {
        self.cancel_token.load(Ordering::SeqCst)
    }

    pub fn initialize_keys(
        &self,
        deepseek_api_key: Option<String>,
        openai_api_key: Option<String>,
        anthropic_api_key: Option<String>,
    ) -> Result<()> {
        let mut config = self.config.write().expect("provider config lock poisoned");
        config.deepseek_api_key = deepseek_api_key.or_else(|| config.deepseek_api_key.clone());
        config.openai_api_key = openai_api_key.or_else(|| config.openai_api_key.clone());
        config.anthropic_api_key = anthropic_api_key.or_else(|| config.anthropic_api_key.clone());
        drop(config);
        self.save_session()
    }

    pub fn save_session(&self) -> Result<()> {
        self.session
            .read()
            .expect("session lock poisoned")
            .save()
            .context("failed to save DeepSeek Code session")
    }

    pub fn restored_counts(&self) -> (usize, usize) {
        let session = self.session.read().expect("session lock poisoned");
        let graph_len = self
            .workspace_graph
            .read()
            .expect("workspace graph lock poisoned")
            .len();
        (session.conversation.len(), graph_len)
    }

    pub fn set_workspace_files(&self, files: Vec<FileEntry>) -> Result<usize> {
        let count = files.len();
        {
            let mut graph = self
                .workspace_graph
                .write()
                .expect("workspace graph lock poisoned");
            graph.ingest_full_file_list(files);
            graph
                .save_to_disk(&workspace_graph_path()?)
                .context("failed to save workspace graph")?;
        }
        {
            let files = self
                .workspace_graph
                .read()
                .expect("workspace graph lock poisoned")
                .files
                .keys()
                .cloned()
                .collect();
            let provider = self
                .config
                .read()
                .expect("provider config lock poisoned")
                .requested
                .clone();
            let mut session = self.session.write().expect("session lock poisoned");
            session.workspace_snapshot = files;
            session.provider = provider;
        }
        self.save_session()?;
        Ok(count)
    }

    pub fn apply_workspace_changes(&self, changes: Vec<WorkspaceChange>) -> Result<usize> {
        let count = {
            let mut graph = self
                .workspace_graph
                .write()
                .expect("workspace graph lock poisoned");
            for change in changes {
                graph.apply_change(change)?;
            }
            graph
                .save_to_disk(&workspace_graph_path()?)
                .context("failed to save workspace graph")?;
            graph.len()
        };
        {
            let files = self
                .workspace_graph
                .read()
                .expect("workspace graph lock poisoned")
                .files
                .keys()
                .cloned()
                .collect();
            self.session
                .write()
                .expect("session lock poisoned")
                .workspace_snapshot = files;
        }
        self.save_session()?;
        Ok(count)
    }

    pub fn workspace_graph(&self) -> WorkspaceGraph {
        self.workspace_graph
            .read()
            .expect("workspace graph lock poisoned")
            .clone()
    }

    pub fn status(&self) -> Result<(String, usize, usize, bool, bool, bool, PermissionPolicy)> {
        let provider = self
            .config
            .read()
            .expect("provider config lock poisoned")
            .requested
            .clone();
        let file_count = self
            .workspace_graph
            .read()
            .expect("workspace graph lock poisoned")
            .len();
        let conversation_len = self
            .session
            .read()
            .expect("session lock poisoned")
            .conversation
            .len();
        let permissions = self
            .permissions
            .read()
            .expect("permissions lock poisoned")
            .clone();
        let cancelled = self.is_cancelled();
        Ok((
            provider,
            file_count,
            conversation_len,
            true,
            true,
            cancelled,
            permissions,
        ))
    }

    pub fn create_probe_plan(&self, uri: String) -> Result<EditPlan> {
        let plan = self
            .edit_plans
            .write()
            .expect("edit plan lock poisoned")
            .create_probe_plan(uri);
        {
            let mut session = self.session.write().expect("session lock poisoned");
            if !session.active_plan_ids.contains(&plan.plan_id) {
                session.active_plan_ids.push(plan.plan_id.clone());
            }
        }
        self.save_session()?;
        Ok(plan)
    }

    pub fn create_snippet_plan(&self, uri: String) -> Result<EditPlan> {
        let range = EditRange {
            start: Position {
                line: 0,
                character: 0,
            },
            end: Position {
                line: 0,
                character: 0,
            },
        };
        let plan = EditPlan {
            plan_id: format!("plan-{}", now_ms()),
            summary: "Insert a chthonic snippet-guarded probe comment".to_owned(),
            edits: vec![FileEdit {
                uri,
                range,
                new_text: "// chthonic snippet-guarded edit\n".to_owned(),
                snippet_id: None,
            }],
            required_permissions: vec![Permission::WriteFile],
            created_at_ms: now_ms(),
        };
        self.register_provider_plan(plan)
    }

    pub fn register_provider_plan(&self, mut plan: EditPlan) -> Result<EditPlan> {
        self.check_permissions(&plan.required_permissions)?;
        {
            let mut snippets = self.snippets.write().expect("snippet store lock poisoned");
            for edit in &mut plan.edits {
                let snippet = snippets.create(&edit.uri, edit.range.clone())?;
                edit.snippet_id = Some(snippet.snippet_id);
            }
        }

        self.edit_plans
            .write()
            .expect("edit plan lock poisoned")
            .insert_pending(plan.clone());
        {
            let mut session = self.session.write().expect("session lock poisoned");
            if !session.active_plan_ids.contains(&plan.plan_id) {
                session.active_plan_ids.push(plan.plan_id.clone());
            }
        }
        self.save_session()?;
        Ok(plan)
    }

    pub fn pending_plan(&self, plan_id: &str) -> Result<EditPlan> {
        self.edit_plans
            .read()
            .expect("edit plan lock poisoned")
            .pending_plan(plan_id)
            .with_context(|| format!("unknown pending edit plan: {plan_id}"))
    }

    pub fn check_permissions(&self, permissions: &[Permission]) -> Result<()> {
        self.permissions
            .read()
            .expect("permissions lock poisoned")
            .check(permissions)
    }

    pub fn validate_plan_snippets(&self, plan: &EditPlan) -> Result<()> {
        let snippets = self.snippets.read().expect("snippet store lock poisoned");
        for edit in &plan.edits {
            if let Some(snippet_id) = &edit.snippet_id {
                snippets.validate(snippet_id)?;
            }
        }
        Ok(())
    }

    pub fn confirm_plan(&self, plan_id: &str) -> Result<EditPlan> {
        let plan = self
            .edit_plans
            .write()
            .expect("edit plan lock poisoned")
            .confirm(plan_id)?;
        {
            let mut session = self.session.write().expect("session lock poisoned");
            session.active_plan_ids.retain(|id| id != plan_id);
        }
        self.save_session()?;
        Ok(plan)
    }

    pub fn reject_plan(&self, plan_id: &str) -> Result<bool> {
        let rejected = self
            .edit_plans
            .write()
            .expect("edit plan lock poisoned")
            .reject(plan_id);
        {
            let mut session = self.session.write().expect("session lock poisoned");
            session.active_plan_ids.retain(|id| id != plan_id);
        }
        self.save_session()?;
        Ok(rejected)
    }

    pub fn rollback_plan(&self, plan_id: Option<&str>) -> Result<(String, Vec<FileEdit>)> {
        let rollback = self
            .edit_plans
            .write()
            .expect("edit plan lock poisoned")
            .rollback(plan_id)?;
        self.save_session()?;
        Ok(rollback)
    }

    pub fn stream_chat(
        &self,
        request: &ChatRequest,
        mut on_delta: impl FnMut(&str) -> Result<()>,
    ) -> Result<Vec<EditPlan>> {
        let config = self
            .config
            .read()
            .expect("provider config lock poisoned")
            .clone();
        let indexed_count = self
            .workspace_graph
            .read()
            .expect("workspace graph lock poisoned")
            .len();
        let mut request = request.clone();
        request.workspace = format!("{} ({} files indexed)", request.workspace, indexed_count);
        let provider =
            provider_from_config(&config).context("failed to initialize chat provider")?;
        {
            let mut session = self.session.write().expect("session lock poisoned");
            session.provider = config.requested.clone();
            session.conversation.push(ChatMessage {
                role: "user".to_owned(),
                content: request.text.clone(),
                timestamp_ms: now_ms(),
            });
        }

        let mut assistant_response = String::new();
        let mut proposed_plans = Vec::new();
        self.reset_cancel();
        let result = provider.stream(&request, &self.cancel_token, &mut |event| match event {
            ProviderResponse::Token(delta) => {
                assistant_response.push_str(&delta);
                on_delta(&delta)
            }
            ProviderResponse::Plan(plan) => {
                proposed_plans.push(plan);
                Ok(())
            }
        });

        if result.is_ok() {
            let mut session = self.session.write().expect("session lock poisoned");
            session.conversation.push(ChatMessage {
                role: "assistant".to_owned(),
                content: assistant_response,
                timestamp_ms: now_ms(),
            });
        }

        self.save_session()?;
        if self.is_cancelled() {
            self.reset_cancel();
        }
        result?;

        let mut registered_plans = Vec::new();
        for plan in proposed_plans {
            registered_plans.push(self.register_provider_plan(plan)?);
        }

        Ok(registered_plans)
    }
}

fn path_or_uri_to_uri(path_or_uri: &str) -> String {
    if path_or_uri.starts_with("file://") {
        path_or_uri.to_owned()
    } else {
        format!("file:///{}", path_or_uri.replace('\\', "/"))
    }
}
