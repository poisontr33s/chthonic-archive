---
name: gh-address-comments
description: "REDIRECT - PR comment handling is now in gh-fix-ci. Use gh-fix-ci for both CI failures and review comment triage."
allowed-tools: "Read, Write, Glob, Grep, Bash"
user-invocable: true
---

# gh-address-comments -> gh-fix-ci

**This skill has been absorbed into gh-fix-ci.**

The PR review comment workflow (fetch, triage, apply fixes) is now a section in gh-fix-ci alongside the CI failure workflow. Both share auth verification and PR resolution.

See: `.claude/skills/gh-fix-ci/SKILL.md`
