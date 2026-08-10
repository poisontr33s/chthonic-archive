use serde::{Deserialize, Serialize};
use serde_json::Value;

pub const JSONRPC_VERSION: &str = "2.0";

#[derive(Debug, Clone)]
pub struct ChatRequest {
    pub text: String,
    pub workspace: String,
}

#[derive(Debug, Deserialize)]
pub struct RpcRequest {
    #[allow(dead_code)]
    pub jsonrpc: Option<String>,
    pub id: Option<Value>,
    pub method: String,
    #[serde(default)]
    pub params: Value,
}

#[derive(Debug, Serialize)]
pub struct RpcSuccess {
    pub jsonrpc: &'static str,
    pub id: Value,
    pub result: Value,
}

#[derive(Debug, Serialize)]
pub struct RpcError {
    pub jsonrpc: &'static str,
    pub id: Value,
    pub error: RpcErrorBody,
}

#[derive(Debug, Serialize)]
pub struct RpcErrorBody {
    pub code: i64,
    pub message: String,
}

impl RpcSuccess {
    pub fn new(id: Value, result: Value) -> Self {
        Self {
            jsonrpc: JSONRPC_VERSION,
            id,
            result,
        }
    }
}

impl RpcError {
    pub fn new(id: Value, code: i64, message: impl Into<String>) -> Self {
        Self {
            jsonrpc: JSONRPC_VERSION,
            id,
            error: RpcErrorBody {
                code,
                message: message.into(),
            },
        }
    }
}
