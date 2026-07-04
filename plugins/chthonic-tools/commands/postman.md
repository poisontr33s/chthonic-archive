---
description: Generate a "Response: <topic>" mailbox continuation skeleton from the latest handoff (Codex/Claude).
argument-hint: <codex|claude> [--to codex|claude]
allowed-tools: [Bash, Read]
---

# Postman (Mailbox Continuation)

This command exists to eliminate manual boilerplate like `# Response: <topic>`.

## Usage

- Emit a response skeleton for the latest handoff in a mailbox:

```text
uv run .codex/skills/mailbox-handoff/scripts/mailbox_check.py --mailbox $ARGUMENTS --emit-response --to claude
```

Notes:
- Use `--mailbox codex` or `--mailbox claude`.
- For cross-handoff, set `--to codex` or `--to claude`.

## Tip: Codex -> Claude crossover

If you need a single, structured task packet created for Claude to continue from inside the IDE:

```text
pwsh -NoProfile -File scripts/claude_crossover.ps1 -Topic "<what to do next>"
```
