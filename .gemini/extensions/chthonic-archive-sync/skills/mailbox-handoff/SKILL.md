---
name: mailbox-handoff
description: Continue triad work from the latest mailbox handoff and respond with one concise completion note.
---

# Mailbox Handoff

Use this skill when the task says "check mailbox", "check your mail", "continue from handoff", or needs Claude/Codex/Gemini coordination.

## Workflow

1. Read the newest relevant file in `claude/mailbox/`, `codex/mailbox/`, or `gemini/mailbox/`.
2. Treat the mailbox as continuation, not analysis.
3. Execute the requested work in the workspace.
4. Write one response note with actions taken, files changed, tests run, and next actions.

## References

- `AGENT_COMMON.md`
- `.temple/protocols/MAILBOX_PROTOCOL.md`
- `.codex/skills/mailbox-handoff/SKILL.md`

## Command Hints

- `Get-ChildItem claude/mailbox -Filter *.md | Sort-Object LastWriteTime -Descending`
- `Get-ChildItem codex/mailbox -Filter *.md | Sort-Object LastWriteTime -Descending`
- `Get-ChildItem gemini/mailbox -Filter *.md | Sort-Object LastWriteTime -Descending`
