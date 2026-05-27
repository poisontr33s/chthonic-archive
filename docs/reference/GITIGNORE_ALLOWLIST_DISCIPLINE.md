---
sid: DOC_GITIGNORE_ALLOWLIST_DISCIPLINE
title: Gitignore Allowlist Discipline
type: reference
status: canonical
created: 2026-05-15
authors:
  - Codex
audience:
  - all
tags:
  - git
  - gitignore
  - ci
  - source-visibility
---

<!--
@SID: DOC_GITIGNORE_ALLOWLIST_DISCIPLINE
@Type: Reference
@Context: Prevent allowlist .gitignore drift from hiding source files
-->

# Gitignore Allowlist Discipline

This repository uses an allowlist `.gitignore`: it starts with `*`, then re-opens approved paths with `!` rules. That posture protects the archive from accidental model weights, build outputs, caches, and binary payloads. The cost is predictable: a new source lane can exist on disk while Git, VS Code source control, and agents do not see it.

Git is the source of truth. VS Code and VS Code Insiders follow Git visibility; they do not overrule `.gitignore`.

## Rule

When adding a new source lane, update [.gitignore](../../.gitignore) in the same change.

Every new lane needs both forms:

```gitignore
!path/to/lane/
!path/to/lane/**/*.ts
```

Use the narrowest useful extension pattern. Prefer source-shaped patterns like `*.ts`, `*.py`, `*.rs`, `*.md`, `*.json`, `*.toml`, `*.svg`, or a small directory-specific glob. Keep generated outputs ignored near the same block:

```gitignore
path/to/lane/dist/
path/to/lane/node_modules/
path/to/lane/.venv/
```

## Required Check

Run this after creating files or new directories:

```powershell
bun run ignore:audit
```

Equivalent CI lane:

```powershell
bun run ci/run.ts --check ignored-source
```

The check scans managed source roots for ignored source-shaped files. A failure means a file is being swallowed by `.gitignore` and must either get a narrow `!` rule or move into an existing allowed lane.

## Commit Automation

The staged CI gate includes `ignored-source`, and the Git pre-commit hook runs that staged gate:

```powershell
bun run ci:staged
```

`bun install` refreshes the local pre-commit hook through [scripts/postinstall.ps1](../../scripts/postinstall.ps1). To install or repair it directly:

```powershell
bun run hooks:precommit
```

To verify that normal Git commits, including VS Code and VS Code Insiders Commit button commits, will run the gate:

```powershell
bun run hooks:verify
```

The hook blocks the commit when `ignored-source` finds a swallowed source file. A user can still bypass hooks with Git's explicit no-verify path, but the normal commit path is guarded.

## Debug Commands

Show all visible untracked files:

```powershell
git status --short --untracked-files=all
```

Explain why a specific path is ignored:

```powershell
git check-ignore -v path/to/file
```

List the ignored-source check in the local CI registry:

```powershell
bun run ci/run.ts --list
```

## Agent Convention

Before saying a new file "does not exist," "is not visible," or "VS Code ignored it," run `bun run ignore:audit` and inspect `git check-ignore -v <path>`.

When adding a new app, extension, script subtree, MCP lane, or generated-source bridge, include the `.gitignore` allowlist change with the implementation. Do not leave this as a user memory burden.
