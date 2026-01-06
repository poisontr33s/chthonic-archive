# PR: Harden preflight_execution_context + Add Validation Schema

## Summary

Hardened the `preflight_execution_context` MCP tool to fix fragility issues in environment detection and added JSON schema validation for automated testing.

## Changes

### 1. Hardened Runtime Detection (`mcp/tools/preflightExecutionContext.ts`)

**Import Fixes:**
- Renamed `type` import to `osTypeFn` to avoid keyword collision
- Removed unused `version` import

**Robustness Improvements:**
- Use `globalThis.Bun` instead of bare `Bun` for runtime detection
- Use `globalThis.process?.env?.SHELL` for safe shell detection
- Check both `process.versions.node` and `versions.node` for Node compatibility
- Normalized shell name extraction with better path handling

**Added Field:**
- `governance_version: "session-learning.v1"` for downstream version assertions

### 2. Test Examples (`mcp/tools/preflightExecutionContext.test.json`)

Provides:
- Sample MCP request/response pairs
- Expected response structure
- How to run tests locally
- Validation instructions

### 3. JSON Schema (`mcp/tools/ExecutionContextSchema.json`)

Enables automated validation of tool responses with:
- Strict type constraints for all fields
- Enum validation for OS/platform/runtime
- Required field enforcement
- Governance invariant validation (F1/F2/F3/F4 compliance)

## Rationale

**Why globalThis?**
- More robust across different execution contexts (Bun, Node, bundlers)
- Avoids assumptions about global scope pollution

**Why explicit type annotations?**
- Improves clarity and maintainability
- Catches type errors at compile time

**Why governance_version?**
- Enables clients to validate compatibility with governance rules
- Supports future schema evolution

## Testing

Run the test locally:

```bash
cd mcp && echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"preflight_execution_context","arguments":{}}}' | bun run server.ts
```

Validate response against schema:

```bash
# Extract response content
response=$(cd mcp && echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"preflight_execution_context","arguments":{}}}' | bun run server.ts 2>/dev/null)

# Parse and validate (requires ajv-cli or similar)
echo "$response" | jq -r '.result.content[0].text' | ajv validate -s mcp/tools/ExecutionContextSchema.json -d -
```

## Files Changed

- `mcp/tools/preflightExecutionContext.ts` - Hardened implementation
- `mcp/tools/preflightExecutionContext.test.json` - Test examples (new)
- `mcp/tools/ExecutionContextSchema.json` - JSON schema (new)

## Governance Alignment

- **F1 (Shell Sovereignty)**: Reports canonical shell, no cross-shell execution
- **F2 (Retry Policy)**: Structural failures non-retryable
- **F3 (Permission Preflight)**: Explicit "unknown" permission state
- **F4 (No False Progress)**: Hard-fails on ambiguity

Tool remains:
- Read-only (no process spawning, no environment mutation)
- Deterministic (same environment → same output)
- Governance-first (refusal over false progress)

## Commit Hash

Already pushed to main: `b8e4f05`

---

**Note for Reviewers:**

The `globalThis` pattern may look unusual but is the correct way to handle runtime detection in environments where global scope may vary (Bun native, Bun with Node compat, pure Node, bundled code, etc.).

The JSON schema enforces governance invariants at the protocol level, making it impossible for clients to receive invalid permission states or retry policy signals.
