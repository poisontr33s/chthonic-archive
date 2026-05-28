---
name: scm-triage
description: Audit working tree state, classify edits, and move forward without clobbering user work.
---

# SCM Triage

Use this skill when the repo is dirty, before large edits, or when you need to separate active work from noise.

## Workflow

1. Run `git status --short`.
2. Classify changes into user work, active task changes, generated artifacts, and unrelated noise.
3. Do not revert user edits.
4. Before any destructive cleanup, preserve useful signal first.

## References

- `AGENT_COMMON.md`
- `.codex/skills/scm-triage/SKILL.md`
