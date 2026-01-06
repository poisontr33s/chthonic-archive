# PR: Harden preflight_execution_context + Add Validation Schema

## Summary
Adds a governance-first MCP tool that reports the execution ABI and refuses ambiguity.
This externalizes session-derived constraints (F1–F4) as protocol semantics.

## What
- New MCP tool: `preflight_execution_context`
- Deterministic, read-only, stdio-only
- Hard-fails on OS / shell / runtime ambiguity
- Explicitly reports permission state as `unknown` (never assumes authority)
- JSON schema for client validation and golden request/response example

## Why
- Prevents false progress and cross-shell confusion
- Provides a canonical preflight check that clients must call before mutating actions
- Makes governance machine-readable and enforceable

## Testing
- Use the golden I/O vector in `mcp/tools/preflightExecutionContext.test.json`
- Validate responses with `mcp/tools/ExecutionContext.schema.json`
