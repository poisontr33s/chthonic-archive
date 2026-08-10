use crate::agent::Agent;
use crate::edit_plan::{EditPlan, FileEdit};
use crate::protocol::{ChatRequest, RpcError, RpcRequest, RpcSuccess, JSONRPC_VERSION};
use crate::workspace_graph::{file_entry_from_path, uri_to_path, FileEntry, WorkspaceChange};
use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::io::{self, BufRead, Write};
use std::sync::Arc;
use std::thread;

pub fn run() -> Result<()> {
    let stdin = io::stdin();
    let agent = Arc::new(Agent::from_env()?);
    let (restored_messages, restored_files) = agent.restored_counts();
    write_json(&json!({
        "jsonrpc": JSONRPC_VERSION,
        "method": "core.log",
        "params": {
            "level": "info",
            "message": format!("Session restored: {restored_messages} messages, {restored_files} files indexed")
        }
    }))?;

    for line in stdin.lock().lines() {
        let line = line.context("failed to read stdin line")?;
        if line.trim().is_empty() {
            continue;
        }

        let request: RpcRequest = match serde_json::from_str(&line) {
            Ok(request) => request,
            Err(error) => {
                write_json(&RpcError::new(
                    Value::Null,
                    -32700,
                    format!("parse error: {error}"),
                ))?;
                continue;
            }
        };

        if let Err(error) = handle_request(agent.clone(), request) {
            write_json(&json!({
                "jsonrpc": JSONRPC_VERSION,
                "method": "core.log",
                "params": { "level": "error", "message": error.to_string() }
            }))?;
        }
    }

    Ok(())
}

fn handle_request(agent: Arc<Agent>, request: RpcRequest) -> Result<()> {
    match request.method.as_str() {
        "core.ping" => write_json(&RpcSuccess::new(
            request_id(&request),
            json!({ "ok": true, "engine": "deepseek-core", "version": env!("CARGO_PKG_VERSION") }),
        )),
        "initialize" => handle_initialize(&agent, request),
        "workspace/files" => handle_workspace_files(&agent, request),
        "workspace/fileChanged" => handle_workspace_file_changed(&agent, request),
        "workspace/graph" => handle_workspace_graph(&agent, request),
        "agent/status" => handle_status(&agent, request),
        "agent/cancel" => handle_cancel(&agent, request),
        "edit/confirm" => handle_edit_confirm(&agent, request),
        "edit/reject" => handle_edit_reject(&agent, request),
        "edit/rollback" => handle_edit_rollback(&agent, request),
        "chat.stream" => handle_chat_stream(agent, request),
        "core.shutdown" => {
            write_json(&RpcSuccess::new(
                request_id(&request),
                json!({ "ok": true }),
            ))?;
            std::process::exit(0);
        }
        method => write_json(&RpcError::new(
            request_id(&request),
            -32601,
            format!("unknown method: {method}"),
        )),
    }
}

fn handle_cancel(agent: &Agent, request: RpcRequest) -> Result<()> {
    agent.cancel();
    write_json(&RpcSuccess::new(
        request_id(&request),
        json!({ "ok": true, "cancelled": true }),
    ))
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct InitializeParams {
    deepseek_api_key: Option<String>,
    openai_api_key: Option<String>,
    anthropic_api_key: Option<String>,
}

#[derive(Debug, Deserialize)]
struct WorkspaceFilesParams {
    files: Vec<WorkspaceFileParam>,
}

#[derive(Debug, Deserialize)]
#[serde(untagged)]
enum WorkspaceFileParam {
    Path(String),
    Entry(FileEntry),
}

#[derive(Debug, Deserialize)]
struct WorkspaceFileChangedParams {
    changes: Vec<WorkspaceChange>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct PlanIdParams {
    plan_id: Option<String>,
}

fn handle_initialize(agent: &Agent, request: RpcRequest) -> Result<()> {
    let id = request_id(&request);
    let params: InitializeParams =
        serde_json::from_value(request.params).unwrap_or(InitializeParams {
            openai_api_key: None,
            anthropic_api_key: None,
            deepseek_api_key: None,
        });

    let has_deepseek = params
        .deepseek_api_key
        .as_ref()
        .is_some_and(|key| !key.is_empty());
    let has_openai = params
        .openai_api_key
        .as_ref()
        .is_some_and(|key| !key.is_empty());
    let has_anthropic = params
        .anthropic_api_key
        .as_ref()
        .is_some_and(|key| !key.is_empty());

    agent.initialize_keys(
        params.deepseek_api_key.filter(|key| !key.is_empty()),
        params.openai_api_key.filter(|key| !key.is_empty()),
        params.anthropic_api_key.filter(|key| !key.is_empty()),
    )?;

    write_json(&RpcSuccess::new(
        id,
        json!({
            "ok": true,
            "deepseekKeyLoaded": has_deepseek,
            "openaiKeyLoaded": has_openai,
            "anthropicKeyLoaded": has_anthropic
        }),
    ))
}

fn handle_workspace_files(agent: &Agent, request: RpcRequest) -> Result<()> {
    let id = request_id(&request);
    let params: WorkspaceFilesParams = serde_json::from_value(request.params)
        .context("workspace/files params must contain files: string[]")?;
    let files = params
        .files
        .into_iter()
        .map(workspace_file_param_to_entry)
        .collect::<Result<Vec<_>>>()?;
    let count = agent.set_workspace_files(files)?;
    write_json(&RpcSuccess::new(id, json!({ "ok": true, "count": count })))
}

fn handle_status(agent: &Agent, request: RpcRequest) -> Result<()> {
    let (
        provider,
        workspace_file_count,
        conversation_len,
        session_loaded,
        graph_loaded,
        cancelled,
        permissions,
    ) = agent.status()?;
    write_json(&RpcSuccess::new(
        request_id(&request),
        json!({
            "ok": true,
            "provider": provider,
            "workspaceFileCount": workspace_file_count,
            "conversationLength": conversation_len,
            "sessionLoaded": session_loaded,
            "workspaceGraphLoaded": graph_loaded,
            "cancelled": cancelled,
            "permissions": permissions
        }),
    ))
}

fn handle_workspace_file_changed(agent: &Agent, request: RpcRequest) -> Result<()> {
    let has_id = request.id.is_some();
    let id = request_id(&request);
    let params: WorkspaceFileChangedParams = serde_json::from_value(request.params)
        .context("workspace/fileChanged params must contain changes")?;
    let count = agent.apply_workspace_changes(params.changes)?;
    write_json(&json!({
        "jsonrpc": JSONRPC_VERSION,
        "method": "core.log",
        "params": {
            "level": "info",
            "message": format!("Workspace graph updated: {count} files indexed")
        }
    }))?;
    if has_id {
        write_json(&RpcSuccess::new(id, json!({ "ok": true, "count": count })))?;
    }
    Ok(())
}

fn handle_workspace_graph(agent: &Agent, request: RpcRequest) -> Result<()> {
    write_json(&RpcSuccess::new(
        request_id(&request),
        json!({ "ok": true, "graph": agent.workspace_graph() }),
    ))
}

fn handle_edit_confirm(agent: &Agent, request: RpcRequest) -> Result<()> {
    let id = request_id(&request);
    let result = (|| -> Result<EditPlan> {
        let params: PlanIdParams =
            serde_json::from_value(request.params).context("edit/confirm requires planId")?;
        let plan_id = params.plan_id.context("edit/confirm requires planId")?;
        let pending = agent.pending_plan(&plan_id)?;
        agent.check_permissions(&pending.required_permissions)?;
        agent.validate_plan_snippets(&pending)?;
        agent.confirm_plan(&plan_id)
    })();

    match result {
        Ok(plan) => {
            emit_diff_apply(&plan.edits)?;
            write_json(&RpcSuccess::new(
                id,
                json!({ "ok": true, "planId": plan.plan_id, "applied": plan.edits.len() }),
            ))
        }
        Err(error) => {
            let message = error.to_string();
            write_json(&json!({
                "jsonrpc": JSONRPC_VERSION,
                "method": "core.log",
                "params": { "level": "error", "message": message }
            }))?;
            write_json(&RpcError::new(id, -32000, message))
        }
    }
}

fn handle_edit_reject(agent: &Agent, request: RpcRequest) -> Result<()> {
    let id = request_id(&request);
    let params: PlanIdParams =
        serde_json::from_value(request.params).context("edit/reject requires planId")?;
    let plan_id = params.plan_id.context("edit/reject requires planId")?;
    let rejected = agent.reject_plan(&plan_id)?;
    write_json(&RpcSuccess::new(
        id,
        json!({ "ok": true, "planId": plan_id, "rejected": rejected }),
    ))
}

fn handle_edit_rollback(agent: &Agent, request: RpcRequest) -> Result<()> {
    let id = request_id(&request);
    let params: PlanIdParams =
        serde_json::from_value(request.params).unwrap_or(PlanIdParams { plan_id: None });
    let (plan_id, edits) = agent.rollback_plan(params.plan_id.as_deref())?;
    emit_diff_apply(&edits)?;
    write_json(&RpcSuccess::new(
        id,
        json!({ "ok": true, "planId": plan_id, "reverted": edits.len() }),
    ))
}

fn handle_chat_stream(agent: Arc<Agent>, request: RpcRequest) -> Result<()> {
    let id = request_id(&request);
    let chat = ChatRequest {
        text: request
            .params
            .get("text")
            .and_then(Value::as_str)
            .unwrap_or_default()
            .trim()
            .to_owned(),
        workspace: request
            .params
            .get("workspace")
            .and_then(Value::as_str)
            .unwrap_or("unknown workspace")
            .to_owned(),
    };

    if let Some(path) = chat.text.trim().strip_prefix("/snippet-plan ") {
        let uri = if path.starts_with("file://") {
            path.to_owned()
        } else {
            format!("file:///{}", path.replace('\\', "/"))
        };

        write_json(&json!({
            "jsonrpc": JSONRPC_VERSION,
            "method": "edit/plan",
            "params": agent.create_snippet_plan(uri)?
        }))?;
    } else if let Some(path) = chat.text.trim().strip_prefix("/plan-edit ") {
        let uri = if path.starts_with("file://") {
            path.to_owned()
        } else {
            format!("file:///{}", path.replace('\\', "/"))
        };

        write_json(&json!({
            "jsonrpc": JSONRPC_VERSION,
            "method": "edit/plan",
            "params": agent.create_probe_plan(uri)?
        }))?;
    } else {
        thread::spawn(move || {
            let stream_result = agent.stream_chat(&chat, |delta| {
                write_json(&json!({
                    "jsonrpc": JSONRPC_VERSION,
                    "method": "chat.chunk",
                    "params": {
                        "id": id,
                        "delta": delta,
                    }
                }))
            });

            match stream_result {
                Ok(provider_plans) => {
                    for plan in provider_plans {
                        if let Err(error) = write_json(&json!({
                            "jsonrpc": JSONRPC_VERSION,
                            "method": "edit/plan",
                            "params": plan
                        })) {
                            let _ = write_json(&RpcError::new(
                                id.clone(),
                                -32000,
                                format!("failed to emit edit plan: {error}"),
                            ));
                            return;
                        }
                    }

                    let _ = write_json(&RpcSuccess::new(
                        id,
                        json!({ "ok": true, "finishReason": "stop" }),
                    ));
                }
                Err(error) => {
                    let message = error.to_string();
                    let _ = write_json(&json!({
                        "jsonrpc": JSONRPC_VERSION,
                        "method": "core.log",
                        "params": { "level": "error", "message": message }
                    }));
                    let _ = write_json(&RpcError::new(id, -32000, message));
                }
            }
        });
        return Ok(());
    }

    write_json(&RpcSuccess::new(
        id,
        json!({ "ok": true, "finishReason": "stop" }),
    ))
}

fn workspace_file_param_to_entry(file: WorkspaceFileParam) -> Result<FileEntry> {
    match file {
        WorkspaceFileParam::Entry(entry) => Ok(entry),
        WorkspaceFileParam::Path(path) => {
            let uri = if path.starts_with("file://") {
                path.clone()
            } else {
                format!("file:///{}", path.replace('\\', "/"))
            };
            file_entry_from_path(
                uri.clone(),
                uri_to_path(&uri).unwrap_or_else(|_| std::path::PathBuf::from(path)),
                None,
                None,
            )
        }
    }
}

fn request_id(request: &RpcRequest) -> Value {
    request.id.clone().unwrap_or(Value::Null)
}

fn emit_diff_apply(edits: &[FileEdit]) -> Result<()> {
    write_json(&json!({
        "jsonrpc": JSONRPC_VERSION,
        "method": "diff/apply",
        "params": {
            "edits": edits
        }
    }))
}

fn write_json<T: Serialize>(value: &T) -> Result<()> {
    let mut stdout = io::stdout().lock();
    serde_json::to_writer(&mut stdout, value).context("failed to serialize response")?;
    stdout
        .write_all(b"\n")
        .context("failed to write response newline")?;
    stdout.flush().context("failed to flush stdout")
}
