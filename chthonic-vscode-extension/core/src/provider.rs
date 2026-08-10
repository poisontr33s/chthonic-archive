use crate::edit_plan::{EditPlan, EditRange, FileEdit, Position};
use crate::permissions::Permission;
use crate::plan_parser::parse_plan_from_text;
use crate::protocol::ChatRequest;
use anyhow::{bail, Context, Result};
use reqwest::blocking::{Client, Response};
use reqwest::header::{ACCEPT, CONTENT_TYPE};
use serde_json::{json, Value};
use std::env;
use std::io::{BufRead, BufReader};
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;
use std::time::Duration;

const OPENAI_RESPONSES_URL: &str = "https://api.openai.com/v1/responses";
const ANTHROPIC_MESSAGES_URL: &str = "https://api.anthropic.com/v1/messages";
const DEEPSEEK_CHAT_COMPLETIONS_URL: &str = "https://api.deepseek.com/chat/completions";
const DEFAULT_OPENAI_MODEL: &str = "gpt-5.3-codex";
const DEFAULT_ANTHROPIC_MODEL: &str = "claude-opus-4-8";
const DEFAULT_DEEPSEEK_MODEL: &str = "deepseek-chat";

pub trait ChatProvider {
    fn stream(
        &self,
        request: &ChatRequest,
        cancel: &AtomicBool,
        on_event: &mut dyn FnMut(ProviderResponse) -> Result<()>,
    ) -> Result<()>;
}

#[derive(Debug, Clone)]
pub enum ProviderResponse {
    Token(String),
    Plan(EditPlan),
}

#[derive(Debug, Clone)]
pub struct ProviderConfig {
    pub requested: String,
    pub deepseek_api_key: Option<String>,
    pub openai_api_key: Option<String>,
    pub anthropic_api_key: Option<String>,
    pub deepseek_model: String,
    pub openai_model: String,
    pub anthropic_model: String,
    pub anthropic_version: String,
}

impl ProviderConfig {
    pub fn from_env() -> Self {
        Self {
            requested: env::var("CHTHONIC_PROVIDER")
                .or_else(|_| env::var("DEEPSEEK_CORE_PROVIDER"))
                .unwrap_or_else(|_| "auto".to_owned())
                .to_lowercase(),
            deepseek_api_key: env::var("DEEPSEEK_API_KEY").ok(),
            openai_api_key: env::var("OPENAI_API_KEY").ok(),
            anthropic_api_key: env::var("ANTHROPIC_API_KEY").ok(),
            deepseek_model: env::var("DEEPSEEK_MODEL")
                .or_else(|_| env::var("CHTHONIC_DEEPSEEK_MODEL"))
                .unwrap_or_else(|_| DEFAULT_DEEPSEEK_MODEL.to_owned()),
            openai_model: env::var("OPENAI_MODEL")
                .or_else(|_| env::var("CHTHONIC_OPENAI_MODEL"))
                .unwrap_or_else(|_| DEFAULT_OPENAI_MODEL.to_owned()),
            anthropic_model: env::var("ANTHROPIC_MODEL")
                .or_else(|_| env::var("CHTHONIC_ANTHROPIC_MODEL"))
                .unwrap_or_else(|_| DEFAULT_ANTHROPIC_MODEL.to_owned()),
            anthropic_version: env::var("ANTHROPIC_VERSION")
                .unwrap_or_else(|_| "2023-06-01".to_owned()),
        }
    }
}

pub fn provider_from_config(
    config: &ProviderConfig,
) -> Result<Box<dyn ChatProvider + Send + Sync>> {
    match config.requested.as_str() {
        "auto" => {
            if config.deepseek_api_key.is_some() {
                DeepSeekProvider::from_config(config)
                    .map(|provider| Box::new(provider) as Box<dyn ChatProvider + Send + Sync>)
            } else if config.openai_api_key.is_some() {
                OpenAiProvider::from_config(config)
                    .map(|provider| Box::new(provider) as Box<dyn ChatProvider + Send + Sync>)
            } else if config.anthropic_api_key.is_some() {
                AnthropicProvider::from_config(config)
                    .map(|provider| Box::new(provider) as Box<dyn ChatProvider + Send + Sync>)
            } else {
                Ok(Box::new(DeterministicProvider))
            }
        }
        "deepseek" => DeepSeekProvider::from_config(config)
            .map(|provider| Box::new(provider) as Box<dyn ChatProvider + Send + Sync>),
        "openai" | "codex" => OpenAiProvider::from_config(config)
            .map(|provider| Box::new(provider) as Box<dyn ChatProvider + Send + Sync>),
        "anthropic" | "claude" => AnthropicProvider::from_config(config)
            .map(|provider| Box::new(provider) as Box<dyn ChatProvider + Send + Sync>),
        "deterministic" | "stub" | "offline" => Ok(Box::new(DeterministicProvider)),
        other => bail!("unknown CHTHONIC_PROVIDER value: {other}"),
    }
}

pub struct DeterministicProvider;

impl ChatProvider for DeterministicProvider {
    fn stream(
        &self,
        request: &ChatRequest,
        cancel: &AtomicBool,
        on_event: &mut dyn FnMut(ProviderResponse) -> Result<()>,
    ) -> Result<()> {
        if let Some(uri) = deterministic_edit_target(&request.text) {
            let response = format!(
                "I drafted a snippet-guarded edit plan for {uri}. Review it before applying."
            );
            for chunk in response_chunks(&response) {
                if cancel.load(Ordering::SeqCst) {
                    bail!("chat stream cancelled");
                }
                on_event(ProviderResponse::Token(chunk))?;
                thread::sleep(Duration::from_millis(18));
            }
            on_event(ProviderResponse::Plan(deterministic_edit_plan(uri)))?;
            return Ok(());
        }

        let response = if request.text.trim().is_empty() {
            "DeepSeek-Core is alive. Send a prompt to start the sidecar stream.".to_owned()
        } else {
            format!(
                "DeepSeek-Core agent received the prompt inside {}.\n\nPrompt: {}\n\nProvider routing is isolated behind the Rust ChatProvider trait. Set CHTHONIC_PROVIDER=deepseek, openai, or anthropic with the matching API key to use live SSE streaming.",
                request.workspace,
                request.text.trim()
            )
        };

        for chunk in response_chunks(&response) {
            if cancel.load(Ordering::SeqCst) {
                bail!("chat stream cancelled");
            }
            on_event(ProviderResponse::Token(chunk))?;
            thread::sleep(Duration::from_millis(18));
        }

        Ok(())
    }
}

struct DeepSeekProvider {
    client: Client,
    api_key: String,
    model: String,
}

impl DeepSeekProvider {
    fn from_config(config: &ProviderConfig) -> Result<Self> {
        Ok(Self {
            client: Client::builder()
                .timeout(Duration::from_secs(300))
                .build()
                .context("failed to build DeepSeek HTTP client")?,
            api_key: config.deepseek_api_key.clone().context(
                "DEEPSEEK_API_KEY or SecretStorage deepseek key is required for DeepSeek provider",
            )?,
            model: config.deepseek_model.clone(),
        })
    }
}

impl ChatProvider for DeepSeekProvider {
    fn stream(
        &self,
        request: &ChatRequest,
        cancel: &AtomicBool,
        on_event: &mut dyn FnMut(ProviderResponse) -> Result<()>,
    ) -> Result<()> {
        if cancel.load(Ordering::SeqCst) {
            bail!("chat stream cancelled");
        }
        let response = self
            .client
            .post(DEEPSEEK_CHAT_COMPLETIONS_URL)
            .bearer_auth(&self.api_key)
            .header(ACCEPT, "text/event-stream")
            .header(CONTENT_TYPE, "application/json")
            .json(&json!({
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": provider_system_prompt(&request.workspace)
                    },
                    {
                        "role": "user",
                        "content": request.text
                    }
                ],
                "stream": true
            }))
            .send()
            .context("failed to send DeepSeek Chat Completions request")?;

        let mut full_text = String::new();
        stream_sse(response, cancel, |event| {
            if event.event.as_deref() == Some("error") {
                bail!("DeepSeek stream error: {}", event.data);
            }

            let value: Value = serde_json::from_str(&event.data).unwrap_or(Value::Null);
            if let Some(error) = value.get("error") {
                bail!("DeepSeek stream error: {error}");
            }

            for choice in value
                .get("choices")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
            {
                if let Some(content) = choice
                    .get("delta")
                    .and_then(|delta| delta.get("content"))
                    .and_then(Value::as_str)
                {
                    full_text.push_str(content);
                    on_event(ProviderResponse::Token(content.to_owned()))?;
                }
                if let Some(reasoning) = choice
                    .get("delta")
                    .and_then(|delta| delta.get("reasoning_content"))
                    .and_then(Value::as_str)
                {
                    full_text.push_str(reasoning);
                    on_event(ProviderResponse::Token(reasoning.to_owned()))?;
                }
            }

            Ok(())
        })?;
        emit_plan_if_present(&full_text, on_event)
    }
}

struct OpenAiProvider {
    client: Client,
    api_key: String,
    model: String,
}

impl OpenAiProvider {
    fn from_config(config: &ProviderConfig) -> Result<Self> {
        Ok(Self {
            client: Client::builder()
                .timeout(Duration::from_secs(300))
                .build()
                .context("failed to build OpenAI HTTP client")?,
            api_key: config.openai_api_key.clone().context(
                "OPENAI_API_KEY or SecretStorage openai key is required for OpenAI provider",
            )?,
            model: config.openai_model.clone(),
        })
    }
}

impl ChatProvider for OpenAiProvider {
    fn stream(
        &self,
        request: &ChatRequest,
        cancel: &AtomicBool,
        on_event: &mut dyn FnMut(ProviderResponse) -> Result<()>,
    ) -> Result<()> {
        if cancel.load(Ordering::SeqCst) {
            bail!("chat stream cancelled");
        }
        let response = self
            .client
            .post(OPENAI_RESPONSES_URL)
            .bearer_auth(&self.api_key)
            .header(ACCEPT, "text/event-stream")
            .header(CONTENT_TYPE, "application/json")
            .json(&json!({
                "model": self.model,
                "input": [
                    {
                        "role": "developer",
                        "content": provider_system_prompt(&request.workspace)
                    },
                    {
                        "role": "user",
                        "content": request.text
                    }
                ],
                "stream": true
            }))
            .send()
            .context("failed to send OpenAI Responses request")?;

        let mut full_text = String::new();
        stream_sse(response, cancel, |event| {
            if event.event.as_deref() == Some("error") {
                bail!("OpenAI stream error: {}", event.data);
            }

            let value: Value = serde_json::from_str(&event.data).unwrap_or(Value::Null);
            match value.get("type").and_then(Value::as_str) {
                Some("response.output_text.delta") => {
                    if let Some(delta) = value.get("delta").and_then(Value::as_str) {
                        full_text.push_str(delta);
                        on_event(ProviderResponse::Token(delta.to_owned()))?;
                    }
                }
                Some("error") => bail!("OpenAI stream error: {value}"),
                _ => {}
            }

            Ok(())
        })?;
        emit_plan_if_present(&full_text, on_event)
    }
}

struct AnthropicProvider {
    client: Client,
    api_key: String,
    model: String,
    version: String,
}

impl AnthropicProvider {
    fn from_config(config: &ProviderConfig) -> Result<Self> {
        Ok(Self {
            client: Client::builder()
                .timeout(Duration::from_secs(300))
                .build()
                .context("failed to build Anthropic HTTP client")?,
            api_key: config
                .anthropic_api_key
                .clone()
                .context("ANTHROPIC_API_KEY or SecretStorage anthropic key is required for Anthropic provider")?,
            model: config.anthropic_model.clone(),
            version: config.anthropic_version.clone(),
        })
    }
}

impl ChatProvider for AnthropicProvider {
    fn stream(
        &self,
        request: &ChatRequest,
        cancel: &AtomicBool,
        on_event: &mut dyn FnMut(ProviderResponse) -> Result<()>,
    ) -> Result<()> {
        if cancel.load(Ordering::SeqCst) {
            bail!("chat stream cancelled");
        }
        let response = self
            .client
            .post(ANTHROPIC_MESSAGES_URL)
            .header("x-api-key", &self.api_key)
            .header("anthropic-version", &self.version)
            .header(ACCEPT, "text/event-stream")
            .header(CONTENT_TYPE, "application/json")
            .json(&json!({
                "model": self.model,
                "max_tokens": 4096,
                "system": provider_system_prompt(&request.workspace),
                "messages": [
                    {
                        "role": "user",
                        "content": request.text
                    }
                ],
                "stream": true
            }))
            .send()
            .context("failed to send Anthropic Messages request")?;

        let mut full_text = String::new();
        stream_sse(response, cancel, |event| {
            if event.event.as_deref() == Some("error") {
                bail!("Anthropic stream error: {}", event.data);
            }

            let value: Value = serde_json::from_str(&event.data).unwrap_or(Value::Null);
            match value.get("type").and_then(Value::as_str) {
                Some("content_block_delta") => {
                    if value
                        .get("delta")
                        .and_then(|delta| delta.get("type"))
                        .and_then(Value::as_str)
                        == Some("text_delta")
                    {
                        if let Some(text) = value
                            .get("delta")
                            .and_then(|delta| delta.get("text"))
                            .and_then(Value::as_str)
                        {
                            full_text.push_str(text);
                            on_event(ProviderResponse::Token(text.to_owned()))?;
                        }
                    }
                }
                Some("error") => bail!("Anthropic stream error: {value}"),
                _ => {}
            }

            Ok(())
        })?;
        emit_plan_if_present(&full_text, on_event)
    }
}

struct SseEvent {
    event: Option<String>,
    data: String,
}

fn stream_sse(
    mut response: Response,
    cancel: &AtomicBool,
    mut on_event: impl FnMut(SseEvent) -> Result<()>,
) -> Result<()> {
    let status = response.status();
    if !status.is_success() {
        let body = response.text().unwrap_or_default();
        bail!("provider HTTP error {status}: {body}");
    }

    let mut reader = BufReader::new(&mut response);
    let mut event = None;
    let mut data_lines = Vec::new();
    let mut line = String::new();

    loop {
        if cancel.load(Ordering::SeqCst) {
            bail!("chat stream cancelled");
        }
        line.clear();
        let read = reader
            .read_line(&mut line)
            .context("failed to read provider SSE line")?;
        if read == 0 {
            break;
        }

        let trimmed = line.trim_end_matches(['\r', '\n']);
        if trimmed.is_empty() {
            if !data_lines.is_empty() {
                let data = data_lines.join("\n");
                if data != "[DONE]" {
                    on_event(SseEvent {
                        event: event.take(),
                        data,
                    })?;
                }
                data_lines.clear();
            }
            continue;
        }

        if let Some(value) = trimmed.strip_prefix("event:") {
            event = Some(value.trim().to_owned());
        } else if let Some(value) = trimmed.strip_prefix("data:") {
            data_lines.push(value.trim_start().to_owned());
        }
    }

    if !data_lines.is_empty() {
        let data = data_lines.join("\n");
        if data != "[DONE]" {
            on_event(SseEvent { event, data })?;
        }
    }

    Ok(())
}

fn response_chunks(text: &str) -> impl Iterator<Item = String> + '_ {
    let mut chunks = Vec::new();
    let mut current = String::new();

    for character in text.chars() {
        current.push(character);
        if current.len() >= 16 {
            chunks.push(std::mem::take(&mut current));
        }
    }

    if !current.is_empty() {
        chunks.push(current);
    }

    chunks.into_iter()
}

fn deterministic_edit_target(text: &str) -> Option<String> {
    let trimmed = text.trim();
    let path = trimmed
        .strip_prefix("suggest an edit to ")
        .or_else(|| trimmed.strip_prefix("suggest edit to "))?
        .trim()
        .trim_matches('"');
    if path.is_empty() {
        return None;
    }
    Some(path_or_uri_to_uri(path))
}

fn deterministic_edit_plan(uri: String) -> EditPlan {
    EditPlan {
        plan_id: format!("plan-{}", crate::session::now_ms()),
        summary: "Provider-generated deterministic edit plan".to_owned(),
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
            new_text: "// chthonic provider-planned edit\n".to_owned(),
            snippet_id: None,
        }],
        required_permissions: vec![Permission::WriteFile],
        created_at_ms: crate::session::now_ms(),
    }
}

fn path_or_uri_to_uri(path_or_uri: &str) -> String {
    if path_or_uri.starts_with("file://") {
        path_or_uri.to_owned()
    } else {
        format!("file:///{}", path_or_uri.replace('\\', "/"))
    }
}

fn emit_plan_if_present(
    text: &str,
    on_event: &mut dyn FnMut(ProviderResponse) -> Result<()>,
) -> Result<()> {
    if let Some(plan) = parse_plan_from_text(text) {
        on_event(ProviderResponse::Plan(plan))?;
    }
    Ok(())
}

fn provider_system_prompt(workspace: &str) -> String {
    format!(
        "You are Chthonic Code, a Rust-native local coding agent running inside workspace {workspace}. Be concise and code-oriented.\n\nWhen you only need to answer, stream normal text. When you propose file edits, include exactly one JSON object in a fenced ```json block that matches this schema:\n{{\"planId\":\"plan-<short-id>\",\"summary\":\"short user-facing summary\",\"edits\":[{{\"uri\":\"file:///absolute/path\",\"range\":{{\"start\":{{\"line\":0,\"character\":0}},\"end\":{{\"line\":0,\"character\":0}}}},\"newText\":\"replacement text\"}}],\"requiredPermissions\":[\"writeFile\"],\"createdAtMs\":0}}\nUse zero-based line and character positions. Omit snippetId; the Rust core creates snippets before confirmation. Do not include comments inside JSON."
    )
}
