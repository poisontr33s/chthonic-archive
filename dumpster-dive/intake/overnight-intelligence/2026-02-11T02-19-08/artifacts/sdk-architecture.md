# SDK Architecture Analysis — 2026-02-11T02-19-08

## Exported Functions
**None in this excerpt** — only type definitions and interfaces.

## Key Interfaces/Types

| Name | Purpose |
|------|---------|
| `AbortEvent` | User-triggered turn cancellation with reason |
| `AgentMode` | UI mode enum: `interactive`, `plan`, `autopilot` |
| `AgentStopHook` | Callback fired when agent naturally stops (async) |
| `AgentStopHookInput` | Hook input: `sessionId`, `transcriptPath`, `stopReason` |
| `AgentStopHookOutput` | Hook decision: `block` or `allow` to continue |
| `AgentTask` | Background agent task (id, status, prompt, result, error) |
| `AssistantIntentEvent` | Ephemeral intent extraction event |
| `AssistantMessageDeltaEvent` | Streaming delta chunks for LLM responses |
| `AssistantMessageEvent` | Full LLM message with tool calls |
| `ApiKeyAuthInfo` | Auth credentials (api-key type) |
| `AssessedCommand` | Shell command audit (identifier, readOnly flag) |

## Patterns Worth Noting

1. **Zod Runtime Validation**: All events use `z_2.infer<typeof EventSchema>` — runtime-validated types for stream reliability.
2. **Event Architecture**: Base events share `{id, timestamp, parentId, ephemeral}` — tree-structured message flow with transient flags.
3. **Hook/Callback Extensibility**: `AgentStopHook` pattern allows intercepting agent lifecycle (decision gates for `block|allow`).
4. **Streaming + Persistence Split**: `ephemeral: true` for deltas; omitted for persistent messages.
5. **MCP + OpenAI Stack**: Combines MCP SDK (transports: SSE, Stdio, HTTP) with OpenAI Chat Completions API.
6. **Tool Call Integration**: Types reference `ChatCompletionMessageToolCall`, `ChatCompletionTool` — full agentic loop support.