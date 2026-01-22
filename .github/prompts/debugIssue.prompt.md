---
name: debugIssue
description: Identify and fix issues in the codebase
argument-hint: Describe the bug or select error location
tools: [ 'edit', 'search', 'run_in_terminal', 'get_errors' ]
mode: agent
---

Debug: {{argument}}

## Investigation Steps

1. Reproduce the issue
2. Analyze error messages and stack traces
3. Identify root cause
4. Propose and implement fix
5. Verify resolution

## Output

Provide:
- Root cause analysis
- Fix implementation
- Verification approach
