---
sid: FORGE_WORKFLOW_CATALOG_V1
title: Recovered Workflow Pattern Catalogue
created: 2026-03-05T16:04:23+00:00
source_files: [".github/workflows/claude-code-review.yml.off", ".github/workflows/claude.yml.off", ".github/workflows/gemini-dispatch.yml.off", ".github/workflows/gemini-invoke.yml.off", ".github/workflows/gemini-review.yml.off", ".github/workflows/gemini-scheduled-triage.yml.off", ".github/workflows/gemini-triage.yml.off"]
pathway: workflow.off -> job and action extraction -> pattern catalogue
kept: Workflow names, jobs, and action versions.
discarded: The disabled-by-rename wrapper around the live logic.
---
# Recovered Workflow Pattern Catalogue

## Claude Code Review

- Source: `.github/workflows/claude-code-review.yml.off`
- Jobs: pull_request, claude-review
- Actions: actions/checkout@v4, anthropics/claude-code-action@v1

## Claude Code

- Source: `.github/workflows/claude.yml.off`
- Jobs: issue_comment, issues, claude
- Actions: actions/checkout@v4, anthropics/claude-code-action@v1

## '🔀 Gemini Dispatch'

- Source: `.github/workflows/gemini-dispatch.yml.off`
- Jobs: pull_request, issues, issue_comment, defaults, run, debugger, dispatch, review, triage, invoke
- Actions: 'actions/create-github-app-token@29824e69f54612133e76f7eaac726eef6c875baf', 'actions/github-script@60a0d83039c74a4aee543508d2ffcb1c3799cdea', './.github/workflows/gemini-review.yml', './.github/workflows/gemini-triage.yml', './.github/workflows/gemini-invoke.yml', 'actions/create-github-app-token@29824e69f54612133e76f7eaac726eef6c875baf'

## '▶️ Gemini Invoke'

- Source: `.github/workflows/gemini-invoke.yml.off`
- Jobs: workflow_call, concurrency, defaults, run, invoke
- Actions: 'actions/create-github-app-token@29824e69f54612133e76f7eaac726eef6c875baf', 'google-github-actions/run-gemini-cli@v0'

## '🔎 Gemini Review'

- Source: `.github/workflows/gemini-review.yml.off`
- Jobs: workflow_call, concurrency, defaults, run, review
- Actions: 'actions/create-github-app-token@29824e69f54612133e76f7eaac726eef6c875baf', 'actions/checkout@8e8c483db84b4bee98b60c0593521ed34d9990e8', 'google-github-actions/run-gemini-cli@v0'

## '📋 Gemini Scheduled Issue Triage'

- Source: `.github/workflows/gemini-scheduled-triage.yml.off`
- Jobs: schedule, workflow_dispatch, concurrency, defaults, run, triage, label
- Actions: 'actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd', 'google-github-actions/run-gemini-cli@v0', 'actions/create-github-app-token@29824e69f54612133e76f7eaac726eef6c875baf', 'actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd'

## '🔀 Gemini Triage'

- Source: `.github/workflows/gemini-triage.yml.off`
- Jobs: workflow_call, concurrency, defaults, run, triage, label
- Actions: 'actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd', 'google-github-actions/run-gemini-cli@v0', 'actions/create-github-app-token@29824e69f54612133e76f7eaac726eef6c875baf', 'actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd'

