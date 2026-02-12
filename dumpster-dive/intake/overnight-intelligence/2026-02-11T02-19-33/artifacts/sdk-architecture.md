# SDK Architecture Analysis — 2026-02-11T02-19-33

## Analysis: GitHub Copilot SDK Type Definitions

### 1. Exported Functions
**None visible in snippet.** Only type/interface exports shown.

### 2. Key Interfaces/Types

| Name | Purpose |
|------|---------|
| `AbortEvent` | User abort event; triggers completion of orphaned tool calls |
| `AgentMode` | UI mode enum: "interactive" \| "plan" \| "autopilot" |
| `AgentStopHook` | Callback fired when agent naturally stops (no more tool calls) |
| `AgentStopHookInput` | Hook input with sessionId, transcriptPath, stopReason |
| `AgentStopHookOutput` | Hook output allowing "block" or "allow" decision |
| `AgentTask` | Background subagent task with status, result, timing |
| `AssistantIntentEvent` | Ephemeral event carrying assistant intent string |
| `AssistantMessageDeltaEvent` | Streaming delta chunk with messageId, deltaContent, sizeBytes |
| `AssistantMessageEvent` | Persistent message from LLM (with tool calls & reasoning) |
| `AgentAction` | Union literal: "fix" \| "fix-pr-comment" \| "task" |
| `ApiKeyAuthInfo` | Auth config: type + apiKey + host |
| `AssessedCommand` | Command assessment with identifier + readOnly flag |

### 3. Integration Patterns Worth Noting

1. **Zod-based validation**: All events use `z_2.infer<typeof [Schema]>` for type-safe schema definitions.
2. **Ephemeral vs persistent**: Events flagged `ephemeral: true` (streaming) vs persistent (transcript).
3. **Streaming support**: `AssistantMessageDeltaEvent` accumulates chunks for incremental response building.
4. **Hook extensibility**: `AgentStopHook` allows custom decision logic ("block" | "allow") on agent completion.
5. **Hierarchical events**: Base event structure with `id`, `timestamp`, `parentId` for session tracing.
6. **MCP + OpenAI integration**: Imports from both `@modelcontextprotocol` and `openai` SDKs for multi-LLM support.
7. **Background task tracking**: `AgentTask` supports status lifecycle with optional error + modelOverride.